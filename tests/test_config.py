"""Tests for onepaste.config."""

import json

import pytest

import onepaste.config as config_module
from onepaste.config import CollectorConfig


@pytest.fixture
def no_git_repo(monkeypatch):
    monkeypatch.setattr(config_module, "is_inside_git_work_tree", lambda p: False)


@pytest.fixture
def git_repo(monkeypatch):
    monkeypatch.setattr(config_module, "is_inside_git_work_tree", lambda p: True)


class TestAutoGitignore:
    def test_off_outside_git(self, isolated_config, tmp_path, no_git_repo):
        cfg = CollectorConfig.from_sources(root_path=tmp_path)
        assert cfg.respect_gitignore is False

    def test_on_inside_git(self, isolated_config, tmp_path, git_repo):
        cfg = CollectorConfig.from_sources(root_path=tmp_path)
        assert cfg.respect_gitignore is True

    def test_explicit_override_beats_auto(self, isolated_config, tmp_path, git_repo):
        cfg = CollectorConfig.from_sources(
            root_path=tmp_path,
            overrides={"respect_gitignore": False},
        )
        assert cfg.respect_gitignore is False

    def test_config_file_value_wins_over_auto(
        self, isolated_config, tmp_path, no_git_repo
    ):
        config_file = tmp_path / "c.json"
        config_file.write_text(json.dumps({"respect_gitignore": True}))

        cfg = CollectorConfig.from_sources(root_path=tmp_path, config_file=str(config_file))

        assert cfg.respect_gitignore is True

    def test_real_non_git_dir_defaults_off(self, isolated_config, tmp_path):
        # No monkeypatch: real probe. tmp dirs are not git repos.
        cfg = CollectorConfig.from_sources(root_path=tmp_path)
        assert cfg.respect_gitignore is False


class TestPatternFields:
    def test_lists_normalized(self, isolated_config, tmp_path, no_git_repo):
        cfg = CollectorConfig.from_sources(
            root_path=tmp_path,
            overrides={"include_patterns": ["src/**"], "exclude_patterns": ["*.log"]},
        )

        assert cfg.include_patterns == ["src/**"]
        assert cfg.exclude_patterns == ["*.log"]

    def test_save_roundtrip(self, isolated_config, tmp_path):
        out = tmp_path / "saved.json"
        cfg = CollectorConfig(
            root_path=tmp_path,
            include_patterns=["a/*", "b/*"],
            exclude_patterns=["*.tmp"],
        )
        cfg.save_to_file(str(out))

        data = json.loads(out.read_text())
        assert data["include_patterns"] == ["a/*", "b/*"]
        assert data["exclude_patterns"] == ["*.tmp"]

    def test_unknown_keys_ignored(self, isolated_config, tmp_path):
        cfg = CollectorConfig.from_sources(
            root_path=tmp_path,
            overrides={"not_a_field": 1},
        )
        assert not hasattr(cfg, "not_a_field")
