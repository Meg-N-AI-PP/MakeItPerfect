"""Pydantic settings models with validation."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator


class OpenAISettings(BaseModel):
    api_key: str = ""
    default_model: str = "gpt-5"
    available_models: List[str] = Field(default_factory=lambda: ["gpt-5"])

    @field_validator("available_models")
    @classmethod
    def _non_empty_models(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("available_models must contain at least one model")
        return value


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
    always_show_ui: bool = False
    theme: str = "dark"


class BehaviorSettings(BaseModel):
    copy_wait_ms: int = Field(default=120, ge=10, le=2000)
    paste_wait_ms: int = Field(default=80, ge=10, le=2000)
    request_timeout_seconds: int = Field(default=20, ge=1, le=120)
    restore_clipboard: bool = True


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
