# F2 Commander Documentation Directory

## Purpose

This directory contains comprehensive technical documentation for F2 Commander, designed to help developers understand, maintain, and extend the codebase. The documentation is particularly valuable for AI-assisted development tools like Claude Code.

## Documentation Philosophy

The documentation is organized into three complementary types:

1. **PRD (Product Requirements Documents)**: Focus on **WHAT** - describes features from a user perspective
2. **ARCH (Architecture Documents)**: Focus on **HOW** - explains technical design and implementation
3. **SOP (Standard Operating Procedures)**: Focus on **HOW TO** - provides step-by-step implementation patterns

This three-tier approach ensures you can quickly find the right information whether you're understanding features, learning the architecture, or implementing new code.

## Quick Navigation

### 🎯 I want to understand what F2 Commander does
Start with the **PRD files**:
- Core file operations → [prd-file-management.md](#prd-file-managementmd)
- Remote storage → [prd-remote-filesystems.md](#prd-remote-filesystemsmd)
- Archive handling → [prd-archives.md](#prd-archivesmd)
- File previews → [prd-preview.md](#prd-previewmd)
- Configuration → [prd-configuration.md](#prd-configurationmd)

### 🏗️ I want to understand how it's built
Start with the **ARCH files**:
- UI framework → [arch-ui-framework.md](#arch-ui-frameworkmd)
- Filesystem abstraction → [arch-filesystem-abstraction.md](#arch-filesystem-abstractionmd)
- Configuration system → [arch-config-management.md](#arch-config-managementmd)
- External tools → [arch-external-tools.md](#arch-external-toolsmd)

### 💻 I want to implement a feature
Start with the **SOP files**:
- Adding features → [sop-adding-features.md](#sop-adding-featuresmd)
- Error handling → [sop-error-handling.md](#sop-error-handlingmd)
- Working with Nodes → [sop-working-with-nodes.md](#sop-working-with-nodesmd)

## Document Reference

### Product Requirements Documents (PRD)

#### prd-file-management.md
**What it covers:** Core file management features - navigation, file operations (copy, move, delete, rename), selection, sorting, searching, shell integration.

**When to read:**
- Understanding basic file manager functionality
- Planning enhancements to file operations
- Learning about user interaction patterns
- Understanding selection and batch operations

**Key sections:**
- User stories for all file operations
- Conflict resolution patterns
- Directory size calculation
- File attribute display

---

#### prd-remote-filesystems.md
**What it covers:** Remote filesystem access including cloud storage (S3, GCS, Azure), network protocols (FTP, SFTP, SMB), and specialized systems (HDFS, DVC).

**When to read:**
- Working with remote file system features
- Understanding download/upload workflows
- Adding support for new protocols
- Troubleshooting remote connections

**Key sections:**
- Connection management
- Cross-remote operations
- Preconfigured connections
- Supported protocols list

---

#### prd-archives.md
**What it covers:** Archive file handling - browsing archives as filesystems, extracting contents, creating new archives in various formats (ZIP, TAR, 7-Zip, etc.).

**When to read:**
- Working with archive features
- Understanding archive format support
- Planning archive-related improvements
- Learning about read-only constraints

**Key sections:**
- Archive detection and browsing
- Supported formats (read and write)
- Archive creation workflow
- Extraction patterns

---

#### prd-preview.md
**What it covers:** File preview panel functionality - text files with syntax highlighting, image display, PDF preview, directory tree views.

**When to read:**
- Working on preview features
- Adding new preview types
- Understanding preview rendering
- Troubleshooting preview issues

**Key sections:**
- Preview activation mechanism
- File type detection
- Image and PDF rendering
- Directory tree algorithm

---

#### prd-configuration.md
**What it covers:** Configuration system - display settings, bookmarks, remote connections, startup behavior, external tool configuration.

**When to read:**
- Adding new configuration options
- Understanding config file structure
- Working with bookmarks or connections
- Planning configuration UI changes

**Key sections:**
- Configuration file structure
- Default values strategy
- Configuration UI
- Security considerations

---

### Architecture Documents (ARCH)

#### arch-ui-framework.md
**What it covers:** Textual TUI framework integration - reactive components, widget hierarchy, message passing, styling system (TCSS), async operations.

**When to read:**
- Understanding the UI architecture
- Adding new widgets or dialogs
- Working with reactive properties
- Debugging UI issues
- Learning Textual framework patterns

**Key sections:**
- Application architecture
- Widget hierarchy
- Reactive properties and watchers
- Message passing system
- Command palette implementation
- Async operations with @work

**Key framework: Textual** - Modern TUI framework with React-like reactive components

---

#### arch-filesystem-abstraction.md
**What it covers:** fsspec filesystem abstraction, Node immutable data structure, metadata normalization, file operations across different filesystem types.

**When to read:**
- Understanding filesystem abstraction layer
- Working with Node class
- Adding filesystem operations
- Supporting new protocols
- Debugging filesystem issues

**Key sections:**
- fsspec protocol support
- Node design philosophy
- Metadata normalization across filesystems
- File operation strategies (copy, move, delete)
- Archive filesystem integration
- Path handling with posixpath

**Key framework: fsspec** - Universal filesystem interface for local, remote, and archive access

---

#### arch-config-management.md
**What it covers:** Pydantic-based configuration management, autosave mechanism, platform-specific paths, validation, legacy migration.

**When to read:**
- Adding configuration options
- Understanding autosave pattern
- Working with Pydantic models
- Implementing validation
- Debugging config issues

**Key sections:**
- Configuration model hierarchy
- Autosave context manager pattern
- Configuration loading and validation
- Platform-specific paths with platformdirs
- Legacy migration strategy

**Key frameworks: Pydantic, platformdirs** - Type-safe config with OS-standard locations

---

#### arch-external-tools.md
**What it covers:** External tool integration - editor, viewer, shell detection and invocation, subprocess management, native OS integration.

**When to read:**
- Working with external tools
- Adding new tool integrations
- Understanding auto-detection
- Debugging subprocess issues
- Platform-specific behaviors

**Key sections:**
- Auto-detection strategy
- Subprocess wrapper with UI suspension
- Remote file download/upload for editing
- Platform-specific commands
- Error handling for external tools

---

### Standard Operating Procedures (SOP)

#### sop-error-handling.md
**What it covers:** Standard error handling patterns - decorators, context managers, dialog display, logging, testing error paths.

**When to read:**
- **FIRST THING** when implementing any new feature
- Adding error handling to existing code
- Understanding error display patterns
- Debugging error scenarios

**Key sections:**
- `@with_error_handler` decorator usage
- `async with error_handler_async()` context manager
- Error dialog display patterns
- Debug logging
- Common error scenarios
- Testing error handling

**Critical for:** Every feature implementation

---

#### sop-adding-features.md
**What it covers:** Step-by-step procedures for adding new features - actions, dialogs, file operations, configuration options, widgets, panel types.

**When to read:**
- **Starting any new feature development**
- Adding commands or keybindings
- Creating new dialogs
- Implementing file operations
- Adding configuration options
- Creating new widgets

**Key sections:**
- Adding new actions (complete walkthrough)
- Creating custom dialogs
- Implementing file operations
- Adding configuration options
- Code style guidelines
- Testing strategies
- Feature checklist
- Common pitfalls

**Critical for:** All feature development

---

#### sop-working-with-nodes.md
**What it covers:** Practical guide to the Node abstraction - creation patterns, navigation, operations, FileList integration, testing.

**When to read:**
- Working with file/directory representations
- Implementing any feature that uses Nodes
- Understanding immutability constraints
- Debugging Node-related issues
- Learning filesystem traversal patterns

**Key sections:**
- Node creation methods (from_url, from_path, etc.)
- Accessing properties
- Parent/child relationships
- Common patterns (navigation, operations, reading)
- FileList integration
- Advanced patterns (tree building, filtering)
- Testing with Nodes
- Common pitfalls

**Critical for:** Most feature implementations

---

## How to Use This Documentation

### Scenario: "I'm adding a new file operation"

1. **Understand the feature** (PRD):
   - Read [prd-file-management.md](#prd-file-managementmd) to understand existing operations

2. **Learn the architecture** (ARCH):
   - Read [arch-filesystem-abstraction.md](#arch-filesystem-abstractionmd) § File Operations
   - Understand fsspec patterns and Node usage

3. **Follow implementation patterns** (SOP):
   - Follow [sop-adding-features.md](#sop-adding-featuresmd) § Adding a New File Operation
   - Apply [sop-error-handling.md](#sop-error-handlingmd) patterns
   - Use [sop-working-with-nodes.md](#sop-working-with-nodesmd) for Node manipulation

### Scenario: "I'm fixing a bug in remote file operations"

1. **Understand expected behavior** (PRD):
   - Read [prd-remote-filesystems.md](#prd-remote-filesystemsmd)

2. **Understand implementation** (ARCH):
   - Read [arch-filesystem-abstraction.md](#arch-filesystem-abstractionmd) § Remote File Operations
   - Check Node handling patterns

3. **Check implementation patterns** (SOP):
   - Verify error handling follows [sop-error-handling.md](#sop-error-handlingmd)
   - Check Node usage follows [sop-working-with-nodes.md](#sop-working-with-nodesmd)

### Scenario: "I'm adding a new panel type"

1. **Understand existing panels** (PRD):
   - Read [prd-preview.md](#prd-previewmd) for example panel

2. **Understand UI architecture** (ARCH):
   - Read [arch-ui-framework.md](#arch-ui-frameworkmd) § Panel Widget
   - Understand Textual patterns

3. **Follow implementation guide** (SOP):
   - Follow [sop-adding-features.md](#sop-adding-featuresmd) § Adding a New Panel Type
   - Apply [sop-error-handling.md](#sop-error-handlingmd) patterns

### Scenario: "I'm learning the codebase"

**Day 1 - Feature Understanding:**
- Read all PRD files to understand what F2 Commander does
- Skim through each PRD to get the big picture

**Day 2 - Architecture Understanding:**
- Read [arch-ui-framework.md](#arch-ui-frameworkmd) for UI structure
- Read [arch-filesystem-abstraction.md](#arch-filesystem-abstractionmd) for core abstraction

**Day 3 - Implementation Patterns:**
- Read [sop-adding-features.md](#sop-adding-featuresmd) thoroughly
- Read [sop-error-handling.md](#sop-error-handlingmd)
- Read [sop-working-with-nodes.md](#sop-working-with-nodesmd)

**Day 4+ - Dive Deeper:**
- Read remaining ARCH files as needed
- Start with small feature additions
- Reference SOPs frequently

## Cross-References

Documents are extensively cross-referenced. Look for:
- **"See: [document-name.md]"** - Points to related information
- **"Location: `file.py:123`"** - Points to source code
- **§ Section Name** - References specific sections within documents

## Documentation Maintenance

When modifying code:
- ✅ Update PRD if user-facing behavior changes
- ✅ Update ARCH if architectural patterns change
- ✅ Update SOP if implementation patterns change
- ✅ Keep code examples in sync with actual code
- ✅ Update cross-references if section names change

## External Resources

For library-specific details not covered here, refer to:
- **Textual**: https://textual.textualize.io/
- **fsspec**: https://filesystem-spec.readthedocs.io/
- **Pydantic**: https://docs.pydantic.dev/
- **libarchive-c**: https://github.com/Changaco/python-libarchive-c
- **platformdirs**: https://platformdirs.readthedocs.io/

## Getting Started

**New to the project?** Start here:
1. Read this README
2. Read [../CLAUDE.md](../CLAUDE.md) for project overview
3. Skim all PRD files (30 minutes)
4. Read [sop-adding-features.md](#sop-adding-featuresmd) (critical for development)
5. Set up dev environment following [../README.md](../README.md)

**Ready to code?** Keep these open:
- [sop-adding-features.md](#sop-adding-featuresmd) - Your implementation guide
- [sop-error-handling.md](#sop-error-handlingmd) - Error handling patterns
- [sop-working-with-nodes.md](#sop-working-with-nodesmd) - Node usage patterns

**Need deep understanding?** Reference:
- ARCH files for design decisions
- PRD files for feature specifications

---

**This documentation is optimized for Claude Code and AI-assisted development, providing comprehensive context for understanding and extending F2 Commander.**
