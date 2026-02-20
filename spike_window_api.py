"""
SPIKE: Window API Verification (Robust Version)

This version logs everything to a file so you can review even if the window closes.
"""

import json
import time
import platform
import sys
import traceback
import io
from datetime import datetime

# Fix Unicode output for Windows Command Prompt
if platform.system() == "Windows":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

LOG_FILE = "spike_log.txt"

def log(msg, to_file=True, to_console=True):
    """Log to both console and file."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    
    if to_console:
        # Use ASCII-safe output for Windows cmd.exe (also sanitize window titles)
        line_ascii = line.replace("✓", "[OK]").replace("✗", "[X]").replace("⚠", "[!]")
        try:
            print(line_ascii)
        except UnicodeEncodeError:
            # Fallback: replace any remaining problematic chars
            print(line_ascii.encode('ascii', errors='replace').decode('ascii'))
        sys.stdout.flush()  # Force immediate output
    
    if to_file:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()


def main():
    # Clear old log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"Spike Log - {datetime.now()}\n")
        f.write("=" * 60 + "\n\n")
    
    try:
        log("Starting Window API Verification Spike...")
        
        # Platform check
        log(f"Detected platform: {platform.system()}")
        if platform.system() != "Windows":
            log("ERROR: This must run on native Windows!")
            log("Please run from Windows Command Prompt or PowerShell.")
            input("\nPress Enter to exit...")
            return
        
        log("✓ Running on Windows")
        
        # Try to import win32gui
        log("Importing pywin32...")
        try:
            import win32gui
            import win32con
            log("✓ pywin32 imported successfully")
        except ImportError as e:
            log(f"✗ ERROR: pywin32 not installed: {e}")
            log("Fix: uv sync --extra windows")
            input("\nPress Enter to exit...")
            return
        
        # Enumerate windows
        log("\n" + "=" * 60)
        log("STEP 1: Enumerating visible windows...")
        
        windows = []
        
        def callback(hwnd, extra):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and len(title.strip()) > 0:
                        windows.append({
                            "hwnd": hwnd,
                            "title": title,
                        })
            except Exception as e:
                log(f"  Error reading window {hwnd}: {e}", to_console=False)
            return True
        
        win32gui.EnumWindows(callback, None)
        log(f"✓ Found {len(windows)} visible windows with titles")
        
        # Show sample
        log("\nSample windows (first 15):")
        for i, w in enumerate(windows[:15], 1):
            log(f"  {i}. [{w['hwnd']}] {w['title'][:55]}")
        
        if len(windows) > 15:
            log(f"  ... and {len(windows) - 15} more")
        
        # Find common apps
        log("\n" + "=" * 60)
        log("STEP 2: Looking for common apps...")
        
        targets = [
            ("VS Code", ["code", "visual studio code", "code.exe"]),
            ("Chrome", ["chrome", "google chrome"]),
            ("Edge", ["edge", "microsoft edge"]),
            ("Terminal", ["terminal", "wt", "windows terminal"]),
            ("WSL", ["wsl", "ubuntu", "debian"]),
            ("Notepad", ["notepad"]),
            ("Explorer", ["file explorer", "explorer"]),
        ]
        
        found_apps = {}
        for app_name, keywords in targets:
            for keyword in keywords:
                matches = [w for w in windows if keyword.lower() in w["title"].lower()]
                if matches:
                    found_apps[app_name] = matches[0]
                    log(f"  ✓ Found {app_name}: '{matches[0]['title'][:50]}'")
                    break
            else:
                log(f"  ✗ {app_name} not found")
        
        # Test activation
        log("\n" + "=" * 60)
        log("STEP 3: Testing window activation...")
        log("(Windows will try to come to front - watch for them!)")
        
        if found_apps:
            test_list = list(found_apps.items())[:3]
            log(f"\nWill test {len(test_list)} window(s):")
            
            for i, (app_name, window) in enumerate(test_list, 1):
                log(f"\n  Test {i}: Activating {app_name}...")
                log(f"    HWND: {window['hwnd']}, Title: '{window['title'][:40]}'")
                
                try:
                    # Restore if minimized
                    log("    Calling ShowWindow(SW_RESTORE)...")
                    win32gui.ShowWindow(window['hwnd'], win32con.SW_RESTORE)
                    time.sleep(0.5)
                    
                    # Set foreground
                    log("    Calling SetForegroundWindow()...")
                    win32gui.SetForegroundWindow(window['hwnd'])
                    time.sleep(0.5)
                    
                    # Verify
                    fg_window = win32gui.GetForegroundWindow()
                    fg_title = win32gui.GetWindowText(fg_window)
                    
                    if fg_window == window['hwnd']:
                        log(f"    ✓ SUCCESS - Window is now in foreground")
                    else:
                        log(f"    ⚠ PARTIAL - Foreground is '{fg_title[:40]}' (expected {window['hwnd']}, got {fg_window})")
                    
                    if i < len(test_list):
                        log("    Pausing 1 second before next test...")
                        time.sleep(1)
                        
                except Exception as e:
                    log(f"    ✗ FAILED: {e}")
                    traceback.print_exc()
        else:
            log("  ⚠ No apps found to test!")
            log("  Open VS Code, Chrome, or Terminal and try again.")
        
        # Save results
        log("\n" + "=" * 60)
        log("STEP 4: Saving results...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "window_count": len(windows),
            "sample_windows": windows[:20],
            "found_apps": {k: {"hwnd": v["hwnd"], "title": v["title"]} 
                          for k, v in found_apps.items()},
            "success": len(found_apps) > 0
        }
        
        with open("spike_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        log("✓ Results saved to spike_results.json")
        log(f"✓ Full log saved to {LOG_FILE}")
        
        # Summary
        log("\n" + "=" * 60)
        log("SUMMARY")
        log("=" * 60)
        
        if found_apps:
            log(f"✓ Found {len(found_apps)} app(s)")
            log("✓ Window API is working!")
            log("\nNext: Build the full app (Step 2: Project Skeleton)")
        else:
            log("⚠ No common apps detected")
            log("  Open VS Code, Chrome, Terminal, etc. and re-run")
        
        log("\n" + "=" * 60)
        
    except Exception as e:
        log(f"\n✗ UNEXPECTED ERROR: {e}")
        log(traceback.format_exc())
        log(f"\nCheck {LOG_FILE} for details")
    
    # Always pause
    log("\nPress Enter to exit...")
    try:
        input()
    except:
        pass  # In case input fails too


if __name__ == "__main__":
    main()
