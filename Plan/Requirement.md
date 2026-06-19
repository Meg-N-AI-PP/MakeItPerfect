I want a custom tool that written with python or c#, the tool is a ready to paste with AI help in text/sentences correct/fix, for example, user open the tool, then they can select a model from a models list which is available model from open ai for generate text (gpt-5, gpt-5.4,...), then they can choose one mode from 3 mode available from the tool which are:
1. Correct Grammar: which fix grammar issue on a sentences
2. Make it better: make the sentence better
3. Super: make the sentence more better

after a mode is selected, user start the tool and it will running in background. When it run, when user select a sentence and type CTRL + R, the tool will use AI model to make the sentence better based on the mode user selected, then update the selected sentence which user is selected. It can work any where. Whjle the tool running, user can change the mode and the mode will be apply.

The tool UI is small, enough space for mode select and model select, with start/stop/exit button, the UI is modern and look cool. Apply a small widget or make the tool always show in screen and only hide when user hide it.

I want you to based on that requirement, write a very detail implemetation plan step by step and send it here

This is actually a very good candidate for a desktop productivity tool.

Based on your requirements, I would recommend:

Technology Choice

Option 1 (Recommended): C# + .NET 9 + WPF

Native Windows experience
Easy global hotkey support
Better clipboard handling
Better UI/UX
Easy tray icon support
Easy startup with Windows
Better performance

Option 2: Python

Faster development
Easier AI integration
Harder to build polished UI
Global keyboard hooks less stable

For a tool you want to use every day, C# WPF is the best choice.

1. High-Level Architecture
┌─────────────────────────────┐
│        Floating Widget      │
│                             │
│ Model: GPT-5 ▼             │
│ Mode : Better ▼            │
│                             │
│ Start  Stop  Exit          │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│      Background Service     │
│                             │
│ Global Hotkey Listener      │
│ CTRL + R                    │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Clipboard Capture Service   │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ OpenAI API Service          │
│                             │
│ GPT-5                       │
│ GPT-5.4                     │
│ GPT-4.1                     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Clipboard Replace Service   │
└─────────────┬───────────────┘
              │
              ▼
      Replace selected text
2. User Flow
Start Tool

User opens application.

┌─────────────────────┐
│ AI Writing Helper   │
│                     │
│ Model              ▼│
│ [ GPT-5          ]  │
│                     │
│ Mode               ▼│
│ [ Make Better    ]  │
│                     │
│ ● Running          │
│                     │
│ Start Stop Exit    │
└─────────────────────┘
Example Usage

Original:

Please check and let me know if have any issue.

User:

Highlight sentence
CTRL + R

Tool automatically:

Please review this and let me know if there are any issues.

replaces the selected text.

Works in:

Outlook
Teams
Word
Browser
VS Code
Notepad++
ChatGPT
Slack
Anywhere text can be selected
3. UI Design
Floating Widget

Always visible.

╔════════════════════╗
║ AI Assistant       ║
╠════════════════════╣
║ Model: GPT-5     ▼║
║ Mode : Better    ▼║
║                    ║
║ [Start] [Stop]    ║
║                    ║
║ Ctrl+R Active     ║
╚════════════════════╝

Size:

250 x 180 px

Features:

Always on top
Draggable
Minimize to tray
Dark mode
Acrylic background

Windows 11 style.

4. Mode Definition
Mode 1
Correct Grammar

Prompt:

Correct grammar only.

Do not change meaning.
Do not add explanations.

Return corrected text only.

Example:

I has finish the report.

↓

I have finished the report.
Mode 2
Make It Better

Prompt:

Improve clarity and professionalism.

Keep original meaning.

Return text only.

Example:

Can you check this.

↓

Could you please review this?
Mode 3
Super

Prompt:

Rewrite professionally.

Improve grammar,
clarity,
tone,
impact.

Return text only.

Example:

Can you check this.

↓

Could you please review this and let me know if any adjustments are needed?
5. OpenAI Integration
Model List

Loaded from config:

[
  "gpt-5",
  "gpt-5.4",
  "gpt-4.1",
  "gpt-4o"
]

Or dynamically from OpenAI API.

6. Global Hotkey

Register:

CTRL + R

Using:

RegisterHotKey()

Windows API.

7. Text Capture Mechanism

This is the most important part.

Method

When CTRL + R pressed:

Step 1

Store clipboard.

oldClipboard
Step 2

Send:

CTRL + C

Programmatically.

Step 3

Wait

100 ms
Step 4

Read selected text from clipboard.

selectedText
8. AI Processing

Request:

{
  "model": "gpt-5",
  "input": "selected text"
}

Prompt depends on mode.

Response:

improved text
9. Replace Text

After AI response:

Copy response to clipboard.

Send:

CTRL + V

Result:

Selected text replaced automatically.

Restore original clipboard after completion.

10. Error Handling

If no text selected:

Toast:
"No text selected."

If API fails:

Toast:
"AI request failed."

If OpenAI timeout:

Toast:
"Request timeout."
11. Configuration

appsettings.json

{
  "OpenAI": {
    "ApiKey": "",
    "Model": "gpt-5"
  },
  "Hotkey": {
    "Modifier": "CTRL",
    "Key": "R"
  }
}
12. Tray Icon

When minimized:

Windows Tray

AI Writing Assistant

Right click:

Show
Start
Stop
Exit
13. Startup With Windows

Checkbox:

☑ Start with Windows

Registry:

HKCU\Software\Microsoft\Windows\CurrentVersion\Run
14. Modern UI Components

Recommended library:

WPF + ModernWPF

or

WPF + Material Design

Result:

Rounded corners
Blur background
Dark mode
Modern dropdown
Animated buttons
15. Suggested Project Structure
AIWritingAssistant
│
├── UI
│   ├── MainWindow.xaml
│   ├── SettingsWindow.xaml
│
├── Services
│   ├── OpenAIService.cs
│   ├── ClipboardService.cs
│   ├── TextReplacementService.cs
│   ├── HotkeyService.cs
│
├── Models
│   ├── AppSettings.cs
│   ├── PromptMode.cs
│
├── ViewModels
│   ├── MainViewModel.cs
│
├── Helpers
│   ├── ToastHelper.cs
│
└── Program.cs
16. Future Version (v2)

After MVP works, add:

Custom Prompts
Correct Grammar
Make Better
Super
Translate EN→VN
Translate VN→EN
Email Professional
Summarize
Custom Hotkeys
CTRL+R
CTRL+SHIFT+R
ALT+R
Streaming Response

Show:

Improving...

instead of waiting.

Local Models

Support:

Ollama
LM Studio
OpenAI
Azure OpenAI

User chooses provider.

17. Enterprise-Level Version (Best Architecture)

For long-term scalability:

WPF Desktop App
        │
        ▼
Local Background Service
        │
        ▼
Provider Layer
 ├─ OpenAI
 ├─ Azure OpenAI
 ├─ Ollama
 └─ LM Studio
        │
        ▼
Prompt Engine
        │
        ▼
Clipboard Replacement Engine

This architecture lets you later turn the tool into a commercial product similar to:

Grammarly
LanguageTool
Wordtune

while remaining lightweight and optimized for power users who need a universal Ctrl+R → AI rewrite selected text anywhere in Windows workflow.