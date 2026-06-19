"""Wraps the OpenAI SDK with timeout, retry, and response normalization."""
from __future__ import annotations

import time

from app.models.enums import PromptMode
from app.prompts.prompt_builder import build_system_prompt, build_user_prompt
from app.services.errors import (
    InvalidModelError,
    MissingApiKeyError,
    RateLimitedError,
    RewriteError,
    TimeoutErrorRewrite,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

_MAX_RETRIES = 2
_RETRY_BACKOFF_SECONDS = 1.5


class OpenAIService:
    def __init__(self, api_key: str, timeout_seconds: int) -> None:
        if not api_key.strip():
            raise MissingApiKeyError()
        # Imported lazily so the app can start even if the SDK errors on import.
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key, timeout=timeout_seconds)

    def rewrite(self, text: str, model: str, mode: PromptMode) -> str:
        system_prompt = build_system_prompt(mode)
        user_prompt = build_user_prompt(text)

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = response.choices[0].message.content or ""
                return self._normalize(content)
            except Exception as exc:  # noqa: BLE001 - mapped below
                last_exc = exc
                mapped = self._map_error(exc)
                if isinstance(mapped, (InvalidModelError, MissingApiKeyError)):
                    raise mapped
                if attempt < _MAX_RETRIES:
                    logger.warning("OpenAI call failed (attempt %s): %s", attempt + 1, exc)
                    time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
                    continue
                raise mapped from exc

        raise RewriteError() from last_exc

    @staticmethod
    def _normalize(text: str) -> str:
        result = text.strip()
        if len(result) >= 2 and result[0] in "\"'" and result[-1] == result[0]:
            result = result[1:-1].strip()
        return result

    @staticmethod
    def _map_error(exc: Exception) -> RewriteError:
        name = exc.__class__.__name__.lower()
        message = str(exc).lower()
        if "timeout" in name or "timeout" in message:
            return TimeoutErrorRewrite()
        if "ratelimit" in name or "rate limit" in message or "429" in message:
            return RateLimitedError()
        if "notfound" in name or "model" in message and "not" in message:
            return InvalidModelError()
        if "authentication" in name or "api key" in message or "401" in message:
            return MissingApiKeyError()
        return RewriteError(str(exc))
