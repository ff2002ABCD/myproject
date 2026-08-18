# build.py
import os
import shutil
import subprocess


def get_script_dir():
    """获取脚本所在目录"""
    return os.path.dirname(os.path.abspath(__file__))


def clean_build():
    """清理之前的构建文件"""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除: {dir_name}")
    
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            os.remove(file)
            print(f"已删除: {file}")


def build_exe():
    """构建exe文件（排除大库）"""
    print("开始打包程序...")
    
    # 切换到脚本所在目录
    script_dir = get_script_dir()
    os.chdir(script_dir)
    
    clean_build()
    
    main_script = 'FD-DMO-A.py'
    
    if not os.path.exists(main_script):
        print(f"错误: 找不到主文件 {main_script}")
        print(f"当前目录: {os.getcwd()}")
        print("请确保 FD-DMO-A.py 和 build.py 在同一目录下")
        return
    
    # 排除的大库列表
    exclude_modules = [
        'torch', 'torchvision', 'tensorflow', 'tensorflow_core',
        'keras', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'Django', 'flask', 'tornado', 'aiohttp',
        'boto3', 'botocore', 'opencv', 'cv2',
        'pygame', 'scikit-learn', 'sklearn',
        'cryptography', 'paramiko', 'selenium',
        'beautifulsoup4', 'lxml',
        'pytest', 'pip', 'IPython', 'jupyter', 'notebook',
        'scipy', 'statsmodels', 'seaborn', 'plotly', 'bokeh',
        'dask', 'distributed', 'ray',
        'mxnet', 'caffe', 'caffe2', 'theano', 'chainer', 'cntk',
        'nltk', 'spacy', 'transformers',
        'pytorch', 'torchaudio', 'torchtext',
    ]
    
    # 构建排除参数
    exclude_args = []
    for mod in exclude_modules:
        exclude_args.append(f'--exclude-module={mod}')
    
    # 构建命令
    cmd = (
        'pyinstaller --onefile --windowed --name=光电效应实验系统 '
        '--add-data=background;background '
        '--hidden-import=matplotlib '
        '--hidden-import=matplotlib.backends.backend_tkagg '
        '--hidden-import=numpy '
        '--hidden-import=PIL '
        '--hidden-import=PIL._tkinter_finder '
        '--hidden-import=tkinter '
        '--hidden-import=tkinter.ttk '
        '--hidden-import=math '
        '--hidden-import=json '
        '--collect-all=matplotlib '
        '--collect-all=numpy '
        '--optimize=2 '
        f"{' '.join(exclude_args)} "
        f'{main_script}'
    )
    
    print("执行命令:", cmd)
    result = os.system(cmd)
    
    if result == 0:
        print("\n打包完成!")
        print(f"输出文件: dist/光电效应实验系统.exe")
        
        if os.path.exists('background'):
            dist_background = os.path.join('dist', 'background')
            if os.path.exists(dist_background):
                shutil.rmtree(dist_background)
            shutil.copytree('background', dist_background)
            print("已复制background文件夹到dist目录")
        
        exe_path = os.path.join('dist', '光电效应实验系统.exe')
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"文件大小: {size:.2f} MB")
    else:
        print("打包失败!")


def build_with_console():
    """构建带控制台的版本（排除大库）"""
    print("开始打包程序（带控制台版本）...")
    
    # 切换到脚本所在目录
    script_dir = get_script_dir()
    os.chdir(script_dir)
    
    clean_build()
    
    main_script = 'FD-DMO-A.py'
    
    if not os.path.exists(main_script):
        print(f"错误: 找不到主文件 {main_script}")
        print(f"当前目录: {os.getcwd()}")
        print("请确保 FD-DMO-A.py 和 build.py 在同一目录下")
        return
    
    # 排除的大库列表
    exclude_modules = [
        'torch', 'torchvision', 'tensorflow', 'tensorflow_core',
        'keras', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'Django', 'flask', 'tornado', 'aiohttp',
        'boto3', 'botocore', 'opencv', 'cv2',
        'pygame', 'scikit-learn', 'sklearn',
        'cryptography', 'paramiko', 'selenium',
        'beautifulsoup4', 'lxml',
        'pytest', 'pip', 'IPython', 'jupyter', 'notebook',
        'scipy', 'statsmodels', 'seaborn', 'plotly', 'bokeh',
        'dask', 'distributed', 'ray',
        'mxnet', 'caffe', 'caffe2', 'theano', 'chainer', 'cntk',
        'nltk', 'spacy', 'transformers',
        'pytorch', 'torchaudio', 'torchtext',
    ]
    
    exclude_args = []
    for mod in exclude_modules:
        exclude_args.append(f'--exclude-module={mod}')
    
    cmd = (
        'pyinstaller --onefile --name=光电效应实验系统_调试 '
        '--add-data=background;background '
        '--hidden-import=matplotlib '
        '--hidden-import=matplotlib.backends.backend_tkagg '
        '--hidden-import=numpy '
        '--hidden-import=PIL '
        '--hidden-import=PIL._tkinter_finder '
        '--collect-all=matplotlib '
        '--collect-all=numpy '
        '--optimize=2 '
        f"{' '.join(exclude_args)} "
        f'{main_script}'
    )
    
    result = os.system(cmd)
    
    if result == 0:
        print("\n打包完成（带控制台）!")
        print(f"输出文件: dist/光电效应实验系统_调试.exe")
        
        if os.path.exists('background'):
            dist_background = os.path.join('dist', 'background')
            if os.path.exists(dist_background):
                shutil.rmtree(dist_background)
            shutil.copytree('background', dist_background)
            print("已复制background文件夹到dist目录")
    else:
        print("打包失败!")


def main():
    print("=" * 50)
    print("  光电效应实验系统 - 打包工具")
    print("=" * 50)
    print("说明: 已排除torch、tensorflow、keras、PyQt、scipy等大库")
    print("      以减小exe体积")
    print("-" * 50)
    print("请选择打包方式:")
    print("1. 标准打包 (无控制台窗口，推荐)")
    print("2. 调试打包 (带控制台窗口)")
    print("3. 清理构建文件")
    print("4. 退出")
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    if choice == '1':
        build_exe()
    elif choice == '2':
        build_with_console()
    elif choice == '3':
        # 切换到脚本所在目录
        os.chdir(get_script_dir())
        clean_build()
        print("清理完成!")
    elif choice == '4':
        print("退出")
    else:
        print("无效选项")


if __name__ == "__main__":
    main()