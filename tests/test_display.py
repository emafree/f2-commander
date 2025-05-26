# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test basic display (file listing) features"""

from datetime import datetime, timedelta

THEME = "textual-dark"
RED = "#ba3c5b"
YELLOW = "#ffa62b"


def col(data_table, col_key):
    return [str(x).strip() for x in data_table.get_column(col_key)]


def cell(data_table, row_key, col_key):
    return str(data_table.get_cell(row_key, col_key))


async def test_simple_names(app, sample_fs):
    async with app.run_test(size=(200, 80)):
        app._on_go_to(sample_fs.as_posix())
        assert "Downloads" in col(app.active_filelist.table, "name")
        assert "todo.md" in col(app.active_filelist.table, "name")
        assert "settings.json" in col(app.active_filelist.table, "name")


async def test_hidden(app, sample_fs):
    async with app.run_test(size=(200, 80)):
        app._on_go_to(sample_fs.as_posix())
        app.show_hidden = False
        assert ".bashrc" not in col(app.active_filelist.table, "name")
        app.show_hidden = True
        assert ".bashrc" in col(app.active_filelist.table, "name")


async def test_size(app, sample_fs):
    async with app.run_test(size=(200, 80)):
        app._on_go_to(sample_fs.as_posix())
        assert cell(app.active_filelist.table, "todo.md", "size") == "5.0 kB"
        assert cell(app.active_filelist.table, "Downloads", "size") == "-- DIR --"


async def test_mtime(app, sample_fs):
    now = datetime.now().strftime("%b %d %H:%M")
    minute_before = (datetime.now() - timedelta(minutes=1)).strftime("%b %d %H:%M")
    async with app.run_test(size=(200, 80)):
        app._on_go_to(sample_fs.as_posix())
        actual_mtime = cell(app.active_filelist.table, "todo.md", "mtime")
        assert actual_mtime == now or actual_mtime == minute_before


async def test_summary(app, sample_fs):
    async with app.run_test(size=(200, 80)):
        app._on_go_to(sample_fs.as_posix())
        assert app.active_filelist.parent.border_title == sample_fs.as_posix()
        subtitle = app.active_filelist.parent.border_subtitle
        assert subtitle == "44.2 kB in 9 files | 7 dirs"


async def test_styles(app, sample_fs):
    async with app.run_test(size=(200, 80)):
        app.theme = THEME
        app.show_hidden = True
        app._on_go_to(sample_fs.as_posix())
        table = app.active_filelist.table
        assert table.get_cell("todo.md", "name").markup.strip() == "todo.md"
        assert (
            table.get_cell("Downloads", "name").markup.strip()
            == "[bold]Downloads[/bold]"
        )
        assert (
            table.get_cell("Photos", "name").markup.strip()
            == "[underline]Photos[/underline]"
        )
        assert (
            table.get_cell("update.sh", "name").markup.strip()
            == f"[{RED}]update.sh[/{RED}]"
        )
        assert table.get_cell(".bashrc", "name").markup.strip() == "[dim].bashrc[/dim]"
        assert (
            table.get_cell("backup.zip", "name").markup.strip()
            == f"[{YELLOW}]backup.zip[/{YELLOW}]"
        )


async def test_padding(app, sample_fs):
    async with app.run_test(size=(200, 80)) as pilot:
        app._on_go_to(sample_fs.as_posix())
        assert len(app.active_filelist.table.get_cell("todo.md", "name").markup) > 50
        await pilot.resize_terminal(80, 40)
        assert len(app.active_filelist.table.get_cell("todo.md", "name").markup) < 10
        await pilot.resize_terminal(200, 80)
        assert len(app.active_filelist.table.get_cell("todo.md", "name").markup) > 50


async def test_display_truncated(app, sample_fs):
    async with app.run_test(size=(80, 40)):
        app._on_go_to(sample_fs.as_posix())
        assert "todo.md" in col(app.active_filelist.table, "name")
        assert "settin..." in col(app.active_filelist.table, "name")
        # long border title should be truncated:
        title = app.active_filelist.parent.border_title
        assert "..." in title
        assert title.endswith(sample_fs.name)
