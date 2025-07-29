# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test the remote connection dialog"""

from .f2pilot import run_test
from f2.widgets.connect import ConnectToRemoteDialog


# TODO: remote connection tests


async def test_remotes_dialog(app):
    async with run_test(app=app) as (pilot, f2pilot):
        await pilot.press("ctrl+t")
        assert isinstance(app.screen, ConnectToRemoteDialog)
