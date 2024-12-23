# Validation scenarios

This document is a complete validation test suite for a release. Eventually,
all of the below should be automated.

It also lists all known bugs (see the **KNOWN BUG** tags).

1. Display

 - Listing is complete in any directory (all files and directories are listed,
   considering the "Show hidden" toggle state).
 - Files and directories have size and mtime information displayed.
 - Directory summary is displayed in the panel border (size, # of files, # of
   directories).
 - Directories, files, executable files, hidden files, and links have different
   display styles.
 - Columns take full width of the panel.
   - When terminal changes the size, panels and columns resize accordingly.
 - Footer includes common file actions, bound keys, and is clickable with mouse.
   - Known limitation: except for the "Command Palette" footer item.

**KNOWN BUG**: no scroll bar in long listings

2. Basic navigation

 - `j`/`k` and `up`/`down` move the cursor one row at a time.
 - `g` moves cursor to the top of the list.
 - `G` moves cursor to the bottom of the list.
 - `C-f` and `C-b` move one page down and up respectively,
 - `C-d` and `C-u` move **half** a page down and up respectively,
   - at edge all above do nothing,
   - in an empty directory they do nothing.
 - `Enter` on a directory navigates to that directory.
 - `Enter` on `..` goes up.
 - `Backspace` pressed anywhere goes up.

**KNOWN BUG**: `C+u`/`C+d` should scroll half a page (not en entire page).

3. Navigation with mouse

 - Mouse movements highlight the rows under the cursor.
 - Clicking on a directory navigates to that directory.
 - Clicking on `..` goes up.
 - Clicking on file does nothing.

4. Selection

 - `Space`/`Shift+down`/`J`(`Shift+j`) selects current row and moves the cursor
   one row down;
   - does not move at the bottom of the list.
 - `Shift+up`/`K` selects current row and moves the cursor one row up;
   - does not move at the bottom of the list.
 - `-` removes all selection;
   - does nothing if there is no selection.
 - `+` selects all rows;
   - even is some were already selected,
   - does nothing is all rows are already selected.
 - `*` inverts selection;
   - selects all or nothing when nothing/all was selected.
 - `..` (directory up) row is never selected.
 - Select two files and move the cursor to a third one, do not select it. Copy
   files. A file under cursor is not copied (not considered as selected).

5. Ordering

 - With the "Directories first" option deactivated,
 - and with "case sensitivity" option deactivated:
 - `n`/`N` orders all rows by entry name, asc/desc
 - `s`/`S` orders all rows by size, asc/desc
 - `t`/`T` orders all rows by mtime, asc/desc
 - Pressing same ordering key twice reverses the order direction.
 - With the "directories first" option activated, directories go first, then
   files, but each group respects selected ordering.
 - With the "case sensitive name order" activated, ordering by name respects
   letter case.

**KNOWN BUG**: with "Directories first" option activated, soft links to
directories are considered as files, but should be listed among directories.

6. Refresh:

 - Touch a new file in current directory in another program,
 - then type `R`,
 - expect a new file to apper in the listing.

7. Filtering

 - Type `f`, enter a glob pattern, submit.
 - Verify that:
   - only matching entries are displayed,
   - glob is displayed in the panel border,
   - directory summary is updated in the panel border (shows filtered rows
     summary).
 - Type `f`, clear the input field, and submit it empty.
 - Full listing should be now shown, with a regular panel border (full
   directory summary).

**TODO**: More tests are necessary (invalid inputs and other edge cases)

8. Other listing actions

 - `h` toggles the display of hidden files and directories in both panels.
 - `o` opens current directory (not the highlighted row) in an OS file manager.
 - `C-Space` calculates the full size of the directory under the cursor
   (recursively), and moves the cursor down;
   - does not move cursor at the bottom at the list,
   - if calculation is slow, replaces size with "..." while calculating, but
     moves the cursor instantly.
 - `Enter` on a file opens it in a default associated OS application;
   - `Enter` on an executable file does nothing.
 - `C-w` swaps the panels (left to right, right to left).
 - `C-s` opens the current panel directory in the other (inactive) panel.

**TODO**: More tests needed for the "Swap Panels" feature, ensure that swapped
panels are correctly reflected when changing left/right panel type.

**TODO**: Tests for other actions available in the Command Palette, but having
no key bindings.

**KNOWN BUG**: Enable "Show hidden files" option, select a regular file,
disable the option. As a result, the selection is cleared. Instead, it should
be kept unchanged, unless it included any of the hidden file.

