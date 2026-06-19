"""Simple data transfer objects."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClipboardSnapshot:
    """Stores the clipboard text state before a rewrite operation."""

    text: str
    had_text: bool


@dataclass
class RewriteResult:
    """Outcome of a rewrite pipeline run."""

    success: bool
    message: str
    original_text: str = ""
    rewritten_text: str = ""
