"""Clipboard read/write, snapshot, selection capture, and paste."""
from __future__ import annotations

import time

import keyboard
import pyperclip

from app.models.dto import ClipboardSnapshot
from app.utils.logger import get_logger

logger = get_logger(__name__)

# A sentinel value used to reliably detect whether Ctrl+C produced new content.
_BASELINE_SENTINEL = "\x00__sentencetool_baseline__\x00"


class ClipboardService:
    def __init__(self, copy_wait_ms: int, paste_wait_ms: int) -> None:
        self._copy_wait = copy_wait_ms / 1000.0
        self._paste_wait = paste_wait_ms / 1000.0

    def read_text(self) -> str:
        try:
            return pyperclip.paste() or ""
        except Exception as exc:  # noqa: BLE001
            logger.warning("Clipboard read failed: %s", exc)
            return ""

    def write_text(self, text: str) -> None:
        pyperclip.copy(text)

    def snapshot(self) -> ClipboardSnapshot:
        current = self.read_text()
        return ClipboardSnapshot(text=current, had_text=bool(current))

    def restore(self, snapshot: ClipboardSnapshot) -> None:
        try:
            self.write_text(snapshot.text if snapshot.had_text else "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Clipboard restore failed: %s", exc)

    def capture_selection(self) -> str:
        """Copy the active selection via Ctrl+C and return it, or '' if none."""
        self.write_text(_BASELINE_SENTINEL)
        keyboard.send("ctrl+c")
        time.sleep(self._copy_wait)

        captured = self.read_text()
        if captured == _BASELINE_SENTINEL:
            return ""
        return captured

    def paste_text(self, text: str) -> None:
        self.write_text(text)
        time.sleep(0.02)
        keyboard.send("ctrl+v")
        time.sleep(self._paste_wait)
