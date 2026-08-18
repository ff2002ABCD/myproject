import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
import sys
import json

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def get_resource_path(relative_path):
    """获取资源的绝对路径，支持打包后的环境"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class EditableTreeview(ttk.Treeview):
    """可编辑的Treeview组件"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind('<Double-1>', self.on_double_click)
        self.edit_entry = None
        
    def on_double_click(self, event):
        """双击编辑单元格"""
        region = self.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        column = self.identify_column(event.x)
        if column != '#2':
            return
            
        row_id = self.identify_row(event.y)
        if not row_id:
            return
            
        x, y, width, height = self.bbox(row_id, column)
        current_value = self.item(row_id, 'values')[1]
        
        self.edit_entry = tk.Entry(self)
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.focus()
        
        self.edit_entry.bind('<Return>', lambda e: self.save_edit(row_id, column))
        self.edit_entry.bind('<Escape>', self.cancel_edit)
        self.edit_entry.bind('<FocusOut>', lambda e: self.save_edit(row_id, column))
        
    def save_edit(self, row_id, column):
        if self.edit_entry:
            new_value = self.edit_entry.get().strip()
            if new_value:
                try:
                    float(new_value)
                    values = list(self.item(row_id, 'values'))
                    values[1] = new_value
                    self.item(row_id, values=values)
                    
                    if hasattr(self, 'on_data_change'):
                        self.on_data_change(row_id, new_value)
                except ValueError:
                    messagebox.showwarning("输入错误", "请输入有效的数字！")
            
            self.edit_entry.destroy()
            self.edit_entry = None
            
    def cancel_edit(self, event):
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None


