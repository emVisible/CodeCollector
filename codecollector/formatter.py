"""输出格式化器模块"""

from pathlib import Path
from typing import List, Tuple
from datetime import datetime
from codecollector.config import CollectorConfig


class OutputFormatter:
    """输出格式化器"""

    @staticmethod
    def format_file_content(
        file_path: Path, relative_to: Path, format_type: str = "detailed"
    ) -> str:
        """格式化单个文件内容"""
        relative_path = file_path.relative_to(relative_to)

        if format_type == "markdown":
            return OutputFormatter._format_markdown(file_path, relative_path)
        elif format_type == "simple":
            return OutputFormatter._format_simple(file_path, relative_path)
        else:  # detailed
            return OutputFormatter._format_detailed(file_path, relative_path)

    @staticmethod
    def _format_detailed(file_path: Path, relative_path: Path) -> str:
        """详细格式"""
        separator = "=" * 80
        file_info = f"📄 文件: {relative_path}"
        file_size = f"📏 大小: {file_path.stat().st_size:,} 字节"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 统计行数
            line_count = content.count("\n") + 1

            return (
                f"{separator}\n"
                f"{file_info}\n"
                f"{'─' * 80}\n"
                f"📊 行数: {line_count} | {file_size}\n"
                f"{separator}\n\n"
                f"{content}\n\n"
            )
        except Exception as e:
            return (
                f"{separator}\n"
                f"{file_info}\n"
                f"{'─' * 80}\n"
                f"❌ 读取失败: {e}\n"
                f"{separator}\n\n"
            )

    @staticmethod
    def _format_markdown(file_path: Path, relative_path: Path) -> str:
        """Markdown格式"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            extension = file_path.suffix.lstrip(".")
            if not extension:
                extension = "text"

            return (
                f"## 📄 {relative_path}\n\n"
                f"```{extension}\n"
                f"{content}\n"
                f"```\n\n"
            )
        except Exception as e:
            return f"## ❌ {relative_path}\n\n读取失败: {e}\n\n"

    @staticmethod
    def _format_simple(file_path: Path, relative_path: Path) -> str:
        """简单格式"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return f"--- {relative_path} ---\n{content}\n\n"
        except Exception as e:
            return f"--- {relative_path} ---\n读取失败: {e}\n\n"

    @staticmethod
    def format_summary(
        collected_files: List[Path],
        skipped_files: List[Tuple[Path, str]],
        config: CollectorConfig,
    ) -> str:
        """格式化摘要信息"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 计算总行数
        total_lines = 0
        total_size = 0
        for file_path in collected_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    total_lines += f.read().count("\n") + 1
                total_size += file_path.stat().st_size
            except:
                pass

        summary = []
        summary.append("=" * 80)
        summary.append("📦 代码收集器 - 收集摘要")
        summary.append("=" * 80)
        summary.append(f"🕐 生成时间: {now}")
        summary.append(f"📁 根目录: {config.root_path.absolute()}")
        summary.append(f"📋 收集模式: {'递归' if config.recursive else '非递归'}")
        summary.append("─" * 80)
        summary.append(f"✅ 收集文件数: {len(collected_files)}")
        summary.append(f"📊 总代码行数: {total_lines:,}")
        summary.append(f"💾 总文件大小: {total_size / 1024:.1f} KB")

        if skipped_files:
            summary.append("─" * 80)
            summary.append(f"⏭️  跳过的文件: {len(skipped_files)} 个")
            for file_path, reason in skipped_files[:5]:
                try:
                    rel_path = file_path.relative_to(config.root_path)
                    summary.append(f"  • {rel_path}")
                    summary.append(f"    原因: {reason}")
                except ValueError:
                    summary.append(f"  • {file_path}")
                    summary.append(f"    原因: {reason}")
            if len(skipped_files) > 5:
                summary.append(f"  ... 以及另外 {len(skipped_files) - 5} 个文件")

        summary.append("─" * 80)
        summary.append("📝 文件列表:")

        # 按类型分组显示
        files_by_type = {}
        for file_path in collected_files:
            ext = file_path.suffix or "no_ext"
            if ext not in files_by_type:
                files_by_type[ext] = []
            try:
                rel_path = file_path.relative_to(config.root_path)
                files_by_type[ext].append(rel_path)
            except ValueError:
                files_by_type[ext].append(file_path)

        for ext, files in sorted(files_by_type.items()):
            summary.append(f"\n  [{ext}] ({len(files)} 个文件)")
            for f in files[:3]:  # 每种类型最多显示3个
                summary.append(f"    ✓ {f}")
            if len(files) > 3:
                summary.append(f"    ... 还有 {len(files) - 3} 个文件")

        summary.append("\n" + "=" * 80)
        summary.append("📖 以下是收集的代码内容:")
        summary.append("=" * 80 + "\n")

        return "\n".join(summary)
