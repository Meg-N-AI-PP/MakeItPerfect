"""Pydantic settings models with validation."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ResultLanguage

SUPPORTED_MODELS: List[str] = ["gpt-5.4", "gpt-5.5", "gpt-5.6"]
DEFAULT_MODEL: str = "gpt-5.4"


class OpenAISettings(BaseModel):
    api_key: str = ""
    default_model: str = DEFAULT_MODEL
    available_models: List[str] = Field(default_factory=lambda: list(SUPPORTED_MODELS))

    @field_validator("available_models")
    @classmethod
    def _restrict_models(cls, value: List[str]) -> List[str]:
        """Keep only supported models; fall back to the full supported list."""
        filtered = [model for model in value if model in SUPPORTED_MODELS]
        return filtered or list(SUPPORTED_MODELS)


class HotkeySettings(BaseModel):
    # Free-form combination understood by the `keyboard` library, e.g.
    # "ctrl+alt+r". Ctrl+R / Ctrl+1..9 are avoided because browsers and many
    # apps already bind them (reload / switch tab).
    combination: str = "ctrl+alt+r"

    model_config = {"extra": "ignore"}

    @property
    def normalized(self) -> str:
        return self.combination.lower().replace(" ", "")

    @property
    def pretty(self) -> str:
        return "+".join(part.capitalize() for part in self.normalized.split("+"))


class UISettings(BaseModel):
    always_on_top: bool = True
    start_minimized_to_tray: bool = False
    minimize_to_bubble: bool = True
    theme: str = "dark"


class BehaviorSettings(BaseModel):
    copy_wait_ms: int = Field(default=120, ge=10, le=2000)
    paste_wait_ms: int = Field(default=80, ge=10, le=2000)
    request_timeout_seconds: int = Field(default=20, ge=1, le=120)
    restore_clipboard: bool = True
    result_language: ResultLanguage = ResultLanguage.ENGLISH


class StartupSettings(BaseModel):
    run_on_windows_login: bool = False


class AppSettings(BaseModel):
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    hotkey: HotkeySettings = Field(default_factory=HotkeySettings)
    ui: UISettings = Field(default_factory=UISettings)
    behavior: BehaviorSettings = Field(default_factory=BehaviorSettings)
    startup: StartupSettings = Field(default_factory=StartupSettings)

    def resolve_default_model(self) -> str:
        """Return the default model, falling back to the first available one."""
        if self.openai.default_model in self.openai.available_models:
            return self.openai.default_model
        return self.openai.available_models[0]
