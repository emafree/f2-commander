# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test delete feature"""

from pathlib import Path

from f2.widgets.dialogs import StaticDialog

from ..f2pilot import run_test


# NOTE: some manual testing required, or more automation to verify Trash behavior:
# - verify that files are put in Trash
# - verify that files from Trash can be actually restored

# TODO: parametize all tests to test remote deelete behavior (hard delete, no Trash)


async def test_dialog(app, sample_fs):
    """Test that delete action opens confirmation dialog"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await f2pilot.select("todo.md")
        await pilot.press("D")
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Delete?"
        assert app.screen.message is not None
        assert "This will move todo.md to Trash" in app.screen.message


async def test_cancel(app, sample_fs):
    """Test canceling delete operation"""
    source_path = sample_fs / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await f2pilot.select("todo.md")
        await pilot.press("D", "escape")

        # source should still exist (operation was cancelled)
        assert source_path.exists()
        assert "todo.md" in f2pilot.listing


async def test_cancel_button(app, sample_fs):
    """Test canceling delete operation using cancel button"""
    source_path = sample_fs / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await f2pilot.select("todo.md")
        await pilot.press("D")
        await pilot.click("#cancel")

        # source should still exist (operation was cancelled)
        assert source_path.exists()
        assert "todo.md" in f2pilot.listing


async def test_file_delete(app, sample_fs):
    """Test deleting a single file"""
    source_path = sample_fs / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await f2pilot.select("todo.md")
        await pilot.press("D", "tab", "enter")

        # file should no longer exist in the directory
        assert not source_path.exists()
        assert "todo.md" not in f2pilot.listing


async def test_file_delete_button(app, sample_fs):
    """Test deleting a single file using delete button"""
    source_path = sample_fs / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await f2pilot.select("todo.md")
        await pilot.press("D")
        await pilot.click("#ok")

        # file should no longer exist in the directory
        assert not source_path.exists()
        assert "todo.md" not in f2pilot.listing


async def test_dir_delete(app, sample_fs):
    """Test deleting a directory"""
    source_path = sample_fs / "Documents"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await f2pilot.select("Documents")
        await pilot.press("D", "tab", "enter")

        # directory should no longer exist
        assert not source_path.exists()
        assert "Documents" not in f2pilot.listing


async def test_multiple_selection_delete(app, sample_fs):
    """Test deleting multiple selected entries"""
    source_todo_path = sample_fs / "todo.md"
    source_docs_path = sample_fs / "Documents"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # select multiple entries
        await f2pilot.select("todo.md")
        await pilot.press("space")
        await f2pilot.select("Documents")
        await pilot.press("space")

        # note the file under cursor
        cursor_node_path = f2pilot.cursor_node.path

        await pilot.press("D", "tab", "enter")

        # all selected entries should be deleted
        assert not source_todo_path.exists()
        assert not source_docs_path.exists()
        assert "todo.md" not in f2pilot.listing
        assert "Documents" not in f2pilot.listing

        # cursor entry should not have been deleted
        assert Path(cursor_node_path).exists()


async def test_delete_nonexistent_file(app, sample_fs):
    """Test deleting a file that was removed externally"""
    source_path = sample_fs / "todo.md"
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await f2pilot.select("todo.md")

        # remove the file externally
        source_path.unlink()

        # try to delete it in the UI
        await pilot.press("D", "tab", "enter")

        # error dialog should be shown
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Error"
        # The exact error message may vary by OS, but should indicate file not found
        assert app.screen.message is not None
        message_lower = app.screen.message.lower()
        assert (
            "todo.md" in message_lower
            or "not found" in message_lower
            or "no such file" in message_lower
        )


async def test_delete_dirup(app, sample_fs):
    """Test that deleting '..' entry does nothing"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await f2pilot.select("..")
        await pilot.press("D")
        # delete dialog should not open for '..' entry
        assert not isinstance(app.screen, StaticDialog)
