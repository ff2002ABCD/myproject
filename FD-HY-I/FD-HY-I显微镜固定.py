import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import math
import random
from tkinter import filedialog

def get_resource_path(relative_path):
    """获取资源的绝对路径，支持打包后的环境"""
    try:
        # 打包后的临时文件夹路径
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)


class YangsModulusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("弯曲法测量横梁的杨氏模量")
        self.root.geometry("1300x800")  # 加宽窗口
        self.root.resizable(False, False)  # 禁止窗口调整大小
        # 初始化变量
        self.crosshair_pos = 4.0  # 十字线位置 (mm)
        self.knife_edge_pos = 5.0  # 刀口架基线位置 (mm)
        self.weight_count = 0  # 砝码数量 (0-12)
        self.total_weight = 0  # 总重量 (g)
        self.current_tab = "霍尔位置传感器静态特性测量"
        
        # 数据存储
        self.hall_data = [[0]*6 for _ in range(3)]  # 3行6列
        self.hall_table_entries = []
        
        self.brass_data = [[0]*6 for _ in range(2)]  # 2行6列
        self.brass_table_entries = []
        
        # 黄铜样品参数
        self.length = tk.DoubleVar(value=23.0)  # mm
        self.width = tk.DoubleVar(value=2.3)    # mm  
        self.thickness = tk.DoubleVar(value=0.995)  # mm
        
        # 调零值
        self.zero_value = tk.IntVar(value=0)
        
        # 初始电压值（随机生成 -100 到 100）
        self.initial_voltage = random.randint(-100, 100)
        self.current_voltage = self.initial_voltage

        # 砝码对应的位移和电压增量（初始化时确定，每个砝码10g）
        # 原来每个砝码20g，现在改为10g，变化量减半
        self.weight_displacements = []  # 每个砝码对应的位移增量 (mm)
        self.weight_voltages = []       # 每个砝码对应的电压增量 (mV)
        for _ in range(12):  # 最多12个砝码 (120g)
            # 原来是0.24-0.26mm，现在减半为0.12-0.13mm
            self.weight_displacements.append(random.uniform(0.12, 0.13))
            # 原来是71-75mV，现在减半为36-37mV
            self.weight_voltages.append(random.randint(36, 37))

        # 磁铁位置对电压的影响（范围-100到100，步进1mV）
        self.magnet_voltage_offset = 0  # 磁铁引起的电压偏移
        self.magnet_position = 0  # 磁铁当前位置 (-100到100)
        # 创建四个区域
        self.create_top_left()
        self.create_bottom_left()
        self.create_top_right()
        self.create_bottom_right()
        
        # 初始化画布绘制
        self.draw_microscope()
    
    
    def create_top_left(self):
        """左上区域：读数显微镜区域"""
        frame = tk.Frame(self.root, bg='white', relief=tk.RAISED, bd=2)
        frame.place(x=100, y=10, width=360, height=370)
        
        tk.Label(frame, text="读数显微镜", font=("Arial", 12, "bold"), 
                 bg='white').pack(pady=5)
        
        # 显微镜画布 (直径300px)
        self.microscope_canvas = tk.Canvas(frame, width=320, height=320, 
                                            bg='lightgray', highlightthickness=1)
        self.microscope_canvas.pack(pady=5)
        
    def draw_microscope(self):
        """绘制显微镜刻度、十字线和刀口架"""
        self.microscope_canvas.delete("all")
        
        # 绘制圆形显微镜 (直径300px)
        self.microscope_canvas.create_oval(10, 10, 310, 310, outline='black', width=3)
        
        # 刻度范围: y从30到290 (对应0-8mm, 上下各空出10px)
        # 0mm在底部(290), 8mm在顶部(30)
        # 刻度间距: 260px / 8mm = 32.5px/mm
        start_y_bottom = 290  # 0mm位置(底部)
        
        # 绘制刻度线 (0-8mm)
        for i in range(0, 9):  # 0到8mm
            y = 290 - i * 32.5
            # 主刻度线
            if i % 1 == 0:
                self.microscope_canvas.create_line(140, y, 180, y, width=2)
                # 添加数字标签
                label_y = y - 5
                # 数字显示在左侧
                self.microscope_canvas.create_text(125, label_y, text=str(i), 
                                                     font=("Arial", 8), anchor='e')
        
        # 绘制短的细分刻度 (每0.2mm)
        for i in range(0, 41):
            mm_val = i * 0.2
            y = 290 - mm_val * 32.5
            if mm_val % 1 != 0:  # 不是整数mm
                self.microscope_canvas.create_line(155, y, 165, y, width=1)
        
        # 绘制刻度尺边框
        self.microscope_canvas.create_line(160, 30, 160, 290, width=1)
        
        # 绘制十字线 (可移动, 范围0-8mm)
        crosshair_y = 290 - self.crosshair_pos * 32.5
        # 确保十字线在圆形内
        crosshair_y = max(30, min(290, crosshair_y))
        # 水平线 (贯穿整个圆形)
        self.microscope_canvas.create_line(10, crosshair_y, 310, crosshair_y, 
                                            fill='red', width=2)
        # 垂直线
        self.microscope_canvas.create_line(200, 10, 200, 310,
                                            fill='red', width=2)
        # 标注十字线
        self.microscope_canvas.create_text(260, crosshair_y - 8, text="十字线", 
                                            fill='red', font=("Arial", 8))
        
        # 绘制刀口架基线 (可移动, 范围0-8mm, 粗横线)
        knife_y = 290 - self.knife_edge_pos * 32.5
        knife_y = max(30, min(290, knife_y))
        self.microscope_canvas.create_line(10, knife_y, 310, knife_y, 
                                            fill='blue', width=4)
        self.microscope_canvas.create_text(260, knife_y - 8, text="刀口架基线", 
                                            fill='blue', font=("Arial", 8))
        
    def create_bottom_left(self):
        """左下区域：实验操作区域"""
        frame = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        frame.place(x=10, y=390, width=680, height=450)
        
        tk.Label(frame, text="实验操作区域", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 创建左右分栏的容器
        content_frame = tk.Frame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：图片区域
        left_frame = tk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # 右侧：控制区域
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # 加载装置图片（放在左侧）
        img_path = get_resource_path("background/装置.jpg")
        try:
            img = Image.open(img_path)
            # 调整图片大小以适应左侧区域
            img = img.resize((300, 250), Image.Resampling.LANCZOS)
            self.device_img = ImageTk.PhotoImage(img)
            img_label = tk.Label(left_frame, image=self.device_img)
            img_label.pack(pady=10)
        except Exception as e:
            tk.Label(left_frame, text=f"无法加载图片:\n装置.jpg\n{e}", fg='red').pack(pady=20)
        
        # 十字线位置控制
        crosshair_container = tk.Frame(right_frame)
        crosshair_container.pack(fill=tk.X, pady=5)

        tk.Label(crosshair_container, text="十字线位置 (mm):", font=("Arial", 9)).pack(anchor='w')

        # 十字线进度条和微调按钮放在同一行
        crosshair_row = tk.Frame(crosshair_container)
        crosshair_row.pack(fill=tk.X)

        # 左微调按钮（长按支持）
        self.crosshair_minus_btn = tk.Button(crosshair_row, text="-", font=("Arial", 10, "bold"),
                                            width=2)
        self.crosshair_minus_btn.pack(side=tk.LEFT, padx=(0, 5))
        # 绑定长按事件
        self.crosshair_minus_btn.bind("<ButtonPress-1>", lambda e: self.start_repeat(self.crosshair_minus))
        self.crosshair_minus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_repeat())

        # 十字线进度条
        self.crosshair_slider = tk.Scale(crosshair_row, from_=0, to=8, resolution=0.01,
                                        orient=tk.HORIZONTAL, length=180,
                                        command=self.update_crosshair,
                                        showvalue=0)
        self.crosshair_slider.set(4.0)
        self.crosshair_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 右微调按钮（长按支持）
        self.crosshair_plus_btn = tk.Button(crosshair_row, text="+", font=("Arial", 10, "bold"),
                                            width=2)
        self.crosshair_plus_btn.pack(side=tk.LEFT, padx=(5, 0))
        # 绑定长按事件
        self.crosshair_plus_btn.bind("<ButtonPress-1>", lambda e: self.start_repeat(self.crosshair_plus))
        self.crosshair_plus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_repeat())

        # 显示当前值
        self.crosshair_value_label = tk.Label(crosshair_container, text="4.00 mm", 
                                            font=("Arial", 9), fg='red')
        self.crosshair_value_label.pack(anchor='e', pady=(0, 5))

        # 刀口架基线控制
        knife_container = tk.Frame(right_frame)
        knife_container.pack(fill=tk.X, pady=5)

        tk.Label(knife_container, text="刀口架基线位置 (mm):", font=("Arial", 9)).pack(anchor='w')

        # 刀口架基线进度条和微调按钮放在同一行
        knife_row = tk.Frame(knife_container)
        knife_row.pack(fill=tk.X)

        # 左微调按钮（长按支持）
        self.knife_minus_btn = tk.Button(knife_row, text="-", font=("Arial", 10, "bold"),
                                        width=2)
        self.knife_minus_btn.pack(side=tk.LEFT, padx=(0, 5))
        # 绑定长按事件
        self.knife_minus_btn.bind("<ButtonPress-1>", lambda e: self.start_repeat(self.knife_minus))
        self.knife_minus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_repeat())

        # 刀口架基线进度条
        self.knife_slider = tk.Scale(knife_row, from_=0, to=8, resolution=0.01,
                                    orient=tk.HORIZONTAL, length=180,
                                    command=self.update_knife_edge,
                                    showvalue=0)
        self.knife_slider.set(5.0)
        self.knife_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 右微调按钮（长按支持）
        self.knife_plus_btn = tk.Button(knife_row, text="+", font=("Arial", 10, "bold"),
                                        width=2)
        self.knife_plus_btn.pack(side=tk.LEFT, padx=(5, 0))
        # 绑定长按事件
        self.knife_plus_btn.bind("<ButtonPress-1>", lambda e: self.start_repeat(self.knife_plus))
        self.knife_plus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_repeat())

        # 显示当前值
        self.knife_value_label = tk.Label(knife_container, text="5.00 mm", 
                                        font=("Arial", 9), fg='blue')
        self.knife_value_label.pack(anchor='e', pady=(0, 5))
        
        # 移动磁铁进度条
        tk.Label(right_frame, text="磁铁位置:", font=("Arial", 9)).pack(anchor='w')
        self.magnet_slider = tk.Scale(right_frame, from_=-100, to=100, resolution=1,
                                    orient=tk.HORIZONTAL, length=220, 
                                    command=self.update_magnet_position,
                                    showvalue=0)
        self.magnet_slider.set(0)  # 设置初始位置为中间
        self.magnet_slider.pack(pady=5, fill=tk.X)
        
        # # 调零控件（放在移动磁铁进度条下方）
        # zero_container = tk.Frame(right_frame)
        # zero_container.pack(pady=10, fill=tk.X)
        
        # 调零控件标题
        tk.Label(right_frame, text="调零:", font=("Arial", 9), 
                 fg='black').pack(anchor='w')
        
        # 调零进度条和数值放在同一行
        zero_slider_frame = tk.Frame(right_frame)
        zero_slider_frame.pack(fill=tk.X, pady=0)
        
        self.zero_slider = tk.Scale(zero_slider_frame, from_=-100, to=100, resolution=1,
                                     orient=tk.HORIZONTAL, length=370,
                                     variable=self.zero_value,
                                     command=self.update_zero_value,
                                     showvalue=0)
        self.zero_slider.set(0)
        self.zero_slider.pack(pady=5, fill=tk.X)
        
        # # 显示当前调零值
        # self.zero_display_label = tk.Label(zero_slider_frame, text="0 mV", 
        #                                     font=("Arial", 9, "bold"), fg='red', width=8)
        # self.zero_display_label.pack(side=tk.LEFT)
        
        # 重置按钮
        # reset_btn = tk.Button(zero_container, text="重置", command=self.reset_zero,
        #                       font=("Arial", 8), bg='lightgray', width=8)
        # reset_btn.pack(pady=5)
        
        # 砝码控制按钮
        btn_frame = tk.Frame(right_frame)
        btn_frame.pack(pady=15)

        self.add_weight_btn = tk.Button(btn_frame, text="增加砝码 (+10g)", command=self.add_weight,
                                        font=("Arial", 10), bg='lightgreen', width=12)
        self.add_weight_btn.pack(side=tk.LEFT, padx=5)

        self.remove_weight_btn = tk.Button(btn_frame, text="减少砝码 (-10g)", command=self.remove_weight,
                                            font=("Arial", 10), bg='lightcoral', width=12)
        self.remove_weight_btn.pack(side=tk.LEFT, padx=5)

        self.weight_label = tk.Label(right_frame, text="砝码: 0个 (0g)", font=("Arial", 10))
        self.weight_label.pack(pady=5)
    
    def start_repeat(self, callback, interval=50):
        """开始长按重复触发"""
        self.repeat_id = self.root.after(interval, self.repeat_callback, callback, interval)

    def stop_repeat(self):
        """停止长按重复触发"""
        if hasattr(self, 'repeat_id') and self.repeat_id is not None:
            self.root.after_cancel(self.repeat_id)
            self.repeat_id = None

    def repeat_callback(self, callback, interval):
        """长按重复回调"""
        callback()
        self.repeat_id = self.root.after(interval, self.repeat_callback, callback, interval)

    def crosshair_plus(self):
        """十字线位置增加0.01mm"""
        new_value = self.crosshair_pos + 0.01
        if new_value <= 8.0:
            self.crosshair_slider.set(new_value)
            self.update_crosshair(new_value)

    def crosshair_minus(self):
        """十字线位置减少0.01mm"""
        new_value = self.crosshair_pos - 0.01
        if new_value >= 0:
            self.crosshair_slider.set(new_value)
            self.update_crosshair(new_value)

    def knife_plus(self):
        """刀口架基线位置增加0.01mm"""
        new_value = self.knife_edge_pos + 0.01
        if new_value <= 8.0:
            self.knife_slider.set(new_value)
            self.update_knife_edge(new_value)

    def knife_minus(self):
        """刀口架基线位置减少0.01mm"""
        new_value = self.knife_edge_pos - 0.01
        if new_value >= 0:
            self.knife_slider.set(new_value)
            self.update_knife_edge(new_value)

    def update_magnet_position(self, value):
        """更新磁铁位置对电压的影响（步进1mV）"""
        self.magnet_position = int(float(value))
        self.magnet_voltage_offset = self.magnet_position
        
        # 更新电压显示
        self.current_voltage = self.initial_voltage + self.zero_value.get() + self.magnet_voltage_offset
        if hasattr(self, 'voltage_text'):
            self.host_canvas.itemconfig(self.voltage_text, text=str(self.current_voltage))

    def update_crosshair(self, value):
        """更新十字线位置"""
        self.crosshair_pos = float(value)
        # 更新显示标签
        if hasattr(self, 'crosshair_value_label'):
            self.crosshair_value_label.config(text=f"{self.crosshair_pos:.2f} mm")
        self.draw_microscope()
        
    def update_knife_edge(self, value):
        """更新刀口架基线位置"""
        self.knife_edge_pos = float(value)
        # 更新显示标签
        if hasattr(self, 'knife_value_label'):
            self.knife_value_label.config(text=f"{self.knife_edge_pos:.2f} mm")
        self.draw_microscope()
        
    def add_weight(self):
        """增加砝码 (+10g)"""
        if self.weight_count < 12:  # 最多12个砝码
            self.weight_count += 1
            self.total_weight = self.weight_count * 10  # 计算总重量
            
            # 刀口架基线向上移动（数值减小）
            displacement = self.weight_displacements[self.weight_count - 1]
            self.knife_edge_pos -= displacement
            self.knife_edge_pos = max(0, min(8, self.knife_edge_pos))
            self.knife_slider.set(self.knife_edge_pos)
            
            # 电压增加
            voltage_increment = self.weight_voltages[self.weight_count - 1]
            self.initial_voltage += voltage_increment
            self.current_voltage = self.initial_voltage + self.zero_value.get() + self.magnet_voltage_offset
            
            # 更新电压显示
            if hasattr(self, 'voltage_text'):
                # 如果电压是整数则显示为整数，否则显示1位小数
                if abs(self.current_voltage - round(self.current_voltage)) < 0.01:
                    self.host_canvas.itemconfig(self.voltage_text, text=str(int(round(self.current_voltage))))
                else:
                    self.host_canvas.itemconfig(self.voltage_text, text=f"{self.current_voltage:.1f}")
            
            # 更新砝码显示（显示总重量）
            self.weight_label.config(text=f"砝码: {self.weight_count}个 ({self.total_weight}g)")
            self.draw_microscope()
        else:
            messagebox.showwarning("警告", "已达到最大砝码数量(12个，120g)")
            
    def remove_weight(self):
        """减少砝码 (-10g)"""
        if self.weight_count > 0:
            # 移除最后一个砝码的影响
            displacement = self.weight_displacements[self.weight_count - 1]
            self.knife_edge_pos += displacement
            self.knife_edge_pos = max(0, min(8, self.knife_edge_pos))
            self.knife_slider.set(self.knife_edge_pos)
            
            voltage_increment = self.weight_voltages[self.weight_count - 1]
            self.initial_voltage -= voltage_increment
            self.current_voltage = self.initial_voltage + self.zero_value.get() + self.magnet_voltage_offset
            
            if hasattr(self, 'voltage_text'):
                if abs(self.current_voltage - round(self.current_voltage)) < 0.01:
                    self.host_canvas.itemconfig(self.voltage_text, text=str(int(round(self.current_voltage))))
                else:
                    self.host_canvas.itemconfig(self.voltage_text, text=f"{self.current_voltage:.1f}")
            
            self.weight_count -= 1
            self.total_weight = self.weight_count * 10
            self.weight_label.config(text=f"砝码: {self.weight_count}个 ({self.total_weight}g)")
            self.draw_microscope()
        else:
            messagebox.showwarning("警告", "已经没有砝码了")
            
    def create_top_right(self):
        """右上区域：实验仪主机区域"""
        frame = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        frame.place(x=480, y=10, width=800, height=370)
        
        tk.Label(frame, text="实验仪主机", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 创建容器用于放置图片和电压显示
        image_container = tk.Frame(frame)
        image_container.pack(pady=10)
        
        # 加载主机图片
        img_path = get_resource_path("background/主机.jpg")
        try:
            img = Image.open(img_path)
            # 保持原始比例 700:240
            display_width = 750
            display_height = int(display_width * 240 / 700)
            img = img.resize((display_width, display_height), Image.Resampling.LANCZOS)
            self.host_img = ImageTk.PhotoImage(img)
            
            # 在Canvas上放置图片，这样可以叠加其他元素
            self.host_canvas = tk.Canvas(image_container, width=display_width, height=display_height,
                                          highlightthickness=0)
            self.host_canvas.pack()
            self.host_canvas.create_image(0, 0, anchor=tk.NW, image=self.host_img)
            
            # 在图片上添加电压显示框（白色背景，黑色边框）
            # 计算显示框位置（图片右上角）
            box_x = display_width - 600  # 距离右边120px
            box_y = 120  # 距离顶部20px
            
            # # 绘制电压显示框背景
            # self.voltage_box = self.host_canvas.create_rectangle(
            #     box_x, box_y, box_x + 100, box_y + 50,
            #     fill='white', outline='black', width=2
            # )
            
            # 添加电压显示标签
            self.voltage_text = self.host_canvas.create_text(
                box_x + 65, box_y + 20,
                text=str(self.current_voltage),
                font=("Arial",48, "bold"), fill='black'
            )
            
        except Exception as e:
            tk.Label(frame, text=f"无法加载图片: 主机.jpg\n{e}", fg='red').pack(pady=50)
    
    def update_zero_value(self, value):
        """更新调零值显示（1mV步进）"""
        zero_val = int(float(value))
        
        # 计算最终显示的电压值 = 初始电压 + 调零值 + 磁铁偏移
        final_voltage = self.initial_voltage + zero_val + self.magnet_voltage_offset
        self.current_voltage = final_voltage
        
        # 更新图片上的电压显示
        if hasattr(self, 'voltage_text'):
            self.host_canvas.itemconfig(self.voltage_text, text=str(final_voltage))
        self.host_canvas.itemconfig(self.voltage_text, fill='black')

    def reset_zero(self):
        """重置调零值为0"""
        self.zero_slider.set(0)
        
        # 重置电压显示
        self.current_voltage = self.initial_voltage + self.magnet_voltage_offset
        if hasattr(self, 'voltage_text'):
            self.host_canvas.itemconfig(self.voltage_text, text=str(self.current_voltage))
            self.host_canvas.itemconfig(self.voltage_text, fill='black')
         
            
    def create_bottom_right(self):
        """右下区域：数据记录区域"""
        frame = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        frame.place(x=680, y=390, width=600, height=450)
        
        tk.Label(frame, text="数据记录", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 选项卡1: 霍尔位置传感器静态特性测量
        self.hall_frame = tk.Frame(self.notebook)
        self.notebook.add(self.hall_frame, text="霍尔位置传感器静态特性测量")
        self.create_hall_tab()
        
        # 选项卡2: 黄铜样品位移测量
        self.brass_frame = tk.Frame(self.notebook)
        self.notebook.add(self.brass_frame, text="黄铜样品位移测量")
        self.create_brass_tab()
        
        # 绑定选项卡切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
    def create_hall_tab(self):
        """创建霍尔传感器选项卡"""
        # 表格框架
        table_frame = tk.Frame(self.hall_frame)
        table_frame.pack(pady=10)
        
        # 创建3行7列表格
        headers = ["", "1", "2", "3", "4", "5", "6"]
        row_headers = ["M/g", "Z/mm", "U/mV"]
        
        self.hall_table_entries = []
        
        for i in range(4):  # 4行 (包括表头)
            row_entries = []
            for j in range(7):  # 7列
                if i == 0:  # 第一行表头
                    if j == 0:
                        label = tk.Label(table_frame, text=headers[j], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                    else:
                        label = tk.Label(table_frame, text=headers[j], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                    label.grid(row=i, column=j, padx=1, pady=1)
                elif i == 1:  # M/g
                    if j == 0:
                        label = tk.Label(table_frame, text=row_headers[i-1], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                        label.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(None)
                    else:
                        entry = tk.Entry(table_frame, width=10, justify='center')
                        entry.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(entry)
                elif i == 2:  # Z/mm
                    if j == 0:
                        label = tk.Label(table_frame, text=row_headers[i-1], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                        label.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(None)
                    else:
                        entry = tk.Entry(table_frame, width=10, justify='center')
                        entry.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(entry)
                elif i == 3:  # U/mV
                    if j == 0:
                        label = tk.Label(table_frame, text=row_headers[i-1], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                        label.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(None)
                    else:
                        entry = tk.Entry(table_frame, width=10, justify='center')
                        entry.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(entry)
            self.hall_table_entries.append(row_entries)
        
        # 按钮框架
        button_frame = tk.Frame(self.hall_frame)
        button_frame.pack(pady=5)
        
        # 计算按钮
        calc_btn = tk.Button(button_frame, text="计算灵敏度", 
                            command=self.calculate_hall_sensitivity,
                            font=("Arial", 10), bg='lightblue', width=10)
        calc_btn.pack(side=tk.LEFT, padx=5)
        
        # 清空数据按钮
        clear_btn = tk.Button(button_frame, text="清空数据", 
                            command=self.clear_hall_data,
                            font=("Arial", 10), bg='lightyellow', width=10)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出数据按钮
        export_btn = tk.Button(button_frame, text="导出数据", 
                            command=self.export_hall_data,
                            font=("Arial", 10), bg='lightgreen', width=10)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # 导入数据按钮
        import_btn = tk.Button(button_frame, text="导入数据", 
                            command=self.import_hall_data,
                            font=("Arial", 10), bg='lightcoral', width=10)
        import_btn.pack(side=tk.LEFT, padx=5)
        
        # 灵敏度显示
        sens_frame = tk.Frame(self.hall_frame)
        sens_frame.pack(pady=10)
        
        tk.Label(sens_frame, text="霍尔传感器灵敏度:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.hall_sensitivity = tk.StringVar(value="---")
        sens_label = tk.Label(sens_frame, textvariable=self.hall_sensitivity, 
                            font=("Arial", 10, "bold"), fg='blue')
        sens_label.pack(side=tk.LEFT, padx=10)
        tk.Label(sens_frame, text="mV/mm", font=("Arial", 10)).pack(side=tk.LEFT)

    def clear_hall_data(self):
        """清空霍尔传感器表格数据"""
        for i in range(1, 4):  # 第1-3行数据行
            for j in range(1, 7):  # 第1-6列
                # 注意：hall_table_entries[i] 的长度是7（包含索引0的None）
                # 但索引0是行标题，所以数据列从索引1开始
                if j < len(self.hall_table_entries[i]):
                    entry = self.hall_table_entries[i][j]
                    if entry:
                        entry.delete(0, tk.END)
        self.hall_sensitivity.set("---")
        messagebox.showinfo("提示", "霍尔传感器数据已清空")

    def export_hall_data(self):
        """导出霍尔传感器数据到CSV文件"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="保存霍尔传感器数据"
        )
        
        if filename:
            try:
                data = []
                # 表头行：第一列是"项目"，后面是序号1-6
                header = ["项目", "1", "2", "3", "4", "5", "6"]
                data.append(header)
                
                # M/g行：从索引1开始读取（跳过索引0的None）
                mg_row = ["M/g"]
                for col in range(1, 7):  # 索引1到6
                    entry = self.hall_table_entries[1][col]
                    if entry:
                        value = entry.get().strip()
                        mg_row.append(value if value else "")
                    else:
                        mg_row.append("")
                data.append(mg_row)
                
                # Z/mm行：从索引1开始读取
                z_row = ["Z/mm"]
                for col in range(1, 7):
                    entry = self.hall_table_entries[2][col]
                    if entry:
                        value = entry.get().strip()
                        z_row.append(value if value else "")
                    else:
                        z_row.append("")
                data.append(z_row)
                
                # U/mV行：从索引1开始读取
                u_row = ["U/mV"]
                for col in range(1, 7):
                    entry = self.hall_table_entries[3][col]
                    if entry:
                        value = entry.get().strip()
                        u_row.append(value if value else "")
                    else:
                        u_row.append("")
                data.append(u_row)
                
                # 写入CSV文件
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerows(data)
                
                messagebox.showinfo("提示", f"数据已导出到:\n{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def import_hall_data(self):
        """导入霍尔传感器数据从CSV文件"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="选择霍尔传感器数据文件"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                
                if len(rows) >= 4:
                    # 清空现有数据（索引1-6）
                    for i in range(1, 4):  # 行1-3
                        for j in range(1, 7):  # 列1-6
                            if j < len(self.hall_table_entries[i]):
                                entry = self.hall_table_entries[i][j]
                                if entry:
                                    entry.delete(0, tk.END)
                    
                    # 导入M/g数据（第2行，索引1）
                    if len(rows) >= 2 and len(rows[1]) >= 7:
                        for j in range(1, 7):
                            if j < len(rows[1]) and rows[1][j].strip():
                                self.hall_table_entries[1][j].insert(0, rows[1][j])
                    
                    # 导入Z/mm数据（第3行，索引2）
                    if len(rows) >= 3 and len(rows[2]) >= 7:
                        for j in range(1, 7):
                            if j < len(rows[2]) and rows[2][j].strip():
                                self.hall_table_entries[2][j].insert(0, rows[2][j])
                    
                    # 导入U/mV数据（第4行，索引3）
                    if len(rows) >= 4 and len(rows[3]) >= 7:
                        for j in range(1, 7):
                            if j < len(rows[3]) and rows[3][j].strip():
                                self.hall_table_entries[3][j].insert(0, rows[3][j])
                    
                    messagebox.showinfo("提示", f"数据已从文件导入:\n{filename}")
                else:
                    messagebox.showwarning("警告", "文件格式不正确")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")

    def calculate_hall_sensitivity(self):
        """计算霍尔传感器灵敏度"""
        try:
            # 获取位移数据(Z)和电压数据(U)
            z_values = []
            u_values = []
            
            for col in range(6):
                z_entry = self.hall_table_entries[2][col]  # Z/mm行（第3行，索引2）
                u_entry = self.hall_table_entries[3][col]  # U/mV行（第4行，索引3）
                
                if z_entry and u_entry and z_entry.get().strip() and u_entry.get().strip():
                    z = float(z_entry.get())
                    u = float(u_entry.get())
                    z_values.append(z)
                    u_values.append(u)
            
            if len(z_values) >= 2:
                # 使用线性回归计算灵敏度
                n = len(z_values)
                sum_z = sum(z_values)
                sum_u = sum(u_values)
                sum_zu = sum(z * u for z, u in zip(z_values, u_values))
                sum_z2 = sum(z**2 for z in z_values)
                
                # 斜率 = (n*sum_zu - sum_z*sum_u) / (n*sum_z2 - sum_z^2)
                denominator = n * sum_z2 - sum_z ** 2
                if denominator != 0:
                    sensitivity = (n * sum_zu - sum_z * sum_u) / denominator
                    self.hall_sensitivity.set(f"{sensitivity:.3f}")
                else:
                    self.hall_sensitivity.set("计算错误")
            else:
                self.hall_sensitivity.set("数据不足")
        except Exception as e:
            messagebox.showerror("错误", f"数据格式错误: {e}")
            self.hall_sensitivity.set("错误")
            
    def create_brass_tab(self):
        """创建黄铜样品选项卡"""
        # 表格框架
        table_frame = tk.Frame(self.brass_frame)
        table_frame.pack(pady=10)
        
        # 创建2行7列表格
        headers = ["", "1", "2", "3", "4", "5", "6"]
        row_headers = ["M/g", "Z/mm"]
        
        self.brass_table_entries = []
        
        for i in range(3):  # 3行 (包括表头)
            row_entries = []
            for j in range(7):
                if i == 0:  # 表头行
                    label = tk.Label(table_frame, text=headers[j], width=10,
                                    bg='lightgray', relief=tk.RAISED)
                    label.grid(row=i, column=j, padx=1, pady=1)
                else:  # 数据行
                    if j == 0:
                        label = tk.Label(table_frame, text=row_headers[i-1], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                        label.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(None)
                    else:
                        entry = tk.Entry(table_frame, width=10, justify='center')
                        entry.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(entry)
            if i > 0:
                self.brass_table_entries.append(row_entries)
        
        # 样品参数设置
        param_frame = tk.LabelFrame(self.brass_frame, text="样品参数设置", font=("Arial", 9))
        param_frame.pack(pady=10, padx=10, fill=tk.X)
        
        param_inner = tk.Frame(param_frame)
        param_inner.pack(pady=5)
        
        # 横梁长度 - 只读显示
        tk.Label(param_inner, text="横梁长度 d =", font=("Arial", 9)).grid(row=0, column=0, padx=5)
        d_label = tk.Label(param_inner, text="23.0", font=("Arial", 9), bg='lightgray', width=10, relief=tk.SUNKEN)
        d_label.grid(row=0, column=1, padx=2)
        tk.Label(param_inner, text="cm", font=("Arial", 9)).grid(row=0, column=2, padx=5)
        
        # 横梁宽度 - 只读显示
        tk.Label(param_inner, text="横梁宽度 b =", font=("Arial", 9)).grid(row=0, column=3, padx=5)
        b_label = tk.Label(param_inner, text="2.3", font=("Arial", 9), bg='lightgray', width=10, relief=tk.SUNKEN)
        b_label.grid(row=0, column=4, padx=2)
        tk.Label(param_inner, text="cm", font=("Arial", 9)).grid(row=0, column=5, padx=5)
        
        # 横梁厚度 - 只读显示
        tk.Label(param_inner, text="横梁厚度 a =", font=("Arial", 9)).grid(row=1, column=0, padx=5, pady=5)
        a_label = tk.Label(param_inner, text="0.995", font=("Arial", 9), bg='lightgray', width=10, relief=tk.SUNKEN)
        a_label.grid(row=1, column=1, padx=2)
        tk.Label(param_inner, text="mm", font=("Arial", 9)).grid(row=1, column=2, padx=5)
        
        # 按钮框架
        button_frame = tk.Frame(self.brass_frame)
        button_frame.pack(pady=5)
        
        # 计算按钮
        calc_btn = tk.Button(button_frame, text="计算杨氏模量", 
                            command=self.calculate_yang_modulus,
                            font=("Arial", 10), bg='lightgreen', width=12)
        calc_btn.pack(side=tk.LEFT, padx=5)
        
        # 清空数据按钮
        clear_btn = tk.Button(button_frame, text="清空数据", 
                            command=self.clear_brass_data,
                            font=("Arial", 10), bg='lightyellow', width=10)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出数据按钮
        export_btn = tk.Button(button_frame, text="导出数据", 
                            command=self.export_brass_data,
                            font=("Arial", 10), bg='lightgreen', width=10)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # 导入数据按钮
        import_btn = tk.Button(button_frame, text="导入数据", 
                            command=self.import_brass_data,
                            font=("Arial", 10), bg='lightcoral', width=10)
        import_btn.pack(side=tk.LEFT, padx=5)
        
        # 杨氏模量显示
        yang_frame = tk.Frame(self.brass_frame)
        yang_frame.pack(pady=10)

        tk.Label(yang_frame, text="黄铜样品的杨氏模量:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.yang_modulus = tk.StringVar(value="---")
        yang_label = tk.Label(yang_frame, textvariable=self.yang_modulus, 
                            font=("Arial", 10, "bold"), fg='red', width=15, anchor='w')
        yang_label.pack(side=tk.LEFT, padx=5)
        tk.Label(yang_frame, text="N/m²", font=("Arial", 10)).pack(side=tk.LEFT)

        # 误差显示（单独一栏）
        error_frame = tk.Frame(self.brass_frame)
        error_frame.pack(pady=5)

        tk.Label(error_frame, text="相对误差:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.error_percent = tk.StringVar(value="---")
        error_label = tk.Label(error_frame, textvariable=self.error_percent, 
                            font=("Arial", 10, "bold"), fg='orange', width=10, anchor='w')
        error_label.pack(side=tk.LEFT, padx=5)
        tk.Label(error_frame, text="%", font=("Arial", 10)).pack(side=tk.LEFT)

        # 理论值显示
        theory_frame = tk.Frame(self.brass_frame)
        theory_frame.pack(pady=5)

        tk.Label(theory_frame, text="理论值:", font=("Arial", 9)).pack(side=tk.LEFT)
        self.theory_value = tk.StringVar(value="1.055×10¹¹")
        theory_label = tk.Label(theory_frame, textvariable=self.theory_value, 
                                font=("Arial", 9, "bold"), fg='blue')
        theory_label.pack(side=tk.LEFT, padx=5)
        tk.Label(theory_frame, text="N/m²", font=("Arial", 9)).pack(side=tk.LEFT)

    def clear_brass_data(self):
        """清空黄铜样品表格数据"""
        for i in range(2):  # 2行数据行
            for j in range(1, 7):  # 第1-6列
                # brass_table_entries[i] 的长度是7（包含索引0的None）
                if j < len(self.brass_table_entries[i]):
                    entry = self.brass_table_entries[i][j]
                    if entry:
                        entry.delete(0, tk.END)
        self.yang_modulus.set("---")
        self.error_percent.set("---")
        messagebox.showinfo("提示", "黄铜样品数据已清空")

    def export_brass_data(self):
        """导出黄铜样品数据到CSV文件"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="保存黄铜样品数据"
        )
        
        if filename:
            try:
                data = []
                # 表头行
                header = ["项目", "1", "2", "3", "4", "5", "6"]
                data.append(header)
                
                # M/g行：从索引1开始读取
                mg_row = ["M/g"]
                for col in range(1, 7):
                    if col < len(self.brass_table_entries[0]):
                        entry = self.brass_table_entries[0][col]
                        if entry:
                            value = entry.get().strip()
                            mg_row.append(value if value else "")
                        else:
                            mg_row.append("")
                    else:
                        mg_row.append("")
                data.append(mg_row)
                
                # Z/mm行：从索引1开始读取
                z_row = ["Z/mm"]
                for col in range(1, 7):
                    if col < len(self.brass_table_entries[1]):
                        entry = self.brass_table_entries[1][col]
                        if entry:
                            value = entry.get().strip()
                            z_row.append(value if value else "")
                        else:
                            z_row.append("")
                    else:
                        z_row.append("")
                data.append(z_row)
                
                # 添加空行
                data.append([])
                
                # 样品参数
                data.append(["参数", "值", "单位"])
                data.append(["横梁长度 d", str(self.length.get()), "cm"])
                data.append(["横梁宽度 b", str(self.width.get()), "cm"])
                data.append(["横梁厚度 a", str(self.thickness.get()), "mm"])
                
                # 写入CSV文件
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerows(data)
                
                messagebox.showinfo("提示", f"数据已导出到:\n{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def import_brass_data(self):
        """导入黄铜样品数据从CSV文件"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="选择黄铜样品数据文件"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                
                if len(rows) >= 3:
                    # 清空现有数据（索引1-6）
                    for i in range(2):  # 2行数据行
                        for j in range(1, 7):  # 列1-6
                            if j < len(self.brass_table_entries[i]):
                                entry = self.brass_table_entries[i][j]
                                if entry:
                                    entry.delete(0, tk.END)
                    
                    # 导入M/g数据（第2行，索引1）
                    if len(rows) >= 2 and len(rows[1]) >= 7:
                        for j in range(1, 7):
                            if j < len(rows[1]) and rows[1][j].strip():
                                # 注意：brass_table_entries[0] 是 M/g 行
                                self.brass_table_entries[0][j].insert(0, rows[1][j])
                    
                    # 导入Z/mm数据（第3行，索引2）
                    if len(rows) >= 3 and len(rows[2]) >= 7:
                        for j in range(1, 7):
                            if j < len(rows[2]) and rows[2][j].strip():
                                # brass_table_entries[1] 是 Z/mm 行
                                self.brass_table_entries[1][j].insert(0, rows[2][j])
                    
                    # 导入样品参数（如果有）
                    for row in rows:
                        if len(row) >= 3:
                            if row[0] == "横梁长度 d" and row[1].strip():
                                self.length.set(float(row[1]))
                            elif row[0] == "横梁宽度 b" and row[1].strip():
                                self.width.set(float(row[1]))
                            elif row[0] == "横梁厚度 a" and row[1].strip():
                                self.thickness.set(float(row[1]))
                    
                    messagebox.showinfo("提示", f"数据已从文件导入:\n{filename}")
                else:
                    messagebox.showwarning("警告", f"文件格式不正确，需要至少3行数据，当前有{len(rows)}行")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")
            
    def calculate_yang_modulus(self):
        """计算黄铜样品的杨氏模量"""
        try:
            # 获取质量和位移数据
            masses = []  # g
            displacements = []  # mm
            
            for col in range(6):
                m_entry = self.brass_table_entries[0][col]
                z_entry = self.brass_table_entries[1][col]
                
                if m_entry and z_entry and m_entry.get().strip() and z_entry.get().strip():
                    m = float(m_entry.get())
                    z = float(z_entry.get())
                    masses.append(m)
                    displacements.append(z)
            
            if len(masses) < 2:
                self.yang_modulus.set("数据不足")
                self.error_percent.set("---")
                return
            
            # 单位转换
            # d: cm -> m (除以100)
            # b: cm -> m (除以100)
            # a: mm -> m (除以1000)
            d = self.length.get() / 100      # 23 cm = 0.23 m
            b = self.width.get() / 100       # 2.3 cm = 0.023 m
            a = self.thickness.get() / 1000  # 0.995 mm = 0.000995 m
            
            g = 9.8
            
            # 标准值（黄铜的杨氏模量）
            standard_value = 1.055e11  # 1.055 × 10^11 N/m²
            
            # 显示理论值（格式化显示）
            self.theory_value.set(f"{standard_value:.3e}")
            
            # 计算每一组数据的杨氏模量
            e_values = []
            
            for i in range(len(masses)):
                # 力: g -> kg -> N
                F = (masses[i] / 1000) * g
                # 位移: mm -> m
                z = displacements[i] / 1000
                
                if z != 0:
                    # 杨氏模量公式: E = (F * d^3) / (4 * b * a^3 * z)
                    e = (F * d**3) / (4 * b * a**3 * z)
                    e_values.append(e)
            
            if e_values:
                # 计算平均值
                average_e = sum(e_values) / len(e_values)
                
                # 计算相对误差
                relative_error = abs(average_e - standard_value) / standard_value * 100
                
                # 显示结果
                self.yang_modulus.set(f"{average_e:.3e}")
                self.error_percent.set(f"{relative_error:.2f}")
            else:
                self.yang_modulus.set("计算错误")
                self.error_percent.set("---")
                
        except Exception as e:
            messagebox.showerror("错误", f"数据格式错误: {e}")
            self.yang_modulus.set("错误")
            self.error_percent.set("---")
            
    def on_tab_changed(self, event):
        """选项卡切换事件"""
        selected = self.notebook.tab(self.notebook.select(), "text")
        self.current_tab = selected


def main():
    root = tk.Tk()
    app = YangsModulusApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()