## SentenceTool Implementation Plan (Python Version)

## 1. Goal

Build a small Windows desktop productivity tool in Python that stays available as a floating widget or tray-based background app. The tool lets the user:

- choose an OpenAI model from a configurable list
- choose one of three rewrite modes
- start or stop background listening
- press `Ctrl + R` anywhere in Windows after selecting text
- send the selected text to an AI model
- replace the selected text with the improved result

The tool must feel lightweight, fast, modern, and practical for daily use.

## 2. Recommended Python Stack

Use Python for the first version because it is faster to ship and simpler to iterate on.

### Core runtime

- Python 3.12

### UI

- PySide6 for the desktop UI

Reason:

- more polished than Tkinter
- supports modern styling and animations
- good system tray support
- better long-term maintainability for desktop apps

### Global hotkey and keyboard simulation

- `keyboard` for global hotkey listening
- `pyautogui` or `keyboard` for sending `Ctrl + C` and `Ctrl + V`

### Clipboard

- `pyperclip` for text clipboard operations

### OpenAI integration

- official `openai` Python SDK

### Configuration and validation

- `pydantic` for settings validation
- built-in `json` for config storage

### Windows integration

- `pystray` is optional, but PySide6 already supports tray behavior through `QSystemTrayIcon`
- `winreg` for startup-with-Windows support

### Packaging

- `PyInstaller` for building a standalone `.exe`

## 3. Functional Scope for MVP

The first version should include only the features required to make the tool useful and reliable.

### In scope

- floating always-on-top widget
- model dropdown
- mode dropdown
- start button
- stop button
- hide to tray behavior
- exit button
- global hotkey: `Ctrl + R`
- clipboard-based text capture
- AI request to OpenAI
- selected text replacement
- runtime mode switching while the app is active
- runtime model switching while the app is active
- error notification for common failures
- local config file for API key and defaults

### Out of scope for MVP

- user login
- prompt history
- custom prompts
- translation modes
- OCR or image text capture
- support for local models
- response streaming in UI
- plugin system

## 4. Product Behavior Definition

### User workflow

1. User launches the app.
2. The widget appears in a small floating window.
3. User selects a model.
4. User selects a mode.
5. User clicks `Start`.
6. The app registers the global hotkey and enters running state.
7. In any text-editable application, the user highlights text.
8. The user presses `Ctrl + R`.
9. The app copies the selected text.
10. The app sends the text to OpenAI using the selected mode prompt.
11. The app pastes the AI response over the selected text.
12. The app restores the previous clipboard content.
13. The user may change model or mode without restarting the app.
14. The user may stop listening at any time.

### Rewrite modes

#### Mode 1: Correct Grammar

Behavior:

- fix grammar only
- keep meaning unchanged
- preserve tone as much as possible
- return corrected text only

Prompt intent:

"Correct the grammar and obvious sentence structure issues only. Keep the original meaning and tone. Return only the corrected text."

#### Mode 2: Make It Better

Behavior:

- improve clarity
- improve fluency
- keep original meaning
- sound more natural and professional
- return text only

Prompt intent:

"Improve this text for clarity, fluency, and professionalism while keeping the original meaning. Return only the improved text."

#### Mode 3: Super

Behavior:

- rewrite more strongly
- improve grammar, tone, clarity, and impact
- keep the user's core intent
- return text only

Prompt intent:

"Rewrite this text to be polished, professional, clear, and impactful while preserving the original intent. Return only the rewritten text."

## 5. Architecture

Use a layered structure so the UI, hotkey listener, clipboard logic, and AI service stay separate.

### Logical components

1. UI Layer
2. Application State Layer
3. Hotkey Listener Service
4. Clipboard Capture and Restore Service
5. Text Rewrite Orchestrator
6. OpenAI Client Service
7. Notification Service
8. Configuration Service
9. Windows Startup and Tray Service

### Data flow

