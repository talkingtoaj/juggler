"""
Window Manager - Windows API wrapper using pywin32
"""

import platform
from typing import List, Dict, Optional, Tuple

# Only import on Windows
if platform.system() == "Windows":
    import win32gui
    import win32con
    import win32process
else:
    win32gui = None
    win32con = None
    win32process = None


class WindowManager:
    """Wrapper for Windows window management APIs."""
    
    @staticmethod
    def is_available() -> bool:
        """Check if Windows APIs are available."""
        return platform.system() == "Windows" and win32gui is not None
    
    @staticmethod
    def get_all_windows() -> List[Dict[str, any]]:
        """Get all visible windows with titles."""
        if not WindowManager.is_available():
            return []
        
        windows = []
        
        def callback(hwnd, _):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and len(title.strip()) > 0:
                        # Get window class name
                        class_name = ""
                        try:
                            class_name = win32gui.GetClassName(hwnd)
                        except:
                            pass
                        
                        # Get process name
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        except:
                            pid = 0
                        
                        windows.append({
                            "hwnd": hwnd,
                            "title": title,
                            "class_name": class_name,
                            "pid": pid
                        })
            except:
                pass
            return True
        
        win32gui.EnumWindows(callback, None)
        return windows
    
    @staticmethod
    def find_windows_by_name(keyword: str, case_sensitive: bool = False) -> List[Dict]:
        """Find windows whose titles contain the keyword."""
        all_windows = WindowManager.get_all_windows()
        
        if case_sensitive:
            return [w for w in all_windows if keyword in w["title"]]
        else:
            keyword_lower = keyword.lower()
            return [w for w in all_windows if keyword_lower in w["title"].lower()]
    
    @staticmethod
    def get_window_info(hwnd: int) -> Optional[Dict]:
        """Get detailed info about a specific window."""
        if not WindowManager.is_available():
            return None
        
        try:
            if not win32gui.IsWindow(hwnd):
                return None
            
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            rect = win32gui.GetWindowRect(hwnd)
            
            return {
                "hwnd": hwnd,
                "title": title,
                "class_name": class_name,
                "visible": win32gui.IsWindowVisible(hwnd),
                "enabled": win32gui.IsWindowEnabled(hwnd),
                "rect": {
                    "left": rect[0],
                    "top": rect[1],
                    "right": rect[2],
                    "bottom": rect[3]
                }
            }
        except:
            return None
    
    @staticmethod
    def activate_window(hwnd: int) -> Tuple[bool, str]:
        """Bring a window to the foreground.
        
        Returns:
            (success: bool, message: str)
        """
        if not WindowManager.is_available():
            return False, "Windows API not available"
        
        try:
            if not win32gui.IsWindow(hwnd):
                return False, f"Window handle {hwnd} is invalid"
            
            # First, try to restore if minimized
            # SW_RESTORE = 9, but win32con.SW_RESTORE is 9
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            except:
                pass
            
            # Then try to bring to front
            win32gui.SetForegroundWindow(hwnd)
            
            return True, "Window activated"
            
        except Exception as e:
            return False, f"Failed to activate: {e}"
    
    @staticmethod
    def minimize_window(hwnd: int) -> bool:
        """Minimize a window."""
        if not WindowManager.is_available():
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        except:
            return False
    
    @staticmethod
    def maximize_window(hwnd: int) -> bool:
        """Maximize a window."""
        if not WindowManager.is_available():
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return True
        except:
            return False
    
    @staticmethod
    def restore_window(hwnd: int) -> bool:
        """Restore a window to its previous size."""
        if not WindowManager.is_available():
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            return True
        except:
            return False
    
    @staticmethod
    def is_window_valid(hwnd: int) -> bool:
        """Check if a window handle is still valid."""
        if not WindowManager.is_available():
            return False
        
        try:
            return win32gui.IsWindow(hwnd)
        except:
            return False
    
    @staticmethod
    def is_window_minimized(hwnd: int) -> bool:
        """Check if a window is minimized."""
        if not WindowManager.is_available():
            return False
        
        try:
            return win32gui.IsIconic(hwnd)
        except:
            return False


# Filter functions for common window types
def filter_system_windows(windows: List[Dict]) -> List[Dict]:
    """Filter out system windows we don't want to show."""
    exclude_classes = {
        "Shell_TrayWnd",           # Taskbar
        "Shell_SecondaryTrayWnd",  # Secondary taskbar
        "Windows.UI.Core.CoreWindow",  # Windows 10/11 UI elements
        "ApplicationFrameWindow",  # UWP apps (often duplicates)
        "Progman",                 # Desktop
        "WorkerW",                 # Desktop worker
        "DV2ControlHost",         # Start menu
        "Windows.Internal.Shell.TabProxy",  # Tabbed windows
    }
    
    # Also exclude by title patterns
    exclude_titles = {
        "Program Manager",
        "Windows Input Experience",
        "Settings",
    }
    
    filtered = []
    for w in windows:
        # Skip excluded classes
        if w.get("class_name") in exclude_classes:
            continue
        
        # Skip excluded titles
        if w.get("title") in exclude_titles:
            continue
        
        # Skip very short titles
        if len(w.get("title", "").strip()) < 2:
            continue
            
        filtered.append(w)
    
    return filtered