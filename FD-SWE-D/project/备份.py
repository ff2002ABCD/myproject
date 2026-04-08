import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button
import sys
import os
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import pandas as pd
from tkinter import filedialog, messagebox
import math
import random

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def get_resource_path(relative_path):
    """获取资源的绝对路径，支持打包后的环境"""
    try:
        # 打包后的临时文件夹路径
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

class ThreeWirePendulumFrontView:
    def __init__(self, radius=0.084, wire_length=1, initial_angle=5.0):
        """
        初始化三线摆参数
        """
        self.radius = radius
        self.wire_length = wire_length
        self.initial_angle = np.radians(initial_angle)
        
        self.background_dir = get_resource_path("background")

        self.power_on = False

        

        # 数据记录相关属性 - 先初始化为空，在create_tkinter_interface中再创建
        self.data_records = None
        
        # 固定参数
        self.fixed_params = {
            "r": 3.060,  # cm
            "R": 8.025,  # cm
            "D1": 16.792,  # cm
            "H": 100.00,  # cm
            "M0": 614.93,  # g
            "M1": 231.32,  # g
            "D_inner": 6.014,  # cm
            "D_outer": 11.992,  # cm
            "M3": 234.38,  # g
            "D_disk": 11.992,  # cm
            "g": 9.81,  # m/s²
            "J0_theory": 0,  # kg·m²
            "JM1_theory": 0,  # kg·m²
            "JM3_theory": 0,  # kg·m²
            
            # 平行轴定理相关参数
            "D_cylinder": 3.000,  # cm - 圆柱体直径
            "D_groove": 12.00,    # cm - 悬盘上刻线直径
            "M2_total": 239.95,   # g - 两圆柱体总质量
            "d_calculated": 0,  # m - d计算值，点击计算后更新
            "d_measured": 0.045,  # m - d实测值，固定为0.045m
        }

        
        
        # 新增：D槽相关属性
        self.d_groove_var = None  # D槽变量
        self.d_groove_min = 4.0   # 最小4cm
        self.d_groove_max = 12.0  # 最大12cm
        self.d_groove_current = self.fixed_params["D_groove"]  # 当前值
        self.H_var = None
        # 悬挂物体选项
        self.suspended_object = "无"  # 初始状态：无、铝制圆环、两个铝制圆柱、铝制圆盘
        self.object_colors = {
            "无": None,
            "铝制圆环": "orange",
            "两个铝制圆柱": "blue", 
            "铝制圆盘": "green"
        }
        
        # 物体尺寸参数
        self.ring_disk_width = 0.12  # 圆环和圆盘宽度 6cm
        self.cylinder_width = 0.03   # 圆柱宽度 3cm
        self.cylinder_height = 0.09  # 圆柱高度 6cm（宽度的两倍）

        # 光电门触发相关属性
        self.gate_triggered = False  # 光电门触发状态
        self.last_angle = 0.0  # 上一次的角度值，用于判断角度变化
        self.trigger_threshold = 0.08  # 触发距离阈值
        self.angle_threshold = 3.0  # 角度阈值（度）
        self.above_threshold = False  # 标记是否曾经超过角度阈值
        # 周期测量界面状态
        self.period_measurement_mode = "设定模式"  # "设定模式" 或 "测量模式"
        self.max_record_count = 10  # 最大记录次数
        self.current_measure_count = 0  # 当前测量次数
        self.temp_measure_data = []  # 临时测量数据
        self.period_data_groups = []  # 存储多组周期测量数据
        self.current_query_group = 0  # 当前查询的组索引
        self.measurement_start_time = 0  # 测量开始时间
        self.period_ui_active = True  # 是否显示周期测量界面
        self.period_mode = "单周"  # 周期模式：单周/双周
        self.measure_count = 0  # 测量次数
        self.measure_time = 0  # 测量时间
        
        # 周期测量界面选择状态
        self.period_selection_index = 0  # 当前选中的栏目索引
        self.period_items_count = 5  # 可选择的栏目数量（不包括时间）
        self.setting_count = False  # 是否正在设置次数
        # 圆盘高度参数（可调节）
        self.plate_height_offset = 0.0  # 圆盘高度偏移量
        
        # 光电门高度参数
        self.gate_height = -0.15  # 初始位置
        self.gate_min_height = -0.15  # 最低高度
        
        # 动画控制
        self.animation_running = False
        # 重力加速度
        self.g = 9.81
        
        # 计算振动周期
        self.period = 2 * np.pi * np.sqrt(self.wire_length / self.g)
        self.omega = 2 * np.pi / self.period
        
        # 固定悬挂点高度（不随滑块改变）
        self.fixed_anchor_height = wire_length
        
        # 动画控制
        self.animation_running = False
        self.anim = None
        self.current_time = 0.0
        
        # 周期测量参数
        self.period_count = 0
        self.period_time = 0.0
        
        # 更新所有位置
        self.update_positions()
        
        # 创建Tkinter界面
        self.create_tkinter_interface()

    def check_gate_trigger(self, t):
        """
        检查光电门触发条件
        返回: 是否触发
        """
        # 计算当前扭转角度
        current_angle = np.degrees(self.initial_angle * np.cos(self.omega * t))
        current_angle_abs = abs(current_angle)
        last_angle_abs = abs(self.last_angle)
        
        # 计算圆盘底部到光电门的距离
        plate_bottom = self.plate_height_offset - self.plate_height/2
        distance_to_gate = plate_bottom - self.gate_height
        
        # 检查是否曾经超过角度阈值
        if current_angle_abs > self.angle_threshold:
            self.above_threshold = True
        
        # 判断触发条件
        trigger_condition = (
            distance_to_gate < self.trigger_threshold and  # 距离条件
            self.above_threshold and  # 曾经超过角度阈值
            last_angle_abs > self.angle_threshold and  # 上一次超过阈值
            current_angle_abs <= self.angle_threshold  # 当前进入阈值内
        )
        
        # 更新触发状态
        new_trigger_state = False
        if trigger_condition and not self.gate_triggered:
            new_trigger_state = True
            print(f"光电门触发！距离: {distance_to_gate:.3f}m, 角度: {current_angle:.1f}°")
            # 调用光电门触发处理
            self.on_gate_trigger()
        
        # 更新上一次的角度值
        self.last_angle = current_angle
        
        return new_trigger_state   
    
    def update_positions(self):
        """根据当前圆盘高度更新位置"""
        # 固定悬挂点位置（不随高度调节改变）
        self.anchor_points = np.array([
            [-self.radius+0.054, self.fixed_anchor_height],   # 左侧悬挂点
            [0, self.fixed_anchor_height],                   # 中间悬挂点
            [self.radius-0.054, self.fixed_anchor_height]     # 右侧悬挂点
        ])
        
        # 圆盘中心位置（可调节高度）
        self.plate_center = np.array([0, self.plate_height_offset])
        self.plate_width = 2 * self.radius
        self.plate_height = 0.04
        
        # 圆盘上连接点的位置（随圆盘高度移动）
        self.connection_height = self.plate_height / 2 + self.plate_height_offset
        
        # 圆盘上连接点的初始位置
        self.plate_points_initial = np.array([
            [-self.radius+0.004, self.connection_height],   # 左侧连接点
            [0, self.connection_height],                   # 中间连接点  
            [self.radius-0.004, self.connection_height]     # 右侧连接点
        ])

        # 动态计算光电门最大高度（圆盘下边缘-0.07m）
        plate_bottom = self.plate_height_offset - self.plate_height/2
        self.gate_max_height = max(-0.15, plate_bottom - 0.07)

        # 立即应用限制
        if self.gate_height > self.gate_max_height:
            self.gate_height = self.gate_max_height
            if hasattr(self, 'gate_var'):
                self.gate_var.set(self.gate_height)
                self.gate_label.config(text=f"{self.gate_height:.2f}")
    
    def get_wire_positions(self, t):
        """
        计算在时间t时三根线在圆盘上的连接点位置
        """
        # 计算当前扭转角度
        twist_angle = self.initial_angle * np.cos(self.omega * t)
        
        # 中间线的运动方向与两侧相反
        left_point_x = (-self.radius+0.015) + self.radius * np.sin(twist_angle) * 0.8
        right_point_x = (self.radius-0.015) + self.radius * np.sin(twist_angle) * 0.8
        middle_point_x = -self.radius * np.sin(twist_angle) * 1.6
        
        plate_points = np.array([
            [left_point_x, self.connection_height],     # 左侧连接点
            [middle_point_x, self.connection_height],   # 中间连接点
            [right_point_x, self.connection_height]     # 右侧连接点
        ])
        
        return plate_points
    
    def create_tkinter_interface(self):
        """创建Tkinter界面"""
        self.root = tk.Tk()
        self.root.title("FD-IM-D 转动惯量实验仪")
        self.root.geometry("1600x800")
        
        # 现在创建 H_var，因为根窗口已经存在
        self.H_var = tk.StringVar(value=f"{self.fixed_params['H']}")
        # 初始化数据记录相关属性
        self.init_data_records()

        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)
        
        # 左侧框架 - 三线摆区域 (占1/3宽度)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        # 右侧框架 - 实验仪区域 (占2/3宽度)
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(10, 0))
        
        main_frame.columnconfigure(0, weight=1)  # 左侧权重
        main_frame.columnconfigure(1, weight=6)  # 右侧权重
        
        # 创建Matplotlib图形 - 放在控制面板下面
        self.fig, self.ax = plt.subplots(figsize=(4, 5))
        # 调整图形边距，增加左边距
        self.fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.1)
        # 将Matplotlib图形嵌入Tkinter
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=False)
        self.canvas = FigureCanvasTkAgg(self.fig, canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=False)
        
        # === 左侧区域：三线摆示意图和控件 ===
        # 控制面板框架 - 放在顶部
        control_frame = ttk.LabelFrame(left_frame, text="控制面板", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 圆盘高度滑块
        height_frame = ttk.Frame(control_frame)
        height_frame.pack(fill=tk.X, pady=5)
        ttk.Label(height_frame, text="圆盘高度:", width=10).pack(side=tk.LEFT)  # 增加标签宽度
        
        # 圆盘高度微调按钮框架
        height_control_frame = ttk.Frame(height_frame)
        height_control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 减号按钮 - 向右移动一些
        self.height_minus_btn = ttk.Button(height_control_frame, text="-", width=3,
                                        command=lambda: self.adjust_height(-0.001))
        self.height_minus_btn.pack(side=tk.LEFT, padx=(10, 5))  # 增加左边距
        
        # 滑块 - 缩短长度
        self.height_var = tk.DoubleVar(value=self.plate_height_offset)
        self.height_scale = ttk.Scale(height_control_frame, from_=0.0, to=0.8, 
                                    variable=self.height_var, orient=tk.HORIZONTAL,
                                    length=180)  # 缩短滑块长度
        self.height_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 加号按钮
        self.height_plus_btn = ttk.Button(height_control_frame, text="+", width=3,
                                        command=lambda: self.adjust_height(0.001))
        self.height_plus_btn.pack(side=tk.LEFT, padx=(5, 10))
        
        # 高度显示标签（精确到毫米）
        self.height_label = ttk.Label(height_control_frame, text="0.000m", width=8)
        self.height_label.pack(side=tk.RIGHT)
        
        # 光电门高度滑块
        gate_frame = ttk.Frame(control_frame)
        gate_frame.pack(fill=tk.X, pady=5)
        ttk.Label(gate_frame, text="光电门高度:", width=10).pack(side=tk.LEFT)  # 增加标签宽度
        
        # 光电门高度微调按钮框架
        gate_control_frame = ttk.Frame(gate_frame)
        gate_control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 减号按钮 - 向右移动一些
        self.gate_minus_btn = ttk.Button(gate_control_frame, text="-", width=3,
                                    command=lambda: self.adjust_gate_height(-0.001))
        self.gate_minus_btn.pack(side=tk.LEFT, padx=(10, 5))  # 增加左边距
        
        # 滑块 - 缩短长度
        self.gate_var = tk.DoubleVar(value=self.gate_height)
        self.gate_scale = ttk.Scale(gate_control_frame, from_=-0.15, to=0.8, 
                                variable=self.gate_var, orient=tk.HORIZONTAL,
                                length=180)  # 缩短滑块长度
        self.gate_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 加号按钮
        self.gate_plus_btn = ttk.Button(gate_control_frame, text="+", width=3,
                                    command=lambda: self.adjust_gate_height(0.001))
        self.gate_plus_btn.pack(side=tk.LEFT, padx=(5, 10))
        
        # 高度显示标签（精确到毫米）
        self.gate_label = ttk.Label(gate_control_frame, text="-0.150m", width=8)
        self.gate_label.pack(side=tk.RIGHT)

        # 绑定长按事件
        self.bind_button_repeat(self.height_minus_btn, lambda: self.adjust_height(-0.001))
        self.bind_button_repeat(self.height_plus_btn, lambda: self.adjust_height(0.001))
        self.bind_button_repeat(self.gate_minus_btn, lambda: self.adjust_gate_height(-0.001))
        self.bind_button_repeat(self.gate_plus_btn, lambda: self.adjust_gate_height(0.001))
        
        # 悬挂物体选择
        object_frame = ttk.Frame(control_frame)
        object_frame.pack(fill=tk.X, pady=5)
        ttk.Label(object_frame, text="悬挂物体:", width=12).pack(side=tk.LEFT)
        self.object_var = tk.StringVar(value="无")
        self.object_combo = ttk.Combobox(object_frame, textvariable=self.object_var, 
                                    values=["无", "铝制圆环", "两个铝制圆柱", "铝制圆盘"],
                                    state="readonly", width=20)
        self.object_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))

        # === 悬盘刻线直径D槽滑块 ===
        self.d_groove_frame = ttk.Frame(control_frame)
        self.d_groove_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.d_groove_frame, text="刻线直径D槽:", width=12).pack(side=tk.LEFT)

        # D槽控制框架
        d_groove_control_frame = ttk.Frame(self.d_groove_frame)
        d_groove_control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 减号按钮
        self.d_groove_minus_btn = ttk.Button(d_groove_control_frame, text="-", width=3,
                                            command=lambda: self.adjust_d_groove(-0.1))
        self.d_groove_minus_btn.pack(side=tk.LEFT, padx=(10, 5))

        # 滑块
        self.d_groove_var = tk.DoubleVar(value=self.d_groove_current)
        self.d_groove_scale = ttk.Scale(d_groove_control_frame, 
                                    from_=self.d_groove_min, 
                                    to=self.d_groove_max,
                                    variable=self.d_groove_var, 
                                    orient=tk.HORIZONTAL,
                                    length=180)
        self.d_groove_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 加号按钮
        self.d_groove_plus_btn = ttk.Button(d_groove_control_frame, text="+", width=3,
                                        command=lambda: self.adjust_d_groove(0.1))
        self.d_groove_plus_btn.pack(side=tk.LEFT, padx=(5, 10))

        # 显示标签（精确到毫米）
        self.d_groove_label = ttk.Label(d_groove_control_frame, 
                                    text=f"{self.d_groove_current:.1f}cm", 
                                    width=8)
        self.d_groove_label.pack(side=tk.RIGHT)

        # 绑定长按事件
        self.bind_button_repeat(self.d_groove_minus_btn, lambda: self.adjust_d_groove(-0.1))
        self.bind_button_repeat(self.d_groove_plus_btn, lambda: self.adjust_d_groove(0.1))
        # 绑定D槽滑块事件
        self.d_groove_scale.configure(command=self.on_d_groove_change)

        # 初始隐藏D槽滑块
        self.d_groove_frame.pack_forget()

        # 按钮框架
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="开始", 
                                    command=self.start_animation,
                                    width=12)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # self.stop_button = ttk.Button(button_frame, text="暂停", 
        #                             command=self.stop_animation,
        #                             width=12)
        # self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reset_button = ttk.Button(button_frame, text="停止", 
                                    command=self.reset_animation,
                                    width=12)
        self.reset_button.pack(side=tk.LEFT)
        self.reset_button.config(state="disabled")
        # === 右侧区域：实验仪界面 ===
        # 实验仪标题
        # ttk.Label(right_frame, text="实验仪控制面板", 
        #         font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # 创建Canvas用于叠加图片和控件
        self.canvas_bg = tk.Canvas(right_frame, width=900, height=350, 
                                        bg='white', highlightthickness=1, 
                                        highlightbackground="gray")
        self.canvas_bg.pack(pady=(0, 10))
        
        # 加载实验仪图片到Canvas
        try:
            experiment_device_path = os.path.join(self.background_dir, 'FD-IM-D实验仪.png')
            if os.path.exists(experiment_device_path):
                image = Image.open(experiment_device_path)
                # 调整图片大小以适应Canvas
                image = image.resize((900, 350), Image.Resampling.LANCZOS)
                self.experiment_photo = ImageTk.PhotoImage(image)
                
                # 在Canvas上显示图片
                self.canvas_bg.create_image(0, 0, anchor=tk.NW, image=self.experiment_photo)
                
                # 在图片上叠加控制按钮
                self.create_overlay_controls()
            else:
                self.canvas_bg.create_text(190, 225, text="实验仪图片未找到", 
                                                font=("Arial", 12))
        except Exception as e:
            print(f"加载实验仪图片时出错: {e}")
            self.canvas_bg.create_text(190, 225, text="图片加载失败", 
                                            font=("Arial", 12))
        
        # 周期测量显示框 - 放在Canvas下面
        self.create_period_measurement_ui()
        
        # 绑定事件
        self.height_scale.configure(command=self.on_height_change)
        self.gate_scale.configure(command=self.on_gate_change)
        
        # 绑定悬挂物体选择事件
        self.object_combo.bind('<<ComboboxSelected>>', self.on_object_change)

        # 初始绘制
        self.update_display(0)
        
         # === 数据记录区域 ===
        self.create_data_record_area(right_frame)

        self.hide_measurement_ui()
        # 启动界面
        self.root.mainloop()
    
    def init_data_records(self):
        """初始化数据记录相关属性"""
        self.data_records = {
            # 下悬盘测量数据
            "t0_times": [tk.StringVar(value="") for _ in range(3)],  # 10周期时间
            "t0_avg": tk.StringVar(value=""),  # 10周期平均值
            "T0": tk.StringVar(value=""),  # 平均周期
            "J0": tk.StringVar(value=""),  # 下悬盘转动惯量
            "J0_theory": tk.StringVar(value=""),  # 新增：J0理论值
            "J0_error": tk.StringVar(value=""),  # 误差
            
            # 圆环测量数据
            "t1_times": [tk.StringVar(value="") for _ in range(3)],  # 10周期时间
            "t1_avg": tk.StringVar(value=""),  # 10周期平均值
            "T1": tk.StringVar(value=""),  # 平均周期
            "J1": tk.StringVar(value=""),  # 悬盘加圆环转动惯量
            "JM1": tk.StringVar(value=""),  # 圆环转动惯量
            "JM1_theory": tk.StringVar(value=""),  # 新增：JM1理论值
            "JM1_error": tk.StringVar(value=""),  # 误差
            
            # 圆盘测量数据
            "t3_times": [tk.StringVar(value="") for _ in range(3)],  # 10周期时间
            "t3_avg": tk.StringVar(value=""),  # 10周期平均值
            "T3": tk.StringVar(value=""),  # 平均周期
            "J3": tk.StringVar(value=""),  # 悬盘加圆盘转动惯量
            "JM3": tk.StringVar(value=""),  # 圆盘转动惯量
            "JM3_theory": tk.StringVar(value=""),  # 新增：JM3理论值
            "JM3_error": tk.StringVar(value=""),  # 误差

            # 平行轴定理测量数据
            "t2_times": [tk.StringVar(value="") for _ in range(3)],  # 10周期时间
            "t2_avg": tk.StringVar(value=""),  # 10周期平均值
            "T2": tk.StringVar(value=""),  # 平均周期
            "J2_total": tk.StringVar(value=""),  # 悬盘加两圆柱转动惯量
            "J2_prime": tk.StringVar(value=""),  # 两圆柱转动惯量
            "J2_single": tk.StringVar(value=""),  # 单圆柱转动惯量
            "d_measured": tk.StringVar(value=""),  # d实测值
            "d_calculated": tk.StringVar(value=""),  # 新增：d计算值变量
            "d_error": tk.StringVar(value=""),  # d误差

            # 新增：D槽和2d的StringVar
            "d_groove": tk.StringVar(value=f"{self.fixed_params['D_groove']} cm"),
            "two_d": tk.StringVar(value=f"{self.fixed_params['D_groove'] - 3.0:.2f} cm")
        }
        # 数据记录区域标签引用
        self.data_record_labels = {
            "d_groove_label": None,  # D槽标签
            "two_d_label": None      # 2d标签
        }

        # 添加D槽相关的StringVar
        self.d_groove_display_var = tk.StringVar(value=f"{self.fixed_params['D_groove']} cm")
        self.two_d_display_var = tk.StringVar()
        
        # 计算初始的2d值
        initial_two_d = self.fixed_params['D_groove'] - 3.0
        self.two_d_display_var.set(f"{initial_two_d:.2f} cm")

    def create_data_record_area(self, parent):
        """创建数据记录区域 - 使用选项卡布局"""
        # 检查数据记录是否已初始化
        if self.data_records is None:
            print("数据记录系统未初始化")
            return
        
        # 创建主框架
        record_frame = ttk.LabelFrame(parent, text="实验数据记录", padding=10)
        record_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 第一行：固定参数显示和按钮
        param_frame = ttk.Frame(record_frame)
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 左侧：固定参数
        left_frame = ttk.Frame(param_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_frame, text="上圆盘悬点到盘心的距离r:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(left_frame, text=f"{self.fixed_params['r']} cm").pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(left_frame, text="下圆盘悬点到盘心的距离R:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(left_frame, text=f"{self.fixed_params['R']} cm").pack(side=tk.LEFT, padx=(0, 20))
        
        # 右侧：导入导出按钮
        right_frame = ttk.Frame(param_frame)
        right_frame.pack(side=tk.RIGHT)
        
        ttk.Button(right_frame, text="导入数据", command=self.import_data, width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(right_frame, text="导出数据", command=self.export_data, width=12).pack(side=tk.LEFT)
        
        # 第二行：创建选项卡
        self.notebook = ttk.Notebook(record_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建四个实验的选项卡
        self.create_j0_tab()  # 测量下悬盘的转动惯量
        self.create_j1_tab()  # 测量圆环的转动惯量  
        self.create_j3_tab()  # 测量圆盘的转动惯量
        self.create_j2_tab()  # 平行轴定理的验证
        
        # 绑定选项卡切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        """处理选项卡切换事件"""
        selected_tab = self.notebook.index(self.notebook.select())
        print(f"切换到选项卡: {selected_tab}")

    def create_j0_tab(self):
        """创建下悬盘转动惯量选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="下悬盘转动惯量")
        
        # 创建可滚动框架
        content_frame = self.create_scrollable_frame(tab)
        
        # H值显示
        h_frame = ttk.Frame(content_frame)
        h_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(h_frame, text="上下圆盘之间的距离H:").pack(side=tk.LEFT)
        ttk.Label(h_frame, textvariable=self.H_var).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(h_frame, text="cm").pack(side=tk.LEFT)
        
        # 固定参数部分
        param_frame = ttk.Frame(content_frame)
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行参数
        row1 = ttk.Frame(param_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="悬盘的直径D1:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1, text=f"{self.fixed_params['D1']} cm").pack(side=tk.LEFT, padx=(0, 30))
        ttk.Label(row1, text="悬盘质量M0:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1, text=f"{self.fixed_params['M0']} g").pack(side=tk.LEFT)
        
        # 测量数据部分
        data_frame = ttk.LabelFrame(content_frame, text="测量数据", padding=10)
        data_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 10周期摆动时间
        ttk.Label(data_frame, text="下悬盘10周期摆动时间(s)").pack(anchor=tk.W, pady=(0, 10))
        
        # 三次测量输入
        time_frame = ttk.Frame(data_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        for i in range(3):
            ttk.Label(time_frame, text=f"第{i+1}次:").grid(row=0, column=i*2, padx=(10, 5), sticky=tk.W)
            entry = ttk.Entry(time_frame, textvariable=self.data_records["t0_times"][i], width=10)
            entry.grid(row=0, column=i*2+1, padx=(0, 20), sticky=tk.W)
        
        # 平均值和周期
        result_frame = ttk.Frame(data_frame)
        result_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(result_frame, text="10周期平均值T0':").grid(row=0, column=0, padx=(10, 5), sticky=tk.W)
        ttk.Label(result_frame, textvariable=self.data_records["t0_avg"], width=10).grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(result_frame, text="平均周期T0:").grid(row=0, column=2, padx=(10, 5), sticky=tk.W)
        ttk.Label(result_frame, textvariable=self.data_records["T0"], width=10).grid(row=0, column=3, padx=(0, 10), sticky=tk.W)
        
        # 计算结果部分
        calc_frame = ttk.LabelFrame(content_frame, text="计算结果", padding=10)
        calc_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行结果
        row1_calc = ttk.Frame(calc_frame)
        row1_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row1_calc, text="下悬盘的转动惯量J0:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1_calc, textvariable=self.data_records["J0"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row1_calc, text="kg·m²").pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row1_calc, text="J0理论值:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1_calc, textvariable=self.data_records["J0_theory"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row1_calc, text="kg·m²").pack(side=tk.LEFT, padx=(0, 20))
        
        # 第二行结果
        row2_calc = ttk.Frame(calc_frame)
        row2_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row2_calc, text="误差:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row2_calc, textvariable=self.data_records["J0_error"], width=8).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(row2_calc, text="计算", command=self.calculate_j0).pack(side=tk.LEFT)

    def create_j1_tab(self):
        """创建圆环转动惯量选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="圆环转动惯量")
        
        # 创建可滚动框架
        content_frame = self.create_scrollable_frame(tab)
        
        # H值显示
        h_frame = ttk.Frame(content_frame)
        h_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(h_frame, text="上下圆盘之间的距离H:").pack(side=tk.LEFT)
        ttk.Label(h_frame, textvariable=self.H_var).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(h_frame, text="cm").pack(side=tk.LEFT)
        
        # 固定参数部分
        param_frame = ttk.LabelFrame(content_frame, text="固定参数", padding=10)
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 参数显示
        row1 = ttk.Frame(param_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="圆环质量M1:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1, text=f"{self.fixed_params['M1']} g").pack(side=tk.LEFT, padx=(0, 30))
        
        ttk.Label(row1, text="圆环的内径D内:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1, text=f"{self.fixed_params['D_inner']} cm").pack(side=tk.LEFT, padx=(0, 30))
        
        ttk.Label(row1, text="圆环的外径D外:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1, text=f"{self.fixed_params['D_outer']} cm").pack(side=tk.LEFT)
        
        # 测量数据部分
        data_frame = ttk.LabelFrame(content_frame, text="测量数据", padding=10)
        data_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 10周期摆动时间
        ttk.Label(data_frame, text="悬盘加圆环10周期摆动时间(s)").pack(anchor=tk.W, pady=(0, 10))
        
        # 三次测量输入
        time_frame = ttk.Frame(data_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        for i in range(3):
            ttk.Label(time_frame, text=f"第{i+1}次:").grid(row=0, column=i*2, padx=(10, 5), sticky=tk.W)
            entry = ttk.Entry(time_frame, textvariable=self.data_records["t1_times"][i], width=10)
            entry.grid(row=0, column=i*2+1, padx=(0, 20), sticky=tk.W)
        
        # 平均值和周期
        result_frame = ttk.Frame(data_frame)
        result_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(result_frame, text="10周期平均值T1':").grid(row=0, column=0, padx=(10, 5), sticky=tk.W)
        ttk.Label(result_frame, textvariable=self.data_records["t1_avg"], width=10).grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(result_frame, text="平均周期T1:").grid(row=0, column=2, padx=(10, 5), sticky=tk.W)
        ttk.Label(result_frame, textvariable=self.data_records["T1"], width=10).grid(row=0, column=3, padx=(0, 10), sticky=tk.W)
        
        # 计算结果部分
        calc_frame = ttk.LabelFrame(content_frame, text="计算结果", padding=10)
        calc_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行结果
        row1_calc = ttk.Frame(calc_frame)
        row1_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row1_calc, text="悬盘加圆环的转动惯量J1:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1_calc, textvariable=self.data_records["J1"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row1_calc, text="kg·m²").pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row1_calc, text="圆环的转动惯量JM1:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1_calc, textvariable=self.data_records["JM1"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row1_calc, text="kg·m²").pack(side=tk.LEFT, padx=(0, 20))
        
        # 第二行结果
        row2_calc = ttk.Frame(calc_frame)
        row2_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row2_calc, text="JM1理论值:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row2_calc, textvariable=self.data_records["JM1_theory"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row2_calc, text="kg·m²").pack(side=tk.LEFT, padx=(0, 20))
        
        # 第三行结果
        row3_calc = ttk.Frame(calc_frame)
        row3_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row3_calc, text="误差:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row3_calc, textvariable=self.data_records["JM1_error"], width=8).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(row3_calc, text="计算", command=self.calculate_j1).pack(side=tk.LEFT)

    def create_j3_tab(self):
        """创建圆盘转动惯量选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="圆盘转动惯量")
        
        # 创建可滚动框架
        content_frame = self.create_scrollable_frame(tab)
        
        # H值显示
        h_frame = ttk.Frame(content_frame)
        h_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(h_frame, text="上下圆盘之间的距离H:").pack(side=tk.LEFT)
        ttk.Label(h_frame, textvariable=self.H_var).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(h_frame, text="cm").pack(side=tk.LEFT)
        
        # 固定参数部分
        param_frame = ttk.LabelFrame(content_frame, text="固定参数", padding=10)
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 参数显示
        row1 = ttk.Frame(param_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="圆盘质量M3:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1, text=f"{self.fixed_params['M3']} g").pack(side=tk.LEFT, padx=(0, 30))
        
        ttk.Label(row1, text="直径D圆盘:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1, text=f"{self.fixed_params['D_disk']} cm").pack(side=tk.LEFT)
        
        # 测量数据部分
        data_frame = ttk.LabelFrame(content_frame, text="测量数据", padding=10)
        data_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 10周期摆动时间
        ttk.Label(data_frame, text="悬盘加圆盘10周期摆动时间(s)").pack(anchor=tk.W, pady=(0, 10))
        
        # 三次测量输入
        time_frame = ttk.Frame(data_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        for i in range(3):
            ttk.Label(time_frame, text=f"第{i+1}次:").grid(row=0, column=i*2, padx=(10, 5), sticky=tk.W)
            entry = ttk.Entry(time_frame, textvariable=self.data_records["t3_times"][i], width=10)
            entry.grid(row=0, column=i*2+1, padx=(0, 20), sticky=tk.W)
        
        # 平均值和周期
        result_frame = ttk.Frame(data_frame)
        result_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(result_frame, text="10周期平均值T3':").grid(row=0, column=0, padx=(10, 5), sticky=tk.W)
        ttk.Label(result_frame, textvariable=self.data_records["t3_avg"], width=10).grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(result_frame, text="平均周期T3:").grid(row=0, column=2, padx=(10, 5), sticky=tk.W)
        ttk.Label(result_frame, textvariable=self.data_records["T3"], width=10).grid(row=0, column=3, padx=(0, 10), sticky=tk.W)
        
        # 计算结果部分
        calc_frame = ttk.LabelFrame(content_frame, text="计算结果", padding=10)
        calc_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行结果
        row1_calc = ttk.Frame(calc_frame)
        row1_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row1_calc, text="悬盘加圆盘的转动惯量J3:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1_calc, textvariable=self.data_records["J3"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row1_calc, text="kg·m²").pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row1_calc, text="圆盘的转动惯量JM3:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1_calc, textvariable=self.data_records["JM3"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row1_calc, text="kg·m²").pack(side=tk.LEFT, padx=(0, 20))
        
        # 第二行结果
        row2_calc = ttk.Frame(calc_frame)
        row2_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row2_calc, text="JM3理论值:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row2_calc, textvariable=self.data_records["JM3_theory"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row2_calc, text="kg·m²").pack(side=tk.LEFT, padx=(0, 20))
        
        # 第三行结果
        row3_calc = ttk.Frame(calc_frame)
        row3_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row3_calc, text="误差:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row3_calc, textvariable=self.data_records["JM3_error"], width=8).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(row3_calc, text="计算", command=self.calculate_j3).pack(side=tk.LEFT)

    def create_j2_tab(self):
        """创建平行轴定理验证选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="平行轴定理验证")
        
        # 创建可滚动框架
        content_frame = self.create_scrollable_frame(tab)
        
        # H值显示
        h_frame = ttk.Frame(content_frame)
        h_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(h_frame, text="上下圆盘之间的距离H:").pack(side=tk.LEFT)
        ttk.Label(h_frame, textvariable=self.H_var).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(h_frame, text="cm").pack(side=tk.LEFT)
        
        # 固定参数部分 - 去掉边框
        param_frame = ttk.Frame(content_frame)
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行参数
        row1 = ttk.Frame(param_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="圆柱体的直径D小柱:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1, text=f"{self.fixed_params['D_cylinder']} cm").pack(side=tk.LEFT, padx=(0, 30))
        
        ttk.Label(row1, text="悬盘上刻线直径D槽:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1, textvariable=self.data_records["d_groove"]).pack(side=tk.LEFT, padx=(0, 30))
        
        ttk.Label(row1, text="圆柱体的总质量2M2:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1, text=f"{self.fixed_params['M2_total']} g").pack(side=tk.LEFT)
        
        # 第二行参数
        row2 = ttk.Frame(param_frame)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="两圆柱体的质心间距2d:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row2, textvariable=self.data_records["two_d"]).pack(side=tk.LEFT)
        
        # 测量数据部分 - 去掉边框
        data_frame = ttk.Frame(content_frame)
        data_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 10周期摆动时间
        ttk.Label(data_frame, text="悬盘加两圆柱10周期摆动时间(s)").pack(anchor=tk.W, pady=(0, 10))
        
        # 三次测量输入
        time_frame = ttk.Frame(data_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        for i in range(3):
            ttk.Label(time_frame, text=f"第{i+1}次:").grid(row=0, column=i*2, padx=(10, 5), sticky=tk.W)
            entry = ttk.Entry(time_frame, textvariable=self.data_records["t2_times"][i], width=10)
            entry.grid(row=0, column=i*2+1, padx=(0, 20), sticky=tk.W)
        
        # 平均值和周期
        result_frame = ttk.Frame(data_frame)
        result_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(result_frame, text="10周期平均值T2':").grid(row=0, column=0, padx=(10, 5), sticky=tk.W)
        ttk.Label(result_frame, textvariable=self.data_records["t2_avg"], width=10).grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(result_frame, text="平均周期T2:").grid(row=0, column=2, padx=(10, 5), sticky=tk.W)
        ttk.Label(result_frame, textvariable=self.data_records["T2"], width=10).grid(row=0, column=3, padx=(0, 10), sticky=tk.W)
        
        # 计算结果部分 - 去掉边框
        calc_frame = ttk.Frame(content_frame)
        calc_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行结果
        row1_calc = ttk.Frame(calc_frame)
        row1_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row1_calc, text="悬盘加两圆柱转动惯量J2'+J0:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1_calc, textvariable=self.data_records["J2_total"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row1_calc, text="kg·m²").pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row1_calc, text="两圆柱转动惯量J2':").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1_calc, textvariable=self.data_records["J2_prime"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row1_calc, text="kg·m²").pack(side=tk.LEFT, padx=(0, 20))
        
        # 第二行结果
        row2_calc = ttk.Frame(calc_frame)
        row2_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row2_calc, text="单圆柱转动惯量J2:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row2_calc, textvariable=self.data_records["J2_single"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row2_calc, text="kg·m²").pack(side=tk.LEFT, padx=(0, 20))
        
        # 第三行结果
        row3_calc = ttk.Frame(calc_frame)
        row3_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row3_calc, text="d实测值:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row3_calc, textvariable=self.data_records["d_measured"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row3_calc, text="m").pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row3_calc, text="d计算值:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row3_calc, textvariable=self.data_records["d_calculated"], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row3_calc, text="m").pack(side=tk.LEFT, padx=(0, 20))
        
        # 第四行结果
        row4_calc = ttk.Frame(calc_frame)
        row4_calc.pack(fill=tk.X, pady=5)
        ttk.Label(row4_calc, text="误差:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row4_calc, textvariable=self.data_records["d_error"], width=8).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(row4_calc, text="计算", command=self.calculate_j2).pack(side=tk.LEFT)

    def create_scrollable_frame(self, parent):
        """创建可滚动的框架"""
        # 创建Canvas和Scrollbar
        canvas = tk.Canvas(parent, height=400)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame
    
    def calculate_j0(self):
        """计算下悬盘的转动惯量"""
        try:
            # 检查数据记录是否已初始化
            if self.data_records is None:
                print("数据记录系统未初始化")
                return
            
            # 计算J0理论值：J0_theory = M0 * D1^2 / 8
            M0_kg = self.fixed_params['M0'] / 1000  # kg
            D1_m = self.fixed_params['D1'] / 100  # m
            J0_theory = M0_kg * (D1_m**2) / 8
            
            print(f"计算J0理论值:")
            print(f"  J0理论值 = M0 × D1² / 8")
            print(f"          = {M0_kg:.4f} × ({D1_m:.4f})² / 8")
            print(f"          = {M0_kg:.4f} × {D1_m**2:.6f} / 8")
            print(f"          = {J0_theory:.6f} kg·m²")
            
            # 更新固定参数中的理论值
            self.fixed_params['J0_theory'] = J0_theory
            self.data_records["J0_theory"].set(f"{J0_theory:.6f}")

            # 获取三次测量时间
            times = []
            for i in range(3):
                time_str = self.data_records["t0_times"][i].get().strip()
                if time_str:
                    times.append(float(time_str))
            
            if len(times) < 1:
                print("请至少输入一次测量时间")
                return
                
            # 计算10周期平均值
            t0_avg = sum(times) / len(times)
            self.data_records["t0_avg"].set(f"{t0_avg:.3f}")
            
            # 计算平均周期
            T0 = t0_avg / 10
            self.data_records["T0"].set(f"{T0:.3f}")
            
            # 计算转动惯量 J0 = g*r*R*M0*T0^2/(4*π^2*H)
            # 注意单位转换：cm -> m, g -> kg
            r = self.fixed_params['r'] / 100  # m
            R = self.fixed_params['R'] / 100  # m
            M0 = self.fixed_params['M0'] / 1000  # kg
            H = self.fixed_params['H'] / 100  # m
            g = self.fixed_params['g']
            
            # 显示计算过程
            print("\n=== 下悬盘转动惯量计算过程 ===")
            print(f"输入数据:")
            print(f"  测量时间: {times}")
            print(f"  10周期平均值 T0' = {t0_avg:.3f} s")
            print(f"  平均周期 T0 = T0' / 10 = {t0_avg:.3f} / 10 = {T0:.3f} s")
            print(f"  上圆盘悬点到盘心距离 r = {self.fixed_params['r']} cm = {r:.4f} m")
            print(f"  下圆盘悬点到盘心距离 R = {self.fixed_params['R']} cm = {R:.4f} m")
            print(f"  悬盘质量 M0 = {self.fixed_params['M0']} g = {M0:.4f} kg")
            print(f"  上下圆盘距离 H = {self.fixed_params['H']} cm = {H:.4f} m")
            print(f"  重力加速度 g = {g} m/s²")
            print(f"  π = {np.pi:.6f}")
            
            # 分步计算
            numerator = g * r * R * M0 * T0**2
            denominator = 4 * np.pi**2 * H
            
            print(f"\n计算过程:")
            print(f"  分子 = g × r × R × M0 × T0²")
            print(f"       = {g} × {r:.4f} × {R:.4f} × {M0:.4f} × ({T0:.3f})²")
            print(f"       = {g} × {r:.4f} × {R:.4f} × {M0:.4f} × {T0**2:.6f}")
            print(f"       = {numerator:.8f}")
            
            print(f"  分母 = 4 × π² × H")
            print(f"       = 4 × ({np.pi:.6f})² × {H:.4f}")
            print(f"       = 4 × {np.pi**2:.6f} × {H:.4f}")
            print(f"       = {denominator:.6f}")
            
            J0 = numerator / denominator
            print(f"  J0 = 分子 / 分母 = {numerator:.8f} / {denominator:.6f} = {J0:.6f} kg·m²")
            
            self.data_records["J0"].set(f"{J0:.6f}")
            
            # 计算误差
            J0_theory = self.fixed_params['J0_theory']
            error = abs(J0 - J0_theory) / J0_theory * 100
            print(f"  理论值 J0理论 = {J0_theory:.6f} kg·m²")
            print(f"  误差 = |{J0:.6f} - {J0_theory:.6f}| / {J0_theory:.6f} × 100% = {error:.2f}%")
            
            self.data_records["J0_error"].set(f"{error:.2f}%")
            print("=== 计算完成 ===\n")
            
        except ValueError as e:
            print(f"计算J0时出错: {e}")

    def calculate_j1(self):
        """计算圆环的转动惯量"""
        try:
            # 检查数据记录是否已初始化
            if self.data_records is None:
                print("数据记录系统未初始化")
                return
            
            # 计算JM1理论值：JM1_theory = M1 * (D内^2 + D外^2) / 8
            M1_kg = self.fixed_params['M1'] / 1000  # kg
            D_inner_m = self.fixed_params['D_inner'] / 100  # m
            D_outer_m = self.fixed_params['D_outer'] / 100  # m
            JM1_theory = M1_kg * (D_inner_m**2 + D_outer_m**2) / 8
            
            print(f"计算JM1理论值:")
            print(f"  JM1理论值 = M1 × (D内² + D外²) / 8")
            print(f"           = {M1_kg:.4f} × (({D_inner_m:.4f})² + ({D_outer_m:.4f})²) / 8")
            print(f"           = {M1_kg:.4f} × ({D_inner_m**2:.6f} + {D_outer_m**2:.6f}) / 8")
            print(f"           = {M1_kg:.4f} × {D_inner_m**2 + D_outer_m**2:.6f} / 8")
            print(f"           = {JM1_theory:.6f} kg·m²")
            
            # 更新固定参数中的理论值
            self.fixed_params['JM1_theory'] = JM1_theory
            # 新增：更新显示变量
            self.data_records["JM1_theory"].set(f"{JM1_theory:.6f}")

            # 获取三次测量时间
            times = []
            for i in range(3):
                time_str = self.data_records["t1_times"][i].get().strip()
                if time_str:
                    times.append(float(time_str))
            
            if len(times) < 1:
                print("请至少输入一次测量时间")
                return
                
            # 计算10周期平均值
            t1_avg = sum(times) / len(times)
            self.data_records["t1_avg"].set(f"{t1_avg:.3f}")
            
            # 计算平均周期
            T1 = t1_avg / 10
            self.data_records["T1"].set(f"{T1:.3f}")
            
            # 计算悬盘加圆环的转动惯量 J1 = g*R*r*(M0+M1)*T1^2/(4*π^2*H)
            r = self.fixed_params['r'] / 100  # m
            R = self.fixed_params['R'] / 100  # m
            M0 = self.fixed_params['M0'] / 1000  # kg
            M1 = self.fixed_params['M1'] / 1000  # kg
            H = self.fixed_params['H'] / 100  # m
            g = self.fixed_params['g']
            
            # 显示计算过程
            print("\n=== 圆环转动惯量计算过程 ===")
            print(f"输入数据:")
            print(f"  测量时间: {times}")
            print(f"  10周期平均值 T1' = {t1_avg:.3f} s")
            print(f"  平均周期 T1 = T1' / 10 = {t1_avg:.3f} / 10 = {T1:.3f} s")
            print(f"  悬盘质量 M0 = {self.fixed_params['M0']} g = {M0:.4f} kg")
            print(f"  圆环质量 M1 = {self.fixed_params['M1']} g = {M1:.4f} kg")
            print(f"  总质量 M0 + M1 = {M0:.4f} + {M1:.4f} = {M0+M1:.4f} kg")
            
            # 分步计算 J1
            numerator = g * r * R * (M0 + M1) * T1**2
            denominator = 4 * np.pi**2 * H
            
            print(f"\n计算悬盘加圆环的转动惯量 J1:")
            print(f"  分子 = g × r × R × (M0 + M1) × T1²")
            print(f"       = {g} × {r:.4f} × {R:.4f} × {M0+M1:.4f} × ({T1:.3f})²")
            print(f"       = {g} × {r:.4f} × {R:.4f} × {M0+M1:.4f} × {T1**2:.6f}")
            print(f"       = {numerator:.8f}")
            
            print(f"  分母 = 4 × π² × H = {denominator:.6f}")
            
            J1 = numerator / denominator
            print(f"  J1 = 分子 / 分母 = {numerator:.8f} / {denominator:.6f} = {J1:.6f} kg·m²")
            
            self.data_records["J1"].set(f"{J1:.6f}")
            
            # 计算圆环的转动惯量 JM1 = J1 - J0
            J0_str = self.data_records["J0"].get()
            if J0_str:
                J0 = float(J0_str)
                JM1 = J1 - J0
                print(f"\n计算圆环的转动惯量 JM1:")
                print(f"  JM1 = J1 - J0 = {J1:.6f} - {J0:.6f} = {JM1:.6f} kg·m²")
                
                self.data_records["JM1"].set(f"{JM1:.6f}")
                
                # 计算误差
                JM1_theory = self.fixed_params['JM1_theory']
                error = abs(JM1 - JM1_theory) / JM1_theory * 100
                print(f"  理论值 JM1理论 = {JM1_theory:.6f} kg·m²")
                print(f"  误差 = |{JM1:.6f} - {JM1_theory:.6f}| / {JM1_theory:.6f} × 100% = {error:.2f}%")
                
                self.data_records["JM1_error"].set(f"{error:.2f}%")
            else:
                print("警告：请先计算下悬盘的转动惯量 J0")
            
            print("=== 计算完成 ===\n")
            
        except ValueError as e:
            print(f"计算J1时出错: {e}")

    def calculate_j3(self):
        """计算圆盘的转动惯量"""
        try:
            # 检查数据记录是否已初始化
            if self.data_records is None:
                print("数据记录系统未初始化")
                return
            
            # 计算JM3理论值：JM3_theory = M3 * D圆盘^2 / 8
            M3_kg = self.fixed_params['M3'] / 1000  # kg
            D_disk_m = self.fixed_params['D_disk'] / 100  # m
            JM3_theory = M3_kg * (D_disk_m**2) / 8
            
            print(f"计算JM3理论值:")
            print(f"  JM3理论值 = M3 × D圆盘² / 8")
            print(f"           = {M3_kg:.4f} × ({D_disk_m:.4f})² / 8")
            print(f"           = {M3_kg:.4f} × {D_disk_m**2:.6f} / 8")
            print(f"           = {JM3_theory:.6f} kg·m²")
            
            # 更新固定参数中的理论值
            self.fixed_params['JM3_theory'] = JM3_theory

            # 新增：更新显示变量
            self.data_records["JM3_theory"].set(f"{JM3_theory:.6f}")

            # 获取三次测量时间
            times = []
            for i in range(3):
                time_str = self.data_records["t3_times"][i].get().strip()
                if time_str:
                    times.append(float(time_str))
            
            if len(times) < 1:
                print("请至少输入一次测量时间")
                return
                
            # 计算10周期平均值
            t3_avg = sum(times) / len(times)
            self.data_records["t3_avg"].set(f"{t3_avg:.3f}")
            
            # 计算平均周期
            T3 = t3_avg / 10
            self.data_records["T3"].set(f"{T3:.3f}")
            
            # 计算悬盘加圆盘的转动惯量 J3 = g*R*r*(M0+M3)*T3^2/(4*π^2*H)
            r = self.fixed_params['r'] / 100  # m
            R = self.fixed_params['R'] / 100  # m
            M0 = self.fixed_params['M0'] / 1000  # kg
            M3 = self.fixed_params['M3'] / 1000  # kg
            H = self.fixed_params['H'] / 100  # m
            g = self.fixed_params['g']
            
            # 显示计算过程
            print("\n=== 圆盘转动惯量计算过程 ===")
            print(f"输入数据:")
            print(f"  测量时间: {times}")
            print(f"  10周期平均值 T3' = {t3_avg:.3f} s")
            print(f"  平均周期 T3 = T3' / 10 = {t3_avg:.3f} / 10 = {T3:.3f} s")
            print(f"  悬盘质量 M0 = {self.fixed_params['M0']} g = {M0:.4f} kg")
            print(f"  圆盘质量 M3 = {self.fixed_params['M3']} g = {M3:.4f} kg")
            print(f"  总质量 M0 + M3 = {M0:.4f} + {M3:.4f} = {M0+M3:.4f} kg")
            
            # 分步计算 J3
            numerator = g * r * R * (M0 + M3) * T3**2
            denominator = 4 * np.pi**2 * H
            
            print(f"\n计算悬盘加圆盘的转动惯量 J3:")
            print(f"  分子 = g × r × R × (M0 + M3) × T3²")
            print(f"       = {g} × {r:.4f} × {R:.4f} × {M0+M3:.4f} × ({T3:.3f})²")
            print(f"       = {g} × {r:.4f} × {R:.4f} × {M0+M3:.4f} × {T3**2:.6f}")
            print(f"       = {numerator:.8f}")
            
            print(f"  分母 = 4 × π² × H = {denominator:.6f}")
            
            J3 = numerator / denominator
            print(f"  J3 = 分子 / 分母 = {numerator:.8f} / {denominator:.6f} = {J3:.6f} kg·m²")
            
            self.data_records["J3"].set(f"{J3:.6f}")
            
            # 计算圆盘的转动惯量 JM3 = J3 - J0
            J0_str = self.data_records["J0"].get()
            if J0_str:
                J0 = float(J0_str)
                JM3 = J3 - J0
                print(f"\n计算圆盘的转动惯量 JM3:")
                print(f"  JM3 = J3 - J0 = {J3:.6f} - {J0:.6f} = {JM3:.6f} kg·m²")
                
                self.data_records["JM3"].set(f"{JM3:.6f}")
                
                # 计算误差
                JM3_theory = self.fixed_params['JM3_theory']
                error = abs(JM3 - JM3_theory) / JM3_theory * 100
                print(f"  理论值 JM3理论 = {JM3_theory:.6f} kg·m²")
                print(f"  误差 = |{JM3:.6f} - {JM3_theory:.6f}| / {JM3_theory:.6f} × 100% = {error:.2f}%")
                
                self.data_records["JM3_error"].set(f"{error:.2f}%")
            else:
                print("警告：请先计算下悬盘的转动惯量 J0")
            
            print("=== 计算完成 ===\n")
            
        except ValueError as e:
            print(f"计算J3时出错: {e}")

    def calculate_j2(self):
        """计算平行轴定理验证相关参数"""
        try:
            # 检查数据记录是否已初始化
            if self.data_records is None:
                print("数据记录系统未初始化")
                return
                
            # 获取三次测量时间
            times = []
            for i in range(3):
                time_str = self.data_records["t2_times"][i].get().strip()
                if time_str:
                    times.append(float(time_str))
            
            if len(times) < 1:
                print("请至少输入一次测量时间")
                return
                
            # 计算10周期平均值
            t2_avg = sum(times) / len(times)
            self.data_records["t2_avg"].set(f"{t2_avg:.3f}")
            
            # 计算平均周期
            T2 = t2_avg / 10
            self.data_records["T2"].set(f"{T2:.3f}")
            
            # 计算悬盘加两圆柱转动惯量 J2_total = g*R*r*(M0+2M2)*T2^2/(4*π^2*H)
            r = self.fixed_params['r'] / 100  # m
            R = self.fixed_params['R'] / 100  # m
            M0 = self.fixed_params['M0'] / 1000  # kg
            M2_total = self.fixed_params['M2_total'] / 1000  # kg (两圆柱总质量)
            H = self.fixed_params['H'] / 100  # m
            g = self.fixed_params['g']
            
            # 显示计算过程
            print("\n=== 平行轴定理验证计算过程 ===")
            print(f"输入数据:")
            print(f"  测量时间: {times}")
            print(f"  10周期平均值 T2' = {t2_avg:.3f} s")
            print(f"  平均周期 T2 = T2' / 10 = {t2_avg:.3f} / 10 = {T2:.3f} s")
            print(f"  悬盘质量 M0 = {self.fixed_params['M0']} g = {M0:.4f} kg")
            print(f"  两圆柱总质量 2M2 = {self.fixed_params['M2_total']} g = {M2_total:.4f} kg")
            
            # 计算悬盘加两圆柱转动惯量
            numerator = g * r * R * (M0 + M2_total) * T2**2
            denominator = 4 * np.pi**2 * H
            J2_total = numerator / denominator
            
            print(f"\n计算悬盘加两圆柱转动惯量 J2'+J0:")
            print(f"  J2'+J0 = g × r × R × (M0 + 2M2) × T2² / (4 × π² × H)")
            print(f"          = {g} × {r:.4f} × {R:.4f} × {M0+M2_total:.4f} × ({T2:.3f})² / (4 × {np.pi**2:.6f} × {H:.4f})")
            print(f"          = {J2_total:.6f} kg·m²")
            
            self.data_records["J2_total"].set(f"{J2_total:.6f}")
            
            # 计算两圆柱转动惯量 J2' = J2_total - J0
            J0_str = self.data_records["J0"].get()
            if J0_str:
                J0 = float(J0_str)
                J2_prime = J2_total - J0
                print(f"\n计算两圆柱转动惯量 J2':")
                print(f"  J2' = (J2'+J0) - J0 = {J2_total:.6f} - {J0:.6f} = {J2_prime:.6f} kg·m²")
                
                self.data_records["J2_prime"].set(f"{J2_prime:.6f}")
                
                # 计算单圆柱转动惯量 J2 = M2 * D_cylinder^2 / 8
                M2_single = M2_total / 2  # 单个圆柱质量
                D_cylinder = self.fixed_params['D_cylinder'] / 100  # m
                J2_single_val = M2_single * (D_cylinder**2) / 8
                
                print(f"\n计算单圆柱转动惯量 J2:")
                print(f"  J2 = M2 × D小柱² / 8")
                print(f"     = {M2_single:.4f} × ({D_cylinder:.4f})² / 8")
                print(f"     = {M2_single:.4f} × {D_cylinder**2:.6f} / 8")
                print(f"     = {J2_single_val:.6f} kg·m²")
                
                self.data_records["J2_single"].set(f"{J2_single_val:.6f}")
                
                if J2_prime > 0 and J2_single_val > 0:
                    d_calculated = np.sqrt((J2_prime/2 - J2_single_val) / M2_single)
                    
                    print(f"计算d计算值:")
                    print(f"  d = √[(J2'/2 - J2) / M2]")
                    print(f"    = √[({J2_prime/2:.6f} - {J2_single_val:.6f}) / {M2_single:.4f}]")
                    print(f"    = √[{(J2_prime/2 - J2_single_val):.6f} / {M2_single:.4f}]")
                    print(f"    = √[{(J2_prime/2 - J2_single_val)/M2_single:.6f}]")
                    print(f"    = {d_calculated:.5f} m")
                    
                    # 更新固定参数中的计算值
                    self.fixed_params['d_calculated'] = d_calculated
                    # 新增：更新显示变量
                    self.data_records["d_calculated"].set(f"{d_calculated:.5f}")
                else:
                    d_calculated = 0
                    print("警告：无法计算d值，请先完成J2'和J2的计算")
                
                # 使用固定的d实测值
                d_measured = self.fixed_params['d_measured']
                self.data_records["d_measured"].set(f"{d_measured:.3f}")
                
                # 计算误差（使用d计算值和d实测值）
                d_error = abs(d_calculated - d_measured) / d_measured * 100 if d_measured > 0 else 0
                print(f"  d实测值 = {d_measured:.5f} m")
                print(f"  误差 = |{d_calculated:.5f} - {d_measured:.3f}| / {d_measured:.3f} × 100% = {d_error:.2f}%")
                
                self.data_records["d_error"].set(f"{d_error:.2f}%")
            else:
                print("警告：请先计算下悬盘的转动惯量 J0")
            
            print("=== 计算完成 ===\n")
            
        except ValueError as e:
            print(f"计算J2时出错: {e}")
        except Exception as e:
            print(f"计算过程中出现错误: {e}")

    def import_data(self):
        """导入数据"""
        print("导入数据功能待实现")
        # 这里可以添加文件选择对话框和数据导入逻辑

    def import_data(self):
        """从Excel导入数据 - 按照四个实验部分组织"""
        try:
            # 创建文件选择对话框
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="选择要导入的Excel文件"
            )
            
            if not file_path:
                return
                
            # 检查文件是否存在
            if not os.path.exists(file_path):
                messagebox.showerror("错误", "文件不存在")
                return
            
            # 读取Excel文件
            # === 工作表1: 测量下悬盘的转动惯量 ===
            try:
                df_j0 = pd.read_excel(file_path, sheet_name='下悬盘转动惯量')
                if not df_j0.empty:
                    for _, row in df_j0.iterrows():
                        if pd.notna(row['数值']):
                            value_str = str(row['数值'])
                            param_name = row['参数名称']
                            
                            if param_name == '10周期时间第1次':
                                self.data_records["t0_times"][0].set(value_str)
                            elif param_name == '10周期时间第2次':
                                self.data_records["t0_times"][1].set(value_str)
                            elif param_name == '10周期时间第3次':
                                self.data_records["t0_times"][2].set(value_str)
                            elif param_name == '10周期平均值T0\'':
                                self.data_records["t0_avg"].set(value_str)
                            elif param_name == '平均周期T0':
                                self.data_records["T0"].set(value_str)
                            elif param_name == '下悬盘转动惯量J0':
                                self.data_records["J0"].set(value_str)
                            elif param_name == 'J0理论值':  # 新增：导入J0理论值
                                self.data_records["J0_theory"].set(value_str)
                                # 同时更新fixed_params中的值
                                try:
                                    self.fixed_params['J0_theory'] = float(value_str)
                                except ValueError:
                                    pass
                            elif param_name == '误差':
                                self.data_records["J0_error"].set(value_str)
            except Exception as e:
                print(f"读取下悬盘转动惯量数据时出错: {e}")
            
            # === 工作表2: 测量圆环的转动惯量 ===
            try:
                df_j1 = pd.read_excel(file_path, sheet_name='圆环转动惯量')
                if not df_j1.empty:
                    for _, row in df_j1.iterrows():
                        if pd.notna(row['数值']):
                            value_str = str(row['数值'])
                            param_name = row['参数名称']
                            
                            if param_name == '10周期时间第1次':
                                self.data_records["t1_times"][0].set(value_str)
                            elif param_name == '10周期时间第2次':
                                self.data_records["t1_times"][1].set(value_str)
                            elif param_name == '10周期时间第3次':
                                self.data_records["t1_times"][2].set(value_str)
                            elif param_name == '10周期平均值T1\'':
                                self.data_records["t1_avg"].set(value_str)
                            elif param_name == '平均周期T1':
                                self.data_records["T1"].set(value_str)
                            elif param_name == '悬盘加圆环转动惯量J1':
                                self.data_records["J1"].set(value_str)
                            elif param_name == '圆环转动惯量JM1':
                                self.data_records["JM1"].set(value_str)
                            elif param_name == 'JM1理论值':  # 新增：导入JM1理论值
                                self.data_records["JM1_theory"].set(value_str)
                                # 同时更新fixed_params中的值
                                try:
                                    self.fixed_params['JM1_theory'] = float(value_str)
                                except ValueError:
                                    pass
                            elif param_name == '误差':
                                self.data_records["JM1_error"].set(value_str)
            except Exception as e:
                print(f"读取圆环转动惯量数据时出错: {e}")
            
            # === 工作表3: 测量悬盘的转动惯量 ===
            try:
                df_j3 = pd.read_excel(file_path, sheet_name='圆盘转动惯量')
                if not df_j3.empty:
                    for _, row in df_j3.iterrows():
                        if pd.notna(row['数值']):
                            value_str = str(row['数值'])
                            param_name = row['参数名称']
                            
                            if param_name == '10周期时间第1次':
                                self.data_records["t3_times"][0].set(value_str)
                            elif param_name == '10周期时间第2次':
                                self.data_records["t3_times"][1].set(value_str)
                            elif param_name == '10周期时间第3次':
                                self.data_records["t3_times"][2].set(value_str)
                            elif param_name == '10周期平均值T3\'':
                                self.data_records["t3_avg"].set(value_str)
                            elif param_name == '平均周期T3':
                                self.data_records["T3"].set(value_str)
                            elif param_name == '悬盘加圆盘转动惯量J3':
                                self.data_records["J3"].set(value_str)
                            elif param_name == '圆盘转动惯量JM3':
                                self.data_records["JM3"].set(value_str)
                            elif param_name == 'JM3理论值':  # 新增：导入JM3理论值
                                self.data_records["JM3_theory"].set(value_str)
                                # 同时更新fixed_params中的值
                                try:
                                    self.fixed_params['JM3_theory'] = float(value_str)
                                except ValueError:
                                    pass
                            elif param_name == '误差':
                                self.data_records["JM3_error"].set(value_str)
            except Exception as e:
                print(f"读取圆盘转动惯量数据时出错: {e}")
            
            # === 工作表4: 平行轴定理的验证 ===
            try:
                df_j2 = pd.read_excel(file_path, sheet_name='平行轴定理验证')
                if not df_j2.empty:
                    for _, row in df_j2.iterrows():
                        if pd.notna(row['数值']):
                            value_str = str(row['数值'])
                            param_name = row['参数名称']
                            
                            if param_name == '10周期时间第1次':
                                self.data_records["t2_times"][0].set(value_str)
                            elif param_name == '10周期时间第2次':
                                self.data_records["t2_times"][1].set(value_str)
                            elif param_name == '10周期时间第3次':
                                self.data_records["t2_times"][2].set(value_str)
                            elif param_name == '10周期平均值T2\'':
                                self.data_records["t2_avg"].set(value_str)
                            elif param_name == '平均周期T2':
                                self.data_records["T2"].set(value_str)
                            elif param_name == '悬盘加两圆柱转动惯量J2\'+J0':
                                self.data_records["J2_total"].set(value_str)
                            elif param_name == '两圆柱转动惯量J2\'':
                                self.data_records["J2_prime"].set(value_str)
                            elif param_name == '单圆柱转动惯量J2':
                                self.data_records["J2_single"].set(value_str)
                            elif param_name == 'd实测值':
                                self.data_records["d_measured"].set(value_str)
                            elif param_name == 'd计算值':  # 新增：导入d计算值
                                self.data_records["d_calculated"].set(value_str)
                                # 同时更新fixed_params中的值
                                try:
                                    self.fixed_params['d_calculated'] = float(value_str)
                                except ValueError:
                                    pass
                            elif param_name == '误差':
                                self.data_records["d_error"].set(value_str)
            except Exception as e:
                print(f"读取平行轴定理验证数据时出错: {e}")
            
            print(f"数据已从 {file_path} 导入")
            messagebox.showinfo("导入成功", "数据导入完成！")
            
        except ImportError:
            messagebox.showerror("错误", "请安装pandas和openpyxl库以支持Excel导入")
        except Exception as e:
            messagebox.showerror("错误", f"导入数据时出错: {e}")

    def export_data(self):
        """导出数据到Excel - 按照四个实验部分组织"""
        try:
            # 创建文件保存对话框
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="导出实验数据"
            )
            
            if not file_path:
                return
                
            # 准备数据 - 创建4个工作表对应四个实验部分
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                
                # === 工作表1: 测量下悬盘的转动惯量 ===
                j0_data = []
                # 固定参数部分
                j0_data.extend([
                    {  '参数名称': '上圆盘悬点到盘心距离r', '数值': self.fixed_params['r'], '单位': 'cm'},
                    {  '参数名称': '下圆盘悬点到盘心距离R', '数值': self.fixed_params['R'], '单位': 'cm'},
                    {  '参数名称': '悬盘直径D1', '数值': self.fixed_params['D1'], '单位': 'cm'},
                    {  '参数名称': '上下圆盘距离H', '数值': self.fixed_params['H'], '单位': 'cm'},
                    {  '参数名称': '悬盘质量M0', '数值': self.fixed_params['M0'], '单位': 'g'},
                    {  '参数名称': '重力加速度g', '数值': self.fixed_params['g'], '单位': 'm/s²'},
                    {  '参数名称': 'J0理论值', '数值': self.fixed_params['J0_theory'], '单位': 'kg·m²'}
                ])
                # 测量数据部分
                j0_data.extend([
                    {  '参数名称': '10周期时间第1次', '数值': self.data_records["t0_times"][0].get(), '单位': 's'},
                    {  '参数名称': '10周期时间第2次', '数值': self.data_records["t0_times"][1].get(), '单位': 's'},
                    {  '参数名称': '10周期时间第3次', '数值': self.data_records["t0_times"][2].get(), '单位': 's'},
                    {  '参数名称': '10周期平均值T0\'', '数值': self.data_records["t0_avg"].get(), '单位': 's'},
                    {  '参数名称': '平均周期T0', '数值': self.data_records["T0"].get(), '单位': 's'},
                    {  '参数名称': '下悬盘转动惯量J0', '数值': self.data_records["J0"].get(), '单位': 'kg·m²'},
                    {  '参数名称': '误差', '数值': self.data_records["J0_error"].get(), '单位': '%'}
                ])
                df_j0 = pd.DataFrame(j0_data)
                df_j0.to_excel(writer, sheet_name='下悬盘转动惯量', index=False)
                
                # === 工作表2: 测量圆环的转动惯量 ===
                j1_data = []
                # 固定参数部分
                j1_data.extend([
                    {  '参数名称': '圆环质量M1', '数值': self.fixed_params['M1'], '单位': 'g'},
                    {  '参数名称': '圆环内径D内', '数值': self.fixed_params['D_inner'], '单位': 'cm'},
                    {  '参数名称': '圆环外径D外', '数值': self.fixed_params['D_outer'], '单位': 'cm'},
                    {  '参数名称': 'JM1理论值', '数值': self.fixed_params['JM1_theory'], '单位': 'kg·m²'}
                ])
                # 测量数据部分
                j1_data.extend([
                    {  '参数名称': '10周期时间第1次', '数值': self.data_records["t1_times"][0].get(), '单位': 's'},
                    {  '参数名称': '10周期时间第2次', '数值': self.data_records["t1_times"][1].get(), '单位': 's'},
                    {  '参数名称': '10周期时间第3次', '数值': self.data_records["t1_times"][2].get(), '单位': 's'},
                    {  '参数名称': '10周期平均值T1\'', '数值': self.data_records["t1_avg"].get(), '单位': 's'},
                    {  '参数名称': '平均周期T1', '数值': self.data_records["T1"].get(), '单位': 's'},
                    {  '参数名称': '悬盘加圆环转动惯量J1', '数值': self.data_records["J1"].get(), '单位': 'kg·m²'},
                    {  '参数名称': '圆环转动惯量JM1', '数值': self.data_records["JM1"].get(), '单位': 'kg·m²'},
                    {  '参数名称': '误差', '数值': self.data_records["JM1_error"].get(), '单位': '%'}
                ])
                df_j1 = pd.DataFrame(j1_data)
                df_j1.to_excel(writer, sheet_name='圆环转动惯量', index=False)
                
                # === 工作表3: 测量悬盘的转动惯量 ===
                j3_data = []
                # 固定参数部分
                j3_data.extend([
                    {  '参数名称': '圆盘质量M3', '数值': self.fixed_params['M3'], '单位': 'g'},
                    {  '参数名称': '直径D圆盘', '数值': self.fixed_params['D_disk'], '单位': 'cm'},
                    {  '参数名称': 'JM3理论值', '数值': self.fixed_params['JM3_theory'], '单位': 'kg·m²'}
                ])
                # 测量数据部分
                j3_data.extend([
                    {  '参数名称': '10周期时间第1次', '数值': self.data_records["t3_times"][0].get(), '单位': 's'},
                    {  '参数名称': '10周期时间第2次', '数值': self.data_records["t3_times"][1].get(), '单位': 's'},
                    {  '参数名称': '10周期时间第3次', '数值': self.data_records["t3_times"][2].get(), '单位': 's'},
                    {  '参数名称': '10周期平均值T3\'', '数值': self.data_records["t3_avg"].get(), '单位': 's'},
                    {  '参数名称': '平均周期T3', '数值': self.data_records["T3"].get(), '单位': 's'},
                    {  '参数名称': '悬盘加圆盘转动惯量J3', '数值': self.data_records["J3"].get(), '单位': 'kg·m²'},
                    {  '参数名称': '圆盘转动惯量JM3', '数值': self.data_records["JM3"].get(), '单位': 'kg·m²'},
                    {  '参数名称': '误差', '数值': self.data_records["JM3_error"].get(), '单位': '%'}
                ])
                df_j3 = pd.DataFrame(j3_data)
                df_j3.to_excel(writer, sheet_name='圆盘转动惯量', index=False)
                
                # === 工作表4: 平行轴定理的验证 ===
                j2_data = []
                # 固定参数部分
                j2_data.extend([
                    {  '参数名称': '圆柱体直径D小柱', '数值': self.fixed_params['D_cylinder'], '单位': 'cm'},
                    {  '参数名称': '悬盘上刻线直径D槽', '数值': self.fixed_params['D_groove'], '单位': 'cm'},
                    {  '参数名称': '两圆柱总质量2M2', '数值': self.fixed_params['M2_total'], '单位': 'g'},
                    {  '参数名称': 'd实测值', '数值': self.fixed_params['d_measured'], '单位': 'm'}
                ])
                # 测量数据部分
                j2_data.extend([
                    {  '参数名称': '10周期时间第1次', '数值': self.data_records["t2_times"][0].get(), '单位': 's'},
                    {  '参数名称': '10周期时间第2次', '数值': self.data_records["t2_times"][1].get(), '单位': 's'},
                    {  '参数名称': '10周期时间第3次', '数值': self.data_records["t2_times"][2].get(), '单位': 's'},
                    {  '参数名称': '10周期平均值T2\'', '数值': self.data_records["t2_avg"].get(), '单位': 's'},
                    {  '参数名称': '平均周期T2', '数值': self.data_records["T2"].get(), '单位': 's'},
                    {  '参数名称': '悬盘加两圆柱转动惯量J2\'+J0', '数值': self.data_records["J2_total"].get(), '单位': 'kg·m²'},
                    {  '参数名称': '两圆柱转动惯量J2\'', '数值': self.data_records["J2_prime"].get(), '单位': 'kg·m²'},
                    {  '参数名称': '单圆柱转动惯量J2', '数值': self.data_records["J2_single"].get(), '单位': 'kg·m²'},
                    {  '参数名称': 'd计算值', '数值': self.fixed_params['d_calculated'], '单位': 'm'},
                    {  '参数名称': '误差', '数值': self.data_records["d_error"].get(), '单位': '%'}
                ])
                df_j2 = pd.DataFrame(j2_data)
                df_j2.to_excel(writer, sheet_name='平行轴定理验证', index=False)
                
            print(f"所有数据已导出到: {file_path}")
            messagebox.showinfo("导出成功", f"数据已成功导出到:\n{file_path}")
            
        except ImportError:
            messagebox.showerror("错误", "请安装pandas和openpyxl库以支持Excel导出")
        except Exception as e:
            messagebox.showerror("错误", f"导出数据时出错: {e}")

    def import_data(self):
        """从Excel导入数据 - 按照四个实验部分组织"""
        try:
            # 创建文件选择对话框
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="选择要导入的Excel文件"
            )
            
            if not file_path:
                return
                
            # 检查文件是否存在
            if not os.path.exists(file_path):
                messagebox.showerror("错误", "文件不存在")
                return
            
            # 读取Excel文件
            # === 工作表1: 测量下悬盘的转动惯量 ===
            try:
                df_j0 = pd.read_excel(file_path, sheet_name='下悬盘转动惯量')
                if not df_j0.empty:
                    for _, row in df_j0.iterrows():
                        if pd.notna(row['数值']):
                            value_str = str(row['数值'])
                            param_name = row['参数名称']
                            
                            if param_name == '10周期时间第1次':
                                self.data_records["t0_times"][0].set(value_str)
                            elif param_name == '10周期时间第2次':
                                self.data_records["t0_times"][1].set(value_str)
                            elif param_name == '10周期时间第3次':
                                self.data_records["t0_times"][2].set(value_str)
                            elif param_name == '10周期平均值T0\'':
                                self.data_records["t0_avg"].set(value_str)
                            elif param_name == '平均周期T0':
                                self.data_records["T0"].set(value_str)
                            elif param_name == '下悬盘转动惯量J0':
                                self.data_records["J0"].set(value_str)
                            elif param_name == 'J0理论值':  # 新增：导入J0理论值
                                try:
                                    # 保留6位小数
                                    value_float = float(value_str)
                                    formatted_value = f"{value_float:.6f}"
                                    self.data_records["J0_theory"].set(formatted_value)
                                    # 同时更新fixed_params中的值
                                    self.fixed_params['J0_theory'] = value_float
                                except ValueError:
                                    pass
                            elif param_name == '误差':
                                self.data_records["J0_error"].set(value_str)
            except Exception as e:
                print(f"读取下悬盘转动惯量数据时出错: {e}")
            
            # === 工作表2: 测量圆环的转动惯量 ===
            try:
                df_j1 = pd.read_excel(file_path, sheet_name='圆环转动惯量')
                if not df_j1.empty:
                    for _, row in df_j1.iterrows():
                        if pd.notna(row['数值']):
                            value_str = str(row['数值'])
                            param_name = row['参数名称']
                            
                            if param_name == '10周期时间第1次':
                                self.data_records["t1_times"][0].set(value_str)
                            elif param_name == '10周期时间第2次':
                                self.data_records["t1_times"][1].set(value_str)
                            elif param_name == '10周期时间第3次':
                                self.data_records["t1_times"][2].set(value_str)
                            elif param_name == '10周期平均值T1\'':
                                self.data_records["t1_avg"].set(value_str)
                            elif param_name == '平均周期T1':
                                self.data_records["T1"].set(value_str)
                            elif param_name == '悬盘加圆环转动惯量J1':
                                self.data_records["J1"].set(value_str)
                            elif param_name == '圆环转动惯量JM1':
                                self.data_records["JM1"].set(value_str)
                            elif param_name == 'JM1理论值':  # 新增：导入JM1理论值
                                try:
                                    # 保留6位小数
                                    value_float = float(value_str)
                                    formatted_value = f"{value_float:.6f}"
                                    self.data_records["JM1_theory"].set(formatted_value)
                                    # 同时更新fixed_params中的值
                                    self.fixed_params['JM1_theory'] = value_float
                                except ValueError:
                                    pass
                            elif param_name == '误差':
                                self.data_records["JM1_error"].set(value_str)
            except Exception as e:
                print(f"读取圆环转动惯量数据时出错: {e}")
            
            # === 工作表3: 测量悬盘的转动惯量 ===
            try:
                df_j3 = pd.read_excel(file_path, sheet_name='圆盘转动惯量')
                if not df_j3.empty:
                    for _, row in df_j3.iterrows():
                        if pd.notna(row['数值']):
                            value_str = str(row['数值'])
                            param_name = row['参数名称']
                            
                            if param_name == '10周期时间第1次':
                                self.data_records["t3_times"][0].set(value_str)
                            elif param_name == '10周期时间第2次':
                                self.data_records["t3_times"][1].set(value_str)
                            elif param_name == '10周期时间第3次':
                                self.data_records["t3_times"][2].set(value_str)
                            elif param_name == '10周期平均值T3\'':
                                self.data_records["t3_avg"].set(value_str)
                            elif param_name == '平均周期T3':
                                self.data_records["T3"].set(value_str)
                            elif param_name == '悬盘加圆盘转动惯量J3':
                                self.data_records["J3"].set(value_str)
                            elif param_name == '圆盘转动惯量JM3':
                                self.data_records["JM3"].set(value_str)
                            elif param_name == 'JM3理论值':  # 新增：导入JM3理论值
                                try:
                                    # 保留6位小数
                                    value_float = float(value_str)
                                    formatted_value = f"{value_float:.6f}"
                                    self.data_records["JM3_theory"].set(formatted_value)
                                    # 同时更新fixed_params中的值
                                    self.fixed_params['JM3_theory'] = value_float
                                except ValueError:
                                    pass
                            elif param_name == '误差':
                                self.data_records["JM3_error"].set(value_str)
            except Exception as e:
                print(f"读取圆盘转动惯量数据时出错: {e}")
            
            # === 工作表4: 平行轴定理的验证 ===
            try:
                df_j2 = pd.read_excel(file_path, sheet_name='平行轴定理验证')
                if not df_j2.empty:
                    for _, row in df_j2.iterrows():
                        if pd.notna(row['数值']):
                            value_str = str(row['数值'])
                            param_name = row['参数名称']
                            
                            if param_name == '10周期时间第1次':
                                self.data_records["t2_times"][0].set(value_str)
                            elif param_name == '10周期时间第2次':
                                self.data_records["t2_times"][1].set(value_str)
                            elif param_name == '10周期时间第3次':
                                self.data_records["t2_times"][2].set(value_str)
                            elif param_name == '10周期平均值T2\'':
                                self.data_records["t2_avg"].set(value_str)
                            elif param_name == '平均周期T2':
                                self.data_records["T2"].set(value_str)
                            elif param_name == '悬盘加两圆柱转动惯量J2\'+J0':
                                self.data_records["J2_total"].set(value_str)
                            elif param_name == '两圆柱转动惯量J2\'':
                                self.data_records["J2_prime"].set(value_str)
                            elif param_name == '单圆柱转动惯量J2':
                                self.data_records["J2_single"].set(value_str)
                            elif param_name == 'd实测值':
                                self.data_records["d_measured"].set(value_str)
                            elif param_name == 'd计算值':  # 新增：导入d计算值
                                try:
                                    # 保留5位小数
                                    value_float = float(value_str)
                                    formatted_value = f"{value_float:.5f}"
                                    self.data_records["d_calculated"].set(formatted_value)
                                    # 同时更新fixed_params中的值
                                    self.fixed_params['d_calculated'] = value_float
                                except ValueError:
                                    pass
                            elif param_name == '误差':
                                self.data_records["d_error"].set(value_str)
            except Exception as e:
                print(f"读取平行轴定理验证数据时出错: {e}")
            
            print(f"数据已从 {file_path} 导入")
            messagebox.showinfo("导入成功", "数据导入完成！")
            
        except ImportError:
            messagebox.showerror("错误", "请安装pandas和openpyxl库以支持Excel导入")
        except Exception as e:
            messagebox.showerror("错误", f"导入数据时出错: {e}")

    def on_object_change(self, event=None):
        """悬挂物体变化回调"""
        self.suspended_object = self.object_var.get()
        print(f"悬挂物体更改为: {self.suspended_object}")
        
        # 控制D槽滑块的显示/隐藏和状态
        if self.suspended_object == "两个铝制圆柱":
            self.d_groove_frame.pack(fill=tk.X, pady=5)
            # 启用D槽控件
            if hasattr(self, 'd_groove_scale'):
                self.d_groove_scale.config(state="normal")
            if hasattr(self, 'd_groove_minus_btn'):
                self.d_groove_minus_btn.config(state="normal")
            if hasattr(self, 'd_groove_plus_btn'):
                self.d_groove_plus_btn.config(state="normal")
            
            # 确保数据记录区域显示D槽相关信息
            if self.data_record_labels["d_groove_label"]:
                self.data_record_labels["d_groove_label"].grid()
            if self.data_record_labels["two_d_label"]:
                self.data_record_labels["two_d_label"].grid()
        else:
            self.d_groove_frame.pack_forget()
            # 隐藏数据记录区域的D槽相关信息
            if self.data_record_labels["d_groove_label"]:
                self.data_record_labels["d_groove_label"].grid_remove()
            if self.data_record_labels["two_d_label"]:
                self.data_record_labels["two_d_label"].grid_remove()
        
        self.update_display(self.current_time)

    def create_overlay_controls(self):
        """在背景图片上创建叠加控件"""
        # 在图片上叠加按钮
        button_positions = {
            "向上": (340+50, 170-20+2-5),
            "向下": (340+50, 250-20+7-5),
            "确定": (420+60, 170-20+2-5),
            "返回": (420+60, 250-20+7-5),
            "打开电源": (700+80+13, 180-20+36+2-5),  # 新增打开电源按钮
            "关闭电源": (700+80+13, 220-20+36-5-5)   # 新增关闭电源按钮
            # "电源开关": (700+80, 220-20)
        }
        
        self.buttons = {}
        for text, (x, y) in button_positions.items():
            # 根据按钮类型设置背景颜色
            if text in ["打开电源", "关闭电源"]:
                # 电源按钮使用粉色背景 #CC667F
                btn_bg = self.canvas_bg.create_rectangle(x-15, y-15, x+15, y+15, 
                                                    fill="#CC667F", outline="", width=1)
            else:
                # 其他按钮使用黑色背景
                btn_bg = self.canvas_bg.create_rectangle(x-12, y-12, x+12, y+12, 
                                                    fill="#333333", outline="", width=1)
            
            # 根据按钮类型设置文字
            if text == "打开电源":
                display_text = "I"  # 打开电源显示"I"
            elif text == "关闭电源":
                display_text = "O"  # 关闭电源显示"O"
            else:
                display_text = ""   # 其他按钮不显示文字
            
            btn_text = self.canvas_bg.create_text(x, y, text=display_text, 
                                                font=("Arial", 12, "bold"),  # 调整字体大小
                                                fill="black")  # 黑色文字
        
            # 存储按钮信息用于点击检测
            self.buttons[text] = (btn_bg, btn_text, x-15, y-15, x+15, y+15)
        
        # 绑定画布点击事件
        self.canvas_bg.bind("<Button-1>", self.on_canvas_click)
        
        self.create_period_measurement_ui()
    
    def on_canvas_click(self, event):
        """处理画布点击事件"""
        # 检查是否点击了按钮
        for button_name, (bg, text, x1, y1, x2, y2) in self.buttons.items():
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.handle_button_click(button_name)
                return

    def set_power_state(self, power_on):
        """设置电源状态"""
        self.power_on = power_on
        print("power_on:", power_on)
        if power_on:
            self.measurement_mode = "周期测量"
            # 更新按钮状态
            # self.update_power_buttons()
            print("电源已打开")
            self.show_period_measurement_ui()
        else:
            # 电源关闭：隐藏所有实验仪界面
            self.hide_measurement_ui()
            # 更新按钮状态
            # self.update_power_buttons()
            print("电源已关闭")

    def show_period_measurement_ui(self):
        """显示周期测量界面"""

        
        # 显示周期测量界面
        self.canvas_bg.itemconfig(self.period_bg, state="normal")
        self.canvas_bg.itemconfig(self.period_mode_bg, state="normal")
        self.canvas_bg.itemconfig(self.period_mode_text, state="normal")
        self.canvas_bg.itemconfig(self.count_bg, state="normal")
        self.canvas_bg.itemconfig(self.count_text, state="normal")
        self.canvas_bg.itemconfig(self.time_bg, state="normal")
        self.canvas_bg.itemconfig(self.time_text, state="normal")
        self.canvas_bg.itemconfig(self.start_bg, state="normal")
        self.canvas_bg.itemconfig(self.start_text, state="normal")
        self.canvas_bg.itemconfig(self.query_bg, state="normal")
        self.canvas_bg.itemconfig(self.query_text, state="normal")
        self.canvas_bg.itemconfig(self.clear_bg, state="normal")
        self.canvas_bg.itemconfig(self.clear_text, state="normal")
        
        self.period_measurement_mode = "设定模式"
        self.canvas_bg.itemconfig(self.start_text, text="开始")

        # 更新周期测量界面状态
        self.period_ui_active = True
        self.pulse_ui_active = False
        self.period_selection_index = 0
        self.setting_count = False
        
        # 高亮初始选中的栏目
        self.highlight_period_selection()

    def hide_measurement_ui(self):
        """隐藏所有测量界面，返回主界面"""
        # 隐藏周期测量界面
        self.canvas_bg.itemconfig(self.period_bg, state="hidden")
        self.canvas_bg.itemconfig(self.period_mode_bg, state="hidden")
        self.canvas_bg.itemconfig(self.period_mode_text, state="hidden")
        self.canvas_bg.itemconfig(self.count_bg, state="hidden")
        self.canvas_bg.itemconfig(self.count_text, state="hidden")
        self.canvas_bg.itemconfig(self.time_bg, state="hidden")
        self.canvas_bg.itemconfig(self.time_text, state="hidden")
        self.canvas_bg.itemconfig(self.start_bg, state="hidden")
        self.canvas_bg.itemconfig(self.start_text, state="hidden")
        self.canvas_bg.itemconfig(self.query_bg, state="hidden")
        self.canvas_bg.itemconfig(self.query_text, state="hidden")
        self.canvas_bg.itemconfig(self.clear_bg, state="hidden")
        self.canvas_bg.itemconfig(self.clear_text, state="hidden")

        self.clear_all_period_data()
        
        # 更新界面状态
        self.period_ui_active = False
        self.pulse_ui_active = False
        self.period_selection_index = 0
        self.pulse_selection_index = 1
        self.setting_count = False
        self.setting_pulse_count = False

        # +++ 新增：清空所有测量数据 +++
        # 清空周期测量数据
        self.period_mode = "单周"
        self.measure_count = 0
        self.measure_time = 0
        self.canvas_bg.itemconfig(self.period_mode_text, text="周期：单周")
        self.update_count_display()
        self.update_time_display()

    def highlight_period_selection(self):
        """高亮周期测量界面中的选中栏目"""
        # 根据当前模式调整可选择的项目
        if self.period_measurement_mode == "测量模式":
            # 测量模式下只能选择复位和清空（索引2和4）
            self.period_items_count = 2  # 只有2个可选项
            # 调整选择索引范围：2=复位，4=清空
            # 将索引映射到实际位置
            if self.period_selection_index < 2:
                self.period_selection_index = 2
            elif self.period_selection_index > 4:
                self.period_selection_index = 4
        else:
            self.period_items_count = 5

        # 重置所有栏目颜色
        self.canvas_bg.itemconfig(self.period_mode_bg, fill="white")
        self.canvas_bg.itemconfig(self.count_bg, fill="white")
        self.canvas_bg.itemconfig(self.start_bg, fill="white")
        self.canvas_bg.itemconfig(self.query_bg, fill="white")
        self.canvas_bg.itemconfig(self.clear_bg, fill="white")
        
        # 重置字体样式
        self.canvas_bg.itemconfig(self.period_mode_text, font=("Arial", 20))
        self.canvas_bg.itemconfig(self.count_text, font=("Arial", 20))
        
        # 根据当前选择状态高亮对应栏目
        if self.setting_count:
            # 在设置次数模式下，使用橙色高亮次数栏目
            self.canvas_bg.itemconfig(self.count_bg, fill="orange")
            self.canvas_bg.itemconfig(self.count_text, font=("Arial", 20, "bold"))
        else:
            # 在正常模式下，根据选择索引高亮
            if self.period_selection_index == 0:
                self.canvas_bg.itemconfig(self.period_mode_bg, fill="lightblue")
                self.canvas_bg.itemconfig(self.period_mode_text, font=("Arial", 20, "bold"))
            elif self.period_selection_index == 1:
                self.canvas_bg.itemconfig(self.count_bg, fill="lightblue")
                self.canvas_bg.itemconfig(self.count_text, font=("Arial", 20, "bold"))
            elif self.period_selection_index == 2:
                self.canvas_bg.itemconfig(self.start_bg, fill="lightblue")
            elif self.period_selection_index == 3:
                self.canvas_bg.itemconfig(self.query_bg, fill="lightblue")
            elif self.period_selection_index == 4:
                self.canvas_bg.itemconfig(self.clear_bg, fill="lightblue")

    def clear_all_period_data(self):
        """清空所有周期测量数据"""
        print("清空所有周期测量数据")
        self.period_mode = "单周"
        self.measure_count = 0
        self.measure_time = 0
        self.canvas_bg.itemconfig(self.period_mode_text, text="周期：单周")
        self.period_data_groups = []
        self.current_measure_count = 0
        self.temp_measure_data = []
        self.period_measurement_mode = "设定模式"
        
        # 恢复界面显示
        self.canvas_bg.itemconfig(self.start_text, text="开始")
        self.update_count_display()
        self.update_time_display()
        
        # 重置选择索引
        self.period_selection_index = 0
        self.highlight_period_selection()
    
    def reset_measurement(self):
        """复位测量"""
        print("复位测量")
        self.current_measure_count = 0
        self.temp_measure_data = []
        self.measurement_start_time = 0
        
        # 重置双周模式计数器
        if hasattr(self, 'double_period_counter'):
            self.double_period_counter = 0
        
        self.update_count_display()
        self.update_time_display()
    
    def clear_temp_data(self):
        """清空临时数据"""
        print("清空临时数据")
        self.current_measure_count = 0
        self.temp_measure_data = []
        self.update_count_display()
        self.update_time_display()
    
    def on_gate_trigger(self):
        """处理光电门触发事件（用于计数）"""
        if (self.period_ui_active and 
            self.period_measurement_mode == "测量模式" and 
            self.current_measure_count < self.measure_count):  # 改为与预设次数比较
            
            # 初始化计数器（如果不存在）
            if not hasattr(self, 'gate_release_counter'):
                self.gate_release_counter = 0
            
            # 增加释放计数器
            self.gate_release_counter += 1
            
            # 首次穿过不计数，从第二次穿过开始计数
            if self.gate_release_counter >= 2:
                # 根据单周/双周模式判断是否计数
                should_count = False
                if self.period_mode == "单周":
                    # 单周模式：每次释放都计数（从第二次开始）
                    should_count = True
                    count_increment = 1
                else:  # 双周模式
                    # 双周模式：每两次释放计数一次（从第二次开始）
                    if not hasattr(self, 'double_period_counter'):
                        self.double_period_counter = 0
                    
                    self.double_period_counter += 1
                    if self.double_period_counter % 2 == 0:
                        should_count = True
                        count_increment = 1
                    else:
                        should_count = False
                        count_increment = 0
                
                if should_count:
                    self.current_measure_count += count_increment
                    
                    # 计算时间（基于理论周期）
                    theoretical_period = self.get_period()
                    if self.period_mode == "单周":
                        # 单周模式：每次计数对应1/2周期
                        measure_time = theoretical_period * self.current_measure_count / 2
                    else:
                        # 双周模式：每次计数对应1周期
                        measure_time = theoretical_period * self.current_measure_count / 1
                    
                    # 记录数据
                    self.temp_measure_data.append(measure_time)
                    self.update_count_display()
                    self.update_time_display()
                    
                    print(f"光电门释放计数！模式:{self.period_mode}, 计数:{self.current_measure_count}/{self.measure_count}, 时间:{measure_time:.3f}s")
                    
                    # 检查是否达到预设测量次数
                    if self.current_measure_count >= self.measure_count:
                        self.finish_measurement()
                else:
                    # 双周模式下不计数但显示状态
                    print(f"光电门释放（双周模式，第{self.double_period_counter}次触发，不计数）")
            else:
                # 首次穿过，不计数
                print(f"光电门首次释放，不计数（释放计数器: {self.gate_release_counter}）")
        else:
            # 非测量模式下的释放，只显示不记录
            print("光电门释放（非测量模式）")

    def get_period(self):
        """计算周期"""
        # 基础周期值
        if self.suspended_object == "铝制圆环":
            base_period = 1.652
        elif self.suspended_object == "两个铝制圆柱":
            base_period = 1.640
        elif self.suspended_object == "铝制圆盘":
            base_period = 1.621
        else:  # 无悬挂物体
            base_period = 1.739
        
        # 获取当前的H值（单位：cm）
        H_cm = self.fixed_params['H']
        
        # 根据悬挂物体类型使用不同的计算公式
        if self.suspended_object == "两个铝制圆柱":
            # 使用新公式：T = sqrt( (4*π²*H/g/R/r*(2*m*d_measured² + 2*J2) + M0*T0²) / (M0 + 2M2) )
            
            # 获取所有需要的参数（转换为标准单位）
            H = H_cm / 100  # 转换为米
            g = self.fixed_params['g']  # m/s²
            R = self.fixed_params['R'] / 100  # 转换为米
            r = self.fixed_params['r'] / 100  # 转换为米
            M0 = self.fixed_params['M0'] / 1000  # 转换为kg
            M2_total = self.fixed_params['M2_total'] / 1000  # 转换为kg（两圆柱总质量）
            m = M2_total / 2  # 单个圆柱质量，kg
            d_measured = self.fixed_params['d_measured']  # 单位：米
            
            # 获取J0和T0（如果已计算）
            try:
                T0_str = self.data_records["T0"].get()
                T0 = float(T0_str) if T0_str else base_period
            except:
                T0 = base_period
            
            try:
                J0_str = self.data_records["J0"].get()
                J0 = float(J0_str) if J0_str else 0
            except:
                J0 = 0
            
            # 计算单圆柱转动惯量 J2 = M2 * D_cylinder^2 / 8
            D_cylinder = self.fixed_params['D_cylinder'] / 100  # 转换为米
            J2 = m * (D_cylinder**2) / 8
            
            # 计算分子部分：4*π²*H/g/R/r*(2*m*d_measured² + 2*J2) + M0*T0²
            pi_squared = math.pi ** 2
            numerator_part1 = 4 * pi_squared * H / (g * R * r) * (2 * m * d_measured**2 + 2 * J2)
            numerator_part2 = M0 * T0**2
            numerator = numerator_part1 + numerator_part2
            
            # 计算分母部分：M0 + 2M2
            denominator = M0 + M2_total
            
            # 计算最终周期
            final_period = math.sqrt(numerator / denominator)
            
            # 打印详细计算过程
            print(f"两个铝制圆柱周期计算（新公式）:")
            print(f"  输入参数:")
            print(f"    H = {H_cm}cm = {H}m")
            print(f"    g = {g} m/s²")
            print(f"    R = {self.fixed_params['R']}cm = {R}m")
            print(f"    r = {self.fixed_params['r']}cm = {r}m")
            print(f"    M0 = {self.fixed_params['M0']}g = {M0}kg")
            print(f"    M2_total = {self.fixed_params['M2_total']}g = {M2_total}kg")
            print(f"    m = {m}kg (单圆柱质量)")
            print(f"    d_measured = {d_measured}m")
            print(f"    T0 = {T0}s")
            print(f"    D_cylinder = {self.fixed_params['D_cylinder']}cm = {D_cylinder}m")
            print(f"    J2 = {J2:.6f} kg·m²")
            
            print(f"  计算过程:")
            print(f"    分子第一部分 = 4 × π² × H / (g × R × r) × (2 × m × d_measured² + 2 × J2)")
            print(f"                = 4 × {pi_squared:.6f} × {H:.4f} / ({g} × {R:.4f} × {r:.4f}) × (2 × {m:.4f} × {d_measured**2:.6f} + 2 × {J2:.6f})")
            print(f"                = 4 × {pi_squared:.6f} × {H:.4f} / {g*R*r:.6f} × ({2*m*d_measured**2:.6f} + {2*J2:.6f})")
            print(f"                = {4*pi_squared*H:.6f} / {g*R*r:.6f} × {2*m*d_measured**2 + 2*J2:.6f}")
            print(f"                = {4*pi_squared*H/(g*R*r):.6f} × {2*m*d_measured**2 + 2*J2:.6f}")
            print(f"                = {numerator_part1:.6f}")
            
            print(f"    分子第二部分 = M0 × T0² = {M0:.4f} × {T0**2:.6f} = {numerator_part2:.6f}")
            print(f"    总分子 = {numerator_part1:.6f} + {numerator_part2:.6f} = {numerator:.6f}")
            
            print(f"    分母 = M0 + 2M2 = {M0:.4f} + {M2_total:.4f} = {denominator:.4f}kg")
            
            print(f"    最终周期 = √({numerator:.6f} / {denominator:.4f}) = √{numerator/denominator:.6f} = {final_period:.6f}s")
            
        else:
            # 其他物体使用原有公式：√(T_base² × H / 51.9)
            final_period = math.sqrt((base_period ** 2) * H_cm / 51.9)
            
            print(f"{self.suspended_object}周期计算:")
            print(f"  基础值={base_period}s")
            print(f"  H={H_cm}cm")
            print(f"  计算: √({base_period}² × {H_cm} / 51.9)")
            print(f"      = √({base_period**2:.6f} × {H_cm/51.9:.6f})")
            print(f"      = √{base_period**2 * H_cm/51.9:.6f}")
            print(f"      = {final_period:.6f}s")
        
        # 添加千分之一（0.1%）的随机误差
        error_scale = 0.001  # 千分之一
        random_factor = 1 + random.uniform(-error_scale, error_scale)
        final_period_with_error = final_period * random_factor
        
        # 打印调试信息
        print(f"  最终值（含误差）: {final_period:.6f} × {random_factor:.6f} = {final_period_with_error:.6f}s")
        print("-" * 50)
        
        return final_period_with_error
    
    def finish_measurement(self):
        """完成测量"""
        print("测量完成，保存数据")
        # 保存数据到组
        group_data = {
            "mode": self.period_mode,
            "max_count": self.measure_count,  # 使用预设次数
            "time_data": self.temp_measure_data.copy()
        }
        self.period_data_groups.append(group_data)
        
        # 返回设定模式
        self.period_measurement_mode = "设定模式"
        self.canvas_bg.itemconfig(self.start_text, text="开始")
        self.period_selection_index = 2
        self.highlight_period_selection()

    def show_query_ui(self):
        """显示查询界面"""
        # 隐藏周期测量界面元素
        self.canvas_bg.itemconfig(self.period_mode_bg, state="hidden")
        self.canvas_bg.itemconfig(self.period_mode_text, state="hidden")
        self.canvas_bg.itemconfig(self.count_bg, state="hidden")
        self.canvas_bg.itemconfig(self.count_text, state="hidden")
        self.canvas_bg.itemconfig(self.time_bg, state="hidden")
        self.canvas_bg.itemconfig(self.time_text, state="hidden")
        self.canvas_bg.itemconfig(self.start_bg, state="hidden")
        self.canvas_bg.itemconfig(self.start_text, state="hidden")
        self.canvas_bg.itemconfig(self.query_bg, state="hidden")
        self.canvas_bg.itemconfig(self.query_text, state="hidden")
        self.canvas_bg.itemconfig(self.clear_bg, state="hidden")
        self.canvas_bg.itemconfig(self.clear_text, state="hidden")
        
        # 创建查询界面背景
        self.query_ui_bg = self.canvas_bg.create_rectangle(80, 100-10, 320, 240-10, 
                                                        fill="white", width=2,
                                                        state="normal")
        
        # 第一行：组信息、周期模式、次数
        self.query_group_bg = self.canvas_bg.create_rectangle(90, 110-13, 310, 135-13, 
                                                            fill="white", outline="", width=1,
                                                            state="normal")
        self.query_group_text = self.canvas_bg.create_text(200, 122-13, text="", 
                                                        font=("Arial", 16, "bold"),
                                                        state="normal")
        
        # 第二行：时间
        self.query_time_bg = self.canvas_bg.create_rectangle(90, 145-13, 310, 170-13, 
                                                            fill="white", outline="", width=1,
                                                            state="normal")
        self.query_time_text = self.canvas_bg.create_text(200, 157-13, text="", 
                                                        font=("Arial", 16),
                                                        state="normal")
        
        # 第三行：平均值
        self.query_avg_bg = self.canvas_bg.create_rectangle(90, 180-13, 310, 205-13, 
                                                        fill="white", outline="", width=1,
                                                        state="normal")
        self.query_avg_text = self.canvas_bg.create_text(200, 192-13, text="", 
                                                        font=("Arial", 16),
                                                        state="normal")
        
        # 第四行：方差
        self.query_variance_bg = self.canvas_bg.create_rectangle(90, 215-13, 310, 240-13, 
                                                                fill="white", outline="", width=1,
                                                                state="normal")
        self.query_variance_text = self.canvas_bg.create_text(200, 227-13, text="", 
                                                            font=("Arial", 16),
                                                            state="normal")
        
        # 更新查询显示
        self.update_query_display()

    def update_query_display(self):
        """更新查询显示"""
        if not self.period_data_groups:
            # 没有数据时显示提示
            self.canvas_bg.itemconfig(self.query_group_text, text="无测量数据")
            self.canvas_bg.itemconfig(self.query_time_text, text="")
            self.canvas_bg.itemconfig(self.query_avg_text, text="")
            self.canvas_bg.itemconfig(self.query_variance_text, text="")
            return
        
        group_data = self.period_data_groups[self.current_query_group]
        time_data = group_data["time_data"]
        mode = group_data["mode"]
        max_count = group_data["max_count"]
        
        if not time_data:
            self.canvas_bg.itemconfig(self.query_group_text, text=f"第{self.current_query_group + 1}组 数据为空")
            self.canvas_bg.itemconfig(self.query_time_text, text="")
            self.canvas_bg.itemconfig(self.query_avg_text, text="")
            self.canvas_bg.itemconfig(self.query_variance_text, text="")
            return
        
        # 计算统计信息
        last_time = time_data[-1]  # 最后一次测量时间
        # avg_time = sum(time_data) / len(time_data)  # 平均时间
        avg_time = time_data[0]
        
        # 计算方差
        if len(time_data) > 1:
            # variance = sum((t - avg_time) ** 2 for t in time_data) / len(time_data)
            variance=time_data[0]*(random.uniform(0.0003,0.0005))
            std_deviation = variance ** 0.5  # 标准差

        else:
            variance = 0
            std_deviation = 0
        
        # 更新显示
        # 第一行：第X组 单周/双周 X次
        group_info = f"第{self.current_query_group + 1}组 {mode} {max_count}次"
        self.canvas_bg.itemconfig(self.query_group_text, text=group_info)
        
        # 第二行：时间：Xs
        time_info = f"时间：{last_time:.3f}s"
        self.canvas_bg.itemconfig(self.query_time_text, text=time_info)
        
        # 第三行：平均：Xs
        avg_info = f"平均：{avg_time:.3f}s"
        self.canvas_bg.itemconfig(self.query_avg_text, text=avg_info)
        
        # 第四行：方差：X (标准差：X)
        variance_info = f"方差：{variance:.6f}"
        self.canvas_bg.itemconfig(self.query_variance_text, text=variance_info)
        
        # 调试信息
        print(f"查询显示更新：{group_info}")
        print(f"时间数据：{time_data}")
        print(f"平均值：{avg_time:.3f}s, 方差：{variance:.4f}")

    def hide_query_ui(self):
        """隐藏查询界面"""
        # 隐藏查询界面元素
        self.canvas_bg.itemconfig(self.query_ui_bg, state="hidden")
        self.canvas_bg.itemconfig(self.query_group_bg, state="hidden")
        self.canvas_bg.itemconfig(self.query_group_text, state="hidden")
        self.canvas_bg.itemconfig(self.query_time_bg, state="hidden")
        self.canvas_bg.itemconfig(self.query_time_text, state="hidden")
        self.canvas_bg.itemconfig(self.query_avg_bg, state="hidden")
        self.canvas_bg.itemconfig(self.query_avg_text, state="hidden")
        self.canvas_bg.itemconfig(self.query_variance_bg, state="hidden")
        self.canvas_bg.itemconfig(self.query_variance_text, state="hidden")

    def handle_power_on(self):
        """处理打开电源"""
        if not self.power_on:
            self.set_power_state(True)
        else:
            print("电源已经打开")

    def handle_power_off(self):
        """处理关闭电源"""
        if self.power_on:
            self.set_power_state(False)
        else:
            print("电源已经关闭")
    
    def handle_button_click(self, button_name):
        """处理按钮点击"""
        print(f"点击了按钮: {button_name}")
        # 电源按钮处理
        if button_name == "打开电源":
            self.handle_power_on()
            return
        elif button_name == "关闭电源":
            self.handle_power_off()
            return

        # 其他按钮处理（只有在电源打开时才响应）
        if not self.power_on:
            print("电源未打开，无法操作")
            return

        if button_name == "向上":
            self.handle_up_button()
        elif button_name == "向下":
            self.handle_down_button()
        elif button_name == "确定":
            self.handle_ok_button()
        elif button_name == "返回":
            self.handle_back_button()
        elif button_name == "电源开关":
            self.handle_power_button()

    def handle_up_button(self):
        """处理向上按钮"""
        if self.period_ui_active:
            if self.period_measurement_mode == "查询模式":
                # 查询模式下向上切换到上一组数据
                if self.period_data_groups:
                    self.current_query_group = (self.current_query_group - 1) % len(self.period_data_groups)
                    self.update_query_display()
                    print(f"查询上一组数据：第{self.current_query_group + 1}组")
                return
            
            if self.period_measurement_mode == "测量模式":
                # 测量模式下只能在复位(2)和清空(4)之间切换
                if self.period_selection_index == 2:
                    self.period_selection_index = 4
                elif self.period_selection_index == 4:
                    self.period_selection_index = 2
                self.highlight_period_selection()
                return
                
            if self.setting_count:
                # 在设置次数模式下，增加次数
                self.measure_count = min(100, self.measure_count + 1)
                self.update_count_display()
            else:
                # 在正常模式下，向上移动选择
                self.period_selection_index = (self.period_selection_index - 1) % self.period_items_count
                self.highlight_period_selection()

    
    def handle_down_button(self):
        """处理向下按钮"""
        if self.period_ui_active:
            if self.period_measurement_mode == "查询模式":
                # 查询模式下向下切换到下一组数据
                if self.period_data_groups:
                    self.current_query_group = (self.current_query_group + 1) % len(self.period_data_groups)
                    self.update_query_display()
                    print(f"查询下一组数据：第{self.current_query_group + 1}组")
                return
            
            if self.period_measurement_mode == "测量模式":
                # 测量模式下只能在复位(2)和清空(4)之间切换
                if self.period_selection_index == 2:
                    self.period_selection_index = 4
                elif self.period_selection_index == 4:
                    self.period_selection_index = 2
                self.highlight_period_selection()
                return
                
            if self.setting_count:
                # 在设置次数模式下，减少次数
                self.measure_count = max(0, self.measure_count - 1)
                self.update_count_display()
            else:
                # 在正常模式下，向下移动选择
                self.period_selection_index = (self.period_selection_index + 1) % self.period_items_count
                self.highlight_period_selection()
        
    
    def handle_ok_button(self):
        """处理确定按钮"""
        if self.period_ui_active:
            if self.period_measurement_mode == "设定模式":
                # 设定模式下的确定按钮逻辑
                if self.setting_count:
                    # 退出设置次数模式
                    self.setting_count = False
                    self.highlight_period_selection()
                else:
                    # 根据当前选择执行操作
                    if self.period_selection_index == 0:
                        # 切换周期模式
                        self.period_mode = "双周" if self.period_mode == "单周" else "单周"
                        self.canvas_bg.itemconfig(self.period_mode_text, text=f"周期：{self.period_mode}")
                    elif self.period_selection_index == 1:
                        # 进入设置次数模式
                        self.setting_count = True
                        self.highlight_period_selection()
                    elif self.period_selection_index == 2:
                        # 开始测量 - 进入测量模式
                        self.start_period_measurement()
                    elif self.period_selection_index == 3:
                        # 查询 - 只有有数据时才可进入
                        if self.period_data_groups:
                            self.enter_query_mode()
                        else:
                            print("没有测量数据，无法查询")
                    elif self.period_selection_index == 4:
                        # 清空 - 清除所有数据
                        self.clear_all_period_data()

            elif self.period_measurement_mode == "测量模式":
                # 测量模式下的确定按钮逻辑
                if self.period_selection_index == 2:  # 复位按钮
                    self.reset_measurement()
                elif self.period_selection_index == 4:  # 清空按钮
                    self.clear_all_period_data()
    
    def handle_back_button(self):
        """处理返回按钮"""
        if self.period_ui_active:
            if self.period_measurement_mode == "查询模式":
                # 查询模式下按返回回到周期测量界面
                self.exit_query_mode()
                return
                
            if self.setting_count:
                # 退出设置次数模式
                self.setting_count = False
                self.highlight_period_selection()
            # else:
            #     # 从测量界面返回主界面
            #     self.hide_measurement_ui()
    
    
    def create_period_measurement_ui(self):
        """创建周期测量界面"""
        # 周期测量界面背景 - 尺寸减小30%
        self.period_bg = self.canvas_bg.create_rectangle(80, 100-10, 320, 240-10, 
                                                        fill="white", width=2,
                                                        state="hidden")
        
        # 创建六个栏目 - 位置和尺寸相应调整
        # 第一行：周期模式
        self.period_mode_bg = self.canvas_bg.create_rectangle(90, 110-10, 310, 135-10, 
                                                            fill="lightblue", outline="", width=1,
                                                            state="hidden")
        self.period_mode_text = self.canvas_bg.create_text(200, 122-10, text="周期：单周", 
                                                        font=("Arial", 20, "bold"),
                                                        state="hidden")
        
        # 第二行：次数
        self.count_bg = self.canvas_bg.create_rectangle(90, 145-10, 310, 170-10, 
                                                    fill="white", outline="", width=1,
                                                    state="hidden")
        self.count_text = self.canvas_bg.create_text(200, 157-10, text="次数：0次", 
                                                    font=("Arial", 20),
                                                    state="hidden")
        
        # 第三行：时间
        self.time_bg = self.canvas_bg.create_rectangle(90, 180-10, 310, 205-10, 
                                                    fill="lightgray", outline="", width=1,
                                                    state="hidden")
        self.time_text = self.canvas_bg.create_text(200, 192-10, text="时间：0s", 
                                                font=("Arial", 20),
                                                state="hidden")
        
        # 第四行：三个按钮 - 按钮尺寸相应减小
        self.start_bg = self.canvas_bg.create_rectangle(90, 210-10, 150, 235-10, 
                                                    fill="white", outline="", width=1,
                                                    state="hidden")
        self.start_text = self.canvas_bg.create_text(120, 222-10, text="开始", 
                                                    font=("Arial", 20),
                                                    state="hidden")
        
        self.query_bg = self.canvas_bg.create_rectangle(160, 210-10, 220, 235-10, 
                                                    fill="white", outline="", width=1,
                                                    state="hidden")
        self.query_text = self.canvas_bg.create_text(190, 222-10, text="查询", 
                                                    font=("Arial", 20),
                                                    state="hidden")
        
        self.clear_bg = self.canvas_bg.create_rectangle(230, 210-10, 290, 235-10, 
                                                    fill="white", outline="", width=1,
                                                    state="hidden")
        self.clear_text = self.canvas_bg.create_text(260, 222-10, text="清空", 
                                                    font=("Arial", 20),
                                                    state="hidden")
    
    def update_count_display(self):
        """更新周期测量次数显示"""
        if self.period_measurement_mode == "测量模式":
            # 测量模式下显示当前测量次数
            self.canvas_bg.itemconfig(self.count_text, text=f"次数：{self.current_measure_count}次")
        else:
            # 设定模式下显示预设次数
            self.canvas_bg.itemconfig(self.count_text, text=f"次数：{self.measure_count}次")
    
    def update_time_display(self):
        """更新周期测量时间显示"""
        if self.period_measurement_mode == "测量模式" and self.temp_measure_data:
            # 测量模式下显示最新测量时间
            latest_time = self.temp_measure_data[-1]
            self.canvas_bg.itemconfig(self.time_text, text=f"时间：{latest_time:.3f}s")
        else:
            # 其他情况下显示0
            self.canvas_bg.itemconfig(self.time_text, text="时间：0s")

    def enter_query_mode(self):
        """进入查询模式"""
        print("进入查询模式")
        self.period_measurement_mode = "查询模式"
        self.current_query_group = 0
        self.show_query_ui()

    def exit_query_mode(self):
        """退出查询模式"""
        print("退出查询模式")
        self.period_measurement_mode = "设定模式"
        self.hide_query_ui()
        
        # 重新显示周期测量界面元素
        self.canvas_bg.itemconfig(self.period_mode_bg, state="normal")
        self.canvas_bg.itemconfig(self.period_mode_text, state="normal")
        self.canvas_bg.itemconfig(self.count_bg, state="normal")
        self.canvas_bg.itemconfig(self.count_text, state="normal")
        self.canvas_bg.itemconfig(self.time_bg, state="normal")
        self.canvas_bg.itemconfig(self.time_text, state="normal")
        self.canvas_bg.itemconfig(self.start_bg, state="normal")
        self.canvas_bg.itemconfig(self.start_text, state="normal")
        self.canvas_bg.itemconfig(self.query_bg, state="normal")
        self.canvas_bg.itemconfig(self.query_text, state="normal")
        self.canvas_bg.itemconfig(self.clear_bg, state="normal")
        self.canvas_bg.itemconfig(self.clear_text, state="normal")
        
        self.highlight_period_selection()

    def bind_button_repeat(self, button, command):
        """绑定按钮长按连续触发事件"""
        def on_press(event):
            button.after_id = button.after(300, lambda: self.repeat_command(button, command))
        
        def on_release(event):
            if hasattr(button, 'after_id'):
                button.after_cancel(button.after_id)
        
        button.bind('<ButtonPress-1>', on_press)
        button.bind('<ButtonRelease-1>', on_release)

    def repeat_command(self, button, command):
        """重复执行命令"""
        command()
        button.after_id = button.after(50, lambda: self.repeat_command(button, command))

    def adjust_height(self, delta):
        """调整圆盘高度，步长1mm"""
        new_height = self.plate_height_offset + delta
        # 限制范围
        new_height = max(0.0, min(0.8, new_height))
        
        if new_height != self.plate_height_offset:
            self.plate_height_offset = new_height
            self.height_var.set(new_height)
            self.update_height_display()
            self.on_height_change(new_height)

    def adjust_gate_height(self, delta):
        """调整光电门高度，步长1mm"""
        new_gate_height = self.gate_height + delta
        # 限制范围
        new_gate_height = max(-0.15, min(self.gate_max_height, new_gate_height))
        
        if new_gate_height != self.gate_height:
            self.gate_height = new_gate_height
            self.gate_var.set(new_gate_height)
            self.update_gate_display()
            self.on_gate_change(new_gate_height)
    
    def adjust_d_groove(self, delta):
        """调整D槽直径，步长1mm"""
        if self.suspended_object == "两个铝制圆柱":
            new_d_groove = self.d_groove_current + delta
            # 限制范围
            new_d_groove = max(self.d_groove_min, min(self.d_groove_max, new_d_groove))
            
            if new_d_groove != self.d_groove_current:
                self.d_groove_current = new_d_groove
                self.d_groove_var.set(new_d_groove)
                self.update_d_groove_display()
                self.on_d_groove_change(new_d_groove)

    def update_d_groove_display(self):
        """更新D槽直径显示"""
        self.d_groove_label.config(text=f"{self.d_groove_current:.1f}cm")

    def update_data_record_display(self, d_groove_value):
        """更新数据记录区域中的D槽和2d显示"""
        try:
            # 计算两圆柱体的质心间距2d = D槽 - 3
            two_d_value = d_groove_value - 3.0
            
            # 使用StringVar更新显示
            self.d_groove_display_var.set(f"{d_groove_value:.1f} cm")
            self.two_d_display_var.set(f"{two_d_value:.2f} cm")
            
            print(f"数据记录区域已更新: D槽={d_groove_value:.1f}cm, 2d={two_d_value:.2f}cm")
            
        except Exception as e:
            print(f"更新数据记录显示时出错: {e}")

    def on_d_groove_change(self, val):
        """D槽直径变化回调"""
        if isinstance(val, (float, int)):
            new_d_groove = val
        else:
            new_d_groove = float(val)
        
        # 应用范围限制
        new_d_groove = max(self.d_groove_min, min(self.d_groove_max, new_d_groove))
        
        self.d_groove_current = new_d_groove
        self.update_d_groove_display()
        
        # 更新固定参数
        self.fixed_params['D_groove'] = new_d_groove
        
        # 计算d实测值 = (D槽 - D小柱) / 2
        d_cylinder = self.fixed_params['D_cylinder']  # 圆柱体直径
        d_measured = (new_d_groove - d_cylinder) / 2 / 100  # 转换为米
        
        # 更新固定参数中的d实测值
        self.fixed_params['d_measured'] = d_measured
        
        # 更新数据记录区域的显示 - 使用和d实测值相同的方法
        if hasattr(self, 'data_records') and self.data_records is not None:
            self.data_records["d_measured"].set(f"{d_measured:.3f}")
            # 新增：更新D槽和2d的显示
            self.data_records["d_groove"].set(f"{new_d_groove:.1f} cm")
            
            # 计算并更新2d值
            two_d_value = new_d_groove - 3.0
            self.data_records["two_d"].set(f"{two_d_value:.2f} cm")
        
        # 新增：重绘画布以更新圆柱位置
        if self.suspended_object == "两个铝制圆柱":
            self.update_display(self.current_time)
        
        print(f"D槽更新: {new_d_groove:.1f}cm, d实测值: {d_measured:.3f}m, 2d: {two_d_value:.2f}cm")

    def update_data_record_display(self, d_groove_value):
        """更新数据记录区域中的D槽和2d显示"""
        # 计算两圆柱体的质心间距2d = D槽 - 3·
        two_d_value = d_groove_value - 3.0
        
        # 这里需要找到数据记录区域中对应的标签并更新
        # 由于数据记录区域是动态创建的，我们需要在创建时给这些标签设置特定的tag或variable
        
        # 方法1：如果数据记录区域有对应的StringVar，可以直接更新
        # 方法2：遍历canvas的子项，找到对应的文本进行更新
        
        print(f"更新数据记录显示: D槽={d_groove_value:.1f}cm, 2d={two_d_value:.2f}cm")
        
        # 由于数据记录区域是使用grid布局的，我们需要找到对应的标签
        # 这里需要根据实际的数据记录区域结构来更新
        # 假设我们在create_record_content方法中给相关标签设置了特定的tag
        
        # 临时方案：在控制台输出，确认计算正确
        print(f"D槽直径: {d_groove_value:.1f} cm")
        print(f"两圆柱体质心间距2d: {two_d_value:.2f} cm")
        print(f"单圆柱体质心到转轴距离d: {two_d_value/2:.2f} cm")

    def update_height_display(self):
        """更新圆盘高度显示（精确到毫米）"""
        self.height_label.config(text=f"{self.plate_height_offset:.3f}m")

    def update_gate_display(self):
        """更新光电门高度显示（精确到毫米）"""
        self.gate_label.config(text=f"{self.gate_height:.3f}m")

    def on_height_change(self, val):
        """圆盘高度变化回调"""
        if isinstance(val, (float, int)):
            self.plate_height_offset = val
        else:
            self.plate_height_offset = float(val)
        
        self.update_height_display()
        
        # 自动计算上下圆盘距离H = 1m - 圆盘高度(m)，然后转换为cm
        H_m = 1.0 - self.plate_height_offset  # 单位：m
        H_cm = H_m * 100  # 单位：cm
        self.fixed_params['H'] = H_cm
        self.H_var.set(f"{H_cm:.1f}")  # 更新显示
        
        self.update_positions()
        
        # 检查当前光电门高度是否超过新限制
        if self.gate_height > self.gate_max_height:
            self.gate_height = self.gate_max_height
            self.gate_var.set(self.gate_height)
            self.update_gate_display()
        
        self.update_display(self.current_time)

    def on_gate_change(self, val):
        """光电门高度变化回调"""
        if isinstance(val, (float, int)):
            new_gate_height = val
        else:
            new_gate_height = float(val)
        
        # 应用高度限制
        if new_gate_height > self.gate_max_height:
            new_gate_height = self.gate_max_height
            self.gate_var.set(new_gate_height)
        elif new_gate_height < -0.15:  # 添加下限检查
            new_gate_height = -0.15
            self.gate_var.set(new_gate_height)
        
        self.gate_height = new_gate_height
        self.update_gate_display()
        self.update_display(self.current_time)
    
    def start_animation(self, event=None):
        """开始动画"""
        if not self.animation_running:
            self.animation_running = True
            # 禁用控制控件
            self.disable_controls()
            self.anim = FuncAnimation(
                self.fig, self.animate, 
                frames=None,
                interval=50,
                repeat=True,
                blit=False
            )
            self.canvas.draw()
    
    def stop_animation(self, event=None):
        """停止动画"""
        self.animation_running = False
        if self.anim:
            self.anim.event_source.stop()
        # 启用控制控件
        self.enable_controls()
    
    def reset_animation(self, event=None):
        """复位动画到初始状态"""
        self.stop_animation()
        self.current_time = 0.0
        # 重置光电门触发状态
        self.gate_triggered = False
        self.last_angle = 0.0
        self.above_threshold = False
        self.update_display(0)
    
    def disable_controls(self):
        """禁用控制控件"""
        # 圆盘高度控件
        self.height_scale.config(state="disabled")
        self.height_minus_btn.config(state="disabled")
        self.height_plus_btn.config(state="disabled")
        
        # 光电门高度控件
        self.gate_scale.config(state="disabled")
        self.gate_minus_btn.config(state="disabled")
        self.gate_plus_btn.config(state="disabled")
        
        self.start_button.config(state="disabled")
        self.reset_button.config(state="normal")
        # 悬挂物体选择
        if hasattr(self, 'object_combo'):
            self.object_combo.config(state="disabled")
        
        # D槽控件
        if hasattr(self, 'd_groove_scale'):
            self.d_groove_scale.config(state="disabled")
        if hasattr(self, 'd_groove_minus_btn'):
            self.d_groove_minus_btn.config(state="disabled")
        if hasattr(self, 'd_groove_plus_btn'):
            self.d_groove_plus_btn.config(state="disabled")

        print("控件已禁用 - 动画运行中")

    def enable_controls(self):
        """启用控制控件"""
        # 圆盘高度控件
        self.height_scale.config(state="normal")
        self.height_minus_btn.config(state="normal")
        self.height_plus_btn.config(state="normal")
        
        # 光电门高度控件
        self.gate_scale.config(state="normal")
        self.gate_minus_btn.config(state="normal")
        self.gate_plus_btn.config(state="normal")
        
        self.start_button.config(state="normal")
        
        self.reset_button.config(state="disabled")
        # 悬挂物体选择
        if hasattr(self, 'object_combo'):
            self.object_combo.config(state="readonly")
        
        # D槽控件（仅在两个铝制圆柱时启用）
        if hasattr(self, 'd_groove_scale'):
            if self.suspended_object == "两个铝制圆柱":
                self.d_groove_scale.config(state="normal")
        if hasattr(self, 'd_groove_minus_btn'):
            if self.suspended_object == "两个铝制圆柱":
                self.d_groove_minus_btn.config(state="normal")
        if hasattr(self, 'd_groove_plus_btn'):
            if self.suspended_object == "两个铝制圆柱":
                self.d_groove_plus_btn.config(state="normal")

        print("控件已启用 - 动画已停止")

    def animate(self, frame):
        """动画更新函数"""
        if self.animation_running:
            self.current_time += 0.1
            self.update_display(self.current_time)
        return []
    
    def update_display(self, t):
        """更新显示"""
        self.ax.clear()
        # 设置等比例显示，确保圆形显示为圆形
        self.ax.set_aspect('equal')
        # 添加背景图片
        if self.background_dir:
            try:
                gate_path = os.path.join(self.background_dir, 'gate.jpg')
                device_path = os.path.join(self.background_dir, 'device.jpg')
                
                if os.path.exists(gate_path) and os.path.exists(device_path):
                    gate_img = plt.imread(gate_path)
                    device_img = plt.imread(device_path)
                    
                    # 设备背景图片
                    device_extent = [-0.18, 0.18, -0.3, 1.1]
                    self.ax.imshow(device_img, extent=device_extent, aspect='auto', alpha=1, zorder=0)
                    # 光电门图片位置
                    gate_height_center = self.gate_height
                    gate_height_range = 0.10
                    gate_extent = [-0.177, -0.025, 
                                gate_height_center - gate_height_range/2, 
                                gate_height_center + gate_height_range/2]
                    self.ax.imshow(gate_img, extent=gate_extent, aspect='auto', alpha=1, zorder=0)
                    
                    
                    
            except Exception as e:
                print(f"加载背景图片时出错: {e}")

        # 获取当前线缆位置
        plate_points = self.get_wire_positions(t)
        
        # 绘制三根线
        line_colors = ['black', 'black', 'black']
        
        for i in range(3):
            self.ax.plot([self.anchor_points[i, 0], plate_points[i, 0]],
                    [self.anchor_points[i, 1], plate_points[i, 1]], 
                    color=line_colors[i], linewidth=3)
        
        # 绘制圆盘
        plate_rect = plt.Rectangle((self.plate_center[0] - self.plate_width/2, 
                            self.plate_center[1] - self.plate_height/2),
                            self.plate_width, self.plate_height,
                            facecolor='lightblue', edgecolor='darkblue',
                            linewidth=3, alpha=0.8, label='圆盘')
        self.ax.add_patch(plate_rect)
        
        # 计算当前扭转角度
        twist_angle = self.initial_angle * np.cos(self.omega * t)
        current_angle = np.degrees(twist_angle)
        # === 绘制悬挂物体 ===
        if self.suspended_object != "无":
            object_color = self.object_colors[self.suspended_object]
            
            if self.suspended_object == "铝制圆环":
                # 绘制铝制圆环（矩形表示）
                ring_width = self.ring_disk_width
                ring_height = self.plate_height  # 与圆盘高度相同
                ring_x = self.plate_center[0] - ring_width/2
                ring_y = self.plate_center[1] - ring_height/2 +0.05
                
                ring_rect = plt.Rectangle((ring_x, ring_y), ring_width, ring_height,
                                        facecolor=object_color, edgecolor='darkorange',
                                        linewidth=2, alpha=0.7, label='铝制圆环')
                self.ax.add_patch(ring_rect)
                
            elif self.suspended_object == "两个铝制圆柱":
                # 绘制两个铝制圆柱（矩形表示）
                cylinder_width = self.cylinder_width
                cylinder_height = self.cylinder_height  # 高度的两倍
                edge_offset = 0.015  # 距离边缘3cm
                
                # D槽直径转换为米，然后计算实际间距
                d_groove_m = self.d_groove_current / 100  # 转换为米
                cylinder_offset = (d_groove_m - self.cylinder_width) / 2
                # 计算圆柱的初始位置（在圆盘坐标系中）
                left_cylinder_x_local = -self.plate_width/2 + edge_offset + cylinder_width/2
                right_cylinder_x_local = self.plate_width/2 - edge_offset - cylinder_width/2
                # 应用旋转变换
                cos_angle = np.cos(twist_angle)
                sin_angle = np.sin(twist_angle)
                # print(f'sin_angle=',sin_angle)
                # 左侧圆柱
                left_cylinder_x = self.plate_center[0] - self.plate_width/2 + edge_offset+abs(sin_angle*0.05)- cylinder_offset+0.035
                left_cylinder_y = self.plate_center[1] - cylinder_height/2 +0.06
                
                left_cylinder = plt.Rectangle((left_cylinder_x, left_cylinder_y), 
                                            cylinder_width, cylinder_height,
                                            facecolor=object_color, edgecolor='darkblue',
                                            linewidth=2, alpha=0.7, label='铝制圆柱')
                self.ax.add_patch(left_cylinder)
                
                # 右侧圆柱
                right_cylinder_x = self.plate_center[0] + self.plate_width/2 - edge_offset - cylinder_width-abs(sin_angle*0.05) + cylinder_offset-0.035
                right_cylinder_y = self.plate_center[1] - cylinder_height/2 +0.06
                
                right_cylinder = plt.Rectangle((right_cylinder_x, right_cylinder_y), 
                                            cylinder_width, cylinder_height,
                                            facecolor=object_color, edgecolor='darkblue',
                                            linewidth=2, alpha=0.7)
                self.ax.add_patch(right_cylinder)
                
            elif self.suspended_object == "铝制圆盘":
                # 绘制铝制圆盘（矩形表示）
                disk_width = self.ring_disk_width
                disk_height = self.plate_height  # 与圆盘高度相同
                disk_x = self.plate_center[0] - disk_width/2
                disk_y = self.plate_center[1] - disk_height/2 +0.05
                
                disk_rect = plt.Rectangle((disk_x, disk_y), disk_width, disk_height,
                                        facecolor=object_color, edgecolor='darkgreen',
                                        linewidth=2, alpha=0.7, label='铝制圆盘')
                self.ax.add_patch(disk_rect)

        # 绘制竖线标记
        line_offset = 0.005
        line_length = 0.03
        
        plate_left = plate_points[0, 0] - 0.004
        plate_right = plate_points[2, 0] + 0.004
        
        # 左侧竖线
        left_line_x = plate_left + line_offset
        left_line_bottom = self.plate_center[1] - self.plate_height/2
        left_line_top = left_line_bottom - line_length
        
        self.ax.plot([left_line_x, left_line_x], 
                [left_line_bottom, left_line_top], 
                color='red', linewidth=3)
        
        # 右侧竖线  
        right_line_x = plate_right - line_offset
        right_line_bottom = self.plate_center[1] - self.plate_height/2
        right_line_top = right_line_bottom - line_length
        
        self.ax.plot([right_line_x, right_line_x], 
                [right_line_bottom, right_line_top], 
                color='red', linewidth=3)
        
        # 计算当前扭转角度
        current_angle = np.degrees(self.initial_angle * np.cos(self.omega * t))
        
        # === 光电门触发判断 ===
        self.gate_triggered = self.check_gate_trigger(t)
        
        # === 绘制光电门红灯 ===
        # 红灯位置（在光电门图片上方）
        light_x = -0.07  # 光电门中心偏右
        light_y = self.gate_height +0.02   # 光电门上方
        
        # 根据触发状态选择颜色
        if self.gate_triggered:
            # 绘制圆点指示灯
            light_circle = plt.Circle((light_x, light_y), 0.02, 
                                    color='red', alpha=1.0, zorder=10)
            self.ax.add_patch(light_circle)
            
        # 设置图形属性
        self.ax.set_xlabel('水平位置 X (m)')
        self.ax.set_ylabel('高度 Z (m)')
        
        status = "运行中" if self.animation_running else "已停止"
        gate_status = "触发" if self.gate_triggered else "未触发"
        # self.ax.set_title(f'时间: {t:.2f}s, 扭转角: {current_angle:.1f}°')
        
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(-0.45, 0.45)
        self.ax.set_ylim(-0.3, self.fixed_anchor_height + 0.2)
        
        # 显示图例 - 使用紧凑布局
        self.ax.legend(loc='upper right', fontsize='small', framealpha=0.7)
        
        # 更新当前时间
        self.current_time = t
        self.canvas.draw_idle()
    
    def start_period_measurement(self):
        """开始周期测量 - 进入测量模式"""
        # 检查次数是否至少为1
        self.gate_release_counter = 0
        if self.measure_count < 1:
            print("错误：测量次数必须至少为1次")
            # 可以添加弹窗提示或状态显示
            return
        
        print("进入测量模式")
        self.period_measurement_mode = "测量模式"
        self.current_measure_count = 0  # 当前测量次数从0开始
        self.temp_measure_data = []
        self.measurement_start_time = 0
        
        # 重置双周模式计数器
        if hasattr(self, 'double_period_counter'):
            self.double_period_counter = 0
        
        # 更新界面显示 - 第二行显示当前测量次数（从0开始）
        self.canvas_bg.itemconfig(self.start_text, text="复位")
        self.update_count_display()
        self.update_time_display()
        
        # 重置选择索引，初始选中复位按钮(索引2)
        self.period_selection_index = 2
        self.highlight_period_selection()
    
    def query_period(self):
        """查询周期数据"""
        print(f"查询周期数据 - 次数: {self.period_count}, 时间: {self.period_time}s")
    
    def clear_period_measurement(self):
        """清空周期测量数据"""
        print("清空周期测量")
        self.measure_count = 0
        self.measure_time = 0
        self.canvas_bg.itemconfig(self.count_text, text="次数：0次")
        self.canvas_bg.itemconfig(self.time_text, text="时间：0s")

# 创建三线摆实例
pendulum_front = ThreeWirePendulumFrontView(initial_angle=5.0)