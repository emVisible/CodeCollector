"""Output file splitting for large collections."""

from pathlib import Path
from typing import List, Tuple

from codecollector.config import CollectorConfig
from codecollector.output import resolve_unique_filename

HEADER_SIZE_BUFFER = 512
ESTIMATED_PART_HEADER = (
    "# CodeCollector - Part 999 of 999\n\n"
    f"- **Root:** `{'x' * 60}`\n"
    "- **Files in this part:** 999\n"
    + "\n".join(f"  - `{'x' * 60}`" for _ in range(10))
    + "\n\n---\n\n"
)


def byte_size(text: str) -> int:
    return len(text.encode("utf-8"))


def make_part_filename(base_filename: str, part: int) -> str:
    path = Path(base_filename)
    return f"{path.stem}.part{part}{path.suffix}"


def format_part_header(
    part: int,
    total: int,
    config: CollectorConfig,
    files_in_part: List[Path],
) -> str:
    """Format the header for a split output file."""
    lines = [
        f"# CodeCollector - Part {part} of {total}",
        "",
    ]

    if part > 1:
        lines.append(f"- **Root:** `{config.root_path.absolute()}`")
        lines.append(f"- **Files in this part:** {len(files_in_part)}")
        lines.append("")
        for fp in files_in_part:
            try:
                lines.append(f"  - `{fp.relative_to(config.root_path)}`")
            except ValueError:
                lines.append(f"  - `{fp}`")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def plan_parts(
    chunks: List[str],
    first_part_prefix: str,
    max_bytes: int,
) -> List[List[int]]:
    """Plan which chunk indices belong in each output part."""
    if max_bytes <= 0:
        return [list(range(len(chunks)))]

    parts: List[List[int]] = []
    current: List[int] = []
    current_size = 0
    part_num = 1
    header_overhead = byte_size(ESTIMATED_PART_HEADER) + HEADER_SIZE_BUFFER

    for idx, chunk in enumerate(chunks):
        chunk_size = byte_size(chunk)
        overhead = header_overhead

        if part_num == 1:
            overhead += byte_size(first_part_prefix)

        budget = max_bytes - overhead

        if current and current_size + chunk_size > budget:
            parts.append(current)
            current = [idx]
            current_size = chunk_size
            part_num += 1
        else:
            current.append(idx)
            current_size += chunk_size

    if current:
        parts.append(current)

    return parts


def write_collection_output(
    output_dir: Path,
    base_filename: str,
    summary: str,
    collected_files: List[Path],
    file_contents: List[str],
    config: CollectorConfig,
    force: bool = False,
) -> Tuple[List[Path], str]:
    """Write collection output, splitting into multiple files when needed.

    Returns (output_paths, resolved_base_filename).
    """
    resolved_name = base_filename
    if config.auto_increment_output:
        resolved_name = resolve_unique_filename(output_dir, base_filename, force=force)

    max_bytes = int(config.max_output_size_mb * 1024 * 1024)
    output_path = output_dir / resolved_name

    part_indices = plan_parts(file_contents, summary, max_bytes)

    if len(part_indices) <= 1:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
            for content in file_contents:
                f.write(content)
        return [output_path], resolved_name

    total_parts = len(part_indices)
    output_paths: List[Path] = []

    for part_num, indices in enumerate(part_indices, start=1):
        part_filename = make_part_filename(resolved_name, part_num)
        part_path = output_dir / part_filename
        files_in_part = [collected_files[i] for i in indices]
        header = format_part_header(part_num, total_parts, config, files_in_part)

        with open(part_path, "w", encoding="utf-8") as f:
            f.write(header)
            if part_num == 1:
                f.write(summary)
            for i in indices:
                f.write(file_contents[i])

        output_paths.append(part_path)

    return output_paths, resolved_name
