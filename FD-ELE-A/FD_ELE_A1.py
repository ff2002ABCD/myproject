import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog  # 添加 simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
import sys
from PIL import Image, ImageTk
import openpyxl
import random

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ElectromagnetismExperiment:
    def __init__(self, parent):
        self.parent = parent
        self.root = parent.winfo_toplevel()
        
        # 标记当前显示的是哪个界面
        self.current_display = None
        
        # 电流方向标志
        self.current_direction = True
        self.current_direction_text = tk.StringVar(value="正向")
        # ===== 箭头标签引用 =====
        self.arrow_experiment = None      # 实验指示箭头（固定向右）
        self.arrow_excitation = None      # 励磁电流方向指示
        
        # 初始化数据
        self.init_data()
        
        # 加载Excel数据
        self.load_excel_data()
        
        # 创建主框架并立即显示（由主程序首次显示时pack）
        self.main_frame = tk.Frame(self.parent, bg='white')
        # 首次创建时pack，由主程序在show_solenoid_experiment中控制
        # 但为了确保子控件能正确创建，需要先pack再创建子控件
        # 或者先创建子控件再pack
        
        # 创建界面（子控件）
        self.create_ui()
        
        # 设置初始化随机偏移
        self.init_random_offsets()
        
        # 长按定时器
        self.hold_timer = None

    def create_ui(self):
        """创建UI界面"""
        # 确保主框架可见（首次创建时由主程序pack，但这里也做保障）
        # 注意：不要在每次切换时重复pack导致错误
        try:
            self.main_frame.pack(fill=tk.BOTH, expand=True)
        except:
            pass
        
        # 创建主布局
        self.create_main_layout()
        
        # 创建左侧实验装置区域
        self.create_left_area()
        
        # 创建右上实验操作区域
        self.create_right_top_area()
        
        # 创建右下数据记录区域
        self.create_right_bottom_area()
        
        # 初始化默认选择
        self.on_experiment_select()

    def on_show(self):
        """当实验被显示时调用"""
        # 确保主框架可见
        try:
            self.main_frame.pack(fill=tk.BOTH, expand=True)
        except:
            pass
        
        # 更新显示 - 添加安全检查
        try:
            self.update_magnetic_field()
        except:
            pass
        
        # 更新箭头
        try:
            self.update_arrows()
        except:
            pass
        
        try:
            # 检查当前显示的是哪个界面，只更新对应界面的图表
            if self.current_display == "ub_relation" or self.current_display is None:
                self.update_ub_plot()
            elif self.current_display == "position_relation":
                self.update_position_plot()
        except Exception as e:
            print(f"更新图表时出错: {e}")
    
    def get_resource_path(self, relative_path):
        """获取资源的绝对路径"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    def init_position_data(self):
        """初始化位置关系数据"""
        self.position_x_values = [""] * 30
        self.position_u1_values = [""] * 30
        self.position_u2_values = [""] * 30
        self.position_u_values = [""] * 30
        self.position_b_values = [""] * 30
        self.position_entries_x = []
        self.position_entries_u1 = []
        self.position_entries_u2 = []
        self.position_entries_u = []
        self.position_entries_b = []
        self.position_scroll_start = 0  # 当前滚动起始行

    def init_random_offsets(self):
        """初始化时给电压和毫特计添加随机偏移"""
        # 电压偏移 (-10, 10) 范围
        self.voltage_offset = random.uniform(-10, 10)
        # 毫特计偏移 (-10, 10) 范围
        self.millitesla_offset = random.uniform(-10, 10)
        
        # 注意：不更新进度条，只保存偏移值用于显示计算
        
        # 更新显示（如果控件已创建）
        if hasattr(self, 'voltage_var'):
            self.update_voltage_display()
        if hasattr(self, 'millitesla_var'):
            self.update_millitesla_display()
        # if hasattr(self, 'voltage_var') and hasattr(self, 'millitesla_var'):
        #     self.update_magnetic_field()
        
        print(f"初始化随机偏移: 电压偏移={self.voltage_offset:.2f}mV, 毫特计偏移={self.millitesla_offset:.2f}mT")

    def init_data(self):
        """初始化数据"""
        # U-B关系表格数据
        self.ub_current_values = [""] * 9
        self.ub_voltage_values = [""] * 9
        
        # 位置-B关系表格数据
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
        
        # 各参数的当前值
        self.current_position = 0.0
        self.current_current = 0
        self.user_position_input = 0.0  # 用户手动输入的螺线管位置X
        
        # 存储从Excel读取的数据
        self.excel_data = []  # 存储 [(x, u1, u2), ...]
        
        # 位置关系数据
        self.position_x_values = [""] * 30
        self.position_u1_values = [""] * 30
        self.position_u2_values = [""] * 30
        self.position_u_values = [""] * 30
        self.position_b_values = [""] * 30
        self.position_scroll_start = 0
    
    def load_excel_data(self):
        """从Excel文件读取螺线管位置与电压数据"""
        try:
            excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "螺线管U-X(250MA).xlsx")
            if not os.path.exists(excel_path):
                print(f"Excel文件不存在: {excel_path}")
                return False
            
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            ws = wb.active
            
            self.excel_data = []
            for row in ws.iter_rows(min_row=2, values_only=True):  # 从第二行开始
                if row[0] is not None and row[1] is not None and row[2] is not None:
                    self.excel_data.append((float(row[0]), float(row[1]), float(row[2])))
            
            # 按X排序
            self.excel_data.sort(key=lambda x: x[0])
            print(f"成功加载 {len(self.excel_data)} 条数据")
            return True
        except Exception as e:
            print(f"加载Excel数据失败: {e}")
            return False

    def interpolate_voltage(self, position, is_forward):
        """根据位置插值查询电压
        position: 螺线管位置 (cm)
        is_forward: True为正向，False为反向
        返回: 插值后的电压值 (mV)
        """
        if not self.excel_data:
            return 0.0
        
        # 如果数据点少于2个，无法插值
        if len(self.excel_data) < 2:
            return 0.0
        
        # 获取数据列索引: 正向用U1(索引1)，反向用U2(索引2)
        col_idx = 1 if is_forward else 2
        
        # 如果位置超出范围，返回最近点的值
        if position <= self.excel_data[0][0]:
            return self.excel_data[0][col_idx]
        if position >= self.excel_data[-1][0]:
            return self.excel_data[-1][col_idx]
        
        # 找到相邻两个数据点进行线性插值
        for i in range(len(self.excel_data) - 1):
            x1 = self.excel_data[i][0]
            x2 = self.excel_data[i + 1][0]
            if x1 <= position <= x2:
                y1 = self.excel_data[i][col_idx]
                y2 = self.excel_data[i + 1][col_idx]
                # 线性插值
                t = (position - x1) / (x2 - x1) if (x2 - x1) != 0 else 0
                return y1 + t * (y2 - y1)
        
        return 0.0

    
    def create_main_layout(self):
        """创建主布局"""
        # 主要内容框架 - 不创建顶部框架
        main_content = tk.Frame(self.main_frame)
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
        pass
        
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
            self.canvas.create_rectangle(0, 0, 680, 700, fill='lightgray')
            self.canvas.create_text(340, 350, text="螺线管图片加载失败", font=("Arial", 14))
        
        # 加载并叠加刻度图片 - 添加tags
        try:
            scale_img_path = self.get_resource_path("background/刻度.jpg")
            pil_scale = Image.open(scale_img_path)
            pil_scale = pil_scale.resize((700, 40), Image.Resampling.LANCZOS)
            self.scale_image = ImageTk.PhotoImage(pil_scale)
            self.canvas.create_image(578, 50, anchor=tk.NW, image=self.scale_image, tags="scale_bg")
            print("刻度图片加载成功")
        except Exception as e:
            print(f"无法加载刻度图片: {e}")

        # 加载并叠加遮盖图片
        try:
            zhegai_img_path = self.get_resource_path("background/遮盖.png")
            zhegai_scale = Image.open(zhegai_img_path)
            zhegai_scale = zhegai_scale.resize((563, 87), Image.Resampling.LANCZOS)
            self.zhegai_image = ImageTk.PhotoImage(zhegai_scale)
            self.canvas.create_image(0, 26, anchor=tk.NW, image=self.zhegai_image)
            print("遮盖图片加载成功")
        except Exception as e:
            print(f"无法加载遮盖图片: {e}")

        # 在x=578位置画红色竖线
        self.canvas.create_line(575, 40, 575, 100, fill='red', width=2, tags="red_line")
        
        # 创建文本框叠加在图片上
        self.create_textboxes_on_image()
        
        # ===== 创建箭头指示标签 =====
        self.create_arrow_indicators()
    
    def create_arrow_indicators(self):
        """在图片上创建箭头指示标签"""
        
        # ===== 1. 实验指示箭头（固定向右） =====
        # 位置：在螺线管图片右侧空白区域
        self.arrow_experiment = self.canvas.create_text(
            160, 610,          # 位置在螺线管右侧
            text="→",          # 固定向右
            font=("Arial", 32, "bold"),
            fill="#FF6B00",    # 橙色
            tags="arrow_experiment"
        )
        
        # ===== 2. 励磁电流方向指示 =====
        # 位置：电流表附近，显示向左或向右的箭头
        self.arrow_excitation = self.canvas.create_text(
            157, 130,          # 电流表下方位置
            text="←",          # 默认向右，后续更新
            font=("Arial", 32, "bold"),
            fill="red",
            tags="arrow_excitation"
        )

    def update_arrows(self):
        """更新所有箭头指示标签"""
        try:
            # ===== 1. 更新励磁电流方向 =====
            if hasattr(self, 'arrow_excitation') and self.arrow_excitation:
                if self.current_direction:
                    # 正向 → 显示向左的箭头（电流从左向右流）
                    self.canvas.itemconfig(self.arrow_excitation, text="←")
                else:
                    # 反向 → 显示向右的箭头（电流从右向左流）
                    self.canvas.itemconfig(self.arrow_excitation, text="→")
            
            # 实验指示箭头固定向右，不需要更新
                    
        except (tk.TclError, RuntimeError):
            # 箭头可能还未创建，忽略错误
            pass

    def create_textboxes_on_image(self):
        """在图片上创建文本框"""
        # 电压表文本框 - 显示实际电压（包含调零），设置为只读
        self.voltage_var = tk.StringVar(value="0")
        voltage_entry = tk.Entry(self.left_frame, textvariable=self.voltage_var, 
                                width=8, font=("Arial", 10), justify='center',
                                state='readonly', readonlybackground='white')
        self.canvas.create_window(85, 535, window=voltage_entry, anchor=tk.NW)
        
        # 电流表文本框 - 显示电流值，设置为只读
        self.current_var = tk.StringVar(value="0")
        current_entry = tk.Entry(self.left_frame, textvariable=self.current_var,
                                width=8, font=("Arial", 10), justify='center',
                                state='readonly', readonlybackground='white')
        self.canvas.create_window(265, 535, window=current_entry, anchor=tk.NW)
        
        # # 毫特计文本框 - 显示实际磁感应强度（包含调零），设置为只读
        # self.millitesla_var = tk.StringVar(value="0")
        # millitesla_entry = tk.Entry(self.left_frame, textvariable=self.millitesla_var,
        #                             width=8, font=("Arial", 10), justify='center',
        #                             state='readonly', readonlybackground='white')
        # self.canvas.create_window(410, 535, window=millitesla_entry, anchor=tk.NW)
    
    def create_hold_button(self, parent, text, command, repeat_delay=300, repeat_interval=50):
        """创建一个支持长按重复触发的按钮"""
        button = tk.Button(parent, text=text, width=2)
        
        def on_press(event):
            # 首次点击执行一次
            command()
            # 取消之前的定时器
            self.cancel_hold_timer()
            # 启动长按定时器
            self.hold_timer = self.root.after(repeat_delay, lambda: self.start_repeat(command, repeat_interval))
        
        def on_release(event):
            self.cancel_hold_timer()
        
        button.bind("<ButtonPress-1>", on_press)
        button.bind("<ButtonRelease-1>", on_release)
        # 当鼠标离开按钮时也停止重复
        button.bind("<Leave>", on_release)
        
        return button
    
    def cancel_hold_timer(self):
        """取消长按定时器"""
        if self.hold_timer is not None:
            self.root.after_cancel(self.hold_timer)
            self.hold_timer = None
    
    def start_repeat(self, command, interval):
        """开始重复执行命令"""
        command()
        self.hold_timer = self.root.after(interval, lambda: self.start_repeat(command, interval))
    
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
                                    length=200, resolution=0.1, command=self.update_position)
        self.position_scale.pack(side=tk.LEFT, padx=5)
        # 添加长按支持的+-微调按钮
        btn_minus_pos = self.create_hold_button(position_frame, "-", 
                                                lambda: self.adjust_position(-0.1))
        btn_minus_pos.pack(side=tk.LEFT, padx=1)
        btn_plus_pos = self.create_hold_button(position_frame, "+",
                                               lambda: self.adjust_position(0.1))
        btn_plus_pos.pack(side=tk.LEFT, padx=1)
        
        # 第1行第2列：励磁电流进度条
        current_frame = tk.Frame(main_frame, bg='lightyellow')
        current_frame.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        tk.Label(current_frame, text="励磁电流(mA):", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.current_scale = tk.Scale(current_frame, from_=0, to=500, orient=tk.HORIZONTAL,
                                    length=200, command=self.update_current)
        self.current_scale.pack(side=tk.LEFT, padx=5)
        # 添加长按支持的+-微调按钮
        btn_minus_cur = self.create_hold_button(current_frame, "-",
                                                lambda: self.adjust_current(-1))
        btn_minus_cur.pack(side=tk.LEFT, padx=1)
        btn_plus_cur = self.create_hold_button(current_frame, "+",
                                               lambda: self.adjust_current(1))
        btn_plus_cur.pack(side=tk.LEFT, padx=1)
        
        # 电流方向切换按钮（放在励磁电流同一行右侧）
        self.direction_btn = tk.Button(current_frame, textvariable=self.current_direction_text,
                                       command=self.toggle_current_direction,
                                       width=6, bg='lightblue')
        self.direction_btn.pack(side=tk.LEFT, padx=10)
        
        # 第2行第1列：电压表调零进度条
        voltage_offset_frame = tk.Frame(main_frame, bg='lightyellow')
        voltage_offset_frame.grid(row=1, column=0, padx=10, pady=10, sticky='w')
        tk.Label(voltage_offset_frame, text="电压表调零(mV):", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.voltage_offset_scale = tk.Scale(voltage_offset_frame, from_=-50, to=50, orient=tk.HORIZONTAL,
                                            length=200, resolution=0.1,showvalue=0, command=self.update_voltage_offset)
        self.voltage_offset_scale.pack(side=tk.LEFT, padx=5)
        # 添加长按支持的+-微调按钮
        btn_minus_voff = self.create_hold_button(voltage_offset_frame, "-",
                                                 lambda: self.adjust_voltage_offset(-0.1))
        btn_minus_voff.pack(side=tk.LEFT, padx=1)
        btn_plus_voff = self.create_hold_button(voltage_offset_frame, "+",
                                                lambda: self.adjust_voltage_offset(0.1))
        btn_plus_voff.pack(side=tk.LEFT, padx=1)
       
        
        # # 第2行第2列：毫特计调零进度条
        # millitesla_offset_frame = tk.Frame(main_frame, bg='lightyellow')
        # millitesla_offset_frame.grid(row=1, column=1, padx=10, pady=10, sticky='w')
        # tk.Label(millitesla_offset_frame, text="毫特计调零(mT):", bg='lightyellow',
        #         font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        # self.millitesla_offset_scale = tk.Scale(millitesla_offset_frame, from_=-50, to=50, orient=tk.HORIZONTAL,
        #                                         length=200, showvalue=0, resolution=0.1, command=self.update_millitesla_offset)
        # self.millitesla_offset_scale.pack(side=tk.LEFT, padx=5)
        # # 添加长按支持的+-微调按钮
        # btn_minus_moff = self.create_hold_button(millitesla_offset_frame, "-",
        #                                          lambda: self.adjust_millitesla_offset(-0.1))
        # btn_minus_moff.pack(side=tk.LEFT, padx=1)
        # btn_plus_moff = self.create_hold_button(millitesla_offset_frame, "+",
        #                                         lambda: self.adjust_millitesla_offset(0.1))
        # btn_plus_moff.pack(side=tk.LEFT, padx=1)
    
    
        # 配置列权重，使布局更均匀
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
    
    # ---------- 微调按钮回调函数 ----------
    def adjust_position(self, delta):
        """调整位置值"""
        new_val = self.current_position + delta
        new_val = max(0, min(30, round(new_val, 1)))  # 限制范围并保留1位小数
        self.current_position = new_val
        self.position_scale.set(new_val)
        self.update_magnetic_field()
    
    def adjust_current(self, delta):
        """调整电流值"""
        new_val = self.current_current + delta
        new_val = max(0, min(500, new_val))  # 限制范围
        self.current_current = new_val
        self.current_scale.set(new_val)
        self.current_var.set(str(new_val))
        self.update_magnetic_field()
    
    def adjust_voltage_offset(self, delta):
        """调整电压表调零"""
        new_val = self.voltage_offset + delta
        new_val = max(-50, min(50, new_val))
        self.voltage_offset = new_val
        if hasattr(self, 'voltage_offset_scale'):
            self.voltage_offset_scale.set(new_val)
        self.update_voltage_display()
        self.update_magnetic_field()

    # def adjust_millitesla_offset(self, delta):
    #     """调整毫特计调零"""
    #     new_val = self.millitesla_offset + delta
    #     new_val = max(-50, min(50, new_val))
    #     self.millitesla_offset = new_val
    #     if hasattr(self, 'millitesla_offset_scale'):
    #         self.millitesla_offset_scale.set(new_val)
    #     self.update_millitesla_display()
    #     self.update_magnetic_field()
    
    # ---------- 电流方向切换 ----------
    def toggle_current_direction(self):
        """切换电流方向"""
        self.current_direction = not self.current_direction
        if self.current_direction:
            self.current_direction_text.set("正向")
            self.direction_btn.config(bg='lightblue')
        else:
            self.current_direction_text.set("反向")
            self.direction_btn.config(bg='lightcoral')
        # 更新显示
        self.update_magnetic_field()
        self.update_arrows()  # ← 添加这行
    
    def create_right_bottom_area(self):
        """创建右下数据记录区域"""
        # 内部选项卡
        self.data_tab_frame = tk.Frame(self.right_bottom_frame)
        self.data_tab_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建选项卡按钮并保存引用
        self.btn_ub = tk.Button(self.data_tab_frame, text="霍尔传感器电压U与磁感应强度B的关系",
                                command=lambda: self.show_ub_relation(),
                                width=35, bg='lightblue')
        self.btn_ub.pack(side=tk.LEFT, padx=5)
        
        self.btn_position = tk.Button(self.data_tab_frame, text="螺线管内磁感应强度B与位置刻度X的关系",
                                    command=lambda: self.show_position_relation(),
                                    width=35)
        self.btn_position.pack(side=tk.LEFT, padx=5)
        
        # 内容框架 - 使用水平布局
        self.bottom_content_frame = tk.Frame(self.right_bottom_frame, bg='white')
        self.bottom_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧曲线图框架
        self.plot_frame = tk.Frame(self.bottom_content_frame, bg='white')
        self.plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 右侧参数显示框架
        self.params_frame = tk.Frame(self.bottom_content_frame, bg='lightgray', width=200)
        self.params_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        self.params_frame.pack_propagate(False)  # 固定宽度
        
        # 在右侧框架中显示参数
        self.create_params_display()
        
        # 初始显示U-B关系界面
        self.show_ub_relation()
    
    def create_params_display(self):
        """创建右侧参数显示区域"""
        # 清空原有内容
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        # 实验参数（U-B关系使用）
        self.params_fit_frame = tk.Frame(self.params_frame, bg='lightgray')
        # 默认显示
        self.params_fit_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(self.params_fit_frame, text="=== 实验参数 ===", font=("Arial", 10, "bold"), 
                bg='lightgray').pack(pady=(10, 5))
        
        tk.Label(self.params_fit_frame, text="N = 3000 匝", font=("Arial", 9), 
                bg='lightgray').pack(pady=2)
        tk.Label(self.params_fit_frame, text="L = 26 cm", font=("Arial", 9), 
                bg='lightgray').pack(pady=2)
        tk.Label(self.params_fit_frame, text="D = 35 mm", font=("Arial", 9), 
                bg='lightgray').pack(pady=2)
        
        # 螺线管位置X输入
        pos_frame = tk.Frame(self.params_fit_frame, bg='lightgray')
        pos_frame.pack(pady=5)
        tk.Label(pos_frame, text="位置 X =", font=("Arial", 9), bg='lightgray').pack(side=tk.LEFT)
        self.position_entry = tk.Entry(pos_frame, width=8, font=("Arial", 9), justify='center')
        self.position_entry.pack(side=tk.LEFT, padx=3)
        self.position_entry.insert(0, "0.0")
        tk.Label(pos_frame, text="cm", font=("Arial", 9), bg='lightgray').pack(side=tk.LEFT)
        
        # 分隔线
        tk.Frame(self.params_fit_frame, height=2, bg='gray').pack(fill=tk.X, pady=10)
        
        # 拟合结果
        tk.Label(self.params_fit_frame, text="=== 拟合结果 ===", font=("Arial", 10, "bold"), 
                bg='lightgray').pack(pady=(0, 5))
        
        # 斜率k
        k_frame = tk.Frame(self.params_fit_frame, bg='lightgray')
        k_frame.pack(pady=2)
        tk.Label(k_frame, text="斜率 k =", font=("Arial", 9), bg='lightgray').pack(side=tk.LEFT)
        self.k_label = tk.Label(k_frame, text="0.0000", font=("Arial", 9, "bold"), 
                                fg='blue', bg='lightgray')
        self.k_label.pack(side=tk.LEFT)
        tk.Label(k_frame, text="mV/mA", font=("Arial", 9), bg='lightgray').pack(side=tk.LEFT)
        
        # 霍尔传感器灵敏度K
        k_sensitivity_frame = tk.Frame(self.params_fit_frame, bg='lightgray')
        k_sensitivity_frame.pack(pady=5)
        tk.Label(k_sensitivity_frame, text="霍尔灵敏度 K =", font=("Arial", 9), 
                bg='lightgray').pack(side=tk.LEFT)
        self.k_sensitivity_label = tk.Label(k_sensitivity_frame, text="0.00", 
                                            font=("Arial", 9, "bold"), fg='red', bg='lightgray')
        self.k_sensitivity_label.pack(side=tk.LEFT)
        tk.Label(k_sensitivity_frame, text="V/T", font=("Arial", 9), 
                bg='lightgray').pack(side=tk.LEFT)
        
        # 位置关系参数（默认隐藏）
        self.params_position_frame = tk.Frame(self.params_frame, bg='lightgray')
        # 不pack，默认隐藏
        
        tk.Label(self.params_position_frame, text="=== 实验参数 ===", font=("Arial", 10, "bold"), 
                bg='lightgray').pack(pady=(10, 5))
        
        tk.Label(self.params_position_frame, text="N = 3000 匝", font=("Arial", 9), 
                bg='lightgray').pack(pady=2)
        tk.Label(self.params_position_frame, text="L = 26 cm", font=("Arial", 9), 
                bg='lightgray').pack(pady=2)
        tk.Label(self.params_position_frame, text="D = 35 mm", font=("Arial", 9), 
                bg='lightgray').pack(pady=2)
        
        # 励磁电流I输入
        current_input_frame = tk.Frame(self.params_position_frame, bg='lightgray')
        current_input_frame.pack(pady=5)
        tk.Label(current_input_frame, text="励磁电流 I =", font=("Arial", 9), bg='lightgray').pack(side=tk.LEFT)
        self.position_current_entry = tk.Entry(current_input_frame, width=8, font=("Arial", 9), justify='center')
        self.position_current_entry.pack(side=tk.LEFT, padx=3)
        self.position_current_entry.insert(0, "250")
        tk.Label(current_input_frame, text="mA", font=("Arial", 9), bg='lightgray').pack(side=tk.LEFT)
        
        # 中心磁感应强度理论值 (显示为 B₀ = 3.592/250*I)
        b0_frame = tk.Frame(self.params_position_frame, bg='lightgray')
        b0_frame.pack(pady=5)
        tk.Label(b0_frame, text="B₀ =", font=("Arial", 9), bg='lightgray').pack(side=tk.LEFT)
        self.b0_label = tk.Label(b0_frame, text="3.592", font=("Arial", 9, "bold"), 
                                fg='green', bg='lightgray')
        self.b0_label.pack(side=tk.LEFT)
        tk.Label(b0_frame, text="mT", font=("Arial", 9), bg='lightgray').pack(side=tk.LEFT)

    def record_ub_data(self):
        """记录当前电压电流到U-B表格"""
        if not hasattr(self, 'ub_current_entries') or not self.ub_current_entries:
            messagebox.showwarning("警告", "表格未初始化！")
            return
        
        # 获取当前电流和电压
        current = self.current_current
        # 获取当前显示的电压值（含调零偏移）
        try:
            voltage_str = self.voltage_var.get()
            voltage = float(voltage_str)
        except ValueError:
            voltage = 0.0
        
        # 查找第一个空行
        empty_index = -1
        for i in range(9):
            current_val = self.ub_current_entries[i].get().strip()
            voltage_val = self.ub_voltage_entries[i].get().strip()
            if not current_val and not voltage_val:
                empty_index = i
                break
        
        if empty_index == -1:
            messagebox.showwarning("警告", "表格已满（9行已全部有数据）！")
            return
        
        # 填入数据
        self.ub_current_entries[empty_index].delete(0, tk.END)
        self.ub_current_entries[empty_index].insert(0, f"{current:.0f}")
        self.ub_current_values[empty_index] = f"{current:.0f}"
        
        self.ub_voltage_entries[empty_index].delete(0, tk.END)
        self.ub_voltage_entries[empty_index].insert(0, f"{voltage:.1f}")
        self.ub_voltage_values[empty_index] = f"{voltage:.1f}"
        
        # 更新曲线图
        self.update_ub_plot()
        

    def show_ub_relation(self):
        """显示U-B关系界面 - 保留数据"""
        # 更新选项卡按钮高亮
        if hasattr(self, 'btn_ub'):
            self.btn_ub.config(bg='lightblue')
        if hasattr(self, 'btn_position'):
            self.btn_position.config(bg='SystemButtonFace')
        
        # 如果是第一次创建或者需要切换，才重建界面
        if self.current_display == "ub_relation" and hasattr(self, 'plot_frame') and self.plot_frame.winfo_children():
            return  # 已经是这个界面且有内容，不需要切换
        
        # 如果当前显示的是位置关系界面，保存数据
        if self.current_display == "position_relation":
            self.save_position_data()
        
        # 清空plot_frame内容
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        # 显示拟合结果框架，隐藏位置参数框架
        if hasattr(self, 'params_fit_frame'):
            self.params_fit_frame.pack(fill=tk.X, pady=5)
        if hasattr(self, 'params_position_frame'):
            self.params_position_frame.pack_forget()
        
        # 按钮框架
        button_frame = tk.Frame(self.plot_frame)
        button_frame.pack(pady=10)
        
        buttons = [
            ("记录数据", self.record_ub_data),
            ("计算", self.calculate_ub),
            ("清空数据", self.clear_ub_data),
            ("导出数据", self.export_ub_data),
            ("导入数据", self.import_ub_data)
        ]
        
        for text, command in buttons:
            btn = tk.Button(button_frame, text=text, command=command, 
                        width=12, bg='lightblue')
            btn.pack(side=tk.LEFT, padx=5)

        # 创建表格
        table_frame = tk.Frame(self.plot_frame)
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
        self.create_ub_plot()
        
        
        
        self.current_display = "ub_relation"
        
        # 更新曲线图
        self.update_ub_plot()
    
    def delete_selected_position_row(self):
        """删除选中的位置关系行（光标所在行）"""
        if not hasattr(self, 'position_entries_x') or not self.position_entries_x:
            messagebox.showwarning("警告", "表格未初始化！")
            return
        
        # 获取当前选中的行
        row_index = self.selected_position_row
        
        if row_index < 0 or row_index >= 30:
            messagebox.showwarning("警告", "请先点击选中要删除的行！")
            return
        
        # 检查该行是否有数据
        x_val = self.position_entries_x[row_index].get().strip()
        u1_val = self.position_entries_u1[row_index].get().strip()
        u2_val = self.position_entries_u2[row_index].get().strip()
        
        if not x_val and not u1_val and not u2_val:
            messagebox.showwarning("警告", f"第{row_index+1}行没有数据！")
            return
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除第{row_index+1}行的数据吗？"):
            return
        
        # 清空该行所有数据
        self.position_entries_x[row_index].delete(0, tk.END)
        self.position_x_values[row_index] = ""
        
        self.position_entries_u1[row_index].delete(0, tk.END)
        self.position_u1_values[row_index] = ""
        
        self.position_entries_u2[row_index].delete(0, tk.END)
        self.position_u2_values[row_index] = ""
        
        self.position_entries_u[row_index].config(state='normal')
        self.position_entries_u[row_index].delete(0, tk.END)
        self.position_entries_u[row_index].config(state='readonly')
        self.position_u_values[row_index] = ""
        
        self.position_entries_b[row_index].config(state='normal')
        self.position_entries_b[row_index].delete(0, tk.END)
        self.position_entries_b[row_index].config(state='readonly')
        self.position_b_values[row_index] = ""
        
        # 清除高亮
        self.position_entries_x[row_index].config(bg='white')
        self.position_entries_u1[row_index].config(bg='white')
        self.position_entries_u2[row_index].config(bg='white')
        self.position_entries_u[row_index].config(bg='white')
        self.position_entries_b[row_index].config(bg='white')
        self.selected_position_row = -1
        
        # 更新曲线图
        self.update_position_plot()
        
        messagebox.showinfo("删除成功", f"已删除第{row_index+1}行数据")

    # 在 update_voltage_display 方法之后添加这个方法

    def get_displayed_voltage(self):
        """获取当前显示的电压值（包含调零偏移）"""
        measured_voltage = self.get_current_voltage()
        return measured_voltage + self.voltage_offset

    # 修改 record_position_data 方法
    def record_position_data(self):
        """记录当前螺线管位置和电压到表格 - 如果X相同则更新同一行"""
        if not hasattr(self, 'position_entries_x') or not self.position_entries_x:
            messagebox.showwarning("警告", "表格未初始化！")
            return
        
        # 获取当前参数
        position = self.current_position
        # 使用包含调零偏移的显示电压（与左侧电压表显示一致）
        voltage = self.get_displayed_voltage()
        
        # 判断当前方向：正向记录到U1，反向记录到U2
        is_forward = self.current_direction
        
        # ===== 先检查是否已存在相同X值的行 =====
        existing_index = -1
        for i in range(30):
            x_val = self.position_entries_x[i].get().strip()
            if x_val and abs(float(x_val) - position) < 0.01:  # 浮点数比较
                existing_index = i
                break
        
        if existing_index >= 0:
            # 更新已有行
            row_index = existing_index
            # 根据方向填入U1或U2
            if is_forward:
                self.position_entries_u1[row_index].delete(0, tk.END)
                self.position_entries_u1[row_index].insert(0, f"{voltage:.1f}")
                self.position_u1_values[row_index] = f"{voltage:.1f}"
                direction_text = "正向"
            else:
                self.position_entries_u2[row_index].delete(0, tk.END)
                self.position_entries_u2[row_index].insert(0, f"{voltage:.1f}")
                self.position_u2_values[row_index] = f"{voltage:.1f}"
                direction_text = "反向"
            
            action_text = "更新"
        else:
            # 查找第一个空行（X为空的行）
            empty_index = -1
            for i in range(30):
                x_val = self.position_entries_x[i].get().strip()
                if not x_val:
                    empty_index = i
                    break
            
            if empty_index == -1:
                messagebox.showwarning("警告", "表格已满（30行全部有数据）！")
                return
            
            row_index = empty_index
            
            # 填入位置X
            self.position_entries_x[row_index].delete(0, tk.END)
            self.position_entries_x[row_index].insert(0, f"{position:.1f}")
            self.position_x_values[row_index] = f"{position:.1f}"
            
            # 根据方向填入U1或U2
            if is_forward:
                self.position_entries_u1[row_index].delete(0, tk.END)
                self.position_entries_u1[row_index].insert(0, f"{voltage:.1f}")
                self.position_u1_values[row_index] = f"{voltage:.1f}"
                direction_text = "正向"
            else:
                self.position_entries_u2[row_index].delete(0, tk.END)
                self.position_entries_u2[row_index].insert(0, f"{voltage:.1f}")
                self.position_u2_values[row_index] = f"{voltage:.1f}"
                direction_text = "反向"
            
            action_text = "添加"
        
        # 自动计算该行的U和B值
        try:
            K = 31.11  # V/T
            u1_val = float(self.position_entries_u1[row_index].get().strip()) if self.position_entries_u1[row_index].get().strip() else 0
            u2_val = float(self.position_entries_u2[row_index].get().strip()) if self.position_entries_u2[row_index].get().strip() else 0
            u = (u1_val - u2_val) / 2
            b = u / K
            
            # 更新U列
            self.position_entries_u[row_index].config(state='normal')
            self.position_entries_u[row_index].delete(0, tk.END)
            self.position_entries_u[row_index].insert(0, f"{u:.1f}")
            self.position_entries_u[row_index].config(state='readonly')
            self.position_u_values[row_index] = f"{u:.1f}"
            
            # 更新B列
            self.position_entries_b[row_index].config(state='normal')
            self.position_entries_b[row_index].delete(0, tk.END)
            self.position_entries_b[row_index].insert(0, f"{b:.3f}")
            self.position_entries_b[row_index].config(state='readonly')
            self.position_b_values[row_index] = f"{b:.3f}"
        except ValueError:
            pass
        
        # 更新曲线图
        self.update_position_plot()
        
        # 显示提示
        messagebox.showinfo("记录成功", f"{action_text}: X={position:.1f}cm, {direction_text} U={voltage:.1f}mV")

    def show_position_relation(self):
        """显示位置-B关系界面"""
        # 更新选项卡按钮高亮
        if hasattr(self, 'btn_position'):
            self.btn_position.config(bg='lightblue')
        if hasattr(self, 'btn_ub'):
            self.btn_ub.config(bg='SystemButtonFace')
        
        if self.current_display == "position_relation":
            return
        
        # 保存U-B数据
        self.save_ub_data()
        
        # 清空plot_frame内容
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        # 隐藏拟合结果框架，显示位置参数框架
        if hasattr(self, 'params_fit_frame'):
            self.params_fit_frame.pack_forget()
        if hasattr(self, 'params_position_frame'):
            self.params_position_frame.pack(fill=tk.X, pady=5)
        
        # 清除U-B关系界面的实验参数（拟合结果）
        try:
            if hasattr(self, 'sensitivity_label') and self.sensitivity_label is not None:
                try:
                    self.sensitivity_label.config(text="0.00")
                except tk.TclError:
                    pass
        except:
            pass
        try:
            if hasattr(self, 'k_label') and self.k_label is not None:
                try:
                    self.k_label.config(text="0.0000")
                except tk.TclError:
                    pass
        except:
            pass
        try:
            if hasattr(self, 'k_sensitivity_label') and self.k_sensitivity_label is not None:
                try:
                    self.k_sensitivity_label.config(text="0.00")
                except tk.TclError:
                    pass
        except:
            pass
        self.sensitivity = 0
        
        # 按钮框架
        button_frame = tk.Frame(self.plot_frame)
        button_frame.pack(pady=10)
        
        buttons = [
            ("记录数据", self.record_position_data),
            ("计算", self.calculate_position),
            ("删除选中行", self.delete_selected_position_row),
            ("清空数据", self.clear_position_data),
            ("导出数据", self.export_position_data),
            ("导入数据", self.import_position_data)
        ]
        
        for text, command in buttons:
            btn = tk.Button(button_frame, text=text, command=command, 
                        width=12, bg='lightblue')
            btn.pack(side=tk.LEFT, padx=5)

        # 创建位置关系表格（带滚动条）
        self.create_position_table()
        
        
        # 创建曲线图
        self.create_position_plot()
        
        
        
        self.current_display = "position_relation"
        
        # 更新曲线图
        self.update_position_plot()
        
    def create_ub_plot(self):
        """创建U-B关系曲线图"""
        plot_canvas_frame = tk.Frame(self.plot_frame)
        plot_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=0)
        
        self.fig, self.ax = plt.subplots(figsize=(2, 2))
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=plot_canvas_frame)
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.ax.set_xlabel('Im (mA)')
        self.ax.set_ylabel('U (mV)')
        self.ax.set_title('霍尔传感器电压U与电流Im的关系')
        self.ax.grid(True)
    
    def select_position_row(self, row_index):
        """选择指定行，高亮显示"""
        # 清除之前的高亮
        if self.selected_position_row >= 0:
            old_row = self.selected_position_row
            # 恢复所有列的背景色
            self.position_entries_x[old_row].config(bg='white')
            self.position_entries_u1[old_row].config(bg='white')
            self.position_entries_u2[old_row].config(bg='white')
            self.position_entries_u[old_row].config(bg='white')
            self.position_entries_b[old_row].config(bg='white')
        
        # 高亮新选中的行
        self.selected_position_row = row_index
        self.position_entries_x[row_index].config(bg='lightblue')
        self.position_entries_u1[row_index].config(bg='lightblue')
        self.position_entries_u2[row_index].config(bg='lightblue')
        self.position_entries_u[row_index].config(bg='lightblue')
        self.position_entries_b[row_index].config(bg='lightblue')

    def create_position_table(self):
        """创建位置关系表格（带滚动条）- 支持点击选中行"""
        # 创建表格容器
        table_container = tk.Frame(self.plot_frame)
        table_container.pack(pady=5, fill=tk.X)
        
        # 创建画布和滚动条
        self.position_canvas = tk.Canvas(table_container, height=150, bg='white')
        scrollbar = tk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.position_canvas.yview)
        self.position_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.position_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 在画布中创建表格框架
        self.position_table_frame = tk.Frame(self.position_canvas, bg='white')
        self.position_canvas.create_window((0, 0), window=self.position_table_frame, anchor=tk.NW)
        
        # 表头
        headers = ["X/cm", "U1/mV", "U2/mV", "U/mV", "B/mT"]
        for col, header in enumerate(headers):
            label = tk.Label(self.position_table_frame, text=header, relief=tk.RIDGE, 
                        width=18, bg='lightgray', font=("Arial", 9, "bold"))
            label.grid(row=0, column=col, padx=1, pady=1, sticky='ew')
        
        # 创建30行数据
        self.position_entries_x = []
        self.position_entries_u1 = []
        self.position_entries_u2 = []
        self.position_entries_u = []
        self.position_entries_b = []
        
        # ===== 用于记录选中的行 =====
        self.selected_position_row = -1
        self.row_bg_colors = {}  # 存储每行的背景色
        
        for row in range(30):
            # X列 - 可编辑
            entry_x = tk.Entry(self.position_table_frame, width=18, justify='center')
            entry_x.grid(row=row+1, column=0, padx=1, pady=1)
            if self.position_x_values[row]:
                entry_x.insert(0, self.position_x_values[row])
            # 绑定点击事件
            entry_x.bind("<Button-1>", lambda e, r=row: self.select_position_row(r))
            self.position_entries_x.append(entry_x)
            
            # U1列 - 可编辑
            entry_u1 = tk.Entry(self.position_table_frame, width=18, justify='center')
            entry_u1.grid(row=row+1, column=1, padx=1, pady=1)
            if self.position_u1_values[row]:
                entry_u1.insert(0, self.position_u1_values[row])
            entry_u1.bind("<Button-1>", lambda e, r=row: self.select_position_row(r))
            self.position_entries_u1.append(entry_u1)
            
            # U2列 - 可编辑
            entry_u2 = tk.Entry(self.position_table_frame, width=18, justify='center')
            entry_u2.grid(row=row+1, column=2, padx=1, pady=1)
            if self.position_u2_values[row]:
                entry_u2.insert(0, self.position_u2_values[row])
            entry_u2.bind("<Button-1>", lambda e, r=row: self.select_position_row(r))
            self.position_entries_u2.append(entry_u2)
            
            # U列 - 只读
            entry_u = tk.Entry(self.position_table_frame, width=18, justify='center',
                            state='readonly', readonlybackground='white')
            entry_u.grid(row=row+1, column=3, padx=1, pady=1)
            if self.position_u_values[row]:
                entry_u.config(state='normal')
                entry_u.insert(0, self.position_u_values[row])
                entry_u.config(state='readonly')
            entry_u.bind("<Button-1>", lambda e, r=row: self.select_position_row(r))
            self.position_entries_u.append(entry_u)
            
            # B列 - 只读
            entry_b = tk.Entry(self.position_table_frame, width=18, justify='center',
                            state='readonly', readonlybackground='white')
            entry_b.grid(row=row+1, column=4, padx=1, pady=1)
            if self.position_b_values[row]:
                entry_b.config(state='normal')
                entry_b.insert(0, self.position_b_values[row])
                entry_b.config(state='readonly')
            entry_b.bind("<Button-1>", lambda e, r=row: self.select_position_row(r))
            self.position_entries_b.append(entry_b)
            
            # 保存行的背景色
            self.row_bg_colors[row] = 'white'
        
        # 更新画布滚动区域
        self.position_table_frame.update_idletasks()
        self.position_canvas.configure(scrollregion=self.position_canvas.bbox("all"))
        
    def create_position_plot(self):
        """创建位置关系曲线图"""
        plot_canvas_frame = tk.Frame(self.plot_frame)
        plot_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 增加图形尺寸，并调整布局边距
        self.position_fig, self.position_ax = plt.subplots(figsize=(3.5, 2.5))
        # 调整子图边距，为xlabel留出空间
        self.position_fig.subplots_adjust(bottom=0.13, left=0.1, right=0.95, top=0.9)
        
        self.position_canvas_plot = FigureCanvasTkAgg(self.position_fig, master=plot_canvas_frame)
        self.position_canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.position_ax.set_xlabel('X (cm)', fontsize=9)
        self.position_ax.set_ylabel('B (mT)', fontsize=9)
        self.position_ax.set_title('通电螺线管内磁感应强度分布', fontsize=10)
        self.position_ax.grid(True)
    
    def update_ub_plot(self):
        """更新U-B关系曲线图"""
        if not hasattr(self, 'ax') or self.ax is None:
            return
        
        self.ax.clear()
        
        # 获取有效数据 - 添加安全检查
        currents = []
        voltages = []
        if hasattr(self, 'ub_current_entries') and self.ub_current_entries:
            for i in range(9):
                try:
                    # 检查entry是否还存在
                    if i < len(self.ub_current_entries) and self.ub_current_entries[i] is not None:
                        # 检查entry的widget是否还存在
                        try:
                            entry_value = self.ub_current_entries[i].get().strip()
                            if entry_value:
                                current = float(entry_value)
                                voltage = float(self.ub_voltage_entries[i].get().strip())
                                currents.append(current)
                                voltages.append(voltage)
                        except (tk.TclError, ValueError, IndexError):
                            continue
                except (ValueError, IndexError, tk.TclError):
                    continue
        
        slope = 0
        if currents and voltages:
            # 绘制散点图
            self.ax.scatter(currents, voltages, color='blue', s=50, label='实验数据')
            
            # 线性拟合
            if len(currents) >= 2:
                coeffs = np.polyfit(currents, voltages, 1)
                slope = coeffs[0]
                intercept = coeffs[1]
                self.sensitivity = slope
                if hasattr(self, 'sensitivity_label') and self.sensitivity_label is not None:
                    try:
                        self.sensitivity_label.config(text=f"{slope:.4f}")
                    except tk.TclError:
                        pass
                
                # 更新右侧参数显示
                self.update_params_display(slope)
                
                # 绘制拟合直线
                x_line = np.array([min(currents), max(currents)])
                y_line = slope * x_line + intercept
                self.ax.plot(x_line, y_line, 'r-', label=f'拟合直线: y={slope:.4f}x+{intercept:.4f}')
                
                # 显示公式
                formula_text = f'拟合公式: U = {slope:.4f} * Im + {intercept:.4f}'
                self.ax.text(0.05, 0.95, formula_text, transform=self.ax.transAxes,
                        fontsize=10, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            else:
                if hasattr(self, 'sensitivity_label') and self.sensitivity_label is not None:
                    try:
                        self.sensitivity_label.config(text="0.00")
                    except tk.TclError:
                        pass
                self.sensitivity = 0
                self.update_params_display(0)
        else:
            if hasattr(self, 'sensitivity_label') and self.sensitivity_label is not None:
                try:
                    self.sensitivity_label.config(text="0.00")
                except tk.TclError:
                    pass
            self.update_params_display(0)
        
        self.ax.set_xlabel('Im (mA)')
        self.ax.set_ylabel('U (mV)')
        self.ax.set_title('霍尔传感器电压U与电流Im的关系')
        self.ax.grid(True)
        if currents and voltages:
            self.ax.legend()
        
        if hasattr(self, 'canvas_plot') and self.canvas_plot:
            try:
                self.canvas_plot.draw()
            except:
                pass
    
    def update_position_plot(self):
        """更新位置关系曲线图"""
        if not hasattr(self, 'position_ax') or self.position_ax is None:
            return
        
        self.position_ax.clear()
        
        # 获取有效数据 - 添加安全检查
        x_data = []
        b_data = []
        if hasattr(self, 'position_entries_x') and hasattr(self, 'position_entries_b'):
            for i in range(min(30, len(self.position_entries_x), len(self.position_entries_b))):
                try:
                    if self.position_entries_x[i] is not None and self.position_entries_b[i] is not None:
                        try:
                            x_val_str = self.position_entries_x[i].get().strip()
                            b_val_str = self.position_entries_b[i].get().strip()
                            
                            if x_val_str and b_val_str:
                                x_val = float(x_val_str)
                                b_val = float(b_val_str)
                                if b_val != 0:
                                    x_data.append(x_val)
                                    b_data.append(b_val)
                        except (tk.TclError, ValueError):
                            continue
                except (IndexError, tk.TclError):
                    continue
        
        # 获取当前B0值
        b0_value = 3.592
        if hasattr(self, 'b0_label') and self.b0_label is not None:
            try:
                b0_value = float(self.b0_label.cget('text'))
            except:
                pass
        
        if x_data and b_data:
            sorted_data = sorted(zip(x_data, b_data))
            x_sorted = [d[0] for d in sorted_data]
            b_sorted = [d[1] for d in sorted_data]
            
            self.position_ax.scatter(x_sorted, b_sorted, color='blue', s=30, label='实验数据')
            self.position_ax.plot(x_sorted, b_sorted, 'b-', alpha=0.7)
            self.position_ax.axhline(y=b0_value, color='r', linestyle='--', label=f'B0={b0_value:.3f}mT')
        
        self.position_ax.set_xlabel('X (cm)')
        self.position_ax.set_ylabel('B (mT)')
        self.position_ax.set_title('通电螺线管内磁感应强度分布')
        self.position_ax.grid(True)
        if x_data and b_data:
            self.position_ax.legend()
        
        if hasattr(self, 'position_canvas_plot') and self.position_canvas_plot:
            try:
                self.position_canvas_plot.draw()
            except:
                pass
    
    def update_params_display(self, slope):
        """更新右侧参数显示"""
        if hasattr(self, 'k_label') and self.k_label is not None:
            try:
                self.k_label.config(text=f"{slope:.4f}")
            except tk.TclError:
                pass
        
        # 计算霍尔灵敏度 K
        L = 0.26  # m
        D = 0.035  # m
        N = 3000
        mu0 = 4 * np.pi * 1e-7
        
        k_via = slope
        
        if mu0 * N != 0:
            K = np.sqrt(L**2 + D**2) * k_via / (mu0 * N)
        else:
            K = 0
        
        if hasattr(self, 'k_sensitivity_label') and self.k_sensitivity_label is not None:
            try:
                self.k_sensitivity_label.config(text=f"{K:.2f}")
            except tk.TclError:
                pass

    # ---------- U-B关系数据操作 ----------
    def save_ub_data(self):
        """保存U-B数据"""
        if hasattr(self, 'ub_current_entries') and self.ub_current_entries:
            for i in range(9):
                self.ub_current_values[i] = self.ub_current_entries[i].get()
                self.ub_voltage_values[i] = self.ub_voltage_entries[i].get()
    
    def calculate_ub(self):
        """计算U-B拟合直线"""
        self.update_ub_plot()
        messagebox.showinfo("计算完成", "拟合直线计算完成！")
    
    def clear_ub_data(self):
        """清空U-B数据"""
        if not messagebox.askyesno("确认清空", "确定要清空所有数据吗？"):
            return
        
        if hasattr(self, 'ub_current_entries') and self.ub_current_entries:
            for entry in self.ub_current_entries:
                entry.delete(0, tk.END)
                entry.insert(0, "")
            for entry in self.ub_voltage_entries:
                entry.delete(0, tk.END)
                entry.insert(0, "")
        
        self.ub_current_values = [""] * 9
        self.ub_voltage_values = [""] * 9
        self.sensitivity = 0
        
        if hasattr(self, 'sensitivity_label') and self.sensitivity_label:
            self.sensitivity_label.config(text="0.00")
        
        if hasattr(self, 'k_label'):
            self.k_label.config(text="0.0000")
        if hasattr(self, 'k_sensitivity_label'):
            self.k_sensitivity_label.config(text="0.00")
        
        self.update_ub_plot()
        messagebox.showinfo("清空数据", "数据已清空！")
    
    def export_ub_data(self):
        """导出U-B数据到CSV"""
        if not hasattr(self, 'ub_current_entries') or not self.ub_current_entries:
            messagebox.showwarning("警告", "没有可导出的数据！")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv")]
        )
        
        if file_path:
            try:
                slope = self.sensitivity
                L = 0.26
                D = 0.035
                N = 3000
                mu0 = 4 * np.pi * 1e-7
                k_via = slope
                if mu0 * N != 0:
                    K = np.sqrt(L**2 + D**2) * k_via / (mu0 * N)
                else:
                    K = 0
                
                try:
                    position_x = float(self.position_entry.get().strip()) if hasattr(self, 'position_entry') else 0.0
                except ValueError:
                    position_x = 0.0
                    messagebox.showwarning("警告", "位置X输入无效，使用默认值0.0")
                
                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write("=== 实验参数 ===\n")
                    f.write(f"N,{N}\n")
                    f.write(f"L,{L*100}\n")
                    f.write(f"D,{D*1000}\n")
                    f.write(f"位置X,{position_x:.1f}\n")
                    f.write("\n")
                    
                    f.write("=== 拟合结果 ===\n")
                    f.write(f"斜率k,{slope:.4f}\n")
                    f.write(f"霍尔灵敏度K,{K:.2f}\n")
                    f.write("\n")
                    
                    f.write("Im(mA),U(mV)\n")
                    for i in range(9):
                        current = self.ub_current_entries[i].get().strip()
                        voltage = self.ub_voltage_entries[i].get().strip()
                        if current and voltage:
                            f.write(f"{current},{voltage}\n")
                messagebox.showinfo("导出成功", f"数据已导出到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出数据时出错:\n{str(e)}")
    
    def import_ub_data(self):
        """从CSV导入U-B数据"""
        if not hasattr(self, 'ub_current_entries') or not self.ub_current_entries:
            messagebox.showwarning("警告", "请先切换到U-B关系界面！")
            return
            
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                
                position_value = None
                slope_value = None
                
                data_start = 0
                in_data_section = False
                
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue
                    
                    if line_stripped.startswith("Im(mA)") or line_stripped.startswith("Im"):
                        data_start = i + 1
                        in_data_section = True
                        continue
                    
                    if not in_data_section:
                        parts = line_stripped.split(',')
                        if len(parts) >= 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            if key == "位置X":
                                try:
                                    position_value = float(value)
                                except:
                                    pass
                            elif key == "斜率k":
                                try:
                                    slope_value = float(value)
                                except:
                                    pass
                
                if position_value is not None:
                    if hasattr(self, 'position_entry'):
                        self.position_entry.delete(0, tk.END)
                        self.position_entry.insert(0, f"{position_value:.1f}")
                    self.current_position = position_value
                    self.position_scale.set(position_value)
                    offset_x = 578 - position_value * 19.95
                    self.canvas.coords("scale_bg", offset_x, 50)
                    self.update_magnetic_field()
                
                if slope_value is not None:
                    self.sensitivity = slope_value
                    self.update_params_display(slope_value)
                    # 安全检查
                    if hasattr(self, 'sensitivity_label') and self.sensitivity_label is not None:
                        try:
                            self.sensitivity_label.config(text=f"{slope_value:.4f}")
                        except tk.TclError:
                            pass
                
                data_lines = []
                for line in lines[data_start:]:
                    line_stripped = line.strip()
                    if line_stripped and not line_stripped.startswith('==='):
                        data_lines.append(line_stripped)
                
                for i in range(9):
                    self.ub_current_entries[i].delete(0, tk.END)
                    self.ub_voltage_entries[i].delete(0, tk.END)
                    self.ub_current_values[i] = ""
                    self.ub_voltage_values[i] = ""
                
                for i, line in enumerate(data_lines[:9]):
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        try:
                            current_val = parts[0].strip()
                            voltage_val = parts[1].strip()
                            float(current_val)
                            float(voltage_val)
                            self.ub_current_entries[i].insert(0, current_val)
                            self.ub_voltage_entries[i].insert(0, voltage_val)
                            self.ub_current_values[i] = current_val
                            self.ub_voltage_values[i] = voltage_val
                        except ValueError:
                            continue
                
                self.update_ub_plot()
                messagebox.showinfo("导入成功", "数据导入完成！")
            except Exception as e:
                messagebox.showerror("导入失败", f"导入数据时出错:\n{str(e)}")

    # ---------- 位置关系数据操作 ----------
    def save_position_data(self):
        """保存位置关系数据"""
        if hasattr(self, 'position_entries_x') and self.position_entries_x:
            for i in range(30):
                self.position_x_values[i] = self.position_entries_x[i].get()
                self.position_u1_values[i] = self.position_entries_u1[i].get()
                self.position_u2_values[i] = self.position_entries_u2[i].get()
    
    def calculate_position(self):
        """计算位置关系的U和B值"""
        K = 31.11  # V/T
        
        # 获取用户输入的励磁电流
        try:
            current_ma = float(self.position_current_entry.get().strip()) if hasattr(self, 'position_current_entry') else 250
        except ValueError:
            current_ma = 250
            messagebox.showwarning("警告", "励磁电流输入无效，使用默认值250mA")
        
        # 计算B0理论值: B0 = 3.592 / 250 * I (mT)
        b0_theoretical = 3.592 * current_ma / 250.0
        
        # 更新B0显示
        if hasattr(self, 'b0_label'):
            self.b0_label.config(text=f"{b0_theoretical:.3f}")
        
        # 先保存当前X值
        for i in range(30):
            self.position_x_values[i] = self.position_entries_x[i].get()
            self.position_u1_values[i] = self.position_entries_u1[i].get()
            self.position_u2_values[i] = self.position_entries_u2[i].get()
        
        # 计算U和B - 只计算有输入的行
        for i in range(30):
            # 检查是否有输入数据（X、U1、U2至少有一个有值才计算）
            has_input = (self.position_entries_x[i].get().strip() != "" or 
                        self.position_entries_u1[i].get().strip() != "" or 
                        self.position_entries_u2[i].get().strip() != "")
            
            if not has_input:
                # 清空U和B列
                self.position_entries_u[i].config(state='normal')
                self.position_entries_u[i].delete(0, tk.END)
                self.position_entries_u[i].config(state='readonly')
                self.position_u_values[i] = ""
                
                self.position_entries_b[i].config(state='normal')
                self.position_entries_b[i].delete(0, tk.END)
                self.position_entries_b[i].config(state='readonly')
                self.position_b_values[i] = ""
                continue
            
            try:
                # 如果X为空，跳过
                if not self.position_entries_x[i].get().strip():
                    continue
                    
                u1_str = self.position_entries_u1[i].get().strip()
                u2_str = self.position_entries_u2[i].get().strip()
                
                # 如果U1和U2都为空，跳过
                if not u1_str and not u2_str:
                    continue
                    
                u1 = float(u1_str) if u1_str else 0
                u2 = float(u2_str) if u2_str else 0
                u = (u1 - u2) / 2
                # B = U / K，单位mT (u是mV，K是V/T，u/K得到mT)
                b = u / K
                
                # 更新U列
                self.position_entries_u[i].config(state='normal')
                self.position_entries_u[i].delete(0, tk.END)
                self.position_entries_u[i].insert(0, f"{u:.1f}")
                self.position_entries_u[i].config(state='readonly')
                self.position_u_values[i] = f"{u:.1f}"
                
                # 更新B列
                self.position_entries_b[i].config(state='normal')
                self.position_entries_b[i].delete(0, tk.END)
                self.position_entries_b[i].insert(0, f"{b:.3f}")
                self.position_entries_b[i].config(state='readonly')
                self.position_b_values[i] = f"{b:.3f}"
            except ValueError:
                # 如果数据格式错误，清空U和B列
                self.position_entries_u[i].config(state='normal')
                self.position_entries_u[i].delete(0, tk.END)
                self.position_entries_u[i].config(state='readonly')
                self.position_u_values[i] = ""
                
                self.position_entries_b[i].config(state='normal')
                self.position_entries_b[i].delete(0, tk.END)
                self.position_entries_b[i].config(state='readonly')
                self.position_b_values[i] = ""
                continue
        
        # 强制更新曲线图
        self.update_position_plot()
        messagebox.showinfo("计算完成", f"位置关系计算完成！\nB₀ = {b0_theoretical:.3f} mT")
    
    def clear_position_data(self):
        """清空位置关系数据"""
        if not messagebox.askyesno("确认清空", "确定要清空所有数据吗？"):
            return
        
        if hasattr(self, 'position_entries_x') and self.position_entries_x:
            for i in range(30):
                self.position_entries_x[i].delete(0, tk.END)
                self.position_entries_u1[i].delete(0, tk.END)
                self.position_entries_u2[i].delete(0, tk.END)
                
                self.position_entries_u[i].config(state='normal')
                self.position_entries_u[i].delete(0, tk.END)
                self.position_entries_u[i].config(state='readonly')
                
                self.position_entries_b[i].config(state='normal')
                self.position_entries_b[i].delete(0, tk.END)
                self.position_entries_b[i].config(state='readonly')
                
                self.position_x_values[i] = ""
                self.position_u1_values[i] = ""
                self.position_u2_values[i] = ""
                self.position_u_values[i] = ""
                self.position_b_values[i] = ""
        
        self.update_position_plot()
        messagebox.showinfo("清空数据", "数据已清空！")
    
    def export_position_data(self):
        """导出位置关系数据到CSV（包含实验参数）"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv")]
        )
        
        if file_path:
            try:
                # 获取实验参数
                position_x = self.position_entry.get().strip() if hasattr(self, 'position_entry') else "0.0"
                try:
                    current_ma = float(self.position_current_entry.get().strip()) if hasattr(self, 'position_current_entry') else 250
                except ValueError:
                    current_ma = 250
                
                b0_theoretical = 3.592 * current_ma / 250.0
                
                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    # 写入实验参数
                    f.write("=== 实验参数 ===\n")
                    f.write(f"N,3000\n")
                    f.write(f"L,26\n")
                    f.write(f"D,35\n")
                    f.write(f"位置X,{position_x}\n")
                    f.write(f"励磁电流I,{current_ma}\n")
                    f.write(f"B0,{b0_theoretical:.3f}\n")
                    f.write("\n")
                    
                    # 写入数据表头
                    f.write("X(cm),U1(mV),U2(mV),U(mV),B(mT)\n")
                    for i in range(30):
                        x = self.position_entries_x[i].get().strip()
                        u1 = self.position_entries_u1[i].get().strip()
                        u2 = self.position_entries_u2[i].get().strip()
                        u = self.position_entries_u[i].get().strip()
                        b = self.position_entries_b[i].get().strip()
                        if x or u1 or u2 or u or b:
                            f.write(f"{x},{u1},{u2},{u},{b}\n")
                messagebox.showinfo("导出成功", f"数据已导出到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出数据时出错:\n{str(e)}")
    
    def import_position_data(self):
        """从CSV导入位置关系数据（包含实验参数）"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                
                # 解析实验参数
                position_x = None
                current_ma = None
                b0_value = None
                
                data_start = 0
                in_data_section = False
                
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue
                    
                    # 检测数据部分开始
                    if line_stripped.startswith("X(cm)") or line_stripped.startswith("X"):
                        data_start = i + 1
                        in_data_section = True
                        continue
                    
                    # 解析实验参数
                    if not in_data_section:
                        parts = line_stripped.split(',')
                        if len(parts) >= 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            if key == "位置X":
                                try:
                                    position_x = float(value)
                                except:
                                    pass
                            elif key == "励磁电流I":
                                try:
                                    current_ma = float(value)
                                except:
                                    pass
                            elif key == "B0":
                                try:
                                    b0_value = float(value)
                                except:
                                    pass
                
                # 更新实验参数
                if position_x is not None and hasattr(self, 'position_entry'):
                    self.position_entry.delete(0, tk.END)
                    self.position_entry.insert(0, f"{position_x:.1f}")
                
                if current_ma is not None and hasattr(self, 'position_current_entry'):
                    self.position_current_entry.delete(0, tk.END)
                    self.position_current_entry.insert(0, f"{current_ma:.0f}")
                    
                if b0_value is not None and hasattr(self, 'b0_label'):
                    self.b0_label.config(text=f"{b0_value:.3f}")
                
                # 读取数据
                data_lines = []
                for line in lines[data_start:]:
                    line_stripped = line.strip()
                    if line_stripped:
                        data_lines.append(line_stripped)
                
                # 清空现有数据
                for i in range(30):
                    self.position_entries_x[i].delete(0, tk.END)
                    self.position_entries_u1[i].delete(0, tk.END)
                    self.position_entries_u2[i].delete(0, tk.END)
                    
                    self.position_entries_u[i].config(state='normal')
                    self.position_entries_u[i].delete(0, tk.END)
                    self.position_entries_u[i].config(state='readonly')
                    
                    self.position_entries_b[i].config(state='normal')
                    self.position_entries_b[i].delete(0, tk.END)
                    self.position_entries_b[i].config(state='readonly')
                    
                    self.position_x_values[i] = ""
                    self.position_u1_values[i] = ""
                    self.position_u2_values[i] = ""
                    self.position_u_values[i] = ""
                    self.position_b_values[i] = ""
                
                # 填充数据
                for i, line in enumerate(data_lines[:30]):
                    parts = line.strip().split(',')
                    if len(parts) >= 5:
                        try:
                            self.position_entries_x[i].insert(0, parts[0])
                            self.position_x_values[i] = parts[0]
                            
                            self.position_entries_u1[i].insert(0, parts[1])
                            self.position_u1_values[i] = parts[1]
                            
                            self.position_entries_u2[i].insert(0, parts[2])
                            self.position_u2_values[i] = parts[2]
                            
                            self.position_entries_u[i].config(state='normal')
                            self.position_entries_u[i].insert(0, parts[3])
                            self.position_entries_u[i].config(state='readonly')
                            self.position_u_values[i] = parts[3]
                            
                            self.position_entries_b[i].config(state='normal')
                            self.position_entries_b[i].insert(0, parts[4])
                            self.position_entries_b[i].config(state='readonly')
                            self.position_b_values[i] = parts[4]
                        except:
                            continue
                
                self.update_position_plot()
                messagebox.showinfo("导入成功", "数据导入完成！")
            except Exception as e:
                messagebox.showerror("导入失败", f"导入数据时出错:\n{str(e)}")

    # ---------- 显示更新函数 ----------
    def update_position(self, value):
        """更新位置显示"""
        self.current_position = float(value)
        
        offset_x = 578 - self.current_position * 19.95
        self.canvas.coords("scale_bg", offset_x, 50)
        
        self.update_magnetic_field()
    
    def update_current(self, value):
        """更新电流显示"""
        self.current_current = int(float(value))
        self.current_var.set(str(self.current_current))
        self.update_magnetic_field()
        self.update_arrows()  # ← 添加这行
    
    def update_voltage_offset(self, value):
        """更新电压表调零"""
        self.voltage_offset = float(value)
        self.update_voltage_display()
        self.update_magnetic_field()

    def update_millitesla_offset(self, value):
        """更新毫特计调零"""
        self.millitesla_offset = float(value)
        self.update_millitesla_display()
        self.update_magnetic_field()
    
    def update_voltage_display(self):
        """更新电压表显示"""
        measured_voltage = self.get_current_voltage()
        displayed_voltage = measured_voltage + self.voltage_offset
        if hasattr(self, 'voltage_var'):
            self.voltage_var.set(f"{displayed_voltage:.1f}")

    def get_displayed_voltage(self):
        """获取当前显示的电压值（包含调零偏移）"""
        measured_voltage = self.get_current_voltage()
        return measured_voltage + self.voltage_offset
        
    def update_millitesla_display(self):
        """更新毫特计显示"""
        measured_b = self.get_current_magnetic_field()
        displayed_b = measured_b + self.millitesla_offset
        if hasattr(self, 'millitesla_var'):
            self.millitesla_var.set(f"{displayed_b:.1f}")
    
    def get_current_voltage(self):
        """获取当前计算的电压值（不含偏移）"""
        position = self.current_position
        current_ma = self.current_current
        
        voltage_250ma = self.interpolate_voltage(position, self.current_direction)
        
        if current_ma != 0:
            return voltage_250ma * current_ma / 250.0
        else:
            return 0

    def get_current_magnetic_field(self):
        """获取当前计算的磁感应强度值（不含偏移）"""
        voltage = self.get_current_voltage()
        hall_sensitivity = 0.1  # mV/mT
        if hall_sensitivity != 0:
            return voltage / hall_sensitivity
        else:
            return 0

    def update_magnetic_field(self):
        """根据位置和电流计算理论磁场值并更新显示"""
        measured_voltage = self.get_current_voltage()
        
        displayed_voltage = measured_voltage + self.voltage_offset
        if hasattr(self, 'voltage_var'):
            self.voltage_var.set(f"{displayed_voltage:.1f}")
        
        displayed_b = self.millitesla_offset
        if hasattr(self, 'millitesla_var'):
            self.millitesla_var.set(f"{displayed_b:.1f}")
    
    def save_position_data_old(self):
        """保存位置数据（旧）"""
        pass
    
    def on_experiment_select(self):
        """螺线管实验选择"""
        self.position_scale.config(state='normal')
        self.current_scale.config(state='normal')
        self.voltage_offset_scale.config(state='normal')
        # self.millitesla_offset_scale.config(state='normal')

