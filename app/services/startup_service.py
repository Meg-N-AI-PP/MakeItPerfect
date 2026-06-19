"""Manages the 'Start with Windows' registry entry."""
from __future__ import annotations

import sys
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "SentenceTool"


def _executable_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    script = Path(__file__).resolve().parents[2] / "app" / "main.py"
    return f'"{sys.executable}" "{script}"'


def set_run_on_login(enabled: bool) -> bool:
    """Add or remove the startup entry. Returns True on success."""
    try:
        import winreg
    except ImportError:
        logger.warning("winreg unavailable; startup integration skipped")
        return False

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(
                    key, _APP_NAME, 0, winreg.REG_SZ, _executable_command()
                )
            else:
                try:
                    winreg.DeleteValue(key, _APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError as exc:
        logger.error("Failed to update startup entry: %s", exc)
        return False
