# PRD: File Management Core Features

## Overview
F2 Commander provides comprehensive file management capabilities in a terminal-based orthodox (two-panel) file manager interface. This document describes the core file management features that users interact with daily.

## User Stories

### Basic Navigation
- As a user, I want to browse directories in a two-panel interface so I can easily compare and work with files across different locations
- As a user, I want to use Vi-like keybindings (j/k for up/down, g/G for top/bottom) so I can navigate efficiently without leaving the keyboard home row
- As a user, I want to see ".." as the first entry to navigate to parent directories
- As a user, I want to use backspace to quickly go up one directory level

### File Operations
- As a user, I want to copy files and directories between panels so I can organize my data
- As a user, I want to move files and directories so I can reorganize my file system
- As a user, I want to rename files and directories to keep my data organized
- As a user, I want to delete files (with trash support on local systems) so I can safely remove unwanted data
- As a user, I want to create new files and directories quickly
- As a user, I want confirmation dialogs for destructive operations to prevent accidents

### Selection and Batch Operations
- As a user, I want to select multiple files using Space, Shift+Up/Down keys
- As a user, I want to select all files with + key
- As a user, I want to deselect all with - key
- As a user, I want to invert selection with * key
- As a user, I want visual feedback (highlighting) for selected files
- As a user, I want to perform operations on multiple selected files at once

### File Viewing and Editing
- As a user, I want to view file contents with syntax highlighting for code
- As a user, I want to edit files using my preferred editor
- As a user, I want to open files with their default system applications
- As a user, I want to open the current directory in my system's file manager

### File Information and Display
- As a user, I want to see file size, modification time, and type for each entry
- As a user, I want to toggle visibility of hidden files (starting with .)
- As a user, I want to sort files by name, size, or modification time (ascending or descending)
- As a user, I want directories to optionally appear first in listings
- As a user, I want case-sensitive or case-insensitive sorting options
- As a user, I want visual indicators for file types (directories bold, executables colored, archives highlighted, symlinks underlined)

### Search and Filter
- As a user, I want incremental search with fuzzy matching (/) to quickly find files
- As a user, I want the search to highlight matches as I type
- As a user, I want to exit search with Esc or Enter

### Shell Integration
- As a user, I want to drop to a shell (x key) in the current directory
- As a user, I want to return to the file manager after shell operations
- As a user, I want the file list to refresh after returning from the shell

### Command Palette
- As a user, I want a command palette (Ctrl-P) to discover and execute all available commands
- As a user, I want fuzzy search in the command palette
- As a user, I want to see keyboard shortcuts next to commands

## Feature Details

### Conflict Resolution
When copying or moving files, the system should:
- Detect when destination files already exist
- For files: offer to overwrite or skip
- For directories during copy: offer to merge contents
- For directories during move: disallow merge (explicit design decision)
- When operating on multiple files: offer "remember my choice" option

### Directory Size Calculation
- Users can calculate directory sizes on-demand (Ctrl+Space)
- Calculation happens asynchronously to avoid blocking
- Results are displayed inline in the file list

### File Attributes
The system displays:
- Name (truncated if too long, with "..." indicator)
- Size (human-readable format, or special indicators for directories "--DIR--" and links "--LNK--")
- Modification time (formatted as "MMM DD HH:MM")
- Visual styling based on file type

## Non-Goals
- This PRD does not cover remote file system access (see prd-remote-filesystems.md)
- This PRD does not cover archive handling (see prd-archives.md)
- This PRD does not cover preview functionality (see prd-preview.md)
- This PRD does not cover configuration options (see prd-configuration.md)
