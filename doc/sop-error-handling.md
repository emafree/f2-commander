# SOP: Error Handling

## Overview
This document describes the standard patterns for error handling in F2 Commander. The codebase uses decorators and context managers for consistent error presentation to users.

## Error Handling Patterns

### Synchronous Error Handler Decorator
Location: `f2/errors.py`

**Pattern:**
```python
from f2.errors import with_error_handler

@with_error_handler(self)
def callback(result):
    # Code that might raise exceptions
    fs.copy(src, dst)
```

**Usage:**
Wrap callbacks (especially dialog callbacks) to catch and display exceptions.

**Example from app.py:366:**
```python
@with_error_handler(self)
def on_download(result: bool):
    if result:
        _, tmp_file_path = tempfile.mkstemp(...)
        node.fs.get(node.path, tmp_file_path)
        cont_fn(tmp_file_path)
```

**What It Does:**
- Catches any exception in the wrapped function
- Shows error dialog with exception message
- Logs error if debug mode is enabled
- Prevents app crash

### Async Error Handler Context Manager
Location: `f2/errors.py`

**Pattern:**
```python
from f2.errors import error_handler_async

async def some_action(self):
    async with error_handler_async(self):
        # Code that might raise exceptions
        await some_async_operation()
```

**Usage:**
Wrap async operation blocks in actions.

**Example from app.py:571:**
```python
@work
async def action_copy(self):
    # ... get user input ...

    async with error_handler_async(self):
        copy(src_fs, src, dst_fs, dst)

    self.active_filelist.update_listing()
```

**What It Does:**
- Catches exceptions in async context
- Shows error dialog
- Logs error if debug mode enabled
- Allows subsequent cleanup code to run

### When to Use Each

**Use Decorator** (`@with_error_handler`) when:
- Wrapping dialog callbacks
- Wrapping event handlers
- Single function needs protection

**Use Context Manager** (`async with error_handler_async`) when:
- Inside async actions
- Protecting blocks of code
- Need to run cleanup after error

**Use Neither** when:
- Error should propagate to caller
- Custom error handling needed
- Error is expected and handled locally

## Error Dialog Display

### Error Dialog Creation
Errors are shown via StaticDialog:
```python
from f2.widgets.dialogs import StaticDialog, Style

self.push_screen(StaticDialog.error("Title", "Message"))
self.push_screen(StaticDialog.warning("Title", "Message"))
self.push_screen(StaticDialog.info("Title", "Message"))
```

**Styles:**
- `StaticDialog.error()` - Red border, for errors
- `StaticDialog.warning()` - Yellow border, for warnings
- `StaticDialog.info()` - Blue border, for information

### Error Message Format
Keep error messages:
- **Clear:** Describe what went wrong
- **Actionable:** Suggest what user can do
- **Concise:** One or two sentences

**Good:**
```python
StaticDialog.error(
    "Cannot copy file",
    f"Destination file {dst} already exists. Use Move instead."
)
```

**Bad:**
```python
StaticDialog.error(
    "Error",
    str(exception)  # Raw exception text can be cryptic
)
```

## Logging Errors

### Debug Logging
Location: `f2/errors.py`, `f2/debug.py`

When debug mode enabled (`f2 --debug`):
```python
if self.f2_app_debug:
    log_error(exception)
```

**Log Location:**
- `debug.log` in current directory
- Also reported by `log_dir()` function

**Log Format:**
```
2024-10-13 23:20:15,123 - ERROR - Exception in action_copy:
Traceback (most recent call last):
  File "f2/app.py", line 571, in action_copy
    copy(src_fs, src, dst_fs, dst)
  File "f2/fs/util.py", line 215, in copy
    src_fs.copy(src, dst, recursive=True)
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/foo'
```

### Log Uncaught Errors
For errors that escape to main:
```python
from f2.errors import log_uncaught_error

try:
    app.run()
except Exception as ex:
    click.echo("Fatal error in the application:")
    click.echo(ex)
    log_uncaught_error(debug_enabled=debug)
    sys.exit(2)
```

## Common Error Scenarios

### File Operation Errors

**Pattern:**
```python
async with error_handler_async(self):
    copy(src_fs, src_path, dst_fs, dst_path)

self.active_filelist.update_listing()  # Always refresh
```

**Why:**
- File operations can fail for many reasons
- fsspec raises standard exceptions (FileNotFoundError, PermissionError, etc.)
- Always refresh UI to show actual state

### Remote Connection Errors

**Pattern:**
```python
async with error_handler_async(self):
    protocol, path, fs_args = connection_params
    remote_fs = fsspec.filesystem(protocol, **fs_args)
    node = Node.from_path(remote_fs, path or "/")
    self.active_filelist.node = node
```

