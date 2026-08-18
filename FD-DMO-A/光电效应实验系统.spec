# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('background', 'background')]
binaries = []
hiddenimports = ['matplotlib', 'matplotlib.backends.backend_tkagg', 'numpy', 'PIL', 'PIL._tkinter_finder', 'tkinter', 'tkinter.ttk', 'math', 'json']
tmp_ret = collect_all('matplotlib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('numpy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['FD-DMO-A.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'tensorflow', 'tensorflow_core', 'keras', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'Django', 'flask', 'tornado', 'aiohttp', 'boto3', 'botocore', 'opencv', 'cv2', 'pygame', 'scikit-learn', 'sklearn', 'cryptography', 'paramiko', 'selenium', 'beautifulsoup4', 'lxml', 'pytest', 'pip', 'IPython', 'jupyter', 'notebook', 'scipy', 'statsmodels', 'seaborn', 'plotly', 'bokeh', 'dask', 'distributed', 'ray', 'mxnet', 'caffe', 'caffe2', 'theano', 'chainer', 'cntk', 'nltk', 'spacy', 'transformers', 'pytorch', 'torchaudio', 'torchtext'],
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
    name='光电效应实验系统',
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
