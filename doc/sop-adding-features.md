# SOP: Adding New Features

## Overview
This document describes the standard patterns and procedures for adding new features to F2 Commander. Follow these patterns to maintain consistency with the existing codebase.

## Feature Types

### 1. New Action (Keybinding/Command)
Actions are user-triggered operations (e.g., copy, delete, new command).

### 2. New Widget
Widgets are UI components (e.g., new dialog type, new panel type).

### 3. New File System Operation
Low-level operations on files/directories.

### 4. New Configuration Option
User-configurable settings.

## Adding a New Action

### Step 1: Define the Command
Location: In the appropriate class (F2Commander or FileList)

```python
class F2Commander(App):
    BINDINGS_AND_COMMANDS = [
        # ... existing commands ...
        Command(
            "my_new_feature",
            "My New Feature",
            "Description of what this feature does",
            "ctrl+n",  # Optional keyboard shortcut
        ),
    ]
```

**Command Fields:**
- `action`: Method name (without "action_" prefix)
- `name`: Display name in command palette
- `description`: Help text
- `binding_key`: Keyboard shortcut (optional)

### Step 2: Implement the Action Method
```python
@work
async def action_my_new_feature(self):
    # Get input if needed
    value = await self.push_screen_wait(
        InputDialog("Enter value", btn_ok="OK")
    )
    if value is None:  # User cancelled
        return

    # Perform operation with error handling
    async with error_handler_async(self):
        # Your implementation here
        do_something(value)

    # Refresh UI
    self.active_filelist.update_listing()
```

**Pattern Elements:**
- `@work`: Makes action async, non-blocking
- Dialog for user input (if needed)
- Early return if user cancels
- Error handler context manager
- UI refresh after operation

### Step 3: Add Binding (if needed)
If you want a dedicated key binding in footer:
```python
BINDINGS = [
    # ... existing bindings ...
    Binding("n", "my_new_feature", "NewFeat"),
]
```

**Footer Bindings:** Only add if very commonly used (space is limited).

### Step 4: Add Conditional Logic (if needed)
If action should be disabled in some contexts:
```python
def check_action(self, action, parameters):
    if self.active_filelist and self.active_filelist.node.is_archive:
        if action in ("my_new_feature", "edit", "delete"):
            return None  # Visible but disabled
    return True
```

## Adding a New Dialog

### Step 1: Choose Base Dialog Type
- `StaticDialog`: Message with OK/Cancel
- `StaticDialogR`: Message with OK/Cancel + "Remember" checkbox
- `InputDialog`: Text input
- `SelectDialog`: Choose from list

### Step 2: Create Custom Dialog (if needed)
Location: `f2/widgets/dialogs.py` or new file in `f2/widgets/`

```python
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Button, Static
from textual.containers import Vertical

class MyCustomDialog(ModalScreen[bool]):
    """Dialog description"""

    DEFAULT_CSS = """
    MyCustomDialog {
        align: center middle;
    }
    #dialog-container {
        border: solid $primary;
        width: 60;
        height: auto;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-container"):
            yield Static("Dialog content", id="content")
            yield Button("OK", id="ok", variant="primary")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "ok":
            self.dismiss(True)
        else:
            self.dismiss(False)
```

### Step 3: Use the Dialog
```python
result = await self.push_screen_wait(MyCustomDialog())
if result:
    # User clicked OK
    ...
```

**Async Pattern:**
- `push_screen_wait()` for async actions
- `push_screen(dialog, callback)` for sync callbacks

## Adding a New File Operation

### Step 1: Implement in fs/util.py
Location: `f2/fs/util.py`

```python
def my_operation(fs: AbstractFileSystem, path: str, param: str):
    """
    Description of operation.

    Args:
        fs: The filesystem to operate on
        path: Path to the file/directory
        param: Description of parameter

    Raises:
        FileNotFoundError: If path doesn't exist
        PermissionError: If operation not permitted
    """
    if not fs.exists(path):
        raise FileNotFoundError(f"Path not found: {path}")

    # Implementation using fsspec methods:
    # fs.open(), fs.copy(), fs.move(), fs.rm(), fs.makedirs(), etc.
    ...
```

