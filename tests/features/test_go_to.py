# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test "go to" action"""

import os

from f2.widgets.dialogs import InputDialog, StaticDialog

from ..f2pilot import run_test


async def test_go_to_dialog(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+g")
        assert isinstance(app.screen, InputDialog)
        assert app.screen.value == sample_fs.as_posix()


async def test_go_to_path(sample_fs):
    async with run_test(cwd=sample_fs) as (pilot, f2pilot):
        assert f2pilot.panel_title.endswith(sample_fs.name)
        await pilot.press("ctrl+g", "right", "/", *"Documents")
        await pilot.press("enter")
        assert f2pilot.panel_title.endswith("Documents")


async def test_go_to_invalid_path(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        assert f2pilot.panel_title.endswith(sample_fs.name)
        await pilot.press("ctrl+g", "right", "/", *"ThisDoesNotExist")
        await pilot.press("enter")
        assert f2pilot.panel_title.endswith(sample_fs.name)
        assert isinstance(app.screen, StaticDialog)
        assert "Errno 2" in app.screen.message
        assert "ThisDoesNotExist" in app.screen.message


async def test_go_to_empty(sample_fs):
    async with run_test(cwd=sample_fs) as (pilot, f2pilot):
        assert f2pilot.panel_title.endswith(sample_fs.name)
        await pilot.press("ctrl+g", "backspace", "enter")
        assert f2pilot.panel_title.endswith(os.path.basename(os.getcwd()))


async def test_go_to_same(sample_fs):
    async with run_test(cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+g", "enter")
        assert f2pilot.panel_title.endswith(sample_fs.name)


async def test_go_to_cancel(sample_fs):
    async with run_test(cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+g", "escape")
        assert f2pilot.panel_title.endswith(sample_fs.name)


# TODO: entering a simple URL will also navigate to it, provided
#       that an according implementation is available
