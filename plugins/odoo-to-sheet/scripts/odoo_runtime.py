"""Resolve stable per-user paths for the Odoo To Sheet local runtime."""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path


ENV_DIR_NAME = ".odoo2sheet-env"


def platform_details() -> dict[str, str]:
    system = platform.system() or sys.platform
    labels = {"Windows": "Windows", "Darwin": "macOS", "Linux": "Linux"}
    return {
        "system": system,
        "display_name": labels.get(system, system),
        "release": platform.release(),
        "architecture": platform.machine() or "unknown",
    }


def user_data_dir() -> Path:
    override = os.environ.get("ODOO2SHEET_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        return (Path(base) if base else Path.home() / "AppData" / "Local") / "OdooToSheet"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "OdooToSheet"
    base = os.environ.get("XDG_DATA_HOME")
    return (Path(base).expanduser() if base else Path.home() / ".local" / "share") / "odoo2sheet"


def user_config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        return (Path(base) if base else Path.home() / "AppData" / "Roaming") / "OdooToSheet"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "OdooToSheet"
    base = os.environ.get("XDG_CONFIG_HOME")
    return (Path(base).expanduser() if base else Path.home() / ".config") / "odoo2sheet"


def default_config_path() -> Path:
    canonical = user_config_dir() / "config.json"
    legacy = Path.home() / ".config" / "odoo2sheet" / "config.json"
    if canonical.exists() or not legacy.exists():
        return canonical
    return legacy


def runtime_python(env_dir: Path) -> Path:
    return env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def select_runtime_env() -> tuple[Path, str]:
    override = os.environ.get("ODOO2SHEET_ENV_DIR")
    if override:
        return Path(override).expanduser(), "configured"
    return user_data_dir() / ENV_DIR_NAME, "per_user"
