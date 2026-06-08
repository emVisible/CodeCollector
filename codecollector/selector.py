"""交互式选择器模块 - 使用Rich和Questionary实现美观的界面"""

import os
from pathlib import Path
from typing import Optional, List
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import print as rprint
from rich.theme import Theme

# 自定义主题
custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "red bold",
        "success": "green bold",
        "path": "blue",
        "highlight": "magenta bold",
    }
)

console = Console(theme=custom_theme)


class InteractiveSelector:
    """交互式目录选择器"""

    @staticmethod
    def select_directory(start_path: Optional[Path] = None) -> Optional[Path]:
        """交互式选择目录"""
        if start_path is None:
            start_path = Path.cwd()

        current_path = start_path.resolve()

        while True:
            # 清屏
            os.system("clear" if os.name != "nt" else "cls")

            # 显示头部
            console.print()
            console.print(
                Panel.fit(
                    "[bold cyan]📦 CodeCollector[/bold cyan] [dim]- 代码收集工具[/dim]",
                    border_style="cyan",
                )
            )

            # 显示当前路径
            path_text = Text()
            path_text.append("📁 当前目录: ", style="bold white")
            path_text.append(str(current_path), style="blue")
            console.print(path_text)
            console.print("─" * 60)

            # 获取并显示子目录
            try:
                items = sorted(current_path.iterdir())

                # 分离目录和文件
                dirs = [item for item in items if item.is_dir()]
                files = [item for item in items if item.is_file()]

                # 构建选择列表
                choices = []

                # 导航选项
                choices.append(questionary.Separator("─" * 30 + " 📂 导航 " + "─" * 30))
                if current_path != current_path.parent:
                    choices.append({"name": "  📤  .. (返回上级目录)", "value": ".."})
                choices.append({"name": "  ✅  . (选择当前目录)", "value": "."})

                # 子目录
                if dirs:
                    choices.append(
                        questionary.Separator("─" * 30 + " 📁 子目录 " + "─" * 30)
                    )
                    for d in dirs:
                        name = d.name
                        # 跳过隐藏目录
                        if name.startswith("."):
                            continue

                        # 添加图标
                        icon = "📁"
                        if "src" in name.lower():
                            icon = "💻"
                        elif "test" in name.lower():
                            icon = "🧪"
                        elif "doc" in name.lower():
                            icon = "📚"
                        elif "build" in name.lower():
                            icon = "🔨"
                        elif "config" in name.lower():
                            icon = "⚙️"

                        choices.append({"name": f"  {icon}  {name}/", "value": name})

                # 文件统计
                if files:
                    choices.append(
                        questionary.Separator("─" * 30 + " 📄 文件统计 " + "─" * 30)
                    )
                    code_files = [
                        f
                        for f in files
                        if f.suffix
                        in {
                            ".py",
                            ".js",
                            ".ts",
                            ".jsx",
                            ".tsx",
                            ".java",
                            ".cpp",
                            ".c",
                            ".go",
                            ".rs",
                            ".rb",
                            ".php",
                            ".swift",
                            ".vue",
                            ".svelte",
                        }
                    ]
                    choices.append(
                        {
                            "name": f"  📊 文件总数: {len(files)} (代码文件: {len(code_files)})",
                            "value": None,
                            "disabled": True,
                        }
                    )

                choices.append(questionary.Separator("─" * 60))
                choices.append({"name": "  ❌ 退出", "value": "quit"})

                # 使用questionary创建选择界面
                selected = questionary.select(
                    "请选择目录:",
                    choices=choices,
                    style=custom_style_fancy,
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
                    # 进入子目录
                    new_path = current_path / selected
                    if new_path.is_dir():
                        current_path = new_path
                    else:
                        console.print(f"\n[error]❌ 无法进入目录: {selected}[/error]")
                        console.input("[dim]按回车继续...[/dim]")

            except PermissionError:
                console.print("\n[error]❌ 没有访问权限[/error]")
                console.input("[dim]按回车继续...[/dim]")
                if current_path != current_path.parent:
                    current_path = current_path.parent
                else:
                    return None
            except KeyboardInterrupt:
                console.print("\n\n[yellow]👋 已取消[/yellow]")
                return None

    @staticmethod
    def select_mode() -> Optional[str]:
        """选择收集模式"""
        os.system("clear" if os.name != "nt" else "cls")

        console.print()
        console.print(
            Panel.fit("[bold cyan]📋 选择收集模式[/bold cyan]", border_style="cyan")
        )

        mode = questionary.select(
            "请选择模式:",
            choices=[
                questionary.Separator("─" * 40),
                {"name": "  📦  递归模式 - 收集所有子目录的文件", "value": "recursive"},
                {
                    "name": "  📄  非递归模式 - 仅收集当前目录的文件",
                    "value": "non_recursive",
                },
                questionary.Separator("─" * 40),
                {"name": "  ❌  退出", "value": "quit"},
            ],
            style=custom_style_fancy,
            qmark="👉",
            pointer="❯",
        ).ask()

        return mode if mode != "quit" else None


# 自定义样式
custom_style_fancy = questionary.Style(
    [
        ("qmark", "fg:#673ab7 bold"),
        ("question", "bold"),
        ("answer", "fg:#f44336 bold"),
        ("pointer", "fg:#673ab7 bold"),
        ("highlighted", "fg:#673ab7 bold"),
        ("selected", "fg:#cc5454"),
        ("separator", "fg:#cc5454"),
        ("instruction", ""),
        ("text", ""),
        ("disabled", "fg:#858585 italic"),
    ]
)