9. Go to path

 - `C-g` opens an input dialog with a current directory path.
 - Entering any invalid or not existing path yields an error message ("info"
   level) and closes the dialog; nothing changes in the UI.
 - Entering an existing file path results in no change in the UI.
 - Submitting an empty input navigates to the directory the Commander was
   started in (CWD of the Commander).

**TODO**: Entering a valid URL may connect to a "simple" remote file system

10. Bookmarks

 - `b` opens a Bookmarks dialog.
 - The dialog displays all bookmarks listed in the configuration file.
 - Selecting (`up`/`down`+`Enter`, or a mouse click) an item opens the selected
   directory in the active panel.
 - Non-existing directories are disabled and cannot be selected with arrow keys
   or a mouse click.
 - First 9 entries (except the very first one) are enumerated, according
   keyboard keys select them.
 - Select non-existing (disabled) directory by its hot key. An info message is
   displayed telling the use that the directory does not exist.

11. View

 - View (footer action) or `v` opens the currently highlighted file in a viewer
   program.
 - Quitting the Viewer returns the user to the Commander, which is in the same
   state as before running it.
 - View action does nothing if the currently highlighted row is not a file.
 - If the viewer program ends in error for any reason, an error message is
   displayed to the user. To test:
   - Having a file with no read access (e.g., `chmod -r` on it),
   - View it,
   - A warning message is displayed with viewer exit code (code `1` for
     `less`).
 - Viewer program selection:
   - View action selects to run either `less`, `more` or the same program as
     Edit action, whichever is available in the command line, in this order.
   - If the viewer program cannot be found (none of the above exist), an error
     message is shown to the user.
     - To test: add `return None` as a first statement in `shell.py:viewer()`

**TODO**: Remote files logic (download)

12. Edit

 - Edit (footer action) or `e` should have the same behavior as View, but opens
   an editor program.
 - Editor program selection:
   - Edit action selects to run either `$EDITOR`, `vi`, `nano`, or `edit`,
     whichever is available in the command line, in this order.
   - If the editor program cannot be found (not one from above exists), an
     error message is shown to the user.
     - To test: add `return None` as a first statement in `shell.py:editor()`

**TODO**: Remote files logic (download, upload if user confirms)

13. Copy

 - Generic Copy dialog behavior:
   - Copy (footer action) or `c` opens a copy dialog.
   - By default, an inactive panel path is shown in the input box.
   - Selecting "Cancel" closes dialog, nothing else changes.
   - Selecting "Copy" copies selected items (workflow tests below).

 - Copy a **file** between different source and target directories:
   - Select **different** directories on left and right,
   - copy a file,
   - submit a default path,
   - the file is copied to the target directory,
   - target directory listing is updated and shows a new file in it.

 - Copy a file with new name:
   - Select **same** directory on left and right,
   - copy a file,
   - add a new file name to the default path, submit,
   - the file is copied in the same directory with a provided name,
   - directory listing is updated (both left and right) and shows a new file.

 - Copy a file to another directory:
   - Copy a file,
   - change the target path to any existing directory path, **without**
     trailing slash, submit,
   - the file is copied into that directory.
   - Redo the same test **with** a trailing slash, same effect is expected.

 - Copy a file to a new directory:
   - Copy a file,
   - change the target path to include a non-existing directory,
   - an error message is shown to the the user.

 - Overwrite a file on copy:
   - Copy a file to an existing file,
   - a confirmation dialog is shown to the user to confirm the overwrite,
   - the file is copied only if confirmed.

 - Copy a file in same directory:
   - Select same directory on left and right,
   - copy a file,
   - submit the default path,
   - an error message is shown to the the user.

 - Copy a **directory** between different source and target directories:
   Same scenario as for the file copy, directory is copied recursively with all
   of its content.

 - Copy a directory with a new name:
   Same scenario as for the file copy, directory is copied recursively with all
   of its content.
   Caution: only tests when the target name contains no trailing slash.

 - Copy a directory to another directory:
   Same scenario as for the file copy, directory is copied recursively with all
   of its content.
   Caution: only tests when the target name contains no trailing slash.

 - Copy a directory to a new directory:
   - Copy a directory,
   - change target path to add a new last level directory and a trailing slash,
   - a specified directory is created and a source directory is copied into it.
   - Test the same with arbitrary (e.g., 2) intermediate non-existing
     directories and no trailing slash. Non-existing directories are created,
     and the source directory is copied with a new name (last path element)
     into it.

 - Merge a directory on copy:
   - Copy a directory to some target directory; perform the copy;
   - Add a file to the source directory,
   - delete another file in the source directory,
   - modify another file in the source directory,
   - and copy it again to the same target directory;
   - a confirmation dialog asks a user to confirm the merge and overwrite,
   - copy continues only if the user confirms;
   - target directory contains a new file, a modified file, and also contains a
     copy of the file that was deleted in the source directory.

 - Copy a directory in same directory:
   Same scenario as for the file copy

 - Copy a selection:
   - Select multiple entries: directories and files (at least 1 directory and 1
     file),
   - copy,
   - enter a new directory path as a target path,
   - selected entries are copied with same logic as they would have been copied
     individually (one by one).
   - Test same with only directories selected (2 directories).
   - Test same with only files selected (2 files).

 - Copy error:
   - Create a read-only directory (`chmod -w`),
   - copy a file into it,
   - a error message is shown to the user.

 - Copy '..' entry, nothing happens (copy dialog does not open).

