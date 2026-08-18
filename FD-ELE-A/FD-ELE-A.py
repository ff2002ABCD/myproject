import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
import sys
from PIL import Image, ImageTk

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ElectromagnetismExperiment:
    def __init__(self, root):
        self.root = root
        self.root.title("电磁学综合实验")
        self.root.geometry("1200x700")
        
        # 标记当前显示的是哪个界面
        self.current_display = None  # 初始为None
        
        # 初始化数据
        self.init_data()
        
        # 创建主框架
        self.create_main_layout()
        
        # 创建顶部选项卡
        self.create_top_tab()
        
        # 创建左侧实验装置区域
        self.create_left_area()
        
        # 创建右上实验操作区域
        self.create_right_top_area()
        
        # 创建右下数据记录区域
        self.create_right_bottom_area()
        
        # 初始化默认选择
        self.on_experiment_select()
        
    def init_data(self):
        """初始化数据"""
        # U-B关系表格数据
        self.ub_current_values = [""] * 9
        self.ub_voltage_values = [""] * 9
        
        # 位置-B关系表格数据（预留）
        self.position_data = [""] * 10
        
        # 灵敏度
        self.sensitivity = 0
        
        # 调零偏移量
        self.voltage_offset = 0  # 电压表调零偏移量 (mV)
        self.millitesla_offset = 0  # 毫特计调零偏移量 (mT)
        
        # 控件引用
        self.ub_current_entries = []
        self.ub_voltage_entries = []
        self.fig = None
        self.ax = None
        self.canvas_plot = None
        self.sensitivity_label = None
        
    def get_resource_path(self, relative_path):
        """获取资源的绝对路径，支持打包后的环境"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    
    def create_main_layout(self):
        """创建主布局"""
        # 顶部框架
        self.top_frame = tk.Frame(self.root, height=50, bg='lightgray')
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 主要内容框架
        main_content = tk.Frame(self.root)
        main_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧框架
        self.left_frame = tk.Frame(main_content, width=400, bg='white')
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        # 右侧框架
        right_frame = tk.Frame(main_content)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 右上框架
        self.right_top_frame = tk.Frame(right_frame, height=220, bg='lightyellow')
        self.right_top_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # 右下框架
        self.right_bottom_frame = tk.Frame(right_frame, bg='lightgreen')
        self.right_bottom_frame.pack(fill=tk.BOTH, expand=True)
        
    def create_top_tab(self):
        """创建顶部选项卡"""
        btn_solenoid = tk.Button(self.top_frame, text="螺线管磁场测量实验", 
                                 command=lambda: self.on_experiment_select(),
                                 width=20, height=1)
        btn_solenoid.pack(side=tk.LEFT, padx=10, pady=10)
        
        btn_hall = tk.Button(self.top_frame, text="用霍尔传感器测磁场",
                            command=lambda: self.on_hall_select(),
                            width=20, height=1)
        btn_hall.pack(side=tk.LEFT, padx=10, pady=10)
        
    def create_left_area(self):
        """创建左侧实验装置区域 - 叠加图片"""
        # 创建画布
        self.canvas = tk.Canvas(self.left_frame, width=680, height=700, bg='white')
        self.canvas.pack()
        
        # 加载并显示底图（螺线管.jpg）
        try:
            solenoid_img_path = self.get_resource_path("background/螺线管.jpg")
            pil_solenoid = Image.open(solenoid_img_path)
            pil_solenoid = pil_solenoid.resize((680, 700), Image.Resampling.LANCZOS)
            self.solenoid_image = ImageTk.PhotoImage(pil_solenoid)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.solenoid_image)
        except Exception as e:
            print(f"无法加载螺线管图片: {e}")
            # 创建灰色背景
            self.canvas.create_rectangle(0, 0, 680, 700, fill='lightgray')
            self.canvas.create_text(340, 350, text="螺线管图片加载失败", font=("Arial", 14))
        
        # 加载并叠加刻度图片
        try:
            scale_img_path = self.get_resource_path("background/刻度.jpg")
            pil_scale = Image.open(scale_img_path)
            # 可以调整刻度图片的大小和位置
            pil_scale = pil_scale.resize((700, 40), Image.Resampling.LANCZOS)
            self.scale_image = ImageTk.PhotoImage(pil_scale)
            # 叠加在螺线管图片上，设置透明度或直接叠加
            # 使用create_image叠加，设置合适的坐标
            self.canvas.create_image(566, 50, anchor=tk.NW, image=self.scale_image)
            print("刻度图片加载成功")
        except Exception as e:
            print(f"无法加载刻度图片: {e}")

        # 加载并叠加遮盖图片
        try:
            zhegai_img_path = self.get_resource_path("background/遮盖.png")
            zhegai_scale = Image.open(zhegai_img_path)
            # 可以调整刻度图片的大小和位置
            zhegai_scale = zhegai_scale.resize((563, 87), Image.Resampling.LANCZOS)
            self.zhegai_image = ImageTk.PhotoImage(zhegai_scale)
            # 叠加在螺线管图片上，设置透明度或直接叠加
            # 使用create_image叠加，设置合适的坐标
            self.canvas.create_image(0, 26, anchor=tk.NW, image=self.zhegai_image)
            print("遮盖图片加载成功")
        except Exception as e:
            print(f"无法加载遮盖图片: {e}")
        
        # 创建文本框叠加在图片上
        self.create_textboxes_on_image()
    
    def create_textboxes_on_image(self):
        """在图片上创建文本框"""
        # 电压表文本框 - 显示实际电压（包含调零）
        self.voltage_var = tk.StringVar(value="0")
        voltage_entry = tk.Entry(self.left_frame, textvariable=self.voltage_var, 
                                 width=8, font=("Arial", 10), justify='center')
        self.canvas.create_window(85, 535, window=voltage_entry, anchor=tk.NW)
        
        # 电流表文本框
        self.current_var = tk.StringVar(value="0")
        current_entry = tk.Entry(self.left_frame, textvariable=self.current_var,
                                 width=8, font=("Arial", 10), justify='center')
        self.canvas.create_window(265, 535, window=current_entry, anchor=tk.NW)
        
        # 毫特计文本框 - 显示实际磁感应强度（包含调零）
        self.millitesla_var = tk.StringVar(value="0")
        millitesla_entry = tk.Entry(self.left_frame, textvariable=self.millitesla_var,
                                    width=8, font=("Arial", 10), justify='center')
        self.canvas.create_window(410, 535, window=millitesla_entry, anchor=tk.NW)
    
    def create_right_top_area(self):
        """创建右上实验操作区域 - 两行两列布局"""
        # 创建主框架，使用网格布局
        main_frame = tk.Frame(self.right_top_frame, bg='lightyellow')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 第1行第1列：螺线管位置进度条
        position_frame = tk.Frame(main_frame, bg='lightyellow')
        position_frame.grid(row=0, column=0, padx=10, pady=10, sticky='w')
        tk.Label(position_frame, text="螺线管位置(cm):", bg='lightyellow', 
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.position_scale = tk.Scale(position_frame, from_=0, to=30, orient=tk.HORIZONTAL,
                                    length=250, resolution=0.1, command=self.update_position)
        self.position_scale.pack(side=tk.LEFT, padx=5)
        self.position_label = tk.Label(position_frame, text="0.0", width=6, 
                                    bg='white', relief=tk.SUNKEN)
        self.position_label.pack(side=tk.LEFT, padx=5)
        
        # 第1行第2列：励磁电流进度条
        current_frame = tk.Frame(main_frame, bg='lightyellow')
        current_frame.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        tk.Label(current_frame, text="励磁电流(mA):", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.current_scale = tk.Scale(current_frame, from_=0, to=500, orient=tk.HORIZONTAL,
                                    length=250, command=self.update_current)
        self.current_scale.pack(side=tk.LEFT, padx=5)
        self.current_value_label = tk.Label(current_frame, text="0", width=6,
                                        bg='white', relief=tk.SUNKEN)
        self.current_value_label.pack(side=tk.LEFT, padx=5)
        
        # 第2行第1列：电压表调零进度条
        voltage_offset_frame = tk.Frame(main_frame, bg='lightyellow')
        voltage_offset_frame.grid(row=1, column=0, padx=10, pady=10, sticky='w')
        tk.Label(voltage_offset_frame, text="电压表调零(mV):", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.voltage_offset_scale = tk.Scale(voltage_offset_frame, from_=-50, to=50, orient=tk.HORIZONTAL,
                                            length=250, resolution=1, command=self.update_voltage_offset)
        self.voltage_offset_scale.pack(side=tk.LEFT, padx=5)
        self.voltage_offset_label = tk.Label(voltage_offset_frame, text="0", width=6,
                                            bg='white', relief=tk.SUNKEN)
        self.voltage_offset_label.pack(side=tk.LEFT, padx=5)
        
        # 第2行第2列：毫特计调零进度条
        millitesla_offset_frame = tk.Frame(main_frame, bg='lightyellow')
        millitesla_offset_frame.grid(row=1, column=1, padx=10, pady=10, sticky='w')
        tk.Label(millitesla_offset_frame, text="毫特计调零(mT):", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.millitesla_offset_scale = tk.Scale(millitesla_offset_frame, from_=-50, to=50, orient=tk.HORIZONTAL,
                                                length=250, resolution=1, command=self.update_millitesla_offset)
        self.millitesla_offset_scale.pack(side=tk.LEFT, padx=5)
        self.millitesla_offset_label = tk.Label(millitesla_offset_frame, text="0", width=6,
                                                bg='white', relief=tk.SUNKEN)
        self.millitesla_offset_label.pack(side=tk.LEFT, padx=5)
    
        # 配置列权重，使布局更均匀
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
    
    def create_right_bottom_area(self):
        """创建右下数据记录区域"""
        # 内部选项卡
        self.data_tab_frame = tk.Frame(self.right_bottom_frame)
        self.data_tab_frame.pack(fill=tk.X, padx=5, pady=5)
        
        btn_ub = tk.Button(self.data_tab_frame, text="霍尔传感器电压U与磁感应强度B的关系",
                          command=self.show_ub_relation)
        btn_ub.pack(side=tk.LEFT, padx=5)
        
        btn_position = tk.Button(self.data_tab_frame, text="螺线管内磁感应强度与位置刻度的关系",
                                command=self.show_position_relation)
        btn_position.pack(side=tk.LEFT, padx=5)
        
        # 内容框架
        self.bottom_content_frame = tk.Frame(self.right_bottom_frame, bg='white')
        self.bottom_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 初始显示U-B关系界面
        self.show_ub_relation()
    
    def show_ub_relation(self):
        """显示U-B关系界面 - 保留数据"""
        # 如果是第一次创建或者需要切换，才重建界面
        if self.current_display == "ub_relation" and hasattr(self, 'bottom_content_frame') and self.bottom_content_frame.winfo_children():
            return  # 已经是这个界面且有内容，不需要切换
        
        # 如果当前显示的是其他界面，先保存数据
        if self.current_display == "position_relation":
            self.save_position_data()
        
        # 清空内容
        for widget in self.bottom_content_frame.winfo_children():
            widget.destroy()
        
        # 创建表格
        table_frame = tk.Frame(self.bottom_content_frame)
        table_frame.pack(pady=10)
        
        # 表头
        headers = ["", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        for col, header in enumerate(headers):
            label = tk.Label(table_frame, text=header, relief=tk.RIDGE, 
                           width=8, bg='lightgray')
            label.grid(row=0, column=col, padx=1, pady=1)
        
        # Im/mA行
        tk.Label(table_frame, text="Im/mA", relief=tk.RIDGE, 
                width=8, bg='lightgray').grid(row=1, column=0, padx=1, pady=1)
        
        self.ub_current_entries = []
        for col in range(1, 10):
            entry = tk.Entry(table_frame, width=8, justify='center')
            entry.grid(row=1, column=col, padx=1, pady=1)
            # 恢复保存的数据
            if self.ub_current_values[col-1]:
                entry.insert(0, self.ub_current_values[col-1])
            self.ub_current_entries.append(entry)
        
        # U/mV行
        tk.Label(table_frame, text="U/mV", relief=tk.RIDGE, 
                width=8, bg='lightgray').grid(row=2, column=0, padx=1, pady=1)
        
        self.ub_voltage_entries = []
        for col in range(1, 10):
            entry = tk.Entry(table_frame, width=8, justify='center')
            entry.grid(row=2, column=col, padx=1, pady=1)
            # 恢复保存的数据
            if self.ub_voltage_values[col-1]:
                entry.insert(0, self.ub_voltage_values[col-1])
            self.ub_voltage_entries.append(entry)
        
        # 曲线图
        self.create_plot()
        
        # 灵敏度显示
        sensitivity_frame = tk.Frame(self.bottom_content_frame)
        sensitivity_frame.pack(pady=5)
        tk.Label(sensitivity_frame, text="霍尔传感器灵敏度:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.sensitivity_label = tk.Label(sensitivity_frame, text=f"{self.sensitivity:.4f}" if self.sensitivity != 0 else "0.00", 
                                         font=("Arial", 10, "bold"), fg='red')
        self.sensitivity_label.pack(side=tk.LEFT, padx=5)
        tk.Label(sensitivity_frame, text="mV/mA", font=("Arial", 10)).pack(side=tk.LEFT)
        
        # 按钮框架
        button_frame = tk.Frame(self.bottom_content_frame)
        button_frame.pack(pady=10)
        
        buttons = [
            ("计算", self.calculate),
            ("清空数据", self.clear_ub_data),
            ("导出数据", self.export_ub_data),
            ("导入数据", self.import_ub_data)
        ]
        
        for text, command in buttons:
            btn = tk.Button(button_frame, text=text, command=command, 
                          width=12, bg='lightblue')
            btn.pack(side=tk.LEFT, padx=5)
        
        self.current_display = "ub_relation"
        
        # 更新曲线图
        self.update_plot()
    
    def create_plot(self):
        """创建曲线图"""
        plot_frame = tk.Frame(self.bottom_content_frame)
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=0)
        
        self.fig, self.ax = plt.subplots(figsize=(4, 2))
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.ax.set_xlabel('Im (mA)')
        self.ax.set_ylabel('U (mV)')
        self.ax.set_title('霍尔传感器电压U与电流Im的关系')
        self.ax.grid(True)
    
    def update_plot(self):
        """更新曲线图"""
        if not hasattr(self, 'ax') or self.ax is None:
            return
        
        self.ax.clear()
        
        # 获取有效数据
        currents = []
        voltages = []
        if hasattr(self, 'ub_current_entries') and self.ub_current_entries:
            for i in range(9):
                try:
                    if self.ub_current_entries[i].get().strip():
                        current = float(self.ub_current_entries[i].get())
                        voltage = float(self.ub_voltage_entries[i].get())
                        currents.append(current)
                        voltages.append(voltage)
                except (ValueError, IndexError):
                    continue
        
        if currents and voltages:
            # 绘制散点图
            self.ax.scatter(currents, voltages, color='blue', s=50, label='实验数据')
            
            # 线性拟合
            if len(currents) >= 2:
                coeffs = np.polyfit(currents, voltages, 1)
                self.sensitivity = coeffs[0]
                if hasattr(self, 'sensitivity_label') and self.sensitivity_label:
                    self.sensitivity_label.config(text=f"{self.sensitivity:.4f}")
                
                # 绘制拟合直线
                x_line = np.array([min(currents), max(currents)])
                y_line = coeffs[0] * x_line + coeffs[1]
                self.ax.plot(x_line, y_line, 'r-', label=f'拟合直线: y={coeffs[0]:.4f}x+{coeffs[1]:.4f}')
                
                # 显示公式
                formula_text = f'拟合公式: U = {coeffs[0]:.4f} * Im + {coeffs[1]:.4f}'
                self.ax.text(0.05, 0.95, formula_text, transform=self.ax.transAxes,
                           fontsize=10, verticalalignment='top',
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            else:
                if hasattr(self, 'sensitivity_label') and self.sensitivity_label:
                    self.sensitivity_label.config(text="0.00")
                self.sensitivity = 0
        else:
            if hasattr(self, 'sensitivity_label') and self.sensitivity_label:
                self.sensitivity_label.config(text="0.00")
        
        self.ax.set_xlabel('Im (mA)')
        self.ax.set_ylabel('U (mV)')
        self.ax.set_title('霍尔传感器电压U与电流Im的关系')
        self.ax.grid(True)
        if currents and voltages:
            self.ax.legend()
        
        if hasattr(self, 'canvas_plot') and self.canvas_plot:
            self.canvas_plot.draw()
    
    def save_ub_data(self):
        """保存U-B数据"""
        if hasattr(self, 'ub_current_entries') and self.ub_current_entries:
            for i in range(9):
                self.ub_current_values[i] = self.ub_current_entries[i].get()
                self.ub_voltage_values[i] = self.ub_voltage_entries[i].get()
    
    def save_position_data(self):
        """保存位置数据（预留）"""
        pass
    
    def show_position_relation(self):
        """显示位置-B关系界面"""
        if self.current_display == "position_relation":
            return
        
        # 保存U-B数据
        self.save_ub_data()
        
        # 清空内容
        for widget in self.bottom_content_frame.winfo_children():
            widget.destroy()
        
        # 创建位置关系界面
        label = tk.Label(self.bottom_content_frame, text="螺线管内磁感应强度与位置刻度的关系\n功能待开发",
                        font=("Arial", 14), bg='white')
        label.pack(expand=True)
        
        self.current_display = "position_relation"
    
    def calculate(self):
        """计算拟合直线"""
        self.update_plot()
        messagebox.showinfo("计算完成", "拟合直线计算完成！")
    
    def clear_ub_data(self):
        """清空U-B数据"""
        if hasattr(self, 'ub_current_entries') and self.ub_current_entries:
            for entry in self.ub_current_entries:
                entry.delete(0, tk.END)
                entry.insert(0, "")
            for entry in self.ub_voltage_entries:
                entry.delete(0, tk.END)
                entry.insert(0, "")
        
        # 清空存储的数据
        self.ub_current_values = [""] * 9
        self.ub_voltage_values = [""] * 9
        self.sensitivity = 0
        
        if hasattr(self, 'sensitivity_label') and self.sensitivity_label:
            self.sensitivity_label.config(text="0.00")
        
        self.update_plot()
        messagebox.showinfo("清空数据", "数据已清空！")
    
    def export_ub_data(self):
        """导出U-B数据"""
        if not hasattr(self, 'ub_current_entries') or not self.ub_current_entries:
            messagebox.showwarning("警告", "没有可导出的数据！")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("Im(mA)\tU(mV)\n")
                    for i in range(9):
                        current = self.ub_current_entries[i].get().strip()
                        voltage = self.ub_voltage_entries[i].get().strip()
                        if current and voltage:
                            f.write(f"{current}\t{voltage}\n")
                messagebox.showinfo("导出成功", f"数据已导出到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出数据时出错:\n{str(e)}")
    
    def import_ub_data(self):
        """导入U-B数据"""
        if not hasattr(self, 'ub_current_entries') or not self.ub_current_entries:
            messagebox.showwarning("警告", "请先切换到U-B关系界面！")
            return
            
        file_path = filedialog.askopenfilename(
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 跳过表头
                data_lines = [line for line in lines[1:] if line.strip()]
                
                for i, line in enumerate(data_lines[:9]):
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        self.ub_current_entries[i].delete(0, tk.END)
                        self.ub_current_entries[i].insert(0, parts[0])
                        self.ub_voltage_entries[i].delete(0, tk.END)
                        self.ub_voltage_entries[i].insert(0, parts[1])
                        # 同时保存到数据数组
                        self.ub_current_values[i] = parts[0]
                        self.ub_voltage_values[i] = parts[1]
                
                self.update_plot()
                messagebox.showinfo("导入成功", "数据导入完成！")
            except Exception as e:
                messagebox.showerror("导入失败", f"导入数据时出错:\n{str(e)}")
    
    def update_position(self, value):
        """更新位置显示"""
        self.position_label.config(text=f"{float(value):.1f}")
        # 这里可以根据位置和电流计算理论磁场值
        self.update_magnetic_field()
    
    def update_current(self, value):
        """更新电流显示"""
        current_ma = int(float(value))
        self.current_value_label.config(text=str(current_ma))
        self.current_var.set(str(current_ma / 1000))  # 转换为A显示
        # 这里可以根据位置和电流计算理论磁场值
        self.update_magnetic_field()
    
    def update_voltage_offset(self, value):
        """更新电压表调零"""
        self.voltage_offset = int(float(value))
        self.voltage_offset_label.config(text=str(self.voltage_offset))
        # 更新电压表显示（考虑调零）
        self.update_voltage_display()
    
    def update_millitesla_offset(self, value):
        """更新毫特计调零"""
        self.millitesla_offset = int(float(value))
        self.millitesla_offset_label.config(text=str(self.millitesla_offset))
        # 更新毫特计显示（考虑调零）
        self.update_millitesla_display()
    
    def update_voltage_display(self):
        """更新电压表显示 - 这里可以根据实际测量值加上调零偏移"""
        # 示例：假设测量电压为 current_voltage，实际显示需要加上调零偏移
        # 这里先用0作为演示，实际使用时需要接入真实的测量数据
        measured_voltage = 0  # 这里应该是实际测量的电压值
        displayed_voltage = measured_voltage + self.voltage_offset
        self.voltage_var.set(f"{displayed_voltage:.1f}")
    
    def update_millitesla_display(self):
        """更新毫特计显示 - 这里可以根据实际测量值加上调零偏移"""
        # 示例：假设测量磁感应强度为 measured_b，实际显示需要加上调零偏移
        measured_b = 0  # 这里应该是实际测量的磁感应强度值
        displayed_b = measured_b + self.millitesla_offset
        self.millitesla_var.set(f"{displayed_b:.1f}")
    
    def update_magnetic_field(self):
        """根据位置和电流计算理论磁场值并更新显示"""
        # 修改这里：Label用cget获取文本，或者直接用之前保存的值
        position = float(self.position_label.cget('text'))  # 方法1：用cget
        # 或者方法2：直接用 self.position_label['text']
        # position = float(self.position_label['text'])
        
        current_a = float(self.current_var.get())
        
        # 示例参数（需要根据实际实验调整）
        n = 1000  # 单位长度匝数 (匝/m)
        mu0 = 4 * np.pi * 1e-7  # 真空磁导率
        
        # 简单计算中心磁场
        theoretical_b = mu0 * n * current_a * 1000  # 转换为mT
    
    def on_experiment_select(self):
        """螺线管实验选择"""
        self.position_scale.config(state='normal')
        self.current_scale.config(state='normal')
        self.voltage_offset_scale.config(state='normal')
        self.millitesla_offset_scale.config(state='normal')
    
    def on_hall_select(self):
        """霍尔实验选择"""
        messagebox.showinfo("提示", "用霍尔传感器测磁场实验功能待开发")

def main():
    root = tk.Tk()
    app = ElectromagnetismExperiment(root)
    root.mainloop()

if __name__ == "__main__":
    main()