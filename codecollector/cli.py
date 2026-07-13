"""Command-line interface for CodeCollector."""

import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

from codecollector.config import CollectorConfig, CONFIG_FILE, ensure_config_dir
from codecollector.collector import FileCollector
from codecollector.selector import InteractiveSelector
from codecollector.formatter import OutputFormatter
from codecollector.splitter import write_collection_output
from codecollector.output import write_manifest, output_files_exist
from codecollector.uninstall import uninstall_package

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


class CodeCollectorApp:
    """Main application class for CodeCollector."""

    def __init__(self):
        self.config: Optional[CollectorConfig] = None
        self.collector: Optional[FileCollector] = None
        self.dry_run: bool = False
        self.force: bool = False

    def run_interactive(self, filter_mode: bool = False) -> None:
        """Run in interactive mode: select directory, then collect immediately."""
        self._print_banner()

        selected_path = InteractiveSelector.select_directory()

        if selected_path is None:
            console.print("\n[yellow]Exited[/yellow]")
            return

        console.print(f"\n[success]Collecting:[/success] [path]{selected_path}[/path]")
        if filter_mode:
            console.print("[dim]Filter mode: .gitignore enabled[/dim]")

        self.config = CollectorConfig.from_sources(
            root_path=selected_path,
            overrides={
                "recursive": True,
                "respect_gitignore": filter_mode,
            },
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
        filter_mode: bool = False,
        dry_run: bool = False,
        force: bool = False,
    ) -> None:
        """Run with a specific directory path."""
        target_path = Path(path_str).resolve()

        if not target_path.exists():
            console.print(f"[error]Directory not found: {target_path}[/error]")
            sys.exit(1)

        if not target_path.is_dir():
            console.print(f"[error]Not a directory: {target_path}[/error]")
            sys.exit(1)

        overrides: dict = {
            "recursive": recursive,
            "output_file": output_file,
            "respect_gitignore": filter_mode,
        }
        if max_output_size_mb is not None:
            overrides["max_output_size_mb"] = max_output_size_mb
        if output_dir is not None:
            overrides["output_dir"] = Path(output_dir)
        if exclude_dirs:
            overrides["extra_exclude_dirs"] = set(exclude_dirs)

        self.config = CollectorConfig.from_sources(
            root_path=target_path,
            config_file=config_file,
            overrides=overrides,
        )
        self.dry_run = dry_run
        self.force = force

        self._execute_collection()

    def _execute_collection(self) -> None:
        """Execute the code collection process."""
        console.print("\n[info]Collecting code files...[/info]")

        self.collector = FileCollector(self.config)

        with console.status("[cyan]Scanning...[/cyan]"):
            try:
                collected_files = self.collector.collect_files()
            except Exception as e:
                console.print(f"\n[error]Collection error: {e}[/error]")
                return

        if not collected_files:
            console.print("\n[warning]No matching code files found[/warning]")
            return

        if self.dry_run:
            self._print_dry_run(collected_files)
            return

        output_dir = self.config.output_dir or Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        if (
            self.config.auto_increment_output
            and not self.force
            and output_files_exist(output_dir, self.config.output_file)
        ):
            console.print(
                f"\n[warning]Output exists:[/warning] [path]{self.config.output_file}[/path] "
                "[dim](will auto-increment)[/dim]"
            )

        formatter = OutputFormatter()

        file_contents = [
            formatter.format_file_content(file_path, self.config.root_path)
            for file_path in collected_files
        ]
        summary = formatter.format_summary(
            collected_files, self.collector.skipped_files, self.config
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
            console.print(
                f"\n[info]Output renamed to avoid overwrite:[/info] "
                f"[path]{resolved_name}[/path]"
            )

        if len(output_paths) == 1:
            console.print(
                f"\n[info]Done:[/info] [path]{output_paths[0]}[/path]"
            )
        else:
            console.print(
                f"\n[info]Done ({len(output_paths)} parts):[/info]"
            )
            for p in output_paths:
                console.print(f"  [path]{p}[/path]")

        manifest_path = None
        if self.config.write_manifest and len(output_paths) > 1:
            manifest_path = write_manifest(
                output_dir,
                resolved_name,
                output_paths,
                self.config.root_path,
                len(collected_files),
            )
            console.print(f"  [dim]Manifest: {manifest_path.name}[/dim]")

        self._print_results(output_paths, collected_files, manifest_path)

    def _print_dry_run(self, collected_files: list) -> None:
        """Print dry-run preview without writing output."""
        console.print("\n[highlight]Dry Run[/highlight] [dim](no files written)[/dim]\n")

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

        output_dir = self.config.output_dir or Path.cwd()
        table.add_row("Output dir", str(output_dir))
        table.add_row("Output file", self.config.output_file)

        console.print(table)

        if self.collector.skipped_files and self.config.show_skipped:
            console.print("\n[warning]Skipped files (first 10):[/warning]")
            for fp, reason in self.collector.skipped_files[:10]:
                try:
                    rel = fp.relative_to(self.config.root_path)
                except ValueError:
                    rel = fp
                console.print(f"  [dim]• {rel}: {reason}[/dim]")
            if len(self.collector.skipped_files) > 10:
                console.print(f"  [dim]... and {len(self.collector.skipped_files) - 10} more[/dim]")

    def _print_results(
        self,
        output_paths: list,
        collected_files: list,
        manifest_path: Optional[Path] = None,
    ) -> None:
        """Print collection results."""
        console.print()

        table = Table(title="[bold cyan]Collection Results[/bold cyan]", show_header=False)
        table.add_column(style="bold cyan", width=20)
        table.add_column(style="white")

        table.add_row("Files collected", f"[success]{len(collected_files)}[/success]")

        if self.collector.skipped_files:
            table.add_row("Files skipped", f"[warning]{len(self.collector.skipped_files)}[/warning]")

        total_lines = 0
        total_size = 0
        file_types = set()

        for fp in collected_files:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    total_lines += f.read().count("\n") + 1
                total_size += fp.stat().st_size
                file_types.add(fp.suffix or "no_ext")
            except Exception:
                pass

        table.add_row("Total lines", f"{total_lines:,}")
        table.add_row("Total size", f"{total_size / 1024:.1f} KB")
        table.add_row("File types", str(len(file_types)))

        if len(output_paths) == 1:
            table.add_row("Output file", f"[path]{output_paths[0]}[/path]")
        else:
            table.add_row("Output files", f"[success]{len(output_paths)} parts[/success]")
            for p in output_paths:
                table.add_row("", f"[path]{p.name}[/path]")
            if manifest_path:
                table.add_row("Manifest", f"[path]{manifest_path.name}[/path]")

        console.print(table)

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

        console.print(Panel(tip, border_style="green"))

    @staticmethod
    def _print_banner() -> None:
        """Print application banner."""
        console.print()
        console.print(
            Panel(
                "[title]CodeCollector[/title]\n"
                "[subtitle]Select a directory → Enter → ready for LLM[/subtitle]\n"
                "[dim]v1.2.0[/dim]",
                border_style="cyan",
                padding=(1, 2),
            )
        )


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="CodeCollector - Collect project code for AI assistants",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  collect                        Select directory interactively, then collect
  collect -i                       Interactive mode with .gitignore filter
  collect .                        Collect current directory
  collect . -i                     Collect with .gitignore filter enabled
  collect /path/to/project         Collect specific directory
  collect . -n                     Non-recursive (current directory only)
  collect . -o output.md           Custom output filename
  collect . --max-output-size 5    Split output when exceeding 5MB per file
  collect . --dry-run              Preview without writing output
  collect . --force                Overwrite existing output files
  collect . -d ./output            Write output to specific directory
  collect . --exclude vendor       Extra directory to exclude
  collect --init-config            Initialize default configuration
  collect --uninstall              Uninstall codecollector (pipx/pip)
  collect --uninstall --purge-config  Uninstall and remove ~/.config/codecollector
        """,
    )

    parser.add_argument("path", nargs="?", help="Directory path to collect code from")
    parser.add_argument(
        "-i",
        action="store_true",
        help="Enable filter mode (respect .gitignore)",
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
        help="Uninstall codecollector (via pipx and/or pip)",
    )
    parser.add_argument(
        "--purge-config",
        action="store_true",
        help="Also remove ~/.config/codecollector (use with --uninstall)",
    )
    parser.add_argument("-v", "--version", action="version", version="CodeCollector v1.2.0")

    args = parser.parse_args()

    if args.uninstall:
        ok, messages = uninstall_package(purge_config=args.purge_config)
        for msg in messages:
            console.print(msg)
        sys.exit(0 if ok else 1)

    if args.purge_config and not args.uninstall:
        console.print("[error]--purge-config must be used with --uninstall[/error]")
        sys.exit(2)

    ensure_config_dir()

    if args.init_config:
        config = CollectorConfig(root_path=Path.cwd())
        config.save_to_file(str(CONFIG_FILE))
        console.print(f"[success]Config created:[/success] [path]{CONFIG_FILE}[/path]")
        return

    try:
        app = CodeCollectorApp()

        if not args.path and not args.config:
            app.run_interactive(filter_mode=args.i)
        else:
            app.run_with_path(
                path_str=args.path or ".",
                recursive=not args.non_recursive,
                output_file=args.output or "code_collection.md",
                max_output_size_mb=args.max_output_size,
                output_dir=args.output_dir,
                config_file=args.config,
                exclude_dirs=args.exclude,
                filter_mode=args.i,
                dry_run=args.dry_run,
                force=args.force,
            )

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[error]Error: {e}[/error]")
        sys.exit(1)


if __name__ == "__main__":
    main()
