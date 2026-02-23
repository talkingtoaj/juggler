# 🐙 Context Switcher

A lightweight Windows utility that keeps a curated list of your open windows with personal notes, so you can switch between them instantly — without hunting through the taskbar.

---

## Features

- **Pin any open window** with a colour-coded card
- **Add a note** to each card ("debugging auth", "chapter 3", etc.)
- **Click a card** to bring that window to the foreground
- **Ctrl+Alt+O** to cycle to the next pinned window from anywhere — no need to open the app
- Closed windows are automatically removed from the list

---

## Installation (Windows)

### Option A — Automatic installer (recommended)

1. Download `ContextSwitcher.exe` and `install.ps1` from the [latest release](../../releases/latest)
2. Put both files in the same folder
3. Right-click `install.ps1` → **Run with PowerShell**

The installer will:
- Copy `ContextSwitcher.exe` to `%LOCALAPPDATA%\Programs\ContextSwitcher\`
- Add it to **Windows startup** (runs when you log in)
- Create a **Desktop shortcut**

### Option B — Manual

1. Download `ContextSwitcher.exe` from the [latest release](../../releases/latest)
2. Copy it anywhere you like (e.g. `C:\Users\<you>\Programs\ContextSwitcher\`)
3. Double-click to run

To add to startup manually: press `Win+R`, type `shell:startup`, and paste a shortcut to the exe there.

---

## Usage

1. Launch Context Switcher
2. Click the **+** button to add windows you want to track
3. Type a note on any card to remind yourself what you're doing there
4. Click a card to jump to that window, or press **Ctrl+Alt+O** from anywhere

### Keyboard shortcut

| Shortcut | Action |
|----------|--------|
| `Ctrl+Alt+O` | Cycle to the next pinned window (works globally, app can be in background) |
| `F5` | Refresh — removes any closed windows from the list |
| `Ctrl+Q` | Quit |

---

## Uninstall

Run `install.ps1` again and choose **Uninstall**, or manually:
1. Delete `%LOCALAPPDATA%\Programs\ContextSwitcher\`
2. Delete the Desktop shortcut
3. Open Task Manager → Startup apps → disable Context Switcher

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
    --name ContextSwitcher main.py
```

---

## Data

Settings and pinned windows are saved to `%USERPROFILE%\.context-switcher\data.json`.
