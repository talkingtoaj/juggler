# Build Juggler.exe using PyInstaller
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Building Juggler.exe..." -ForegroundColor Cyan

python -m PyInstaller `
    --onefile `
    --windowed `
    --name Juggler `
    --icon "$ScriptDir\icon.png" `
    --add-data "$ScriptDir\icon.png;." `
    --hidden-import win32api `
    --hidden-import win32gui `
    --hidden-import win32con `
    --hidden-import win32process `
    --hidden-import pywintypes `
    "$ScriptDir\main.py"

if ($LASTEXITCODE -eq 0) {
    Copy-Item "$ScriptDir\dist\Juggler.exe" "$ScriptDir\Juggler.exe" -Force
    Write-Host "Done: $ScriptDir\Juggler.exe" -ForegroundColor Green
} else {
    Write-Host "Build FAILED (exit $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}
