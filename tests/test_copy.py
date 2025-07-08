# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test copy feature"""

import time
import stat
import pytest
from pathlib import Path
from typing import Optional

from f2.widgets.dialogs import StaticDialog, InputDialog

from .f2pilot import run_test, SAMPLE_CONTENT


# TODO: parametrize all tests to test remote copy behavior, including
#       download, upload and download-upload


def tree(path: Path, from_path: Optional[Path] = None) -> list[str]:
    if from_path is None:
        from_path = path
    entries = []
    for entry in sorted(path.iterdir()):
        entries.append(str(entry.relative_to(from_path)))
        if entry.is_dir():
            entries.extend(tree(entry, from_path=from_path))
    return entries


async def open_other(path, pilot, f2pilot):
    await pilot.press("tab")
    f2pilot.go_to(path)
    await pilot.press("tab")


async def test_copy_dialog(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press("c")
        assert isinstance(app.screen, InputDialog)
        assert app.screen.value == (sample_fs / "Downloads").as_posix()


async def test_copy_nominal(app, sample_fs):
    target_path = sample_fs / "Downloads" / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(target_path.parent, pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press("c", "enter")

        assert target_path.exists()
        assert target_path.read_bytes() == SAMPLE_CONTENT
        mtime = target_path.stat().st_mtime
        now = time.time()
        assert now > mtime >= now - 1
        mode = target_path.stat().st_mode
        assert stat.S_IMODE(mode) == 0o644

        await pilot.press("tab")
        assert "todo.md" in f2pilot.listing


async def test_copy_cancel(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press("c", "escape")
        assert not (sample_fs / "Downloads" / "todo.md").exists()
        await pilot.press("tab")
        assert "todo.md" not in f2pilot.listing


async def test_copy_button(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press("c")
        await pilot.click("#ok")
        assert (sample_fs / "Downloads" / "todo.md").exists()
        await pilot.press("tab")
        assert "todo.md" in f2pilot.listing


async def test_cancel_button(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press("c")
        await pilot.click("#cancel")
        assert not (sample_fs / "Downloads" / "todo.md").exists()
        await pilot.press("tab")
        assert "todo.md" not in f2pilot.listing


async def test_copy_in_same_dir(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("todo.md")
        await pilot.press("c")
        await pilot.press(*"/todo2.md")
        await pilot.press("enter")
        assert (sample_fs / "todo2.md").exists()
        assert "todo2.md" in f2pilot.listing
        await pilot.press("tab")
        assert "todo2.md" in f2pilot.listing


@pytest.mark.parametrize("with_trailing_slash", [True, False])
async def test_copy_to_another_path(app, sample_fs, with_trailing_slash):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")
        await f2pilot.select("todo.md")
        await pilot.press("c")
        await pilot.press(*"/Downloads")
        if with_trailing_slash:
            await pilot.press("/")
        await pilot.press("enter")
        assert (sample_fs / "Downloads" / "todo.md").exists()


async def test_copy_to_rel_path(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")
        await f2pilot.select("todo.md")
        await pilot.press("c")
        await pilot.press(*"/Downloads/../Templates")
        await pilot.press("enter")
        assert (sample_fs / "Templates" / "todo.md").exists()


async def test_copy_to_non_existing_path(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")
        await f2pilot.select("todo.md")
        await pilot.press("c")
        await pilot.press(*"/foo/bar.md")
        await pilot.press("enter")
        assert not (sample_fs / "foo" / "bar.md").exists()
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Error"
        assert "No such file or directory" in app.screen.message
        assert "foo/bar.md" in app.screen.message


async def test_copy_overwrite_cancel(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # create an empty file in the copy target path:
        target_path = sample_fs / "Downloads" / "todo.md"
        target_path.touch()

        # try to overwrite:
        await open_other(target_path.parent, pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press("c", "enter")

        # overwrite dialog:
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Overwrite?"
        assert target_path.as_posix() in app.screen.message

        # cancel:
        await pilot.click("#cancel")
        assert target_path.read_bytes() == b""


async def test_copy_overwrite_confirm(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # create an empty file in the copy target path:
        target_path = sample_fs / "Downloads" / "todo.md"
        target_path.touch()

        # overwrite:
        await open_other(target_path.parent, pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press("c", "enter")
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Overwrite?"

        # confirm:
        await pilot.click("#ok")
        assert target_path.read_bytes() == SAMPLE_CONTENT


async def test_copy_overwrite_in_same_dir(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # copy in same dir with same name:
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("todo.md")
        await pilot.press("c", "enter")

        # confirm overwrite:
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Overwrite?"
        await pilot.click("#ok")

        # error should be shown:
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Error"
        assert "are the same" in app.screen.message
        assert "todo.md" in app.screen.message


async def test_copy_dir(app, sample_fs):
    target_path = sample_fs / "Downloads" / "Documents"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(target_path.parent, pilot, f2pilot)
        await f2pilot.select("Documents")
        await pilot.press("c", "enter")

        # entire file tree should have been copied:
        assert target_path.exists()
        assert tree(target_path) == tree(sample_fs / "Documents")

        # copeid entry should be shown in the target directory listing:
        await pilot.press("tab")
        assert "Documents" in f2pilot.listing


async def test_copy_dir_with_different_name(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("Documents")
        await pilot.press("c")
        await pilot.press(*"/Copy")
        await pilot.press("enter")
        assert tree(sample_fs / "Copy") == tree(sample_fs / "Documents")


async def test_copy_dir_with_another_name(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("Documents")
        await pilot.press("c")
        await pilot.press(*"/Downloads")
        await pilot.press("enter")
        assert tree(sample_fs / "Downloads" / "Documents") == tree(
            sample_fs / "Documents"
        )


@pytest.mark.parametrize("with_trailing_slash", [True, False])
async def test_copy_dir_to_new_path(app, sample_fs, with_trailing_slash):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("Documents")
        await pilot.press("c")
        await pilot.press(*"/foo/bar/baz")
        if with_trailing_slash:
            await pilot.press("/")
        await pilot.press("enter")

        expected_path = sample_fs / "foo" / "bar" / "baz"
        if with_trailing_slash:
            expected_path = expected_path / "Documents"

        assert expected_path.exists()
        assert tree(expected_path) == tree(sample_fs / "Documents")


async def test_copy_merge_dirs(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # copy source dir once:
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("Documents")
        await pilot.press("c", "enter")

        # modify source dir:
        (sample_fs / "Documents" / "new_file.txt").touch()
        (sample_fs / "Documents" / "Work" / "summary.txt").unlink()
        (sample_fs / "Documents" / "Personal" / "expenses.csv").write_bytes(b"")

        # overwrite:
        await f2pilot.select("Documents")
        await pilot.press("c", "enter")
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Merge and overwrite?"
        assert (sample_fs / "Downloads" / "Documents").as_posix() in app.screen.message

        # confirm:
        await pilot.click("#ok")

        # check the merge result:
        assert (sample_fs / "Downloads" / "Documents" / "new_file.txt").exists()
        assert (sample_fs / "Downloads" / "Documents" / "Work" / "summary.txt").exists()
        assert (
            sample_fs / "Downloads" / "Documents" / "Personal" / "expenses.csv"
        ).read_bytes() == b""


async def test_copy_dir_in_same_dir(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # copy in same dir with same name:
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("Documents")
        await pilot.press("c", "enter")

        # confirm overwrite:
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Merge and overwrite?"
        await pilot.click("#ok")

        # error should be shown:
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Error"
        assert "are the same" in app.screen.message
        assert "Documents" in app.screen.message


async def test_copy_selection(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)

        # select multiple entries:
        await f2pilot.select("todo.md")
        await pilot.press("space")
        await f2pilot.select("Documents")
        await pilot.press("space")
        await pilot.press("c", "enter")

        # all of selected should have been copied
        assert (sample_fs / "Downloads" / "todo.md").exists()
        assert tree(sample_fs / "Downloads" / "Documents") == tree(
            sample_fs / "Documents"
        )

        # cursor entry should not have been copied:
        assert not (sample_fs / "Downloads" / f2pilot.cursor_node.name).exists()


async def test_copy_error(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        (sample_fs / "Templates").chmod(0o444)
        await open_other(sample_fs / "Templates", pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press("c", "enter")
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Error"
        assert "permission denied" in app.screen.message.lower()


async def test_copy_dirup(app, sample_fs):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("..")
        await pilot.press("c")
        assert not isinstance(app.screen, InputDialog)
