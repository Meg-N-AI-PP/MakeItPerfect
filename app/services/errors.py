"""Custom exceptions mapped to user-facing messages."""
from __future__ import annotations


class RewriteError(Exception):
    """Base error with a UI-friendly message."""

    user_message = "AI request failed."


class MissingApiKeyError(RewriteError):
    user_message = "OpenAI API key is missing."


class TimeoutErrorRewrite(RewriteError):
    user_message = "Request timed out."


class RateLimitedError(RewriteError):
    user_message = "Rate limited. Try again shortly."


class InvalidModelError(RewriteError):
    user_message = "Selected model is not available."


class NoSelectionError(RewriteError):
    user_message = "No text selected."
