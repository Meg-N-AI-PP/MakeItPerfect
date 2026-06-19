"""Coordinates the full capture -> AI -> replace -> restore pipeline."""
from __future__ import annotations

import threading

from app.models.app_state import AppState
from app.models.dto import RewriteResult
from app.services.clipboard_service import ClipboardService
from app.services.errors import NoSelectionError, RewriteError
from app.services.openai_service import OpenAIService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RewriteService:
    """Runs one rewrite at a time and reports the result."""

    def __init__(
        self,
        state: AppState,
        clipboard: ClipboardService,
        openai_service: OpenAIService,
        restore_clipboard: bool,
    ) -> None:
        self._state = state
        self._clipboard = clipboard
        self._openai = openai_service
        self._restore_clipboard = restore_clipboard
        self._lock = threading.Lock()

    @property
    def is_busy(self) -> bool:
        return self._lock.locked()

    def run(self) -> RewriteResult:
        """Execute the pipeline. Returns immediately if already busy."""
        if not self._lock.acquire(blocking=False):
            return RewriteResult(success=False, message="Busy, please wait.")
        try:
            return self._run_pipeline()
        finally:
            self._lock.release()

    def _run_pipeline(self) -> RewriteResult:
        snapshot = self._clipboard.snapshot()
        try:
            selected = self._clipboard.capture_selection()
            if not selected.strip():
                raise NoSelectionError()

            logger.info("Rewriting %d chars with model=%s mode=%s",
                        len(selected), self._state.model, self._state.mode.value)

            rewritten = self._openai.rewrite(
                text=selected,
                model=self._state.model,
                mode=self._state.mode,
            )
            if not rewritten.strip():
                raise RewriteError("Empty response from AI.")

            self._clipboard.paste_text(rewritten)
            return RewriteResult(
                success=True,
                message="Done",
                original_text=selected,
                rewritten_text=rewritten,
            )
        except RewriteError as exc:
            logger.warning("Rewrite failed: %s", exc)
            return RewriteResult(success=False, message=exc.user_message)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected rewrite error")
            return RewriteResult(success=False, message="Unexpected error.")
        finally:
            if self._restore_clipboard:
                self._clipboard.restore(snapshot)
