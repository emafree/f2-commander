# Architecture: External Tools and System Integration

## Overview
F2 Commander integrates with external tools (editors, viewers, shells) and the native OS (file managers, default applications). This architecture document describes the detection, invocation, and integration patterns.

## External Tool Detection

### Auto-Detection Strategy
Location: `f2/shell.py`

When config value is `None`, system attempts auto-detection:

```python
def default_editor() -> Optional[str]:
    # 1. Check environment variables
    if editor := os.getenv("VISUAL"):
        return editor
    if editor := os.getenv("EDITOR"):
        return editor

    # 2. Try common editors
    for editor in ["nano", "vi", "vim", "emacs", "notepad"]:
        if shutil.which(editor):
            return editor

    return None
```

**Priority Order:**
1. Environment variables (user preference)
2. Common tools (availability check via `shutil.which()`)
3. Fallback/combination strategies

### Editor Detection
```python
def default_editor() -> Optional[str]:
    return (
        os.getenv("VISUAL")
        or os.getenv("EDITOR")
        or _first_available(["nano", "vi", "vim", "emacs", "notepad"])
    )
```

**Searched editors:**
- nano (beginner-friendly)
- vi, vim (ubiquitous on Unix)
- emacs (alternative)
- notepad (Windows fallback)

### Viewer Detection
```python
def default_viewer(or_editor: bool = False) -> Optional[str]:
    viewer = (
        os.getenv("PAGER")
        or _first_available(["less", "more", "bat", "most"])
    )
    if viewer:
        return viewer
    if or_editor:
        return default_editor()
    return None
```

**Searched viewers:**
- less (standard Unix pager)
- more (basic pager)
- bat (modern pager with syntax highlighting)
- most (another option)

**Fallback:** Can fall back to editor if viewer not found (for "view" action)

### Shell Detection
```python
def default_shell() -> Optional[str]:
    return (
        os.getenv("SHELL")
        or _first_available(["bash", "zsh", "fish", "sh", "cmd.exe", "powershell"])
    )
```

**Searched shells:**
- bash (most common)
- zsh (macOS default, popular on Linux)
- fish (modern alternative)
- sh (POSIX fallback)
- cmd.exe, powershell (Windows)

### Helper Function
```python
def _first_available(commands: list[str]) -> Optional[str]:
    for cmd in commands:
        if shutil.which(cmd):
            return cmd
    return None
```

Uses `shutil.which()` to check PATH for executable.

## Native OS Integration

### Opening Files with Default Application
```python
def native_open() -> Optional[str]:
    system = platform.system()
    if system == "Darwin":
        return "open"
    elif system == "Linux":
        return "xdg-open"
    elif system == "Windows":
        return "start"
    else:
        return None
```

**Platform Commands:**
- macOS: `open` - opens with default app
- Linux: `xdg-open` - freedesktop standard
- Windows: `start` - Windows command

**Usage:**
```python
self.subprocess_run(native_open(), path)
```

Opens file/directory with system's default application.

## External Tool Invocation

### Subprocess Wrapper
Location: `f2/app.py:309`

```python
def subprocess_run(self, cmd: str, *args, **kwargs) -> Optional[int]:
    err = None
    with self.suspend():
        try:
            full_cmd = shlex.split(cmd)
            full_cmd.extend(args)
            return subprocess.run(full_cmd, **kwargs).returncode
        except Exception as ex:
            err = str(ex)

    if err is not None:
        self.push_screen(StaticDialog.error("Error", err))
        return None
```

**Key Features:**
1. **Suspension:** `with self.suspend()` - returns terminal to normal mode
2. **Command Splitting:** `shlex.split(cmd)` - handles quoted arguments
3. **Error Handling:** Catches exceptions, shows dialog
4. **Return Code:** Returns exit code for caller to handle

**Why Suspend?**
- Textual takes over terminal (alternate screen, raw mode)
- External apps need normal terminal behavior
- Suspension temporarily restores terminal
- UI automatically restored after subprocess

### View Action
Location: `f2/app.py:411`

```python
def action_view(self):
    node = self.active_filelist.cursor_node
    if not node.is_file:
        return

    viewer_cmd = self.config.system.viewer or default_viewer(or_editor=True)
    if viewer_cmd:
        exit_code = self.subprocess_run(viewer_cmd, node.path)
        self.refresh()
        if exit_code:
            msg = f"Viewer exited with an error ({exit_code})"
            self.push_screen(StaticDialog.warning("Warning", msg))
    else:
        self.push_screen(StaticDialog.error("Error", "No viewer found!"))
```

**Flow:**
1. Get configured viewer or auto-detect
2. Suspend UI and run viewer
3. Refresh UI after return
4. Show warning if non-zero exit code

### Edit Action
Location: `f2/app.py:439`

Similar to view, but:
- Uses editor instead of viewer
- Supports upload after editing remote files
- Tracks modification time for change detection

### Shell Action
Location: `f2/app.py:776`

```python
def action_shell(self):
    node = self.active_filelist.node
    cwd = node.path if node.is_local else Path.cwd()

    shell_cmd = self.config.system.shell or default_shell()
    if shell_cmd:
        exit_code = self.subprocess_run(shell_cmd, cwd=cwd)
        self.refresh()
        self.active_filelist.update_listing()
        self.inactive_filelist.update_listing()
        if exit_code != 0:
            msg = f"Shell exited with an error ({exit_code})"
            self.push_screen(StaticDialog.warning("Warning", msg))
    else:
        self.push_screen(StaticDialog.error("Error", "No shell found!"))
```

