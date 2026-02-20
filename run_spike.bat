@echo off
echo Context Switcher - Run Spike
echo ==============================
echo.
echo This must be run on native Windows (not WSL).
echo.

REM Check if we're on Windows
if "%OS%"=="Windows_NT" goto windows
echo ERROR: This script is for Windows only.
echo Please run from Windows Command Prompt or PowerShell.
exit /b 1

:windows
echo ✓ Running on Windows

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+
    exit /b 1
)

echo ✓ Python found

REM Check for uv
uv --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv not found. Installing via powershell...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
)

echo ✓ uv found

REM Navigate to project directory
cd /d "%~dp0"

REM Install dependencies with Windows extras
echo.
echo Installing dependencies (including pywin32)...
uv sync --extra windows

REM Run the spike
echo.
echo ===========================================
echo Running spike script...
echo Make sure you have VS Code, Chrome, or Terminal windows open!
echo ===========================================
echo.
echo If the window closes immediately, check these files:
echo   - spike_log.txt (full log with timestamps)
echo   - spike_results.json (summary results)
echo.
uv run python spike_window_api.py

REM If we get here, the script finished
if exist "spike_log.txt" (
    echo.
    echo ===========================================
    echo Spike completed. Check spike_log.txt for details.
    echo ===========================================
)

pause
