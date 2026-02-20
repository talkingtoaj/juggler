"""
Data Store - JSON Persistence for Context Switcher
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Default data directory
DATA_DIR = Path.home() / ".context-switcher"
DATA_FILE = DATA_DIR / "data.json"


def ensure_data_dir():
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> Dict[str, Any]:
    """Load saved data from JSON file."""
    ensure_data_dir()
    
    if not DATA_FILE.exists():
        return get_default_data()
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading data: {e}")
        return get_default_data()


def save_data(data: Dict[str, Any]) -> bool:
    """Save data to JSON file."""
    ensure_data_dir()
    
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error saving data: {e}")
        return False


def get_default_data() -> Dict[str, Any]:
    """Get default data structure."""
    return {
        "pinned_windows": [],
        "mini_widget": {
            "enabled": False,
            "x": 1800,
            "y": 50
        },
        "settings": {
            "always_on_top": False,
            "start_minimized": False
        }
    }


# Convenience functions
def get_pinned_windows() -> List[Dict[str, Any]]:
    """Get list of pinned windows."""
    data = load_data()
    return data.get("pinned_windows", [])


def save_pinned_windows(windows: List[Dict[str, Any]]) -> bool:
    """Save pinned windows list."""
    data = load_data()
    data["pinned_windows"] = windows
    return save_data(data)


def add_pinned_window(window: Dict[str, Any]) -> bool:
    """Add a pinned window."""
    data = load_data()
    data["pinned_windows"].append(window)
    return save_data(data)


def remove_pinned_window(hwnd: int) -> bool:
    """Remove a pinned window by hwnd."""
    data = load_data()
    data["pinned_windows"] = [
        w for w in data["pinned_windows"] if w.get("hwnd") != hwnd
    ]
    return save_data(data)


def update_pinned_window(hwnd: int, updates: Dict[str, Any]) -> bool:
    """Update a pinned window's data."""
    data = load_data()
    for w in data["pinned_windows"]:
        if w.get("hwnd") == hwnd:
            w.update(updates)
            break
    return save_data(data)


def get_settings() -> Dict[str, Any]:
    """Get app settings."""
    data = load_data()
    return data.get("settings", {})


def save_settings(settings: Dict[str, Any]) -> bool:
    """Save app settings."""
    data = load_data()
    data["settings"] = settings
    return save_data(data)