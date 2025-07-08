# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test file selection feature"""

import pytest

from .f2pilot import YELLOW, run_test


EXCLUDE = ["backup.zip"]  # archive already has YELLOW in its style


@pytest.mark.parametrize(
    "key,offset", [("J", 1), ("K", -1), ("shift+down", 1), ("shift+up", -1)]
)
async def test_select(key, offset):
    async with run_test() as (pilot, f2pilot):
        name = "contacts.csv"
        idx = f2pilot.listing.index(name)
        await f2pilot.select(name)
        # select:
        await pilot.press(key)
        assert f2pilot.cursor_node.name == f2pilot.listing[idx + offset]
        assert (
            f2pilot.cell(name, "name").markup.strip()
            == f"[{YELLOW} italic]{name}[/{YELLOW} italic]"
        )


async def test_deselect():
    async with run_test() as (pilot, f2pilot):
        name = "contacts.csv"
        await f2pilot.select(name)
        # select:
        await pilot.press("J")
        assert YELLOW in f2pilot.cell(name, "name").markup
        # deslect:
        await pilot.press("k", "J")
        assert YELLOW not in f2pilot.cell(name, "name").markup


async def test_select_down_at_bottom():
    async with run_test() as (pilot, f2pilot):
        # move to the bottom of the list:
        name = f2pilot.listing[-1]
        await pilot.press("G")
        assert YELLOW not in f2pilot.cell(name, "name").markup
        # select:
        await pilot.press("J")
        assert f2pilot.cursor_node.name == name  # still on the same node
        assert YELLOW in f2pilot.cell(name, "name").markup


async def test_cannot_select_dir_up():
    async with run_test() as (pilot, f2pilot):
        await pilot.press("g")
        assert f2pilot.cursor_node.name == ".."
        await pilot.press("K")
        assert f2pilot.cursor_node.name == ".."
        assert YELLOW not in f2pilot.cell("..", "name").markup


async def test_select_all():
    async with run_test() as (pilot, f2pilot):
        # select all:
        await pilot.press("plus")
        for name in f2pilot.listing[1:]:
            assert YELLOW in f2pilot.cell(name, "name").markup

        # re-selecting all changes nothing:
        await pilot.press("plus")
        for name in f2pilot.listing[1:]:
            assert YELLOW in f2pilot.cell(name, "name").markup

        # deselect all:
        await pilot.press("minus")
        for name in f2pilot.listing[1:]:
            if name in EXCLUDE:
                continue
            assert YELLOW not in f2pilot.cell(name, "name").markup

        # second deselect all changes nothing:
        await pilot.press("minus")
        for name in f2pilot.listing[1:]:
            if name in EXCLUDE:
                continue
            assert YELLOW not in f2pilot.cell(name, "name").markup


async def test_select_all_with_preselection():
    async with run_test() as (pilot, f2pilot):
        # select all, with some entries already selected before:
        await pilot.press("j", "J")  # pre-select one entry
        await pilot.press("plus")
        for name in f2pilot.listing[1:]:
            assert YELLOW in f2pilot.cell(name, "name").markup

        # deselect all, with some entries already selected before:
        await pilot.press("j", "J")  # de-select one entry
        await pilot.press("minus")
        for name in f2pilot.listing[1:]:
            if name in EXCLUDE:
                continue
            assert YELLOW not in f2pilot.cell(name, "name").markup


async def test_invert_selection():
    async with run_test() as (pilot, f2pilot):
        names = f2pilot.listing[1:3]
        for name in names:
            await f2pilot.select(name)
            await pilot.press("J")
        await pilot.press("asterisk")
        for name in f2pilot.listing[1:]:
            if name in EXCLUDE:
                continue
            if name in names:
                assert YELLOW not in f2pilot.cell(name, "name").markup
            else:
                assert YELLOW in f2pilot.cell(name, "name").markup


async def test_selection_cursor_excluded(app):
    async with run_test(app) as (pilot, f2pilot):
        await pilot.press("j", "J", "J")
        expected_selection = sorted(f2pilot.listing[1:3])
        actual_selection = sorted([node.name for node in app.active_filelist.selection])
        assert actual_selection == expected_selection