class PolarizationExperiment:
    def __init__(self, root):
        self.root = root
        self.root.title("光学综合实验系统")
        self.root.geometry("1400x800")
        
        # 实验参数
        self.C0 = 0.3333
        self.tube_length = 1.0
        self.theoretical_rotation = 54.1
        
        self.concentrations = [self.C0, self.C0/2, self.C0/4, self.C0/8]
        self.concentration_labels = ['C0', 'C0/2', 'C0/4', 'C0/8']
        self.rotation_data = [0.0, 0.0, 0.0, 0.0]
        
        # 光功率计相关变量
        self.power_ranges = ["5mW", "500uW", "50uW", "5uW"]
        self.current_power_range = tk.StringVar(value="5mW")
        self.zero_offset = 0  # 调零偏移量 (uW)
        
        # 主机显示变量
        self.current_power = 0.0  # 当前光功率 (mW)
        self.current_angle = 0.0  # 当前检偏器角度 (度)
        
        self.create_main_layout()
        self.init_table_data()
        self.init_plot()
        self.current_concentration = "C0"
        
    def create_main_layout(self):
        """创建主布局"""
        # 顶部选项卡按钮区域
        self.create_tab_buttons()
        
        # 主要内容区域（左右分屏）
        main_content_frame = tk.Frame(self.root)
        main_content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧区域 - 包含实验主机和实验装置
        self.left_frame = tk.Frame(main_content_frame, bg='#f0f0f0', relief=tk.RAISED, bd=2)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 左侧上半部分：实验主机
        self.left_top_frame = tk.Frame(self.left_frame, bg='#f0f0f0', relief=tk.RAISED, bd=1)
        self.left_top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 左侧中部分：光功率计控制
        self.left_mid_frame = tk.Frame(self.left_frame, bg='#f0f0f0', relief=tk.RAISED, bd=1)
        self.left_mid_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 左侧下半部分：实验装置
        self.left_bottom_frame = tk.Frame(self.left_frame, bg='#f0f0f0', relief=tk.RAISED, bd=1)
        self.left_bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 右侧区域
        self.right_frame = tk.Frame(main_content_frame, bg='#f0f0f0', relief=tk.RAISED, bd=2)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.create_left_top_content()  # 实验主机
        self.create_left_mid_content()  # 光功率计控制
        self.create_left_bottom_content()  # 实验装置
        self.create_right_content()  # 右侧内容（表格、曲线图、参数、按钮）
    
    def create_tab_buttons(self):
        """创建顶部选项卡按钮组"""
        # 选项卡按钮容器
        tab_frame = tk.Frame(self.root, bg='#e0e0e0', relief=tk.RAISED, bd=2)
        tab_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # 按钮样式
        button_style = {
            'font': ('Microsoft YaHei', 11),
            'fg': 'white',
            'activebackground': '#357ABD',
            'activeforeground': 'white',
            'relief': tk.RAISED,
            'bd': 2,
            'cursor': 'hand2',
            'width': 20,
            'height': 1
        }
        
        # 选项卡按钮文本列表
        tab_names = [
            "1. 光偏振实验",
            "2. 旋光效应实验",
            "3. 焦距测量实验",
            "4. 干涉实验",
            "5. 光强分布实验"
        ]
        
        # 创建按钮
        self.tab_buttons = []
        for i, text in enumerate(tab_names):
            # 为第一个按钮设置不同颜色作为默认选中
            if i == 0:
                btn = tk.Button(tab_frame, text=text, bg='#2E75B6', **button_style)
            else:
                btn = tk.Button(tab_frame, text=text, bg='#4A90D9', **button_style)
            
            # 绑定点击事件
            btn.config(command=lambda idx=i, b=btn: self.on_tab_click(idx, b))
            btn.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
            self.tab_buttons.append(btn)
    
    def on_tab_click(self, tab_index, clicked_button):
        """选项卡点击事件（暂时只切换样式）"""
        # 重置所有按钮的颜色
        for btn in self.tab_buttons:
            btn.config(bg='#4A90D9')
        
        # 高亮当前选中的按钮
        clicked_button.config(bg='#2E75B6')
        
        # 显示提示信息（表示功能暂未实现）
        tab_names = [
            "光偏振实验",
            "激光法测量蔗糖溶液的旋光角",
            "测量蔗糖水溶液的浓度",
            "半荫法测蔗糖水溶液旋光角与浓度",
            "测量果糖溶液的旋光率"
        ]
        messagebox.showinfo("提示", f"您选择了：{tab_names[tab_index]}\n该功能正在开发中...")
    
    def create_left_top_content(self):
        """创建左侧实验主机区域（带叠加文本框）"""
        # 创建一个容器Frame来放置图片和叠加的文本框
        self.host_container = tk.Frame(self.left_top_frame, bg='#f0f0f0')
        self.host_container.pack(pady=5, expand=True, fill=tk.BOTH)
        
        try:
            img_path = get_resource_path("background/主机.jpg")
            img = Image.open(img_path)
            img = img.resize((600, 220), Image.Resampling.LANCZOS)
            self.left_top_img = ImageTk.PhotoImage(img)
            
            # 创建Label显示图片
            self.img_label = tk.Label(self.host_container, image=self.left_top_img, bg='#f0f0f0')
            self.img_label.pack()
            
            # 在图片上叠加文本框（使用place方法定位）
            # 光功率文本框 - 位置根据图片布局调整
            self.power_display_frame = tk.Frame(self.img_label, bg='white', bd=2)
            self.power_display_frame.place(x=40, y=60, width=160, height=40)
            
            tk.Label(self.power_display_frame, text="光功率:", font=("Microsoft YaHei", 9), 
                    bg='white').pack(side=tk.LEFT, padx=5)
            self.power_display_label = tk.Label(self.power_display_frame, text="0.00", 
                                                font=("Microsoft YaHei", 10, "bold"), 
                                                fg='blue', bg='white', width=8)
            self.power_display_label.pack(side=tk.LEFT)
            tk.Label(self.power_display_frame, text="mW", font=("Microsoft YaHei", 9), 
                    bg='white').pack(side=tk.LEFT)
            
            # 检偏器角度文本框
            self.angle_display_frame = tk.Frame(self.img_label, bg='white', bd=2)
            self.angle_display_frame.place(x=40, y=90, width=150, height=40)
            
            tk.Label(self.angle_display_frame, text="检偏器:", font=("Microsoft YaHei", 9), 
                    bg='white').pack(side=tk.LEFT, padx=5)
            self.angle_display_label = tk.Label(self.angle_display_frame, text="0.0", 
                                                font=("Microsoft YaHei", 10, "bold"), 
                                                fg='green', bg='white', width=8)
            self.angle_display_label.pack(side=tk.LEFT)
            tk.Label(self.angle_display_frame, text="°", font=("Microsoft YaHei", 9), 
                    bg='white').pack(side=tk.LEFT)
            
            # # 添加角度调节按钮
            # angle_control_frame = tk.Frame(self.img_label, bg='#f0f0f0')
            # angle_control_frame.place(x=300, y=75, width=150, height=25)
            
            # btn_dec = tk.Button(angle_control_frame, text="-", command=self.decrease_angle,
            #                    font=("Microsoft YaHei", 8), width=3)
            # btn_dec.pack(side=tk.LEFT, padx=2)
            
            # btn_inc = tk.Button(angle_control_frame, text="+", command=self.increase_angle,
            #                    font=("Microsoft YaHei", 8), width=3)
            # btn_inc.pack(side=tk.LEFT, padx=2)
            
            # tk.Label(angle_control_frame, text="步长:1°", font=("Microsoft YaHei", 8), 
            #         bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            error_label = tk.Label(self.left_top_frame, text=f"图片加载失败\n{str(e)}", 
                                  font=("Microsoft YaHei", 10), bg='#f0f0f0', fg='red')
            error_label.pack(pady=5)
    
    def decrease_angle(self):
        """减小检偏器角度"""
        self.current_angle -= 1.0
        if self.current_angle < 0:
            self.current_angle = 0
        self.update_angle_display()
        # 模拟光功率随角度变化（余弦平方关系）
        self.simulate_power_from_angle()
    
    def increase_angle(self):
        """增加检偏器角度"""
        self.current_angle += 1.0
        if self.current_angle > 180:
            self.current_angle = 180
        self.update_angle_display()
        # 模拟光功率随角度变化（余弦平方关系）
        self.simulate_power_from_angle()
    
    def update_angle_display(self):
        """更新角度显示"""
        self.angle_display_label.config(text=f"{self.current_angle:.1f}")
    
    def simulate_power_from_angle(self):
        """根据检偏器角度模拟光功率（马吕斯定律）"""
        # 马吕斯定律: I = I0 * cos²(θ)
        import math
        max_power = 5.0  # 最大光功率 5mW
        angle_rad = math.radians(self.current_angle)
        power = max_power * (math.cos(angle_rad) ** 2)
        self.current_power = power
        self.update_power_display_on_host(power)
    
    def update_power_display_on_host(self, power_mw):
        """更新主机上的光功率显示"""
        self.power_display_label.config(text=f"{power_mw:.2f}")
    
    def create_left_mid_content(self):
        """创建左侧光功率计控制区域"""
        # 标题
        title_label = tk.Label(self.left_mid_frame, text="光功率计控制", 
                               font=("Microsoft YaHei", 12, "bold"), bg='#f0f0f0')
        title_label.pack(pady=5)
        
        # 挡位选择区域
        range_frame = tk.Frame(self.left_mid_frame, bg='#f0f0f0')
        range_frame.pack(pady=5)
        
        tk.Label(range_frame, text="挡位选择:", font=("Microsoft YaHei", 10), 
                bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
        
        # 横向排列挡位选项
        for range_val in self.power_ranges:
            rb = tk.Radiobutton(range_frame, text=range_val, value=range_val, 
                               variable=self.current_power_range,
                               font=("Microsoft YaHei", 9), bg='#f0f0f0',
                               command=self.on_power_range_change)
            rb.pack(side=tk.LEFT, padx=8)
        
        # 调零滑块区域
        zero_frame = tk.Frame(self.left_mid_frame, bg='#f0f0f0')
        zero_frame.pack(pady=10, padx=10, fill=tk.X)
        
        tk.Label(zero_frame, text="调零调节:", font=("Microsoft YaHei", 10), 
                bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
        
        # 创建滑块 (范围 -100 到 100 uW)
        self.zero_slider = tk.Scale(zero_frame, from_=-100, to=100, orient=tk.HORIZONTAL,
                                     resolution=1, length=300, command=self.on_zero_adjust,
                                     bg='#f0f0f0', font=("Microsoft YaHei", 9))
        self.zero_slider.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 显示当前偏移值
        self.offset_label = tk.Label(zero_frame, text="0 uW", font=("Microsoft YaHei", 10, "bold"), 
                                     bg='#f0f0f0', fg='blue', width=10)
        self.offset_label.pack(side=tk.LEFT, padx=5)
        
        # 重置调零按钮
        reset_button = tk.Button(self.left_mid_frame, text="重置调零", 
                                command=self.reset_zero,
                                font=("Microsoft YaHei", 10), bg='#FF9800', fg='white',
                                width=12, height=1, cursor='hand2')
        reset_button.pack(pady=5)
        
        # 当前光功率显示（从光功率计读取）
        power_frame = tk.Frame(self.left_mid_frame, bg='#f0f0f0')
        power_frame.pack(pady=5)
        
        # tk.Label(power_frame, text="当前光功率:", font=("Microsoft YaHei", 10), 
        #         bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
        
        # self.power_value_label = tk.Label(power_frame, text="0.00", 
        #                                   font=("Microsoft YaHei", 10, "bold"), 
        #                                   fg='blue', bg='#f0f0f0', width=10)
        # self.power_value_label.pack(side=tk.LEFT, padx=5)
        
        # tk.Label(power_frame, text="mW", font=("Microsoft YaHei", 10), 
        #         bg='#f0f0f0').pack(side=tk.LEFT)
    
    def on_power_range_change(self):
        """挡位改变时的回调"""
        current_range = self.current_power_range.get()
        print(f"挡位切换到: {current_range}")
    
    def on_zero_adjust(self, value):
        """调零滑块调节回调"""
        self.zero_offset = int(float(value))
        self.offset_label.config(text=f"{self.zero_offset:+d} uW")
        # 更新光功率显示
        self.update_power_display(self.current_power)
    
    def reset_zero(self):
        """重置调零"""
        self.zero_slider.set(0)
        self.zero_offset = 0
        self.offset_label.config(text="0 uW")
        self.update_power_display(self.current_power)
        messagebox.showinfo("提示", "调零已重置！")
    
    def update_power_display(self, measured_mw):
        """更新光功率显示（考虑调零偏移）"""
        # 将测量值转换为uW进行偏移调整
        measured_uw = measured_mw * 1000
        adjusted_uw = measured_uw + self.zero_offset
        adjusted_mw = adjusted_uw / 1000
        
        # 根据挡位选择合适的单位显示
        current_range = self.current_power_range.get()
        
        if current_range == "5mW":
            display_value = adjusted_mw
            unit = "mW"
        elif current_range == "500uW":
            display_value = adjusted_uw
            unit = "uW"
        elif current_range == "50uW":
            display_value = adjusted_uw
            unit = "uW"
        else:  # 5uW
            display_value = adjusted_uw
            unit = "uW"
        
        # 限制显示范围
        if adjusted_mw < 0:
            display_value = 0
        
        self.power_value_label.config(text=f"{display_value:.2f}")
        
        # 更新主机上的光功率显示
        self.power_display_label.config(text=f"{adjusted_mw:.2f}")
    
    def create_left_bottom_content(self):
        """创建左侧实验装置区域"""
        try:
            img_path = get_resource_path("background/图1.jpg")
            img = Image.open(img_path)
            img = img.resize((550, 150), Image.Resampling.LANCZOS)
            self.left_bottom_img = ImageTk.PhotoImage(img)
            img_label = tk.Label(self.left_bottom_frame, image=self.left_bottom_img, bg='#f0f0f0')
            img_label.pack(pady=5)
        except Exception as e:
            error_label = tk.Label(self.left_bottom_frame, text=f"图片加载失败\n{str(e)}", 
                                  font=("Microsoft YaHei", 10), bg='#f0f0f0', fg='red')
            error_label.pack(pady=5)
        
        # 溶液浓度选择区域 - 横向排列
        conc_frame = tk.Frame(self.left_bottom_frame, bg='#f0f0f0')
        conc_frame.pack(pady=10)
        
        tk.Label(conc_frame, text="溶液浓度:", font=("Microsoft YaHei", 11), 
                bg='#f0f0f0').pack(side=tk.LEFT, padx=10)
        
        self.concentration_var = tk.StringVar(value="C0")
        concentrations = [("C0", "C0"), ("C0/2", "C0/2"), ("C0/4", "C0/4"), ("C0/8", "C0/8")]
        
        for text, value in concentrations:
            rb = tk.Radiobutton(conc_frame, text=text, value=value, 
                               variable=self.concentration_var,
                               font=("Microsoft YaHei", 10), bg='#f0f0f0',
                               command=self.change_concentration)
            rb.pack(side=tk.LEFT, padx=10)
    
    def on_data_change(self, row_id, new_value):
        idx = int(row_id)
        if 0 <= idx < len(self.rotation_data):
            try:
                self.rotation_data[idx] = float(new_value) if new_value else 0.0
                self.update_plot()
                self.update_parameters_display()
            except ValueError:
                pass
    
    def create_right_content(self):
        """创建右侧内容（表格在上，曲线图在下）"""
        # 表格区域
        table_frame = tk.Frame(self.right_frame)
        table_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        table_label = tk.Label(table_frame, text="数据记录表", font=("Microsoft YaHei", 11, "bold"),
                               bg='#f0f0f0')
        table_label.pack(pady=(0, 5))
        
        # 创建表格
        columns = ('浓度', '旋光度平均值 θ°')
        self.tree = EditableTreeview(table_frame, columns=columns, show='headings', height=5)
        self.tree.on_data_change = self.on_data_change
        
        self.tree.heading('浓度', text='浓度')
        self.tree.heading('旋光度平均值 θ°', text='旋光度平均值 θ°')
        
        self.tree.column('浓度', width=150, anchor='center')
        self.tree.column('旋光度平均值 θ°', width=180, anchor='center')
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 曲线图区域
        plot_frame = tk.Frame(self.right_frame)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        plot_canvas_frame = tk.Frame(plot_frame)
        plot_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 3.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 参数显示区域
        param_container = tk.Frame(self.right_frame)
        param_container.pack(fill=tk.X, pady=5, padx=10)
        
        # 创建参数框架 - 使用网格布局
        param_frame = tk.Frame(param_container, bg='#f0f0f0', relief=tk.GROOVE, bd=1)
        param_frame.pack(fill=tk.X)
        
        # 参数1: 试管长度
        self.label_length = tk.Label(param_frame, text="试管长度 l = 1.00 dm", 
                                     font=("Microsoft YaHei", 10), bg='#f0f0f0')
        self.label_length.grid(row=0, column=0, padx=15, pady=5, sticky='w')
        
        # 参数2: 浓度C0
        self.label_c0 = tk.Label(param_frame, text=f"浓度 C0 = {self.C0:.4f} g/cm³", 
                                 font=("Microsoft YaHei", 10), bg='#f0f0f0')
        self.label_c0.grid(row=0, column=1, padx=15, pady=5, sticky='w')
        
        # 参数3: 理论旋光率
        self.label_theoretical = tk.Label(param_frame, text=f"理论旋光率 = {self.theoretical_rotation:.1f} (°)/dm/(g/cm³)", 
                                          font=("Microsoft YaHei", 10), bg='#f0f0f0')
        self.label_theoretical.grid(row=1, column=0, padx=15, pady=5, sticky='w')
        
        # 参数4: 实验旋光率
        self.label_experimental = tk.Label(param_frame, text="实验旋光率 = 待计算", 
                                           font=("Microsoft YaHei", 10), bg='#f0f0f0')
        self.label_experimental.grid(row=1, column=1, padx=15, pady=5, sticky='w')
        
        # 参数5: 相对误差
        self.label_error = tk.Label(param_frame, text="相对误差 = 待计算", 
                                    font=("Microsoft YaHei", 10), bg='#f0f0f0')
        self.label_error.grid(row=2, column=0, padx=15, pady=5, sticky='w')
        
        # 参数6: 拟合公式
        self.label_formula = tk.Label(param_frame, text="拟合公式 = 待计算", 
                                      font=("Microsoft YaHei", 10), bg='#f0f0f0')
        self.label_formula.grid(row=2, column=1, padx=15, pady=5, sticky='w')
        
        # 配置网格列权重
        param_frame.grid_columnconfigure(0, weight=1)
        param_frame.grid_columnconfigure(1, weight=1)
        
        # 按钮区域
        button_frame = tk.Frame(self.right_frame)
        button_frame.pack(pady=(5, 10))
        
        buttons = [
            ("计算", self.calculate),
            ("清空数据", self.clear_data),
            ("导出数据", self.export_data),
            ("导入数据", self.import_data)
        ]
        
        for text, command in buttons:
            btn = tk.Button(button_frame, text=text, command=command, 
                          font=("Microsoft YaHei", 10), width=10, height=1)
            btn.pack(side=tk.LEFT, padx=8)
    
    def init_table_data(self):
        for i, label in enumerate(self.concentration_labels):
            self.tree.insert('', 'end', iid=str(i), values=(label, ''))
    
    def change_concentration(self):
        self.current_concentration = self.concentration_var.get()
    
    def init_plot(self):
        self.update_plot()
    
    def update_plot(self):
        self.ax.clear()
        
        valid_data = [(self.concentrations[i], self.rotation_data[i]) 
                     for i in range(4) if self.rotation_data[i] != 0]
        
        if len(valid_data) > 1:
            x = [d[0] for d in valid_data]
            y = [d[1] for d in valid_data]
            self.ax.scatter(x, y, color='blue', s=50, label='实验数据', zorder=5)
            
            coeffs = np.polyfit(x, y, 1)
            poly = np.poly1d(coeffs)
            x_fit = np.linspace(min(x), max(x), 100)
            y_fit = poly(x_fit)
            self.ax.plot(x_fit, y_fit, 'r-', linewidth=2, label=f'y={coeffs[0]:.2f}x+{coeffs[1]:.2f}')
            
            r2 = self.calculate_r_squared(x, y, coeffs)
            self.ax.text(0.05, 0.95, f'R² = {r2:.4f}', transform=self.ax.transAxes, 
                        fontsize=9, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            self.ax.set_title('浓度-旋光度关系曲线', fontsize=11, fontweight='bold')
        else:
            self.ax.set_title('浓度-旋光度关系曲线\n(需要至少2个数据点)', fontsize=10)
        
        self.ax.set_xlabel('浓度 (g/cm³)', fontsize=9)
        self.ax.set_ylabel('旋光度 θ°', fontsize=9)
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.legend(loc='best', fontsize=8)
        
        self.ax.set_facecolor('#f8f9fa')
        self.fig.patch.set_facecolor('#f0f0f0')
        self.fig.tight_layout()
        
        self.canvas.draw()
    
    def update_parameters_display(self):
        """更新参数显示"""
        experimental_rotation = None
        relative_error = None
        formula_text = "待计算"
        
        valid_data = [(self.concentrations[i], self.rotation_data[i]) 
                     for i in range(4) if self.rotation_data[i] != 0]
        
        if len(valid_data) >= 2:
            x = [d[0] for d in valid_data]
            y = [d[1] for d in valid_data]
            coeffs = np.polyfit(x, y, 1)
            experimental_rotation = coeffs[0] / self.tube_length
            relative_error = abs(experimental_rotation - self.theoretical_rotation) / self.theoretical_rotation * 100
            r2 = self.calculate_r_squared(x, y, coeffs)
            formula_text = f"y = {coeffs[0]:.4f}x + {coeffs[1]:.4f}  (R²={r2:.4f})"
        
        # 更新各个参数标签
        self.label_length.config(text=f"试管长度 l = {self.tube_length:.2f} dm")
        self.label_c0.config(text=f"浓度 C0 = {self.C0:.4f} g/cm³")
        self.label_theoretical.config(text=f"理论旋光率 = {self.theoretical_rotation:.1f} (°)/dm/(g/cm³)")
        
        if experimental_rotation is not None:
            self.label_experimental.config(text=f"实验旋光率 = {experimental_rotation:.2f} (°)/dm/(g/cm³)")
            self.label_error.config(text=f"相对误差 = {relative_error:.2f} %")
            self.label_formula.config(text=f"拟合公式 = {formula_text}")
        else:
            self.label_experimental.config(text="实验旋光率 = 待计算 (需要≥2个数据点)")
            self.label_error.config(text="相对误差 = 待计算")
            self.label_formula.config(text="拟合公式 = 待计算")
    
    def calculate(self):
        valid_data = [(self.concentrations[i], self.rotation_data[i]) 
                     for i in range(4) if self.rotation_data[i] != 0]
        
        if len(valid_data) < 2:
            messagebox.showwarning("数据不足", "至少需要输入两个有效数据点才能进行拟合！")
            return
        
        x = [d[0] for d in valid_data]
        y = [d[1] for d in valid_data]
        coeffs = np.polyfit(x, y, 1)
        r2 = self.calculate_r_squared(x, y, coeffs)
        
        formula = f"拟合结果:\n"
        formula += f"拟合公式: y = {coeffs[0]:.4f}x + {coeffs[1]:.4f}\n"
        formula += f"R² = {r2:.4f}\n"
        formula += f"旋光率 = {coeffs[0] / self.tube_length:.2f} (°)/dm/(g/cm³)"
        
        messagebox.showinfo("计算结果", formula)
        self.update_parameters_display()
    
    def calculate_r_squared(self, x, y, coeffs):
        poly = np.poly1d(coeffs)
        y_pred = poly(x)
        y_mean = np.mean(y)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        return 1 - (ss_res / ss_tot)
    
    def clear_data(self):
        if messagebox.askyesno("确认", "确定要清空所有数据吗？"):
            self.rotation_data = [0.0, 0.0, 0.0, 0.0]
            for i in range(4):
                self.tree.item(str(i), values=(self.concentration_labels[i], ''))
            self.update_plot()
            self.update_parameters_display()
            messagebox.showinfo("完成", "数据已清空！")
    
    def export_data(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            data = {
                "concentration_labels": self.concentration_labels,
                "concentration_values": self.concentrations,
                "rotation_data": self.rotation_data,
                "C0": self.C0,
                "tube_length": self.tube_length,
                "theoretical_rotation": self.theoretical_rotation
            }
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                messagebox.showinfo("成功", f"数据已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def import_data(self):
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "rotation_data" in data:
                    self.rotation_data = data["rotation_data"]
                    for i in range(4):
                        value = self.rotation_data[i] if self.rotation_data[i] != 0 else ''
                        self.tree.item(str(i), values=(self.concentration_labels[i], value))
                    
                    self.update_plot()
                    self.update_parameters_display()
                    messagebox.showinfo("成功", "数据导入成功！")
                else:
                    messagebox.showwarning("格式错误", "文件格式不正确！")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {str(e)}")


def main():
    root = tk.Tk()
    app = PolarizationExperiment(root)
    root.mainloop()


if __name__ == "__main__":
    main()