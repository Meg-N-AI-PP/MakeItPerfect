# SentenceTool

A lightweight Windows desktop tool that rewrites the text you have selected — anywhere — with a single hotkey. Select text, press **Ctrl + Alt + R**, and the selection is replaced with an AI-improved version based on the mode you chose.

## Features

- Floating, always-on-top widget; minimizes to a small draggable bubble (click to reopen)
- Three rewrite modes (radio buttons): **Correct Grammar**, **Make It Better**, **Super**
- Global hotkey **`Ctrl + Alt + R`** that works in most text inputs (Notepad, browsers, VS Code, chat apps); the combo is suppressed so the underlying app doesn't also react to it
- In-app **Settings** dialog to store your API key, model list, and timeout
- Runtime model/mode switching — no restart needed
- System tray support (Show / Start / Stop / Settings / Exit)
- Optional "Start with Windows"
- Original clipboard is restored after each rewrite

## Quick start (portable, no Python needed)

1. Build (or obtain) `dist\SentenceTool.exe` — see [Build a portable .exe](#build-a-portable-exe).
2. Double-click `SentenceTool.exe`.
3. Click the **⚙ gear** (or tray → Settings), paste your **OpenAI API key**, click **Save**.
4. Pick a model and mode, click **Start**.
5. Select text anywhere and press **Ctrl + Alt + R**.

Your settings are stored per-user at `%APPDATA%\SentenceTool\appsettings.json` (and logs at `%APPDATA%\SentenceTool\logs\`). The executable itself stays clean and portable.

## Where the API key lives

- **In the app:** open **Settings** and paste the key — saved to `%APPDATA%\SentenceTool\appsettings.json`.
- **Developer override:** set `OPENAI_API_KEY` (e.g. in a `.env` file at the project root). If present, it overrides the saved key at runtime.

The bundled template ships with an empty key, so no secret is distributed.

## Run from source (development)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

For development you can put your key in a `.env` file (git-ignored; see `.env.example`):

```
OPENAI_API_KEY=sk-...
```

> Note: global hotkeys may require running with sufficient permissions. If the hotkey does not fire, try launching from an elevated terminal.

## Build a portable .exe

```powershell
.\build.ps1
```

This installs PyInstaller and produces a single-file **`dist\SentenceTool.exe`**. Under the hood it runs `SentenceTool.spec`, which bundles the stylesheet and config template.

To distribute: share `dist\SentenceTool.exe`. Each user opens Settings and enters their own API key.

## Auto-start with Windows

Tick **Start with Windows** in the widget. This adds a `Run` registry entry pointing at the executable (or the dev launcher). Untick to remove it.

## Tests

```powershell
pip install pytest
pytest
```

## Privacy

When you trigger a rewrite, the selected text is sent to the OpenAI API. No text history is stored locally.

## Project layout

```
app/
  config/      settings + config loading (per-user, seeded from template)
  models/      enums, DTOs, runtime state
  prompts/     prompt builder
  services/    clipboard, hotkey, openai, rewrite orchestrator, startup
  ui/          floating widget, mini bubble, settings dialog, stylesheet
  utils/       logger, resource/path helpers
  main.py      entry point
config/        appsettings.json (bundled template)
tests/         unit tests
SentenceTool.spec, build.ps1   packaging
```

