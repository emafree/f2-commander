# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test file selection feature"""


from .f2pilot import YELLOW, F2AppPilot


async def test_file_selection(app, sample_fs):
    async with app.run_test(size=(200, 80)) as pilot:

        f2pilot = F2AppPilot(app)
        f2pilot.go_to_path(sample_fs)

        await pilot.press("j", "j")
        assert f2pilot.cursor_node.name == "contacts.csv"
        assert f2pilot.cell("contacts.csv", "name").markup.strip() == "contacts.csv"

        await pilot.press("J")
        assert f2pilot.cursor_node.name == "credentials.txt"
        assert (
            f2pilot.cell("contacts.csv", "name").markup.strip()
            == f"[{YELLOW} italic]contacts.csv[/{YELLOW} italic]"
        )

        await pilot.press("k", "shift+down")
        assert f2pilot.cursor_node.name == "credentials.txt"
        assert f2pilot.cell("contacts.csv", "name").markup.strip() == "contacts.csv"
        assert (
            f2pilot.cell("credentials.txt", "name").markup.strip() == "credentials.txt"
        )

        await pilot.press("+")
        # FIXME: rather iterate all rows (and all columns?)
        assert (
            f2pilot.cell("contacts.csv", "name").markup.strip()
            == f"[{YELLOW} italic]contacts.csv[/{YELLOW} italic]"
        )
        assert (
            f2pilot.cell("credentials.txt", "name").markup.strip()
            == f"[{YELLOW} italic]credentials.txt[/{YELLOW} italic]"
        )

        await pilot.press("-")
        assert f2pilot.cell("contacts.csv", "name").markup.strip() == "contacts.csv"
        assert (
            f2pilot.cell("credentials.txt", "name").markup.strip() == "credentials.txt"
        )

        await pilot.press("K", "K")
        assert f2pilot.cursor_node.name == "backup.zip"
        assert (
            f2pilot.cell("contacts.csv", "name").markup.strip()
            == f"[{YELLOW} italic]contacts.csv[/{YELLOW} italic]"
        )
        assert (
            f2pilot.cell("credentials.txt", "name").markup.strip()
            == f"[{YELLOW} italic]credentials.txt[/{YELLOW} italic]"
        )

        # selection adds to other styles:
        await pilot.press("K")
        assert f2pilot.cursor_node.name == ".."
        assert (
            f2pilot.cell("backup.zip", "name").markup.strip()
            == f"[{YELLOW} italic]backup.zip[/{YELLOW} italic]"
        )
