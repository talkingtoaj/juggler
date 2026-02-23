"""
Main Window - PyQt6 UI for Context Switcher
"""

import sys
import platform
from datetime import datetime
from typing import Optional

# Windows API — imported lazily inside methods to avoid crash-at-import in frozen exe
_win32api = None
_win32gui = None
_win32con = None

def _load_win32():
    global _win32api, _win32gui, _win32con
    if _win32api is not None:
        return True
    try:
        import win32api, win32gui, win32con
        _win32api = win32api
        _win32gui = win32gui
        _win32con = win32con
        return True
    except Exception:
        return False

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit,
    QFrame, QMessageBox, QInputDialog, QMenuBar, QMenu, QStatusBar,
    QSystemTrayIcon, QDialog, QScrollArea, QGridLayout, QCheckBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QColor, QPalette, QBrush

# Our imports
from .window_manager import WindowManager, filter_system_windows
from .data_store import (
    get_pinned_windows, save_pinned_windows,
    add_pinned_window, remove_pinned_window, update_pinned_window,
    get_settings, save_settings,
    get_last_activated_index, set_last_activated_index
)


# Bright/pale color palette for pinned windows (20 colors)
# These are all light/pastel colors suitable for backgrounds with dark text
COLORS = [
    "#FFCDD2",  # Pale Red
    "#F8BBD0",  # Pale Pink
    "#E1BEE7",  # Pale Purple
    "#D1C4E9",  # Pale Lavender
    "#C5CAE9",  # Pale Blue
    "#BBDEFB",  # Light Blue
    "#B3E5FC",  # Light Cyan
    "#B2EBF2",  # Pale Cyan
    "#B2DFDB",  # Pale Teal
    "#C8E6C9",  # Pale Green
    "#DCEDC8",  # Pale Lime
    "#F0F4C3",  # Pale Yellow-Green
    "#FFF9C4",  # Pale Yellow
    "#FFECB3",  # Pale Amber
    "#FFE0B2",  # Pale Orange
    "#FFCCBC",  # Pale Deep Orange
    "#D7CCC8",  # Pale Brown
    "#CFD8DC",  # Pale Blue Grey
    "#FFCDD2",  # Pale Red (backup)
    "#F8BBD0",  # Pale Pink (backup)
]


def get_next_color(used_colors: list) -> str:
    """Get the first color not already used.
    
    Args:
        used_colors: List of color strings already assigned to pinned windows
        
    Returns:
        The next available color from the palette
    """
    for color in COLORS:
        if color not in used_colors:
            return color
    # If all colors used, cycle back to first
    return COLORS[0]


