#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成包含所有DLL的PyInstaller spec文件
"""

import os
from pathlib import Path

def generate_spec_file():
    """生成包含所有DLL的spec文件"""
    
    # 获取dll_for_pack目录中的所有DLL文件
    dll_dir = Path('dll_for_pack')
    if not dll_dir.exists():
        print("错误：dll_for_pack 目录不存在！")
        return False
    
    dll_files = sorted(dll_dir.glob('*.dll'))
    
    if not dll_files:
        print("警告：dll_for_pack 目录中没有找到DLL文件！")
        binaries_list = []
    else:
        print(f"找到 {len(dll_files)} 个DLL文件")
        # 生成binaries列表
        binaries_list = [f"('dll_for_pack/{dll.name}', '.')" for dll in dll_files]
    
    # 生成spec文件内容
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# 自动生成的spec文件 - 包含所有DLL依赖

block_cipher = None

a = Analysis(
    ['FD_MGS_A_Main.py'],
    pathex=[],
    binaries=[
        # 包含所有Windows API DLL文件
{chr(10).join('        ' + dll for dll in binaries_list)},
    ],
    datas=[
        ('FD-MGS-A.ui', '.'),
        ('Ui_FD_MGS_A.py', '.'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.uic',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.figure',
        'matplotlib.pyplot',
        'numpy',
        'serial',
        'serial.tools.list_ports',
    ],
    hookspath=[],
    hooksconfig={{}},
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
    name='FD-MGS-A',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""
    
    # 写入spec文件
    spec_file = Path('FD_MGS_A.spec')
    spec_file.write_text(spec_content, encoding='utf-8')
    
    print(f"✓ 已生成 {spec_file}")
    print(f"✓ 包含 {len(dll_files)} 个DLL文件")
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("生成包含所有DLL的PyInstaller spec文件")
    print("=" * 60)
    
    if generate_spec_file():
        print("\n✓ 完成！")
    else:
        print("\n✗ 失败！")
        exit(1)












