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
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 获取程序所在目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    program_dir = os.path.dirname(sys.executable)
else:
    # 如果是Python脚本
    program_dir = os.path.dirname(os.path.abspath(__file__))

print(f"程序所在目录: {program_dir}")

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
        self.hammer_mass = 0.126  # 每个摆锤的质量

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
        rod_distance = abs(0.5 * self.length - self.pivot_position * self.length)  # 杆的质心在中心
        total_I = I_cm_rod + self.mass * rod_distance**2
        
        # 添加摆锤的转动惯量贡献（点质量）
        if self.hammer_a_placed:
            hammer_a_distance = abs(self.hammer_a_position * self.length - self.pivot_position * self.length)
            total_I += self.hammer_mass * hammer_a_distance**2
        
        if self.hammer_b_placed:
            hammer_b_distance = abs(self.hammer_b_position * self.length - self.pivot_position * self.length)
            total_I += self.hammer_mass * hammer_b_distance**2
        
        self.I = total_I

    
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
    
    def get_positions(self):
        """获取关键点的位置（包括摆锤）"""
        # 转轴位置固定在原点，加上高度偏移
        pivot = (0, self.height_offset)
        
        # 计算杆的起点和终点位置（相对于转轴）
        start_offset = -self.pivot_position * self.length
        end_offset = (1 - self.pivot_position) * self.length
        
        start_x = start_offset * np.sin(self.angle)
        start_y = -start_offset * np.cos(self.angle) + self.height_offset
        
        end_x = end_offset * np.sin(self.angle)
        end_y = -end_offset * np.cos(self.angle) + self.height_offset
        
        # 质心位置
        com_offset = self.com - self.pivot_position * self.length
        com_x = com_offset * np.sin(self.angle)
        com_y = -com_offset * np.cos(self.angle) + self.height_offset
        
        # 摆锤位置
        hammer_a_pos = None
        hammer_b_pos = None
        
        if self.hammer_a_placed:
            hammer_a_offset = self.hammer_a_position * self.length - self.pivot_position * self.length
            hammer_a_x = hammer_a_offset * np.sin(self.angle)
            hammer_a_y = -hammer_a_offset * np.cos(self.angle) + self.height_offset
            hammer_a_pos = (hammer_a_x, hammer_a_y)
        
        if self.hammer_b_placed:
            hammer_b_offset = self.hammer_b_position * self.length - self.pivot_position * self.length
            hammer_b_x = hammer_b_offset * np.sin(self.angle)
            hammer_b_y = -hammer_b_offset * np.cos(self.angle) + self.height_offset
            hammer_b_pos = (hammer_b_x, hammer_b_y)
        
        return pivot, (start_x, start_y), (end_x, end_y), (com_x, com_y), hammer_a_pos, hammer_b_pos
    
    def get_period(self):
        """计算小角度近似下的周期"""
        if self.effective_com < 1e-3:
            return float('inf')  # 转轴在质心时周期为无穷大
        
        period = 2 * np.pi * np.sqrt(self.I / (self.mass * self.g * self.effective_com))
        return period

class IntegratedApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FD-CP-A复摆实验仪")
        self.root.geometry("1600x800")
        
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
        self.hammer_mass = 0.1  # 摆锤质量（kg）

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
    
    def load_background_images(self):
        """加载并显示背景图片"""
        try:
            # 图片文件路径
            image_files = {
                'gate': 'gate.jpg',
                'angle': 'angle.jpg', 
                'grid': 'grid.jpg',
                'device': 'device.jpg'
            }
            
            # 图片位置和大小配置 - 调整为适应0.7m杆长的范围
            # 修改zorder值：数值越大，图层越靠上
            image_configs = {
                'gate': {'extent': [-0.05, 0.03, -0.75, -0.65], 'zorder': 4},    
                'angle': {'extent': [-0.052, 0.05, -0.05, 0.05], 'zorder': 3},      
                'grid': {'extent': [0.2, 0.2, -0.8, 0.4], 'zorder': 1},      
                'device': {'extent': [-0.225, 0.175, -0.8, 0.4], 'zorder': 2}       
            }
            
            self.background_images = {}
            
            for image_name, filename in image_files.items():
                image_path = os.path.join(program_dir, "background", filename)
                
                if os.path.exists(image_path):
                    # 加载图片
                    img = plt.imread(image_path)
                    config = image_configs[image_name]
                    
                    # 显示图片 - 修改alpha值来调整透明度
                    im = self.ax.imshow(img, extent=config['extent'], 
                                    zorder=config['zorder'], alpha=0.9)
                    self.background_images[image_name] = im
                    print(f"成功加载背景图片: {filename}")
                else:
                    print(f"背景图片未找到: {image_path}")
                    
        except Exception as e:
            print(f"加载背景图片时发生错误: {e}")

    def on_pivot_slider_changed(self, value):
        """处理转轴位置滑块变化"""
        pivot_pos = float(value)
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
        # 末端的最低位置（当摆角为180度时，末端在最高点；摆角为0度时，末端在最低点）
        end_min_y = -end_offset + height_offset
        
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
        angle_degrees = float(value)
        self.pendulum.update_angle(angle_degrees)
        self.angle_label.config(text=f"{angle_degrees:.0f}°")
    
    def on_height_slider_changed(self, value):
        """处理复摆高度滑块变化"""
        height_offset = float(value)
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
            # 开始动画
            self.animation_running = True
            self.start_stop_button.config(text="停止")
            # 禁用所有控件
            self.enable_controls(False)
    
    def enable_controls(self, enabled):
        """启用或禁用所有控制控件"""
        state = "normal" if enabled else "disabled"
        
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
        
        # 摆锤A（初始不可见）
        self.hammer_a_point = Circle((0, 0), 0.025, color='purple', zorder=6, visible=False)
        self.ax.add_patch(self.hammer_a_point)
        
        # 摆锤B（初始不可见）
        self.hammer_b_point = Circle((0, 0), 0.025, color='brown', zorder=6, visible=False)
        self.ax.add_patch(self.hammer_b_point)

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
        
        # 添加图例标注（包括摆锤）
        self.ax.plot([], [], 'ro', markersize=8, label='转轴')
        self.ax.plot([], [], 'mo', markersize=8, label='摆锤A')  # 紫色
        self.ax.plot([], [], 'o', color='brown', markersize=8, label='摆锤B')  # 棕色
        self.ax.legend(loc='lower right')
        
        # 将matplotlib图形嵌入到tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建滑块框架
        slider_frame = ttk.Frame(parent)
        slider_frame.pack(fill=tk.X, pady=(0, 5))
        
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
        
        self.pivot_minus_btn = ttk.Button(pivot_button_frame, text="-", width=2,
                                        command=lambda: self.adjust_pivot(-0.001))
        self.pivot_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.pivot_plus_btn = ttk.Button(pivot_button_frame, text="+", width=2,
                                    command=lambda: self.adjust_pivot(0.001))
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
                                    command=lambda: self.adjust_gate(-0.001))
        self.gate_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.gate_plus_btn = ttk.Button(gate_button_frame, text="+", width=2,
                                    command=lambda: self.adjust_gate(0.001))
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
                                        command=lambda: self.adjust_angle(-1))
        self.angle_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.angle_plus_btn = ttk.Button(angle_button_frame, text="+", width=2,
                                    command=lambda: self.adjust_angle(1))
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
                                        command=lambda: self.adjust_height(-0.001))
        self.height_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.height_plus_btn = ttk.Button(height_button_frame, text="+", width=2,
                                        command=lambda: self.adjust_height(0.001))
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
                                        command=lambda: self.adjust_hammer_a(-0.001))
        self.hammer_a_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.hammer_a_plus_btn = ttk.Button(hammer_a_button_frame, text="+", width=2,
                                        command=lambda: self.adjust_hammer_a(0.001))
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
        self.hammer_a_point.set_visible(False)
        
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
                                        command=lambda: self.adjust_hammer_b(-0.001))
        self.hammer_b_minus_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.hammer_b_plus_btn = ttk.Button(hammer_b_button_frame, text="+", width=2,
                                        command=lambda: self.adjust_hammer_b(0.001))
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
        self.hammer_b_point.set_visible(False)
        
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

    def check_gate_trigger(self):
        """检查光电门是否触发"""
        try:
            # 获取光电门位置和复摆参数
            gate_y = self.gate_var.get()  # 光电门垂直位置
            pendulum_length = self.pendulum.length  # 细杆长度
            pivot_position = self.pendulum.pivot_position  # 转轴位置（比例）
            height_offset = self.pendulum.height_offset  # 复摆高度偏移
            
            # 计算复摆末端位置
            end_offset = (1 - pivot_position) * pendulum_length
            end_y = -end_offset * np.cos(self.pendulum.angle) + height_offset
            
            # 获取当前摆角（角度制）
            current_angle_degrees = abs(np.degrees(self.pendulum.angle))
            initial_angle_degrees = abs(self.angle_var.get())
            
            # 条件2: 根据初始摆角设置触发阈值
            if initial_angle_degrees <= 5:
                trigger_threshold = 1.0
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
        current = self.pivot_var.get()
        new_value = max(0.0, min(1.0, current + delta))
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
        current = self.height_var.get()
        new_value = max(-0.3, min(0.1, current + delta))
        self.height_var.set(new_value)
        self.on_height_slider_changed(new_value)

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

    def start_continuous_adjust(self, control_type, delta):
        """开始连续调整"""
        self.continuous_adjust_running = True
        self.continuous_adjust_type = control_type
        self.continuous_adjust_delta = delta
        self.continuous_adjust()

    def stop_continuous_adjust(self):
        """停止连续调整"""
        self.continuous_adjust_running = False

    def continuous_adjust(self):
        """连续调整函数"""
        if self.continuous_adjust_running:
            if self.continuous_adjust_type == "pivot":
                self.adjust_pivot(self.continuous_adjust_delta)
            elif self.continuous_adjust_type == "gate":
                self.adjust_gate(self.continuous_adjust_delta)
            elif self.continuous_adjust_type == "angle":
                self.adjust_angle(self.continuous_adjust_delta)
            elif self.continuous_adjust_type == "height":
                self.adjust_height(self.continuous_adjust_delta)
            elif self.continuous_adjust_type == "hammer_a":
                self.adjust_hammer_a(self.continuous_adjust_delta)
            elif self.continuous_adjust_type == "hammer_b":
                self.adjust_hammer_b(self.continuous_adjust_delta)
            
            # 50ms后再次调用，实现连续调整
            self.root.after(50, self.continuous_adjust)

    def toggle_hammer_a(self):
        """切换摆锤A状态"""
        if not self.hammer_a_placed:
            # 放置摆锤A
            self.hammer_a_placed = True
            self.hammer_a_button.config(text="取下摆锤A")
            self.hammer_a_slider.config(state="normal")
            # 启用微调按钮
            self.hammer_a_minus_btn.config(state="normal")
            self.hammer_a_plus_btn.config(state="normal")
            self.pendulum.update_hammer_a(True, self.hammer_a_var.get())
            self.hammer_a_point.set_visible(True)
        else:
            # 取下摆锤A
            self.hammer_a_placed = False
            self.hammer_a_button.config(text="放置摆锤A")
            self.hammer_a_slider.config(state="disabled")
            # 禁用微调按钮
            self.hammer_a_minus_btn.config(state="disabled")
            self.hammer_a_plus_btn.config(state="disabled")
            self.pendulum.update_hammer_a(False)
            self.hammer_a_point.set_visible(False)
        
        self.canvas.draw_idle()

    def toggle_hammer_b(self):
        """切换摆锤B状态"""
        if not self.hammer_b_placed:
            # 放置摆锤B
            self.hammer_b_placed = True
            self.hammer_b_button.config(text="取下摆锤B")
            self.hammer_b_slider.config(state="normal")
            # 启用微调按钮
            self.hammer_b_minus_btn.config(state="normal")
            self.hammer_b_plus_btn.config(state="normal")
            self.pendulum.update_hammer_b(True, self.hammer_b_var.get())
            self.hammer_b_point.set_visible(True)
        else:
            # 取下摆锤B
            self.hammer_b_placed = False
            self.hammer_b_button.config(text="放置摆锤B")
            self.hammer_b_slider.config(state="disabled")
            # 禁用微调按钮
            self.hammer_b_minus_btn.config(state="disabled")
            self.hammer_b_plus_btn.config(state="disabled")
            self.pendulum.update_hammer_b(False)
            self.hammer_b_point.set_visible(False)
        
        self.canvas.draw_idle()

    def on_hammer_a_slider_changed(self, value):
        """处理摆锤A位置滑块变化"""
        position = float(value)
        self.hammer_a_position = position
        self.pendulum.update_hammer_a(True, position)
        
        # 更新位置显示（单位mm）
        position_mm = position * self.pendulum.length * 1000
        self.hammer_a_label.config(text=f"{position_mm:.0f}mm")
        
        self.canvas.draw_idle()

    def on_hammer_b_slider_changed(self, value):
        """处理摆锤B位置滑块变化"""
        position = float(value)
        self.hammer_b_position = position
        self.pendulum.update_hammer_b(True, position)
        
        # 更新位置显示（单位mm）
        position_mm = position * self.pendulum.length * 1000
        self.hammer_b_label.config(text=f"{position_mm:.0f}mm")
        
        self.canvas.draw_idle()

    def setup_control_panel(self, parent):
        # 创建画布用于显示背景图片和叠加控件
        self.canvas_bg = tk.Canvas(parent, width=900, height=600, bg="white")
        self.canvas_bg.pack(fill=tk.BOTH, expand=True)
        
        # 加载并显示实验仪图片
        image_path = os.path.join(program_dir, "background", "FD-CP-A复摆实验仪.png")
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
        
    def create_placeholder_bg(self):
        """创建占位背景"""
        self.canvas_bg.create_rectangle(0, 0, 330, 360, fill="lightgray", outline="")
        self.canvas_bg.create_text(200, 200, text="FD-CP-A复摆实验仪", 
                                  font=("Arial", 16, "bold"), fill="black")
        self.canvas_bg.create_text(200, 250, text="图片未找到", 
                                  font=("Arial", 12), fill="black")
        
    def create_overlay_controls(self):
        """在背景图片上创建叠加控件"""
        
        # # 测量模式显示区域 - 放置在图片上的适当位置
        # mode_bg = self.canvas_bg.create_rectangle(150, 100, 250, 160, 
        #                                          fill="white", outline="black", width=2)
        
        # 周期测量标签
        self.period_text = self.canvas_bg.create_text(160, 115, text="周期测量", 
                                                     font=("Arial", 20, "bold"),
                                                     fill="green")
        
        # 脉宽测量标签
        self.pulse_text = self.canvas_bg.create_text(160, 145, text="脉宽测量", 
                                                    font=("Arial", 20),
                                                    fill="gray")
        
        # 在图片上叠加按钮
        button_positions = {
            "向上": (340+50, 170-20+2),
            "向下": (340+50, 250-20+7),
            "确定": (420+60, 170-20+2),
            "返回": (420+60, 250-20+7),
            # "电源开关": (700+80, 220-20)
        }
        
        self.buttons = {}
        for text, (x, y) in button_positions.items():
            btn_bg = self.canvas_bg.create_rectangle(x-12, y-12, x+12, y+12, 
                                                   fill="#333333", outline="", width=1)
            btn_text = self.canvas_bg.create_text(x, y, text="", 
                                                font=("Arial", 10, "bold"))
            
            # 存储按钮信息用于点击检测
            self.buttons[text] = (btn_bg, btn_text, x-15, y-15, x+15, y+15)
        
        # 绑定画布点击事件
        self.canvas_bg.bind("<Button-1>", self.on_canvas_click)
        
        # 初始高亮显示周期测量
        self.highlight_selected_mode()
        
        # 创建周期测量界面元素（初始隐藏）
        self.create_period_measurement_ui()
        
        # 创建脉宽测量界面元素（初始隐藏）
        self.create_pulse_measurement_ui()
    
    def create_period_measurement_ui(self):
        """创建周期测量界面"""
        # 周期测量界面背景 - 尺寸减小30%
        self.period_bg = self.canvas_bg.create_rectangle(80, 100, 320, 240, 
                                                        fill="white", width=2,
                                                        state="hidden")
        
        # 创建六个栏目 - 位置和尺寸相应调整
        # 第一行：周期模式
        self.period_mode_bg = self.canvas_bg.create_rectangle(90, 110, 310, 135, 
                                                            fill="lightgreen", outline="", width=1,
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
                                                            fill="lightyellow", outline="", width=1,
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
        
        # 高亮初始选中的栏目
        self.highlight_pulse_selection()
    
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
        
        # 显示主界面元素
        self.canvas_bg.itemconfig(self.period_text, state="normal")
        self.canvas_bg.itemconfig(self.pulse_text, state="normal")
        
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

        # 更新界面状态
        self.period_ui_active = False
        self.pulse_ui_active = False
        self.period_selection_index = 0
        self.pulse_selection_index = 1
        self.setting_count = False
        self.setting_pulse_count = False
    
    def highlight_selected_mode(self):
        """高亮显示选中的测量模式"""
        if self.measurement_mode == "周期测量":
            self.canvas_bg.itemconfig(self.period_text, fill="green", font=("Arial", 20, "bold"))
            self.canvas_bg.itemconfig(self.pulse_text, fill="gray", font=("Arial", 20))
        else:
            self.canvas_bg.itemconfig(self.period_text, fill="gray", font=("Arial", 20))
            self.canvas_bg.itemconfig(self.pulse_text, fill="green", font=("Arial", 20, "bold"))
    
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
                self.canvas_bg.itemconfig(self.period_mode_bg, fill="lightgreen")
                self.canvas_bg.itemconfig(self.period_mode_text, font=("Arial", 20, "bold"))
            elif self.period_selection_index == 1:
                self.canvas_bg.itemconfig(self.count_bg, fill="lightyellow")
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
            # 在正常模式下，根据选择索引高亮
            if self.pulse_selection_index == 1:
                self.canvas_bg.itemconfig(self.pulse_count_bg, fill="lightyellow")
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
            self.canvas_bg.itemconfig(self.time_text, text=f"时间：{latest_time:.2f}s")
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

        elif self.pulse_ui_active:
            if self.setting_pulse_count:
                # 在设置次数模式下，增加次数
                self.pulse_count = min(100, self.pulse_count + 1)
                self.update_pulse_count_display()
            else:
                # 修复：简单的索引循环 1->2->3->4->1
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
            if self.setting_pulse_count:
                # 在设置次数模式下，减少次数
                self.pulse_count = max(0, self.pulse_count - 1)
                self.update_pulse_count_display()
            else:
                # 修复：简单的索引循环 1->2->3->4->1
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
            
            elif self.period_measurement_mode == "查询模式":
                # 查询模式下按确定返回周期测量界面
                self.exit_query_mode()
        
        elif self.pulse_ui_active:
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
                    # 开始测量
                    self.start_pulse_measurement()
                elif self.pulse_selection_index == 3:
                    # 查询
                    self.query_pulse_measurement()
                elif self.pulse_selection_index == 4:
                    # 清空
                    self.clear_pulse_measurement()
        
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
        """开始脉宽测量"""
        print("开始脉宽测量")
        # 这里可以添加实际的脉宽测量逻辑
    
    def query_pulse_measurement(self):
        """查询脉宽测量结果"""
        print("查询脉宽测量")
        # 这里可以添加实际的查询逻辑
    
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
                    measure_time = theoretical_period / 4 * self.current_measure_count
                else:
                    measure_time = theoretical_period / 2 * (self.current_measure_count)
                
                # 记录数据
                self.temp_measure_data.append(measure_time)
                self.update_count_display()
                self.update_time_display()
                
                print(f"光电门触发！模式:{self.period_mode}, 计数:{self.current_measure_count}/{self.max_record_count}, 时间:{measure_time:.2f}s")
                
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
        self.period_selection_index = 0
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
                                                        fill="lightyellow", outline="", width=1,
                                                        state="normal")
        self.query_avg_text = self.canvas_bg.create_text(200, 192, text="", 
                                                        font=("Arial", 16),
                                                        state="normal")
        
        # 第四行：方差
        self.query_variance_bg = self.canvas_bg.create_rectangle(90, 215, 310, 240, 
                                                                fill="lightgreen", outline="", width=1,
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
        avg_time = sum(time_data) / len(time_data)  # 平均时间
        
        # 计算方差
        if len(time_data) > 1:
            variance = sum((t - avg_time) ** 2 for t in time_data) / len(time_data)
            std_deviation = variance ** 0.5  # 标准差
        else:
            variance = 0
            std_deviation = 0
        
        # 更新显示
        # 第一行：第X组 单周/双周 X次
        group_info = f"第{self.current_query_group + 1}组 {mode} {max_count}次"
        self.canvas_bg.itemconfig(self.query_group_text, text=group_info)
        
        # 第二行：时间：Xs
        time_info = f"时间：{last_time:.2f}s"
        self.canvas_bg.itemconfig(self.query_time_text, text=time_info)
        
        # 第三行：平均：Xs
        avg_info = f"平均：{avg_time:.2f}s"
        self.canvas_bg.itemconfig(self.query_avg_text, text=avg_info)
        
        # 第四行：方差：X (标准差：X)
        variance_info = f"方差：{variance:.4f}"
        self.canvas_bg.itemconfig(self.query_variance_text, text=variance_info)
        
        # 调试信息
        print(f"查询显示更新：{group_info}")
        print(f"时间数据：{time_data}")
        print(f"平均值：{avg_time:.2f}s, 方差：{variance:.4f}")

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
            
            # 在测量模式下，光电门释放时计数
            if (self.period_ui_active and 
                self.period_measurement_mode == "测量模式" and 
                self.current_measure_count < self.max_record_count):
                
                self.handle_gate_release()
                
        elif current_gate_state and not self.last_gate_state:
            # 光电门从释放变为触发
            self.gate_triggered = True
            print("=== 光电门状态变化: 触发 ===")
        
        self.last_gate_state = current_gate_state
        
        # 更新光电门红点状态
        self.update_gate_dot()
        
        # 原有的位置更新和显示代码...
        # 获取位置（现在包括摆锤位置）
        pivot, start, end, com, hammer_a_pos, hammer_b_pos = self.pendulum.get_positions()
        
        # 更新摆杆
        self.rod.set_data([start[0], end[0]], [start[1], end[1]])
        
        # 新增：计算延长部分的位置
        extension_length = 0.03
        
        # 计算起点延长部分（从起点向外延伸）
        start_extension_x = start[0] - extension_length * np.sin(self.pendulum.angle)
        start_extension_y = start[1] + extension_length * np.cos(self.pendulum.angle)
        
        # 计算终点延长部分（从终点向外延伸）
        end_extension_x = end[0] + extension_length * np.sin(self.pendulum.angle)
        end_extension_y = end[1] - extension_length * np.cos(self.pendulum.angle)
        
        # 更新延长部分
        self.rod_extension_start.set_data([start[0], start_extension_x], [start[1], start_extension_y])
        self.rod_extension_end.set_data([end[0], end_extension_x], [end[1], end_extension_y])
        
        # 更新转轴点
        self.pivot_point.center = pivot

        # 更新摆锤位置
        if self.hammer_a_placed and hammer_a_pos is not None:
            self.hammer_a_point.center = hammer_a_pos
            self.hammer_a_point.set_visible(True)
        else:
            self.hammer_a_point.set_visible(False)
        
        if self.hammer_b_placed and hammer_b_pos is not None:
            self.hammer_b_point.center = hammer_b_pos
            self.hammer_b_point.set_visible(True)
        else:
            self.hammer_b_point.set_visible(False)

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
        
        info = (f"摆角: {angle_degrees:.1f}°\n"
                f"角速度: {self.pendulum.angular_velocity:.2f} rad/s\n"
                f"周期: {period:.2f} s\n"
                f"转轴位置: {pivot_distance_mm:.0f} mm"
                f"{hammer_a_info}{hammer_b_info}\n"
                f"总质量: {total_mass:.3f} kg\n"
                f"转动惯量: {self.pendulum.I:.4f} kg·m^2\n"
                f"有效质心距: {self.pendulum.effective_com:.3f} m\n"
                f"高度偏移: {height_offset_mm:.0f} mm"
                f"{gate_info}{debug_info}")
        self.info_text.set_text(info)
        
        # 修改返回元素：添加光电门红点
        return [self.rod, self.rod_extension_start, self.rod_extension_end, 
                self.pivot_point, self.hammer_a_point, self.hammer_b_point,
                self.com_point, self.end_point, self.start_point, self.trajectory, 
                self.gate_dot, self.info_text]
    
    def handle_gate_release(self):
        """处理光电门释放事件（用于计数）"""
        if (self.period_ui_active and 
            self.period_measurement_mode == "测量模式" and 
            self.current_measure_count < self.measure_count):  # 改为与预设次数比较
            
            # 根据单周/双周模式判断是否计数
            should_count = False
            if self.period_mode == "单周":
                # 单周模式：每次释放都计数
                should_count = True
                count_increment = 1
            else:  # 双周模式
                # 双周模式：每两次释放计数一次
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
                    # 单周模式：每次计数对应1/4周期
                    measure_time = theoretical_period * self.current_measure_count / 4
                else:
                    # 双周模式：每次计数对应1/2周期
                    measure_time = theoretical_period * self.current_measure_count / 2
                
                # 记录数据
                self.temp_measure_data.append(measure_time)
                self.update_count_display()
                self.update_time_display()
                
                print(f"光电门释放计数！模式:{self.period_mode}, 计数:{self.current_measure_count}/{self.measure_count}, 时间:{measure_time:.2f}s")
                
                # 检查是否达到预设测量次数
                if self.current_measure_count >= self.measure_count:
                    self.finish_measurement()
            else:
                # 双周模式下不计数但显示状态
                print(f"光电门释放（双周模式，第{self.double_period_counter}次触发，不计数）")
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