**Guidelines:**
- Use fsspec AbstractFileSystem methods
- Don't use the Node abstraction (util.py is lower-level)
- Use posixpath for path manipulation
- Raise standard Python exceptions
- Handle both local and remote filesystems

### Step 2: Handle Special Cases
```python
def my_operation(fs, path, param):
    # Check if local filesystem
    if _is_local_fs(fs):
        # Use special local-only features
        send2trash(path)
    else:
        # Generic remote handling
        fs.rm(path)
```

### Step 3: Use in Actions
```python
@work
async def action_my_operation(self):
    node = self.active_filelist.cursor_node

    async with error_handler_async(self):
        my_operation(node.fs, node.path, "param")

    self.active_filelist.update_listing()
```

## Adding a New Configuration Option

### Step 1: Add to Config Model
Location: `f2/config.py`

```python
class MySection(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    my_option: bool = True
    my_string: str = "default value"
    my_number: int = 42
```

Then add to main Config:
```python
class Config(pydantic.BaseModel):
    # ... existing sections ...
    my_section: MySection = MySection()
```

### Step 2: Add Validation (if needed)
```python
from pydantic import field_validator

class MySection(pydantic.BaseModel):
    my_option: str

    @field_validator('my_option')
    def validate_option(cls, v):
        if v not in VALID_OPTIONS:
            raise ValueError(f"Invalid option: {v}")
        return v
```

### Step 3: Use Configuration
**Read value:**
```python
value = self.config.my_section.my_option
```

**Update with autosave:**
```python
with self.config.autosave() as config:
    config.my_section.my_option = new_value
```

### Step 4: Add to Config Dialog (optional)
Location: `f2/widgets/config.py`

Add form fields for editing the new option.

## Adding a New Panel Type

### Step 1: Create Widget
Location: `f2/widgets/my_panel.py`

```python
from textual.widgets import Static
from textual.app import ComposeResult

class MyPanel(Static):
    """Description of panel"""

    def compose(self) -> ComposeResult:
        # Your UI components
        yield ...

    def on_mount(self):
        # Initialization
        ...

    # Optional: respond to other panel selections
    def on_other_panel_selected(self, node: Node):
        # React to file selection in other panel
        ...
```

### Step 2: Register Panel Type
Location: `f2/widgets/panel.py`

```python
from .my_panel import MyPanel

PANEL_TYPES = [
    # ... existing types ...
    PanelType("My Panel", "my_panel", MyPanel),
]
```

### Step 3: Use Panel
Users can now switch to your panel via Ctrl+E/R and selecting it.

## Modifying FileList Behavior

FileList is the core widget that displays and manages file listings. Understanding its architecture is essential for modifications.

### FileList Architecture

**The Two-Stage Pipeline:**

```python
# Stage 1: Build listing (data preparation)
def update_listing(self):
    ls = self.node.list()              # Get files from filesystem
    if self.node.parent:
        up = dataclasses.replace(...)   # Add special UP entry
        ls.insert(0, up)
    self.listing = ls                   # Store in instance
    self._update_table()                # Trigger stage 2

# Stage 2: Render to table (filtering + display)
def _update_table(self):
    self.table.clear()
    for node in self.listing:
        if not self.show_hidden and node.is_hidden:  # FILTERING
            continue
        style = self._row_style(node)
        self.table.add_row(...)          # RENDERING
```

**When to Modify Each Stage:**

| Modification Type | Location | Example |
|-------------------|----------|---------|
| Add/modify entries | `update_listing()` | UP entry creation, virtual entries |
| Filter entries | `_update_table()` | Hidden files, file type filters |
| Change display | `_fmt_*()` methods | Size format, date format, colors |
| Change sorting | `sort_key_*()` methods | Custom sort orders |
| Change selection | `add_selection()` | Selection restrictions |

### Common FileList Modification Points

#### 1. Filtering Logic (`_update_table()` method)

**Current filtering:**
```python
def _update_table(self):
    for node in self.listing:
        if not self.show_hidden and node.is_hidden:
            continue  # Skip hidden files
        # ... render node
```

**Adding new filter:**
```python
def _update_table(self):
    for node in self.listing:
        # Existing filter
        if not self.show_hidden and node.is_hidden:
            continue

        # New filter: Skip files larger than limit
        if self.max_file_size and node.size > self.max_file_size:
            continue

        # ... render node
```

