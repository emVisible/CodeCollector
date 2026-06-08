"""主程序模块"""

import sys
import os
from pathlib import Path
from typing import Optional, List
import argparse

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich import print as rprint
from rich.theme import Theme
from codecollector.config import CollectorConfig, CONFIG_DIR, CONFIG_FILE, ensure_config_dir
from codecollector.collector import FileCollector
from codecollector.selector import InteractiveSelector
from codecollector.formatter import OutputFormatter


# 自定义主题
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


class CodeCollector:
    """代码收集器主类"""

    def __init__(self):
        self.config: Optional[CollectorConfig] = None
        self.collector: Optional[FileCollector] = None

    def run(self, args):
        """运行收集器"""
        if args.interactive or (not args.path and not args.config):
            self.run_interactive()
        else:
            self.run_command_line(args)

    def run_interactive(self):
        """交互模式"""
        self._print_banner()

        # 选择目录
        console.print("\n[info]📌 开始选择目标目录...[/info]")
        selected_path = InteractiveSelector.select_directory()

        if selected_path is None:
            console.print("\n[yellow]👋 已退出[/yellow]")
            return

        console.print(f"\n[success]✅ 已选择目录:[/success] [path]{selected_path}[/path]")

        # 选择模式
        mode = InteractiveSelector.select_mode()
        if mode is None:
            console.print("\n[yellow]👋 已退出[/yellow]")
            return

        # 选择输出格式
        output_format = self._select_output_format()
        if output_format is None:
            console.print("\n[yellow]👋 已退出[/yellow]")
            return

        # 创建配置
        self.config = CollectorConfig(
            root_path=selected_path,
            recursive=(mode == 'recursive'),
            output_format=output_format
        )

        # 执行收集
        self._execute_collection()

    def run_command_line(self, args):
        """命令行模式"""
        # 确定目标路径
        if args.path:
            target_path = Path(args.path).resolve()
        else:
            target_path = Path.cwd()

        if not target_path.exists():
            console.print(f"[error]❌ 目录不存在: {target_path}[/error]")
            sys.exit(1)

        # 加载或创建配置
        if args.config:
            try:
                self.config = CollectorConfig.load_from_file(args.config)
                self.config.root_path = target_path
            except Exception as e:
                console.print(f"[error]❌ 配置文件加载失败: {e}[/error]")
                sys.exit(1)
        else:
            self.config = CollectorConfig(
                root_path=target_path,
                recursive=not args.non_recursive,
                output_format=args.format or 'detailed',
                output_file=args.output or 'code_collection.txt'
            )

        # 执行收集
        self._execute_collection()

    def _select_output_format(self) -> Optional[str]:
        """选择输出格式"""
        import questionary

        format_choice = questionary.select(
            "选择输出格式:",
            choices=[
                {
                    'name': '  📋 详细格式 - 包含完整文件信息和分隔符',
                    'value': 'detailed'
                },
                {
                    'name': '  📝 Markdown格式 - 适合粘贴到支持Markdown的平台',
                    'value': 'markdown'
                },
                {
                    'name': '  📄 简单格式 - 仅文件名和内容',
                    'value': 'simple'
                },
            ],
            style=fancy_style,
            qmark='👉',
            pointer='❯'
        ).ask()

        return format_choice

    def _execute_collection(self):
        """执行代码收集"""
        console.print("\n[info]🔍 正在分析目录结构...[/info]")

        # 创建收集器
        self.collector = FileCollector(self.config)

        # 使用Rich进度条
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            task = progress.add_task("[cyan]收集代码文件中...", total=None)

            # 收集文件
            try:
                collected_files = self.collector.collect_files(progress)
                progress.update(task, completed=100, description="[green]收集完成!")
            except Exception as e:
                console.print(f"\n[error]❌ 收集过程出错: {e}[/error]")
                return

        if not collected_files:
            console.print("\n[warning]⚠️  没有找到符合条件的代码文件[/warning]")
            return

        # 生成输出
        output_path = Path.cwd() / self.config.output_file
        formatter = OutputFormatter()

        console.print(f"\n[info]📝 正在生成输出文件:[/info] [path]{output_path}[/path]")

        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入摘要
            summary = formatter.format_summary(
                collected_files,
                self.collector.skipped_files,
                self.config
            )
            f.write(summary)

            # 写入文件内容
            for file_path in collected_files:
                content = formatter.format_file_content(
                    file_path,
                    self.config.root_path,
                    self.config.output_format
                )
                f.write(content)

        # 显示结果
        self._print_results(output_path, collected_files)

    def _print_results(self, output_path: Path, collected_files: List[Path]):
        """打印结果"""
        console.print()

        # 创建结果表格
        table = Table(title="[bold cyan]📊 收集结果[/bold cyan]", show_header=False)
        table.add_column(style="bold cyan", width=20)
        table.add_column(style="white")

        table.add_row("✅ 收集文件数", f"[success]{len(collected_files)}[/success]")

        if self.collector.skipped_files:
            table.add_row("⏭️  跳过文件数", f"[warning]{len(self.collector.skipped_files)}[/warning]")

        # 计算统计信息
        total_lines = 0
        total_size = 0
        file_types = set()
        for fp in collected_files:
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    total_lines += f.read().count('\n') + 1
                total_size += fp.stat().st_size
                file_types.add(fp.suffix or 'no_ext')
            except:
                pass

        table.add_row("📊 总代码行数", f"{total_lines:,}")
        table.add_row("💾 总文件大小", f"{total_size / 1024:.1f} KB")
        table.add_row("📁 文件类型数", str(len(file_types)))
        table.add_row("📄 输出文件", f"[path]{output_path}[/path]")

        console.print(table)

        console.print(Panel(
            "[info]💡 提示: 可以直接将输出文件的内容复制给AI助手[/info]\n"
            "[dim]文件路径: {0}[/dim]".format(output_path.absolute()),
            border_style="green"
        ))

    def _print_banner(self):
        """打印横幅"""
        console.print()
        console.print(Panel(
            "[title]📦 CodeCollector[/title]\n"
            "[subtitle]一键收集项目代码，方便与AI助手对话[/subtitle]\n"
            "[dim]v1.0.0 - 专业的代码收集工具[/dim]",
            border_style="cyan",
            padding=(1, 2)
        ))


