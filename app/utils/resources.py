"""Path helpers that work in both development and PyInstaller builds."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_APP_DIR_NAME = "SentenceTool"


def resource_path(relative: str) -> Path:
    """Resolve a bundled resource path.

    In a PyInstaller build, data files live under sys._MEIPASS. In development
    they live relative to the project root.
    """
    base = getattr(sys, "_MEIPASS", None)
    root = Path(base) if base else _PROJECT_ROOT
    return root / relative


def user_data_dir() -> Path:
    """Return a per-user writable directory for config and logs."""
    base = os.environ.get("APPDATA") or str(Path.home())
    path = Path(base) / _APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_config_path() -> Path:
    return user_data_dir() / "appsettings.json"
