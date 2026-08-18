#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本 - 将FD-BH-C项目打包成exe
运行方式: python build_exe.py
"""
import subprocess
import sys
import os

def main():
    # 确保在项目目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print("PyInstaller已安装")
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # PyInstaller命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=FD-BH-C",
        "--onefile",           # 打包成单个exe
        "--windowed",          # 无控制台窗口
        "--icon=NONE",         # 无图标（可以后续添加.ico文件）
        "--clean",             # 清理之前的构建
        # 添加数据文件
        f"--add-data=1.jpg;.",  # 添加背景图片
        f"--add-data=calibration.json;.",  # 添加校准数据
        f"--add-data=physics_model_config.json;.",  # 添加配置文件
        f"--add-data=hysteresis_data.csv;.",  # 添加磁滞数据
        # 添加Python模块文件
        f"--add-data=Ui_bhc.py;.",
        f"--add-data=physics_model.py;.",
        f"--add-data=plot_widget.py;.",
        f"--add-data=data_manager.py;.",
        f"--add-data=ui_additions.py;.",
        f"--add-data=experiment_controller.py;.",
        # 隐藏导入
        "--hidden-import=PyQt5",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=numpy",
        "--hidden-import=pyqtgraph",
        "--hidden-import=pyqtgraph.graphicsItems",
        "--hidden-import=pyqtgraph.graphicsItems.PlotItem",
        "--hidden-import=pyqtgraph.graphicsItems.ViewBox",
        "--hidden-import=pyqtgraph.graphicsItems.PlotCurveItem",
        "--hidden-import=scipy",
        "--hidden-import=scipy.optimize",
        "--hidden-import=Ui_bhc",
        "--hidden-import=physics_model",
        "--hidden-import=plot_widget",
        "--hidden-import=data_manager",
        "--hidden-import=ui_additions",
        "--hidden-import=experiment_controller",
        "--collect-all=pyqtgraph",  # 收集pyqtgraph所有文件
        "run_bhc.py"           # 主入口文件
    ]
    
    print("开始打包...")
    print(" ".join(cmd))
    
    try:
        subprocess.check_call(cmd)
        print("\n打包完成！")
        print(f"exe文件位置: {os.path.join(project_dir, 'dist', 'FD-BH-C.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
