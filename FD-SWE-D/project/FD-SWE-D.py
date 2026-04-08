import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import threading
import time
import os
import sys
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
import random
from PIL import Image, ImageTk
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

class StringVibrationSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("弦振动仿真系统")
        self.root.minsize(1500, 830)
        self.root.resizable(False, False)
        self.show_resonance_info = False  # 默认开启谐振频率提示
        self.string_tightened = False  # 初始为松开状态
        # 长按相关变量 - 为每个参数添加独立控制
        self.tension_increase_pressed = False
        self.tension_decrease_pressed = False
        self.length_increase_pressed = False
        self.length_decrease_pressed = False
        self.probe_increase_pressed = False
        self.probe_decrease_pressed = False

        self.long_press_delay = 300  # 长按延迟（毫秒）
        self.long_press_interval = 100  # 长按重复间隔（毫秒）
        self.tension_long_press_timer = None
        self.tension_long_press_repeat_timer = None
        self.length_long_press_timer = None
        self.length_long_press_repeat_timer = None
        self.probe_long_press_timer = None
        self.probe_long_press_repeat_timer = None

        # 实验仪按钮状态
        # 实验仪倍率设置 - 增加一个"none"表示不指向任何位
        self.instr_freq_multipliers = [1000, 100, 10, 1, 0.1, 0.01, None]  # None表示不指向任何位
        self.instr_freq_multiplier_labels = ["×1000", "×100", "×10", "×1", "×0.1", "×0.01", "无"]
        self.instr_freq_multiplier_index = 6  # 初始指向"无"（最后一个）

        # 调节步长设置 - 为每个参数单独设置
        self.freq_multipliers = [1000, 100, 10, 1, 0.1, 0.01]
        self.freq_multiplier_labels = ["×1000", "×100", "×10", "×1", "×0.1", "×0.01"]
        
        self.tension_multipliers = [1, 0.1, 0.01]
        self.tension_multiplier_labels = ["×1", "×0.1", "×0.01"]
        
        self.length_multipliers = [10, 1, 0.1]
        self.length_multiplier_labels = ["×10", "×1", "×0.1"]
        
        self.amplitude_multipliers = [100, 10, 1, 0.01]
        self.amplitude_multiplier_labels = ["×100", "×10", "×1", "×0.01"]
        
        # 初始化数据记录相关变量
        self.init_data_record_variables()
        # 每个参数的当前倍率索引
        self.freq_multiplier_index = 3  # 频率默认×1
        self.tension_multiplier_index = 0  # 拉力默认×1
        self.length_multiplier_index = 1  # 长度默认×1
        self.amplitude_multiplier_index = 2  # 振幅默认×1

        # 长按相关变量
        self.increase_pressed = False
        self.decrease_pressed = False
        self.long_press_delay = 300  # 长按延迟（毫秒）
        self.long_press_interval = 100  # 长按重复间隔（毫秒）
        self.long_press_timer = None
        self.long_press_repeat_timer = None
        
        # 初始参数
        self.frequency = 0.01  # Hz
        self.tension = 0  # kg
        # 修改初始化长度，确保不小于探测位置+10cm
        self.length = 50
        self.diameter = 0.7  # mm
        self.amplitude_mv = 100.0  # 振幅 (mV)
        self.string_tightened = False  # 初始为松开状态

        # 物理常数
        self.density_iron = 7.87  # g/cm³ 铁的密度
        
        # 振幅探测位置
        self.probe_position = 15.0  # 初始探测位置
        self.probe_amplitude = 0.0  # 探测到的振幅

        # 实验仪相关参数
        self.zero_offset = 0.0  # 拉力计调零偏移量
        self.random_offset = random.uniform(-0.3, 0.3)  # 随机偏移量
        self.display_mode = "tension"  # 显示模式：tension或vibration
        
        # 初始化 display_var
        self.display_var = tk.StringVar()
        self.display_var.set(f"拉力: {self.get_display_tension():.2f} kg")
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左侧框架（实验动画）
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建右侧框架（实验仪）
        right_frame = ttk.Frame(main_frame, width=800)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=0, pady=0)
        right_frame.pack_propagate(False)  # 防止框架收缩
        
        # 创建左侧matplotlib图形
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        
        # 初始化弦的位置
        self.x = np.linspace(0, self.length, 1000)
        self.y = np.zeros_like(self.x)
        
        # 绘制初始弦
        self.line, = self.ax.plot(self.x, self.y, 'b-', linewidth=2)
        # 绘制红色直线（从弦线末端到x=120）
        self.red_line, = self.ax.plot([self.length, 120], [0, 0], 'r-', linewidth=2)
        self.ax.set_xlim(0, 140)
        self.ax.set_ylim(-10, 10)
        self.ax.set_xlabel('位置 (cm)')
        self.ax.set_ylabel('振幅')
        self.ax.set_title('弦振动仿真')
        self.ax.grid(True)
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.25, top=0.75)
        #self.ax.set_axis_off()  # 完全隐藏坐标轴
        # 或者只隐藏坐标轴刻度但保留边框：
        # self.ax.set_xticks([])  # 隐藏x轴刻度
        self.ax.set_yticks([])  # 隐藏y轴刻度
        # self.ax.set_xlabel('')  # 清空x轴标签
        self.ax.set_ylabel('')  # 清空y轴标签
        # self.ax.set_title('')   # 清空标题
        
        # 添加共振频率提示文本
        self.resonance_text = self.ax.text(0.02, 0.8, '', transform=self.ax.transAxes, 
                                        fontsize=10, color='red', weight='bold')
        
        # # 添加振幅探测显示文本
        # self.probe_text = self.ax.text(0.02, 0.85, '', transform=self.ax.transAxes,
        #                             fontsize=9, color='blue', weight='bold')

        # 将matplotlib图形嵌入到左侧框架
        self.canvas = FigureCanvasTkAgg(self.fig, master=left_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=False)
        
        # 在左侧框架底部创建控制面板
        self.create_control_panel(left_frame)
        
        # 创建右侧实验仪界面
        self.create_experiment_panel(right_frame)
        
        self.create_data_record_area(right_frame)
        # 计算并显示共振频率
        self.update_resonance_info()
        
        # 动画控制
        self.time = 0
        self.running = True
        self.animation_thread = threading.Thread(target=self.animation_loop)
        self.animation_thread.daemon = True
        self.animation_thread.start()
        self.load_background_images()

        # 绑定自动更新
        self.T1_kgf_var.trace('w', self.update_T1_N)
        self.T2_kgf_var.trace('w', self.update_T2_N)
        self.d3_var.trace('w', lambda *args: self.update_mu3_data())
        
        # 绑定L变量的自动更新
        for i, var in enumerate(self.L2_vars):
            var.trace('w', lambda *args, idx=i: self.update_single_invL2_data(idx))
        
        # 绑定关系3的自动更新
        for i, var in enumerate(self.T3_kgf_vars):
            var.trace('w', lambda *args, idx=i: self.update_single_relation3_data(idx))
        for i, var in enumerate(self.f3_vars):
            var.trace('w', lambda *args, idx=i: self.update_single_relation3_data(idx))
        self.L3_var.trace('w', lambda *args: self.update_relation3_calculations())
        self.n3_var.trace('w', lambda *args: self.update_relation3_calculations())

        self.disable_controls()
    # def check_image_file(file_path):
    #     """检查图片文件是否有效"""
    #     try:
    #         with Image.open(file_path) as img:
    #             print(f"图片格式: {img.format}")
    #             print(f"图片尺寸: {img.size}")
    #             print(f"图片模式: {img.mode}")
    #             return True
    #     except Exception as e:
    #         print(f"图片文件无效: {e}")
    #         return False
    
    def init_data_record_variables(self):
        """初始化数据记录相关变量"""
        # 关系1的变量
        self.d1_var = tk.StringVar(value="")
        self.L1_var = tk.StringVar(value="")
        self.T1_kgf_var = tk.StringVar(value="")
        self.T1_N_var = tk.StringVar()
        self.f1_vars = [tk.StringVar() for _ in range(8)]
        self.n1_vars = [tk.StringVar() for _ in range(8)]
        self.k1_fit_var = tk.StringVar()
        self.k1_theory_var = tk.StringVar()
        
        # 关系2的变量
        self.d2_var = tk.StringVar(value="")
        self.n2_var = tk.StringVar(value="")
        self.T2_kgf_var = tk.StringVar(value="")
        self.T2_N_var = tk.StringVar()
        self.L2_vars = [tk.StringVar() for _ in range(12)]
        self.invL2_vars = [tk.StringVar() for _ in range(12)]
        self.f2_vars = [tk.StringVar() for _ in range(12)]
        self.k2_fit_var = tk.StringVar()
        self.k2_theory_var = tk.StringVar()
        
        # 关系3的变量
        self.d3_var = tk.StringVar(value="")
        self.mu3_var = tk.StringVar()
        self.n3_var = tk.StringVar(value="")
        self.L3_var = tk.StringVar(value="")
        self.T3_kgf_vars = [tk.StringVar() for _ in range(8)]
        self.T3_N_vars = [tk.StringVar() for _ in range(8)]
        self.f3_vars = [tk.StringVar() for _ in range(8)]
        self.f3_sq_vars = [tk.StringVar() for _ in range(8)]
        self.V3_calc_vars = [tk.StringVar() for _ in range(8)]
        self.V3_theory_vars = [tk.StringVar() for _ in range(8)]
        self.k3_fit_var = tk.StringVar()
        self.k3_theory_var = tk.StringVar()

    def create_experiment_panel(self, parent):
        """创建右侧实验仪面板"""
        
        instrument_path = get_resource_path(os.path.join('background', '实验仪.jpg'))
        print(f"尝试加载图片: {instrument_path}")
        print(f"文件是否存在: {os.path.exists(instrument_path)}")
        
        if os.path.exists(instrument_path):
            # 检查文件大小
            file_size = os.path.getsize(instrument_path)
            print(f"文件大小: {file_size} 字节")
            
            # 检查图片有效性
            # if self.check_image_file(instrument_path):
            try:
                # 创建画布用于显示背景图片
                self.instrument_canvas = tk.Canvas(parent, width=800, height=305, bg='white')
                self.instrument_canvas.pack(fill=tk.BOTH, expand=True)
                
                # 使用 PIL 加载并显示背景图片
                pil_image = Image.open(instrument_path)
                # 调整图片大小以适应画布
                pil_image = pil_image.resize((800, 305), Image.Resampling.LANCZOS)
                self.instrument_bg = ImageTk.PhotoImage(pil_image)
                
                self.instrument_canvas.create_image(0, 0, anchor=tk.NW, image=self.instrument_bg)
                
                # 在背景图片上叠加控件
                self.create_instrument_controls()
                return
            except Exception as e:
                print(f"使用 PIL 加载图片失败: {e}")
        
        print("图片加载失败，使用默认界面")
        self.create_default_instrument_panel(parent)
        # else:
        #     print("图片文件不存在，使用默认界面")
        #     self.create_default_instrument_panel(parent)

            
    def create_data_record_area(self, parent):
        """创建数据记录区域"""
        # 创建主框架 - 去掉边距，紧贴上方
        data_frame = ttk.Frame(parent)
        data_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)  # 去掉边距
        
        # 创建选项卡按钮组 - 减少上边距
        tab_frame = ttk.Frame(data_frame)
        tab_frame.pack(fill=tk.X, pady=(2, 5))  # 上边距2，下边距5
        
        self.tab_var = tk.StringVar(value="relation1")
        
        ttk.Radiobutton(tab_frame, text="验证弦线波腹数与共振频率的关系", 
                    variable=self.tab_var, value="relation1",
                    command=self.on_tab_changed).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(tab_frame, text="验证共振频率与弦长的关系", 
                    variable=self.tab_var, value="relation2",
                    command=self.on_tab_changed).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(tab_frame, text="验证弦线共振频率、传播速度与张力、线密度的关系", 
                    variable=self.tab_var, value="relation3",
                    command=self.on_tab_changed).pack(side=tk.LEFT, padx=5)
        
        # 创建内容区域 - 去掉边距
        self.content_frame = ttk.Frame(data_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)  # 去掉边距
        
        # 初始化第一个选项卡
        self.on_tab_changed()

    def on_tab_changed(self):
        """选项卡切换事件"""
        # 清空内容区域
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        tab_type = self.tab_var.get()
        
        if tab_type == "relation1":
            self.create_relation1_content()
        elif tab_type == "relation2":
            self.create_relation2_content()
        elif tab_type == "relation3":
            self.create_relation3_content()

    def create_relation1_content(self):
        """创建关系1的内容"""
        # 实验条件框架
        condition_frame = ttk.Frame(self.content_frame)
        condition_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 实验条件输入
        ttk.Label(condition_frame, text="弦线线径d (mm):").grid(row=0, column=0, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.d1_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(condition_frame, text="弦长L (cm):").grid(row=0, column=2, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.L1_var, width=10).grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(condition_frame, text="张力T (kgf):").grid(row=0, column=4, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.T1_kgf_var, width=10).grid(row=0, column=5, padx=5, pady=2)
        
        ttk.Label(condition_frame, text="张力T (N):").grid(row=0, column=6, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.T1_N_var, width=10, state='readonly').grid(row=0, column=7, padx=5, pady=2)
        
        # 表格框架
        table_frame = ttk.Frame(self.content_frame)
        table_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建表格
        self.create_relation1_table(table_frame)
        
        # 图表框架
        chart_frame = ttk.Frame(self.content_frame)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建图表
        self.create_relation1_chart(chart_frame)
        # 创建完成后立即重绘（如果有数据）
        self.root.after(100, self.redraw_relation1_chart)  # 延迟100ms确保组件完全创建

        # 计算结果框架
        result_frame = ttk.Frame(self.content_frame)
        result_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(result_frame, text="拟合斜率k1(s):").grid(row=0, column=0, padx=5)
        ttk.Entry(result_frame, textvariable=self.k1_fit_var, width=15, state='readonly').grid(row=0, column=1, padx=5)
        
        ttk.Label(result_frame, text="理论值K1(s):").grid(row=0, column=2, padx=5)
        ttk.Entry(result_frame, textvariable=self.k1_theory_var, width=15, state='readonly').grid(row=0, column=3, padx=5)
        
        ttk.Button(result_frame, text="计算", command=self.calculate_relation1).grid(row=0, column=4, padx=5)
        ttk.Button(result_frame, text="清空数据", command=self.clear_relation1_data).grid(row=0, column=5, padx=5)
        
        # 导入导出按钮
        io_frame = ttk.Frame(self.content_frame)
        io_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(io_frame, text="导入数据", command=self.import_relation1_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="导出数据", command=self.export_relation1_data).pack(side=tk.LEFT, padx=5)

    def redraw_relation1_chart(self):
        """重绘关系1的图表"""
        try:
            # 获取有效数据
            f_values = []
            n_values = []
            
            for i in range(8):
                f_val = self.f1_vars[i].get()
                n_val = self.n1_vars[i].get()
                if f_val and n_val:
                    f_values.append(float(f_val))
                    n_values.append(float(n_val))
            
            # 如果有数据且已经计算过拟合结果，重新绘制拟合直线
            if len(f_values) >= 2 and self.k1_fit_var.get():
                # 线性拟合
                f_array = np.array(f_values)
                n_array = np.array(n_values)
                slope, intercept = np.polyfit(f_array, n_array, 1)
                
                # 清空并重绘图表
                self.relation1_ax.clear()
                self.relation1_ax.scatter(f_values, n_values, color='blue', label='实验数据')
                
                # 绘制拟合直线
                f_fit = np.linspace(min(f_values), max(f_values), 100)
                n_fit = slope * f_fit + intercept
                
                # 显示拟合直线公式
                if intercept >= 0:
                    equation = f'n = {slope:.4f}f + {intercept:.4f}'
                else:
                    equation = f'n = {slope:.4f}f - {abs(intercept):.4f}'
                
                self.relation1_ax.plot(f_fit, n_fit, 'r-', label=equation)
                
            elif len(f_values) > 0:
                # 只有数据点，没有拟合结果
                self.relation1_ax.clear()
                self.relation1_ax.scatter(f_values, n_values, color='blue', label='实验数据')
            
            else:
                # 没有数据，清空图表
                self.relation1_ax.clear()
            
            # 设置图表属性
            self.relation1_ax.set_xlabel('共振频率 f(Hz)')
            self.relation1_ax.set_ylabel('波腹数 n')
            self.relation1_ax.grid(True)
            if len(f_values) > 0:
                self.relation1_ax.legend()
            
            # 调整边距
            self.relation1_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            
            # 刷新图表
            self.relation1_fig.canvas.draw()
            
        except Exception as e:
            # 如果重绘失败，初始化一个空图表
            self.relation1_ax.clear()
            self.relation1_ax.set_xlabel('共振频率 f(Hz)')
            self.relation1_ax.set_ylabel('波腹数 n')
            self.relation1_ax.grid(True)
            self.relation1_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            self.relation1_fig.canvas.draw()

    def clear_relation1_data(self):
        """清空关系1的数据"""
        # 确认对话框
        result = tk.messagebox.askyesno("确认清空", "确定要清空所有数据吗？此操作不可撤销！")
        if not result:
            return
        
        try:
            # 清空实验条件
            self.d1_var.set("")
            self.L1_var.set("")
            self.T1_kgf_var.set("")
            self.T1_N_var.set("")
            
            # 清空表格数据
            for var in self.f1_vars:
                var.set("")
            for var in self.n1_vars:
                var.set("")
            
            # 清空计算结果
            self.k1_fit_var.set("")
            self.k1_theory_var.set("")
            
            # 清空图表
            self.relation1_ax.clear()
            self.relation1_ax.set_xlabel('共振频率 f(Hz)')
            self.relation1_ax.set_ylabel('波腹数 n')
            self.relation1_ax.grid(True)
            self.relation1_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            self.relation1_fig.canvas.draw()
            
            tk.messagebox.showinfo("成功", "数据已清空")
            
        except Exception as e:
            tk.messagebox.showerror("错误", f"清空数据时发生错误: {str(e)}")

    def create_relation1_table(self, parent):
        """创建关系1的表格"""
        # 表头
        headers = ["项目", "1", "2", "3", "4", "5", "6", "7", "8"]
        for i, header in enumerate(headers):
            ttk.Label(parent, text=header, borderwidth=1, relief="solid", width=10).grid(row=0, column=i, padx=1, pady=1)
        
        # 共振频率行
        ttk.Label(parent, text="共振频率 f(Hz)", borderwidth=1, relief="solid", width=12).grid(row=1, column=0, padx=1, pady=1)
        for i in range(8):
            ttk.Entry(parent, textvariable=self.f1_vars[i], width=10).grid(row=1, column=i+1, padx=1, pady=1)
        
        # 波腹数行
        ttk.Label(parent, text="波腹数 n", borderwidth=1, relief="solid", width=12).grid(row=2, column=0, padx=1, pady=1)
        for i in range(8):
            ttk.Entry(parent, textvariable=self.n1_vars[i], width=10).grid(row=2, column=i+1, padx=1, pady=1)

    def create_relation1_chart(self, parent):
        """创建关系1的图表 - 减小高度并调整边距"""
        fig, ax = plt.subplots(figsize=(6, 2.85))  # 稍微增加高度到2.5
        self.relation1_fig = fig
        self.relation1_ax = ax
        self.relation1_ax.set_xlabel('共振频率 f(Hz)')
        self.relation1_ax.set_ylabel('波腹数 n')
        self.relation1_ax.grid(True)
        
        # 调整边距，确保坐标轴标签可见
        fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def calculate_relation1(self):
        """计算关系1"""
        try:
            # 获取实验数据
            f_values = []
            n_values = []
            
            for i in range(8):
                f_val = self.f1_vars[i].get()
                n_val = self.n1_vars[i].get()
                if f_val and n_val:
                    f_values.append(float(f_val))
                    n_values.append(float(n_val))
            
            if len(f_values) < 2:
                tk.messagebox.showwarning("警告", "请至少输入2组有效数据")
                return
            
            # 线性拟合
            f_array = np.array(f_values)
            n_array = np.array(n_values)
            
            # 使用numpy进行线性拟合
            slope, intercept = np.polyfit(f_array, n_array, 1)
            
            # 计算理论值
            d_mm = float(self.d1_var.get())
            L_cm = float(self.L1_var.get())
            T_kgf = float(self.T1_kgf_var.get())
            
            # 计算线密度
            mu = self.calculate_linear_density(d_mm)  # kg/m
            T_N = T_kgf * 9.8  # N
            
            # 理论斜率 K1 = 2L * sqrt(μ/T)
            L_m = L_cm / 100  # 转换为米
            K1_theory = 2 * L_m * np.sqrt(mu / T_N)
            
            # 更新显示
            self.k1_fit_var.set(f"{slope:.4f}")
            self.k1_theory_var.set(f"{K1_theory:.4f}")
            
            # 更新图表
            self.relation1_ax.clear()
            self.relation1_ax.scatter(f_values, n_values, color='blue', label='实验数据')
            
            # 绘制拟合直线
            f_fit = np.linspace(min(f_values), max(f_values), 100)
            n_fit = slope * f_fit + intercept
            
            # 显示拟合直线公式
            if intercept >= 0:
                equation = f'n = {slope:.4f}f + {intercept:.4f}'
            else:
                equation = f'n = {slope:.4f}f - {abs(intercept):.4f}'
            
            self.relation1_ax.plot(f_fit, n_fit, 'r-', label=equation)
            
            self.relation1_ax.set_xlabel('共振频率 f(Hz)')
            self.relation1_ax.set_ylabel('波腹数 n')
            self.relation1_ax.grid(True)
            self.relation1_ax.legend()
            
            # 调整边距，确保坐标轴标签可见
            self.relation1_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            
            # 刷新图表
            self.relation1_fig.canvas.draw()
            
        except ValueError as e:
            tk.messagebox.showerror("错误", f"数据格式错误: {str(e)}")
        except Exception as e:
            tk.messagebox.showerror("错误", f"计算失败: {str(e)}")

    def import_relation1_data(self):
        """导入关系1数据"""
        try:
            file_path = tk.filedialog.askopenfilename(
                title="选择Excel文件",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if not file_path:
                return
            
            import pandas as pd
            df = pd.read_excel(file_path, header=None)  # 不读取表头
            
            # 重新组织数据读取逻辑
            data_dict = {}
            current_section = None
            
            for index, row in df.iterrows():
                if pd.notna(row[0]):
                    key = str(row[0]).strip()
                    if key == '实验条件':
                        current_section = 'conditions'
                        continue
                    elif key == '项目':
                        current_section = 'table_header'
                        continue
                    elif key == '拟合斜率k1(s)':
                        current_section = 'results'
                        data_dict['k1_fit'] = str(row[1]) if pd.notna(row[1]) else ""
                        continue
                    elif key == '理论值K1(s)':
                        data_dict['k1_theory'] = str(row[1]) if pd.notna(row[1]) else ""
                        continue
                    elif key == '':
                        continue
                    
                    if current_section == 'conditions':
                        if key == '弦线线径d (mm)':
                            data_dict['d1'] = str(row[1]) if pd.notna(row[1]) else ""
                        elif key == '弦长L (cm)':
                            data_dict['L1'] = str(row[1]) if pd.notna(row[1]) else ""
                        elif key == '张力T (kgf)':
                            data_dict['T1_kgf'] = str(row[1]) if pd.notna(row[1]) else ""
                    
                    elif current_section == 'table_header':
                        if key == '共振频率 f(Hz)':
                            # 读取共振频率数据
                            f_data = []
                            for i in range(1, 7):
                                if i < len(row) and pd.notna(row[i]):
                                    f_data.append(str(row[i]))
                                else:
                                    f_data.append("")
                            data_dict['f_data'] = f_data
                        
                        elif key == '波腹数 n':
                            # 读取波腹数数据 - 处理为整数
                            n_data = []
                            for i in range(1, 7):
                                if i < len(row) and pd.notna(row[i]):
                                    # 尝试转换为整数
                                    try:
                                        n_value = float(row[i])
                                        if n_value.is_integer():
                                            n_data.append(str(int(n_value)))
                                        else:
                                            n_data.append(str(row[i]))
                                    except:
                                        n_data.append(str(row[i]))
                                else:
                                    n_data.append("")
                            data_dict['n_data'] = n_data
        
            
            # 更新UI
            if 'd1' in data_dict:
                self.d1_var.set(data_dict['d1'])
            if 'L1' in data_dict:
                self.L1_var.set(data_dict['L1'])
            if 'T1_kgf' in data_dict:
                self.T1_kgf_var.set(data_dict['T1_kgf'])
            
            if 'f_data' in data_dict:
                for i, value in enumerate(data_dict['f_data']):
                    if i < len(self.f1_vars):
                        self.f1_vars[i].set(value)
            
            if 'n_data' in data_dict:
                for i, value in enumerate(data_dict['n_data']):
                    if i < len(self.n1_vars):
                        self.n1_vars[i].set(value)
            
            if 'k1_fit' in data_dict:
                self.k1_fit_var.set(data_dict['k1_fit'])
            if 'k1_theory' in data_dict:
                self.k1_theory_var.set(data_dict['k1_theory'])
            self.redraw_relation1_chart()
            tk.messagebox.showinfo("成功", "数据导入成功")
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas和openpyxl库: pip install pandas openpyxl")
        except Exception as e:
            tk.messagebox.showerror("错误", f"导入失败: {str(e)}\n请检查Excel文件格式是否正确")
            import traceback
            print(traceback.format_exc())

    def export_relation1_data(self):
        """导出关系1数据"""
        try:
            file_path = tk.filedialog.asksaveasfilename(
                title="保存Excel文件",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if not file_path:
                return
            
            import pandas as pd
            
            # 创建数据框 - 使用更清晰的格式
            data = []
            
            # 实验条件部分
            data.append(['实验条件', '', '', '', '', '', ''])
            data.append(['弦线线径d (mm)', self.d1_var.get(), '', '', '', '', ''])
            data.append(['弦长L (cm)', self.L1_var.get(), '', '', '', '', ''])
            data.append(['张力T (kgf)', self.T1_kgf_var.get(), '', '', '', '', ''])
            data.append(['', '', '', '', '', '', ''])  # 空行分隔
            
            # 表格数据部分
            headers = ['项目', '1', '2', '3', '4', '5', '6']
            data.append(headers)
            
            # 共振频率数据
            f_row = ['共振频率 f(Hz)']
            for var in self.f1_vars:
                f_row.append(var.get() if var.get() else '')
            data.append(f_row)
            
            # 波腹数数据
            n_row = ['波腹数 n']
            for var in self.n1_vars:
                n_row.append(var.get() if var.get() else '')
            data.append(n_row)
            
            data.append(['', '', '', '', '', '', ''])  # 空行分隔
            
            # 计算结果部分
            data.append(['拟合斜率k1(s)', self.k1_fit_var.get(), '', '', '', '', ''])
            data.append(['理论值K1(s)', self.k1_theory_var.get(), '', '', '', '', ''])
            
            # 创建DataFrame并保存
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, header=False)
            
            tk.messagebox.showinfo("成功", f"数据已导出到: {file_path}")
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas和openpyxl库: pip install pandas openpyxl")
        except Exception as e:
            tk.messagebox.showerror("错误", f"导出失败: {str(e)}")

    def create_relation2_content(self):
        """创建关系2的内容"""
        # 实验条件框架
        condition_frame = ttk.Frame(self.content_frame)
        condition_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 实验条件输入
        ttk.Label(condition_frame, text="弦线线径d (mm):").grid(row=0, column=0, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.d2_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(condition_frame, text="波腹数n:").grid(row=0, column=2, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.n2_var, width=10).grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(condition_frame, text="张力T (kgf):").grid(row=0, column=4, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.T2_kgf_var, width=10).grid(row=0, column=5, padx=5, pady=2)
        
        ttk.Label(condition_frame, text="张力T (N):").grid(row=0, column=6, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.T2_N_var, width=10, state='readonly').grid(row=0, column=7, padx=5, pady=2)
        
        # 表格框架
        table_frame = ttk.Frame(self.content_frame)
        table_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建表格
        self.create_relation2_table(table_frame)
        
        # 图表框架
        chart_frame = ttk.Frame(self.content_frame)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建图表
        self.create_relation2_chart(chart_frame)
        
        # 计算结果框架
        result_frame = ttk.Frame(self.content_frame)
        result_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(result_frame, text="拟合斜率k2(m/s):").grid(row=0, column=0, padx=5)
        ttk.Entry(result_frame, textvariable=self.k2_fit_var, width=15, state='readonly').grid(row=0, column=1, padx=5)
        
        ttk.Label(result_frame, text="理论值K2(m/s):").grid(row=0, column=2, padx=5)
        ttk.Entry(result_frame, textvariable=self.k2_theory_var, width=15, state='readonly').grid(row=0, column=3, padx=5)
        
        ttk.Button(result_frame, text="计算", command=self.calculate_relation2).grid(row=0, column=4, padx=5)
        ttk.Button(result_frame, text="清空数据", command=self.clear_relation2_data).grid(row=0, column=5, padx=5)
        
        # 导入导出按钮
        io_frame = ttk.Frame(self.content_frame)
        io_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(io_frame, text="导入数据", command=self.import_relation2_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="导出数据", command=self.export_relation2_data).pack(side=tk.LEFT, padx=5)
        
        # 创建完成后立即重绘（如果有数据）
        self.root.after(100, self.redraw_relation2_chart)

    def create_relation2_table(self, parent):
        """创建关系2的表格"""
        # 表头
        headers = ["项目"] + [str(i+1) for i in range(10)]
        for i, header in enumerate(headers):
            if i == 0:
                # 第一列宽度增大
                ttk.Label(parent, text=header, borderwidth=1, relief="solid", width=12).grid(row=0, column=i, padx=1, pady=1)
            else:
                ttk.Label(parent, text=header, borderwidth=1, relief="solid", width=8).grid(row=0, column=i, padx=1, pady=1)
        
        # 弦长L行 - 第一列宽度增大
        ttk.Label(parent, text="弦长L (cm)", borderwidth=1, relief="solid", width=12).grid(row=1, column=0, padx=1, pady=1)
        for i in range(10):
            ttk.Entry(parent, textvariable=self.L2_vars[i], width=8).grid(row=1, column=i+1, padx=1, pady=1)
        
        # 1/L行 - 第一列宽度增大
        ttk.Label(parent, text="1/L (1/m)", borderwidth=1, relief="solid", width=12).grid(row=2, column=0, padx=1, pady=1)
        for i in range(10):
            ttk.Entry(parent, textvariable=self.invL2_vars[i], width=8, state='readonly').grid(row=2, column=i+1, padx=1, pady=1)
        
        # 共振频率f行 - 第一列宽度增大
        ttk.Label(parent, text="共振频率f (Hz)", borderwidth=1, relief="solid", width=12).grid(row=3, column=0, padx=1, pady=1)
        for i in range(10):
            ttk.Entry(parent, textvariable=self.f2_vars[i], width=8).grid(row=3, column=i+1, padx=1, pady=1)

    def create_relation2_chart(self, parent):
        """创建关系2的图表"""
        fig, ax = plt.subplots(figsize=(6, 2.6))
        self.relation2_fig = fig
        self.relation2_ax = ax
        self.relation2_ax.set_xlabel('1/L (1/m)')
        self.relation2_ax.set_ylabel('共振频率 f(Hz)')
        self.relation2_ax.grid(True)
        
        # 调整边距
        fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_single_invL2_data(self, index):
        """更新单个1/L数据"""
        try:
            L_val = self.L2_vars[index].get()
            if L_val:
                L_cm = float(L_val)
                if L_cm > 0:
                    invL_cm = 1 / L_cm
                    invL_m = invL_cm * 100  # 转换为m⁻¹ (1/cm * 100 = 1/m)
                    self.invL2_vars[index].set(f"{invL_m:.2f}")  # 显示为m⁻¹
                else:
                    self.invL2_vars[index].set("")
            else:
                self.invL2_vars[index].set("")
        except:
            self.invL2_vars[index].set("")

    def calculate_relation2(self):
        """计算关系2"""
        try:
            # 获取实验数据
            invL_values = []
            f_values = []
            
            for i in range(10):
                L_val = self.L2_vars[i].get()
                f_val = self.f2_vars[i].get()
                if L_val and f_val:
                    L_cm = float(L_val)
                    if L_cm > 0:  # 避免除零错误
                        invL_cm = 1 / L_cm  # 1/cm
                        invL_m = invL_cm * 100  # 转换为1/m
                        invL_values.append(invL_m)
                        f_values.append(float(f_val))
            
            if len(invL_values) < 2:
                tk.messagebox.showwarning("警告", "请至少输入2组有效数据")
                return
            
            # 线性拟合
            invL_array = np.array(invL_values)
            f_array = np.array(f_values)
            
            slope, intercept = np.polyfit(invL_array, f_array, 1)
            
            # 计算理论值
            d_mm = float(self.d2_var.get()) if self.d2_var.get() else 0.7
            n = float(self.n2_var.get()) if self.n2_var.get() else 1
            T_kgf = float(self.T2_kgf_var.get()) if self.T2_kgf_var.get() else 2.0
            
            # 计算线密度
            mu = self.calculate_linear_density(d_mm)  # kg/m
            T_N = T_kgf * 9.8  # N
            
            # 理论斜率 K2 = sqrt(T/μ) / 2
            K2_theory = np.sqrt(T_N / mu) / 2 *n
            
            # 更新显示
            self.k2_fit_var.set(f"{slope:.1f}")
            self.k2_theory_var.set(f"{K2_theory:.1f}")
            
            # 更新图表
            self.relation2_ax.clear()
            self.relation2_ax.scatter(invL_values, f_values, color='blue', label='实验数据')
            
            # 绘制拟合直线
            invL_fit = np.linspace(min(invL_values), max(invL_values), 100)
            f_fit = slope * invL_fit + intercept
            
            # 显示拟合直线公式
            if intercept >= 0:
                equation = f'f = {slope:.1f}(1/L) + {intercept:.1f}'
            else:
                equation = f'f = {slope:.1f}(1/L) - {abs(intercept):.1f}'
            
            self.relation2_ax.plot(invL_fit, f_fit, 'r-', label=equation)
            
            self.relation2_ax.set_xlabel('1/L (1/m)')
            self.relation2_ax.set_ylabel('共振频率 f(Hz)')
            self.relation2_ax.grid(True)
            self.relation2_ax.legend()
            
            # 调整边距
            self.relation2_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            
            # 刷新图表
            self.relation2_fig.canvas.draw()
            
        except ValueError as e:
            tk.messagebox.showerror("错误", f"数据格式错误: {str(e)}")
        except Exception as e:
            tk.messagebox.showerror("错误", f"计算失败: {str(e)}")

    def redraw_relation2_chart(self):
        """重绘关系2的图表"""
        try:
            # 获取有效数据
            invL_values = []
            f_values = []
            
            for i in range(10):
                L_val = self.L2_vars[i].get()
                f_val = self.f2_vars[i].get()
                if L_val and f_val:
                    L_cm = float(L_val)
                    if L_cm > 0:
                        invL_cm = 1 / L_cm
                        invL_m = invL_cm * 100
                        invL_values.append(invL_m)
                        f_values.append(float(f_val))
            
            # 如果有数据且已经计算过拟合结果，重新绘制拟合直线
            if len(invL_values) >= 2 and self.k2_fit_var.get():
                # 线性拟合
                invL_array = np.array(invL_values)
                f_array = np.array(f_values)
                slope, intercept = np.polyfit(invL_array, f_array, 1)
                
                # 清空并重绘图表
                self.relation2_ax.clear()
                self.relation2_ax.scatter(invL_values, f_values, color='blue', label='实验数据')
                
                # 绘制拟合直线
                invL_fit = np.linspace(min(invL_values), max(invL_values), 100)
                f_fit = slope * invL_fit + intercept
                
                # 显示拟合直线公式
                if intercept >= 0:
                    equation = f'f = {slope:.1f}(1/L) + {intercept:.1f}'
                else:
                    equation = f'f = {slope:.1f}(1/L) - {abs(intercept):.1f}'
                
                self.relation2_ax.plot(invL_fit, f_fit, 'r-', label=equation)
                
            elif len(invL_values) > 0:
                # 只有数据点，没有拟合结果
                self.relation2_ax.clear()
                self.relation2_ax.scatter(invL_values, f_values, color='blue', label='实验数据')
            
            else:
                # 没有数据，清空图表
                self.relation2_ax.clear()
            
            # 设置图表属性
            self.relation2_ax.set_xlabel('1/L (1/m)')
            self.relation2_ax.set_ylabel('共振频率 f(Hz)')
            self.relation2_ax.grid(True)
            if len(invL_values) > 0:
                self.relation2_ax.legend()
            
            # 调整边距
            self.relation2_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            
            # 刷新图表
            self.relation2_fig.canvas.draw()
            
        except Exception as e:
            # 如果重绘失败，初始化一个空图表
            self.relation2_ax.clear()
            self.relation2_ax.set_xlabel('1/L (1/m)')
            self.relation2_ax.set_ylabel('共振频率 f(Hz)')
            self.relation2_ax.grid(True)
            self.relation2_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            self.relation2_fig.canvas.draw()

    def clear_relation2_data(self):
        """清空关系2的数据"""
        result = tk.messagebox.askyesno("确认清空", "确定要清空所有数据吗？此操作不可撤销！")
        if not result:
            return
        
        try:
            # 清空实验条件
            self.d2_var.set("")
            self.n2_var.set("")
            self.T2_kgf_var.set("")
            self.T2_N_var.set("")
            
            # 清空表格数据
            for var in self.L2_vars:
                var.set("")
            for var in self.invL2_vars:
                var.set("")
            for var in self.f2_vars:
                var.set("")
            
            # 清空计算结果
            self.k2_fit_var.set("")
            self.k2_theory_var.set("")
            
            # 清空图表
            self.relation2_ax.clear()
            self.relation2_ax.set_xlabel('1/L (1/m)')
            self.relation2_ax.set_ylabel('共振频率 f(Hz)')
            self.relation2_ax.grid(True)
            self.relation2_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            self.relation2_fig.canvas.draw()
            
            tk.messagebox.showinfo("成功", "数据已清空")
            
        except Exception as e:
            tk.messagebox.showerror("错误", f"清空数据时发生错误: {str(e)}")

    def import_relation2_data(self):
        """导入关系2数据"""
        try:
            file_path = tk.filedialog.askopenfilename(
                title="选择Excel文件",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if not file_path:
                return
            
            import pandas as pd
            df = pd.read_excel(file_path, header=None)
            
            data_dict = {}
            current_section = None
            
            for index, row in df.iterrows():
                if pd.notna(row[0]):
                    key = str(row[0]).strip()
                    if key == '实验条件':
                        current_section = 'conditions'
                        continue
                    elif key == '项目':
                        current_section = 'table_header'
                        continue
                    elif key == '拟合斜率k2(m/s)':
                        current_section = 'results'
                        data_dict['k2_fit'] = str(row[1]) if pd.notna(row[1]) else ""
                        continue
                    elif key == '理论值K2(m/s)':
                        data_dict['k2_theory'] = str(row[1]) if pd.notna(row[1]) else ""
                        continue
                    elif key == '':
                        continue
                    
                    if current_section == 'conditions':
                        if key == '弦线线径d (mm)':
                            data_dict['d2'] = str(row[1]) if pd.notna(row[1]) else ""
                        elif key == '波腹数n':
                            data_dict['n2'] = str(row[1]) if pd.notna(row[1]) else ""
                        elif key == '张力T (kgf)':
                            data_dict['T2_kgf'] = str(row[1]) if pd.notna(row[1]) else ""
                    
                    elif current_section == 'table_header':
                        if key == '弦长L (cm)':
                            L_data = []
                            for i in range(1, 13):
                                if i < len(row) and pd.notna(row[i]):
                                    L_data.append(str(row[i]))
                                else:
                                    L_data.append("")
                            data_dict['L_data'] = L_data
                        
                        elif key == '共振频率f (Hz)':
                            f_data = []
                            for i in range(1, 13):
                                if i < len(row) and pd.notna(row[i]):
                                    f_data.append(str(row[i]))
                                else:
                                    f_data.append("")
                            data_dict['f_data'] = f_data
            
            # 更新UI
            if 'd2' in data_dict:
                self.d2_var.set(data_dict['d2'])
            if 'n2' in data_dict:
                self.n2_var.set(data_dict['n2'])
            if 'T2_kgf' in data_dict:
                self.T2_kgf_var.set(data_dict['T2_kgf'])
            
            if 'L_data' in data_dict:
                for i, value in enumerate(data_dict['L_data']):
                    if i < len(self.L2_vars):
                        self.L2_vars[i].set(value)
            
            if 'f_data' in data_dict:
                for i, value in enumerate(data_dict['f_data']):
                    if i < len(self.f2_vars):
                        self.f2_vars[i].set(value)
            
            if 'k2_fit' in data_dict:
                self.k2_fit_var.set(data_dict['k2_fit'])
            if 'k2_theory' in data_dict:
                self.k2_theory_var.set(data_dict['k2_theory'])
                
            # 更新1/L数据
            self.update_invL2_data()
            self.redraw_relation2_chart()
            tk.messagebox.showinfo("成功", "数据导入成功")
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas和openpyxl库: pip install pandas openpyxl")
        except Exception as e:
            tk.messagebox.showerror("错误", f"导入失败: {str(e)}")

    def export_relation2_data(self):
        """导出关系2数据"""
        try:
            file_path = tk.filedialog.asksaveasfilename(
                title="保存Excel文件",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if not file_path:
                return
            
            import pandas as pd
            
            # 创建数据框
            data = []
            
            # 实验条件部分
            data.append(['实验条件', '', '', '', '', '', '', '', '', '', '', '', ''])
            data.append(['弦线线径d (mm)', self.d2_var.get(), '', '', '', '', '', '', '', '', '', '', ''])
            data.append(['波腹数n', self.n2_var.get(), '', '', '', '', '', '', '', '', '', '', ''])
            data.append(['张力T (kgf)', self.T2_kgf_var.get(), '', '', '', '', '', '', '', '', '', '', ''])
            data.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
            
            # 表格数据部分
            headers = ['项目', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
            data.append(headers)
            
            # 弦长L数据
            L_row = ['弦长L (cm)']
            for var in self.L2_vars:
                L_row.append(var.get() if var.get() else '')
            data.append(L_row)
            
            # 1/L数据
            invL_row = ['1/L (1/m)']
            for var in self.invL2_vars:
                invL_row.append(var.get() if var.get() else '')
            data.append(invL_row)
            
            # 共振频率数据
            f_row = ['共振频率f (Hz)']
            for var in self.f2_vars:
                f_row.append(var.get() if var.get() else '')
            data.append(f_row)
            
            data.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
            
            # 计算结果部分
            data.append(['拟合斜率k2(m/s)', self.k2_fit_var.get(), '', '', '', '', '', '', '', '', '', '', ''])
            data.append(['理论值K2(m/s)', self.k2_theory_var.get(), '', '', '', '', '', '', '', '', '', '', ''])
            
            # 创建DataFrame并保存
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, header=False)
            
            tk.messagebox.showinfo("成功", f"数据已导出到: {file_path}")
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas和openpyxl库: pip install pandas openpyxl")
        except Exception as e:
            tk.messagebox.showerror("错误", f"导出失败: {str(e)}")

    def update_invL2_data(self):
        """更新所有1/L数据"""
        for i in range(10):
            self.update_single_invL2_data(i)

    def update_T2_N(self, *args):
        """更新关系2的张力N值"""
        try:
            T_kgf = float(self.T2_kgf_var.get())
            self.T2_N_var.set(f"{self.kgf_to_newton(T_kgf):.1f}")
        except:
            self.T2_N_var.set("")

    def create_relation3_content(self):
        """创建关系3的内容"""
        # 实验条件框架
        condition_frame = ttk.Frame(self.content_frame)
        condition_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 实验条件输入
        ttk.Label(condition_frame, text="弦线线径d (mm):").grid(row=0, column=0, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.d3_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(condition_frame, text="铁丝线密度μ (kg/m):").grid(row=0, column=2, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.mu3_var, width=10, state='readonly').grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(condition_frame, text="波腹数n:").grid(row=0, column=4, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.n3_var, width=10).grid(row=0, column=5, padx=5, pady=2)
        
        ttk.Label(condition_frame, text="弦长L (cm):").grid(row=0, column=6, padx=5, pady=2)
        ttk.Entry(condition_frame, textvariable=self.L3_var, width=10).grid(row=0, column=7, padx=5, pady=2)
        
        # 表格框架
        table_frame = ttk.Frame(self.content_frame)
        table_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建表格
        self.create_relation3_table(table_frame)
        
        # 图表框架
        chart_frame = ttk.Frame(self.content_frame)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建图表
        self.create_relation3_chart(chart_frame)
        
        # 计算结果框架
        result_frame = ttk.Frame(self.content_frame)
        result_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(result_frame, text="拟合斜率k3(1/(m*kg)):").grid(row=0, column=0, padx=5)
        ttk.Entry(result_frame, textvariable=self.k3_fit_var, width=15, state='readonly').grid(row=0, column=1, padx=5)
        
        ttk.Label(result_frame, text="理论值K3(1/(m*kg)):").grid(row=0, column=2, padx=5)
        ttk.Entry(result_frame, textvariable=self.k3_theory_var, width=15, state='readonly').grid(row=0, column=3, padx=5)
        
        ttk.Button(result_frame, text="计算", command=self.calculate_relation3).grid(row=0, column=4, padx=5)
        ttk.Button(result_frame, text="清空数据", command=self.clear_relation3_data).grid(row=0, column=5, padx=5)
        
        # 导入导出按钮
        io_frame = ttk.Frame(self.content_frame)
        io_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(io_frame, text="导入数据", command=self.import_relation3_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="导出数据", command=self.export_relation3_data).pack(side=tk.LEFT, padx=5)
        
        # 创建完成后立即重绘（如果有数据）
        self.root.after(100, self.redraw_relation3_chart)

    def create_relation3_table(self, parent):
        """创建关系3的表格"""
        # 表头
        headers = ["项目"] + [str(i+1) for i in range(8)]
        for i, header in enumerate(headers):
            if i == 0:
                ttk.Label(parent, text=header, borderwidth=1, relief="solid", width=14).grid(row=0, column=i, padx=1, pady=1)
            else:
                ttk.Label(parent, text=header, borderwidth=1, relief="solid", width=10).grid(row=0, column=i, padx=1, pady=1)
        
        # 张力T (kgf)行
        ttk.Label(parent, text="张力T (kgf)", borderwidth=1, relief="solid", width=14).grid(row=1, column=0, padx=1, pady=1)
        for i in range(8):
            ttk.Entry(parent, textvariable=self.T3_kgf_vars[i], width=10).grid(row=1, column=i+1, padx=1, pady=1)
        
        # 张力T (N)行
        ttk.Label(parent, text="张力T (N)", borderwidth=1, relief="solid", width=14).grid(row=2, column=0, padx=1, pady=1)
        for i in range(8):
            ttk.Entry(parent, textvariable=self.T3_N_vars[i], width=10, state='readonly').grid(row=2, column=i+1, padx=1, pady=1)
        
        # 共振频率f行
        ttk.Label(parent, text="共振频率f (Hz)", borderwidth=1, relief="solid", width=14).grid(row=3, column=0, padx=1, pady=1)
        for i in range(8):
            ttk.Entry(parent, textvariable=self.f3_vars[i], width=10).grid(row=3, column=i+1, padx=1, pady=1)
        
        # f^2行
        ttk.Label(parent, text="f^2 (Hz^2)", borderwidth=1, relief="solid", width=14).grid(row=4, column=0, padx=1, pady=1)
        for i in range(8):
            ttk.Entry(parent, textvariable=self.f3_sq_vars[i], width=10, state='readonly').grid(row=4, column=i+1, padx=1, pady=1)
        
        # 波速计算值V行
        ttk.Label(parent, text="波速V (m/s)", borderwidth=1, relief="solid", width=14).grid(row=5, column=0, padx=1, pady=1)
        for i in range(8):
            ttk.Entry(parent, textvariable=self.V3_calc_vars[i], width=10, state='readonly').grid(row=5, column=i+1, padx=1, pady=1)
        
        # 波速理论值V0行
        ttk.Label(parent, text="波速V0 (m/s)", borderwidth=1, relief="solid", width=14).grid(row=6, column=0, padx=1, pady=1)
        for i in range(8):
            ttk.Entry(parent, textvariable=self.V3_theory_vars[i], width=10, state='readonly').grid(row=6, column=i+1, padx=1, pady=1)

    def create_relation3_chart(self, parent):
        """创建关系3的图表"""
        fig, ax = plt.subplots(figsize=(6, 1.83))
        self.relation3_fig = fig
        self.relation3_ax = ax
        self.relation3_ax.set_xlabel('张力 T (N)')
        self.relation3_ax.set_ylabel('f^2 (Hz^2)')
        self.relation3_ax.grid(True)
        
        # 调整边距
        fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def calculate_relation3(self):
        """计算关系3"""
        try:
            # 获取实验数据
            T_N_values = []
            f_sq_values = []
            
            for i in range(8):
                T_kgf_val = self.T3_kgf_vars[i].get()
                f_val = self.f3_vars[i].get()
                if T_kgf_val and f_val:
                    T_N = float(T_kgf_val) * 9.8
                    f_sq = float(f_val) ** 2
                    T_N_values.append(T_N)
                    f_sq_values.append(f_sq)
            
            if len(T_N_values) < 2:
                tk.messagebox.showwarning("警告", "请至少输入2组有效数据")
                return
            
            # 线性拟合
            T_N_array = np.array(T_N_values)
            f_sq_array = np.array(f_sq_values)
            
            slope, intercept = np.polyfit(T_N_array, f_sq_array, 1)
            
            # 计算理论值
            d_mm = float(self.d3_var.get()) if self.d3_var.get() else 0.7
            n = float(self.n3_var.get()) if self.n3_var.get() else 1
            L_cm = float(self.L3_var.get()) if self.L3_var.get() else 50.0
            
            # 计算线密度
            mu = self.calculate_linear_density(d_mm)  # kg/m
            L_m = L_cm / 100  # 转换为米
            
            # 理论斜率 K3 = 1/(4 * L² * μ)
            K3_theory = 1 / (4 * L_m**2 * mu) *n*n
            
            # 更新显示 - 保留一位小数
            self.k3_fit_var.set(f"{slope:.1f}")
            self.k3_theory_var.set(f"{K3_theory:.1f}")
            
            # 更新图表
            self.relation3_ax.clear()
            self.relation3_ax.scatter(T_N_values, f_sq_values, color='blue', label='实验数据')
            
            # 绘制拟合直线
            T_fit = np.linspace(min(T_N_values), max(T_N_values), 100)
            f_sq_fit = slope * T_fit + intercept
            
            # 显示拟合直线公式 - 使用一位小数
            if intercept >= 0:
                equation = f'f^2 = {slope:.1f}T + {intercept:.1f}'
            else:
                equation = f'f^2 = {slope:.1f}T - {abs(intercept):.1f}'
            
            self.relation3_ax.plot(T_fit, f_sq_fit, 'r-', label=equation)
            
            self.relation3_ax.set_xlabel('张力 T (N)')
            self.relation3_ax.set_ylabel('f^2 (Hz^2)')
            self.relation3_ax.grid(True)
            self.relation3_ax.legend()
            
            # 调整边距
            self.relation3_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            
            # 刷新图表
            self.relation3_fig.canvas.draw()
            
        except ValueError as e:
            tk.messagebox.showerror("错误", f"数据格式错误: {str(e)}")
        except Exception as e:
            tk.messagebox.showerror("错误", f"计算失败: {str(e)}")

    def update_mu3_data(self):
        """更新线密度数据"""
        try:
            d_val = self.d3_var.get()
            if d_val:
                mu = self.calculate_linear_density(float(d_val))
                self.mu3_var.set(f"{mu:.3e}")
            else:
                self.mu3_var.set("")
        except:
            self.mu3_var.set("")

    def redraw_relation3_chart(self):
        """重绘关系3的图表"""
        try:
            # 获取有效数据
            T_N_values = []
            f_sq_values = []
            
            for i in range(8):
                T_kgf_val = self.T3_kgf_vars[i].get()
                f_val = self.f3_vars[i].get()
                if T_kgf_val and f_val:
                    T_N = float(T_kgf_val) * 9.8
                    f_sq = float(f_val) ** 2
                    T_N_values.append(T_N)
                    f_sq_values.append(f_sq)
            
            # 如果有数据且已经计算过拟合结果，重新绘制拟合直线
            if len(T_N_values) >= 2 and self.k3_fit_var.get():
                # 线性拟合
                T_N_array = np.array(T_N_values)
                f_sq_array = np.array(f_sq_values)
                slope, intercept = np.polyfit(T_N_array, f_sq_array, 1)
                
                # 清空并重绘图表
                self.relation3_ax.clear()
                self.relation3_ax.scatter(T_N_values, f_sq_values, color='blue', label='实验数据')
                
                # 绘制拟合直线
                T_fit = np.linspace(min(T_N_values), max(T_N_values), 100)
                f_sq_fit = slope * T_fit + intercept
                
                # 显示拟合直线公式 - 使用一位小数
                if intercept >= 0:
                    equation = f'f^2 = {slope:.1f}T + {intercept:.1f}'
                else:
                    equation = f'f^2 = {slope:.1f}T - {abs(intercept):.1f}'
                
                self.relation3_ax.plot(T_fit, f_sq_fit, 'r-', label=equation)
                
            elif len(T_N_values) > 0:
                # 只有数据点，没有拟合结果
                self.relation3_ax.clear()
                self.relation3_ax.scatter(T_N_values, f_sq_values, color='blue', label='实验数据')
            
            else:
                # 没有数据，清空图表
                self.relation3_ax.clear()
            
            # 设置图表属性
            self.relation3_ax.set_xlabel('张力 T (N)')
            self.relation3_ax.set_ylabel('f^2 (Hz^2)')
            self.relation3_ax.grid(True)
            if len(T_N_values) > 0:
                self.relation3_ax.legend()
            
            # 调整边距
            self.relation3_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            
            # 刷新图表
            self.relation3_fig.canvas.draw()
            
        except Exception as e:
            # 如果重绘失败，初始化一个空图表
            self.relation3_ax.clear()
            self.relation3_ax.set_xlabel('张力 T (N)')
            self.relation3_ax.set_ylabel('f^2 (Hz^2)')
            self.relation3_ax.grid(True)
            self.relation3_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            self.relation3_fig.canvas.draw()

    def clear_relation3_data(self):
        """清空关系3的数据"""
        result = tk.messagebox.askyesno("确认清空", "确定要清空所有数据吗？此操作不可撤销！")
        if not result:
            return
        
        try:
            # 清空实验条件
            self.d3_var.set("")
            self.mu3_var.set("")
            self.n3_var.set("")
            self.L3_var.set("")
            
            # 清空表格数据
            for var in self.T3_kgf_vars:
                var.set("")
            for var in self.T3_N_vars:
                var.set("")
            for var in self.f3_vars:
                var.set("")
            for var in self.f3_sq_vars:
                var.set("")
            for var in self.V3_calc_vars:
                var.set("")
            for var in self.V3_theory_vars:
                var.set("")
            
            # 清空计算结果
            self.k3_fit_var.set("")
            self.k3_theory_var.set("")
            
            # 清空图表
            self.relation3_ax.clear()
            self.relation3_ax.set_xlabel('张力 T (N)')
            self.relation3_ax.set_ylabel('f^2 (Hz^2)')
            self.relation3_ax.grid(True)
            self.relation3_fig.subplots_adjust(bottom=0.25, left=0.15, right=0.95, top=0.9)
            self.relation3_fig.canvas.draw()
            
            tk.messagebox.showinfo("成功", "数据已清空")
            
        except Exception as e:
            tk.messagebox.showerror("错误", f"清空数据时发生错误: {str(e)}")

    def import_relation3_data(self):
        """导入关系3数据"""
        try:
            file_path = tk.filedialog.askopenfilename(
                title="选择Excel文件",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if not file_path:
                return
            
            import pandas as pd
            df = pd.read_excel(file_path, header=None)
            
            data_dict = {}
            current_section = None
            
            for index, row in df.iterrows():
                if pd.notna(row[0]):
                    key = str(row[0]).strip()
                    if key == '实验条件':
                        current_section = 'conditions'
                        continue
                    elif key == '项目':
                        current_section = 'table_header'
                        continue
                    elif key == '拟合斜率k3(1/(m*kg))':
                        current_section = 'results'
                        data_dict['k3_fit'] = str(row[1]) if pd.notna(row[1]) else ""
                        continue
                    elif key == '理论值K3(1/(m*kg))':
                        data_dict['k3_theory'] = str(row[1]) if pd.notna(row[1]) else ""
                        continue
                    elif key == '':
                        continue
                    
                    if current_section == 'conditions':
                        if key == '弦线线径d (mm)':
                            data_dict['d3'] = str(row[1]) if pd.notna(row[1]) else ""
                        elif key == '波腹数n':
                            data_dict['n3'] = str(row[1]) if pd.notna(row[1]) else ""
                        elif key == '弦长L (cm)':
                            data_dict['L3'] = str(row[1]) if pd.notna(row[1]) else ""
                    
                    elif current_section == 'table_header':
                        if key == '张力T (kgf)':
                            T_data = []
                            for i in range(1, 8):
                                if i < len(row) and pd.notna(row[i]):
                                    T_data.append(str(row[i]))
                                else:
                                    T_data.append("")
                            data_dict['T_data'] = T_data
                        
                        elif key == '共振频率f (Hz)':
                            f_data = []
                            for i in range(1, 8):
                                if i < len(row) and pd.notna(row[i]):
                                    f_data.append(str(row[i]))
                                else:
                                    f_data.append("")
                            data_dict['f_data'] = f_data
            
            # 更新UI
            if 'd3' in data_dict:
                self.d3_var.set(data_dict['d3'])
            if 'n3' in data_dict:
                self.n3_var.set(data_dict['n3'])
            if 'L3' in data_dict:
                self.L3_var.set(data_dict['L3'])
            
            if 'T_data' in data_dict:
                for i, value in enumerate(data_dict['T_data']):
                    if i < len(self.T3_kgf_vars):
                        self.T3_kgf_vars[i].set(value)
            
            if 'f_data' in data_dict:
                for i, value in enumerate(data_dict['f_data']):
                    if i < len(self.f3_vars):
                        self.f3_vars[i].set(value)
            
            if 'k3_fit' in data_dict:
                self.k3_fit_var.set(data_dict['k3_fit'])
            if 'k3_theory' in data_dict:
                self.k3_theory_var.set(data_dict['k3_theory'])
                
            # 更新自动计算的数据
            self.update_relation3_calculations()
            self.redraw_relation3_chart()
            tk.messagebox.showinfo("成功", "数据导入成功")
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas和openpyxl库: pip install pandas openpyxl")
        except Exception as e:
            tk.messagebox.showerror("错误", f"导入失败: {str(e)}")

    def export_relation3_data(self):
        """导出关系3数据"""
        try:
            file_path = tk.filedialog.asksaveasfilename(
                title="保存Excel文件",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if not file_path:
                return
            
            import pandas as pd
            
            # 创建数据框
            data = []
            
            # 实验条件部分
            data.append(['实验条件', '', '', '', '', '', '', ''])
            data.append(['弦线线径d (mm)', self.d3_var.get(), '', '', '', '', '', ''])
            data.append(['铁丝线密度μ (kg/m)', self.mu3_var.get(), '', '', '', '', '', ''])
            data.append(['波腹数n', self.n3_var.get(), '', '', '', '', '', ''])
            data.append(['弦长L (cm)', self.L3_var.get(), '', '', '', '', '', ''])
            data.append(['', '', '', '', '', '', '', ''])
            
            # 表格数据部分
            headers = ['项目', '1', '2', '3', '4', '5', '6', '7','8']
            data.append(headers)
            
            # 张力T (kgf)数据
            T_kgf_row = ['张力T (kgf)']
            for var in self.T3_kgf_vars:
                T_kgf_row.append(var.get() if var.get() else '')
            data.append(T_kgf_row)
            
            # 张力T (N)数据
            T_N_row = ['张力T (N)']
            for var in self.T3_N_vars:
                T_N_row.append(var.get() if var.get() else '')
            data.append(T_N_row)
            
            # 共振频率数据
            f_row = ['共振频率f (Hz)']
            for var in self.f3_vars:
                f_row.append(var.get() if var.get() else '')
            data.append(f_row)
            
            # f^2数据
            f_sq_row = ['f^2 (Hz^2)']
            for var in self.f3_sq_vars:
                f_sq_row.append(var.get() if var.get() else '')
            data.append(f_sq_row)
            
            # 波速计算值数据
            V_calc_row = ['波速V (m/s)']
            for var in self.V3_calc_vars:
                V_calc_row.append(var.get() if var.get() else '')
            data.append(V_calc_row)
            
            # 波速理论值数据
            V_theory_row = ['波速V0 (m/s)']
            for var in self.V3_theory_vars:
                V_theory_row.append(var.get() if var.get() else '')
            data.append(V_theory_row)
            
            data.append(['', '', '', '', '', '', '', ''])
            
            # 计算结果部分
            data.append(['拟合斜率k3(1/(m*kg))', self.k3_fit_var.get(), '', '', '', '', '', ''])
            data.append(['理论值K3(1/(m*kg))', self.k3_theory_var.get(), '', '', '', '', '', ''])
            
            # 创建DataFrame并保存
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, header=False)
            
            tk.messagebox.showinfo("成功", f"数据已导出到: {file_path}")
            
        except ImportError:
            tk.messagebox.showerror("错误", "请安装pandas和openpyxl库: pip install pandas openpyxl")
        except Exception as e:
            tk.messagebox.showerror("错误", f"导出失败: {str(e)}")

    def update_relation3_calculations(self):
        """更新关系3的所有自动计算数据"""
        # 更新线密度
        self.update_mu3_data()
        
        # 更新其他计算数据
        for i in range(8):
            self.update_single_relation3_data(i)

    def update_single_relation3_data(self, index):
        """更新单个关系3的计算数据"""
        try:
            T_kgf_val = self.T3_kgf_vars[index].get()
            f_val = self.f3_vars[index].get()
            L_val = self.L3_var.get()
            d_val = self.d3_var.get()
            n_val = self.n3_var.get()  # 从n3_var获取波腹数
            
            # 更新张力T (N) - 保留一位小数
            if T_kgf_val:
                T_N = float(T_kgf_val) * 9.8
                self.T3_N_vars[index].set(f"{T_N:.1f}")  # 保留一位小数
            else:
                self.T3_N_vars[index].set("")
            
            # 更新f^2 - 保留到整数
            if f_val:
                f_sq = float(f_val) ** 2
                self.f3_sq_vars[index].set(f"{f_sq:.0f}")  # 保留到整数
            else:
                self.f3_sq_vars[index].set("")
            
            # 更新波速计算值V - 修正：除以波腹数
            if f_val and L_val:
                L_m = float(L_val) / 100
                # 获取波腹数，如果没有输入则默认为1
                n = float(n_val) if n_val and n_val.strip() else 1.0
                V_calc = (2 * L_m * float(f_val)) / n  # 修正：除以波腹数n
                self.V3_calc_vars[index].set(f"{V_calc:.1f}")
            else:
                self.V3_calc_vars[index].set("")
            
            # 更新波速理论值V0 
            if T_kgf_val and d_val:
                T_N = float(T_kgf_val) * 9.8
                mu = self.calculate_linear_density(float(d_val))
                # 获取波腹数，如果没有输入则默认为1
                n = float(n_val) if n_val and n_val.strip() else 1.0
                V_theory = np.sqrt(T_N / mu) 
                self.V3_theory_vars[index].set(f"{V_theory:.1f}")
            else:
                self.V3_theory_vars[index].set("")
                
        except:
            self.T3_N_vars[index].set("")
            self.f3_sq_vars[index].set("")
            self.V3_calc_vars[index].set("")
            self.V3_theory_vars[index].set("")

    # 还需要添加其他辅助方法：
    def calculate_linear_density(self, diameter_mm):
        """计算线密度"""
        print(f"计算线密度，直径: {diameter_mm}mm")  # 调试信息
        diameter_m = float(diameter_mm) / 1000  # mm转m
        cross_area = np.pi * (diameter_m / 2) ** 2
        density = self.density_iron * 1000 * cross_area  # kg/m
        print(f"线密度结果: {density} kg/m")  # 调试信息
        return density

    def kgf_to_newton(self, kgf):
        """kgf转N"""
        return float(kgf) * 9.8

    def update_T1_N(self, *args):
        """更新关系1的张力N值"""
        try:
            T_kgf = float(self.T1_kgf_var.get())
            self.T1_N_var.set(f"{self.kgf_to_newton(T_kgf):.1f}")
        except:
            self.T1_N_var.set("")

    def create_instrument_controls(self):
        """在实验仪背景上创建控件"""
        canvas = self.instrument_canvas
        
        # 首先创建所有需要的 StringVar 变量
        if not hasattr(self, 'display_var'):
            self.display_var = tk.StringVar()
        self.display_var.set(f"拉力: {self.get_display_tension():.2f} kg")
        
        # 注意：这里移除了 zero_var 和 amplitude_var_instr 的创建
        # 因为它们现在由左侧控制面板管理
        
        # 显示框 - 显示拉力或振动信息
        self.display_label = tk.Label(canvas, textvariable=self.display_var, 
                                    font=('Arial', 12, 'bold'), bg='white', 
                                    width=15, height=2)
        canvas.create_window(140, 110, window=self.display_label)
        
        # 按钮区域
        button_y = 180
        button_spacing = 40
        
        # 增大按钮 - 使用 Frame 包装设置固定大小 60x30
        increase_frame = tk.Frame(canvas, width=22, height=22)
        increase_frame.pack_propagate(False)  # 防止 Frame 收缩
        self.increase_btn = tk.Button(increase_frame, text="", command=self.on_increase_click,bg='#545454',relief='flat')
        self.increase_btn.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.increase_btn.bind('<ButtonPress-1>', lambda e: self.on_increase_press())
        self.increase_btn.bind('<ButtonRelease-1>', lambda e: self.on_increase_release())
        
        canvas.create_window(80+240+2, button_y-50, window=increase_frame)

        # 减小按钮 - 使用 Frame 包装设置固定大小 60x30
        decrease_frame = tk.Frame(canvas, width=22, height=22)
        decrease_frame.pack_propagate(False)  # 防止 Frame 收缩
        self.decrease_btn = tk.Button(decrease_frame, text="", command=self.on_decrease_click,bg='#545454',relief='flat')
        self.decrease_btn.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.decrease_btn.bind('<ButtonPress-1>', lambda e: self.on_decrease_press())
        self.decrease_btn.bind('<ButtonRelease-1>', lambda e: self.on_decrease_release())
        
        canvas.create_window(320+2, button_y+25, window=decrease_frame)

        # 位数按钮 - 使用 Frame 包装设置固定大小 60x30
        digit_frame = tk.Frame(canvas, width=22, height=22)
        digit_frame.pack_propagate(False)  # 防止 Frame 收缩
        self.digit_btn = tk.Button(digit_frame, 
                                text="", 
                                command=self.change_digit,relief='flat',bg='#545454')
        self.digit_btn.pack(fill=tk.BOTH, expand=True)
        canvas.create_window(80+325, button_y + button_spacing-90, window=digit_frame)

        # 拉力/振动切换按钮 - 使用 Frame 包装设置固定大小 80x30
        mode_frame = tk.Frame(canvas, width=22, height=22)
        mode_frame.pack_propagate(False)  # 防止 Frame 收缩
        self.mode_btn = tk.Button(mode_frame, text="", command=self.toggle_display_mode,bg='#545454',relief='flat')
        self.mode_btn.pack(fill=tk.BOTH, expand=True)
        canvas.create_window(200+205, button_y + button_spacing-15, window=mode_frame)
        
        # 注意：这里移除了 zero_scale 和 amplitude_scale 的创建
        # 因为它们现在由左侧控制面板管理

    def on_increase_click(self):
        """增大按钮单击事件"""
        self.increase_value()

    def on_increase_press(self):
        """增大按钮按下事件"""
        self.increase_pressed = True
        
        # 设置长按定时器
        self.long_press_timer = self.root.after(self.long_press_delay, self.start_increase_repeat)

    def on_increase_release(self):
        """增大按钮释放事件"""
        self.increase_pressed = False
        
        # 取消定时器
        if self.long_press_timer:
            self.root.after_cancel(self.long_press_timer)
            self.long_press_timer = None
        
        if self.long_press_repeat_timer:
            self.root.after_cancel(self.long_press_repeat_timer)
            self.long_press_repeat_timer = None

    def start_increase_repeat(self):
        """开始增大按钮的长按重复"""
        if self.increase_pressed:
            self.increase_value()
            # 设置重复定时器
            self.long_press_repeat_timer = self.root.after(self.long_press_interval, self.start_increase_repeat)

    def on_decrease_click(self):
        """减小按钮单击事件"""
        self.decrease_value()

    def on_decrease_press(self):
        """减小按钮按下事件"""
        self.decrease_pressed = True
        
        # 设置长按定时器
        self.long_press_timer = self.root.after(self.long_press_delay, self.start_decrease_repeat)

    def on_decrease_release(self):
        """减小按钮释放事件"""
        self.decrease_pressed = False
        
        # 取消定时器
        if self.long_press_timer:
            self.root.after_cancel(self.long_press_timer)
            self.long_press_timer = None
        
        if self.long_press_repeat_timer:
            self.root.after_cancel(self.long_press_repeat_timer)
            self.long_press_repeat_timer = None

    def start_decrease_repeat(self):
        """开始减小按钮的长按重复"""
        if self.decrease_pressed:
            self.decrease_value()
            # 设置重复定时器
            self.long_press_repeat_timer = self.root.after(self.long_press_interval, self.start_decrease_repeat)

    def update_amplitude_from_left(self, val):
        """从左控制面板更新振幅"""
        self.amplitude_mv = float(val)
        
        # 不需要显示数值，所以移除相关代码

    def update_zero_offset(self, val):
        """更新拉力计调零偏移（现在此功能由左侧控制面板处理）"""
        # 这个方法现在应该被废弃或更新为同步左侧控制面板
        # 保留它用于向后兼容，但实际功能由左侧控制面板处理
        pass

    def reset_zero_offset(self):
        """重置拉力计调零偏移"""
        self.zero_offset = 0.0
        self.zero_scale_left.set(0.0)
        
        # 更新显示
        self.update_display()

    def create_amplitude_zero_controls(self, parent, row):
        """创建振幅和拉力计调零控制 - 不显示数值"""
        # 主框架
        main_frame = ttk.Frame(parent)
        main_frame.grid(row=row, column=0, columnspan=4, sticky="ew", pady=10)
        
        # 左侧框架 - 振幅控制
        amplitude_frame = ttk.LabelFrame(main_frame, text="起振幅度")
        amplitude_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 振幅控制滑块
        self.amplitude_scale_left = ttk.Scale(amplitude_frame, from_=0, to=200, 
                                            orient=tk.HORIZONTAL,
                                            command=self.update_amplitude_from_left)
        self.amplitude_scale_left.set(self.amplitude_mv)
        self.amplitude_scale_left.pack(fill=tk.X, expand=True, padx=10, pady=5)
        
        # 右侧框架 - 拉力计调零控制
        zero_frame = ttk.LabelFrame(main_frame, text="拉力计调零")
        zero_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 拉力计调零滑块
        self.zero_scale_left = ttk.Scale(zero_frame, from_=-1.0, to=1.0,
                                        orient=tk.HORIZONTAL,
                                        command=self.update_zero_offset_from_left)
        self.zero_scale_left.set(self.zero_offset)
        self.zero_scale_left.pack(fill=tk.X, expand=True, padx=10, pady=5)
        
        # # 重置按钮 - 放在滑块下方
        # reset_button = ttk.Button(zero_frame, text="重置", 
        #                         command=self.reset_zero_offset, width=6)
        # reset_button.pack(side=tk.BOTTOM, pady=(0, 5))

    def create_default_instrument_panel(self, parent):
        """创建默认的实验仪面板（当背景图片不存在时）"""
        # 显示框
        display_frame = ttk.Frame(parent)
        display_frame.pack(pady=10)
        
        self.display_var = tk.StringVar()
        self.display_var.set(f"拉力: {self.get_display_tension():.2f} kg")
        self.display_label = ttk.Label(display_frame, textvariable=self.display_var, 
                                     font=('Arial', 14, 'bold'), 
                                     width=20, height=2, relief='sunken')
        self.display_label.pack()
        
        # 按钮区域
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="增大", command=self.increase_value).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="减小", command=self.decrease_value).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(button_frame, text="位数", command=self.change_digit).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="", command=self.toggle_display_mode).grid(row=1, column=1, padx=5, pady=5)
        
        # 旋钮区域
        scale_frame = ttk.Frame(parent)
        scale_frame.pack(pady=10)
        
        # 拉力计调零旋钮
        ttk.Label(scale_frame, text="拉力计调零").grid(row=0, column=0, padx=10)
        self.zero_scale = ttk.Scale(scale_frame, from_=-0.3, to=0.3, 
                                  orient=tk.VERTICAL, length=100,
                                  command=self.update_zero_offset)
        self.zero_scale.set(0.0)
        self.zero_scale.grid(row=1, column=0, padx=10)
        
        # 起振幅度旋钮
        ttk.Label(scale_frame, text="起振幅度").grid(row=0, column=1, padx=10)
        self.amplitude_scale = ttk.Scale(scale_frame, from_=0, to=200, 
                                       orient=tk.VERTICAL, length=100,
                                       command=self.update_amplitude_from_instrument)
        self.amplitude_scale.set(self.amplitude_mv)
        self.amplitude_scale.grid(row=1, column=1, padx=10)
        
        # 旋钮值显示
        value_frame = ttk.Frame(parent)
        value_frame.pack(pady=5)
        
        self.zero_var = tk.StringVar(value="0.00")
        ttk.Label(value_frame, textvariable=self.zero_var).grid(row=0, column=0, padx=20)
        
        self.amplitude_var_instr = tk.StringVar(value=f"{self.amplitude_mv:.0f}")
        ttk.Label(value_frame, textvariable=self.amplitude_var_instr).grid(row=0, column=1, padx=20)

    def get_display_tension(self):
        """获取显示的拉力值（包含随机偏移和调零偏移）"""
        return self.tension + self.random_offset + self.zero_offset

    def update_zero_offset(self, val):
        """更新拉力计调零偏移"""
        self.zero_offset = float(val)
        self.zero_var.set(f"{self.zero_offset:.2f}")
        self.update_display()

    def update_amplitude_from_instrument(self, val):
        """从实验仪更新振幅（现在此功能由左侧控制面板处理）"""
        # 这个方法现在应该被废弃或更新为同步左侧控制面板
        # 保留它用于向后兼容，但实际功能由左侧控制面板处理
        pass

    def toggle_display_mode(self):
        """切换显示模式"""
        if self.display_mode == "tension":
            self.display_mode = "vibration"
            print("切换到振动模式")
        else:
            self.display_mode = "tension"
            
            # 重置时间，确保从静止开始
            self.time = 0
            
            # 立即将弦设为全0
            self.y = np.zeros_like(self.x)
            self.line.set_data(self.x, self.y)
            
            # 探测振幅设为0
            self.probe_amplitude = 0.0
            
            print("切换到拉力模式")
        
        # 每次切换模式时，重置倍率为"无"状态
        self.instr_freq_multiplier_index = 6  # 指向"无"
        
        self.update_display()  # 更新显示
        # 强制立即重绘
        self.canvas.draw_idle()

    def update_display(self):
        """更新显示框内容"""
        if self.display_mode == "tension":
            display_text = f"拉力: {self.get_display_tension():.2f} kg"
        else:
            # 获取频率字符串
            freq_str, highlighted_freq = self.get_highlighted_frequency()
            
            # 如果存在高亮频率，使用高亮版本，否则使用普通版本
            display_freq = highlighted_freq if highlighted_freq else freq_str
            display_text = f"频率: {display_freq} Hz\n振幅: {self.probe_amplitude:.1f}mV"
        
        self.display_var.set(display_text)

    def get_formatted_frequency(self):
        """获取格式化后的频率字符串（XXXX.XX格式）"""
        if self.frequency < 0.01:
            self.frequency = 0.01
        
        freq_int = int(self.frequency)
        freq_decimal = int(round((self.frequency - freq_int) * 100))
        return f"{freq_int:04d}.{freq_decimal:02d}"

    def get_highlighted_frequency(self):
        """获取高亮显示的频率字符串"""
        # 确保频率最小值为0.01，最大值为1000.00
        if self.frequency < 0.01:
            self.frequency = 0.01
        elif self.frequency > 1000.00:
            self.frequency = 1000.00
        
        # 格式化为4位整数+2位小数：XXXX.XX
        # 对于最大1000Hz，需要支持4位整数
        freq_int = int(self.frequency)
        freq_decimal = int(round((self.frequency - freq_int) * 100))
        
        # 确保小数部分为2位，不足补0
        freq_str = f"{freq_int:04d}.{freq_decimal:02d}"
        
        # 如果不在振动模式或频率为0，不进行高亮
        if self.display_mode != "vibration" or self.frequency == 0:
            return freq_str, None
        
        # 获取当前倍率
        multiplier = self.instr_freq_multipliers[self.instr_freq_multiplier_index]
        
        # 如果当前倍率为None（不指向任何位），返回不高亮的频率
        if multiplier is None:
            return freq_str, None
        
        # 根据当前倍率确定高亮位置
        if multiplier == 1000:  # ×1000，调节千位
            highlighted_freq = f"[{freq_str[0]}]{freq_str[1:]}"
        elif multiplier == 100:  # ×100，调节百位
            highlighted_freq = f"{freq_str[0]}[{freq_str[1]}]{freq_str[2:]}"
        elif multiplier == 10:  # ×10，调节十位
            highlighted_freq = f"{freq_str[:2]}[{freq_str[2]}]{freq_str[3:]}"
        elif multiplier == 1:  # ×1，调节个位
            highlighted_freq = f"{freq_str[:3]}[{freq_str[3]}].{freq_str[5:]}"
        elif multiplier == 0.1:  # ×0.1，调节十分位
            highlighted_freq = f"{freq_str[:5]}[{freq_str[5]}]{freq_str[6]}"
        elif multiplier == 0.01:  # ×0.01，调节百分位
            highlighted_freq = f"{freq_str[:6]}[{freq_str[6]}]"
        else:
            # 其他情况不高亮
            highlighted_freq = None
        
        return freq_str, highlighted_freq

    def increase_value(self):
        """增大按钮功能 - 增加频率"""
        if self.display_mode != "vibration":
            return  # 只有在振动模式下才能调节频率
        
        # 检查当前是否指向某一位（不是"无"状态）
        multiplier = self.instr_freq_multipliers[self.instr_freq_multiplier_index]
        if multiplier is None:
            return  # 如果不指向任何位，不执行增减
        
        step = 1 * multiplier
        new_val = min(self.frequency + step, 1000.00)  # 最大1000.00Hz
        
        # 确保最小值为0.01
        if new_val < 0.01:
            new_val = 0.01
        
        self.frequency = new_val
        # 同步更新左侧控制面板
        if hasattr(self, 'freq_slider'):
            self.freq_slider.set(new_val)
        if hasattr(self, 'freq_var'):
            self.freq_var.set(f"{new_val:.2f}")
        
        self.update_resonance_info()
        self.update_display()  # 更新显示，会高亮相应位

    def decrease_value(self):
        """减小按钮功能 - 减少频率"""
        if self.display_mode != "vibration":
            return  # 只有在振动模式下才能调节频率
 
        
        # 检查当前是否指向某一位（不是"无"状态）
        multiplier = self.instr_freq_multipliers[self.instr_freq_multiplier_index]
        if multiplier is None:
            return  # 如果不指向任何位，不执行增减
        
        step = 1 * multiplier
        new_val = max(self.frequency - step, 0.01)  # 最小0.01Hz
        
        self.frequency = new_val
        # 同步更新左侧控制面板
        if hasattr(self, 'freq_slider'):
            self.freq_slider.set(new_val)
        if hasattr(self, 'freq_var'):
            self.freq_var.set(f"{new_val:.2f}")
        
        self.update_resonance_info()
        self.update_display()  # 更新显示，会高亮相应位

    # 修改 change_digit 方法
    def change_digit(self):
        """位数按钮功能 - 切换频率调节倍率"""
        if self.display_mode != "vibration":
            return  # 只有在振动模式下才能调节频率
        
        # 循环切换倍率
        self.instr_freq_multiplier_index = (self.instr_freq_multiplier_index + 1) % len(self.instr_freq_multipliers)
        
        # 按钮保持为空，不需要更新文本
        # 更新显示框，高亮相应位
        self.update_display()
        
        current_label = self.instr_freq_multiplier_labels[self.instr_freq_multiplier_index]
        print(f"频率调节倍率切换为: {current_label}")

    def load_background_images(self):
        """加载背景图片"""
        # 初始化图片属性为None
        self.pulley_img = None
        self.probe_img = None
        
        try:
            # 实验装置图片 - 覆盖整个x轴
            setup_path = get_resource_path(os.path.join('background', '实验装置.jpg'))
            if os.path.exists(setup_path):
                setup_img = mpimg.imread(setup_path)
                self.ax.imshow(setup_img, extent=[0, 140, -2.5, 4], aspect='auto', alpha=1)
            else:
                print("警告: 实验装置.jpg 未找到")
            
            # 滑轮组图片 - 使用固定范围显示
            pulley_path = get_resource_path(os.path.join('background', '滑轮组.jpg'))
            if os.path.exists(pulley_path):
                self.pulley_img = mpimg.imread(pulley_path)
                # 使用固定大小显示，避免过度缩小
                
                pulley_extent = [self.length-3, self.length+3, -1.5, 1.5]  # 固定显示范围
                self.pulley_display = self.ax.imshow(self.pulley_img, extent=pulley_extent, aspect='auto', alpha=1)
            else:
                print("警告: 滑轮组.jpg 未找到")
                # 创建默认的滑轮组标记
                self.ax.plot(self.length, 0, 's', markersize=10, color='red', label='滑轮组')
            
            # 振幅探测图片 - 使用固定范围显示
            probe_path = get_resource_path(os.path.join('background', '振幅探测.jpg'))
            if os.path.exists(probe_path):
                self.probe_img = mpimg.imread(probe_path)
                # 使用固定大小显示
                offset=1.4
                probe_extent = [self.probe_position-3.2 + offset, self.probe_position+3.2 + offset, -1.5, 4 ]
                self.probe_display = self.ax.imshow(self.probe_img, extent=probe_extent, aspect='auto', alpha=1)
            else:
                print("警告: 振幅探测.jpg 未找到")
                # 创建默认的探测标记
                self.probe_point, = self.ax.plot(self.probe_position, 0, '^', markersize=8, color='blue', label='探测点')
                
        except Exception as e:
            print(f"加载图片失败: {e}")
            # 创建默认标记
            self.ax.plot(self.length, 0, 's', markersize=10, color='red', label='滑轮组')
            self.probe_point, = self.ax.plot(self.probe_position, 0, '^', markersize=8, color='blue', label='探测点')

    def create_control_panel(self, parent):
        # 创建主控制框架
        control_frame = ttk.Frame(parent)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # 第一行：拉紧/松开弦线按钮
        tighten_frame = ttk.Frame(control_frame)
        tighten_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 10))
        
        self.tighten_button = ttk.Button(
            tighten_frame, 
            text="拉紧弦线",  # 初始状态为松开
            command=self.toggle_string_tension,
            width=15
        )
        self.tighten_button.pack()
        
        # 第二行：弦线直径选择（从原来的第5行移上来）
        self.diameter_frame = ttk.Frame(control_frame)
        self.diameter_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
        
        ttk.Label(self.diameter_frame, text="弦线直径 (mm):").pack(side=tk.LEFT)
        
        self.diameter_var = tk.StringVar(value=str(self.diameter))
        diameters = ["0.6", "0.7", "0.8", "0.9"]
        for diameter in diameters:
            ttk.Radiobutton(self.diameter_frame, text=diameter, variable=self.diameter_var, 
                        value=diameter, command=self.update_diameter_from_radio).pack(side=tk.LEFT, padx=5)
        
        # 第三行：拉力控制 - 基础步长改为1
        self.create_parameter_control(control_frame, "张力 (kgf)", 0, 12, self.tension, 1, 
                                    self.update_tension, 2)
        
        # 第四行：长度控制 - 基础步长改为1
        self.create_parameter_control(control_frame, "弦长 (cm)", 17, 103, self.length, 1, 
                                    self.update_length, 3)
        
        # 第五行：振幅探测位置控制
        self.create_probe_control(control_frame, 4)
        
        # 第六行：在探测位置下方添加振幅和拉力计调零控制
        self.create_amplitude_zero_controls(control_frame, 5)  # 修改为第5行
        
        # 第七行：谐振频率提示开关 - 在振幅和拉力计调零下方添加
        resonance_toggle_frame = ttk.Frame(control_frame)
        resonance_toggle_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=2)
        
        # 添加一个布尔变量来控制是否显示谐波信息
        self.show_resonance_info = tk.BooleanVar(value=False)  # 默认开启
        
        # 创建复选框
        self.resonance_toggle = ttk.Checkbutton(
            resonance_toggle_frame, 
            text="谐振频率提示", 
            variable=self.show_resonance_info,
            command=self.toggle_resonance_info
        )
        self.resonance_toggle.pack(side=tk.LEFT)

    def create_probe_control(self, parent, row):
        """创建振幅探测位置控制"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, columnspan=4, sticky="ew", pady=2)
        self.probe_control_frame = frame  # 存储框架引用
        
        # 标签和数值显示在同一行，标签在左，数值在右
        label_frame = ttk.Frame(frame)
        label_frame.pack(side=tk.LEFT)
        
        # 标签
        ttk.Label(label_frame, text="探测位置 (cm)", width=12).pack(side=tk.LEFT)
        
        # 数值显示 - 放在标签右侧
        self.probe_var = tk.StringVar(value=f"{self.probe_position:.1f}")
        value_label = ttk.Label(label_frame, textvariable=self.probe_var, width=8)
        value_label.pack(side=tk.LEFT, padx=5)
        self.probe_value_label = value_label  # 存储引用
        
        # - 按钮
        btn_minus = ttk.Button(frame, text="-", width=3)
        btn_minus.pack(side=tk.LEFT, padx=(5, 5))

        # 绑定鼠标事件
        btn_minus.bind('<ButtonPress-1>', lambda e: self.on_probe_decrease_press())
        btn_minus.bind('<ButtonRelease-1>', lambda e: self.on_probe_decrease_release())

        self.probe_minus_btn = btn_minus  # 存储引用
        
        # 滑块框架
        slider_frame = ttk.Frame(frame)
        slider_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 创建滑块
        self.probe_slider = ttk.Scale(slider_frame, from_=15, to=90, value=self.probe_position,
                                    orient=tk.HORIZONTAL, length=200, command=self.update_probe_position)
        self.probe_slider.pack(side=tk.TOP, fill=tk.X, expand=True)
        
        # + 按钮
        btn_plus = ttk.Button(frame, text="+", width=3)
        btn_plus.pack(side=tk.LEFT, padx=(5, 5))

        # 绑定鼠标事件
        btn_plus.bind('<ButtonPress-1>', lambda e: self.on_probe_increase_press())
        btn_plus.bind('<ButtonRelease-1>', lambda e: self.on_probe_increase_release())
        self.probe_plus_btn = btn_plus  # 存储引用
        
        # 调节步长说明和切换按钮
        multiplier_frame = ttk.Frame(frame)
        multiplier_frame.pack(side=tk.LEFT, padx=(0, 5))
        
        # 添加"调节步长："说明
        ttk.Label(multiplier_frame, text="调节步长：").pack(side=tk.LEFT)
        
        # 倍率切换按钮
        self.probe_multipliers = [100, 10, 1, 0.1]
        self.probe_multiplier_labels = ["×100", "×10", "×1", "×0.1"]
        self.probe_multiplier_index = 2  # 默认×1
        
        self.probe_multiplier_btn = ttk.Button(multiplier_frame, 
                                            text=self.probe_multiplier_labels[self.probe_multiplier_index], 
                                            width=5, 
                                            command=self.toggle_probe_multiplier)
        self.probe_multiplier_btn.pack(side=tk.LEFT)
    # 张力增加按钮长按控制
    def on_tension_increase_press(self):
        """张力增加按钮按下事件"""
        self.tension_increase_pressed = True
        self.increment_parameter("张力 (kgf)", 1, self.update_tension)
        
        # 设置长按定时器
        self.tension_long_press_timer = self.root.after(self.long_press_delay, self.start_tension_increase_repeat)

    def on_tension_increase_release(self):
        """张力增加按钮释放事件"""
        self.tension_increase_pressed = False
        
        # 取消定时器
        if self.tension_long_press_timer:
            self.root.after_cancel(self.tension_long_press_timer)
            self.tension_long_press_timer = None
        
        if self.tension_long_press_repeat_timer:
            self.root.after_cancel(self.tension_long_press_repeat_timer)
            self.tension_long_press_repeat_timer = None

    def start_tension_increase_repeat(self):
        """开始张力增加按钮的长按重复"""
        if self.tension_increase_pressed:
            self.increment_parameter("张力 (kgf)", 1, self.update_tension)
            # 设置重复定时器
            self.tension_long_press_repeat_timer = self.root.after(self.long_press_interval, self.start_tension_increase_repeat)

    # 张力减少按钮长按控制
    def on_tension_decrease_press(self):
        """张力减少按钮按下事件"""
        self.tension_decrease_pressed = True
        self.decrement_parameter("张力 (kgf)", 1, self.update_tension)
        
        # 设置长按定时器
        self.tension_long_press_timer = self.root.after(self.long_press_delay, self.start_tension_decrease_repeat)

    def on_tension_decrease_release(self):
        """张力减少按钮释放事件"""
        self.tension_decrease_pressed = False
        
        # 取消定时器
        if self.tension_long_press_timer:
            self.root.after_cancel(self.tension_long_press_timer)
            self.tension_long_press_timer = None
        
        if self.tension_long_press_repeat_timer:
            self.root.after_cancel(self.tension_long_press_repeat_timer)
            self.tension_long_press_repeat_timer = None

    def start_tension_decrease_repeat(self):
        """开始张力减少按钮的长按重复"""
        if self.tension_decrease_pressed:
            self.decrement_parameter("张力 (kgf)", 1, self.update_tension)
            # 设置重复定时器
            self.tension_long_press_repeat_timer = self.root.after(self.long_press_interval, self.start_tension_decrease_repeat)

    # 弦长增加按钮长按控制
    def on_length_increase_press(self):
        """弦长增加按钮按下事件"""
        self.length_increase_pressed = True
        self.increment_parameter("弦长 (cm)", 1, self.update_length)
        
        # 设置长按定时器
        self.length_long_press_timer = self.root.after(self.long_press_delay, self.start_length_increase_repeat)

    def on_length_increase_release(self):
        """弦长增加按钮释放事件"""
        self.length_increase_pressed = False
        
        # 取消定时器
        if self.length_long_press_timer:
            self.root.after_cancel(self.length_long_press_timer)
            self.length_long_press_timer = None
        
        if self.length_long_press_repeat_timer:
            self.root.after_cancel(self.length_long_press_repeat_timer)
            self.length_long_press_repeat_timer = None

    def start_length_increase_repeat(self):
        """开始弦长增加按钮的长按重复"""
        if self.length_increase_pressed:
            self.increment_parameter("弦长 (cm)", 1, self.update_length)
            # 设置重复定时器
            self.length_long_press_repeat_timer = self.root.after(self.long_press_interval, self.start_length_increase_repeat)

    # 弦长减少按钮长按控制（类似增加按钮）
    def on_length_decrease_press(self):
        """弦长减少按钮按下事件"""
        self.length_decrease_pressed = True
        self.decrement_parameter("弦长 (cm)", 1, self.update_length)
        
        # 设置长按定时器
        self.length_long_press_timer = self.root.after(self.long_press_delay, self.start_length_decrease_repeat)

    def on_length_decrease_release(self):
        """弦长减少按钮释放事件"""
        self.length_decrease_pressed = False
        
        # 取消定时器
        if self.length_long_press_timer:
            self.root.after_cancel(self.length_long_press_timer)
            self.length_long_press_timer = None
        
        if self.length_long_press_repeat_timer:
            self.root.after_cancel(self.length_long_press_repeat_timer)
            self.length_long_press_repeat_timer = None

    def start_length_decrease_repeat(self):
        """开始弦长减少按钮的长按重复"""
        if self.length_decrease_pressed:
            self.decrement_parameter("弦长 (cm)", 1, self.update_length)
            # 设置重复定时器
            self.length_long_press_repeat_timer = self.root.after(self.long_press_interval, self.start_length_decrease_repeat)

    # 探测位置增加按钮长按控制
    def on_probe_increase_press(self):
        """探测位置增加按钮按下事件"""
        self.probe_increase_pressed = True
        self.increment_probe()
        
        # 设置长按定时器
        self.probe_long_press_timer = self.root.after(self.long_press_delay, self.start_probe_increase_repeat)

    def on_probe_increase_release(self):
        """探测位置增加按钮释放事件"""
        self.probe_increase_pressed = False
        
        # 取消定时器
        if self.probe_long_press_timer:
            self.root.after_cancel(self.probe_long_press_timer)
            self.probe_long_press_timer = None
        
        if self.probe_long_press_repeat_timer:
            self.root.after_cancel(self.probe_long_press_repeat_timer)
            self.probe_long_press_repeat_timer = None

    def start_probe_increase_repeat(self):
        """开始探测位置增加按钮的长按重复"""
        if self.probe_increase_pressed:
            self.increment_probe()
            # 设置重复定时器
            self.probe_long_press_repeat_timer = self.root.after(self.long_press_interval, self.start_probe_increase_repeat)

    # 探测位置减少按钮长按控制
    def on_probe_decrease_press(self):
        """探测位置减少按钮按下事件"""
        self.probe_decrease_pressed = True
        self.decrement_probe()
        
        # 设置长按定时器
        self.probe_long_press_timer = self.root.after(self.long_press_delay, self.start_probe_decrease_repeat)

    def on_probe_decrease_release(self):
        """探测位置减少按钮释放事件"""
        self.probe_decrease_pressed = False
        
        # 取消定时器
        if self.probe_long_press_timer:
            self.root.after_cancel(self.probe_long_press_timer)
            self.probe_long_press_timer = None
        
        if self.probe_long_press_repeat_timer:
            self.root.after_cancel(self.probe_long_press_repeat_timer)
            self.probe_long_press_repeat_timer = None

    def start_probe_decrease_repeat(self):
        """开始探测位置减少按钮的长按重复"""
        if self.probe_decrease_pressed:
            self.decrement_probe()
            # 设置重复定时器
            self.probe_long_press_repeat_timer = self.root.after(self.long_press_interval, self.start_probe_decrease_repeat)
            
    def toggle_string_tension(self):
        """切换弦线拉紧/松开状态"""
        self.string_tightened = not self.string_tightened
        
        if self.string_tightened:
            # 切换到拉紧状态
            self.tighten_button.config(text="松开弦线")
            self.tension = 0  # 恢复默认张力
            self.enable_controls()  # 启用所有控件
            # 更新张力进度条位置 - 这个最重要
            if hasattr(self, 'tension_slider'):
                self.tension_slider.set(self.tension)
           
            
           
        else:
            # 切换到松开状态
            self.tighten_button.config(text="拉紧弦线")
            self.tension = 0.0  # 张力设为0
            if hasattr(self, 'tension_slider'):
                self.tension_slider.set(self.tension)
            # 重置时间，确保从静止开始
            self.time = 0
            
            # 立即将弦设为全0
            self.y = np.zeros_like(self.x)
            self.line.set_data(self.x, self.y)
            
            # 探测振幅设为0
            self.probe_amplitude = 0.0
            
        
            # 每次切换模式时，重置倍率为"无"状态
            self.instr_freq_multiplier_index = 6  # 指向"无"
            
            self.update_display()  # 更新显示
            # 强制立即重绘
            self.canvas.draw_idle()
            self.disable_controls()  # 禁用相关控件
        
        # 更新显示
        self.update_display()
        self.update_resonance_info()
        
        # 如果处于拉力模式，立即更新弦线显示
        if self.display_mode == "tension":
            self.time = 0
            self.y = np.zeros_like(self.x)
            self.line.set_data(self.x, self.y)
            self.canvas.draw_idle()

    def enable_controls(self):
        """启用所有相关控件"""
        # 启用张力控制
        self.tension_slider.state(['!disabled'])
        self.tension_minus_btn.state(['!disabled'])
        self.tension_plus_btn.state(['!disabled'])
        self.tension_multiplier_btn.state(['!disabled'])
        
        # 启用长度控制
        self.length_slider.state(['!disabled'])
        self.length_minus_btn.state(['!disabled'])
        self.length_plus_btn.state(['!disabled'])
        self.length_multiplier_btn.state(['!disabled'])
        
        # 启用探测位置控制
        self.probe_slider.state(['!disabled'])
        self.probe_minus_btn.state(['!disabled'])
        self.probe_plus_btn.state(['!disabled'])
        self.probe_multiplier_btn.state(['!disabled'])
        
        # 禁用直径选择
        for widget in self.diameter_frame.winfo_children():
            if isinstance(widget, ttk.Radiobutton):
                widget.state(['disabled'])
        
        # 启用振幅控制
        self.amplitude_scale_left.state(['!disabled'])
        
        # 禁用拉力计调零控制
        self.zero_scale_left.state(['disabled'])

    def disable_controls(self):
        """禁用所有相关控件"""
        # 禁用张力控制
        self.tension_slider.state(['disabled'])
        self.tension_minus_btn.state(['disabled'])
        self.tension_plus_btn.state(['disabled'])
        self.tension_multiplier_btn.state(['disabled'])
        
        # 禁用长度控制
        self.length_slider.state(['disabled'])
        self.length_minus_btn.state(['disabled'])
        self.length_plus_btn.state(['disabled'])
        self.length_multiplier_btn.state(['disabled'])
        
        # 禁用探测位置控制
        self.probe_slider.state(['disabled'])
        self.probe_minus_btn.state(['disabled'])
        self.probe_plus_btn.state(['disabled'])
        self.probe_multiplier_btn.state(['disabled'])
        
        # 启用直径选择
        for widget in self.diameter_frame.winfo_children():
            if isinstance(widget, ttk.Radiobutton):
                widget.state(['!disabled'])
        
        # 禁用振幅控制
        self.amplitude_scale_left.state(['disabled'])
        
        # 启用拉力计调零控制
        self.zero_scale_left.state(['!disabled'])


    def toggle_resonance_info(self):
        """切换谐振频率提示的显示状态"""
        if self.show_resonance_info.get():
            self.resonance_toggle.config(text="谐振频率提示")
            # 显示共振信息
            self.update_resonance_info()
        else:
            self.resonance_toggle.config(text="谐振频率提示")
            # 隐藏共振信息
            self.resonance_text.set_text('')
            self.canvas.draw_idle()

    def update_resonance_info(self):
        """更新共振频率信息"""
        # 检查是否开启了谐振频率提示
        if not self.show_resonance_info.get():
            self.resonance_text.set_text('')  # 清空文本
            self.canvas.draw_idle()
            return
        
        fundamental, harmonics = self.calculate_resonance_frequencies(5)  # 显示更多谐波
        
        # 检查当前频率是否接近任何共振频率
        resonance_detected = False
        resonance_harmonic = 0
        
        # 计算最接近的谐波
        if fundamental > 0:
            n_harmonic = max(1, round(self.frequency / fundamental))  # 确保至少为1
            expected_freq = n_harmonic * fundamental
            if abs(self.frequency - expected_freq) < 0.5:
                resonance_detected = True
                resonance_harmonic = n_harmonic
        
        # 更新文本
        # if resonance_detected:
        #     self.resonance_text.set_text(f'共振检测到! 第{resonance_harmonic}谐波\n基频: {fundamental:.2f} Hz')
        #     self.resonance_text.set_color('red')
        # else:
        # 显示更多谐波信息
        harmonic_text = ", ".join([f"{h:.1f}" for h in harmonics[:15]])  # 显示前15个谐波
        self.resonance_text.set_text(f'谐振频率: {harmonic_text} Hz...')
        self.resonance_text.set_color('black')
        
        self.canvas.draw_idle()

    def toggle_probe_multiplier(self):
        """切换探测位置的调节步长"""
        self.probe_multiplier_index = (self.probe_multiplier_index + 1) % len(self.probe_multipliers)
        self.probe_multiplier_btn.config(text=self.probe_multiplier_labels[self.probe_multiplier_index])

    def get_current_probe_multiplier(self):
        """获取探测位置的当前倍率"""
        return self.probe_multipliers[self.probe_multiplier_index]
    
    def create_parameter_control(self, parent, label, min_val, max_val, init_val, step, callback, row):
        """创建参数控制行"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, columnspan=4, sticky="ew", pady=2)
        
        # 存储框架引用，以便后续启用/禁用
        if label == "张力 (kgf)":
            self.tension_control_frame = frame
        elif label == "弦长 (cm)":
            self.length_control_frame = frame
        
        # 标签和数值显示在同一行，标签在左，数值在右
        label_frame = ttk.Frame(frame)
        label_frame.pack(side=tk.LEFT)
        
        # 标签
        ttk.Label(label_frame, text=label, width=12).pack(side=tk.LEFT)
        
        # 数值显示 - 放在标签右侧
        if label == "弦长 (cm)":
            value_var = tk.StringVar(value=f"{init_val:.1f}")
            value_label = ttk.Label(label_frame, textvariable=value_var, width=8)
            value_label.pack(side=tk.LEFT, padx=5)
            self.length_var = value_var
        # 注意：张力不需要在控制面板显示数值
        
        # - 按钮
        btn_minus = ttk.Button(frame, text="-", width=3)
        btn_minus.pack(side=tk.LEFT, padx=(5, 5))

        # 绑定鼠标事件
        if label == "张力 (kgf)":
            btn_minus.bind('<ButtonPress-1>', lambda e: self.on_tension_decrease_press())
            btn_minus.bind('<ButtonRelease-1>', lambda e: self.on_tension_decrease_release())
        elif label == "弦长 (cm)":
            btn_minus.bind('<ButtonPress-1>', lambda e: self.on_length_decrease_press())
            btn_minus.bind('<ButtonRelease-1>', lambda e: self.on_length_decrease_release())
                
        # 存储按钮引用
        if label == "张力 (kgf)":
            self.tension_minus_btn = btn_minus
        elif label == "弦长 (cm)":
            self.length_minus_btn = btn_minus
        
        # 滑块框架
        slider_frame = ttk.Frame(frame)
        slider_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 创建滑块
        if label == "弦长 (cm)":
            slider = ttk.Scale(slider_frame, from_=min_val, to=max_val, value=init_val,
                            orient=tk.HORIZONTAL, length=200, command=callback)
        else:
            slider = ttk.Scale(slider_frame, from_=min_val, to=max_val, value=init_val,
                            orient=tk.HORIZONTAL, length=200, command=callback)
        slider.pack(side=tk.TOP, fill=tk.X, expand=True)
        
        # + 按钮
        btn_plus = ttk.Button(frame, text="+", width=3)
        btn_plus.pack(side=tk.LEFT, padx=(5, 5))

        # 绑定鼠标事件
        if label == "张力 (kgf)":
            btn_plus.bind('<ButtonPress-1>', lambda e: self.on_tension_increase_press())
            btn_plus.bind('<ButtonRelease-1>', lambda e: self.on_tension_increase_release())
        elif label == "弦长 (cm)":
            btn_plus.bind('<ButtonPress-1>', lambda e: self.on_length_increase_press())
            btn_plus.bind('<ButtonRelease-1>', lambda e: self.on_length_increase_release())
        
        # 存储按钮引用
        if label == "张力 (kgf)":
            self.tension_plus_btn = btn_plus
        elif label == "弦长 (cm)":
            self.length_plus_btn = btn_plus
        
        # 调节步长说明和切换按钮
        multiplier_frame = ttk.Frame(frame)
        multiplier_frame.pack(side=tk.LEFT, padx=(0, 5))
        
        # 添加"调节步长："说明
        ttk.Label(multiplier_frame, text="调节步长：").pack(side=tk.LEFT)
        
        # 倍率切换按钮
        if label == "张力 (kgf)":
            initial_text = self.tension_multiplier_labels[self.tension_multiplier_index]
            multiplier_btn = ttk.Button(multiplier_frame, text=initial_text, width=5, 
                                    command=lambda: self.toggle_step_multiplier(label))
            multiplier_btn.pack(side=tk.LEFT)
            self.tension_multiplier_btn = multiplier_btn
            self.tension_slider = slider  # 只存储滑块引用
        elif label == "弦长 (cm)":
            initial_text = self.length_multiplier_labels[self.length_multiplier_index]
            multiplier_btn = ttk.Button(multiplier_frame, text=initial_text, width=5, 
                                    command=lambda: self.toggle_step_multiplier(label))
            multiplier_btn.pack(side=tk.LEFT)
            self.length_multiplier_btn = multiplier_btn
            self.length_slider = slider

    def update_probe_position(self, val):
        """更新探测位置 - 仅处理滑块事件"""
        new_position = float(val)
        # 限制探测位置范围：最小15cm，最大不超过弦长-10cm
        max_position = max(15, self.length - 10)
        new_position = min(max(new_position, 15), max_position)
        
        self.probe_position = new_position
        self.probe_var.set(f"{self.probe_position:.1f}")
        
        # 更新弦长的最小限制
        min_length = new_position + 10
        if self.length < min_length:
            self.length = min_length
            self.length_slider.set(min_length)
            self.length_var.set(f"{min_length:.1f}")
            self.update_length_display()
            self.update_resonance_info()
        
        self.update_probe_display()  # 这会自动更新图片位置
        

    def increment_probe(self):
        """增加探测位置"""
        if not self.string_tightened:
            return  # 弦线未拉紧时不执行
        
        step = 1 * self.get_current_probe_multiplier()
        max_position = max(15, self.length - 7)
        new_position = min(self.probe_position + step, max_position)
        
        self.probe_position = new_position
        self.probe_var.set(f"{self.probe_position:.1f}")
        self.probe_slider.set(new_position)
        self.update_probe_display()

    def decrement_probe(self):
        """减少探测位置"""
        if not self.string_tightened:
            return  # 弦线未拉紧时不执行
        
        step = 1 * self.get_current_probe_multiplier()
        new_position = max(self.probe_position - step, 15)
        
        self.probe_position = new_position
        self.probe_var.set(f"{self.probe_position:.1f}")
        self.probe_slider.set(new_position)
        self.update_probe_display()

    def update_probe_display(self):
        """更新探测位置显示"""
        # 移除旧的探测显示
        if hasattr(self, 'probe_display'):
            self.probe_display.remove()
        if hasattr(self, 'probe_point'):
            self.probe_point.remove()
        if hasattr(self, 'probe_box'):
            self.probe_box.remove()
        
        # 重新创建探测显示 - 使用固定范围显示，位置偏右
        if self.probe_img is not None:
            # 设置偏右的偏移量（比如偏右2cm）
            offset = 1.4  # 偏右2cm
            probe_extent = [self.probe_position-3 + offset, self.probe_position+3 + offset, -1.5, 4]
            self.probe_display = self.ax.imshow(self.probe_img, extent=probe_extent, aspect='auto', alpha=1)
        else:
            # 使用默认标记，也偏右
            offset = 1.4
            self.probe_point, = self.ax.plot(self.probe_position + offset, 0, '^', markersize=8, color='blue', label='探测点')
        
        # 更新探测位置滑块的最大值
        max_position = max(13, self.length -7)
        self.probe_slider.configure(to=max_position)
        
        self.canvas.draw_idle()

    def toggle_step_multiplier(self, label):
        """切换指定参数的调节步长"""
        
        if label == "张力 (kgf)":
            self.tension_multiplier_index = (self.tension_multiplier_index + 1) % len(self.tension_multipliers)
            self.update_multiplier_button("张力 (kgf)")
        elif label == "弦长 (cm)":
            self.length_multiplier_index = (self.length_multiplier_index + 1) % len(self.length_multipliers)
            self.update_multiplier_button("弦长 (cm)")
        elif label == "振幅 (mV)":
            self.amplitude_multiplier_index = (self.amplitude_multiplier_index + 1) % len(self.amplitude_multipliers)
            self.update_multiplier_button("振幅 (mV)")

    def update_multiplier_button(self, label):
        """更新倍率按钮的显示文本"""
        if label == "张力 (kgf)":
            index = self.tension_multiplier_index
            btn = self.tension_multiplier_btn
            labels = self.tension_multiplier_labels
        elif label == "弦长 (cm)":
            index = self.length_multiplier_index
            btn = self.length_multiplier_btn
            labels = self.length_multiplier_labels
        elif label == "振幅 (mV)":
            index = self.amplitude_multiplier_index
            btn = self.amplitude_multiplier_btn
            labels = self.amplitude_multiplier_labels
        
        btn.config(text=labels[index])

    def increment_parameter(self, label, base_step, callback):
        """增加参数值"""
        # 获取当前倍率
        multiplier = self.get_current_multiplier(label)
        step = base_step * multiplier
        if label == "张力 (kgf)":
            new_val = min(self.tension + step, 5)
            self.tension = new_val
            self.tension_slider.set(new_val)
            # self.tension_var.set(f"{new_val:.2f}")
        elif label == "弦长 (cm)":
            new_val = min(self.length + step, 103)
            self.length = new_val
            self.length_slider.set(new_val)
            self.length_var.set(f"{new_val:.1f}")
            self.update_length_display()
        elif label == "振幅 (mV)":
            new_val = min(self.amplitude_mv + step, 200)
            self.amplitude_mv = new_val
            self.amplitude_slider.set(new_val)
            self.amplitude_var.set(f"{new_val:.2f}")
        
        self.update_resonance_info()

    def decrement_parameter(self, label, base_step, callback):
        """减少参数值"""
        # 获取当前倍率
        multiplier = self.get_current_multiplier(label)
        step = base_step * multiplier
        if label == "张力 (kgf)":
            new_val = max(self.tension - step, 0)
            self.tension = new_val
            self.tension_slider.set(new_val)
            # self.tension_var.set(f"{new_val:.2f}")
        elif label == "弦长 (cm)":
            # 计算最小允许弦长：探测位置+10cm
            min_length = self.probe_position + 10
            new_val = max(self.length - step, min_length)
            self.length = new_val
            self.length_slider.set(new_val)
            self.length_var.set(f"{new_val:.1f}")
            self.update_length_display()
        elif label == "振幅 (mV)":
            new_val = max(self.amplitude_mv - step, 0)
            self.amplitude_mv = new_val
            self.amplitude_slider.set(new_val)
            self.amplitude_var.set(f"{new_val:.2f}")
        
        self.update_resonance_info()
    
    def get_current_multiplier(self, label):
        """获取指定参数的当前倍率"""
        if label == "张力 (kgf)":
            return self.tension_multipliers[self.tension_multiplier_index]
        elif label == "弦长 (cm)":
            return self.length_multipliers[self.length_multiplier_index]
        elif label == "振幅 (mV)":
            return self.amplitude_multipliers[self.amplitude_multiplier_index]
    
    def update_frequency(self, val):
        self.frequency = float(val)
        self.freq_var.set(f"{self.frequency:.2f}")
        self.update_resonance_info()
        self.update_display()  # 更新显示
    
    def update_tension(self, val):
        self.tension = float(val)
        # self.tension_var.set(f"{self.tension:.2f}")
        self.update_resonance_info()
        self.update_display()  # 更新显示
    
    def update_length(self, val):
        """更新弦长，确保不小于探测位置+10cm"""
        new_length = float(val)
        
        # 计算最小允许弦长：探测位置+10cm
        min_length = self.probe_position + 10
        
        # 如果新长度小于最小允许值，则调整到最小允许值
        if new_length < min_length:
            new_length = min_length
            # 同时更新滑块值
            self.length_slider.set(new_length)
        
        self.length = new_length
        self.length_var.set(f"{self.length:.1f}")
        self.update_length_display()
        self.update_resonance_info()
        self.update_display()
        # 强制立即重绘
        self.canvas.draw_idle()
        
    def update_zero_offset_from_left(self, val):
        """从左控制面板更新拉力计调零偏移"""
        self.zero_offset = float(val)
        
        # 更新显示
        self.update_display()


    def update_amplitude(self, val):
        # 这个函数现在只用于左侧控制面板的同步
        self.amplitude_mv = float(val)
        self.amplitude_var.set(f"{self.amplitude_mv:.2f}")
        # 同步更新实验仪的振幅旋钮
        if hasattr(self, 'amplitude_scale'):
            self.amplitude_scale.set(self.amplitude_mv)
        if hasattr(self, 'amplitude_var_instr'):
            self.amplitude_var_instr.set(f"{self.amplitude_mv:.0f}")
    
    def update_diameter_from_radio(self):
        self.diameter = float(self.diameter_var.get())
        self.update_resonance_info()
    
    def update_length_display(self):
        """更新长度显示和坐标轴"""
        # 重新生成x坐标
        self.x = np.linspace(0, self.length, 1000)
        
        # 根据当前模式更新y坐标
        if self.display_mode == "tension":
            # 拉力模式下，y坐标为全0
            self.y = np.zeros_like(self.x)
        else:
            # 振动模式下，保持原有的y值
            pass
        
        # 更新蓝线的数据
        self.line.set_data(self.x, self.y)
        
        # 更新滑轮组位置 - 使用固定范围显示
        if hasattr(self, 'pulley_display') and self.pulley_img is not None:
            # 移除旧的显示
            self.pulley_display.remove()
            # 重新创建显示，保持固定大小
            pulley_extent = [self.length-3, self.length+3, -1.5, 1.5]
            self.pulley_display = self.ax.imshow(self.pulley_img, extent=pulley_extent, aspect='auto', alpha=1)
        elif hasattr(self, 'pulley_box'):
            # 更新默认滑轮组标记
            self.pulley_box.remove()
            self.ax.plot(self.length, 0, 's', markersize=10, color='red', label='滑轮组')
        
        # 更新红色直线（从弦线末端到x=120）
        self.red_line.set_data([self.length, 120], [0, 0])
        
        # 更新探测位置限制
        self.update_probe_display()
        
        # 设置x轴范围，确保所有内容可见
        self.ax.set_xlim(0, max(140, self.length + 20))
        
        self.canvas.draw_idle()
    
    def calculate_wave_speed(self):
        """计算波在弦上的传播速度"""
        # 计算线密度 (g/cm)
        cross_section_area = np.pi * (self.diameter / 20) ** 2  # 转换为cm²
        linear_density = self.density_iron * cross_section_area  # g/cm
        
        # 计算波速 (cm/s)
        # 拉力转换为牛顿: 1 kg = 9.8 N
        tension_newton = self.tension * 9.8
        # 线密度转换为kg/m
        linear_density_kg_m = linear_density / 1000 * 100  # kg/m
        # 波速公式: v = sqrt(T/μ)
        wave_speed = np.sqrt(tension_newton / linear_density_kg_m) * 100  # cm/s
        
        return wave_speed
    
    def calculate_resonance_frequencies(self, n_harmonics=10):
        """计算共振频率"""
        wave_speed = self.calculate_wave_speed()
        fundamental_freq = wave_speed / (2 * self.length)  # 基频
        
        harmonics = []
        for n in range(1, n_harmonics + 1):
            harmonics.append(fundamental_freq * n)
        
        return fundamental_freq, harmonics
    
    # def update_resonance_info(self):
    #     """更新共振频率信息"""
    #     fundamental, harmonics = self.calculate_resonance_frequencies(5)  # 显示更多谐波
        
    #     # 检查当前频率是否接近任何共振频率
    #     resonance_detected = False
    #     resonance_harmonic = 0
        
    #     # 计算最接近的谐波
    #     if fundamental > 0:
    #         n_harmonic = max(1, round(self.frequency / fundamental))  # 确保至少为1
    #         expected_freq = n_harmonic * fundamental
    #         if abs(self.frequency - expected_freq) < 0.5:
    #             resonance_detected = True
    #             resonance_harmonic = n_harmonic
        
    #     # 更新文本
    #     if resonance_detected:
    #         self.resonance_text.set_text(f'共振检测到! 第{resonance_harmonic}谐波\n基频: {fundamental:.2f} Hz')
    #         self.resonance_text.set_color('red')
    #         # self.status_var.set(f"共振检测到! 第{resonance_harmonic}谐波")
    #     else:
    #         # 显示更多谐波信息
    #         harmonic_text = ", ".join([f"{h:.1f}" for h in harmonics[:15]])  # 显示前15个谐波
    #         self.resonance_text.set_text(f'谐振频率: {harmonic_text} Hz...')
    #         self.resonance_text.set_color('black')
    #         # self.status_var.set("系统运行中")
        
    #     self.canvas.draw_idle()
    
    def animation_loop(self):
        """动画循环"""
        while self.running:
            self.time += 0.00099
            
            if self.display_mode == "tension" or self.tension <= 0:
                # 拉力模式下，使用频率0来计算，这样弦完全静止
                effective_frequency = 0.0
                
                # 计算弦的位移 - 频率为0时，时间部分为0
                spatial_part = np.zeros_like(self.x)  # 也可以设为0，确保没有空间变化
                temporal_part = 0.0  # 频率为0，时间部分为0
                
                self.y = 0.0 * spatial_part * temporal_part  # 结果就是全0
                
                # 更新弦线显示属性
                self.line.set_color('b')
                self.line.set_linewidth(2)
                
                # 探测振幅也为0
                self.probe_amplitude = 0.0
            else:
                # 计算波速和基频
                wave_speed = self.calculate_wave_speed()
                fundamental_freq = wave_speed / (2 * self.length)
                
                # 计算最接近的谐波数
                if fundamental_freq > 0:
                    n_harmonic = self.frequency / fundamental_freq
                    n_int = round(n_harmonic)
                    
                    # 计算共振因子 - 越接近谐振频率，共振因子越大
                    if fundamental_freq > 0:
                        # 计算频率偏移百分比
                        freq_offset = abs(self.frequency - n_int * fundamental_freq)
                        freq_offset_ratio = freq_offset / fundamental_freq
                        
                        # 共振因子计算公式：偏移越小，共振因子越大
                        # 使用高斯函数来模拟共振曲线
                        if n_int >= 1 and freq_offset_ratio < 0.1:  # 在10%基频范围内
                            # 高斯共振曲线：exp(-(偏移)^2 / (2*宽度^2))
                            sigma = 0.02  # 共振宽度参数
                            resonance_factor = 2.0 * np.exp(-(freq_offset_ratio**2) / (2 * sigma**2))
                            n_harmonic = n_int
                        else:
                            # 远离谐振频率，共振因子较小
                            # 越远离，共振因子越小
                            resonance_factor = 1.0 / (1 + 10 * freq_offset_ratio**2)
                            n_harmonic = max(1, int(n_harmonic))  # 至少为1
                    else:
                        resonance_factor = 1.0
                        n_harmonic = 1
                else:
                    n_harmonic = 1
                    resonance_factor = 1.0
                
                # 将mV转换为图形振幅
                amplitude_factor = self.amplitude_mv / 1000.0
                
                # 额外增加一个基于共振因子的振幅增强
                # 当接近谐振频率时，振幅会显著增大
                enhanced_amplitude = amplitude_factor * resonance_factor
                
                # 添加频率匹配度对振幅的影响
                # 当频率与谐振频率完全匹配时，振幅最大
                if fundamental_freq > 0:
                    # 计算频率匹配度
                    freq_match_ratio = 1.0 - min(1.0, abs(self.frequency - n_int * fundamental_freq) / (0.1 * fundamental_freq))
                    
                    # 匹配度越高，振幅越大
                    enhanced_amplitude = enhanced_amplitude * (1 + 2 * freq_match_ratio**2)
                
                # 计算弦的位移
                spatial_part = np.sin(n_harmonic * np.pi * self.x / self.length)
                temporal_part = np.sin(2 * np.pi * self.frequency * self.time)
                
                self.y = enhanced_amplitude * spatial_part * temporal_part
                
                # 确保边界条件
                self.y[0] = 0.0
                self.y[-1] = 0.0
                
                # 更新图形
                self.line.set_data(self.x, self.y)
                
                # 计算探测位置的最大振幅
                probe_spatial = np.sin(n_harmonic * np.pi * self.probe_position / self.length)
                max_amplitude_at_probe = enhanced_amplitude * abs(probe_spatial)
                
                # 更新探测振幅显示 - 同时更新实例变量
                self.probe_amplitude = max_amplitude_at_probe * 100  # 这里更新探测振幅
            
            # 更新实验仪显示
            self.update_display()

            # 在GUI线程中更新画布
            self.root.after(0, self.canvas.draw_idle)
            
            time.sleep(0.05)
    
    def close(self):
        """关闭应用"""
        # 清理所有长按定时器
        timers = [
            self.tension_long_press_timer,
            self.tension_long_press_repeat_timer,
            self.length_long_press_timer,
            self.length_long_press_repeat_timer,
            self.probe_long_press_timer,
            self.probe_long_press_repeat_timer
        ]
        
        for timer in timers:
            if timer:
                self.root.after_cancel(timer)
        
        self.running = False
        if self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
        self.root.quit()
        self.root.destroy()

# 创建并运行仿真
if __name__ == "__main__":
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", lambda: None)  # 防止直接关闭
    
    simulator = StringVibrationSimulator(root)
    
    # 设置关闭事件
    root.protocol("WM_DELETE_WINDOW", simulator.close)
    
    root.mainloop()