# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['FD-TTT-D.py'],
    pathex=[],
    binaries=[],
    datas=[('background', 'background')],
    hiddenimports=['jaraco.classes', 'jaraco.text', 'jaraco.functools', 'pkg_resources', 'pkg_resources.extern', 'pkg_resources.extern.jaraco', 'PIL._imagingtk', 'PIL.ImageTk', 'matplotlib.backends.backend_tkagg', 'scipy.special', 'scipy.stats', 'openpyxl.cell', 'openpyxl.styles', 'openpyxl.utils', 'numpy.core._methods', 'numpy.lib.format'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'tensorflow', 'tensorflow_core', 'keras', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'Django', 'flask', 'tornado', 'aiohttp', 'boto3', 'botocore', 'opencv', 'cv2', 'pygame', 'scikit-learn', 'sklearn', 'cryptography', 'paramiko', 'selenium', 'beautifulsoup4', 'lxml', 'numpy.distutils', 'pytest', 'pip', 'IPython', 'jupyter', 'notebook', 'pandas'],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    name='温度传感器特性测量实验',
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
