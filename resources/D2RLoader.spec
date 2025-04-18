# -*- mode: python ; coding: utf-8 -*-
import sys


a = Analysis(
    ['..\\d2rloader\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('.\\icons\\d2rloader.ico', '.')],
    hiddenimports=[*list(sys.stdlib_module_names)],
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
    [],
    exclude_binaries=True,
    name='D2RLoader',
    icon='.\\icons\\d2rloader.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='D2RLoader',
)
