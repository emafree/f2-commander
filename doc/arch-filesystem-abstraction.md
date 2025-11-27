# Architecture: Filesystem Abstraction (fsspec)

## Overview
F2 Commander's ability to treat local, remote, and archive file systems uniformly is powered by fsspec (Filesystem Spec). This abstraction layer enables the same code to work across vastly different storage systems.

## Key Framework: fsspec

### What is fsspec?
fsspec (https://github.com/fsspec/filesystem_spec) is a unified Pythonic interface to local, remote and embedded file systems and bytes storage.

**Core Concept:**
All file systems, regardless of location or protocol, expose the same API:
```python
fs = fsspec.filesystem('s3', anon=False)
fs.ls('/my-bucket')
fs.open('/my-bucket/file.txt', 'r')
fs.cp('/my-bucket/a.txt', '/my-bucket/b.txt')
```

### Why fsspec?
- **Universal API**: Same methods for all file systems
- **Extensive Support**: 50+ file system implementations
- **Protocol Detection**: URL-based automatic protocol selection
- **Pluggable**: Third-party implementations available
- **Production Ready**: Used by Dask, Pandas, Zarr, PyTorch

## File System Protocol Support

### Built-in Protocols
- `file://` - Local file system (default)
- `memory://` - In-memory storage
- `zip://` - ZIP file access
- `tar://` - TAR archive access

### Cloud Storage (with dependencies)
- `s3://` - Amazon S3 (requires s3fs)
- `gcs://` or `gs://` - Google Cloud Storage (requires gcsfs)
- `az://` or `abfs://` - Azure Blob/Data Lake (requires adlfs)
- `oci://` - Oracle Cloud Infrastructure (requires ocifs)
- `oss://` - Alibaba Cloud OSS (requires ossfs)

### Network Protocols (with dependencies)
- `ftp://` - FTP (requires fsspec[ftp])
- `sftp://` or `ssh://` - SFTP/SSH (requires fsspec[sftp])
- `smb://` - Windows SMB/Samba (requires fsspec[smb])
- `webdav://` or `dav://` - WebDAV (requires webdav4)

### Cloud Drives (with dependencies)
- `dropbox://` - Dropbox (requires dropboxdrivefs)
- `gdrive://` - Google Drive (requires gdrivefs)

### Specialized Systems (with dependencies)
- `hdfs://` - Hadoop HDFS (requires fsspec[hdfs])
- `dvc://` - DVC (Data Version Control)
- `lakefs://` - LakeFS

## Node Abstraction

### The Node Class
Location: `f2/fs/node.py:20`

**Design Philosophy:**
The Node is an immutable, eager-loaded representation of a file system entry. It captures all necessary information at creation time and does not maintain open file handles.

```python
@dataclass(frozen=True)
class Node:
    # Identity
    fs: AbstractFileSystem
    path: str

    # Attributes (cached)
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

    # Hierarchy
    _parent: Optional["Node"] = None
```

**Why Immutable?**
- Safe to pass between async operations
- Can be used as dictionary keys or in sets
- No accidental state changes
- Clear data flow

**Why Eager Loading?**
- All metadata fetched once via `fs.stat()`
- No lazy loading surprises
- Predictable performance
- Works well with reactive UI updates

### Node Creation

**From URL:**
```python
node = Node.from_url("s3://my-bucket/path")
node = Node.from_url("file:///home/user/file.txt")
```

Uses `fsspec.core.url_to_fs()` to parse URL and create appropriate filesystem.

**From Path:**
```python
fs = fsspec.filesystem('s3', key='...', secret='...')
node = Node.from_path(fs, '/my-bucket/data')
```

Explicitly provide filesystem and path.

**From stat dict:**
```python
stat = fs.stat('/path')
node = Node.from_path(fs, '/path', stat=stat)
```

Provide pre-fetched stat to avoid extra call.

### Node Operations

**Listing:**
```python
def list(self) -> list["Node"]:
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

**Parent Navigation:**
```python
@property
def parent(self) -> Optional["Node"]:
    if self._parent is not None:
        return self._parent

    parent_path = posixpath.dirname(self.path)
    return Node.from_path(self.fs, parent_path) if parent_path != self.path else None
```

**Equality:**
```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, Node):
        return False
    return self.fs == other.fs and self.path == other.path
