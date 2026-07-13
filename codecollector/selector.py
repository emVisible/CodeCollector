"""Interactive directory selector module."""

import os
from pathlib import Path
from typing import Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from rich.text import Text

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold",
    "path": "blue",
})

console = Console(theme=custom_theme)

custom_style = questionary.Style([
    ("qmark", "fg:#673ab7 bold"),
    ("question", "bold"),
    ("answer", "fg:#f44336 bold"),
    ("pointer", "fg:#673ab7 bold"),
    ("highlighted", "fg:#673ab7 bold"),
    ("selected", "fg:#cc5454"),
    ("separator", "fg:#cc5454"),
    ("disabled", "fg:#858585 italic"),
])


class InteractiveSelector:
    """Interactive directory selector with keyboard navigation."""

    @staticmethod
    def select_directory(start_path: Optional[Path] = None) -> Optional[Path]:
        """Interactively select a directory to collect."""
        if start_path is None:
            start_path = Path.cwd()

        current_path = start_path.resolve()

        while True:
            os.system("clear" if os.name != "nt" else "cls")

            console.print()
            console.print(Panel.fit(
                "[bold cyan]CodeCollector[/bold cyan] [dim]- Select directory, press Enter to collect[/dim]",
                border_style="cyan",
            ))

            path_text = Text()
            path_text.append("Directory: ", style="bold white")
            path_text.append(str(current_path), style="blue")
            console.print(path_text)
            console.print("─" * 60)

            try:
                items = sorted(current_path.iterdir())
                dirs = [item for item in items if item.is_dir() and not item.name.startswith(".")]

                choices = []

                choices.append(questionary.Separator("─" * 28 + " Collect " + "─" * 28))
                choices.append({
                    "name": "  ✅  Collect this directory",
                    "value": ".",
                })

                choices.append(questionary.Separator("─" * 28 + " Navigate " + "─" * 28))
                if current_path != current_path.parent:
                    choices.append({"name": "  ⬆️  .. (parent directory)", "value": ".."})

                for d in dirs:
                    choices.append({"name": f"  📁  {d.name}/", "value": d.name})

                choices.append(questionary.Separator("─" * 60))
                choices.append({"name": "  Exit", "value": "quit"})

                selected = questionary.select(
                    "Select:",
                    choices=choices,
                    style=custom_style,
                    use_indicator=True,
                    qmark="👉",
                    pointer="❯",
                ).ask()

                if selected is None or selected == "quit":
                    return None
                elif selected == "..":
                    current_path = current_path.parent
                elif selected == ".":
                    return current_path
                else:
                    new_path = current_path / selected
                    if new_path.is_dir():
                        current_path = new_path
                    else:
                        console.print(f"\n[error]Cannot enter: {selected}[/error]")
                        console.input("[dim]Press Enter to continue...[/dim]")

            except PermissionError:
                console.print("\n[error]Permission denied[/error]")
                console.input("[dim]Press Enter to continue...[/dim]")
                if current_path != current_path.parent:
                    current_path = current_path.parent
                else:
                    return None
            except KeyboardInterrupt:
                console.print("\n\n[yellow]Cancelled[/yellow]")
                return None
