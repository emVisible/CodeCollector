"""Output formatter module."""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from onepaste.config import CollectorConfig
from onepaste.tokens import count_tokens, method_label

_FENCE_RUN_RE = re.compile(r"`{3,}")
_TOP_TOKEN_FILES = 10


class OutputFormatter:
    """Formats collected code files into LLM-ready Markdown."""

    @staticmethod
    def fence_marker(content: str) -> str:
        """Return a backtick fence long enough to safely wrap the content."""
        longest = max(
            (len(m.group(0)) for m in _FENCE_RUN_RE.finditer(content)),
            default=0,
        )
        return "`" * max(3, longest + 1)

    @staticmethod
    def format_file_content(file_path: Path, relative_to: Path) -> str:
        """Format a single file as detailed Markdown."""
        relative_path = file_path.relative_to(relative_to)
        lang = file_path.suffix.lstrip(".") or "text"

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            line_count = content.count("\n") + 1
            file_size = file_path.stat().st_size
            tokens = count_tokens(content)
            fence = OutputFormatter.fence_marker(content)

            return (
                f"### `{relative_path}`\n\n"
                f"**Lines:** {line_count} | **Size:** {file_size:,} bytes "
                f"| **Tokens:** {tokens:,}\n\n"
                f"{fence}{lang}\n"
                f"{content}\n"
                f"{fence}\n\n"
            )
        except Exception as e:
            return f"### `{relative_path}`\n\n**Read Error:** {e}\n\n"

    @staticmethod
    def format_summary(
        collected_files: List[Path],
        skipped_files: List[Tuple[Path, str]],
        config: CollectorConfig,
    ) -> str:
        """Format the collection summary as Markdown."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        total_lines = 0
        total_size = 0
        total_tokens = 0
        file_tokens: List[Tuple[Path, int]] = []
        for fp in collected_files:
            try:
                with open(fp, encoding="utf-8") as f:
                    content = f.read()
                total_lines += content.count("\n") + 1
                total_size += fp.stat().st_size
                tokens = count_tokens(content)
                total_tokens += tokens
                file_tokens.append((fp, tokens))
            except Exception:
                file_tokens.append((fp, 0))

        summary = [
            "# OnePaste - Collection Summary",
            "",
            f"**Generated:** {now}  ",
            f"**Root:** `{config.root_path.absolute()}`  ",
            f"**Mode:** {'Recursive' if config.recursive else 'Non-recursive'}  ",
        ]

        if config.respect_gitignore:
            summary.append("**Filter:** `.gitignore` enabled  ")

        summary.extend([
            "",
            f"**Files collected:** {len(collected_files)}  ",
            f"**Total lines:** {total_lines:,}  ",
            f"**Total size:** {total_size / 1024:.1f} KB  ",
            f"**Total tokens:** {total_tokens:,} *({method_label()})*  ",
        ])

        if collected_files:
            summary.extend([
                "",
                "## Top Files by Tokens",
                "",
                "| File | Tokens |",
                "| --- | ---: |",
            ])
            top_files = sorted(file_tokens, key=lambda x: x[1], reverse=True)
            for fp, tokens in top_files[:_TOP_TOKEN_FILES]:
                try:
                    rel_path = fp.relative_to(config.root_path).as_posix()
                except ValueError:
                    rel_path = str(fp)
                summary.append(f"| `{rel_path}` | {tokens:,} |")

        if skipped_files:
            summary.append("")
            summary.append(f"**Files skipped:** {len(skipped_files)}")
            summary.append("")
            for fp, reason in skipped_files[:5]:
                try:
                    rel_path = fp.relative_to(config.root_path)
                    summary.append(f"- `{rel_path}`: {reason}")
                except ValueError:
                    summary.append(f"- `{fp}`: {reason}")
            if len(skipped_files) > 5:
                summary.append(f"- ... and {len(skipped_files) - 5} more")

        summary.extend([
            "",
            "## Directory Tree",
            "",
            "```",
            *OutputFormatter._build_directory_tree(collected_files, config.root_path),
            "```",
            "",
            "## File List",
            "",
        ])

        files_by_ext: dict = {}
        for fp in collected_files:
            ext = fp.suffix or "no_ext"
            files_by_ext.setdefault(ext, [])
            try:
                files_by_ext[ext].append(fp.relative_to(config.root_path))
            except ValueError:
                files_by_ext[ext].append(fp)

        for ext, files in sorted(files_by_ext.items()):
            summary.append(f"**{ext}** ({len(files)} files)")
            for f in files[:5]:
                summary.append(f"- `{f}`")
            if len(files) > 5:
                summary.append(f"- ... and {len(files) - 5} more")
            summary.append("")

        summary.extend([
            "---",
            "",
            "# Collected Code Content",
            "",
        ])

        return "\n".join(summary)

    @staticmethod
    def _build_directory_tree(collected_files: List[Path], root: Path) -> List[str]:
        """Build a simple directory tree from collected files."""
        tree: dict = {}
        for fp in collected_files:
            try:
                rel = fp.relative_to(root)
            except ValueError:
                rel = fp
            parts = rel.parts
            node = tree
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            if parts:
                node.setdefault(parts[-1], None)

        lines: List[str] = []

        def walk(node: dict, prefix: str = "") -> None:
            items = sorted(node.items(), key=lambda x: (x[1] is None, x[0]))
            for i, (name, children) in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{name}")
                if isinstance(children, dict) and children:
                    extension = "    " if is_last else "│   "
                    walk(children, prefix + extension)

        if tree:
            walk(tree)
        else:
            lines.append("(empty)")

        return lines
