"""Git-aware ignore checking for filter mode."""

import fnmatch
import subprocess
from pathlib import Path
from typing import List, Optional, Set, Tuple


class GitignoreMatcher:
    """Match paths against .gitignore rules (fallback when git is unavailable)."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self._rules: List[Tuple[str, bool, bool]] = []  # pattern, negation, dir_only

    def load_all(self) -> None:
        """Load the root .gitignore and nested ones (skipping .git)."""
        root_gitignore = self.root / ".gitignore"
        if root_gitignore.is_file():
            self._load_file(root_gitignore)

        for gitignore in self.root.rglob(".gitignore"):
            if gitignore == root_gitignore:
                continue
            try:
                if ".git" in gitignore.relative_to(self.root).parts:
                    continue
            except ValueError:
                continue
            self._load_file(gitignore)

    def _load_file(self, gitignore_path: Path) -> None:
        try:
            rel_base = gitignore_path.parent.relative_to(self.root)
            prefix = "" if rel_base == Path(".") else rel_base.as_posix() + "/"
        except ValueError:
            return

        try:
            lines = gitignore_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            negation = line.startswith("!")
            if negation:
                line = line[1:].strip()
                if not line:
                    continue

            dir_only = line.endswith("/")
            if dir_only:
                line = line.rstrip("/")

            if line.startswith("/"):
                pattern = prefix + line.lstrip("/")
            elif "/" in line:
                pattern = prefix + line
            else:
                # gitignore: pattern without slash matches in any directory
                pattern = prefix + "**/" + line if prefix else "**/" + line

            self._rules.append((pattern, negation, dir_only))

    def is_ignored(self, path: Path, is_dir: bool = False) -> bool:
        try:
            rel = path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return False

        if not rel or rel == ".":
            return False

        name = path.name
        ignored = False

        for pattern, negation, dir_only in self._rules:
            if dir_only and not is_dir:
                continue
            if self._matches(pattern, rel, name):
                ignored = not negation

        return ignored

    @staticmethod
    def _matches(pattern: str, rel_path: str, name: str) -> bool:
        candidates = {rel_path, name}

        # "**/foo" also matches top-level "foo"
        if pattern.startswith("**/"):
            candidates.add(pattern[3:])
            bare = pattern[3:]
            if fnmatch.fnmatch(name, bare) or fnmatch.fnmatch(rel_path, bare):
                return True
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # match in nested path segments
            parts = rel_path.split("/")
            for i in range(len(parts)):
                sub = "/".join(parts[i:])
                if fnmatch.fnmatch(sub, bare) or fnmatch.fnmatch(parts[i], bare):
                    return True
            return False

        for target in candidates:
            if fnmatch.fnmatch(target, pattern):
                return True

        return False


def list_git_visible_files(root: Path) -> Optional[Set[Path]]:
    """Return files that are tracked or untracked-but-not-ignored.

    Uses `git ls-files -co --exclude-standard`. Returns None if git is
    unavailable or root is not inside a git work tree.
    """
    root = root.resolve()
    try:
        probe = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None

    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return None

    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    files: Set[Path] = set()
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", errors="replace")
        files.add((root / rel).resolve())
    return files
