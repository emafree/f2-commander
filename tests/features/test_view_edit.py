# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test view and edit actions"""

from ..f2pilot import run_test


async def test_view(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await f2pilot.select("todo.md")
        # await pilot.press("v")
        # FIXME: suspend() cannot be used in tests;
        #        inject another (mock?) impl for action_view?