**TODO**: Test different target paths, including relative and absolute path
(starting with `./`, `../`, `/`).

**TODO**: Test an invalid path (e.g, with `:` colon character).

**TODO**: Remote copy behavior: download, upload and download-upload.

14. Move

Same test scenarios as Copy, but with "move" behavior: source file or directory
does not exist after move, file listing is updated to reflect it.

Some differences:
 - Moving a directory has no "overwrite" option

**TODO**: Remote move behavior: download, upload and download-upload.

15. Delete

 - Highlight a file, Delete (footer action) or `D` (`Shift+d`) opens
   confirmation dialog,
 - select "Cancel", dialog closes, nothing happens.
 - Highlight a file, `D`,
 - select "Delete",
 - the file is moved to system Trash (Recycle Bin),
 - and it is not present in the directory listing.

 - Repeat the same test with a directory. The entire directory is moved to
   Trash, if confirmed.

 - Repeat the same test with a multiple selection. After a single confirmation
   all selected entries (files and directories) are moved to Trash.

 - Restore any of the deleted entries (OS feature). They should be correctly
   restored to their original location.

 - Touch a file, and then remove it in an another program,
 - delete it, confirm,
 - an error message is shown to the user indicating that the file does not
   exist.

 - Delete '..' entry, nothing happens (copy dialog does not open).

**TODO**: Remote delete behavior (no Trash, hard delete).

**KNOWN BUG**: If same dir is open in both panels, only active file listing is
refrehsed after a delete.

16. New directory

 - New dir (footer action) or `C-n` opens an input dialog, empty by default.
 - Select "Cancel", dialog closes, nothing happens.
 - Submit empty input, expect same effect as for "Cancel".

 - Submit a single valid directory name (e.g., `foo`),
 - a directory is created and a file listing is updated.

 - Submit an invalid directory name (e.g., `for:bar`, with a colon),
 - an error message is show to the user indicating that the directory was not
   created.
   **TODO**: how to test in macOS? Any character are now allowed in HFS+. Test
   on a different file system?

 - Submit a valid path consisting of multiple new directories (e.g., `foo/bar`),
 - directory chain is created and a file listing is updated.
 - Test same with a trailing slash, expect same effect regardless the trailing
   slash.

 - Submit a path like `./foo/bar`, expect same behavior as for `foo/bar`.

 - Submit a path like `../foo`, expect a directory to be crated in the parent
   directory of the currently active panel.

 - Submit a path like `/tmp/foo`, expect a directory to be created in the
   defined absolute path.

**TODO**: Remote directory creation behavior.

17. Shell

 - Shell (footer action) or `x` starts a new shell in the same terminal,
 - terminal content is the same as before running the Commander,
 - new shell started in the same directory as the directory of the active file
   listing when then action was invoked.
 - Run `touch foo`.
 - Quit the shell (e.g., `quit` or `EOF`/`C-d`), user returns the user to the
   Commander.
 - Commander state is not changed, new file is shown in the listing.

 - Run shell,
 - invoke `exit 42`,
 - user is returned to the Commander,
 - and an error message is shown to the user indicating that the shell exited
   with an error code `42`.

