# SOP: Working with Nodes

## Overview
The Node abstraction is central to F2 Commander's architecture. This document describes how to work with Nodes effectively, covering common patterns and best practices.

## Node Basics

### What is a Node?
A Node represents a file system entry (file, directory, or symlink) with all its metadata eagerly loaded and cached.

**Location:** `f2/fs/node.py:20`

```python
@dataclass(frozen=True)
class Node:
    # Identity
    fs: AbstractFileSystem
    path: str

    # Cached attributes
    name: str
    size: int
    mtime: float
    is_file: bool
    is_dir: bool
    is_link: bool
    is_hidden: bool
    is_executable: bool
    is_archive: bool
    is_local: bool

    # Parent relationship
    _parent: Optional["Node"] = None
```

### Why Immutable?
- Safe to pass between components
- Can be used in sets and as dict keys
- No accidental state changes
- Clear data flow

**Implications:**
- Cannot modify a Node's attributes
- To "change" a Node, create a new one
- Refreshing requires new Node creation

## Creating Nodes

### From URL
**Use when:** User provides a path/URL string

```python
from f2.fs.node import Node

node = Node.from_url("file:///home/user/docs")
node = Node.from_url("s3://my-bucket/data")
node = Node.from_url("~/Documents")  # Expands ~
```

**Error Handling:**
```python
try:
    node = Node.from_url(user_input)
except ValueError as e:
    # Invalid URL format
    show_error(f"Invalid path: {e}")
```

### From Path + Filesystem
**Use when:** You already have a filesystem object

```python
import fsspec
from f2.fs.node import Node

fs = fsspec.filesystem('s3', key='...', secret='...')
node = Node.from_path(fs, '/bucket/path')
```

### From Pre-Fetched Stat
**Use when:** You have stat info from listing

```python
for stat in fs.ls(path, detail=True):
    node = Node.from_path(
        fs,
        posixpath.join(path, posixpath.basename(stat["name"])),
        stat=stat,
        parent=parent_node
    )
```

**Benefits:**
- Avoids extra stat() call
- More efficient for listings
- Preserves parent relationship

### Current Working Directory
**Use when:** You need a default/starting node

```python
node = Node.cwd()
# Equivalent to: Node.from_url(Path.cwd().as_uri())
```

## Accessing Node Properties

### Identity
```python
fs = node.fs          # AbstractFileSystem
path = node.path      # str: "/absolute/path"
name = node.name      # str: "filename.txt"
```

### File Attributes
```python
size = node.size      # int: bytes
mtime = node.mtime    # float: Unix timestamp

is_file = node.is_file           # bool
is_dir = node.is_dir             # bool
is_link = node.is_link           # bool
is_hidden = node.is_hidden       # bool
is_executable = node.is_executable  # bool
is_archive = node.is_archive     # bool
is_local = node.is_local         # bool
```

### Derived Properties
```python
from datetime import datetime
import humanize

# Format modification time
mtime_str = datetime.fromtimestamp(node.mtime).strftime("%Y-%m-%d %H:%M")

# Human-readable size
size_str = humanize.naturalsize(node.size)

# Full URL
url = str(node)  # Uses fs.unstrip_protocol(path)
```

## Node Relationships

### Parent Node
```python
parent = node.parent  # Optional[Node]

if parent:
    # Navigate up one level
    self.active_filelist.node = parent
```

**How it works:**
1. If `_parent` was provided at creation, returns it
2. Otherwise, computes parent from path
3. Returns None for root

**Example:**
```python
# Archive with explicit parent
archive_node = Node.from_path(archive_fs, "", parent=file_node)
archive_node.parent  # Returns file_node

# Regular filesystem
node = Node.from_path(fs, "/home/user/file.txt")
node.parent  # Returns Node for "/home/user"
```

### Listing Children
```python
children = node.list()  # list[Node]

for child in children:
    print(f"{child.name}: {child.size} bytes")
```

**Requirements:**
- Node must be a directory
- Raises ValueError if not a directory

