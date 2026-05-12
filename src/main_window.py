"""
Main Window - PyQt6 UI for Juggler
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
    QFrame, QMessageBox, QScrollArea, QDialog
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QIcon, QColor, QPalette, QBrush, QKeySequence, QShortcut

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
    """Get the first color not already used."""
    for color in COLORS:
        if color not in used_colors:
            return color
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

        all_windows = WindowManager.get_all_windows()
        windows = filter_system_windows(all_windows)

        pinned = get_pinned_windows()
        pinned_hwids = set(w.get("hwnd") for w in pinned)

        filtered = [
            w for w in windows
            if w["hwnd"] not in pinned_hwids
            and "juggler" not in w["title"].lower()
            and w["title"].strip()
        ]

        filtered.sort(key=lambda w: w["title"].lower())

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

    _hotkey_signal = pyqtSignal()
    _update_prev_button_signal = pyqtSignal(str)  # thread-safe prev button update

    def __init__(self):
        super().__init__()
        self._hotkey_thread = None
        self._hotkey_thread_win_id = None
        self._fg_tracker_thread = None
        self._last_other_hwnd = None  # hwnd of last non-Juggler foreground window
        self._last_other_title = ""
        self._our_hwnd = 0
        self._hotkey_signal.connect(self.cycle_and_activate_window)
        self._update_prev_button_signal.connect(self._on_prev_button_update)
        self.setup_ui()
        self.load_pinned_windows()
        self.check_window_validity()
        if platform.system() == "Windows":
            QTimer.singleShot(1500, self._start_hotkey_thread)

    def setup_ui(self):
        """Build the main UI."""
        self.setWindowTitle("🐙 Juggler")
        self.setMinimumSize(400, 300)
        self.resize(450, 500)

        import os
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Button row: [📌 15%] [← 50%] [+ 35%] with 6px gaps
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        # Pin / always-on-top toggle (15%)
        self.pin_btn = QPushButton("📌")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setFixedHeight(40)
        self.pin_btn.setToolTip("Always on top")
        self.pin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pin_btn.setStyleSheet("""
            QPushButton {
                background-color: #546E7A;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #607D8B; }
            QPushButton:checked { background-color: #1565C0; }
            QPushButton:checked:hover { background-color: #1976D2; }
        """)
        self.pin_btn.clicked.connect(self.toggle_always_on_top)

        # Add previous window (50%)
        self.prev_btn = QPushButton("←")
        self.prev_btn.setFixedHeight(40)
        self.prev_btn.setEnabled(False)
        self.prev_btn.setToolTip("No previous window tracked yet")
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:pressed { background-color: #0D47A1; }
            QPushButton:disabled { background-color: #90A4AE; color: #CFD8DC; }
        """)
        self.prev_btn.clicked.connect(self.add_previous_window)

        # Add from list (35%)
        add_btn = QPushButton("+")
        add_btn.setFixedHeight(40)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setToolTip("Add window from list")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 26px;
                font-weight: bold;
                padding-bottom: 3px;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:pressed { background-color: #1B5E20; }
        """)
        add_btn.clicked.connect(self.show_window_picker)

        btn_row.addWidget(self.pin_btn, 15)
        btn_row.addWidget(self.prev_btn, 50)
        btn_row.addWidget(add_btn, 35)
        layout.addLayout(btn_row)

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

        # Keyboard shortcuts (documented in README)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.check_window_validity)
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)

    def changeEvent(self, event):
        """Auto-prune dead windows when app gains focus."""
        if event.type() == QEvent.Type.WindowActivate:
            self.check_window_validity()
        super().changeEvent(event)

    def toggle_always_on_top(self, checked: bool):
        """Toggle always on top."""
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self.show()
            self.statusBar().showMessage("Always on top enabled")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self.show()
            self.statusBar().showMessage("Always on top disabled")

    def _on_prev_button_update(self, title: str):
        """Thread-safe slot to update the ← button state."""
        if title:
            self.prev_btn.setEnabled(True)
            self.prev_btn.setToolTip(f"Add: {title}")
        else:
            self.prev_btn.setEnabled(False)
            self.prev_btn.setToolTip("No previous window tracked yet")

    def load_pinned_windows(self):
        """Load pinned windows from storage."""
        while self.pinned_layout.count() > 1:  # Keep the stretch
            item = self.pinned_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        pinned = get_pinned_windows()

        for window_data in pinned:
            self.add_pinned_item(window_data)

        if not pinned:
            self.statusBar().showMessage("No windows pinned. Click '← or +' to get started.")
        else:
            self.statusBar().showMessage(f"{len(pinned)} window(s) pinned")

    def add_pinned_item(self, window_data: dict):
        """Add a pinned window item to the list."""
        item = PinnedWindowItem(window_data)
        item.activated.connect(self.activate_window)
        item.deleted.connect(self.delete_window)
        item.note_edited.connect(self.save_note)

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
        pinned = get_pinned_windows()
        used_colors = [w.get("color") for w in pinned if w.get("color")]
        next_color = get_next_color(used_colors)

        new_entry = {
            "hwnd": window_data["hwnd"],
            "title": window_data["title"],
            "note": "",
            "color": next_color,
            "added_at": datetime.now().isoformat()
        }

        if add_pinned_window(new_entry):
            self.add_pinned_item(new_entry)
            self.statusBar().showMessage(f"Added: {window_data['title'][:40]}")
        else:
            QMessageBox.warning(self, "Error", "Failed to save window")

    def add_previous_window(self):
        """Add the last tracked non-Juggler foreground window."""
        hwnd = self._last_other_hwnd
        if not hwnd:
            return
        if not WindowManager.is_window_valid(hwnd):
            self._last_other_hwnd = None
            self._update_prev_button_signal.emit("")
            QMessageBox.warning(self, "Window Gone", "The previous window no longer exists.")
            return
        # Refresh title in case it changed
        title = self._last_other_title or "Unknown"
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
            if buf.value:
                title = buf.value
        except Exception:
            pass
        self.add_window({"hwnd": hwnd, "title": title})

    def activate_window(self, hwnd: int):
        """Activate a pinned window."""
        success, msg = WindowManager.activate_window(hwnd)

        if success:
            self.statusBar().showMessage("Window activated")
        else:
            QMessageBox.warning(self, "Cannot Activate", msg)
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
        """Remove closed and duplicate pinned windows."""
        if not WindowManager.is_available():
            return

        # Collect invalid (closed) hwnds from the UI
        to_remove = []
        for i in range(self.pinned_layout.count() - 1):  # Skip stretch
            item = self.pinned_layout.itemAt(i).widget()
            if isinstance(item, PinnedWindowItem):
                if not WindowManager.is_window_valid(item.hwnd):
                    to_remove.append(item.hwnd)

        # Collect duplicate hwnds from stored data (keep first occurrence)
        seen = set()
        for w in get_pinned_windows():
            hwnd = w.get("hwnd")
            if hwnd in seen:
                to_remove.append(hwnd)
            else:
                seen.add(hwnd)

        if to_remove:
            for hwnd in to_remove:
                remove_pinned_window(hwnd)
            self.load_pinned_windows()
            return  # load_pinned_windows updates the status bar

        pinned = get_pinned_windows()
        self.statusBar().showMessage(f"{len(pinned)} window(s) pinned")

    def _dbg(self, msg: str):
        """Append a timestamped line to the debug log."""
        import threading
        from pathlib import Path
        try:
            log_path = Path.home() / ".juggler" / "debug.txt"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().strftime('%H:%M:%S.%f')} tid={threading.get_ident()} {msg}\n")
        except Exception:
            pass

    def _start_hotkey_thread(self):
        """Spawn background threads for hotkey and foreground tracking."""
        import threading
        self._dbg("_start_hotkey_thread called")
        try:
            self._our_hwnd = int(self.winId())
        except Exception:
            self._our_hwnd = 0
        self._hotkey_thread = threading.Thread(
            target=self._hotkey_thread_func, daemon=True
        )
        self._hotkey_thread.start()
        self._fg_tracker_thread = threading.Thread(
            target=self._fg_tracker_thread_func, daemon=True
        )
        self._fg_tracker_thread.start()

    def _fg_tracker_thread_func(self):
        """Poll GetForegroundWindow every 250ms and track last non-Juggler window."""
        import ctypes
        import time
        user32 = ctypes.windll.user32
        last_seen_hwnd = None
        while True:
            time.sleep(0.25)
            try:
                hwnd = user32.GetForegroundWindow()
                if not hwnd or hwnd == last_seen_hwnd:
                    continue
                last_seen_hwnd = hwnd
                buf = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, buf, 256)
                title = buf.value
                if not title or 'juggler' in title.lower():
                    continue
                self._last_other_hwnd = hwnd
                self._last_other_title = title
                self._update_prev_button_signal.emit(title[:40])
            except Exception:
                pass

    def _hotkey_thread_func(self):
        """Background thread: registers Ctrl+Alt+O and blocks on GetMessageW."""
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32

        self._hotkey_thread_win_id = kernel32.GetCurrentThreadId()
        self._dbg(f"hotkey thread started, win_tid={self._hotkey_thread_win_id}")

        MOD_CTRL_ALT = 0x0003
        VK_O = 0x4F
        HOTKEY_ID = 1
        WM_HOTKEY = 0x0312
        WM_QUIT = 0x0012

        user32.UnregisterHotKey(None, HOTKEY_ID)
        result = user32.RegisterHotKey(None, HOTKEY_ID, MOD_CTRL_ALT, VK_O)
        last_err = ctypes.GetLastError()
        self._dbg(f"RegisterHotKey result={result} GetLastError={last_err}")

        if not result:
            self._dbg("RegisterHotKey FAILED — hotkey thread exiting")
            return

        msg = wintypes.MSG()
        self._dbg("entering GetMessageW loop")
        while True:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            self._dbg(f"GetMessageW ret={ret} message={msg.message:#06x} wParam={msg.wParam}")
            if ret == 0 or ret == -1:
                break
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self._dbg("HOTKEY FIRED — emitting signal")
                self._hotkey_signal.emit()
            if msg.message == WM_QUIT:
                break

        user32.UnregisterHotKey(None, HOTKEY_ID)
        self._dbg("hotkey thread exiting")

    def cycle_and_activate_window(self):
        """Cycle to the next valid pinned window and activate it."""
        self._dbg("cycle_and_activate_window called")
        try:
            import ctypes
            user32 = ctypes.windll.user32
        except Exception as e:
            self._dbg(f"ctypes import failed: {e}")
            return

        pinned = get_pinned_windows()
        self._dbg(f"pinned count={len(pinned)}")
        if not pinned:
            return

        last_index = get_last_activated_index()
        n = len(pinned)
        dead_hwnds = []
        for offset in range(1, n + 1):
            next_index = (last_index + offset) % n
            window = pinned[next_index]
            hwnd = window.get("hwnd")
            self._dbg(f"trying index={next_index} hwnd={hwnd} title={window.get('title','?')[:30]}")
            if not hwnd:
                continue
            try:
                if not user32.IsWindow(hwnd):
                    self._dbg(f"IsWindow=False, removing")
                    dead_hwnds.append(hwnd)
                    continue
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.AllowSetForegroundWindow(0xFFFFFFFF)
                user32.SetForegroundWindow(hwnd)
                set_last_activated_index(next_index)
                self._dbg(f"SetForegroundWindow done for hwnd={hwnd}")
                if dead_hwnds:
                    for dead in dead_hwnds:
                        remove_pinned_window(dead)
                    self.load_pinned_windows()
                self.statusBar().showMessage(
                    f"Ctrl+Alt+O → {window.get('title', 'Unknown')[:40]}"
                )
                return
            except Exception as e:
                self._dbg(f"exception on hwnd={hwnd}: {e}")
                continue
        if dead_hwnds:
            for hwnd in dead_hwnds:
                remove_pinned_window(hwnd)
            self.load_pinned_windows()
        self._dbg("no valid window found to activate")

    def closeEvent(self, event):
        """Handle window close."""
        try:
            if self._hotkey_thread_win_id is not None:
                import ctypes
                ctypes.windll.user32.PostThreadMessageW(
                    self._hotkey_thread_win_id, 0x0012, 0, 0  # WM_QUIT
                )
        except Exception:
            pass
        event.accept()


def main():
    """Entry point."""
    if platform.system() != "Windows":
        print("ERROR: This application requires Windows.")
        print("The window management features only work on Windows.")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
