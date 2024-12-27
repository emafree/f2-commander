# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import os
import posixpath
import subprocess
import tempfile
from functools import partial
from importlib.metadata import version
from pathlib import Path
from typing import Any, Optional, Union

import fsspec
from fsspec.core import url_to_fs
from rich.text import Text
from send2trash import send2trash
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.command import DiscoveryHit, Hit, Provider
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Footer

from .commands import Command
from .config import config, set_user_has_accepted_license, user_has_accepted_license
from .errors import error_handler_async, with_error_handler
from .fs import (
    copy,
    is_archive_fs,
    is_executable,
    is_local_fs,
    is_supported_archive,
    move,
    open_archive,
    write_archive,
)
from .shell import editor, native_open, shell, viewer
from .widgets.bookmarks import GoToBookmarkDialog
from .widgets.connect import ConnectToRemoteDialog
from .widgets.dialogs import InputDialog, SelectDialog, StaticDialog, Style
from .widgets.filelist import FileList
from .widgets.panel import Panel


class F2AppCommands(Provider):
    @property
    def all_commands(self):
        app_commands = [(self.app, cmd) for cmd in self.app.BINDINGS_AND_COMMANDS]
        flist = self.app.active_filelist
        flist_commands = [(flist, cmd) for cmd in flist.BINDINGS_AND_COMMANDS]
        return app_commands + flist_commands

    def _fmt_name(self, cmd, text: Optional[Text] = None):
        t = text or Text(cmd.name)
        if cmd.binding_key is not None:
            t.append(" ")
            t.append(f"[{cmd.binding_key}]", style="dim")
        return t

    async def search(self, query: str):
        matcher = self.matcher(query)
        for node, cmd in self.all_commands:
            score = matcher.match(cmd.name)
            if score > 0:
                yield Hit(
                    score,
                    self._fmt_name(cmd, matcher.highlight(cmd.name)),
                    partial(node.run_action, cmd.action),
                    help=f"{cmd.description}\n",
                )

    async def discover(self):
        for node, cmd in self.all_commands:
            yield DiscoveryHit(
                self._fmt_name(cmd),
                partial(node.run_action, cmd.action),
                help=f"{cmd.description}\n",
            )


