"""Configuration management for CodeCollector."""

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, Optional, Set
import json


CONFIG_DIR = Path.home() / ".config" / "codecollector"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir() -> None:
    """Ensure configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


_SET_FIELDS = {"exclude_dirs", "include_extensions", "special_files", "extra_exclude_dirs"}


@dataclass
class CollectorConfig:
    """Configuration for the code collector."""

    root_path: Path
    recursive: bool = True
    output_file: str = "code_collection.md"
    output_dir: Optional[Path] = None

    exclude_dirs: Set[str] = field(default_factory=lambda: {
        "__pycache__", ".git", ".svn", ".hg",
        "node_modules", "venv", ".venv", "env", ".env",
        ".idea", ".vscode", "build", "dist", "target",
        ".eggs", "*.egg-info", ".tox", ".mypy_cache",
        ".pytest_cache", "__pypackages__", ".next",
        ".nuxt", ".output", "coverage", ".coverage",
        "tmp", "temp", "logs",
    })

    extra_exclude_dirs: Set[str] = field(default_factory=set)

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
    max_output_size_mb: float = 2.0
    respect_gitignore: bool = False
    auto_increment_output: bool = True
    write_manifest: bool = True
    show_progress: bool = True
    show_skipped: bool = True

    @property
    def all_exclude_dirs(self) -> Set[str]:
        return self.exclude_dirs | self.extra_exclude_dirs

    @classmethod
    def _normalize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {}
        valid_names = {f.name for f in fields(cls)}

        for key, value in data.items():
            if key not in valid_names:
                continue
            if key in _SET_FIELDS and isinstance(value, list):
                normalized[key] = set(value)
            elif key in ("root_path", "output_dir") and value is not None:
                normalized[key] = Path(value)
            else:
                normalized[key] = value

        return normalized

    @classmethod
    def load_from_file(cls, filepath: str) -> Dict[str, Any]:
        """Load configuration dict from a JSON file."""
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        return cls._normalize_dict(data)

    @classmethod
    def from_sources(
        cls,
        root_path: Path,
        config_file: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> "CollectorConfig":
        """Build config by merging global config, file config, and CLI overrides."""
        merged: Dict[str, Any] = {}

        if CONFIG_FILE.exists():
            merged.update(cls.load_from_file(str(CONFIG_FILE)))

        if config_file:
            merged.update(cls.load_from_file(config_file))

        merged["root_path"] = root_path

        if overrides:
            for key, value in overrides.items():
                if value is not None:
                    if key in _SET_FIELDS and isinstance(value, list):
                        merged[key] = set(value)
                    else:
                        merged[key] = value

        return cls(**cls._normalize_dict(merged))

    def save_to_file(self, filepath: str) -> None:
        """Save configuration to a JSON file."""
        config_dict = {
            "exclude_dirs": sorted(self.exclude_dirs),
            "extra_exclude_dirs": sorted(self.extra_exclude_dirs),
            "include_extensions": sorted(self.include_extensions),
            "max_file_size_mb": self.max_file_size_mb,
            "max_output_size_mb": self.max_output_size_mb,
            "auto_increment_output": self.auto_increment_output,
            "write_manifest": self.write_manifest,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)
