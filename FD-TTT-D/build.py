"""
温度传感器特性测量实验 - 打包程序
使用 PyInstaller 打包成单个可执行文件
"""

import os
import sys
import shutil
import subprocess

# 切换到脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f"工作目录: {os.getcwd()}")

# 项目信息
APP_NAME = "温度传感器特性测量实验"
MAIN_SCRIPT = "FD-TTT-D.py"

# 需要排除的库（减小exe体积）
EXCLUDES = [
    'torch', 'torchvision', 'tensorflow', 'tensorflow_core',
    'keras', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
    'Django', 'flask', 'tornado', 'aiohttp',
    'boto3', 'botocore', 'opencv', 'cv2',
    'pygame', 'scikit-learn', 'sklearn',
    'cryptography', 'paramiko', 'selenium',
    'beautifulsoup4', 'lxml',
    'numpy.distutils',
    'pytest', 'pip',
    'IPython', 'jupyter', 'notebook',
    'pandas',
]

# 隐藏导入（确保这些库被正确打包）
HIDDEN_IMPORTS = [
    'jaraco.classes', 'jaraco.text', 'jaraco.functools',
    'pkg_resources', 'pkg_resources.extern', 'pkg_resources.extern.jaraco',
    'PIL._imagingtk', 'PIL.ImageTk',
    'matplotlib.backends.backend_tkagg',
    'scipy.special', 'scipy.stats',
    'openpyxl.cell', 'openpyxl.styles', 'openpyxl.utils',
    'numpy.core._methods', 'numpy.lib.format',
]

def check_files():
    """检查必要文件是否存在"""
    if not os.path.exists(MAIN_SCRIPT):
        print(f"错误: 找不到 {MAIN_SCRIPT} 文件")
        print(f"当前目录: {os.getcwd()}")
        print("请确保 build.py 和 FD-TTT-D.py 在同一目录下")
        return False
    
    if not os.path.exists("background"):
        print("警告: 找不到 background 文件夹")
        print("请确保 background 文件夹存在，包含背景图片")
    
    return True

def clean_build():
    """清理之前的构建文件"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理 {dir_name}...")
            shutil.rmtree(dir_name)
    
    # 清理 .spec 文件
    spec_file = "FD-TTT-D.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"清理 {spec_file}...")

def build_exe():
    """执行打包"""
    print("\n开始打包程序...\n")
    
    # 构建 PyInstaller 命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--add-data=background;background',
        f'--name={APP_NAME}',
        '--clean',
        '--noconfirm',
        '--optimize=2',
    ]
    
    # 添加隐藏导入
    for imp in HIDDEN_IMPORTS:
        cmd.extend(['--hidden-import', imp])
    
    # 添加排除参数
    for pkg in EXCLUDES:
        cmd.extend(['--exclude', pkg])
    
    # 如果存在图标文件
    if os.path.exists('icon.ico'):
        cmd.extend(['--icon', 'icon.ico'])
    
    # 主脚本
    cmd.append(MAIN_SCRIPT)
    
    print("执行命令:")
    print(" ".join(cmd[:10]) + " ...\n")
    
    # 执行打包
    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 50)
        print("打包完成！")
        print("=" * 50)
        
        exe_path = f"dist/{APP_NAME}.exe"
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"文件大小: {size:.2f} MB")
            print(f"可执行文件: {os.path.abspath(exe_path)}")
        else:
            print("警告: 未找到生成的可执行文件")
            
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("  温度传感器特性测量实验 - 打包工具")
    print("=" * 50)
    print(f"\n工作目录: {os.getcwd()}")
    print(f"将排除 {len(EXCLUDES)} 个库以减小文件体积")
    print()
    
    # 检查文件
    if not check_files():
        input("\n按 Enter 键退出...")
        sys.exit(1)
    
    # 清理旧文件
    clean_build()
    
    # 执行打包
    success = build_exe()
    
    if success:
        print("\n提示: 打包后的程序位于 dist 文件夹中")
        print(f"运行: dist/{APP_NAME}.exe")
    
    input("\n按 Enter 键退出...")