# CodeCollector

Collect project code files into a single output for AI assistants.

## Installation

### pipx (recommended)

```bash
brew install pipx
pipx ensurepath
pipx install codecollector
```

### From source

```bash
git clone https://github.com/yourusername/codecollector.git
cd codecollector
pipx install -e .
```

## Usage

```bash
# Interactive mode (keyboard navigation)
collect

# Collect current directory recursively
collect .

# Collect specific directory
collect /path/to/project

# Non-recursive mode
collect . -n

# Markdown output
collect . -f markdown

# Custom output file
collect . -o output.txt
```

## Options

| Option                | Description                                                      |
| --------------------- | ---------------------------------------------------------------- |
| `path`                | Directory to collect from (default: interactive mode)            |
| `-n, --non-recursive` | Only current directory, skip subdirectories                      |
| `-o, --output`        | Output filename (default: code_collection.txt)                   |
| `-f, --format`        | Output format: `detailed`, `markdown`, `simple`                  |
| `-i, --interactive`   | Force interactive mode                                           |
| `--config`            | Path to config file                                              |
| `--init-config`       | Generate default config at `~/.config/codecollector/config.json` |
| `-v, --version`       | Show version                                                     |
| `-h, --help`          | Show help                                                        |

## Configuration

Generate default config:

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
  "output_format": "detailed"
}
```

## Output Formats

| Format     | Description                                  |
| ---------- | -------------------------------------------- |
| `detailed` | Full separators, line counts, and file sizes |
| `markdown` | Fenced code blocks with language hints       |
| `simple`   | Filename headers with raw content            |

## Requirements

- Python 3.8+
- pipx (for installation)

```

```
