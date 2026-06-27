# Logo Widget, System Tray, Exit, and Portable EXE — Implementation Detail

This document explains how the following four capabilities are implemented in the
current SentenceTool application:

1. The floating logo widget shown when the app/tool is hidden.
2. The Windows system tray icon and menu.
3. Exit behavior that fully terminates the running instance.
4. The portable `.exe` that runs without installation.

All behavior described here reflects the actual code in `app/` and the packaging
configuration in `SentenceTool.spec` and `build.ps1`.

---

## 1. Floating Logo Widget (Mini Bubble)

### Goal

When the user hides the main window, the app does not disappear entirely. A small
circular floating bubble showing the `Meg` logo stays on screen. Clicking it
restores the main window. It can be dragged anywhere.

### Owning Component

- Class: `MiniWidget`
- File: `app/ui/main_window.py`

### Window Configuration

The bubble is a frameless, always-on-top, translucent tool window:

- `Qt.FramelessWindowHint` removes the title bar and borders.
- `Qt.Tool` keeps it off the taskbar.
- `Qt.WindowStaysOnTopHint` keeps it above other windows.
- `Qt.WA_TranslucentBackground` allows the rounded/transparent corners to show.
- Fixed size: 58 x 58 pixels.

The visible surface is a child `QFrame` named `MiniBubble`, styled in
`app/ui/styles.qss`. The frame background is transparent with no border, so only
the circular logo is visible:

```css
#MiniBubble {
    background-color: transparent;
    border: none;
}
```

### Logo Rendering

The logo lives at `assets/Media/Meg.png` and is resolved with `resource_path(...)`
so it works both in development and inside the packaged `.exe`.

Rendering pipeline (`MiniWidget._set_logo_or_fallback`):

1. Load the image into a `QPixmap`.
2. If the pixmap is valid, mask it into a circle with `_circular_pixmap(...)`.
3. Set the resulting circular pixmap on the inner `QLabel`.
4. If the image fails to load, fall back to showing the hotkey text instead.

The circular masking (`MiniWidget._circular_pixmap`) works as follows:

1. Scale the source with `Qt.KeepAspectRatioByExpanding` so it fully fills the
   target circle without leaving empty edges.
2. Center-crop the scaled image to an exact square (the circle diameter, 54 px).
3. Create a transparent target pixmap.
4. Use `QPainter` with antialiasing and a `QPainterPath` ellipse clip.
5. Draw the cropped image inside the clipped circular region.

This produces a clean circular logo with no blue ring or square edges.

### Fallback and Hotkey Discoverability

Because the bubble shows the logo (not the hotkey text), the hotkey stays
discoverable through the tooltip:

- `MiniWidget.set_hotkey_tooltip(...)` sets a tooltip like
  `SentenceTool — Alt+Shift+R (click to open)`.
- The main window also shows a `Hotkey: ...` label.
- `set_hotkey_text(...)` still exists and is used only as the visual fallback
  when the logo image is missing.

### Interaction Behavior

`MiniWidget` handles its own mouse events:

- `mousePressEvent` records the press offset and resets a `_moved` flag.
- `mouseMoveEvent` drags the bubble by moving the window with the cursor.
- `mouseReleaseEvent` emits the `clicked` signal only if the bubble was not
  dragged (a clean click, not a drag), which restores the main window.

### Show / Hide Wiring

In `MainWindow`:

- `self._mini = MiniWidget(...)` is created in `__init__`.
- `self._mini.clicked.connect(self._restore_from_mini)`.
- `_hide_to_mini()` positions the bubble at the top-right of the current window
  geometry, shows it, then hides the main window.
- `_restore_from_mini()` simply calls `_show_window()`.
- `_show_window()` hides the bubble, shows and raises the main window, and
  ensures the tray icon stays visible.

If `ui.minimize_to_bubble` is `False` in settings, `_hide_to_mini()` skips the
bubble and hides to the tray only.

---

## 2. System Tray Integration

### Goal

The app always has a tray icon while running. The tray provides quick access to
show the window, start/stop listening, open settings, and exit. The tray is also
how the app surfaces notifications.

### Owning Component

- Setup method: `MainWindow._setup_tray`
- File: `app/ui/main_window.py`
- Qt class: `QSystemTrayIcon`