**Important:** Filtering happens during rendering, not during listing creation.

#### 2. Sorting Behavior (`sort_key_*()` methods)

**Sorting system uses sort keys:**
```python
def sort_key_by_name(self, node: Node) -> str:
    # Special case: UP entry always at top
    if node.name == "..":
        return "\u0000" if not self.sort_options.reverse else "\uffff"

    # Normal sorting
    return node.name.lower()
```

**Adding custom sort:**
```python
def sort_key_by_extension(self, node: Node) -> Tuple[str, str]:
    # UP entry handling
    if node.name == "..":
        return ("", "\u0000")

    # Sort by extension, then name
    ext = posixpath.splitext(node.name)[1]
    return (ext, node.name.lower())
```

**Register new sort option:**
```python
Command(
    "order('extension', False)",
    "Order by extension, asc",
    "Order entries by file extension",
    "e",
)
```

#### 3. Display Formatting (`_fmt_*()` methods)

**Formatting methods:**
- `_fmt_name()` - File name display with padding/truncation
- `_fmt_size()` - Size display (bytes, KB, MB, special markers)
- `_fmt_mtime()` - Modification time display
- `_row_style()` - Row styling (bold, dim, colors)

**Example: Custom size display**
```python
def _fmt_size(self, node: Node, style: str) -> Text:
    if node.name == "..":
        return Text("-- UP⇧ --", style=style, justify="center")
    elif node.is_dir:
        return Text("-- DIR --", style=style, justify="center")
    elif node.size > 1_000_000_000:  # > 1GB
        return Text(f"{node.size / 1e9:.1f} GB", style="bold red", justify="right")
    else:
        return Text(naturalsize(node.size), style=style, justify="right")
```

#### 4. Selection Logic (`add_selection()` method)

**Current selection:**
```python
def add_selection(self, node: Node):
    if node == self.node.parent:  # Can't select UP entry
        return
    self._selection.add(node)
```

**Adding selection restriction:**
```python
def add_selection(self, node: Node):
    # Existing: Can't select UP entry
    if node == self.node.parent:
        return

    # New: Can't select files over 1GB
    if node.is_file and node.size > 1_000_000_000:
        self.app.notify("Cannot select files over 1GB", severity="warning")
        return

    self._selection.add(node)
```

### Special Handling for UP Entry

The UP entry (`..`) requires special handling in multiple places. Always check if your modification affects it.

**Locations where UP entry is special:**

1. **Creation** (in `update_listing()` method)
   ```python
   if self.node.parent:
       # UP entry should never be hidden, even if parent dir is hidden
       up = dataclasses.replace(self.node.parent, name="..", is_hidden=False)
       ls.insert(0, up)
   ```

2. **Selection** (in `add_selection()` method)
   ```python
   if node == self.node.parent:  # Can't select UP entry
       return
   ```

3. **Sorting** (in `sort_key_by_name()`, `sort_key_by_size()`, `sort_key_by_mtime()` methods)
   ```python
   if node.name == "..":
       return "\u0000"  # Always sort to top
   ```

4. **Size display** (in `_fmt_size()` method)
   ```python
   if node.name == "..":
       return Text("-- UP⇧ --", style=style, justify="center")
   ```

5. **Statistics** (in `update_listing()` method, directory summary calculation)
   ```python
   total_size = sum(node.size for node in ls if node.name != "..")
   dir_count = sum(1 for node in ls if node.is_dir and node.name != "..")
   ```

**Pattern for UP entry checks:**
- Use `node.name == ".."` when you only have the node
- Use `node == self.node.parent` for identity checks (more reliable)

### Example: Adding a File Type Filter

**Goal:** Only show Python files when filter is active

**Step 1: Add configuration option**
```python
# In f2/config.py
class Display(pydantic.BaseModel):
    # ... existing options ...
    file_type_filter: Optional[str] = None  # e.g., ".py", ".txt"
```

**Step 2: Add reactive property**
```python
# In f2/widgets/filelist.py
class FileList(Static):
    # ... existing reactive properties ...
    file_type_filter: reactive[Optional[str]] = reactive(None, init=False)
```

