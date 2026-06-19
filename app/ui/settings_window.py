"""Settings dialog for entering the API key and model list."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.config.config_manager import ConfigManager


class SettingsDialog(QDialog):
    """Lets the user store the OpenAI API key, models, and timeout."""

    def __init__(self, config: ConfigManager, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._settings = config.settings

        self.setWindowTitle("SentenceTool — Settings")
        self.setObjectName("SettingsDialog")
        self.setModal(True)
        self.setFixedWidth(380)
        if parent is not None:
            self.setStyleSheet(parent.styleSheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        title = QLabel("Settings")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        # --- API key ---
        layout.addWidget(self._field_label("OpenAI API Key"))
        key_row = QHBoxLayout()
        self.key_edit = QLineEdit(self._settings.openai.api_key)
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setPlaceholderText("sk-...")
        key_row.addWidget(self.key_edit)
        self.show_key = QPushButton("Show")
        self.show_key.setObjectName("IconButton")
        self.show_key.setCheckable(True)
        self.show_key.setFixedWidth(54)
        self.show_key.toggled.connect(self._toggle_key_visibility)
        key_row.addWidget(self.show_key)
        layout.addLayout(key_row)

        if ConfigManager.env_key_active():
            warn = QLabel(
                "Note: an OPENAI_API_KEY environment variable is set and will "
                "override this value at runtime."
            )
            warn.setObjectName("HotkeyLabel")
            warn.setWordWrap(True)
            layout.addWidget(warn)

        # --- Models ---
        layout.addWidget(self._field_label("Available models (one per line)"))
        self.models_edit = QPlainTextEdit(
            "\n".join(self._settings.openai.available_models)
        )
        self.models_edit.setFixedHeight(96)
        layout.addWidget(self.models_edit)

        # --- Hotkey ---
        layout.addWidget(self._field_label("Hotkey combination"))
        self.hotkey_edit = QLineEdit(self._settings.hotkey.normalized)
        self.hotkey_edit.setPlaceholderText("ctrl+alt+r")
        layout.addWidget(self.hotkey_edit)

        # --- Timeout ---
        layout.addWidget(self._field_label("Request timeout (seconds)"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 120)
        self.timeout_spin.setValue(self._settings.behavior.request_timeout_seconds)
        layout.addWidget(self.timeout_spin)

        # --- Restore clipboard ---
        self.restore_check = QCheckBox("Restore clipboard after each rewrite")
        self.restore_check.setChecked(self._settings.behavior.restore_clipboard)
        layout.addWidget(self.restore_check)

        # --- Window behavior ---
        self.always_show_ui_check = QCheckBox(
            "Always show main UI (disable minimize to floating bubble)"
        )
        self.always_show_ui_check.setChecked(self._settings.ui.always_show_ui)
        layout.addWidget(self.always_show_ui_check)

        layout.addSpacing(6)

        # --- Buttons ---
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setObjectName("StartButton")
        save.clicked.connect(self._save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _toggle_key_visibility(self, shown: bool) -> None:
        self.key_edit.setEchoMode(QLineEdit.Normal if shown else QLineEdit.Password)
        self.show_key.setText("Hide" if shown else "Show")

    def _save(self) -> None:
        models = [
            line.strip()
            for line in self.models_edit.toPlainText().splitlines()
            if line.strip()
        ]
        if not models:
            models = ["gpt-4o"]

        hotkey_parts = [
            part.strip().lower()
            for part in self.hotkey_edit.text().split("+")
            if part.strip()
        ]
        hotkey = "+".join(hotkey_parts) if hotkey_parts else "ctrl+alt+r"

        self._settings.openai.api_key = self.key_edit.text().strip()
        self._settings.openai.available_models = models
        if self._settings.openai.default_model not in models:
            self._settings.openai.default_model = models[0]
        self._settings.hotkey.combination = hotkey
        self._settings.behavior.request_timeout_seconds = self.timeout_spin.value()
        self._settings.behavior.restore_clipboard = self.restore_check.isChecked()
        self._settings.ui.always_show_ui = self.always_show_ui_check.isChecked()

        self._config.save()
        self.accept()