**Why:**
- Connection can fail (credentials, network, protocol errors)
- fsspec implementations raise various exceptions
- UI should stay functional if connection fails

### Configuration Errors

**Pattern:**
```python
try:
    config = Config.model_validate_json(config_path.read_text())
    return ConfigWithAutosave(config_path, config)
except pydantic.ValidationError as err:
    msg = err.json(include_input=False, include_url=False, include_context=False)
    raise ConfigError(msg)
```

**Why:**
- Config errors are fatal (app can't start)
- Pydantic provides structured error info
- Custom ConfigError signals specific error type

**Handling in main:**
```python
except ConfigError as err:
    click.echo("Application could not start because of malformed configuration:")
    click.echo(err)
    sys.exit(1)
```

## Implementation Examples

### Example 1: Simple Action with Error Handling
```python
@work
async def action_mkdir(self):
    node = self.active_filelist.node

    new_name = await self.push_screen_wait(
        InputDialog("New directory", btn_ok="Create")
    )
    if new_name is None:
        return

    async with error_handler_async(self):
        mkdir(node.fs, node.path, new_name)

    self.active_filelist.update_listing()
    self.active_filelist.scroll_to_entry(new_name)
```

### Example 2: Dialog Callback with Error Handling
```python
def _on_go_to(self, location: Union[str, FileSystem, None]):
    if location is None:
        return

    if isinstance(location, str):
        try:
            node = Node.from_url(location)
            err_msg = f"{location} is not a directory" if not node.is_dir else None
        except Exception as err:
            node = None
            err_msg = str(err)

        if node and node.is_dir:
            self.active_filelist.node = node
        else:
            self.push_screen(
                StaticDialog.info(f"Cannot navigate to {location}", err_msg)
            )
```

**Note:** This uses try/except directly because it needs to check conditions after catching.

### Example 3: Operation with Cleanup
```python
async def _copy_one(self, src_fs, src, dst_fs, dst, many, overwrite):
    # ... conflict detection and confirmation ...

    if not conflict or (conflict and overwrite_one):
        async with error_handler_async(self):
            copy(src_fs, src, dst_fs, dst)

    return overwrite_one if overwrite_mem else None  # Always returns
```

**Note:** Return statement outside error handler ensures it always executes.

## Testing Error Handling

### Testing Error Display
```python
async def test_error_dialog():
    async with app.run_test() as pilot:
        # Trigger error condition
        app.active_filelist.node = Node.from_url("file:///nonexistent")

        # Check error dialog appeared
        await pilot.pause()
        assert "Error" in app.screen.title
        assert "No such file" in app.screen.query_one("#message").content
```

### Testing Error Recovery
```python
async def test_error_recovery():
    async with app.run_test() as pilot:
        # Trigger error
        await pilot.press("c")  # Copy with no selection

        # Dismiss error
        await pilot.press("escape")

        # Verify app still functional
        await pilot.press("j")
        assert app.active_filelist.cursor_node is not None
```

### Mocking for Error Testing
```python
@patch('f2.fs.util.copy')
def test_copy_error_handling(mock_copy):
    mock_copy.side_effect = PermissionError("Access denied")

    app.action_copy()

    # Verify error dialog shown
    assert "Error" in app.screen.title
    assert "Access denied" in str(app.screen.query_one("#message").content)
```

## Best Practices

### DO:
- ✅ Use error handlers for all file operations
- ✅ Always refresh UI after file operations (even if they fail)
- ✅ Show actionable error messages
- ✅ Log errors in debug mode
- ✅ Let user continue using app after error

### DON'T:
- ❌ Let exceptions crash the app
- ❌ Show raw exception text to users
- ❌ Silently ignore errors
- ❌ Log errors in normal mode (privacy concern)
- ❌ Block UI while showing errors

### Error Message Guidelines:
1. **Title:** Brief category ("Cannot copy file", "Connection failed")
2. **Message:** Specific details ("Destination file exists", "Invalid credentials")
3. **Tone:** Neutral and helpful, never blaming user
4. **Length:** 1-3 sentences maximum

### When to Let Errors Propagate:
- Fatal errors that should terminate app
- Configuration errors at startup
- Errors in error handler itself (avoid infinite loops)
- Errors in test code

## Debugging Tips

### Enable Debug Mode:
```bash
f2 --debug
```

### Check Log:
```bash
tail -f debug.log
```

### Add Custom Logging:
```python
from f2.debug import log

log(f"Debug info: {variable}")
```

### Test Error Paths:
```python
# Temporarily inject an error to test handling
if True:  # Set to True for testing
    raise ValueError("Test error")
```

## References
- Error handler implementation: `f2/errors.py`
- Dialog widgets: `f2/widgets/dialogs.py`
- Debug logging: `f2/debug.py`
