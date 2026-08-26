"""Output path resolution and manifest generation."""

import json
from datetime import datetime
from pathlib import Path
from typing import List


def output_files_exist(output_dir: Path, base_filename: str) -> bool:
    """Check if a collection output (single or split) already exists."""
    if (output_dir / base_filename).exists():
        return True

    stem = Path(base_filename).stem
    suffix = Path(base_filename).suffix
    return any(output_dir.glob(f"{stem}.part*{suffix}"))


def resolve_unique_filename(
    output_dir: Path,
    base_filename: str,
    force: bool = False,
) -> str:
    """Return a filename that won't overwrite existing collection output."""
    if force or not output_files_exist(output_dir, base_filename):
        return base_filename

    stem = Path(base_filename).stem
    suffix = Path(base_filename).suffix
    counter = 1

    while True:
        candidate = f"{stem}_{counter}{suffix}"
        if not output_files_exist(output_dir, candidate):
            return candidate
        counter += 1


def write_manifest(
    output_dir: Path,
    base_filename: str,
    output_paths: List[Path],
    root_path: Path,
    files_collected: int,
) -> Path:
    """Write a manifest JSON describing the collection output."""
    stem = Path(base_filename).stem
    manifest_path = output_dir / f"{stem}.manifest.json"
    manifest = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "root": str(root_path.absolute()),
        "base_filename": base_filename,
        "total_parts": len(output_paths),
        "files_collected": files_collected,
        "parts": [p.name for p in output_paths],
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return manifest_path
