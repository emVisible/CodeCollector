# 📦 CodeCollector

<div align="center">

![CodeCollector](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/platform-linux%20|%20macos%20|%20windows-lightgrey.svg)

**一键收集项目代码，让AI助手更懂你的项目**

[特性](#-特性) • [安装](#-安装) • [快速开始](#-快速开始) • [使用指南](#-使用指南) • [配置](#-配置)

</div>

---

## 📖 为什么需要 CodeCollector？

在与 ChatGPT、Claude 等 AI 助手对话时，我们经常需要粘贴项目代码来获取帮助。手动逐个打开文件、复制粘贴不仅耗时，还容易遗漏关键文件。

**CodeCollector** 解决了这个问题：
- ✅ **一键收集**整个项目的代码文件
- ✅ **智能过滤**，自动排除 node_modules、.git 等无关目录
- ✅ **格式化输出**，生成结构清晰的单个文件
- ✅ **美观界面**，方向键选择目录，彩色终端输出

## ✨ 特性

<details open>
<summary><b>核心功能</b></summary>

- 🎨 **美观的交互界面** — 基于 Rich 和 Questionary，支持方向键选择，彩色输出
- 📁 **智能目录导航** — 直观的文件系统浏览器，轻松定位目标目录
- 🔍 **双模式收集** — 递归模式（包含子目录）/ 非递归模式（仅当前目录）
- 📊 **详细统计信息** — 代码行数、文件大小、文件类型分布一目了然
- 🎯 **智能过滤系统** — 自动排除二进制文件、超大文件、无关目录
- 📝 **多种输出格式** — Detailed（详细）/ Markdown / Simple（简洁）
- ⚡ **高性能扫描** — 优化的文件遍历算法，大型项目也能快速完成
- 🔧 **可定制配置** — 支持自定义排除目录、文件类型、大小限制等

</details>

## 📸 效果预览

### 交互式界面
```
╔══════════════════════════════════════════════════╗
║              📦 CodeCollector                     ║
║      一键收集项目代码，方便与AI助手对话           ║
║                  v1.0.0                           ║
╚══════════════════════════════════════════════════╝

📁 当前目录: /home/user/awesome-project
──────────────────────────────────────────────────
  📤  .. (返回上级目录)
  ✅  .  (选择当前目录)
──────────────────────────────────────────────────
  💻  src/
  🧪  tests/
  📚  docs/
  ⚙️  config/
  📦  components/
  🔧  utils/
──────────────────────────────────────────────────
  📊 文件总数: 156 (代码文件: 98)
  ❌  退出
```

### 收集结果展示
```
╔══════════════════════════════════════════════════╗
║              📊 收集结果                          ║
╠══════════════════════════════════════════════════╣
║ ✅ 收集文件数     │ 45                            ║
║ ⏭️  跳过文件数    │ 12                            ║
║ 📊 总代码行数     │ 8,234                         ║
║ 💾 总文件大小     │ 256.3 KB                      ║
║ 📁 文件类型数     │ 8                             ║
║ 📄 输出文件       │ code_collection.txt           ║
╚══════════════════════════════════════════════════╝
```

## 📦 安装

### 系统要求
- Python 3.8 或更高版本
- pip 包管理器

### 方式一：从 GitHub 克隆安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/codecollector.git
cd codecollector

# 安装依赖并安装工具
pip install -e .

# 验证安装
collect --version
```

### 方式二：使用 pip 直接安装

```bash
pip install git+https://github.com/yourusername/codecollector.git
```

### 方式三：一键安装脚本

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/codecollector/main/install.sh | bash
```

### 方式四：手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/codecollector.git
cd codecollector

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建命令链接
sudo cp collect /usr/local/bin/collect
sudo chmod +x /usr/local/bin/collect

# 或添加到用户路径
mkdir -p ~/.local/bin
cp collect ~/.local/bin/collect
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 🚀 快速开始

### 最简单的用法

```bash
# 进入你的项目目录
cd my-awesome-project

# 运行收集器
collect .
```

就这么简单！会在当前目录生成 `code_collection.txt` 文件。

### 常用命令

```bash
# 交互模式（推荐新手使用）
collect

# 收集当前目录（递归，包含所有子目录）
collect .

# 收集指定目录
collect /path/to/your/project

# 仅收集当前目录的文件（不包含子目录）
collect . --non-recursive
# 或简写
collect . -n

# 指定输出文件名
collect . --output my_project_code.txt
# 或简写
collect . -o my_project_code.txt

# 使用 Markdown 格式输出（适合粘贴到 GitHub Issues）
collect . --format markdown
# 或简写
collect . -f markdown
```

## 📚 使用指南

### 交互模式详解

运行 `collect`（不带参数）进入交互模式：

1. **选择目录**：使用 `↑` `↓` 方向键浏览目录，按 `Enter` 进入子目录
2. **导航操作**：
   - 选择 `..` 返回上级目录
   - 选择 `.` 确认当前目录
   - 选择 `退出` 取消操作
3. **选择模式**：
   - `递归模式` — 收集所有子目录的文件
   - `非递归模式` — 仅收集当前目录的文件
4. **选择格式**：
   - `详细格式` — 包含完整文件信息和分隔符
   - `Markdown格式` — 适合粘贴到支持 Markdown 的平台
   - `简单格式` — 仅文件名和内容

### 命令行参数

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `path` | — | 目标目录路径 | `collect ./src` |
| `--non-recursive` | `-n` | 非递归模式 | `collect . -n` |
| `--output` | `-o` | 输出文件名 | `collect . -o code.txt` |
| `--format` | `-f` | 输出格式 | `collect . -f markdown` |
| `--interactive` | `-i` | 强制交互模式 | `collect -i` |
| `--config` | — | 配置文件路径 | `collect --config my.json` |
| `--init-config` | — | 生成默认配置 | `collect --init-config` |
| `--version` | `-v` | 显示版本号 | `collect -v` |
| `--help` | `-h` | 显示帮助信息 | `collect -h` |

### 输出格式对比

**Detailed 格式**（默认）：
```
================================================================================
📄 文件: src/main.py
────────────────────────────────────────────────────────────────────────────────
📊 行数: 156 | 📏 大小: 4,523 字节
================================================================================

[文件内容...]
```

**Markdown 格式**：
```markdown
## 📄 src/main.py

```python
[文件内容...]
```
```

**Simple 格式**：
```
--- src/main.py ---
[文件内容...]
```

## ⚙️ 配置

### 初始化配置文件

```bash
collect --init-config
```

会在 `~/.config/codecollector/config.json` 创建默认配置文件。

### 配置文件示例

```json
{
  "exclude_dirs": [
    "node_modules",
    ".git",
    "__pycache__",
    "venv",
    "dist",
    "build"
  ],
  "include_extensions": [
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".vue",
    ".go",
    ".rs"
  ],
  "special_files": [
    "Dockerfile",
    "Makefile",
    ".env.example",
    ".gitignore"
  ],
  "max_file_size_mb": 5.0,
  "output_format": "detailed",
  "show_progress": true,
  "show_skipped": true
}
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `exclude_dirs` | `string[]` | `["node_modules", ".git", ...]` | 排除的目录列表 |
| `include_extensions` | `string[]` | `[".py", ".js", ...]` | 包含的文件扩展名 |
| `special_files` | `string[]` | `["Dockerfile", ...]` | 特殊文件名（无扩展名） |
| `max_file_size_mb` | `float` | `5.0` | 最大文件大小（MB） |
| `output_format` | `string` | `"detailed"` | 输出格式 |
| `show_progress` | `bool` | `true` | 是否显示进度条 |
| `show_skipped` | `bool` | `true` | 是否显示跳过的文件 |

### 使用自定义配置

```bash
# 使用自定义配置文件
collect . --config my_custom_config.json

# 为特定项目创建配置
cd my-project
collect --init-config
# 编辑 ~/.config/codecollector/config.json
collect .
```

## 🎯 典型使用场景

### 场景 1：向 AI 助手提问

```bash
# 1. 收集项目代码
cd my-buggy-project
collect . -o for_ai.txt

# 2. 打开文件，复制全部内容
cat for_ai.txt | xclip -selection clipboard  # Linux
# 或直接打开文件 Ctrl+A, Ctrl+C

# 3. 粘贴到 ChatGPT/Claude，附上问题
```

### 场景 2：代码审查

```bash
# 收集最近修改的文件
git diff --name-only HEAD~5 | grep -E '\.(py|js|ts)$' > changed_files.txt

# 或直接收集整个模块
collect ./src/modules/user-auth -o review_code.txt
```

### 场景 3：生成项目文档

```bash
# 收集源码并输出为 Markdown
collect ./src -f markdown -o project_source.md

# 可以在 Markdown 文件中直接查看代码
```

### 场景 4：定期备份关键代码

```bash
# 创建备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
collect /path/to/project -o "backup_${DATE}.txt"
```

## 🛠️ 技术架构

```
codecollector/
├── collect                 # 命令行入口
├── src/
│   ├── __init__.py        # 包初始化
│   ├── main.py            # 主程序逻辑
│   ├── config.py          # 配置管理
│   ├── collector.py       # 文件收集器
│   ├── selector.py        # 交互式选择器
│   └── formatter.py       # 输出格式化器
├── setup.py               # 安装脚本
├── requirements.txt       # 依赖列表
└── README.md             # 项目文档
```

### 核心依赖

| 库 | 版本 | 用途 |
|----|------|------|
| [Rich](https://github.com/Textualize/rich) | ≥13.0.0 | 终端美化、进度条 |
| [Questionary](https://github.com/tmbo/questionary) | ≥2.0.0 | 交互式选择菜单 |
| [Pathspec](https://github.com/cpburnz/python-pathspec) | ≥0.11.0 | Gitignore 风格路径匹配 |

## 🤝 贡献指南

欢迎各种形式的贡献！无论是新功能、Bug修复还是文档改进。

### 如何贡献

1. **Fork 本仓库**
2. **创建特性分支**：`git checkout -b feature/amazing-feature`
3. **提交更改**：`git commit -m 'Add amazing feature'`
4. **推送到分支**：`git push origin feature/amazing-feature`
5. **创建 Pull Request**

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/codecollector.git
cd codecollector

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/
```

## ❓ 常见问题

<details>
<summary><b>Q: 为什么某些文件没有被收集？</b></summary>

可能的原因：
- 文件在排除目录中（如 `node_modules`、`.git`）
- 文件扩展名不在包含列表中
- 文件大小超过限制（默认 5MB）
- 文件是二进制格式

可以通过查看输出文件开头的摘要信息了解跳过的文件。
</details>

<details>
<summary><b>Q: 如何添加自定义文件类型？</b></summary>

使用配置文件：
```bash
collect --init-config
# 编辑 ~/.config/codecollector/config.json
# 在 include_extensions 中添加你的文件扩展名
```
</details>

<details>
<summary><b>Q: 支持 Windows 吗？</b></summary>

完全支持！在 Windows 上使用相同的命令，交互界面会自动适配。
</details>

<details>
<summary><b>Q: 输出文件太大怎么办？</b></summary>

可以：
1. 使用非递归模式：`collect . -n`
2. 限制文件大小：在配置中减小 `max_file_size_mb`
3. 针对特定子目录：`collect ./src`
</details>

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🌟 致谢

- [Rich](https://github.com/Textualize/rich) - 让终端变得美丽
- [Questionary](https://github.com/tmbo/questionary) - 优雅的交互式命令行
- 所有贡献者和用户

## 📮 联系方式

- **GitHub Issues**: [提交问题和建议](https://github.com/yourusername/codecollector/issues)
- **GitHub Discussions**: [参与讨论](https://github.com/yourusername/codecollector/discussions)
- **Email**: your.email@example.com

---

<div align="center">

**如果这个工具对你有帮助，请给个 ⭐ Star！**

Made with ❤️ by [Your Name](https://github.com/yourusername)

</div>