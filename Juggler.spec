# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['\\\\wsl.localhost\\Ubuntu-24.04\\home\\talkingtoaj\\repos\\context-switcher\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('\\\\wsl.localhost\\Ubuntu-24.04\\home\\talkingtoaj\\repos\\context-switcher\\icon.png', '.')],
    hiddenimports=['win32api', 'win32gui', 'win32con', 'win32process', 'pywintypes'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Juggler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['\\\\wsl.localhost\\Ubuntu-24.04\\home\\talkingtoaj\\repos\\context-switcher\\icon.png'],
)
