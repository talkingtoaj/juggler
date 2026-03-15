# Juggler - Installer / Uninstaller
# Single-click: right-click -> Run with PowerShell
# If Juggler.exe is not next to this script it is downloaded from the latest release.

$AppName      = "Juggler"
$ExeName      = "Juggler.exe"
$InstallDir   = "$env:LOCALAPPDATA\Programs\$AppName"
$StartupKey   = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$ShortcutPath = "$env:USERPROFILE\Desktop\Juggler.lnk"
$SourceExe    = Join-Path $PSScriptRoot $ExeName
$ReleaseApi   = "https://api.github.com/repos/talkingtoaj/juggler/releases/latest"

function Get-LatestExe {
    Write-Host "  Juggler.exe not found locally - downloading from latest release..." -ForegroundColor Cyan
    try {
        $release  = Invoke-RestMethod -Uri $ReleaseApi -UseBasicParsing
        $asset    = $release.assets | Where-Object { $_.name -eq $ExeName } | Select-Object -First 1
        if (-not $asset) { throw "No $ExeName asset found in the latest release." }
        $dest = Join-Path $PSScriptRoot $ExeName
        Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $dest -UseBasicParsing
        Write-Host "  Downloaded $ExeName ($([math]::Round($asset.size/1MB,1)) MB)" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Could not download $ExeName - $_" -ForegroundColor Red
        Write-Host "Please download $ExeName from https://github.com/talkingtoaj/juggler/releases/latest"
        Write-Host "and place it in the same folder as this script, then run again."
        Pause
        exit 1
    }
}

function Install {
    if (-not (Test-Path $SourceExe)) {
        Get-LatestExe
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
    $Shortcut.Description  = "Juggler - juggle your windows, not your attention"
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
