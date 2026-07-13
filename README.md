# CodeCollector

Collect project code into LLM-ready Markdown. Select a directory, press Enter, copy and paste.

## Installation

### pipx (recommended)

```bash
brew install pipx
pipx ensurepath
```

```bash
git clone https://github.com/emVisible/codecollector.git
cd codecollector
pipx install -e .
```

### Uninstall / reinstall (for updates & debugging)

```bash
# Uninstall package
collect --uninstall

# Uninstall and remove ~/.config/codecollector
collect --uninstall --purge-config

# Reinstall editable from local source
cd /path/to/CodeCollector
pipx install -e .
```

## Quick Start

```bash
# Interactive: navigate to folder → select "Collect this directory" → Enter
collect

# Collect current directory
collect .

# Enable filter mode (respect .gitignore)
collect . -i
```

Output is a single Markdown file (`code_collection.md`) ready to copy-paste into any LLM.

## Usage

```bash
# Interactive mode
collect
collect -i                    # with .gitignore filter

# Collect a specific directory
collect /path/to/project
collect . -i                  # with filter mode

# Non-recursive (current directory only)
collect . -n

# Custom output
collect . -o my_project.md
collect . -d ./collected

# Split large output (default: 2MB per part)
collect . --max-output-size 5

# Preview without writing
collect . --dry-run

# Extra exclusions
collect . --exclude vendor --exclude tmp
```

## Options

| Option                 | Description                                                      |
| ---------------------- | ---------------------------------------------------------------- |
| `path`                 | Directory to collect (default: interactive picker)               |
| `-i`                   | Enable filter mode — respect `.gitignore`                        |
| `-n, --non-recursive`  | Only current directory, skip subdirectories                      |
| `-o, --output`         | Output filename (default: `code_collection.md`)                  |
| `-d, --output-dir`     | Output directory (default: current working directory)            |
| `--max-output-size MB` | Max output size per file; auto-split when exceeded (default: 2)  |
| `--exclude DIR`        | Extra directory to exclude (repeatable)                          |
| `--dry-run`            | Preview collection without writing output                        |
| `--force`              | Overwrite existing output instead of auto-incrementing           |
| `--config`             | Path to config file (merged with global config)                  |
| `--init-config`        | Generate default config at `~/.config/codecollector/config.json` |
| `--uninstall`          | Uninstall codecollector via pipx and/or pip                      |
| `--purge-config`       | Also remove `~/.config/codecollector` (with `--uninstall`)       |
| `-v, --version`        | Show version                                                     |
| `-h, --help`           | Show help                                                        |

## Output Format

All output is **detailed Markdown** optimized for LLM consumption:

- Summary with metadata, directory tree, and file list
- Each source file as a `###` heading with line count, size, and fenced code block
- Auto-split into parts for large projects, each with `Part X of N` header

## Output Behavior

### Auto-increment (no overwrite)

If `code_collection.md` already exists, the next run writes to `code_collection_1.md`, then `_2.md`, etc.

Use `--force` to overwrite.

### Auto-split

When output exceeds the size limit, files are split at source-file boundaries. A manifest JSON is written alongside multi-part output.

## Configuration

```bash
collect --init-config
```

Edit `~/.config/codecollector/config.json`:

```json
{
  "exclude_dirs": [
    "node_modules",
    ".git",
    "__pycache__",
    "venv",
    "dist",
    "build"
  ],
  "include_extensions": [".py", ".js", ".ts", ".go", ".rs", ".java"],
  "max_file_size_mb": 5.0,
  "max_output_size_mb": 2.0,
  "auto_increment_output": true,
  "write_manifest": true
}
```

## Requirements

- Python 3.8+
- pipx (for installation)
