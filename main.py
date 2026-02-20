#!/usr/bin/env python3
"""
Context Switcher - Main Entry Point

A Windows window manager with context notes.
Helps you keep track of what you're working on across multiple apps.

Usage:
    python main.py

Requirements:
    - Windows (native, not WSL)
    - Python 3.11+
    - PyQt6
    - pywin32
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main_window import main

if __name__ == "__main__":
    main()