"""Registers and unregisters the global hotkey."""
from __future__ import annotations

from typing import Callable

import keyboard

from app.utils.logger import get_logger

logger = get_logger(__name__)


class HotkeyService:
    def __init__(self, combination: str, callback: Callable[[], None]) -> None:
        self._combination = combination
        self._callback = callback
        self._handle = None

    @property
    def is_active(self) -> bool:
        return self._handle is not None

    def start(self) -> None:
        if self._handle is not None:
            return
        try:
            # suppress=True stops the combo from also reaching the focused app
            # (so e.g. the browser does not act on it).
            self._handle = keyboard.add_hotkey(
                self._combination, self._callback, suppress=True
            )
            logger.info("Hotkey registered: %s", self._combination)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to register hotkey: %s", exc)
            raise

    def stop(self) -> None:
        if self._handle is None:
            return
        try:
            keyboard.remove_hotkey(self._handle)
        except (KeyError, ValueError) as exc:
            logger.warning("Failed to remove hotkey: %s", exc)
        finally:
            self._handle = None
            logger.info("Hotkey unregistered")