class PinnedWindowItem(QFrame):
    """A single pinned window in the list."""
    
    # Signal when user clicks to activate
    activated = pyqtSignal(int)
    # Signal when user wants to delete
    deleted = pyqtSignal(int)
    # Signal when note is edited
    note_edited = pyqtSignal(int, str)
    
    def __init__(self, window_data: dict, parent=None):
        super().__init__(parent)
        self.window_data = window_data
        self.hwnd = window_data.get("hwnd")
        self.setup_ui()
        
    def setup_ui(self):
        """Build the UI for this item."""
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

        bg_color = self.window_data.get("color", COLORS[0])
        self.setStyleSheet(f"QFrame {{ background-color: {bg_color}; border-radius: 8px; }}")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Delete button on the left — always visible
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedWidth(34)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #c62828;
                font-size: 13px;
                font-weight: bold;
                border-radius: 8px 0 0 8px;
            }
            QPushButton:hover {
                background-color: #FF6B6B;
                color: white;
            }
        """)
        self.delete_btn.clicked.connect(lambda: self.deleted.emit(self.hwnd))
        layout.addWidget(self.delete_btn)

        # Window info: title + note
        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(4, 10, 12, 10)
        info_layout.setSpacing(4)

        title = self.window_data.get("title", "Unknown")
        if len(title) > 50:
            title = title[:47] + "..."
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #000000; background: transparent;"
        )
        self.title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.title_label.mousePressEvent = self._handle_click
        info_layout.addWidget(self.title_label)

        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Add a note...")
        self.note_edit.setText(self.window_data.get("note", ""))
        self.note_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #1a237e;
                font-size: 12px;
            }
        """)
        self.note_edit.textChanged.connect(lambda text: self.note_edited.emit(self.hwnd, text))
        info_layout.addWidget(self.note_edit)

        layout.addWidget(info_widget)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _handle_click(self, event):
        """Handle click on color bar to activate window."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self.hwnd)
        
    def mousePressEvent(self, event):
        """Handle click to activate window."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self.hwnd)
        super().mousePressEvent(event)
    
    def update_valid_state(self, is_valid: bool):
        """Update visual state based on window validity."""
        bg_color = self.window_data.get("color", COLORS[0])
        if is_valid:
            self.setStyleSheet(f"QFrame {{ background-color: {bg_color}; border-radius: 8px; }}")
            self.title_label.setStyleSheet(
                "font-weight: bold; font-size: 13px; color: #000000; background: transparent;"
            )
        else:
            self.setStyleSheet("QFrame { background-color: #ffebee; border-radius: 8px; }")
            self.title_label.setStyleSheet(
                "font-weight: bold; font-size: 13px; color: #999; text-decoration: line-through; background: transparent;"
            )


