"""Application entry point."""
from __future__ import annotations

import atexit
import os
import sys
import tempfile

# Allow running both as `python -m app.main` and `python app/main.py`.
if __package__ in (None, ""):
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.config.config_manager import ConfigManager
from app.ui.main_window import MainWindow
from app.utils.logger import get_logger

logger = get_logger("main")

_LOCK_FILE = None
_LOCK_PATH = str(Path(tempfile.gettempdir()) / "sentence_tool.lock")


def _acquire_single_instance_lock() -> bool:
    """Return True if this is the first instance, False if another is running."""
    global _LOCK_FILE  # noqa: PLW0603
    try:
        _LOCK_FILE = open(_LOCK_PATH, "a+", encoding="utf-8")  # noqa: WPS515
        import msvcrt
        _LOCK_FILE.seek(0)
        msvcrt.locking(_LOCK_FILE.fileno(), msvcrt.LK_NBLCK, 1)
        _LOCK_FILE.seek(0)
        _LOCK_FILE.truncate()
        _LOCK_FILE.write(str(os.getpid()))
        _LOCK_FILE.flush()
        return True
    except (OSError, ImportError):
        if _LOCK_FILE is not None:
            try:
                _LOCK_FILE.close()
            except OSError:
                pass
            _LOCK_FILE = None
        return False


def _release_single_instance_lock() -> None:
    global _LOCK_FILE  # noqa: PLW0603
    if _LOCK_FILE is None:
        return
    try:
        import msvcrt
        _LOCK_FILE.seek(0)
        msvcrt.locking(_LOCK_FILE.fileno(), msvcrt.LK_UNLCK, 1)
    except OSError:
        pass
    finally:
        try:
            _LOCK_FILE.close()
        except OSError:
            pass
        _LOCK_FILE = None


def main() -> int:
    if not _acquire_single_instance_lock():
        logger.warning("Another instance is already running. Exiting.")
        return 0

    atexit.register(_release_single_instance_lock)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Segoe UI", 9))

    config = ConfigManager()
    try:
        config.load()
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load config: %s", exc)

    window = MainWindow(config)
    if config.settings.ui.start_minimized_to_tray:
        window.hide()
    else:
        window.show()

    exit_code = app.exec()
    _release_single_instance_lock()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
