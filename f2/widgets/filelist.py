# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import functools
import posixpath
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from fsspec import AbstractFileSystem, filesystem
from humanize import naturalsize
from rich.text import Text
from textual import events, on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.fuzzy import FuzzySearch
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import DataTable, Input, Static
from textual.widgets.data_table import RowDoesNotExist

from f2.fs import DirEntry, DirList, is_local_fs, list_dir

from ..commands import Command
from ..config import config_root
from ..shell import native_open
from .dialogs import InputDialog


class TextAndValue(Text):
    """Like `rich.text.Text`, but also holds a given `value`"""

    def __init__(self, value, text):
        self.value = value
        self.text = text

    def __getattr__(self, attr):
        return getattr(self.text, attr)


@dataclass
class SortOptions:
    key: str
    reverse: bool = False  # ascending by default, descending if True


class FileList(Static):
    BINDINGS_AND_COMMANDS = [
        Command(
            "order('name', False)",
            "Order by name, asc",
            "Order entries by name, from A to Z",
            "n",
        ),
        Command(
            "order('name', True)",
            "Order by name, desc",
            "Order entries by name, from Z to A",
            "N",
        ),
        Command(
            "order('size', False)",
            "Order by size, asc",
            "Order entries by size, smallest first",
            "s",
        ),
        Command(
            "order('size', True)",
            "Order by size, desc",
            "Order entries by size, largest first",
            "S",
        ),
        Command(
            "order('mtime', False)",
            "Order by mtime, asc",
            "Order entries by last modification time, oldest first",
            "t",
        ),
        Command(
            "order('mtime', True)",
            "Order by mtime, desc",
            "Order entries by last modification time, newest first",
            "T",
        ),
        Command(
            "find",
            "Find / filter with glob",
            "Filter files to show only those matching a glob",
            "f",
        ),
        Command(
            "search",
            "Incremental search",
            "Incremental search in the file list, with fuzzy matching",
            "/",
        ),
        Command(
            "open_in_os_file_manager",
            "Open in OS file manager",
            "Open current location in the default OS file manager",
            "o",
        ),
        Command(
            "calc_dir_size",
            "Calculate directory size",
            "Calculate the size of the directory tree",
            "ctrl+@",  # this is `ctrl+space`
        ),
        Command(
            "navigate_to_config",
            "Show the configuration directory",
            "Open the user's configuration directory in the file list",
            None,
        ),
    ]
    BINDINGS = [  # type: ignore
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
    ] + [
        Binding(cmd.binding_key, cmd.action, cmd.description, show=False)
        for cmd in BINDINGS_AND_COMMANDS
        if cmd.binding_key is not None
    ]

    COLUMN_PADDING = 2  # a column uses this many chars more to render
    SCROLLBAR_SIZE = 2
    TIME_FORMAT = "%b %d %H:%M"

    class Selected(Message):
        def __init__(self, fs: AbstractFileSystem, path: str, file_list: "FileList"):
            self.fs = fs
            self.path = path
            self.file_list = file_list
            super().__init__()

        @property
        def contol(self) -> "FileList":
            return self.file_list

    class Open(Message):
        def __init__(self, fs: AbstractFileSystem, path: str, file_list: "FileList"):
            self.fs = fs
            self.path = path
            self.file_list = file_list
            super().__init__()

        @property
        def contol(self) -> "FileList":
            return self.file_list

    path = reactive(Path.cwd().as_posix())

    sort_options = reactive(SortOptions("name"), init=False)
    show_hidden = reactive(False, init=False)
    dirs_first = reactive(False, init=False)
    order_case_sensitive = reactive(False, init=False)
    # FIXME: cursor_path only makes sense with the fs instance; users just "need" to
    #        know this fact; ideally need an anstraction for fs+path, or generate
    #        events for changes in cursor_path, or just expose a get_cursor_path()
    cursor_path = reactive(Path.cwd().as_posix())
    active = reactive(False)
    glob = reactive(None, init=False)
    search_mode = reactive(None)
    # FIXME: same as for cursor_path above
    selection: set[str] = set()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fs = filesystem("file")
        self.parent_fs = None
        self.parent_path = None

    def compose(self) -> ComposeResult:
        self.table: DataTable = DataTable(cursor_type="row")
        self.search_input: Input = Input(
            classes="search hidden",
            placeholder="Quick search (Esc or Enter to exit)",
        )
        with Vertical():
            yield self.table
            yield self.search_input

    def on_mount(self) -> None:
        self._add_columns()

    def _add_columns(self):
        self.table.add_column("Name", key="name")
        self.table.add_column("Size", key="size")
        self.table.add_column("Modified", key="mtime")

    @work
    async def on_resize(self):
        self.table.clear(columns=True)
        self._add_columns()
        self.update_listing()
        self.watch_sort_options(None, self.sort_options)

    def selected_paths(self) -> list[str]:
        if len(self.selection) > 0:
            return list([posixpath.join(self.path, name) for name in self.selection])
        elif posixpath.basename(self.cursor_path) != "..":
            return [self.cursor_path]
        else:
            return []  # FIXME: should be None

    def reset_selection(self):
        self.selection = set()

    def add_selection(self, name):
        if name == "..":
            return
        self.selection.add(name)

    def remove_selection(self, name):
        self.selection.remove(name)

    def toggle_selection(self, name):
        if name in self.selection:
            self.remove_selection(name)
        else:
            self.add_selection(name)

    def scroll_to_entry(self, name: str):
        try:
            idx = self.table.get_row_index(name)
            self.table.cursor_coordinate = (idx, 0)  # type: ignore
        except RowDoesNotExist:
            pass

    #
    # FORMATTING:
    #

    def _row_style(self, e: DirEntry) -> str:
        # FIXME: use CSS instead
        theme = self.app.available_themes[self.app.theme]
        style = ""

        if e.is_dir:
            style = "bold"
        elif e.is_executable:
            style = theme.error or "red"
        elif e.is_hidden:
            style = "dim"
        elif e.is_link:
            style = "underline"
        elif e.is_archive:
            style = theme.accent or "yellow"

        if e.name in self.selection:
            style += f" {theme.accent or 'yellow'} italic"

        return style

    def _fmt_name(self, e: DirEntry, style: str) -> Text:
        text = Text()

        width_target = self._width_name()
        if not width_target:
            # container width is not known yet => assume smallest size, let the
            # container render once, then render the text on the next round
            return text

        # adjust width: cut long names
        if len(e.name) > width_target:
            suffix = "..."
            cut_idx = width_target - len(suffix)
            text.append(e.name[:cut_idx] + suffix, style=style)

        # FIXME: remove if textual supports full-width data tables
        # adjust width: pad short names to span the column
        else:
            pad_size = width_target - len(e.name)
            text.append(e.name, style=style)
            text.append(" " * pad_size)  # FIXME: the only reason to pass style as arg

        return text

    def _width_name(self):
        if self.size.width > 0:
            return (
                self.size.width
                - self._width_mtime()
                - self._width_size()
                - self.COLUMN_PADDING
                - self.SCROLLBAR_SIZE
            )
        else:
            return None

    def _fmt_size(self, e: DirEntry, style: str) -> Text:
        if e.name == "..":
            return Text("-- UP⇧ --", style=style, justify="center")
        elif e.is_dir:
            return Text("-- DIR --", style=style, justify="center")
        elif e.is_link:
            return Text("-- LNK --", style=style, justify="center")
        else:
            return Text(naturalsize(e.size), style=style, justify="right")

    @functools.cache
    def _width_size(self):
        return len(naturalsize(123)) + self.COLUMN_PADDING

    def _fmt_mtime(self, e: DirEntry, style: str) -> Text:
        return Text(
            time.strftime(self.TIME_FORMAT, time.localtime(e.mtime)),
            style=style,
        )

    @functools.cache
    def _width_mtime(self):
        return len(time.strftime(self.TIME_FORMAT)) + self.COLUMN_PADDING

    #
    # END OF FORMATTING
    #

    #
    # ORDERING:
    #

    def sort_key(self, name_and_value):
        sort_key_fn = {
            "name": self.sort_key_by_name,
            "size": self.sort_key_by_size,
            "mtime": self.sort_key_by_mtime,
        }[self.sort_options.key]
        entry: DirEntry = name_and_value.value
        return sort_key_fn(entry)

    def sort_key_by_name(self, e: DirEntry) -> str:
        # stick ".." at the top of the list, regardless of the order (asc/desc)
        if e.name == "..":
            return "\u0000" if not self.sort_options.reverse else "\uFFFF"

        # dirs first, if asked for
        prefix = ""
        if self.dirs_first and e.is_dir:
            prefix = "\u0001" if not self.sort_options.reverse else "\uFFFE"

        # handle case sensetivity
        name = e.name
        if not self.order_case_sensitive:
            name = name.lower() + name  # keeping original name for stable ordering

        return prefix + name

    def sort_key_by_size(self, e: DirEntry) -> Tuple[int, Optional[str]]:
        max_file_size = 2**64  # maximum file size in zfs, and probably on the planet
        # stick ".." at the top of the list, regardless of the order (asc/desc)
        if e.name == "..":
            size_key = -1 if not self.sort_options.reverse else max_file_size + 1
            return (size_key, None)

        size_key = e.size
        # when ordering by size, dirs are always first
        if e.is_dir or e.is_link:
            size_key = 0 if not self.sort_options.reverse else max_file_size

        return (size_key, self.sort_key_by_name(e))  # add name for stable ordering

    def sort_key_by_mtime(self, e: DirEntry) -> Tuple[float, Optional[str]]:
        y3k = 32_503_680_000  # this program has Y3K issues
        # stick ".." at the top of the list, regardless of the order (asc/desc)
        if e.name == "..":
            key = -1 if not self.sort_options.reverse else 2 * y3k
            return (key, None)

        mtime_key = e.mtime
        if self.dirs_first:
            if not self.sort_options.reverse and not e.is_dir:
                mtime_key = e.mtime + y3k
            elif self.sort_options.reverse and e.is_dir:
                mtime_key = e.mtime + y3k

        return (mtime_key, self.sort_key_by_name(e))  # add name for stable ordering

    #
    # END OF ORDERING
    #

    def _update_table(self, ls: DirList):
        self.table.clear()
        for child in ls.entries:
            style = self._row_style(child)
            self.table.add_row(
                # name column also holds original values:
                TextAndValue(child, self._fmt_name(child, style)),
                self._fmt_size(child, style),
                self._fmt_mtime(child, style),
                key=child.name,
            )
        self.table.sort("name", key=self.sort_key, reverse=self.sort_options.reverse)

    def update_listing(self):
        old_cursor_path = self.cursor_path
        ls = list_dir(
            self.fs,
            self.path,
            include_hidden=self.show_hidden,
            glob_expression=self.glob,
        )

        if self.path == "":
            entry = DirEntry.from_info(
                self.parent_fs, self.parent_fs.info(self.parent_path)
            )
            entry.name = ".."
            ls.entries.insert(0, entry)

        self._update_table(ls)
        # if stil in same dir as before, restore the cursor position
        if self.path == posixpath.dirname(old_cursor_path):
            self.scroll_to_entry(posixpath.basename(old_cursor_path))
        # update list border with some information about the directory:
        total_size_str = naturalsize(ls.total_size)
        if is_local_fs(self.fs):
            self.parent.border_title = self.path
        elif self.parent_fs is not None:
            self.parent.border_title = posixpath.join(self.parent_path, self.path)
        else:
            self.parent.border_title = self.fs.unstrip_protocol(self.path)
        subtitle = f"{total_size_str} in {ls.file_count} files | {ls.dir_count} dirs"
        if self.glob is not None:
            subtitle = f"[red]{self.glob}[/red] | {subtitle}"
        self.parent.border_subtitle = subtitle

    def watch_path(self, old_path: str, new_path: str):
        self.reset_selection()
        self.glob = None
        self.update_listing()
        # if navigated "up", select source dir in the new list:
        if new_path == posixpath.dirname(old_path):
            self.scroll_to_entry(posixpath.basename(old_path))

    def watch_show_hidden(self, old: bool, new: bool):
        if not new:  # if some files will be not shown anymore, better be safe:
            self.reset_selection()
        self.update_listing()

    def watch_dirs_first(self, old: bool, new: bool):
        self.update_listing()

    def watch_order_case_sensitive(self, old: bool, new: bool):
        self.update_listing()

    def watch_sort_options(self, old: SortOptions, new: SortOptions):
        self.update_listing()
        # remove sort label from the previously sorted column:
        if old is not None:
            prev_sort_col = self.table.columns[old.key]  # type: ignore
            prev_sort_col.label = prev_sort_col.label[:-2]
        # add the new sort label:
        new_sort_col = self.table.columns[new.key]  # type: ignore
        direction = "⬆" if new.reverse else "⬇"
        new_sort_col.label = f"{new_sort_col.label} {direction}"  # type: ignore

    def watch_glob(self, old: Optional[str], new: Optional[str]):
        self.reset_selection()
        self.update_listing()

    # FIXME: refactor (simplify) ordering logic; see if DataTable provides better API
    def action_order(self, key: str, reverse: bool):
        # if the user chooses the same order again, reverse it:
        # (e.g., pressing `n` twice will reverse the order the second time)
        new_sort_options = SortOptions(key, reverse)
        if self.sort_options == new_sort_options:
            new_sort_options = SortOptions(key, not reverse)
        self.sort_options = new_sort_options

    @work
    async def action_find(self):
        def on_find(value):
            if value is None:
                return

            if value.strip() == "" or value.strip() == "*":
                self.glob = None
            else:
                self.glob = value

        self.app.push_screen(
            InputDialog(
                title="Find files, enter glob expression",
                value=self.glob or "*",
                btn_ok="Find",
            ),
            on_find,
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        entry_name: str = event.row_key.value  # type: ignore
        if entry_name == "..":
            self.on_navigate_up()
        else:
            selected_path = posixpath.join(self.path, entry_name)
            if self.fs.isdir(selected_path):
                self.path = selected_path

    def on_navigate_up(self):
        if self.path != "":
            # regular upwards navigation
            self.path = posixpath.dirname(self.path)
        else:
            # navgiate to the parent file system, if at root of a child one
            self.fs = self.parent_fs
            self.set_reactive(FileList.path, self.parent_path)
            self.path = posixpath.dirname(self.parent_path)
            self.parent_fs = None
            self.parent_path = None

    def action_search(self):
        self.search_mode = True
        self.refresh_bindings()
        self.search_input.remove_class("hidden")
        self.search_input.focus()

    def dismiss_search(self):
        with self.search_input.prevent(Input.Changed):
            self.search_input.value = ""
        self.table.focus()
        self.search_input.add_class("hidden")
        self.search_mode = False
        self.refresh_bindings()

    @on(Input.Submitted, ".search")
    def on_search_input_submitted(self, event: Input.Submitted):
        self.dismiss_search()

    @on(Input.Changed, ".search")
    def on_search_input_changed(self, event: Input.Changed):
        if not event.value:
            return

        matcher = FuzzySearch()
        query = event.value
        names: list[str] = [key.value for key in self.table.rows]  # type: ignore
        scores = [matcher.match(query, name)[0] for name in names]
        max_score = max(scores)
        if max_score > 0:
            idx = scores.index(max_score)
            self.scroll_to_entry(names[idx])

    def action_open(self):
        # "open" is handled separately from "table.row_selected" to distinguish
        # between "enter" and mouse click (avoid navigation and running
        # apps on mouse clickd)
        if self.fs.isdir(posixpath.normpath(self.cursor_path)):
            pass  # already handled by on_data_table_row_selected
        elif self.fs.isfile(self.cursor_path):
            self.post_message(
                self.Open(fs=self.fs, path=self.cursor_path, file_list=self)
            )

    def action_open_in_os_file_manager(self):
        if not is_local_fs(self.fs):
            return

        open_cmd = native_open()
        if open_cmd is not None:
            with self.app.suspend():
                subprocess.run(open_cmd + [self.path])
            self.app.refresh()

    def action_navigate_to_config(self):
        self.fs = filesystem("file")
        self.path = config_root().as_posix()

    @work
    async def action_calc_dir_size(self):
        path = self.cursor_path  # hold on to the requsted path
        self.action_cursor_down()  # and move the cursor
        if not self.fs.isdir(path):
            return

        cursor_name = posixpath.basename(self.cursor_path)

        entry = DirEntry.from_info(self.fs, self.fs.info(path))
        style = self._row_style(entry)

        # show a placeholder and move the cursor at once:
        placeholder = Text("...", style=style, justify="right")
        self.table.update_cell(cursor_name, "size", placeholder)

        # then, calculate and show the size (can be slow):
        size = self.fs.du(self.cursor_path, total=True, withdirs=True)
        size_text = Text(naturalsize(size), style=style, justify="right")
        self.table.update_cell(cursor_name, "size", size_text)

    def action_cursor_down(self):
        new_coord = (self.table.cursor_coordinate[0] + 1, 0)
        self.table.cursor_coordinate = new_coord  # type: ignore

    def action_cursor_up(self):
        new_coord = (self.table.cursor_coordinate[0] - 1, 0)
        self.table.cursor_coordinate = new_coord  # type: ignore

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        name: str = event.row_key.value  # type: ignore
        self.cursor_path = posixpath.join(self.path, name)
        self.post_message(
            self.Selected(fs=self.fs, path=self.cursor_path, file_list=self)
        )

    def on_descendant_focus(self, event):
        self.active = True
        self.add_class("focused")

    def on_descendant_blur(self, event):
        self.active = False
        self.remove_class("focused")
        if event.widget == self.search_input:
            self.dismiss_search()

    def on_key(self, event: events.Key) -> None:
        if self.search_mode:
            self.on_key_search_mode(event)
        else:
            self.on_key_normal_mode(event)

    def on_key_search_mode(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss_search()

    def on_key_normal_mode(self, event: events.Key) -> None:
        # FIXME: refactor to use actions?
        if event.key == "g":
            self.table.action_scroll_top()
        elif event.key == "G":
            self.table.action_scroll_bottom()
        elif event.key in ("ctrl+f", "ctrl+d"):
            self.table.action_page_down()
        elif event.key in ("ctrl+b", "ctrl+u"):
            self.table.action_page_up()
        elif event.key == "backspace":
            self.on_navigate_up()
        elif event.key == "R":
            self.update_listing()
        elif event.key == "enter":
            self.action_open()
        elif event.key in ("space", "J", "shift+down"):
            self.toggle_selection(posixpath.basename(self.cursor_path))
            self.update_listing()
            self.action_cursor_down()
        elif event.key in ("K", "shift+up"):
            self.toggle_selection(posixpath.basename(self.cursor_path))
            self.update_listing()
            self.action_cursor_up()
        elif event.key == "minus":
            self.reset_selection()
            self.update_listing()
        elif event.key == "plus":
            for key in self.table.rows:
                self.add_selection(key.value)
            self.update_listing()
        elif event.key == "asterisk":
            for key in self.table.rows:
                self.toggle_selection(key.value)
            self.update_listing()
