#!/usr/bin/env python
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
    error_msg = f"导入模块失败: {e}\n\n请确保所有文件都在同一目录下"
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
        error_msg = f"程序启动失败: {e}\n\n{traceback.format_exc()}"
        try:
            root = tk.Tk()
            root.withdraw()
            tk.messagebox.showerror("启动错误", error_msg)
            root.destroy()
        except:
            print(error_msg)

if __name__ == "__main__":
    main()
