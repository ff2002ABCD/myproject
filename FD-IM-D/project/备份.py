import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk
import os
import sys
import time
import random
import math
from tkinter import messagebox, filedialog

import pandas as pd  # 用于Excel操作
import numpy as np   # 用于数值计算

def get_resource_path(relative_path):
    """获取资源的绝对路径，支持打包后的环境"""
    try:
        # 打包后的临时文件夹路径
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

class ExperimentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("实验系统")
        self.root.geometry("1569x800")
        self.root.resizable(False, False)
        # 当前界面状态
        self.current_interface = "平衡法"  # 平衡法/动态法/参数设置

        self.selected_index = 0  # 当前选中项的索引
        
        # 计时相关变量
        self.is_timing = False  # 是否正在计时
        self.start_time = 0  # 开始时间
        self.timer_id = None  # 定时器ID
        self.elapsed_time = 0.0  # 经过的时间（秒）
    
        # 电压控制参数
        self.lift_voltage = tk.IntVar(value=250)  # 提升电压，初始250V
        self.balance_voltage_slider = tk.IntVar(value=250)  # 平衡电压滑块，初始250V
        
        # 油滴相关变量
        self.oil_droplets = []  # 存储油滴对象
        self.is_oil_simulating = False  # 是否正在模拟油滴运动
        self.oil_timer_id = None  # 油滴模拟定时器ID
        self.focus_scale = tk.DoubleVar(value=2.0)  # 对焦进度条，控制油滴大小 (1-3倍)
        
        # 物理常数
        self.electron_charge = 1.602e-19  # 电子电荷 (C)
        self.plate_distance = 5.00e-3  # 极板间距 (m)
        self.oil_density = 981  # 油滴密度 (kg/m³)
        self.gravity = 9.7940  # 重力加速度 (m/s²)
        
        # 数据存储
        self.balance_params = {
            "平衡电压": "0.0",
            "下落时间": "0.0",
        }
        
        self.dynamic_params = {
            "平衡电压": "0.0",
            "下落时间": "0.0",
            "上升电压": "0.0",
            "上升时间": "0.0",
        }
        
        self.settings_params = {
            "运动距离": "2.0",
            "油滴密度": "981",
            "室温": "24",
            "大气压强": "101325",
            "重力加速度": "9.7940",
            "修正常数": "0.00823",
        }
        
        # 电荷显示框数据 - 平衡法和动态法共用，不清除
        self.charge_display_data = ["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0"]
        self.current_charge_index = 0  # 当前要更新的电荷显示框索引

        # 存储图片引用
        self.images = {}
        self.photo_refs = {}  # 防止图片被垃圾回收
        
        # 创建主框架
        self.create_frames()
        
        # 加载图片
        self.load_all_images()
        
        # 初始化显示屏区域
        self.init_display_area()
        
        # 创建实验仪区域按钮
        self.create_instrument_buttons()
        
        # 创建数据记录区域
        self.create_data_record_area()
        
        self.create_charge_display_boxes()
        # 显示实验装置区域图片
        self.show_experiment_device()

    def create_charge_display_boxes(self):
        """创建七个电荷显示框 - 叠加在显示屏区域的背景图上"""
        # 注意：这里使用 self.frame_top_left 作为父容器
        # 电荷显示框容器
        charge_frame = tk.Frame(self.frame_top_left, bg='white')
        charge_frame.place(x=10+440+20, y=320-200, width=70, height=180)
        
        # 创建七个显示框
        self.charge_labels = []
        positions = [(0, 0), (0, 25), (0, 50), (0, 75),
                    (0, 100), (0, 125), (0, 150)]
        
        for i in range(7):
            frame = tk.Frame(charge_frame, bd=1, relief=tk.SUNKEN, bg='white')
            frame.place(x=positions[i][0], y=positions[i][1], width=70, height=25)
            
            # 显示框编号
            tk.Label(frame, text=f"{i+1}", font=('Arial', 8), 
                    bg='lightgray', width=3).place(x=0, y=0)
            
            # 电荷值标签
            label = tk.Label(frame, text=self.charge_display_data[i], 
                        font=('Arial', 8, 'bold'), bg='white')
            label.place(x=30, y=0)
            self.charge_labels.append(label)

    def update_charge_indicator(self):
        """更新电荷显示框的当前索引指示器"""
        if not hasattr(self, 'charge_indicator'):
            return
        
        # 指示器应该放在每个显示框下方
        positions = [(45, 70), (145, 70), (245, 70), (345, 70),
                    (95, 120), (195, 120), (295, 120)]
        
        if 0 <= self.current_charge_index < len(positions):
            self.charge_indicator.place(x=positions[self.current_charge_index][0], 
                                    y=positions[self.current_charge_index][1])

    def update_charge_display(self, charge_value):
        """更新电荷显示框的值"""
        # 如果电荷显示框还没创建，先创建
        if not hasattr(self, 'charge_labels'):
            self.create_charge_display_boxes()
        
        # 将电荷值转换为科学计数法显示（×10⁻¹⁹ C）
        if charge_value != 0:
            charge_display = f"{charge_value/1e-19:.2f}"
        else:
            charge_display = "0.00"
        
        # 更新当前显示框
        self.charge_display_data[self.current_charge_index] = charge_display
        
        # 确保列表存在且有足够元素
        if hasattr(self, 'charge_labels') and self.current_charge_index < len(self.charge_labels):
            self.charge_labels[self.current_charge_index].config(text=charge_display)
        
        # 移动到下一个显示框（循环）
        self.current_charge_index = (self.current_charge_index + 1) % 7
            
    def create_frames(self):
        """创建四个区域"""
        # 左上区域 - 显示屏区域
        self.frame_top_left = tk.Frame(self.root, bd=2, relief=tk.SUNKEN, bg='white')
        self.frame_top_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # 右上区域 - 实验仪区域
        self.frame_top_right = tk.Frame(self.root, bd=2, relief=tk.SUNKEN, bg='white')
        self.frame_top_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # 左下区域 - 实验装置区域
        self.frame_bottom_left = tk.Frame(self.root, bd=2, relief=tk.SUNKEN, bg='white')
        self.frame_bottom_left.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # 右下区域 - 数据记录区域
        self.frame_bottom_right = tk.Frame(self.root, bd=2, relief=tk.RAISED)
        self.frame_bottom_right.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        # 配置网格权重
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        self.root.grid_columnconfigure(0, weight=2)  # 左列
        self.root.grid_columnconfigure(1, weight=3)  # 右列

        # 区域标签
        tk.Label(self.frame_top_left, text="显示屏区域", font=('Arial', 12, 'bold')).pack(pady=5)
        tk.Label(self.frame_bottom_left, text="实验装置区域", font=('Arial', 12, 'bold')).pack(pady=5)
        tk.Label(self.frame_top_right, text="实验仪区域", font=('Arial', 12, 'bold')).pack(pady=5)
        tk.Label(self.frame_bottom_right, text="数据记录区域", font=('Arial', 12, 'bold')).pack(pady=5)
    
    def load_all_images(self):
        """加载所有需要的图片"""
        try:
            # 获取程序目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            background_dir = os.path.join(current_dir, 'background')
            
            # 检查background目录是否存在
            if not os.path.exists(background_dir):
                print(f"警告: background目录不存在: {background_dir}")
                os.makedirs(background_dir, exist_ok=True)
            
            # 显示屏区域图片
            balance_img_path = os.path.join(background_dir, "平衡法.jpg")
            dynamic_img_path = os.path.join(background_dir, "动态法.jpg")
            
            # 实验装置区域图片
            device_img_path = os.path.join(background_dir, "实验装置.jpg")
            
            # 实验仪区域图片
            instrument_img_path = os.path.join(background_dir, "FD-MLG-A.jpg")
            
            # 加载图片
            if os.path.exists(balance_img_path):
                self.images['平衡法'] = Image.open(balance_img_path)
                print("加载平衡法图片成功")
            else:
                print(f"平衡法图片不存在: {balance_img_path}")
                self.images['平衡法'] = Image.new('RGB', (400, 300), color='lightblue')
            
            if os.path.exists(dynamic_img_path):
                self.images['动态法'] = Image.open(dynamic_img_path)
                print("加载动态法图片成功")
            else:
                print(f"动态法图片不存在: {dynamic_img_path}")
                self.images['动态法'] = Image.new('RGB', (400, 300), color='lightgreen')
            
            if os.path.exists(device_img_path):
                self.images['实验装置'] = Image.open(device_img_path)
                print("加载实验装置图片成功")
            else:
                print(f"实验装置图片不存在: {device_img_path}")
                self.images['实验装置'] = Image.new('RGB', (100, 300), color='lightgray')
            
            if os.path.exists(instrument_img_path):
                self.images['实验仪'] = Image.open(instrument_img_path)
                print("加载实验仪图片成功")
            else:
                print(f"实验仪图片不存在: {instrument_img_path}")
                self.images['实验仪'] = Image.new('RGB', (800, 300), color='gray')
                
        except Exception as e:
            print(f"加载图片时出错: {e}")
            # 创建空白图片
            for name in ['平衡法', '动态法', '参数设置', '实验装置', '实验仪']:
                self.images[name] = Image.new('RGB', (400, 300), color='gray')
    
    def show_experiment_device(self):
        """显示实验装置区域的图片和电压调节滑块"""
        # 创建主容器Frame，水平排列图片和滑块
        main_container = tk.Frame(self.frame_bottom_left, bg='white')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：实验装置图片
        left_frame = tk.Frame(main_container, bg='white')
        left_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        try:
            # 获取实验装置图片
            if '实验装置' in self.images:
                img = self.images['实验装置']
                # 调整图片大小以适应区域
                img_resized = img.resize((200, 300), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_resized)
                
                # 创建标签显示图片
                label = tk.Label(left_frame, image=photo, bg='white')
                label.image = photo  # 保持引用
                label.pack()
        except Exception as e:
            print(f"显示实验装置图片失败: {e}")
            tk.Label(left_frame, text="实验装置图片", 
                    font=('Arial', 12), bg='white', width=20, height=10).pack()
        
        # 右侧：电压调节滑块和油滴控制按钮
        right_frame = tk.Frame(main_container, bg='white')
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建滑块
        self.create_voltage_sliders(right_frame)

    def create_voltage_sliders(self, parent_frame):
        """在指定父容器中创建电压调节滑块和油滴控制"""
        # 创建滑块框架
        slider_frame = tk.Frame(parent_frame, bg='white')
        slider_frame.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)
        
        # ====== 提升电压滑块 ======
        lift_frame = tk.Frame(slider_frame, bg='white')
        lift_frame.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(lift_frame, text="提升电压:", 
                font=('Arial', 10, 'bold'), bg='white').pack(anchor='w', pady=(0, 5))
        
        # 创建滑块和数值显示
        lift_slider_frame = tk.Frame(lift_frame, bg='white')
        lift_slider_frame.pack(fill=tk.X)
        
        # 数值标签
        self.lift_voltage_label = tk.Label(lift_slider_frame, 
                                        text=f"{self.lift_voltage.get()} V", 
                                        font=('Arial', 10, 'bold'), 
                                        bg='white', 
                                        width=6,
                                        fg='blue')
        self.lift_voltage_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # 滑块
        self.lift_slider = tk.Scale(lift_slider_frame, 
                                from_=200, to=300, 
                                orient=tk.HORIZONTAL,
                                variable=self.lift_voltage,
                                length=100,
                                showvalue=0,
                                command=self.on_lift_voltage_changed,
                                bg='white',
                                highlightbackground='white',
                                troughcolor='lightgray',
                                sliderrelief=tk.RAISED,
                                sliderlength=20)
        self.lift_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 范围标签
        range_label = tk.Label(lift_slider_frame, text="(200-300V)", 
                            font=('Arial', 9), bg='white', fg='gray')
        range_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # ====== 平衡电压滑块和微调按钮 ======
        balance_frame = tk.Frame(slider_frame, bg='white')
        balance_frame.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(balance_frame, text="平衡电压:", 
                font=('Arial', 10, 'bold'), bg='white').pack(anchor='w', pady=(0, 5))
        
        # 创建滑块和数值显示
        balance_slider_frame = tk.Frame(balance_frame, bg='white')
        balance_slider_frame.pack(fill=tk.X)
        
        # 数值标签
        self.balance_voltage_label = tk.Label(balance_slider_frame, 
                                            text=f"{self.balance_voltage_slider.get()} V", 
                                            font=('Arial', 10, 'bold'), 
                                            bg='white', 
                                            width=6,
                                            fg='green')
        self.balance_voltage_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # 创建微调按钮容器
        adjustment_frame = tk.Frame(balance_slider_frame, bg='white')
        adjustment_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # 减小按钮 (-1V)
        self.decrease_button = tk.Button(adjustment_frame, text="◀", 
                                    font=('Arial', 8, 'bold'),
                                    width=2, height=1,
                                    command=self.decrease_balance_voltage,
                                    bg='lightblue',
                                    relief=tk.RAISED,
                                    activebackground='skyblue')
        self.decrease_button.pack(side=tk.LEFT, padx=(0, 2))
        
        # 滑块
        self.balance_slider = tk.Scale(balance_slider_frame, 
                                    from_=0, to=500, 
                                    orient=tk.HORIZONTAL,
                                    variable=self.balance_voltage_slider,
                                    length=80,  # 稍微缩短滑块长度
                                    showvalue=0,
                                    command=self.on_balance_voltage_changed,
                                    bg='white',
                                    highlightbackground='white',
                                    troughcolor='lightgray',
                                    sliderrelief=tk.RAISED,
                                    sliderlength=20)
        self.balance_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 增加按钮 (+1V)
        self.increase_button = tk.Button(adjustment_frame, text="▶", 
                                    font=('Arial', 8, 'bold'),
                                    width=2, height=1,
                                    command=self.increase_balance_voltage,
                                    bg='lightcoral',
                                    relief=tk.RAISED,
                                    activebackground='salmon')
        self.increase_button.pack(side=tk.LEFT, padx=(2, 0))
        
        # 快速调整按钮容器
        quick_adjust_frame = tk.Frame(balance_slider_frame, bg='white')
        quick_adjust_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        # # -10V 快速调整按钮
        # tk.Button(quick_adjust_frame, text="-10", 
        #         font=('Arial', 7, 'bold'),
        #         width=3, height=1,
        #         command=lambda: self.adjust_balance_voltage(-10),
        #         bg='lightblue',
        #         relief=tk.RAISED,
        #         activebackground='skyblue').pack(side=tk.LEFT, padx=(0, 2))
        
        # # +10V 快速调整按钮
        # tk.Button(quick_adjust_frame, text="+10", 
        #         font=('Arial', 7, 'bold'),
        #         width=3, height=1,
        #         command=lambda: self.adjust_balance_voltage(10),
        #         bg='lightcoral',
        #         relief=tk.RAISED,
        #         activebackground='salmon').pack(side=tk.LEFT, padx=(0, 0))
        
        # 范围标签
        range_label2 = tk.Label(balance_slider_frame, text="(0-500V)", 
                            font=('Arial', 9), bg='white', fg='gray')
        range_label2.pack(side=tk.LEFT, padx=(15, 0))
        
        # ====== 油滴控制按钮组 ======
        oil_control_frame = tk.Frame(slider_frame, bg='white')
        oil_control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 喷入油雾按钮
        self.spray_button = tk.Button(oil_control_frame, text="喷入油雾", 
                                    font=('Arial', 10, 'bold'),
                                    bg='lightblue',
                                    command=self.spray_oil_droplets,
                                    relief=tk.RAISED,
                                    width=12)
        self.spray_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清空油滴按钮
        self.clear_button = tk.Button(oil_control_frame, text="清空油滴", 
                                    font=('Arial', 10, 'bold'),
                                    bg='lightcoral',
                                    command=self.clear_oil_droplets,
                                    relief=tk.RAISED,
                                    width=12)
        self.clear_button.pack(side=tk.LEFT)
        
        # ====== 对焦进度条 ======
        focus_frame = tk.Frame(slider_frame, bg='white')
        focus_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(focus_frame, text="对焦调节:", 
                font=('Arial', 10, 'bold'), bg='white').pack(anchor='w', pady=(0, 5))
        
        # 创建滑块和数值显示
        focus_slider_frame = tk.Frame(focus_frame, bg='white')
        focus_slider_frame.pack(fill=tk.X)
        
        # 数值标签
        self.focus_label = tk.Label(focus_slider_frame, 
                                text=f"{self.focus_scale.get():.1f}倍", 
                                font=('Arial', 10, 'bold'), 
                                bg='white', 
                                width=6,
                                fg='purple')
        self.focus_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # 滑块
        self.focus_slider = tk.Scale(focus_slider_frame, 
                                from_=1, to=3, 
                                orient=tk.HORIZONTAL,
                                variable=self.focus_scale,
                                length=100,
                                resolution=0.1,
                                showvalue=0,
                                command=self.on_focus_changed,
                                bg='white',
                                highlightbackground='white',
                                troughcolor='lightgray',
                                sliderrelief=tk.RAISED,
                                sliderlength=20)
        self.focus_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 范围标签
        range_label3 = tk.Label(focus_slider_frame, text="(1-3倍)", 
                            font=('Arial', 9), bg='white', fg='gray')
        range_label3.pack(side=tk.LEFT, padx=(15, 0))

    def decrease_balance_voltage(self):
        """减小平衡电压 1V"""
        current_value = self.balance_voltage_slider.get()
        if current_value > 0:
            new_value = current_value - 1
            self.balance_voltage_slider.set(new_value)
            self.on_balance_voltage_changed(new_value)
            print(f"平衡电压减小: {current_value}V → {new_value}V")

    def increase_balance_voltage(self):
        """增加平衡电压 1V"""
        current_value = self.balance_voltage_slider.get()
        if current_value < 500:
            new_value = current_value + 1
            self.balance_voltage_slider.set(new_value)
            self.on_balance_voltage_changed(new_value)
            print(f"平衡电压增加: {current_value}V → {new_value}V")

    def adjust_balance_voltage(self, delta):
        """按指定值调整平衡电压"""
        current_value = self.balance_voltage_slider.get()
        new_value = current_value + delta
        
        # 限制在有效范围内
        new_value = max(0, min(500, new_value))
        
        if new_value != current_value:
            self.balance_voltage_slider.set(new_value)
            self.on_balance_voltage_changed(new_value)
            
            direction = "增加" if delta > 0 else "减小"
            print(f"平衡电压{direction}{abs(delta)}V: {current_value}V → {new_value}V")

    def on_focus_changed(self, value):
        """对焦滑块变化时的回调"""
        self.focus_label.config(text=f"{float(value):.1f}倍")
        # 更新所有油滴的大小
        self.update_oil_droplet_sizes()

    def update_oil_droplet_sizes(self):
        """更新所有油滴的大小（根据对焦倍数）"""
        for droplet in self.oil_droplets:
            # 获取基础显示半径
            base_radius = droplet['display_radius_base']
            
            # 计算新的显示半径（基于对焦倍数）
            new_radius = int(base_radius * self.focus_scale.get())
            
            # 更新Canvas上的油滴大小
            if 'id' in droplet:
                self.display_canvas.coords(droplet['id'],
                                        droplet['x'] - new_radius,
                                        droplet['y'] - new_radius,
                                        droplet['x'] + new_radius,
                                        droplet['y'] + new_radius)
            
            # 更新存储的半径
            droplet['radius'] = new_radius

    def spray_oil_droplets(self):
        """喷入油雾 - 在显示屏区域生成随机油滴"""
        print("喷入油雾...")
        
        # 清空旧的油滴
        self.clear_oil_droplets()
        
        # 随机生成3-8个油滴
        num_droplets = random.randint(3, 15)
        
        # 获取显示屏区域的尺寸
        canvas_width = 400
        canvas_height = 300
        
        for i in range(num_droplets):
            # 随机油滴类型和大小
            size_type = random.choices(['small', 'medium', 'large'], weights=[0.4, 0.4, 0.2])[0]
            
            # 定义不同大小油滴的实际半径范围（微米）
            if size_type == 'small':
                actual_radius = random.uniform(0.5e-6, 1.0e-6)  # 0.5-1.0微米
                display_radius_base = 2  # 小油滴：基础显示半径2像素
            elif size_type == 'medium':
                actual_radius = random.uniform(1.0e-6, 1.5e-6)  # 1.0-1.5微米
                display_radius_base = 3  # 中油滴：基础显示半径3像素
            else:  # large
                actual_radius = random.uniform(1.5e-6, 2.0e-6)  # 1.5-2.0微米
                display_radius_base = 4  # 大油滴：基础显示半径4像素
            
            # 根据对焦倍数计算显示半径
            display_radius = int(display_radius_base * self.focus_scale.get())
            
            # 随机位置（根据油滴大小留出不同的边界）
            x = random.randint(display_radius*2, canvas_width - display_radius*2)
            y = random.randint(display_radius*2, canvas_height - display_radius*2)
            
            # 随机电荷数（1-8个电子）
            electron_count = random.randint(0, 8)
            charge = electron_count * self.electron_charge
            
            # 计算油滴质量
            volume = (4/3) * math.pi * (actual_radius ** 3)
            mass = self.oil_density * volume
            
            # 计算该油滴的平衡电压
            balanced_voltage = (mass * self.gravity * self.plate_distance) / charge if charge > 0 else 250
            
            # 限制平衡电压在合理范围内
            balanced_voltage = max(50, min(450, balanced_voltage))
            
            # 为油滴添加轻微的水平速度（随机扰动）
            velocity_x = random.uniform(-0.0001, 0.0001)
            
            # 在Canvas上绘制油滴（不同大小的红点）
            droplet_id = self.display_canvas.create_oval(
                x - display_radius, y - display_radius,
                x + display_radius, y + display_radius,
                fill='red', outline='darkred', width=1
            )
            
            # 存储油滴信息
            droplet = {
                'id': droplet_id,
                'x': x,
                'y': y,
                'radius': display_radius,
                'display_radius_base': display_radius_base,  # 存储基础显示半径
                'actual_radius': actual_radius,
                'charge': charge,
                'electron_count': electron_count,
                'mass': mass,
                'velocity_y': 0,
                'velocity_x': velocity_x,
                'balanced_voltage': balanced_voltage,
                'is_balanced': False,
                'last_update_time': time.time(),
                'color': 'red',
                'base_color': 'red',
                'size_type': size_type,
            }
            
            self.oil_droplets.append(droplet)
            print(f"油滴{i+1}: 大小={size_type}, 实际半径={actual_radius*1e6:.2f}μm, 显示半径={display_radius}px, 电荷={electron_count}e, 平衡电压={balanced_voltage:.1f}V")
        
        print(f"生成了 {num_droplets} 个大小不同的油滴")
        
        # 开始油滴运动模拟
        if not self.is_oil_simulating:
            self.start_oil_simulation()

    def clear_oil_droplets(self):
        """清空所有油滴"""
        print("清空油滴...")
        
        # 停止油滴模拟
        if self.is_oil_simulating and self.oil_timer_id:
            self.root.after_cancel(self.oil_timer_id)
            self.oil_timer_id = None
            self.is_oil_simulating = False
        
        # 从Canvas上删除所有油滴和标签
        for droplet in self.oil_droplets:
            self.display_canvas.delete(droplet['id'])
            # if 'label_id' in droplet:
            #     self.display_canvas.delete(droplet['label_id'])
        
        # 清空油滴列表
        self.oil_droplets.clear()

    def start_oil_simulation(self):
        """开始油滴运动模拟"""
        self.is_oil_simulating = True
        self.update_oil_droplet_motion()

    # 在 update_oil_droplet_motion 方法中进行以下修改：

    def update_oil_droplet_motion(self):
        """根据电荷公式反推速度更新油滴运动"""
        if not self.is_oil_simulating or not self.oil_droplets:
            self.is_oil_simulating = False
            return
        
        mode = self.voltage_mode.get()
        current_time = time.time()
        droplets_to_remove = []
        
        # 获取实验参数
        l = float(self.settings_params["运动距离"]) / 1000  # 运动距离 m
        rho = float(self.settings_params["油滴密度"])        # 油滴密度 kg/m³
        g = float(self.settings_params["重力加速度"])        # 重力加速度 m/s²
        d = self.plate_distance                             # 极板间距 m
        b = float(self.settings_params["修正常数"])          # 修正常数 N/m
        p = float(self.settings_params["大气压强"])          # 大气压强 Pa
        T = float(self.settings_params["室温"]) + 273.15     # 温度 K
        
        # 空气粘滞系数
        eta = 1.83e-5  # 室温下的空气粘滞系数 Pa·s
        
        # 速度放大系数
        SPEED_MULTIPLIER = 1.2
        if mode == "提升":
            SPEED_MULTIPLIER = 1
        
        for i, droplet in enumerate(self.oil_droplets):
            dt = current_time - droplet['last_update_time']
            if dt <= 0:
                dt = 0.05
            
            # 计算油滴实际半径和质量
            a = droplet['actual_radius']
            mass = droplet['mass']
            
            # 统一使用修正因子
            correction = 1 + b / (p * a)
            
            # 计算自由下落终端速度（基础速度，所有模式共用）
            v_free_fall = (2/9) * (rho * g * a**2) / eta
            v_free_fall = v_free_fall / correction  # 修正
            v_free_fall *= SPEED_MULTIPLIER  # 放大
            
            if mode == "平衡":
                # 平衡模式
                U = self.balance_voltage_slider.get()
                
                if U == 0:
                    # 电压为0时，就是自由下落
                    droplet['velocity_y'] = v_free_fall
                    droplet['is_balanced'] = False
                else:
                    # 计算电场力
                    E = U / d if d > 0 else 0  # 电场强度 V/m
                    F_e = droplet['charge'] * E  # 电场力
                    
                    # 计算重力
                    F_g = mass * g
                    
                    # 计算净力
                    net_force = F_e - F_g
                    
                    if abs(net_force) > 1e-20:
                        # 从力平衡计算速度
                        v_net = net_force / (6 * math.pi * eta * a * correction)
                        v_net *= SPEED_MULTIPLIER
                        
                        # 方向：电场力大于重力时向上，否则向下
                        if net_force > 0:
                            droplet['velocity_y'] = -abs(v_net)  # 向上为负
                        else:
                            droplet['velocity_y'] = abs(v_net)   # 向下为正
                    else:
                        droplet['velocity_y'] = 0  # 平衡状态
                
                # 判断平衡状态 (在平衡电压±1V范围内)
                if U > 0:  # 只有电压>0时才可能平衡
                    voltage_diff = abs(U - droplet['balanced_voltage'])
                    if voltage_diff < 1.0:
                        droplet['is_balanced'] = True
                        droplet['velocity_y'] = 0
                        if droplet['color'] != 'green':
                            self.display_canvas.itemconfig(droplet['id'], fill='green')
                            droplet['color'] = 'green'
                        droplet['last_update_time'] = current_time
                        continue
                    else:
                        droplet['is_balanced'] = False
                        if droplet['color'] != droplet['base_color']:
                            self.display_canvas.itemconfig(droplet['id'], fill=droplet['base_color'])
                            droplet['color'] = droplet['base_color']
                else:
                    droplet['is_balanced'] = False
                    if droplet['color'] != droplet['base_color']:
                        self.display_canvas.itemconfig(droplet['id'], fill=droplet['base_color'])
                        droplet['color'] = droplet['base_color']
                        
            elif mode == "提升":
                # 提升模式 - 油滴上升
                droplet['is_balanced'] = False
                if droplet['color'] != droplet['base_color']:
                    self.display_canvas.itemconfig(droplet['id'], fill=droplet['base_color'])
                    droplet['color'] = droplet['base_color']
                
                U_rise = self.lift_voltage.get() + self.balance_voltage_slider.get()
                
                if U_rise == 0:
                    # 总电压为0时，自由下落
                    droplet['velocity_y'] = v_free_fall
                else:
                    # 计算向上的电场力
                    E_rise = U_rise / d if d > 0 else 0
                    F_e_up = droplet['charge'] * E_rise
                    
                    # 计算重力
                    F_g = mass * g
                    
                    # 净力
                    net_force_up = F_e_up - F_g
                    
                    if net_force_up > 0:
                        # 上升速度
                        v_rise = net_force_up / (6 * math.pi * eta * a * correction)
                        v_rise *= SPEED_MULTIPLIER
                        droplet['velocity_y'] = -v_rise  # 向上为负
                    else:
                        # 净力向下或为零，则下落
                        droplet['velocity_y'] = v_free_fall
            
            else:  # 下落模式
                # 下落模式：自由下落，只受重力
                droplet['is_balanced'] = False
                if droplet['color'] != droplet['base_color']:
                    self.display_canvas.itemconfig(droplet['id'], fill=droplet['base_color'])
                    droplet['color'] = droplet['base_color']
                
                # 直接使用自由下落速度
                droplet['velocity_y'] = v_free_fall  # 向下为正
            
            # # 根据油滴大小调整速度比例（保持差异）
            # if droplet['size_type'] == 'small':
            #     speed_factor = 0.7  # 小油滴慢一些
            # elif droplet['size_type'] == 'medium':
            #     speed_factor = 1.0  # 中等油滴正常
            # else:  # large
            #     speed_factor = 1.3  # 大油滴快一些
            
            speed_factor=1
            
            droplet['velocity_y'] *= speed_factor
            
            # 转换速度：实际速度 -> 像素速度
            pixel_per_meter = 115000
            velocity_y_pixels = droplet['velocity_y'] * pixel_per_meter * dt
            
            # 更新位置
            new_x = droplet['x']
            new_y = droplet['y'] + velocity_y_pixels
            
            # 边界检查
            canvas_height = 300
            canvas_width = 400
            
            # 左右边界反弹
            if droplet['velocity_x'] != 0:
                if new_x < droplet['radius']:
                    new_x = droplet['radius']
                    droplet['velocity_x'] = -droplet['velocity_x'] * 0.8
                elif new_x > canvas_width - droplet['radius']:
                    new_x = canvas_width - droplet['radius']
                    droplet['velocity_x'] = -droplet['velocity_x'] * 0.8
            
            # 上下边界检查
            if new_y < droplet['radius']:
                new_y = droplet['radius']
                droplet['velocity_y'] = 0
            elif new_y > canvas_height - droplet['radius']:
                new_y = canvas_height - droplet['radius']
                droplet['velocity_y'] = 0
            
            # 更新Canvas上的位置
            dx = new_x - droplet['x']
            dy = new_y - droplet['y']
            
            if abs(dx) > 0.01 or abs(dy) > 0.01:
                self.display_canvas.move(droplet['id'], dx, dy)
            
            # 更新存储的位置和最后更新时间
            droplet['x'] = new_x
            droplet['y'] = new_y
            droplet['last_update_time'] = current_time
        
        # 删除碰到边界的油滴
        for index in sorted(droplets_to_remove, reverse=True):
            if 0 <= index < len(self.oil_droplets):
                droplet = self.oil_droplets[index]
                self.display_canvas.delete(droplet['id'])
                del self.oil_droplets[index]
        
        if not self.oil_droplets:
            self.is_oil_simulating = False
            return
        
        # 增加刷新频率
        self.oil_timer_id = self.root.after(30, self.update_oil_droplet_motion)


    def update_balance_status(self):
        """更新平衡状态显示"""
        # if not self.oil_droplets:
        #     # 如果没有油滴，显示提示
        #     if hasattr(self, 'balance_status_text'):
        #         self.display_canvas.delete(self.balance_status_text)
            
        #     current_voltage = self.balance_voltage_slider.get()
        #     self.balance_status_text = self.display_canvas.create_text(
        #         200, 20, text=f"电压:{current_voltage}V | 无油滴 (点击'喷入油雾')", 
        #         font=('Arial', 10, 'bold'), fill='gray'
        #     )
        #     return
        
        # balanced_count = sum(1 for d in self.oil_droplets if d['is_balanced'])
        # total_count = len(self.oil_droplets)
        
        # current_voltage = self.balance_voltage_slider.get()
        
        # # 在屏幕上显示平衡状态
        # if hasattr(self, 'balance_status_text'):
        #     self.display_canvas.delete(self.balance_status_text)
        
        # # 显示平衡的油滴编号
        # balanced_droplets = []
        # for i, droplet in enumerate(self.oil_droplets):
        #     voltage_diff = abs(current_voltage - droplet['balanced_voltage'])
        #     if voltage_diff < 1.0:
        #         balanced_droplets.append(str(i+1))
        
        # if balanced_droplets:
        #     status_text = f"电压:{current_voltage}V | 平衡油滴: #{','.join(balanced_droplets)}"
        #     color = "green"
        # else:
        #     # 找到最接近平衡的油滴
        #     closest_droplet = min(
        #         self.oil_droplets, 
        #         key=lambda d: abs(d['balanced_voltage'] - current_voltage)
        #     )
        #     closest_diff = closest_droplet['balanced_voltage'] - current_voltage
        #     closest_index = self.oil_droplets.index(closest_droplet) + 1
            
        #     status_text = f"电压:{current_voltage}V | 最近:油滴#{closest_index}(差{closest_diff:+.1f}V)"
        #     color = "blue" if abs(closest_diff) < 5 else "black"
        
        # self.balance_status_text = self.display_canvas.create_text(
        #     200, 20, text=status_text, 
        #     font=('Arial', 10, 'bold'), fill=color
        # )

    def on_lift_voltage_changed(self, value):
        """提升电压滑块变化时的回调"""
        self.lift_voltage_label.config(text=f"{value} V")
        self.update_voltage_display()
        
    def on_balance_voltage_changed(self, value):
        """平衡电压滑块变化时的回调"""
        voltage = int(value)
        self.balance_voltage_label.config(text=f"{voltage} V")
        
        # 更新参数
        self.balance_params["平衡电压"] = f"{voltage:.1f}"
        self.dynamic_params["平衡电压"] = f"{voltage:.1f}"
        
        # # 如果油滴存在，显示平衡状态
        # if self.oil_droplets:
        #     balanced_droplets = []
        #     for i, droplet in enumerate(self.oil_droplets):
        #         voltage_diff = abs(voltage - droplet['balanced_voltage'])
        #         if voltage_diff < 1.0:
        #             balanced_droplets.append(i+1)
            
        #     if balanced_droplets:
        #         print(f"🎯 电压{voltage}V: 油滴#{balanced_droplets}已达到平衡！")
        #     else:
        #         # 找到最接近平衡的油滴
        #         closest_droplet = min(
        #             self.oil_droplets, 
        #             key=lambda d: abs(d['balanced_voltage'] - voltage)
        #         )
        #         closest_index = self.oil_droplets.index(closest_droplet) + 1
        #         diff = closest_droplet['balanced_voltage'] - voltage
                
        #         if abs(diff) < 2:
        #             print(f"🔍 接近平衡: 油滴#{closest_index} 差{diff:+.1f}V")
        #         elif abs(diff) < 5:
        #             direction = "调高" if diff > 0 else "调低"
        #             print(f"📏 调整建议: {direction}电压{diff:.1f}V可使油滴#{closest_index}平衡")
        
        self.update_voltage_display()
        
    def update_voltage_display(self):
        """根据电压模式和滑块值更新显示屏上的电压显示"""
        mode = self.voltage_mode.get()
        balance_value = self.balance_voltage_slider.get()
        lift_value = self.lift_voltage.get()
        
        if mode == "提升":
            # 上升电压 = 提升电压 + 平衡电压
            total_voltage = lift_value + balance_value
            self.dynamic_params["上升电压"] = f"{total_voltage:.1f}"
            
            # 更新动态法界面的上升电压显示
            if hasattr(self, 'rise_voltage_text'):
                self.display_canvas.itemconfig(self.rise_voltage_text, 
                                            text=f"{total_voltage:.1f} V")
            
            print(f"提升模式: 上升电压 = {lift_value} + {balance_value} = {total_voltage}V")
            
        elif mode == "平衡":
            # 平衡电压 = 平衡电压滑块值
            self.balance_params["平衡电压"] = f"{balance_value:.1f}"

            self.dynamic_params["平衡电压"] = f"{balance_value:.1f}"
            
            # 更新平衡法界面的平衡电压显示
            if hasattr(self, 'balance_voltage_text'):
                self.display_canvas.itemconfig(self.balance_voltage_text, 
                                            text=f"{balance_value:.1f} V")
            
            if hasattr(self, 'dynamic_balance_text'):
                self.display_canvas.itemconfig(self.dynamic_balance_text, 
                                            text=f"{balance_value:.1f} V")
            print(f"平衡模式: 平衡电压 = {balance_value}V")
            
        elif mode == "下落":
            print(f"下落模式: 平衡电压 = {balance_value}V")
            # 在下落模式下，可以添加其他逻辑
        #   
    def init_display_area(self):
        """初始化显示屏区域"""
        # 创建画布用于显示图片和参数
        self.display_canvas = tk.Canvas(self.frame_top_left, width=400, height=300)
        self.display_canvas.pack(padx=10, pady=10)
        
        # 不需要Frame容器了
        # 直接使用Canvas存储界面元素
        self.display_items = {}  # 存储Canvas上的元素引用
        
        # 初始化显示
        self.switch_display_interface("平衡法")
    
    def create_instrument_buttons(self):
        """在实验仪区域创建控制按钮"""
        # 先显示背景图片
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            img_path3 = get_resource_path(os.path.join('background', "FD-MLG-A.jpg"))
            img3 = Image.open(img_path3)
            img3 = img3.resize((800, 300), Image.Resampling.LANCZOS)
            self.photo3 = ImageTk.PhotoImage(img3)
            bg_label = tk.Label(self.frame_top_right, image=self.photo3)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"无法加载实验仪图片: {e}")
        
        # 不使用Frame，直接在区域上放置按钮
        
        # ====== 电压控制按钮组 ======
        # 这三个按钮是互斥的单选按钮，只能选择一个
        
        # 当前选择的电压模式
        self.voltage_mode = tk.StringVar(value="平衡")  # 初始选择平衡模式
        
        # 提升按钮 - 可以自定义位置 (x=150, y=100)
        self.lift_button = tk.Radiobutton(
            self.frame_top_right, 
            text="", 
            variable=self.voltage_mode, 
            value="提升",
            command=self.on_voltage_mode_changed,
            font=('Arial', 8),
            bg='white',
            fg='white',
            # selectcolor='#333333',
            activebackground='#545454',
            activeforeground='white',
            indicatoron=0,  # 不使用小圆圈指示器，显示为普通按钮
            width=6,
            height=1,
            relief=tk.FLAT
        )
        self.lift_button.place(x=150-50-2, y=100+60)  # 可自定义位置
        
        # 平衡按钮 - 可以自定义位置 (x=150, y=130)
        self.balance_button = tk.Radiobutton(
            self.frame_top_right, 
            text="", 
            variable=self.voltage_mode, 
            value="平衡",
            command=self.on_voltage_mode_changed,
            font=('Arial', 8),
            bg='white',
            fg='white',
            # selectcolor='#333333',
            activebackground='#545454',
            activeforeground='white',
            indicatoron=0,
            width=6,
            height=1,
            relief=tk.FLAT
        )
        self.balance_button.place(x=100-2, y=195)  # 可自定义位置
        
        # 下落按钮 - 可以自定义位置 (x=150, y=160)
        self.fall_button = tk.Radiobutton(
            self.frame_top_right, 
            text="", 
            variable=self.voltage_mode, 
            value="下落",
            command=self.on_voltage_mode_changed,
            font=('Arial', 8),
            bg='white',
            fg='white',
            # selectcolor='#333333',
            activebackground='#545454',
            activeforeground='white',
            indicatoron=0,
            width=6,
            height=1,
            relief=tk.FLAT
        )
        self.fall_button.place(x=150-50-2, y=160+70)  # 可自定义位置
        
        # 初始处于平衡状态
        self.balance_button.select()  # 确保平衡按钮被选中
        self.on_balance_mode()  # 调用平衡模式初始化函数
        
        # ====== 原来的控制按钮 ======
        # 向上按钮 - 位置 (x=300, y=100)
        up_button = tk.Button(self.frame_top_right, text="", font=('Arial', 8), 
                            width=2, height=1, command=self.navigate_up, bg='#545454',relief=tk.FLAT)
        up_button.place(x=300-30+37, y=100+72)
        
        # 向下按钮 - 位置 (x=300, y=170)
        down_button = tk.Button(self.frame_top_right, text="", font=('Arial', 8),
                                width=2, height=1, command=self.navigate_down, bg='#545454',relief=tk.FLAT)
        down_button.place(x=300-30+37, y=170+74)
        
        # 确定按钮 - 位置 (x=380, y=135)
        ok_button = tk.Button(self.frame_top_right, text="", font=('Arial', 8),
                            width=2, height=1, command=self.select_item, bg='#545454',relief=tk.FLAT)
        ok_button.place(x=350+37, y=172)
        
        # 返回按钮 - 位置 (x=220, y=135)
        back_button = tk.Button(self.frame_top_right, text="", font=('Arial', 8),
                                width=2, height=1, command=self.go_back, bg='#545454',relief=tk.FLAT)
        back_button.place(x=350+37, y=244)

    def on_voltage_mode_changed(self):
        """电压模式改变时的回调函数"""
        mode = self.voltage_mode.get()
        print(f"电压模式已切换为: {mode}")
        
        # 根据不同的电压模式执行不同的操作
        if mode == "提升":
            self.on_lift_mode()
        elif mode == "平衡":
            self.on_balance_mode()
        elif mode == "下落":
            self.on_fall_mode()
        
        # 更新电压显示
        self.update_voltage_display()

    def on_lift_mode(self):
        """提升模式下的操作"""
        print("切换到提升模式")
        # 在提升模式下，更新动态法界面的上升电压
        
    def on_balance_mode(self):
        """平衡模式下的操作"""
        print("切换到平衡模式")
        # 在平衡模式下，更新平衡法界面的平衡电压
        
    def on_fall_mode(self):
        """下落模式下的操作"""
        print("切换到下落模式：电场关闭，油滴只受重力作用自由下落")
        print("提示：在下落模式下，可以测量油滴的下落时间")
        
        # 更新电压显示
        self.update_voltage_display()
        
        # 如果有油滴，重置颜色为红色（因为不再平衡）
        for droplet in self.oil_droplets:
            if droplet['color'] != 'red':
                self.display_canvas.itemconfig(droplet['id'], fill='red')
                droplet['color'] = 'red'
            droplet['is_balanced'] = False
            # 重置最后更新时间，避免dt过大
            droplet['last_update_time'] = time.time()
        
        # 确保模拟继续运行
        if self.oil_droplets and not self.is_oil_simulating:
            self.start_oil_simulation()
    
    def show_balance_interface_canvas(self):
        """在Canvas上显示平衡法界面"""
        canvas = self.display_canvas
        
        # 存储所有可选择的项目（按照你想要的导航顺序）
        self.balance_items = []
        
        # 实验方法标题 - 位置 (x=20, y=20)
        method_text = canvas.create_text(20, 55, text="平衡法", 
                                        font=('Arial', 12, 'bold'), anchor='w', tags="balance_method")
        self.balance_items.append(method_text)  # 索引0：实验方法
        
        # 平衡电压 - 位置 (x=20, y=50) - 改为只读标签
        self.balance_voltage_text = canvas.create_text(30, 100, text=f"{self.balance_params['平衡电压']} V", 
                                                    font=('Arial', 10), anchor='w', fill='black')
        # 注意：平衡电压不加入导航循环
        
        # 下落时间 - 位置 (x=20, y=80) - 改为只读标签
        self.fall_time_text = canvas.create_text(30, 145, text=f"{self.balance_params['下落时间']} s", 
                                            font=('Arial', 10), anchor='w', fill='black')
        self.balance_items.append(self.fall_time_text)  # 索引1：下落时间
        
        # 计算并保存按钮 - 位置 (x=20, y=110)
        calc_button = canvas.create_text(10, 270, text="计算并保存", 
                                        font=('Arial', 10), anchor='w', tags="calc_save")
        self.balance_items.append(calc_button)  # 索引2：计算并保存
        
        # 参数设置按钮 - 位置 (x=20, y=280)
        settings_text = canvas.create_text(330, 270, text="参数设置", 
                                        font=('Arial', 10), anchor='w', tags="settings")
        self.balance_items.append(settings_text)  # 索引3：参数设置
        
        # 重新绘制油滴
        self.redraw_oil_droplets()


    def switch_display_interface(self, interface_name):
        """切换显示屏区域的界面"""
        # 如果正在计时，先停止计时
        if self.is_timing:
            if self.current_interface == "平衡法":
                self.stop_timing("平衡法", "下落时间")
            elif self.current_interface == "动态法":
                # 判断当前选中的是哪个时间
                if hasattr(self, 'dynamic_items') and self.selected_index < len(self.dynamic_items):
                    if self.selected_index == 1:  # 上升时间
                        self.stop_timing("动态法", "上升时间")
                    elif self.selected_index == 2:  # 下落时间
                        self.stop_timing("动态法", "下落时间")
        
        # 切换界面时重置所有时间数据
        if interface_name != self.current_interface:  # 只有真的切换界面时才重置
            print(f"从 {self.current_interface} 切换到 {interface_name}")
            
            # 只在切换到不同实验方法时重置时间数据，不清空油滴
            if interface_name in ["平衡法", "动态法"] and self.current_interface in ["平衡法", "动态法"]:
                # 从平衡法切换到动态法或反之，重置时间数据
                self.balance_params["下落时间"] = "0.0"
                self.dynamic_params["下落时间"] = "0.0"
                self.dynamic_params["上升时间"] = "0.0"
            elif interface_name == "参数设置":
                # 切换到参数设置时，保留时间数据，因为可能会返回
                print("切换到参数设置界面")
            elif self.current_interface == "参数设置" and interface_name in ["平衡法", "动态法"]:
                # 从参数设置返回时，不重置时间数据
                print(f"从参数设置返回到 {interface_name}")
            
            # 注意：不清空油滴！油滴在切换实验方法时保持存在
        
        self.current_interface = interface_name
        
        # 清除Canvas上的所有元素（除了背景）
        self.display_canvas.delete("all")
        
        # 只有在切换到参数设置时才清空油滴
        # if interface_name == "参数设置":
        #     print("切换到参数设置，清空油滴")
        #     self.clear_oil_droplets()
        # else:
        #     # 切换到平衡法或动态法时，不清空油滴
        #     print(f"切换到{interface_name}，保持现有{len(self.oil_droplets)}个油滴")
        
        # 更新背景图片
        if interface_name in self.images:
            img = self.images[interface_name].resize((400, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.photo_refs[interface_name] = photo  # 保存引用
            self.display_canvas.create_image(0, 0, image=photo, anchor='nw')
        
        # 重置选中索引为0（总是从第一个项目开始）
        self.selected_index = 0
        
        # 根据界面显示不同的参数
        if interface_name == "平衡法":
            self.show_balance_interface_canvas()
        elif interface_name == "动态法":
            self.show_dynamic_interface_canvas()
        elif interface_name == "参数设置":
            self.show_settings_interface_canvas()
        
        # 延迟高亮，确保所有控件都已创建
        self.root.after(100, self.highlight_selected_canvas)
        
        # 切换界面后更新电压显示
        self.root.after(150, self.update_voltage_display)
        
        # 如果还有油滴，重新开始模拟
        if interface_name in ["平衡法", "动态法"] and self.oil_droplets and not self.is_oil_simulating:
            print(f"切换到{interface_name}，重新开始油滴模拟")
            self.start_oil_simulation()
    
    def highlight_selected_canvas(self):
        """高亮Canvas上的当前选中项"""
        # 清除所有文本类型的高亮
        try:
            highlighted_items = self.display_canvas.find_withtag("highlight")
            for item_id in highlighted_items:
                try:
                    # 只对文本类型应用fill选项
                    item_type = self.display_canvas.type(item_id)
                    if item_type == "text":
                        # 检查这个项目是否是正在计时的时间显示
                        if self.is_timing:
                            if self.current_interface == "平衡法" and hasattr(self, 'fall_time_text') and item_id == self.fall_time_text:
                                continue  # 跳过正在计时的项目
                            elif self.current_interface == "动态法":
                                if (hasattr(self, 'rise_time_text') and item_id == self.rise_time_text) or \
                                (hasattr(self, 'dynamic_fall_text') and item_id == self.dynamic_fall_text):
                                    continue  # 跳过正在计时的项目
                        
                        self.display_canvas.itemconfig(item_id, fill="black", font=('Arial', 10))
                except:
                    pass
        except:
            pass
        
        # 根据当前界面获取项目列表
        if self.current_interface == "平衡法":
            items = self.balance_items
        elif self.current_interface == "动态法":
            items = self.dynamic_items
        elif self.current_interface == "参数设置":
            items = self.settings_items
        else:
            return
        
        # 高亮当前选中项
        if 0 <= self.selected_index < len(items):
            item_id = items[self.selected_index]
            
            try:
                # 检查项目类型
                item_type = self.display_canvas.type(item_id)
                if item_type == "text":
                    # 检查这个项目是否是正在计时的时间显示
                    if self.is_timing:
                        if self.current_interface == "平衡法" and hasattr(self, 'fall_time_text') and item_id == self.fall_time_text:
                            return  # 如果是正在计时的项目，不设置为蓝色
                        elif self.current_interface == "动态法":
                            if (hasattr(self, 'rise_time_text') and item_id == self.rise_time_text) or \
                            (hasattr(self, 'dynamic_fall_text') and item_id == self.dynamic_fall_text):
                                return  # 如果是正在计时的项目，不设置为蓝色
                    
                    # 设置为蓝色高亮
                    self.display_canvas.itemconfig(item_id, fill="blue", font=('Arial', 10, 'bold'))
            except Exception as e:
                print(f"高亮时出错: {e}")
            
            # 给选中项添加highlight标签
            self.display_canvas.addtag_withtag("highlight", item_id)
    
    def show_dynamic_interface_canvas(self):
        """在Canvas上显示动态法界面"""
        canvas = self.display_canvas
        
        # 存储所有可选择的项目（按照你想要的导航顺序）
        self.dynamic_items = []
        
        # 实验方法标题 - 位置 (x=20, y=20)
        method_text = canvas.create_text(20, 55, text="动态法", 
                                        font=('Arial', 12, 'bold'), anchor='w', tags="dynamic_method")
        self.dynamic_items.append(method_text)  # 索引0：实验方法
        
        # 上升时间 - 位置 (x=20, y=50) - 改为只读标签
        self.rise_time_text = canvas.create_text(30, 190, text=f"{self.dynamic_params['上升时间']} s", 
                                            font=('Arial', 10), anchor='w', fill='black')
        self.dynamic_items.append(self.rise_time_text)  # 索引1：上升时间
        
        # 下落时间 - 位置 (x=20, y=80) - 改为只读标签
        self.dynamic_fall_text = canvas.create_text(30, 235, text=f"{self.dynamic_params['下落时间']} s", 
                                                font=('Arial', 10), anchor='w', fill='black')
        self.dynamic_items.append(self.dynamic_fall_text)  # 索引2：下落时间
        
        # 上升电压 - 位置 (x=20, y=110) - 改为只读标签
        self.rise_voltage_text = canvas.create_text(30, 80+65, text=f"{self.dynamic_params['上升电压']} V", 
                                                font=('Arial', 10), anchor='w', fill='black')
        
        # 平衡电压 - 位置 (x=20, y=140) - 改为只读标签
        self.dynamic_balance_text = canvas.create_text(30, 100, text=f"{self.dynamic_params['平衡电压']} V", 
                                                    font=('Arial', 10), anchor='w', fill='black')
        
        # 计算并保存按钮 - 位置 (x=20, y=170)
        dynamic_calc_button = canvas.create_text(10, 270, text="计算并保存", 
                                                font=('Arial', 10), anchor='w')
        self.dynamic_items.append(dynamic_calc_button)  # 索引3：计算并保存
        
        # 参数设置按钮 - 位置 (x=20, y=200)
        dynamic_settings_button = canvas.create_text(330, 270, text="参数设置", 
                                                    font=('Arial', 10), anchor='w')
        self.dynamic_items.append(dynamic_settings_button)  # 索引4：参数设置
        
        # 重新绘制油滴
        self.redraw_oil_droplets()

    def redraw_oil_droplets(self):
        """重新绘制所有油滴到Canvas上"""
        if not self.oil_droplets:
            return
        
        print(f"重新绘制 {len(self.oil_droplets)} 个大小不同的油滴")
        
        # 重新创建所有油滴在Canvas上
        for droplet in self.oil_droplets:
            x = droplet['x']
            y = droplet['y']
            radius = droplet['radius']
            color = droplet['color']
            
            # 在Canvas上重新绘制油滴
            droplet['id'] = self.display_canvas.create_oval(
                x - radius, y - radius,
                x + radius, y + radius,
                fill=color, outline='darkred', width=1
            )

    def show_settings_interface_canvas(self):
        """在Canvas上显示参数设置界面"""
        canvas = self.display_canvas
        
        # 存储所有可选择的项目
        self.settings_items = []
        
        # 运动距离 - 位置 (x=20, y=20)
        canvas.create_text(20, 20, text="运动距离:", font=('Arial', 10), anchor='w')
        self.distance_var = tk.StringVar(value=self.settings_params["运动距离"])
        self.distance_entry = tk.Entry(canvas, textvariable=self.distance_var,
                                    width=10, font=('Arial', 10), bg='white')
        distance_window = canvas.create_window(100, 20, window=self.distance_entry, anchor='w')
        canvas.create_text(180, 20, text="mm", font=('Arial', 9), anchor='w')
    
        # 油滴密度 - 位置 (x=20, y=50)
        canvas.create_text(20, 50, text="油滴密度:", font=('Arial', 10), anchor='w')
        self.density_var = tk.StringVar(value=self.settings_params["油滴密度"])
        self.density_entry = tk.Entry(canvas, textvariable=self.density_var,
                                    width=10, font=('Arial', 10), bg='white')
        density_window = canvas.create_window(100, 50, window=self.density_entry, anchor='w')
        canvas.create_text(180, 50, text="kg/m³", font=('Arial', 9), anchor='w')
        
        # 室温 - 位置 (x=20, y=80)
        canvas.create_text(20, 80, text="室温:", font=('Arial', 10), anchor='w')
        self.temp_var = tk.StringVar(value=self.settings_params["室温"])
        self.temp_entry = tk.Entry(canvas, textvariable=self.temp_var,
                                width=10, font=('Arial', 10), bg='white')
        temp_window = canvas.create_window(100, 80, window=self.temp_entry, anchor='w')
        canvas.create_text(180, 80, text="℃", font=('Arial', 9), anchor='w')

        # 大气压强 - 位置 (x=20, y=110)
        canvas.create_text(20, 110, text="大气压强:", font=('Arial', 10), anchor='w')
        self.pressure_var = tk.StringVar(value=self.settings_params["大气压强"])
        self.pressure_entry = tk.Entry(canvas, textvariable=self.pressure_var,
                                    width=10, font=('Arial', 10), bg='white')
        pressure_window = canvas.create_window(100, 110, window=self.pressure_entry, anchor='w')
        canvas.create_text(180, 110, text="Pa", font=('Arial', 9), anchor='w')

        # 重力加速度 - 位置 (x=20, y=140)
        canvas.create_text(20, 140, text="重力加速度:", font=('Arial', 10), anchor='w')
        self.gravity_var = tk.StringVar(value=self.settings_params["重力加速度"])
        self.gravity_entry = tk.Entry(canvas, textvariable=self.gravity_var,
                                    width=10, font=('Arial', 10), bg='white')
        gravity_window = canvas.create_window(100, 140, window=self.gravity_entry, anchor='w')
        canvas.create_text(180, 140, text="m/s²", font=('Arial', 9), anchor='w')

        # 修正常数 - 位置 (x=20, y=170)
        canvas.create_text(20, 170, text="修正常数:", font=('Arial', 10), anchor='w')
        self.correction_var = tk.StringVar(value=self.settings_params["修正常数"])
        self.correction_entry = tk.Entry(canvas, textvariable=self.correction_var,
                                    width=10, font=('Arial', 10), bg='white')
        correction_window = canvas.create_window(100, 170, window=self.correction_entry, anchor='w')
        canvas.create_text(180, 170, text="N/m", font=('Arial', 9), anchor='w')

        # 保存并返回按钮 - 位置 (x=20, y=210)
        save_return_text = canvas.create_text(20, 210, text="保存并返回", 
                                            font=('Arial', 10, 'bold'), anchor='w')
        self.settings_items.append(save_return_text)
        
        # 重置为默认按钮 - 位置 (x=20, y=240)
        reset_text = canvas.create_text(20, 240, text="重置为默认", 
                                    font=('Arial', 10, 'bold'), anchor='w')
        self.settings_items.append(reset_text)
    

    def start_timing(self, method, time_type):
        """开始计时 - 从0开始"""
        self.is_timing = True
        self.elapsed_time = 0.0  # 重置为0
        self.start_time = time.time()  # 使用time模块获取当前时间（秒）
        
        # 清除之前的定时器
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        
        # 立即显示0.00s
        if method == "平衡法" and time_type == "下落时间" and hasattr(self, 'fall_time_text'):
            self.display_canvas.itemconfig(self.fall_time_text, 
                                        text="0.00 s")
            # 将时间显示变为红色，表示正在计时
            self.display_canvas.itemconfig(self.fall_time_text, fill="red")
            # 从highlight标签中移除，防止被重置颜色
            self.display_canvas.dtag(self.fall_time_text, "highlight")
        elif method == "动态法":
            if time_type == "上升时间" and hasattr(self, 'rise_time_text'):
                self.display_canvas.itemconfig(self.rise_time_text, 
                                            text="0.00 s")
                # 将时间显示变为红色，表示正在计时
                self.display_canvas.itemconfig(self.rise_time_text, fill="red")
                # 从highlight标签中移除，防止被重置颜色
                self.display_canvas.dtag(self.rise_time_text, "highlight")
            elif time_type == "下落时间" and hasattr(self, 'dynamic_fall_text'):
                self.display_canvas.itemconfig(self.dynamic_fall_text, 
                                            text="0.00 s")
                # 将时间显示变为红色，表示正在计时
                self.display_canvas.itemconfig(self.dynamic_fall_text, fill="red")
                # 从highlight标签中移除，防止被重置颜色
                self.display_canvas.dtag(self.dynamic_fall_text, "highlight")
        
        print(f"开始计时: {method} - {time_type}")
        print("提示：正在计时中，上下键已被禁用")
        
        # 开始定时器
        self.update_timer(method, time_type)

    def stop_timing(self, method, time_type):
        """停止计时"""
        if not self.is_timing:
            return
        
        self.is_timing = False
        
        # 取消定时器
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        
        # 更新时间数据
        final_time = self.elapsed_time  # 使用已经计算好的时间
        
        if method == "平衡法" and time_type == "下落时间":
            self.balance_params[time_type] = f"{final_time:.2f}"
            print(f"停止计时: {method} - {time_type} = {final_time:.2f}s")
            
            # 恢复时间显示颜色 - 直接调用高亮方法让系统处理颜色
            if hasattr(self, 'fall_time_text'):
                # 重新高亮当前选中的项目
                self.highlight_selected_canvas()
            
        elif method == "动态法":
            self.dynamic_params[time_type] = f"{final_time:.2f}"
            print(f"停止计时: {method} - {time_type} = {final_time:.2f}s")
            
            # 恢复时间显示颜色 - 直接调用高亮方法让系统处理颜色
            if hasattr(self, 'rise_time_text') or hasattr(self, 'dynamic_fall_text'):
                # 重新高亮当前选中的项目
                self.highlight_selected_canvas()
        
        print("提示：计时已停止，可以移动光标")

    def update_timer(self, method, time_type):
        """更新计时器显示 - 50毫秒刷新频率"""
        if not self.is_timing:
            return
        
        # 计算经过的时间（使用time模块）
        current_time = time.time()
        self.elapsed_time = current_time - self.start_time  # 直接计算经过的时间
        
        # 更新显示（保留2位小数）
        time_str = f"{self.elapsed_time:.2f} s"
        if method == "平衡法" and time_type == "下落时间" and hasattr(self, 'fall_time_text'):
            self.display_canvas.itemconfig(self.fall_time_text, 
                                        text=time_str)
        elif method == "动态法":
            if time_type == "上升时间" and hasattr(self, 'rise_time_text'):
                self.display_canvas.itemconfig(self.rise_time_text, 
                                            text=time_str)
            elif time_type == "下落时间" and hasattr(self, 'dynamic_fall_text'):
                self.display_canvas.itemconfig(self.dynamic_fall_text, 
                                            text=time_str)
        
        # 继续定时器，使用50毫秒的间隔（每秒20次刷新）
        self.timer_id = self.root.after(50, lambda: self.update_timer(method, time_type))

    # 修改 calculate_elapsed_time 方法
    def calculate_elapsed_time(self):
        """计算经过的时间（秒）- 直接从elapsed_time变量获取"""
        return self.elapsed_time

    # 修改 navigate_up 和 navigate_down 方法
    def navigate_up(self):
        """向上导航"""
        # 如果正在计时，不允许移动光标
        if self.is_timing:
            print("正在计时，请先停止计时再移动光标")
            return
        
        if self.current_interface == "平衡法":
            self.selected_index = (self.selected_index - 1) % len(self.balance_items)
        elif self.current_interface == "动态法":
            self.selected_index = (self.selected_index - 1) % len(self.dynamic_items)
        elif self.current_interface == "参数设置":
            self.selected_index = (self.selected_index - 1) % len(self.settings_items)
        
        # 调用Canvas版本的高亮方法
        self.highlight_selected_canvas()

    def navigate_down(self):
        """向下导航"""
        # 如果正在计时，不允许移动光标
        if self.is_timing:
            print("正在计时，请先停止计时再移动光标")
            return
        
        if self.current_interface == "平衡法":
            self.selected_index = (self.selected_index + 1) % len(self.balance_items)
        elif self.current_interface == "动态法":
            self.selected_index = (self.selected_index + 1) % len(self.dynamic_items)
        elif self.current_interface == "参数设置":
            self.selected_index = (self.selected_index + 1) % len(self.settings_items)
        
        # 调用Canvas版本的高亮方法
        self.highlight_selected_canvas()

    
    
    def select_item(self):
        """确定按钮的功能"""
        # 检查当前是否正在计时
        if self.is_timing:
            # 如果正在计时，停止计时
            if self.current_interface == "平衡法":
                self.stop_timing("平衡法", "下落时间")
            elif self.current_interface == "动态法":
                if self.selected_index == 1:  # 上升时间
                    self.stop_timing("动态法", "上升时间")
                elif self.selected_index == 2:  # 下落时间
                    self.stop_timing("动态法", "下落时间")
            return
        
        # 如果不是计时状态，正常处理选择
        if self.current_interface == "平衡法":
            self.handle_balance_selection()
        elif self.current_interface == "动态法":
            self.handle_dynamic_selection()
        elif self.current_interface == "参数设置":
            self.handle_settings_selection()
    
    def handle_balance_selection(self):
        """处理平衡法界面的选择"""
        if self.selected_index == 0:  # 实验方法
            # 切换到动态法界面
            self.switch_display_interface("动态法")
        elif self.selected_index == 1:  # 下落时间
            # 开始计时
            self.start_timing("平衡法", "下落时间")
        elif self.selected_index == 2:  # 计算并保存
            self.calculate_and_save("平衡法")
        elif self.selected_index == 3:  # 参数设置
            self.switch_display_interface("参数设置")

    def handle_dynamic_selection(self):
        """处理动态法界面的选择"""
        if self.selected_index == 0:  # 实验方法
            # 切换到平衡法界面
            self.switch_display_interface("平衡法")
        elif self.selected_index == 1:  # 上升时间
            # 开始计时
            self.start_timing("动态法", "上升时间")
        elif self.selected_index == 2:  # 下落时间
            # 开始计时
            self.start_timing("动态法", "下落时间")
        elif self.selected_index == 3:  # 计算并保存
            self.calculate_and_save("动态法")
        elif self.selected_index == 4:  # 参数设置
            self.switch_display_interface("参数设置")


    def update_balance_display(self):
        """更新平衡法界面的显示值"""
        # 如果当前是平衡模式，从滑块获取平衡电压
        if self.voltage_mode.get() == "平衡":
            balance_value = self.balance_voltage_slider.get()
            self.balance_params["平衡电压"] = f"{balance_value:.1f}"
        
        if hasattr(self, 'balance_voltage_text'):
            # 更新平衡电压显示
            self.display_canvas.itemconfig(self.balance_voltage_text, 
                                        text=f"{self.balance_params['平衡电压']} V")
        if hasattr(self, 'fall_time_text'):
            # 更新下落时间显示
            self.display_canvas.itemconfig(self.fall_time_text, 
                                        text=f"{self.balance_params['下落时间']} s")

    def update_dynamic_display(self):
        """更新动态法界面的显示值"""
        # 如果当前是提升模式，计算上升电压
        if self.voltage_mode.get() == "提升":
            total_voltage = self.lift_voltage.get() + self.balance_voltage_slider.get()
            self.dynamic_params["上升电压"] = f"{total_voltage:.1f}"
        
        if hasattr(self, 'rise_time_text'):
            # 更新上升时间显示
            self.display_canvas.itemconfig(self.rise_time_text, 
                                        text=f"{self.dynamic_params['上升时间']} s")
        if hasattr(self, 'dynamic_fall_text'):
            # 更新下落时间显示
            self.display_canvas.itemconfig(self.dynamic_fall_text, 
                                        text=f"{self.dynamic_params['下落时间']} s")
        if hasattr(self, 'rise_voltage_text'):
            # 更新上升电压显示
            self.display_canvas.itemconfig(self.rise_voltage_text, 
                                        text=f"{self.dynamic_params['上升电压']} V")
        if hasattr(self, 'dynamic_balance_text'):
            # 更新平衡电压显示
            self.display_canvas.itemconfig(self.dynamic_balance_text, 
                                        text=f"{self.dynamic_params['平衡电压']} V")
        
    def handle_settings_selection(self):
        """处理参数设置界面的选择"""
        # 保存数据
        self.settings_params["运动距离"] = self.distance_var.get()
        self.settings_params["油滴密度"] = self.density_var.get()
        self.settings_params["室温"] = self.temp_var.get()
        self.settings_params["大气压强"] = self.pressure_var.get()
        self.settings_params["重力加速度"] = self.gravity_var.get()
        self.settings_params["修正常数"] = self.correction_var.get()
        
        if self.selected_index == 0:  # 保存并返回
            # 保存设置
            print("保存设置")
            # 总是返回到平衡法界面
            self.switch_display_interface("平衡法")
        elif self.selected_index == 1:  # 重置为默认
            self.reset_to_default()
    
    def calculate_and_save(self, method):
        """计算并保存数据"""
        print(f"执行{method}计算并保存")
        
        # 根据实验方法计算油滴电荷
        if method == "平衡法":
            # 使用实际测量数据
            balance_voltage = float(self.balance_params["平衡电压"])
            fall_time = float(self.balance_params["下落时间"])
            
            if balance_voltage == 0 or fall_time == 0:
                print("错误：平衡电压或下落时间为零，无法计算")
                return
            
            # 计算油滴电荷
            charge = self.calculate_balance_method_charge(balance_voltage, fall_time)
            print(f"平衡法计算结果: 电荷 = {charge:.2e} C")
            
            # 更新显示框
            self.update_charge_display(charge)
            
        else:  # 动态法
            # 使用实际测量数据
            balance_voltage = float(self.dynamic_params["平衡电压"])
            fall_time = float(self.dynamic_params["下落时间"])
            rise_voltage = float(self.dynamic_params["上升电压"])
            rise_time = float(self.dynamic_params["上升时间"])
            
            if balance_voltage == 0 or fall_time == 0 or rise_voltage == 0 or rise_time == 0:
                print("错误：电压或时间为零，无法计算")
                return
            
            # 计算油滴电荷
            charge = self.calculate_dynamic_method_charge(balance_voltage, fall_time, rise_voltage, rise_time)
            print(f"动态法计算结果: 电荷 = {charge:.2e} C")
            
            # 更新显示框
            self.update_charge_display(charge)

    
    def calculate_balance_method_charge(self, U, t_g):
        """计算平衡法油滴电荷"""
        import math
        
        # 获取实验参数
        rho = float(self.settings_params["油滴密度"])          # 油滴密度 (kg/m³)
        g = float(self.settings_params["重力加速度"])          # 重力加速度 (m/s²)
        l = float(self.settings_params["运动距离"]) / 1000     # 运动距离 (m)
        b = float(self.settings_params["修正常数"])           # 修正常数 (N/m)
        p = float(self.settings_params["大气压强"])           # 大气压强 (Pa)
        d = 5.00e-3                                           # 极板间距 (m)
        
        # 空气粘滞系数 (Pa·s)，根据室温计算
        T = float(self.settings_params["室温"]) + 273.15      # 转换为开尔文
        eta = 1.818e-5 * (T/293.15)**0.735                    # 温度修正
        
        # 计算油滴半径 a（迭代计算）
        v_g = l / t_g  # 下落速度
        
        # 第一次近似
        a = math.sqrt((9 * eta * v_g) / (2 * rho * g))
        
        # 迭代修正（通常2-3次迭代即可）
        for _ in range(3):
            correction_factor = 1 + b / (p * a)
            a = math.sqrt((9 * eta * l) / (2 * rho * g * t_g * correction_factor))
        
        # 最终修正因子
        correction_factor_final = 1 + b / (p * a)
        
        # 计算油滴电荷 q
        q = (18 * math.pi / math.sqrt(2 * rho * g)) * \
            math.pow((eta * l) / (t_g * correction_factor_final), 1.5) * \
            (d / U)
        
        return q

    def calculate_dynamic_method_charge(self, U_balance, t_fall, U_rise, t_rise):
        """计算动态法油滴电荷 - 使用上升电压"""
        import math
        
        # 获取参数
        l = float(self.settings_params["运动距离"]) / 1000  # m
        rho = float(self.settings_params["油滴密度"])        # kg/m³
        g = float(self.settings_params["重力加速度"])        # m/s²
        d = 5.00e-3                                         # 极板间距 m
        
        # 空气粘滞系数
        T = float(self.settings_params["室温"]) + 273.15
        eta = 1.818e-5 * (T/293.15)**0.735
        
        # 计算速度
        v_fall = l / t_fall  # 下落速度
        v_rise = l / t_rise  # 上升速度
        
        # 计算油滴半径 a（使用下落时间）
        a = math.sqrt((9 * eta * v_fall) / (2 * rho * g))
        
        # 动态法电荷公式：q = (6πηad/U_rise) * (v_fall + v_rise)
        q = (6 * math.pi * eta * a * d / U_rise) * (v_fall + v_rise)
        
        return q

    def reset_to_default(self):
        """重置为默认参数"""
        default_settings = {
            "运动距离": "2.0",
            "油滴密度": "981",
            "室温": "24",
            "大气压强": "101325",
            "重力加速度": "9.7940",
            "修正常数": "0.00823",
        }
        
        self.settings_params.update(default_settings)
        
        # 重置时间数据（但不重置电荷显示框）
        self.balance_params["下落时间"] = "0.0"
        self.dynamic_params["下落时间"] = "0.0"
        self.dynamic_params["上升时间"] = "0.0"
        
        # 更新界面显示
        self.distance_var.set(default_settings["运动距离"])
        self.density_var.set(default_settings["油滴密度"])
        self.temp_var.set(default_settings["室温"])
        self.pressure_var.set(default_settings["大气压强"])
        self.gravity_var.set(default_settings["重力加速度"])
        self.correction_var.set(default_settings["修正常数"])
        
        print("已重置为默认参数")
    
    def go_back(self):
        """返回按钮的功能"""
        if self.current_interface == "参数设置":
            # 从参数设置返回时，总是回到平衡法界面
            self.switch_display_interface("平衡法")
        else:
            print("返回功能")
            # 可以添加其他返回逻辑
    
    # 以下部分保持原有功能...
    def create_data_record_area(self):
        """创建数据记录区域（与原代码相同）"""
        # 创建选项卡框架
        tab_frame = tk.Frame(self.frame_bottom_right)
        tab_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 创建选项卡
        tk.Label(tab_frame, text="选择实验方法:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        # 创建选项变量
        self.method_var = tk.StringVar(value="平衡法")
        
        # 创建单选按钮
        balance_radio = tk.Radiobutton(tab_frame, text="平衡法", variable=self.method_var, 
                                       value="平衡法", command=self.update_content)
        balance_radio.pack(side=tk.LEFT, padx=10)
        
        dynamic_radio = tk.Radiobutton(tab_frame, text="动态法", variable=self.method_var, 
                                       value="动态法", command=self.update_content)
        dynamic_radio.pack(side=tk.LEFT, padx=10)

        
        # 创建内容显示区域
        self.content_frame = tk.Frame(self.frame_bottom_right, bd=1, relief=tk.SUNKEN)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 初始显示平衡法内容
        self.update_content()
    
    def update_content(self):
        """根据选择更新内容"""
        # 清除当前内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        method = self.method_var.get()
        
        if method == "平衡法":
            self.show_balance_method()
        else:
            self.show_dynamic_method()
    
    def show_balance_method(self):
        """显示平衡法内容"""
        tk.Label(self.content_frame, text="平衡法实验内容", 
                font=('Arial', 14, 'bold'), fg='blue').pack(pady=10)
        
        # 创建滚动文本框
        text_frame = tk.Frame(self.content_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, height=10, yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # 添加示例内容
        content = """平衡法实验步骤：
        
1. 调节实验装置至水平状态
2. 安装待测样品
3. 调节传感器位置
4. 记录初始读数
5. 施加平衡力
6. 记录最终读数
7. 计算相关参数

实验参数设置：
- 样品质量：______ g
- 力臂长度：______ cm
- 测量精度：______ N
- 环境温度：______ °C

数据记录表：
测量次数 | 初始读数 | 平衡读数 | 差值
1        |          |          |
2        |          |          |
3        |          |          |
"""
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)
        
        # 添加操作按钮
        button_frame = tk.Frame(self.content_frame)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="开始记录", command=self.start_recording).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="停止记录", command=self.stop_recording).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="导出数据", command=self.export_data).pack(side=tk.LEFT, padx=5)
    
    def show_dynamic_method(self):
        """显示动态法内容"""
        tk.Label(self.content_frame, text="动态法实验内容", 
                font=('Arial', 14, 'bold'), fg='green').pack(pady=10)
        
        # 创建滚动文本框
        text_frame = tk.Frame(self.content_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, height=10, yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # 添加示例内容
        content = """动态法实验步骤：
        
1. 设置动态参数
2. 启动振荡装置
3. 记录振荡频率
4. 监测振幅变化
5. 采集动态数据
6. 分析衰减曲线
7. 计算动态参数

实验参数设置：
- 振荡频率：______ Hz
- 初始振幅：______ mm
- 采样频率：______ Hz
- 测量时间：______ s

数据记录表：
时间(s) | 振幅(mm) | 频率(Hz) | 相位(rad)
0.0     |          |          |
0.1     |          |          |
0.2     |          |          |
"""
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)
        
        # 添加操作按钮
        button_frame = tk.Frame(self.content_frame)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="开始采集", command=self.start_acquisition).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="暂停采集", command=self.pause_acquisition).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="数据分析", command=self.analyze_data).pack(side=tk.LEFT, padx=5)
    
    # 以下为功能占位方法
    def start_recording(self):
        print("开始记录数据")
    
    def stop_recording(self):
        print("停止记录数据")
    
    def export_data(self):
        print("导出数据")
    
    def start_acquisition(self):
        print("开始采集数据")
    
    def pause_acquisition(self):
        print("暂停采集数据")
    
    def analyze_data(self):
        print("进行数据分析")

def main():
    root = tk.Tk()
    app = ExperimentApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()  