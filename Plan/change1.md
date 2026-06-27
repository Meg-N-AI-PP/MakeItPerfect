# Change 1 Implementation Detail

## Purpose

This document turns the requests from `Plan/changeandimprove.md` into a repo-specific implementation plan for the current Python/PySide6 application.

Requested changes:

1. Replace the floating circle widget hotkey text with the `Meg` logo image.
2. Remove the current model list and keep only `gpt-5.4`, `gpt-5.5`, and `gpt-5.6`.
3. Add a `Result Language` dropdown with `English`, `Chinese`, `Japanese`, and `Swiss German`.

## Current Repo Findings

The existing code already has clear ownership for each requested change:

- The floating circle widget is `MiniWidget` in `app/ui/main_window.py`.
- The widget currently renders hotkey text through `MiniWidget.set_hotkey_text()`.
- The model dropdown is built in `app/ui/main_window.py` from `self._settings.openai.available_models`.
- The Settings dialog also allows model editing in `app/ui/settings_window.py`.
- Model defaults and validation live in `app/config/settings.py` and `config/appsettings.json`.
- The prompt currently forces the output to stay in the original language in `app/prompts/prompt_builder.py`.
- The runtime state currently tracks only `model`, `mode`, and `is_running` in `app/models/app_state.py`.
- The requested image already exists in `Plan/Media/Meg.png`, but the app currently packages runtime assets from `assets/...`, not `Plan/...`.

## Recommended Implementation Order

Implement the three changes in this order:

1. Add the logo asset to the runtime package path.
2. Replace the mini bubble text with the logo rendering.
3. Lock down the model list to the three requested models.
4. Add a result-language enum/state/UI flow.
5. Update prompt construction so the selected result language is applied.
6. Add or update tests for config and prompt behavior.

This order reduces risk because the bubble image and model list are isolated UI/config changes, while language selection changes the app state, prompt generation, and rewrite path together.

## Change 1: Show the `Meg` Logo in the Circle Widget

### Goal

When the main window is hidden to the mini floating bubble, the circle should display the `Meg` logo image instead of showing the hotkey text split across lines.

### Current Behavior

In `app/ui/main_window.py`, `MiniWidget`:

- creates a 58 x 58 frameless always-on-top bubble
- creates `self._label = QLabel("")`
- calls `set_hotkey_text()`
- renders the hotkey text such as `Ctrl\n+R`

### Required Code Changes

#### 1. Move or copy the logo into a runtime asset location

Current file found:

- `Plan/Media/Meg.png`

Recommended runtime location:

- `assets/Media/Meg.png`

Reason:

- the app already resolves packaged files with `resource_path(...)`
- the tray icon already uses `assets/icon.ico`
- `SentenceTool.spec` already bundles `assets` selectively

Do not load the image from `Plan/...` at runtime. That folder is clearly planning documentation, not application assets.

#### 2. Update PyInstaller packaging

In `SentenceTool.spec`, add the new image to `datas`, for example:

```python
datas = [
    ("app/ui/styles.qss", "app/ui"),
    ("config/appsettings.json", "config"),
    ("assets/Media/Meg.png", "assets/Media"),
]
```

This ensures the mini widget image still loads in the built `.exe`.

#### 3. Replace text rendering in `MiniWidget`

In `app/ui/main_window.py`:

- import `QPixmap` from `PySide6.QtGui`
- change `MiniWidget.__init__` so it can accept a logo path or resolve it internally
- replace the current text-only label logic with image loading and scaling
- keep a fallback path so the widget still works if the image is missing

Recommended approach:

- keep `QLabel` as the display surface
- load `QPixmap(str(resource_path("assets/Media/Meg.png")))`
- scale it to fit inside the 58 x 58 bubble, for example about 42 to 46 px
- set `Qt.KeepAspectRatio` and `Qt.SmoothTransformation`
- if the pixmap does not load, fall back to the existing hotkey text logic

Suggested implementation shape:

```python
class MiniWidget(QWidget):
    def __init__(self, hotkey_text: str) -> None:
        ...
        self._label = QLabel("")
        ...
        self._set_logo_or_fallback(hotkey_text)

    def _set_logo_or_fallback(self, hotkey_text: str) -> None:
        logo_path = resource_path("assets/Media/Meg.png")
        pixmap = QPixmap(str(logo_path))
        if not pixmap.isNull():
            self._label.setPixmap(
                pixmap.scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self._label.setText("")
            return
        self.set_hotkey_text(hotkey_text)
```

#### 4. Preserve hotkey visibility somewhere else

Because the bubble will no longer show the hotkey text visually, keep the hotkey discoverable in one of these places:

- keep it in the main window label: `Hotkey: Alt+Shift+R`
- include it in the bubble tooltip, for example `SentenceTool — Alt+Shift+R`

This is a usability improvement and avoids losing the shortcut hint entirely.

### Validation

Manual validation:

1. Launch the app.
2. Hide the main widget to the mini bubble.
3. Confirm the bubble shows the `Meg` image.
4. Delete or temporarily rename the image and confirm the fallback still shows hotkey text.
5. Build the executable and confirm the image still appears in the packaged app.

