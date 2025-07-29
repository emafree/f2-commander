# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test Help panel"""

from ..f2pilot import run_test


async def test_help_opens_from_shortcut(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("?")
        assert app.right.parent.border_title == "Help"
        await pilot.press("tab", "q")
        assert app.right.parent.border_title != "Help"
