"""The floating widget window and its wiring to services."""
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QAction, QIcon, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QRadioButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from app.config.config_manager import ConfigManager
from app.models.app_state import AppState
from app.models.dto import RewriteResult
from app.models.enums import PromptMode
from app.services.clipboard_service import ClipboardService
from app.services.errors import MissingApiKeyError
from app.services.hotkey_service import HotkeyService
from app.services.openai_service import OpenAIService
from app.services.rewrite_service import RewriteService
from app.services.startup_service import set_run_on_login
from app.ui.settings_window import SettingsDialog
from app.utils.logger import get_logger
from app.utils.resources import resource_path

logger = get_logger(__name__)

_STYLE_PATH = resource_path("app/ui/styles.qss")


class MainWindow(QWidget):
    # Hotkey fires on a background thread; bridge back to the UI thread.
    rewrite_requested = Signal()
    result_ready = Signal(object)

    def __init__(self, config: ConfigManager) -> None:
        super().__init__()
        self._config = config
        self._settings = config.settings
        self._is_exiting = False
        self._state = AppState(
            model=self._settings.resolve_default_model(),
            mode=PromptMode.MAKE_IT_BETTER,
        )
        self._clipboard = ClipboardService(
            copy_wait_ms=self._settings.behavior.copy_wait_ms,
            paste_wait_ms=self._settings.behavior.paste_wait_ms,
        )
        self._rewrite_service: RewriteService | None = None
        self._hotkey = HotkeyService(
            combination=self._settings.hotkey.normalized,
            callback=self._on_hotkey,
        )
        self._drag_offset: QPoint | None = None
        self._mini = MiniWidget(self._settings.hotkey.pretty)
        self._mini.clicked.connect(self._restore_from_mini)
        self.tray: QSystemTrayIcon | None = None
        self._tray_menu: QMenu | None = None

        self._build_ui()
        self._apply_style()
        self._mini.setStyleSheet(self.styleSheet())
        self._setup_tray()

        self.rewrite_requested.connect(self._process_rewrite)
        self.result_ready.connect(self._on_result)

    # ----- UI construction -------------------------------------------------
    def _build_ui(self) -> None:
        self.setWindowTitle("SentenceTool")
        self.setFixedSize(300, 400)
        flags = Qt.FramelessWindowHint | Qt.Tool
        if self._settings.ui.always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        root = QFrame()
        root.setObjectName("RootFrame")
        outer.addWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("AI Assistant")
        title.setObjectName("TitleLabel")
        header.addWidget(title)
        header.addStretch()
        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("IconButton")
        settings_btn.setFixedWidth(30)
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self._open_settings)
        header.addWidget(settings_btn)
        self._hide_btn = QPushButton("—")
        self._hide_btn.setObjectName("IconButton")
        self._hide_btn.setFixedWidth(30)
        self._hide_btn.setToolTip("Hide to floating bubble")
        self._hide_btn.clicked.connect(self._hide_to_mini)
        self._hide_btn.setVisible(not self._settings.ui.always_show_ui)
        header.addWidget(self._hide_btn)
        layout.addLayout(header)

        model_label = QLabel("Model")
        model_label.setObjectName("FieldLabel")
        layout.addWidget(model_label)
        self.model_combo = QComboBox()
        self.model_combo.addItems(self._settings.openai.available_models)
        self.model_combo.setCurrentText(self._state.model)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        layout.addWidget(self.model_combo)

        mode_label = QLabel("Mode")
        mode_label.setObjectName("FieldLabel")
        layout.addWidget(mode_label)
        self.mode_group = QButtonGroup(self)
        for mode in PromptMode:
            radio = QRadioButton(mode.label)
            radio.setProperty("mode_value", mode.value)
            if mode == self._state.mode:
                radio.setChecked(True)
            radio.toggled.connect(self._on_mode_radio)
            self.mode_group.addButton(radio)
            layout.addWidget(radio)

        layout.addSpacing(4)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("StartButton")
        self.start_btn.clicked.connect(self.start_listening)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("StopButton")
        self.stop_btn.clicked.connect(self.stop_listening)
        self.stop_btn.setEnabled(False)
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self._exit_app)
        buttons.addWidget(self.start_btn)
        buttons.addWidget(self.stop_btn)
        buttons.addWidget(exit_btn)
        layout.addLayout(buttons)

        self.startup_check = QCheckBox("Start with Windows")
        self.startup_check.setChecked(self._settings.startup.run_on_windows_login)
        self.startup_check.toggled.connect(self._on_startup_toggled)
        layout.addWidget(self.startup_check)

        self.hotkey_label = QLabel(f"Hotkey: {self._settings.hotkey.pretty}")
        self.hotkey_label.setObjectName("HotkeyLabel")
        layout.addWidget(self.hotkey_label)

        layout.addStretch()

        self.status_label = QLabel(self._status_text("Idle"))
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

    def _apply_style(self) -> None:
        if _STYLE_PATH.exists():
            self.setStyleSheet(_STYLE_PATH.read_text(encoding="utf-8"))

    def _setup_tray(self) -> None:
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self._tray_icon())
        self.tray.setToolTip("SentenceTool")

        # Keep menu/actions as instance attributes so PySide does not GC them.
        self._tray_menu = QMenu(self)
        show_action = QAction("Show", self)
        show_action.triggered.connect(self._show_window)
        start_action = QAction("Start", self)
        start_action.triggered.connect(self.start_listening)
        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self.stop_listening)
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._open_settings)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._exit_app)
        self._tray_menu.addAction(show_action)
        self._tray_menu.addAction(start_action)
        self._tray_menu.addAction(stop_action)
        self._tray_menu.addAction(settings_action)
        self._tray_menu.addSeparator()
        self._tray_menu.addAction(exit_action)
        self.tray.setContextMenu(self._tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _ensure_tray_visible(self) -> None:
        if self._is_exiting or self.tray is None:
            return
        if not self.tray.isVisible():
            self.tray.show()

    def _tray_icon(self) -> QIcon:
        icon_path = resource_path("assets/icon.ico")
        if icon_path.exists():
            return QIcon(str(icon_path))
        return self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)

    # ----- State handlers --------------------------------------------------
    def _on_model_changed(self, model: str) -> None:
        self._state.model = model
        logger.info("Model changed to %s", model)

    def _on_mode_radio(self, checked: bool) -> None:
        if not checked:
            return
        button = self.sender()
        self._state.mode = PromptMode(button.property("mode_value"))
        logger.info("Mode changed to %s", self._state.mode.value)
        self._set_status("Listening" if self._state.is_running else "Idle")

    def _on_startup_toggled(self, enabled: bool) -> None:
        if set_run_on_login(enabled):
            self._settings.startup.run_on_windows_login = enabled
            self._config.save()
        else:
            self.startup_check.blockSignals(True)
            self.startup_check.setChecked(not enabled)
            self.startup_check.blockSignals(False)

    def _open_settings(self) -> None:
        previous_hotkey = self._settings.hotkey.normalized
        dialog = SettingsDialog(self._config, parent=self)
        if dialog.exec():
            self._refresh_models()
            self._apply_hotkey_change(previous_hotkey)
            self._hide_btn.setVisible(not self._settings.ui.always_show_ui)
            if self._settings.ui.always_show_ui:
                self._mini.hide()
                self.show()
                self.raise_()
            self._set_status("Listening" if self._state.is_running else "Idle",
                             "Settings saved")
        self._ensure_tray_visible()

    def _apply_hotkey_change(self, previous_hotkey: str) -> None:
        current_hotkey = self._settings.hotkey.normalized
        self.hotkey_label.setText(f"Hotkey: {self._settings.hotkey.pretty}")
        self._mini.set_hotkey_text(self._settings.hotkey.pretty)

        if current_hotkey == previous_hotkey:
            return

        was_running = self._state.is_running
        self._hotkey.stop()
        self._hotkey = HotkeyService(
            combination=current_hotkey,
            callback=self._on_hotkey,
        )

        if not was_running:
            return

        try:
            self._hotkey.start()
        except Exception:
            self._state.is_running = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self._set_status("Error", "Hotkey registration failed.")
            self.tray.showMessage(
                "SentenceTool",
                "Failed to apply new hotkey. Please check it in Settings.",
                QSystemTrayIcon.MessageIcon.Warning,
            )

    def _refresh_models(self) -> None:
        """Re-sync the model dropdown after the model list changed in Settings."""
        models = self._settings.openai.available_models
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        self.model_combo.addItems(models)
        if self._state.model not in models:
            self._state.model = self._settings.resolve_default_model()
        self.model_combo.setCurrentText(self._state.model)
        self.model_combo.blockSignals(False)


    # ----- Start / stop ----------------------------------------------------
    def start_listening(self) -> None:
        if self._state.is_running:
            return
        try:
            self._rewrite_service = RewriteService(
                state=self._state,
                clipboard=self._clipboard,
                openai_service=OpenAIService(
                    api_key=self._settings.openai.api_key,
                    timeout_seconds=self._settings.behavior.request_timeout_seconds,
                ),
                restore_clipboard=self._settings.behavior.restore_clipboard,
            )
        except MissingApiKeyError as exc:
            self._set_status("Error", exc.user_message)
            self.tray.showMessage("SentenceTool", exc.user_message,
                                  QSystemTrayIcon.MessageIcon.Warning)
            self._open_settings()
            return

        try:
            self._hotkey.start()
        except Exception:
            self._set_status("Error", "Hotkey registration failed.")
            return

        self._state.is_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._set_status("Listening")

    def stop_listening(self) -> None:
        if not self._state.is_running:
            return
        self._hotkey.stop()
        self._state.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._set_status("Idle")

    # ----- Rewrite pipeline ------------------------------------------------
    def _on_hotkey(self) -> None:
        # Runs on the keyboard library thread -> hand off to the UI thread.
        self.rewrite_requested.emit()

    def _process_rewrite(self) -> None:
        if not self._state.is_running or self._rewrite_service is None:
            return
        if self._rewrite_service.is_busy:
            return
        self._set_status("Sending request")
        worker = _RewriteWorker(self._rewrite_service, self.result_ready)
        worker.start()

    def _on_result(self, result: RewriteResult) -> None:
        if result.success:
            self._set_status("Listening", "Done")
        else:
            self._set_status("Listening", result.message)
            self.tray.showMessage("SentenceTool", result.message,
                                  QSystemTrayIcon.MessageIcon.Information)

    # ----- Status helpers --------------------------------------------------
    def _status_text(self, state: str, detail: str | None = None) -> str:
        base = f"{state}  ·  {self._state.mode.label}"
        return f"{base}  ·  {detail}" if detail else base

    def _set_status(self, state: str, detail: str | None = None) -> None:
        self.status_label.setText(self._status_text(state, detail))

    # ----- Window / tray behavior -----------------------------------------
    def _show_window(self) -> None:
        self._mini.hide()
        self.show()
        self.raise_()
        self.activateWindow()
        self._ensure_tray_visible()

    def _hide_to_mini(self) -> None:
        """Hide the main window and show the floating bubble instead."""
        if self._settings.ui.always_show_ui:
            return
        geo = self.frameGeometry()
        self._mini.move(geo.right() - self._mini.width(), geo.top())
        self._mini.show()
        self._mini.raise_()
        self.hide()
        self._ensure_tray_visible()

    def _restore_from_mini(self) -> None:
        self._show_window()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_window()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt signature
        if self._is_exiting:
            event.accept()
            return
        event.ignore()
        if not self._settings.ui.always_show_ui:
            self._hide_to_mini()

    def _exit_app(self) -> None:
        if self._is_exiting:
            return
        self._is_exiting = True
        self.stop_listening()
        self._mini.hide()
        if self.tray is not None:
            self.tray.hide()
        self.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    # ----- Dragging --------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_offset = None