# questionary样式
fancy_style = None  # 将在需要时导入

def main():
    """主入口函数"""
    # 确保配置目录存在
    ensure_config_dir()

    parser = argparse.ArgumentParser(
        description='📦 CodeCollector - 专业的代码收集工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  collect                          交互模式（推荐）
  collect .                        收集当前目录（递归）
  collect . -n                     收集当前目录（非递归）
  collect /path/to/project         收集指定目录
  collect . -f markdown            Markdown格式输出
  collect . -o output.txt          指定输出文件名
  collect --config config.json     使用配置文件

更多信息: https://github.com/yourusername/codecollector
        """
    )

    parser.add_argument(
        'path',
        nargs='?',
        help='要收集代码的目录路径'
    )

    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='强制使用交互模式'
    )

    parser.add_argument(
        '-n', '--non-recursive',
        action='store_true',
        help='非递归模式（仅当前目录）'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='输出文件名（默认: code_collection.txt）'
    )

    parser.add_argument(
        '-f', '--format',
        choices=['detailed', 'markdown', 'simple'],
        help='输出格式'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )

    parser.add_argument(
        '--init-config',
        action='store_true',
        help='初始化默认配置文件'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='CodeCollector v1.0.0'
    )

    args = parser.parse_args()

    # 初始化配置文件
    if args.init_config:
        config = CollectorConfig(root_path=Path.cwd())
        config.save_to_file(str(CONFIG_FILE))
        console.print(f"[success]✅ 配置文件已创建:[/success] [path]{CONFIG_FILE}[/path]")
        return

    try:
        app = CodeCollector()
        app.run(args)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 已取消[/yellow]")
    except Exception as e:
        console.print(f"\n[error]❌ 错误: {e}[/error]")
        sys.exit(1)


if __name__ == '__main__':
    main()