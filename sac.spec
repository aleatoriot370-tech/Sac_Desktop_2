# -*- mode: python ; coding: utf-8 -*-
"""
Spec file para empacotamento com PyInstaller.

Como usar:
    pyinstaller sac.spec

O executável será gerado em dist/SAC_Grupo_Lamoia/
"""
import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    [str(root / 'app.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / 'frontend' / 'templates'), 'frontend/templates'),
        (str(root / 'frontend' / 'static'), 'frontend/static'),
        (str(root / 'assets'), 'assets'),
    ],
    hiddenimports=['engineio.async_drivers.threading'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SAC_Grupo_Lamoia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Sem console (app desktop)
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SAC_Grupo_Lamoia',
)
