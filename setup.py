#!/usr/bin/env python3
"""安装脚本"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme_path = Path(__file__).parent / 'README.md'
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ''

# 读取requirements
requirements_path = Path(__file__).parent / 'requirements.txt'
with open(requirements_path) as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='codecollector',
    version='1.0.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='📦 专业的代码收集工具 - 一键收集项目代码用于AI对话',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/codecollector',
    packages=find_packages(),
    scripts=['collect'],
    install_requires=requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'collect=codecollector.main:main',
        ],
    },
)