### Tray Icon

`MainWindow._tray_icon()` resolves the icon:

1. Try `assets/icon.ico` via `resource_path(...)`.
2. If present, return a `QIcon` from it.
3. Otherwise fall back to a standard Qt system icon
   (`SP_ComputerIcon`) so the tray always has a valid icon.

### Tray Menu

A `QMenu` is built once and stored on the instance (so PySide does not garbage
collect it). It contains:

- Show — `_show_window`
- Start — `start_listening`
- Stop — `stop_listening`
- Settings — `_open_settings`
- separator
- Exit — `_exit_app`

The menu is attached with `self.tray.setContextMenu(self._tray_menu)`.

### Tray Activation

`self.tray.activated.connect(self._on_tray_activated)`:

- On `ActivationReason.Trigger` (left click), the main window is restored via
  `_show_window()`.

### Keeping the Tray Alive

`_ensure_tray_visible()` re-shows the tray icon if it was hidden, unless the app
is in the middle of exiting. This is called after hide/restore/settings actions
so the tray never silently disappears while the app is still running.

### Notifications

The tray doubles as the notification channel using
`self.tray.showMessage(...)`, for example:

- Missing API key warnings.
- Hotkey registration failures.
- Rewrite result messages (success/failure feedback).

---

## 3. Exit Behavior (Terminating the Instance)

### Goal

Closing the window must not kill the app (it hides instead), but an explicit
Exit must fully terminate the process, release the tray icon, and free the
single-instance lock.

### The Close-vs-Exit Distinction

The app intentionally separates "hide" from "exit":

- `closeEvent` (`MainWindow.closeEvent`):
  - If `_is_exiting` is `True`, accept the event and let the window close.
  - Otherwise, ignore the close and call `_hide_to_mini()` instead.
  - This is why clicking the window's close path hides the app rather than
    quitting it.

- `app.setQuitOnLastWindowClosed(False)` in `app/main.py` ensures Qt does not
  auto-quit when the visible window is hidden/closed.

### Explicit Exit

`MainWindow._exit_app()` performs a clean shutdown:

1. Guard against re-entry with `_is_exiting`.
2. Set `_is_exiting = True` (so `closeEvent` will now accept).
3. `stop_listening()` — unregisters the global hotkey.
4. Hide the mini bubble.
5. Hide the tray icon.
6. Call `self.close()` (now accepted because `_is_exiting` is set).
7. Call `QApplication.instance().quit()` to end the event loop.

### Process-Level Cleanup

In `app/main.py`, after `app.exec()` returns, `_release_single_instance_lock()`
is called to release the lock file. An `atexit` handler is also registered as a
safety net so the lock is released even on unexpected termination.

---

## 4. Single-Instance Enforcement

### Goal

Only one copy of the app may run at a time. A second launch should detect the
existing instance and exit quietly.

### Implementation

- File: `app/main.py`
- Mechanism: an exclusive lock on a temp lock file using Windows `msvcrt`.

Flow:

1. `_acquire_single_instance_lock()`:
   - Opens `sentence_tool.lock` in the system temp directory.
   - Uses `msvcrt.locking(..., LK_NBLCK, 1)` for a non-blocking exclusive lock.
   - On success, writes the current PID and returns `True`.
   - On failure (already locked), returns `False`.
2. In `main()`, if the lock cannot be acquired, the app logs a warning and
   returns immediately (exit code 0) without showing any UI.
3. `_release_single_instance_lock()` unlocks and closes the file on shutdown and
   via `atexit`.

> Note: there is also a standalone reference implementation in
> `TraySingleInstanceApp/tray_single_instance_app.py`, but the production
> single-instance logic that ships in the app is the lock-file approach in
> `app/main.py`.

---

## 5. Portable EXE (Run Without Installation)

### Goal

Ship a single self-contained `SentenceTool.exe` that a user can copy and run
with no Python install, no dependency setup, and no installer.

### Tooling

- Packager: PyInstaller
- Spec file: `SentenceTool.spec`
- Build script: `build.ps1`

### What Gets Bundled (`SentenceTool.spec`)

`datas` declares the non-code files copied into the bundle:

- `app/ui/styles.qss` -> `app/ui` (the stylesheet)
- `config/appsettings.json` -> `config` (the default config template)
- `assets/icon.ico` -> `assets` (tray/app icon, only if present)
- `assets/Media/Meg.png` -> `assets/Media` (the logo, only if present)

Hidden import:

- `keyboard` is force-included via `hiddenimports` because the global hotkey
  library is imported in a way PyInstaller may not auto-detect.

### Single-File Output

The `EXE(...)` block is configured for a portable, windowed build:

- `name="SentenceTool"` -> output `SentenceTool.exe`.
- `console=False` -> no console window (GUI app).
- `upx=True` -> compress to reduce size.
- `runtime_tmpdir=None` -> default one-folder extraction at runtime.
- `icon=...` -> uses `assets/icon.ico` when available.

Because `a.binaries` and `a.datas` are passed into `EXE(...)`, the result is a
single `.exe` containing the Python runtime, PySide6, all dependencies, and the
bundled data files.

### Resource Resolution at Runtime

`app/utils/resources.py` makes bundled paths work in both dev and packaged mode:

- `resource_path(relative)` checks `sys._MEIPASS` (set by PyInstaller at runtime).
  - In a packaged build, it resolves relative to the extracted bundle dir.
  - In development, it resolves relative to the project root.

This is why the QSS, icon, logo, and config template all load correctly from the
portable `.exe`.

### Writable Config Outside the Bundle

The bundle is read-only at runtime, so user settings cannot be written back into
it. `app/config/config_manager.py` handles this:

- `user_config_path()` (from `app/utils/resources.py`) points to a writable
  per-user location under `%APPDATA%\SentenceTool\appsettings.json`.
- On first run, `_seed_from_template()` copies the bundled
  `config/appsettings.json` into that writable location.
- All saves go to the writable copy, so settings persist across runs of the
  portable exe.

### Optional Startup Integration

`app/services/startup_service.py` supports "Start with Windows" using the
registry Run key. In a frozen build it registers `sys.executable` (the exe path),
so the portable exe can auto-start on login without an installer.

### Build Steps (`build.ps1`)

1. Create `.venv` if missing.
2. Upgrade pip and install `requirements.txt` plus `pyinstaller`.
3. Run `pyinstaller --noconfirm --clean SentenceTool.spec`.
4. Output the portable app at `dist\SentenceTool.exe`.

To rebuild after code changes:

```powershell
.\build.ps1
```

---

## 6. End-to-End Lifecycle Summary

1. User double-clicks the portable `dist\SentenceTool.exe`.
2. `main()` acquires the single-instance lock; a second launch exits silently.
3. Qt starts with `quitOnLastWindowClosed=False`.
4. Config loads from `%APPDATA%`, seeded from the bundled template on first run.
5. The main window and tray icon appear.
6. Hiding the window shows the circular logo bubble (or tray-only) and keeps the
   tray icon alive.
7. Clicking the bubble or the tray restores the window.
8. Exit (window button or tray menu) stops the hotkey, hides the bubble and tray,
   quits the Qt loop, and releases the lock file.

---

## 7. Key Files Reference

| Concern | File | Key symbols |
| --- | --- | --- |
| Logo bubble | `app/ui/main_window.py` | `MiniWidget`, `_set_logo_or_fallback`, `_circular_pixmap` |
| Bubble styling | `app/ui/styles.qss` | `#MiniBubble`, `#MiniLabel` |
| Hide / restore | `app/ui/main_window.py` | `_hide_to_mini`, `_restore_from_mini`, `_show_window` |
| Tray | `app/ui/main_window.py` | `_setup_tray`, `_tray_icon`, `_on_tray_activated`, `_ensure_tray_visible` |
| Exit | `app/ui/main_window.py` | `closeEvent`, `_exit_app` |
| Single instance | `app/main.py` | `_acquire_single_instance_lock`, `_release_single_instance_lock` |
| Resource paths | `app/utils/resources.py` | `resource_path`, `user_config_path` |
| Writable config | `app/config/config_manager.py` | `_seed_from_template`, `load`, `save` |
| Startup | `app/services/startup_service.py` | `set_run_on_login` |
| Packaging | `SentenceTool.spec`, `build.ps1` | `datas`, `EXE(...)` |
