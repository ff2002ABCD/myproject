"""
build_quick.py - 快速打包脚本
"""

import os
import PyInstaller.__main__

def quick_build():
    """快速打包"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(current_dir, "FD-EFL-C.py")
    bg_dir = os.path.join(current_dir, 'background')
    
    if not os.path.exists(bg_dir):
        print("警告: background 目录不存在！")
        print("请确保以下文件存在:")
        print("  - background/导电玻璃1.jpg")
        print("  - background/导电玻璃2.jpg")
        print("  - background/主机.jpg")
    
    dist_path = os.path.join(current_dir, 'dist')
    work_path = os.path.join(current_dir, 'build')
    
    args = [
        main_script,
        '--name=静电场描绘实验',
        '--windowed',
        '--onefile',    
        '--noconfirm',
        '--clean',
        f'--add-data={bg_dir};background',
        f'--distpath={dist_path}',
        f'--workpath={work_path}',
        '--noconsole',
    ]
    
    PyInstaller.__main__.run(args)
    print(f"\n打包完成！文件位于: {os.path.join(dist_path, '静电场描绘实验.exe')}")

if __name__ == "__main__":
    quick_build()