"""Application entry point."""
from __future__ import annotations

import sys

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


def main() -> int:
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

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
