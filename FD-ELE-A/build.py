# build.py
"""
修复版打包脚本 - 解决 pandas 缺失和 input 错误
"""

import os
import sys
import shutil
import PyInstaller.__main__

# ==================== 自动切换到脚本所在目录 ====================
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f"📂 工作目录: {os.getcwd()}")

# ==================== 配置 ====================
APP_NAME = "FD-ELE-A"
MAIN_SCRIPT = "FD_ELE_A_Main.py"  # 如果文件名不同，请修改这里
OUTPUT_DIR = "dist"
BUILD_DIR = "build"

PYTHON_FILES = [
    "FD_ELE_A_Main.py",
    "FD_ELE_A1.py",
    "FD_ELE_A2.py",
    "FD_ELE_A3.py",
]

DATA_FOLDERS = [
    "data",
    "background",
]

# ==================== 清理 ====================
def clean_build():
    """清理旧的构建文件"""
    print("🧹 清理旧的构建文件...")
    for dir_name in [OUTPUT_DIR, BUILD_DIR]:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"  已删除: {dir_name}")
            except:
                pass
    for file in os.listdir("."):
        if file.endswith(".spec"):
            try:
                os.remove(file)
                print(f"  已删除: {file}")
            except:
                pass
    print("✅ 清理完成\n")

