import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
from matplotlib.widgets import Slider
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk 
import os
import sys
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def resource_path(relative_path):
    """获取资源的绝对路径，支持开发模式和打包后模式"""
    try:
        # 打包后，sys._MEIPASS 属性包含临时文件夹路径
        base_path = sys._MEIPASS
    except Exception:
        # 开发模式下，使用当前文件所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class PhysicalPendulum:
    def __init__(self, length=0.7, mass=0.625, center_of_mass=0.35, 
                 initial_angle=np.radians(5), pivot_position=0.5, height_offset=0.0):
        self.length = length  # 刚体长度
        self.mass = mass      # 质量
        self.com = center_of_mass  # 质心位置（从起点开始）
        self.pivot_position = pivot_position  # 转轴位置（0-1，相对于杆长的比例）
        self.height_offset = height_offset  # 高度偏移量
        
        # 计算相对于转轴的质心距离
        self.effective_com = abs(self.com - self.pivot_position * self.length)
        
        # 使用平行轴定理计算转动惯量
        # 绕质心的转动惯量（细杆）
        I_cm = (1/12) * mass * length**2
        # 使用平行轴定理计算绕转轴的转动惯量
        self.I = I_cm + mass * self.effective_com**2
            
        self.angle = initial_angle
        self.angular_velocity = 0.0
        self.g = 9.81
        
        # 记录轨迹
        self.trajectory = []
        self.max_trajectory_length = 200

        # 摆锤相关属性
        self.hammer_a_placed = False
        self.hammer_b_placed = False
        self.hammer_a_position = 0.3  # 从起点开始的比例
        self.hammer_b_position = 0.6  # 从起点开始的比例
        self.hammer_mass = 0.125  # 每个摆锤的质量

    def recalculate_properties(self):
        """重新计算物理属性（考虑摆锤）"""
        # 基础转动惯量（细杆）
        I_cm_rod = (1/12) * self.mass * self.length**2
        
        # 总质量（包括摆锤）
        total_mass = self.mass
        if self.hammer_a_placed:
            total_mass += self.hammer_mass
        if self.hammer_b_placed:
            total_mass += self.hammer_mass
        
        # 计算新的质心位置（从起点开始）
        moment_sum = self.mass * 0.5 * self.length  # 杆的质心在中心位置
        
        if self.hammer_a_placed:
            moment_sum += self.hammer_mass * self.hammer_a_position * self.length
        
        if self.hammer_b_placed:
            moment_sum += self.hammer_mass * self.hammer_b_position * self.length
        
        # 新的质心位置（从起点开始）
        if total_mass > 0:
            self.com = moment_sum / total_mass
        else:
            self.com = 0.5 * self.length  # 默认质心在杆中心
        
        # 计算相对于转轴的质心距离
        self.effective_com = abs(self.com - self.pivot_position * self.length)
        
        # 计算总转动惯量（使用平行轴定理）
        # 杆的转动惯量（相对于转轴）
        rod_distance = abs(0.5 * self.length - self.pivot_position * self.length)
        total_I = I_cm_rod + self.mass * rod_distance**2
        # print("I_cm_rod =",I_cm_rod,total_I)
        
        # 添加摆锤的转动惯量贡献（点质量）
        if self.hammer_a_placed:
            hammer_a_distance = abs(self.hammer_a_position * self.length - self.pivot_position * self.length)
            total_I += self.hammer_mass * hammer_a_distance**2
        
        if self.hammer_b_placed:
            hammer_b_distance = abs(self.hammer_b_position * self.length - self.pivot_position * self.length)
            total_I += self.hammer_mass * hammer_b_distance**2
        
        self.I = total_I
        print("")

    
    def update_hammer_a(self, placed, position=None):
        """更新摆锤A状态"""
        self.hammer_a_placed = placed
        if position is not None:
            self.hammer_a_position = position
        self.recalculate_properties()
    
    def update_hammer_b(self, placed, position=None):
        """更新摆锤B状态"""
        self.hammer_b_placed = placed
        if position is not None:
            self.hammer_b_position = position
        self.recalculate_properties()

    def update_pivot(self, new_pivot_position, current_angle_degrees=None):
        """更新转轴位置"""
        self.pivot_position = new_pivot_position
        
        # 重新计算所有物理属性（包括摆锤影响）
        self.recalculate_properties()
        
        # 如果提供了当前角度，使用它；否则保持当前角度
        if current_angle_degrees is not None:
            self.angle = np.radians(current_angle_degrees)
        self.angular_velocity = 0.0
        # 不清空轨迹，保持轨迹连续性
        # self.tendulum.trajectory = []  # 注释掉这行以保持轨迹
    
    def update_angle(self, new_angle_degrees):
        """更新摆角（角度制）"""
        self.angle = np.radians(new_angle_degrees)
        self.angular_velocity = 0.0  # 重置角速度
    
    def update_height(self, new_height_offset):
        """更新复摆高度"""
        self.height_offset = new_height_offset
    
    def update(self, dt):
        """更新复摆状态"""
        # 如果有效质心距很小，几乎不运动
        if self.effective_com < 1e-3:
            self.angular_velocity = 0
            return
        
        # 计算角加速度：τ = Iα, τ = -mgd sinθ
        torque = -self.mass * self.g * self.effective_com * np.sin(self.angle)
        angular_acceleration = torque / self.I
        
        # 使用欧拉-克罗默方法更新
        self.angular_velocity += angular_acceleration * dt
        self.angle += self.angular_velocity * dt
        
        # 记录质心轨迹
        com_x = self.effective_com * np.sin(self.angle)
        com_y = -self.effective_com * np.cos(self.angle) + self.height_offset
        self.trajectory.append((com_x, com_y))
        
        # 限制轨迹长度
        if len(self.trajectory) > self.max_trajectory_length:
            self.trajectory.pop(0)
    
    def get_positions(self, hanging_mode="正挂"):
        """获取关键点的位置（包括摆锤）"""
        # 转轴位置固定在原点，加上高度偏移
        pivot = (0, self.height_offset)
        
        # 计算杆的起点和终点位置（相对于转轴）
        start_offset = -self.pivot_position * self.length
        end_offset = (1 - self.pivot_position) * self.length
        
        # 使用相同的角度计算所有位置
        angle = self.angle

        # 计算起点和终点位置
        start_x = start_offset * np.sin(angle)
        start_y = -start_offset * np.cos(angle) + self.height_offset
        end_x = end_offset * np.sin(angle)
        end_y = -end_offset * np.cos(angle) + self.height_offset
        
        # 质心位置
        com_offset = self.com - self.pivot_position * self.length
        com_x = com_offset * np.sin(angle)
        com_y = -com_offset * np.cos(angle) + self.height_offset
        
        # 摆锤位置
        hammer_a_pos = None
        hammer_b_pos = None

        if self.hammer_a_placed:
            # 计算摆锤相对于转轴的位置
            hammer_a_offset = self.hammer_a_position * self.length - self.pivot_position * self.length
            hammer_a_x = hammer_a_offset * np.sin(angle)
            hammer_a_y = -hammer_a_offset * np.cos(angle) + self.height_offset
            hammer_a_pos = (hammer_a_x, hammer_a_y)
            # print(f"摆锤A原始计算: 位置比例={self.hammer_a_position:.3f}, 转轴比例={self.pivot_position:.3f}, 偏移={hammer_a_offset:.3f}m")
            # print(f"摆锤A原始坐标: ({hammer_a_x:.3f}, {hammer_a_y:.3f}), 角度={np.degrees(angle):.1f}°")

        if self.hammer_b_placed:
            # 计算摆锤相对于转轴的位置
            hammer_b_offset = self.hammer_b_position * self.length - self.pivot_position * self.length
            hammer_b_x = hammer_b_offset * np.sin(angle)
            hammer_b_y = -hammer_b_offset * np.cos(angle) + self.height_offset
            hammer_b_pos = (hammer_b_x, hammer_b_y)
            # print(f"摆锤B原始计算: 位置比例={self.hammer_b_position:.3f}, 转轴比例={self.pivot_position:.3f}, 偏移={hammer_b_offset:.3f}m")
            # print(f"摆锤B原始坐标: ({hammer_b_x:.3f}, {hammer_b_y:.3f}), 角度={np.degrees(angle):.1f}°")
        
        # 如果是倒挂模式，以转轴为中心进行对称变换
        if hanging_mode == "倒挂":
            # print(f"=== 倒挂模式对称变换 ===")
            # print(f"转轴中心: (0, {self.height_offset:.3f})")
            
            # 对起点、终点、质心和摆锤进行对称变换
            # 对称变换：相对于转轴(0, height_offset)进行中心对称
            def symmetric_transform(point, name):
                x, y = point
                new_x = -x
                new_y = 2 * self.height_offset - y
                # print(f"{name}对称变换: ({x:.3f}, {y:.3f}) -> ({new_x:.3f}, {new_y:.3f})")
                return (new_x, new_y)
            
            start = symmetric_transform((start_x, start_y), "起点")
            end = symmetric_transform((end_x, end_y), "终点")
            com = symmetric_transform((com_x, com_y), "质心")
            
            if hammer_a_pos:
                hammer_a_pos = symmetric_transform(hammer_a_pos, "摆锤A")
            if hammer_b_pos:
                hammer_b_pos = symmetric_transform(hammer_b_pos, "摆锤B")
            
            # print("=== 对称变换完成 ===\n")
            return pivot, start, end, com, hammer_a_pos, hammer_b_pos
        else:
            # print(f"正挂模式 - 转轴高度: {self.height_offset:.3f}\n")
            return pivot, (start_x, start_y), (end_x, end_y), (com_x, com_y), hammer_a_pos, hammer_b_pos

    def get_period(self):
        """计算小角度近似下的周期"""
        if self.effective_com < 1e-3:
            return float('inf')  # 转轴在质心时周期为无穷大
        total_mass = self.mass
        if self.hammer_a_placed:
            total_mass += self.hammer_mass
        if self.hammer_b_placed:
            total_mass += self.hammer_mass

        period = 2 * np.pi * np.sqrt(self.I / (total_mass * self.g * self.effective_com))
        return period

class IntegratedApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FD-CP-A复摆实验仪")
        self.root.geometry("1600x840")
        self.root.resizable(False, False)
        self.export_in_progress = False
        self.power_on = False  # 电源状态，初始为关闭
        # 主界面高亮背景矩形
        self.period_bg_rect = None
        self.pulse_bg_rect = None

        self.period_measurement_mode = "设定模式"  # "设定模式" 或 "测量模式"
        self.max_record_count = 10  # 最大记录次数
        self.current_measure_count = 0  # 当前测量次数
        self.temp_measure_data = []  # 临时测量数据
        self.period_data_groups = []  # 存储多组周期测量数据
        self.current_query_group = 0  # 当前查询的组索引
        self.measurement_start_time = 0  # 测量开始时间
        # 当前选中的测量模式
        self.measurement_mode = "周期测量"  # 初始选中周期测量
        
        # 在现有初始化代码中添加以下变量
        self.gate_triggered = False  # 光电门触发状态
        self.last_gate_state = False  # 上一次光电门状态（用于边缘检测）
        self.gate_dot = None  # 光电门红点

        # 连续调整相关属性
        self.continuous_adjust_running = False
        self.continuous_adjust_type = None
        self.continuous_adjust_delta = 0

        # 摆锤A和B的状态
        self.hammer_a_placed = False  # 摆锤A是否放置
        self.hammer_b_placed = False  # 摆锤B是否放置
        self.hammer_a_position = 0.3  # 摆锤A位置（从起点开始的比例，0-1）
        self.hammer_b_position = 0.6  # 摆锤B位置（从起点开始的比例，0-1）
        
        # 摆锤物理参数
        self.hammer_mass = 0.125  # 摆锤质量（kg）

        # 周期测量界面状态
        self.period_ui_active = False  # 是否显示周期测量界面
        self.period_mode = "单周"  # 周期模式：单周/双周
        self.measure_count = 0  # 测量次数
        self.measure_time = 0  # 测量时间
        
        # 周期测量界面选择状态
        self.period_selection_index = 0  # 当前选中的栏目索引
        self.period_items_count = 5  # 可选择的栏目数量（不包括时间）
        self.setting_count = False  # 是否正在设置次数
        
        # 脉宽测量界面状态
        self.pulse_ui_active = False  # 是否显示脉宽测量界面
        self.pulse_time = 0  # 脉宽测量时间（ms）
        self.pulse_count = 0  # 脉宽测量次数
        
        # 脉宽测量界面选择状态
        self.pulse_selection_index = 1  # 当前选中的栏目索引（初始选中次数）
        self.pulse_items_count = 4  # 可选择的栏目数量（不包括时间和空白行）
        self.setting_pulse_count = False  # 是否正在设置脉宽次数
        
        self.pulse_measurement_mode = "设定模式"  # "设定模式" 或 "测量模式"
        self.pulse_data_groups = []  # 存储多组脉宽测量数据
        self.current_pulse_query_group = 0  # 当前查询的组索引
        self.temp_pulse_data = []  # 临时脉宽测量数据
        self.current_pulse_measure_count = 0  # 当前测量次数

        # 脉宽查询模式状态
        self.pulse_query_mode_state = "group_select"  # "group_select" 或 "data_scroll"
        self.pulse_query_start_index = 0

        # 实验数据存储 - 确保所有键都存在
        self.experiment_data = {
            "gravity_method1": {},
            "gravity_method2": {
                "table_data": [],
                "xy_data_points": [],
                "g": "",
                "e": ""
            },
            "gravity_method3": {},
            "moment_of_inertia": {},
            "parallel_axis": {}
        }
    

        # 创建复摆实例
        self.pendulum = PhysicalPendulum(
            length=0.7,
            mass=0.625,
            center_of_mass=0.35,
            initial_angle=np.radians(5),
            pivot_position=0.5,
            height_offset=0.0  # 初始高度偏移为0
        )
        
        # 动画控制状态
        self.animation_running = False  # 动画是否正在运行
        
        self.setup_ui()
        self.setup_animation()
        
    
    def show_export_progress(self, message="正在导出..."):
        """显示导出进度提示"""
        if hasattr(self, 'export_progress_window') and self.export_progress_window.winfo_exists():
            self.export_progress_window.destroy()
        
        self.export_progress_window = tk.Toplevel(self.root)
        self.export_progress_window.title("导出数据")
        self.export_progress_window.geometry("300x100")
        self.export_progress_window.transient(self.root)
        self.export_progress_window.grab_set()
        
        # 居中显示
        self.export_progress_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 300) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 100) // 2
        self.export_progress_window.geometry(f"+{x}+{y}")
        
        ttk.Label(self.export_progress_window, text=message, font=("Arial", 12)).pack(pady=20)
        
        # 进度条
        self.export_progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(self.export_progress_window, variable=self.export_progress_var, 
                                    mode='indeterminate', length=250)
        progress_bar.pack(pady=10)
        progress_bar.start(10)

    def hide_export_progress(self):
        """隐藏导出进度提示"""
        if hasattr(self, 'export_progress_window') and self.export_progress_window.winfo_exists():
            self.export_progress_window.destroy()

        
    def setup_ui(self):
        # 创建主框架 - 左右布局
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：动画区域
        left_frame = ttk.Frame(main_frame, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_frame.pack_propagate(False)
        
        
        # 右侧：实验仪控制面板
        right_frame = ttk.Frame(main_frame, width=900)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # 设置左侧动画区域
        self.setup_animation_area(left_frame)
        
        # 设置右侧控制面板
        self.setup_control_panel(right_frame)

        # 单行修复：禁用Tkinter的自动重绘
        self.root.update_idletasks()
        self.root.option_add('*TkFDialog*foreground', 'black')
        
        # 禁用Canvas的自动更新
        self.canvas._tkcanvas.config(highlightthickness=0)
        self.canvas._tkcanvas.pack_propagate(0)
    
    def load_background_images(self):
        """加载并显示背景图片"""
        try:
            # 图片文件路径 - 使用 resource_path 包装
            image_files = {
                'gate': resource_path(os.path.join('background', 'gate.jpg')),
                'angle': resource_path(os.path.join('background', 'angle.jpg')), 
                'grid': resource_path(os.path.join('background', 'grid.jpg')),
                'device': resource_path(os.path.join('background', 'device.jpg'))
            }
            
            # 图片位置和大小配置
            image_configs = {
                'gate': {'extent': [-0.05, 0.03, -0.75, -0.65], 'zorder': 4},    
                'angle': {'extent': [-0.052, 0.05, -0.05, 0.05], 'zorder': 3},      
                'grid': {'extent': [0.2, 0.2, -0.8, 0.4], 'zorder': 1},      
                'device': {'extent': [-0.225, 0.175, -0.8, 0.4], 'zorder': 2}       
            }
            
            self.background_images = {}
            
            for image_name, image_path in image_files.items():
                if os.path.exists(image_path):
                    # 加载图片
                    img = plt.imread(image_path)
                    config = image_configs[image_name]
                    
                    # 显示图片
                    im = self.ax.imshow(img, extent=config['extent'], 
                                    zorder=config['zorder'], alpha=0.9)
                    self.background_images[image_name] = im
                    print(f"成功加载背景图片: {os.path.basename(image_path)}")
                else:
                    print(f"背景图片未找到: {image_path}")
                    
        except Exception as e:
            print(f"加载背景图片时发生错误: {e}")

    def on_pivot_slider_changed(self, value):
        """处理转轴位置滑块变化"""
        # 如果动画正在运行，不响应调整
        if self.animation_running:
            return
            
        pivot_pos = float(value)
        
        # 计算当前细杆位置限制
        current_height = self.height_var.get()
        pendulum_length = self.pendulum.length
        
        # 计算起点和末端位置（相对于转轴）
        start_offset = -pivot_pos * pendulum_length  # 起点在转轴上方
        end_offset = (1 - pivot_pos) * pendulum_length  # 末端在转轴下方
        
        # 计算绝对位置（考虑高度偏移）
        if self.hanging_mode == "正挂":
            start_y = -start_offset + current_height  # 起点实际Y坐标（注意符号）
            end_y = -end_offset + current_height      # 末端实际Y坐标
        else:
            # 倒挂模式：起点在下方，末端在上方
            start_y = start_offset + current_height   # 起点实际Y坐标
            end_y = end_offset + current_height       # 末端实际Y坐标
        
        # 检查限制条件
        if self.hanging_mode == "正挂":
            if start_y > 0.36:  # 起点不能高于0.4
                # 自动调整到最大允许位置
                max_start_y = 0.36
                required_start_offset = max_start_y - current_height
                pivot_pos = (required_start_offset) / pendulum_length
                print(f"current_height:",current_height,f"pivot_pos:",pivot_pos,f"pendulum_length",pendulum_length)
                pivot_pos = max(0.3, min(1.0, pivot_pos))
                self.pivot_var.set(pivot_pos)
                print(f"起点位置限制：自动调整转轴位置到 {pivot_pos:.3f}")
            
            if end_y < -0.65:  # 末端不能低于-0.65
                # 自动调整到最大允许位置
                min_end_y = -0.65
                required_end_offset = current_height - min_end_y
                pivot_pos = 1.0 - (required_end_offset / pendulum_length)
                pivot_pos = max(0.1, min(1.0, pivot_pos))
                self.pivot_var.set(pivot_pos)
                print(f"末端位置限制：自动调整转轴位置到 {pivot_pos:.3f}")
        else:
            # 倒挂模式的限制
            if start_y < -0.65:  # 起点不能低于-0.65
                # 自动调整到最大允许位置
                min_start_y = -0.65
                required_start_offset = min_start_y - current_height
                pivot_pos = (-required_start_offset) / pendulum_length
                pivot_pos = max(0.45, min(1.0, pivot_pos))
                self.pivot_var.set(pivot_pos)
                print(f"倒挂起点位置限制：自动调整转轴位置到 {pivot_pos:.3f}")
            
            if end_y > 0.35:  # 末端不能高于0.4
                # 自动调整到最大允许位置
                max_end_y = 0.35
                required_end_offset = max_end_y - current_height
                pivot_pos = 1.0 - (required_end_offset / pendulum_length)
                print(f"pivot_pos",pivot_pos)
                pivot_pos = max(0.1, min(1.0, pivot_pos))
                self.pivot_var.set(pivot_pos)
                print(f"倒挂末端位置限制：自动调整转轴位置到 {pivot_pos:.3f}")
        
        # 获取当前角度滑块的值
        current_angle_degrees = self.angle_var.get()
        # 传递当前角度给pendulum
        self.pendulum.update_pivot(pivot_pos, current_angle_degrees)
        
        # 修改：将转轴位置改为起点到转轴的距离（单位mm）
        pivot_distance_mm = pivot_pos * self.pendulum.length * 1000  # 转换为mm
        self.pivot_label.config(text=f"{pivot_distance_mm:.0f}mm")
        
        # 当转轴位置变化时，重新检查并限制光电门位置
        current_gate_pos = self.gate_var.get()
        self.on_gate_slider_changed(current_gate_pos)

    def on_gate_slider_changed(self, value):
        """处理光电门位置滑块变化"""
        gate_pos = float(value)
        
        # 计算复摆末端的最低位置（考虑高度偏移）
        pendulum_length = self.pendulum.length
        pivot_position = self.pendulum.pivot_position
        height_offset = self.pendulum.height_offset
        
        # 末端相对于转轴的最大偏移（当摆角为0度时）
        end_offset = (1 - pivot_position) * pendulum_length
        
        if self.hanging_mode == "正挂":
            # 正挂模式：末端的最低位置（当摆角为0度时，末端在最低点）
            end_min_y = -end_offset + height_offset
        else:
            # 倒挂模式：末端的最低位置（当摆角为0度时，末端在最低点）
            end_min_y = -pivot_position * pendulum_length + height_offset
        
        # 限制光电门位置不能超过末端-0.1m
        max_gate_pos = end_min_y - 0.1
        
        # 如果当前值超过限制，自动调整
        if gate_pos > max_gate_pos:
            gate_pos = max_gate_pos
            self.gate_var.set(gate_pos)
        
        # 更新光电门图片的位置
        if 'gate' in self.background_images:
            # 计算新的图片位置（保持宽度不变，只改变垂直位置）
            new_extent = [-0.05, 0.03, gate_pos, gate_pos + 0.1]  # 高度保持0.1m
            self.background_images['gate'].set_extent(new_extent)
            # 强制刷新画布
            self.canvas.draw_idle()
        
        # 修改：将光电门位置改为mm表示
        gate_pos_mm = gate_pos * 1000  # 转换为mm
        self.gate_label.config(text=f"{gate_pos_mm:.0f}mm")
    
    def on_angle_slider_changed(self, value):
        """处理摆角滑块变化"""
        if self.animation_running:
            return
        angle_degrees = float(value)
        self.pendulum.update_angle(angle_degrees)
        self.angle_label.config(text=f"{angle_degrees:.0f}°")
    
    def on_height_slider_changed(self, value):
        """处理复摆高度滑块变化"""
        if self.animation_running:
            return
                
        height_offset = float(value)
        
        # 计算当前细杆位置限制
        current_pivot = self.pivot_var.get()
        pendulum_length = self.pendulum.length
        
        # 计算起点和末端位置（相对于转轴）
        start_offset = -current_pivot * pendulum_length  # 起点在转轴上方
        end_offset = (1 - current_pivot) * pendulum_length  # 末端在转轴下方
        
        # 计算绝对位置（考虑高度偏移）
        if self.hanging_mode == "正挂":
            start_y = -start_offset + height_offset  # 起点实际Y坐标（注意符号）
            end_y = -end_offset + height_offset      # 末端实际Y坐标
        else:
            # 倒挂模式：起点在下方，末端在上方
            start_y = start_offset + height_offset   # 起点实际Y坐标
            end_y = end_offset + height_offset       # 末端实际Y坐标
        
        # 检查限制条件
        if self.hanging_mode == "正挂":
            if start_y > 0.4:  # 起点不能高于0.4
                # 自动调整到最大允许高度
                max_height = 0.4 + start_offset
                height_offset = max_height
                self.height_var.set(height_offset)
                print(f"起点位置限制：自动调整高度到 {height_offset:.3f}")
            
            if end_y < -0.65:  # 末端不能低于-0.65
                # 自动调整到最小允许高度
                min_height = -0.65 + end_offset
                height_offset = min_height
                self.height_var.set(height_offset)
                print(f"末端位置限制：自动调整高度到 {height_offset:.3f}")
        else:
            # 倒挂模式的限制
            if start_y < -0.65:  # 起点不能低于-0.65
                # 自动调整到最小允许高度
                min_height = -0.65 - start_offset
                height_offset = min_height
                self.height_var.set(height_offset)
                print(f"倒挂起点位置限制：自动调整高度到 {height_offset:.3f}")
            
            if end_y > 0.36:  # 末端不能高于0.4
                # 自动调整到最大允许高度
                max_height = 0.36 - end_offset
                height_offset = max_height
                self.height_var.set(height_offset)
                print(f"倒挂末端位置限制：自动调整高度到 {height_offset:.3f}")
        
        self.pendulum.update_height(height_offset)
        
        # 修改：将复摆高度改为mm表示
        height_offset_mm = height_offset * 1000  # 转换为mm
        self.height_label.config(text=f"{height_offset_mm:.0f}mm")
        
        # 更新角度图片的位置，使其与复摆同步移动
        if 'angle' in self.background_images:
            # 计算新的角度图片位置，保持相对位置不变
            new_extent = [-0.052, 0.05, height_offset - 0.05, height_offset + 0.05]
            self.background_images['angle'].set_extent(new_extent)
            # 强制刷新画布
            self.canvas.draw_idle()
        
        # 当复摆高度变化时，重新检查并限制光电门位置
        current_gate_pos = self.gate_var.get()
        self.on_gate_slider_changed(current_gate_pos)

    
    def toggle_animation(self):
        """切换动画运行状态"""
        if self.animation_running:
            # 停止动画
            self.animation_running = False
            self.start_stop_button.config(text="开始")
            # 启用所有控件
            self.enable_controls(True)
            # 复位复摆
            self.reset_pendulum()
        else:
            # 检查质心位置
            pivot_pos = self.pivot_var.get() * self.pendulum.length
            com_pos = self.pendulum.com
            
            # 如果质心高于转轴，禁止开始
            if self.hanging_mode == "正挂":
                if com_pos <= pivot_pos:
                    tk.messagebox.showwarning("警告", "质心必须低于转轴！")
                    return
            else:
                if com_pos >= pivot_pos:
                    tk.messagebox.showwarning("警告", "质心必须低于转轴！")
                    return
            # 开始动画
            self.animation_running = True
            self.start_stop_button.config(text="停止")
            # 禁用所有控件
            self.enable_controls(False)
    
    def enable_controls(self, enabled):
        """启用或禁用所有控制控件"""
        state = "normal" if enabled else "disabled"
        
        # 挂载模式按钮
        self.normal_hanging_btn.config(state=state)
        self.inverted_hanging_btn.config(state=state)

        # 转轴位置滑块和按钮
        self.pivot_slider.config(state=state)
        self.pivot_minus_btn.config(state=state)
        self.pivot_plus_btn.config(state=state)
        
        # 光电门位置滑块和按钮
        self.gate_slider.config(state=state)
        self.gate_minus_btn.config(state=state)
        self.gate_plus_btn.config(state=state)
        
        # 摆角滑块和按钮
        self.angle_slider.config(state=state)
        self.angle_minus_btn.config(state=state)
        self.angle_plus_btn.config(state=state)
        
        # 复摆高度滑块和按钮
        self.height_slider.config(state=state)
        self.height_minus_btn.config(state=state)
        self.height_plus_btn.config(state=state)
        
        # 摆锤A控制
        if self.hammer_a_placed:
            self.hammer_a_slider.config(state=state)
            self.hammer_a_minus_btn.config(state=state)
            self.hammer_a_plus_btn.config(state=state)
        self.hammer_a_button.config(state=state)
        
        # 摆锤B控制
        if self.hammer_b_placed:
            self.hammer_b_slider.config(state=state)
            self.hammer_b_minus_btn.config(state=state)
            self.hammer_b_plus_btn.config(state=state)
        self.hammer_b_button.config(state=state)

    def reset_pendulum(self):
        """复位复摆到初始状态"""
        current_angle = self.angle_var.get()
        self.pendulum.angle = np.radians(current_angle)
        self.pendulum.angular_velocity = 0.0
        self.pendulum.trajectory = []
        # 更新动画显示
        self.update_animation(0)
        
    def setup_animation_area(self, parent):
        # 创建matplotlib图形 - 调整图形大小，为滑块留出空间
        self.fig = plt.figure(figsize=(3, 5))  # 减小高度
        
        # 调整子图位置，为底部控件留出空间
        self.ax = self.fig.add_axes([0.15, 0.1, 0.7, 0.8])  # [left, bottom, width, height]
        
        # 修改：调整坐标范围以适应0.7m杆长和高度调整
        self.ax.set_xlim(-0.5, 0.5)
        self.ax.set_ylim(-0.8, 0.4)
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_title('复摆运动', fontsize=14, fontweight='bold')
        self.ax.set_xlabel('x (米)')
        self.ax.set_ylabel('y (米)')
        
        # 加载并显示背景图片
        self.load_background_images()
        
        # 创建图形元素
        # 摆杆
        self.rod, = self.ax.plot([], [], 'b-', linewidth=4, alpha=0.7)
        
        # 新增：延长部分（头尾各3cm）
        self.rod_extension_start, = self.ax.plot([], [], 'b-', linewidth=4/3, alpha=0.7)  # 宽度为原杆的1/3
        self.rod_extension_end, = self.ax.plot([], [], 'b-', linewidth=4/3, alpha=0.7)    # 宽度为原杆的1/3

        # 转轴（固定在原点）
        self.pivot_point = Circle((0, 0), 0.02, color='red', zorder=5)  # 修改：调整转轴点大小
        self.ax.add_patch(self.pivot_point)

        # 光电门红点（初始不可见）
        self.gate_dot = Circle((0, 0), 0.015, color='red', zorder=10, visible=False)
        self.ax.add_patch(self.gate_dot)
        
        self.start_label = self.ax.text(0, 0, "0", fontsize=10, color='red', zorder=10, 
                                   ha='center', va='center', fontweight='bold')
        self.end_label = self.ax.text(0, 0, "70", fontsize=10, color='red', zorder=10, 
                                 ha='center', va='center', fontweight='bold')

        # 摆锤A（初始不可见）- 改为方形
        self.hammer_a_rect = plt.Rectangle((0, 0), 0.05, 0.05, color='purple', zorder=6, visible=False)
        self.ax.add_patch(self.hammer_a_rect)

        # 摆锤B（初始不可见）- 改为方形
        self.hammer_b_rect = plt.Rectangle((0, 0), 0.05, 0.05, color='green', zorder=6, visible=False)
        self.ax.add_patch(self.hammer_b_rect)

        # 质心
        self.com_point = Circle((0, 0), 0.00, color='green', zorder=5)  # 修改：调整质心点大小
        self.ax.add_patch(self.com_point)
        
        # 末端点
        self.end_point = Circle((0, 0), 0.00, color='blue', zorder=5)  # 修改：调整末端点大小
        self.ax.add_patch(self.end_point)
        
        # 起点（杆的另一端）
        self.start_point = Circle((0, 0), 0.00, color='orange', zorder=5)  # 修改：调整起点大小
        self.ax.add_patch(self.start_point)
        
        # 轨迹
        self.trajectory, = self.ax.plot([], [], 'r-', alpha=0.5, linewidth=0)
        
        # 信息文本
        self.info_text = self.ax.text(0.02, 0.98, '', transform=self.ax.transAxes, 
                                    verticalalignment='top', fontsize=8,
                                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 添加图例标注（包括摆锤）- 更新为方形
        self.ax.plot([], [], 'ro', markersize=8, label='转轴')
        self.ax.plot([], [], 's', color='purple', markersize=8, label='摆锤A')  # 方形
        self.ax.plot([], [], 's', color='green', markersize=8, label='摆锤B')  # 方形
        self.ax.legend(loc='lower right')
        
        # 将matplotlib图形嵌入到tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建滑块框架
        slider_frame = ttk.Frame(parent)
        slider_frame.pack(fill=tk.X, pady=(0, 5))

        # 挂载模式部分 - 放在最上面
        hanging_mode_frame = ttk.Frame(slider_frame)
        hanging_mode_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(hanging_mode_frame, text="挂载模式:").pack(side=tk.LEFT, padx=(10, 5))
    
        # 挂载模式变量
        self.hanging_mode = "正挂"  # 初始为正挂
        
        # 正挂按钮
        self.normal_hanging_btn = ttk.Button(
            hanging_mode_frame,
            text="正挂",
            command=lambda: self.set_hanging_mode("正挂"),
            width=8
        )
        self.normal_hanging_btn.pack(side=tk.LEFT, padx=(5, 2))
        
        # 倒挂按钮
        self.inverted_hanging_btn = ttk.Button(
            hanging_mode_frame,
            text="倒挂",
            command=lambda: self.set_hanging_mode("倒挂"),
            width=8
        )
        self.inverted_hanging_btn.pack(side=tk.LEFT, padx=(2, 5))
        
        # 初始高亮正挂按钮
        self.update_hanging_buttons_style()

        # 转轴位置滑块
        pivot_frame = ttk.Frame(slider_frame)
        pivot_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(pivot_frame, text="转轴位置:").pack(side=tk.LEFT, padx=(10, 5))
        self.pivot_var = tk.DoubleVar(value=0.5)
        self.pivot_slider = ttk.Scale(pivot_frame, from_=0.0, to=1.0, 
                                    orient=tk.HORIZONTAL, variable=self.pivot_var,
                                    command=self.on_pivot_slider_changed)
        self.pivot_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 添加微调按钮
        pivot_button_frame = ttk.Frame(pivot_frame)
        pivot_button_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.pivot_minus_btn = ttk.Button(pivot_button_frame, text="-", width=2
                                        )
        self.pivot_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.pivot_plus_btn = ttk.Button(pivot_button_frame, text="+", width=2,
                                    )
        self.pivot_plus_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 绑定长按事件
        self.pivot_minus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("pivot", -0.001))
        self.pivot_minus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())
        self.pivot_plus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("pivot", 0.001))
        self.pivot_plus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())

        self.pivot_label = ttk.Label(pivot_frame, text="350mm", width=7)
        self.pivot_label.pack(side=tk.RIGHT, padx=(5, 10))
        
        # 光电门位置滑块
        gate_frame = ttk.Frame(slider_frame)
        gate_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(gate_frame, text="光电门位置:").pack(side=tk.LEFT, padx=(10, 5))
        self.gate_var = tk.DoubleVar(value=-0.75)
        self.gate_slider = ttk.Scale(gate_frame, from_=-0.75, to=0.0,
                                orient=tk.HORIZONTAL, variable=self.gate_var,
                                command=self.on_gate_slider_changed)
        self.gate_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 添加微调按钮
        gate_button_frame = ttk.Frame(gate_frame)
        gate_button_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.gate_minus_btn = ttk.Button(gate_button_frame, text="-", width=2,
                                    )
        self.gate_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.gate_plus_btn = ttk.Button(gate_button_frame, text="+", width=2,
                                    )
        self.gate_plus_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 绑定长按事件
        self.gate_minus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("gate", -0.001))
        self.gate_minus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())
        self.gate_plus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("gate", 0.001))
        self.gate_plus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())

        self.gate_label = ttk.Label(gate_frame, text="-750mm", width=7)
        self.gate_label.pack(side=tk.RIGHT, padx=(5, 10))
        
        # 摆角滑块
        angle_frame = ttk.Frame(slider_frame)
        angle_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(angle_frame, text="初始摆角:").pack(side=tk.LEFT, padx=(10, 5))
        self.angle_var = tk.DoubleVar(value=5.0)
        self.angle_slider = ttk.Scale(angle_frame, from_=-90.0, to=90.0, 
                                    orient=tk.HORIZONTAL, variable=self.angle_var,
                                    command=self.on_angle_slider_changed)
        self.angle_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 添加微调按钮
        angle_button_frame = ttk.Frame(angle_frame)
        angle_button_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.angle_minus_btn = ttk.Button(angle_button_frame, text="-", width=2,
                                        )
        self.angle_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.angle_plus_btn = ttk.Button(angle_button_frame, text="+", width=2,
                                    )
        self.angle_plus_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 绑定长按事件
        self.angle_minus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("angle", -1))
        self.angle_minus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())
        self.angle_plus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("angle", 1))
        self.angle_plus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())

        self.angle_label = ttk.Label(angle_frame, text="5°", width=7)
        self.angle_label.pack(side=tk.RIGHT, padx=(5, 10))
        
        # 复摆高度滑块
        height_frame = ttk.Frame(slider_frame)
        height_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(height_frame, text="复摆高度:").pack(side=tk.LEFT, padx=(10, 5))
        self.height_var = tk.DoubleVar(value=0.0)
        self.height_slider = ttk.Scale(height_frame, from_=-0.3, to=0.1,
                                    orient=tk.HORIZONTAL, variable=self.height_var,
                                    command=self.on_height_slider_changed)
        self.height_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 添加微调按钮
        height_button_frame = ttk.Frame(height_frame)
        height_button_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.height_minus_btn = ttk.Button(height_button_frame, text="-", width=2,
                                        )
        self.height_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.height_plus_btn = ttk.Button(height_button_frame, text="+", width=2,
                                        )
        self.height_plus_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 绑定长按事件
        self.height_minus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("height", -0.001))
        self.height_minus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())
        self.height_plus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("height", 0.001))
        self.height_plus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())

        self.height_label = ttk.Label(height_frame, text="0mm", width=7)
        self.height_label.pack(side=tk.RIGHT, padx=(5, 10))
        
        # +++ 新增：摆锤控制区域 +++
        hammer_frame = ttk.Frame(slider_frame)
        hammer_frame.pack(fill=tk.X, pady=(10, 5))

        # 摆锤A控制
        hammer_a_frame = ttk.Frame(hammer_frame)
        hammer_a_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.hammer_a_button = ttk.Button(
            hammer_a_frame,
            text="放置摆锤A",
            command=self.toggle_hammer_a,
            width=12
        )
        self.hammer_a_button.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(hammer_a_frame, text="摆锤A位置:").pack(side=tk.LEFT, padx=(10, 5))
        self.hammer_a_var = tk.DoubleVar(value=0.3)
        self.hammer_a_slider = ttk.Scale(hammer_a_frame, from_=0.0, to=1.0,
                                        orient=tk.HORIZONTAL, variable=self.hammer_a_var,
                                        command=self.on_hammer_a_slider_changed)
        self.hammer_a_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.hammer_a_slider.config(state="disabled")
        
        # 添加微调按钮
        hammer_a_button_frame = ttk.Frame(hammer_a_frame)
        hammer_a_button_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.hammer_a_minus_btn = ttk.Button(hammer_a_button_frame, text="-", width=2,
                                        )
        self.hammer_a_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.hammer_a_plus_btn = ttk.Button(hammer_a_button_frame, text="+", width=2,
                                        )
        self.hammer_a_plus_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 绑定长按事件
        self.hammer_a_minus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("hammer_a", -0.001))
        self.hammer_a_minus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())
        self.hammer_a_plus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("hammer_a", 0.001))
        self.hammer_a_plus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())

        self.hammer_a_label = ttk.Label(hammer_a_frame, text="210mm", width=7)
        self.hammer_a_label.pack(side=tk.RIGHT, padx=(5, 10))

        # 禁用微调按钮
        self.hammer_a_minus_btn.config(state="disabled")
        self.hammer_a_plus_btn.config(state="disabled")
        self.pendulum.update_hammer_a(False)
        self.hammer_a_rect.set_visible(False)
        
        # 摆锤B控制
        hammer_b_frame = ttk.Frame(hammer_frame)
        hammer_b_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.hammer_b_button = ttk.Button(
            hammer_b_frame,
            text="放置摆锤B",
            command=self.toggle_hammer_b,
            width=12
        )
        self.hammer_b_button.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(hammer_b_frame, text="摆锤B位置:").pack(side=tk.LEFT, padx=(10, 5))
        self.hammer_b_var = tk.DoubleVar(value=0.6)
        self.hammer_b_slider = ttk.Scale(hammer_b_frame, from_=0.0, to=1.0,
                                        orient=tk.HORIZONTAL, variable=self.hammer_b_var,
                                        command=self.on_hammer_b_slider_changed)
        self.hammer_b_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.hammer_b_slider.config(state="disabled")
        
        # 添加微调按钮
        hammer_b_button_frame = ttk.Frame(hammer_b_frame)
        hammer_b_button_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.hammer_b_minus_btn = ttk.Button(hammer_b_button_frame, text="-", width=2,
                                        )
        self.hammer_b_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.hammer_b_plus_btn = ttk.Button(hammer_b_button_frame, text="+", width=2,
                                        )
        self.hammer_b_plus_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 绑定长按事件
        self.hammer_b_minus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("hammer_b", -0.001))
        self.hammer_b_minus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())
        self.hammer_b_plus_btn.bind("<ButtonPress-1>", lambda e: self.start_continuous_adjust("hammer_b", 0.001))
        self.hammer_b_plus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_continuous_adjust())

        self.hammer_b_label = ttk.Label(hammer_b_frame, text="420mm", width=7)
        self.hammer_b_label.pack(side=tk.RIGHT, padx=(5, 10))

        # 禁用微调按钮
        self.hammer_b_minus_btn.config(state="disabled")
        self.hammer_b_plus_btn.config(state="disabled")
        self.pendulum.update_hammer_b(False)
        self.hammer_b_rect.set_visible(False)
        
        # 开始/停止按钮
        button_frame = ttk.Frame(slider_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.start_stop_button = ttk.Button(
            button_frame, 
            text="开始", 
            command=self.toggle_animation,
            width=10
        )
        self.start_stop_button.pack(pady=5)

    def set_hanging_mode(self, mode):
        """设置挂载模式"""
        if self.animation_running:
            return
            
        self.hanging_mode = mode
        self.update_hanging_buttons_style()
        
        # 根据挂载模式更新复摆
        if mode == "正挂":
            # 正挂模式：起点在上方，末端在下方（默认）
            self.pendulum.height_offset = self.height_var.get()
        else:
            # 倒挂模式：保持相同的角度范围，但在get_positions方法中会处理显示
            self.pendulum.height_offset = self.height_var.get()
        
        # 更新显示
        self.canvas.draw_idle()

    def update_hanging_buttons_style(self):
        """更新挂载模式按钮样式"""
        if self.hanging_mode == "正挂":
            self.normal_hanging_btn.config(style="Accent.TButton")
            self.inverted_hanging_btn.config(style="TButton")
        else:
            self.normal_hanging_btn.config(style="TButton")
            self.inverted_hanging_btn.config(style="Accent.TButton")

    def check_gate_trigger(self):
        """检查光电门是否触发"""
        try:
            # 获取光电门位置和复摆参数
            gate_y = self.gate_var.get()  # 光电门垂直位置
            pendulum_length = self.pendulum.length  # 细杆长度
            pivot_position = self.pendulum.pivot_position  # 转轴位置（比例）
            height_offset = self.pendulum.height_offset  # 复摆高度偏移
            
            # 计算复摆末端位置
            if self.hanging_mode == "正挂":
            # 正挂模式：末端位置计算
                end_offset = (1 - pivot_position) * pendulum_length
            else:
                end_offset = pivot_position * pendulum_length
            end_y = -end_offset * np.cos(self.pendulum.angle) + height_offset
            
            # 获取当前摆角（角度制）
            current_angle_degrees = abs(np.degrees(self.pendulum.angle))
            initial_angle_degrees = abs(self.angle_var.get())
            
            # 条件2: 根据初始摆角设置触发阈值
            if initial_angle_degrees <= 5:
                trigger_threshold = 1.5
            elif initial_angle_degrees <= 45:
                trigger_threshold = 5.0
            else:
                trigger_threshold = 10.0
            
            # 检查当前摆角是否小于阈值
            angle_condition = current_angle_degrees <= trigger_threshold
            
            # 检查复摆末端是否在光电门位置附近（放宽容差）
            gate_tolerance = 0.13  # 增加到5cm容差
            position_condition = abs(end_y - gate_y) <= gate_tolerance
            
            # 调试信息
            debug_info = f"末端Y: {end_y:.3f}, 光电门Y: {gate_y:.3f}, 差值: {abs(end_y - gate_y):.3f}, 角度: {current_angle_degrees:.1f}°, 阈值: {trigger_threshold}°"
            
            # 同时满足角度条件和位置条件
            triggered = angle_condition and position_condition
            
            if triggered:
                print(f"光电门触发! {debug_info}")
            
            return triggered
            
        except Exception as e:
            print(f"光电门检测错误: {e}")
            return False

    def update_gate_dot(self):
        """更新光电门红点显示状态"""
        try:
            if self.gate_triggered:
                # 获取光电门位置
                gate_y = self.gate_var.get()
                
                # 光电门图片高度为0.1m，中心在Y方向中间，X方向在原点附近
                # 根据gate.jpg图片的extent [-0.05, 0.03, gate_y, gate_y + 0.1]
                # 中心位置在X=(-0.05+0.03)/2 = -0.01, Y=gate_y + 0.05
                gate_center_x = -0.01  # 光电门图片中心X坐标
                gate_center_y = gate_y + 0.05  # 光电门图片中心Y坐标
                
                # 设置红点位置并显示
                self.gate_dot.center = (gate_center_x, gate_center_y)
                self.gate_dot.set_visible(True)
                self.gate_dot.set_radius(0.02)  # 增大红点尺寸以便观察
                self.gate_dot.set_color('red')
                self.gate_dot.set_alpha(1.0)
                self.gate_dot.set_zorder(15)  # 确保在最上层
            else:
                # 隐藏红点
                self.gate_dot.set_visible(False)
                
        except Exception as e:
            print(f"更新光电门红点错误: {e}")
        
    def adjust_pivot(self, delta):
        """微调转轴位置"""
        # 如果动画正在运行，不响应调整
        if self.animation_running:
            return
            
        current = self.pivot_var.get()
        new_value = max(0.0, min(1.0, current + delta))
        
        # 检查位置限制
        if self.check_pivot_position_limit(new_value):
            self.pivot_var.set(new_value)
            self.on_pivot_slider_changed(new_value)

    def adjust_gate(self, delta):
        """微调光电门位置"""
        current = self.gate_var.get()
        
        # 计算复摆末端的最低位置（考虑高度偏移）
        pendulum_length = self.pendulum.length
        pivot_position = self.pendulum.pivot_position
        height_offset = self.pendulum.height_offset
        
        # 末端相对于转轴的最大偏移（当摆角为0度时）
        end_offset = (1 - pivot_position) * pendulum_length
        # 末端的最低位置
        end_min_y = -end_offset + height_offset
        
        # 限制光电门位置不能超过末端-0.1m
        max_gate_pos = end_min_y - 0.1
        min_gate_pos = -0.75  # 原有的下限
        
        new_value = max(min_gate_pos, min(max_gate_pos, current + delta))
        self.gate_var.set(new_value)
        self.on_gate_slider_changed(new_value)

    def adjust_angle(self, delta):
        """微调摆角"""
        current = self.angle_var.get()
        new_value = max(-90.0, min(90.0, current + delta))
        self.angle_var.set(new_value)
        self.on_angle_slider_changed(new_value)

    def adjust_height(self, delta):
        """微调复摆高度"""
        # 如果动画正在运行，不响应调整
        if self.animation_running:
            return
            
        current = self.height_var.get()
        new_value = max(-0.3, min(0.1, current + delta))
        
        # 检查位置限制
        if self.check_height_limit(new_value):
            self.height_var.set(new_value)
            self.on_height_slider_changed(new_value)

    def check_pivot_position_limit(self, pivot_pos):
        """检查转轴位置是否超出限制"""
        current_height = self.height_var.get()
        pendulum_length = self.pendulum.length
        
        # 计算起点和末端位置
        start_offset = -pivot_pos * pendulum_length
        end_offset = (1 - pivot_pos) * pendulum_length

        # 根据挂载模式计算实际位置
        if self.hanging_mode == "正挂":
            start_y = -start_offset + current_height
            end_y = -end_offset + current_height
        else:
            # 倒挂模式：起点在下方，末端在上方
            start_y = start_offset + current_height
            end_y = end_offset + current_height
        
        # 检查限制
        if self.hanging_mode == "正挂":
            if start_y > 0.36:  # 起点不能高于0.4
                print(f"警告：起点位置 {start_y:.3f} 超过上限 0.4")
                return False
            if end_y < -0.65:  # 末端不能低于-0.65
                print(f"警告：末端位置 {end_y:.3f} 超过下限 -0.65")
                return False
        else:
            # 倒挂模式的限制
            if start_y < -0.65:  # 起点不能低于-0.65
                print(f"警告：倒挂起点位置 {start_y:.3f} 超过下限 -0.65")
                return False
            if end_y > 0.37:  # 末端不能高于0.4
                print(f"警告：倒挂末端位置 {end_y:.3f} 超过上限 0.35")
                return False
        
        return True

    def check_height_limit(self, height_offset):
        """检查复摆高度是否超出限制"""
        current_pivot = self.pivot_var.get()
        pendulum_length = self.pendulum.length
        
        # 计算起点和末端位置
        start_offset = -current_pivot * pendulum_length
        end_offset = (1 - current_pivot) * pendulum_length
        
         # 根据挂载模式计算实际位置
        if self.hanging_mode == "正挂":
            start_y = -start_offset + height_offset
            end_y = -end_offset + height_offset
        else:
            # 倒挂模式：起点在下方，末端在上方
            start_y = start_offset + height_offset
            end_y = end_offset + height_offset
        
        # 检查限制
        if self.hanging_mode == "正挂":
            if start_y > 0.4:  # 起点不能高于0.4
                print(f"警告：起点位置 {start_y:.3f} 超过上限 0.4")
                return False
            if end_y < -0.65:  # 末端不能低于-0.65
                print(f"警告：末端位置 {end_y:.3f} 超过下限 -0.65")
                return False
        else:
            # 倒挂模式的限制
            if start_y < -0.65:  # 起点不能低于-0.65
                print(f"警告：倒挂起点位置 {start_y:.3f} 超过下限 -0.65")
                return False
            if end_y > 0.4:  # 末端不能高于0.4
                print(f"警告：倒挂末端位置 {end_y:.3f} 超过上限 0.4")
                return False
        
        return True

    def adjust_hammer_a(self, delta):
        """微调摆锤A位置"""
        if self.hammer_a_placed:
            current = self.hammer_a_var.get()
            new_value = max(0.0, min(1.0, current + delta))
            self.hammer_a_var.set(new_value)
            self.on_hammer_a_slider_changed(new_value)

    def adjust_hammer_b(self, delta):
        """微调摆锤B位置"""
        if self.hammer_b_placed:
            current = self.hammer_b_var.get()
            new_value = max(0.0, min(1.0, current + delta))
            self.hammer_b_var.set(new_value)
            self.on_hammer_b_slider_changed(new_value)

    def execute_single_adjust(self, control_type, delta):
        """执行单次调整"""
        # 如果动画正在运行，不响应调整
        if self.animation_running:
            return

        if control_type == "pivot":
            self.adjust_pivot(delta)
        elif control_type == "gate":
            self.adjust_gate(delta)
        elif control_type == "angle":
            self.adjust_angle(delta)
        elif control_type == "height":
            self.adjust_height(delta)
        elif control_type == "hammer_a":
            self.adjust_hammer_a(delta)
        elif control_type == "hammer_b":
            self.adjust_hammer_b(delta)

    def start_continuous_adjust(self, control_type, delta):
        """开始连续调整"""
        # 如果动画正在运行，不响应调整
        if self.animation_running:
            return
        self.continuous_adjust_running = True
        self.continuous_adjust_type = control_type
        self.continuous_adjust_delta = delta
        
        # 立即执行一次调整（短按效果）
        self.execute_single_adjust(control_type, delta)
        
        # 延迟后开始连续调整
        self.root.after(500, self.continuous_adjust)  # 300ms延迟后开始连续调整

    def stop_continuous_adjust(self):
        """停止连续调整"""
        self.continuous_adjust_running = False

    def continuous_adjust(self):
        """连续调整函数"""
        if self.continuous_adjust_running:
            self.execute_single_adjust(self.continuous_adjust_type, self.continuous_adjust_delta)
            # 50ms后再次调用，实现连续调整
            self.root.after(50, self.continuous_adjust)

    def toggle_hammer_a(self):
        """切换摆锤A状态"""
        if self.animation_running:
            return
        if not self.hammer_a_placed:
            # 放置摆锤A
            self.hammer_a_placed = True
            self.hammer_a_button.config(text="取下摆锤A")
            self.hammer_a_slider.config(state="normal")
            # 启用微调按钮
            self.hammer_a_minus_btn.config(state="normal")
            self.hammer_a_plus_btn.config(state="normal")
            self.pendulum.update_hammer_a(True, self.hammer_a_var.get())
            self.hammer_a_rect.set_visible(True)  # 改为方形
        else:
            # 取下摆锤A
            self.hammer_a_placed = False
            self.hammer_a_button.config(text="放置摆锤A")
            self.hammer_a_slider.config(state="disabled")
            # 禁用微调按钮
            self.hammer_a_minus_btn.config(state="disabled")
            self.hammer_a_plus_btn.config(state="disabled")
            self.pendulum.update_hammer_a(False)
            self.hammer_a_rect.set_visible(False)  # 改为方形
        
        self.canvas.draw_idle()

    def toggle_hammer_b(self):
        """切换摆锤B状态"""
        if self.animation_running:
            return
        if not self.hammer_b_placed:
            # 放置摆锤B
            self.hammer_b_placed = True
            self.hammer_b_button.config(text="取下摆锤B")
            self.hammer_b_slider.config(state="normal")
            # 启用微调按钮
            self.hammer_b_minus_btn.config(state="normal")
            self.hammer_b_plus_btn.config(state="normal")
            self.pendulum.update_hammer_b(True, self.hammer_b_var.get())
            self.hammer_b_rect.set_visible(True)  # 改为方形
        else:
            # 取下摆锤B
            self.hammer_b_placed = False
            self.hammer_b_button.config(text="放置摆锤B")
            self.hammer_b_slider.config(state="disabled")
            # 禁用微调按钮
            self.hammer_b_minus_btn.config(state="disabled")
            self.hammer_b_plus_btn.config(state="disabled")
            self.pendulum.update_hammer_b(False)
            self.hammer_b_rect.set_visible(False)  # 改为方形
        
        self.canvas.draw_idle()

    def on_hammer_a_slider_changed(self, value):
        """处理摆锤A位置滑块变化"""
        if self.animation_running:
            return
        position = float(value)
        self.hammer_a_position = position
        self.pendulum.update_hammer_a(True, position)
        
        # 更新位置显示（单位mm）
        position_mm = position * self.pendulum.length * 1000
        self.hammer_a_label.config(text=f"{position_mm:.0f}mm")
        
        self.canvas.draw_idle()

    def on_hammer_b_slider_changed(self, value):
        """处理摆锤B位置滑块变化"""
        if self.animation_running:
            return
        position = float(value)
        self.hammer_b_position = position
        self.pendulum.update_hammer_b(True, position)
        
        # 更新位置显示（单位mm）
        position_mm = position * self.pendulum.length * 1000
        self.hammer_b_label.config(text=f"{position_mm:.0f}mm")
        
        self.canvas.draw_idle()

    def setup_control_panel(self, parent):
        
        # 创建画布用于显示背景图片和叠加控件
        self.canvas_bg = tk.Canvas(parent, width=900, height=360, bg="white")
        self.canvas_bg.pack(fill=tk.X, pady=(0, 0))  # 去除垂直间距

        # 创建主框架
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 加载并显示实验仪图片
        image_path = resource_path(os.path.join('background', 'FD-CP-A复摆实验仪.png'))
        print(f"尝试加载图片路径: {image_path}")
        
        try:
            if os.path.exists(image_path):
                self.bg_image = Image.open(image_path)
                # 调整图片大小以适应画布
                self.bg_image = self.bg_image.resize((900, 360), Image.Resampling.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(self.bg_image)
                
                # 在画布上显示背景图片
                self.canvas_bg.create_image(450, 180, image=self.bg_photo)
                print("背景图片加载成功")
            else:
                # 如果图片不存在，创建占位符
                self.create_placeholder_bg()
        except Exception as e:
            print(f"加载背景图片时发生错误: {e}")
            self.create_placeholder_bg()
        
        # 在背景图片上叠加按钮和显示区域
        self.create_overlay_controls()
        # +++ 新增：数据记录区域 +++
        self.create_data_record_area(main_frame)
    
    def create_data_record_area(self, parent):
        """创建数据记录区域"""
        # 数据记录区域主框架
        data_frame = ttk.Frame(parent)
        data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 实验步骤选项卡
        self.create_experiment_tabs(data_frame)
        
        # 实验内容区域
        self.create_experiment_content(data_frame)

    def create_experiment_tabs(self, parent):
        """创建实验步骤选项卡"""
        tabs_frame = ttk.Frame(parent)
        tabs_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 实验步骤名称
        self.experiment_steps = [
            "测量重力加速度（方法一）",
            "测量重力加速度（方法二）", 
            "测量重力加速度（方法三）",
            "测量物体转动惯量",
            "验证平行轴定理"
        ]
        
        self.current_experiment = 0  # 默认选择第一个
        
        # 创建选项卡按钮
        self.tab_buttons = []
        for i, step_name in enumerate(self.experiment_steps):
            btn = ttk.Button(
                tabs_frame,
                text=step_name,
                command=lambda idx=i: self.switch_experiment_tab(idx),
                width=20
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.tab_buttons.append(btn)
        
        # 设置初始选中状态
        self.update_tab_buttons_style()

    # 修改 switch_experiment_tab 方法，添加数据保存和恢复
    def switch_experiment_tab(self, tab_index):
        """切换实验步骤选项卡"""
        print(f"切换选项卡: {self.current_experiment} -> {tab_index}")
        # 保存当前实验步骤的数据
        self.save_current_experiment_data()
        
        self.current_experiment = tab_index
        self.update_tab_buttons_style()
        self.show_experiment_content()
    
        # 恢复新实验步骤的数据
        self.restore_experiment_data()

    # 添加数据保存和恢复方法
    def save_current_experiment_data(self):
        """保存当前实验步骤的数据"""
        print(f"正在保存实验数据，当前步骤: {self.current_experiment}")
        if self.current_experiment == 0:
            # 保存重力加速度方法一的数据
            self.experiment_data["gravity_method1"] = {
                "h1": self.h1_var.get() if hasattr(self, 'h1_var') else "",
                "t1": self.t1_var.get() if hasattr(self, 't1_var') else "",
                "t2": self.t2_var.get() if hasattr(self, 't2_var') else "",
                "g": self.g_var.get() if hasattr(self, 'g_var') else "",
                "e": self.e_var.get() if hasattr(self, 'e_var') else ""
            }
        elif self.current_experiment == 1:
            # 保存重力加速度方法二的数据
            self.save_method2_data()
        elif self.current_experiment == 2:
            # 保存重力加速度方法三的数据
            self.save_method3_data()  # 新增这行
        elif self.current_experiment == 3:
            # 保存转动惯量测量的数据
            self.experiment_data["moment_of_inertia"] = {
                "h0": self.h0_var.get() if hasattr(self, 'h0_var') else "",
                "t0": self.t0_var.get() if hasattr(self, 't0_var') else "",
                "t": self.t_var.get() if hasattr(self, 't_var') else "",
                "i0": self.i0_var.get() if hasattr(self, 'i0_var') else "",
                "i0_theory": self.i0_theory_var.get() if hasattr(self, 'i0_theory_var') else "",
                "e_i0": self.e_i0_var.get() if hasattr(self, 'e_i0_var') else "",
                "ia": self.ia_var.get() if hasattr(self, 'ia_var') else "",
                "ia_theory": self.ia_theory_var.get() if hasattr(self, 'ia_theory_var') else "",
                "e_ia": self.e_ia_var.get() if hasattr(self, 'e_ia_var') else ""
            }
        elif self.current_experiment == 4:
            # 保存平行轴定理验证的数据
            self.save_parallel_data()

        

    def restore_experiment_data(self):
        """恢复当前实验步骤的数据"""
        if self.current_experiment == 0:
            # 恢复重力加速度方法一的数据
            data = self.experiment_data["gravity_method1"]
            if hasattr(self, 'h1_var') and "h1" in data:
                self.h1_var.set(data["h1"])
            if hasattr(self, 't1_var') and "t1" in data:
                self.t1_var.set(data["t1"])
            if hasattr(self, 't2_var') and "t2" in data:
                self.t2_var.set(data["t2"])
            if hasattr(self, 'g_var') and "g" in data:
                self.g_var.set(data["g"])
            if hasattr(self, 'e_var') and "e" in data:
                self.e_var.set(data["e"])
                
            # 自动计算h2
            self.auto_calculate_h2()
            
        elif self.current_experiment == 1:
            # 恢复重力加速度方法二的数据
            self.restore_method2_data()
            
        elif self.current_experiment == 2:
            # 恢复重力加速度方法三的数据
            self.restore_method3_data()  # 新增这行
            
        elif self.current_experiment == 3:
            # 恢复转动惯量测量的数据
            data = self.experiment_data["moment_of_inertia"]
            if hasattr(self, 'h0_var') and "h0" in data:
                self.h0_var.set(data["h0"])
            if hasattr(self, 't0_var') and "t0" in data:
                self.t0_var.set(data["t0"])
            if hasattr(self, 't_var') and "t" in data:
                self.t_var.set(data["t"])
            if hasattr(self, 'i0_var') and "i0" in data:
                self.i0_var.set(data["i0"])
            if hasattr(self, 'i0_theory_var') and "i0_theory" in data:
                self.i0_theory_var.set(data["i0_theory"])
            if hasattr(self, 'e_i0_var') and "e_i0" in data:
                self.e_i0_var.set(data["e_i0"])
            if hasattr(self, 'ia_var') and "ia" in data:
                self.ia_var.set(data["ia"])
            if hasattr(self, 'ia_theory_var') and "ia_theory" in data:
                self.ia_theory_var.set(data["ia_theory"])
            if hasattr(self, 'e_ia_var') and "e_ia" in data:
                self.e_ia_var.set(data["e_ia"])
                
        elif self.current_experiment == 4:
            # 恢复平行轴定理验证的数据
            self.restore_parallel_data()

    def update_tab_buttons_style(self):
        """更新选项卡按钮样式"""
        for i, btn in enumerate(self.tab_buttons):
            if i == self.current_experiment:
                btn.config(style="Accent.TButton")  # 选中样式
            else:
                btn.config(style="TButton")  # 普通样式

    def create_experiment_content(self, parent):
        """创建实验内容区域"""
        # 实验内容主框架
        self.content_frame = ttk.Frame(parent, relief="solid", borderwidth=1)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 初始显示第一个实验的内容
        self.show_experiment_content()

    def show_experiment_content(self):
        """显示当前实验步骤的内容"""
        # 清空现有内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 根据当前实验步骤显示相应内容
        if self.current_experiment == 0:
            self.create_gravity_acceleration_method1()
        elif self.current_experiment == 1:
            self.create_gravity_acceleration_method2()
        elif self.current_experiment == 2:
            self.create_gravity_acceleration_method3()
        elif self.current_experiment == 3:
            self.create_moment_of_inertia()
        elif self.current_experiment == 4:
            self.create_parallel_axis_verification()

    def create_gravity_acceleration_method1(self):
        """创建测量重力加速度（方法一）的实验内容"""
        # 标题
        title_label = ttk.Label(self.content_frame, text="测量重力加速度（方法一）", 
                            font=("Arial", 12, "bold"))
        title_label.pack(pady=(10, 20))
        
        # 第一行：输入字段
        row1_frame = ttk.Frame(self.content_frame)
        row1_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 质心到转轴距离h1 (mm)
        ttk.Label(row1_frame, text="质心到转轴距离h1 (cm):").pack(side=tk.LEFT, padx=5)
        self.h1_var = tk.StringVar()
        h1_entry = ttk.Entry(row1_frame, textvariable=self.h1_var, width=10)
        h1_entry.pack(side=tk.LEFT, padx=5)
        
        # 质心到转轴距离h2 (mm)（自动计算，只读）
        ttk.Label(row1_frame, text="质心到转轴距离h2 (cm):").pack(side=tk.LEFT, padx=5)
        self.h2_var = tk.StringVar()
        h2_entry = ttk.Entry(row1_frame, textvariable=self.h2_var, width=10, state="readonly")
        h2_entry.pack(side=tk.LEFT, padx=5)
        
        # 周期T1
        ttk.Label(row1_frame, text="周期T1 (s):").pack(side=tk.LEFT, padx=5)
        self.t1_var = tk.StringVar()
        t1_entry = ttk.Entry(row1_frame, textvariable=self.t1_var, width=10)
        t1_entry.pack(side=tk.LEFT, padx=5)
        
        # 周期T2（手动输入）
        ttk.Label(row1_frame, text="周期T2 (s):").pack(side=tk.LEFT, padx=5)
        self.t2_var = tk.StringVar()
        t2_entry = ttk.Entry(row1_frame, textvariable=self.t2_var, width=10)
        t2_entry.pack(side=tk.LEFT, padx=5)
        
        # 第二行：结果显示和计算按钮
        row2_frame = ttk.Frame(self.content_frame)
        row2_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 重力加速度g
        ttk.Label(row2_frame, text="重力加速度g (m/s^2)(参考值9.8):").pack(side=tk.LEFT, padx=5)
        self.g_var = tk.StringVar()
        g_entry = ttk.Entry(row2_frame, textvariable=self.g_var, width=10, state="readonly")
        g_entry.pack(side=tk.LEFT, padx=5)
        
        # 百分误差E
        ttk.Label(row2_frame, text="误差E (%):").pack(side=tk.LEFT, padx=5)
        self.e_var = tk.StringVar()
        e_entry = ttk.Entry(row2_frame, textvariable=self.e_var, width=10, state="readonly")
        e_entry.pack(side=tk.LEFT, padx=5)
        
        # 计算按钮
        calc_button = ttk.Button(row2_frame, text="计算", 
                            command=self.calculate_gravity_method1)
        calc_button.pack(side=tk.LEFT, padx=20)
        
        # +++ 新增：导出数据按钮 +++
        export_button = ttk.Button(row2_frame, text="导出数据", 
                                command=self.export_method1_data)
        export_button.pack(side=tk.LEFT, padx=5)

        import_button = ttk.Button(row2_frame, text="导入数据", 
                            command=self.import_method1_data)
        import_button.pack(side=tk.LEFT, padx=5)

        # 绑定h1变化事件，自动计算h2
        self.h1_var.trace('w', self.auto_calculate_h2)

    # 添加方法一的导入数据功能
    def import_method1_data(self):
        """从Excel导入方法一数据"""
        try:
            import pandas as pd
            from tkinter import filedialog
            import threading
            
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            self.show_import_progress("正在导入方法一数据...")
            
            def import_thread():
                try:
                    # 读取Excel文件
                    df = pd.read_excel(file_path)
                    
                    # 在主线程中更新UI
                    self.root.after(0, self.update_method1_data, df)
                    
                    self.root.after(0, self.hide_import_progress)
                    self.root.after(0, lambda: tk.messagebox.showinfo("成功", "数据导入完成"))
                    
                except Exception as e:
                    self.root.after(0, self.hide_import_progress)
                    self.root.after(0, lambda: tk.messagebox.showerror("错误", f"导入失败: {str(e)}"))
            
            thread = threading.Thread(target=import_thread, daemon=True)
            thread.start()
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas库: pip install pandas")
        except Exception as e:
            self.hide_import_progress()
            tk.messagebox.showerror("错误", f"导入失败: {str(e)}")

    def update_method1_data(self, df):
        """更新方法一的数据"""
        try:
            # 检查数据格式
            if '参数' not in df.columns or '数值' not in df.columns:
                tk.messagebox.showerror("错误", "Excel文件格式不正确，需要包含'参数'和'数值'列")
                return
            
            # 更新各个字段
            for _, row in df.iterrows():
                param = row['参数']
                value = row['数值']
                
                if pd.notna(param) and pd.notna(value):
                    param_str = str(param).strip()
                    value_str = str(value)
                    
                    if "质心到转轴距离h1" in param_str:
                        self.h1_var.set(value_str)
                    elif "质心到转轴距离h2" in param_str:
                        self.h2_var.set(value_str)
                    elif "周期T1" in param_str:
                        self.t1_var.set(value_str)
                    elif "周期T2" in param_str:
                        self.t2_var.set(value_str)
                    elif "重力加速度g" in param_str:
                        self.g_var.set(value_str)
                    elif "误差E" in param_str:
                        self.e_var.set(value_str)
            
            # 自动计算h2
            self.auto_calculate_h2()
            
            print("方法一数据导入完成")
            
        except Exception as e:
            tk.messagebox.showerror("错误", f"更新数据时发生错误: {str(e)}")

    # 添加导出方法一数据的功能
    def export_method1_data(self):
        """导出方法一的数据到Excel - 多线程版本"""
        try:
            import pandas as pd
            from tkinter import filedialog
            import threading
            
            # 收集数据
            data = {
                "参数": ["质心到转轴距离h1 (cm)", "质心到转轴距离h2 (cm)", "周期T1 (s)", "周期T2 (s)", 
                    "重力加速度g (m/s^2)", "误差E (%)"],
                "数值": [
                    self.h1_var.get() if self.h1_var.get() else "",
                    self.h2_var.get() if self.h2_var.get() else "",
                    self.t1_var.get() if self.t1_var.get() else "",
                    self.t2_var.get() if self.t2_var.get() else "",
                    self.g_var.get() if self.g_var.get() else "",
                    self.e_var.get() if self.e_var.get() else ""
                ]
            }
            
            # 检查是否有数据可导出
            if not any(data["数值"]):
                tk.messagebox.showwarning("警告", "没有可导出的数据")
                return
            
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            self.show_export_progress("正在导出方法一数据...")
            
            def export_thread():
                try:
                    df = pd.DataFrame(data)
                    df.to_excel(file_path, index=False)
                    
                    # 在主线程中显示完成消息
                    self.root.after(0, lambda: self.hide_export_progress())
                    self.root.after(0, lambda: tk.messagebox.showinfo("成功", f"数据已导出到: {file_path}"))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.hide_export_progress())
                    self.root.after(0, lambda: tk.messagebox.showerror("错误", f"导出失败: {str(e)}"))
            
            # 在新线程中执行导出
            thread = threading.Thread(target=export_thread, daemon=True)
            thread.start()
        
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas库: pip install pandas")
        except Exception as e:
            self.hide_export_progress()
            tk.messagebox.showerror("错误", f"导出失败: {str(e)}")

    def auto_calculate_h2(self, *args):
        """根据h1自动计算h2 = 2 * h1 (cm)"""
        try:
            if self.h1_var.get():
                h1 = float(self.h1_var.get())  # 单位：cm
                h2 = 2 * h1  # 单位：cm
                self.h2_var.set(f"{h2:.1f}")  # 保留1位小数
            else:
                self.h2_var.set("")
        except ValueError:
            self.h2_var.set("")

    def calculate_gravity_method1(self):
        """计算方法一的重力加速度和误差"""
        try:
            # 验证输入数据
            if not all([self.h1_var.get(), self.t1_var.get(), self.t2_var.get()]):
                tk.messagebox.showerror("错误", "请完整输入h1、T1和T2的值")
                return
            
            h1_cm = float(self.h1_var.get())  # 单位：cm
            t1 = float(self.t1_var.get())
            t2 = float(self.t2_var.get())
            
            # 将h1从mm转换为m
            h1 = h1_cm / 100.0
            
            # 计算公式: g = 12 * π^2 * h1 / (2 * T2^2 - T1^2)
            pi_squared = 3.1415 * 3.1415
            numerator = 12 * pi_squared * h1
            denominator = 2 * t2 * t2 - t1 * t1
            
            if denominator <= 0:
                tk.messagebox.showerror("错误", "计算错误：分母必须大于0")
                return
                
            g = numerator / denominator
            
            # 计算百分误差（理论值9.8）
            theoretical_g = 9.8
            error_percent = abs((g - theoretical_g) / theoretical_g) * 100
            
            # 更新显示
            self.g_var.set(f"{g:.4f}")
            self.e_var.set(f"{error_percent:.2f}%")
        
            # 自动保存数据（因为用户可能切换到其他步骤）
            self.save_current_experiment_data()

        except ValueError:
            tk.messagebox.showerror("错误", "请输入有效的数值")
        except Exception as e:
            tk.messagebox.showerror("错误", f"计算过程中发生错误: {str(e)}")

    def create_gravity_acceleration_method2(self):
        """创建测量重力加速度（方法二）的实验内容"""
        # 清空现有内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_label = ttk.Label(self.content_frame, text="测量重力加速度（方法二）", 
                                font=("Arial", 12, "bold"))
        title_label.pack(pady=(10, 5))
        
        # 主内容框架 - 左右布局
        main_content_frame = ttk.Frame(self.content_frame)
        main_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：数据表格
        left_frame = ttk.Frame(main_content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 表格标题
        table_title = ttk.Label(left_frame, text="数据记录表", font=("Arial", 10, "bold"))
        table_title.pack(pady=(0, 3))
        
        # 创建表格框架 - 固定高度
        table_frame = ttk.Frame(left_frame, height=180)
        table_frame.pack(fill=tk.BOTH, expand=False)
        table_frame.pack_propagate(False)
        
        # 创建Treeview表格
        columns = ("h", "T", "x", "y")
        self.method2_table = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            height=6
        )
        
        # 设置列标题
        self.method2_table.heading("h", text="h/cm")
        self.method2_table.heading("T", text="T/s")
        self.method2_table.heading("x", text="x/m^2")
        self.method2_table.heading("y", text="y/m·s^2")
        
        # 设置列宽
        self.method2_table.column("h", width=70)
        self.method2_table.column("T", width=70)
        self.method2_table.column("x", width=90)
        self.method2_table.column("y", width=90)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.method2_table.yview)
        self.method2_table.configure(yscrollcommand=scrollbar.set)
        
        # 布局表格和滚动条
        self.method2_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定表格事件 - 修改：移除双击事件绑定，添加编辑事件
        self.method2_table.bind('<Double-1>', self.on_method2_table_double_click)
        self.method2_table.bind('<<TreeviewSelect>>', self.on_method2_table_select)
        
        # 创建编辑条目
        self.method2_entry = ttk.Entry(table_frame, width=10)
        self.method2_entry.pack_forget()  # 初始隐藏
        
        # 绑定编辑条目的相关事件
        self.method2_entry.bind('<Return>', self.save_method2_cell_edit)
        self.method2_entry.bind('<FocusOut>', self.save_method2_cell_edit)
        self.method2_entry.bind('<Escape>', self.cancel_method2_cell_edit)
        
        # 初始化数据存储
        self.method2_data = []
        
        # 添加初始2行
        self.add_method2_table_row()
        self.add_method2_table_row()

        # 初始化变量
        if not hasattr(self, 'method2_g_var'):
            self.method2_g_var = tk.StringVar()
        if not hasattr(self, 'method2_e_var'):
            self.method2_e_var = tk.StringVar()
        
        
        
        # 右侧：曲线图 - 限制高度
        right_frame = ttk.Frame(main_content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 曲线图标题
        plot_title = ttk.Label(right_frame, text="x-y关系曲线", font=("Arial", 10, "bold"))
        plot_title.pack(pady=(0, 3))
        
        # 创建matplotlib图形 - 进一步减小图形尺寸
        self.method2_fig = plt.figure(figsize=(2.6, 2))  # 进一步减小尺寸
        self.method2_ax = self.method2_fig.add_subplot(111)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        self.method2_ax.set_xlabel('x/m^2', fontsize=8)
        self.method2_ax.set_ylabel('y/m·s^2', fontsize=8)
        # self.method2_ax.set_title('x-y关系曲线', fontsize=9)
        self.method2_ax.grid(True, alpha=0.3)
        
        # 进一步调整图形布局，减少边距
        self.method2_fig.tight_layout(pad=0.5)
        
        # 将matplotlib图形嵌入到tkinter
        self.method2_canvas = FigureCanvasTkAgg(self.method2_fig, right_frame)
        self.method2_canvas.draw()
        self.method2_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 恢复保存的数据 - 在界面创建完成后立即调用
        self.restore_method2_data()

        # +++ 修复：结果和按钮框架 - 放在主内容框架外部 +++
        bottom_frame = ttk.Frame(self.content_frame)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 第一行：结果显示
        result_frame = ttk.Frame(bottom_frame)
        result_frame.pack(fill=tk.X, pady=(5, 5))
        
        # 重力加速度g
        ttk.Label(result_frame, text="重力加速度g (m/s^2)(参考值9.8):").pack(side=tk.LEFT, padx=5)
        self.method2_g_var = tk.StringVar()
        g_entry = ttk.Entry(result_frame, textvariable=self.method2_g_var, width=12, state="readonly")
        g_entry.pack(side=tk.LEFT, padx=5)
        
        # 误差E
        ttk.Label(result_frame, text="误差E (%):").pack(side=tk.LEFT, padx=5)
        self.method2_e_var = tk.StringVar()
        e_entry = ttk.Entry(result_frame, textvariable=self.method2_e_var, width=10, state="readonly")
        e_entry.pack(side=tk.LEFT, padx=5)
        
        # 第二行：按钮
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 使用更小的按钮布局
        button_config = {'side': tk.LEFT, 'padx': 3, 'pady': 2}

        # 计算按钮
        calc_button = ttk.Button(button_frame, text="计算", 
                                command=self.calculate_gravity_method2)
        calc_button.pack(**button_config)

        # 删除选中行按钮
        delete_button = ttk.Button(button_frame, text="删除选中行", 
                                command=self.delete_selected_method2_row)
        delete_button.pack(**button_config)
        
        # 清空数据按钮
        clear_button = ttk.Button(button_frame, text="清空数据", 
                                command=self.clear_method2_data)
        clear_button.pack(**button_config)
        
        # 导出数据按钮
        export_button = ttk.Button(button_frame, text="导出数据", 
                                command=self.export_method2_data)
        export_button.pack(**button_config)
        
        # 导入数据按钮
        import_button = ttk.Button(button_frame, text="导入数据", 
                                command=self.import_method2_data)
        import_button.pack(**button_config)
        
        
        
        # 初始化选中行
        self.selected_method2_row = None
        
        # 恢复保存的数据
        self.restore_method2_data()

    def add_method2_table_row(self):
        """添加新行到方法二表格 - 确保数据结构正确"""
        item_id = self.method2_table.insert("", "end", values=("", "", "", ""))
        self.method2_data.append({
            "id": item_id, 
            "h": "", 
            "T": "", 
            "x": "", 
            "y": ""
        })
        print(f"添加新行，ID: {item_id}")

    def on_method2_table_double_click(self, event):
        """处理表格双击事件 - 直接编辑"""
        item = self.method2_table.selection()[0] if self.method2_table.selection() else None
        if item:
            column = self.method2_table.identify_column(event.x)
            col_index = int(column.replace('#', '')) - 1
            
            # 只允许编辑前两列（h和T）
            if col_index in [0, 1]:
                self.start_method2_cell_edit(item, col_index)

    def start_method2_cell_edit(self, item, col_index):
        """开始编辑单元格"""
        # 获取单元格位置和大小
        bbox = self.method2_table.bbox(item, column=f'#{col_index+1}')
        if not bbox:
            return
        
        # 获取当前值
        current_values = self.method2_table.item(item, 'values')
        current_value = current_values[col_index]
        
        # 设置编辑条目的位置和大小
        self.method2_entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        
        # 设置编辑条目的值
        self.method2_entry.delete(0, tk.END)
        self.method2_entry.insert(0, current_value)
        self.method2_entry.select_range(0, tk.END)
        self.method2_entry.focus()
        
        # 保存编辑状态
        self.method2_editing_item = item
        self.method2_editing_column = col_index

    def cancel_method2_cell_edit(self, event=None):
        """取消单元格编辑"""
        self.method2_entry.place_forget()
        self.method2_editing_item = None
        self.method2_editing_column = None

    def save_method2_cell_edit(self, event=None):
        """保存单元格编辑"""
        if not hasattr(self, 'method2_editing_item') or not self.method2_editing_item:
            return
        
        new_value = self.method2_entry.get().strip()
        item = self.method2_editing_item
        col_index = self.method2_editing_column
        
        # 验证输入
        try:
            if new_value and float(new_value) <= 0:
                # 输入值无效，恢复原值
                self.cancel_method2_cell_edit()
                return
        except ValueError:
            if new_value:  # 非空值需要是数字
                self.cancel_method2_cell_edit()
                return
        
        # 更新表格
        current_values = list(self.method2_table.item(item, 'values'))
        current_values[col_index] = new_value
        self.method2_table.item(item, values=current_values)
        
        # 更新数据存储
        self.update_method2_data(item, col_index, new_value)
        
        # 自动计算x和y
        if new_value and col_index in [0, 1]:
            self.calculate_method2_xy(item)
        
        # 立即保存数据
        self.save_current_experiment_data()
        
        # 隐藏编辑条目
        self.method2_entry.place_forget()
        
        # 清除编辑状态
        self.method2_editing_item = None
        self.method2_editing_column = None

    def on_method2_table_select(self, event):
        """处理表格选择事件"""
        selection = self.method2_table.selection()
        self.selected_method2_row = selection[0] if selection else None

    def update_method2_data(self, item_id, col_index, value):
        """更新数据存储"""
        for data in self.method2_data:
            if data["id"] == item_id:
                if col_index == 0:  # h列
                    data["h"] = value
                elif col_index == 1:  # T列
                    data["T"] = value
                break

    def calculate_method2_xy(self, item_id):
        """计算x和y值"""
        for data in self.method2_data:
            if data["id"] == item_id:
                try:
                    h = float(data["h"]) if data["h"] else 0
                    T = float(data["T"]) if data["T"] else 0
                    
                    if h > 0 and T > 0:
                        # x = h^2 (转换为m^2)
                        x = (h / 100) ** 2  # cm转换为m
                        # y = T^2 * h (转换为m·s^2)
                        y = (T ** 2) * (h / 100)  # cm转换为m
                        
                        data["x"] = f"{x:.4f}"
                        data["y"] = f"{y:.3f}"
                        
                        # 更新表格显示
                        current_values = list(self.method2_table.item(item_id, 'values'))
                        current_values[2] = f"{x:.4f}"
                        current_values[3] = f"{y:.3f}"
                        self.method2_table.item(item_id, values=current_values)
                        
                    else:
                        data["x"] = ""
                        data["y"] = ""
                        current_values = list(self.method2_table.item(item_id, 'values'))
                        current_values[2] = ""
                        current_values[3] = ""
                        self.method2_table.item(item_id, values=current_values)
                        
                except ValueError:
                    data["x"] = ""
                    data["y"] = ""
                    current_values = list(self.method2_table.item(item_id, 'values'))
                    current_values[2] = ""
                    current_values[3] = ""
                    self.method2_table.item(item_id, values=current_values)
                
                break
        
        # 更新曲线图
        self.update_method2_plot()
        
        # 检查是否需要添加新行
        self.check_add_method2_row()

    def check_add_method2_row(self):
        """检查是否需要添加新行"""
        # 检查最后一行是否有数据
        last_item = self.method2_table.get_children()[-1]
        last_values = self.method2_table.item(last_item, 'values')
        
        if last_values[0] or last_values[1]:  # h或T有数据
            self.add_method2_table_row()

    def update_method2_plot(self):
        """更新曲线图 - 修改为使用保存的数据"""
        # 收集有效数据点
        x_data = []
        y_data = []
        
        for data in self.method2_data:
            if data["x"] and data["y"]:
                try:
                    x = float(data["x"])
                    y = float(data["y"])
                    x_data.append(x)
                    y_data.append(y)
                except ValueError:
                    continue
        
        # 保存当前数据点到实验数据中
        xy_data_points = [{"x": x, "y": y} for x, y in zip(x_data, y_data)]
        if "gravity_method2" in self.experiment_data:
            self.experiment_data["gravity_method2"]["xy_data_points"] = xy_data_points
        
        # 绘制图形
        self.method2_ax.clear()
        
        if x_data and y_data:
            self.method2_ax.scatter(x_data, y_data, color='blue', s=30, alpha=0.7, label='数据点')
            
            # 如果有两个以上点，显示拟合线（但不在计算按钮按下时不显示公式）
            if len(x_data) >= 2:
                # 只是显示点，不拟合直线，等计算按钮按下时才拟合
                pass
        
        self.method2_ax.set_xlabel('x/m^2', fontsize=9)
        self.method2_ax.set_ylabel('y/m·s^2', fontsize=9)
        # self.method2_ax.set_title('x-y关系曲线', fontsize=10)
        self.method2_ax.grid(True, alpha=0.3)
        if x_data and y_data:
            self.method2_ax.legend(fontsize=8)
        
        self.method2_fig.tight_layout(pad=0.5)
        self.method2_fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.20)
        self.method2_canvas.draw()

    def delete_selected_method2_row(self):
        """删除选中行"""
        if self.selected_method2_row:
            if tk.messagebox.askyesno("确认", "确定要删除选中的行吗？"):
                # 从数据存储中删除
                self.method2_data = [data for data in self.method2_data if data["id"] != self.selected_method2_row]
                
                # 从表格中删除
                self.method2_table.delete(self.selected_method2_row)
                self.selected_method2_row = None
                
                # 更新曲线图
                self.update_method2_plot()

    def clear_method2_data(self):
        """清空所有数据"""
        if tk.messagebox.askyesno("确认", "确定要清空所有数据吗？"):
            # 清空表格
            for item in self.method2_table.get_children():
                self.method2_table.delete(item)
            
            # 清空数据存储
            self.method2_data = []
            
            # 添加初始2行
            self.add_method2_table_row()
            self.add_method2_table_row()
            
            # 清空曲线图
            self.method2_ax.clear()
            self.method2_ax.set_xlabel('x/m^2')
            self.method2_ax.set_ylabel('y/m·s^2')
            # self.method2_ax.set_title('x-y关系曲线')
            self.method2_ax.grid(True, alpha=0.3)
            self.method2_canvas.draw()
            
            # 清空结果显示
            self.method2_g_var.set("")
            self.method2_e_var.set("")
            # 保存清空后的状态
            self.save_current_experiment_data()

    def export_method2_data(self):
        """导出方法二的数据到Excel - 多线程版本"""
        try:
            import pandas as pd
            from tkinter import filedialog
            import threading
            
            # 预先收集数据，避免在子线程中访问UI
            export_data = []
            for data in self.method2_data:
                if data["h"] or data["T"]:
                    export_data.append({
                        "h_cm": data["h"] if data["h"] else "",
                        "T_s": data["T"] if data["T"] else "",
                        "x_m2": data["x"] if data["x"] else "",
                        "y_ms2": data["y"] if data["y"] else ""
                    })
            
            if not export_data:
                tk.messagebox.showwarning("警告", "没有可导出的数据")
                return
            
            # 收集计算结果数据
            result_data = {
                "参数": ["重力加速度g (m/s^2)", "误差E (%)"],
                "数值": [
                    self.method2_g_var.get() if self.method2_g_var.get() else "",
                    self.method2_e_var.get() if self.method2_e_var.get() else ""
                ]
            }
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            self.show_export_progress("正在导出方法二数据...")
            
            def export_thread():
                try:
                    # 使用openpyxl引擎，性能更好
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        # 第一页：表格数据
                        if export_data:
                            df_table = pd.DataFrame(export_data)
                            df_table.to_excel(writer, sheet_name='数据记录表', index=False)
                        
                        # 第二页：计算结果
                        df_result = pd.DataFrame(result_data)
                        df_result.to_excel(writer, sheet_name='计算结果', index=False)
                    
                    self.root.after(0, lambda: self.hide_export_progress())
                    self.root.after(0, lambda: tk.messagebox.showinfo("成功", f"数据已导出到: {file_path}"))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.hide_export_progress())
                    self.root.after(0, lambda: tk.messagebox.showerror("错误", f"导出失败: {str(e)}"))
            
            thread = threading.Thread(target=export_thread, daemon=True)
            thread.start()
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas库: pip install pandas")
        except Exception as e:
            self.hide_export_progress()
            tk.messagebox.showerror("错误", f"导出失败: {str(e)}")

    def import_method2_data(self):
        """从Excel导入数据 - 修复卡顿版本"""
        try:
            import pandas as pd
            from tkinter import filedialog
            import threading
            
            # 选择文件
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            # 显示导入进度
            self.show_import_progress("正在导入数据...")
            
            # 在新线程中执行导入操作
            def import_thread():
                try:
                    # 读取第一页：数据记录表
                    df_table = pd.read_excel(file_path, sheet_name='数据记录表')
                    
                    # 在主线程中更新UI
                    self.root.after(0, self.update_method2_table, df_table)
                    
                    # 读取第二页：计算结果
                    try:
                        df_result = pd.read_excel(file_path, sheet_name='计算结果')
                        self.root.after(0, self.update_method2_results, df_result)
                    except Exception as e:
                        print(f"读取计算结果失败: {e}")
                    
                    # 隐藏进度提示
                    self.root.after(0, self.hide_import_progress)
                    self.root.after(0, lambda: tk.messagebox.showinfo("成功", "数据导入完成"))
                    
                except Exception as e:
                    # 错误处理
                    self.root.after(0, self.hide_import_progress)
                    self.root.after(0, lambda: tk.messagebox.showerror("错误", f"导入失败: {str(e)}"))
            
            # 启动导入线程
            thread = threading.Thread(target=import_thread, daemon=True)
            thread.start()
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas库: pip install pandas")
        except Exception as e:
            self.hide_import_progress()
            tk.messagebox.showerror("错误", f"导入失败: {str(e)}")
    
    def update_method2_table(self, df_table):
        """更新方法二表格数据"""
        # 清空现有数据
        for item in self.method2_table.get_children():
            self.method2_table.delete(item)
        self.method2_data = []
        
        # 导入表格数据
        for index, row in df_table.iterrows():
            if index >= len(self.method2_data):
                self.add_method2_table_row()
            
            item_id = self.method2_data[index]["id"]
            
            # 更新数据
            h_value = str(row['h_cm']) if 'h_cm' in row and pd.notna(row['h_cm']) else ""
            T_value = str(row['T_s']) if 'T_s' in row and pd.notna(row['T_s']) else ""
            
            # 更新表格
            self.method2_table.item(item_id, values=(h_value, T_value, "", ""))
            
            # 更新数据存储并计算x,y
            self.update_method2_data(item_id, 0, h_value)
            self.update_method2_data(item_id, 1, T_value)
            if h_value or T_value:
                self.calculate_method2_xy(item_id)

    def update_method2_results(self, df_result):
        """更新方法二计算结果"""
        
        if not df_result.empty and '参数' in df_result.columns and '数值' in df_result.columns:
            for _, row in df_result.iterrows():
                param = row['参数']
                value = row['数值']
                
                if pd.notna(param) and pd.notna(value):
                    if param == "重力加速度g (m/s^2)":
                        self.method2_g_var.set(str(value))
                    elif param == "误差E (%)":
                        self.method2_e_var.set(str(value))

    def show_import_progress(self, message="正在导入..."):
        """显示导入进度提示"""
        if hasattr(self, 'progress_window') and self.progress_window.winfo_exists():
            self.progress_window.destroy()
        
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("导入数据")
        self.progress_window.geometry("300x100")
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        
        # 居中显示
        self.progress_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 300) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 100) // 2
        self.progress_window.geometry(f"+{x}+{y}")
        
        ttk.Label(self.progress_window, text=message, font=("Arial", 12)).pack(pady=20)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(self.progress_window, variable=self.progress_var, 
                                    mode='indeterminate', length=250)
        progress_bar.pack(pady=10)
        progress_bar.start(10)

    def hide_import_progress(self):
        """隐藏导入进度提示"""
        if hasattr(self, 'progress_window') and self.progress_window.winfo_exists():
            self.progress_window.destroy()

    def calculate_gravity_method2(self):
        """计算方法二的重力加速度和误差"""
        try:
            # 收集有效数据点
            x_data = []
            y_data = []
            
            for data in self.method2_data:
                if data["x"] and data["y"]:
                    try:
                        x = float(data["x"])
                        y = float(data["y"])
                        x_data.append(x)
                        y_data.append(y)
                    except ValueError:
                        continue
            
            if len(x_data) < 2:
                tk.messagebox.showerror("错误", "至少需要2个有效数据点进行计算")
                return
            
            # 线性拟合
            import numpy as np
            slope, intercept = np.polyfit(x_data, y_data, 1)
            
            # 计算重力加速度: g = 4π^2 / 斜率
            g = 4 * (3.1415 ** 2) / slope
            
            # 计算误差
            theoretical_g = 9.8
            error_percent = abs((g - theoretical_g) / theoretical_g) * 100
            
            # 更新结果显示
            self.method2_g_var.set(f"{g:.4f}")
            self.method2_e_var.set(f"{error_percent:.2f}%")
            
            # 更新曲线图，显示拟合直线和公式
            self.method2_ax.clear()
            
            # 绘制散点
            self.method2_ax.scatter(x_data, y_data, color='blue', s=30, alpha=0.7, label='数据点')
            
            # 绘制拟合直线
            x_fit = np.linspace(min(x_data), max(x_data), 100)
            y_fit = slope * x_fit + intercept
            self.method2_ax.plot(x_fit, y_fit, 'r-', linewidth=1, label=f'y={slope:.4f}x+{intercept:.4f}')
            
            # 显示公式
            equation_text = f'y = {slope:.4f}x + {intercept:.4f}\n'
            equation_text += f'g = 4π^2/k = {g:.4f} m/s^2\n'
            equation_text += f'误差: {error_percent:.2f}%'
            
            self.method2_ax.text(0.05, 0.95, equation_text, transform=self.method2_ax.transAxes,
                            verticalalignment='top', fontsize=8,
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            self.method2_ax.set_xlabel('x/m^2', fontsize=9)
            self.method2_ax.set_ylabel('y/m·s^2', fontsize=9)
            # self.method2_ax.set_title('x-y关系曲线', fontsize=10)
            self.method2_ax.grid(True, alpha=0.3)
            self.method2_ax.legend(fontsize=8)
            
            self.method2_fig.tight_layout(pad=0.5)
            self.method2_canvas.draw()
            
            # 保存数据和计算结果
            self.save_current_experiment_data()
            
            print(f"重力加速度计算完成: g = {g:.4f} m/s^2, 误差: {error_percent:.2f}%")
        
        except Exception as e:
            tk.messagebox.showerror("错误", f"计算过程中发生错误: {str(e)}")

    def restore_method2_data(self):
        """恢复方法二的数据 - 修复版本"""
        if "gravity_method2" not in self.experiment_data:
            return
            
        data = self.experiment_data["gravity_method2"]
        
        # 清空现有数据
        for item in self.method2_table.get_children():
            self.method2_table.delete(item)
        self.method2_data = []
        
        # 恢复表格数据
        if "table_data" in data and data["table_data"]:
            for row_data in data["table_data"]:
                # 添加新行
                item_id = self.method2_table.insert("", "end", values=("", "", "", ""))
                
                # 更新数据存储
                new_data = {
                    "id": item_id,
                    "h": row_data.get("h", ""),
                    "T": row_data.get("T", ""),
                    "x": row_data.get("x", ""),
                    "y": row_data.get("y", "")
                }
                self.method2_data.append(new_data)
                
                # 更新表格显示
                self.method2_table.item(item_id, values=(
                    new_data["h"],
                    new_data["T"], 
                    new_data["x"],
                    new_data["y"]
                ))
        
        # 如果没有数据，添加默认的2行
        if not self.method2_data:
            self.add_method2_table_row()
            self.add_method2_table_row()
        
        # 恢复计算结果
        if "g" in data:
            self.method2_g_var.set(data["g"])
        if "e" in data:
            self.method2_e_var.set(data["e"])
        
        # +++ 新增：如果有计算结果，恢复拟合曲线 +++
        if (self.method2_g_var.get() and self.method2_e_var.get() and 
            "xy_data_points" in data and data["xy_data_points"]):
            self.restore_method2_plot_with_fit(data["xy_data_points"])
        elif "xy_data_points" in data and data["xy_data_points"]:
            # 只有数据点，没有计算结果
            self.update_method2_plot_with_data(data["xy_data_points"])
        else:
            # 没有数据，显示空图表
            self.update_method2_plot()
        
        print(f"方法二数据恢复完成，恢复{len(self.method2_data)}行数据")

    def restore_method2_plot_with_fit(self, xy_data_points):
        """恢复方法二的拟合曲线"""
        try:
            import numpy as np
            
            # 提取数据点
            x_data = [point["x"] for point in xy_data_points]
            y_data = [point["y"] for point in xy_data_points]
            
            if len(x_data) < 2:
                return
            
            # 重新计算拟合参数
            slope, intercept = np.polyfit(x_data, y_data, 1)
            
            # 计算重力加速度和误差
            g = 4 * (3.1415 ** 2) / slope
            theoretical_g = 9.8
            error_percent = abs((g - theoretical_g) / theoretical_g) * 100
            
            # 更新曲线图
            self.method2_ax.clear()
            
            # 绘制散点
            self.method2_ax.scatter(x_data, y_data, color='blue', s=30, alpha=0.7, label='数据点')
            
            # 绘制拟合直线
            x_fit = np.linspace(min(x_data), max(x_data), 100)
            y_fit = slope * x_fit + intercept
            self.method2_ax.plot(x_fit, y_fit, 'r-', linewidth=1, label=f'y={slope:.4f}x+{intercept:.4f}')
            
            # 显示公式
            equation_text = f'y = {slope:.4f}x + {intercept:.4f}\n'
            equation_text += f'g = 4π^2/k = {g:.4f} m/s^2\n'
            equation_text += f'误差: {error_percent:.2f}%'
            
            self.method2_ax.text(0.05, 0.95, equation_text, transform=self.method2_ax.transAxes,
                            verticalalignment='top', fontsize=8,
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            self.method2_ax.set_xlabel('x/m^2', fontsize=9)
            self.method2_ax.set_ylabel('y/m·s^2', fontsize=9)
            self.method2_ax.grid(True, alpha=0.3)
            self.method2_ax.legend(fontsize=8)
            
            self.method2_fig.tight_layout(pad=0.5)
            self.method2_canvas.draw()
            
            print("方法二拟合曲线恢复完成")
            
        except Exception as e:
            print(f"恢复方法二拟合曲线时出错: {e}")
            # 回退到只显示散点图
            self.update_method2_plot_with_data(xy_data_points)

    def update_method2_plot_with_data(self, xy_data_points):
        """使用保存的数据点更新曲线图"""
        self.method2_ax.clear()
        
        if xy_data_points:
            # 提取x和y数据
            x_data = [point["x"] for point in xy_data_points]
            y_data = [point["y"] for point in xy_data_points]
            
            # 绘制散点图
            self.method2_ax.scatter(x_data, y_data, color='blue', s=30, alpha=0.7, label='数据点')
            
            # 检查是否有计算结果需要显示拟合线
            if self.method2_g_var.get() and len(x_data) >= 2:
                try:
                    import numpy as np
                    # 重新计算拟合线
                    slope, intercept = np.polyfit(x_data, y_data, 1)
                    
                    # 绘制拟合直线
                    x_fit = np.linspace(min(x_data), max(x_data), 100)
                    y_fit = slope * x_fit + intercept
                    self.method2_ax.plot(x_fit, y_fit, 'r-', linewidth=1, label=f'y={slope:.4f}x+{intercept:.4f}')
                    
                    # 显示公式
                    g = 4 * (3.1415 ** 2) / slope
                    error_percent = float(self.method2_e_var.get().replace('%', '')) if self.method2_e_var.get() else 0
                    
                    equation_text = f'y = {slope:.4f}x + {intercept:.4f}\n'
                    equation_text += f'g = 4π^2/k = {g:.4f} m/s^2\n'
                    equation_text += f'误差: {error_percent:.2f}%'
                    
                    self.method2_ax.text(0.05, 0.95, equation_text, transform=self.method2_ax.transAxes,
                                    verticalalignment='top', fontsize=8,
                                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                    
                except Exception as e:
                    print(f"重新绘制拟合线时出错: {e}")
        
        self.method2_ax.set_xlabel('x/m^2', fontsize=9)
        self.method2_ax.set_ylabel('y/m·s^2', fontsize=9)
        # self.method2_ax.set_title('x-y关系曲线', fontsize=10)
        self.method2_ax.grid(True, alpha=0.3)
        if xy_data_points:
            self.method2_ax.legend(fontsize=8)
        
        self.method2_fig.tight_layout(pad=0.5)
        self.method2_fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.2)
        self.method2_canvas.draw()

    def save_method2_data(self):
        """保存方法二的数据 - 修复版本"""
        try:
            # 收集表格数据
            table_data = []
            for data in self.method2_data:
                table_data.append({
                    "h": data.get("h", ""),
                    "T": data.get("T", ""), 
                    "x": data.get("x", ""),
                    "y": data.get("y", "")
                })
            
            # 收集x-y数据点用于曲线图
            xy_data_points = []
            for data in self.method2_data:
                if data.get("x") and data.get("y"):
                    try:
                        x = float(data["x"])
                        y = float(data["y"])
                        xy_data_points.append({"x": x, "y": y})
                    except ValueError:
                        continue
            
            # 保存到实验数据
            self.experiment_data["gravity_method2"] = {
                "table_data": table_data,
                "xy_data_points": xy_data_points,
                "g": self.method2_g_var.get() if hasattr(self, 'method2_g_var') else "",
                "e": self.method2_e_var.get() if hasattr(self, 'method2_e_var') else ""
            }
            print(f"方法二数据保存成功: {len(table_data)}行数据")
        except Exception as e:
            print(f"保存方法二数据时出错: {e}")
            import traceback
            traceback.print_exc()

    def create_gravity_acceleration_method3(self):
        """创建测量重力加速度（方法三）的实验内容"""
        # 清空现有内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_label = ttk.Label(self.content_frame, text="测量重力加速度（方法三）", 
                                font=("Arial", 12, "bold"))
        title_label.pack(pady=(10, 5))
        
        # 主内容框架 - 左右布局
        main_content_frame = ttk.Frame(self.content_frame)
        main_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：数据表格
        left_frame = ttk.Frame(main_content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 表格标题
        table_title = ttk.Label(left_frame, text="数据记录表", font=("Arial", 10, "bold"))
        table_title.pack(pady=(0, 3))
        
        # 创建表格框架
        table_frame = ttk.Frame(left_frame, height=150)
        table_frame.pack(fill=tk.BOTH, expand=False)
        table_frame.pack_propagate(False)
        
        # 创建Treeview表格
        columns = ("o1a", "t1", "t2")
        self.method3_table = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            height=4
        )
        
        # 设置列标题
        self.method3_table.heading("o1a", text="O1A/cm")
        self.method3_table.heading("t1", text="T1/s")
        self.method3_table.heading("t2", text="T2/s")
        
        # 设置列宽
        self.method3_table.column("o1a", width=80)
        self.method3_table.column("t1", width=80)
        self.method3_table.column("t2", width=80)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.method3_table.yview)
        self.method3_table.configure(yscrollcommand=scrollbar.set)
        
        # 布局表格和滚动条
        self.method3_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定表格事件
        self.method3_table.bind('<Double-1>', self.on_method3_table_double_click)
        self.method3_table.bind('<<TreeviewSelect>>', self.on_method3_table_select)
        
        # 创建编辑条目
        self.method3_entry = ttk.Entry(table_frame, width=10)
        self.method3_entry.pack_forget()  # 初始隐藏
        
        # 绑定编辑条目的相关事件
        self.method3_entry.bind('<Return>', self.save_method3_cell_edit)
        self.method3_entry.bind('<FocusOut>', self.save_method3_cell_edit)
        self.method3_entry.bind('<Escape>', self.cancel_method3_cell_edit)
        
        # 初始化数据存储
        self.method3_data = []
        
        # 添加初始2行
        self.add_method3_table_row()
        self.add_method3_table_row()

        # 右侧：曲线图
        right_frame = ttk.Frame(main_content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 曲线图标题
        plot_title = ttk.Label(right_frame, text="T1、T2与O1A关系曲线", font=("Arial", 10, "bold"))
        plot_title.pack(pady=(0, 3))
        
        # 创建matplotlib图形
        self.method3_fig = plt.figure(figsize=(2.6, 1.6))
        self.method3_ax = self.method3_fig.add_subplot(111)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        self.method3_ax.set_xlabel('O1A/cm', fontsize=8)
        self.method3_ax.set_ylabel('T/s', fontsize=8)
        self.method3_ax.grid(True, alpha=0.3)
        
        # 调整图形布局
        self.method3_fig.tight_layout(pad=0.5)
        
        # 将matplotlib图形嵌入到tkinter
        self.method3_canvas = FigureCanvasTkAgg(self.method3_fig, right_frame)
        self.method3_canvas.draw()
        self.method3_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 底部：输入框和结果显示区域
        bottom_frame = ttk.Frame(self.content_frame)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 第一行：输入和结果显示
        row1_frame = ttk.Frame(bottom_frame)
        row1_frame.pack(fill=tk.X, pady=(5, 5))
        
        # O1位置
        ttk.Label(row1_frame, text="O1位置 (cm):").pack(side=tk.LEFT, padx=5)
        self.o1_var = tk.StringVar()
        o1_entry = ttk.Entry(row1_frame, textvariable=self.o1_var, width=10)
        o1_entry.pack(side=tk.LEFT, padx=5)
        
        # O2位置
        ttk.Label(row1_frame, text="O2位置 (cm):").pack(side=tk.LEFT, padx=5)
        self.o2_var = tk.StringVar()
        o2_entry = ttk.Entry(row1_frame, textvariable=self.o2_var, width=10)
        o2_entry.pack(side=tk.LEFT, padx=5)

        # O1O2距离l（自动计算，只读）
        ttk.Label(row1_frame, text="O1O2距离l (cm):").pack(side=tk.LEFT, padx=5)
        self.l_var = tk.StringVar()
        l_entry = ttk.Entry(row1_frame, textvariable=self.l_var, width=10, state="readonly")
        l_entry.pack(side=tk.LEFT, padx=5)
        
        # 绑定O1和O2变化事件，自动计算距离
        self.o1_var.trace_add('write', self.auto_calculate_o1o2_distance)
        self.o2_var.trace_add('write', self.auto_calculate_o1o2_distance)

        # 第二行：交点坐标和平均值
        row2_frame = ttk.Frame(bottom_frame)
        row2_frame.pack(fill=tk.X, pady=(5, 5))

        # 交点P1纵坐标
        ttk.Label(row2_frame, text="交点P1纵坐标(s):").pack(side=tk.LEFT, padx=5)
        self.p1_var = tk.StringVar()
        p1_entry = ttk.Entry(row2_frame, textvariable=self.p1_var, width=10, state="readonly")
        p1_entry.pack(side=tk.LEFT, padx=5)
        
        # 交点P2纵坐标
        ttk.Label(row2_frame, text="交点P2纵坐标(s):").pack(side=tk.LEFT, padx=5)
        self.p2_var = tk.StringVar()
        p2_entry = ttk.Entry(row2_frame, textvariable=self.p2_var, width=10, state="readonly")
        p2_entry.pack(side=tk.LEFT, padx=5)
        
        # 平均值T
        ttk.Label(row2_frame, text="平均值T(s):").pack(side=tk.LEFT, padx=5)
        self.t_avg_var = tk.StringVar()
        t_avg_entry = ttk.Entry(row2_frame, textvariable=self.t_avg_var, width=10, state="readonly")
        t_avg_entry.pack(side=tk.LEFT, padx=5)
        
        # 第三行：重力加速度和误差
        row3_frame = ttk.Frame(bottom_frame)
        row3_frame.pack(fill=tk.X, pady=(5, 5))
        
        # 重力加速度g
        ttk.Label(row3_frame, text="重力加速度g (m/s^2)(参考值9.8):").pack(side=tk.LEFT, padx=5)
        self.method3_g_var = tk.StringVar()
        g_entry = ttk.Entry(row3_frame, textvariable=self.method3_g_var, width=12, state="readonly")
        g_entry.pack(side=tk.LEFT, padx=5)
        
        # 误差E
        ttk.Label(row3_frame, text="误差E (%):").pack(side=tk.LEFT, padx=5)
        self.method3_e_var = tk.StringVar()
        e_entry = ttk.Entry(row3_frame, textvariable=self.method3_e_var, width=10, state="readonly")
        e_entry.pack(side=tk.LEFT, padx=5)
        
        # 第三行：按钮
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X, pady=(5, 5))
        
        # 按钮配置
        button_config = {'side': tk.LEFT, 'padx': 3, 'pady': 2}
        
        # 计算按钮
        calc_button = ttk.Button(button_frame, text="计算", 
                                command=self.calculate_gravity_method3)
        calc_button.pack(**button_config)

        # 删除选中行按钮
        delete_button = ttk.Button(button_frame, text="删除选中行", 
                                command=self.delete_selected_method3_row)
        delete_button.pack(**button_config)
        
        # 清空数据按钮
        clear_button = ttk.Button(button_frame, text="清空数据", 
                                command=self.clear_method3_data)
        clear_button.pack(**button_config)
        
        # 导出数据按钮
        export_button = ttk.Button(button_frame, text="导出数据", 
                                command=self.export_method3_data)
        export_button.pack(**button_config)
        
        # 导入数据按钮
        import_button = ttk.Button(button_frame, text="导入数据", 
                                command=self.import_method3_data)
        import_button.pack(**button_config)
        
        
        
        # 初始化选中行
        self.selected_method3_row = None
        
        # 恢复保存的数据
        self.restore_method3_data()

    def auto_calculate_o1o2_distance(self, *args):
        """根据O1和O2位置自动计算O1O2距离"""
        try:
            if self.o1_var.get() and self.o2_var.get():
                o1 = float(self.o1_var.get())
                o2 = float(self.o2_var.get())
                # 计算距离：l = |O2 - O1|
                distance = abs(o2 - o1)
                self.l_var.set(f"{distance:.1f}")  # 保留1位小数
            else:
                self.l_var.set("")
        except ValueError:
            self.l_var.set("")

    def add_method3_table_row(self):
        """添加新行到方法三表格"""
        item_id = self.method3_table.insert("", "end", values=("", "", ""))
        self.method3_data.append({
            "id": item_id, 
            "o1a": "", 
            "t1": "", 
            "t2": ""
        })

    def on_method3_table_double_click(self, event):
        """处理表格双击事件"""
        item = self.method3_table.selection()[0] if self.method3_table.selection() else None
        if item:
            column = self.method3_table.identify_column(event.x)
            col_index = int(column.replace('#', '')) - 1
            self.start_method3_cell_edit(item, col_index)

    def start_method3_cell_edit(self, item, col_index):
        """开始编辑单元格"""
        bbox = self.method3_table.bbox(item, column=f'#{col_index+1}')
        if not bbox:
            return
        
        current_values = self.method3_table.item(item, 'values')
        current_value = current_values[col_index]
        
        self.method3_entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        self.method3_entry.delete(0, tk.END)
        self.method3_entry.insert(0, current_value)
        self.method3_entry.select_range(0, tk.END)
        self.method3_entry.focus()
        
        self.method3_editing_item = item
        self.method3_editing_column = col_index

    def save_method3_cell_edit(self, event=None):
        """保存单元格编辑"""
        if not hasattr(self, 'method3_editing_item') or not self.method3_editing_item:
            return
        
        new_value = self.method3_entry.get().strip()
        item = self.method3_editing_item
        col_index = self.method3_editing_column
        
        # 验证输入
        try:
            if new_value and float(new_value) <= 0:
                self.cancel_method3_cell_edit()
                return
        except ValueError:
            if new_value:
                self.cancel_method3_cell_edit()
                return
        
        # 更新表格
        current_values = list(self.method3_table.item(item, 'values'))
        current_values[col_index] = new_value
        self.method3_table.item(item, values=current_values)
        
        # 更新数据存储
        self.update_method3_data(item, col_index, new_value)
        
        # 更新曲线图
        self.update_method3_plot()
        
        # 检查是否需要添加新行
        self.check_add_method3_row()
        
        # 隐藏编辑条目
        self.method3_entry.place_forget()
        self.method3_editing_item = None
        self.method3_editing_column = None

    def cancel_method3_cell_edit(self, event=None):
        """取消单元格编辑"""
        self.method3_entry.place_forget()
        self.method3_editing_item = None
        self.method3_editing_column = None

    def on_method3_table_select(self, event):
        """处理表格选择事件"""
        selection = self.method3_table.selection()
        self.selected_method3_row = selection[0] if selection else None

    def update_method3_data(self, item_id, col_index, value):
        """更新数据存储"""
        for data in self.method3_data:
            if data["id"] == item_id:
                if col_index == 0:  # o1a列
                    data["o1a"] = value
                elif col_index == 1:  # t1列
                    data["t1"] = value
                elif col_index == 2:  # t2列
                    data["t2"] = value
                break

    def check_add_method3_row(self):
        """检查是否需要添加新行"""
        last_item = self.method3_table.get_children()[-1]
        last_values = self.method3_table.item(last_item, 'values')
        
        if last_values[0] or last_values[1] or last_values[2]:  # 任意列有数据
            self.add_method3_table_row()

    def update_method3_plot(self):
        """更新曲线图 - 只显示散点"""
        # 收集有效数据点
        o1a_data = []
        t1_data = []
        t2_data = []
        
        for data in self.method3_data:
            if data["o1a"] and data["t1"] and data["t2"]:
                try:
                    o1a = float(data["o1a"])
                    t1 = float(data["t1"])
                    t2 = float(data["t2"])
                    o1a_data.append(o1a)
                    t1_data.append(t1)
                    t2_data.append(t2)
                except ValueError:
                    continue
        
        # 绘制图形
        self.method3_ax.clear()
        
        if o1a_data and t1_data:
            self.method3_ax.scatter(o1a_data, t1_data, color='blue', s=30, alpha=0.7, label='T1')
        
        if o1a_data and t2_data:
            self.method3_ax.scatter(o1a_data, t2_data, color='red', s=30, alpha=0.7, label='T2')
        
        self.method3_ax.set_xlabel('O1A/cm', fontsize=9)
        self.method3_ax.set_ylabel('T/s', fontsize=9)
        self.method3_ax.grid(True, alpha=0.3)
        if o1a_data:
            self.method3_ax.legend(fontsize=8)
        

        self.method3_fig.tight_layout(pad=0.5)
        self.method3_fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.25)
        self.method3_canvas.draw()

    def delete_selected_method3_row(self):
        """删除选中行"""
        if self.selected_method3_row:
            if tk.messagebox.askyesno("确认", "确定要删除选中的行吗？"):
                if self.selected_method3_row:
                    self.method3_data = [data for data in self.method3_data if data["id"] != self.selected_method3_row]
                    self.method3_table.delete(self.selected_method3_row)
                    self.selected_method3_row = None
                    self.update_method3_plot()

    def clear_method3_data(self):
        """清空所有数据"""
        if tk.messagebox.askyesno("确认", "确定要清空所有数据吗？"):
            for item in self.method3_table.get_children():
                self.method3_table.delete(item)
            
            self.method3_data = []
            self.add_method3_table_row()
            self.add_method3_table_row()
            
            self.method3_ax.clear()
            self.method3_ax.set_xlabel('O1A/cm')
            self.method3_ax.set_ylabel('T/s')
            self.method3_ax.grid(True, alpha=0.3)
            self.method3_canvas.draw()
            
             # +++ 新增：清空O1O2位置和距离 +++
            self.o1_var.set("")
            self.o2_var.set("")
            self.l_var.set("")

            # 清空结果显示
            self.p1_var.set("")
            self.p2_var.set("")
            self.t_avg_var.set("")
            self.method3_g_var.set("")
            self.method3_e_var.set("")

    def export_method3_data(self):
        """导出方法三的数据到Excel - 多线程版本"""
        try:
            import pandas as pd
            from tkinter import filedialog
            import threading
            
            # 预先收集数据
            export_data = []
            for data in self.method3_data:
                if data["o1a"] or data["t1"] or data["t2"]:
                    export_data.append({
                        "O1A_cm": data["o1a"] if data["o1a"] else "",
                        "T1_s": data["t1"] if data["t1"] else "",
                        "T2_s": data["t2"] if data["t2"] else ""
                    })
            
            if not export_data:
                tk.messagebox.showwarning("警告", "没有可导出的数据")
                return
            
            # 收集计算结果数据
            result_data = {
                "参数": [
                    "O1位置 (cm)", "O2位置 (cm)", "O1O2距离l (cm)",
                    "交点P1纵坐标(s)", "交点P2纵坐标(s)", "平均值T(s)",
                    "重力加速度g (m/s^2)", "误差E (%)"
                ],
                "数值": [
                    self.o1_var.get() if self.o1_var.get() else "",
                    self.o2_var.get() if self.o2_var.get() else "",
                    self.l_var.get() if self.l_var.get() else "",
                    self.p1_var.get() if self.p1_var.get() else "",
                    self.p2_var.get() if self.p2_var.get() else "",
                    self.t_avg_var.get() if self.t_avg_var.get() else "",
                    self.method3_g_var.get() if self.method3_g_var.get() else "",
                    self.method3_e_var.get() if self.method3_e_var.get() else ""
                ]
            }
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            self.show_export_progress("正在导出方法三数据...")
            
            def export_thread():
                try:
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        # 第一页：表格数据
                        if export_data:
                            df_table = pd.DataFrame(export_data)
                            df_table.to_excel(writer, sheet_name='数据记录表', index=False)
                        
                        # 第二页：计算结果
                        df_result = pd.DataFrame(result_data)
                        df_result.to_excel(writer, sheet_name='计算结果', index=False)
                    
                    self.root.after(0, lambda: self.hide_export_progress())
                    self.root.after(0, lambda: tk.messagebox.showinfo("成功", f"数据已导出到: {file_path}"))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.hide_export_progress())
                    self.root.after(0, lambda: tk.messagebox.showerror("错误", f"导出失败: {str(e)}"))
            
            thread = threading.Thread(target=export_thread, daemon=True)
            thread.start()
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas库: pip install pandas")
        except Exception as e:
            self.hide_export_progress()
            tk.messagebox.showerror("错误", f"导出失败: {str(e)}")

    def import_method3_data(self):
        """从Excel导入方法三数据 - 修复卡顿版本"""
        try:
            import pandas as pd
            from tkinter import filedialog
            import threading
            
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            self.show_import_progress("正在导入方法三数据...")
            
            def import_thread():
                try:
                    # 读取数据记录表
                    df_table = pd.read_excel(file_path, sheet_name='数据记录表')
                    self.root.after(0, self.update_method3_table, df_table)
                    
                    # 读取计算结果
                    try:
                        df_result = pd.read_excel(file_path, sheet_name='计算结果')
                        self.root.after(0, self.update_method3_results, df_result)
                    except Exception as e:
                        print(f"读取计算结果失败: {e}")
                    
                    self.root.after(0, self.hide_import_progress)
                    self.root.after(0, lambda: tk.messagebox.showinfo("成功", "数据导入完成"))
                    
                except Exception as e:
                    self.root.after(0, self.hide_import_progress)
                    self.root.after(0, lambda: tk.messagebox.showerror("错误", f"导入失败: {str(e)}"))
            
            thread = threading.Thread(target=import_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            self.hide_import_progress()
            tk.messagebox.showerror("错误", f"导入失败: {str(e)}")

    def update_method3_table(self, df_table):
        """更新方法三表格数据"""
        for item in self.method3_table.get_children():
            self.method3_table.delete(item)
        self.method3_data = []
        
        for index, row in df_table.iterrows():
            if index >= len(self.method3_data):
                self.add_method3_table_row()
            
            item_id = self.method3_data[index]["id"]
            
            o1a_value = str(row['O1A_cm']) if 'O1A_cm' in row and pd.notna(row['O1A_cm']) else ""
            t1_value = str(row['T1_s']) if 'T1_s' in row and pd.notna(row['T1_s']) else ""
            t2_value = str(row['T2_s']) if 'T2_s' in row and pd.notna(row['T2_s']) else ""
            
            self.method3_table.item(item_id, values=(o1a_value, t1_value, t2_value))
            
            self.update_method3_data(item_id, 0, o1a_value)
            self.update_method3_data(item_id, 1, t1_value)
            self.update_method3_data(item_id, 2, t2_value)
        
        self.update_method3_plot()

    def update_method3_results(self, df_result):
        """更新方法三计算结果"""
        if not df_result.empty and '参数' in df_result.columns and '数值' in df_result.columns:
            for _, row in df_result.iterrows():
                param = row['参数']
                value = row['数值']
                
                if pd.notna(param) and pd.notna(value):
                    if param == "O1位置 (cm)":
                        self.o1_var.set(str(value))
                    elif param == "O2位置 (cm)":
                        self.o2_var.set(str(value))
                    elif param == "O1O2距离l (cm)":
                        self.l_var.set(str(value))
                    elif param == "交点P1纵坐标(s)":
                        self.p1_var.set(str(value))
                    elif param == "交点P2纵坐标(s)":
                        self.p2_var.set(str(value))
                    elif param == "平均值T(s)":
                        self.t_avg_var.set(str(value))
                    elif param == "重力加速度g (m/s^2)":
                        self.method3_g_var.set(str(value))
                    elif param == "误差E (%)":
                        self.method3_e_var.set(str(value))
            
            # 自动计算O1O2距离
            if self.o1_var.get() and self.o2_var.get():
                self.auto_calculate_o1o2_distance()

    def calculate_gravity_method3(self):
        """计算方法三的重力加速度和误差"""
        try:
            # 验证输入数据
            if not all([self.o1_var.get(), self.o2_var.get(), self.l_var.get()]):
                tk.messagebox.showerror("错误", "请输入O1位置和O2位置的值")
                return
            
            # 收集有效数据点
            o1a_data = []
            t1_data = []
            t2_data = []
            
            for data in self.method3_data:
                if data["o1a"] and data["t1"] and data["t2"]:
                    try:
                        o1a = float(data["o1a"])
                        t1 = float(data["t1"])
                        t2 = float(data["t2"])
                        o1a_data.append(o1a)
                        t1_data.append(t1)
                        t2_data.append(t2)
                    except ValueError:
                        continue
            
            if len(o1a_data) < 2:
                tk.messagebox.showerror("错误", "至少需要2个有效数据点进行计算")
                return
            
            # 按O1A排序
            sorted_data = sorted(zip(o1a_data, t1_data, t2_data))
            o1a_sorted, t1_sorted, t2_sorted = zip(*sorted_data)
            
            # 绘制连线
            self.method3_ax.clear()
            
            # 绘制T1曲线（蓝色）
            self.method3_ax.plot(o1a_sorted, t1_sorted, 'b-', linewidth=1, label='T1')
            self.method3_ax.scatter(o1a_sorted, t1_sorted, color='blue', s=30, alpha=0.7)
            
            # 绘制T2曲线（红色）
            self.method3_ax.plot(o1a_sorted, t2_sorted, 'r-', linewidth=1, label='T2')
            self.method3_ax.scatter(o1a_sorted, t2_sorted, color='red', s=30, alpha=0.7)
            
            # 寻找交点
            intersections = self.find_intersections(o1a_sorted, t1_sorted, t2_sorted)
            
            if len(intersections) >= 2:
                p1_y = intersections[0][1]  # 第一个交点的纵坐标
                p2_y = intersections[1][1]  # 第二个交点的纵坐标
                t_avg = (p1_y + p2_y) / 2   # 平均值
                
                # 获取O1O2距离
                l_cm = float(self.l_var.get())
                l = l_cm / 100.0  # 转换为米
                
                # 计算重力加速度: g = 4π^2l / T^2
                g = 4 * (3.1415 ** 2) * l / (t_avg ** 2)
                
                # 计算误差
                theoretical_g = 9.8
                error_percent = abs((g - theoretical_g) / theoretical_g) * 100
                
                # 更新显示
                self.p1_var.set(f"{p1_y:.3f}")
                self.p2_var.set(f"{p2_y:.3f}")
                self.t_avg_var.set(f"{t_avg:.3f}")
                self.method3_g_var.set(f"{g:.4f}")
                self.method3_e_var.set(f"{error_percent:.2f}%")
                
                # 标记交点
                self.method3_ax.scatter([intersections[0][0], intersections[1][0]], 
                                    [p1_y, p2_y], color='green', s=50, marker='x', 
                                    label='交点', zorder=5)
                
                # 显示交点信息
                info_text = f'P1: {p1_y:.3f}s\nP2: {p2_y:.3f}s\nT_avg: {t_avg:.3f}s\ng: {g:.4f}m/s^2'
                self.method3_ax.text(0.05, 0.95, info_text, transform=self.method3_ax.transAxes,
                                verticalalignment='top', fontsize=8,
                                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            else:
                tk.messagebox.showerror("错误", f"找到的交点数量不足: {len(intersections)}个，需要2个")
                return
            
            self.method3_ax.set_xlabel('O1A/cm', fontsize=9)
            self.method3_ax.set_ylabel('T/s', fontsize=9)
            self.method3_ax.grid(True, alpha=0.3)
            self.method3_ax.legend(fontsize=8)
            
            self.method3_fig.tight_layout(pad=0.5)
            self.method3_canvas.draw()
            
        except Exception as e:
            tk.messagebox.showerror("错误", f"计算过程中发生错误: {str(e)}")

    def find_intersections(self, x, y1, y2):
        """寻找两条曲线的交点"""
        intersections = []
        
        for i in range(len(x) - 1):
            # 检查当前区间是否有交点
            if (y1[i] - y2[i]) * (y1[i+1] - y2[i+1]) <= 0:
                # 线性插值求交点
                x_intersect = x[i] + (x[i+1] - x[i]) * (y2[i] - y1[i]) / (y1[i+1] - y1[i] - y2[i+1] + y2[i])
                y_intersect = y1[i] + (y1[i+1] - y1[i]) * (x_intersect - x[i]) / (x[i+1] - x[i])
                intersections.append((x_intersect, y_intersect))
        
        return intersections

    def restore_method3_data(self):
        """恢复方法三的数据"""
        if "gravity_method3" not in self.experiment_data:
            return
            
        data = self.experiment_data["gravity_method3"]
        
        # 清空现有数据
        for item in self.method3_table.get_children():
            self.method3_table.delete(item)
        self.method3_data = []
        
        # 恢复表格数据
        if "table_data" in data and data["table_data"]:
            for row_data in data["table_data"]:
                item_id = self.method3_table.insert("", "end", values=("", "", ""))
                
                new_data = {
                    "id": item_id,
                    "o1a": row_data.get("o1a", ""),
                    "t1": row_data.get("t1", ""),
                    "t2": row_data.get("t2", "")
                }
                self.method3_data.append(new_data)
                
                self.method3_table.item(item_id, values=(
                    new_data["o1a"],
                    new_data["t1"], 
                    new_data["t2"]
                ))
        
        # 如果没有数据，添加默认的2行
        if not self.method3_data:
            self.add_method3_table_row()
            self.add_method3_table_row()
        
        # 恢复其他数据
        if "o1" in data:
            self.o1_var.set(data["o1"])
        if "o2" in data:
            self.o2_var.set(data["o2"])
        if "l" in data:
            self.l_var.set(data["l"])
        if "p1" in data:
            self.p1_var.set(data["p1"])
        if "p2" in data:
            self.p2_var.set(data["p2"])
        if "t_avg" in data:
            self.t_avg_var.set(data["t_avg"])
        if "g" in data:
            self.method3_g_var.set(data["g"])
        if "e" in data:
            self.method3_e_var.set(data["e"])
        
        # +++ 新增：如果有交点数据，恢复完整曲线 +++
        if (self.p1_var.get() and self.p2_var.get() and 
            self.t_avg_var.get() and self.method3_g_var.get()):
            self.restore_method3_plot_with_curves()
        else:
            # 只显示散点图
            self.update_method3_plot()

    def restore_method3_plot_with_curves(self):
        """恢复方法三的完整曲线（包括连线和交点）"""
        try:
            # 收集有效数据点
            o1a_data = []
            t1_data = []
            t2_data = []
            
            for data in self.method3_data:
                if data["o1a"] and data["t1"] and data["t2"]:
                    try:
                        o1a = float(data["o1a"])
                        t1 = float(data["t1"])
                        t2 = float(data["t2"])
                        o1a_data.append(o1a)
                        t1_data.append(t1)
                        t2_data.append(t2)
                    except ValueError:
                        continue
            
            if len(o1a_data) < 2:
                return
            
            # 按O1A排序
            sorted_data = sorted(zip(o1a_data, t1_data, t2_data))
            o1a_sorted, t1_sorted, t2_sorted = zip(*sorted_data)
            
            # 绘制图形
            self.method3_ax.clear()
            
            # 绘制T1曲线（蓝色）
            self.method3_ax.plot(o1a_sorted, t1_sorted, 'b-', linewidth=1, label='T1')
            self.method3_ax.scatter(o1a_sorted, t1_sorted, color='blue', s=30, alpha=0.7)
            
            # 绘制T2曲线（红色）
            self.method3_ax.plot(o1a_sorted, t2_sorted, 'r-', linewidth=1, label='T2')
            self.method3_ax.scatter(o1a_sorted, t2_sorted, color='red', s=30, alpha=0.7)
            
            # 寻找交点
            intersections = self.find_intersections(o1a_sorted, t1_sorted, t2_sorted)
            
            if len(intersections) >= 2:
                p1_y = intersections[0][1]  # 第一个交点的纵坐标
                p2_y = intersections[1][1]  # 第二个交点的纵坐标
                
                # 标记交点
                self.method3_ax.scatter([intersections[0][0], intersections[1][0]], 
                                    [p1_y, p2_y], color='green', s=50, marker='x', 
                                    label='交点', zorder=5)
                
                # 显示交点信息
                t_avg = float(self.t_avg_var.get())
                g = float(self.method3_g_var.get())
                error_percent = float(self.method3_e_var.get().replace('%', '')) if self.method3_e_var.get() else 0
                
                info_text = f'P1: {p1_y:.3f}s\nP2: {p2_y:.3f}s\nT_avg: {t_avg:.3f}s\ng: {g:.4f}m/s^2'
                self.method3_ax.text(0.05, 0.95, info_text, transform=self.method3_ax.transAxes,
                                verticalalignment='top', fontsize=7,
                                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            self.method3_ax.set_xlabel('O1A/cm', fontsize=9)
            self.method3_ax.set_ylabel('T/s', fontsize=9)
            self.method3_ax.grid(True, alpha=0.3)
            self.method3_ax.legend(fontsize=8)
            
            self.method3_fig.tight_layout(pad=0.5)
            self.method3_fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.15)
            self.method3_canvas.draw()
            
            print("方法三完整曲线恢复完成")
            
        except Exception as e:
            print(f"恢复方法三曲线时出错: {e}")
            # 回退到只显示散点图
            self.update_method3_plot()

    def save_method3_data(self):
        """保存方法三的数据"""
        try:
            # 收集表格数据
            table_data = []
            for data in self.method3_data:
                table_data.append({
                    "o1a": data.get("o1a", ""),
                    "t1": data.get("t1", ""), 
                    "t2": data.get("t2", "")
                })
            
            # 保存到实验数据
            self.experiment_data["gravity_method3"] = {
                "table_data": table_data,
                "o1": self.o1_var.get() if hasattr(self, 'o1_var') else "",
                "o2": self.o2_var.get() if hasattr(self, 'o2_var') else "",
                "l": self.l_var.get() if hasattr(self, 'l_var') else "",
                "p1": self.p1_var.get() if hasattr(self, 'p1_var') else "",
                "p2": self.p2_var.get() if hasattr(self, 'p2_var') else "",
                "t_avg": self.t_avg_var.get() if hasattr(self, 't_avg_var') else "",
                "g": self.method3_g_var.get() if hasattr(self, 'method3_g_var') else "",
                "e": self.method3_e_var.get() if hasattr(self, 'method3_e_var') else ""
            }
        except Exception as e:
            print(f"保存方法三数据时出错: {e}")

    def create_moment_of_inertia(self):
        """创建测量物体转动惯量的实验内容"""
        # 清空现有内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_label = ttk.Label(self.content_frame, text="测量物体转动惯量", 
                                font=("Arial", 12, "bold"))
        title_label.pack(pady=(10, 20))
        
        # 第一行：转轴到质心距离h0和周期T0
        row1_frame = ttk.Frame(self.content_frame)
        row1_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 转轴到质心距离h0 (cm)
        ttk.Label(row1_frame, text="转轴到质心距离h0 (cm):").pack(side=tk.LEFT, padx=5)
        self.h0_var = tk.StringVar()
        h0_entry = ttk.Entry(row1_frame, textvariable=self.h0_var, width=10)
        h0_entry.pack(side=tk.LEFT, padx=5)
        
        # 摆动周期T0 (s)
        ttk.Label(row1_frame, text="摆动周期T0 (s):").pack(side=tk.LEFT, padx=5)
        self.t0_var = tk.StringVar()
        t0_entry = ttk.Entry(row1_frame, textvariable=self.t0_var, width=10)
        t0_entry.pack(side=tk.LEFT, padx=5)
        
        # 摆杆长L (cm) - 固定值
        ttk.Label(row1_frame, text="摆杆长L (cm):").pack(side=tk.LEFT, padx=5)
        self.l_var = tk.StringVar(value="70.0")
        l_entry = ttk.Entry(row1_frame, textvariable=self.l_var, width=10, state="readonly")
        l_entry.pack(side=tk.LEFT, padx=5)
        
        # 摆杆质量m (g) - 固定值
        ttk.Label(row1_frame, text="摆杆质量m (g):").pack(side=tk.LEFT, padx=5)
        self.m_var = tk.StringVar(value="625.0")
        m_entry = ttk.Entry(row1_frame, textvariable=self.m_var, width=10, state="readonly")
        m_entry.pack(side=tk.LEFT, padx=5)
        
        # 第二行：转动惯量I0计算结果
        row2_frame = ttk.Frame(self.content_frame)
        row2_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 转动惯量I0
        ttk.Label(row2_frame, text="转动惯量I0 (kg·m^2):").pack(side=tk.LEFT, padx=5)
        self.i0_var = tk.StringVar()
        i0_entry = ttk.Entry(row2_frame, textvariable=self.i0_var, width=12, state="readonly")
        i0_entry.pack(side=tk.LEFT, padx=5)
        
        # 转动惯量I0理论值
        ttk.Label(row2_frame, text="I0理论值 (kg·m^2):").pack(side=tk.LEFT, padx=5)
        self.i0_theory_var = tk.StringVar()
        i0_theory_entry = ttk.Entry(row2_frame, textvariable=self.i0_theory_var, width=12, state="readonly")
        i0_theory_entry.pack(side=tk.LEFT, padx=5)
        
        # 误差E
        ttk.Label(row2_frame, text="误差E (%):").pack(side=tk.LEFT, padx=5)
        self.e_i0_var = tk.StringVar()
        e_i0_entry = ttk.Entry(row2_frame, textvariable=self.e_i0_var, width=10, state="readonly")
        e_i0_entry.pack(side=tk.LEFT, padx=5)

        # 计算I0按钮
        calc_i0_button = ttk.Button(row2_frame, text="计算I0", 
                                    command=self.calculate_i0)
        calc_i0_button.pack(side=tk.LEFT, padx=10)

        
        # 第三行：标题
        row3_frame = ttk.Frame(self.content_frame)
        row3_frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(row3_frame, text="在质心固定摆锤后", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        # 第四行：固定摆锤后的参数
        row4_frame = ttk.Frame(self.content_frame)
        row4_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 摆动周期T
        ttk.Label(row4_frame, text="摆动周期T (s):").pack(side=tk.LEFT, padx=5)
        self.t_var = tk.StringVar()
        t_entry = ttk.Entry(row4_frame, textvariable=self.t_var, width=10)
        t_entry.pack(side=tk.LEFT, padx=5)
        
        # 摆锤内径d1 (mm)
        ttk.Label(row4_frame, text="摆锤内径d1 (mm):").pack(side=tk.LEFT, padx=5)
        self.d1_var = tk.StringVar(value="12.0")
        d1_entry = ttk.Entry(row4_frame, textvariable=self.d1_var, width=10, state="readonly")
        d1_entry.pack(side=tk.LEFT, padx=5)
        
        # 摆锤外径d2 (mm)
        ttk.Label(row4_frame, text="摆锤外径d2 (mm):").pack(side=tk.LEFT, padx=5)
        self.d2_var = tk.StringVar(value="34.0")
        d2_entry = ttk.Entry(row4_frame, textvariable=self.d2_var, width=10, state="readonly")
        d2_entry.pack(side=tk.LEFT, padx=5)
        
        # 厚度a (mm)
        ttk.Label(row4_frame, text="厚度a (mm):").pack(side=tk.LEFT, padx=5)
        self.a_var = tk.StringVar(value="20.0")
        a_entry = ttk.Entry(row4_frame, textvariable=self.a_var, width=10, state="readonly")
        a_entry.pack(side=tk.LEFT, padx=5)
        
        # 第五行：转动惯量IA计算结果
        row5_frame = ttk.Frame(self.content_frame)
        row5_frame.pack(fill=tk.X, padx=20, pady=5)

        # 摆锤质量ma (g)
        ttk.Label(row5_frame, text="摆锤质量ma (g):").pack(side=tk.LEFT, padx=5)
        self.ma_var = tk.StringVar(value="125.0")
        ma_entry = ttk.Entry(row5_frame, textvariable=self.ma_var, width=10, state="readonly")
        ma_entry.pack(side=tk.LEFT, padx=5)
        
        # 转动惯量IA
        ttk.Label(row5_frame, text="转动惯量IA (kg·m^2):").pack(side=tk.LEFT, padx=5)
        self.ia_var = tk.StringVar()
        ia_entry = ttk.Entry(row5_frame, textvariable=self.ia_var, width=12, state="readonly")
        ia_entry.pack(side=tk.LEFT, padx=5)
        
        # 转动惯量IA理论值
        ttk.Label(row5_frame, text="IA理论值 (kg·m^2):").pack(side=tk.LEFT, padx=5)
        self.ia_theory_var = tk.StringVar()
        ia_theory_entry = ttk.Entry(row5_frame, textvariable=self.ia_theory_var, width=12, state="readonly")
        ia_theory_entry.pack(side=tk.LEFT, padx=5)
        
        # 误差E
        ttk.Label(row5_frame, text="误差E (%):").pack(side=tk.LEFT, padx=5)
        self.e_ia_var = tk.StringVar()
        e_ia_entry = ttk.Entry(row5_frame, textvariable=self.e_ia_var, width=10, state="readonly")
        e_ia_entry.pack(side=tk.LEFT, padx=5)
        
        # 第五行：转动惯量IA计算结果
        row6_frame = ttk.Frame(self.content_frame)
        row6_frame.pack(fill=tk.X, padx=20, pady=5)

        # 计算IA按钮
        calc_ia_button = ttk.Button(row6_frame, text="计算IA", 
                                    command=self.calculate_ia)
        calc_ia_button.pack(side=tk.LEFT, padx=10)
        
        # +++ 新增：导出全部数据按钮 +++
        export_all_button = ttk.Button(row6_frame, text="导出数据", 
                                    command=self.export_inertia_all_data)
        export_all_button.pack(side=tk.LEFT, padx=5)

         # +++ 新增：导入数据按钮 +++
        import_all_button = ttk.Button(row6_frame, text="导入数据", 
                                    command=self.import_inertia_all_data)
        import_all_button.pack(side=tk.LEFT, padx=5)

        # 初始化数据存储
        if not hasattr(self, 'inertia_data'):
            self.inertia_data = {}

    # 添加转动惯量的导入数据功能
    def import_inertia_all_data(self):
        """导入全部转动惯量数据"""
        try:
            import pandas as pd
            from tkinter import filedialog
            import threading
            
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            self.show_import_progress("正在导入转动惯量数据...")
            
            def import_thread():
                try:
                    # 读取Excel文件
                    df = pd.read_excel(file_path)
                    
                    # 在主线程中更新UI
                    self.root.after(0, self.update_inertia_data, df)
                    
                    self.root.after(0, self.hide_import_progress)
                    self.root.after(0, lambda: tk.messagebox.showinfo("成功", "数据导入完成"))
                    
                except Exception as e:
                    self.root.after(0, self.hide_import_progress)
                    self.root.after(0, lambda: tk.messagebox.showerror("错误", f"导入失败: {str(e)}"))
            
            thread = threading.Thread(target=import_thread, daemon=True)
            thread.start()
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas库: pip install pandas")
        except Exception as e:
            self.hide_import_progress()
            tk.messagebox.showerror("错误", f"导入失败: {str(e)}")

    def update_inertia_data(self, df):
        """更新转动惯量数据"""
        try:
            # 检查数据格式
            if '参数' not in df.columns or '数值' not in df.columns:
                tk.messagebox.showerror("错误", "Excel文件格式不正确，需要包含'参数'和'数值'列")
                return
            
            # 更新各个字段
            for _, row in df.iterrows():
                param = row['参数']
                value = row['数值']
                
                if pd.notna(param) and pd.notna(value):
                    param_str = str(param).strip()
                    value_str = str(value)
                    
                    if "转轴到质心距离h0" in param_str:
                        self.h0_var.set(value_str)
                    elif "摆动周期T0" in param_str:
                        self.t0_var.set(value_str)
                    elif "摆杆长L" in param_str:
                        self.l_var.set(value_str)
                    elif "摆杆质量m" in param_str:
                        self.m_var.set(value_str)
                    elif "转动惯量I0" in param_str and "理论" not in param_str:
                        self.i0_var.set(value_str)
                    elif "I0理论值" in param_str:
                        self.i0_theory_var.set(value_str)
                    elif "I0误差E" in param_str:
                        self.e_i0_var.set(value_str)
                    elif "摆动周期T" in param_str and "T0" not in param_str:
                        self.t_var.set(value_str)
                    elif "摆锤内径d1" in param_str:
                        self.d1_var.set(value_str)
                    elif "摆锤外径d2" in param_str:
                        self.d2_var.set(value_str)
                    elif "厚度a" in param_str:
                        self.a_var.set(value_str)
                    elif "摆锤质量ma" in param_str:
                        self.ma_var.set(value_str)
                    elif "转动惯量IA" in param_str and "理论" not in param_str:
                        self.ia_var.set(value_str)
                    elif "IA理论值" in param_str:
                        self.ia_theory_var.set(value_str)
                    elif "IA误差E" in param_str:
                        self.e_ia_var.set(value_str)
            
            print("转动惯量数据导入完成")
            
        except Exception as e:
            tk.messagebox.showerror("错误", f"更新数据时发生错误: {str(e)}")

    def export_inertia_all_data(self):
        """导出全部转动惯量数据到Excel - 多线程版本"""
        try:
            import pandas as pd
            from tkinter import filedialog
            import threading
            
            # 收集所有转动惯量数据
            data = {
                "参数": [
                    "转轴到质心距离h0 (cm)", "摆动周期T0 (s)", "摆杆长L (cm)", "摆杆质量m (g)",
                    "转动惯量I0 (kg·m^2)", "I0理论值 (kg·m^2)", "I0误差E (%)",
                    "摆动周期T (s)", "摆锤内径d1 (mm)", "摆锤外径d2 (mm)", "厚度a (mm)", "摆锤质量ma (g)",
                    "转动惯量IA (kg·m^2)", "IA理论值 (kg·m^2)", "IA误差E (%)"
                ],
                "数值": [
                    self.h0_var.get() if self.h0_var.get() else "",
                    self.t0_var.get() if self.t0_var.get() else "",
                    self.l_var.get() if self.l_var.get() else "",
                    self.m_var.get() if self.m_var.get() else "",
                    self.i0_var.get() if self.i0_var.get() else "",
                    self.i0_theory_var.get() if self.i0_theory_var.get() else "",
                    self.e_i0_var.get() if self.e_i0_var.get() else "",
                    self.t_var.get() if self.t_var.get() else "",
                    self.d1_var.get() if self.d1_var.get() else "",
                    self.d2_var.get() if self.d2_var.get() else "",
                    self.a_var.get() if self.a_var.get() else "",
                    self.ma_var.get() if self.ma_var.get() else "",
                    self.ia_var.get() if self.ia_var.get() else "",
                    self.ia_theory_var.get() if self.ia_theory_var.get() else "",
                    self.e_ia_var.get() if self.e_ia_var.get() else ""
                ]
            }
            
            # 检查是否有数据可导出
            if not any(data["数值"]):
                tk.messagebox.showwarning("警告", "没有可导出的数据")
                return
            
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            self.show_export_progress("正在导出转动惯量数据...")
            
            def export_thread():
                try:
                    df = pd.DataFrame(data)
                    df.to_excel(file_path, index=False)
                    
                    self.root.after(0, lambda: self.hide_export_progress())
                    self.root.after(0, lambda: tk.messagebox.showinfo("成功", f"转动惯量数据已导出到: {file_path}"))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.hide_export_progress())
                    self.root.after(0, lambda: tk.messagebox.showerror("错误", f"导出失败: {str(e)}"))
            
            thread = threading.Thread(target=export_thread, daemon=True)
            thread.start()
        
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas库: pip install pandas")
        except Exception as e:
            self.hide_export_progress()
            tk.messagebox.showerror("错误", f"导出失败: {str(e)}")

    def calculate_i0(self):
        """计算转动惯量I0"""
        try:
            # 验证输入数据
            if not all([self.h0_var.get(), self.t0_var.get()]):
                tk.messagebox.showerror("错误", "请输入h0和T0的值")
                return
            
            h0_cm = float(self.h0_var.get())  # 单位：cm
            t0 = float(self.t0_var.get())
            l_cm = float(self.l_var.get())    # 单位：cm
            m_g = float(self.m_var.get())     # 单位：g
            
            # 转换为标准单位
            h0 = h0_cm / 100.0  # m
            l = l_cm / 100.0    # m
            m = m_g / 1000.0    # kg
            
            # 计算公式: I0 = m * g * h0 * T0^2 / (4 * π^2)
            pi_squared = 3.1415 * 3.1415
            i0 = m * 9.8 * h0 * t0 * t0 / (4 * pi_squared)
            
            # 计算理论值: I0理论值 = 1/12 * m * L^2 + m * h0^2
            i0_theory = (1/12) * m * l * l + m * h0 * h0
            
            # 计算百分误差
            if i0_theory > 0:
                error_percent = abs((i0 - i0_theory) / i0_theory) * 100
            else:
                error_percent = 0
            
            # 更新显示
            self.i0_var.set(f"{i0:.6f}")
            self.i0_theory_var.set(f"{i0_theory:.6f}")
            self.e_i0_var.set(f"{error_percent:.2f}%")
            
            # 保存计算结果
            self.inertia_data['i0'] = i0
            self.inertia_data['i0_theory'] = i0_theory
            self.inertia_data['h0'] = h0
            self.inertia_data['t0'] = t0
            
            # 自动保存到实验数据
            self.save_current_experiment_data()
        
        
        except ValueError:
            tk.messagebox.showerror("错误", "请输入有效的数值")
        except Exception as e:
            tk.messagebox.showerror("错误", f"计算过程中发生错误: {str(e)}")

    def calculate_ia(self):
        """计算转动惯量IA"""
        try:
            # 验证输入数据
            if not all([self.t_var.get()]):
                tk.messagebox.showerror("错误", "请输入T的值")
                return
            
            if 'i0' not in self.inertia_data:
                tk.messagebox.showerror("错误", "请先计算I0")
                return
            
            t = float(self.t_var.get())
            d1_mm = float(self.d1_var.get())  # 单位：mm
            d2_mm = float(self.d2_var.get())  # 单位：mm
            a_mm = float(self.a_var.get())    # 单位：mm
            ma_g = float(self.ma_var.get())   # 单位：g
            
            # 获取之前计算的I0和h0
            i0 = self.inertia_data['i0']
            h0 = self.inertia_data['h0']
            m = float(self.m_var.get()) / 1000.0  # kg
            ma = ma_g / 1000.0  # kg
            
            # 转换为标准单位
            d1 = d1_mm / 1000.0  # m
            d2 = d2_mm / 1000.0  # m
            a = a_mm / 1000.0    # m
            
            # 计算公式: IA = (m + ma) * g * h0 * T^2 / (4 * π^2) - I0
            pi_squared = 3.1415 * 3.1415
            ia = (m + ma) * 9.8 * h0 * t * t / (4 * pi_squared) - i0
            
            # 计算理论值: IA理论值 = ma * ((d1^2 + d2^2)/16 + a^2/12) + ma * h0^2
            ia_theory = ma * ((d1*d1 + d2*d2) / 16 + a*a / 12) + ma * h0 * h0
            
            # 计算百分误差
            if ia_theory > 0:
                error_percent = abs((ia - ia_theory) / ia_theory) * 100
            else:
                error_percent = 0
            
            # 更新显示
            self.ia_var.set(f"{ia:.6f}")
            self.ia_theory_var.set(f"{ia_theory:.6f}")
            self.e_ia_var.set(f"{error_percent:.2f}%")
            
            # 保存计算结果
            self.inertia_data['ia'] = ia
            self.inertia_data['ia_theory'] = ia_theory
            self.inertia_data['t'] = t
            
            # 自动保存到实验数据
            self.save_current_experiment_data()
        

        except ValueError:
            tk.messagebox.showerror("错误", "请输入有效的数值")
        except Exception as e:
            tk.messagebox.showerror("错误", f"计算过程中发生错误: {str(e)}")

    
    # 在 create_parallel_axis_verification 方法中替换原有内容
    def create_parallel_axis_verification(self):
        """创建验证平行轴定理的实验内容"""
        # 清空现有内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_label = ttk.Label(self.content_frame, text="验证平行轴定理", 
                                font=("Arial", 12, "bold"))
        title_label.pack(pady=(10, 5))
        
        # 主内容框架 - 左右布局
        main_content_frame = ttk.Frame(self.content_frame)
        main_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：数据表格
        left_frame = ttk.Frame(main_content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 表格标题
        table_title = ttk.Label(left_frame, text="数据记录表", font=("Arial", 10, "bold"))
        table_title.pack(pady=(0, 3))
        
        # 创建表格框架
        table_frame = ttk.Frame(left_frame, height=180)
        table_frame.pack(fill=tk.BOTH, expand=False)
        table_frame.pack_propagate(False)
        
        # 创建Treeview表格
        columns = ("d_cm", "d_m", "T", "d2", "T2")
        self.parallel_table = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            height=6
        )
        
        # 设置列标题
        self.parallel_table.heading("d_cm", text="d/cm")
        self.parallel_table.heading("d_m", text="d/m")
        self.parallel_table.heading("T", text="T/s")
        self.parallel_table.heading("d2", text="d^2/m^2")
        self.parallel_table.heading("T2", text="T^2/s^2")
        
        # 设置列宽
        self.parallel_table.column("d_cm", width=40)
        self.parallel_table.column("d_m", width=40)
        self.parallel_table.column("T", width=40)
        self.parallel_table.column("d2", width=60)
        self.parallel_table.column("T2", width=60)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.parallel_table.yview)
        self.parallel_table.configure(yscrollcommand=scrollbar.set)
        
        # 布局表格和滚动条
        self.parallel_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定表格事件
        self.parallel_table.bind('<Double-1>', self.on_parallel_table_double_click)
        self.parallel_table.bind('<<TreeviewSelect>>', self.on_parallel_table_select)
        
        # 创建编辑条目
        self.parallel_entry = ttk.Entry(table_frame, width=10)
        self.parallel_entry.pack_forget()  # 初始隐藏
        
        # 绑定编辑条目的相关事件
        self.parallel_entry.bind('<Return>', self.save_parallel_cell_edit)
        self.parallel_entry.bind('<FocusOut>', self.save_parallel_cell_edit)
        self.parallel_entry.bind('<Escape>', self.cancel_parallel_cell_edit)
        
        # 初始化数据存储
        self.parallel_data = []
        
        # 添加初始2行
        self.add_parallel_table_row()
        self.add_parallel_table_row()
        
        # 右侧：曲线图
        right_frame = ttk.Frame(main_content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 曲线图标题
        plot_title = ttk.Label(right_frame, text="d^2-T^2关系曲线", font=("Arial", 10, "bold"))
        plot_title.pack(pady=(0, 3))
        
        # 创建matplotlib图形
        self.parallel_fig = plt.figure(figsize=(2.6, 2))
        self.parallel_ax = self.parallel_fig.add_subplot(111)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        self.parallel_ax.set_xlabel('d^2/m^2', fontsize=8)
        self.parallel_ax.set_ylabel('T^2/s^2', fontsize=8)
        self.parallel_ax.grid(True, alpha=0.3)
        
        # 调整图形布局
        self.parallel_fig.tight_layout(pad=0.5)
        
        # 将matplotlib图形嵌入到tkinter
        self.parallel_canvas = FigureCanvasTkAgg(self.parallel_fig, right_frame)
        self.parallel_canvas.draw()
        self.parallel_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 底部：输入框和结果显示区域
        bottom_frame = ttk.Frame(self.content_frame)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 第一行：参数输入
        row1_frame = ttk.Frame(bottom_frame)
        row1_frame.pack(fill=tk.X, pady=(5, 5))
        
        # 转轴到质心距离h0
        ttk.Label(row1_frame, text="转轴到质心距离h0 (cm):").pack(side=tk.LEFT, padx=5)
        self.h0_parallel_var = tk.StringVar()
        h0_entry = ttk.Entry(row1_frame, textvariable=self.h0_parallel_var, width=12)
        h0_entry.pack(side=tk.LEFT, padx=5)
        
        # 斜率k理论值
        ttk.Label(row1_frame, text="斜率k理论值(s^2/m^2):").pack(side=tk.LEFT, padx=5)
        self.k_theory_var = tk.StringVar()
        k_entry = ttk.Entry(row1_frame, textvariable=self.k_theory_var, width=12, state="readonly")
        k_entry.pack(side=tk.LEFT, padx=5)
        
        # 截距b理论值
        ttk.Label(row1_frame, text="截距b理论值(s^2):").pack(side=tk.LEFT, padx=5)
        self.b_theory_var = tk.StringVar()
        b_entry = ttk.Entry(row1_frame, textvariable=self.b_theory_var, width=12, state="readonly")
        b_entry.pack(side=tk.LEFT, padx=5)
        
         # +++ 新增：斜率k计算值和截距b计算值 +++
        # 第二行：计算结果
        row1_2_frame = ttk.Frame(bottom_frame)
        row1_2_frame.pack(fill=tk.X, pady=(5, 5))
        
            # 斜率k计算值
        ttk.Label(row1_2_frame, text="斜率k计算值(s^2/m^2):").pack(side=tk.LEFT, padx=5)
        self.k_calc_var = tk.StringVar()
        k_calc_entry = ttk.Entry(row1_2_frame, textvariable=self.k_calc_var, width=12, state="readonly")
        k_calc_entry.pack(side=tk.LEFT, padx=5)
        
        # 截距b计算值
        ttk.Label(row1_2_frame, text="截距b计算值(s^2):").pack(side=tk.LEFT, padx=5)
        self.b_calc_var = tk.StringVar()
        b_calc_entry = ttk.Entry(row1_2_frame, textvariable=self.b_calc_var, width=12, state="readonly")
        b_calc_entry.pack(side=tk.LEFT, padx=5)

        # 第二行：按钮
        row2_frame = ttk.Frame(bottom_frame)
        row2_frame.pack(fill=tk.X, pady=(5, 5))
        
        # 按钮配置
        button_config = {'side': tk.LEFT, 'padx': 3, 'pady': 2}
        
        # 计算按钮
        calc_button = ttk.Button(row2_frame, text="计算", 
                                command=self.calculate_parallel_axis)
        calc_button.pack(**button_config)
        
        # 删除选中行按钮
        delete_button = ttk.Button(row2_frame, text="删除选中行", 
                                command=self.delete_selected_parallel_row)
        delete_button.pack(**button_config)
        
        # 清空数据按钮
        clear_button = ttk.Button(row2_frame, text="清空数据", 
                                command=self.clear_parallel_data)
        clear_button.pack(**button_config)
        
        # 导出数据按钮
        export_button = ttk.Button(row2_frame, text="导出数据", 
                                command=self.export_parallel_data)
        export_button.pack(**button_config)
        
        # 导入数据按钮
        import_button = ttk.Button(row2_frame, text="导入数据", 
                                command=self.import_parallel_data)
        import_button.pack(**button_config)
        
        
        
        # 初始化选中行
        self.selected_parallel_row = None
        
        # 恢复保存的数据
        self.restore_parallel_data()

    def add_parallel_table_row(self):
        """添加新行到平行轴定理表格"""
        item_id = self.parallel_table.insert("", "end", values=("", "", "", "", ""))
        self.parallel_data.append({
            "id": item_id, 
            "d_cm": "", 
            "d_m": "", 
            "T": "", 
            "d2": "", 
            "T2": ""
        })

    def on_parallel_table_double_click(self, event):
        """处理表格双击事件"""
        item = self.parallel_table.selection()[0] if self.parallel_table.selection() else None
        if item:
            column = self.parallel_table.identify_column(event.x)
            col_index = int(column.replace('#', '')) - 1
            # 只允许编辑第一列和第三列（d_cm和T）
            if col_index in [0, 2]:
                self.start_parallel_cell_edit(item, col_index)

    def start_parallel_cell_edit(self, item, col_index):
        """开始编辑单元格"""
        bbox = self.parallel_table.bbox(item, column=f'#{col_index+1}')
        if not bbox:
            return
        
        current_values = self.parallel_table.item(item, 'values')
        current_value = current_values[col_index]
        
        self.parallel_entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        self.parallel_entry.delete(0, tk.END)
        self.parallel_entry.insert(0, current_value)
        self.parallel_entry.select_range(0, tk.END)
        self.parallel_entry.focus()
        
        self.parallel_editing_item = item
        self.parallel_editing_column = col_index

    def save_parallel_cell_edit(self, event=None):
        """保存单元格编辑"""
        if not hasattr(self, 'parallel_editing_item') or not self.parallel_editing_item:
            return
        
        new_value = self.parallel_entry.get().strip()
        item = self.parallel_editing_item
        col_index = self.parallel_editing_column
        
        # 验证输入
        try:
            if new_value and float(new_value) <= 0:
                self.cancel_parallel_cell_edit()
                return
        except ValueError:
            if new_value:
                self.cancel_parallel_cell_edit()
                return
        
        # 更新表格
        current_values = list(self.parallel_table.item(item, 'values'))
        current_values[col_index] = new_value
        self.parallel_table.item(item, values=current_values)
        
        # 更新数据存储
        self.update_parallel_data(item, col_index, new_value)
        
        # 自动计算其他列
        if new_value and col_index in [0, 2]:
            self.calculate_parallel_columns(item)
        
        # 隐藏编辑条目
        self.parallel_entry.place_forget()
        self.parallel_editing_item = None
        self.parallel_editing_column = None

    def cancel_parallel_cell_edit(self, event=None):
        """取消单元格编辑"""
        self.parallel_entry.place_forget()
        self.parallel_editing_item = None
        self.parallel_editing_column = None

    def on_parallel_table_select(self, event):
        """处理表格选择事件"""
        selection = self.parallel_table.selection()
        self.selected_parallel_row = selection[0] if selection else None

    def update_parallel_data(self, item_id, col_index, value):
        """更新数据存储"""
        for data in self.parallel_data:
            if data["id"] == item_id:
                if col_index == 0:  # d_cm列
                    data["d_cm"] = value
                elif col_index == 2:  # T列
                    data["T"] = value
                break

    def calculate_parallel_columns(self, item_id):
        """计算自动列的值"""
        for data in self.parallel_data:
            if data["id"] == item_id:
                try:
                    # 计算d_m (d_cm转换为米)
                    if data["d_cm"]:
                        d_cm = float(data["d_cm"])
                        d_m = d_cm / 100.0
                        data["d_m"] = f"{d_m:.3f}"
                    else:
                        data["d_m"] = ""
                    
                    # 计算d^2
                    if data["d_m"]:
                        d_m = float(data["d_m"])
                        d2 = d_m ** 2
                        data["d2"] = f"{d2:.4f}"
                    else:
                        data["d2"] = ""
                    
                    # 计算T^2
                    if data["T"]:
                        T = float(data["T"])
                        T2 = T ** 2
                        data["T2"] = f"{T2:.3f}"
                    else:
                        data["T2"] = ""
                    
                    # 更新表格显示
                    current_values = list(self.parallel_table.item(item_id, 'values'))
                    current_values[1] = data["d_m"]
                    current_values[3] = data["d2"]
                    current_values[4] = data["T2"]
                    self.parallel_table.item(item_id, values=current_values)
                    
                except ValueError:
                    data["d_m"] = ""
                    data["d2"] = ""
                    data["T2"] = ""
                    current_values = list(self.parallel_table.item(item_id, 'values'))
                    current_values[1] = ""
                    current_values[3] = ""
                    current_values[4] = ""
                    self.parallel_table.item(item_id, values=current_values)
                
                break
        
        # 更新曲线图
        self.update_parallel_plot()
        
        # 检查是否需要添加新行
        self.check_add_parallel_row()

    def check_add_parallel_row(self):
        """检查是否需要添加新行"""
        last_item = self.parallel_table.get_children()[-1]
        last_values = self.parallel_table.item(last_item, 'values')
        
        if last_values[0] or last_values[2]:  # d_cm或T有数据
            self.add_parallel_table_row()

    def update_parallel_plot(self):
        """更新曲线图 - 只显示散点"""
        # 收集有效数据点
        d2_data = []
        T2_data = []
        
        for data in self.parallel_data:
            if data["d2"] and data["T2"]:
                try:
                    d2 = float(data["d2"])
                    T2 = float(data["T2"])
                    d2_data.append(d2)
                    T2_data.append(T2)
                except ValueError:
                    continue
        
        # 绘制图形
        self.parallel_ax.clear()
        
        if d2_data and T2_data:
            self.parallel_ax.scatter(d2_data, T2_data, color='blue', s=30, alpha=0.7, label='数据点')
        
        self.parallel_ax.set_xlabel('d^2/m^2', fontsize=9)
        self.parallel_ax.set_ylabel('T^2/s^2', fontsize=9)
        self.parallel_ax.grid(True, alpha=0.3)
        if d2_data:
            self.parallel_ax.legend(fontsize=8)
        
        self.parallel_fig.tight_layout(pad=0.5)
        self.parallel_fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.25)
        self.parallel_canvas.draw()

    def delete_selected_parallel_row(self):
        """删除选中行"""
        if self.selected_parallel_row:
            if tk.messagebox.askyesno("确认", "确定要删除选中的行吗？"):
                self.parallel_data = [data for data in self.parallel_data if data["id"] != self.selected_parallel_row]
                self.parallel_table.delete(self.selected_parallel_row)
                self.selected_parallel_row = None
                self.update_parallel_plot()

    def clear_parallel_data(self):
        """清空所有数据"""
        if tk.messagebox.askyesno("确认", "确定要清空所有数据吗？"):
            for item in self.parallel_table.get_children():
                self.parallel_table.delete(item)
            
            self.parallel_data = []
            self.add_parallel_table_row()
            self.add_parallel_table_row()
            
            self.parallel_ax.clear()
            self.parallel_ax.set_xlabel('d^2/m^2')
            self.parallel_ax.set_ylabel('T^2/s^2')
            self.parallel_ax.grid(True, alpha=0.3)
            self.parallel_canvas.draw()
            
            # 清空结果显示
            self.k_theory_var.set("")
            self.b_theory_var.set("")
            self.k_calc_var.set("")    # 新增：清空斜率计算值
            self.b_calc_var.set("")    # 新增：清空截距计算值

    def export_parallel_data(self):
        """导出平行轴定理数据到Excel - 多线程版本"""
        try:
            import pandas as pd
            from tkinter import filedialog
            import threading
            
            # 预先收集数据
            export_data = []
            for data in self.parallel_data:
                if data["d_cm"] or data["T"]:
                    export_data.append({
                        "d_cm": data["d_cm"] if data["d_cm"] else "",
                        "d_m": data["d_m"] if data["d_m"] else "",
                        "T_s": data["T"] if data["T"] else "",
                        "d2_m2": data["d2"] if data["d2"] else "",
                        "T2_s2": data["T2"] if data["T2"] else ""
                    })
            
            if not export_data:
                tk.messagebox.showwarning("警告", "没有可导出的数据")
                return
            
            # 收集计算结果数据
            result_data = {
                "参数": [
                    "转轴到质心距离h0 (cm)",
                    "斜率k理论值(s^2/m^2)", 
                    "截距b理论值(s^2)",
                    "斜率k计算值(s^2/m^2)",  # 新增
                    "截距b计算值(s^2)"      # 新增
                ],
                "数值": [
                    self.h0_parallel_var.get() if self.h0_parallel_var.get() else "",
                    self.k_theory_var.get() if self.k_theory_var.get() else "",
                    self.b_theory_var.get() if self.b_theory_var.get() else "",
                    self.k_calc_var.get() if self.k_calc_var.get() else "",  # 新增
                    self.b_calc_var.get() if self.b_calc_var.get() else ""   # 新增
                ]
            }
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            self.show_export_progress("正在导出平行轴定理数据...")
            
            def export_thread():
                try:
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        # 第一页：表格数据
                        if export_data:
                            df_table = pd.DataFrame(export_data)
                            df_table.to_excel(writer, sheet_name='数据记录表', index=False)
                        
                        # 第二页：计算结果
                        df_result = pd.DataFrame(result_data)
                        df_result.to_excel(writer, sheet_name='计算结果', index=False)
                    
                    self.root.after(0, lambda: self.hide_export_progress())
                    self.root.after(0, lambda: tk.messagebox.showinfo("成功", f"数据已导出到: {file_path}"))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.hide_export_progress())
                    self.root.after(0, lambda: tk.messagebox.showerror("错误", f"导出失败: {str(e)}"))
            
            thread = threading.Thread(target=export_thread, daemon=True)
            thread.start()
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas库: pip install pandas")
        except Exception as e:
            self.hide_export_progress()
            tk.messagebox.showerror("错误", f"导出失败: {str(e)}")

    def import_parallel_data(self):
        """从Excel导入平行轴定理数据 - 修复卡顿版本"""
        try:
            import pandas as pd
            from tkinter import filedialog
            import threading
            
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            self.show_import_progress("正在导入平行轴定理数据...")
            
            def import_thread():
                try:
                    # 读取数据记录表
                    df_table = pd.read_excel(file_path, sheet_name='数据记录表')
                    self.root.after(0, self.update_parallel_table, df_table)
                    
                    # 读取计算结果
                    try:
                        df_result = pd.read_excel(file_path, sheet_name='计算结果')
                        self.root.after(0, self.update_parallel_results, df_result)
                    except Exception as e:
                        print(f"读取计算结果失败: {e}")
                    
                    self.root.after(0, self.hide_import_progress)
                    self.root.after(0, lambda: tk.messagebox.showinfo("成功", "数据导入完成"))
                    
                except Exception as e:
                    self.root.after(0, self.hide_import_progress)
                    self.root.after(0, lambda: tk.messagebox.showerror("错误", f"导入失败: {str(e)}"))
            
            thread = threading.Thread(target=import_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            self.hide_import_progress()
            tk.messagebox.showerror("错误", f"导入失败: {str(e)}")

    def update_parallel_table(self, df_table):
        """更新平行轴定理表格数据"""
        try:
            # 清空现有数据
            for item in self.parallel_table.get_children():
                self.parallel_table.delete(item)
            self.parallel_data = []
            
            print(f"导入平行轴定理数据，行数: {len(df_table)}")
            print(f"列名: {df_table.columns.tolist()}")
            
            # 导入表格数据
            for index, row in df_table.iterrows():
                # 添加新行
                self.add_parallel_table_row()
                item_id = self.parallel_data[index]["id"]
                
                # 尝试不同的列名可能性
                d_cm_value = ""
                T_value = ""
                
                # 检查可能的列名
                if 'd_cm' in df_table.columns and pd.notna(row['d_cm']):
                    d_cm_value = str(row['d_cm'])
                elif 'd/cm' in df_table.columns and pd.notna(row['d/cm']):
                    d_cm_value = str(row['d/cm'])
                elif 'd' in df_table.columns and pd.notna(row['d']):
                    d_cm_value = str(row['d'])
                
                if 'T_s' in df_table.columns and pd.notna(row['T_s']):
                    T_value = str(row['T_s'])
                elif 'T/s' in df_table.columns and pd.notna(row['T/s']):
                    T_value = str(row['T/s'])
                elif 'T' in df_table.columns and pd.notna(row['T']):
                    T_value = str(row['T'])
                
                print(f"第{index+1}行数据: d_cm={d_cm_value}, T={T_value}")
                
                # 更新表格
                self.parallel_table.item(item_id, values=(d_cm_value, "", T_value, "", ""))
                
                # 更新数据存储并计算其他列
                self.update_parallel_data(item_id, 0, d_cm_value)
                self.update_parallel_data(item_id, 2, T_value)
                if d_cm_value or T_value:
                    self.calculate_parallel_columns(item_id)
            
            # 更新曲线图
            self.update_parallel_plot()
            
        except Exception as e:
            print(f"更新平行轴定理表格时出错: {e}")
            import traceback
            traceback.print_exc()

    def update_parallel_results(self, df_result):
        """更新平行轴定理计算结果"""
        try:
            print(f"导入平行轴定理结果，行数: {len(df_result)}")
            print(f"列名: {df_result.columns.tolist()}")
            
            if not df_result.empty and '参数' in df_result.columns and '数值' in df_result.columns:
                for _, row in df_result.iterrows():
                    param = row['参数']
                    value = row['数值']
                    
                    if pd.notna(param) and pd.notna(value):
                        param_str = str(param).strip()
                        value_str = str(value)
                        
                        print(f"处理参数: {param_str} = {value_str}")
                        
                        if "转轴到质心距离" in param_str or "h0" in param_str:
                            self.h0_parallel_var.set(value_str)
                        elif "斜率k理论值" in param_str or "k理论值" in param_str:
                            self.k_theory_var.set(value_str)
                        elif "截距b理论值" in param_str or "b理论值" in param_str:
                            self.b_theory_var.set(value_str)
                        elif "斜率k计算值" in param_str:  # 新增
                            self.k_calc_var.set(value_str)
                        elif "截距b计算值" in param_str:  # 新增
                            self.b_calc_var.set(value_str)
            
            print("平行轴定理结果导入完成")
            
        except Exception as e:
            print(f"更新平行轴定理结果时出错: {e}")
            import traceback
            traceback.print_exc()

    def calculate_parallel_axis(self):
        """计算平行轴定理验证"""
        try:
            # 验证输入数据
            if not self.h0_parallel_var.get():
                tk.messagebox.showerror("错误", "请输入转轴到质心距离h0的值")
                return
            
            # 收集有效数据点
            d2_data = []
            T2_data = []
            
            for data in self.parallel_data:
                if data["d2"] and data["T2"]:
                    try:
                        d2 = float(data["d2"])
                        T2 = float(data["T2"])
                        d2_data.append(d2)
                        T2_data.append(T2)
                    except ValueError:
                        continue
            
            if len(d2_data) < 2:
                tk.messagebox.showerror("错误", "至少需要2个有效数据点进行计算")
                return
            
            # 线性拟合
            import numpy as np
            slope, intercept = np.polyfit(d2_data, T2_data, 1)
            
            # 获取物理参数
            h0_cm = float(self.h0_parallel_var.get())
            h0 = h0_cm / 100.0  # 转换为米
            
            # 获取系统参数
            rod_mass = self.pendulum.mass  # 杆质量
            hammer_mass = self.pendulum.hammer_mass  # 单个摆锤质量
            total_mass = rod_mass + 2 * hammer_mass  # 总质量（假设两个摆锤都放置）
            
            # 计算摆锤绕质心的转动惯量（空心圆柱体绕中心轴）
            single_hammer_inertia = hammer_mass*(h0**2)
            
            # 计算两个摆锤的总转动惯量
            two_hammers_inertia = 2 * single_hammer_inertia
            
            # 获取复摆绕转轴的转动惯量（杆的转动惯量）
            pendulum_inertia = 1/12*rod_mass*(self.pendulum.length**2) + rod_mass*(h0**2)
            
            # 计算整个系统的总转动惯量
            total_inertia = two_hammers_inertia + pendulum_inertia
            
            # 计算理论值
            # k理论值 = 8 * π^2 * 单个摆锤质量 / (总质量) / g / h0
            k_theory = 8 * (3.1415 ** 2) * hammer_mass / (total_mass * 9.8 * h0)
            
            # b理论值 = 4 * π^2 * (2*(摆锤绕质心的转动惯量 + 摆锤质量*h0^2) + 复摆绕转轴的转动惯量) / (总质量) / g / h0
            b_theory = 4 * (3.1415 ** 2) * total_inertia / (total_mass * 9.8 * h0)
            
             # +++ 新增：更新计算值 +++
            # 斜率k计算值 = 拟合曲线的斜率
            k_calc = slope
            
            # 截距b计算值 = 拟合曲线的截距
            b_calc = intercept

            # 更新显示
            self.k_theory_var.set(f"{k_theory:.6f}")
            self.b_theory_var.set(f"{b_theory:.6f}")
            self.k_calc_var.set(f"{k_calc:.6f}")
            self.b_calc_var.set(f"{b_calc:.6f}")
            
            # 更新曲线图，显示拟合直线和公式
            self.parallel_ax.clear()
            
            # 绘制散点
            self.parallel_ax.scatter(d2_data, T2_data, color='blue', s=30, alpha=0.7, label='数据点')
            
            # 绘制拟合直线
            d2_fit = np.linspace(min(d2_data), max(d2_data), 100)
            T2_fit = slope * d2_fit + intercept
            self.parallel_ax.plot(d2_fit, T2_fit, 'r-', linewidth=1, label=f'T^2={slope:.4f}d^2+{intercept:.4f}')
            
            # 显示公式和理论值
            equation_text = f'T^2 = {slope:.4f}d^2 + {intercept:.4f}'
            
            self.parallel_ax.text(0.05, 0.95, equation_text, transform=self.parallel_ax.transAxes,
                            verticalalignment='top', fontsize=7,  # 减小字体以适应更多内容
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            self.parallel_ax.set_xlabel('d^2/m^2', fontsize=9)
            self.parallel_ax.set_ylabel('T^2/s^2', fontsize=9)
            self.parallel_ax.grid(True, alpha=0.3)
            self.parallel_ax.legend(fontsize=8)
            
            self.parallel_fig.tight_layout(pad=0.5)
            self.parallel_canvas.draw()
            
            # 保存数据和计算结果
            self.save_current_experiment_data()
            
            print(f"平行轴定理验证计算完成:")
            # print(f"  摆锤绕质心转动惯量: {hammer_inertia_cm:.6f} kg·m^2")
            print(f"  单个摆锤绕转轴转动惯量: {single_hammer_inertia:.6f} kg·m^2")
            print(f"  两个摆锤总转动惯量: {two_hammers_inertia:.6f} kg·m^2")
            print(f"  复摆转动惯量: {pendulum_inertia:.6f} kg·m^2")
            print(f"  系统总转动惯量: {total_inertia:.6f} kg·m^2")
            print(f"  实验斜率: {slope:.6f}")
            print(f"  实验截距: {intercept:.6f}")
            print(f"  理论斜率: {k_theory:.6f}")
            print(f"  理论截距: {b_theory:.6f}")
        
        except Exception as e:
            tk.messagebox.showerror("错误", f"计算过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

    def restore_parallel_data(self):
        """恢复平行轴定理的数据"""
        if "parallel_axis" not in self.experiment_data:
            return
            
        data = self.experiment_data["parallel_axis"]
        
        # 清空现有数据
        for item in self.parallel_table.get_children():
            self.parallel_table.delete(item)
        self.parallel_data = []
        
        # 恢复表格数据
        if "table_data" in data and data["table_data"]:
            for row_data in data["table_data"]:
                item_id = self.parallel_table.insert("", "end", values=("", "", "", "", ""))
                
                new_data = {
                    "id": item_id,
                    "d_cm": row_data.get("d_cm", ""),
                    "d_m": row_data.get("d_m", ""),
                    "T": row_data.get("T", ""),
                    "d2": row_data.get("d2", ""),
                    "T2": row_data.get("T2", "")
                }
                self.parallel_data.append(new_data)
                
                self.parallel_table.item(item_id, values=(
                    new_data["d_cm"],
                    new_data["d_m"], 
                    new_data["T"],
                    new_data["d2"],
                    new_data["T2"]
                ))
        
        # 如果没有数据，添加默认的2行
        if not self.parallel_data:
            self.add_parallel_table_row()
            self.add_parallel_table_row()
        
        # 恢复其他数据
        if "h0" in data:
            self.h0_parallel_var.set(data["h0"])
        if "k_theory" in data:
            self.k_theory_var.set(data["k_theory"])
        if "b_theory" in data:
            self.b_theory_var.set(data["b_theory"])
        if "k_calc" in data:  # 新增
            self.k_calc_var.set(data["k_calc"])
        if "b_calc" in data:  # 新增
            self.b_calc_var.set(data["b_calc"])
        
        # +++ 新增：如果有计算值，恢复拟合曲线 +++
        if (self.k_calc_var.get() and self.b_calc_var.get() and 
            self.k_theory_var.get() and self.b_theory_var.get()):
            self.restore_parallel_plot_with_fit()
        else:
            # 如果没有计算值，只显示散点图
            self.update_parallel_plot()

    def restore_parallel_plot_with_fit(self):
        """恢复带拟合曲线的图形"""
        try:
            import numpy as np
            
            # 收集有效数据点
            d2_data = []
            T2_data = []
            
            for data in self.parallel_data:
                if data["d2"] and data["T2"]:
                    try:
                        d2 = float(data["d2"])
                        T2 = float(data["T2"])
                        d2_data.append(d2)
                        T2_data.append(T2)
                    except ValueError:
                        continue
            
            # 绘制图形
            self.parallel_ax.clear()
            
            if d2_data and T2_data:
                # 绘制散点
                self.parallel_ax.scatter(d2_data, T2_data, color='blue', s=30, alpha=0.7, label='数据点')
                
                # 获取保存的计算值
                k_calc = float(self.k_calc_var.get())
                b_calc = float(self.b_calc_var.get())
                k_theory = float(self.k_theory_var.get())
                b_theory = float(self.b_theory_var.get())
                
                # 绘制拟合直线
                if len(d2_data) >= 2:
                    d2_fit = np.linspace(min(d2_data), max(d2_data), 100)
                    T2_fit = k_calc * d2_fit + b_calc
                    self.parallel_ax.plot(d2_fit, T2_fit, 'r-', linewidth=1, 
                                        label=f'T^2={k_calc:.4f}d^2+{b_calc:.4f}')
                
                # 显示公式和理论值
                equation_text = f'T^2 = {k_calc:.4f}d^2 + {b_calc:.4f}'
                
                self.parallel_ax.text(0.05, 0.95, equation_text, transform=self.parallel_ax.transAxes,
                                verticalalignment='top', fontsize=7,
                                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            self.parallel_ax.set_xlabel('d^2/m^2', fontsize=9)
            self.parallel_ax.set_ylabel('T^2/s^2', fontsize=9)
            self.parallel_ax.grid(True, alpha=0.3)
            if d2_data:
                self.parallel_ax.legend(fontsize=8)
            
            self.parallel_fig.tight_layout(pad=0.5)
            self.parallel_fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.25)
            self.parallel_canvas.draw()
            
            print("平行轴定理拟合曲线恢复完成")
            
        except Exception as e:
            print(f"恢复拟合曲线时出错: {e}")
            # 如果恢复失败，回退到只显示散点图
            self.update_parallel_plot()

    def save_parallel_data(self):
        """保存平行轴定理的数据"""
        try:
            # 收集表格数据
            table_data = []
            for data in self.parallel_data:
                table_data.append({
                    "d_cm": data.get("d_cm", ""),
                    "d_m": data.get("d_m", ""), 
                    "T": data.get("T", ""),
                    "d2": data.get("d2", ""),
                    "T2": data.get("T2", "")
                })
            
            # 保存到实验数据
            self.experiment_data["parallel_axis"] = {
                "table_data": table_data,
                "h0": self.h0_parallel_var.get() if hasattr(self, 'h0_parallel_var') else "",
                "k_theory": self.k_theory_var.get() if hasattr(self, 'k_theory_var') else "",
                "b_theory": self.b_theory_var.get() if hasattr(self, 'b_theory_var') else "",
                "k_calc": self.k_calc_var.get() if hasattr(self, 'k_calc_var') else "",  # 新增
                "b_calc": self.b_calc_var.get() if hasattr(self, 'b_calc_var') else ""   # 新增
            }
        except Exception as e:
            print(f"保存平行轴定理数据时出错: {e}")

    def create_placeholder_bg(self):
        """创建占位背景"""
        self.canvas_bg.create_rectangle(0, 0, 330, 360, fill="lightgray", outline="")
        self.canvas_bg.create_text(200, 200, text="FD-CP-A复摆实验仪", 
                                  font=("Arial", 16, "bold"), fill="black")
        self.canvas_bg.create_text(200, 250, text="图片未找到", 
                                  font=("Arial", 12), fill="black")
        
    def create_overlay_controls(self):
        """在背景图片上创建叠加控件"""
        
        # 周期测量标签 - 先创建背景矩形，再创建文字
        self.period_bg_rect = self.canvas_bg.create_rectangle(100, 100, 220, 130, 
                                                            fill="lightblue", outline="black", width=0)  # 暂时添加边框便于调试
        
        self.period_text = self.canvas_bg.create_text(160, 115, text="周期测量", 
                                                    font=("Arial", 20, "bold"),
                                                    fill="black")
        
        # 脉宽测量标签
        self.pulse_bg_rect = self.canvas_bg.create_rectangle(100, 130, 220, 160, 
                                                            fill="lightblue", outline="black", width=0)  # 暂时添加边框便于调试
        
        self.pulse_text = self.canvas_bg.create_text(160, 145, text="脉宽测量", 
                                                    font=("Arial", 20),
                                                    fill="gray")
        
        # 在图片上叠加按钮
        button_positions = {
            "向上": (340+50, 170-20+2),
            "向下": (340+50, 250-20+7),
            "确定": (420+60, 170-20+2),
            "返回": (420+60, 250-20+7),
            "打开电源": (700+80+13, 180-20+36+2),  # 新增打开电源按钮
            "关闭电源": (700+80+13, 220-20+36-5)   # 新增关闭电源按钮
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
        
        # 初始高亮显示周期测量
        self.highlight_selected_mode()
        
        # 初始电源状态为关闭，隐藏实验仪界面
        self.set_power_state(False)

        # 创建周期测量界面元素（初始隐藏）
        self.create_period_measurement_ui()
        
        # 创建脉宽测量界面元素（初始隐藏）
        self.create_pulse_measurement_ui()

    def set_power_state(self, power_on):
        """设置电源状态"""
        self.power_on = power_on
        
        if power_on:
            # 电源打开：显示实验仪界面
            self.canvas_bg.itemconfig(self.period_text, state="normal")
            self.canvas_bg.itemconfig(self.pulse_text, state="normal")
            if hasattr(self, 'period_bg_rect'):
                self.canvas_bg.itemconfig(self.period_bg_rect, state="normal")
            if hasattr(self, 'pulse_bg_rect'):
                self.canvas_bg.itemconfig(self.pulse_bg_rect, state="normal")

            self.measurement_mode = "周期测量"
            self.highlight_selected_mode()
            # 更新按钮状态
            # self.update_power_buttons()
            print("电源已打开")
        else:
            # 电源关闭：隐藏所有实验仪界面
            self.hide_all_measurement_ui()
            
            # 隐藏主界面元素
            self.canvas_bg.itemconfig(self.period_text, state="hidden")
            self.canvas_bg.itemconfig(self.pulse_text, state="hidden")
            if hasattr(self, 'period_bg_rect'):
                self.canvas_bg.itemconfig(self.period_bg_rect, state="hidden")
            if hasattr(self, 'pulse_bg_rect'):
                self.canvas_bg.itemconfig(self.pulse_bg_rect, state="hidden")
            
            # 更新按钮状态
            # self.update_power_buttons()
            print("电源已关闭")

    def hide_all_measurement_ui(self):
        """隐藏所有测量界面"""
        # 隐藏周期测量界面
        if hasattr(self, 'period_ui_active') and self.period_ui_active:
            self.hide_measurement_ui()
        
        # 隐藏脉宽测量界面
        if hasattr(self, 'pulse_ui_active') and self.pulse_ui_active:
            self.hide_measurement_ui()
        
        # 确保所有测量界面都被隐藏
        self.period_ui_active = False
        self.pulse_ui_active = False

    def update_power_buttons(self):
        """更新电源按钮显示状态"""
        # 打开电源按钮：电源关闭时可用，打开时不可用（灰色）
        if "打开电源" in self.buttons:
            bg, text, x1, y1, x2, y2 = self.buttons["打开电源"]
            if self.power_on:
                self.canvas_bg.itemconfig(bg, fill="#A8556F")  # 变暗的 #CC667F
                self.canvas_bg.itemconfig(text, fill="#666666")  # 文字变灰
            else:
                self.canvas_bg.itemconfig(bg, fill="#CC667F")  # 正常颜色
                self.canvas_bg.itemconfig(text, fill="black")  # 黑色文字
        
        # 关闭电源按钮：电源打开时可用，关闭时不可用（变暗）
        if "关闭电源" in self.buttons:
            bg, text, x1, y1, x2, y2 = self.buttons["关闭电源"]
            if self.power_on:
                self.canvas_bg.itemconfig(bg, fill="#CC667F")  # 正常颜色
                self.canvas_bg.itemconfig(text, fill="black")  # 黑色文字
            else:
                self.canvas_bg.itemconfig(bg, fill="#A8556F")  # 变暗的 #CC667F
                self.canvas_bg.itemconfig(text, fill="#666666")  # 文字变灰


    def create_period_measurement_ui(self):
        """创建周期测量界面"""
        # 周期测量界面背景 - 尺寸减小30%
        self.period_bg = self.canvas_bg.create_rectangle(80, 100, 320, 240, 
                                                        fill="white", width=2,
                                                        state="hidden")
        
        # 创建六个栏目 - 位置和尺寸相应调整
        # 第一行：周期模式
        self.period_mode_bg = self.canvas_bg.create_rectangle(90, 110, 310, 135, 
                                                            fill="lightblue", outline="", width=1,
                                                            state="hidden")
        self.period_mode_text = self.canvas_bg.create_text(200, 122, text="周期：单周", 
                                                        font=("Arial", 20, "bold"),
                                                        state="hidden")
        
        # 第二行：次数
        self.count_bg = self.canvas_bg.create_rectangle(90, 145, 310, 170, 
                                                    fill="white", outline="", width=1,
                                                    state="hidden")
        self.count_text = self.canvas_bg.create_text(200, 157, text="次数：0次", 
                                                    font=("Arial", 20),
                                                    state="hidden")
        
        # 第三行：时间
        self.time_bg = self.canvas_bg.create_rectangle(90, 180, 310, 205, 
                                                    fill="lightgray", outline="", width=1,
                                                    state="hidden")
        self.time_text = self.canvas_bg.create_text(200, 192, text="时间：0s", 
                                                font=("Arial", 20),
                                                state="hidden")
        
        # 第四行：三个按钮 - 按钮尺寸相应减小
        self.start_bg = self.canvas_bg.create_rectangle(90, 210, 150, 235, 
                                                    fill="white", outline="", width=1,
                                                    state="hidden")
        self.start_text = self.canvas_bg.create_text(120, 222, text="开始", 
                                                    font=("Arial", 20),
                                                    state="hidden")
        
        self.query_bg = self.canvas_bg.create_rectangle(160, 210, 220, 235, 
                                                    fill="white", outline="", width=1,
                                                    state="hidden")
        self.query_text = self.canvas_bg.create_text(190, 222, text="查询", 
                                                    font=("Arial", 20),
                                                    state="hidden")
        
        self.clear_bg = self.canvas_bg.create_rectangle(230, 210, 290, 235, 
                                                    fill="white", outline="", width=1,
                                                    state="hidden")
        self.clear_text = self.canvas_bg.create_text(260, 222, text="清空", 
                                                    font=("Arial", 20),
                                                    state="hidden")
    
    def create_pulse_measurement_ui(self):
        """创建脉宽测量界面"""
        # 脉宽测量界面背景 - 尺寸减小30%
        self.pulse_bg = self.canvas_bg.create_rectangle(80, 100, 320, 240, 
                                                    fill="white", outline="", width=2,
                                                    state="hidden")
        
        # 第一行：时间（不可选中）
        self.pulse_time_bg = self.canvas_bg.create_rectangle(90, 110, 310, 135, 
                                                            fill="lightgray", outline="", width=1,
                                                            state="hidden")
        self.pulse_time_text = self.canvas_bg.create_text(200, 122, text="时间：0ms", 
                                                        font=("Arial", 20),
                                                        state="hidden")
        
        # 第二行：次数
        self.pulse_count_bg = self.canvas_bg.create_rectangle(90, 145, 310, 170, 
                                                            fill="lightblue", outline="", width=1,
                                                            state="hidden")
        self.pulse_count_text = self.canvas_bg.create_text(200, 157, text="次数：0次", 
                                                        font=("Arial", 20, "bold"),
                                                        state="hidden")
        
        # 第三行：空白
        self.pulse_blank_bg = self.canvas_bg.create_rectangle(90, 180, 310, 205, 
                                                            fill="white", outline="", width=1,
                                                            state="hidden")
        
        # 第四行：三个按钮 - 按钮尺寸相应减小
        self.pulse_start_bg = self.canvas_bg.create_rectangle(90, 210, 150, 235, 
                                                            fill="white", outline="", width=1,
                                                            state="hidden")
        self.pulse_start_text = self.canvas_bg.create_text(120, 222, text="开始", 
                                                        font=("Arial", 20),
                                                        state="hidden")
        
        self.pulse_query_bg = self.canvas_bg.create_rectangle(160, 210, 220, 235, 
                                                            fill="white", outline="", width=1,
                                                            state="hidden")
        self.pulse_query_text = self.canvas_bg.create_text(190, 222, text="查询", 
                                                        font=("Arial", 20),
                                                        state="hidden")
        
        self.pulse_clear_bg = self.canvas_bg.create_rectangle(230, 210, 290, 235, 
                                                            fill="white", outline="", width=1,
                                                            state="hidden")
        self.pulse_clear_text = self.canvas_bg.create_text(260, 222, text="清空", 
                                                        font=("Arial", 20),
                                                        state="hidden")
    
    def show_period_measurement_ui(self):
        """显示周期测量界面"""
        # 隐藏主界面元素
        self.canvas_bg.itemconfig(self.period_text, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_text, state="hidden")
        
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
    
    def show_pulse_measurement_ui(self):
        """显示脉宽测量界面"""
        # 隐藏主界面元素
        self.canvas_bg.itemconfig(self.period_text, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_text, state="hidden")
        
        # 显示脉宽测量界面
        self.canvas_bg.itemconfig(self.pulse_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_time_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_time_text, state="normal")
        self.canvas_bg.itemconfig(self.pulse_count_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_count_text, state="normal")
        self.canvas_bg.itemconfig(self.pulse_blank_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_start_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_start_text, state="normal")
        self.canvas_bg.itemconfig(self.pulse_query_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_query_text, state="normal")
        self.canvas_bg.itemconfig(self.pulse_clear_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_clear_text, state="normal")
        
        # 更新脉宽测量界面状态
        self.period_ui_active = False
        self.pulse_ui_active = True
        self.pulse_selection_index = 1  # 初始选中次数栏目
        self.setting_pulse_count = False

        # 重置显示
        self.canvas_bg.itemconfig(self.pulse_start_text, text="开始")
        self.update_pulse_count_display()
        self.update_pulse_time_display()
        
        # 高亮初始选中的栏目
        self.highlight_pulse_selection()
    
    def clear_all_pulse_data(self):
        """清空所有脉宽测量数据"""
        print("清空所有脉宽测量数据")
        
        self.pulse_data_groups = []
        self.pulse_count = 0
        self.pulse_time = 0
        self.current_pulse_measure_count = 0
        self.temp_pulse_data = []
        self.pulse_measurement_mode = "设定模式"
        
        # 重置显示
        self.update_pulse_count_display()
        self.update_pulse_time_display()
        

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
        
        # 隐藏脉宽测量界面
        self.canvas_bg.itemconfig(self.pulse_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_time_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_time_text, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_count_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_count_text, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_blank_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_start_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_start_text, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_query_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_query_text, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_clear_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_clear_text, state="hidden")
        
        # +++ 修复：确保也隐藏脉宽查询界面 +++
        self.hide_pulse_query_ui()
        
        # 显示主界面元素
        self.canvas_bg.itemconfig(self.period_text, state="normal")
        self.canvas_bg.itemconfig(self.pulse_text, state="normal")
        
        # +++ 修复：清空所有脉宽测量数据 +++
        self.clear_all_pulse_data()
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
        
        # 清空脉宽测量数据
        self.pulse_count = 0
        self.pulse_time = 0
        self.update_pulse_count_display()
        self.update_pulse_time_display()
        # +++ 结束新增 +++
    
    def highlight_selected_mode(self):
        """高亮显示选中的测量模式"""
        if self.measurement_mode == "周期测量":
            # 周期测量选中：蓝色背景，黑色文字
            self.canvas_bg.itemconfig(self.period_text, fill="black", font=("Arial", 20, "bold"))
            # 创建或更新蓝色背景
            if hasattr(self, 'period_bg_rect'):
                self.canvas_bg.coords(self.period_bg_rect, 100, 100, 220, 130)
                self.canvas_bg.itemconfig(self.period_bg_rect, state="normal")  # 确保显示
            else:
                self.period_bg_rect = self.canvas_bg.create_rectangle(100, 100, 220, 130, 
                                                                    fill="lightblue", outline="", width=0)
            # 脉宽测量未选中：无背景，灰色文字
            self.canvas_bg.itemconfig(self.pulse_text, fill="gray", font=("Arial", 20))
            # 隐藏脉宽测量的背景
            if hasattr(self, 'pulse_bg_rect'):
                self.canvas_bg.itemconfig(self.pulse_bg_rect, state="hidden")
        else:
            # 脉宽测量选中：蓝色背景，黑色文字
            self.canvas_bg.itemconfig(self.pulse_text, fill="black", font=("Arial", 20, "bold"))
            # 创建或更新蓝色背景
            if hasattr(self, 'pulse_bg_rect'):
                self.canvas_bg.coords(self.pulse_bg_rect, 100, 130, 220, 160)
                self.canvas_bg.itemconfig(self.pulse_bg_rect, state="normal")  # 确保显示
            else:
                self.pulse_bg_rect = self.canvas_bg.create_rectangle(100, 130, 220, 160, 
                                                                    fill="lightblue", outline="", width=0)
            # 周期测量未选中：无背景，灰色文字
            self.canvas_bg.itemconfig(self.period_text, fill="gray", font=("Arial", 20))
            # 隐藏周期测量的背景
            if hasattr(self, 'period_bg_rect'):
                self.canvas_bg.itemconfig(self.period_bg_rect, state="hidden")
    
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
    
    def highlight_pulse_selection(self):
        """高亮脉宽测量界面中的选中栏目"""
        # 重置所有栏目颜色
        self.canvas_bg.itemconfig(self.pulse_count_bg, fill="white")
        self.canvas_bg.itemconfig(self.pulse_start_bg, fill="white")
        self.canvas_bg.itemconfig(self.pulse_query_bg, fill="white")
        self.canvas_bg.itemconfig(self.pulse_clear_bg, fill="white")
        
        # 重置字体样式
        self.canvas_bg.itemconfig(self.pulse_count_text, font=("Arial", 20))
        
        # 根据当前选择状态高亮对应栏目
        if self.setting_pulse_count:
            # 在设置次数模式下，使用橙色高亮次数栏目
            self.canvas_bg.itemconfig(self.pulse_count_bg, fill="orange")
            self.canvas_bg.itemconfig(self.pulse_count_text, font=("Arial", 20, "bold"))
        else:
            # +++ 新增：测量模式下只能选择复位(2)和清空(4) +++
            if self.pulse_measurement_mode == "测量模式":
                self.pulse_items_count = 2  # 只有2个可选项
                # 调整选择索引范围：2=复位，4=清空
                if self.pulse_selection_index < 2:
                    self.pulse_selection_index = 2
                elif self.pulse_selection_index > 4:
                    self.pulse_selection_index = 4
                
                # 根据当前选择索引高亮
                if self.pulse_selection_index == 2:  # 复位按钮
                    self.canvas_bg.itemconfig(self.pulse_start_bg, fill="lightblue")
                elif self.pulse_selection_index == 4:  # 清空按钮
                    self.canvas_bg.itemconfig(self.pulse_clear_bg, fill="lightblue")
            else:
                # 正常模式下，根据选择索引高亮
                if self.pulse_selection_index == 1:
                    self.canvas_bg.itemconfig(self.pulse_count_bg, fill="lightblue")
                    self.canvas_bg.itemconfig(self.pulse_count_text, font=("Arial", 20, "bold"))
                elif self.pulse_selection_index == 2:
                    self.canvas_bg.itemconfig(self.pulse_start_bg, fill="lightblue")
                elif self.pulse_selection_index == 3:
                    self.canvas_bg.itemconfig(self.pulse_query_bg, fill="lightblue")
                elif self.pulse_selection_index == 4:
                    self.canvas_bg.itemconfig(self.pulse_clear_bg, fill="lightblue")

    
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
    
    def update_pulse_count_display(self):
        """更新脉宽测量次数显示"""
        self.canvas_bg.itemconfig(self.pulse_count_text, text=f"次数：{self.pulse_count}次")
    
    def update_pulse_time_display(self):
        """更新脉宽测量时间显示"""
        self.canvas_bg.itemconfig(self.pulse_time_text, text=f"时间：{self.pulse_time}ms")

    def on_canvas_click(self, event):
        """处理画布点击事件"""
        # 检查是否点击了按钮
        for button_name, (bg, text, x1, y1, x2, y2) in self.buttons.items():
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.handle_button_click(button_name)
                return
        
        # 只有在电源打开时才处理其他点击事件
        if not self.power_on:
            return

        # 检查是否在测量模式选择区域
        if 150 <= event.x <= 250 and 100 <= event.y <= 160:
            # 点击了周期测量或脉宽测量区域
            if 100 <= event.y <= 130:
                # 点击了周期测量
                self.measurement_mode = "周期测量"
                self.highlight_selected_mode()
            elif 130 <= event.y <= 160:
                # 点击了脉宽测量
                self.measurement_mode = "脉宽测量"
                self.highlight_selected_mode()
        
        # 检查是否在周期测量界面中点击了栏目
        if self.period_ui_active:
            if 60 <= event.x <= 340:
                if 310 <= event.y <= 340:
                    # 点击了周期模式栏目
                    self.period_selection_index = 0
                    self.setting_count = False
                    self.highlight_period_selection()
                elif 350 <= event.y <= 380:
                    # 点击了次数栏目
                    self.period_selection_index = 1
                    self.setting_count = True
                    self.highlight_period_selection()
                elif 430 <= event.y <= 470:
                    if 60 <= event.x <= 140:
                        # 点击了开始按钮
                        self.start_period_measurement()
                    elif 150 <= event.x <= 230:
                        # 点击了查询按钮
                        self.query_period_measurement()
                    elif 240 <= event.x <= 320:
                        # 点击了清空按钮
                        self.clear_period_measurement()
        
        # 检查是否在脉宽测量界面中点击了栏目
        if self.pulse_ui_active:
            if 60 <= event.x <= 340:
                if 350 <= event.y <= 380:
                    # 点击了次数栏目
                    self.pulse_selection_index = 1
                    self.setting_pulse_count = True
                    self.highlight_pulse_selection()
                elif 430 <= event.y <= 470:
                    if 60 <= event.x <= 140:
                        # 点击了开始按钮
                        self.start_pulse_measurement()
                    elif 150 <= event.x <= 230:
                        # 点击了查询按钮
                        self.query_pulse_measurement()
                    elif 240 <= event.x <= 320:
                        # 点击了清空按钮
                        self.clear_pulse_measurement()
    
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

        elif self.pulse_ui_active:
            if self.pulse_measurement_mode == "查询模式":
                if self.pulse_query_mode_state == "group_select":
                    # +++ 组选择模式：向上切换组 +++
                    if self.pulse_data_groups:
                        self.current_pulse_query_group = (self.current_pulse_query_group - 1) % len(self.pulse_data_groups)
                        self.pulse_query_start_index = 0  # 重置到组内起始位置
                        self.update_pulse_query_display()
                        print(f"切换到上一组：第{self.current_pulse_query_group + 1}组")
                    return
                else:
                    # +++ 数据滚动模式：向上滚动数据 +++
                    if hasattr(self, 'pulse_query_start_index') and self.pulse_data_groups:
                        group_data = self.pulse_data_groups[self.current_pulse_query_group]
                        pulse_data = group_data["pulse_data"]
                        
                        # 向上滚动（显示更早的数据）
                        if self.pulse_query_start_index > 0:
                            self.pulse_query_start_index = max(0, self.pulse_query_start_index - 1)
                            self.update_pulse_query_display()
                            print(f"向上滚动，显示第{self.pulse_query_start_index + 1}条开始的数据")
                        else:
                            print("已显示最早的数据")
                    return
            
            if self.pulse_measurement_mode == "测量模式":
                if self.pulse_selection_index == 2:  # 当前在复位
                    self.pulse_selection_index = 4   # 切换到清空
                elif self.pulse_selection_index == 4:  # 当前在清空
                    self.pulse_selection_index = 2   # 切换到复位
                self.highlight_pulse_selection()
                return
        
            if self.setting_pulse_count:
                # 在设置次数模式下，增加次数
                self.pulse_count = min(100, self.pulse_count + 1)
                self.update_pulse_count_display()
            else:
                # 在正常模式下，向上移动选择
                self.pulse_selection_index = (self.pulse_selection_index - 2) % 4 + 1
                self.highlight_pulse_selection()
        
        else:
            # 在主界面，向上切换测量模式
            if self.measurement_mode == "周期测量":
                self.measurement_mode = "脉宽测量"
            else:
                self.measurement_mode = "周期测量"
            self.highlight_selected_mode()
    
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
        
        elif self.pulse_ui_active:
            if self.pulse_measurement_mode == "查询模式":
                if self.pulse_query_mode_state == "group_select":
                    # +++ 组选择模式：向下切换组 +++
                    if self.pulse_data_groups:
                        self.current_pulse_query_group = (self.current_pulse_query_group + 1) % len(self.pulse_data_groups)
                        self.pulse_query_start_index = 0  # 重置到组内起始位置
                        self.update_pulse_query_display()
                        print(f"切换到下一组：第{self.current_pulse_query_group + 1}组")
                    return
                else:
                    # +++ 数据滚动模式：向下滚动数据 +++
                    if hasattr(self, 'pulse_query_start_index') and self.pulse_data_groups:
                        group_data = self.pulse_data_groups[self.current_pulse_query_group]
                        pulse_data = group_data["pulse_data"]
                        
                        # 向下滚动（显示更新的数据）
                        max_start_index = max(0, len(pulse_data) - 3)
                        if self.pulse_query_start_index < max_start_index:
                            self.pulse_query_start_index = min(max_start_index, self.pulse_query_start_index + 1)
                            self.update_pulse_query_display()
                            print(f"向下滚动，显示第{self.pulse_query_start_index + 1}条开始的数据")
                        else:
                            print("已显示最新的数据")
                    return
            
            if self.pulse_measurement_mode == "测量模式":
                if self.pulse_selection_index == 2:  # 当前在复位
                    self.pulse_selection_index = 4   # 切换到清空
                elif self.pulse_selection_index == 4:  # 当前在清空
                    self.pulse_selection_index = 2   # 切换到复位
                self.highlight_pulse_selection()
                return
        
            if self.setting_pulse_count:
                # 在设置次数模式下，减少次数
                self.pulse_count = max(0, self.pulse_count - 1)
                self.update_pulse_count_display()
            else:
                # 在正常模式下，向下移动选择
                self.pulse_selection_index = (self.pulse_selection_index % 4) + 1
                self.highlight_pulse_selection()
        
        else:
            # 在主界面，向下切换测量模式
            if self.measurement_mode == "周期测量":
                self.measurement_mode = "脉宽测量"
            else:
                self.measurement_mode = "周期测量"
            self.highlight_selected_mode()
    
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
                    self.clear_temp_data()
        
        elif self.pulse_ui_active:
            if self.pulse_measurement_mode == "查询模式":
            # +++ 修改：确定按钮用于进入/退出数据滚动模式 +++
                if self.pulse_query_mode_state == "group_select":
                    # 从组选择模式进入数据滚动模式
                    self.pulse_query_mode_state = "data_scroll"
                    self.pulse_query_start_index = 0  # 从第一条数据开始
                    self.update_pulse_query_display()
                    print("进入数据滚动模式")
                else:
                    # 数据滚动模式下确定按钮无效
                    print("数据滚动模式下确定按钮无效")
                return
            if self.setting_pulse_count:
                # 退出设置次数模式
                self.setting_pulse_count = False
                self.highlight_pulse_selection()
            else:
                # 根据当前选择执行操作
                if self.pulse_selection_index == 1:
                    # 进入设置次数模式
                    self.setting_pulse_count = True
                    self.highlight_pulse_selection()
                elif self.pulse_selection_index == 2:
                    if self.pulse_measurement_mode == "设定模式":
                        # 开始测量
                        self.start_pulse_measurement()
                    else:
                        # 测量模式下的复位
                        self.reset_pulse_measurement()
                elif self.pulse_selection_index == 3:
                    # 查询 - 只有有数据时才可进入
                    if self.pulse_data_groups:
                        self.enter_pulse_query_mode()
                    else:
                        print("没有脉宽测量数据，无法查询")
                elif self.pulse_selection_index == 4:
                    # 清空
                    self.clear_pulse_measurement()
                    self.clear_all_pulse_data()
            
        else:
            # 在主界面，进入选中的测量模式
            if self.measurement_mode == "周期测量":
                self.show_period_measurement_ui()
            else:
                self.show_pulse_measurement_ui()
    
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
            else:
                # 从测量界面返回主界面
                self.hide_measurement_ui()
        elif self.pulse_ui_active:          
            if self.pulse_measurement_mode == "查询模式":
                if self.pulse_query_mode_state == "data_scroll":
                    # +++ 数据滚动模式下按返回回到组选择模式 +++
                    self.pulse_query_mode_state = "group_select"
                    self.pulse_query_start_index = 0  # 重置显示位置
                    self.update_pulse_query_display()
                    print("返回组选择模式")
                    return
                else:
                    # 组选择模式下按返回回到脉宽测量界面
                    self.exit_pulse_query_mode()
                    return
                
            if self.setting_pulse_count:
                # 退出设置次数模式
                self.setting_pulse_count = False
                self.highlight_pulse_selection()
            else:
                # 从测量界面返回主界面
                self.hide_measurement_ui()
        else:
            # 在主界面，返回操作（如果有的话）
            print("返回主界面")
    
    def handle_power_button(self):
        """处理电源开关按钮"""
        print("电源开关被点击")
        # 这里可以添加电源开关的实际逻辑
    
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
        
    def clear_temp_data(self):
        """清空临时数据"""
        print("清空临时数据")
        self.current_measure_count = 0
        self.temp_measure_data = []
        self.update_count_display()
        self.update_time_display()

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

    def show_query_display(self):
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
        
        # 显示查询界面元素（需要创建）
        self.show_query_ui()

    def hide_query_display(self):
        """隐藏查询界面"""
        # 隐藏查询界面元素
        self.hide_query_ui()
        
        # 显示周期测量界面元素
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


    def query_period_measurement(self):
        """查询周期测量结果"""
        print("查询周期测量")
        # 这里可以添加实际的查询逻辑
    
    def clear_period_measurement(self):
        """清空周期测量数据"""
        print("清空周期测量")
        self.measure_count = 0
        self.measure_time = 0
        self.canvas_bg.itemconfig(self.count_text, text="次数：0次")
        self.canvas_bg.itemconfig(self.time_text, text="时间：0s")
    
    def start_pulse_measurement(self):
        """开始脉宽测量 - 进入测量模式"""
        # 检查次数是否至少为1
        if self.pulse_count < 1:
            print("错误：测量次数必须至少为1次")
            return
        
        print("进入脉宽测量模式")
        self.pulse_measurement_mode = "测量模式"
        self.current_pulse_measure_count = 0  # 当前测量次数从0开始
        self.temp_pulse_data = []  # 清空临时数据
        
        # 更新界面显示
        self.canvas_bg.itemconfig(self.pulse_start_text, text="复位")
        self.update_pulse_count_display()
        self.update_pulse_time_display()
        
        # 重置选择索引，只能选择复位和清空
        self.pulse_selection_index = 2  # 复位按钮
        self.highlight_pulse_selection()
    
    def handle_pulse_gate_release(self):
        """处理脉宽测量模式下的光电门释放事件"""
        if (self.pulse_ui_active and 
            self.pulse_measurement_mode == "测量模式" and 
            self.current_pulse_measure_count < self.pulse_count):
            
            # 计算当前脉宽
            pulse_width = self.calculate_pulse_width()
            print(f'脉宽测量 - 第{self.current_pulse_measure_count}次: {pulse_width:.1f}ms')
            if pulse_width > 0:
                
                # 更新测量次数
                self.current_pulse_measure_count += 1
                
                # 记录脉宽数据
                self.temp_pulse_data.append({
                    "count": self.current_pulse_measure_count,
                    "pulse_width": pulse_width
                })
                
                # 更新显示
                
                self.update_pulse_count_display()
                self.update_pulse_time_display()
                
                print(f"脉宽测量 - 第{self.current_pulse_measure_count}次: {pulse_width:.1f}ms")
                
                # 检查是否达到预设测量次数
                if self.current_pulse_measure_count >= self.pulse_count:
                    self.finish_pulse_measurement()

    def finish_pulse_measurement(self):
        """完成脉宽测量"""
        print("脉宽测量完成，保存数据")
        
        # 保存数据到组
        group_data = {
            "group_id": len(self.pulse_data_groups) + 1,
            "total_count": self.pulse_count,
            "pulse_data": self.temp_pulse_data.copy()
        }
        self.pulse_data_groups.append(group_data)
        
        # 返回设定模式
        self.pulse_measurement_mode = "设定模式"
        self.canvas_bg.itemconfig(self.pulse_start_text, text="开始")
        # self.pulse_selection_index = 1
        # self.highlight_pulse_selection()
        
        print(f"已保存第{group_data['group_id']}组脉宽测量数据")

    def reset_pulse_measurement(self):
        """复位脉宽测量"""
        print("复位脉宽测量")
        self.current_pulse_measure_count = 0
        self.temp_pulse_data = []
        self.update_pulse_count_display()
        self.update_pulse_time_display()

    def clear_pulse_measurement(self):
        """清空脉宽测量数据"""
        print("清空所有脉宽测量数据")
        self.pulse_data_groups = []
        self.current_pulse_measure_count = 0
        self.temp_pulse_data = []
        self.pulse_measurement_mode = "设定模式"
        
        # 恢复界面显示
        self.canvas_bg.itemconfig(self.pulse_start_text, text="开始")
        self.update_pulse_count_display()
        self.update_pulse_time_display()
        
        # 重置选择索引
        self.pulse_selection_index = 1
        self.highlight_pulse_selection()

    def update_pulse_count_display(self):
        """更新脉宽测量次数显示"""
        if self.pulse_measurement_mode == "测量模式":
            # 测量模式下显示当前测量次数
            self.canvas_bg.itemconfig(self.pulse_count_text, text=f"次数：{self.current_pulse_measure_count}次")
        else:
            # 设定模式下显示预设次数
            self.canvas_bg.itemconfig(self.pulse_count_text, text=f"次数：{self.pulse_count}次")

    def update_pulse_time_display(self):
        """更新脉宽测量时间显示"""
        if (self.pulse_measurement_mode == "测量模式" and 
            self.temp_pulse_data and 
            self.current_pulse_measure_count > 0):
            # 测量模式下显示最新脉宽时间
            latest_pulse = self.temp_pulse_data[-1]["pulse_width"]
            self.canvas_bg.itemconfig(self.pulse_time_text, text=f"时间：{latest_pulse:.1f}ms")
        else:
            # 其他情况下显示0
            self.canvas_bg.itemconfig(self.pulse_time_text, text="时间：0ms")

    def enter_pulse_query_mode(self):
        """进入脉宽查询模式"""
        print("进入脉宽查询模式")
        self.pulse_measurement_mode = "查询模式"
        self.current_pulse_query_group = 0
        # +++ 新增：初始状态为组选择模式 +++
        self.pulse_query_mode_state = "group_select"  # "group_select" 或 "data_scroll"
        self.pulse_query_start_index = 0
        self.show_pulse_query_ui()

    def exit_pulse_query_mode(self):
        """退出脉宽查询模式"""
        print("退出脉宽查询模式")
        self.pulse_measurement_mode = "设定模式"
        
        # +++ 修复：正确隐藏查询界面并显示脉宽测量界面 +++
        self.hide_pulse_query_ui()
        
        # 重新显示脉宽测量界面
        self.canvas_bg.itemconfig(self.pulse_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_time_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_time_text, state="normal")
        self.canvas_bg.itemconfig(self.pulse_count_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_count_text, state="normal")
        self.canvas_bg.itemconfig(self.pulse_blank_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_start_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_start_text, state="normal")
        self.canvas_bg.itemconfig(self.pulse_query_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_query_text, state="normal")
        self.canvas_bg.itemconfig(self.pulse_clear_bg, state="normal")
        self.canvas_bg.itemconfig(self.pulse_clear_text, state="normal")
        
        # 重置选择索引
        self.pulse_selection_index = 1
        self.highlight_pulse_selection()

    def show_pulse_query_ui(self):
        """显示脉宽查询界面"""
        # 隐藏脉宽测量界面元素
        self.canvas_bg.itemconfig(self.pulse_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_time_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_time_text, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_count_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_count_text, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_blank_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_start_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_start_text, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_query_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_query_text, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_clear_bg, state="hidden")
        self.canvas_bg.itemconfig(self.pulse_clear_text, state="hidden")
        
        # 创建脉宽查询界面
        self.pulse_query_bg_ui = self.canvas_bg.create_rectangle(80, 100, 320, 240, 
                                                            fill="white", width=2,
                                                            state="normal")
        
        # 第一行：组信息（在组选择模式下高亮）
        self.pulse_query_group_bg = self.canvas_bg.create_rectangle(90, 110, 310, 135, 
                                                                fill="lightblue", outline="", width=1,
                                                                state="normal")
        self.pulse_query_group_text = self.canvas_bg.create_text(200, 122, text="", 
                                                            font=("Arial", 16, "bold"),
                                                            state="normal")
        
        # 滚动文本区域（3行）
        self.pulse_query_text_bg = self.canvas_bg.create_rectangle(90, 145, 310, 220, 
                                                                fill="lightyellow", outline="", width=1,
                                                                state="normal")
        
        # 创建3行文本用于显示脉宽数据
        self.pulse_query_line1 = self.canvas_bg.create_text(200, 160, text="", 
                                                        font=("Arial", 12), anchor="center",
                                                        state="normal")
        self.pulse_query_line2 = self.canvas_bg.create_text(200, 180, text="", 
                                                        font=("Arial", 12), anchor="center",
                                                        state="normal")
        self.pulse_query_line3 = self.canvas_bg.create_text(200, 200, text="", 
                                                        font=("Arial", 12), anchor="center",
                                                        state="normal")
        
        # 更新查询显示
        self.update_pulse_query_display()

    def hide_pulse_query_ui(self):
        """隐藏脉宽查询界面"""
        # 隐藏所有查询界面元素
        items_to_hide = [
            'pulse_query_bg_ui', 'pulse_query_group_bg', 'pulse_query_group_text',
            'pulse_query_text_bg', 'pulse_query_line1', 'pulse_query_line2', 'pulse_query_line3'
        ]
        
        for item_name in items_to_hide:
            if hasattr(self, item_name):
                item = getattr(self, item_name)
                self.canvas_bg.itemconfig(item, state="hidden")

    def update_pulse_query_display(self):
        """更新脉宽查询显示"""
        if not self.pulse_data_groups:
            # 没有数据时显示提示
            self.canvas_bg.itemconfig(self.pulse_query_group_text, text="无脉宽测量数据")
            self.canvas_bg.itemconfig(self.pulse_query_line1, text="")
            self.canvas_bg.itemconfig(self.pulse_query_line2, text="")
            self.canvas_bg.itemconfig(self.pulse_query_line3, text="")
            return
        
        group_data = self.pulse_data_groups[self.current_pulse_query_group]
        pulse_data = group_data["pulse_data"]
        group_id = group_data["group_id"]
        total_count = group_data["total_count"]
        
        if not pulse_data:
            self.canvas_bg.itemconfig(self.pulse_query_group_text, text=f"第{group_id}组 数据为空")
            self.canvas_bg.itemconfig(self.pulse_query_line1, text="")
            self.canvas_bg.itemconfig(self.pulse_query_line2, text="")
            self.canvas_bg.itemconfig(self.pulse_query_line3, text="")
            return
        
        # 更新组信息
        total_groups = len(self.pulse_data_groups)
        group_info = f"第{group_id}/{total_groups}组 共{total_count}次"
        self.canvas_bg.itemconfig(self.pulse_query_group_text, text=group_info)
        
        # 根据模式更新显示
        if self.pulse_query_mode_state == "group_select":
            # 组选择模式下显示前3条数据
            self.pulse_query_start_index = 0
            lines = []
            for i in range(3):
                if i < len(pulse_data):
                    data = pulse_data[i]
                    line_text = f"第{data['count']}次: {data['pulse_width']:.1f}ms"
                    lines.append(line_text)
                else:
                    lines.append("")
            
        else:  # data_scroll 模式
            # 数据滚动模式下根据当前起始索引显示
            lines = []
            for i in range(3):
                data_index = self.pulse_query_start_index + i
                if data_index < len(pulse_data):
                    data = pulse_data[data_index]
                    line_text = f"第{data['count']}次: {data['pulse_width']:.1f}ms"
                    lines.append(line_text)
                else:
                    lines.append("")
        
        # 更新显示行
        self.canvas_bg.itemconfig(self.pulse_query_line1, text=lines[0])
        self.canvas_bg.itemconfig(self.pulse_query_line2, text=lines[1])
        self.canvas_bg.itemconfig(self.pulse_query_line3, text=lines[2])
        
        # +++ 修改：根据模式设置背景颜色 +++
        if self.pulse_query_mode_state == "group_select":
            # 组选择模式下：组信息行蓝色，数据部分白色
            self.canvas_bg.itemconfig(self.pulse_query_group_bg, fill="lightblue")
            self.canvas_bg.itemconfig(self.pulse_query_text_bg, fill="white")
        else:
            # 数据滚动模式下：组信息行白色，数据部分黄色
            self.canvas_bg.itemconfig(self.pulse_query_group_bg, fill="white")
            self.canvas_bg.itemconfig(self.pulse_query_text_bg, fill="lightblue")
    
    def clear_pulse_measurement(self):
        """清空脉宽测量数据"""
        print("清空脉宽测量")
        self.pulse_count = 0
        self.pulse_time = 0
        self.canvas_bg.itemconfig(self.pulse_count_text, text="次数：0次")
        self.canvas_bg.itemconfig(self.pulse_time_text, text="时间：0ms")
    
    def setup_animation(self):
        """设置动画"""
        self.animation = FuncAnimation(
            self.fig, self.update_animation,
            frames=None, interval=10, blit=False, cache_frame_data=False
        )
    
    def on_gate_trigger(self):
        """光电门触发处理"""
        if (self.period_ui_active and 
            self.period_measurement_mode == "测量模式" and 
            self.current_measure_count < self.max_record_count):
            
            # 根据单周/双周模式判断是否计数
            should_count = False
            if self.period_mode == "单周":
                # 单周模式：每次触发都计数
                should_count = True
                count_increment = 1
            else:  # 双周模式
                # 双周模式：每两次触发计数一次
                # 这里需要记录触发次数，可以使用一个额外的计数器
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
                
                # 计算时间
                theoretical_period = self.pendulum.get_period()
                if self.period_mode == "单周":
                    measure_time = theoretical_period / 2 * self.current_measure_count
                else:
                    measure_time = theoretical_period / 1 * (self.current_measure_count)
                
                # 记录数据
                self.temp_measure_data.append(measure_time)
                self.update_count_display()
                self.update_time_display()
                
                print(f"光电门触发！模式:{self.period_mode}, 计数:{self.current_measure_count}/{self.max_record_count}, 时间:{measure_time:.3f}s")
                
                # 检查是否达到最大记录次数
                if self.current_measure_count >= self.max_record_count:
                    self.finish_measurement()
        else:
            # 非测量模式下的触发，只显示不记录
            print("光电门触发（非测量模式）")

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
        self.query_ui_bg = self.canvas_bg.create_rectangle(80, 100, 320, 240, 
                                                        fill="white", width=2,
                                                        state="normal")
        
        # 第一行：组信息、周期模式、次数
        self.query_group_bg = self.canvas_bg.create_rectangle(90, 110, 310, 135, 
                                                            fill="lightblue", outline="", width=1,
                                                            state="normal")
        self.query_group_text = self.canvas_bg.create_text(200, 122, text="", 
                                                        font=("Arial", 16, "bold"),
                                                        state="normal")
        
        # 第二行：时间
        self.query_time_bg = self.canvas_bg.create_rectangle(90, 145, 310, 170, 
                                                            fill="white", outline="", width=1,
                                                            state="normal")
        self.query_time_text = self.canvas_bg.create_text(200, 157, text="", 
                                                        font=("Arial", 16),
                                                        state="normal")
        
        # 第三行：平均值
        self.query_avg_bg = self.canvas_bg.create_rectangle(90, 180, 310, 205, 
                                                        fill="lightblue", outline="", width=1,
                                                        state="normal")
        self.query_avg_text = self.canvas_bg.create_text(200, 192, text="", 
                                                        font=("Arial", 16),
                                                        state="normal")
        
        # 第四行：方差
        self.query_variance_bg = self.canvas_bg.create_rectangle(90, 215, 310, 240, 
                                                                fill="lightblue", outline="", width=1,
                                                                state="normal")
        self.query_variance_text = self.canvas_bg.create_text(200, 227, text="", 
                                                            font=("Arial", 16),
                                                            state="normal")
        
        # 更新查询显示
        self.update_query_display()

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
    
    def calculate_pulse_width(self):
        """计算复摆通过光电门的脉宽 - 简化版本"""
        try:
            # 获取复摆参数
            pendulum_length = self.pendulum.length
            pivot_position = self.pendulum.pivot_position
            initial_angle = abs(np.radians(self.angle_var.get()))
            
            # 计算末端相对于转轴的偏移
            end_offset = (1 - pivot_position) * pendulum_length
            
            # 计算复摆在最低点（角度=0）时的角速度
            # 使用能量守恒：初始势能 = 最低点动能
            # 初始势能：m * g * effective_com * (1 - cos(initial_angle))
            # 最低点动能：1/2 * I * ω^2
            # 所以：ω = √(2 * m * g * effective_com * (1 - cos(initial_angle)) / I)
            
            if self.pendulum.effective_com < 1e-6:
                print("有效质心距过小，无法计算脉宽")
                return 0
            
            # 计算最低点的角速度
            potential_energy_loss = self.pendulum.mass * self.pendulum.g * self.pendulum.effective_com * (1 - np.cos(initial_angle))
            angular_velocity = np.sqrt(2 * potential_energy_loss / self.pendulum.I)
            
            if angular_velocity < 1e-6:
                print(f"角速度过小: {angular_velocity:.6f}")
                return 0
            
            # 计算最低点的线速度
            linear_velocity = angular_velocity * end_offset
            
            if linear_velocity < 1e-6:
                print(f"线速度过小: {linear_velocity:.6f}")
                return 0
            
            # 计算脉宽
            beam_width = 0.002  # 光电门光束宽度 1cm
            pulse_width = beam_width / linear_velocity
            
            # 转换为毫秒
            pulse_width_ms = pulse_width * 1000
            
            print(f"脉宽计算（简化版）:")
            print(f"  初始角度: {np.degrees(initial_angle):.1f}°")
            print(f"  末端偏移: {end_offset:.3f}m")
            print(f"  有效质心距: {self.pendulum.effective_com:.3f}m")
            print(f"  角速度: {angular_velocity:.3f} rad/s")
            print(f"  线速度: {linear_velocity:.3f} m/s")
            print(f"  脉宽: {pulse_width_ms:.1f}ms")
            
            return pulse_width_ms
            
        except Exception as e:
            print(f"脉宽计算错误: {e}")
            import traceback
            traceback.print_exc()
            return 0

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
            variance=time_data[0]*0.0005
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

    def update_animation(self, frame):
        if self.animation_running:
            # 更新物理状态
            self.pendulum.update(0.1)  # 100ms时间步长
        
        # 检查光电门触发
        current_gate_state = self.check_gate_trigger()
        
        # +++ 修改：在光电门释放时计数 +++
        if not current_gate_state and self.last_gate_state:
            # 光电门从触发变为释放
            self.gate_triggered = False
            print("=== 光电门状态变化: 释放 ===")
            
            # 周期测量模式下的释放处理
            if (self.period_ui_active and 
                self.period_measurement_mode == "测量模式" and 
                self.current_measure_count < self.measure_count):
                
                self.handle_gate_release()
        
            # 脉宽测量模式下的释放处理
            elif (self.pulse_ui_active and 
                self.pulse_measurement_mode == "测量模式" and 
                self.current_pulse_measure_count < self.pulse_count):
                
                self.handle_pulse_gate_release()
            
        elif current_gate_state and not self.last_gate_state:
            # 光电门从释放变为触发
            self.gate_triggered = True
            print("=== 光电门状态变化: 触发 ===")
        
        self.last_gate_state = current_gate_state
        
        # 更新光电门红点状态
        self.update_gate_dot()
        
        # 原有的位置更新和显示代码...
        # 获取位置（现在包括摆锤位置）
        pivot, start, end, com, hammer_a_pos, hammer_b_pos = self.pendulum.get_positions(self.hanging_mode)
        
        # 更新摆杆
        self.rod.set_data([start[0], end[0]], [start[1], end[1]])
        
        if self.hanging_mode =="正挂":
            self.start_label.set_position((start[0], start[1] + 0.05))
            self.end_label.set_position((end[0], end[1] - 0.05))
        else:
            self.start_label.set_position((start[0], start[1] - 0.05))
            self.end_label.set_position((end[0], end[1] + 0.05))
        # 新增：计算延长部分的位置
        extension_length = 0.03
        
        if self.hanging_mode == "正挂":
            # 正挂：起点延长向上，末端延长向下
            start_extension_x = start[0] - extension_length * np.sin(self.pendulum.angle)
            start_extension_y = start[1] + extension_length * np.cos(self.pendulum.angle)
            end_extension_x = end[0] + extension_length * np.sin(self.pendulum.angle)
            end_extension_y = end[1] - extension_length * np.cos(self.pendulum.angle)
        else:
            # 倒挂：起点延长向下，末端延长向上
            start_extension_x = start[0] + extension_length * np.sin(self.pendulum.angle)
            start_extension_y = start[1] - extension_length * np.cos(self.pendulum.angle)
            end_extension_x = end[0] - extension_length * np.sin(self.pendulum.angle)
            end_extension_y = end[1] + extension_length * np.cos(self.pendulum.angle)
    
        
        # 更新延长部分
        self.rod_extension_start.set_data([start[0], start_extension_x], [start[1], start_extension_y])
        self.rod_extension_end.set_data([end[0], end_extension_x], [end[1], end_extension_y])
        
        # 更新转轴点
        self.pivot_point.center = pivot

         # +++ 修复：更新摆锤位置 +++
        # 更新摆锤A位置
        if self.hammer_a_placed and hammer_a_pos is not None:
            self.hammer_a_rect.set_visible(True)
            # 设置摆锤位置（矩形中心）
            self.hammer_a_rect.set_xy((hammer_a_pos[0] - 0.025, hammer_a_pos[1] - 0.025))  # 中心对齐
            # 设置摆锤角度与摆杆一致
            angle_deg = np.degrees(self.pendulum.angle)
            if self.hanging_mode == "倒挂":
                self.hammer_a_rect.set_xy((hammer_a_pos[0] + 0.025, hammer_a_pos[1] + 0.025))  # 中心对齐
                angle_deg += 180
            self.hammer_a_rect.angle = angle_deg
        else:
            self.hammer_a_rect.set_visible(False)
        
        # 更新摆锤B位置
        if self.hammer_b_placed and hammer_b_pos is not None:
            self.hammer_b_rect.set_visible(True)
            # 设置摆锤位置（矩形中心）
            self.hammer_b_rect.set_xy((hammer_b_pos[0] - 0.025, hammer_b_pos[1] - 0.025))  # 中心对齐
            # 设置摆锤角度与摆杆一致
            angle_deg = np.degrees(self.pendulum.angle)
            if self.hanging_mode == "倒挂":
                self.hammer_b_rect.set_xy((hammer_b_pos[0] + 0.025, hammer_b_pos[1] + 0.025))  # 中心对齐
                angle_deg += 180
            self.hammer_b_rect.angle = angle_deg
        else:
            self.hammer_b_rect.set_visible(False)

        # 更新质心（不可见）
        self.com_point.center = com
        
        # 更新末端点（不可见）
        self.end_point.center = end
        
        # 更新起点（不可见）
        self.start_point.center = start
        
        # 更新轨迹（不可见）
        if self.pendulum.trajectory:
            traj_x, traj_y = zip(*self.pendulum.trajectory)
            self.trajectory.set_data(traj_x, traj_y)
        else:
            self.trajectory.set_data([], [])
        
        # 更新信息文本（添加光电门状态和调试信息）
        angle_degrees = np.degrees(self.pendulum.angle)
        period = self.pendulum.get_period()
        
        pivot_distance_mm = self.pendulum.pivot_position * self.pendulum.length * 1000
        
        # 添加摆锤信息和光电门状态
        hammer_a_info = ""
        hammer_b_info = ""
        
        if self.hammer_a_placed:
            hammer_a_pos_mm = self.hammer_a_position * self.pendulum.length * 1000
            hammer_a_info = f"\n摆锤A位置: {hammer_a_pos_mm:.0f}mm"
        
        if self.hammer_b_placed:
            hammer_b_pos_mm = self.hammer_b_position * self.pendulum.length * 1000
            hammer_b_info = f"\n摆锤B位置: {hammer_b_pos_mm:.0f}mm"
        
        # 计算总质量
        total_mass = self.pendulum.mass
        if self.hammer_a_placed:
            total_mass += self.pendulum.hammer_mass
        if self.hammer_b_placed:
            total_mass += self.pendulum.hammer_mass
        
        # 将高度偏移改为mm表示
        height_offset_mm = self.pendulum.height_offset * 1000
        
        # 计算末端位置（用于调试）
        end_offset = (1 - self.pendulum.pivot_position) * self.pendulum.length
        end_y = -end_offset * np.cos(self.pendulum.angle) + self.pendulum.height_offset
        
        # 添加光电门状态和调试信息
        gate_status = "触发" if self.gate_triggered else "未触发"
        gate_info = f"\n光电门: {gate_status}"
        debug_info = f"\n末端Y: {end_y:.3f}m, 光电门Y: {self.gate_var.get():.3f}m"
        
        # 添加脉宽信息
        pulse_info = ""
        if self.pulse_ui_active:
            current_pulse = self.calculate_pulse_width()
            pulse_info = f"\n当前脉宽: {current_pulse:.1f}ms"


        info = (f"摆角: {angle_degrees:.1f}°\n"
                f"角速度: {self.pendulum.angular_velocity:.2f} rad/s\n"
                f"周期: {period:.3f} s\n"
                f"转轴位置: {pivot_distance_mm:.0f} mm"
                f"{hammer_a_info}{hammer_b_info}\n"
                f"总质量: {total_mass:.3f} kg\n"
                f"转动惯量: {self.pendulum.I:.4f} kg·m^2\n"
                f"有效质心距: {self.pendulum.effective_com:.3f} m\n"
                f"高度偏移: {height_offset_mm:.0f} mm"
                f"{gate_info}{debug_info}")
        # self.info_text.set_text(info)
        
        # 修改返回元素：添加光电门红点
        return [self.rod, self.rod_extension_start, self.rod_extension_end, 
                self.pivot_point, self.hammer_a_rect, self.hammer_b_rect,
                self.com_point, self.end_point, self.start_point, self.trajectory, 
                self.gate_dot, self.info_text]
        
        # return [self.rod, self.rod_extension_start, self.rod_extension_end, 
        #         self.pivot_point, self.hammer_a_point, self.hammer_b_point,
        #         self.com_point, self.end_point, self.start_point, self.trajectory, 
        #         self.gate_dot]
    
    def handle_gate_release(self):
        """处理光电门释放事件（用于计数）"""
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
                    theoretical_period = self.pendulum.get_period()
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

    def run(self):
        """运行应用"""
        self.root.mainloop()

# 创建并运行应用
if __name__ == "__main__":
    app = IntegratedApp()
    app.run()