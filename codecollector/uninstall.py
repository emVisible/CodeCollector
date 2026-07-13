"""Uninstall helpers for development and updates."""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from codecollector.config import CONFIG_DIR


PACKAGE_NAME = "codecollector"


def _run(cmd: List[str]) -> Tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return 127, f"command not found: {cmd[0]}"
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output.strip()


def _has_command(name: str) -> bool:
    return shutil.which(name) is not None


def _pipx_has_package() -> bool:
    code, output = _run(["pipx", "list", "--short"])
    if code != 0:
        return False
    return any(line.split()[0] == PACKAGE_NAME for line in output.splitlines() if line.strip())


def _pip_has_package() -> bool:
    code, _ = _run([sys.executable, "-m", "pip", "show", PACKAGE_NAME])
    return code == 0


def detect_install_methods() -> List[str]:
    """Return known install methods currently present."""
    methods: List[str] = []
    if _has_command("pipx") and _pipx_has_package():
        methods.append("pipx")
    if _pip_has_package():
        methods.append("pip")
    return methods


def remove_config_dir() -> Optional[Path]:
    """Remove the user config directory if it exists."""
    if not CONFIG_DIR.exists():
        return None
    shutil.rmtree(CONFIG_DIR)
    return CONFIG_DIR


def uninstall_package(purge_config: bool = False) -> Tuple[bool, List[str]]:
    """Uninstall codecollector via pipx and/or pip.

    Returns (success, messages).
    """
    messages: List[str] = []
    methods = detect_install_methods()

    if not methods:
        messages.append(
            f"No installed `{PACKAGE_NAME}` found via pipx or pip.\n"
            "If you run from source with PYTHONPATH, just stop using that path."
        )
        if purge_config:
            removed = remove_config_dir()
            if removed:
                messages.append(f"Removed config: {removed}")
            else:
                messages.append(f"No config directory to remove: {CONFIG_DIR}")
        return False, messages

    success = True

    if "pipx" in methods:
        code, output = _run(["pipx", "uninstall", PACKAGE_NAME])
        if code == 0:
            messages.append(f"Uninstalled via pipx: {PACKAGE_NAME}")
        else:
            success = False
            messages.append(f"pipx uninstall failed:\n{output or '(no output)'}")

    if "pip" in methods:
        code, output = _run(
            [sys.executable, "-m", "pip", "uninstall", "-y", PACKAGE_NAME]
        )
        if code == 0:
            messages.append(f"Uninstalled via pip: {PACKAGE_NAME}")
        else:
            success = False
            messages.append(f"pip uninstall failed:\n{output or '(no output)'}")

    if purge_config:
        removed = remove_config_dir()
        if removed:
            messages.append(f"Removed config: {removed}")
        else:
            messages.append(f"No config directory to remove: {CONFIG_DIR}")

    if success:
        messages.append(
            "Reinstall from source with:\n"
            f"  pipx install -e {Path.cwd()}\n"
            "or:\n"
            "  pip install -e ."
        )

    return success, messages