# ==================== 检查 FD_ELE_A3.py 的导入 ====================
def check_a3_imports():
    """检查 FD_ELE_A3.py 中使用了哪些库"""
    if not os.path.exists("FD_ELE_A3.py"):
        print("⚠️  FD_ELE_A3.py 不存在")
        return []
    
    with open("FD_ELE_A3.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 import 语句
    imports = []
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('import ') or line.startswith('from '):
            if line.startswith('import '):
                mod = line.replace('import ', '').split()[0]
                imports.append(mod)
            elif line.startswith('from '):
                mod = line.replace('from ', '').split()[0]
                if mod not in imports:
                    imports.append(mod)
    
    return imports

# ==================== 创建入口文件 ====================
def create_entry_file():
    """创建入口文件 - 无 input() 调用"""
    entry_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电磁学综合实验 - 入口文件
"""

import os
import sys
import tkinter as tk
import traceback

# 获取资源路径
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# 添加当前目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# 显示错误信息（GUI方式）
def show_error(message):
    try:
        root = tk.Tk()
        root.withdraw()
        tk.messagebox.showerror("启动错误", message)
        root.destroy()
    except:
        pass

try:
    from FD_ELE_A1 import ElectromagnetismExperiment
    from FD_ELE_A2 import HallExperiment
    from FD_ELE_A3 import MagneticMaterialExperiment
except ImportError as e:
    error_msg = f"导入模块失败: {e}\\n\\n请确保所有文件都在同一目录下"
    show_error(error_msg)
    sys.exit(1)

class ExperimentManager:
    def __init__(self, root):
        self.root = root
        self.root.title("电磁学综合实验")
        self.root.geometry("1600x800")
        
        self.current_experiment = None
        self.solenoid_experiment = None
        self.hall_experiment = None
        self.magnetic_experiment = None
        
        self.create_top_tab()
        self.content_frame = tk.Frame(self.root, bg='white')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.show_solenoid_experiment()
    
    def create_top_tab(self):
        self.top_frame = tk.Frame(self.root, height=50, bg='lightgray')
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        btn_solenoid = tk.Button(self.top_frame, text="螺线管磁场测量实验",
                                command=self.show_solenoid_experiment,
                                width=20, height=1, bg='lightblue')
        btn_solenoid.pack(side=tk.LEFT, padx=10, pady=10)
        self.btn_solenoid = btn_solenoid
        
        btn_hall = tk.Button(self.top_frame, text="用霍尔传感器测磁场",
                           command=self.show_hall_experiment,
                           width=20, height=1)
        btn_hall.pack(side=tk.LEFT, padx=10, pady=10)
        self.btn_hall = btn_hall
        
        btn_magnetic = tk.Button(self.top_frame, text="铁磁材料磁滞回线",
                                command=self.show_magnetic_experiment,
                                width=20, height=1)
        btn_magnetic.pack(side=tk.LEFT, padx=10, pady=10)
        self.btn_magnetic = btn_magnetic
    
    def show_solenoid_experiment(self):
        if self.current_experiment == "solenoid":
            return
        try:
            if self.hall_experiment is not None:
                self.hall_experiment.main_frame.pack_forget()
            if self.magnetic_experiment is not None:
                self.magnetic_experiment.main_frame.pack_forget()
        except:
            pass
        
        if self.solenoid_experiment is None:
            self.solenoid_experiment = ElectromagnetismExperiment(self.content_frame)
        else:
            try:
                self.solenoid_experiment.main_frame.pack(fill=tk.BOTH, expand=True)
                self.solenoid_experiment.on_show()
            except:
                self.solenoid_experiment = ElectromagnetismExperiment(self.content_frame)
        
        self.btn_solenoid.config(bg='lightblue')
        self.btn_hall.config(bg='SystemButtonFace')
        self.btn_magnetic.config(bg='SystemButtonFace')
        self.current_experiment = "solenoid"

    def show_hall_experiment(self):
        if self.current_experiment == "hall":
            return
        try:
            if self.solenoid_experiment is not None:
                self.solenoid_experiment.main_frame.pack_forget()
            if self.magnetic_experiment is not None:
                self.magnetic_experiment.main_frame.pack_forget()
        except:
            pass
        
        if self.hall_experiment is None:
            self.hall_experiment = HallExperiment(self.content_frame)
        else:
            try:
                self.hall_experiment.main_frame.pack(fill=tk.BOTH, expand=True)
                self.hall_experiment.on_show()
            except:
                self.hall_experiment = HallExperiment(self.content_frame)
        
        self.btn_hall.config(bg='lightblue')
        self.btn_solenoid.config(bg='SystemButtonFace')
        self.btn_magnetic.config(bg='SystemButtonFace')
        self.current_experiment = "hall"

    def show_magnetic_experiment(self):
        if self.current_experiment == "magnetic":
            return
        try:
            if self.solenoid_experiment is not None:
                self.solenoid_experiment.main_frame.pack_forget()
            if self.hall_experiment is not None:
                self.hall_experiment.main_frame.pack_forget()
        except:
            pass
        
        if self.magnetic_experiment is None:
            self.magnetic_experiment = MagneticMaterialExperiment(self.content_frame)
        else:
            try:
                self.magnetic_experiment.main_frame.pack(fill=tk.BOTH, expand=True)
                self.magnetic_experiment.on_show()
            except:
                self.magnetic_experiment = MagneticMaterialExperiment(self.content_frame)
        
        self.btn_magnetic.config(bg='lightblue')
        self.btn_solenoid.config(bg='SystemButtonFace')
        self.btn_hall.config(bg='SystemButtonFace')
        self.current_experiment = "magnetic"

def main():
    try:
        root = tk.Tk()
        app = ExperimentManager(root)
        root.mainloop()
    except Exception as e:
        error_msg = f"程序启动失败: {e}\\n\\n{traceback.format_exc()}"
        try:
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showerror("启动错误", error_msg)
            root.destroy()
        except:
            print(error_msg)

if __name__ == "__main__":
    main()
'''
    
    entry_file = "__entry__.py"
    with open(entry_file, 'w', encoding='utf-8') as f:
        f.write(entry_content)
    
    print(f"✅ 创建入口文件: {entry_file}")
    return entry_file

# ==================== 创建 spec 文件 ====================
def create_spec_file(entry_file):
    """创建 spec 文件 - 包含 pandas"""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{entry_file}'],
    pathex=[],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('background', 'background'),
    ],
    hiddenimports=[
        'PIL', 'PIL.Image', 'PIL.ImageTk',
        'PIL.ImageDraw', 'PIL.ImageFont',
        'matplotlib', 'matplotlib.backends',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_agg',
        'matplotlib.backends._backend_tk',
        'matplotlib.font_manager',
        'matplotlib.ft2font',
        'numpy', 'numpy.core', 'numpy.lib',
        'numpy.random', 'numpy.linalg',
        'openpyxl', 'openpyxl.cell',
        'openpyxl.reader.excel', 'openpyxl.workbook',
        'openpyxl.writer.excel', 'openpyxl.styles',
        'openpyxl.utils', 'openpyxl.formatting',
        'openpyxl.chart',
        'pytz',
        'tkinter', 'tkinter.ttk',
        'tkinter.filedialog', 'tkinter.messagebox',
        'tkinter.simpledialog',
        'cycler', 'kiwisolver', 'dateutil',
        'pyparsing', 'packaging',
        'packaging.version', 'packaging.specifiers',
        'packaging.requirements',
        'random', 'time', 'datetime',
        # pandas 相关（FD_ELE_A3.py 需要）
        'pandas', 'pandas.core', 'pandas.io',
        'pandas.core.frame', 'pandas.core.series',
        'pandas.core.indexes', 'pandas.core.dtypes',
        'pandas.core.groupby', 'pandas.core.reshape',
        'pandas.core.window', 'pandas.core.strings',
        'pandas.core.arrays', 'pandas.core.sorting',
        'pandas.core.missing', 'pandas.core.common',
        'pandas._libs', 'pandas._libs.algos',
        'pandas._libs.indexing', 'pandas._libs.internals',
        'pandas._libs.lib', 'pandas._libs.ops',
        'pandas._libs.properties', 'pandas._libs.tslib',
        'pandas._libs.tslibs', 'pandas._libs.tslibs.nattype',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.timestamps',
        'pandas._libs.tslibs.timezones',
        'pandas._libs.tslibs.offsets',
        'pandas._libs.tslibs.parsing',
        'pandas._libs.tslibs.fields',
        'pandas._libs.tslibs.conversion',
        'pandas._libs.tslibs.period',
        'pandas._libs.tslibs.vectorized',
        'pandas._libs.tslibs.c_tz',
        'pandas._libs.tslibs.dtypes',
        # pandas 依赖
        'dateutil', 'pytz', 'numpy',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchvision', 'tensorflow',
        'keras', 'PyQt5', 'PyQt6', 'PySide2',
        'PySide6', 'Django', 'flask', 'tornado',
        'aiohttp', 'boto3', 'botocore', 
        'opencv', 'cv2', 'pygame', 
        'scikit-learn', 'sklearn',
        'cryptography', 'paramiko', 'selenium',
        'beautifulsoup4', 'lxml',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyd = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyd,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    spec_file = f"{APP_NAME}.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✅ 创建 spec 文件: {spec_file}")
    return spec_file

# ==================== 打包 ====================
def build_exe():
    """执行打包"""
    print("\n🔍 检查文件...")
    
    missing = []
    for file in PYTHON_FILES:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"❌ 缺少: {', '.join(missing)}")
        return False
    
    print("✅ 所有 Python 文件存在")
    
    # 检查 FD_ELE_A3.py 的导入
    imports = check_a3_imports()
    if imports:
        print(f"\n📋 FD_ELE_A3.py 导入的模块: {', '.join(imports[:10])}")
    
    # 检查 pandas 是否安装
    try:
        import pandas
        print(f"✅ pandas 版本: {pandas.__version__}")
    except ImportError:
        print("⚠️  pandas 未安装！正在安装...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pandas"], check=True)
    
    for folder in DATA_FOLDERS:
        if os.path.exists(folder):
            files = len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
            print(f"  ✅ {folder}: {files} 个文件")
        else:
            print(f"  ⚠️  {folder} 不存在")
    
    entry_file = create_entry_file()
    spec_file = create_spec_file(entry_file)
    
    print("\n🔨 开始打包...")
    print("⏳ 请耐心等待 5-10 分钟...\n")
    
    args = [
        spec_file,
        "--noconfirm",
        "--clean",
        "--distpath", OUTPUT_DIR,
        "--workpath", BUILD_DIR,
    ]
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✅ 打包成功！")
        return True
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        return False

# ==================== 调试版本 ====================
def build_debug():
    """构建调试版本"""
    print("\n🔨 构建调试版本...")
    
    # 检查 pandas
    try:
        import pandas
        print(f"✅ pandas 版本: {pandas.__version__}")
    except ImportError:
        print("⚠️  pandas 未安装！")
        return False
    
    args = [
        MAIN_SCRIPT,
        "--name", f"{APP_NAME}_debug",
        "--onefile",
        "--console",
        "--noconfirm",
        "--clean",
        "--distpath", OUTPUT_DIR,
        "--workpath", BUILD_DIR,
        "--add-data", f"data{os.pathsep}data",
        "--add-data", f"background{os.pathsep}background",
        "--exclude-module", "torch",
        "--exclude-module", "tensorflow",
        "--exclude-module", "PyQt5",
        "--exclude-module", "scipy",
        "--exclude-module", "sklearn",
        "--exclude-module", "cryptography",
        # pandas 需要保留
        "--hidden-import", "pandas",
        "--hidden-import", "pandas.core",
        "--hidden-import", "pandas.io",
        "--hidden-import", "pandas._libs",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageTk",
        "--hidden-import", "matplotlib.backends.backend_tkagg",
        "--hidden-import", "numpy",
        "--hidden-import", "openpyxl",
        "--hidden-import", "pytz",
        "--collect-data", "matplotlib",
        "--collect-data", "PIL",
        "--collect-data", "pandas",
    ]
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✅ 调试版本打包成功！")
        return True
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        return False

# ==================== 主函数 ====================
def main():
    print("=" * 70)
    print("  电磁学综合实验 - 打包工具")
    print("=" * 70)
    print(f"📂 工作目录: {os.getcwd()}\n")
    
    if not os.path.exists(MAIN_SCRIPT):
        print(f"❌ 主程序不存在: {MAIN_SCRIPT}")
        print(f"📁 当前目录下的 .py 文件:")
        for f in os.listdir("."):
            if f.endswith(".py"):
                print(f"   - {f}")
        sys.exit(1)
    
    print("选择打包模式:")
    print("  1. 正式打包 (无控制台)")
    print("  2. 调试打包 (带控制台)")
    print("  3. 清理并退出")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "3":
        clean_build()
        return
    
    response = input("是否清理旧的构建文件？(y/n): ").strip().lower()
    if response in ['y', 'yes']:
        clean_build()
    
    if choice == "1":
        success = build_exe()
    elif choice == "2":
        success = build_debug()
    else:
        print("❌ 无效选择")
        return
    
    if success:
        exe_name = f"{APP_NAME}.exe" if choice == "1" else f"{APP_NAME}_debug.exe"
        exe_path = os.path.join(OUTPUT_DIR, exe_name)
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n📊 文件大小: {size:.2f} MB")
        print("\n🎉 打包完成！")
    else:
        print("\n❌ 打包失败")

if __name__ == "__main__":
    main()