**Step 3: Add watcher**
```python
def watch_file_type_filter(self, old: Optional[str], new: Optional[str]):
    self.update_listing()
```

**Step 4: Add filtering logic**
```python
def _update_table(self):
    self.table.clear()
    for node in self.listing:
        # Existing hidden filter
        if not self.show_hidden and node.is_hidden:
            continue

        # New file type filter
        if self.file_type_filter and node.is_file:
            if not node.name.endswith(self.file_type_filter):
                continue

        # ... render node
```

**Step 5: Add action to toggle filter**
```python
Command(
    "toggle_py_filter",
    "Show only Python files",
    "Filter to show only .py files",
    "ctrl+p",
)

def action_toggle_py_filter(self):
    if self.active_filelist.file_type_filter == ".py":
        self.active_filelist.file_type_filter = None
    else:
        self.active_filelist.file_type_filter = ".py"
```

### Example: Modifying UP Entry Creation

**Real-world example:** Hidden parent bug fix (see `doc/sop-debugging.md` for full analysis)

**Problem:** UP entry inherited `is_hidden=True` from hidden parent directory, causing it to be filtered out when `show_hidden=False`.

**Solution:** Explicitly set `is_hidden=False` when creating UP entry.

**Location:** `f2/widgets/filelist.py` in `update_listing()` method
```python
if self.node.parent:
    # UP entry should never be hidden, even if parent dir is hidden
    up = dataclasses.replace(self.node.parent, name="..", is_hidden=False)
    ls.insert(0, up)
```

**Why this works:**
- Fix at source (data creation) rather than filtering
- Clear semantic intent: UP is a navigation element, not a file
- No special cases needed in filtering logic
- Maintains immutable Node pattern with `dataclasses.replace()`

**Lesson:** When using `dataclasses.replace()`, explicitly set any fields that should differ from the source object.

### Pitfalls When Modifying FileList

#### ❌ Forgetting UP entry special cases

```python
# Bug: This breaks UP entry selection prevention
def add_selection(self, node: Node):
    # Missing: if node == self.node.parent: return
    self._selection.add(node)
```

**Fix:** Always check if UP entry needs special handling.

#### ❌ Filtering in wrong stage

```python
# Wrong: Filtering during listing creation
def update_listing(self):
    ls = self.node.list()
    ls = [n for n in ls if not n.is_hidden]  # DON'T DO THIS
```

**Fix:** Filter during rendering in `_update_table()`.

#### ❌ Not refreshing both panels

```python
# Bug: Only active panel refreshed
async def action_operation(self):
    await operation()
    self.active_filelist.update_listing()
    # Missing: self.inactive_filelist.update_listing()
```

**Fix:** Refresh both panels if operation affects both.

#### ❌ Mutating listing without triggering reactive update

```python
# Bug: Mutation doesn't trigger watcher
self.listing.append(new_node)
```

**Fix:** Reassign to trigger reactive update
```python
self.listing = self.listing + [new_node]
```

### Testing FileList Modifications

**Use existing test infrastructure:**
```python
from ..f2pilot import run_test

async def test_my_filelist_modification(app, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    async with run_test(app=app, cwd=tmp_path) as (pilot, f2pilot):
        # Test filtering
        app.active_filelist.file_type_filter = ".py"
        assert "test.py" in f2pilot.listing

        # Test it filters out others
        app.active_filelist.file_type_filter = ".txt"
        assert "test.py" not in f2pilot.listing
```

**Check UP entry behavior:**
```python
async def test_up_entry_with_modification(app, tmp_path):
    child = tmp_path / "child"
    child.mkdir()

    async with run_test(app=app, cwd=child) as (pilot, f2pilot):
        # Verify UP entry survives your modification
        assert ".." in f2pilot.listing

        # Verify navigation still works
        await pilot.press("backspace")
        assert str(tmp_path) in f2pilot.panel_title
```

## Adding Widget to FileList

### Step 1: Add to Composition
Location: `f2/widgets/filelist.py`

```python
def compose(self) -> ComposeResult:
    with Vertical():
        yield self.table
        yield self.search_input
        yield MyNewWidget()  # Add your widget
```

