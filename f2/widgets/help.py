# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko


from importlib.metadata import version

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import MarkdownViewer, Static

from ..config import user_config_path

# FIXME: big potion of this message needs to be in sink
#        with the bindings -> generate it automatically


HELP = f"""
# F2 Commander {version('f2-commander')}

> Presse any key to close this panel

## Usage

### Interface

 - `Tab`: switch focus between the left and right panels
 - `Ctrl+p`: open the command palette
 - `Ctrl+w`: swap the panels
 - `Ctrl+s`: open the same location in the other panel
 - `?`: show this help
 - `q`: quit the application
 - Keys shown in the footer execute the indicated actions

### Navigation

 - `j`/`k` and `up`/`down`: navigate the list up and down one entry at a time
 - `g`: navigate to the top of the list
 - `G`: navigate to the bottom of the list
 - `Ctrl+f`/`Ctrl+b`, `Ctrl+d`/`Ctrl+u`, `Page Up`/`Page Down`: paginate the list
 - `Enter`: enter the directory or run the default program associated with a
    file type under cursor
 - `Backspace` (or `Enter` on the `..`): navigate up in a directory tree
 - `b`: go to a bookmarked location (see also "Bookmarks configuration" below)
 - `Ctrl+g`: enter a path to jump to
 - `/`: incremental fuzzy search in the list
 - `R`: refresh the file listing
 - `o`: open the current location in the default OS file manager

### Controlling the displayed items

 - `h`: show/hide hidden files
 - `n`/`N`: order the entries by name
 - `s`/`S`: order the entries by size
 - `t`/`T`: order the entries by last modification time
 - `f`: filter the displayed entries with a glob expression
 - `Ctrl+Space`: calculate the size of the directory under cursor

### File and directory manipulation

Most tasks for file and directory manipulation are available in the footer menu.
More tasks are available in the Command Palette (`Ctrl+p`).

According key bindings use mnemonics for the actions:

  - `c`: copy
  - `m`: move
  - etc.

Few exceptions are:

  - `D`: delete (requires upper case `D` to avoid accidental deletions)

Some alternative actions are available with `Shift` key:

  - `Shift-M`: rename a file or directory in place

### Multiple file and directory selection

Some actions, such as copy, move and delete, can be performed on multiple entries.

 - `Space` or `Shift`+`j`/`k`/`up`/`down`: select/unselect an entry under the cursor
 - `-`: clear selection
 - `+`: select all displayed entries
 - `*`: invert selection

### Shell

 - `x` starts (forks) a subprocess with a new shell in the current location.
   Quit the shell to return back to the F2 Commander (e.g., `Ctrl+d` or type and
   execute `exit`).

### Remote file systems (FTP, S3, etc.)

Remote file systems support is in "preview" mode. Most functionality is available,
but bugs are possible.

To connect to a remote file system you may need to **install additional packages**
that are indicated in the "Connect" dialog upon selecting a protocol.

For example, if you installed F2 Commander with `pipx`, and you want to connect
to an S3 bucket, you need to install the `s3fs` package:

    pipx inject f2-commander s3fs

"Connect" dialog is in its "alpha" version, exposing the underlying connector
configuration in a very generic way. Refer to the documentation of the installed
additional packages for more information.

 - `Ctrl+t`: connect to a remote file system

### Remote file systems bookmarks

It is possible to persist a connection for a remote file system, to quickly
reconnect to it without using the connection dialog. See the "Remote file systems"
section in the "Configuration" below.

### Extracting an archive or a compressed file

F2 Comamnder can read and extract archives and compressed files supported by
`libarchive`. A non-exhaustive list includes: ZIP, TAR, XAR, LHA/LZH, ISO 0660
(optical disc files), cpio, mtree, shar, ar, pax, RAR, MS CAB, 7-Zip, WARC, and more.
See https://github.com/libarchive/libarchive for more information.

To view and extract files from from an archive, open it (`Enter`) and copy the files
from it (`c`).

### Creating an archive

To create an archive, select one or multiple files and directories, and run the
"Create an archive" action from the Command Palette (`Ctrl+p`).

Target file extension determines an archival and a compression format. Following
extensions are recognized: `.zip`, `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tbz2`,
`.tar.xz`, `.txz`, `.7z`, `.ar`, `.cpio`, `.warc`.

### Panels

F2 Commander comes with these panel types:

 - Files: default panel type, for file system discovery and manipulation
 - Preview: shows excerpts of the text files selected in the (Files) other panel
 - Help: also invoked with `?` binding, a user manual (this one)

Use `Ctrl+e` and `Ctrl+r` to change the type of the panel on the left and right
respectively.

### Options

These toggles can be found in Command Palette:

 - Show directories first, on/off
 - Case-sensitive name ordering, on/off

### Themes (colors)

To change the theme, run the "Change theme" command from the Command Palette.

Themes are built-in and are not customizable in this version of the application.

## Configuration

Your configuration file is:

    {str(user_config_path())}

You can use "Show the configuration directory" command from the Command Palette.

Configuration file is a simple list of key-value pairs, similar to how variables are
declared in Bash. The syntax is that of
`.env` files (see https://saurabh-kumar.com/python-dotenv/#file-format).
Allowed values are Python primitives: strings, numbers, boolean `True` or `False`
(capitalized) and collection of these values (lists, dicts). Values can be quoted.

A deafult configuration is provided with the application.

The application may write to the configuration file (e.g., when you change the
settings within the application itself), but will preserve all other content and
formatting.

### Bookmarks

Bookmarks can be defined under the `bookmarks` key as a list of paths. Every path and
the value itself must be quoted. For example:

    bookmarks = "[
      '~',
      '~/Documents',
      '~/Downloads',
      '~/Pictures',
      '~/Videos',
      '~/Music',
    ]"

By default, bookmarks are set to the typical desktop locations, similar to the example.

### Remote file systems

Connection configuration for remote file systems can be persisted and accessed
from the "Bookmarks" dialog.

Connection configuration is defined under `file_systems` key, as a list of connection
objects. Every connection object is a set of key-value pairs, with following keys:

 - `'display_name'`: a title that will be shown in the bookmarks list
 - `'protocol'`: a name of the protocol recognized by fsspec
 - other keys are considered to be fsspec `storage_options`
   (see https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.filesystem)

Refer to the documentation of the installed additional packages for more information
about the remote file system configuration.

For example, to connect to an ADLS Gen2 storage account:

    file_systems = "[
      {{'display_name': 'My BLOB storage', 'protocol': 'abfs', 'account_name': 'myaccount', 'account_key': 'mykey'}},
    ]"

To connect to a remote file system you may need to install additional packages that
provide `fsspec` implementations for the desired protocol. To find the name of the
package, if it is missing, use the "Connect" dialog (`Ctrl+t`).

For example, if you installed F2 Commander with `pipx`, and you want to connect
to an S3 bucket, you need to install the `s3fs` package:

    pipx inject f2-commander s3fs

Remote bookmarks are in "alpha" version, exposing the underlying connector
configuration in a very generic way. Refer to the documentation of the installed
additional packages for more information.

## License

This application is provided "as is", without warranty of any kind.
This application is licensed under the Mozilla Public License, v. 2.0.
You can find a copy of the license at https://mozilla.org/MPL/2.0/
"""  # noqa: E501


class Help(Static):
    def compose(self) -> ComposeResult:
        parent: Widget = self.parent  # type: ignore
        parent.border_title = "Help"
        parent.border_subtitle = None
        yield MarkdownViewer(HELP, show_table_of_contents=False)

    def on_key(self, event) -> None:
        event.stop()
        self.parent.panel_type = "file_list"  # type: ignore