```

## Metadata Normalization

### Finding mtime
Location: `f2/fs/util.py:47`

Different fsspec implementations return mtime in different formats:
- `int` or `float`: Unix timestamp
- `datetime`: Python datetime object
- `str`: ISO format or custom format
- `tuple`: 6-element date tuple

```python
def find_mtime(info: dict[str, Any]) -> float:
    # Try multiple field names
    for name in ("mtime", "updated", "LastModified", "last_modified", "modify", "date_time"):
        if name in info:
            fs_mtime = info[name]
            break

    # Convert to float timestamp
    if isinstance(fs_mtime, datetime):
        return fs_mtime.timestamp()
    elif isinstance(fs_mtime, str):
        return datetime.fromisoformat(fs_mtime).timestamp()
    # ... more conversions ...

    # Default: epoch
    return datetime(1970, 1, 1).timestamp()
```

### Detecting File Types
```python
def is_hidden(info: dict[str, Any]) -> bool:
    path = info["name"]
    # Unix-style: starts with dot
    if posixpath.basename(path).startswith("."):
        return True
    # Windows: check FILE_ATTRIBUTE_HIDDEN
    # macOS: check UF_HIDDEN flag
    return _is_local_file_hidden(path)
```

```python
def is_executable(statinfo: dict[str, Any]) -> bool:
    if "mode" not in statinfo:
        return False
    mode = statinfo["mode"]
    return stat.S_ISREG(mode) and bool(mode & stat.S_IXUSR)
```

## File Operations

### Copy Operation
Location: `f2/fs/util.py:210`

**Strategy:** Choose appropriate method based on filesystem types:

```python
def copy(src_fs, src, dst_fs, dst):
    if src_fs == dst_fs:
        # Same filesystem: use native copy
        src_fs.copy(src, dst, recursive=src_fs.isdir(src))

    elif _is_local_fs(src_fs):
        # Upload: local -> remote
        dst_fs.put(src, dst, recursive=src_fs.isdir(src))

    elif _is_local_fs(dst_fs):
        # Download: remote -> local
        src_fs.get(src, dst, recursive=src_fs.isdir(src))

    else:
        # Cross-remote: download then upload via temp
        tmp = tempfile.mkdtemp()
        src_fs.get(src, tmp + "/", recursive=True)
        dst_fs.put(tmp + "/" + basename(src), dst, recursive=True)
        shutil.rmtree(tmp)
```

**Key Methods:**
- `fs.copy(src, dst)` - within same filesystem
- `fs.put(local, remote)` - upload
- `fs.get(remote, local)` - download

### Move Operation
Similar to copy, but:
- Followed by `fs.rm(src, recursive=True)`
- Additional validation for trailing slashes
- Handles destination directory semantics carefully

### Delete Operation
```python
def delete(fs, path):
    if _is_local_fs(fs):
        send2trash(path)  # Safe deletion
    else:
        fs.rm(path, recursive=fs.isdir(path))  # Permanent
```

**Design Decision:** Local files go to trash, remote files are permanently deleted (no universal trash concept for remote systems).

## Archive File Systems

### Custom Archive Implementations
Location: `f2/fs/arch.py:106`

**Problem:** Archive filesystems have different `.get()` semantics:
- Remote FS: `fs.get(remote, local_dir/)` puts file inside directory
- Archive FS: `fs.get(file, target)` expects target to be final filename

**Solution:** Wrapper classes that normalize behavior:

```python
class NormArchFileSystem:
    def get(self, rpath: str, lpath: str, *args, **kwargs):
        if os.path.isdir(lpath):
            lpath = os.path.join(lpath, os.path.basename(rpath))
        super().get(rpath, lpath, *args, **kwargs)