### Step 2: Query and Use
```python
def on_mount(self):
    self.my_widget = self.query_one(MyNewWidget)
```

## Code Style Guidelines

### Naming Conventions
- **Actions:** `action_verb_noun` (e.g., `action_copy_file`)
- **Callbacks:** `on_event_name` (e.g., `on_file_selected`)
- **Private methods:** `_method_name` (single underscore)
- **Constants:** `UPPER_CASE` (e.g., `DEFAULT_THEME`)

### Type Hints
Always use type hints:
```python
def my_function(fs: AbstractFileSystem, path: str) -> Optional[Node]:
    ...
```

### Docstrings
Add docstrings for public functions:
```python
def my_function(param: str) -> bool:
    """
    Brief description.

    Longer description if needed.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised
    """
```

### Imports
Follow this order:
```python
# Standard library
import os
from pathlib import Path

# Third-party
from textual.app import App
from fsspec import AbstractFileSystem

# Local
from .config import Config
from .fs.node import Node
```

## Testing New Features

### Unit Tests
Location: `tests/test_my_feature.py`

```python
import pytest
from f2.fs.util import my_operation

def test_my_operation():
    # Arrange
    fs = ...
    path = ...

    # Act
    result = my_operation(fs, path)

    # Assert
    assert result == expected
```

### Integration Tests
```python
async def test_action_integration():
    from f2.app import F2Commander
    from f2.config import Config

    config = Config()
    app = F2Commander(config=config)

    async with app.run_test() as pilot:
        # Simulate user actions
        await pilot.press("ctrl+n")
        await pilot.pause()

        # Verify results
        assert ...
```

### Run Tests
```bash
uv run pytest
uv run pytest tests/test_my_feature.py::test_specific
uv run pytest -v  # Verbose
```

## Checklist for New Features

- [ ] Command added to BINDINGS_AND_COMMANDS (if applicable)
- [ ] Action method implemented with `@work` decorator
- [ ] Error handling with `async with error_handler_async(self)`
- [ ] User input validated (reject invalid input early)
- [ ] UI refreshed after operation
- [ ] Configuration added if needed
- [ ] Autosave used when modifying config
- [ ] Type hints added
- [ ] Docstrings added for public APIs
- [ ] Tests written (unit and/or integration)
- [ ] Manual testing performed
- [ ] Works with both local and remote filesystems (if applicable)
- [ ] Works in both panels
- [ ] Doesn't crash on error
- [ ] Follows existing code style

## Common Pitfalls

### ❌ Forgetting to refresh UI
```python
async with error_handler_async(self):
    delete(node.fs, node.path)
# Missing: self.active_filelist.update_listing()
```

### ❌ Not handling cancellation
```python
value = await self.push_screen_wait(InputDialog("Enter value"))
# Missing: if value is None: return
do_something(value)  # Crashes if user cancelled!
```

### ❌ Using os.path instead of posixpath
```python
import os
path = os.path.join(dir, name)  # Wrong! Breaks on Windows remote paths
```

**Correct:**
```python
import posixpath
path = posixpath.join(dir, name)
```

### ❌ Not using @work for async actions
```python
async def action_my_feature(self):  # Missing @work!
    ...
```

**Correct:**
```python
@work
async def action_my_feature(self):
    ...
```

### ❌ Blocking the UI
```python
@work
async def action_slow_operation(self):
    time.sleep(10)  # Wrong! Blocks UI
```

**Correct:**
```python
@work
async def action_slow_operation(self):
    await asyncio.sleep(10)  # Non-blocking
```

## Getting Help

### Code References
- Similar features: grep for similar action names
- Widget examples: look at existing widgets in `f2/widgets/`
- Dialog examples: `f2/widgets/dialogs.py`
- File operations: `f2/fs/util.py`

### Running in Dev Mode
```bash
uv run textual console  # In one terminal
uv run textual run --dev f2.main:main  # In another
```

Provides live debugging and hot reload.

## References
- Main app: `f2/app.py`
- File list widget: `f2/widgets/filelist.py`
- Dialogs: `f2/widgets/dialogs.py`
- File operations: `f2/fs/util.py`
- Configuration: `f2/config.py`
- Commands: `f2/commands.py`
