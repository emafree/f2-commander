# Features

This document lists all existing and future features, in detail. See a
[README](../README.md) for a shorter overview. Some features may have bugs, see
the [Validation scenarios and Known bugs](testing.md) for more information.

 - User Interface

   - [x] Two-panel interface
   - [x] Classic footer with common user actions
     - [ ] Contextual footer (changes actions based on context)
     - [ ] Configurable key bindings. "Modern" and "Retro" bindings out of the box.
   - [ ] Menu bar
   - [x] Command Palette
   - [x] Preview panel
     - [x] Text files with syntax highlighting
     - [x] Images (works in [supported terminal emulators](https://github.com/lnqs/textual-image/tree/main?tab=readme-ov-file#supported-terminals))
     - [x] Directory trees
   - [ ] File Info panel
   - [x] Drop to shell (command line) temporarily
         - [ ] A simple one-time command input (e.g., an input box on `X`)
   - [ ] "Modern" and "Retro" color themes, ability to customize colors.
   - [x] Mouse click on an empty space below the file list to switch to that panel.
   - [ ] Welcome screen on the first launch (select theme and key bindgins).
   - [ ] Receive dragged and dropped files
   - [ ] Multiple screens (e.g., open multiple editors, viewers; switch b/w those).
   - [ ] Message line (hints about wrong keys, simple confirmation messages, etc.)

 - Configuration

   - [x] User-level configuration file
   - [ ] Action to edit config file and reload after a confirmation
   - [ ] UI for most common configuration options
     - [ ] Options for user-defined viewer, editor, shell, and default file actions
     - [ ] Enable/disable CWD following the user selection
     - [ ] Enable/disable case sensitivity when ordering by name
     - [ ] List dirs first toggle
     - [ ] Starting directory for each pane (cwd, home, fixed path, or last location)

 - Navigation

   - [x] Basic file and directory info: entry names, human-readable size,
         last modification time, show and follow symlinks, etc.
         - [ ] Highlight broken links
   - [x] Vim-like (up/down j/k g/G ctrl+f/d/b/u) navigation
         - [ ] Mouse scrolling
   - [x] Navigate "up" (with backspace or with the ".." entry)
   - [x] Order entries by name, size, time (last modification time)
         - [ ] Remembers non-default ordering (not by name asc) for directories
               (or, when explicitly saved?)
   - [x] Directory summary in the file listing footer
   - [x] "List dirs first/inline" toggle
   - [x] Ordering by name case sensitivity on/off
   - [x] Quick search: navigate file list by typing in the file names
         - [ ] When scrolling to an item, put in in the middle of the screen
   - [x] Navigate to path (enter path, with auto-completion)
   - [x] Configurable bookmarks. Predefined bookmarks to typical desktop directories
         like Downloads, Documents, etc.
         - [ ] Configurable bookmark hotkeys
   - [ ] "Show the Trash" and "Empty the Trash" actions
   - [x] "Same location" and "Swap panels" actions
   - [ ] CWD follows user selection
   - [ ] Detect external changes and update file listing when possible
   - [x] Open current location in the OS default file manager
   - [ ] Search (like `find` in this dir recursively)
   - [ ] Find in files (text search, in a directory, recursive option)

 - File and directory manipulation

   - [x] Basic operations like copy, move, move to trash, etc.
     - [ ] Handles "Trash" errors (e.g., when no Trash available in a server OS, etc.)
     - [x] Confirmation dialogs and user inputs (destination path, etc.)
     - [ ] Copy/Move to a non-existing dir to `mkdir -p` upon confirmation
     - [ ] Copy same file in same dir to create a copy with a suffix
     - [x] Multiple file selection
           - [x] With spacebar
           - [x] Shift+j/k(up/down) selection
           - [ ] Shows selected files summary (count, total size)
     - [ ] Progress bar for long operations (incl. opening large archives,
           copying, etc.)
     - [ ] Option to delete files (as opposed to moving to trash)
     - [ ] After delete (move to Trash), keep the cursor on an adjacent item
   - [x] View and edit files using user default viewer and editor
         - [ ] File-type view (and preview?) tools (e.g., why not preview
               Parquet files, etc.)
   - [x] "Open" files with a default associated program (e.g., view PDF, etc.)
   - [ ] Run programs (run executable files)
   - [x] Create a new directory / new file
   - [x] "Show/hide hidden files" toggle
   - [ ] Create and modify symlinks, show broken, and other symlink tasks
   - [x] Compute directory size on Ctrl+Space
   - [ ] Context menu in the file list ("right click" / "Cmd+click")

 - "File systems" support

   Remote file systems support is in "preview" mode. Most functionality is available,
   but bugs are possible.

   To connect to a remote file system users need to install additional packages that
   are indicated in the "Connect" dialog upon selecting a protocol.

   Checked below are the file systems that are extensively tested and considered
   stable. Unchecked are those that can be used, but are not tested.

   - [x] "Local" OS file system
   - [ ] Azure Blob Storage, Azure DataLake
   - [ ] AWS S3
   - [ ] GCP GCS
   - [ ] Oracle Cloud Object Storage, OCI Data Lake
   - [ ] OSS (Alibaba Cloud)
   - [ ] IMB Box Content Cloud
   - [ ] DVC
   - [ ] LakeFS
   - [ ] Databricks File System
   - [ ] Git (brows a local Git repository by branch, tag, etc.)
   - [ ] GitHub
   - [ ] HDFS
   - [ ] Hugging Face Hub
   - [ ] Dropbox
   - [ ] Google Drive
   - [ ] FTP/FTPS
   - [ ] SFTP
   - [ ] HTTP/HTTPS
   - [ ] SMB
   - [ ] WebDAV
   - [ ] ... more are possible with plugins ...

   - [ ] Predefined "remote" file systems can be bookmarked
   - [ ] Autoamtically download missing packages (with user confirmation)
   - [ ] User confirmations for actions needing download/upload
   - [ ] Test and document SSHFS

 - Archival and compression support (read, write):

   - [x] All libarchive formats
   - [ ] ZIP update in-place (e.g., edit file)
   - [ ] "Extract here" ("extract all") command palette action

 - Documentation

   - [x] Built-in help
   - [ ] User manual

 - Windows support. You are probably better off with WSL, but some day, maybe...

   - [ ] Test all features in Windows
   - [ ] Then, maybe plan fixes

User experience and app behavior:

 - Dialogs

   - [ ] "Do not ask me again" option in "safe" dialogs (e.g., "Quit" dialog)
   - [ ] Allow "Enter" and "y" keys in "safe" dialogs for confirmation

 - Navigation

   - [x] Save user's choises between restarts (hidden files toggle, dirs first, etc.)
     - [ ] Show current value (on or off) in the Command Palette item description
   - [ ] Consistent cursor positioning
     - [x] ... on the source directory when navigating "up"
     - [ ] ... on the source link when navigating back from symlink
     - [ ] ... on the nearest entry after delete or move
   - [ ] Clicking on list headers changes ordering in according columns
   - [ ] Autocompete in the "Jump to path" input
