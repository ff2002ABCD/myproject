# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('1.jpg', '.'), ('calibration.json', '.'), ('physics_model_config.json', '.'), ('hysteresis_data.csv', '.'), ('Ui_bhc.py', '.'), ('physics_model.py', '.'), ('plot_widget.py', '.'), ('data_manager.py', '.'), ('ui_additions.py', '.'), ('experiment_controller.py', '.')]
binaries = []
hiddenimports = ['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'numpy', 'pyqtgraph', 'pyqtgraph.graphicsItems', 'pyqtgraph.graphicsItems.PlotItem', 'pyqtgraph.graphicsItems.ViewBox', 'pyqtgraph.graphicsItems.PlotCurveItem', 'scipy', 'scipy.optimize', 'Ui_bhc', 'physics_model', 'plot_widget', 'data_manager', 'ui_additions', 'experiment_controller']
tmp_ret = collect_all('pyqtgraph')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


block_cipher = None


a = Analysis(
    ['run_bhc.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FD-BH-C',
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
    icon='NONE',
)
