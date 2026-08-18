import tkinter as tk
from tkinter import messagebox
import os
import sys

# 导入三个实验模块
try:
    from FD_ELE_A1 import ElectromagnetismExperiment
except ImportError:
    print("无法导入 FD_ELE_A1，请确保文件存在")
    sys.exit(1)

try:
    from FD_ELE_A2 import HallExperiment
except ImportError:
    print("无法导入 FD_ELE_A2，请确保文件存在")
    sys.exit(1)

try:
    from FD_ELE_A3 import MagneticMaterialExperiment
except ImportError:
    print("无法导入 FD_ELE_A3，请确保文件存在")
    sys.exit(1)


class ExperimentManager:
    def __init__(self, root):
        self.root = root
        self.root.title("电磁学综合实验")
        self.root.geometry("1600x850")
        
        # 当前实验
        self.current_experiment = None
        
        # 实验实例
        self.solenoid_experiment = None
        self.hall_experiment = None
        self.magnetic_experiment = None
        
        # 创建顶部选项卡
        self.create_top_tab()
        
        # 创建内容框架
        self.content_frame = tk.Frame(self.root, bg='white')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 默认显示螺线管实验
        self.show_solenoid_experiment()
    
    def create_top_tab(self):
        """创建顶部选项卡"""
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
        """显示螺线管实验"""
        if self.current_experiment == "solenoid":
            return
        
        if self.hall_experiment is not None:
            self.hall_experiment.main_frame.pack_forget()
        if self.magnetic_experiment is not None:
            self.magnetic_experiment.main_frame.pack_forget()
        
        if self.solenoid_experiment is None:
            self.solenoid_experiment = ElectromagnetismExperiment(self.content_frame)
        else:
            self.solenoid_experiment.main_frame.pack(fill=tk.BOTH, expand=True)
            self.solenoid_experiment.on_show()
        
        self.btn_solenoid.config(bg='lightblue')
        self.btn_hall.config(bg='SystemButtonFace')
        self.btn_magnetic.config(bg='SystemButtonFace')
        self.current_experiment = "solenoid"

    def show_hall_experiment(self):
        """显示霍尔实验"""
        if self.current_experiment == "hall":
            return
        
        if self.solenoid_experiment is not None:
            self.solenoid_experiment.main_frame.pack_forget()
        if self.magnetic_experiment is not None:
            self.magnetic_experiment.main_frame.pack_forget()
        
        if self.hall_experiment is None:
            self.hall_experiment = HallExperiment(self.content_frame)
        else:
            self.hall_experiment.main_frame.pack(fill=tk.BOTH, expand=True)
            self.hall_experiment.on_show()
        
        self.btn_hall.config(bg='lightblue')
        self.btn_solenoid.config(bg='SystemButtonFace')
        self.btn_magnetic.config(bg='SystemButtonFace')
        self.current_experiment = "hall"

    def show_magnetic_experiment(self):
        """显示铁磁材料磁滞回线实验"""
        if self.current_experiment == "magnetic":
            return
        
        if self.solenoid_experiment is not None:
            self.solenoid_experiment.main_frame.pack_forget()
        if self.hall_experiment is not None:
            self.hall_experiment.main_frame.pack_forget()
        
        if self.magnetic_experiment is None:
            self.magnetic_experiment = MagneticMaterialExperiment(self.content_frame)
        else:
            self.magnetic_experiment.main_frame.pack(fill=tk.BOTH, expand=True)
            self.magnetic_experiment.on_show()
        
        self.btn_magnetic.config(bg='lightblue')
        self.btn_solenoid.config(bg='SystemButtonFace')
        self.btn_hall.config(bg='SystemButtonFace')
        self.current_experiment = "magnetic"


def main():
    root = tk.Tk()
    app = ExperimentManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()