1. UI updates selected model and mode in shared app state.
2. Hotkey service observes whether the app is running.
3. When `Ctrl + R` fires, the orchestrator starts a guarded processing pipeline.
4. The orchestrator captures current clipboard content.
5. The orchestrator copies current selected text from the active application.
6. The orchestrator validates that text was actually captured.
7. The orchestrator sends text to the AI client.
8. The orchestrator writes the result to clipboard.
9. The orchestrator pastes the new text into the active application.
10. The orchestrator restores the original clipboard.
11. The notification service reports success or failure.

## 6. Proposed Project Structure

```text
SentenceTool/
├─ app/
│  ├─ main.py
│  ├─ bootstrap.py
│  ├─ config/
│  │  ├─ settings.py
│  │  └─ config_manager.py
│  ├─ ui/
│  │  ├─ main_window.py
│  │  ├─ tray.py
│  │  ├─ widgets.py
│  │  └─ styles.qss
│  ├─ models/
│  │  ├─ app_state.py
│  │  ├─ enums.py
│  │  └─ dto.py
│  ├─ services/
│  │  ├─ hotkey_service.py
│  │  ├─ clipboard_service.py
│  │  ├─ rewrite_service.py
│  │  ├─ openai_service.py
│  │  ├─ notification_service.py
│  │  ├─ startup_service.py
│  │  └─ model_catalog_service.py
│  ├─ prompts/
│  │  └─ prompt_builder.py
│  └─ utils/
│     ├─ logger.py
│     ├─ threading.py
│     └─ retry.py
├─ assets/
│  ├─ icon.ico
│  └─ fonts/
├─ config/
│  └─ appsettings.json
├─ tests/
│  ├─ test_prompt_builder.py
│  ├─ test_config_manager.py
│  ├─ test_rewrite_service.py
│  └─ test_openai_service.py
├─ requirements.txt
├─ README.md
└─ build.spec
```

## 7. Detailed Step-by-Step Implementation Plan

## Phase 1. Define the application contract

### Step 1. Freeze the MVP behavior

Document the exact behavior before coding:

- only process plain text selections in MVP
- only support Windows in MVP
- only one hotkey: `Ctrl + R`
- only one active rewrite operation at a time
- only replace text when the selected text was captured successfully

Why this matters:

- it prevents scope drift
- it reduces inconsistent behavior across different applications

### Step 2. Define success criteria

The MVP is successful when:

- the app can remain running in the background
- the selected mode is respected immediately
- selected text is replaced in at least common apps such as Notepad, browser text boxes, VS Code, and chat inputs
- the app handles empty selections and API errors cleanly
- the app can be packaged as a Windows executable

## Phase 2. Set up the Python project

### Step 3. Initialize the repository structure

Create the directory layout shown above.

### Step 4. Create the environment and dependencies

Install:

- `PySide6`
- `openai`
- `pyperclip`
- `keyboard`
- `pyautogui`
- `pydantic`
- `pytest`
- `python-dotenv` if you decide to support environment-variable loading during development

### Step 5. Create `requirements.txt`

Pin versions after the first stable run to avoid environment drift.

### Step 6. Add logging support early

Create a simple logger that writes to a file under the user profile or app data folder.

Reason:

- clipboard and hotkey issues are hard to debug without logs

## Phase 3. Build configuration management

### Step 7. Design `appsettings.json`

Use a config file with this shape:

```json
{
	"openai": {
		"api_key": "",
		"default_model": "gpt-5",
		"available_models": ["gpt-5", "gpt-5.4", "gpt-4.1", "gpt-4o"]
	},
	"hotkey": {
		"modifier": "ctrl",
		"key": "r"
	},
	"ui": {
		"always_on_top": true,
		"start_minimized_to_tray": false,
		"theme": "dark"
	},
	"behavior": {
		"copy_wait_ms": 120,
		"paste_wait_ms": 80,
		"request_timeout_seconds": 20,
		"restore_clipboard": true
	},
	"startup": {
		"run_on_windows_login": false
	}
}
```

### Step 8. Validate config on startup

