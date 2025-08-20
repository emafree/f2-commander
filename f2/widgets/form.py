# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko


#
# REUSABLE FORM CONTROLS
#

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Input, Static, Switch


class SwitchWithLabel(Static):
    def __init__(self, id: str, title: str, value: bool):
        super().__init__()
        self.id = id
        self.title = title
        self.value = value

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Switch(self.value, id=self.id),
            Static(self.title, classes="inline-label"),
            classes="container",
        )


class InputWithLabel(Static):
    def __init__(
        self, id: str, title: str, placeholder: Optional[str], value: Optional[str]
    ):
        super().__init__()
        self.id = id
        self.title = title
        self.placeholder = placeholder
        self.value = value

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static(self.title, classes="inline-label"),
            Input(
                placeholder=self.placeholder,
                value=self.value,
                id=self.id,
                classes="w-auto",
            ),
            classes="container",
        )
