# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import posixpath
import shutil
from typing import Union

from fsspec import filesystem
from PIL import Image as PillowImage
from rich.syntax import Syntax
from textual import work
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static
from textual_image.widget import Image as TextualImage

from f2.fs.node import Node
from f2.fs.util import breadth_first_walk, is_image_file, is_text_file, shorten


class Preview(Static):
    DEFAULT_CSS = """
    .image-size-auto {
        width: auto;
        height: auto;
        align: center middle;
    }
    """

    node = reactive(Node.cwd())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._preview_content = None
        self._fs = filesystem("file")

    def compose(self) -> ComposeResult:
        yield TextualImage(None, id="image-preview", classes="image-size-auto")
        yield Static("", id="text-preview")

    def on_mount(self):
        self.node = self.app.active_filelist.cursor_node

    # FIXME: push_message (in)directy to the "other" panel only?
    def on_other_panel_selected(self, node: Node):
        self.node = node

    @work(exclusive=True)
    async def watch_node(self, old: Node, new: Node):
        parent: Widget = self.parent  # type: ignore
        image_preview = self.query_one("#image-preview")
        text_preview = self.query_one("#text-preview")

        # set title:
        parent.border_title = shorten(
            new.path, width_target=self.size.width, method="slice"
        )
        parent.border_subtitle = None

        # set a placeholder:
        image_preview.loading = True
        text_preview.loading = True

        # update content:
        self._preview_content = self._format(self.node)
        text, image = (
            ("", self._preview_content)
            if isinstance(self._preview_content, PillowImage.Image)
            else (self._preview_content, None)
        )
        image_preview.image = image
        text_preview.update(text)
        image_preview.loading = False
        text_preview.loading = False

    def _format(self, node: Node) -> Union[str, Syntax, PillowImage]:
        if node is None:
            return ""
        elif node.is_dir:
            return self._dir_tree(node)
        elif node.is_file and is_text_file(node.path):
            try:
                return Syntax(
                    code=self._head(node), lexer=Syntax.guess_lexer(node.path)
                )
            except UnicodeDecodeError:
                return "Cannot preview: text file cannot be read"
        elif node.is_file and is_image_file(node.path):
            try:
                return PillowImage.open(self.node.path)
            except OSError:
                return "Cannot preview: image file cannot be read"
        else:
            # TODO: leave a user a possibility to force the preview?
            return "Cannot preview: not a text or an image file"

    @property
    def _height(self):
        """Viewport is not higher than this number of lines"""
        # FIXME: use Textual API instead?
        return shutil.get_terminal_size(fallback=(200, 80))[1]

    def _head(self, node: Node) -> str:
        lines = []
        with node.fs.open(node.path, "r") as f:
            try:
                for _ in range(self._height):
                    lines.append(next(f))
            except StopIteration:
                pass
        return "".join(lines)

    def _dir_tree(self, node: Node) -> str:
        """To give a best possible overview of a directory, show it traversed
        breadth-first. Some directories may not be walked in a latter case, but
        top-level will be shown first, then the second level exapnded, and so on
        recursively as long as the output fits the screen."""

        # collect paths to show, breadth-first, but at most a screenful:
        collected_paths = []  # type: ignore
        for i, p in enumerate(
            breadth_first_walk(node.fs, node.path, self.app.config.display.show_hidden)
        ):
            if i > self._height:
                break
            if posixpath.dirname(p) in collected_paths:
                siblings = [
                    e
                    for e in collected_paths
                    if posixpath.dirname(e) == posixpath.dirname(p)
                ]
                insert_at = (
                    collected_paths.index(posixpath.dirname(p)) + len(siblings) + 1
                )
                collected_paths.insert(insert_at, p)
            else:
                collected_paths.append(p)

        # format paths:
        lines = [node.path]
        for p in collected_paths:
            name = posixpath.relpath(p, node.path)
            if self._fs.isdir(p):
                name += "/"
            lines.append(f"┣ {name}")
        return "\n".join(lines)
