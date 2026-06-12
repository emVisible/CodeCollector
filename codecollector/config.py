"""Configuration management for CodeCollector."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Set
import json


CONFIG_DIR = Path.home() / ".config" / "codecollector"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir() -> None:
    """Ensure configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class CollectorConfig:
    """Configuration for the code collector."""

    root_path: Path
    recursive: bool = True
    output_file: str = "code_collection.txt"
    output_format: str = "detailed"

    exclude_dirs: Set[str] = field(default_factory=lambda: {
        "__pycache__", ".git", ".svn", ".hg",
        "node_modules", "venv", ".venv", "env", ".env",
        ".idea", ".vscode", "build", "dist", "target",
        ".eggs", "*.egg-info", ".tox", ".mypy_cache",
        ".pytest_cache", "__pypackages__", ".next",
        ".nuxt", ".output", "coverage", ".coverage",
        "tmp", "temp", "logs",
    })

    include_extensions: Set[str] = field(default_factory=lambda: {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte",
        ".html", ".css", ".scss", ".less",
        ".java", ".kt", ".go", ".rs", ".rb", ".php", ".swift",
        ".c", ".cpp", ".h", ".hpp",
        ".sh", ".bash", ".zsh",
        ".yml", ".yaml", ".json", ".xml", ".toml",
        ".cfg", ".ini", ".conf", ".env",
        ".md", ".txt", ".rst",
        ".sql", ".graphql",
        "Dockerfile", ".dockerignore",
        "Makefile", ".gitignore",
    })

    special_files: Set[str] = field(default_factory=lambda: {
        "Dockerfile", "Makefile", "Vagrantfile",
        ".gitignore", ".dockerignore", ".env",
        ".editorconfig", ".prettierrc",
    })

    max_file_size_mb: float = 5.0
    show_progress: bool = True
    show_skipped: bool = True

    @classmethod
    def load_from_file(cls, filepath: str) -> "CollectorConfig":
        """Load configuration from a JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        return cls(**data)

    def save_to_file(self, filepath: str) -> None:
        """Save configuration to a JSON file."""
        config_dict = {
            "exclude_dirs": sorted(self.exclude_dirs),
            "include_extensions": sorted(self.include_extensions),
            "max_file_size_mb": self.max_file_size_mb,
            "output_format": self.output_format,
        }
        with open(filepath, "w") as f:
            json.dump(config_dict, f, indent=2)