18. Command palette

 - `C-\` opens a command palette
 - Command Palette lists at least the some actions available with hotkeys and
   some other actions. Hotkeys are shown for actions where they exist (e.g.,
   "Filter" `f`, "Order by name" `n`). Some other actions do not have hotkeys
   (e.g., "Toggle directories first"). Actions available in the footer are not
   displayed in the Command Palette (e.g., "Quit", "Copy").

19. Quit

 - Quit (footer action) or `q` opens a confirmation dialog to quit the Commander.
 - Select "No", dialog closes, nothing happens.
 - `q`, then select "Yes", Commander quits and user is returned so same directory
   where Commander was originally started.

20. Change the panel type

 - `C-r` opens a dialog allowing to change the **right** panel type.
 - `Esc`/`q`/`Backspace` closes the dialog with no change.
 - Selecting another panel type from the list change the right panel type
   accordingly.

 - Same tests for **left** panel, invoked with `C-e`.

 - With a file listing in both left and right panels,
 - and an active panel on the **left**,
 - `C-e` and select "Preview" panel,
 - right panel is automatically activated (cursor is in the right panel,
   navigation instantly responds to `j`/`k` and other keys).

**KNOWN BUG**: Navigate to any directory that is not a starting directory,
enable "Show hidden files" option, change active panel type to Preview, then
change it back to "Files". A previously selected directory should be shown,
with hidden files. Instead, a starting directory is shown and the "Show hidden
files" option is not respected (note: ideally, restore the previous panel
state, including ordering, etc.).

21. Preview panel

 - With a file listing in both left and right panels,
 - and an active panel on the left,
 - `C-r` and select a "Preview" panel;
 - Preview panel instantly shows a file or a directory preview,
 - navigating in the file listing on the left updates the preview with a
   content of a highlighted entry.

 - Text file preview:
   - Preview a text file with no syntax (e.g., raw text file)
   - a head of the file is displayed in the preview panel
   - preview panel cannot be scrolled (only the head is displayed)
   - preview panel shows content for its entire visible height
     - provided that the file is long enough,
     - or, shows the entire file content if the file is short enough to fit the
       preview window.

 - Large text file preview:
   - Preview a very large text file (n GB),
   - preview shows the file header instantly

 - Syntax preview:
   - Preview a text file with a syntax (e.g., Python file, etc.),
   - preview panel shows a head of the file with its syntax highlighted.

 - Preview a "binary" file:
   - Preview a file that is not a text file (e.g., a PDF, a binary executable,
     etc.),
    - preview panel shows a message about the file not being a text file.

 - Preview a directory:
   - Preview a directory with a complex structure and more nested directories
     and files than the height of the Commander.
   - a flattened list of child entries names (directories and files) is shown,
     - directory names end with a trailing slash,
   - the list of name is breadth-first: all child entries of **every**
     sub-directory are first listed, only the their direct children are listed,
     and so on.
   - Previewing a `..` directory is possible.

 - Preview a soft link:
   - Soft links to files and directories are previewed same way as respective
     files and directories themselves.

**TODO**: Remote Preview behavior

22. Help panel

 - `C-r` and select a "Help" panel;
 - Help panel is shown with a long, scrollable, formatted and highlighted help
   content.
 - Pressing any key switches the right panel to the file listing.

23. Connect to a remote location

**TODO**

24. Archives and compressed files

**TODO**

25. About dialog

 - Open the Command Palette, select the "About" action.
 - A message with Commander version and a short license and a "no warranty"
   information is shown.

26. Generic dialog behavior

 - In any dialog,
 - `Esc` quits the dialog with the same behavior as the "No" / "Cancel" action.
   - In an input dialog, `Esc` needs to be pressed twice (first time to exit
     the input box)
 - `q` has the same effect as `Esc`
 - `Backspace` has the same effect as `Esc`

27. Configuration file

**TODO**

**KNOWN BUG**: configuration file syntax is not validated, incorrect
configuration may break the app (error on startup).

28. License message

 - Delete the file `user_has_accepted_license` from the configuration directory,
 - (re)start the Commander
 - user is presented a message about the license and no warranty,
 - restart the Commander,
 - the message does not appear anymore.


## Other known bugs

 - Default viewer, editor, shell and "open" programs are mostly macOS-specific,
   choices are too rigid. Make sure defaults work on clean macOS and Linux
   installs.

 - File list has an unnecessary 2-column (2 character wide) gap even when no
   vertical scroll bar is present (2 characters are reserved for the scroll
   bar).
