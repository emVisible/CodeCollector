"""Command-line interface for OnePaste."""

import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

from onepaste import __version__
from onepaste.collector import FileCollector
from onepaste.config import CONFIG_FILE, CollectorConfig, ensure_config_dir
from onepaste.formatter import OutputFormatter
from onepaste.output import output_files_exist, write_manifest
from onepaste.selector import InteractiveSelector
from onepaste.splitter import write_collection_output
from onepaste.tokens import count_tokens, method_label
from onepaste.uninstall import uninstall_package

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold",
    "path": "blue",
    "highlight": "magenta bold",
    "title": "bold cyan",
    "subtitle": "dim white",
})

console = Console(theme=custom_theme)
# Diagnostics and errors always go to stderr so piped stdout stays clean.
err_console = Console(file=sys.stderr, theme=custom_theme)


class OnePasteApp:
    """Main application class for OnePaste."""

    def __init__(self):
        self.config: Optional[CollectorConfig] = None
        self.collector: Optional[FileCollector] = None
        self.dry_run: bool = False
        self.force: bool = False
        self.stdout_mode: bool = False
        # In --stdout mode all human-readable output goes to stderr so the
        # piped stream stays clean.
        self.console: Console = console

    def run_interactive(self, filter_mode: Optional[bool] = None) -> None:
        """Run in interactive mode: select directory, then collect immediately."""
        self._print_banner()

        selected_path = InteractiveSelector.select_directory()

        if selected_path is None:
            console.print("\n[yellow]Exited[/yellow]")
            return

        console.print(f"\n[success]Collecting:[/success] [path]{selected_path}[/path]")

        overrides: dict = {"recursive": True}
        if filter_mode is not None:
            overrides["respect_gitignore"] = filter_mode

        self.config = CollectorConfig.from_sources(
            root_path=selected_path,
            overrides=overrides,
        )

        self._execute_collection()

    def run_with_path(
        self,
        path_str: str,
        recursive: bool = True,
        output_file: str = "code_collection.md",
        max_output_size_mb: Optional[float] = None,
        output_dir: Optional[str] = None,
        config_file: Optional[str] = None,
        exclude_dirs: Optional[List[str]] = None,
        respect_gitignore: Optional[bool] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        dry_run: bool = False,
        force: bool = False,
        stdout_mode: bool = False,
    ) -> None:
        """Run with a specific directory path."""
        target_path = Path(path_str).resolve()

        if not target_path.exists():
            err_console.print(f"[error]Directory not found: {target_path}[/error]")
            sys.exit(1)

        if not target_path.is_dir():
            err_console.print(f"[error]Not a directory: {target_path}[/error]")
            sys.exit(1)

        overrides: dict = {
            "recursive": recursive,
            "output_file": output_file,
        }
        # None means "auto": from_sources defaults .gitignore filtering on
        # inside git work trees.
        if respect_gitignore is not None:
            overrides["respect_gitignore"] = respect_gitignore
        if max_output_size_mb is not None:
            overrides["max_output_size_mb"] = max_output_size_mb
        if output_dir is not None:
            overrides["output_dir"] = Path(output_dir)
        if exclude_dirs:
            overrides["extra_exclude_dirs"] = set(exclude_dirs)
        if include_patterns:
            overrides["include_patterns"] = list(include_patterns)
        if exclude_patterns:
            overrides["exclude_patterns"] = list(exclude_patterns)

        self.config = CollectorConfig.from_sources(
            root_path=target_path,
            config_file=config_file,
            overrides=overrides,
        )
        self.dry_run = dry_run
        self.force = force
        self.stdout_mode = stdout_mode

        if stdout_mode:
            self.console = Console(
                file=sys.stderr,
                theme=custom_theme,
            )

        self._execute_collection()

    def _execute_collection(self) -> None:
        """Execute the code collection process."""
        c = self.console
        filter_state = "on" if self.config.respect_gitignore else "off"
        c.print("\n[info]Collecting code files...[/info]")
        c.print(f"[dim].gitignore filter: {filter_state}[/dim]")

        self.collector = FileCollector(self.config)

        with c.status("[cyan]Scanning...[/cyan]"):
            try:
                collected_files = self.collector.collect_files()
            except Exception as e:
                c.print(f"\n[error]Collection error: {e}[/error]")
                return

        if not collected_files:
            c.print("\n[warning]No matching code files found[/warning]")
            return

        if self.dry_run:
            self._print_dry_run(collected_files)
            return

        formatter = OutputFormatter()

        file_contents = [
            formatter.format_file_content(file_path, self.config.root_path)
            for file_path in collected_files
        ]
        summary = formatter.format_summary(
            collected_files, self.collector.skipped_files, self.config
        )

        if self.stdout_mode:
            self._write_stdout(summary, file_contents, collected_files)
            return

        output_dir = self.config.output_dir or Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        if (
            self.config.auto_increment_output
            and not self.force
            and output_files_exist(output_dir, self.config.output_file)
        ):
            c.print(
                f"\n[warning]Output exists:[/warning] [path]{self.config.output_file}[/path] "
                "[dim](will auto-increment)[/dim]"
            )

        output_paths, resolved_name = write_collection_output(
            output_dir,
            self.config.output_file,
            summary,
            collected_files,
            file_contents,
            self.config,
            force=self.force,
        )

        if resolved_name != self.config.output_file:
            c.print(
                f"\n[info]Output renamed to avoid overwrite:[/info] "
                f"[path]{resolved_name}[/path]"
            )

        if len(output_paths) == 1:
            c.print(
                f"\n[info]Done:[/info] [path]{output_paths[0]}[/path]"
            )
        else:
            c.print(
                f"\n[info]Done ({len(output_paths)} parts):[/info]"
            )
            for p in output_paths:
                c.print(f"  [path]{p}[/path]")

        manifest_path = None
        if self.config.write_manifest and len(output_paths) > 1:
            manifest_path = write_manifest(
                output_dir,
                resolved_name,
                output_paths,
                self.config.root_path,
                len(collected_files),
            )
            c.print(f"  [dim]Manifest: {manifest_path.name}[/dim]")

        self._print_results(output_paths, collected_files, manifest_path)

    def _write_stdout(
        self,
        summary: str,
        file_contents: List[str],
        collected_files: list,
    ) -> None:
        """Write collection output to stdout (pipe-friendly).

        Progress and stats go to stderr; splitting is disabled.
        """
        c = self.console

        max_bytes = int(self.config.max_output_size_mb * 1024 * 1024)
        total_bytes = len(summary.encode("utf-8")) + sum(
            len(part.encode("utf-8")) for part in file_contents
        )
        if max_bytes > 0 and total_bytes > max_bytes:
            c.print(
                f"[warning]Output is {total_bytes / (1024 * 1024):.1f} MB "
                f"(> {self.config.max_output_size_mb:g} MB limit); "
                "--stdout does not split[/warning]"
            )

        sys.stdout.write(summary + "".join(file_contents))
        sys.stdout.flush()

        total_tokens = count_tokens(summary) + sum(
            count_tokens(part) for part in file_contents
        )
        c.print(
            f"\n[success]Done:[/success] {len(collected_files)} files, "
            f"{total_tokens:,} tokens ({method_label()}) [dim]-> stdout[/dim]"
        )

    def _print_dry_run(self, collected_files: list) -> None:
        """Print dry-run preview without writing output."""
        c = self.console
        c.print("\n[highlight]Dry Run[/highlight] [dim](no files written)[/dim]\n")

        table = Table(title="[bold cyan]Collection Preview[/bold cyan]", show_header=False)
        table.add_column(style="bold cyan", width=20)
        table.add_column(style="white")

        table.add_row("Root", str(self.config.root_path))
        table.add_row("Files to collect", f"[success]{len(collected_files)}[/success]")

        if self.collector.skipped_files:
            table.add_row("Files skipped", f"[warning]{len(self.collector.skipped_files)}[/warning]")

        total_size = sum(fp.stat().st_size for fp in collected_files if fp.exists())
        table.add_row("Estimated size", f"{total_size / 1024:.1f} KB")
        table.add_row("Filter mode", "on" if self.config.respect_gitignore else "off")
        if self.config.include_patterns:
            shown = ", ".join(self.config.include_patterns[:3])
            more = f" (+{len(self.config.include_patterns) - 3})" if len(self.config.include_patterns) > 3 else ""
            table.add_row("Include patterns", f"{shown}{more}")
        if self.config.exclude_patterns:
            shown = ", ".join(self.config.exclude_patterns[:3])
            more = f" (+{len(self.config.exclude_patterns) - 3})" if len(self.config.exclude_patterns) > 3 else ""
            table.add_row("Exclude patterns", f"{shown}{more}")
        if self.stdout_mode:
            table.add_row("Output", "[path]stdout[/path]")
        else:
            output_dir = self.config.output_dir or Path.cwd()
            table.add_row("Output dir", str(output_dir))
            table.add_row("Output file", self.config.output_file)

        c.print(table)

        if self.collector.skipped_files and self.config.show_skipped:
            c.print("\n[warning]Skipped files (first 10):[/warning]")
            for fp, reason in self.collector.skipped_files[:10]:
                try:
                    rel = fp.relative_to(self.config.root_path)
                except ValueError:
                    rel = fp
                c.print(f"  [dim]• {rel}: {reason}[/dim]")
            if len(self.collector.skipped_files) > 10:
                c.print(f"  [dim]... and {len(self.collector.skipped_files) - 10} more[/dim]")

    def _print_results(
        self,
        output_paths: list,
        collected_files: list,
        manifest_path: Optional[Path] = None,
    ) -> None:
        """Print collection results."""
        c = self.console
        c.print()

        table = Table(title="[bold cyan]Collection Results[/bold cyan]", show_header=False)
        table.add_column(style="bold cyan", width=20)
        table.add_column(style="white")

        table.add_row("Files collected", f"[success]{len(collected_files)}[/success]")

        if self.collector.skipped_files:
            table.add_row("Files skipped", f"[warning]{len(self.collector.skipped_files)}[/warning]")

        total_lines = 0
        total_size = 0
        total_tokens = 0
        file_types = set()

        for fp in collected_files:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                total_lines += content.count("\n") + 1
                total_tokens += count_tokens(content)
                total_size += fp.stat().st_size
                file_types.add(fp.suffix or "no_ext")
            except Exception:
                pass

        table.add_row("Total lines", f"{total_lines:,}")
        table.add_row("Total size", f"{total_size / 1024:.1f} KB")
        table.add_row("Total tokens", f"{total_tokens:,} [dim]({method_label()})[/dim]")
        table.add_row("File types", str(len(file_types)))

        if len(output_paths) == 1:
            table.add_row("Output file", f"[path]{output_paths[0]}[/path]")
        else:
            table.add_row("Output files", f"[success]{len(output_paths)} parts[/success]")
            for p in output_paths:
                table.add_row("", f"[path]{p.name}[/path]")
            if manifest_path:
                table.add_row("Manifest", f"[path]{manifest_path.name}[/path]")

        c.print(table)

        if len(output_paths) == 1:
            tip = (
                "[info]Copy the file content and paste it into your LLM[/info]\n"
                f"[dim]{output_paths[0].absolute()}[/dim]"
            )
        else:
            paths_text = "\n".join(f"[dim]  {p.absolute()}[/dim]" for p in output_paths)
            tip = (
                f"[info]Paste each part into your LLM in order "
                f"(Part 1 → Part {len(output_paths)})[/info]\n"
                f"{paths_text}"
            )

        c.print(Panel(tip, border_style="green"))

    @staticmethod
    def _print_banner() -> None:
        """Print application banner."""
        console.print()
        console.print(
            Panel(
                "[title]OnePaste[/title]\n"
                "[subtitle]Select a directory → Enter → ready for LLM[/subtitle]\n"
                f"[dim]v{__version__}[/dim]",
                border_style="cyan",
                padding=(1, 2),
            )
        )


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="OnePaste - Collect project code for AI assistants",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  onepaste                          Select directory interactively, then collect
  onepaste .                        Collect current directory (.gitignore on inside git repos)
  onepaste . --no-gitignore         Include gitignored files
  onepaste /path/to/project         Collect specific directory
  onepaste . -n                     Non-recursive (current directory only)
  onepaste . -o output.md           Custom output filename
  onepaste . --max-output-size 5    Split output when exceeding 5MB per file
  onepaste . --stdout | llm "..."   Pipe collection straight into another tool
  onepaste . --dry-run              Preview without writing output
  onepaste . --force                Overwrite existing output files
  onepaste . -d ./output            Write output to specific directory
  onepaste . --exclude vendor       Extra directory to exclude
  onepaste . --include "src/**"     Only include files matching glob (repeatable)
  onepaste . --exclude-pattern "*_test.go"   Skip files matching glob (repeatable)
  onepaste --init-config            Initialize default configuration
  onepaste --uninstall              Uninstall onepaste (pipx/pip)
  onepaste --uninstall --purge-config  Uninstall and remove ~/.config/onepaste

