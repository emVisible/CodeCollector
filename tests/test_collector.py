"""Tests for onepaste.collector."""

import os
from pathlib import Path

import pytest

import onepaste.collector as collector_module
from onepaste.collector import FileCollector
from onepaste.config import CollectorConfig

DEFAULT_EXPECTED = {
    ".gitignore",
    "README.md",
    "main.py",
    "notes.txt",
    "fenced.py",
    "deep_fence.md",
    "src/app.py",
    "tests_inner/test_a.py",
    "secret_key.txt",
}


def _collect(root: Path, **overrides) -> FileCollector:
    config = CollectorConfig(root_path=root, **overrides)
    fc = FileCollector(config)
    fc.collect_files()
    return fc


def _rel_names(fc: FileCollector, root: Path):
    return {fp.relative_to(root).as_posix() for fp in fc.collected_files}


class TestDefaultCollection:
    def test_whitelisted_extensions_collected(self, project_dir: Path):
        names = _rel_names(_collect(project_dir), project_dir)
        assert names == DEFAULT_EXPECTED

    def test_excluded_dirs_pruned(self, project_dir: Path):
        fc = _collect(project_dir)
        assert all("node_modules" not in fp.parts for fp in fc.collected_files)

    def test_binary_and_unknown_ext_skipped(self, project_dir: Path):
        fc = _collect(project_dir)
        names = _rel_names(fc, project_dir)
        assert "binary.bin" not in names
        assert "photo.PNG" not in names
        # Files rejected at the extension stage are filtered silently.
        logged = {fp.name for fp, _ in fc.skipped_files}
        assert "binary.bin" not in logged

    def test_symlink_skipped(self, project_dir: Path):
        target = project_dir / "main.py"
        link = project_dir / "link.py"
        try:
            os.symlink(target, link)
        except OSError:
            pytest.skip("symlinks unsupported")
        fc = _collect(project_dir)
        reasons = {fp.name: r for fp, r in fc.skipped_files}
        assert reasons.get("link.py") == "symlink"

    def test_own_output_artifacts_skipped(self, project_dir: Path):
        artifact = project_dir / "code_collection.md"
        artifact.write_text("# stale\n")
        names = _rel_names(_collect(project_dir), project_dir)
        assert "code_collection.md" not in names

    def test_non_recursive(self, project_dir: Path):
        names = _rel_names(_collect(project_dir, recursive=False), project_dir)
        assert "src/app.py" not in names
        assert "tests_inner/test_a.py" not in names
        assert "main.py" in names


class TestGitignoreFiltering:
    @pytest.fixture(autouse=True)
    def force_fallback_matcher(self, monkeypatch):
        monkeypatch.setattr(
            collector_module, "list_git_visible_files", lambda root: None
        )

    def test_gitignored_files_excluded(self, project_dir: Path):
        names = _rel_names(_collect(project_dir, respect_gitignore=True), project_dir)
        assert "secret_key.txt" not in names
        assert DEFAULT_EXPECTED - {"secret_key.txt"} <= names

    def test_filter_off_keeps_them(self, project_dir: Path):
        names = _rel_names(_collect(project_dir, respect_gitignore=False), project_dir)
        assert "secret_key.txt" in names


class TestExcludesAreRootScoped:
    def test_suspicious_ancestor_names_do_not_prune(self, tmp_path: Path):
        """Regression: exclusion names must match segments relative to the
        collection root, never absolute ancestors (CI runs under /tmp)."""
        root = tmp_path / "tmp" / "build" / "env" / "proj"
        (root / "src").mkdir(parents=True)
        (root / "a.py").write_text("x = 1\n")
        (root / "src" / "b.py").write_text("y = 2\n")
        (root / "build").mkdir()  # a REAL excluded dir inside the project
        (root / "build" / "junk.py").write_text("junk\n")

        names = _rel_names(_collect(root), root)

        assert "a.py" in names
        assert "src/b.py" in names
        assert not any(n.startswith("build/") for n in names)

    def test_real_excluded_dirs_inside_root_still_pruned(self, project_dir: Path):
        fc = _collect(project_dir)
        assert all("node_modules" not in fp.parts for fp in fc.collected_files)


class TestGlobPatterns:
    def test_include_overrides_extension_whitelist(self, project_dir: Path):
        names = _rel_names(
            _collect(project_dir, include_patterns=["src/**"]), project_dir
        )
        assert names == {"src/app.py"}

    def test_include_multiple_patterns(self, project_dir: Path):
        names = _rel_names(
            _collect(project_dir, include_patterns=["*.md", "*.txt"]), project_dir
        )
        assert names == {"README.md", "deep_fence.md", "notes.txt", "secret_key.txt"}

    def test_include_matches_basename(self, project_dir: Path):
        names = _rel_names(
            _collect(project_dir, include_patterns=["app.py"]), project_dir
        )
        assert names == {"src/app.py"}

    def test_exclude_pattern_trailing_slash(self, project_dir: Path):
        names = _rel_names(
            _collect(project_dir, exclude_patterns=["tests_inner/"]), project_dir
        )
        assert "tests_inner/test_a.py" not in names
        assert DEFAULT_EXPECTED - {"tests_inner/test_a.py"} <= names

    def test_exclude_pattern_glob(self, project_dir: Path):
        names = _rel_names(
            _collect(project_dir, exclude_patterns=["src/*", "fence*"]), project_dir
        )
        assert "src/app.py" not in names
        assert "fenced.py" not in names

    def test_include_misses_are_silent(self, project_dir: Path):
        fc = _collect(project_dir, include_patterns=["*.nomatch"])
        assert fc.collected_files == []
        include_noise = [r for _, r in fc.skipped_files if "--include" in r]
        assert include_noise == []

    def test_exclude_hits_reported(self, project_dir: Path):
        fc = _collect(project_dir, exclude_patterns=["secret_key.txt"])
        reasons = {fp.name: r for fp, r in fc.skipped_files}
        assert "excluded by pattern" in reasons.get("secret_key.txt", "")


class TestMatchesAny:
    def test_unit_cases(self):
        match = FileCollector._matches_any
        assert match("src/a/b.ts", ["src/**"])
        assert match("a.test.ts", ["*.test.ts"])
        assert match("deep/nested/x.log", ["x.log"])
        assert match("anything/under/dir/f.txt", ["dir/"])
        assert not match("src/main.py", ["tests/**"])