class F2Commander(App):
    CSS_PATH = "tcss/main.tcss"
    BINDINGS_AND_COMMANDS = [
        Command(
            "swap_panels",
            "Swap panels",
            "Swap left and right panels",
            "ctrl+w",
        ),
        Command(
            "same_location",
            "Same location in other panel",
            "Open the same location in the other (inactive) panel",
            "ctrl+s",
        ),
        Command(
            "change_left_panel",
            "Left panel",
            "Change the left panel type",
            "ctrl+e",
        ),
        Command(
            "change_right_panel",
            "Right panel",
            "Change the right panel type",
            "ctrl+r",
        ),
        Command(
            "go_to_path",
            "Enter path",
            "Enter a path to jump to it",
            "ctrl+g",
        ),
        Command(
            "toggle_hidden",
            "Togghle hidden",
            "Show or hide hidden files",
            "h",
        ),
        Command(
            "rename",
            "Rename",
            "Rename a file or a directory",
            "M",
        ),
        Command(
            "mkfile",
            "Create a file",
            "Create a new file (touch)",
            None,
        ),
        Command(
            "archive",
            "Archive / compress files",
            "Archive and optionally compress current selection",
            None,
        ),
        Command(
            "connect",
            "Connect to remote",
            "Connect to a remote file system",
            "ctrl+t",
        ),
        Command(
            "toggle_dirs_first",
            "Toggle directories first",
            "Show directories first or ordered among files",
            None,
        ),
        Command(
            "toggle_order_case_sensitive",
            "Toggle case sensitive name order",
            "Whether name ordering is case sensitive or not",
            None,
        ),
        Command(
            "change_theme",
            "Change theme",
            "Change the theme (colors)",
            None,
        ),
        Command(
            "about",
            "About",
            "Information about this software",
            None,
        ),
    ]
    BINDINGS = [
        Binding("?", "help", "Help"),
        Binding("b", "go_to_bookmark", "Bookmarks"),
        Binding("v", "view", "View"),
        Binding("e", "edit", "Edit"),
        Binding("c", "copy", "Copy"),
        Binding("m", "move", "Move"),
        Binding("D", "delete", "Delete"),
        Binding("ctrl+n", "mkdir", "MkDir"),
        Binding("x", "shell", "Shell"),
        Binding("q", "quit", "Quit"),
    ] + [
        Binding(cmd.binding_key, cmd.action, cmd.description, show=False)
        for cmd in BINDINGS_AND_COMMANDS
        if cmd.binding_key is not None
    ]  # type: ignore
    COMMANDS = {F2AppCommands}

    show_hidden = reactive(config.show_hidden)
    dirs_first = reactive(config.dirs_first)
    order_case_sensitive = reactive(config.order_case_sensitive)
    swapped = reactive(False)

    def compose(self) -> ComposeResult:
        self.panels_container = Horizontal()
        self.panel_left = Panel("left", id="left")
        self.panel_right = Panel("right", id="right")
        with self.panels_container:
            yield self.panel_left
            yield self.panel_right
        yield Footer()

    @work
    async def action_change_theme(self):
        def on_select(theme: str):
            self.theme = theme
            config.theme = theme

        self.push_screen(
            SelectDialog(
                title="Change the theme to:",
                options=sorted([(t, t) for t in self.available_themes.keys()]),
                value=self.theme,
                allow_blank=False,
            ),
            on_select,
        )

    def action_toggle_hidden(self):
        self.show_hidden = not self.show_hidden

    def watch_show_hidden(self, old: bool, new: bool):
        self.left.show_hidden = new
        self.right.show_hidden = new
        config.show_hidden = new

    def action_toggle_dirs_first(self):
        self.dirs_first = not self.dirs_first

    # TODO: save default value to user options, restore on start
    def watch_dirs_first(self, old: bool, new: bool):
        self.left.dirs_first = new
        self.right.dirs_first = new
        config.dirs_first = new

    def action_toggle_order_case_sensitive(self):
        self.order_case_sensitive = not self.order_case_sensitive

    # TODO: save default value to user options, restore on start
    def watch_order_case_sensitive(self, old: bool, new: bool):
        self.left.order_case_sensitive = new
        self.right.order_case_sensitive = new
        config.order_case_sensitive = new

    def action_swap_panels(self):
        self.swapped = not self.swapped

    def watch_swapped(self, old: bool, new: bool):
        # TODO: After the swap the "left" panel will on the right and vice versa.
        #       Maybe there is no left/right at all? Panel A and panel B instead?
        #       Or handle the swap by changing root paths (won't swap other types
        #       of panels, though)?
        if new:
            self.panels_container.move_child(self.panel_left, after=self.panel_right)
        else:
            self.panels_container.move_child(self.panel_left, before=self.panel_right)

    def action_same_location(self):
        self.inactive_filelist.fs = self.active_filelist.fs
        self.inactive_filelist.path = self.active_filelist.path

    @work
    async def action_change_left_panel(self):
        self.panel_left.action_change_panel()

    @work
    async def action_change_right_panel(self):
        self.panel_right.action_change_panel()

    @property
    def left(self):
        try:
            return self.query_one("#left > *")
        except NoMatches:
            return None

    @property
    def right(self):
        try:
            return self.query_one("#right > *")
        except NoMatches:
            return None

    # FIXME: left/right are not necessarily FileList; make Optional and handle None
    @property
    def active_filelist(self) -> Optional[FileList]:
        for panel in (self.left, self.right):
            if isinstance(panel, FileList) and panel.active:
                return panel
        return None

    @property
    def inactive_filelist(self) -> Optional[FileList]:
        for panel in (self.left, self.right):
            if isinstance(panel, FileList) and not panel.active:
                return panel
        return None

    @work
    async def on_mount(self, event):
        self.theme = config.theme
        if not user_has_accepted_license():
            self.action_about()

    @on(FileList.Selected)
    def on_file_selected(self, event: FileList.Selected):
        for c in self.query("Panel > *"):
            if hasattr(c, "on_other_panel_selected"):
                c.on_other_panel_selected(event.fs, event.path)

    @on(FileList.Open)
    def on_file_opened(self, event: FileList.Open):
        fs, path = event.fs, event.path

        if is_local_fs(fs) and is_executable(fs.info(path)):
            # TODO: ask to confirm to run, let choose mode (on a side or in a shell)
            return

        def _open(path: str):
            if (
                is_supported_archive(path)  # probably an archive
                and (  # and it is not nested in another archive
                    self.active_filelist and not is_archive_fs(self.active_filelist.fs)
                )
                and (archive_fs := open_archive(path))  # and it can be open
            ):
                self.active_filelist.parent_fs = self.active_filelist.fs
                self.active_filelist.parent_path = path
                self.active_filelist.fs = archive_fs
                self.active_filelist.path = ""
                self.refresh_bindings()
            else:
                open_cmd = native_open()
                if open_cmd is not None:
                    with self.app.suspend():
                        subprocess.run(open_cmd + [path])
                    self.app.refresh()
                else:
                    # TODO: alert the user
                    pass

        def _open_temp(path: str):
            _open(path)
            os.unlink(path)

        if is_local_fs(fs):
            _open(path)
        else:
            self._download(fs, path, cont_fn=_open_temp)

    def _download(self, fs, path, cont_fn):

        @with_error_handler(self)
        def on_download(result: bool):
            if result:
                _, tmp_file_path = tempfile.mkstemp(
                    prefix=f"{posixpath.basename(path)}.",
                    suffix=posixpath.splitext(path)[1],
                )
                fs.get(path, tmp_file_path)
                cont_fn(tmp_file_path)

        msg = (
            "The file is not in the local file system. "
            "It will be downloaded first. Continue?"
        )
        if is_archive_fs(fs):
            on_download(True)
        else:
            self.push_screen(
                StaticDialog(
                    title="Download?",
                    message=msg,
                    btn_ok="Yes",
                    btn_cancel="No",
                ),
                on_download,
            )

    def _upload(self, fs, local_path, remote_path, cont_fn):

        @with_error_handler(self)
        def on_upload(result: bool):
            if result:
                fs.put(local_path, remote_path)
            cont_fn(local_path)

        self.app.push_screen(
            StaticDialog(
                title="Upload?",
                message="The file was modified. Do you want to upload the new version?",
                btn_ok="Yes",
                btn_cancel="No",
            ),
            on_upload,
        )

    def action_view(self):
        fs = self.active_filelist.fs
        src = self.active_filelist.cursor_path

        if not fs.isfile(src):
            return

        def _view(path: str):
            viewer_cmd = viewer(or_editor=True)
            if viewer_cmd is not None:
                with self.app.suspend():
                    completed_process = subprocess.run(viewer_cmd + [path])
                self.refresh()
                exit_code = completed_process.returncode
                if exit_code != 0:
                    msg = f"Viewer exited with an error ({exit_code})"
                    self.push_screen(StaticDialog.warning("Warning", msg))
            else:
                self.push_screen(StaticDialog.error("Error", "No viewer found!"))

        def _view_temp(path: str):
            _view(path)
            os.unlink(path)

        if is_local_fs(fs):
            _view(src)
        else:
            self._download(fs, src, cont_fn=_view_temp)

    def action_edit(self):
        fs = self.active_filelist.fs
        src = self.active_filelist.cursor_path

        if not fs.isfile(src):
            return

        def _edit(path: str):
            editor_cmd = editor()
            if editor_cmd is not None:
                with self.app.suspend():
                    completed_process = subprocess.run(editor_cmd + [path])
                self.refresh()
                exit_code = completed_process.returncode
                if exit_code != 0:
                    msg = f"Editor exited with an error ({exit_code})"
                    self.push_screen(StaticDialog.warning("Error", msg))
            else:
                self.push_screen(StaticDialog.error("Error", "No editor found!"))

        def _edit_and_upload(path: str):
            prev_mtime = Path(path).stat().st_mtime
            _edit(path)
            new_mtime = Path(path).stat().st_mtime
            if new_mtime > prev_mtime:
                self._upload(fs, path, src, cont_fn=lambda p: os.unlink(p))

        if is_local_fs(fs):
            _edit(src)
        else:
            self._download(fs, src, cont_fn=_edit_and_upload)

    @work
    async def action_copy(self):
        src_fs = self.active_filelist.fs
        sources = self.active_filelist.selected_paths()

        dst_fs = self.inactive_filelist.fs
        destination = self.inactive_filelist.path

        if len(sources) == 0:
            return

        msg = (
            f"Copy {posixpath.basename(sources[0])} to"
            if len(sources) == 1
            else f"Copy {len(sources)} selected entries to"
        )
        dst = await self.push_screen_wait(
            InputDialog(
                title=msg, value=destination, btn_ok="Copy", select_on_focus=False
            )
        )
        if dst is None:  # user cancelled
            return

        if src_fs != dst_fs and not is_local_fs(src_fs) and not is_local_fs(dst_fs):
            if not await self._confirm_download_upload():
                return

        for src in sources:
            await self._copy_one(src_fs, src, dst_fs, dst)

        self.active_filelist.reset_selection()
        self.active_filelist.update_listing()
        self.inactive_filelist.update_listing()

    async def _confirm_download_upload(self):
        msg = (
            "Source and destination are in different remote locations.\n"
            "Continue to download, and then upload?"
        )
        return await self.app.push_screen_wait(
            StaticDialog(
                title="Download, and then upload?",
                message=msg,
                btn_ok="Yes",
                btn_cancel="No",
            )
        )

    async def _copy_one(self, src_fs, src, dst_fs, dst):
        if src_fs.isfile(src):
            dst_path = (
                posixpath.join(dst, posixpath.basename(src))
                if dst_fs.isdir(dst)
                else dst
            )
            if dst_fs.isfile(dst_path):
                msg = f"{dst_path} already exists. Overwrite?"
                if not await self.push_screen_wait(
                    StaticDialog(
                        title="Overwrite?",
                        message=msg,
                        btn_ok="Overwrite",
                        style=Style.WARNING,
                    )
                ):
                    return

        elif src_fs.isdir(src):
            dst_path = (
                posixpath.join(dst, posixpath.basename(src))
                if dst_fs.isdir(dst)
                else dst
            )
            if dst_fs.exists(dst_path):
                msg = (
                    f"{dst_path} already exists.\n"
                    "Merge directories and overwrite existing files?"
                )
                if not await self.push_screen_wait(
                    StaticDialog(
                        title="Merge and overwrite?",
                        message=msg,
                        btn_ok="Merge",
                        style=Style.WARNING,
                    )
                ):
                    return

        async with error_handler_async(self):
            return copy(src_fs, src, dst_fs, dst)

    @work
    async def action_move(self):
        src_fs = self.active_filelist.fs
        sources = self.active_filelist.selected_paths()

        dst_fs = self.inactive_filelist.fs
        destination = self.inactive_filelist.path

        if len(sources) == 0:
            return

        msg = (
            f"Move {posixpath.basename(sources[0])} to"
            if len(sources) == 1
            else f"Move {len(sources)} selected entries to"
        )
        dst = await self.push_screen_wait(
            InputDialog(
                title=msg, value=destination, btn_ok="Move", select_on_focus=False
            )
        )
        if dst is None:  # user cancelled
            return

        if src_fs != dst_fs and not is_local_fs(src_fs) and not is_local_fs(dst_fs):
            if not await self._confirm_download_upload():
                return

        for src in sources:
            await self._move_one(src_fs, src, dst_fs, dst)

        self.active_filelist.reset_selection()
        self.active_filelist.update_listing()
        self.inactive_filelist.update_listing()

    async def _move_one(self, src_fs, src, dst_fs, dst):
        if src_fs.isfile(src):
            dst_path = (
                posixpath.join(dst, posixpath.basename(src))
                if dst_fs.isdir(dst)
                else dst
            )
            if dst_fs.isfile(dst_path):
                dst = dst_path  # CAUTION: overriding with exact **file** path
                # ^^^^^^ : if not done, eventually shutil.move raises an error
                # (try shutil.move('a', 'b') where 'b' is a dir with a file 'a')
                msg = f"{dst_path} already exists. Overwrite?"
                if not await self.push_screen_wait(
                    StaticDialog(
                        title="Overwrite?",
                        message=msg,
                        btn_ok="Overwrite",
                        style=Style.WARNING,
                    )
                ):
                    return

        # CAUTION:
        # Move has no merge for directories intentionally
        # It is considered way too ambiguous and, if necessary,
        # can be achieved otherwise (copy, then delete).

        async with error_handler_async(self):
            return move(src_fs, src, dst_fs, dst)

    @work
    async def action_rename(self):
        src_fs = self.active_filelist.fs

        sources = self.active_filelist.selected_paths()
        if len(sources) != 1:
            return

        src = sources[0]
        name = posixpath.basename(src)

        dst = await self.push_screen_wait(
            InputDialog(title=f"Rename {name} to", value=name, btn_ok="Move")
        )
        if dst is None:  # user cancelled
            return

        # FIXME: only allow simple names in the first place (validation)
        if posixpath.basename(dst) != dst:
            self.push_screen(
                StaticDialog.error(
                    "Error",
                    "Only simple names are allowed for renaming. Otherwise, use Move.",
                )
            )
            return

        async with error_handler_async(self):
            src_fs.mv(src, posixpath.join(posixpath.dirname(src), dst))

        self.active_filelist.reset_selection()
        self.active_filelist.update_listing()
        self.active_filelist.scroll_to_entry(posixpath.basename(dst))

    def action_delete(self):
        fs = self.active_filelist.fs
        paths = self.active_filelist.selected_paths()

        if len(paths) == 0:
            return

        @with_error_handler(self)
        def on_delete(result: bool):
            if result:
                for path in paths:
                    if is_local_fs(fs):
                        send2trash(path)
                    else:
                        fs.rm(path, recursive=fs.isdir(path))
                self.active_filelist.selection = set()  # type: ignore
                self.active_filelist.update_listing()  # type: ignore

        if is_local_fs(fs):
            msg = (
                f"This will move {posixpath.basename(paths[0])} to Trash"
                if len(paths) == 1
                else f"This will move {len(paths)} selected entries to Trash"
            )
        else:
            msg = (
                f"This will PERMANENTLY DELETE {posixpath.basename(paths[0])}"
                if len(paths) == 1
                else f"This will PERMANENTLY DELETE {len(paths)} selected entries"
            )
        self.push_screen(
            StaticDialog(
                title="Delete?",
                message=msg,
                btn_ok="Delete",
                style=Style.DANGER,
            ),
            on_delete,
        )

    @work
    async def action_mkdir(self):
        fs = self.active_filelist.fs
        src = self.active_filelist.path

        new_name = await self.push_screen_wait(
            InputDialog("New directory", btn_ok="Create")
        )
        if new_name is None:
            return

        async with error_handler_async(self):
            new_dir_path = posixpath.join(src, new_name)
            fs.makedirs(new_dir_path, exist_ok=True)
            self.active_filelist.update_listing()
            self.active_filelist.scroll_to_entry(
                posixpath.dirname(new_name) or new_name
            )

    @work
    async def action_mkfile(self):
        fs = self.active_filelist.fs
        src = self.active_filelist.path

        new_name = await self.push_screen_wait(InputDialog("New file", btn_ok="Create"))
        if new_name is None:
            return

        # FIXME: only allow simple names in the first place (validation)
        if posixpath.basename(new_name) != new_name:
            self.push_screen(
                StaticDialog.error("Error", "Only simple names are allowed")
            )
            return

        async with error_handler_async(self):
            new_file_path = posixpath.join(src, new_name)
            fs.touch(new_file_path)
            self.active_filelist.update_listing()
            self.active_filelist.scroll_to_entry(
                posixpath.dirname(new_name) or new_name
            )

    def action_shell(self):
        fs = self.active_filelist.fs
        cwd = self.active_filelist.path if is_local_fs(fs) else Path.cwd().as_posix()

        shell_cmd = shell()
        if shell_cmd is not None:
            with self.app.suspend():
                completed_process = subprocess.run(shell_cmd, cwd=cwd)
            self.refresh()
            self.active_filelist.update_listing()
            self.inactive_filelist.update_listing()
            exit_code = completed_process.returncode
            if exit_code != 0:
                msg = f"Shell exited with an error ({exit_code})"
                self.push_screen(StaticDialog.warning("Warning", msg))
        else:
            self.push_screen(StaticDialog.error("Error", "No shell found!"))

    def _on_go_to(self, location: Union[str, dict, None]):
        if location is None:
            return

        if isinstance(location, str):
            try:
                fs, path = url_to_fs(location)
                is_dir = fs.isdir(path)
                err_msg = f"{location} is not a directory" if not is_dir else None
            except Exception as err:
                is_dir = False
                err_msg = str(err)

            if is_dir:
                self.active_filelist.fs = fs  # type: ignore
                self.active_filelist.path = path  # type: ignore
            else:
                self.push_screen(
                    StaticDialog.info(f"Cannot navigate to {location}", err_msg)
                )

        if isinstance(location, dict):
            protocol = location["protocol"]
            path = location.get("path")
            conf = {
                k: v
                for k, v in location.items()
                if k not in ("display_name", "protocol", "path")
            }
            new_fs = fsspec.filesystem(protocol, **conf)
            self.active_filelist.fs = new_fs  # type: ignore
            self.active_filelist.path = path or "/"  # type: ignore

    @work
    async def action_archive(self):
        if not is_local_fs(self.active_filelist.fs):
            self.push_screen(
                StaticDialog.info(
                    "Cannot archive",
                    "Archival is only supported in the local file system",
                )
            )
            return

        fs = self.active_filelist.fs
        sources = self.active_filelist.selected_paths()
        if len(sources) == 0:
            return

        msg = Text()
        msg.append(
            "Suported archive types: .zip, .tar.gz, .tar.bz2, .tar.xz, .7z, and more",
            style="dim",
        )
        msg.append("\n\n")
        msg.append(
            f"Archive {posixpath.basename(sources[0])} to"
            if len(sources) == 1
            else f"Archive {len(sources)} selected entries to"
        )
        output_suggestion = (
            posixpath.join(
                self.active_filelist.path,
                posixpath.splitext(posixpath.basename(sources[0]))[0],
            )
            if len(sources) == 1
            else posixpath.join(self.active_filelist.path)
        ) + ".zip"
        output_path = await self.push_screen_wait(
            InputDialog(
                msg,
                value=output_suggestion,
                btn_ok="Archive",
                select_on_focus=False,
            )
        )
        if output_path is None:
            return

        if fs.isfile(output_path):
            msg = f"{output_path} already exists. Overwrite?"
            if not await self.push_screen_wait(
                StaticDialog(
                    title="Overwrite?",
                    message=msg,
                    btn_ok="Overwrite",
                    style=Style.WARNING,
                )
            ):
                return

        async with error_handler_async(self):
            write_archive(
                self.active_filelist.selected_paths(),
                self.active_filelist.path,
                output_path,
            )
            self.active_filelist.reset_selection()
            self.active_filelist.update_listing()
            self.active_filelist.scroll_to_entry(posixpath.basename(output_path))

    @work
    async def action_go_to_bookmark(self):
        location = await self.app.push_screen_wait(GoToBookmarkDialog())
        async with error_handler_async(self):
            self._on_go_to(location)

    @work
    async def action_go_to_path(self):
        location = await self.push_screen_wait(
            InputDialog("Jump to...", value=self.active_filelist.path, btn_ok="Go")
        )
        async with error_handler_async(self):
            self._on_go_to(location)

    @work
    async def action_connect(self):

        @with_error_handler(self)
        def _on_conect(result: tuple[str, str, Optional[dict[str, Any]]]):
            if result is None:
                return

            protocol, path, fs_args = result
            remote_fs = fsspec.filesystem(protocol, **fs_args)
            self.active_filelist.fs = remote_fs  # type: ignore
            self.active_filelist.path = path  # type: ignore

        self.push_screen(ConnectToRemoteDialog(), _on_conect)

    def action_quit(self):
        def on_confirm(result: bool):
            if result:
                self.exit()

        self.push_screen(StaticDialog("Quit?"), on_confirm)

    @work
    async def action_about(self):
        def on_dismiss(result):
            set_user_has_accepted_license()

        title = f"F2 Commander {version('f2-commander')}"
        msg = (
            'This application is provided "as is", without warranty of any kind.\n'
            "This application is licensed under the Mozilla Public License, v. 2.0.\n"
            "You can find a copy of the license at https://mozilla.org/MPL/2.0/"
        )
        self.push_screen(StaticDialog.info(title, msg), on_dismiss)

    def action_help(self):
        self.panel_right.panel_type = "help"

    def check_action(self, action, parameters):
        if self.active_filelist and is_archive_fs(self.active_filelist.fs):
            if action in ("move", "delete", "mkfile", "mkdir", "edit"):
                return None  # visible, but disabled
            else:
                return True
        else:
            return True
