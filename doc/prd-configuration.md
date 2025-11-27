# PRD: Configuration and Customization

## Overview
F2 Commander provides extensive configuration options through a JSON configuration file and an in-app configuration dialog. Users can customize display settings, bookmarks, remote connections, startup behavior, and external tools.

## User Stories

### Configuration Access
- As a user, I want to access configuration via Ctrl+Comma
- As a user, I want a command to show the configuration directory
- As a user, I want my configuration saved automatically when I change settings
- As a user, I want to specify a custom config file path with --config flag

### Display Settings
- As a user, I want to control whether directories appear first in listings
- As a user, I want to control whether sorting is case-sensitive
- As a user, I want to toggle hidden file visibility (default: hidden)
- As a user, I want to choose from multiple color themes
- As a user, I want my display preferences preserved across sessions

### Bookmarks
- As a user, I want to define quick-access bookmarks to frequently used directories
- As a user, I want bookmarks to support both local and remote paths
- As a user, I want default bookmarks to common locations (home, documents, downloads, pictures, videos, music)
- As a user, I want to access bookmarks with the 'b' key
- As a user, I want to add new bookmarks to my configuration

### Remote File System Connections
- As a user, I want to preconfigure remote file system connections
- As a user, I want to specify display names for connections
- As a user, I want to store connection parameters (host, credentials, path)
- As a user, I want connections to be available in the connection dialog
- As a user, I want to avoid entering credentials repeatedly

### Startup Behavior
- As a user, I want to control whether the app checks for updates on startup
- As a user, I want to control how often update checks occur
- As a user, I want to accept the license terms once and not see it again
- As a user, I want the app to remember which update version I've been notified about

### External Tool Configuration
- As a user, I want to specify my preferred text editor
- As a user, I want to specify my preferred file viewer
- As a user, I want to specify my preferred shell
- As a user, I want the app to use sensible defaults if I don't configure tools
- As a user, I want to control whether the app asks for confirmation before quitting

### Configuration Discovery
- As a user, I want default configuration generated if none exists
- As a user, I want my configuration file in a standard OS location
- As a user, I want validation errors reported clearly if my config is malformed

## Feature Details

### Configuration File Location
- Platform-specific using platformdirs:
  - Linux: `~/.config/f2commander/config.json`
  - macOS: `~/Library/Application Support/f2commander/config.json`
  - Windows: `%APPDATA%\f2commander\config.json`
- Created automatically on first run with sensible defaults
- Can be overridden with `--config` command line option

### Configuration Structure
```json
{
  "display": {
    "dirs_first": true,
    "order_case_sensitive": true,
    "show_hidden": false,
    "theme": "textual-dark"
  },
  "bookmarks": {
    "paths": ["~", "~/Documents", "~/Downloads", ...]
  },
  "file_systems": [
    {
      "display_name": "Example FTP Server",
      "protocol": "ftp",
      "path": "/",
      "params": {
        "host": "example.com",
        "username": "user",
        "password": "pass"
      }
    }
  ],
  "startup": {
    "license_accepted": false,
    "check_for_updates": true,
    "last_update_check_time": 0,
    "last_update_check_version": "0"
  },
  "system": {
    "ask_before_quit": true,
    "editor": null,
    "viewer": null,
    "shell": null
  }
}
```

### Autosave Feature
- Configuration uses context manager pattern: `with config.autosave()`
- Compares JSON before and after modification
- Writes to disk only if changed
- Used when:
  - Display settings are toggled
  - User accepts license
  - Update check completes
  - Quit confirmation is disabled

### Default Tool Detection
When tools are not configured (null), system attempts to detect:
- **Editor**: $VISUAL, $EDITOR, then common editors (nano, vi, vim, emacs, notepad)
- **Viewer**: $PAGER, then common viewers (less, more, bat, most), falls back to editor
- **Shell**: $SHELL, then common shells (bash, zsh, fish, sh, cmd.exe, powershell)
- **Native Open**: `open` (macOS), `xdg-open` (Linux), `start` (Windows)

### Theme Support
- Uses Textual's built-in theme system
- Available themes: textual-dark, textual-light, and others from Textual
- Theme applied via `self.theme = config.display.theme`
- Theme colors used for file type highlighting

### Legacy Configuration Migration
- Automatically detects old .env-based configuration
- Migrates to new JSON format on first run with new version
- Preserves all previous settings
- Backs up old config as user.env.bak
- Removes old marker files

### Validation
- Uses Pydantic models for configuration validation
- Type checking for all fields
- Clear error messages for invalid configurations
- App refuses to start with malformed config

### Configuration Dialog
- In-app UI for reviewing and modifying settings
- Accessed with Ctrl+Comma or "Configuration" command
- Provides forms for common settings
- Changes are saved via autosave mechanism

### Bookmarks Dialog
- Shows preconfigured bookmarks from config
- Allows navigation to bookmarked locations
- Accessed with 'b' key or "Bookmarks" command
- Supports both local paths and FileSystem objects

### Connection Dialog
- Shows preconfigured remote connections
- Allows manual connection parameter entry
- Accessed with Ctrl+T or "Connect to remote" command
- Connection parameters validated before attempting connection

## Configuration Best Practices

### Storing Credentials
- Config file is plain JSON (no encryption)
- Store credentials only for trusted, non-sensitive systems
- Consider using environment variables or credential managers for production
- Limit file permissions on config file

### Bookmark Organization
- Use tilde (~) for home-relative paths for portability
- Order bookmarks by frequency of use
- Include both local and remote locations
- Use descriptive display names for remote systems

### Tool Configuration
- Leave as null to use auto-detection
- Specify full paths for non-standard installations
- Use command with arguments if needed (e.g., "vim -R" for viewer)
- Test commands in terminal before adding to config

## Non-Goals
- This PRD does not cover encrypted configuration
- This PRD does not cover configuration GUI editor
- This PRD does not cover configuration sync across machines
- This PRD does not cover plugin system or extensibility
