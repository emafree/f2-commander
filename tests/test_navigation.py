# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test basic navigation features"""


async def test_list_navigation(app, sample_fs):

    # CAUTION: screen height = 15 ! to force scroll

    async with app.run_test(size=(200, 15)) as pilot:
        app.order_case_sensitive = False
        app.dirs_first = False
        app.show_hidden = False
        app._on_go_to(sample_fs.as_posix())

        # default:
        assert app.active_filelist.cursor_node.name == ".."

        # already at top - does nothing:
        await pilot.press("k")
        assert app.active_filelist.cursor_node.name == ".."

        # down and up:
        await pilot.press("j")
        assert app.active_filelist.cursor_node.name == "backup.zip"
        await pilot.press("j")
        assert app.active_filelist.cursor_node.name == "contacts.csv"
        await pilot.press("k")
        assert app.active_filelist.cursor_node.name == "backup.zip"

        # bottom:
        await pilot.press("G")
        assert app.active_filelist.cursor_node.name == "Videos"
        # already at bottom - does nothing:
        await pilot.press("G")
        assert app.active_filelist.cursor_node.name == "Videos"

        # down at bottom does nothing:
        await pilot.press("j")
        assert app.active_filelist.cursor_node.name == "Videos"

        # top:
        await pilot.press("g")
        assert app.active_filelist.cursor_node.name == ".."
        # already at top - does nothing:
        await pilot.press("g")
        assert app.active_filelist.cursor_node.name == ".."

        # one screen down:
        await pilot.press("ctrl+f")
        assert app.active_filelist.cursor_node.name == "settings.json"
        # next screen down:
        await pilot.press("ctrl+f")
        assert app.active_filelist.cursor_node.name == "Videos"
        # already at bottom - does nothing:
        await pilot.press("ctrl+f")
        assert app.active_filelist.cursor_node.name == "Videos"

        # screen up:
        await pilot.press("ctrl+b")
        assert app.active_filelist.cursor_node.name == "Documents"
        # next screen up
        await pilot.press("ctrl+b")
        assert app.active_filelist.cursor_node.name == ".."
        # already at top - does nothing:
        await pilot.press("ctrl+b")
        assert app.active_filelist.cursor_node.name == ".."

        # one half-screen down:
        await pilot.press("ctrl+d")
        assert app.active_filelist.cursor_node.name == "settings.json"
        # next hald-screen down:
        await pilot.press("ctrl+d")
        assert app.active_filelist.cursor_node.name == "Videos"
        # already at bottom - does nothing:
        await pilot.press("ctrl+d")
        assert app.active_filelist.cursor_node.name == "Videos"

        # half-screen up:
        await pilot.press("ctrl+u")
        assert app.active_filelist.cursor_node.name == "Documents"
        # next half-screen up
        await pilot.press("ctrl+u")
        assert app.active_filelist.cursor_node.name == ".."
        # already at top - does nothing:
        await pilot.press("ctrl+u")
        assert app.active_filelist.cursor_node.name == ".."


async def test_dir_navigation(app, sample_fs):
    async with app.run_test(size=(200, 80)) as pilot:
        app._on_go_to(sample_fs.as_posix())

        # navigate to a dir:
        while app.active_filelist.cursor_node.name != "Documents":
            await pilot.press("j")
        await pilot.press("enter")

        assert app.active_filelist.parent.border_title.endswith("Documents")
        assert app.active_filelist.cursor_node.name == ".."
        names = [key.value for key in app.active_filelist.table.rows]
        assert "Work" in names
        assert "Personal" in names

        # navigate back:
        await pilot.press("backspace")
        assert app.active_filelist.parent.border_title.endswith(sample_fs.name)
        assert app.active_filelist.cursor_node.name == "Documents"

        # navigate back with .. :
        await pilot.press("enter")
        assert app.active_filelist.parent.border_title.endswith("Documents")
        assert app.active_filelist.cursor_node.name == ".."
        await pilot.press("enter")
        assert app.active_filelist.parent.border_title.endswith(sample_fs.name)
        assert app.active_filelist.cursor_node.name == "Documents"


async def test_empty_dir_navigation(app, sample_fs):
    async with app.run_test(size=(200, 80)) as pilot:
        app._on_go_to(sample_fs.as_posix())

        while app.active_filelist.cursor_node.name != "Templates":
            await pilot.press("j")
        await pilot.press("enter")
        names = list(app.active_filelist.table.rows)
        assert len(names) == 1
        assert names[0] == ".."

        # navigating in an empty list does nothing (no error):
        await pilot.press("j")
        await pilot.press("k")
        await pilot.press("g")
        await pilot.press("G")
        await pilot.press("ctrl+f")
        await pilot.press("ctrl+b")
        await pilot.press("ctrl+d")
        await pilot.press("ctrl+u")
        assert app.active_filelist.cursor_node.name == ".."


async def test_incremental_search(app, sample_fs):
    async with app.run_test(size=(200, 80)) as pilot:
        app._on_go_to(sample_fs.as_posix())

        # ending with escape:
        await pilot.press("/", "c", "r", "d", "escape")
        assert app.active_filelist.cursor_node.name == "credentials.txt"

        # ending with enter:
        await pilot.press("/", "n", "o", "t", "enter")
        assert app.active_filelist.cursor_node.name == "notes.txt"

        # doing nothing:
        await pilot.press("/", "escape")
        assert app.active_filelist.cursor_node.name == "notes.txt"


# FIXME: no easy to way to test highlight on hover?


async def test_mouse_dir_navigation(app, sample_fs):
    async with app.run_test(size=(200, 80)) as pilot:
        app.order_case_sensitive = False
        app.dirs_first = False
        app.show_hidden = False
        app._on_go_to(sample_fs.as_posix())

        # 5th row is "Documents":
        assert app.active_filelist.parent.border_title.endswith(sample_fs.name)
        await pilot.click(widget=app.active_filelist.table, offset=(1, 5))
        assert app.active_filelist.parent.border_title.endswith("Documents")

        # first row is "..":
        await pilot.click(widget=app.active_filelist.table, offset=(1, 1))
        assert app.active_filelist.parent.border_title.endswith(sample_fs.name)

        # click on file, does nothong:
        await pilot.click(widget=app.active_filelist.table, offset=(1, 2))
        assert app.active_filelist.parent.border_title.endswith(sample_fs.name)
