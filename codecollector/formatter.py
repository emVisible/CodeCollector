"""Output formatter module."""

from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from codecollector.config import CollectorConfig


class OutputFormatter:
    """Formats collected code files into various output formats."""

    @staticmethod
    def format_file_content(file_path: Path, relative_to: Path,
                            format_type: str = "detailed") -> str:
        """Format a single file's content."""
        relative_path = file_path.relative_to(relative_to)

        if format_type == "markdown":
            return OutputFormatter._format_markdown(file_path, relative_path)
        elif format_type == "simple":
            return OutputFormatter._format_simple(file_path, relative_path)
        else:
            return OutputFormatter._format_detailed(file_path, relative_path)

    @staticmethod
    def _format_detailed(file_path: Path, relative_path: Path) -> str:
        """Detailed format with full information."""
        separator = "=" * 80

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            line_count = content.count("\n") + 1
            file_size = file_path.stat().st_size

            return (
                f"{separator}\n"
                f"File: {relative_path}\n"
                f"{'─' * 80}\n"
                f"Lines: {line_count} | Size: {file_size:,} bytes\n"
                f"{separator}\n\n"
                f"{content}\n\n"
            )
        except Exception as e:
            return (
                f"{separator}\n"
                f"File: {relative_path}\n"
                f"{'─' * 80}\n"
                f"Read Error: {e}\n"
                f"{separator}\n\n"
            )

    @staticmethod
    def _format_markdown(file_path: Path, relative_path: Path) -> str:
        """Markdown format."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            extension = file_path.suffix.lstrip(".") or "text"

            return (
                f"## {relative_path}\n\n"
                f"```{extension}\n"
                f"{content}\n"
                f"```\n\n"
            )
        except Exception as e:
            return f"## {relative_path}\n\nError: {e}\n\n"

    @staticmethod
    def _format_simple(file_path: Path, relative_path: Path) -> str:
        """Simple format."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            return f"--- {relative_path} ---\n{content}\n\n"
        except Exception as e:
            return f"--- {relative_path} ---\nError: {e}\n\n"

    @staticmethod
    def format_summary(
        collected_files: List[Path],
        skipped_files: List[Tuple[Path, str]],
        config: CollectorConfig,
    ) -> str:
        """Format the collection summary."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        total_lines = 0
        total_size = 0
        for fp in collected_files:
            try:
                with open(fp, encoding="utf-8") as f:
                    total_lines += f.read().count("\n") + 1
                total_size += fp.stat().st_size
            except Exception:
                pass

        summary = []
        summary.append("=" * 80)
        summary.append("CodeCollector - Collection Summary")
        summary.append("=" * 80)
        summary.append(f"Generated: {now}")
        summary.append(f"Root: {config.root_path.absolute()}")
        summary.append(f"Mode: {'Recursive' if config.recursive else 'Non-recursive'}")
        summary.append("─" * 80)
        summary.append(f"Files collected: {len(collected_files)}")
        summary.append(f"Total lines: {total_lines:,}")
        summary.append(f"Total size: {total_size / 1024:.1f} KB")

        if skipped_files:
            summary.append("─" * 80)
            summary.append(f"Files skipped: {len(skipped_files)}")
            for fp, reason in skipped_files[:5]:
                try:
                    rel_path = fp.relative_to(config.root_path)
                    summary.append(f"  • {rel_path}: {reason}")
                except ValueError:
                    summary.append(f"  • {fp}: {reason}")
            if len(skipped_files) > 5:
                summary.append(f"  ... and {len(skipped_files) - 5} more")

        summary.append("─" * 80)
        summary.append("File List:")

        files_by_ext = {}
        for fp in collected_files:
            ext = fp.suffix or "no_ext"
            if ext not in files_by_ext:
                files_by_ext[ext] = []
            try:
                files_by_ext[ext].append(fp.relative_to(config.root_path))
            except ValueError:
                files_by_ext[ext].append(fp)

        for ext, files in sorted(files_by_ext.items()):
            summary.append(f"\n  [{ext}] ({len(files)} files)")
            for f in files[:3]:
                summary.append(f"    {f}")
            if len(files) > 3:
                summary.append(f"    ... and {len(files) - 3} more")

        summary.append("\n" + "=" * 80)
        summary.append("Collected Code Content:")
        summary.append("=" * 80 + "\n")

        return "\n".join(summary)