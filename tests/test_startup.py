# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

"""A smoke test ensuring the application starts up and shows some meaningful content"""

import os

from f2.app import F2Commander


async def test_startup():
    app = F2Commander()

    async with app.run_test() as pilot:  # noqa: F841

        filelist = app.active_filelist
        assert filelist.path == os.getcwd()

        names: list[str] = [key.value for key in filelist.table.rows]  # type: ignore
        assert ".." in names
        assert len(names) > 1
