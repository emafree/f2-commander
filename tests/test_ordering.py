# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test ordering in a file listing"""

from .f2pilot import run_test


async def test_order_by_name():
    async with run_test() as (pilot, f2pilot):
        # default order is by name, ascending:
        assert f2pilot.cursor_node.name == ".."
        assert f2pilot.listing[1:] == sorted(f2pilot.listing[1:], key=str.lower)

        # order by name, descending:
        await pilot.press("N")
        assert f2pilot.cursor_node.name == ".."
        assert f2pilot.listing[0] == ".."
        assert f2pilot.listing[1:] == sorted(
            f2pilot.listing[1:], key=str.lower, reverse=True
        )

        # order by name, ascending:
        await pilot.press("n")
        assert f2pilot.listing[0] == ".."
        assert f2pilot.listing[1:] == sorted(f2pilot.listing[1:], key=str.lower)

        # toggle order descending:
        await pilot.press("n")
        assert f2pilot.listing[0] == ".."
        assert f2pilot.listing[1:] == sorted(
            f2pilot.listing[1:], key=str.lower, reverse=True
        )


async def test_order_by_size():
    async with run_test() as (pilot, f2pilot):
        await pilot.press("s")
        assert f2pilot.cursor_node.name == ".."
        assert f2pilot.listing[0] == ".."  # does not move
        assert f2pilot.listing[1] == "Documents"  # dirs always first
        assert f2pilot.listing[-1] == "backup.zip"  # largest file last

        await pilot.press("S")
        assert f2pilot.listing[0] == ".."  # .. does not move
        assert f2pilot.listing[1] == "Videos"  # dirs first, but reversed
        assert f2pilot.listing[-1] == "todo.md"  # smllest file last

        await pilot.press("S")  # hitting S again reverses the sort order
        assert f2pilot.listing[0] == ".."
        assert f2pilot.listing[1] == "Documents"
        assert f2pilot.listing[-1] == "backup.zip"


async def test_order_by_mtime():
    async with run_test() as (pilot, f2pilot):
        await pilot.press("t")
        assert f2pilot.cursor_node.name == ".."
        assert f2pilot.listing[0] == ".."  # does not move
        assert f2pilot.listing[1] == "todo.md"
        assert f2pilot.listing[-1] == "Templates"

        await pilot.press("T")
        assert f2pilot.listing[0] == ".."
        assert f2pilot.listing[1] == "Templates"
        assert f2pilot.listing[-1] == "todo.md"

        await pilot.press("T")  # hitting T again reverses the sort order
        assert f2pilot.listing[0] == ".."
        assert f2pilot.listing[1] == "todo.md"
        assert f2pilot.listing[-1] == "Templates"


async def test_order_dirs_first(app):
    async with run_test(app=app) as (pilot, f2pilot):
        app.dirs_first = False
        assert f2pilot.listing[0] == ".."  # does not move
        assert f2pilot.listing[1] == "backup.zip"  # first overall by name

        app.dirs_first = True
        assert f2pilot.listing[0] == ".."  # does not move
        assert f2pilot.listing[1] == "Documents"  # first dir by name

        await pilot.press("t")
        assert f2pilot.listing[0] == ".."  # does not move
        assert f2pilot.listing[1] == "Downloads"  # first dir by time


async def test_order_case_sensetive(app):
    async with run_test(app=app) as (pilot, f2pilot):
        app.order_case_sensitive = False
        assert f2pilot.listing[0] == ".."  # does not move
        assert f2pilot.listing[1] == "backup.zip"  # first overall by name
        assert f2pilot.listing[-1] == "Videos"  # last overall by name

        app.order_case_sensitive = True
        assert f2pilot.listing[0] == ".."  # does not move
        assert f2pilot.listing[1] == "Documents"  # first by case-sensetive order
        assert f2pilot.listing[-1] == "update.sh"  # last by case-sensetive order
