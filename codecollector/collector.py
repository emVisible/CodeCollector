"""File collector module."""

import os
from pathlib import Path
from typing import List, Tuple

from codecollector.config import CollectorConfig


class FileCollector:
    """Collects code files from directories."""

    def __init__(self, config: CollectorConfig):
        self.config = config
        self.collected_files: List[Path] = []
        self.skipped_files: List[Tuple[Path, str]] = []

    def should_collect_file(self, file_path: Path) -> bool:
        """Determine if a file should be collected."""
        if not file_path.is_file():
            return False

        if file_path.is_symlink():
            self.skipped_files.append((file_path, "symlink"))
            return False

        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > self.config.max_file_size_mb:
                self.skipped_files.append(
                    (file_path, f"too large ({size_mb:.1f}MB > {self.config.max_file_size_mb}MB)")
                )
                return False
        except OSError as e:
            self.skipped_files.append((file_path, f"access error ({e})"))
            return False

        file_name = file_path.name

        if file_name in self.config.special_files:
            return self._is_text_file(file_path)

        suffix = file_path.suffix.lower()
        if suffix in self.config.include_extensions:
            return self._is_text_file(file_path)

        if file_name.startswith("."):
            for ext in self.config.include_extensions:
                if ext.startswith(".") and file_name.endswith(ext.lstrip(".")):
                    return self._is_text_file(file_path)

        return False

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if a file is a readable text file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                chunk = f.read(1024)
                if "\0" in chunk:
                    self.skipped_files.append((file_path, "binary file"))
                    return False
            return True
        except UnicodeDecodeError:
            self.skipped_files.append((file_path, "encoding error"))
            return False
        except OSError as e:
            self.skipped_files.append((file_path, f"read error ({e})"))
            return False

    def _should_exclude_dir(self, dir_path: Path) -> bool:
        """Check if a directory should be excluded."""
        for part in dir_path.parts:
            if part in self.config.exclude_dirs:
                return True

        dir_name = dir_path.name
        if dir_name.startswith(".") and dir_name != ".git":
            if dir_name not in {".github", ".vscode", ".idea"}:
                return True

        return False

    def collect_files(self) -> List[Path]:
        """Collect all matching code files."""
        self.collected_files.clear()
        self.skipped_files.clear()

        root = self.config.root_path

        if not root.exists():
            raise FileNotFoundError(f"Directory not found: {root}")

        if not root.is_dir():
            raise NotADirectoryError(f"Not a directory: {root}")

        if self.config.recursive:
            for dirpath, dirnames, filenames in os.walk(root):
                current_dir = Path(dirpath)
                dirnames[:] = [
                    d for d in dirnames
                    if not self._should_exclude_dir(current_dir / d)
                ]

                for filename in filenames:
                    file_path = current_dir / filename
                    if self.should_collect_file(file_path):
                        self.collected_files.append(file_path)
        else:
            for item in root.iterdir():
                if item.is_file() and self.should_collect_file(item):
                    self.collected_files.append(item)

        self.collected_files.sort()
        return self.collected_files