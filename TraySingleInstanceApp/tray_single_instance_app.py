"""Single-instance background app runner using pystray.

This module provides:
- Cross-platform single-instance locking.
- A system tray icon with a right-click menu containing Exit.
- A placeholder `main_application_logic()` that runs on a worker thread.

Integration notes:
1. Put your current app logic inside `main_application_logic()`.
2. Keep long-running work in that function so the tray loop remains responsive.
3. When Exit is clicked, `APP_STOP_EVENT` is set. Use it in your logic to stop cleanly.
"""
from __future__ import annotations

import atexit
import logging
import os
import tempfile
import threading
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

APP_NAME = "SentenceTool"
LOCK_FILE_NAME = "sentence_tool_single_instance.lock"
APP_STOP_EVENT = threading.Event()


class SingleInstanceLock:
    """Simple cross-platform single-instance file lock."""

    def __init__(self, lock_path: Path) -> None:
        self._lock_path = lock_path
        self._lock_file: object | None = None
        self._acquired = False

    @property
    def acquired(self) -> bool:
        return self._acquired

    def acquire(self) -> bool:
        """Try to acquire the lock without blocking."""
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_file = open(self._lock_path, "a+", encoding="utf-8")

        try:
            if os.name == "nt":
                import msvcrt

                self._lock_file.seek(0)
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            self._lock_file.seek(0)
            self._lock_file.truncate()
            self._lock_file.write(str(os.getpid()))
            self._lock_file.flush()
            self._acquired = True
            return True
        except (OSError, BlockingIOError):
            self.release()
            return False

    def release(self) -> None:
        """Release the lock and close the lock file."""
        if self._lock_file is None:
            return

        try:
            if self._acquired:
                if os.name == "nt":
                    import msvcrt

                    self._lock_file.seek(0)
                    msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
        except OSError:
            logging.debug("Failed to unlock instance file", exc_info=True)
        finally:
            try:
                self._lock_file.close()
            finally:
                self._lock_file = None
                self._acquired = False


def main_application_logic() -> None:
    """Placeholder for your existing app code.

    Replace this loop with your current script/app startup and runtime code.
    Keep this function long-running if your app is supposed to stay active.

    Use `APP_STOP_EVENT.is_set()` in loops so Exit can shut your app down cleanly.
    """
    while not APP_STOP_EVENT.is_set():
        APP_STOP_EVENT.wait(0.5)


def create_tray_icon_image() -> Image.Image:
    """Create a simple in-memory tray icon image."""
    size = 64
    image = Image.new("RGBA", (size, size), (35, 94, 165, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((12, 12, 52, 52), fill=(255, 255, 255, 230))
    draw.rectangle((30, 18, 34, 46), fill=(35, 94, 165, 255))
    return image


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def run() -> int:
    configure_logging()
    logger = logging.getLogger(APP_NAME)

    lock_path = Path(tempfile.gettempdir()) / LOCK_FILE_NAME
    instance_lock = SingleInstanceLock(lock_path)

    if not instance_lock.acquire():
        logger.info("Another instance is already running. Exiting.")
        return 0

    # Ensure lock is released even if process exits unexpectedly.
    atexit.register(instance_lock.release)

    logic_thread = threading.Thread(
        target=main_application_logic,
        name="main-application-logic",
        daemon=True,
    )
    logic_thread.start()

    def on_exit_clicked(icon: pystray.Icon, item: pystray.MenuItem) -> None:  # noqa: ARG001
        logger.info("Exit clicked from tray menu.")
        APP_STOP_EVENT.set()
        icon.stop()

    icon = pystray.Icon(
        APP_NAME,
        create_tray_icon_image(),
        APP_NAME,
        menu=pystray.Menu(pystray.MenuItem("Exit", on_exit_clicked)),
    )

    try:
        logger.info("Tray icon started. Right-click the tray icon and choose Exit.")
        icon.run()
    finally:
        APP_STOP_EVENT.set()
        if logic_thread.is_alive():
            logic_thread.join(timeout=5)

        icon.visible = False
        instance_lock.release()

        logger.info("Application stopped cleanly.")

    return 0


if __name__ == "__main__":
    # For PyInstaller background mode on Windows, build with:
    # pyinstaller --noconsole --onefile TraySingleInstanceApp/tray_single_instance_app.py
    raise SystemExit(run())
