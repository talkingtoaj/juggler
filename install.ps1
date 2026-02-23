# Juggler — Installer / Uninstaller
# Run with: Right-click -> Run with PowerShell

$AppName      = "Juggler"
$ExeName      = "Juggler.exe"
$InstallDir   = "$env:LOCALAPPDATA\Programs\$AppName"
$StartupKey   = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$ShortcutPath = "$env:USERPROFILE\Desktop\Juggler.lnk"
$SourceExe    = Join-Path $PSScriptRoot $ExeName

function Install {
    # Check exe is present
    if (-not (Test-Path $SourceExe)) {
        Write-Host "ERROR: $ExeName not found next to install.ps1" -ForegroundColor Red
        Write-Host "Please download $ExeName from the release page and put it in the same folder as this script."
        Pause
        exit 1
    }

    Write-Host "Installing Juggler..." -ForegroundColor Cyan

    # Copy exe
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    Copy-Item $SourceExe "$InstallDir\$ExeName" -Force
    Write-Host "  Copied to $InstallDir" -ForegroundColor Green

    # Add to startup
    Set-ItemProperty -Path $StartupKey -Name $AppName -Value "$InstallDir\$ExeName"
    Write-Host "  Added to Windows startup" -ForegroundColor Green

    # Create desktop shortcut
    $Shell    = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath   = "$InstallDir\$ExeName"
    $Shortcut.IconLocation = "$InstallDir\$ExeName"
    $Shortcut.Description  = "Juggler — juggle your windows, not your attention"
    $Shortcut.Save()
    Write-Host "  Desktop shortcut created" -ForegroundColor Green

    Write-Host ""
    Write-Host "Done! Juggler will start automatically when you log in." -ForegroundColor Green
    Write-Host "Tip: press Ctrl+Alt+O from anywhere to cycle through your pinned windows."
    Write-Host ""
    $launch = Read-Host "Launch now? (y/n)"
    if ($launch -eq "y") {
        Start-Process "$InstallDir\$ExeName"
    }
}

function Uninstall {
    Write-Host "Uninstalling Juggler..." -ForegroundColor Cyan

    # Stop if running
    Stop-Process -Name $AppName -Force -ErrorAction SilentlyContinue

    # Remove startup entry
    Remove-ItemProperty -Path $StartupKey -Name $AppName -ErrorAction SilentlyContinue
    Write-Host "  Removed from startup" -ForegroundColor Green

    # Remove desktop shortcut
    Remove-Item $ShortcutPath -ErrorAction SilentlyContinue
    Write-Host "  Desktop shortcut removed" -ForegroundColor Green

    # Remove install dir
    Remove-Item $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  Removed $InstallDir" -ForegroundColor Green

    Write-Host ""
    Write-Host "Juggler has been uninstalled." -ForegroundColor Green
    Write-Host "(Your saved data in %USERPROFILE%\.juggler\ was not deleted.)"
}

# --- Main ---
Write-Host ""
Write-Host "  Juggler Setup" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "$InstallDir\$ExeName") {
    Write-Host "  An existing installation was found at $InstallDir"
    Write-Host ""
    Write-Host "  [1] Update / Reinstall"
    Write-Host "  [2] Uninstall"
    Write-Host "  [3] Cancel"
    Write-Host ""
    $choice = Read-Host "Choose (1/2/3)"
    switch ($choice) {
        "1" { Install }
        "2" { Uninstall }
        default { Write-Host "Cancelled." }
    }
} else {
    Install
}

Pause
