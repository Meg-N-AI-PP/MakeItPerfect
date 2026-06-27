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


class ResultLanguage(str, Enum):
    """The destination language for the rewritten text."""

    ENGLISH = "english"
    CHINESE = "chinese"
    JAPANESE = "japanese"
    SWISS_GERMAN = "swiss_german"

    @property
    def label(self) -> str:
        return {
            ResultLanguage.ENGLISH: "English",
            ResultLanguage.CHINESE: "Chinese",
            ResultLanguage.JAPANESE: "Japanese",
            ResultLanguage.SWISS_GERMAN: "Swiss German",
        }[self]

    @classmethod
    def from_label(cls, label: str) -> "ResultLanguage":
        for language in cls:
            if language.label == label:
                return language
        raise ValueError(f"Unknown language label: {label}")


class AppStatus(str, Enum):
    """High-level lifecycle states surfaced to the UI."""

    IDLE = "Idle"
    LISTENING = "Listening"
    CAPTURING = "Capturing text"
    SENDING = "Sending request"
    REPLACING = "Replacing text"
    SUCCESS = "Done"
    ERROR = "Error"
