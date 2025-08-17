# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test copy and move features"""

import stat
import time
from pathlib import Path
from typing import Optional

import pytest

from f2.widgets.dialogs import InputDialog, StaticDialog

from ..f2pilot import SAMPLE_CONTENT, run_test

# TODO: parametize all tests to test remote copy behavior, including
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


@pytest.mark.parametrize("action", ["c", "m"])
async def test_dialog(app, sample_fs, action):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press(action)
        assert isinstance(app.screen, InputDialog)
        assert app.screen.value == (sample_fs / "Downloads").as_posix()


@pytest.mark.parametrize("action", ["c", "m"])
async def test_nominal(app, sample_fs, action):
    source_path = sample_fs / "todo.md"
    target_path = sample_fs / "Downloads" / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(target_path.parent, pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press(action, "enter")

        assert target_path.exists()
        assert target_path.read_bytes() == SAMPLE_CONTENT
        mode = target_path.stat().st_mode
        assert stat.S_IMODE(mode) == 0o644

        if action == "c":
            # copy: source should still exist
            assert source_path.exists()
            # check mtime for copy
            mtime = target_path.stat().st_mtime
            now = time.time()
            assert now > mtime >= now - 1
        else:
            assert not source_path.exists()
            assert "todo.md" not in f2pilot.listing

        await pilot.press("tab")
        assert "todo.md" in f2pilot.listing


@pytest.mark.parametrize("action", ["c", "m"])
async def test_cancel(app, sample_fs, action):
    source_path = sample_fs / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press(action, "escape")

        # source should still exist (operation was cancelled)
        assert source_path.exists()
        assert not (sample_fs / "Downloads" / "todo.md").exists()
        await pilot.press("tab")
        assert "todo.md" not in f2pilot.listing


@pytest.mark.parametrize("action", ["c", "m"])
async def test_button(app, sample_fs, action):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press(action)
        await pilot.click("#ok")
        assert (sample_fs / "Downloads" / "todo.md").exists()
        await pilot.press("tab")
        assert "todo.md" in f2pilot.listing


@pytest.mark.parametrize("action", ["c", "m"])
async def test_cancel_button(app, sample_fs, action):
    source_path = sample_fs / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press(action)
        await pilot.click("#cancel")

        # source should still exist (operation was cancelled)
        assert source_path.exists()
        assert not (sample_fs / "Downloads" / "todo.md").exists()
        await pilot.press("tab")
        assert "todo.md" not in f2pilot.listing


@pytest.mark.parametrize("action", ["c", "m"])
async def test_in_same_dir(app, sample_fs, action):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("todo.md")
        await pilot.press(action)
        await pilot.press(*"/todo2.md")
        await pilot.press("enter")
        assert (sample_fs / "todo2.md").exists()
        assert "todo2.md" in f2pilot.listing
        await pilot.press("tab")
        assert "todo2.md" in f2pilot.listing


@pytest.mark.parametrize("action", ["c", "m"])
@pytest.mark.parametrize("with_trailing_slash", [True, False])
async def test_to_another_path(app, sample_fs, action, with_trailing_slash):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")
        await f2pilot.select("todo.md")
        await pilot.press(action)
        await pilot.press(*"/Downloads")
        if with_trailing_slash:
            await pilot.press("/")
        await pilot.press("enter")
        assert (sample_fs / "Downloads" / "todo.md").exists()


@pytest.mark.parametrize("action", ["c", "m"])
async def test_to_rel_path(app, sample_fs, action):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")
        await f2pilot.select("todo.md")
        await pilot.press(action)
        await pilot.press(*"/Downloads/../Templates")
        await pilot.press("enter")
        assert (sample_fs / "Templates" / "todo.md").exists()


@pytest.mark.parametrize("action", ["c", "m"])
async def test_to_non_existing_path(app, sample_fs, action):
    source_path = sample_fs / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")
        await f2pilot.select("todo.md")
        await pilot.press(action)
        await pilot.press(*"/foo/bar.md")
        await pilot.press("enter")

        # source should still exist (operation failed)
        assert source_path.exists()
        assert not (sample_fs / "foo" / "bar.md").exists()
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Error"
        assert "No such file or directory" in app.screen.message
        assert "foo/bar.md" in app.screen.message


@pytest.mark.parametrize("action", ["c", "m"])
async def test_overwrite_cancel(app, sample_fs, action):
    source_path = sample_fs / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # create an empty file in the target path:
        target_path = sample_fs / "Downloads" / "todo.md"
        target_path.touch()

        # try to overwrite:
        await open_other(target_path.parent, pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press(action, "enter")

        # overwrite dialog:
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Overwrite?"
        assert target_path.as_posix() in app.screen.message

        # source should still exist (operation was cancelled)
        assert source_path.exists()
        assert target_path.read_bytes() == b""


@pytest.mark.parametrize("action", ["c", "m"])
async def test_overwrite_confirm(app, sample_fs, action):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # create an empty file in the target path:
        target_path = sample_fs / "Downloads" / "todo.md"
        target_path.touch()

        # overwrite:
        await open_other(target_path.parent, pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press(action, "enter")
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Overwrite?"
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


async def test_move_overwrite_in_same_dir(app, sample_fs):
    source_path = sample_fs / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # move in same dir with same name:
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("todo.md")
        await pilot.press("m", "enter")

        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Overwrite?"
        await pilot.click("#ok")

        # `mv file file` works, but changes nothing
        assert source_path.exists()
        assert source_path.read_bytes() == SAMPLE_CONTENT


@pytest.mark.parametrize("action", ["c", "m"])
async def test_dir(app, sample_fs, action):
    source_path = sample_fs / "Documents"
    target_path = sample_fs / "Downloads" / "Documents"
    original_tree = tree(source_path)
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(target_path.parent, pilot, f2pilot)
        await f2pilot.select("Documents")
        await pilot.press(action, "enter")

        # entire file tree should have been copied/moved:
        assert target_path.exists()
        assert tree(target_path) == original_tree

        if action == "c":
            # copy: source should still exist
            assert source_path.exists()
        else:
            # move: source should no longer exist
            assert not source_path.exists()
            assert "Documents" not in f2pilot.listing

        # entry should be shown in the target directory listing:
        await pilot.press("tab")
        assert "Documents" in f2pilot.listing


@pytest.mark.parametrize("action", ["c", "m"])
async def test_dir_with_different_name(app, sample_fs, action):
    source_path = sample_fs / "Documents"
    original_tree = tree(source_path)
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("Documents")
        await pilot.press(action)
        await pilot.press(*"/Target")
        await pilot.press("enter")
        assert tree(sample_fs / "Target") == original_tree


@pytest.mark.parametrize("action", ["c", "m"])
async def test_dir_with_another_name(app, sample_fs, action):
    source_path = sample_fs / "Documents"
    original_tree = tree(source_path)
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("Documents")
        await pilot.press(action)
        await pilot.press(*"/Downloads")
        await pilot.press("enter")
        assert tree(sample_fs / "Downloads" / "Documents") == original_tree


@pytest.mark.parametrize("action", ["c", "m"])
@pytest.mark.parametrize("with_trailing_slash", [True, False])
async def test_dir_to_new_path(app, sample_fs, action, with_trailing_slash):
    source_path = sample_fs / "Documents"
    original_tree = tree(source_path)
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("Documents")
        await pilot.press(action)
        await pilot.press(*"/foo/bar/baz")
        if with_trailing_slash:
            await pilot.press("/")
        await pilot.press("enter")

        if action == "m" and with_trailing_slash:
            # move with trailing slash yields error
            assert app.screen.title == "Error"
            assert "No such directory" in app.screen.message
            # source should still exist (move failed)
            assert source_path.exists()
        else:
            expected_path = sample_fs / "foo" / "bar" / "baz"
            if with_trailing_slash:
                expected_path = expected_path / "Documents"
            assert expected_path.exists()
            assert tree(expected_path) == original_tree


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


async def test_move_dir_to_existing_dir_error(app, sample_fs):
    source_path = sample_fs / "Documents"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # first create a target directory with same name:
        target_dir = sample_fs / "Downloads" / "Documents"
        target_dir.mkdir()

        # try to move source dir to existing target:
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("Documents")
        await pilot.press("m", "enter")

        # should show error dialog (no merge for move):
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Destination exists"
        assert target_dir.as_posix() in app.screen.message

        # source should still exist (move failed):
        assert source_path.exists()
        # target should still be empty:
        assert target_dir.exists()
        assert list(target_dir.iterdir()) == []


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


async def test_move_dir_in_same_dir(app, sample_fs):
    source_path = sample_fs / "Documents"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # move in same dir with same name:
        await pilot.press("ctrl+s")  # open same dir in other panel
        await f2pilot.select("Documents")
        await pilot.press("m", "enter")

        # should show destination exists error (no merge for move):
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Destination exists"

        # source should still exist (move failed):
        assert source_path.exists()


@pytest.mark.parametrize("action", ["c", "m"])
async def test_selection(app, sample_fs, action):
    source_todo_path = sample_fs / "todo.md"
    source_docs_path = sample_fs / "Documents"
    original_docs_tree = tree(source_docs_path)
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)

        # select multiple entries:
        await f2pilot.select("todo.md")
        await pilot.press("space")
        await f2pilot.select("Documents")
        await pilot.press("space")
        await pilot.press(action, "enter")

        # all of selected should have been copied/moved
        assert (sample_fs / "Downloads" / "todo.md").exists()
        assert tree(sample_fs / "Downloads" / "Documents") == original_docs_tree

        if action == "c":
            # copy: sources should still exist
            assert source_todo_path.exists()
            assert source_docs_path.exists()
        else:
            # move: sources should no longer exist
            assert not source_todo_path.exists()
            assert not source_docs_path.exists()

        # cursor entry should not have been copied/moved:
        assert not (sample_fs / "Downloads" / f2pilot.cursor_node.name).exists()


@pytest.mark.parametrize("action", ["c", "m"])
async def test_error(app, sample_fs, action):
    source_path = sample_fs / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        (sample_fs / "Templates").chmod(0o444)
        await open_other(sample_fs / "Templates", pilot, f2pilot)
        await f2pilot.select("todo.md")
        await pilot.press(action, "enter")
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Error"
        assert "permission denied" in app.screen.message.lower()

        # source should still exist (operation failed)
        assert source_path.exists()


@pytest.mark.parametrize("action", ["c", "m"])
async def test_dirup(app, sample_fs, action):
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await open_other(sample_fs / "Downloads", pilot, f2pilot)
        await f2pilot.select("..")
        await pilot.press(action)
        assert not isinstance(app.screen, InputDialog)
