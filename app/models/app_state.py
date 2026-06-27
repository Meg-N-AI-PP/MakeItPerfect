"""Mutable runtime state shared between UI and services."""
from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import PromptMode, ResultLanguage


@dataclass
class AppState:
    """Holds the live model/mode selection and running flag."""

    model: str
    mode: PromptMode = PromptMode.MAKE_IT_BETTER
    result_language: ResultLanguage = ResultLanguage.ENGLISH
    is_running: bool = False