Use `pydantic` models to validate:

- API key presence
- non-empty model list
- valid timeout ranges
- valid hotkey values

If config is invalid:

- show a clear startup error
- disable `Start` until corrected

### Step 9. Separate runtime state from persisted config

Persisted config stores defaults.
Runtime state stores the current selection and running status.

This separation avoids accidental config corruption when the user only changes the active mode temporarily.

## Phase 4. Build the UI shell

### Step 10. Create the main floating widget

Use a small PySide6 window with:

- app title
- model dropdown
- mode dropdown
- running status label
- start button
- stop button
- hide button or minimize behavior
- exit button

Recommended window behavior:

- fixed compact size around 280 x 200
- frameless or low-chrome look if stable
- draggable from the title area
- always on top

### Step 11. Apply a modern visual style

Use Qt Style Sheets for:

- rounded corners
- dark neutral background
- accent color for active state
- modern combo boxes
- subtle hover states on buttons

Do not overcomplicate animation in MVP. Focus on clarity and polish.

### Step 12. Add tray icon support

When the user closes the window:

- optionally hide to tray instead of exiting

Tray menu should include:

- Show
- Start
- Stop
- Exit

### Step 13. Bind UI controls to app state

The UI must update state immediately when:

- model changes
- mode changes
- app starts
- app stops

The currently selected mode must be the one used for the next hotkey action without restart.

## Phase 5. Implement prompt strategy

### Step 14. Create a `PromptMode` enum

Values:

- `CORRECT_GRAMMAR`
- `MAKE_IT_BETTER`
- `SUPER`

### Step 15. Create a prompt builder

The prompt builder should:

- accept mode and input text
- return a clean prompt structure for the OpenAI API
- enforce `return text only`

### Step 16. Add prompt guardrails

To reduce bad output, each prompt should tell the model:

- do not add explanations
- do not wrap the answer in quotes
- do not use bullet points
- return only the rewritten text

### Step 17. Handle short fragments and full paragraphs

The prompt builder should work for:

- one-line sentences
- fragments
- multiple sentences
- email-like text

This avoids mode logic being too narrow.

## Phase 6. Implement OpenAI integration

### Step 18. Create `OpenAIService`

Responsibilities:

- initialize client with API key
- send text rewrite requests
- pass selected model
- apply timeout
- return plain text

### Step 19. Normalize responses

The service should trim:

- leading whitespace
- trailing whitespace
- accidental wrapping quotes if the model returns them

### Step 20. Add retry policy for transient failures

Retry only for safe transient failures such as:

- network interruption
- rate limit with short backoff
- temporary server failure

Do not retry indefinitely.

### Step 21. Define failure classes

Map errors into simple UI-facing messages:

- missing API key
- timeout
- rate limited
- invalid model
- request failed

## Phase 7. Implement the clipboard pipeline

### Step 22. Create a clipboard snapshot model

Store:

- previous text clipboard content
- whether clipboard text existed

For MVP, restoring plain text is enough. Full binary clipboard restoration is more complex and can be a later improvement.

### Step 23. Build `ClipboardService`

Responsibilities:

- read clipboard text
- write clipboard text
- save old clipboard content
- restore old clipboard content

### Step 24. Build selection capture logic

Processing sequence:

1. capture current clipboard text state
2. clear clipboard or mark baseline
3. simulate `Ctrl + C`
4. wait configured milliseconds
5. read clipboard
6. compare with baseline
7. determine whether a valid selection was captured

### Step 25. Protect against false capture

Cases to detect:

- no selected text
- selected object is not text
- clipboard content did not change
- copied text is empty or whitespace only

### Step 26. Build replacement logic

Processing sequence:

1. write rewritten text to clipboard
2. simulate `Ctrl + V`
3. wait briefly
4. restore original clipboard if enabled

## Phase 8. Implement the rewrite orchestrator

### Step 27. Create `RewriteService`

This is the core workflow service. It should coordinate:

- hotkey request admission
- clipboard capture
- prompt generation
- AI call
- paste replacement
- clipboard restoration
- error handling

### Step 28. Prevent concurrent rewrites

Add a processing lock so if the user presses `Ctrl + R` repeatedly:

- only one request runs at a time
- additional presses are ignored or show a short busy message

This prevents clipboard corruption and duplicate pastes.

### Step 29. Keep UI responsive

Run rewrite operations off the UI thread using:

- `QThread`
- `QRunnable` with `QThreadPool`
- or Python threading if carefully bridged back to Qt signals

Recommended choice:

- `QThreadPool` with signals for status updates

### Step 30. Emit clear lifecycle states

Possible statuses:

- Idle
- Running
- Listening
- Capturing text
- Sending request
- Replacing text
- Success
- Error

The UI should display only the most useful states, not all internal details.

## Phase 9. Implement global hotkey behavior

### Step 31. Create `HotkeyService`

Responsibilities:

- register global hotkey
- unregister hotkey
- call rewrite workflow when triggered
- respect app running state

### Step 32. Choose a stable hotkey approach

Recommended MVP approach:

- use `keyboard.add_hotkey('ctrl+r', callback)`

Important note:

- some Windows environments may require elevated permission for global hooks
- this must be documented in README and tested on the target machine

### Step 33. Guard against self-trigger loops

Make sure simulated keyboard actions do not accidentally re-trigger the hotkey pipeline.

Strategy:

- ignore hotkey events while the rewrite service lock is active

## Phase 10. Notifications and UX feedback

### Step 34. Add lightweight notifications

Show small notifications for:

- started
- stopped
- no text selected
- request failed
- timeout
- rewrite complete

Possible implementations:

- tray balloon notifications
- small in-app toast label
- temporary status label in widget

Recommended MVP:

- status label in widget plus tray notification for errors

### Step 35. Show active mode clearly

The user should always be able to see:

- current model
- current mode
- whether listening is active

This is critical because the tool is meant to stay running in the background.

## Phase 11. Windows startup integration

### Step 36. Add startup toggle

Add a checkbox or settings control:

- `Start with Windows`

### Step 37. Implement registry integration

Use `winreg` to add or remove the executable path under:

`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

### Step 38. Handle packaged app path correctly

When running from a packaged `.exe`, write the executable path.
When running in development mode, either disable the setting or clearly document behavior.

## Phase 12. Model management

### Step 39. Start with config-driven models

For MVP, the dropdown should load from config.

Reason:

- simpler and more reliable than dynamic model discovery
- avoids startup dependency on network availability

### Step 40. Validate selected model against config

If a model is removed from config but was saved as default:

- fall back to the first available model
- log the fallback

### Step 41. Keep dynamic model fetch as a future enhancement

Dynamic provider model discovery can be added later after the core workflow is stable.

## Phase 13. Security and privacy decisions

### Step 42. Decide where API key lives

For MVP options:

1. store in config file
2. load from environment variable
3. store in Windows Credential Manager later

Recommended development approach:

- allow environment variable for local development
- allow config file for controlled local use

Recommended production improvement:

- move to Windows Credential Manager in a later version

### Step 43. Document privacy behavior

State clearly in README:

- selected text is sent to OpenAI when hotkey is used
- no local history is stored unless explicitly added later

This is important for user trust.

## Phase 14. Testing plan

### Step 44. Unit test prompt generation

Test:

- each mode builds the intended instruction
- text-only return guardrails are included

### Step 45. Unit test config loading

Test:

- valid config passes
- invalid config fails with useful messages
- default fallbacks work

### Step 46. Unit test OpenAI service wrapping

Mock API responses to test:

- normal success
- timeout
- invalid model
- rate limit

### Step 47. Integration test rewrite orchestration with mocks

Mock:

- clipboard read/write
- keyboard send
- AI response

Validate:

- selected text is captured
- rewritten text is pasted
- clipboard is restored

### Step 48. Manual test matrix on Windows

Test in:

- Notepad
- VS Code editor
- browser textarea
- Outlook compose window if available
- Teams or Slack input if available

Also test:

- no selection
- long paragraph
- multiline content
- API disconnected
- pressing hotkey twice quickly
- changing mode while app is running

## Phase 15. Packaging and distribution

### Step 49. Package with PyInstaller

Build a Windows executable.

Ensure bundling includes:

- icon
- Qt dependencies
- config template
- style assets

### Step 50. Test packaged behavior separately

Validate after packaging:

- tray icon works
- startup registry entry points to packaged executable
- logging path is valid
- config file is discoverable
- hotkey still works outside the terminal

### Step 51. Prepare release artifacts

Deliver:

- `SentenceTool.exe`
- default `appsettings.json`
- short user guide

## 8. Detailed Implementation Order

Use this order to reduce integration risk.

### Milestone 1: foundation

1. create project structure
2. install dependencies
3. build config loader
4. add logger

### Milestone 2: UI shell

5. build PySide6 floating window
6. add model and mode selectors
7. add start, stop, hide, exit buttons
8. add tray icon and tray menu

### Milestone 3: core text pipeline

9. build clipboard service
10. build hotkey service
11. prove `Ctrl + C` capture works in Notepad
12. prove `Ctrl + V` replace works in Notepad

### Milestone 4: AI workflow

13. build prompt builder
14. build OpenAI service
15. connect rewrite orchestrator
16. validate end-to-end rewrite in a simple text editor

### Milestone 5: hardening

17. add locking and busy-state handling
18. add notifications and error mapping
19. test mode switching while active
20. test clipboard restore logic

### Milestone 6: polish and release

21. add startup-with-Windows setting
22. apply modern styling
23. package with PyInstaller
24. run manual Windows compatibility tests

## 9. Key Risks and Mitigations

### Risk 1. Clipboard race conditions

Problem:

- another app or user action may change clipboard during processing

Mitigation:

- keep operations short
- lock processing to one request
- restore clipboard immediately after paste

### Risk 2. Global hotkey reliability

Problem:

- some environments block or intercept hooks

Mitigation:

- test early on target machines
- keep hotkey implementation isolated so it can be replaced later if needed

### Risk 3. Some apps do not support standard copy/paste selection flow

Problem:

- certain apps or secure fields may not allow normal clipboard capture

Mitigation:

- define MVP as best-effort for standard text inputs
- show a graceful error instead of failing silently

### Risk 4. AI output may over-rewrite text

Problem:

- output may change intent too much, especially in `Super` mode

Mitigation:

- tighten prompts
- keep mode definitions strict
- allow users to switch modes instantly

### Risk 5. API key exposure

Problem:

- plain config storage is not ideal

Mitigation:

- support environment variable in development
- plan Credential Manager support next

## 10. Recommended MVP Decisions

To keep the first version stable, use these choices:

- Python 3.12
- PySide6 UI
- config-driven model list
- `keyboard` for global hotkey
- `pyperclip` for text clipboard
- one rewrite at a time
- text-only clipboard restore
- tray support included in MVP
- startup-with-Windows included in MVP if packaging is already stable

## 11. Suggested Future Enhancements After MVP

Only after the base workflow is reliable:

1. custom prompt modes
2. editable hotkey settings
3. Azure OpenAI support
4. Ollama and LM Studio support
5. Windows Credential Manager for secrets
6. model refresh from provider API
7. rewrite preview before paste
8. history and undo for the last replacement
9. richer clipboard restoration for non-text content
10. per-application exclusions

## 12. Final Recommendation

Build the first version as a Python desktop app with PySide6, a clipboard-based rewrite pipeline, and a strict single-hotkey workflow. The most important engineering focus is not the UI or the model list. It is the reliability of this sequence:

- capture selected text
- send it to the right prompt and model
- replace it safely
- restore the clipboard

If that loop is reliable, the tool will already be useful. Everything else can be improved incrementally.
