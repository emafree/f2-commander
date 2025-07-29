# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

"""Test common dialogs"""

from f2.widgets.dialogs import StaticDialog, InputDialog

from ..f2pilot import run_test


async def open_about(pilot):
    await pilot.press("ctrl+p")
    await pilot.press(*"About")
    await pilot.press("enter")


async def test_about_dialog_opens(app, sample_fs):
    """Test that the About dialog opens via command palette"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await open_about(pilot)
        # Check dialog content
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title is not None
        assert "F2 Commander" in app.screen.title
        assert app.screen.message is not None
        assert "Mozilla Public License" in app.screen.message
        assert "without warranty" in app.screen.message


async def test_static_dialog_escape(app, sample_fs):
    """Test that Esc dismisses the About dialog"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await open_about(pilot)
        assert isinstance(app.screen, StaticDialog)

        # Dismiss with Esc
        await pilot.press("escape")
        assert not isinstance(app.screen, StaticDialog)


async def test_input_dialog_escape(app, sample_fs):
    """Test that in input dialogs, Esc needs to be pressed twice"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        # Open an input dialog (using new directory dialog as example)
        await pilot.press("ctrl+n")
        assert isinstance(app.screen, InputDialog)

        # Esc should dismiss the dialog
        await pilot.press("escape")
        assert not isinstance(app.screen, InputDialog)


async def test_about_dialog_q(app, sample_fs):
    """Test that 'q' dismisses the About dialog"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await open_about(pilot)
        assert isinstance(app.screen, StaticDialog)

        # Dismiss with 'q'
        await pilot.press("q")
        assert not isinstance(app.screen, StaticDialog)


async def test_about_dialog_backspace(app, sample_fs):
    """Test that Backspace dismisses the About dialog"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await open_about(pilot)
        assert isinstance(app.screen, StaticDialog)

        # Dismiss with Backspace
        await pilot.press("backspace")
        assert not isinstance(app.screen, StaticDialog)


async def test_quit_dialog_cancel(app, sample_fs):
    """Test that selecting Cancel in quit dialog closes it without quitting"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await pilot.press("q")
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Quit?"

        # Cancel button should be focused by default, so just press enter
        await pilot.press("enter")
        assert not isinstance(app.screen, StaticDialog)
        assert app.return_code is None


async def test_quit(app, sample_fs):
    """Test that selecting Cancel in quit dialog closes it without quitting"""
    async with run_test(app=app, cwd=sample_fs) as (pilot, _):
        await pilot.press("q")
        assert isinstance(app.screen, StaticDialog)
        assert app.screen.title == "Quit?"

        # Confirm Quit
        await pilot.press("tab", "enter")
        assert app.return_code == 0


# TODO: when tests have their own configuration, reset the "user_has_accepted_license"
#       flag and control that a license dialog is shown on startup, but only once
