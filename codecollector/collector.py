"""文件收集器模块"""

import os
from pathlib import Path
from typing import List, Set, Optional, Callable, Tuple
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from codecollector.config import CollectorConfig


class FileCollector:
    """文件收集器"""

    def __init__(self, config: CollectorConfig):
        self.config = config
        self.collected_files: List[Path] = []
        self.skipped_files: List[Tuple[Path, str]] = []

    def should_collect_file(self, file_path: Path) -> bool:
        """判断是否应该收集该文件"""
        # 检查是否为文件
        if not file_path.is_file():
            return False

        # 检查符号链接
        if file_path.is_symlink():
            self.skipped_files.append((file_path, "符号链接"))
            return False

        # 检查文件大小
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > self.config.max_file_size_mb:
                self.skipped_files.append(
                    (
                        file_path,
                        f"文件过大 ({size_mb:.1f}MB > {self.config.max_file_size_mb}MB)",
                    )
                )
                return False
        except OSError as e:
            self.skipped_files.append((file_path, f"无法访问 ({e})"))
            return False

        # 检查文件名
        file_name = file_path.name

        # 检查特殊文件
        if file_name in self.config.special_files:
            return self._is_text_file(file_path)

        # 检查扩展名
        suffix = file_path.suffix.lower()
        if suffix in self.config.include_extensions:
            return self._is_text_file(file_path)

        # 检查点文件
        if file_name.startswith("."):
            for ext in self.config.include_extensions:
                if ext.startswith(".") and file_name.endswith(ext.lstrip(".")):
                    return self._is_text_file(file_path)

        return False

    def _is_text_file(self, file_path: Path) -> bool:
        """检查是否为文本文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # 尝试读取前几个字符
                chunk = f.read(1024)
                # 检查是否包含空字节（二进制文件特征）
                if "\0" in chunk:
                    self.skipped_files.append((file_path, "二进制文件"))
                    return False
            return True
        except UnicodeDecodeError:
            self.skipped_files.append((file_path, "编码错误"))
            return False
        except IOError as e:
            self.skipped_files.append((file_path, f"读取错误 ({e})"))
            return False

    def _should_exclude_dir(self, dir_path: Path) -> bool:
        """检查目录是否应该排除"""
        parts = dir_path.parts

        # 检查完整路径中是否包含排除目录
        for part in parts:
            if part in self.config.exclude_dirs:
                return True

            # 支持通配符匹配
            for exclude_pattern in self.config.exclude_dirs:
                if exclude_pattern.startswith("*") and part.endswith(
                    exclude_pattern[1:]
                ):
                    return True

        # 检查隐藏目录（以.开头，除了.git）
        dir_name = dir_path.name
        if dir_name.startswith(".") and dir_name != ".git":
            # 但保留一些有用的隐藏目录
            if dir_name not in {".github", ".vscode", ".idea"}:
                return True

        return False

    def collect_files(self, progress=None) -> List[Path]:
        """收集文件"""
        self.collected_files.clear()
        self.skipped_files.clear()

        root = self.config.root_path

        if not root.exists():
            raise FileNotFoundError(f"目录不存在: {root}")

        if not root.is_dir():
            raise NotADirectoryError(f"路径不是目录: {root}")

        # 使用os.walk进行更高效的遍历
        if self.config.recursive:
            for dirpath, dirnames, filenames in os.walk(root):
                current_dir = Path(dirpath)

                # 过滤目录
                dirnames[:] = [
                    d for d in dirnames if not self._should_exclude_dir(current_dir / d)
                ]

                # 处理文件
                for filename in filenames:
                    file_path = current_dir / filename
                    if self.should_collect_file(file_path):
                        self.collected_files.append(file_path)

        else:
            # 非递归模式
            for item in root.iterdir():
                if item.is_file() and self.should_collect_file(item):
                    self.collected_files.append(item)

        # 按路径排序
        self.collected_files.sort()
        return self.collected_files


# 需要导入os
import os
