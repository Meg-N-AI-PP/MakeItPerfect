import json

import pytest

from app.config.config_manager import ConfigManager
from app.config.settings import AppSettings


def _write(tmp_path, data):
    path = tmp_path / "appsettings.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_valid_config_loads(tmp_path):
    path = _write(tmp_path, {
        "openai": {"api_key": "k", "default_model": "gpt-5",
                   "available_models": ["gpt-5", "gpt-4o"]},
    })
    manager = ConfigManager(path)
    settings = manager.load()
    assert settings.openai.default_model == "gpt-5"
    assert manager.has_api_key()


def test_missing_file_uses_defaults(tmp_path):
    manager = ConfigManager(tmp_path / "missing.json")
    settings = manager.load()
    assert isinstance(settings, AppSettings)
    assert settings.openai.available_models


def test_empty_models_rejected(tmp_path):
    path = _write(tmp_path, {"openai": {"available_models": []}})
    manager = ConfigManager(path)
    with pytest.raises(ValueError):
        manager.load()


def test_default_model_fallback():
    settings = AppSettings.model_validate({
        "openai": {"default_model": "ghost", "available_models": ["gpt-4o"]}
    })
    assert settings.resolve_default_model() == "gpt-4o"
