"""Command-line interface for CodeCollector."""

import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

from codecollector.config import CollectorConfig, CONFIG_FILE, ensure_config_dir
from codecollector.collector import FileCollector
from codecollector.selector import InteractiveSelector
from codecollector.formatter import OutputFormatter

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

    def run_interactive(self) -> None:
        """Run in interactive mode with directory selection."""
        self._print_banner()

        console.print("\n[info]Select target directory...[/info]")
        selected_path = InteractiveSelector.select_directory()

        if selected_path is None:
            console.print("\n[yellow]Exited[/yellow]")
            return

        console.print(f"\n[success]Selected:[/success] [path]{selected_path}[/path]")

        mode = InteractiveSelector.select_mode()
        if mode is None:
            console.print("\n[yellow]Exited[/yellow]")
            return

        output_format = self._select_output_format()
        if output_format is None:
            console.print("\n[yellow]Exited[/yellow]")
            return

        self.config = CollectorConfig(
            root_path=selected_path,
            recursive=(mode == "recursive"),
            output_format=output_format,
        )

        self._execute_collection()

    def run_with_path(self, path_str: str, recursive: bool = True,
                      output_format: str = "detailed",
                      output_file: str = "code_collection.txt") -> None:
        """Run with a specific directory path."""
        target_path = Path(path_str).resolve()

        if not target_path.exists():
            console.print(f"[error]Directory not found: {target_path}[/error]")
            sys.exit(1)

        if not target_path.is_dir():
            console.print(f"[error]Not a directory: {target_path}[/error]")
            sys.exit(1)

        self.config = CollectorConfig(
            root_path=target_path,
            recursive=recursive,
            output_format=output_format,
            output_file=output_file,
        )

        self._execute_collection()

    def _select_output_format(self) -> Optional[str]:
        """Select output format interactively."""
        import questionary

        return questionary.select(
            "Select output format:",
            choices=[
                {"name": "  Detailed - Full information with separators", "value": "detailed"},
                {"name": "  Markdown - Suitable for Markdown-supported platforms", "value": "markdown"},
                {"name": "  Simple - Only filenames and content", "value": "simple"},
            ],
            qmark="👉",
            pointer="❯",
        ).ask()

    def _execute_collection(self) -> None:
        """Execute the code collection process."""
        console.print("\n[info]Analyzing directory structure...[/info]")

        self.collector = FileCollector(self.config)

        with console.status("[cyan]Collecting code files...[/cyan]"):
            try:
                collected_files = self.collector.collect_files()
            except Exception as e:
                console.print(f"\n[error]Collection error: {e}[/error]")
                return

        if not collected_files:
            console.print("\n[warning]No matching code files found[/warning]")
            return

        output_path = Path.cwd() / self.config.output_file
        formatter = OutputFormatter()

        console.print(f"\n[info]Generating output:[/info] [path]{output_path}[/path]")

        with open(output_path, "w", encoding="utf-8") as f:
            summary = formatter.format_summary(
                collected_files, self.collector.skipped_files, self.config
            )
            f.write(summary)

            for file_path in collected_files:
                content = formatter.format_file_content(
                    file_path, self.config.root_path, self.config.output_format
                )
                f.write(content)

        self._print_results(output_path, collected_files)

    def _print_results(self, output_path: Path, collected_files: list) -> None:
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
        table.add_row("Output file", f"[path]{output_path}[/path]")

        console.print(table)

        console.print(
            Panel(
                "[info]Tip: Copy the output file content directly to your AI assistant[/info]\n"
                f"[dim]File path: {output_path.absolute()}[/dim]",
                border_style="green",
            )
        )

    @staticmethod
    def _print_banner() -> None:
        """Print application banner."""
        console.print()
        console.print(
            Panel(
                "[title]CodeCollector[/title]\n"
                "[subtitle]Collect project code for AI assistant conversations[/subtitle]\n"
                "[dim]v1.0.0[/dim]",
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
  collect                        Interactive mode (recommended)
  collect .                      Collect current directory (recursive)
  collect . -n                   Collect current directory (non-recursive)
  collect /path/to/project       Collect specific directory
  collect . -f markdown          Markdown format output
  collect . -o output.txt        Custom output filename
  collect --init-config          Initialize default configuration
        """,
    )

    parser.add_argument("path", nargs="?", help="Directory path to collect code from")
    parser.add_argument("-i", "--interactive", action="store_true", help="Force interactive mode")
    parser.add_argument("-n", "--non-recursive", action="store_true", help="Non-recursive mode")
    parser.add_argument("-o", "--output", type=str, help="Output filename")
    parser.add_argument("-f", "--format", choices=["detailed", "markdown", "simple"], help="Output format")
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument("--init-config", action="store_true", help="Initialize default config")
    parser.add_argument("-v", "--version", action="version", version="CodeCollector v1.0.0")

    args = parser.parse_args()

    ensure_config_dir()

    if args.init_config:
        config = CollectorConfig(root_path=Path.cwd())
        config.save_to_file(str(CONFIG_FILE))
        console.print(f"[success]Config created:[/success] [path]{CONFIG_FILE}[/path]")
        return

    try:
        app = CodeCollectorApp()

        if args.interactive or (not args.path and not args.config):
            app.run_interactive()
        else:
            app.run_with_path(
                path_str=args.path or ".",
                recursive=not args.non_recursive,
                output_format=args.format or "detailed",
                output_file=args.output or "code_collection.txt",
            )

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[error]Error: {e}[/error]")
        sys.exit(1)


if __name__ == "__main__":
    main()