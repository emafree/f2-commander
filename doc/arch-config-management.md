# Architecture: Configuration Management

## Overview
F2 Commander uses Pydantic for configuration validation, platformdirs for OS-standard locations, and a custom autosave mechanism for seamless configuration persistence.

## Key Libraries

### Pydantic
**Purpose:** Type-safe configuration with validation

```python
class Display(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    dirs_first: bool = True
    order_case_sensitive: bool = True
    show_hidden: bool = False
    theme: str = "textual-dark"
```

**Benefits:**
- Type validation at assignment time
- Clear error messages for invalid data
- Default values defined in model
- JSON serialization/deserialization built-in
- No manual validation code

### platformdirs
**Purpose:** OS-standard configuration directory location

```python
import platformdirs

def config_root() -> Path:
    return platformdirs.user_config_path("f2commander")
```

**Locations:**
- Linux: `~/.config/f2commander/`
- macOS: `~/Library/Application Support/f2commander/`
- Windows: `%APPDATA%\f2commander\`

Creates directories automatically if missing.

## Configuration Model Hierarchy

### Top-Level Config
Location: `f2/config.py:76`

```python
class Config(pydantic.BaseModel):
    display: Display = Display()
    bookmarks: Bookmarks = Bookmarks()
    file_systems: list[FileSystem] = [...]
    startup: Startup = Startup()
    system: System = System()
```

### Sub-Models

**Display:** Visual and sorting preferences
```python
class Display(pydantic.BaseModel):
    dirs_first: bool = True
    order_case_sensitive: bool = True
    show_hidden: bool = False
    theme: str = "textual-dark"
```

**Bookmarks:** Quick-access paths
```python
class Bookmarks(pydantic.BaseModel):
    paths: list[str] = ["~", "~/Documents", ...]
```

**FileSystem:** Remote connection presets
```python
class FileSystem(pydantic.BaseModel):
    display_name: str
    protocol: str
    path: str = ""
    params: dict[str, Any]
```

**Startup:** Lifecycle settings
```python
class Startup(pydantic.BaseModel):
    license_accepted: bool = False
    check_for_updates: bool = True
    last_update_check_time: int = 0
    last_update_check_version: str = "0"
```

**System:** External tool configuration
```python
class System(pydantic.BaseModel):
    ask_before_quit: bool = True
    editor: Optional[str] = None
    viewer: Optional[str] = None
    shell: Optional[str] = None
```

## Autosave Mechanism

### ConfigWithAutosave
Location: `f2/config.py:101`

Extends base Config with automatic persistence:
```python
class ConfigWithAutosave(Config):
    _config_path: Path

    @contextmanager
    def autosave(self):
        before = self.model_dump_json(indent=2)
        yield self
        after = self.model_dump_json(indent=2)
        if before != after:
            self._config_path.write_text(after)
```

**How It Works:**
1. Capture JSON snapshot before modification
2. Yield config for modification within context
3. Capture JSON snapshot after modification
4. Write to disk only if changed

**Usage Pattern:**
```python
with self.config.autosave() as config:
    config.display.show_hidden = True
# File automatically saved if value changed
```

**Benefits:**
- Transactional: all changes in block saved together
- Efficient: no write if no change
- Simple: no explicit save calls
- Safe: JSON serialization validates structure

## Configuration Loading

### Entry Point
Location: `f2/config.py:192`

```python
def user_config(config_path: Path):
    if not config_path.exists():
        config_path.write_text(Config().model_dump_json(indent=2))

    try:
        config = Config.model_validate_json(config_path.read_text())
        return ConfigWithAutosave(config_path, config)
    except pydantic.ValidationError as err:
        msg = err.json(include_input=False, include_url=False, include_context=False)
        raise ConfigError(msg)
```

**Process:**
1. Check if config exists, create default if not
2. Load JSON from file
3. Validate with Pydantic
4. Wrap in autosave wrapper
5. Raise clear error if validation fails

### Application Integration
Location: `f2/main.py:31`

```python
def main(config_path, debug):
    try:
        migrate_legacy_config()
        config = user_config(config_path)
        app = F2Commander(config=config, debug=debug)
        app.run()
    except ConfigError as err:
        click.echo("Application could not start because of malformed configuration:")
        click.echo(err)
        sys.exit(1)
```

## Validation and Error Handling

### Validation Timing
- **Load time:** When config file is read
- **Runtime:** When values are assigned (via `validate_assignment=True`)

### Example Validation Error
```json
[
  {
    "type": "bool_type",
    "loc": ["display", "dirs_first"],
    "msg": "Input should be a valid boolean",
    "input": "yes"
  }
]
```

**User-Friendly Presentation:**
- Error type and location clearly identified
- Expected type shown
- Invalid input shown
- User can fix config file manually

### Custom Validation
Can add validators for complex rules:
```python
@pydantic.field_validator('theme')
def validate_theme(cls, v):
    if v not in AVAILABLE_THEMES:
        raise ValueError(f"Invalid theme: {v}")
    return v
