# OnePaste

[![PyPI](https://img.shields.io/pypi/v/onepaste)](https://pypi.org/project/onepaste/)
[![Python](https://img.shields.io/pypi/pyversions/onepaste)](https://pypi.org/project/onepaste/)
[![License](https://img.shields.io/pypi/l/onepaste)](LICENSE)
[![Publish](https://github.com/emVisible/onepaste/actions/workflows/publish.yml/badge.svg)](https://github.com/emVisible/onepaste/actions/workflows/publish.yml)

Collect project code into LLM-ready Markdown. Select a directory, press Enter, copy and paste.

## Installation

### pipx (recommended)

```bash
brew install pipx
pipx ensurepath
pipx install onepaste

# Optional: exact token counting via tiktoken
pipx install "onepaste[tokens]"
```

Without the `tokens` extra, token counts use a fast characters/4 estimate.

### From source (for development)

```bash
git clone https://github.com/emVisible/onepaste.git
cd onepaste
pipx install -e .
```

### Uninstall / reinstall (for updates & debugging)

```bash
# Uninstall package
onepaste --uninstall

# Uninstall and remove ~/.config/onepaste
onepaste --uninstall --purge-config

# Reinstall editable from local source
cd /path/to/OnePaste
pipx install -e .
```

## Quick Start

```bash
# Interactive: navigate to folder → select "Collect this directory" → Enter
onepaste

# Collect current directory (.gitignore filtering on automatically inside git repos)
onepaste .

# Pipe straight into another tool — no file written
onepaste . --stdout | llm "Explain what this project does"

# Only TypeScript sources, skip tests
onepaste . --include "src/**/*.ts" --exclude-pattern "*.test.ts"
```

Output is a single Markdown file (`code_collection.md`) ready to copy-paste into any LLM.

## Usage

```bash
# Interactive mode
onepaste
onepaste -i                    # force .gitignore filter (deprecated: auto inside git)

# Collect a specific directory
onepaste /path/to/project
onepaste . --no-gitignore      # include gitignored files too

# Non-recursive (current directory only)
onepaste . -n

# Custom output
onepaste . -o my_project.md
onepaste . -d ./collected

# Glob filtering (repeatable)
onepaste . --include "src/**"
onepaste . --include "*.py" --include "*.md"
onepaste . --exclude-pattern "*.min.js" --exclude-pattern "tests/*"

# Split large output (default: 2MB per part)
onepaste . --max-output-size 5

# Preview without writing
onepaste . --dry-run

# Extra exclusions
onepaste . --exclude vendor --exclude tmp
```

## Options

| Option                       | Description                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| `path`                       | Directory to onepaste (default: interactive picker)                                 |
| `-i`                         | Force-enable `.gitignore` filtering (deprecated alias; see below)                  |
| `--no-gitignore`             | Disable `.gitignore` filtering                                                     |
| `-n, --non-recursive`        | Only current directory, skip subdirectories                                        |
| `-o, --output`               | Output filename (default: `code_collection.md`)                                    |
| `-d, --output-dir`           | Output directory (default: current working directory)                              |
| `--max-output-size MB`       | Max output size per file; auto-split when exceeded (default: 2)                    |
| `--exclude DIR`              | Extra directory to exclude (repeatable)                                            |
| `--include GLOB`             | Only onepaste files matching glob (repeatable; overrides extension whitelist)       |
| `--exclude-pattern GLOB`     | Skip files matching glob (repeatable)                                              |
| `--stdout`                   | Write collection to stdout; progress goes to stderr; no file written               |
| `--dry-run`                  | Preview collection without writing output                                          |
| `--force`                    | Overwrite existing output instead of auto-incrementing                             |
| `--config`                   | Path to config file (merged with global config)                                    |
| `--init-config`              | Generate default config at `~/.config/onepaste/config.json`                   |
| `--uninstall`                | Uninstall onepaste via pipx and/or pip                                        |
| `--purge-config`             | Also remove `~/.config/onepaste` (with `--uninstall`)                         |
| `-v, --version`              | Show version                                                                       |
| `-h, --help`                 | Show help                                                                          |

### .gitignore defaults

Inside a git work tree, `.gitignore` filtering is **on by default**. Outside git repos it is off.
Explicit flags win over the default: `-i` forces it on, `--no-gitignore` forces it off.
(`-i` used to be required to enable filtering; it still works but the default has changed.)

### Glob patterns

`--include` / `--exclude-pattern` match against paths relative to the collected root using
[fnmatch](https://docs.python.org/3/library/fnmatch.html) semantics:

| Pattern          | Matches                                             |
| ---------------- | --------------------------------------------------- |
| `*.py`           | any `.py` file anywhere                             |
| `src/**`         | everything under `src/`                             |
| `tests/*`        | files directly inside `tests/`                      |
| `*_test.go`      | Go test files anywhere                              |

When `--include` patterns are given they **replace** the extension whitelist — you get exactly
the matched files (still respecting excludes, size limits and binary detection).

### Token counting

Summaries show total tokens plus per-file counts, with a Top-10 table of the largest files.
With the optional `tokens` extra installed, counts are exact (`tiktoken`, `o200k_base`);
otherwise an estimate (~4 chars/token) is shown and labelled as such.

## Output Format

All output is **detailed Markdown** optimized for LLM consumption:

- Summary with metadata, token totals, top files by tokens, directory tree, and file list
- Each source file as a `###` heading with line count, size, tokens, and a fenced code block
  (fences auto-lengthen so source containing backticks never breaks rendering)
- Auto-split into parts for large projects, each with `Part X of N` header

## Output Behavior

### Auto-increment (no overwrite)

If `code_collection.md` already exists, the next run writes to `code_collection_1.md`, then `_2.md`, etc.

Use `--force` to overwrite.

### Auto-split

When output exceeds the size limit, files are split at source-file boundaries. A manifest JSON is written alongside multi-part output.

`--stdout` never splits; it warns on stderr if the limit would have been exceeded.
It also requires an explicit `path` — the interactive picker would otherwise mix its
own output into the piped stream.

## Configuration

```bash
onepaste --init-config
```

Edit `~/.config/onepaste/config.json`:

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
  "include_patterns": [],
  "exclude_patterns": [],
  "max_file_size_mb": 5.0,
  "max_output_size_mb": 2.0,
  "auto_increment_output": true,
  "write_manifest": true
}
```

`.gitignore` filtering is intentionally not stored in the config file — it resolves
automatically per run (on inside git work trees) unless overridden by `-i` or
`--no-gitignore`.

## Requirements

- Python 3.8+
- pipx (for installation)
