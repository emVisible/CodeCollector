"""Tests for onepaste.formatter."""

from pathlib import Path

from onepaste.config import CollectorConfig
from onepaste.formatter import OutputFormatter


class TestFenceMarker:
    def test_plain_content_uses_triple(self):
        assert OutputFormatter.fence_marker("hello world") == "```"

    def test_inner_triple_gets_quad(self):
        assert OutputFormatter.fence_marker("a\n```\nb") == "````"

    def test_inner_quad_gets_penta(self):
        assert OutputFormatter.fence_marker("````") == "`````"

    def test_longest_run_wins(self):
        content = "```\nplain\n`````\nmore"
        assert len(OutputFormatter.fence_marker(content)) == 6

    def test_short_runs_ignored(self):
        assert OutputFormatter.fence_marker("`inline` and ``double``") == "```"


class TestFormatFileContent:
    def test_basic_file(self, tmp_path: Path):
        fp = tmp_path / "mod.py"
        fp.write_text("x = 1", encoding="utf-8")  # single line, no trailing NL

        out = OutputFormatter.format_file_content(fp, tmp_path)

        assert out.startswith("### `mod.py`")
        assert "```py" in out
        assert "**Lines:** 1" in out
        assert "**Tokens:**" in out

    def test_fenced_content_stays_intact(self, project_dir: Path):
        fp = project_dir / "fenced.py"
        out = OutputFormatter.format_file_content(fp, project_dir)

        content = fp.read_text(encoding="utf-8")
        fence = OutputFormatter.fence_marker(content)

        assert f"{fence}py" in out
        assert out.rstrip("\n").endswith(fence)
        assert "inner fence" in out

    def test_read_error_handled(self, tmp_path: Path):
        missing = tmp_path / "gone.py"
        out = OutputFormatter.format_file_content(missing, tmp_path)
        assert "Read Error" in out


class TestFormatSummary:
    def _config(self, root: Path) -> CollectorConfig:
        return CollectorConfig(root_path=root, respect_gitignore=True)

    def test_contains_totals_and_top_table(self, project_dir: Path):
        files = sorted(project_dir.rglob("*.py")) + [project_dir / "README.md"]
        summary = OutputFormatter.format_summary(files, [], self._config(project_dir))

        assert "**Total tokens:**" in summary
        assert "## Top Files by Tokens" in summary
        assert "| File | Tokens |" in summary
        assert "`src/app.py`" in summary
        assert ".gitignore" in summary  # filter status line

    def test_skipped_files_listed(self, project_dir: Path):
        skipped = [(project_dir / "binary.bin", "binary file")]
        summary = OutputFormatter.format_summary([], skipped, self._config(project_dir))

        assert "**Files skipped:** 1" in summary
        assert "binary.bin" in summary