**Implementation:**
```python
def list(self) -> list["Node"]:
    if not self.is_dir:
        raise ValueError(f"Node is not a directory: {self}")

    return [
        Node.from_path(
            self.fs,
            posixpath.join(self.path, posixpath.basename(stat["name"])),
            stat,
            parent=self,
        )
        for stat in self.fs.ls(self.path, detail=True)
    ]
```

## Node Comparison

### Equality
Nodes are equal if they point to the same file:
```python
node1 == node2  # True if same fs and path

# Examples:
file1 = Node.from_url("file:///tmp/foo")
file2 = Node.from_url("file:///tmp/foo")
file1 == file2  # True

file3 = Node.from_url("file:///tmp/bar")
file1 == file3  # False
```

**Usage in Collections:**
```python
# In sets
selection: set[Node] = {node1, node2}
if node in selection:
    ...

# As dict keys
metadata: dict[Node, dict] = {}
metadata[node] = {"custom": "data"}

# In lists
if node in node_list:
    node_list.remove(node)
```

### Sorting
Nodes don't have natural ordering. Use custom sort keys:
```python
nodes = sorted(children, key=lambda n: n.name)
nodes = sorted(children, key=lambda n: n.size)
nodes = sorted(children, key=lambda n: (not n.is_dir, n.name.lower()))
```

## Common Patterns

### Checking Node Type
```python
if node.is_file:
    # Open, view, edit
    content = node.fs.open(node.path).read()

if node.is_dir:
    # List contents
    children = node.list()

if node.is_archive:
    # Open as filesystem
    archive_fs = open_archive(node.path)
    archive_node = Node.from_path(archive_fs, "", parent=node)
```

### Navigation
```python
# Go up
if node.parent:
    self.active_filelist.node = node.parent

# Go down (into directory)
if child_node.is_dir:
    self.active_filelist.node = child_node

# Go to sibling
siblings = node.parent.list() if node.parent else []
next_node = siblings[siblings.index(node) + 1]
```

### File Operations
```python
from f2.fs.util import copy, move, delete

# Copy
copy(node.fs, node.path, dst_fs, dst_path)

# Move
move(node.fs, node.path, dst_fs, dst_path)

# Delete
delete(node.fs, node.path)
```

### Reading File Contents
```python
# Text file
if node.is_file and is_text_file(node.path):
    with node.fs.open(node.path, 'r') as f:
        content = f.read()

# Binary file
with node.fs.open(node.path, 'rb') as f:
    data = f.read()
```

### Getting Local Path
```python
if node.is_local:
    # Use path directly
    subprocess.run(['editor', node.path])
else:
    # Download first
    tmp_path = tempfile.mktemp()
    node.fs.get(node.path, tmp_path)
    subprocess.run(['editor', tmp_path])
    os.unlink(tmp_path)
```

## FileList Integration

### Current Node
```python
# Get current directory
current = self.active_filelist.node  # Node

# Change directory
self.active_filelist.node = new_node  # Triggers watch_node()
```

**Watch Method:**
When node changes, FileList:
1. Validates it's a directory (or converts to parent)
2. Lists contents
3. Resets selection
4. Updates display

### Cursor Node
```python
# Get file/dir under cursor
cursor = self.active_filelist.cursor_node  # Node

# Operations on cursor node
if cursor.is_file:
    view_file(cursor)
```

### Selection
```python
# Get selected nodes
selected = self.active_filelist.selection  # list[Node]

# Work with selection
for node in selected:
    copy(node.fs, node.path, dst_fs, dst_path)

# Manipulate selection
self.active_filelist.add_selection(node)
self.active_filelist.remove_selection(node)
self.active_filelist.toggle_selection(node)
self.active_filelist.reset_selection()
```

## Advanced Patterns

### Building File Trees
```python
def collect_all_files(node: Node) -> list[Node]:
    """Recursively collect all files under node"""
    result = []

    if node.is_file:
        result.append(node)
    elif node.is_dir:
        for child in node.list():
            result.extend(collect_all_files(child))

    return result
```

