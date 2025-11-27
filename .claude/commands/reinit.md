You will be analyzing a source code repository that uses specific non-popular libraries and generating comprehensive markdown documentation files that can be used by Claude Code for future development work.

Source code location: current directory.

Your task is to create a complete documentation set consisting of:

1. **PRD Files (doc/prd-*.md)**: Product Requirements Documents describing the product and its features
2. **Architecture Files (doc/arch-*.md)**: Technical architecture and design documentation
3. **SOP Files (doc/sop-*.md)**: Standard Operating Procedures for implementation patterns
4. **CLAUDE.md**: A summary file referencing all other files with usage guidance

## Detailed Requirements:

### PRD Files (doc/prd-*.md)
- Create one file per major feature or logical product area
- Focus on WHAT the product does, not HOW it's implemented
- Include user stories, feature descriptions, and business requirements
- Keep technical details minimal - focus on functionality and user experience
- Name files descriptively (e.g., doc/prd-user-authentication.md, doc/prd-data-processing.md)

### Architecture Files (doc/arch-*.md)
- Create separate files for distinct architectural aspects found in the code
- Possible aspects: model/data structures, UI/frontend, database, data storage, configuration, API design, etc.
- Focus on HOW the system is designed and structured
- Include key design decisions, patterns used, and relationships between components
- Document the specific non-popular libraries and their roles
- Name files by architectural concern (e.g., doc/arch-data-model.md, doc/arch-ui-framework.md)

### SOP Files (doc/sop-*.md)
- Create files covering recognizable implementation patterns found in the codebase
- Focus on HOW TO implement specific features or follow established patterns
- Include code style guidelines, typical implementation approaches, and best practices
- Cover library-specific usage patterns and conventions
- Name files by implementation area (e.g., doc/sop-error-handling.md, doc/sop-data-validation.md)

### CLAUDE.md File
- Provide a project summary and overview
- List and describe all generated files
- Include guidance on when to reference each file type
- Serve as an entry point for Claude Code to understand the project structure

## Analysis Process:

Use the scratchpad to:
1. Analyze the source code structure and identify major features/components
2. Identify the non-popular libraries being used and their purposes
3. Plan which files to create for each category
4. Outline the key content for each file

<scratchpad>
[Your analysis and planning here]
</scratchpad>

## Output Format:

Generate all files with proper markdown formatting. For each file, include:
- Clear headings and structure
- Relevant code examples where appropriate (especially for SOP files)
- Cross-references to other documentation files when relevant

Present your final documentation set with each file clearly separated and labeled. Your response should contain the complete content of all generated markdown files, ready to be saved and used by Claude Code.
