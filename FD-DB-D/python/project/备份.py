import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
from PIL import Image, ImageTk
import time
import random
import pandas as pd
from tkinter import filedialog

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 初始物理参数
g = 9.8
L0 = 0.4
theta0_deg = 20
theta0 = np.radians(theta0_deg)
omega0 = 0.0
dt = 0.001
t_max = 99

# 创建时间数组
t = np.arange(0, t_max, dt)

# 初始化角度和角速度数组
theta = np.zeros_like(t)
omega = np.zeros_like(t)
theta[0] = theta0
omega[0] = omega0

# 数值求解单摆运动方程
def solve_pendulum(L, initial_theta):
    theta = np.zeros_like(t)
    omega = np.zeros_like(t)
    theta[0] = initial_theta
    omega[0] = omega0
    
    for i in range(1, len(t)):
        alpha = -g / L * np.sin(theta[i-1])
        omega[i] = omega[i-1] + alpha * dt
        theta[i] = theta[i-1] + omega[i] * dt
    
    return theta, omega

# 初始计算
theta, omega = solve_pendulum(L0, theta0)
x = L0 * np.sin(theta)
y = -L0 * np.cos(theta)

class PendulumSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("单摆运动模拟与实验仪")
        self.root.geometry("1250x850")  # 增加窗口高度以容纳新内容
        self.root.resizable(False, False)  # 禁止调整窗口大小
        
        # 霍尔传感器位置变量
        self.sensor_position = L0 +0.01

        self.show_calculation = False  # 是否显示计算结果的标志

        # 添加插值相关变量
        self.time_scale = 1.0  # 默认速度倍数
        self.sub_frame = 0.0  # 子帧位置（用于插值）
        self.interpolated_data = {}  # 预计算的插值数据缓存

        # 实验仪状态变量
        self.exp_mode = "设定模式"  # 设定模式/查询模式
        self.max_count = 0  # 最多记录次数
        self.current_count = 0  # 当前记录次数
        self.time_records = []  # 时间记录列表
        self.current_record_index = 0  # 当前查看的记录索引
        self.query_start_time = 0.0  # 查询模式开始的时间
        
        # 动画状态
        self.is_animating = False
        self.current_frame = 0
        self.elapsed_time = 0.0
        self.current_L = L0
        self.was_at_bottom = False
        
        # 数据记录相关变量
        self.experiment_type = "固定摆长改变摆角"  # 默认实验类型
        self.data_table = None  # 数据表格
        self.data_rows = 2  # 初始行数
        self.data_headers_fixed = ["θ", "sin(θ/2)^2", "2T/s 第一次", "2T/s 第二次", "2T/s 第三次", 
                                  "2T/s 第四次", "2T/s 第五次", "2T/s 平均值"]
        self.data_headers_variable = ["L/m", "T/s 第一次", "T/s 第二次", "T/s 第三次", 
                                     "T/s 第四次", "T/s 第五次", "T/s 平均值", "T^2/s^2"]
        
        # 新增：用于保存不同实验类型的数据
        self.saved_data = {
            "固定摆长改变摆角": [],
            "改变摆长": []
        }

        # 背景图片
        self.bg_image_matplotlib = None
        self.bg_extent = None
        
        # 创建界面
        self.create_widgets()
        
        # 初始更新
        self.update_display()
        self.update_button_states()  # 初始按钮状态
        # self.recreate_data_table()
        self.update_data_table_structure()
        self.update_chart()  # 更新图表，显示默认实验类型的图表


    def precompute_interpolated_data(self):
        """预计算所有帧的插值数据"""
        print("预计算插值数据...")
        start_time = time.time()
        
        # 预计算所有可能的速度倍数对应的插值数据
        speed_factors = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
        
        for speed_factor in speed_factors:
            frames_needed = int(len(t) / speed_factor)
            x_interp = np.zeros(frames_needed)
            y_interp = np.zeros(frames_needed)
            theta_interp = np.zeros(frames_needed)
            frame_times = np.zeros(frames_needed)
            
            for i in range(frames_needed):
                # 计算对应的原始帧位置
                original_frame_pos = i * speed_factor
                frame_idx = int(original_frame_pos)
                fraction = original_frame_pos - frame_idx
                
                if frame_idx < len(t) - 1:
                    # 线性插值
                    next_idx = min(frame_idx + 1, len(t) - 1)
                    x_interp[i] = x[frame_idx] + fraction * (x[next_idx] - x[frame_idx])
                    y_interp[i] = y[frame_idx] + fraction * (y[next_idx] - y[frame_idx])
                    theta_interp[i] = theta[frame_idx] + fraction * (theta[next_idx] - theta[frame_idx])
                    frame_times[i] = frame_idx * dt  # 保持原始时间精度
                else:
                    x_interp[i] = x[-1]
                    y_interp[i] = y[-1]
                    theta_interp[i] = theta[-1]
                    frame_times[i] = t[-1]
            
            self.interpolated_data[speed_factor] = {
                'x': x_interp,
                'y': y_interp,
                'theta': theta_interp,
                'times': frame_times,
                'total_frames': frames_needed
            }
        
        print(f"预计算完成，耗时: {time.time() - start_time:.2f}秒")

    def get_interpolated_frame(self, frame_index, speed_factor):
        """获取插值后的帧数据"""
        if speed_factor in self.interpolated_data:
            data = self.interpolated_data[speed_factor]
            if frame_index < data['total_frames']:
                return (
                    data['x'][frame_index],
                    data['y'][frame_index],
                    data['theta'][frame_index],
                    data['times'][frame_index]
                )
        
        # 如果预计算数据不存在，实时计算（备用方案）
        original_frame_pos = frame_index * speed_factor
        frame_idx = int(original_frame_pos)
        fraction = original_frame_pos - frame_idx
        
        if frame_idx < len(t) - 1:
            next_idx = min(frame_idx + 1, len(t) - 1)
            x_val = x[frame_idx] + fraction * (x[next_idx] - x[frame_idx])
            y_val = y[frame_idx] + fraction * (y[next_idx] - y[frame_idx])
            theta_val = theta[frame_idx] + fraction * (theta[next_idx] - theta[frame_idx])
            time_val = frame_idx * dt
        else:
            x_val = x[-1]
            y_val = y[-1]
            theta_val = theta[-1]
            time_val = t[-1]
        
        return x_val, y_val, theta_val, time_val


    def get_background_path(self, filename):
        """获取背景图片路径，优先从background文件夹，如果不存在则从程序目录"""
        # 获取程序所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 尝试从background文件夹获取
        bg_dir = os.path.join(script_dir, "background")
        bg_path = os.path.join(bg_dir, filename)
        
        if os.path.exists(bg_path):
            return bg_path
        
        # 如果background文件夹不存在或文件不存在，尝试从程序目录获取
        fallback_path = os.path.join(script_dir, filename)
        if os.path.exists(fallback_path):
            return fallback_path
        
        # 如果都不存在，返回None
        print(f"警告: 未找到图片文件 {filename}")
        return None
    
    # 在类中添加随机误差方法
    def add_random_error(self, time_value):
        """添加千分之二的随机误差"""
        error_percent = 0.0005  # 万分之5
        error_range = time_value * error_percent
        random_error = random.uniform(-error_range, error_range)
        return round(time_value + random_error, 3)

    def create_widgets(self):
        # 创建左侧画布区域
        left_frame = ttk.Frame(self.root, padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建Matplotlib图形
        self.fig = Figure(figsize=(2, 12), dpi=150)
        # 移除图形周围的空白边距
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(-0.1, 0.1)
        self.ax.set_ylim(-0.8, 0.03)
        self.ax.set_aspect('equal')
        self.ax.grid(False)
        self.ax.set_axis_off()  # 隐藏整个坐标轴
        
        # 加载并设置背景图片
        bg_image_path = self.get_background_path("length.jpg")
        
        if os.path.exists(bg_image_path):
            try:
                # 使用PIL加载图片
                pil_image = Image.open(bg_image_path)
                # 转换为numpy数组
                img_array = np.array(pil_image)
                
                # 设置背景图片的显示范围
                self.bg_extent = [-0.1, 0.1, -0.8, 0.02]
                
                # 显示背景图片
                self.bg_image_matplotlib = self.ax.imshow(img_array, 
                                                         extent=self.bg_extent, 
                                                         aspect='auto', 
                                                         alpha=1,  # 设置透明度
                                                         zorder=0)  # 确保背景在最底层
                
                print("成功加载背景图片 length.jpg")
            except Exception as e:
                print(f"加载背景图片失败: {e}")
                # 如果没有背景图片，设置一个简单的背景色
                self.ax.set_facecolor('#f0f0f0')
        else:
            print(f"背景图片未找到: {bg_image_path}")
            # 如果没有背景图片，设置一个简单的背景色
            self.ax.set_facecolor('#f0f0f0')
        
        # 创建摆线和摆锤
        self.line, = self.ax.plot([], [], 'o-', lw=3, color='darkblue', 
                                markerfacecolor='white', markersize=8, zorder=10)
        self.bob = Circle((0, 0), 0.01, fc='red', ec='darkred', alpha=0.9, zorder=11)
        self.ax.add_patch(self.bob)
        
        # 绘制支点
        self.ax.plot(0, 0, 'ko', markersize=10, markerfacecolor='gold', zorder=12)
        
        # 信息文本
        self.time_text = self.ax.text(0.12, 0.96, '', transform=self.ax.transAxes, fontsize=11, 
                                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9),
                                    zorder=13)
        
        # 创建霍尔传感器标记
        sensor_length = 0.05  # 5cm
        self.sensor_line = Rectangle((0, 0), sensor_length, 0.01, fc='red', ec='red', zorder=9)
        self.sensor_text = self.ax.text(0, 0, '', fontsize=9, color='red', ha='center', zorder=9)
        self.ax.add_patch(self.sensor_line)
        self.update_sensor_position(L0)
        
        # 将Matplotlib图形嵌入Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, left_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        # 创建右侧实验仪区域
        right_frame = ttk.Frame(self.root, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 加载背景图片
        bg_image_path = self.get_background_path("FD-DB-D背景图.jpg")
        
        if os.path.exists(bg_image_path):
            try:
                pil_image = Image.open(bg_image_path)
                pil_image = pil_image.resize((700, 300), Image.Resampling.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(pil_image)
                
                self.exp_canvas = tk.Canvas(right_frame, width=700, height=300)
                self.exp_canvas.pack()
                self.exp_canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
                
                # 在最低点位置添加红点
                self.red_dot_id = self.exp_canvas.create_oval(520, 200+5, 550, 230+5, 
                                                            fill="red", outline="red", tags="red_dot")
            except Exception as e:
                print(f"加载背景图片失败: {e}")
                self.exp_canvas = tk.Canvas(right_frame, width=700, height=300, bg="lightgray")
                self.exp_canvas.pack()
                self.red_dot_id = self.exp_canvas.create_oval(200, 150, 220, 170, 
                                                            fill="red", outline="red", tags="red_dot")
        else:
            self.exp_canvas = tk.Canvas(right_frame, width=700, height=300, bg="lightgray")
            self.exp_canvas.pack()
            self.red_dot_id = self.exp_canvas.create_oval(470, 150, 490, 170, 
                                                        fill="red", outline="red", tags="red_dot")

        # 在背景图片下方创建控制面板
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        
        # 速度控制滑块
        ttk.Label(control_frame, text="动画速度:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(control_frame, from_=0.5, to=20.0, 
                                   variable=self.speed_var, orient=tk.HORIZONTAL,
                                   command=self.on_speed_change,
                                   length=200)
        self.speed_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        self.speed_label = ttk.Label(control_frame, text="1.0x", width=6)
        self.speed_label.grid(row=2, column=2, padx=5)

        # 摆长滑块 - 增大长度
        ttk.Label(control_frame, text="摆长(摆线长度＋摆球半径)(m):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.length_var = tk.DoubleVar(value=L0)
        self.length_scale = ttk.Scale(control_frame, from_=0.1, to=0.75, 
                                    variable=self.length_var, orient=tk.HORIZONTAL,
                                    command=self.on_length_change,
                                    length=300)  # 增加进度条长度
        self.length_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.length_label = ttk.Label(control_frame, text=f"{L0:.3f} m", width=8)
        self.length_label.grid(row=0, column=2, padx=5)
        
        # 霍尔传感器位置滑块
        ttk.Label(control_frame, text="霍尔传感器位置(m):").grid(row=0, column=3, sticky=tk.W, padx=(20, 10))
        self.sensor_var = tk.DoubleVar(value=self.sensor_position)
        self.sensor_scale = ttk.Scale(control_frame, from_=L0+0.01, to=0.75, 
                                    variable=self.sensor_var, orient=tk.HORIZONTAL,
                                    command=self.on_sensor_change,
                                    length=300)
        self.sensor_scale.grid(row=0, column=4, sticky=(tk.W, tk.E), padx=5)
        self.sensor_label = ttk.Label(control_frame, text=f"{self.sensor_position:.3f} m", width=8)
        self.sensor_label.grid(row=0, column=5, padx=5)
        
        # 摆角滑块 - 增大长度
        ttk.Label(control_frame, text="摆角 (°):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.angle_var = tk.DoubleVar(value=theta0_deg)
        self.angle_scale = ttk.Scale(control_frame, from_=-50, to=50, 
                                variable=self.angle_var, orient=tk.HORIZONTAL,
                                command=self.on_angle_change,
                                length=300)  # 增加进度条长度
        self.angle_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        self.angle_label = ttk.Label(control_frame, text=f"{theta0_deg}°", width=8)
        self.angle_label.grid(row=1, column=2, padx=5)

        # 按钮 - 放在背景图片下方
        self.start_btn = ttk.Button(control_frame, text="开始", command=self.start_animation)
        self.start_btn.grid(row=3, column=0, pady=5)
        
        self.stop_btn = ttk.Button(control_frame, text="停止", command=self.reset_to_initial_angle)
        self.stop_btn.grid(row=3, column=1, pady=5)
        
        # 实验仪控制面板
        exp_control_frame = ttk.Frame(right_frame)
        exp_control_frame.pack(pady=10)
        
        # 实验仪控制面板 - 直接放在背景图片上
        bg_color = "lightgray"

        self.count_label = tk.Label(self.exp_canvas, text="--", font=("Arial", 50), 
                                relief="flat", width=2, bg="#DB6E8B", fg="black")
        self.count_label.place(x=125, y=60)

        self.time_label = tk.Label(self.exp_canvas, text="0.000", font=("Arial", 50), 
                                relief="flat", width=6, bg="#DB6E8B", fg="black")
        self.time_label.place(x=295, y=60)

        self.plus_btn = tk.Button(self.exp_canvas, text="", width=3,height=1, command=self.on_plus_click,
                                bg="#545454", fg="black", relief="flat", bd=2,
                                activebackground=bg_color, activeforeground="blue")
        self.plus_btn.place(x=110, y=205)

        self.minus_btn = tk.Button(self.exp_canvas, text="", width=3,height=1, command=self.on_minus_click,
                                bg="#545454", fg="black", relief="flat", bd=2,
                                activebackground=bg_color, activeforeground="blue")
        self.minus_btn.place(x=213, y=205)

        self.reset_btn = tk.Button(self.exp_canvas, text="", width=3,height=1, command=self.on_reset_click,
                                bg="red", fg="black", relief="flat", bd=2,
                                activebackground=bg_color, activeforeground="blue")
        self.reset_btn.place(x=393, y=205)
        
        self.mode_label = ttk.Label(self.exp_canvas, text="模式: 设定模式", font=("Arial", 12), 
                                background="lightyellow")
        self.mode_label.place(x=400, y=20)
        
        # 新增数据记录区域
        self.create_data_recording_area(right_frame)
        
        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)
        self.root.rowconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=1)
    
    def on_speed_change(self, val):
        """处理速度改变"""
        new_speed = float(val)
        self.time_scale = new_speed
        self.speed_label.config(text=f"{new_speed:.1f}x")
        
        # 重置动画状态以适应新速度
        if self.is_animating:
            self.is_animating = False
            self.root.after(10, self.start_animation)  # 稍后重新开始

    def create_data_recording_area(self, parent):
        """创建数据记录区域"""
        # 实验步骤选择框
        exp_type_frame = ttk.LabelFrame(parent, text="实验步骤选择", padding="10")
        exp_type_frame.pack(fill=tk.X, pady=5)
        
        # 设置默认值为"固定摆长改变摆角"
        self.exp_type_var = tk.StringVar(value="固定摆长改变摆角")
        
        fixed_angle_btn = ttk.Radiobutton(exp_type_frame, text="固定摆长改变摆角", 
                                        variable=self.exp_type_var, value="固定摆长改变摆角",
                                        command=self.on_experiment_type_change)
        fixed_angle_btn.grid(row=0, column=0, padx=10)
        
        variable_length_btn = ttk.Radiobutton(exp_type_frame, text="改变摆长", 
                                            variable=self.exp_type_var, value="改变摆长",
                                            command=self.on_experiment_type_change)
        variable_length_btn.grid(row=0, column=1, padx=10)
        
        # 数据记录区域（使用PanedWindow实现可调整分割）
        data_frame = ttk.Frame(parent)
        data_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建PanedWindow实现可调整分割
        paned_window = ttk.PanedWindow(data_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 表格区域 - 限制最小宽度
        table_frame = ttk.LabelFrame(paned_window, text="数据表格", padding="5")
        paned_window.add(table_frame, weight=1)
        
        # 创建表格容器（用于动态重建表格）
        self.table_container = ttk.Frame(table_frame)
        self.table_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建初始表格
        self.create_data_table(self.table_container)
        
        # 图表区域 - 限制最小宽度
        chart_frame = ttk.LabelFrame(paned_window, text="数据图表", padding="5")
        paned_window.add(chart_frame, weight=1)
        
        # 创建图表
        self.create_chart_area(chart_frame)
        
        # 设置初始分割比例（表格占40%，图表占60%）
        paned_window.sashpos(0, int(parent.winfo_width() * 0.4))
        
        # 按钮区域
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="删除选中行", command=self.delete_selected_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空数据", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出数据", command=self.export_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导入数据", command=self.import_data).pack(side=tk.LEFT, padx=5)
        # 新增：计算按钮
        self.calculate_btn = ttk.Button(button_frame, text="计算", command=self.on_calculate_click)
        self.calculate_btn.pack(side=tk.LEFT, padx=5)
        
        # 新增：重力加速度和误差显示区域
        self.create_gravity_display_area(parent)

    def create_gravity_display_area(self, parent):
        """创建重力加速度和误差显示区域"""
        gravity_frame = ttk.LabelFrame(parent, text="实验结果", padding="10")
        gravity_frame.pack(fill=tk.X, pady=5)
        
        # 重力加速度显示
        ttk.Label(gravity_frame, text="重力加速度 g:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.g_value_var = tk.StringVar(value="未计算")
        self.g_value_label = ttk.Label(gravity_frame, textvariable=self.g_value_var, 
                                    font=("Arial", 10, "bold"), foreground="blue")
        self.g_value_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # 误差显示
        ttk.Label(gravity_frame, text="误差(理论值9.8m/s²):").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.error_var = tk.StringVar(value="未计算")
        self.error_label = ttk.Label(gravity_frame, textvariable=self.error_var, 
                                    font=("Arial", 10, "bold"), foreground="red")
        self.error_label.grid(row=0, column=3, sticky=tk.W)

    def calculate_gravity_acceleration(self):
        """计算重力加速度和误差"""
        # 检查是否已经创建了显示变量
        if not hasattr(self, 'g_value_var') or not hasattr(self, 'error_var'):
            return
        
        # 只有在点击计算按钮后才显示结果
        if not self.show_calculation:
            self.g_value_var.set("点击'计算'按钮显示结果")
            self.error_var.set("点击'计算'按钮显示结果")
            return
        
        if self.data_table is None or not self.data_table.get_children():
            self.g_value_var.set("数据不足")
            self.error_var.set("数据不足")
            return
    
        if self.data_table is None or not self.data_table.get_children():
            self.g_value_var.set("未计算")
            self.error_var.set("未计算")
            return
        
        try:
            if self.experiment_type == "固定摆长改变摆角":
                # g = 4 * π² * L / (T_avg/2)²
                # 其中 T_avg 是拟合直线的截距（2T的平均值）
                
                # 获取拟合直线的斜率和截距
                x_data = []
                y_data = []
                
                for item in self.data_table.get_children():
                    values = list(self.data_table.item(item, "values"))
                    if values[1] and values[7]:  # sin(θ/2)^2 和 2T/s平均值
                        try:
                            x_val = float(values[1])
                            y_val = float(values[7])
                            x_data.append(x_val)
                            y_data.append(y_val)
                        except ValueError:
                            continue
                
                if len(x_data) < 2:
                    self.g_value_var.set("数据不足")
                    self.error_var.set("数据不足")
                    return
                
                # 线性拟合
                slope, intercept = np.polyfit(x_data, y_data, 1)
                
                # 使用截距计算周期 T（注意：截距是2T，所以T=截距/2）
                T_avg = intercept / 2  # 周期T
                
                # 获取当前摆长
                current_L = self.current_L
                
                # 计算重力加速度
                g_calculated = 4 * (3.1415926 ** 2) * current_L / (T_avg ** 2)
                
            else:  # 改变摆长
                # g = 4 * π² / k，其中k是T²-L图的斜率
                
                # 获取拟合直线的斜率
                x_data = []
                y_data = []
                
                for item in self.data_table.get_children():
                    values = list(self.data_table.item(item, "values"))
                    if values[0] and values[7]:  # L/m 和 T²/s²
                        try:
                            x_val = float(values[0])
                            y_val = float(values[7])
                            x_data.append(x_val)
                            y_data.append(y_val)
                        except ValueError:
                            continue
                
                if len(x_data) < 2:
                    self.g_value_var.set("数据不足")
                    self.error_var.set("数据不足")
                    return
                
                # 线性拟合
                slope, intercept = np.polyfit(x_data, y_data, 1)
                
                # 计算重力加速度
                g_calculated = 4 * (3.1415926 ** 2) / slope
            
            # 计算百分误差（理论值g=9.8）
            g_theoretical = 9.8
            percent_error = abs((g_calculated - g_theoretical) / g_theoretical) * 100
            
            # 更新显示
            self.g_value_var.set(f"{g_calculated:.4f} m/s²")
            self.error_var.set(f"{percent_error:.2f}%")
            
        except Exception as e:
            print(f"计算重力加速度时出错: {e}")
            self.g_value_var.set("计算错误")
            self.error_var.set("计算错误")

    
    def create_data_table(self, parent):
        """创建数据表格"""
        # 创建Treeview作为表格
        # 根据当前实验类型选择表头
        if self.experiment_type == "固定摆长改变摆角":
            headers = self.data_headers_fixed
        else:
            headers = self.data_headers_variable
            
        self.data_table = ttk.Treeview(parent, columns=headers, show="headings", height=6)
        
        # 设置表头
        column_width = 70
        for header in headers:
            self.data_table.heading(header, text=header)
            self.data_table.column(header, width=column_width, anchor=tk.CENTER, minwidth=50)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.data_table.yview)
        self.data_table.configure(yscrollcommand=scrollbar.set)
        
        self.data_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定点击事件
        self.data_table.bind("<ButtonRelease-1>", self.on_table_click)
        
        # 添加初始空行
        for i in range(2):
            if self.experiment_type == "固定摆长改变摆角":
                # 固定摆长改变摆角：sin(θ/2)^2和2T/s平均值列显示空白
                values = []
                for j, header in enumerate(headers):
                    if header in ["sin(θ/2)^2", "2T/s 平均值"]:
                        values.append("")  # 空白
                    else:
                        values.append("点击记录")
            else:
                # 改变摆长：T/s平均值和T^2/s^2列显示空白
                values = []
                for j, header in enumerate(headers):
                    if header in ["T/s 平均值", "T^2/s^2"]:
                        values.append("")  # 空白
                    else:
                        values.append("点击记录")
            
            self.data_table.insert("", "end", values=values)
    
    def create_chart_area(self, parent):
        """创建图表区域"""
        # 创建Matplotlib图形
        self.chart_fig = Figure(figsize=(4, 2), dpi=80)
        self.chart_fig.subplots_adjust(left=0.15, bottom=0.2, right=0.95, top=0.9)
        self.chart_ax = self.chart_fig.add_subplot(111)
        self.chart_ax.set_title("数据图表")
        self.chart_ax.grid(True)
        
        # 将Matplotlib图形嵌入Tkinter
        self.chart_canvas = FigureCanvasTkAgg(self.chart_fig, parent)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.update_chart()
    
    def on_experiment_type_change(self):
        """实验类型改变时的处理"""
        old_type = self.experiment_type  # 保存当前实验类型
        new_type = self.exp_type_var.get()
        
        # 保存当前数据到旧类型
        self.save_current_data(old_type)
        
        # 更新实验类型
        self.experiment_type = new_type
        
        # 恢复新类型的数据
        self.restore_saved_data(new_type)
        
        # 更新图表
        self.update_chart()
        
        # 重置重力加速度显示
        self.g_value_var.set("点击'计算'按钮显示结果")
        self.error_var.set("点击'计算'按钮显示结果")

    def save_current_data(self, exp_type):
        """保存当前表格数据到指定实验类型"""
        if self.data_table is None:
            return
            
        data = []
        for item in self.data_table.get_children():
            values = list(self.data_table.item(item, "values"))
            data.append(values)
        
        self.saved_data[exp_type] = data

    def restore_saved_data(self, exp_type):
        """从保存的数据恢复表格"""
        if self.data_table is None:
            return
            
        # 清空当前表格
        for item in self.data_table.get_children():
            self.data_table.delete(item)
        
        # 获取保存的数据
        saved_data = self.saved_data.get(exp_type, [])
        
        if saved_data:
            # 恢复保存的数据
            for row_data in saved_data:
                self.data_table.insert("", "end", values=row_data)
            self.data_rows = len(saved_data)
        else:
            # 如果没有保存的数据，创建初始空行
            headers = self.data_headers_fixed if exp_type == "固定摆长改变摆角" else self.data_headers_variable
            for i in range(2):
                if exp_type == "固定摆长改变摆角":
                    values = []
                    for j, header in enumerate(headers):
                        if header in ["sin(θ/2)^2", "2T/s 平均值"]:
                            values.append("")
                        else:
                            values.append("点击记录")
                else:
                    values = []
                    for j, header in enumerate(headers):
                        if header in ["T/s 平均值", "T^2/s^2"]:
                            values.append("")
                        else:
                            values.append("点击记录")
                
                self.data_table.insert("", "end", values=values)
            self.data_rows = 2
        
        # 更新表格结构
        self.update_data_table_structure()

    
    def clear_data_on_type_change(self):
        """切换实验类型时不再自动清空数据（由 restore_saved_data 处理）"""
        pass  # 现在这个功能由 restore_saved_data 方法处理

    def update_data_table_structure(self):
        """更新数据表格结构以适应新的实验类型"""
        if self.data_table is None:
            return
        
        # 获取新表头
        if self.experiment_type == "固定摆长改变摆角":
            new_headers = self.data_headers_fixed
        else:
            new_headers = self.data_headers_variable
        
        # 更新表格列配置
        self.data_table["columns"] = new_headers
        
        # 清除旧表头
        for col in self.data_table["columns"]:
            self.data_table.heading(col, text="")
        
        # 设置新表头 - 限制列宽避免表格过宽
        column_width = 70  # 减小列宽
        for header in new_headers:
            self.data_table.heading(header, text=header)
            self.data_table.column(header, width=column_width, anchor=tk.CENTER, minwidth=50)
        
        # 强制更新布局
        self.table_container.update_idletasks()

    def recreate_data_table(self):
        """重新创建数据表格以适应新的实验类型"""
        if self.data_table is None:
            return
            
        # 保存当前数据
        current_data = []
        for item in self.data_table.get_children():
            values = list(self.data_table.item(item, "values"))
            current_data.append(values)
        
        # 销毁旧表格
        self.data_table.destroy()
        
        # 重新创建表格框架
        table_parent = self.data_table.master  # 获取父容器
        self.create_data_table(table_parent)  # 重新创建表格
        
        # 重新填充数据（只保留有效数据）
        if current_data:
            headers = self.data_headers_fixed if self.experiment_type == "固定摆长改变摆角" else self.data_headers_variable
            for row_data in current_data:
                # 只添加与当前实验类型列数匹配的数据
                if len(row_data) == len(headers):
                    self.data_table.insert("", "end", values=row_data)
                else:
                    # 如果列数不匹配，创建空行
                    self.data_table.insert("", "end", values=[""] * len(headers))
        else:
            # 添加初始空行
            headers = self.data_headers_fixed if self.experiment_type == "固定摆长改变摆角" else self.data_headers_variable
            for i in range(2):
                self.data_table.insert("", "end", values=[""] * len(headers))
        
        self.data_rows = len(self.data_table.get_children())

    def update_data_table(self):
        """更新数据表格"""
        if self.data_table is None:
            return
            
        # 清空现有表格
        for item in self.data_table.get_children():
            self.data_table.delete(item)
        
        # 设置表头
        if self.experiment_type == "固定摆长改变摆角":
            headers = self.data_headers_fixed
        else:
            headers = self.data_headers_variable
            
        self.data_table["columns"] = headers
        for header in headers:
            self.data_table.heading(header, text=header)
            self.data_table.column(header, width=80, anchor=tk.CENTER)
        
        # 添加初始行
        for i in range(self.data_rows):
            self.data_table.insert("", "end", values=[""] * len(headers))
    
    def on_table_click(self, event):
        """表格点击事件处理"""
        self.show_calculation = False
        self.g_value_var.set("点击'计算'按钮显示结果")
        self.error_var.set("点击'计算'按钮显示结果")

        item = self.data_table.selection()
        if not item:
            return
            
        item = item[0]
        column = self.data_table.identify_column(event.x)
        column_index = int(column.replace("#", "")) - 1
        
        # 获取当前行的值
        values = list(self.data_table.item(item, "values"))
        
        # 如果单元格显示"点击记录"，则清空以便输入新数据
        if values[column_index] == "点击记录":
            values[column_index] = ""
        
        if self.experiment_type == "固定摆长改变摆角":
            if column_index == 0:  # θ列
                # 获取当前摆角
                current_angle = np.degrees(theta0)
                values[0] = f"{current_angle:.0f}"
                # 自动计算sin(θ/2)^2
                theta_rad = np.radians(current_angle)
                sin_half_theta_sq = (np.sin(theta_rad/2))**2
                values[1] = f"{sin_half_theta_sq:.5f}"
                
            elif 2 <= column_index <= 6:  # 2T/s 第1-5次列
                # 检查是否满足条件（第4次到达最低点）
                if self.current_count < 4:
                    messagebox.showwarning("数据不足", "固定摆长改变摆角实验至少需要4次数据才能记录")
                    return
                    
                # 获取第4次到达最低点的时间（2T）
                if len(self.time_records) >= 4:
                    time_value = self.time_records[3]['displayed']  # 第4次的时间
                    values[column_index] = f"{time_value:.3f}"
                    # 自动计算平均值
                    self.calculate_average_fixed(values)
                else:
                    messagebox.showwarning("数据不足", "尚未记录到足够的到达最低点数据")
                    return
                    
        else:  # 改变摆长
            if column_index == 0:  # L/m列
                # 获取当前摆长
                values[0] = f"{self.current_L:.3f}"
                
            elif 1 <= column_index <= 5:  # T/s 第1-5次列
                # 检查是否满足条件（第2次到达最低点）
                if self.current_count < 2:
                    messagebox.showwarning("数据不足", "改变摆长实验至少需要2次数据才能记录")
                    return
                    
                # 获取第2次到达最低点的时间（T）
                if len(self.time_records) >= 2:
                    time_value = self.time_records[1]['displayed']
                    values[column_index] = f"{time_value:.3f}"
                    # 自动计算平均值和T^2
                    self.calculate_average_variable(values)
                else:
                    messagebox.showwarning("数据不足", "尚未记录到足够的到达最低点数据")
                    return
        
        # 更新表格
        self.data_table.item(item, values=values)
        
        # 检查是否需要添加新行
        self.check_add_new_row()
        
        # 更新图表
        self.update_chart()
    
    def calculate_average_fixed(self, values):
        """计算固定摆长实验的平均值"""
        times = []
        for i in range(2, 7):  # 第3到第7列（索引2-6）
            if values[i] and values[i] != "":
                try:
                    times.append(float(values[i]))
                except ValueError:
                    pass
        
        if times:
            avg = sum(times) / len(times)
            values[7] = f"{avg:.3f}"
        else:
            values[7] = ""
    
    def calculate_average_variable(self, values):
        """改变摆长实验的平均值和T^2计算"""
        times = []
        for i in range(1, 6):  # 第2到第6列（索引1-5）
            if values[i] and values[i] != "":
                try:
                    times.append(float(values[i]))
                except ValueError:
                    pass
        
        if times:
            avg = sum(times) / len(times)
            values[6] = f"{avg:.3f}"
            values[7] = f"{avg**2:.4f}"
        else:
            values[6] = ""
            values[7] = ""
    
    def check_add_new_row(self):
        """检查是否需要添加新行"""
        # 获取所有行
        items = self.data_table.get_children()
        if not items:
            return
            
        # 检查最后一行是否所有必要列都有数据
        last_item = items[-1]
        values = list(self.data_table.item(last_item, "values"))
        
        # 如果最后一行有数据（且不是"点击记录"），则添加新行
        if any(value and value != "点击记录" for value in values):
            # 检查是否已经有空行
            has_empty_row = False
            for item in items:
                item_values = list(self.data_table.item(item, "values"))
                if all(value == "" or value == "点击记录" for value in item_values):
                    has_empty_row = True
                    break
            
            if not has_empty_row:
                headers = self.data_headers_fixed if self.experiment_type == "固定摆长改变摆角" else self.data_headers_variable
                
                if self.experiment_type == "固定摆长改变摆角":
                    # 固定摆长改变摆角：sin(θ/2)^2和2T/s平均值列显示空白
                    values = []
                    for j, header in enumerate(headers):
                        if header in ["sin(θ/2)^2", "2T/s 平均值"]:
                            values.append("")  # 空白
                        else:
                            values.append("点击记录")
                else:
                    # 改变摆长：T/s平均值和T^2/s^2列显示空白
                    values = []
                    for j, header in enumerate(headers):
                        if header in ["T/s 平均值", "T^2/s^2"]:
                            values.append("")  # 空白
                        else:
                            values.append("点击记录")
                
                self.data_table.insert("", "end", values=values)
                self.data_rows += 1
    
    def update_chart(self):
        """更新图表"""
        self.chart_ax.clear()
        
        # 设置图表标题和坐标轴标签（无论是否有数据都显示）
        if self.experiment_type == "固定摆长改变摆角":
            self.chart_ax.set_xlabel("sin(θ/2)^2")
            self.chart_ax.set_ylabel("2T/s")
            self.chart_ax.set_title("摆长不变时角度θ与2T的测量数据")
            self.update_chart_fixed()
        else:
            self.chart_ax.set_xlabel("L/m")
            self.chart_ax.set_ylabel("T^2/s^2")
            self.chart_ax.set_title("改变摆长L测量周期T的实验数据")
            self.update_chart_variable()
        
        self.chart_ax.grid(True)
        self.chart_canvas.draw()
        
        # 新增：每次更新图表后重新计算重力加速度
        self.calculate_gravity_acceleration()
    
    def update_chart_fixed(self):
        """更新固定摆长图表"""
        # 收集数据
        x_data = []
        y_data = []
        
        for item in self.data_table.get_children():
            values = list(self.data_table.item(item, "values"))
            if values[1] and values[7]:  # sin(θ/2)^2 和 2T/s平均值
                try:
                    x_val = float(values[1])
                    y_val = float(values[7])
                    x_data.append(x_val)
                    y_data.append(y_val)
                except ValueError:
                    continue
        
        # 绘制数据点（始终显示）
        if x_data and y_data:
            # 按x值排序
            sorted_data = sorted(zip(x_data, y_data))
            x_sorted, y_sorted = zip(*sorted_data) if sorted_data else ([], [])
            
            # 绘制散点图
            self.chart_ax.plot(x_sorted, y_sorted, 'o', linewidth=2, markersize=6, label='实验数据')
            
            # 只有在点击计算按钮后才显示拟合结果
            if self.show_calculation and len(x_data) >= 2:
                # 转换为numpy数组以便计算
                x_array = np.array(x_sorted)
                y_array = np.array(y_sorted)
                
                # 线性拟合
                slope, intercept = np.polyfit(x_array, y_array, 1)
                r_squared = self.calculate_r_squared(x_array, y_array, slope, intercept)
                
                # 绘制拟合直线
                fit_x = np.linspace(min(x_array), max(x_array), 100)
                fit_y = slope * fit_x + intercept
                self.chart_ax.plot(fit_x, fit_y, 'r--', linewidth=1.5, label='线性拟合')
                
                # 显示拟合公式和R²值
                formula_text = f'y = {slope:.4f}x + {intercept:.4f}\nR^2 = {r_squared:.4f}'
                self.chart_ax.text(0.05, 0.95, formula_text, transform=self.chart_ax.transAxes,
                                fontsize=10, verticalalignment='top',
                                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                
                # 添加图例
                self.chart_ax.legend(loc='lower right')
            else:
                # 未点击计算按钮或数据不足时，只显示数据点
                if len(x_data) >= 2:
                    self.chart_ax.text(0.5, 0.9, '点击"计算"按钮进行线性拟合', 
                                    horizontalalignment='center', verticalalignment='center',
                                    transform=self.chart_ax.transAxes, fontsize=10, color='gray')
        else:
            self.chart_ax.set_xlim(0, 1)
            self.chart_ax.set_ylim(0, 10)
            self.chart_ax.text(0.5, 0.5, '暂无数据，请点击表格单元格添加数据', 
                            horizontalalignment='center', verticalalignment='center',
                            transform=self.chart_ax.transAxes, fontsize=12, color='gray')
    
    def update_chart_variable(self):
        """更新改变摆长图表"""
        # 收集数据
        x_data = []
        y_data = []
        
        for item in self.data_table.get_children():
            values = list(self.data_table.item(item, "values"))
            if values[0] and values[7]:  # L/m 和 T^2/s^2
                try:
                    x_val = float(values[0])
                    y_val = float(values[7])
                    x_data.append(x_val)
                    y_data.append(y_val)
                except ValueError:
                    continue
        
        # 绘制数据点（始终显示）
        if x_data and y_data:
            # 按x值排序
            sorted_data = sorted(zip(x_data, y_data))
            x_sorted, y_sorted = zip(*sorted_data) if sorted_data else ([], [])
            
            # 绘制散点图
            self.chart_ax.plot(x_sorted, y_sorted, 'o', linewidth=2, markersize=6, label='实验数据')
            
            # 只有在点击计算按钮后才显示拟合结果
            if self.show_calculation and len(x_data) >= 2:
                # 转换为numpy数组以便计算
                x_array = np.array(x_sorted)
                y_array = np.array(y_sorted)
                
                # 线性拟合
                slope, intercept = np.polyfit(x_array, y_array, 1)
                r_squared = self.calculate_r_squared(x_array, y_array, slope, intercept)
                
                # 绘制拟合直线
                fit_x = np.linspace(min(x_array), max(x_array), 100)
                fit_y = slope * fit_x + intercept
                self.chart_ax.plot(fit_x, fit_y, 'r--', linewidth=1.5, label='线性拟合')
                
                # 显示拟合公式和R²值
                formula_text = f'y = {slope:.4f}x + {intercept:.4f}\nR^2 = {r_squared:.4f}'
                self.chart_ax.text(0.05, 0.95, formula_text, transform=self.chart_ax.transAxes,
                                fontsize=10, verticalalignment='top',
                                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                
                # 添加图例
                self.chart_ax.legend(loc='lower right')
            else:
                # 未点击计算按钮或数据不足时，只显示数据点
                if len(x_data) >= 2:
                    self.chart_ax.text(0.5, 0.9, '点击"计算"按钮进行线性拟合', 
                                    horizontalalignment='center', verticalalignment='center',
                                    transform=self.chart_ax.transAxes, fontsize=10, color='gray')
        else:
            self.chart_ax.set_xlim(0, 1)
            self.chart_ax.set_ylim(0, 10)
            self.chart_ax.text(0.5, 0.5, '暂无数据，请点击表格单元格添加数据', 
                            horizontalalignment='center', verticalalignment='center',
                            transform=self.chart_ax.transAxes, fontsize=12, color='gray')

                            
    def calculate_r_squared(self, x, y, slope, intercept):
        """计算R²值（决定系数）"""
        # 计算预测值
        y_pred = slope * x + intercept
        # 计算总平方和
        ss_tot = np.sum((y - np.mean(y))**2)
        # 计算残差平方和
        ss_res = np.sum((y - y_pred)**2)
        # 计算R²
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared

    def delete_selected_row(self):
        """删除选中行"""
        selected = self.data_table.selection()
        if selected:
            for item in selected:
                self.data_table.delete(item)
                self.data_rows -= 1
            self.update_chart()
    
    def clear_data(self):
        """清空数据"""
        if messagebox.askyesno("确认", "确定要清空所有数据吗？"):
            # 清除计算结果
            self.show_calculation = False
            # 清空当前表格数据
            for item in self.data_table.get_children():
                self.data_table.delete(item)
            
            # 清空保存的数据
            self.saved_data[self.experiment_type] = []
            
            # 重新添加初始行
            headers = self.data_headers_fixed if self.experiment_type == "固定摆长改变摆角" else self.data_headers_variable
            for i in range(2):
                if self.experiment_type == "固定摆长改变摆角":
                    values = []
                    for j, header in enumerate(headers):
                        if header in ["sin(θ/2)^2", "2T/s 平均值"]:
                            values.append("")
                        else:
                            values.append("点击记录")
                else:
                    values = []
                    for j, header in enumerate(headers):
                        if header in ["T/s 平均值", "T^2/s^2"]:
                            values.append("")
                        else:
                            values.append("点击记录")
                
                self.data_table.insert("", "end", values=values)
            
            self.data_rows = 2
            
            # 清空图表
            self.chart_ax.clear()
            if self.experiment_type == "固定摆长改变摆角":
                self.chart_ax.set_xlabel("sin(θ/2)^2")
                self.chart_ax.set_ylabel("2T/s")
                self.chart_ax.set_title("摆长不变时角度θ与2T的测量数据")
            else:
                self.chart_ax.set_xlabel("L/m")
                self.chart_ax.set_ylabel("T^2/s^2")
                self.chart_ax.set_title("改变摆长L测量周期T的实验数据")
            self.chart_ax.grid(True)
            self.chart_canvas.draw()

            self.g_value_var.set("点击'计算'按钮显示结果")
            self.error_var.set("点击'计算'按钮显示结果")
    
    def export_data(self):
        """导出数据到Excel"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # 收集数据
                data = []
                headers = self.data_headers_fixed if self.experiment_type == "固定摆长改变摆角" else self.data_headers_variable
                
                for item in self.data_table.get_children():
                    values = list(self.data_table.item(item, "values"))
                    data.append(values)
                
                # 创建DataFrame并导出
                df = pd.DataFrame(data, columns=headers)
                df.to_excel(filename, index=False)
                messagebox.showinfo("成功", f"数据已导出到 {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def import_data(self):
        """从Excel导入数据"""
        filename = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # 读取Excel文件
                df = pd.read_excel(filename)
                
                # 清空现有数据
                for item in self.data_table.get_children():
                    self.data_table.delete(item)
                
                # 添加新数据
                for _, row in df.iterrows():
                    values = [str(cell) if not pd.isna(cell) else "" for cell in row]
                    self.data_table.insert("", "end", values=values)
                
                self.data_rows = len(df) + 1  # 更新行数
                self.update_chart()
                messagebox.showinfo("成功", f"数据已从 {filename} 导入")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {str(e)}")
    
    def update_sensor_position(self, L):
        sensor_length = 0.05
        sensor_y = -self.sensor_position-0.01  # 使用独立的传感器位置
        sensor_x_center = 0
        
        self.sensor_line.set_xy((sensor_x_center - sensor_length/2, sensor_y))
        self.sensor_text.set_position((sensor_x_center, sensor_y - 0.03))
        self.sensor_text.set_text('霍尔传感器')
    
    def update_button_states(self):
        """更新按钮状态：运动时禁用开始按钮，静止时禁用停止按钮"""
        if self.is_animating:
            self.start_btn.config(state=tk.DISABLED) 
            self.stop_btn.config(state=tk.NORMAL) 
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED) 
    
    def on_sensor_change(self, val):
        """处理传感器位置改变"""
        sensor_pos = float(val)
        
        # 确保传感器位置不低于当前摆长
        if sensor_pos < self.current_L:
            sensor_pos = self.current_L
            self.sensor_var.set(sensor_pos)
        
        self.sensor_position = sensor_pos
        self.sensor_label.config(text=f"{sensor_pos:.3f} m")
        
        # 更新传感器显示位置
        self.update_sensor_position(self.current_L)
        
        # 新增：重新计算运动轨迹
        global theta, omega, x, y
        theta, omega = solve_pendulum(self.current_L, theta0)
        x = self.current_L * np.sin(theta)
        y = -self.current_L * np.cos(theta)
        
        # 重置动画状态
        if not self.is_animating:
            self.current_frame = 0
            self.elapsed_time = 0.0
            self.was_at_bottom = False
            self.update_display()

    # 修改后
    def on_length_change(self, val):
        global theta, omega, x, y
        if self.is_animating or self.exp_mode == "查询模式":
            self.length_var.set(self.current_L)
            return
            
        L0 = float(val)
        self.current_L = L0
        self.length_label.config(text=f"{L0:.3f} m")
        
        # 更新传感器位置
        if L0 + 0.01 > self.sensor_position:
            self.sensor_position = L0 + 0.01
            self.sensor_var.set(L0 + 0.01)
            self.sensor_label.config(text=f"{L0 + 0.01:.3f} m")
        
        self.sensor_scale.config(from_=L0 + 0.01)
        self.update_sensor_position(L0 + 0.01)

        # 重新计算运动轨迹
        theta, omega = solve_pendulum(L0, theta0)
        x = L0 * np.sin(theta)
        y = -L0 * np.cos(theta)
        
        # 重新预计算插值数据
        self.precompute_interpolated_data()
        
        self.was_at_bottom = False
        self.update_display()
    
    def on_angle_change(self, val):
        global theta0, theta, omega, x, y
        if self.is_animating or self.exp_mode == "查询模式":
            self.angle_var.set(np.degrees(theta0))
            return
            
        theta0 = np.radians(float(val))
        self.angle_label.config(text=f"{float(val):.0f}°")
        
        theta, omega = solve_pendulum(self.current_L, theta0)
        x = self.current_L * np.sin(theta)
        y = -self.current_L * np.cos(theta)
        
        self.is_animating = False
        self.current_frame = 0
        self.elapsed_time = 0.0
        self.was_at_bottom = False
        
        self.update_display()# 这会触发红灯检测
        self.update_button_states()
    
    def start_animation(self):
        """开始动画（重置帧计数器）"""
        self.is_animating = True
        self.current_frame = 0
        self.sub_frame = 0.0
        self.was_at_bottom = False
        self.update_button_states()
        self.animate()
    
    def reset_to_initial_angle(self):
        """复位到设定的摆角"""
        # 停止动画
        self.is_animating = False
        
        # 重置动画状态
        self.current_frame = 0
        self.sub_frame = 0.0
        self.elapsed_time = 0.0
        self.was_at_bottom = False
        
        
        # 更新显示
        self.update_display()# 这会触发红灯检测
        self.update_button_states()
        
        # # 同时复位实验仪
        # self.on_reset_click()
    
    def animate(self):
        if not self.is_animating:
            return
            
        current_speed = self.time_scale
        
        # 获取当前速度下对应的总帧数
        if current_speed in self.interpolated_data:
            total_frames = self.interpolated_data[current_speed]['total_frames']
        else:
            total_frames = int(len(t) / current_speed)
        
        if self.current_frame < total_frames - 1:
            # 获取插值后的帧数据
            x_val, y_val, theta_val, frame_time = self.get_interpolated_frame(
                self.current_frame, current_speed
            )
            
            # 更新显示
            self.update_display_interpolated(x_val, y_val, theta_val)
            
            # 更新经过的时间（使用原始时间精度）
            self.elapsed_time = frame_time
            
            # 修改：使用插值后的数据进行检测，但增加检测灵敏度
            at_bottom = self.is_at_bottom_improved(y_val, theta_val, current_speed)
            
            # 更新红点颜色
            self.update_red_dot_color(at_bottom)
            
            # 记录逻辑
            if at_bottom and not self.was_at_bottom and self.max_count >= 1:
                if self.exp_mode == "设定模式":
                    # 切换到查询模式
                    self.exp_mode = "查询模式"
                    self.query_start_time = self.elapsed_time
                    self.current_count = 0
                    self.time_records = []
                    self.current_record_index = 0
                    self.mode_label.config(text="模式: 查询模式")
                    self.count_label.config(text="0")
                    self.time_label.config(text="0.000")
                    print("切换到查询模式")
                
                elif self.exp_mode == "查询模式":
                    if self.max_count > 0 and self.current_count < self.max_count:
                        self.current_count += 1
                        T_theoretical = self.calculate_period(self.current_L, np.degrees(theta0))
                    
                        # 根据实验类型选择显示的时间值
                        if self.experiment_type == "固定摆长改变摆角":
                            # 固定摆长实验显示2T（两次周期）
                            time_value = T_theoretical/2*self.current_count
                        else:
                            # 改变摆长实验显示T（单次周期）
                            time_value = T_theoretical/2*self.current_count
                        
                        # 添加随机误差
                        displayed_time = self.add_random_error(time_value)
                        
                        self.time_records.append({
                            'actual': round(time_value, 3),
                            'displayed': displayed_time,
                            'theoretical': True,
                            'period': T_theoretical,
                            'angle': np.degrees(theta0)
                        })
                        self.current_record_index = self.current_count - 1
                        
                        self.count_label.config(text=f"{self.current_count}")
                        self.time_label.config(text=f"{displayed_time:.3f}")
                        
                        print(f"记录第 {self.current_count} 次，理论时间: {displayed_time:.3f}s (摆角: {np.degrees(theta0):.1f}°)")
            
            self.was_at_bottom = at_bottom
            self.current_frame += 1
            
            # 根据速度调整更新间隔，保证检测精度
            update_interval = max(5, int(10 / current_speed))  # 最小5ms间隔
            self.root.after(update_interval, self.animate)
        else:
            self.is_animating = False
            self.update_button_states()
    
    def update_display_interpolated(self, x_val, y_val, theta_val):
        """使用插值数据更新显示"""
        self.line.set_data([0, x_val], [0, y_val])
        self.bob.center = (x_val, y_val)
        
        current_angle_deg = np.degrees(theta_val)
        self.time_text.set_text(f'角度:{current_angle_deg:.0f}°')
        
        self.canvas.draw_idle()  # 使用draw_idle提高效率

    def is_at_bottom_improved(self, y_pos, current_theta, speed_factor):
        """改进的最低点检测方法，适应加速动画"""
        # 计算动态检测阈值，根据速度调整灵敏度
        dynamic_threshold = 0.012 * min(2.0, max(1.0, speed_factor / 2.0))
        angle_threshold = 0.02 * min(2.0, max(1.0, speed_factor / 2.0))
        
        # y坐标检测：使用传感器位置
        target_y = -self.sensor_position
        y_condition = abs(y_pos - target_y) < dynamic_threshold
        
        # 角度检测：角度接近0度
        angle_condition = abs(current_theta) < angle_threshold
        
        # 速度较快时，放宽角度条件，主要依赖y坐标检测
        if speed_factor > 3.0:
            angle_condition = abs(current_theta) < angle_threshold * 2.0
        
        # 调试信息（可选）
        if speed_factor > 2.0 and y_condition:
            print(f"速度{speed_factor:.1f}x: y_diff={abs(y_pos - target_y):.4f}, angle={np.degrees(abs(current_theta)):.2f}°")
        
        return y_condition and angle_condition
    
    def update_red_dot_color(self, is_at_bottom):
        if is_at_bottom:
            self.exp_canvas.itemconfig(self.red_dot_id, fill="white", outline="white")
        else:
            self.exp_canvas.itemconfig(self.red_dot_id, fill="red", outline="red")
    
    # 修改后
    # 修改update_display方法用于静态显示
    def update_display(self):
        """静态显示当前帧"""
        if self.current_frame < len(t):
            self.line.set_data([0, x[self.current_frame]], [0, y[self.current_frame]])
            self.bob.center = (x[self.current_frame], y[self.current_frame])
            self.time_text.set_text(f'角度:{np.degrees(theta[self.current_frame]):.0f}°')
            
            current_y = y[self.current_frame]
            current_theta = theta[self.current_frame]
            at_bottom = self.is_at_bottom_improved(current_y, self.current_L, current_theta)
            self.update_red_dot_color(at_bottom)
            
            self.canvas.draw_idle()
    
    def on_calculate_click(self):
        """计算按钮点击事件"""
        self.show_calculation = True
        self.update_chart()  # 更新图表，显示计算结果
        self.calculate_gravity_acceleration()  # 计算重力加速度

    # 完整的周期计算函数（包含多种精度选项）
    # 计算单摆周期理论值（考虑摆角影响）
    @staticmethod
    def calculate_period(L, theta0_deg):
        """计算单摆周期理论值（考虑摆角影响的精确公式）"""
        theta0_rad = np.radians(theta0_deg)
        
        # 小角度近似公式：T = 2π√(L/g)
        T0 = 2 * np.pi * np.sqrt(L / g)
        
        # 当摆角较小时（<10°），使用小角度近似足够精确
        if abs(theta0_deg) < 3:
            return T0
        
        # 当摆角较大时，使用更精确的公式
        # 使用二阶近似：T ≈ T0 × [1 + (1/4)sin²(θ/2) + (9/64)sin⁴(θ/2) + ...]
        sin_half_theta = np.sin(theta0_rad / 2)
        sin_half_theta_sq = sin_half_theta ** 2
        
        # 二阶近似
        # T_corrected = T0 * (1 + (1/4) * sin_half_theta_sq + (9/64)*sin)
        
        # 如果需要更高精度，可以使用更多项
        # 四阶近似：T ≈ T0 × [1 + (1/4)sin²(θ/2) + (9/64)sin⁴(θ/2)]
        T_corrected = T0 * (1 + (1/4) * sin_half_theta_sq + (9/64) * sin_half_theta_sq**2)
        
        return T_corrected
        
    def on_plus_click(self):
        if self.exp_mode == "设定模式":
            self.max_count += 1
            self.count_label.config(text=f"{self.max_count}")
        elif self.exp_mode == "查询模式":
            if self.current_record_index < len(self.time_records) - 1:
                self.current_record_index += 1
                
                # 使用理论计算值而不是动画时间
                # 计算单摆周期理论值
                T_theoretical = self.calculate_period(self.current_L, np.degrees(theta0))
                
                if self.experiment_type == "固定摆长改变摆角":
                    # 固定摆长实验显示2T（两次周期）
                    time_value = T_theoretical/2*self.current_record_index
                else:
                    # 改变摆长实验显示T（单次周期）
                    time_value = T_theoretical/2*self.current_record_index
                
                # 添加随机误差
                displayed_time = self.add_random_error(time_value)
                
                self.time_records.append({
                    'actual': round(time_value, 3),
                    'displayed': displayed_time,
                    'theoretical': True  # 标记为理论值
                })
                self.current_record_index = self.current_count - 1
                
                self.count_label.config(text=f"{self.current_count}")
                self.time_label.config(text=f"{displayed_time:.3f}")
                
                print(f"记录第 {self.current_count} 次，理论时间: {displayed_time:.3f}s")
            
                record = self.time_records[self.current_record_index]
                self.count_label.config(text=f"{self.current_record_index + 1}")
                self.time_label.config(text=f"{record['displayed']:.3f}")

    
    def on_minus_click(self):
        if self.exp_mode == "设定模式":
            if self.max_count > 0:
                self.max_count -= 1
                self.count_label.config(text=f"{self.max_count}")
        elif self.exp_mode == "查询模式":
            if self.current_record_index > 0:
                self.current_record_index -= 1
                # 使用考虑摆角影响的理论计算值
            T_theoretical = self.calculate_period(self.current_L, np.degrees(theta0))
            
            if self.experiment_type == "固定摆长改变摆角":
                # 固定摆长实验显示2T（两次周期）
                time_value = T_theoretical/2*self.current_record_index
            else:
                # 改变摆长实验显示T（单次周期）
                time_value = T_theoretical/2*self.current_record_index
            
            # 添加随机误差
            displayed_time = self.add_random_error(time_value)
            
            self.time_records.append({
                'actual': round(time_value, 3),
                'displayed': displayed_time,
                'theoretical': True,
                'period': T_theoretical,  # 保存周期值
                'angle': np.degrees(theta0)  # 保存摆角
            })
            
            self.count_label.config(text=f"{self.current_count}")
            self.time_label.config(text=f"{displayed_time:.3f}")
            
            print(f"记录第 {self.current_count} 次，理论时间: {displayed_time:.3f}s (摆角: {np.degrees(theta0):.1f}°)")
    
    def on_reset_click(self):
        self.exp_mode = "设定模式"
        self.max_count = 0
        self.current_count = 0
        self.time_records = []
        self.current_record_index = 0
        self.mode_label.config(text="模式: 设定模式")
        self.count_label.config(text="--")
        self.time_label.config(text="0.000")
        # self.stop_animation()
        self.was_at_bottom = False

def main():
    root = tk.Tk()
    app = PendulumSimulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()