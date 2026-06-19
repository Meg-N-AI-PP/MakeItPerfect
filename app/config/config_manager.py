"""Load and persist application configuration."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from app.config.settings import AppSettings
from app.utils.logger import get_logger
from app.utils.resources import resource_path, user_config_path

logger = get_logger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_BUNDLED_TEMPLATE = resource_path("config/appsettings.json")


def _load_dotenv() -> None:
    """Load variables from a project-root .env file, if present (dev only)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = _PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


class ConfigManager:
    """Reads, validates, and writes the JSON config file.

    By default the config lives in a per-user writable location so the tool
    works when installed. On first run it is seeded from the bundled template.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        self._explicit_path = config_path is not None
        self.config_path = config_path or user_config_path()
        self._settings: AppSettings | None = None

    @property
    def settings(self) -> AppSettings:
        if self._settings is None:
            self._settings = self.load()
        return self._settings

    def _seed_from_template(self) -> None:
        if self._explicit_path or self.config_path.exists():
            return
        try:
            if _BUNDLED_TEMPLATE.exists():
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(_BUNDLED_TEMPLATE, self.config_path)
                logger.info("Seeded config from template -> %s", self.config_path)
        except OSError as exc:
            logger.warning("Could not seed config template: %s", exc)

    def load(self) -> AppSettings:
        self._seed_from_template()

        if not self.config_path.exists():
            logger.warning("Config file not found at %s, using defaults", self.config_path)
            self._settings = AppSettings()
        else:
            try:
                raw = json.loads(self.config_path.read_text(encoding="utf-8"))
                self._settings = AppSettings.model_validate(raw)
            except (json.JSONDecodeError, ValueError) as exc:
                logger.error("Invalid config file: %s", exc)
                raise

        # Allow API key override from a .env file or environment variable.
        _load_dotenv()
        env_key = os.environ.get("OPENAI_API_KEY")
        if env_key:
            self._settings.openai.api_key = env_key

        return self._settings

    def save(self) -> None:
        if self._settings is None:
            return
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            self._settings.model_dump_json(indent=2), encoding="utf-8"
        )

    def has_api_key(self) -> bool:
        return bool(self.settings.openai.api_key.strip())

    @staticmethod
    def env_key_active() -> bool:
        """True if an OPENAI_API_KEY env var would override the saved key."""
        _load_dotenv()
        return bool(os.environ.get("OPENAI_API_KEY"))

