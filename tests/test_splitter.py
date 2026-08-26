"""Tests for onepaste.splitter."""

from onepaste.config import CollectorConfig
from onepaste.splitter import (
    ESTIMATED_PART_HEADER,
    HEADER_SIZE_BUFFER,
    byte_size,
    format_part_header,
    make_part_filename,
    plan_parts,
    write_collection_output,
)


def _overhead(first_part_prefix: str = "") -> int:
    return byte_size(ESTIMATED_PART_HEADER) + HEADER_SIZE_BUFFER + byte_size(first_part_prefix)


class TestPlanParts:
    def test_two_chunks_per_part(self):
        chunks = ["a" * 100] * 5
        max_bytes = _overhead() + 200

        parts = plan_parts(chunks, "", max_bytes)

        assert parts == [[0, 1], [2, 3], [4]]

    def test_no_limit_single_part(self):
        assert plan_parts(["x", "y", "z"], "", 0) == [[0, 1, 2]]

    def test_oversized_chunk_gets_own_part(self):
        chunks = ["a" * 5000, "b" * 10]
        parts = plan_parts(chunks, "", _overhead() + 100)

        flat = [i for part in parts for i in part]
        assert flat == [0, 1]
        assert len(parts) >= 2

    def test_order_preserved(self):
        chunks = [str(i) * 50 for i in range(7)]
        parts = plan_parts(chunks, "", _overhead() + 100)
        flat = [i for part in parts for i in part]
        assert flat == list(range(7))


class TestFilenames:
    def test_make_part_filename(self):
        assert make_part_filename("out.md", 2) == "out.part2.md"

    def test_part_header_lists_files(self, tmp_path):
        config = CollectorConfig(root_path=tmp_path)
        header = format_part_header(
            2, 3, config, [tmp_path / "a.py", tmp_path / "b.py"]
        )
        assert "Part 2 of 3" in header
        assert "`a.py`" in header


class TestWriteCollectionOutput:
    def _config(self, root, **kw):
        return CollectorConfig(root_path=root, auto_increment_output=True, **kw)

    def test_single_file_output(self, tmp_path):
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        config = self._config(tmp_path)

        paths, name = write_collection_output(
            out_dir, "code_collection.md", "SUMMARY", [], [], config
        )

        assert len(paths) == 1
        assert name == "code_collection.md"
        assert paths[0].read_text(encoding="utf-8") == "SUMMARY"

    def test_split_into_named_parts(self, tmp_path):
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        # Budget leaves room for exactly one 60-byte chunk per part.
        overhead = (
            byte_size(ESTIMATED_PART_HEADER)
            + HEADER_SIZE_BUFFER
            + byte_size("SUMMARY")
        )
        config = self._config(
            tmp_path, max_output_size_mb=(overhead + 50) / (1024 * 1024)
        )

        contents = ["c" * 60 + "\n", "d" * 60 + "\n"]
        files = [tmp_path / "a.py", tmp_path / "b.py"]

        paths, name = write_collection_output(
            out_dir, "code_collection.md", "SUMMARY", files, contents, config
        )

        assert len(paths) == 2
        assert [p.name for p in paths] == [
            "code_collection.part1.md",
            "code_collection.part2.md",
        ]
        text1 = paths[0].read_text(encoding="utf-8")
        assert text1.startswith("# OnePaste - Part 1 of 2")
        assert "SUMMARY" in text1
        assert "chunk-two" not in text1

    def test_auto_increment_avoids_overwrite(self, tmp_path):
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        (out_dir / "code_collection.md").write_text("old")
        config = self._config(tmp_path)

        _, name = write_collection_output(
            out_dir, "code_collection.md", "S", [], [], config
        )

        assert name == "code_collection_1.md"
