# Architecture: UI Framework (Textual)

## Overview
F2 Commander is built on Textual, a modern TUI (Text User Interface) framework for Python. This architectural decision enables rich terminal interfaces with reactive components, CSS-like styling, and async operation.

## Key Framework: Textual

### What is Textual?
Textual (https://github.com/textualize/textual) is a Rapid Application Development framework for building sophisticated terminal applications. It provides:
- Reactive, composable widgets
- CSS-like styling system (TCSS)
- Async/await support
- Rich text rendering
- Mouse and keyboard input
- Layout system
- Message passing between components

### Why Textual?
- **Modern Python**: Uses async/await, type hints, modern Python features
- **Rich Integration**: Built by same team as Rich library, seamless integration
- **Declarative UI**: Widget composition with CSS-like styling
- **Active Development**: Well-maintained, growing ecosystem
- **Cross-platform**: Works on Linux, macOS, Windows

## Application Architecture

### Main Application: F2Commander(App)
Location: `f2/app.py:84`

The main application class inherits from `textual.app.App`:
```python
class F2Commander(App):
    CSS_PATH = "tcss/main.tcss"
    BINDINGS = [...]
    COMMANDS = {F2AppCommands}
```

**Responsibilities:**
- Application lifecycle management
- Global keybindings and command palette
- Panel management (swap, change type)
- Coordinating file operations across panels
- Managing screens and dialogs
- Configuration integration
- Theme management

### Reactive Properties
Textual's reactive system drives state management:
```python
show_hidden = reactive(False, init=False)
dirs_first = reactive(False, init=False)
order_case_sensitive = reactive(False, init=False)
swapped = reactive(False, init=False)
```

**Watch Methods:**
- `watch_show_hidden()`: Propagates to both panels, saves to config
- `watch_dirs_first()`: Updates both panels, saves to config
- `watch_swapped()`: Reorders panel container

## Widget Hierarchy

### Panel Container Structure
```
F2Commander (App)
├── Horizontal (panels_container)
│   ├── Panel(id="left")
│   │   └── [FileList | Preview | Help]
│   └── Panel(id="right")
│       └── [FileList | Preview | Help]
└── Footer
```

### Panel Widget
Location: `f2/widgets/panel.py:30`

Dynamic container that can host different widget types:
```python
class Panel(Static):
    panel_type = reactive("file_list", recompose=True)

    def compose(self) -> ComposeResult:
        yield PANEL_CLASSES[self.panel_type]()
```

**Panel Types:**
- `file_list`: FileList widget (file browser)
- `preview`: Preview widget (file/directory preview)
- `help`: Help widget (documentation)

**Recomposition:**
- When `panel_type` changes, panel automatically recomposes
- Old widget destroyed, new widget created
- Enables dynamic panel switching

### FileList Widget
Location: `f2/widgets/filelist.py:49`

Core file browsing widget:
```python
class FileList(Static):
    node: reactive[Node] = reactive(Node.cwd())
    cursor_node: reactive[Node] = reactive(Node.cwd())
    active = reactive(False)
    sort_options = reactive(SortOptions("name"), init=False)
```

**Components:**
- `DataTable`: Displays file listing with columns (name, size, mtime)
- `Input`: Search/filter input (hidden by default)
- `Vertical`: Container layout

**Messages:**
- `FileList.Selected`: Posted when cursor moves
- `FileList.Open`: Posted when file is opened (Enter key)

### Preview Widget
Location: `f2/widgets/preview.py:36`

Preview panel for files and directories:
```python
class Preview(Static):
    node = reactive(Node.cwd())

    def compose(self) -> ComposeResult:
        with Horizontal(id="preview-container"):
            yield TextualImage(None, id="image-preview")
            yield Static("", id="text-preview")
```

**Preview Types:**
- Text files: Syntax-highlighted using Rich
- Images: Rendered using textual-image library
- PDFs: First page rendered as image via PyMuPDF
- Directories: Breadth-first tree view

**Update Mechanism:**
- Listens to `on_other_panel_selected()` callback
- Uses `@work(exclusive=True)` for async updates
- Cancels previous preview when cursor moves rapidly

## Dialog System

### Base Dialog Types
Location: `f2/widgets/dialogs.py`

**StaticDialog:**
- Simple message with OK/Cancel buttons
- Supports styles: INFO, WARNING, DANGER
- Returns boolean (confirmed/cancelled)

**StaticDialogR:**
- Extends StaticDialog with "remember" checkbox
- Returns tuple: (confirmed, remember_choice)
- Used for "apply to all" scenarios

**InputDialog:**
- Dialog with text input field
- Returns entered string or None (cancelled)
- Supports default values and selection

**SelectDialog:**
- Dialog with option list
- Returns selected value or None (cancelled)
- Used for panel type selection

### Screen System
Textual's screen system manages dialog stacking:
```python
self.push_screen(dialog, callback)
result = await self.push_screen_wait(dialog)
```

## Styling System (TCSS)

### CSS-Like Styling
Location: `f2/tcss/main.tcss`

Textual uses TCSS (Textual CSS):
```css
FileList {
    border: solid $primary;
}

FileList.focused {
    border: solid $accent;
}
```

**Features:**
- CSS-like selectors (class, id, pseudo-classes)
- Layout properties (display, width, height, padding, margin)
- Border and background styling
- Theme variables ($primary, $accent, etc.)

### Theme System
Textual provides built-in themes:
- `textual-dark` (default)
- `textual-light`
- Custom themes can be added

**Theme Usage:**
```python
self.theme = self.config.display.theme
theme_colors = self.app.theme_  # access active theme
```

## Message Passing

### Textual Messages
Widgets communicate via message passing:
```python
class FileList(Static):
    class Selected(Message):
        def __init__(self, node: Node, control: "FileList"):
            self.node = node
            self._control = control
            super().__init__()
```

**Message Flow:**
1. FileList posts `Selected` message when cursor moves
2. Message bubbles up to parent app
3. App's `on_file_selected()` handler receives it
4. App notifies preview panel via `on_other_panel_selected()`

### Event Handlers
```python
@on(FileList.Selected)
def on_file_selected(self, event: FileList.Selected):
    for c in self.query("Panel > *"):
        if hasattr(c, "on_other_panel_selected"):
            c.on_other_panel_selected(event.node)
```

## Command Palette

### F2AppCommands Provider
Location: `f2/app.py:48`

Custom command provider for Ctrl+P:
```python
class F2AppCommands(Provider):
    def all_commands(self):
        app_commands = [(self.app, cmd) for cmd in self.app.BINDINGS_AND_COMMANDS]
        flist_commands = [(flist, cmd) for cmd in flist.BINDINGS_AND_COMMANDS]
        return app_commands + flist_commands
```

**Features:**
- Fuzzy search through all commands
- Shows keyboard shortcuts
- Executes command actions
- Discovers commands from both app and active widget

### Command Data Structure
Location: `f2/commands.py`

```python
@dataclass
class Command:
    action: str           # Action name to execute
    name: str            # Display name
    description: str     # Help text
    binding_key: Optional[str] = None  # Keyboard shortcut
```

## Async Operations

### Work Decorator
Textual's `@work` decorator enables background tasks:
```python
@work
async def action_copy(self):
    # Long-running file operation
    ...
```

**Features:**
- Runs in background without blocking UI
- `exclusive=True`: Cancel previous operation
- Can be cancelled by user actions

### Subprocess Suspension
For external commands, UI is suspended:
```python
def subprocess_run(self, cmd: str, *args, **kwargs):
    with self.suspend():
        subprocess.run(cmd, ...)
    self.refresh()
```

**Benefits:**
- Terminal returned to normal mode
- External app gets full terminal control
- UI restored automatically

## Key Integrations

### Rich Library
Used for text rendering:
- Syntax highlighting in preview
- Formatted text in dialogs
- Progress indicators
- Styled terminal output

### Textual-Image Library
Location: `f2/widgets/preview.py`

Enables image display in terminal:
```python
from textual_image.widget import Image as TextualImage
from textual_image._terminal import get_cell_size
```

**Features:**
- Multiple terminal graphics protocols
- Automatic scaling
- Cell-based sizing

## Performance Considerations

### Lazy Rendering
- Widgets only render visible portions
- DataTable virtualizes rows
- Preview updates cancelled on rapid navigation

### Debouncing
- Search input uses Textual's built-in debouncing
- File listing updates minimized via reactive watchers

### Memory Management
- Widgets destroyed when panels change type
- Messages don't hold references longer than needed
- Preview content cleared when not displayed

## Testing with Textual

### Development Tools
```bash
uv run textual console  # Debug console
uv run textual run --dev f2.main:main  # Dev mode with hot reload
```

### Pilot Testing
Textual supports programmatic UI testing:
```python
async with app.run_test() as pilot:
    await pilot.press("j", "j", "k")
    assert app.active_filelist.cursor_node.name == "expected"
```

## Non-Standard Textual Usage

### Custom TextAndValue
Location: `f2/widgets/filelist.py:32`

Wrapper around Rich Text that holds associated data:
```python
class TextAndValue(Text):
    def __init__(self, value, text):
        self.value = value
        self.text = text
```

**Purpose:** Store Node object alongside display text in DataTable

## References
- Textual documentation: https://textual.textualize.io/
- Rich documentation: https://rich.readthedocs.io/
- Textual-Image: https://github.com/adamviola/textual-image
