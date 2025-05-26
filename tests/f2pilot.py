# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""
F2 Commander-aware pilot features.

As much as possible, functions in this module assume nothing about the underlying
implementation (do not interface with widgets' API), and rather simulate user behavior.
E.g., navigating to a file would rather use j/k navigation, than setting reactive
attributes on a file list. Widget content is accessed directly with API for simplicity.

Crucially, it abstracts the specifics of the implementation from the test logic. E.g.,
changing where exactly the directly "title" is displayed in the UI will only need
a change in this module, not the test code.
"""

from pathlib import Path

from f2.app import F2Commander
from f2.fs.node import Node

THEME = "textual-dark"
RED = "#ba3c5b"
YELLOW = "#ffa62b"


class F2AppPilot:
    def __init__(self, app):
        self._app = app
        self._apply_default_config()

    def _apply_default_config(self):
        """Apply defualt app configuration"""
        self.order_case_sensitive = False
        self.dirs_first = False
        self.show_hidden = False

    def go_to_path(self, path: Path):
        self._app._on_go_to(path.as_posix())

    def panel_title(self):
        return self._app.active_filelist.border_title

    @property
    def cursor_node(self) -> Node:
        return self._app.active_filelist.cursor_node

    def col(self, col_key: str):
        """Get a specified table column in a currently active panel"""
        return [str(x).strip() for x in self.active_filelist.table.get_column(col_key)]

    def cell(self, row_key: str, col_key: str):
        """Get a specified table cell in a currently active panel"""
        return self._app.active_filelist.table.get_cell(row_key, col_key)
