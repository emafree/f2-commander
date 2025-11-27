# PRD: Archive and Compressed File Support

## Overview
F2 Commander treats archive files (ZIP, TAR, 7-Zip, RAR, etc.) as navigable file systems, allowing users to browse and extract contents without external tools. It also supports creating archives with various compression formats.

## User Stories

### Browsing Archives
- As a user, I want to open archive files by pressing Enter, treating them like directories
- As a user, I want to navigate inside archives using the same keybindings as regular directories
- As a user, I want to see file sizes, dates, and structure within archives
- As a user, I want to see visual indication (highlight/color) for archive files in listings
- As a user, I want to navigate back out of an archive to the parent filesystem

### Extracting from Archives
- As a user, I want to copy files from inside archives to local directories
- As a user, I want to copy entire directories from within archives
- As a user, I want to view text files inside archives with syntax highlighting
- As a user, I want to view images inside archives
- As a user, I want to open files from archives with external applications (automatic extraction)

### Creating Archives
- As a user, I want to archive selected files and directories using a command
- As a user, I want to choose the archive format by specifying the file extension
- As a user, I want to choose compression level by format (.tar.gz, .tar.bz2, .tar.xz, etc.)
- As a user, I want to see supported format suggestions in the dialog
- As a user, I want default archive names suggested based on selection
- As a user, I want to be warned if the output archive already exists

### Supported Formats
- As a user, I want to read from many archive formats: ZIP, TAR (all compression variants), 7-Zip, RAR, LHA/LZH, ISO 9660, CPIO, XAR, PAX, SHAR, AR, CAB, WARC, and more
- As a user, I want to create archives in common formats: .zip, .tar, .tar.gz, .tar.bz2, .tar.xz, .7z, .ar, .xar, .cpio, .pax, .warc

## Feature Details

### Archive Detection
Archives are identified by:
- MIME type matching against known archive types
- File extension matching for formats with ambiguous MIME types
- Verification by attempting to open with appropriate library

### Archive Browsing Implementation
- Archives are opened as read-only filesystems
- Uses ZipFileSystem for .zip files
- Uses LibArchiveFileSystem for all other formats
- Archives can exist on remote filesystems
- Parent relationship is maintained (archive node knows its parent file)

### Archive Creation Workflow
1. User selects files/directories
2. Activates "Archive / compress files" command
3. System suggests format list and default name
4. User enters output path with extension
5. Format and compression determined from extension
6. Archive is created with selected contents
7. File list refreshes and scrolls to new archive

### Extraction Workflow
When copying from archive:
- System normalizes `.get()` behavior across implementations
- Extracts to user-specified destination
- Preserves directory structure
- Handles conflicts like regular copy operations

### Read-Only Nature
Archives in F2 Commander are read-only:
- Move, delete, edit operations are disabled when browsing archives
- Shown as disabled (grayed out) in UI
- System check via `check_action()` prevents execution
- Users must extract, modify externally, and re-archive

### Format Support Details

**Read Support** (via libarchive):
- Standard: TAR, ZIP, CPIO, AR, SHAR, PAX, MTREE
- Compressed: GZIP, BZIP2, XZ, LZIP, LZMA, LZOP, COMPRESS, ZSTD
- Compressed TAR: .tar.gz, .tar.bz2, .tar.xz, .tar.lz, .tar.lzma, .tar.lzo, .tar.Z, .tar.zst
- Special: 7-Zip, RAR, ISO 9660, XAR, LHA/LZH, CAB, WARC, Apple DMG
- Package: RPM, DEB

**Write Support** (via libarchive):
- Formats: gnutar, zip, 7zip, ar_bsd, xar, cpio, pax, warc
- Compression: gzip, bzip2, xz (where applicable)

### Limitations
- Archive creation is only supported for local files
- Cannot modify archives in-place (must extract, modify, re-archive)
- Some exotic formats may be read-only even if libarchive supports writing
- Remote archives require download for modification

## Technical Constraints
- Uses libarchive C library via libarchive-c Python bindings
- Uses Python's zipfile via fsspec's ZipFileSystem
- Requires libarchive to be installed on the system
- Archive operations depend on format support in the installed libarchive version

## Non-Goals
- This PRD does not cover password-protected archives
- This PRD does not cover multi-volume archives
- This PRD does not cover in-place archive modification
- This PRD does not cover archive repair or verification