class WindowPickerDialog(QDialog):
    """Dialog to pick windows to add."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_window = None
        self.setup_ui()
        self.load_windows()
        
    def setup_ui(self):
        """Build the UI."""
        self.setWindowTitle("Add Window")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter windows...")
        self.search_edit.textChanged.connect(self.filter_windows)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Window list
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.list_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("Add Selected")
        add_btn.setDefault(True)
        add_btn.clicked.connect(self.accept)
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
        
    def load_windows(self):
        """Load available windows."""
        if not WindowManager.is_available():
            self.list_widget.addItem("Windows API not available")
            return
        
        # Get all windows
        all_windows = WindowManager.get_all_windows()
        
        # Filter system windows
        windows = filter_system_windows(all_windows)
        
        # Get already pinned window HWNDs
        pinned = get_pinned_windows()
        pinned_hwids = set(w.get("hwnd") for w in pinned)
        
        # Get our own window title to filter out
        our_title = "Context Switcher"
        
        # Filter out already-pinned windows and our own app
        filtered = [
            w for w in windows 
            if w["hwnd"] not in pinned_hwids 
            and "context switcher" not in w["title"].lower()
            and w["title"].strip()  # Skip empty titles
        ]
        
        # Sort by title
        filtered.sort(key=lambda w: w["title"].lower())
        
        # Add to list
        for w in filtered:
            item = QListWidgetItem(w["title"])
            item.setData(Qt.ItemDataRole.UserRole, w)
            self.list_widget.addItem(item)
    
    def filter_windows(self, text: str):
        """Filter the window list."""
        text_lower = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text_lower not in item.text().lower())
    
    def get_selected_window(self) -> Optional[dict]:
        """Get the selected window data."""
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self._hotkey_timer = None
        self._hotkey_cooldown = False
        self.setup_ui()
        self.load_pinned_windows()
        self.check_window_validity()
        if platform.system() == "Windows":
            QTimer.singleShot(1500, self._start_hotkey_polling)
        
    def setup_ui(self):
        """Build the main UI."""
        self.setWindowTitle("🐙 Context Switcher")
        self.setMinimumSize(400, 300)
        self.resize(450, 500)
        
        # Set app icon
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header row with compact green + button
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header = QLabel("Pinned Windows")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        header_row.addWidget(header)
        header_row.addStretch()
        add_btn = QPushButton("+")
        add_btn.setFixedSize(36, 36)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setToolTip("Add Window")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 22px;
                font-weight: bold;
                padding-bottom: 2px;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:pressed { background-color: #1B5E20; }
        """)
        add_btn.clicked.connect(self.show_window_picker)
        header_row.addWidget(add_btn)
        layout.addLayout(header_row)
        
        # Scroll area for pinned windows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.pinned_container = QWidget()
        self.pinned_layout = QVBoxLayout(self.pinned_container)
        self.pinned_layout.setSpacing(8)
        self.pinned_layout.addStretch()
        
        scroll.setWidget(self.pinned_container)
        layout.addWidget(scroll)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Menu bar
        self.create_menu_bar()
        
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        refresh_action = QAction("Refresh Window List", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.check_window_validity)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Always on top toggle
        self.always_on_top_action = QAction("Always on Top (Icon)", self)
        self.always_on_top_action.setCheckable(True)
        self.always_on_top_action.setChecked(False)
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)
        view_menu.addAction(self.always_on_top_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def toggle_always_on_top(self, checked: bool):
        """Toggle always on top behavior."""
        if checked:
            # Set window to stay on top (like an icon that floats above)
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self.show()
            self.statusBar().showMessage("Always on top enabled - window will float above others")
        else:
            # Remove always on top
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self.show()
            self.statusBar().showMessage("Always on top disabled")
    
    def load_pinned_windows(self):
        """Load pinned windows from storage."""
        # Clear existing
        while self.pinned_layout.count() > 1:  # Keep the stretch
            item = self.pinned_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Load from storage
        pinned = get_pinned_windows()
        
        for window_data in pinned:
            self.add_pinned_item(window_data)
        
        if not pinned:
            self.statusBar().showMessage("No windows pinned. Click '+ Add Window' to get started.")
        else:
            self.statusBar().showMessage(f"{len(pinned)} window(s) pinned")
    
    def add_pinned_item(self, window_data: dict):
        """Add a pinned window item to the list."""
        item = PinnedWindowItem(window_data)
        item.activated.connect(self.activate_window)
        item.deleted.connect(self.delete_window)
        item.note_edited.connect(self.save_note)
        
        # Insert before the stretch
        self.pinned_layout.insertWidget(
            self.pinned_layout.count() - 1, 
            item
        )
    
    def show_window_picker(self):
        """Show the window picker dialog."""
        dialog = WindowPickerDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            window_data = dialog.get_selected_window()
            if window_data:
                self.add_window(window_data)
    
    def add_window(self, window_data: dict):
        """Add a new window to the pinned list."""
        # Get all currently used colors
        pinned = get_pinned_windows()
        used_colors = [w.get("color") for w in pinned if w.get("color")]
        
        # Get next available color
        next_color = get_next_color(used_colors)
        
        # Create new pinned window entry
        new_entry = {
            "hwnd": window_data["hwnd"],
            "title": window_data["title"],
            "note": "",
            "color": next_color,
            "added_at": datetime.now().isoformat()
        }
        
        # Save to storage
        if add_pinned_window(new_entry):
            # Add to UI
            self.add_pinned_item(new_entry)
            self.statusBar().showMessage(f"Added: {window_data['title'][:40]}")
        else:
            QMessageBox.warning(self, "Error", "Failed to save window")
    
    def activate_window(self, hwnd: int):
        """Activate a pinned window."""
        success, msg = WindowManager.activate_window(hwnd)
        
        if success:
            self.statusBar().showMessage("Window activated")
        else:
            QMessageBox.warning(self, "Cannot Activate", msg)
            # Mark as potentially invalid
            self.check_window_validity()
    
    def delete_window(self, hwnd: int):
        """Delete a pinned window."""
        if remove_pinned_window(hwnd):
            self.load_pinned_windows()
            self.statusBar().showMessage("Window removed")
        else:
            QMessageBox.warning(self, "Error", "Failed to remove window")
    
    def save_note(self, hwnd: int, note: str):
        """Save the note for a window."""
        update_pinned_window(hwnd, {"note": note})
    
    def check_window_validity(self):
        """Check which pinned windows are still valid."""
        if not WindowManager.is_available():
            return
        
        pinned = get_pinned_windows()
        valid_count = 0
        
        for i in range(self.pinned_layout.count() - 1):  # Skip stretch
            item = self.pinned_layout.itemAt(i).widget()
            if isinstance(item, PinnedWindowItem):
                is_valid = WindowManager.is_window_valid(item.hwnd)
                item.update_valid_state(is_valid)
                if is_valid:
                    valid_count += 1
        
        if valid_count != len(pinned):
            self.statusBar().showMessage(f"{valid_count}/{len(pinned)} windows valid")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Context Switcher",
            "<h3>🐙 Context Switcher</h3>"
            "<p>A simple tool to help you manage multiple windows "
            "with context notes.</p>"
            "<p>Version 0.1.0</p>"
        )
    
    def _start_hotkey_polling(self):
        """Start polling for Win+O using GetAsyncKeyState. No ctypes, no nativeEvent."""
        if not _load_win32():
            return
        self._hotkey_timer = QTimer()
        self._hotkey_timer.timeout.connect(self._check_hotkey)
        self._hotkey_timer.start(50)

    def _check_hotkey(self):
        """Check if Win+O is currently held; fire once per press with cooldown."""
        try:
            win_held = (bool(_win32api.GetAsyncKeyState(0x5B) & 0x8000) or
                        bool(_win32api.GetAsyncKeyState(0x5C) & 0x8000))
            o_held   = bool(_win32api.GetAsyncKeyState(0x4F) & 0x8000)

            if win_held and o_held:
                if not self._hotkey_cooldown:
                    self._hotkey_cooldown = True
                    self.cycle_and_activate_window()
            else:
                self._hotkey_cooldown = False
        except Exception:
            pass

    def cycle_and_activate_window(self):
        """Cycle to the next valid pinned window and activate it."""
        if not _load_win32():
            return
        pinned = get_pinned_windows()
        if not pinned:
            return
        last_index = get_last_activated_index()
        n = len(pinned)
        for offset in range(1, n + 1):
            next_index = (last_index + offset) % n
            window = pinned[next_index]
            hwnd = window.get("hwnd")
            if not hwnd:
                continue
            try:
                if not _win32gui.IsWindow(hwnd):
                    continue
                if _win32gui.IsIconic(hwnd):
                    _win32gui.ShowWindow(hwnd, _win32con.SW_RESTORE)
                fg_hwnd = _win32gui.GetForegroundWindow()
                tgt_tid = _win32gui.GetWindowThreadProcessId(hwnd)[0]
                if fg_hwnd:
                    fg_tid = _win32gui.GetWindowThreadProcessId(fg_hwnd)[0]
                    _win32gui.AttachThreadInput(fg_tid, tgt_tid, True)
                _win32gui.SetForegroundWindow(hwnd)
                if fg_hwnd:
                    _win32gui.AttachThreadInput(fg_tid, tgt_tid, False)
                set_last_activated_index(next_index)
                self.statusBar().showMessage(
                    f"Win+O → {window.get('title', 'Unknown')[:40]}"
                )
                return
            except Exception:
                continue

    def closeEvent(self, event):
        """Handle window close."""
        if self._hotkey_timer is not None:
            self._hotkey_timer.stop()
        event.accept()


def main():
    """Entry point."""
    # Check platform
    if platform.system() != "Windows":
        print("ERROR: This application requires Windows.")
        print("The window management features only work on Windows.")
        sys.exit(1)
    
    # Create application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern look
    
    # Create and show window
    window = MainWindow()
    window.show()
    
    # Run
    sys.exit(app.exec())


if __name__ == "__main__":
    main()