## Change 2: Restrict Model Selection to `gpt-5.4`, `gpt-5.5`, `gpt-5.6`

### Goal

The app should no longer expose old models such as `gpt-5`, `gpt-4.1`, or `gpt-4o`. The effective model list should be exactly:

- `gpt-5.4`
- `gpt-5.5`
- `gpt-5.6`

### Current Behavior

The model list is currently editable in multiple places:

- default values in `app/config/settings.py`
- user config in `config/appsettings.json`
- settings dialog free-form multiline editor in `app/ui/settings_window.py`
- runtime refresh in `MainWindow._refresh_models()`

### Required Code Changes

#### 1. Update application defaults

In `app/config/settings.py`:

- change `default_model` from `gpt-5` to `gpt-5.4`
- change `available_models` default from `["gpt-5"]` to `["gpt-5.4", "gpt-5.5", "gpt-5.6"]`

#### 2. Update shipped config

In `config/appsettings.json`:

- set `default_model` to `gpt-5.4`
- replace the current `available_models` array with only the three requested models

#### 3. Remove the old fallback in Settings

In `app/ui/settings_window.py`, `_save()` currently uses this fallback:

```python
if not models:
    models = ["gpt-4o"]
```

This must be changed to:

```python
if not models:
    models = ["gpt-5.4", "gpt-5.5", "gpt-5.6"]
```

#### 4. Improve the Settings UI design for models

There are two valid approaches.

Preferred approach:

- remove the free-form multiline model editor entirely
- replace it with a read-only explanation or fixed dropdown showing supported models

Reason:

- the user asked for a fixed curated model list
- free-form editing invites invalid or unsupported values
- the app currently treats invalid model selection as a runtime error instead of preventing it up front

Minimal approach:

- keep the multiline editor
- prefill only `gpt-5.4`, `gpt-5.5`, `gpt-5.6`
- validate the saved values against an allowed list

If implementation speed matters most, choose the minimal approach. If product correctness matters more, choose the preferred approach.

#### 5. Centralize the supported model list

Improvement recommended:

- define a single constant for supported models instead of repeating the list across config, UI, and tests

Possible location:

- `app/config/settings.py`
- or a new small module such as `app/config/constants.py`

Suggested constant:

```python
SUPPORTED_MODELS = ["gpt-5.4", "gpt-5.5", "gpt-5.6"]
DEFAULT_MODEL = "gpt-5.4"
```

This avoids drift between defaults, validation, and UI population.

### Validation

Manual validation:

1. Open the app and verify the model dropdown only shows the three requested models.
2. Open Settings and verify old models are no longer present.
3. Save settings and verify the selected model persists.
4. Start a rewrite using each model at least once.

Test updates:

- update `tests/test_config_manager.py` to assert the new default and fallback behavior
- add a validation test that unsupported models are rejected if strict validation is added

## Change 3: Add a `Result Language` Dropdown

### Goal

Add a new dropdown so the user can choose the destination language of the AI result:

- English
- Chinese
- Japanese
- Swiss German

The selected language should apply immediately while the tool is running, just like the current mode selection.

### Current Behavior

The app does not currently support language selection.

Current blocker:

- `app/prompts/prompt_builder.py` explicitly says `Preserve the original language of the text.`

So even if a UI dropdown were added today, the prompt would still instruct the model not to translate.

### Required Code Changes

#### 1. Add a new enum for result language

In `app/models/enums.py`, add a new enum following the existing `PromptMode` pattern.

Suggested shape:

```python
class ResultLanguage(str, Enum):
    ENGLISH = "english"
    CHINESE = "chinese"
    JAPANESE = "japanese"
    SWISS_GERMAN = "swiss_german"

    @property
    def label(self) -> str:
        return {
            ResultLanguage.ENGLISH: "English",
            ResultLanguage.CHINESE: "Chinese",
            ResultLanguage.JAPANESE: "Japanese",
            ResultLanguage.SWISS_GERMAN: "Swiss German",
        }[self]
```

Also add a `from_label()` method if you want symmetry with `PromptMode`.

#### 2. Extend runtime app state

In `app/models/app_state.py`, add a new field:

```python
result_language: ResultLanguage = ResultLanguage.ENGLISH
```

Then initialize it in `MainWindow.__init__` from settings.

#### 3. Persist the selected language in config

Recommended change:

- add a new persisted setting rather than keeping this as session-only state

Simplest place:

- add `result_language` under `behavior` in `app/config/settings.py`

Example:

```python
class BehaviorSettings(BaseModel):
    ...
    result_language: str = "english"
```

Better typed version:

```python
class BehaviorSettings(BaseModel):
    ...
    result_language: ResultLanguage = ResultLanguage.ENGLISH
```

If you use the typed enum, Pydantic will help validate invalid config values.

Also update `config/appsettings.json` to include the default language.

#### 4. Add the dropdown to the main window

In `app/ui/main_window.py`:

- add a new field label: `Result Language`
- add a `QComboBox` under the model dropdown or under the mode controls
- populate it from the new enum labels
- initialize it from `self._state.result_language`
- connect `currentTextChanged` to a new `_on_result_language_changed()` handler

Suggested UI placement:

1. Model
2. Result Language
3. Mode
4. Start / Stop / Exit

This keeps the user’s output choices grouped together.

#### 5. Persist language changes from the UI

In `_on_result_language_changed()`:

- update `self._state.result_language`
- update `self._settings.behavior.result_language`
- call `self._config.save()` so the choice survives restart

This matches the requirement that changes should apply while the tool is active.

#### 6. Update prompt generation

In `app/prompts/prompt_builder.py`:

- stop hard-coding `Preserve the original language of the text.`
- replace it with language-aware guidance based on the selected result language

Recommended API change:

```python
def build_system_prompt(mode: PromptMode, result_language: ResultLanguage) -> str:
    ...
```

Add a helper that maps enum values to explicit instructions.

Example:

```python
_LANGUAGE_INSTRUCTIONS = {
    ResultLanguage.ENGLISH: "Return the final text in English.",
    ResultLanguage.CHINESE: "Return the final text in Chinese.",
    ResultLanguage.JAPANESE: "Return the final text in Japanese.",
    ResultLanguage.SWISS_GERMAN: "Return the final text in Swiss German.",
}
```

Then build the prompt like this:

```python
return f"{_MODE_INSTRUCTIONS[mode]} {_SHARED_GUARDRAILS} {_LANGUAGE_INSTRUCTIONS[result_language]}"
```

#### 7. Pass language through the rewrite path

This change must flow across the service boundary.

In `app/services/rewrite_service.py`:

- pass `self._state.result_language` into `OpenAIService.rewrite(...)`

In `app/services/openai_service.py`:

- update the method signature to accept `result_language`
- pass it through to `build_system_prompt(...)`

Suggested signature:

```python
def rewrite(
    self,
    text: str,
    model: str,
    mode: PromptMode,
    result_language: ResultLanguage,
) -> str:
```

### Important Product Note: `Swiss German` Ambiguity

This item should be reviewed before implementation is considered complete.

`Swiss German` can mean one of two things:

- Swiss Standard German written with Swiss spelling conventions
- true Swiss German dialect output

These are not the same thing, and model output quality may vary significantly if the prompt simply says `Swiss German`.

Recommended prompt wording for now:

- if the user truly wants dialect: `Return the final text in Swiss German dialect.`
- if the user wants business-friendly Swiss German writing: `Return the final text in Swiss Standard German using Swiss spelling conventions.`

If no clarification is provided, keep the UI label as `Swiss German` but document the prompt wording decision in code comments or release notes.

### Validation

Manual validation:

1. Launch the app and verify the new dropdown appears.
2. Select each language and run a rewrite on the same sample input.
3. Confirm the output language changes even when the source language is different.
4. Change the language while the tool is already running and confirm the next rewrite uses the new language.
5. Restart the app and confirm the previous language selection persists.

Test updates:

- update `tests/test_prompt_builder.py` to assert each selected language injects the correct language instruction
- update `tests/test_rewrite_service.py` fakes so the service path covers the new `result_language` argument
- add a config test covering persistence and validation of the new language field

## Suggested File-by-File Change List

### Must change

- `app/ui/main_window.py`
- `app/ui/settings_window.py`
- `app/config/settings.py`
- `app/models/app_state.py`
- `app/models/enums.py`
- `app/prompts/prompt_builder.py`
- `app/services/openai_service.py`
- `app/services/rewrite_service.py`
- `config/appsettings.json`
- `SentenceTool.spec`
- `tests/test_prompt_builder.py`
- `tests/test_config_manager.py`
- `tests/test_rewrite_service.py`

### Must add or move

- add or move `Meg.png` into `assets/Media/Meg.png`

## Recommended Implementation Sequence

1. Create `assets/Media/Meg.png` from the existing planning asset.
2. Update `SentenceTool.spec` so the image is bundled.
3. Update `MiniWidget` to display the image with text fallback.
4. Update model defaults and config to the three requested models.
5. Simplify or restrict the Settings model editor.
6. Add `ResultLanguage` enum.
7. Extend `AppState` and config persistence.
8. Add the main-window dropdown and live change handler.
9. Update prompt generation and rewrite service signatures.
10. Update tests.
11. Run focused tests for config, prompt, and rewrite behavior.

## Focused Test Plan

Run these tests after implementation:

```powershell
pytest tests/test_prompt_builder.py tests/test_config_manager.py tests/test_rewrite_service.py
```

Then do one manual UI pass:

1. verify logo bubble
2. verify model list
3. verify result-language dropdown
4. verify persistence after restart
5. verify packaged build still loads the image

## Summary

The requested changes fit the current architecture cleanly. The only non-obvious issue discovered during review is that the `Meg` image currently lives in `Plan/Media/Meg.png`, which is not a runtime asset path and is not bundled by the existing PyInstaller spec. That asset location must be corrected as part of the implementation.