# PRD: File Preview Panel

## Overview
F2 Commander provides a preview panel that can display the contents of files and directories without opening them in external applications. This enables quick inspection and navigation.

## User Stories

### Panel Management
- As a user, I want to change either panel to preview mode (Ctrl+E for left, Ctrl+R for right)
- As a user, I want the preview panel to automatically update as I move the cursor in the file list
- As a user, I want to see the previewed item's path in the panel title
- As a user, I want to return a panel to file list mode when I need to

### Text File Preview
- As a user, I want to see syntax-highlighted text files in the preview
- As a user, I want syntax highlighting to match the file type automatically
- As a user, I want to preview the first screenful of text (no scrolling)
- As a user, I want to see files in common text formats: source code, JSON, XML, shell scripts, LaTeX, emails, etc.

### Image Preview
- As a user, I want to see image files displayed in the preview panel
- As a user, I want images scaled to fit the available terminal space
- As a user, I want support for common formats: PNG, JPG, GIF, BMP, WEBP, TIFF, etc.
- As a user, I want to see a message if an image cannot be rendered

### PDF Preview
- As a user, I want to see the first page of PDF files as an image
- As a user, I want the PDF rendered at sufficient quality for readability
- As a user, I want to see a message if a PDF cannot be rendered

### Directory Preview
- As a user, I want to see a tree structure when previewing directories
- As a user, I want the tree to show multiple levels (breadth-first)
- As a user, I want the tree limited to approximately one screenful
- As a user, I want directory names to end with "/" for clarity
- As a user, I want the tree to respect the "show hidden files" setting

### Unsupported Files
- As a user, I want to see a message "Cannot preview: not a text or an image file" for binary files
- As a user, I want to see a message if file reading fails

## Feature Details

### Preview Activation
- Preview panels automatically update when the cursor moves in the active file list
- Only one panel needs to be in preview mode; the other remains as file list
- Preview subscribes to FileList.Selected messages

### Text File Detection
System attempts to detect text files using:
1. `file` command MIME type detection (for local files)
2. Fallback to Python mimetypes by extension
3. Matches against known text MIME types and patterns

Recognized as text:
- MIME types starting with "text/"
- MIME types ending with "+xml" or "+json"
- Specific types: application/json, application/xml, application/x-sh, application/x-sql, application/x-latex, .bat files, .eml files

### Image File Detection
- Based on file extensions supported by PIL/Pillow
- Explicitly excludes PDF (handled separately)
- All formats registered in PIL are supported

### Syntax Highlighting
- Uses Rich library's Syntax module
- Automatically guesses lexer from file path
- Provides colored, formatted output in terminal
- Falls back to plain text if lexer cannot be determined

### Image Rendering
- Uses textual-image library for terminal graphics
- Converts images to terminal-compatible format
- Calculates cell sizes for proper scaling
- Scales down to fit container width or height
- Does not scale up (preserves original size if smaller)

### PDF Rendering
- Uses PyMuPDF (fitz) library
- Renders only the first page
- Applies 2x zoom matrix for improved quality
- Converts to PNG format for display
- Displayed as image using same rendering pipeline

### Directory Tree
- Uses breadth-first traversal for balanced display
- Limits output to terminal height
- Shows paths relative to previewed directory
- Format: "┣ relative/path" for entries
- Respects hidden file settings from main config

### Performance Considerations
- Preview updates use `@work(exclusive=True)` decorator
- Only one preview operation runs at a time
- Previous preview is cancelled when cursor moves quickly
- Text preview reads only first screenful of lines
- Directory tree limits depth based on terminal height

### Error Handling
- UnicodeDecodeError → "Cannot preview: text file cannot be read"
- OSError on image → "Cannot preview: image file cannot be read"
- Exception on PDF → "Cannot preview: PDF file cannot be read"
- Unknown type → "Cannot preview: not a text or an image file"

## Technical Details

### Supported Image Formats
Any format supported by PIL/Pillow, including:
- Raster: PNG, JPEG, GIF, BMP, TIFF, WEBP, ICO
- Others: PPM, PGM, PBM, XBM, PCX, TGA, and more

### Syntax Highlighting Languages
Any language supported by Pygments (via Rich), including:
- Programming: Python, JavaScript, Java, C, C++, Go, Rust, Ruby, PHP
- Markup: HTML, XML, Markdown, LaTeX
- Data: JSON, YAML, TOML, CSV
- Config: INI, .env files
- Many others

## Non-Goals
- This PRD does not cover scrollable preview (preview is always first screen only)
- This PRD does not cover preview of multi-page PDFs
- This PRD does not cover video or audio preview
- This PRD does not cover hex dump for binary files
- This PRD does not cover preview of archive contents (archives are navigable)
