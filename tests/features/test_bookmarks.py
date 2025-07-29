# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test the bookmarks dialog"""

from ..f2pilot import run_test
from f2.widgets.bookmarks import GoToBookmarkDialog

# Scenarios:
#
# - The dialog displays all bookmarks listed in the configuration file.
# - Selecting (`up`/`down`+`Enter`, or a mouse click) an item opens the selected
#   directory in the active panel.
# - Non-existing directories are disabled and cannot be selected with arrow keys
#   or a mouse click.
# - First 9 entries (except the very first one) are enumerated, according keyboard
#   keys select them.
# - Select non-existing (disabled) directory by its hot key. An info message is
#   displayed telling the use that the directory does not exist.

# FIXME: preferrably, may rework the config system first, and have a
#        clean test configuration, before implementing this test


async def test_bookmarks_dialog(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("b")
        assert isinstance(app.screen, GoToBookmarkDialog)
