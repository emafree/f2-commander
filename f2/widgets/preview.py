# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import posixpath
import shutil

from fsspec import filesystem
from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from f2.config import config
from f2.fs.node import Node
from f2.fs.util import breadth_first_walk, is_text_file, shorten


class Preview(Static):
    node = reactive(Node.cwd(), recompose=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content = None
        self._fs = filesystem("file")

    def compose(self) -> ComposeResult:
        self._content = self._format(self.node)
        yield Static(self._content)

    def on_mount(self):
        self.node = self.app.active_filelist.cursor_node

    # FIXME: push_message (in)directy to the "other" panel only?
    def on_other_panel_selected(self, node: Node):
        self.node = node

    def watch_node(self, old: Node, new: Node):
        parent: Widget = self.parent  # type: ignore
        parent.border_title = shorten(
            new.path, width_target=self.size.width, method="slice"
        )
        parent.border_subtitle = None

    def _format(self, node: Node):
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
                # file appears to be a binary file after all
                return "Cannot preview, probably not a text file"
        else:
            # TODO: leavey a user a possibility to force the preview?
            return "Cannot preview, probably not a text file"

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
            breadth_first_walk(node.fs, node.path, config.show_hidden)
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
