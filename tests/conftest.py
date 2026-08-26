"""Shared fixtures for OnePaste tests."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Build a sample project tree used across collector/formatter tests."""
    root = tmp_path / "proj"
    (root / "src").mkdir(parents=True)
    (root / "tests_inner").mkdir()
    (root / "node_modules" / "pkg").mkdir(parents=True)
    (root / ".git").mkdir()

    (root / ".gitignore").write_text("*.log\nsecret*\n", encoding="utf-8")
    (root / "README.md").write_text("# Demo\n\nSome docs.\n", encoding="utf-8")
    (root / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (root / "notes.txt").write_text("plain notes\n", encoding="utf-8")
    (root / "fenced.py").write_text(
        'DOC = """\n```\ninner fence\n```\n"""\n',
        encoding="utf-8",
    )
    (root / "deep_fence.md").write_text("````\nquad fence\n````\n", encoding="utf-8")
    (root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (root / "tests_inner" / "test_a.py").write_text(
        "def test_a():\n    assert True\n",
        encoding="utf-8",
    )
    (root / "debug.log").write_text("log line\n", encoding="utf-8")
    (root / "secret_key.txt").write_text("abc123\n", encoding="utf-8")
    (root / "binary.bin").write_bytes(b"\x00\x01binary")
    (root / "photo.PNG").write_bytes(b"\x89PNG fake")
    (root / "node_modules" / "pkg" / "dep.js").write_text(
        "module.exports = 1;\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def isolated_config(monkeypatch, tmp_path: Path):
    """Point the global config at a missing temp path for determinism."""
    import onepaste.config as config_module

    fake_global = tmp_path / "global_config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", fake_global)
    return fake_global
