"""End-to-end CLI tests (subprocess based, offline friendly)."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


def run_cli(args, cwd, home):
    env = dict(os.environ)
    env["HOME"] = str(home)  # isolate ~/.config/onepaste
    return subprocess.run(
        [sys.executable, "-m", "onepaste", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.fixture
def git_project(project_dir: Path) -> Path:
    subprocess.run(
        ["git", "init", "-q"],
        cwd=str(project_dir),
        capture_output=True,
        timeout=30,
        check=False,
    )
    return project_dir


class TestMeta:
    def test_version_flag(self, tmp_path):
        r = run_cli(["-v"], cwd=tmp_path, home=tmp_path)
        assert r.returncode == 0
        assert "OnePaste v" in (r.stdout + r.stderr)

    def test_version_matches_package(self, tmp_path):
        from onepaste import __version__

        pyproject = (
            Path(__file__).resolve().parent.parent / "pyproject.toml"
        ).read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
        assert match is not None
        assert match.group(1) == __version__

    def test_help(self, tmp_path):
        r = run_cli(["--help"], cwd=tmp_path, home=tmp_path)
        assert r.returncode == 0
        for flag in ("--stdout", "--include", "--exclude-pattern", "--no-gitignore"):
            assert flag in r.stdout


class TestValidation:
    def test_stdout_with_output_file_conflict(self, project_dir, tmp_path):
        r = run_cli([str(project_dir), "--stdout", "-o", "x.md"], cwd=tmp_path, home=tmp_path)
        assert r.returncode == 2
        assert "--stdout" in r.stderr

    def test_stdout_without_path_rejected(self, tmp_path):
        r = run_cli(["--stdout"], cwd=tmp_path, home=tmp_path)
        assert r.returncode == 2

    def test_gitignore_flags_mutually_exclusive(self, project_dir, tmp_path):
        r = run_cli(
            [str(project_dir), "-i", "--no-gitignore"],
            cwd=tmp_path,
            home=tmp_path,
        )
        assert r.returncode == 2
        assert "mutually exclusive" in r.stderr

    def test_missing_directory(self, tmp_path):
        r = run_cli([str(tmp_path / "nope")], cwd=tmp_path, home=tmp_path)
        assert r.returncode == 1


class TestStdoutMode:
    def test_pipes_clean_markdown(self, project_dir, tmp_path):
        out_file = tmp_path / "should_not_exist.md"
        r = run_cli(
            [str(project_dir), "--stdout", "-o", str(out_file)],
            cwd=tmp_path,
            home=tmp_path,
        )
        # -o conflicts even when pointing elsewhere.
        assert r.returncode == 2

        r = run_cli([str(project_dir), "--stdout"], cwd=tmp_path, home=tmp_path)
        assert r.returncode == 0
        assert "# OnePaste - Collection Summary" in r.stdout
        assert "### `main.py`" in r.stdout
        assert "print('hi')" in r.stdout
        assert not out_file.exists()
        assert "Done:" in r.stderr

    def test_no_files_written_to_cwd(self, project_dir, tmp_path):
        run_cli([str(project_dir), "--stdout"], cwd=tmp_path, home=tmp_path)
        # HOME isolation may create ~/.config; no collection artifacts allowed.
        artifacts = [
            p
            for p in tmp_path.iterdir()
            if p.name.startswith("code_collection")
        ]
        assert artifacts == []


class TestGitignoreDefaults:
    def _collect_md(self, project: Path, extra, tmp_path: Path, name="work"):
        work = tmp_path / name
        work.mkdir(parents=True, exist_ok=True)
        r = run_cli([str(project), *extra], cwd=work, home=tmp_path)
        assert r.returncode == 0, r.stderr
        produced = list(work.glob("code_collection*.md"))
        assert len(produced) >= 1, r.stderr
        return "\n".join(p.read_text(encoding="utf-8") for p in produced)

    def test_on_inside_git_repo(self, git_project, tmp_path):
        out = self._collect_md(git_project, [], tmp_path)
        # secret_key.txt matches the repo .gitignore pattern `secret*`
        assert "secret_key.txt" not in out
        assert "### `main.py`" in out

    def test_off_with_explicit_flag(self, git_project, tmp_path):
        out = self._collect_md(
            git_project, ["--no-gitignore"], tmp_path, name="w2"
        )
        assert "secret_key.txt" in out

    def test_off_outside_git_repo(self, tmp_path):
        plain = tmp_path / "plain"
        plain.mkdir()
        (plain / "notes.txt").write_text("t")
        (plain / ".gitignore").write_text("*.txt\n")

        out = self._collect_md(plain, [], tmp_path, name="w3")
        assert "`notes.txt`" in out


class TestFileOutputModes:
    def test_writes_default_file(self, project_dir, tmp_path):
        work = tmp_path / "work"
        work.mkdir()
        r = run_cli([str(project_dir)], cwd=work, home=tmp_path)
        assert r.returncode == 0, r.stderr
        produced = list(work.glob("code_collection*.md"))
        assert len(produced) == 1
        content = produced[0].read_text(encoding="utf-8")
        assert "**Total tokens:**" in content
        assert "## Top Files by Tokens" in content

    def test_glob_include(self, project_dir, tmp_path):
        work = tmp_path / "work"
        work.mkdir()
        r = run_cli(
            [str(project_dir), "--include", "src/**", "-o", "only_src.md"],
            cwd=work,
            home=tmp_path,
        )
        assert r.returncode == 0, r.stderr
        content = (work / "only_src.md").read_text(encoding="utf-8")
        assert "`src/app.py`" in content
        assert "`main.py`" not in content

    def test_dry_run_writes_nothing(self, project_dir, tmp_path):
        work = tmp_path / "work"
        work.mkdir()
        r = run_cli([str(project_dir), "--dry-run"], cwd=work, home=tmp_path)
        assert r.returncode == 0, r.stderr
        assert list(work.glob("*")) == []
