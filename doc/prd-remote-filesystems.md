# PRD: Remote File Systems

## Overview
F2 Commander extends the traditional file manager paradigm by treating "anything that can contain files" as a navigable file system. This enables users to work with remote storage systems (cloud storage, FTP, SFTP, etc.) using the same interface and operations they use for local files.

## Vision
A "file system" in F2 Commander can be:
- A local disk
- Cloud storage (AWS S3, Google Cloud Storage, Azure Data Lake, etc.)
- Network protocols (FTP, FTPS, SFTP, SMB, WebDAV)
- Cloud drives (Dropbox, Google Drive)
- Specialized systems (HDFS, DVC, LakeFS, OCI, OSS)
- Any system supported by fsspec implementations

## User Stories

### Connection Management
- As a user, I want to connect to remote file systems using a connection dialog (Ctrl+T)
- As a user, I want to see preconfigured connections from my config file
- As a user, I want to enter connection parameters manually (protocol, host, credentials, path)
- As a user, I want the connection to be established before I can browse files
- As a user, I want to see the remote protocol and path in the panel title

### Browsing Remote Files
- As a user, I want to navigate remote directories just like local ones
- As a user, I want to see file sizes and modification times from remote systems
- As a user, I want visual indication that I'm browsing a remote location
- As a user, I want to refresh listings to see updated remote state

### Remote File Operations
- As a user, I want to copy files from remote to local (download)
- As a user, I want to copy files from local to remote (upload)
- As a user, I want to move files between remote and local systems
- As a user, I want to delete files on remote systems (permanent deletion, no trash)
- As a user, I want to create directories on remote systems
- As a user, I want to rename files on remote systems

### Cross-Remote Operations
- As a user, I want to be warned when copying between two different remote systems (requires download then upload)
- As a user, I want to confirm before initiating expensive cross-remote transfers
- As a user, I want operations to use temporary local storage as intermediary when needed

### Remote File Viewing/Editing
- As a user, I want to view remote files (with automatic download)
- As a user, I want to edit remote files with my local editor
- As a user, I want to be prompted to upload modified files after editing
- As a user, I want to open remote files with local applications (with download)

### Bookmarks and Quick Access
- As a user, I want to bookmark remote locations for quick access
- As a user, I want to jump to remote paths using "Jump to path" (Ctrl+G)
- As a user, I want to see bookmarked remote systems in the bookmark dialog (b key)

## Feature Details

### Preconfigured Connections
Users can define file systems in their configuration:
```json
{
  "file_systems": [
    {
      "display_name": "My S3 Bucket",
      "protocol": "s3",
      "path": "/my-bucket",
      "params": {
        "key": "...",
        "secret": "..."
      }
    }
  ]
}
```

### Supported Protocols
The system leverages fsspec to support many protocols:
- **Cloud Storage**: s3, gcs, adls, abfs, oci, oss
- **Network**: ftp, ftps, sftp, smb, webdav
- **Cloud Drives**: dropbox, gdrive
- **Specialized**: hdfs, dvc, lakefs
- **Custom**: Any fsspec plugin

### Remote File System Detection
- System detects if a filesystem is remote by checking if "file" is NOT in the protocol list
- Archives are treated specially (can exist on remote systems)
- Local filesystem operations use native OS features (trash, permissions)
- Remote operations use fsspec abstractions

### Download/Upload Workflow
For viewing/editing:
1. User attempts to view/edit remote file
2. System prompts for download confirmation
3. File is downloaded to temporary location
4. Operation is performed locally
5. For edits: system detects changes and prompts for upload
6. Temporary file is cleaned up

### Limitations
- Some operations (like archiving) are only available for local files
- Remote systems lack trash functionality (deletions are permanent)
- Edit operations on remote files require download/upload cycle
- Cross-remote transfers require local temporary storage

## Status
**Remote file systems are in PREVIEW**:
- All features are implemented and available
- Not extensively tested across all protocols
- Connection dialog is functional but basic
- Users are encouraged to preconfigure connections in config files

## Non-Goals
- This PRD does not cover archive file systems (see prd-archives.md)
- This PRD does not cover the UI for connection dialogs (see arch-ui-framework.md)
- This PRD does not cover fsspec implementation details (see arch-filesystem-abstraction.md)
