"""配置管理模块"""

from dataclasses import dataclass, field
from typing import Set, List, Dict
from pathlib import Path
import json
import os


@dataclass
class CollectorConfig:
    """收集器配置"""
    root_path: Path
    recursive: bool = True
    output_file: str = "code_collection.txt"

    # 排除目录
    exclude_dirs: Set[str] = field(default_factory=lambda: {
        '__pycache__', '.git', '.svn', '.hg',
        'node_modules', 'venv', '.venv', 'env', '.env',
        '.idea', '.vscode', 'build', 'dist', 'target',
        '.eggs', '*.egg-info', '.tox', '.mypy_cache',
        '.pytest_cache', '__pypackages__', '.next',
        '.nuxt', '.output', 'coverage', '.coverage',
        'tmp', 'temp', 'logs', 'vendor', 'bower_components'
    })

    # 包含的文件扩展名
    include_extensions: Set[str] = field(default_factory=lambda: {
        # Web
        '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte', '.astro',
        '.html', '.htm', '.css', '.scss', '.sass', '.less',
        # Python
        '.py', '.pyx', '.pyi', '.ipynb',
        # Java/Kotlin
        '.java', '.kt', '.kts', '.groovy',
        # C/C++
        '.c', '.cpp', '.h', '.hpp', '.cc', '.cxx',
        # Go
        '.go', '.mod', '.sum',
        # Rust
        '.rs', '.toml',
        # Ruby
        '.rb', '.rake', '.gemspec',
        # PHP
        '.php', '.phtml',
        # Swift
        '.swift',
        # Shell
        '.sh', '.bash', '.zsh', '.fish',
        # Config
        '.yml', '.yaml', '.json', '.xml', '.toml',
        '.cfg', '.ini', '.conf', '.env', '.env.example',
        # Documentation
        '.md', '.mdx', '.rst', '.txt', '.log',
        # Docker/K8s
        'Dockerfile', '.dockerignore',
        'docker-compose.yml', 'docker-compose.yaml',
        # Others
        '.sql', '.graphql', '.gql', '.proto',
        '.gitignore', '.gitattributes',
        'Makefile', 'CMakeLists.txt',
        '.editorconfig', '.prettierrc',
    })

    # 特殊文件名（无扩展名）
    special_files: Set[str] = field(default_factory=lambda: {
        'Dockerfile', 'Makefile', 'Vagrantfile', 'Gemfile',
        'Rakefile', 'Procfile', 'CMakeLists.txt',
        '.gitignore', '.dockerignore', '.env',
        '.editorconfig', '.prettierrc', '.eslintrc',
    })

    # 文件大小限制（MB）
    max_file_size_mb: float = 5.0

    # 显示选项
    show_progress: bool = True
    show_skipped: bool = True
    color_output: bool = True

    # 输出格式
    output_format: str = "detailed"  # detailed, simple, markdown

    @classmethod
    def load_from_file(cls, filepath: str) -> 'CollectorConfig':
        """从配置文件加载"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def save_to_file(self, filepath: str):
        """保存配置到文件"""
        config_dict = {
            'exclude_dirs': list(self.exclude_dirs),
            'include_extensions': list(self.include_extensions),
            'max_file_size_mb': self.max_file_size_mb,
        }
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)


# 全局配置路径
CONFIG_DIR = Path.home() / '.config' / 'codecollector'
CONFIG_FILE = CONFIG_DIR / 'config.json'

def ensure_config_dir():
    """确保配置目录存在"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)