```

## Legacy Configuration Migration

### Backward Compatibility
Location: `f2/config.py:122`

Supports migration from old `.env` format:
```python
def migrate_legacy_config():
    config_path = user_config_path()
    if config_path.is_file():
        return  # Already migrated

    dotenv_path = config_root() / "user.env"
    if not dotenv_path.is_file():
        return  # Nothing to migrate

    # Load old format
    legacy_config = dotenv.dotenv_values(dotenv_path)

    # Convert to new format
    config = Config()
    if "dirs_first" in legacy_config:
        config.display.dirs_first = legacy_config["dirs_first"]
    # ... more conversions ...

    # Save new format
    config_path.write_text(config.model_dump_json(indent=2))

    # Backup old format
    dotenv_path.rename(f"{dotenv_path}.bak")
```

**Migration Strategy:**
1. Check if new config exists (skip if so)
2. Check if old config exists (skip if not)
3. Parse old .env format with python-dotenv
4. Map old keys to new structure
5. Save as new JSON format
6. Rename old file to .bak
7. Clean up old marker files

**Handled Once:** Migration runs on every startup but is idempotent.

## Configuration Access Patterns

### Read-Only Access
Direct property access:
```python
theme = self.config.display.theme
editor = self.config.system.editor
bookmarks = self.config.bookmarks.paths
```

### Modifying with Autosave
```python
with self.config.autosave() as config:
    config.startup.license_accepted = True
    config.startup.last_update_check_time = int(time.time())
```

### Reactive Propagation
From app to panels:
```python
def watch_show_hidden(self, old: bool, new: bool):
    if self.left:
        self.left.show_hidden = new
    if self.right:
        self.right.show_hidden = new
    with self.config.autosave() as config:
        config.display.show_hidden = new
```

## Default Values Strategy

### Sensible Defaults
All config fields have defaults that work out-of-box:
- `dirs_first = True` - Directories stand out
- `order_case_sensitive = True` - Predictable sorting
- `show_hidden = False` - Cleaner listings
- `theme = "textual-dark"` - Works in most terminals
- `ask_before_quit = True` - Prevent accidents

### Null for Auto-Detection
External tools default to `None`:
```python
editor: Optional[str] = None
viewer: Optional[str] = None
shell: Optional[str] = None
```

**Interpretation:** `None` means "auto-detect" (see arch-external-tools.md)

### Example Remote Connections
```python
file_systems: list[FileSystem] = [
    FileSystem(
        display_name="Rebex.net Demo FTP server",
        protocol="ftp",
        params={
            "host": "test.rebex.net",
            "username": "demo",
            "password": "password",
        },
    )
]
```

Provides working example for users to learn from.

## Configuration UI

### In-App Configuration Dialog
Location: `f2/widgets/config.py`

**Features:**
- Read current settings
- Modify settings via forms
- Changes saved via autosave
- No manual file editing needed

**Access:** Ctrl+Comma or "Configuration" command

### Direct File Editing
Users can also edit `config.json` directly:
1. Find location: `f2 --config` shows path
2. Edit with any text editor
3. Validation happens on next app start
4. Clear error message if invalid

## Platform-Specific Considerations

### Default Bookmarks
Uses platformdirs to find system directories:
```python
paths: list[str] = [
    "~",
    f"~/{Path(platformdirs.user_documents_dir()).relative_to(Path.home())}",
    f"~/{Path(platformdirs.user_downloads_dir()).relative_to(Path.home())}",
    # ... more ...
]
```

**Result:**
- macOS: `~/Documents`, `~/Downloads`, `~/Pictures`, etc.
- Linux: `~/Documents`, `~/Downloads` (or localized names)
- Windows: `%USERPROFILE%\Documents`, etc.

### Path Separators
Config uses `~` and `/` (POSIX-style):
- Works on all platforms (Python Path handles conversion)
- JSON is portable across systems
- Windows users can use `/` or `\\`

## Security Considerations

### Credentials in Config
Config file is plain JSON:
- No encryption
- Readable by user's account
- Should have restricted permissions

**Best Practices:**
- Use only for non-sensitive connections
- Consider environment variables for production
- Limit file permissions: `chmod 600 config.json`
- Keep config out of version control (add to .gitignore)

### Example Secure Setup
```python
# In config.json - no credentials
{
  "file_systems": [
    {
      "display_name": "My S3",
      "protocol": "s3",
      "params": {
        "key": "${AWS_ACCESS_KEY_ID}",
        "secret": "${AWS_SECRET_ACCESS_KEY}"
      }
    }
  ]
}
```

Then use environment variables (fsspec supports this pattern).

## Testing Configuration

### Validation Testing
```python
def test_config_validation():
    # Valid config
    config = Config.model_validate({
        "display": {"theme": "textual-dark"}
    })

    # Invalid config
    with pytest.raises(pydantic.ValidationError):
        Config.model_validate({
            "display": {"theme": 123}  # Wrong type
        })
```

### Migration Testing
```python
def test_legacy_migration(tmp_path):
    # Create old format
    old_config = tmp_path / "user.env"
    old_config.write_text("theme='textual-light'\n")

    # Run migration
    migrate_legacy_config()

    # Check new format
    new_config = tmp_path / "config.json"
    assert new_config.exists()
    config = json.loads(new_config.read_text())
    assert config["display"]["theme"] == "textual-light"
```

## References
- Pydantic documentation: https://docs.pydantic.dev/
- platformdirs documentation: https://platformdirs.readthedocs.io/
- python-dotenv: https://github.com/theskumar/python-dotenv
