# 🐙 Juggler

> Juggle your windows, not your attention.

[![Latest Release](https://img.shields.io/github/v/release/talkingtoaj/context-switcher)](https://github.com/talkingtoaj/context-switcher/releases/latest)
[![Windows](https://img.shields.io/badge/platform-Windows-blue)](https://github.com/talkingtoaj/context-switcher/releases/latest)

Juggler is a tiny Windows utility that keeps a colour-coded shortlist of your open windows — with personal notes — so you can jump between them in one click or one keypress.

---

## Install

**[⬇ Download Juggler.exe + install.ps1](https://github.com/talkingtoaj/context-switcher/releases/latest)**

1. Download both files from the link above
2. Put them in the same folder
3. Right-click `install.ps1` → **Run with PowerShell**

That's it. Juggler will appear on your Desktop and start automatically when you log in.

> **No Python or dependencies needed** — it's a single standalone `.exe`.

---

## How it works

```
1. Pin a window     →   click  +  and pick from your open apps
2. Add a note       →   type a reminder on any card ("debugging auth", "ch.3 draft")
3. Jump to it       →   click the card   or   press  Ctrl+Alt+O
```

**Ctrl+Alt+O** cycles through your pinned windows from anywhere — even when Juggler itself is in the background.

---

## Screenshot

```
┌─────────────────────────────────────┐
│  🐙 Juggler                [_][X]  │
├─────────────────────────────────────┤
│  ✕  █ story.py — VS Code            │
│       "Chapter 3 draft"              │
│                                      │
│  ✕  █ Terminal — WSL                │
│       "Running dev server"           │
│                                      │
│  ✕  █ Chrome — Stack Overflow       │
│       "Research: window API"         │
├─────────────────────────────────────┤
│           [      +      ]            │
│    Ctrl+Alt+O — cycle to next window │
└─────────────────────────────────────┘
```

---

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+Alt+O` | Cycle to next pinned window (global) |
| `F5` | Refresh — removes closed windows |
| `Ctrl+Q` | Quit |

---

## Uninstall

Run `install.ps1` again and choose **Uninstall**, or manually:

1. Delete `%LOCALAPPDATA%\Programs\Juggler\`
2. Delete the Desktop shortcut
3. Press `Win+R` → type `shell:startup` → delete any Juggler shortcut there

Your saved data (`%USERPROFILE%\.juggler\data.json`) is not touched.

---

## Build from source

Requirements: Windows, [uv](https://github.com/astral-sh/uv), Python 3.11+

```powershell
git clone https://github.com/talkingtoaj/context-switcher.git
cd context-switcher
uv run python main.py
```

To build a standalone `.exe`:

```powershell
uv run --with pyinstaller --with pywin32 --with PyQt6 --with pillow pyinstaller `
    --onefile --noconsole --icon=icon2.ico `
    --add-data "icon.png;." --add-data "icon2.png;." --add-data "icon2.ico;." `
    --name Juggler main.py
```
