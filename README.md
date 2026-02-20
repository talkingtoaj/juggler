# Context Switcher

_A Windows window manager with context notes._

## Overview

This is an MVP desktop utility that lets you:
1. Curate a list of currently-open windows (not *all* windows - just the ones relevant to your current task)
2. Add brief context notes to each ("Debugging auth flow", "Chapter 3 draft", etc.)
3. One-click to switch focus to any window
4. Optional: Mini floating widget for quick access

**Icon:** 🐙 [icon.png](./icon.png) — A cheerful octopus juggling multiple app windows, because managing chaos with a smile is the vibe.

## Problem It Solves

Agentic engineering = many terminals, browsers, editors open simultaneously. It's hard to remember which windows belong to which mental context. This is a lightweight "mission control" for your workflow.

---

## 🚀 Next Steps (Priority Order)

### 1. Spike: Verify Window API Works (30 min)
**Goal:** Confirm `win32gui` can reliably enumerate and activate windows in AJ's environment.

Create `spike_window_api.py`:
- List all visible windows with titles
- Try activating a few common ones (VS Code, Chrome, Terminal)
- Test `SetForegroundWindow()` behavior
- Document any quirks

### 2. Project Skeleton (1 hour)
**Goal:** Working PyQt6 window with basic layout.

Create `main.py`:
- PyQt6 application shell
- Main window with list widget
- "+" button placeholder
- JSON save/load scaffold
- Single-instance check (prevent multiple copies)

### 3. Window Picker Dialog (2 hours)
**Goal:** "+" button opens picker of currently open windows.

- Enumerate visible windows via `win32gui`
- Filter out the app itself, desktop, etc.
- Show list: icon (if possible) + title
- Click to "pin" window (save hwnd + title + random color)
- Add to main list

### 4. Core List Functionality (2 hours)
**Goal:** Pinned items work end-to-end.

- Display pinned windows: color bar, title, editable note
- Click item → `ShowWindow()` + `SetForegroundWindow()`
- Delete item (with confirmation)
- Auto-save JSON on changes
- Handle stale hwnd gracefully ("Window not found" message)

### 5. Mini Floating Widget (2 hours)
**Goal:** Optional draggable mini button.

- Toggle in menu/settings
- Frameless, always-on-top, draggable
- Position persistence
- Click → toggle main window visibility
- Right-click → context menu (Exit, Show Main, Disable Widget)

### 6. Polish & Ship (1 hour)
**Goal:** Usable daily driver.

- Random color assignment (pastel palette)
- Better error messages
- Taskbar/system tray integration
- Test on AJ's actual workflow
- Package for easy launch (shortcut + icon)

---

## Technical Research Summary

### ✅ Feasible (confirmed via research)

| Feature | Approach | Complexity |
|---------|----------|------------|
| **List open windows** | `win32gui.EnumWindows()` + `IsWindowVisible()` | Low |
| **Get window titles** | `win32gui.GetWindowText(hwnd)` | Low |
| **Activate/focus window** | `win32gui.SetForegroundWindow(hwnd)` | Low |
| **Store window handle** | Save `hwnd` (integer) + validate on use | Low |
| **UI Framework** | PyQt6 or tkinter | Medium |
| **Floating widget** | `Qt.WindowStaysOnTopHint` + `FramelessWindowHint` | Medium |
| **Drag to move** | Mouse event handlers | Low |

### ⚠️ Technical Challenges Identified

1. **Window persistence**: Window handles (`hwnd`) can become invalid if apps close/reopen. Need to:
   - Store window title as backup identifier
   - Gracefully handle "window no longer exists"
   - Allow user to "refresh" or re-link if hwnd is stale

2. **Window focus restrictions**: Windows security can block `SetForegroundWindow()` unless:
   - The calling process is already foreground, OR
   - Use `ShowWindow(hwnd, 5)` + `SetForegroundWindow()` combo (shown to work)
   - May need `Alt` key simulation in edge cases

3. **Mini widget positioning**: Need to store position across restarts (user preference)

4. **UI state management**: 
   - Main window (list view) vs mini widget toggle
   - Editable notes that save immediately
   - Random color assignment per item (store in JSON)

5. **Single instance**: Should probably only allow one instance of the app running

### 🛠️ Stack

- **Python 3.11+**
- **PyQt6** (UI framework)
- **pywin32** (Windows API access — Windows only)
- **uv** for dependency management

### Platform Note

**This app requires native Windows** because it uses `win32gui` to control Windows windows. It cannot run in WSL.

**Development approach:**
1. Build/test the spike on native Windows
2. Develop UI code in WSL if preferred (PyQt6 is cross-platform)
3. Always test window management features on native Windows

---

## MVP Feature Set

### v0.1 (MVP)
- [x] App icon designed (octopus mascot)
- [ ] Spike: Window API verification
- [ ] Main window with list of "pinned" windows
- [ ] "+" button opens picker showing currently open windows
- [ ] Each pinned item: color bar, window title, editable note text
- [ ] Click item = `SetForegroundWindow()` to activate
- [ ] Delete item from list
- [ ] Save/load JSON (window hwnd, title, note, color)
- [ ] Mini floating button (toggle show/hide main window)

### v0.2 (Nice to have)
- [ ] Drag-and-drop reordering
- [ ] "Refresh" button to update window titles
- [ ] Auto-detect if window closed (gray out item)
- [ ] Color picker instead of random
- [ ] Global hotkey to show/hide
- [ ] Named "sessions" (save/restore sets)

---

## Data Structure

```json
{
  "pinned_windows": [
    {
      "hwnd": 131844,
      "title": "story.py - VS Code",
      "note": "Working on Chapter 3",
      "color": "#4A90D9",
      "added_at": "2026-02-20T14:30:00"
    }
  ],
  "mini_widget": {
    "enabled": true,
    "x": 1800,
    "y": 50
  }
}
```

---

## UX Design

### Main Window Layout
```
┌─────────────────────────────────────┐
│  🐙 Context Switcher       [_][X] │
├─────────────────────────────────────┤
│  ┌─────┐                            │
│  │  +  │  Add current window         │
│  └─────┘                            │
├─────────────────────────────────────┤
│  █ Story.py - VS Code        [×]   │
│    "Chapter 3 draft"                 │
│                                      │
│  █ Terminal - WSL              [×]   │
│    "Running dev server"              │
│                                      │
│  █ Chrome - Stack Overflow     [×]   │
│    "Research: window API"              │
└─────────────────────────────────────┘
```

### Mini Widget
- Small circular button (40x40px) with octopus icon
- Frameless, always-on-top, draggable
- Top-right default position
- Click → toggle main window visibility
- Right-click → context menu (Exit, Show Main, Disable Mini)

---

## File Structure

```
projects/context-switcher/
├── README.md           # This file
├── icon.png            # App icon (octopus mascot)
├── pyproject.toml      # Dependencies (uv)
├── main.py             # Application entry point
├── spike_window_api.py # API verification script
└── src/
    ├── __init__.py
    ├── window_manager.py   # win32gui wrapper
    ├── main_window.py      # PyQt6 main UI
    ├── picker_dialog.py    # Window picker
    ├── mini_widget.py      # Floating button
    └── data_store.py       # JSON persistence
```

---

## Open Questions

1. Should clicking the mini widget open the main window or a compact dropdown?
2. What happens if a window is minimized when you click it? (Should restore first via `ShowWindow`)
3. Should we exclude certain window types? (Taskbar, system trays, etc.)

---

*Ready to start? Begin with the spike script to verify the core window API works in your environment.*
