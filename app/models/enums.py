"""Enumerations used across the application."""
from __future__ import annotations

from enum import Enum


class PromptMode(str, Enum):
    """The three supported rewrite modes."""

    CORRECT_GRAMMAR = "correct_grammar"
    MAKE_IT_BETTER = "make_it_better"
    SUPER = "super"

    @property
    def label(self) -> str:
        return {
            PromptMode.CORRECT_GRAMMAR: "Correct Grammar",
            PromptMode.MAKE_IT_BETTER: "Make It Better",
            PromptMode.SUPER: "Super",
        }[self]

    @classmethod
    def from_label(cls, label: str) -> "PromptMode":
        for mode in cls:
            if mode.label == label:
                return mode
        raise ValueError(f"Unknown mode label: {label}")


class AppStatus(str, Enum):
    """High-level lifecycle states surfaced to the UI."""

    IDLE = "Idle"
    LISTENING = "Listening"
    CAPTURING = "Capturing text"
    SENDING = "Sending request"
    REPLACING = "Replacing text"
    SUCCESS = "Done"
    ERROR = "Error"