### Filtering
```python
def find_by_extension(node: Node, ext: str) -> list[Node]:
    """Find all files with given extension"""
    all_files = collect_all_files(node)
    return [n for n in all_files if n.name.endswith(ext)]
```

### Path Manipulation
```python
import posixpath

# Join paths
child_path = posixpath.join(node.path, "subdir", "file.txt")
child_node = Node.from_path(node.fs, child_path)

# Get directory
dir_path = posixpath.dirname(node.path)
dir_node = Node.from_path(node.fs, dir_path)

# Get basename
name = posixpath.basename(node.path)
```

### Creating New Files/Directories
```python
from f2.fs.util import mkdir, mkfile

# Create directory
new_dir_path = posixpath.join(node.path, "new_dir")
mkdir(node.fs, node.path, "new_dir")
new_dir_node = Node.from_path(node.fs, new_dir_path)

# Create file
new_file_path = posixpath.join(node.path, "new_file.txt")
mkfile(node.fs, node.path, "new_file.txt")
new_file_node = Node.from_path(node.fs, new_file_path)
```

## Testing with Nodes

### Creating Test Nodes
```python
def test_node_creation():
    from fsspec.implementations.memory import MemoryFileSystem

    # Use in-memory filesystem for testing
    fs = MemoryFileSystem()
    fs.mkdir('/test')
    fs.touch('/test/file.txt')

    node = Node.from_path(fs, '/test')
    assert node.is_dir

    children = node.list()
    assert len(children) == 1
    assert children[0].name == 'file.txt'
```

### Mocking Filesystem
```python
@patch('fsspec.filesystem')
def test_node_operations(mock_fs):
    mock_fs.return_value.stat.return_value = {
        'name': '/test/file.txt',
        'size': 100,
        'type': 'file',
    }

    node = Node.from_path(mock_fs.return_value, '/test/file.txt')
    assert node.size == 100
```

## Common Pitfalls

### ❌ Modifying Node Properties
```python
node.size = 200  # Error! Node is frozen
```

**Solution:** Create a new Node or use dataclasses.replace():
```python
from dataclasses import replace
new_node = replace(node, name="..")  # Used for parent dir display
```

### ❌ Not Checking Node Type
```python
children = node.list()  # Crashes if node is a file!
```

**Solution:** Always check:
```python
if node.is_dir:
    children = node.list()
```

### ❌ Using os.path with Node Paths
```python
import os
full_path = os.path.join(node.path, "file")  # Wrong on remote FS
```

**Solution:** Use posixpath:
```python
import posixpath
full_path = posixpath.join(node.path, "file")
```

### ❌ Assuming Local Filesystem
```python
with open(node.path) as f:  # Fails for remote files!
    content = f.read()
```

**Solution:** Use filesystem API:
```python
with node.fs.open(node.path) as f:
    content = f.read()
```

### ❌ Stale Nodes
```python
old_node = self.active_filelist.cursor_node
delete(old_node.fs, old_node.path)
# old_node still references deleted file!
```

**Solution:** Refresh to get new Nodes:
```python
delete(node.fs, node.path)
self.active_filelist.update_listing()  # Creates new Nodes
```

## Best Practices

### DO:
- ✅ Use Node.from_url() for user-provided paths
- ✅ Use Node.from_path() with stat for batch operations
- ✅ Check is_dir before calling .list()
- ✅ Use posixpath for all path operations
- ✅ Use node.fs for file operations, not built-ins
- ✅ Refresh listings after modifying filesystem

### DON'T:
- ❌ Try to modify Node properties
- ❌ Keep references to Nodes after filesystem changes
- ❌ Use os.path or Path for Node paths
- ❌ Call .list() on files
- ❌ Assume all Nodes are local

## References
- Node implementation: `f2/fs/node.py`
- FileList widget: `f2/widgets/filelist.py`
- File operations: `f2/fs/util.py`
- fsspec documentation: https://filesystem-spec.readthedocs.io/
