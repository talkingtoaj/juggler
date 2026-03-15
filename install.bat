@echo off
REM Juggler - Installer / Uninstaller
REM Double-click to run. Downloads Juggler.exe automatically if not present.

set APP=Juggler
set EXE=Juggler.exe
set INSTALL_DIR=%LOCALAPPDATA%\Programs\Juggler
REM SHORTCUT resolved at runtime via PowerShell to handle OneDrive Desktop redirection
set STARTUP_KEY=HKCU\Software\Microsoft\Windows\CurrentVersion\Run
set DOWNLOAD_URL=https://github.com/talkingtoaj/juggler/releases/latest/download/Juggler.exe

echo.
echo   Juggler Setup
echo.

REM --- Check for existing install ---
if exist "%INSTALL_DIR%\%EXE%" (
    echo   An existing installation was found at %INSTALL_DIR%
    echo.
    echo   [1] Update / Reinstall
    echo   [2] Uninstall
    echo   [3] Cancel
    echo.
    set /p CHOICE="  Choose (1/2/3): "
    if "%CHOICE%"=="1" goto :install
    if "%CHOICE%"=="2" goto :uninstall
    goto :cancel
) else (
    goto :install
)

:install
REM --- Download exe if not next to this script ---
if not exist "%~dp0%EXE%" (
    echo   Juggler.exe not found locally - downloading from latest release...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;" ^
      "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%~dp0%EXE%' -UseBasicParsing"
    if errorlevel 1 (
        echo   Invoke-WebRequest failed, trying curl.exe...
        curl.exe -fL -o "%~dp0%EXE%" "%DOWNLOAD_URL%"
    )
    if not exist "%~dp0%EXE%" (
        echo.
        echo ERROR: Download failed. Please download %EXE% from:
        echo   https://github.com/talkingtoaj/juggler/releases/latest
        echo and place it in the same folder as this script, then run again.
        pause
        exit /b 1
    )
    echo   Download complete.
)

echo   Installing %APP%...

REM --- Copy exe ---
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy /Y "%~dp0%EXE%" "%INSTALL_DIR%\%EXE%" >nul
echo   Copied to %INSTALL_DIR%

REM --- Add to startup ---
reg add "%STARTUP_KEY%" /v "%APP%" /t REG_SZ /d "\"%INSTALL_DIR%\%EXE%\"" /f >nul
echo   Added to Windows startup

REM --- Create desktop shortcut (resolve Desktop via shell to handle OneDrive redirection) ---
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$desk = [Environment]::GetFolderPath('Desktop');" ^
  "$s = (New-Object -ComObject WScript.Shell).CreateShortcut(\"$desk\Juggler.lnk\");" ^
  "$s.TargetPath = '%INSTALL_DIR%\%EXE%';" ^
  "$s.IconLocation = '%INSTALL_DIR%\%EXE%';" ^
  "$s.Description = 'Juggler - juggle your windows, not your attention';" ^
  "$s.Save()"
if errorlevel 1 (
    echo   WARNING: Desktop shortcut could not be created.
) else (
    echo   Desktop shortcut created
)

echo.
echo   Done! Juggler will start automatically when you log in.
echo   Tip: press Ctrl+Alt+O from anywhere to cycle through your pinned windows.
echo.
set /p LAUNCH="  Launch now? (y/n): "
if /i "%LAUNCH%"=="y" start "" "%INSTALL_DIR%\%EXE%"
goto :end

:uninstall
echo   Uninstalling %APP%...
taskkill /IM "%EXE%" /F >nul 2>&1
reg delete "%STARTUP_KEY%" /v "%APP%" /f >nul 2>&1
echo   Removed from startup
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$desk = [Environment]::GetFolderPath('Desktop');" ^
  "$lnk = \"$desk\Juggler.lnk\";" ^
  "if (Test-Path $lnk) { Remove-Item $lnk -Force }"
echo   Desktop shortcut removed
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"
echo   Removed %INSTALL_DIR%
echo.
echo   Juggler has been uninstalled.
echo   (Your saved data in %%USERPROFILE%%\.juggler\ was not deleted.)
goto :end

:cancel
echo   Cancelled.

:end
echo.
pause
