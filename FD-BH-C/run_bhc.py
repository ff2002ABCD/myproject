#!/usr/bin/env python3
# run_bhc.py - launcher for the generated Ui_bhc.py
import sys
import random
from PyQt5 import QtWidgets
from Ui_bhc import Ui_MainWindow
import traceback
import os
import time

# Install a safe top-level excepthook to avoid recursive excepthook errors
_OLD_EXCEPTHOOK = sys.excepthook
def _safe_excepthook(exc_type, exc_value, exc_tb):
    try:
        # Ensure logs directory exists
        logdir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(logdir, exist_ok=True)
        path = os.path.join(logdir, f'error_{int(time.time())}.log')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('Unhandled exception:\\n')
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
        # Print a minimal message to stderr to avoid complex hooks
        try:
            sys.stderr.write(f"Unhandled exception recorded to {path}\n")
        except Exception:
            pass
    except Exception:
        pass
    # Try calling old excepthook in a guarded way
    try:
        if _OLD_EXCEPTHOOK and _OLD_EXCEPTHOOK is not sys.excepthook:
            _OLD_EXCEPTHOOK(exc_type, exc_value, exc_tb)
    except Exception:
        # swallow to avoid recursion
        pass

sys.excepthook = _safe_excepthook

class SimulationEngine:
    """简单的仿真引擎，管理设备状态"""
    def __init__(self):
        self.random_offset_mt = 0.0  # 启动时的随机磁场偏移 (±0.1 mT)

    def initialize_random_field_offset(self):
        """在软件启动时生成随机磁场偏移"""
        # 使用 ±5.0 mT 的随机浮动并保留一位小数（与 per-mm 偏置一致）
        val = random.uniform(-5.0, 5.0)
        # round to 0.1 mT
        self.random_offset_mt = float(round(val, 1))
        return self.random_offset_mt

    def get_random_offset(self):
        """获取当前的随机偏移值"""
        return self.random_offset_mt


def main():
    # 初始化仿真引擎
    sim_engine = SimulationEngine()
     
    # 生成启动时的随机磁场浮动
    random_offset = sim_engine.initialize_random_field_offset()

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)

    # 初始化物理模型为有随机剩磁的状态（程序启动时调用一次）
    try: 
        import physics_model as pm
        if hasattr(pm, 'initialize_models_with_remanence'):
            pm.initialize_models_with_remanence()
    except Exception:
        pass
    
    # 将随机磁场偏移注入物理模型（如果存在），否则回退到 UI 偏移
    try:                                    
        if hasattr(ui, 'model') and ui.model:
            ui.model.set_ambient_offset(random_offset) 
            ui.ambient_offset_mT = float(random_offset)
        else:
            ui.ambient_offset_mT = float(random_offset)
            
        # 同步旋钮到随机偏移值（旋钮范围 -50..50 对应 -5.0..+5.0 mT）
        knob_value = int(round(random_offset * 10))
        ui.Knob_Tesla.blockSignals(True)
        ui.Knob_Tesla.setValue(knob_value)
        ui.Knob_Tesla.blockSignals(False)
        
        ui.update_displays()
    except Exception:
        try:
            ui.apply_random_field_offset(random_offset)
        except Exception: 
            pass

    # 在主窗口菜单栏增加文件操作项（导入/导出/保存/加载会话）
    try:
        menubar = MainWindow.menuBar()
        file_menu = menubar.addMenu("文件")
        act_import = QtWidgets.QAction("导入 CSV", MainWindow)
        act_export = QtWidgets.QAction("导出 CSV", MainWindow)
        act_save = QtWidgets.QAction("保存会话", MainWindow)
        act_load = QtWidgets.QAction("加载会话", MainWindow)
        file_menu.addAction(act_import)
        file_menu.addAction(act_export)
        file_menu.addSeparator()
        # 退磁曲线导入导出
        act_import_degauss = QtWidgets.QAction("导入退磁曲线", MainWindow)
        act_export_degauss = QtWidgets.QAction("导出退磁曲线", MainWindow)
        file_menu.addAction(act_import_degauss)
        file_menu.addAction(act_export_degauss)
        file_menu.addSeparator()
        file_menu.addAction(act_save)
        file_menu.addAction(act_load)
        act_import.triggered.connect(ui.on_import_csv)
        act_export.triggered.connect(ui.on_export_csv)
        act_import_degauss.triggered.connect(ui.on_import_degauss_curve)
        act_export_degauss.triggered.connect(ui.on_export_degauss_curve)
        act_save.triggered.connect(ui.on_save_session)
        act_load.triggered.connect(ui.on_load_session)
    except Exception:
        pass

    # 显示启动信息，提示用户需要调零
    ui.statusbar.showMessage("启动完成，随机偏移: %.1f mT | 调零方法: 电流归0，探针移到±15mm，用右侧旋钮调至0" % random_offset)

    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":  
    main()



