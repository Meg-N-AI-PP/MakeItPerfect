# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec to build a portable single-file SentenceTool.exe."""

from pathlib import Path

project_root = Path(SPECPATH)
icon_path = project_root / "assets" / "icon.ico"

datas = [
    ("app/ui/styles.qss", "app/ui"),
    ("config/appsettings.json", "config"),
]
if icon_path.exists():
    datas.append(("assets/icon.ico", "assets"))

a = Analysis(
    ["app/main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["keyboard"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SentenceTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=str(icon_path) if icon_path.exists() else None,
)
