#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FD-MGS-A 光谱分析系统 - 自动打包脚本
适用于 Python 3.8.9
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

def print_section(title):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def check_python_version():
    """检查Python版本"""
    print("[1/7] 检查Python版本...")
    version = sys.version_info
    print(f"[+] 当前Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor != 8:
        print(f"[!] 警告：推荐使用Python 3.8.9，当前版本为 {version.major}.{version.minor}.{version.micro}")
        response = input("是否继续？(Y/n): ")
        if response.lower() == 'n':
            sys.exit(0)
    else:
        print("[+] Python版本符合要求")

def check_module(module_name, package_name=None):
    """检查模块是否已安装"""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def install_dependencies():
    """安装依赖包"""
    print("\n[2/7] 检查并安装依赖包...")
    
    required_modules = {
        'PyQt5': 'PyQt5',
        'serial': 'pyserial',
        'matplotlib': 'matplotlib',
        'numpy': 'numpy',
        'PyInstaller': 'pyinstaller'
    }
    
    missing = []
    for module, package in required_modules.items():
        if check_module(module):
            print(f"[+] {package} 已安装")
        else:
            print(f"[-] {package} 未安装")
            missing.append(package)
    
    if missing:
        print(f"\n需要安装以下包: {', '.join(missing)}")
        print("正在安装...")
        
        # 使用清华镜像源加速
        pip_cmd = [
            sys.executable, '-m', 'pip', 'install',
            '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'
        ] + missing
        
        result = subprocess.run(pip_cmd)
        if result.returncode != 0:
            print("[X] 依赖安装失败！")
            sys.exit(1)
        print("[+] 所有依赖已安装")
    else:
        print("[+] 所有依赖已满足")

def clean_build_dirs():
    """清理旧的构建目录"""
    print("\n[3/7] 清理旧的构建文件...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  删除 {dir_name}/")
            shutil.rmtree(dir_path)
    
    print("[+] 清理完成")

def check_required_files():
    """检查必需的文件是否存在"""
    print("\n[4/7] 检查必需文件...")
    
    required_files = [
        'FD_MGS_A_Main.py',
        'FD-MGS-A.ui',
        'Ui_FD_MGS_A.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print(f"[+] {file}")
        else:
            print(f"[-] {file} - 缺失！")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n[X] 错误：缺少必需文件: {', '.join(missing_files)}")
        sys.exit(1)
    
    print("[+] 所有必需文件存在")

def generate_spec_with_dlls():
    """生成包含所有DLL的spec文件"""
    print("\n[4.5/7] 生成包含DLL的spec文件...")
    
    # 检查dll_for_pack目录
    dll_dir = Path('dll_for_pack')
    if not dll_dir.exists():
        print("[!] 警告：dll_for_pack 目录不存在，将使用空的binaries列表")
        dll_files = []
    else:
        dll_files = sorted(dll_dir.glob('*.dll'))
        print(f"[+] 找到 {len(dll_files)} 个DLL文件")
    
    # 生成binaries列表
    if dll_files:
        binaries_list = [f"        ('dll_for_pack/{dll.name}', '.')," for dll in dll_files]
        binaries_str = '\n'.join(binaries_list)
    else:
        binaries_str = "        # 未找到DLL文件"
    
    # 生成spec文件内容
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# 自动生成的spec文件 - 包含所有DLL依赖
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

block_cipher = None

a = Analysis(
    ['FD_MGS_A_Main.py'],
    pathex=[],
    binaries=[
{binaries_str}
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
        'importlib_resources.trees',  # 补充缺失的隐藏导入，避免运行时找不到
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
    print(f"[+] 已生成 {spec_file} (包含 {len(dll_files)} 个DLL)")

def build_exe():
    """使用PyInstaller打包"""
    print("\n[5/7] 开始打包...")
    print("这可能需要几分钟时间，请耐心等待...\n")
    print("-" * 60)
    
    # 运行PyInstaller
    cmd = [sys.executable, '-m', 'PyInstaller', '--clean', 'FD_MGS_A.spec']
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\n" + "-" * 60)
        print("[X] 打包失败！")
        print("\n可能的原因：")
        print("1. PyInstaller版本不兼容")
        print("2. 依赖包版本冲突")
        print("3. 系统内存不足")
        print("4. 杀毒软件拦截")
        print("\n建议：")
        print("1. 尝试升级PyInstaller: pip install --upgrade pyinstaller")
        print("2. 临时关闭杀毒软件")
        print("3. 检查上面的错误信息")
        sys.exit(1)
    
    print("-" * 60)
    print("[+] 打包完成")

def verify_output():
    """验证输出文件"""
    print("\n[6/7] 验证生成的文件...")
    
    exe_path = Path('dist/FD-MGS-A.exe')
    if not exe_path.exists():
        print("[X] 错误：未找到生成的EXE文件")
        print("请检查build目录中的日志文件")
        sys.exit(1)
    
    # 获取文件大小
    size_bytes = exe_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    
    print(f"[+] EXE文件已生成")
    print(f"  位置: {exe_path.absolute()}")
    print(f"  大小: {size_mb:.2f} MB ({size_bytes:,} 字节)")

def copy_additional_files():
    """复制额外的文件到dist目录"""
    print("\n[7/7] 复制额外文件...")
    
    dist_dir = Path('dist')
    files_to_copy = [
        'README.md',
        '问题修复总结.txt',
        '数据采集问题修复说明.md',
    ]
    
    for file in files_to_copy:
        src = Path(file)
        if src.exists():
            dst = dist_dir / file
            shutil.copy2(src, dst)
            print(f"[+] 复制 {file}")
        else:
            print(f"[!] 跳过 {file} (不存在)")
    
    print("[+] 文件复制完成")

def create_version_info():
    """创建版本信息文件"""
    print("\n创建版本信息文件...")
    
    version_info = f"""FD-MGS-A 光谱分析系统
版本：v2.1
打包日期：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Python版本：{sys.version.split()[0]}

功能特性：
[+] 3648像素光谱数据采集
[+] 实时光谱图显示和缩放功能
[+] 光谱标定功能（支持6种标准峰）
[+] 积分时间设置（15种选项）
[+] 数据保存/加载和标定导出/导入
[+] 连续/单次采集模式
[+] 拖拽缩放和自动Y轴缩放

使用说明：
1. 直接双击 FD-MGS-A.exe 运行程序
2. 无需安装Python或任何依赖
3. 首次运行可能需要几秒钟加载

注意事项：
- 需要串口权限
- 建议关闭杀毒软件的实时监控（首次运行时）
- Windows Defender可能会扫描exe文件，这是正常现象

支持系统：
- Windows 7 及以上版本
- 64位操作系统
"""
    
    version_file = Path('dist/版本说明.txt')
    version_file.write_text(version_info, encoding='utf-8')
    print(f"[+] 已创建 {version_file}")

def main():
    """主函数"""
    print_section("FD-MGS-A 光谱分析系统 - 自动打包工具")
    
    try:
        # 确保在正确的目录
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        print(f"工作目录: {os.getcwd()}\n")
        
        # 执行打包步骤
        check_python_version()
        install_dependencies()
        clean_build_dirs()
        check_required_files()
        generate_spec_with_dlls()
        build_exe()
        verify_output()
        copy_additional_files()
        create_version_info()
        
        # 打包成功
        print_section("[+] 打包成功完成！")
        
        print("生成的文件：")
        print(f"  [目录] {Path('dist').absolute()}")
        print(f"  [文件] FD-MGS-A.exe")
        print(f"  [文件] README.md")
        print(f"  [文件] 版本说明.txt")
        print()
        
        print("接下来的步骤：")
        print("1. 测试运行 dist/FD-MGS-A.exe")
        print("2. 将整个dist文件夹复制到目标电脑")
        print("3. 目标电脑无需安装Python")
        print()
        
        # 询问是否测试运行（非交互模式下跳过）
        try:
            response = input("是否立即测试运行程序？(Y/n): ")
            if response.lower() != 'n':
                print("\n启动程序...")
                exe_path = Path('dist/FD-MGS-A.exe')
                if sys.platform == 'win32':
                    os.startfile(exe_path)
                else:
                    subprocess.Popen([exe_path])
        except (EOFError, KeyboardInterrupt):
            # 非交互模式或用户取消，跳过测试运行
            pass
        
        print("\n打包完成！")
        try:
            input("按回车键退出...")
        except (EOFError, KeyboardInterrupt):
            pass
        
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n[X] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n按回车键退出...")
        input()
        sys.exit(1)

if __name__ == "__main__":
    main()