**Features:**
- Sets CWD to current directory (if local)
- Refreshes both file lists after return (user may have made changes)
- Only shows warning for non-zero exit (not error, shells often return non-zero)

## Remote File Handling

### Download for Editing
When editing remote files:

```python
def _download(self, node, cont_fn):
    @with_error_handler(self)
    def on_download(result: bool):
        if result:
            _, tmp_file_path = tempfile.mkstemp(
                prefix=f"{posixpath.basename(node.path)}.",
                suffix=posixpath.splitext(node.path)[1],
            )
            node.fs.get(node.path, tmp_file_path)
            cont_fn(tmp_file_path)

    if node.is_archive:
        on_download(True)  # Archives need download regardless
    else:
        msg = "The file is not in the local file system. It will be downloaded first. Continue?"
        self.push_screen(StaticDialog("Download?", msg, btn_ok="Yes", btn_cancel="No"), on_download)
```

**Process:**
1. Prompt user for confirmation (unless archive)
2. Create temp file with same extension (important for editor syntax highlighting)
3. Download to temp file
4. Call continuation function with temp path
5. Temp file cleaned up by continuation

### Upload After Editing
```python
def _edit_and_upload(path: str):
    prev_mtime = Path(path).stat().st_mtime
    _edit(path)  # Blocks until editor closes
    new_mtime = Path(path).stat().st_mtime

    if new_mtime > prev_mtime:
        self._upload(node.fs, path, node.path, cont_fn=lambda p: os.unlink(p))
```

**Change Detection:**
1. Record modification time before edit
2. Run editor (blocking)
3. Check modification time after edit
4. Prompt for upload if changed
5. Clean up temp file after upload

### Upload Confirmation
```python
def _upload(self, fs, local_path, remote_path, cont_fn):
    @with_error_handler(self)
    def on_upload(result: bool):
        if result:
            fs.put(local_path, remote_path)
        cont_fn(local_path)  # Cleanup regardless

    self.push_screen(
        StaticDialog("Upload?", "The file was modified. Do you want to upload the new version?", btn_ok="Yes"),
        on_upload,
    )
```

## Configuration Integration

### Explicit Configuration
Users can configure tools in config.json:
```json
{
  "system": {
    "editor": "vim",
    "viewer": "bat",
    "shell": "/bin/zsh"
  }
}
```

### Command with Arguments
```json
{
  "system": {
    "editor": "vim -R",  // Read-only vim
    "viewer": "less -N"   // Less with line numbers
  }
}
```

Arguments are correctly split via `shlex.split()`.

### Full Path
```json
{
  "system": {
    "editor": "/opt/homebrew/bin/nvim"
  }
}
```

Useful for non-standard installation locations.

## Error Handling

### Tool Not Found
```python
if viewer_cmd is not None:
    # ... run tool ...
else:
    self.push_screen(StaticDialog.error("Error", "No viewer found!"))
```

User gets clear message about missing tool.

### Execution Errors
```python
try:
    return subprocess.run(full_cmd, **kwargs).returncode
except Exception as ex:
    err = str(ex)
# Show dialog with exception message
```

Catches any subprocess errors (command not found, permission denied, etc.)

### Non-Zero Exit Codes
```python
if exit_code:  # Non-zero
    msg = f"Viewer exited with an error ({exit_code})"
    self.push_screen(StaticDialog.warning("Warning", msg))
```

Informs user but doesn't prevent UI restoration.

## Platform-Specific Considerations

### Path Handling
- Local files: passed as-is to external tools
- Remote files: downloaded to temp with native path separators
- Archives: extracted entries use native paths

### Terminal Emulator Compatibility
- Suspension should work in most terminal emulators
- Some exotic terminals may not support alternate screen
- Windows terminal needs special handling (cmd.exe vs PowerShell)

### macOS Specifics
- `open` command can open directories in Finder
- `open -a AppName file` to specify application
- Can use `open -t` for TextEdit

### Linux Specifics
- `xdg-open` respects desktop environment settings
- Requires xdg-utils package (usually installed)
- Can use `xdg-mime` to check/set default applications

### Windows Specifics
- `start` is cmd.exe built-in, not external command
- PowerShell uses `Start-Process`
- Path separators automatically handled by Python

## Open in OS File Manager

### Feature Implementation
Location: `f2/widgets/filelist.py:527`

```python
def action_open_in_os_file_manager(self):
    if not self.node.is_local:
        return  # Only for local files

    open_cmd = native_open()
    if open_cmd is not None:
        self.app.subprocess_run(open_cmd, self.node.path)
        self.app.refresh()
```

**Use Cases:**
- User wants to use native file manager features
- Drag and drop files to other apps
- Access context menu options
- Use OS-specific tools

## Testing External Tool Integration

### Mocking Subprocess
```python
@patch('subprocess.run')
def test_view_action(mock_run):
    mock_run.return_value.returncode = 0
    app.action_view()
    mock_run.assert_called_once()
```

### Testing Auto-Detection
```python
@patch('shutil.which')
def test_editor_detection(mock_which):
    mock_which.side_effect = lambda x: "/usr/bin/vim" if x == "vim" else None
    assert default_editor() == "vim"
```

### Testing Platform Detection
```python
@patch('platform.system', return_value='Darwin')
def test_native_open_macos(mock_system):
    assert native_open() == "open"
```

## References
- subprocess documentation: https://docs.python.org/3/library/subprocess.html
- shlex documentation: https://docs.python.org/3/library/shlex.html
- shutil.which: https://docs.python.org/3/library/shutil.html#shutil.which
- xdg-open: https://portland.freedesktop.org/doc/xdg-open.html
