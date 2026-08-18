# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['FD-IM-E.py'],
    pathex=[],
    binaries=[],
    datas=[('background', 'background')],
    hiddenimports=['openpyxl', 'pandas', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'tensorflow', 'scipy', 'matplotlib', 'PyQt5', 'boto3', 'botocore', 'Django', 'flask', 'opencv-python', 'pygame'],
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
    name='FD-IM-E',
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
)