class NormZipFileSystem(NormArchFileSystem, ZipFileSystem):
    pass

class NormLibArchiveFileSystem(NormArchFileSystem, LibArchiveFileSystem):
    pass
```

### Archive Detection
```python
def is_archive(path: str) -> bool:
    _, ext = posixpath.splitext(path)
    mime_type = mimetypes.guess_type(path)[0]
    return (
        mime_type in ZIP_MIMETYPES
        or mime_type in LIBARCHIVE_MIMETYPES
        or ext in LIBARCHIVE_READ_EXTENSIONS
    )
```

### Opening Archives
```python
def open_archive(path: str) -> Optional[AbstractFileSystem]:
    if mimetypes.guess_type(path)[0] in ZIP_MIMETYPES:
        return NormZipFileSystem(path, mode="r")
    else:
        return NormLibArchiveFileSystem(path, mode="r")
```

**Parent Relationship:**
When opening archives, parent node is explicitly provided:
```python
archive_node = Node.from_path(archive_fs, "", parent=file_node)
```

This preserves the link from archive contents back to the archive file.

## Path Handling

### POSIX Paths Everywhere
F2 Commander uses `posixpath` (forward slashes) consistently:
```python
import posixpath  # Not os.path!

posixpath.join(path, name)
posixpath.basename(path)
posixpath.dirname(path)
```

**Rationale:**
- fsspec uses POSIX-style paths internally
- Works correctly for remote systems
- Consistent behavior across platforms
- Windows local paths converted by fsspec

### Home Directory Expansion
```python
from pathlib import Path

if Path(path).is_relative_to(Path.home()):
    display = "~" / Path(path).relative_to(Path.home())
```

Used for display only, not for operations.

## URL Handling

### Protocol Stripping
fsspec has `strip_protocol()` and `unstrip_protocol()` methods:
```python
# Display to user
display_path = fs.unstrip_protocol(path)  # "s3://bucket/file"

# Internal use
bare_path = fs.strip_protocol(url)  # "/bucket/file"
```

### URL Construction
For local files:
```python
Path.cwd().as_uri()  # "file:///absolute/path"
```

For remote files:
```python
str(node)  # calls fs.unstrip_protocol(node.path)
```

## Error Handling

### fsspec Exceptions
fsspec raises standard Python exceptions:
- `FileNotFoundError` - path doesn't exist
- `FileExistsError` - path already exists
- `PermissionError` - insufficient permissions
- `IsADirectoryError` / `NotADirectoryError`

These are caught and displayed via F2's error handler system.

### Protocol-Specific Errors
Some implementations raise protocol-specific errors (e.g., `botocore.exceptions` for S3). These are caught as general `Exception` and displayed.

## Performance Considerations

### Stat Caching
- Node eagerly fetches stat once
- Subsequent operations don't re-stat
- Trade-off: stale data vs. fewer round-trips
- Refresh operation re-creates all Nodes

### Batch Listing
```python
for stat in self.fs.ls(self.path, detail=True):
    # Create nodes from batch stat results
```

Single `ls()` call returns all stats, avoiding N+1 queries.

### Large Directory Handling
- FileList renders only visible rows (DataTable virtualization)
- Preview directory tree limits depth to screen height
- No pagination, but memory efficient rendering

## Extension Points

### Adding New Protocols
To support a new protocol:
1. Install fsspec implementation: `pip install fsspec[protocol]`
2. No code changes needed in F2 Commander
3. Use via URL: `protocol://path`

### Custom Implementations
Can register custom fsspec implementations:
```python
from fsspec import register_implementation
register_implementation("myproto", MyFileSystem)
```

Then use: `myproto://path`

## References
- fsspec documentation: https://filesystem-spec.readthedocs.io/
- fsspec implementations: https://github.com/fsspec
- s3fs: https://s3fs.readthedocs.io/
- gcsfs: https://gcsfs.readthedocs.io/
- adlfs: https://github.com/fsspec/adlfs
