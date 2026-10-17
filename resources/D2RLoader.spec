# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Qt resolves OpenSSL via exe dir -> System32 -> PATH, so a System32 copy shadows
# the bundled one and mixes versions (see #29). Use the Schannel TLS backend instead.
QT_OPENSSL_BINARIES = {'qopensslbackend.dll', 'libssl-3-x64.dll', 'libcrypto-3-x64.dll'}


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
a.binaries = [
    entry for entry in a.binaries
    if os.path.basename(entry[0]).lower() not in QT_OPENSSL_BINARIES
]
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