class _RewriteWorker:
    """Runs the rewrite pipeline on a daemon thread and emits the result."""

    def __init__(self, service: RewriteService, signal: Signal) -> None:
        import threading

        self._service = service
        self._signal = signal
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _run(self) -> None:
        result = self._service.run()
        self._signal.emit(result)


class MiniWidget(QWidget):
    """A small always-on-top floating bubble shown when the main UI is hidden.

    Clicking it restores the main window; it can also be dragged anywhere.
    """

    clicked = Signal()

    def __init__(self, hotkey_text: str) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(58, 58)
        self.setToolTip("SentenceTool — click to open")

        frame = QFrame(self)
        frame.setObjectName("MiniBubble")
        frame.setGeometry(0, 0, 58, 58)
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(2, 2, 2, 2)
        self._label = QLabel("")
        self._label.setObjectName("MiniLabel")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setWordWrap(True)
        inner.addWidget(self._label)
        self.set_hotkey_text(hotkey_text)

        self._press_offset: QPoint | None = None
        self._moved = False

    def set_hotkey_text(self, hotkey_text: str) -> None:
        display = hotkey_text.replace("+", "\n+")
        self._label.setText(display)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._press_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            self._moved = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._press_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._press_offset)
            self._moved = True

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and not self._moved:
            self.clicked.emit()
        self._press_offset = None