Version: {__version__}
        """,
    )

    parser.add_argument("path", nargs="?", help="Directory path to collect code from")
    parser.add_argument(
        "-i",
        action="store_true",
        help="Force-enable .gitignore filtering "
        "(deprecated: enabled by default inside git repos)",
    )
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Disable .gitignore filtering",
    )
    parser.add_argument("-n", "--non-recursive", action="store_true", help="Non-recursive mode")
    parser.add_argument("-o", "--output", type=str, help="Output filename (default: code_collection.md)")
    parser.add_argument("-d", "--output-dir", type=str, help="Output directory (default: cwd)")
    parser.add_argument(
        "--max-output-size",
        type=float,
        metavar="MB",
        help="Max output file size in MB; auto-split when exceeded (default: 2, 0=disable)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        metavar="DIR",
        help="Extra directory to exclude (repeatable)",
    )
    parser.add_argument(
        "--include",
        action="append",
        metavar="GLOB",
        help="Only include files matching glob, e.g. 'src/**/*.ts' "
        "(repeatable; overrides extension whitelist)",
    )
    parser.add_argument(
        "--exclude-pattern",
        dest="exclude_patterns",
        action="append",
        metavar="GLOB",
        help="Exclude files matching glob, e.g. '*.test.ts' (repeatable)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write the collection to stdout instead of a file (progress goes to stderr)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview collection without writing output",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output files instead of auto-incrementing",
    )
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument("--init-config", action="store_true", help="Initialize default config")
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall onepaste (via pipx and/or pip)",
    )
    parser.add_argument(
        "--purge-config",
        action="store_true",
        help="Also remove ~/.config/onepaste (use with --uninstall)",
    )
    parser.add_argument("-v", "--version", action="version", version=f"OnePaste v{__version__}")

    args = parser.parse_args()

    if args.uninstall:
        ok, messages = uninstall_package(purge_config=args.purge_config)
        for msg in messages:
            console.print(msg)
        sys.exit(0 if ok else 1)

    if args.purge_config and not args.uninstall:
        err_console.print("[error]--purge-config must be used with --uninstall[/error]")
        sys.exit(2)

    if args.i and args.no_gitignore:
        err_console.print("[error]-i and --no-gitignore are mutually exclusive[/error]")
        sys.exit(2)

    if args.stdout:
        conflicts = [
            flag
            for flag, given in (
                ("-o/--output", args.output),
                ("-d/--output-dir", args.output_dir),
                ("--max-output-size", args.max_output_size is not None),
                ("--force", args.force),
            )
            if given
        ]
        if conflicts:
            err_console.print(
                f"[error]--stdout cannot be combined with: {', '.join(conflicts)}[/error]"
            )
            sys.exit(2)
        if not args.path:
            err_console.print(
                "[error]--stdout requires an explicit PATH "
                "(interactive picker would pollute stdout)[/error]"
            )
            sys.exit(2)

    ensure_config_dir()

    if args.init_config:
        config = CollectorConfig(root_path=Path.cwd())
        config.save_to_file(str(CONFIG_FILE))
        console.print(f"[success]Config created:[/success] [path]{CONFIG_FILE}[/path]")
        return

    try:
        app = OnePasteApp()

        if not args.path and not args.config:
            respect = True if args.i else (False if args.no_gitignore else None)
            app.run_interactive(filter_mode=respect)
        else:
            app.run_with_path(
                path_str=args.path or ".",
                recursive=not args.non_recursive,
                output_file=args.output or "code_collection.md",
                max_output_size_mb=args.max_output_size,
                output_dir=args.output_dir,
                config_file=args.config,
                exclude_dirs=args.exclude,
                respect_gitignore=True if args.i else (False if args.no_gitignore else None),
                include_patterns=args.include,
                exclude_patterns=args.exclude_patterns,
                dry_run=args.dry_run,
                force=args.force,
                stdout_mode=args.stdout,
            )

    except KeyboardInterrupt:
        err_console.print("\n\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        err_console.print(f"\n[error]Error: {e}[/error]")
        sys.exit(1)


if __name__ == "__main__":
    main()
