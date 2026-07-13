"""File collector module."""

import os
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple

from codecollector.config import CollectorConfig
from codecollector.gitignore import GitignoreMatcher, list_git_visible_files

# Own outputs should never be re-collected (prevents runaway growth).
_OUTPUT_ARTIFACT_RE = re.compile(
    r"^code_collection(?:_\d+)?(?:\.part\d+)?\.(md|txt)$"
    r"|^code_collection(?:_\d+)?\.manifest\.json$"
)


class FileCollector:
    """Collects code files from directories."""

    def __init__(self, config: CollectorConfig):
        self.config = config
        self.collected_files: List[Path] = []
        self.skipped_files: List[Tuple[Path, str]] = []
        self._gitignore: Optional[GitignoreMatcher] = None
        self._git_files: Optional[Set[Path]] = None

        if config.respect_gitignore:
            self._git_files = list_git_visible_files(config.root_path)
            if self._git_files is None:
                # Fallback when git is unavailable
                self._gitignore = GitignoreMatcher(config.root_path)
                self._gitignore.load_all()

    def _is_output_artifact(self, file_path: Path) -> bool:
        name = file_path.name
        if _OUTPUT_ARTIFACT_RE.match(name):
            return True

        output_name = Path(self.config.output_file).name
        if name == output_name:
            return True

        stem = Path(self.config.output_file).stem
        suffix = Path(self.config.output_file).suffix
        # matches output_1.md / output.part2.md / output_1.part2.md
        custom_re = re.compile(
            rf"^{re.escape(stem)}(?:_\d+)?(?:\.part\d+)?{re.escape(suffix)}$"
            rf"|^{re.escape(stem)}(?:_\d+)?\.manifest\.json$"
        )
        return bool(custom_re.match(name))

    def should_collect_file(self, file_path: Path, *, check_git: bool = True) -> bool:
        """Determine if a file should be collected."""
        if not file_path.is_file():
            return False

        if file_path.is_symlink():
            self.skipped_files.append((file_path, "symlink"))
            return False

        if self._is_output_artifact(file_path):
            self.skipped_files.append((file_path, "collector output"))
            return False

        if check_git:
            if self._git_files is not None:
                if file_path.resolve() not in self._git_files:
                    self.skipped_files.append((file_path, "gitignored"))
                    return False
            elif self._gitignore and self._gitignore.is_ignored(file_path):
                self.skipped_files.append((file_path, "gitignored"))
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

    def _path_in_excluded_dir(self, file_path: Path) -> bool:
        try:
            parts = file_path.resolve().relative_to(self.config.root_path.resolve()).parts
        except ValueError:
            parts = file_path.parts
        return any(part in self.config.all_exclude_dirs for part in parts[:-1])

    def _should_exclude_dir(self, dir_path: Path) -> bool:
        """Check if a directory should be excluded."""
        for part in dir_path.parts:
            if part in self.config.all_exclude_dirs:
                return True

        if self._git_files is None and self._gitignore:
            if self._gitignore.is_ignored(dir_path, is_dir=True):
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

        # Filter mode with git: start from git-visible files (stricter, correct).
        if self.config.respect_gitignore and self._git_files is not None:
            self._collect_from_git_files()
        elif self.config.recursive:
            self._collect_by_walk()
        else:
            for item in root.iterdir():
                if item.is_file() and self.should_collect_file(item):
                    self.collected_files.append(item)

        self.collected_files.sort()
        return self.collected_files

    def _collect_from_git_files(self) -> None:
        assert self._git_files is not None
        root = self.config.root_path.resolve()

        for file_path in sorted(self._git_files):
            try:
                file_path.relative_to(root)
            except ValueError:
                continue

            if not self.config.recursive:
                if file_path.parent.resolve() != root:
                    continue

            if self._path_in_excluded_dir(file_path):
                self.skipped_files.append((file_path, "excluded directory"))
                continue

            # Already known to be git-visible; only apply local filters.
            if self.should_collect_file(file_path, check_git=False):
                self.collected_files.append(file_path)

    def _collect_by_walk(self) -> None:
        root = self.config.root_path
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
