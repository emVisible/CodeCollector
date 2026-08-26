"""Tests for onepaste.output."""

import json

from onepaste.output import (
    output_files_exist,
    resolve_unique_filename,
    write_manifest,
)


class TestOutputFilesExist:
    def test_base_file(self, tmp_path):
        (tmp_path / "code_collection.md").write_text("x")
        assert output_files_exist(tmp_path, "code_collection.md")

    def test_part_files_count(self, tmp_path):
        (tmp_path / "code_collection.part2.md").write_text("x")
        assert output_files_exist(tmp_path, "code_collection.md")

    def test_absent(self, tmp_path):
        assert not output_files_exist(tmp_path, "code_collection.md")


class TestResolveUniqueFilename:
    def test_free_name_untouched(self, tmp_path):
        assert resolve_unique_filename(tmp_path, "out.md") == "out.md"

    def test_increments_on_collision(self, tmp_path):
        (tmp_path / "out.md").write_text("x")
        assert resolve_unique_filename(tmp_path, "out.md") == "out_1.md"

    def test_skips_taken_increments(self, tmp_path):
        (tmp_path / "out.md").write_text("x")
        (tmp_path / "out_1.md").write_text("x")
        assert resolve_unique_filename(tmp_path, "out.md") == "out_2.md"

    def test_force_returns_base(self, tmp_path):
        (tmp_path / "out.md").write_text("x")
        assert resolve_unique_filename(tmp_path, "out.md", force=True) == "out.md"


class TestManifest:
    def test_written_with_fields(self, tmp_path):
        parts = [tmp_path / "out.part1.md", tmp_path / "out.part2.md"]
        manifest = write_manifest(
            tmp_path,
            "out.md",
            parts,
            root_path=tmp_path,
            files_collected=7,
        )

        data = json.loads(manifest.read_text())
        assert data["base_filename"] == "out.md"
        assert data["total_parts"] == 2
        assert data["files_collected"] == 7
        assert data["parts"] == ["out.part1.md", "out.part2.md"]
