# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['FD-TC-D.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('background', 'background'),
        ('data', 'data'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 深度学习框架
        'torch',
        'torchvision',
        'tensorflow',
        'tensorboard',
        'keras',
        
        # 科学计算（不需要的）
        'scipy',
        'sympy',
        'numba',
        
        # 多媒体
        'pygame',
        'pygame._*',
        'PIL.ImageQt',
        
        # 数据处理（额外的）
        'pyarrow',
        'fastparquet',
        
        # 网络/AWS
        'botocore',
        'boto3',
        'cryptography',
        'requests',
        'urllib3',
        
        # 文档/解析
        'lxml',
        'html5lib',
        'bs4',
        'pygments',
        
        # Web框架
        'jupyter',
        'notebook',
        'IPython',
        'ipykernel',
        'nbconvert',
        
        # 测试相关
        'pytest',
        'unittest',
        'nose',
        
        # 库的测试文件
        'numpy.tests',
        'numpy._core.tests',
        'numpy.ma.tests',
        'numpy.typing.tests',
        'numpy.random._examples',
        'pandas.tests',
        'pandas._libs.testing',
        'pandas.io.formats.style',
        'pandas.plotting',
        'matplotlib.tests',
        'matplotlib._api.deprecation',
        'matplotlib.testing',
        
        # 其他
        'setuptools',
        'distutils',
        'pip',
        'wheel',
        'pkg_resources',
        'pywin32',
        'win32com',
        'pythoncom',
        'pywintypes',
        'sqlite3',
        'tkinter.test',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FD-TC-D',
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
    icon=None
)