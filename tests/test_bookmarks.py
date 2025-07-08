# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test the bookmarks dialog"""

import os

from .f2pilot import run_test
from f2.widgets.bookmarks import GoToBookmarkDialog


async def test_bookmarks_dialog(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("b")
        assert isinstance(app.screen, GoToBookmarkDialog)


# FIXME: preferrably, may rework the config system first, and have a
#        clean test configuration, before implementing this test
