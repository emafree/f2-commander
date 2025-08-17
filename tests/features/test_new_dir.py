# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test "New directory" feature"""

import pytest

from f2.widgets.dialogs import InputDialog, StaticDialog

from ..f2pilot import run_test

# TODO: parametize all tests to test remote deelete behavior (hard delete, no Trash)


async def test_dialog_opens(app, sample_fs):
    """Test that ctrl+n opens the new directory input dialog"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await pilot.press("ctrl+n")
        assert isinstance(app.screen, InputDialog)
        assert app.screen.title == "New directory"
        assert app.screen.value == ""
        assert app.screen.btn_ok == "Create"


async def test_cancel_dialog(app, sample_fs):
    """Test canceling the new directory dialog"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await pilot.press("ctrl+n")
        await pilot.press("escape")
        # Should be back to main screen, no new directory created
        assert not isinstance(app.screen, InputDialog)
        assert not (sample_fs / "test_dir").exists()


async def test_cancel_button(app, sample_fs):
    """Test canceling via the Cancel button"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await pilot.press("ctrl+n")
        await pilot.click("#cancel")
        # Should be back to main screen, no new directory created
        assert not isinstance(app.screen, InputDialog)
        assert not (sample_fs / "test_dir").exists()


async def test_empty_input(app, sample_fs):
    """Test submitting empty input (should cancel)"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await pilot.press("ctrl+n")
        await pilot.press("enter")  # Submit empty input
        # Should be back to main screen, no new directory created
        assert not isinstance(app.screen, InputDialog)


async def test_single_directory(app, sample_fs):
    """Test creating a single directory"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+n")
        await pilot.press(*"foo")
        await pilot.press("enter")

        # Directory should be created
        assert (sample_fs / "foo").is_dir()
        assert "foo" in f2pilot.listing

        # Cursor should be on the new directory
        assert f2pilot.cursor_node.name == "foo"


async def test_create_button(app, sample_fs):
    """Test creating directory via Create button"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+n")
        await pilot.press(*"foo")
        await pilot.click("#ok")

        # Directory should be created
        assert (sample_fs / "foo").is_dir()
        assert "foo" in f2pilot.listing


@pytest.mark.parametrize("with_trailing_slash", [True, False])
async def test_directory_chain(app, sample_fs, with_trailing_slash):
    """Test creating a chain of directories"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+n")
        await pilot.press(*"foo/bar/baz")
        if with_trailing_slash:
            await pilot.press("/")
        await pilot.press("enter")

        # All directories in chain should be created
        assert (sample_fs / "foo" / "bar" / "baz").is_dir()
        assert "foo" in f2pilot.listing


async def test_relative_path_dot_slash(app, sample_fs):
    """Test creating directory with ./foo/bar path"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+n")
        await pilot.press(*"./foo/bar")
        await pilot.press("enter")

        # Directories should be created
        assert (sample_fs / "foo" / "bar").is_dir()
        assert "foo" in f2pilot.listing


async def test_parent_directory(app, sample_fs):
    """Test creating directory in parent directory with ../foo"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # Navigate to a subdirectory first
        f2pilot.go_to(sample_fs / "Documents")

        await pilot.press("ctrl+n")
        await pilot.press(*"../foo")
        await pilot.press("enter")

        # Directory should be created in parent (sample_fs)
        assert (sample_fs / "foo").is_dir()


async def test_absolute_path(app, sample_fs):
    """Test creating directory with absolute path"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        abs_path = sample_fs / "absolute_test"

        await pilot.press("ctrl+n")
        await pilot.press(*str(abs_path))
        await pilot.press("enter")

        # Directory should be created at absolute path
        assert abs_path.is_dir()
        assert "absolute_test" in f2pilot.listing


async def test_existing_directory_error(app, sample_fs):
    """Test error when trying to create directory that already exists"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await pilot.press("ctrl+n")
        await pilot.press(*"Documents")
        await pilot.press("enter")

        # Should show error dialog
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Error"
        assert app.screen.message is not None
        assert "already exists" in app.screen.message
        assert "Documents" in app.screen.message


async def test_existing_file_error(app, sample_fs):
    """Test error when trying to create directory with same name as existing file"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await pilot.press("ctrl+n")
        await pilot.press(*"todo.md")
        await pilot.press("enter")

        # Should show error dialog
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Error"
        assert app.screen.message is not None
        assert "already exists" in app.screen.message
        assert "todo.md" in app.screen.message


async def test_permission_error(app, sample_fs):
    """Test error when trying to create directory in read-only location"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        # Make Templates directory read-only
        (sample_fs / "Templates").chmod(0o444)

        # Navigate to Templates directory
        f2pilot.go_to(sample_fs / "Templates")

        await pilot.press("ctrl+n")
        await pilot.press(*"foo")
        await pilot.press("enter")

        # Should show error dialog
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Error"
        assert app.screen.message is not None
        assert "permission denied" in app.screen.message.lower()

        (sample_fs / "Templates").chmod(0o755)  # restore permissions to list dir
        assert not (sample_fs / "Templates" / "foo").exists()


async def test_directory_with_spaces(app, sample_fs):
    """Test creating directory with spaces in name"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, f2pilot):
        await pilot.press("ctrl+n")
        await pilot.press(*"dir with spaces")
        await pilot.press("enter")

        # Directory should be created
        assert (sample_fs / "dir with spaces").is_dir()
        assert "dir with spaces" in f2pilot.listing
