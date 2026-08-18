import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
import sys
from PIL import Image, ImageTk
import random
import time

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class HallExperiment:
    # ==================== 实测数据拟合的多项式系数 ====================
    POLY_UPPER = np.array([
        2.5182118055383348e-18, 1.3492625796343097e-16,
        -1.5030302285583753e-12, 4.885604896961923e-13,
        -1.8965117198829675e-07, -0.0002329886887901997,
        0.6697405093359231, 78.22103482201453
    ])

    POLY_LOWER = np.array([
        -3.701890964829607e-19, -6.574835216815333e-16,
        4.734415967183772e-13, 3.881612891836147e-10,
        -5.806655033947451e-07, 0.00014502345362569802,
        0.6873778445089721, -73.26564770910605
    ])

    POLY_VIRGIN = np.array([
        -1.10625264e-12, 4.12158156e-09, -5.29945015e-06,
        2.63182417e-03, 1.04967057e-01, 0.0
    ])
    def __init__(self, parent):
        self.parent = parent
        self.root = parent.winfo_toplevel()
        
        # 实验状态
        self.is_demagnetizing = False
        self.demagnetize_complete = False
        self.is_zeroed = False
        self.current_display = "demagnetize"
        
        # IV关系界面参数
        self.iv_current_I = 0
        self.iv_current_B = 0
        
        # 灵敏度界面参数
        self.sens_current_Ih = 0

        # ==================== 退磁模型状态 ====================
        self.demag_data = []  # [(H, B), ...]
        self.demag_step = 0
        self.is_demagnetizing = False
        self.demagnetize_complete = False
        self._degauss_end_B = 0.0
        
        # 退磁模型状态
        self._hyst_branch = 'virgin'
        self._hyst_last_I = 0.0
        self._hyst_last_B = 0.0
        self._hyst_direction = 0
        self._hyst_turn_points = []
        self._hyst_loop_amp = 600.0
        self._hyst_max_amp = 0.0
        
        # 箭头标签引用
        self.arrow_excitation = None      # 励磁电流方向
        self.arrow_measure = None         # 测量端指示
        self.arrow_hall = None            # 霍尔电流方向
        self.arrow_experiment = None      # 实验指示箭头

        # 方向
        self.current_direction = 1

        # 初始化数据
        self.init_data()
        
        # 创建主框架并pack（首次显示）
        self.main_frame = tk.Frame(self.parent, bg='white')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建界面
        self.create_ui()
        
        # 设置初始化随机偏移
        self.init_random_offsets()
        
        # 长按定时器
        self.hold_timer = None
    
    # ==================== 物理模型 ====================
    def poly_upper(self, I):
        """上支曲线（下降支）"""
        return float(np.polyval(self.POLY_UPPER, I))

    def poly_lower(self, I):
        """下支曲线（上升支）- 关于原点对称"""
        return -self.poly_upper(-I)

    def poly_virgin(self, I):
        """初始磁化曲线 - 确保从0开始单调上升"""
        if abs(I) < 1.0:
            return 0.0
        val = float(np.polyval(self.POLY_VIRGIN, abs(I))) * (1 if I >= 0 else -1)
        if abs(I) < 200 and val < 0:
            if I >= 0:
                return abs(I) * 0.02
            else:
                return -abs(I) * 0.02
        return val

    def get_B_from_magnetic_model(self, I_mA):
        """
        使用磁滞回线模型计算随电流变化的磁场
        
        初始值等于剩磁，随电流变化沿磁滞回线移动
        """
        I_SAT = 600.0
        dI = I_mA - self._hyst_last_I

        if abs(dI) < 0.5:
            return self._hyst_last_B

        new_direction = 1 if dI > 0 else -1
        abs_I = abs(I_mA)

        # 更新最大幅度
        if abs_I > self._hyst_max_amp:
            self._hyst_max_amp = abs_I
            self._hyst_loop_amp = abs_I

        # 检测方向变化（转折点）
        if self._hyst_direction != 0 and new_direction != self._hyst_direction:
            self._hyst_turn_points.append((self._hyst_last_I, self._hyst_last_B, self._hyst_loop_amp))

            if self._hyst_branch == 'virgin':
                self._hyst_branch = 'upper' if new_direction < 0 else 'lower'
            elif new_direction > 0:
                self._hyst_branch = 'lower'
            else:
                self._hyst_branch = 'upper'

            self._hyst_loop_amp = abs(self._hyst_last_I)
            if len(self._hyst_turn_points) > 30:
                self._hyst_turn_points = self._hyst_turn_points[-30:]

        self._hyst_direction = new_direction

        if self._hyst_turn_points:
            turn_I, turn_B, _ = self._hyst_turn_points[-1]
        else:
            turn_I, turn_B = 0.0, 0.0

        amp = max(self._hyst_loop_amp, 1.0)
        
        # 获取剩磁作为初始值
        br = self.degauss_before_offset  # 使用退磁前偏移作为剩磁

        if self._hyst_branch == 'virgin':
            # 初始磁化曲线：从剩磁出发
            if abs_I < 1.0:
                B_new = br
            else:
                B_virgin = self.poly_virgin(I_mA)
                if I_mA > 0:
                    B_new = br + (B_virgin - br) * (1 - np.exp(-abs_I / 50))
                else:
                    B_new = br + (B_virgin - br) * (1 - np.exp(-abs_I / 50))
        else:
            # 主回线：使用缩放曲线
            scale = amp / I_SAT
            I_scaled = np.clip(I_mA / scale, -I_SAT, I_SAT)

            if self._hyst_branch == 'upper':
                B_boundary = self.poly_upper(I_scaled) * scale
            else:
                B_boundary = self.poly_lower(I_scaled) * scale

            if self._hyst_turn_points:
                turn_I_scaled = turn_I / scale if scale > 0.01 else 0
                turn_I_scaled = np.clip(turn_I_scaled, -I_SAT, I_SAT)

                if self._hyst_branch == 'upper':
                    B_boundary_at_turn = self.poly_upper(turn_I_scaled) * scale
                else:
                    B_boundary_at_turn = self.poly_lower(turn_I_scaled) * scale

                offset = turn_B - B_boundary_at_turn
                travel = abs(I_mA - turn_I)
                offset_factor = np.exp(-0.005 * travel)
                B_new = B_boundary + offset * offset_factor
            else:
                B_new = B_boundary

        # 边界限制
        B_upper = self.poly_upper(I_mA)
        B_lower = self.poly_lower(I_mA)
        B_new = np.clip(B_new, min(B_lower, B_upper), max(B_upper, B_lower))

        self._hyst_last_I = I_mA
        self._hyst_last_B = B_new

        return B_new

    def _is_on_hysteresis_branch(self):
        """
        判断当前是否在磁滞回线的上升支上
        
        返回 True 表示已经到达磁滞回线上升支
        """
        if self._hyst_branch == 'lower':
            return True
        
        if len(self._hyst_turn_points) > 0:
            last_turn_I = self._hyst_turn_points[-1][0] if self._hyst_turn_points else 0
            if last_turn_I > 100:
                return True
        
        if self._hyst_direction > 0 and self._hyst_max_amp > 100:
            return True
        
        return False

    def reset_hysteresis_state(self, use_remanence=True):
        """
        重置磁滞状态
        
        Parameters:
            use_remanence: 是否使用基础剩磁作为初始值
        """
        self._hyst_branch = 'virgin'
        self._hyst_last_I = 0.0
        self._hyst_turn_points = []
        
        if use_remanence:
            self._hyst_last_B = self.degauss_before_offset
        else:
            self._hyst_last_B = 0.0
        
        self._hyst_direction = 0
        self._hyst_loop_amp = 600.0
        self._hyst_max_amp = 0.0
        
    def on_show(self):
        """当实验被显示时调用"""
        # 重新显示主框架
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 更新显示
        self.update_magnetic_field()
        
        # 如果有退磁曲线，使用统一方法更新
        if hasattr(self, 'canvas_plot') and self.canvas_plot is not None and self.demag_data:
            self._update_demag_axes()
            self.canvas_plot.draw()
    
    def create_ui(self):
        """创建UI界面"""
        # 创建主布局
        self.create_main_layout()
        
        # 创建左侧实验装置区域
        self.create_left_area()
        
        # 创建右上实验操作区域
        self.create_right_top_area()
        
        # 创建右下数据记录区域
        self.create_right_bottom_area()
        
        # 初始化默认选择
        self.on_demagnetize_select()
    
    def create_main_layout(self):
        """创建主布局 - 不包含顶部框架"""
        # 主要内容框架
        main_content = tk.Frame(self.main_frame)
        main_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧框架
        self.left_frame = tk.Frame(main_content, width=400, bg='white')
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        # 右侧框架
        right_frame = tk.Frame(main_content)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 右上框架
        self.right_top_frame = tk.Frame(right_frame, height=240, bg='lightyellow')
        self.right_top_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # 右下框架
        self.right_bottom_frame = tk.Frame(right_frame, bg='lightgreen')
        self.right_bottom_frame.pack(fill=tk.BOTH, expand=True)

    def get_resource_path(self, relative_path):
        """获取资源的绝对路径"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    
    def init_data(self):
        """初始化数据"""
        self.voltage_offset = 0
        self.millitesla_offset = 0
        self.hall_position = 0  # mm
        self.excitation_current = 0  # mA
        self.constant_current = 0  # mA
        
        # 测量端选择: "UR" 或 "UH"
        self.measure_mode = "UH"  # 默认UH
        
        # 霍尔电流方向: True为正向, False为反向
        self.hall_current_direction = True
        self.hall_current_direction_text = tk.StringVar(value="正向")
        
        # 退磁数据
        self.demag_data = []  # [(H, B), ...]
        self.current_direction = 1  # 1:正向, -1:反向
        self.current_max = 600  # mA
        self.current_step = 0  # 从0开始
        
        # 退磁模型状态
        self.demag_state = {
            'I': 0.0,
            'B': 0.0,
            'direction': 0,
            'amplitude': 600.0,
            'turn_points': [],
            'branch': 'initial',
            'is_initial_rise': True
        }
        
        # 退磁过程记录
        self.demag_process = []
        
        # 控件引用
        self.fig = None
        self.ax = None
        self.canvas_plot = None

        # 霍尔元件在图片上的位置
        self.hall_element_x = 153
        self.hall_element_y = 367
        self.hall_element_length = 260
    
    def update_direction_button(self):
        """更新方向按钮的显示"""
        try:
            if hasattr(self, 'direction_btn') and self.direction_btn is not None:
                if self.direction_btn.winfo_exists():
                    if self.current_direction == 1:
                        self.direction_btn.config(text="正向", bg='lightblue')
                    else:
                        self.direction_btn.config(text="反向", bg='lightcoral')
        except (tk.TclError, RuntimeError, AttributeError):
            # 按钮已被销毁或不存在，忽略错误
            pass

    def init_random_offsets(self):
        """初始化时给电压和毫特计添加随机偏移（只生成一次）"""
        # 删除这段
        # self.voltage_offset = random.uniform(-10, 10)
        # self.millitesla_offset = random.uniform(-10, 10)
        
        # 改为固定为0
        self.voltage_offset = 0.0
        self.millitesla_offset = random.uniform(-10, 10)
        
        # 额外添加一个退磁前的随机偏移（-150到-100mT），退磁后消除
        self.degauss_before_offset = random.uniform(-30, -20)
        # 保存总偏移（显示用）
        self.total_millitesla_offset = self.millitesla_offset + self.degauss_before_offset
        
        # 保存为固定偏移值，不再变化
        self.fixed_voltage_offset = 0.0  # ← 改为0
        self.fixed_millitesla_offset = self.millitesla_offset
        
        # 更新进度条显示（如果有）
        if hasattr(self, 'voltage_offset_scale'):
            self.voltage_offset_scale.set(self.voltage_offset)
        if hasattr(self, 'millitesla_offset_scale'):
            self.millitesla_offset_scale.set(self.millitesla_offset)
        
        # 更新显示
        if hasattr(self, 'voltage_var'):
            self.update_voltage_display()
        if hasattr(self, 'millitesla_var'):
            self.update_millitesla_display()
        if hasattr(self, 'voltage_var') and hasattr(self, 'millitesla_var'):
            self.update_magnetic_field()
        
        print(f"初始化随机偏移: 电压偏移={self.voltage_offset:.2f}mV, 毫特计偏移={self.millitesla_offset:.2f}mT, 退磁前偏移={self.degauss_before_offset:.2f}mT")
    
    def go_to_solenoid_experiment(self):
        """跳转到螺线管实验"""
        self.root.destroy()
        # 导入并运行螺线管实验
        try:
            import FD_ELE_A1
            new_root = tk.Tk()
            FD_ELE_A1.main()
        except ImportError:
            messagebox.showerror("错误", "无法找到螺线管实验文件 FD-ELE-A.py")
    
    def create_left_area(self):
        """创建左侧实验装置区域"""
        self.canvas = tk.Canvas(self.left_frame, width=680, height=700, bg='white')
        self.canvas.pack()
        
        # 加载霍尔效应图片
        try:
            hall_img_path = self.get_resource_path("background/霍尔效应.jpg")
            pil_hall = Image.open(hall_img_path)
            pil_hall = pil_hall.resize((680, 700), Image.Resampling.LANCZOS)
            self.hall_image = ImageTk.PhotoImage(pil_hall)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.hall_image)
            print("霍尔效应图片加载成功")
        except Exception as e:
            print(f"无法加载霍尔效应图片: {e}")
            self.canvas.create_rectangle(0, 0, 680, 700, fill='lightgray')
            self.canvas.create_text(340, 350, text="霍尔效应图片加载失败", font=("Arial", 14))
        
        # 创建文本框叠加在图片上
        self.create_textboxes_on_image()
        
        # ===== 创建箭头指示标签 =====
        self.create_arrow_indicators()
        
        # 在y=360位置画一条长度260px的横线表示霍尔元件
        self.hall_element_x = 153
        self.hall_element_y = 367
        self.hall_element_length = 260
        self.canvas.create_line(self.hall_element_x, self.hall_element_y, 
                            self.hall_element_x + self.hall_element_length, self.hall_element_y,
                            fill='red', width=3, tags="hall_element")
    
    def create_arrow_indicators(self):
        """在图片上创建箭头指示标签"""
        
        # ===== 1. 励磁电流方向指示 =====
        # 位置：电流表附近，显示向左或向右的箭头
        # 使用 Canvas 绘制箭头
        self.arrow_excitation = self.canvas.create_text(
            80, 295,  # 电流表下方位置
            text="←",  # 默认向左，后续更新
            font=("Arial", 32, "bold"),
            fill="red",
            tags="arrow_excitation"
        )
        
        # ===== 2. 测量端指示 =====
        # 位置：电压表附近，显示向上或向下的箭头
        self.arrow_measure = self.canvas.create_text(
            85+238, 210,   # 电压表下方位置
            text="↑",   # 默认向下（UH），后续更新
            font=("Arial", 32, "bold"),
            fill="blue",
            tags="arrow_measure"
        )
        
        # ===== 3. 霍尔电流方向指示 =====
        # 位置：毫特计附近，显示向上或向下的箭头
        self.arrow_hall = self.canvas.create_text(
            553, 210,  # 毫特计下方位置
            text="↑",   # 默认向上（正向），后续更新
            font=("Arial", 32, "bold"),
            fill="green",
            tags="arrow_hall"
        )
        
        # ===== 4. 实验指示箭头（固定向左） =====
        # 位置：在霍尔元件附近或图片空白区域
        self.arrow_experiment = self.canvas.create_text(
            160, 610,  # 右侧空白区域
            text="←",   # 固定向左
            font=("Arial", 32, "bold"),
            fill="#FF6B00",
            tags="arrow_experiment"
        )

    def update_arrows(self):
        """更新所有箭头指示标签"""
        try:
            # ===== 1. 更新励磁电流方向 =====
            if hasattr(self, 'arrow_excitation') and self.arrow_excitation:
                if self.current_direction == 1:
                    # 正向 → 显示向左的箭头（电流从左向右流）
                    self.canvas.itemconfig(self.arrow_excitation, text="←")
                else:
                    # 反向 → 显示向右的箭头（电流从右向左流）
                    self.canvas.itemconfig(self.arrow_excitation, text="→")
            
            # ===== 2. 更新测量端指示 =====
            if hasattr(self, 'arrow_measure') and self.arrow_measure:
                if self.measure_mode == "UR":
                    self.canvas.itemconfig(self.arrow_measure, text="↓")
                else:  # UH
                    self.canvas.itemconfig(self.arrow_measure, text="↑")
            
            # ===== 3. 更新霍尔电流方向 =====
            if hasattr(self, 'arrow_hall') and self.arrow_hall:
                if self.hall_current_direction:
                    # 正向 → 向上的箭头
                    self.canvas.itemconfig(self.arrow_hall, text="↑")
                else:
                    # 反向 → 向下的箭头
                    self.canvas.itemconfig(self.arrow_hall, text="↓")
                    
            # 实验指示箭头固定，不需要更新
                    
        except (tk.TclError, RuntimeError):
            # 箭头可能还未创建，忽略错误
            pass

    def create_textboxes_on_image(self):
        """在图片上创建文本框"""
        # 电压表文本框
        self.voltage_var = tk.StringVar(value="0")
        voltage_entry = tk.Entry(self.left_frame, textvariable=self.voltage_var,
                                width=8, font=("Arial", 10), justify='center',
                                state='readonly', readonlybackground='white')
        self.canvas.create_window(85, 535, window=voltage_entry, anchor=tk.NW)
        
        # 电流表文本框
        self.current_var = tk.StringVar(value="0")
        current_entry = tk.Entry(self.left_frame, textvariable=self.current_var,
                                width=8, font=("Arial", 10), justify='center',
                                state='readonly', readonlybackground='white')
        self.canvas.create_window(265, 535, window=current_entry, anchor=tk.NW)
        
        # 毫特计文本框
        self.millitesla_var = tk.StringVar(value="0")
        millitesla_entry = tk.Entry(self.left_frame, textvariable=self.millitesla_var,
                                    width=8, font=("Arial", 10), justify='center',
                                    state='readonly', readonlybackground='white')
        self.canvas.create_window(410, 535, window=millitesla_entry, anchor=tk.NW)
    
    def create_hold_button(self, parent, text, command, repeat_delay=300, repeat_interval=50):
        """创建支持长按的按钮"""
        button = tk.Button(parent, text=text, width=2)
        
        def on_press(event):
            command()
            self.cancel_hold_timer()
            self.hold_timer = self.root.after(repeat_delay, lambda: self.start_repeat(command, repeat_interval))
        
        def on_release(event):
            self.cancel_hold_timer()
        
        button.bind("<ButtonPress-1>", on_press)
        button.bind("<ButtonRelease-1>", on_release)
        button.bind("<Leave>", on_release)
        
        return button
    
    def cancel_hold_timer(self):
        """取消长按定时器"""
        if self.hold_timer is not None:
            self.root.after_cancel(self.hold_timer)
            self.hold_timer = None
    
    def start_repeat(self, command, interval):
        """开始重复执行"""
        command()
        self.hold_timer = self.root.after(interval, lambda: self.start_repeat(command, interval))
    
    def create_right_top_area(self):
        """创建右上实验操作区域"""
        main_frame = tk.Frame(self.right_top_frame, bg='lightyellow')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 第1行：霍尔元件位置
        pos_frame = tk.Frame(main_frame, bg='lightyellow')
        pos_frame.grid(row=0, column=0, padx=10, pady=5, sticky='w', columnspan=2)
        tk.Label(pos_frame, text="霍尔元件位置(mm):", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.position_scale = tk.Scale(pos_frame, from_=-20, to=20, orient=tk.HORIZONTAL,
                                    length=300, resolution=1, command=self.update_position)
        self.position_scale.pack(side=tk.LEFT, padx=5)
        # 设置进度条为0且不可用
        self.position_scale.set(0)
        self.position_scale.config(state='disabled')
        # 微调按钮禁用
        btn_minus_pos = self.create_hold_button(pos_frame, "-", lambda: self.adjust_position(-1))
        btn_minus_pos.pack(side=tk.LEFT, padx=1)
        btn_minus_pos.config(state='disabled')
        btn_plus_pos = self.create_hold_button(pos_frame, "+", lambda: self.adjust_position(1))
        btn_plus_pos.pack(side=tk.LEFT, padx=1)
        btn_plus_pos.config(state='disabled')
      
        # 第2行：励磁电流
        current_frame = tk.Frame(main_frame, bg='lightyellow')
        current_frame.grid(row=1, column=0, padx=10, pady=5, sticky='w')
        tk.Label(current_frame, text="励磁电流(mA):", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.excitation_scale = tk.Scale(current_frame, from_=0, to=600, orient=tk.HORIZONTAL,
                                        length=200, command=self.update_excitation_current)
        self.excitation_scale.pack(side=tk.LEFT, padx=5)
        btn_minus_cur = self.create_hold_button(current_frame, "-", lambda: self.adjust_excitation(-1))
        btn_minus_cur.pack(side=tk.LEFT, padx=1)
        btn_plus_cur = self.create_hold_button(current_frame, "+", lambda: self.adjust_excitation(1))
        btn_plus_cur.pack(side=tk.LEFT, padx=1)
        # 电流方向切换
        self.direction_btn = tk.Button(current_frame, text="正向",
                                       command=self.toggle_direction,
                                       width=6, bg='lightblue')
        self.direction_btn.pack(side=tk.LEFT, padx=10)
        
        # 第2行第2列：恒流源电流
        constant_frame = tk.Frame(main_frame, bg='lightyellow')
        constant_frame.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        tk.Label(constant_frame, text="恒流源电流(mA):", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.constant_scale = tk.Scale(constant_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                      length=200, showvalue=0, command=self.update_constant_current)
        self.constant_scale.pack(side=tk.LEFT, padx=5)
        btn_minus_const = self.create_hold_button(constant_frame, "-", lambda: self.adjust_constant(-0.05))
        btn_minus_const.pack(side=tk.LEFT, padx=1)
        btn_plus_const = self.create_hold_button(constant_frame, "+", lambda: self.adjust_constant(0.05))
        btn_plus_const.pack(side=tk.LEFT, padx=1)
        
        # # 第3行：电压表调零
        # voff_frame = tk.Frame(main_frame, bg='lightyellow')
        # voff_frame.grid(row=2, column=0, padx=10, pady=5, sticky='w')
        # tk.Label(voff_frame, text="电压表调零(mV):", bg='lightyellow',
        #         font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        # self.voltage_offset_scale = tk.Scale(voff_frame, from_=-50, to=50, orient=tk.HORIZONTAL,
        #                                     length=200, resolution=0.1, showvalue=0,
        #                                     command=self.update_voltage_offset)
        # self.voltage_offset_scale.pack(side=tk.LEFT, padx=5)
        # btn_minus_voff = self.create_hold_button(voff_frame, "-", lambda: self.adjust_voltage_offset(-0.1))
        # btn_minus_voff.pack(side=tk.LEFT, padx=1)
        # btn_plus_voff = self.create_hold_button(voff_frame, "+", lambda: self.adjust_voltage_offset(0.1))
        # btn_plus_voff.pack(side=tk.LEFT, padx=1)

        # 测量端切换（放在电压表调零同一行右侧）
        mode_frame = tk.Frame(main_frame, bg='lightyellow')
        mode_frame.grid(row=2, column=1, padx=10, pady=5, sticky='w')
        tk.Label(mode_frame, text="测量端:", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        # 创建两个单选按钮
        self.mode_var = tk.StringVar(value="UH")
        btn_ur = tk.Radiobutton(mode_frame, text="UR", variable=self.mode_var, value="UR",
                                command=self.on_mode_changed, bg='lightyellow')
        btn_ur.pack(side=tk.LEFT, padx=2)
        btn_uh = tk.Radiobutton(mode_frame, text="UH", variable=self.mode_var, value="UH",
                                command=self.on_mode_changed, bg='lightyellow')
        btn_uh.pack(side=tk.LEFT, padx=2)

        # ---------- 霍尔电流方向切换（放在测量端右侧） ----------
        hall_dir_frame = tk.Frame(main_frame, bg='lightyellow')
        hall_dir_frame.grid(row=2, column=1, padx=(160, 10), pady=5, sticky='w')
        tk.Label(hall_dir_frame, text="霍尔电流:", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        self.hall_dir_btn = tk.Button(hall_dir_frame, text="正向",
                                    command=self.toggle_hall_direction,
                                    width=6, bg='lightblue')
        self.hall_dir_btn.pack(side=tk.LEFT, padx=2)
        
        # 第4行：毫特计调零（原来在第3行第2列，现在移到第4行）
        moff_frame = tk.Frame(main_frame, bg='lightyellow')
        moff_frame.grid(row=2, column=0, padx=10, pady=5, sticky='w', columnspan=2)
        tk.Label(moff_frame, text="毫特计调零(mT):", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.millitesla_offset_scale = tk.Scale(moff_frame, from_=-50, to=50, orient=tk.HORIZONTAL,
                                            length=200, resolution=0.1, showvalue=0,
                                            command=self.update_millitesla_offset)
        self.millitesla_offset_scale.pack(side=tk.LEFT, padx=5)
        btn_minus_moff = self.create_hold_button(moff_frame, "-", lambda: self.adjust_millitesla_offset(-0.1))
        btn_minus_moff.pack(side=tk.LEFT, padx=1)
        btn_plus_moff = self.create_hold_button(moff_frame, "+", lambda: self.adjust_millitesla_offset(0.1))
        btn_plus_moff.pack(side=tk.LEFT, padx=1)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
    
    def toggle_hall_direction(self):
        """切换霍尔电流方向"""
        self.hall_current_direction = not self.hall_current_direction
        if self.hall_current_direction:
            self.hall_current_direction_text.set("正向")
            self.hall_dir_btn.config(bg='lightblue', text="正向")
        else:
            self.hall_current_direction_text.set("反向")
            self.hall_dir_btn.config(bg='lightcoral', text="反向")
        self.update_voltage_display()
        self.update_magnetic_field()
        self.update_arrows()  # ← 添加这行

    def on_mode_changed(self):
        """测量端切换回调"""
        self.measure_mode = self.mode_var.get()
        self.update_voltage_display()
        self.update_arrows()  # ← 添加这行

    # ---------- 微调按钮回调函数 ----------
    def adjust_position(self, delta):
        new_val = self.hall_position + delta
        new_val = max(-20, min(20, new_val))
        self.hall_position = new_val
        self.position_scale.set(new_val)
        
        # 霍尔元件水平移动：每增大1mm，左移2px
        offset_x = self.hall_position * 1.76
        new_x = 151 - offset_x
        
        # 更新横线位置
        self.canvas.coords("hall_element", new_x, self.hall_element_y, 
                        new_x + self.hall_element_length, self.hall_element_y)

    def adjust_excitation(self, delta):
        new_val = self.excitation_current + delta
        new_val = max(0, min(600, new_val))
        self.excitation_current = new_val
        self.excitation_scale.set(new_val)
     
        self.current_var.set(str(new_val))  # 电流显示框显示励磁电流值
        self.update_magnetic_field()
    
    def adjust_constant(self, delta):
        new_val = self.constant_current + delta
        new_val = max(0, min(100, new_val))
        self.constant_current = new_val
        self.constant_scale.set(new_val)
        self.update_voltage_display()  # 恒流源变化立即更新电压
    
    def adjust_millitesla_offset(self, delta):
        """调整毫特计调零"""
        new_val = self.millitesla_offset + delta
        new_val = max(-50, min(50, new_val))
        self.millitesla_offset = new_val
        self.fixed_millitesla_offset = new_val  # 更新固定偏移
        self.millitesla_offset_scale.set(new_val)
        self.update_millitesla_display()
    
    # ---------- 进度条回调函数 ----------
    def update_position(self, value):
        """更新霍尔元件位置"""
        self.hall_position = int(float(value))
        
        # 霍尔元件水平移动：每增大1mm，左移2px
        # 初始位置在x=200，位置为0时在x=200
        # 位置增大时左移，位置减小时右移
        offset_x = self.hall_position * 1.76  # 每1mm移动2px
        new_x = 151 - offset_x  # 位置增大时左移
        
        # 更新横线位置
        self.canvas.coords("hall_element", new_x, self.hall_element_y, 
                        new_x + self.hall_element_length, self.hall_element_y)
    
    def update_excitation_current(self, value):
        self.excitation_current = int(float(value))
        self.current_var.set(str(self.excitation_current))  # 电流显示框显示励磁电流值
        self.update_magnetic_field()
        self.update_arrows()  # ← 如果需要实时更新
    
    def update_constant_current(self, value):
        self.constant_current = int(float(value))
        self.update_voltage_display()  # 恒流源变化立即更新电压
    
    def adjust_voltage_offset(self, delta):
        pass
    
    def update_voltage_offset(self, value):
        pass

    def update_millitesla_offset(self, value):
        """更新毫特计调零"""
        self.millitesla_offset = float(value)
        self.fixed_millitesla_offset = float(value)  # 更新固定偏移
        self.update_millitesla_display()
    
    def toggle_direction(self):
        """切换电流方向"""
        if hasattr(self, 'current_direction'):
            self.current_direction *= -1
        else:
            self.current_direction = -1
        self.update_direction_button()
        self.update_magnetic_field()
        self.update_arrows()  # ← 添加这行
    
    def update_voltage_display(self):
        """更新电压表显示 - 根据测量端选择显示不同值"""
        measured_voltage = 0
        
        if self.measure_mode == "UR":
            # UR模式：电压 = 恒流源电流 * (-2)
            measured_voltage = self.constant_current * (-2)
        else:
            # ===== UH模式 =====
            # 计算恒流源贡献部分（与励磁电流无关）
            ih_ratio = self.constant_current / 50.0
            constant_part = 0.6 * ih_ratio
            
            # 判断霍尔电流与励磁电流方向是否一致
            excitation_is_forward = (self.current_direction == 1)
            direction_match = (self.hall_current_direction == excitation_is_forward)
            
            # 方向相同时为负，方向不同时为正
            if direction_match:
                constant_part = -constant_part   # 方向一致 → 负
            else:
                constant_part = constant_part    # 方向不一致 → 正
            
            if self.excitation_current != 0:
                # 励磁电流相关部分
                excitation_part = self.constant_current * (-2) * 0.4937 / 240.0 * self.excitation_current
                
                # 方向相同时为负，方向不同时为正
                if direction_match:
                    excitation_part = excitation_part    # 方向一致 → 负
                else:
                    excitation_part = -excitation_part   # 方向不一致 → 正
                
                # 反向励磁电流时乘以0.97的修正系数
                if self.current_direction == -1:
                    excitation_part = excitation_part * 0.97
                
                measured_voltage = excitation_part + constant_part
            else:
                # 励磁电流为0时，只有恒流源贡献
                measured_voltage = constant_part
        
        # 显示电压值（不加偏移）
        displayed_voltage = measured_voltage
        if hasattr(self, 'voltage_var'):
            self.voltage_var.set(f"{displayed_voltage:.1f}")
    
    def update_millitesla_display(self):
        """更新毫特计显示 - 使用固定的随机偏移"""
        # 励磁电流每300mA产生250mT磁场
        # 根据电流方向确定符号
        if self.current_direction == 1:
            # 正向
            measured_b = self.excitation_current * 250.0 / 300.0
        else:
            # 反向
            measured_b = -self.excitation_current * 250.0 / 300.0
        
        # 如果正在退磁或尚未完成退磁，显示包含退磁前偏移
        if not self.demagnetize_complete:
            display_offset = self.millitesla_offset + self.degauss_before_offset
        else:
            display_offset = self.millitesla_offset
        
        # 加上固定的随机偏移
        displayed_b = measured_b + display_offset
        if hasattr(self, 'millitesla_var'):
            self.millitesla_var.set(f"{displayed_b:.1f}")
    
    def update_magnetic_field(self):
        """更新磁场显示"""
        # 励磁电流每300mA产生250mT磁场
        if self.current_direction == 1:
            measured_b = self.excitation_current * 250.0 / 300.0
        else:
            measured_b = -self.excitation_current * 250.0 / 300.0
        
        # 电压值根据测量端选择计算
        measured_voltage = 0
        if self.measure_mode == "UR":
            measured_voltage = self.constant_current * (-2)
        else:
            # ===== UH模式 =====
            ih_ratio = self.constant_current / 50.0
            constant_part = 0.6 * ih_ratio
            
            # 判断霍尔电流与励磁电流方向是否一致
            excitation_is_forward = (self.current_direction == 1)
            direction_match = (self.hall_current_direction == excitation_is_forward)
            
            # 方向相同时为负，方向不同时为正
            if direction_match:
                constant_part = -constant_part
            else:
                constant_part = constant_part
            
            if self.excitation_current != 0:
                excitation_part = self.constant_current * (-2) * 0.4937 / 240.0 * self.excitation_current
                
                if direction_match:
                    excitation_part = excitation_part
                else:
                    excitation_part = -excitation_part
                
                if self.current_direction == -1:
                    excitation_part = excitation_part * 0.97
                
                measured_voltage = excitation_part + constant_part
            else:
                measured_voltage = constant_part
        
        # 电压值显示
        displayed_voltage = measured_voltage
        if hasattr(self, 'voltage_var'):
            self.voltage_var.set(f"{displayed_voltage:.1f}")
        
        # 毫特计显示
        if not self.demagnetize_complete:
            display_offset = self.millitesla_offset + self.degauss_before_offset
        else:
            display_offset = self.millitesla_offset
        
        displayed_b = measured_b + display_offset
        if hasattr(self, 'millitesla_var'):
            self.millitesla_var.set(f"{displayed_b:.1f}")
        
    def create_right_bottom_area(self):
        """创建右下数据记录区域"""
        # 选项卡按钮组
        self.tab_frame = tk.Frame(self.right_bottom_frame)
        self.tab_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建选项卡按钮并保存引用
        self.btn_demag = tk.Button(self.tab_frame, text="退磁和调零",
                                command=self.on_demagnetize_select,
                                width=20, bg='lightblue')
        self.btn_demag.pack(side=tk.LEFT, padx=5)
        
        self.btn_iv = tk.Button(self.tab_frame, text="测量霍尔电流与霍尔电压的关系",
                                command=self.on_iv_relation_select,
                                width=25)
        self.btn_iv.pack(side=tk.LEFT, padx=5)
        
        self.btn_sensitivity = tk.Button(self.tab_frame, text="测量砷化镓霍尔元件的灵敏度",
                                        command=self.on_sensitivity_select,
                                        width=25)
        self.btn_sensitivity.pack(side=tk.LEFT, padx=5)
        
        # 内容框架 - 作为容器放置所有选项卡页面
        self.bottom_content_frame = tk.Frame(self.right_bottom_frame, bg='white')
        self.bottom_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== 创建三个独立的页面框架（只创建一次） =====
        
        # 1. 退磁页面
        self.demag_page = tk.Frame(self.bottom_content_frame, bg='white')
        self.create_demag_page(self.demag_page)
        
        # 2. IV关系页面
        self.iv_page = tk.Frame(self.bottom_content_frame, bg='white')
        self.create_iv_page(self.iv_page)
        
        # 3. 灵敏度页面
        self.sensitivity_page = tk.Frame(self.bottom_content_frame, bg='white')
        self.create_sensitivity_page(self.sensitivity_page)
        
        # 默认显示退磁页面
        self.show_page("demagnetize")
    
    def show_page(self, page_name):
        """显示指定的页面，隐藏其他页面"""
        # ===== 切换前保存当前页面数据（只有当前页面有数据时才保存） =====
        if self.current_display == "iv_relation":
            # 检查IV页面是否有数据
            has_iv_data = False
            if hasattr(self, 'iv_entries') and self.iv_entries:
                for i in range(9):
                    ur = self.iv_entries['ur'][i].get().strip()
                    u1 = self.iv_entries['u1'][i].get().strip()
                    u2 = self.iv_entries['u2'][i].get().strip()
                    u3 = self.iv_entries['u3'][i].get().strip()
                    u4 = self.iv_entries['u4'][i].get().strip()
                    if ur or u1 or u2 or u3 or u4:
                        has_iv_data = True
                        break
            if has_iv_data:
                self.save_iv_data_from_table()
            # 如果没有数据，但之前保存过数据，保留之前的数据（不覆盖）
                
        elif self.current_display == "sensitivity":
            # 检查灵敏度页面是否有数据
            has_sens_data = False
            if hasattr(self, 'sens_entries') and self.sens_entries:
                for i in range(11):
                    b = self.sens_entries['b'][i].get().strip()
                    u1 = self.sens_entries['u1'][i].get().strip()
                    if b or u1:
                        has_sens_data = True
                        break
            if has_sens_data:
                self.save_sensitivity_data_from_table()
            # 如果没有数据，但之前保存过数据，保留之前的数据（不覆盖）
        
        # 隐藏所有页面
        if hasattr(self, 'demag_page'):
            self.demag_page.pack_forget()
        if hasattr(self, 'iv_page'):
            self.iv_page.pack_forget()
        if hasattr(self, 'sensitivity_page'):
            self.sensitivity_page.pack_forget()
        
        # 显示目标页面
        if page_name == "demagnetize":
            self.demag_page.pack(fill=tk.BOTH, expand=True)
            if hasattr(self, 'canvas_plot') and self.canvas_plot:
                self._update_demag_axes()
                self.canvas_plot.draw()
        elif page_name == "iv_relation":
            self.iv_page.pack(fill=tk.BOTH, expand=True)
            # 如果有保存的数据则恢复
            if hasattr(self, 'iv_saved_data') and self.iv_saved_data:
                # 检查是否有实际数据
                has_data = False
                for key in ['ur', 'u1', 'u2', 'u3', 'u4']:
                    if self.iv_saved_data.get(key) and any(v for v in self.iv_saved_data[key] if v):
                        has_data = True
                        break
                if has_data:
                    self.restore_iv_data()
        elif page_name == "sensitivity":
            self.sensitivity_page.pack(fill=tk.BOTH, expand=True)
            if hasattr(self, 'sens_saved_data') and self.sens_saved_data:
                has_data = False
                for key in ['b', 'u1', 'u2', 'u3', 'u4']:
                    if self.sens_saved_data.get(key) and any(v for v in self.sens_saved_data[key] if v):
                        has_data = True
                        break
                if has_data:
                    self.restore_sensitivity_data()
        
        self.current_display = page_name

    def create_demag_page(self, parent):
        """创建退磁页面（只创建一次）"""
        # 退磁按钮
        btn_frame = tk.Frame(parent, bg='white')
        btn_frame.pack(pady=10)
        
        self.demag_btn = tk.Button(btn_frame, text="自动退磁", command=self.start_demagnetize,
                                width=15, height=2, bg='orange', font=("Arial", 12))
        self.demag_btn.pack()
        
        # 退磁曲线图
        plot_frame = tk.Frame(parent, bg='white')
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.fig, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.ax.set_xlabel('H (A/m)')
        self.ax.set_ylabel('B (mT)')
        self.ax.set_title('退磁曲线')
        self.ax.grid(True)
        self.ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        self.ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        
        if self.demag_data:
            self._update_demag_axes()
            self.canvas_plot.draw()
        else:
            self.ax.set_xlim(-7000, 7000)
            self.ax.set_ylim(-400, 400)
            self.canvas_plot.draw()

    def create_iv_page(self, parent):
        """创建IV关系页面（只创建一次）"""
        # 主框架
        main_frame = tk.Frame(parent, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 按钮框架
        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.pack(pady=8)
        
        buttons = [
            ("计算", self.calculate_iv),
            ("删除选中行", self.delete_iv_selected_row),
            ("导出数据", self.export_iv_data),
            ("导入数据", self.import_iv_data),
            ("清空数据", self.clear_iv_data)
        ]
        
        for text, command in buttons:
            btn = tk.Button(button_frame, text=text, command=command,
                        width=11, bg='lightblue')
            btn.pack(side=tk.LEFT, padx=3)

        # 表格容器（带滚动条）
        table_container = tk.Frame(main_frame, bg='white')
        table_container.pack(pady=5, fill=tk.X)
        
        # 创建画布和滚动条
        self.iv_canvas = tk.Canvas(table_container, height=120, bg='white')
        scrollbar = tk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.iv_canvas.yview)
        self.iv_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.iv_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 在画布中创建表格框架
        self.iv_table_frame = tk.Frame(self.iv_canvas, bg='white')
        self.iv_table_window_id = self.iv_canvas.create_window(
            (0, 0), window=self.iv_table_frame, anchor=tk.NW
        )
        
        def on_iv_canvas_resize(event):
            self.iv_canvas.itemconfig(self.iv_table_window_id, width=event.width)
        self.iv_canvas.bind('<Configure>', on_iv_canvas_resize)
        
        # ===== 提示标签放在表头上面（第0行） =====
        hint_label = tk.Label(self.iv_table_frame, text="💡 点击任意单元格选中该行 | 点击单元格自动获取当前值填入", 
                            font=("Arial", 8), fg='blue', bg='white')
        hint_label.grid(row=0, column=0, columnspan=7, pady=2)
        
        # 创建表格（7列10行）
        headers = ["Ur/mV", "Ih/mA", "U1/mV", "U2/mV", "U3/mV", "U4/mV", "Uh/mV"]
        
        for col, header in enumerate(headers):
            label = tk.Label(self.iv_table_frame, text=header, relief=tk.RIDGE,
                            width=16, bg='lightgray', font=("Arial", 8, "bold"))
            label.grid(row=1, column=col, padx=1, pady=1, sticky='ew')
            self.iv_table_frame.columnconfigure(col, weight=1)
        
        self.iv_selected_row = -1
        
        self.iv_entries = {
            'ur': [], 'ih': [], 'u1': [], 'u2': [], 'u3': [], 'u4': [], 'uh': []
        }
        
        def make_row_selector(row_index):
            def select_row(event):
                self.iv_select_row(row_index)
            return select_row

        # 创建9行数据（行2-10，行0是提示，行1是表头）
        for row in range(2, 11):
            user_row = row - 1  # 用户可见行号：1, 2, 3, ..., 9
            idx = row - 2       # 列表索引：0, 1, 2, ..., 8
            
            entry_ur = tk.Entry(self.iv_table_frame, width=15, justify='center', font=("Arial", 8))
            entry_ur.grid(row=row, column=0, padx=1, pady=1, sticky='ew')
            entry_ur.bind("<Button-1>", lambda e, entry=entry_ur: self.iv_auto_fill_entry(entry))
            entry_ur.bind("<Button-1>", make_row_selector(user_row), add="+")
            self.iv_entries['ur'].append(entry_ur)
            
            entry_ih = tk.Entry(self.iv_table_frame, width=15, justify='center',
                            state='readonly', readonlybackground='white', font=("Arial", 8))
            entry_ih.grid(row=row, column=1, padx=1, pady=1, sticky='ew')
            entry_ih.bind("<Button-1>", make_row_selector(user_row))
            self.iv_entries['ih'].append(entry_ih)
            
            entry_u1 = tk.Entry(self.iv_table_frame, width=15, justify='center', font=("Arial", 8))
            entry_u1.grid(row=row, column=2, padx=1, pady=1, sticky='ew')
            entry_u1.bind("<Button-1>", lambda e, entry=entry_u1: self.iv_auto_fill_entry(entry))
            entry_u1.bind("<Button-1>", make_row_selector(user_row), add="+")
            self.iv_entries['u1'].append(entry_u1)
            
            entry_u2 = tk.Entry(self.iv_table_frame, width=15, justify='center', font=("Arial", 8))
            entry_u2.grid(row=row, column=3, padx=1, pady=1, sticky='ew')
            entry_u2.bind("<Button-1>", lambda e, entry=entry_u2: self.iv_auto_fill_entry(entry))
            entry_u2.bind("<Button-1>", make_row_selector(user_row), add="+")
            self.iv_entries['u2'].append(entry_u2)
            
            entry_u3 = tk.Entry(self.iv_table_frame, width=15, justify='center', font=("Arial", 8))
            entry_u3.grid(row=row, column=4, padx=1, pady=1, sticky='ew')
            entry_u3.bind("<Button-1>", lambda e, entry=entry_u3: self.iv_auto_fill_entry(entry))
            entry_u3.bind("<Button-1>", make_row_selector(user_row), add="+")
            self.iv_entries['u3'].append(entry_u3)
            
            entry_u4 = tk.Entry(self.iv_table_frame, width=15, justify='center', font=("Arial", 8))
            entry_u4.grid(row=row, column=5, padx=1, pady=1, sticky='ew')
            entry_u4.bind("<Button-1>", lambda e, entry=entry_u4: self.iv_auto_fill_entry(entry))
            entry_u4.bind("<Button-1>", make_row_selector(user_row), add="+")
            self.iv_entries['u4'].append(entry_u4)
            
            entry_uh = tk.Entry(self.iv_table_frame, width=15, justify='center',
                            state='readonly', readonlybackground='white', font=("Arial", 8))
            entry_uh.grid(row=row, column=6, padx=1, pady=1, sticky='ew')
            entry_uh.bind("<Button-1>", make_row_selector(user_row))
            self.iv_entries['uh'].append(entry_uh)
        
        self.iv_table_frame.update_idletasks()
        self.iv_canvas.configure(scrollregion=self.iv_canvas.bbox("all"))
        
        # ===== 在表格和曲线图之间添加参数显示 =====
        param_frame = tk.Frame(main_frame, bg='white')
        param_frame.pack(pady=5, fill=tk.X)
        
        # 励磁电流显示
        tk.Label(param_frame, text="励磁电流 I =", font=("Arial", 9), bg='white').pack(side=tk.LEFT, padx=5)
        self.iv_I_label = tk.Label(param_frame, text="0", font=("Arial", 9, "bold"), fg='blue', bg='white')
        self.iv_I_label.pack(side=tk.LEFT)
        tk.Label(param_frame, text="mA", font=("Arial", 9), bg='white').pack(side=tk.LEFT)
        
        # 分隔符
        tk.Label(param_frame, text="  |  ", font=("Arial", 9), bg='white').pack(side=tk.LEFT)
        
        # 毫特计值显示
        tk.Label(param_frame, text="磁感应强度 B =", font=("Arial", 9), bg='white').pack(side=tk.LEFT, padx=5)
        self.iv_B_label = tk.Label(param_frame, text="0", font=("Arial", 9, "bold"), fg='red', bg='white')
        self.iv_B_label.pack(side=tk.LEFT)
        tk.Label(param_frame, text="mT", font=("Arial", 9), bg='white').pack(side=tk.LEFT)

        # 曲线图
        plot_frame = tk.Frame(main_frame, bg='white')
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=2)
        
        self.iv_fig, self.iv_ax = plt.subplots(figsize=(5, 2))
        self.iv_fig.subplots_adjust(bottom=0.2, left=0.1, right=0.95, top=0.88)
        self.iv_canvas_plot = FigureCanvasTkAgg(self.iv_fig, master=plot_frame)
        self.iv_canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.iv_ax.set_xlabel('Ih (mA)', fontsize=9)
        self.iv_ax.set_ylabel('Uh (mV)', fontsize=9)
        self.iv_ax.set_title('霍尔电流与霍尔电压关系', fontsize=10)
        self.iv_ax.grid(True)
        
        

    def on_demagnetize_select(self):
        """选择退磁选项卡"""
        if hasattr(self, 'btn_demag'):
            self.btn_demag.config(bg='lightblue')
        if hasattr(self, 'btn_iv'):
            self.btn_iv.config(bg='SystemButtonFace')
        if hasattr(self, 'btn_sensitivity'):
            self.btn_sensitivity.config(bg='SystemButtonFace')
        
        self.show_page("demagnetize")
        self.current_display = "demagnetize"
    
    def _update_demag_axes(self):
        """更新退磁曲线坐标轴和内容（与绘制时保持一致）"""
        if not hasattr(self, 'ax') or self.ax is None or not self.demag_data:
            return
        
        self.ax.clear()
        self.ax.set_xlabel('H (A/m)')
        self.ax.set_ylabel('B (mT)')
        self.ax.set_title('退磁曲线')
        self.ax.grid(True)
        
        h_data = [d[0] * 10 for d in self.demag_data]
        b_data = [d[1] for d in self.demag_data]
        
        # 自适应显示范围（与绘制时完全一致）
        if h_data:
            h_min, h_max = min(h_data), max(h_data)
            b_min, b_max = min(b_data), max(b_data)
            h_range = h_max - h_min
            b_range = b_max - b_min
            h_margin = max(500, h_range * 0.15) if h_range > 0 else 500
            b_margin = max(20, b_range * 0.15) if b_range > 0 else 20
            # 确保包含原点
            h_min = min(h_min, 0) - h_margin
            h_max = max(h_max, 0) + h_margin
            b_min = min(b_min, 0) - b_margin
            b_max = max(b_max, 0) + b_margin
            self.ax.set_xlim(h_min, h_max)
            self.ax.set_ylim(b_min, b_max)
        else:
            self.ax.set_xlim(-7000, 7000)
            self.ax.set_ylim(-400, 400)
        
        self.ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        self.ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        
        # 绘制退磁曲线
        if h_data:
            self.ax.plot(h_data, b_data, 'b-', linewidth=1.5, alpha=0.8)
            
            # 标记起点（绿色）
            self.ax.scatter(h_data[0], b_data[0], color='green', s=40, label='起点')
            
            # 标记当前点（红色）
            self.ax.scatter(h_data[-1], b_data[-1], color='red', s=30, label='当前点')
            
            # 标记原点（灰色十字）
            self.ax.scatter(0, 0, color='gray', marker='+', s=100, linewidths=2)
            
            self.ax.legend(loc='upper right', fontsize=8)

    def on_iv_relation_select(self):
        """选择IV关系选项卡"""
        if not self.demagnetize_complete:
            messagebox.showwarning("警告", "请先完成退磁和调零操作！")
            return
        
        if hasattr(self, 'btn_iv'):
            self.btn_iv.config(bg='lightblue')
        if hasattr(self, 'btn_demag'):
            self.btn_demag.config(bg='SystemButtonFace')
        if hasattr(self, 'btn_sensitivity'):
            self.btn_sensitivity.config(bg='SystemButtonFace')
        
        self.show_page("iv_relation")
        self.current_display = "iv_relation"
    
    def iv_auto_fill_entry(self, entry_widget):
        """IV关系界面：点击单元格自动获取当前电压值填入指定的entry"""
        try:
            # 获取当前电压值（含调零偏移）
            voltage_str = self.voltage_var.get()
            voltage = float(voltage_str)
            
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, f"{voltage:.1f}")
        except ValueError:
            messagebox.showwarning("警告", "无法获取当前电压值！")

    def iv_select_row(self, row_index):
        """选中IV表格的指定行（行号从1开始）"""
        idx = row_index - 1  # 用户可见行号转列表索引
        
        # 清除之前的高亮
        if self.iv_selected_row >= 0:
            old_idx = self.iv_selected_row - 1
            if 0 <= old_idx < len(self.iv_entries['ur']):
                for key in ['ur', 'ih', 'u1', 'u2', 'u3', 'u4', 'uh']:
                    try:
                        self.iv_entries[key][old_idx].config(bg='white')
                    except:
                        pass
        
        # 高亮新选中的行
        if 0 <= idx < len(self.iv_entries['ur']):
            self.iv_selected_row = row_index  # 存储用户可见行号
            for key in ['ur', 'ih', 'u1', 'u2', 'u3', 'u4', 'uh']:
                try:
                    self.iv_entries[key][idx].config(bg='lightblue')
                except:
                    pass

    def delete_iv_selected_row(self):
        """删除IV表格选中的行"""
        if self.iv_selected_row < 0:
            messagebox.showwarning("警告", "请先点击任意单元格选中要删除的行！")
            return
        
        idx = self.iv_selected_row - 1
        
        # 检查该行是否有数据（检查可编辑列）
        has_data = False
        for key in ['ur', 'u1', 'u2', 'u3', 'u4']:
            if self.iv_entries[key][idx].get().strip():
                has_data = True
                break
        
        if not has_data:
            messagebox.showwarning("警告", f"第{self.iv_selected_row}行没有数据！")
            return
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除第{self.iv_selected_row}行的数据吗？"):
            return
        
        # 清空所有列的数据
        for key in ['ur', 'u1', 'u2', 'u3', 'u4']:
            self.iv_entries[key][idx].delete(0, tk.END)
        
        # 清空只读列
        for key in ['ih', 'uh']:
            self.iv_entries[key][idx].config(state='normal')
            self.iv_entries[key][idx].delete(0, tk.END)
            self.iv_entries[key][idx].config(state='readonly')
        
        # 清除高亮
        for key in ['ur', 'ih', 'u1', 'u2', 'u3', 'u4', 'uh']:
            self.iv_entries[key][idx].config(bg='white')
        
        self.iv_selected_row = -1
        
        # 重新计算并更新曲线
        self.calculate_iv()
        messagebox.showinfo("删除成功", f"已删除第{idx+1}行数据")

    def save_iv_data_from_table(self):
        """从表格读取数据保存到 iv_saved_data"""
        if not hasattr(self, 'iv_entries') or not self.iv_entries:
            return
        
        try:
            # ===== 检查表格是否有数据 =====
            has_data = False
            for i in range(9):
                ur = self.iv_entries['ur'][i].get().strip()
                u1 = self.iv_entries['u1'][i].get().strip()
                u2 = self.iv_entries['u2'][i].get().strip()
                u3 = self.iv_entries['u3'][i].get().strip()
                u4 = self.iv_entries['u4'][i].get().strip()
                if ur or u1 or u2 or u3 or u4:
                    has_data = True
                    break
            
            # 如果没有数据，保留原有保存的数据（不覆盖）
            if not has_data and hasattr(self, 'iv_saved_data'):
                # 但参数可能变化了，更新参数（确保是数值类型）
                if hasattr(self, 'iv_current_I'):
                    val = self.iv_current_I
                    if isinstance(val, (int, float)):
                        self.iv_saved_data['excitation_I'] = val
                    elif isinstance(val, list) and val:
                        self.iv_saved_data['excitation_I'] = val[0] if isinstance(val[0], (int, float)) else 0
                    else:
                        self.iv_saved_data['excitation_I'] = 0
                if hasattr(self, 'iv_current_B'):
                    val = self.iv_current_B
                    if isinstance(val, (int, float)):
                        self.iv_saved_data['magnetic_B'] = val
                    elif isinstance(val, list) and val:
                        self.iv_saved_data['magnetic_B'] = val[0] if isinstance(val[0], (int, float)) else 0
                    else:
                        self.iv_saved_data['magnetic_B'] = 0
                return
            
            # 初始化保存字典
            if not hasattr(self, 'iv_saved_data'):
                self.iv_saved_data = {
                    'ur': [], 'ih': [], 'u1': [], 'u2': [], 'u3': [], 'u4': [], 'uh': [],
                    'ih_values': [], 'uh_values': [],
                    'excitation_I': 0, 'magnetic_B': 0
                }

            # 保存参数（确保是数值类型）
            if hasattr(self, 'iv_current_I'):
                val = self.iv_current_I
                if isinstance(val, (int, float)):
                    self.iv_saved_data['excitation_I'] = val
                else:
                    self.iv_saved_data['excitation_I'] = 0
            else:
                self.iv_saved_data['excitation_I'] = 0
                
            if hasattr(self, 'iv_current_B'):
                val = self.iv_current_B
                if isinstance(val, (int, float)):
                    self.iv_saved_data['magnetic_B'] = val
                else:
                    self.iv_saved_data['magnetic_B'] = 0
            else:
                self.iv_saved_data['magnetic_B'] = 0

            # 清空旧数据
            for key in self.iv_saved_data:
                if key not in ['excitation_I', 'magnetic_B']:
                    self.iv_saved_data[key] = []
            
            # 从表格读取数据
            for i in range(9):
                self.iv_saved_data['ur'].append(self.iv_entries['ur'][i].get().strip())
                self.iv_saved_data['ih'].append(self.iv_entries['ih'][i].get().strip())
                self.iv_saved_data['u1'].append(self.iv_entries['u1'][i].get().strip())
                self.iv_saved_data['u2'].append(self.iv_entries['u2'][i].get().strip())
                self.iv_saved_data['u3'].append(self.iv_entries['u3'][i].get().strip())
                self.iv_saved_data['u4'].append(self.iv_entries['u4'][i].get().strip())
                self.iv_saved_data['uh'].append(self.iv_entries['uh'][i].get().strip())
            
            # 重新计算曲线数据
            ih_values = []
            uh_values = []
            for i in range(9):
                ur_str = self.iv_saved_data['ur'][i]
                u1_str = self.iv_saved_data['u1'][i]
                u2_str = self.iv_saved_data['u2'][i]
                u3_str = self.iv_saved_data['u3'][i]
                u4_str = self.iv_saved_data['u4'][i]
                
                if ur_str or u1_str or u2_str or u3_str or u4_str:
                    try:
                        ur = float(ur_str) if ur_str else 0
                        u1 = float(u1_str) if u1_str else 0
                        u2 = float(u2_str) if u2_str else 0
                        u3 = float(u3_str) if u3_str else 0
                        u4 = float(u4_str) if u4_str else 0
                        
                        ih = -ur / 100 if ur != 0 else 0
                        uh = (u1 + u3 - u2 - u4) / 4
                        
                        ih_values.append(ih)
                        uh_values.append(uh)
                    except ValueError:
                        pass
            
            self.iv_saved_data['ih_values'] = ih_values
            self.iv_saved_data['uh_values'] = uh_values
            
        except Exception as e:
            print(f"保存IV数据失败: {e}")

    def calculate_iv(self,use_saved_params=False):
        """计算IV关系数据"""
        try:
            # ===== 记录当前励磁电流和毫特计值 =====
            if use_saved_params and hasattr(self, 'iv_imported_I') and hasattr(self, 'iv_imported_B'):
                # 使用导入时保存的参数
                current_I = self.iv_imported_I
                current_B = self.iv_imported_B
            else:
                # 从界面获取当前值
                current_I = self.excitation_current
                try:
                    current_B = float(self.millitesla_var.get())
                except ValueError:
                    current_B = 0.0
            
            # 更新显示标签
            if hasattr(self, 'iv_I_label'):
                self.iv_I_label.config(text=f"{current_I:.0f}")
            if hasattr(self, 'iv_B_label'):
                self.iv_B_label.config(text=f"{current_B:.1f}")
            
            # 保存参数到数据字典
            self.iv_current_I = current_I
            self.iv_current_B = current_B

            # 获取所有数据并计算
            ih_values = []
            uh_values = []
            
            # 保存原始数据
            self.iv_saved_data = {
                'ur': [],
                'ih': [],
                'u1': [],
                'u2': [],
                'u3': [],
                'u4': [],
                'uh': [],
                'ih_values': [],
                'uh_values': []
            }
            
            for i in range(9):
                ur_str = self.iv_entries['ur'][i].get().strip()
                u1_str = self.iv_entries['u1'][i].get().strip()
                u2_str = self.iv_entries['u2'][i].get().strip()
                u3_str = self.iv_entries['u3'][i].get().strip()
                u4_str = self.iv_entries['u4'][i].get().strip()
                
                # 保存原始数据
                self.iv_saved_data['ur'].append(ur_str)
                self.iv_saved_data['u1'].append(u1_str)
                self.iv_saved_data['u2'].append(u2_str)
                self.iv_saved_data['u3'].append(u3_str)
                self.iv_saved_data['u4'].append(u4_str)
                
                if ur_str or u1_str or u2_str or u3_str or u4_str:
                    ur = float(ur_str) if ur_str else 0
                    u1 = float(u1_str) if u1_str else 0
                    u2 = float(u2_str) if u2_str else 0
                    u3 = float(u3_str) if u3_str else 0
                    u4 = float(u4_str) if u4_str else 0
                    
                    ih = -ur / 100 if ur != 0 else 0
                    uh = (u1 + u3 - u2 - u4) / 4
                    
                    ih_values.append(ih)
                    uh_values.append(uh)
                    
                    # Ih
                    self.iv_entries['ih'][i].config(state='normal')
                    self.iv_entries['ih'][i].delete(0, tk.END)
                    self.iv_entries['ih'][i].insert(0, f"{ih:.3f}")
                    self.iv_entries['ih'][i].config(state='readonly')
                    self.iv_saved_data['ih'].append(f"{ih:.3f}")
                    
                    # Uh
                    self.iv_entries['uh'][i].config(state='normal')
                    self.iv_entries['uh'][i].delete(0, tk.END)
                    self.iv_entries['uh'][i].insert(0, f"{uh:.3f}")
                    self.iv_entries['uh'][i].config(state='readonly')
                    self.iv_saved_data['uh'].append(f"{uh:.3f}")
                else:
                    self.iv_entries['ih'][i].config(state='normal')
                    self.iv_entries['ih'][i].delete(0, tk.END)
                    self.iv_entries['ih'][i].config(state='readonly')
                    self.iv_saved_data['ih'].append("")
                    
                    self.iv_entries['uh'][i].config(state='normal')
                    self.iv_entries['uh'][i].delete(0, tk.END)
                    self.iv_entries['uh'][i].config(state='readonly')
                    self.iv_saved_data['uh'].append("")
            
            # 保存曲线数据
            self.iv_saved_data['ih_values'] = ih_values
            self.iv_saved_data['uh_values'] = uh_values

            # 在保存数据时也保存这两个参数
            self.iv_saved_data['excitation_I'] = current_I
            self.iv_saved_data['magnetic_B'] = current_B
            
            # 更新曲线图
            self.update_iv_plot(ih_values, uh_values)
            
            # ===== 计算完成后保存数据 =====
            self.save_iv_data_from_table()
            
            messagebox.showinfo("计算完成", "IV关系计算完成！")
        except ValueError as e:
            messagebox.showerror("错误", f"输入数据格式错误：{e}")
        except Exception as e:
            messagebox.showerror("错误", f"计算失败：{e}")

    def update_iv_plot(self, ih_values, uh_values):
        """更新IV关系曲线图"""
        if not hasattr(self, 'iv_ax') or self.iv_ax is None:
            return
        
        self.iv_ax.clear()
        
        # 过滤有效数据（Ih和Uh都不为0，且Ih有值）
        filtered_data = []
        for ih, uh in zip(ih_values, uh_values):
            if ih != 0 and uh != 0:
                filtered_data.append((ih, uh))
        
        if filtered_data:
            ih_valid = [d[0] for d in filtered_data]
            uh_valid = [d[1] for d in filtered_data]
            
            # 绘制散点图
            self.iv_ax.scatter(ih_valid, uh_valid, color='blue', s=50, label='实验数据')
            
            # 线性拟合
            if len(ih_valid) >= 2:
                coeffs = np.polyfit(ih_valid, uh_valid, 1)
                slope = coeffs[0]
                intercept = coeffs[1]
                
                # 绘制拟合直线
                x_line = np.array([min(ih_valid), max(ih_valid)])
                y_line = slope * x_line + intercept
                self.iv_ax.plot(x_line, y_line, 'r-', label=f'拟合: Uh={slope:.4f}*Ih+{intercept:.4f}')
                
                # 显示公式
                formula_text = f'Uh = {slope:.4f} * Ih + {intercept:.4f}'
                self.iv_ax.text(0.05, 0.95, formula_text, transform=self.iv_ax.transAxes,
                            fontsize=10, verticalalignment='top',
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                self.iv_ax.legend()
        
        self.iv_ax.set_xlabel('Ih (mA)')
        self.iv_ax.set_ylabel('Uh (mV)')
        self.iv_ax.set_title('霍尔电流与霍尔电压关系')
        self.iv_ax.grid(True)
        
        # ===== 增大边距，确保边缘点可见 =====
        if filtered_data:
            ih_values_list = [d[0] for d in filtered_data]
            uh_values_list = [d[1] for d in filtered_data]
            ih_min, ih_max = min(ih_values_list), max(ih_values_list)
            uh_min, uh_max = min(uh_values_list), max(uh_values_list)
            
            # 计算范围
            ih_range = ih_max - ih_min
            uh_range = uh_max - uh_min
            
            # 边距：至少保留20%的边距，且不小于0.5
            ih_margin = max(0.5, ih_range * 0.25) if ih_range > 0 else 1.0
            uh_margin = max(0.5, uh_range * 0.25) if uh_range > 0 else 1.0
            
            # 确保包含0点（如果数据接近0）
            ih_min = min(ih_min, 0) - ih_margin
            ih_max = max(ih_max, 0) + ih_margin
            uh_min = min(uh_min, 0) - uh_margin
            uh_max = max(uh_max, 0) + uh_margin
            
            # 反转y轴，使纵轴从0开始向上减小
            self.iv_ax.set_xlim(ih_min, ih_max)
            self.iv_ax.set_ylim(uh_max, uh_min)  # 从正到负
        else:
            # 无数据时显示默认范围
            self.iv_ax.set_ylim(1, -1)
        
        if hasattr(self, 'iv_canvas_plot') and self.iv_canvas_plot:
            self.iv_canvas_plot.draw()

    def export_iv_data(self):
        """导出IV数据到CSV"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    # ===== 写入实验参数 =====
                    f.write("=== 实验参数 ===\n")
                    if hasattr(self, 'iv_current_I'):
                        f.write(f"励磁电流 I,{self.iv_current_I:.0f},mA\n")
                    if hasattr(self, 'iv_current_B'):
                        f.write(f"磁感应强度 B,{self.iv_current_B:.1f},mT\n")
                    f.write("\n")
                    
                    # 写入数据表头
                    f.write("Ur(mV),Ih(mA),U1(mV),U2(mV),U3(mV),U4(mV),Uh(mV)\n")
                    for i in range(9):
                        ur = self.iv_entries['ur'][i].get().strip()
                        ih = self.iv_entries['ih'][i].get().strip()
                        u1 = self.iv_entries['u1'][i].get().strip()
                        u2 = self.iv_entries['u2'][i].get().strip()
                        u3 = self.iv_entries['u3'][i].get().strip()
                        u4 = self.iv_entries['u4'][i].get().strip()
                        uh = self.iv_entries['uh'][i].get().strip()
                        if ur or u1 or u2 or u3 or u4:
                            f.write(f"{ur},{ih},{u1},{u2},{u3},{u4},{uh}\n")
                messagebox.showinfo("导出成功", f"数据已导出到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出数据时出错:\n{str(e)}")

    def import_iv_data(self):
        """导入IV数据从CSV"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                
                # 解析实验参数
                excitation_I = None
                magnetic_B = None
                
                # 找到数据起始行
                data_start = 0
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    if line_stripped:
                        # 检查是否是实验参数行
                        if '励磁电流 I' in line_stripped:
                            parts = line_stripped.split(',')
                            if len(parts) >= 2:
                                try:
                                    excitation_I = float(parts[1].strip())
                                except:
                                    pass
                        elif '磁感应强度 B' in line_stripped:
                            parts = line_stripped.split(',')
                            if len(parts) >= 2:
                                try:
                                    magnetic_B = float(parts[1].strip())
                                except:
                                    pass
                        # 检查是否包含表头关键字
                        elif 'Ur' in line_stripped and 'Ih' in line_stripped and 'U1' in line_stripped:
                            data_start = i + 1
                            break
                
                # 如果没有找到标准表头，尝试跳过第一行
                if data_start == 0:
                    first_line = lines[0].strip().split(',') if lines else []
                    is_all_numbers = True
                    for part in first_line:
                        try:
                            float(part.strip())
                        except ValueError:
                            is_all_numbers = False
                            break
                    if not is_all_numbers and len(lines) > 1:
                        data_start = 1
                
                # ===== 保存导入的参数（供 calculate_iv 使用） =====
                self.iv_imported_I = excitation_I if excitation_I is not None else 0
                self.iv_imported_B = magnetic_B if magnetic_B is not None else 0
                
                # 读取数据行
                data_lines = []
                for line in lines[data_start:]:
                    line_stripped = line.strip()
                    if line_stripped:
                        if '===' in line_stripped:
                            continue
                        data_lines.append(line_stripped)
                
                # 先清空所有数据行
                for i in range(9):
                    self.iv_entries['ur'][i].delete(0, tk.END)
                    self.iv_entries['u1'][i].delete(0, tk.END)
                    self.iv_entries['u2'][i].delete(0, tk.END)
                    self.iv_entries['u3'][i].delete(0, tk.END)
                    self.iv_entries['u4'][i].delete(0, tk.END)
                    self.iv_entries['ih'][i].config(state='normal')
                    self.iv_entries['ih'][i].delete(0, tk.END)
                    self.iv_entries['ih'][i].config(state='readonly')
                    self.iv_entries['uh'][i].config(state='normal')
                    self.iv_entries['uh'][i].delete(0, tk.END)
                    self.iv_entries['uh'][i].config(state='readonly')
                
                # 填充数据
                for i, line in enumerate(data_lines[:9]):
                    parts = line.strip().split(',')
                    if len(parts) >= 7:
                        try:
                            float(parts[0].strip())
                            float(parts[1].strip())
                        except ValueError:
                            continue
                        
                        self.iv_entries['ur'][i].delete(0, tk.END)
                        self.iv_entries['ur'][i].insert(0, parts[0].strip())
                        
                        self.iv_entries['ih'][i].config(state='normal')
                        self.iv_entries['ih'][i].delete(0, tk.END)
                        self.iv_entries['ih'][i].insert(0, parts[1].strip())
                        self.iv_entries['ih'][i].config(state='readonly')
                        
                        self.iv_entries['u1'][i].delete(0, tk.END)
                        self.iv_entries['u1'][i].insert(0, parts[2].strip())
                        self.iv_entries['u2'][i].delete(0, tk.END)
                        self.iv_entries['u2'][i].insert(0, parts[3].strip())
                        self.iv_entries['u3'][i].delete(0, tk.END)
                        self.iv_entries['u3'][i].insert(0, parts[4].strip())
                        self.iv_entries['u4'][i].delete(0, tk.END)
                        self.iv_entries['u4'][i].insert(0, parts[5].strip())
                        
                        self.iv_entries['uh'][i].config(state='normal')
                        self.iv_entries['uh'][i].delete(0, tk.END)
                        self.iv_entries['uh'][i].insert(0, parts[6].strip())
                        self.iv_entries['uh'][i].config(state='readonly')
                
                # ===== 使用导入的参数重新计算 =====
                self.calculate_iv(use_saved_params=True)
                
                # 清除导入参数标记，避免影响后续操作
                self.iv_imported_I = None
                self.iv_imported_B = None
                
                messagebox.showinfo("导入成功", "数据导入完成！")
            except Exception as e:
                messagebox.showerror("导入失败", f"导入数据时出错:\n{str(e)}")

    def clear_iv_data(self):
        """清空IV数据"""
        if not messagebox.askyesno("确认清空", "确定要清空所有IV数据吗？"):
            return
        
        for i in range(9):
            self.iv_entries['ur'][i].delete(0, tk.END)
            self.iv_entries['u1'][i].delete(0, tk.END)
            self.iv_entries['u2'][i].delete(0, tk.END)
            self.iv_entries['u3'][i].delete(0, tk.END)
            self.iv_entries['u4'][i].delete(0, tk.END)
            
            self.iv_entries['ih'][i].config(state='normal')
            self.iv_entries['ih'][i].delete(0, tk.END)
            self.iv_entries['ih'][i].config(state='readonly')
            
            self.iv_entries['uh'][i].config(state='normal')
            self.iv_entries['uh'][i].delete(0, tk.END)
            self.iv_entries['uh'][i].config(state='readonly')
        
        # ===== 清空参数显示 =====
        if hasattr(self, 'iv_I_label'):
            self.iv_I_label.config(text="0")
        if hasattr(self, 'iv_B_label'):
            self.iv_B_label.config(text="0")
        
        # 清除保存的参数
        self.iv_current_I = 0
        self.iv_current_B = 0

        # 清空曲线图
        if hasattr(self, 'iv_ax') and self.iv_ax is not None:
            self.iv_ax.clear()
            self.iv_ax.set_xlabel('Ih (mA)')
            self.iv_ax.set_ylabel('Uh (mV)')
            self.iv_ax.set_title('霍尔电流与霍尔电压关系')
            self.iv_ax.grid(True)
            if hasattr(self, 'iv_canvas_plot') and self.iv_canvas_plot:
                self.iv_canvas_plot.draw()
        
        # ===== 保存空数据 =====
        self.save_iv_data_from_table()
        
        messagebox.showinfo("清空数据", "数据已清空！")

    def on_sensitivity_select(self):
        """选择灵敏度选项卡"""
        if not self.demagnetize_complete:
            messagebox.showwarning("警告", "请先完成退磁和调零操作！")
            return
        
        if hasattr(self, 'btn_sensitivity'):
            self.btn_sensitivity.config(bg='lightblue')
        if hasattr(self, 'btn_demag'):
            self.btn_demag.config(bg='SystemButtonFace')
        if hasattr(self, 'btn_iv'):
            self.btn_iv.config(bg='SystemButtonFace')
        
        self.show_page("sensitivity")
        self.current_display = "sensitivity"

    def save_sensitivity_data_from_table(self):
        """从表格读取数据保存到 sens_saved_data"""
        if not hasattr(self, 'sens_entries') or not self.sens_entries:
            return
        
        try:
            # ===== 检查表格是否有数据 =====
            has_data = False
            for i in range(11):
                b = self.sens_entries['b'][i].get().strip()
                u1 = self.sens_entries['u1'][i].get().strip()
                if b or u1:
                    has_data = True
                    break
            
            # 如果没有数据，保留原有保存的数据（不覆盖）
            if not has_data and hasattr(self, 'sens_saved_data'):
                # 但参数可能变化了，更新参数（确保是数值类型）
                if hasattr(self, 'sens_current_Ih'):
                    val = self.sens_current_Ih
                    if isinstance(val, (int, float)):
                        self.sens_saved_data['constant_Ih'] = val
                    elif isinstance(val, list) and val:
                        self.sens_saved_data['constant_Ih'] = val[0] if isinstance(val[0], (int, float)) else 0
                    else:
                        self.sens_saved_data['constant_Ih'] = 0
                return
            
            if not hasattr(self, 'sens_saved_data'):
                self.sens_saved_data = {
                    'b': [], 'u1': [], 'u2': [], 'u3': [], 'u4': [], 'uh': [],
                    'b_values': [], 'uh_values': [],
                    'constant_Ih': 0
                }
        
            # 保存参数（确保是数值类型）
            if hasattr(self, 'sens_current_Ih'):
                val = self.sens_current_Ih
                if isinstance(val, (int, float)):
                    self.sens_saved_data['constant_Ih'] = val
                else:
                    self.sens_saved_data['constant_Ih'] = 0
            else:
                self.sens_saved_data['constant_Ih'] = 0
            
            # 清空旧数据（保留参数）
            for key in self.sens_saved_data:
                if key != 'constant_Ih':
                    self.sens_saved_data[key] = []
            
            for i in range(11):
                self.sens_saved_data['b'].append(self.sens_entries['b'][i].get().strip())
                self.sens_saved_data['u1'].append(self.sens_entries['u1'][i].get().strip())
                self.sens_saved_data['u2'].append(self.sens_entries['u2'][i].get().strip())
                self.sens_saved_data['u3'].append(self.sens_entries['u3'][i].get().strip())
                self.sens_saved_data['u4'].append(self.sens_entries['u4'][i].get().strip())
                self.sens_saved_data['uh'].append(self.sens_entries['uh'][i].get().strip())
            
            # 重新计算曲线数据
            b_values = []
            uh_values = []
            for i in range(11):
                b_str = self.sens_saved_data['b'][i]
                u1_str = self.sens_saved_data['u1'][i]
                u2_str = self.sens_saved_data['u2'][i]
                u3_str = self.sens_saved_data['u3'][i]
                u4_str = self.sens_saved_data['u4'][i]
                
                if b_str and (u1_str or u2_str or u3_str or u4_str):
                    try:
                        b = float(b_str) if b_str else 0
                        u1 = float(u1_str) if u1_str else 0
                        u2 = float(u2_str) if u2_str else 0
                        u3 = float(u3_str) if u3_str else 0
                        u4 = float(u4_str) if u4_str else 0
                        
                        uh = (u1 + u3 - u2 - u4) / 4
                        
                        b_values.append(b)
                        uh_values.append(uh)
                    except ValueError:
                        pass
            
            self.sens_saved_data['b_values'] = b_values
            self.sens_saved_data['uh_values'] = uh_values
            
        except Exception as e:
            print(f"保存灵敏度数据失败: {e}")

    def restore_iv_data(self):
        """恢复IV数据到表格和曲线"""
        if not hasattr(self, 'iv_saved_data') or not self.iv_saved_data:
            return
        
        try:
            # ===== 恢复参数显示 =====
            if hasattr(self, 'iv_I_label') and 'excitation_I' in self.iv_saved_data:
                try:
                    val = self.iv_saved_data['excitation_I']
                    if isinstance(val, (int, float)):
                        self.iv_I_label.config(text=f"{val:.0f}")
                        self.iv_current_I = val
                    else:
                        self.iv_I_label.config(text=str(val))
                        try:
                            self.iv_current_I = float(val)
                        except:
                            self.iv_current_I = 0
                except Exception:
                    self.iv_I_label.config(text="0")
                    self.iv_current_I = 0
                        
            if hasattr(self, 'iv_B_label') and 'magnetic_B' in self.iv_saved_data:
                try:
                    val = self.iv_saved_data['magnetic_B']
                    if isinstance(val, (int, float)):
                        self.iv_B_label.config(text=f"{val:.1f}")
                        self.iv_current_B = val
                    else:
                        self.iv_B_label.config(text=str(val))
                        try:
                            self.iv_current_B = float(val)
                        except:
                            self.iv_current_B = 0
                except Exception:
                    self.iv_B_label.config(text="0")
                    self.iv_current_B = 0
            
            # 检查是否有数据
            has_data = False
            for key in ['ur', 'u1', 'u2', 'u3', 'u4']:
                if self.iv_saved_data.get(key) and any(v for v in self.iv_saved_data[key] if v):
                    has_data = True
                    break
            
            if not has_data:
                # 没有数据时，清空表格
                for i in range(9):
                    self.iv_entries['ur'][i].delete(0, tk.END)
                    self.iv_entries['u1'][i].delete(0, tk.END)
                    self.iv_entries['u2'][i].delete(0, tk.END)
                    self.iv_entries['u3'][i].delete(0, tk.END)
                    self.iv_entries['u4'][i].delete(0, tk.END)
                    self.iv_entries['ih'][i].config(state='normal')
                    self.iv_entries['ih'][i].delete(0, tk.END)
                    self.iv_entries['ih'][i].config(state='readonly')
                    self.iv_entries['uh'][i].config(state='normal')
                    self.iv_entries['uh'][i].delete(0, tk.END)
                    self.iv_entries['uh'][i].config(state='readonly')
                # ===== 保存空数据 =====
                self.save_iv_data_from_table()
                return
            
            # 恢复表格数据
            for i in range(9):
                # Ur
                if i < len(self.iv_saved_data.get('ur', [])):
                    self.iv_entries['ur'][i].delete(0, tk.END)
                    self.iv_entries['ur'][i].insert(0, self.iv_saved_data['ur'][i])
                
                # Ih
                if i < len(self.iv_saved_data.get('ih', [])):
                    self.iv_entries['ih'][i].config(state='normal')
                    self.iv_entries['ih'][i].delete(0, tk.END)
                    self.iv_entries['ih'][i].insert(0, self.iv_saved_data['ih'][i])
                    self.iv_entries['ih'][i].config(state='readonly')
                
                # U1
                if i < len(self.iv_saved_data.get('u1', [])):
                    self.iv_entries['u1'][i].delete(0, tk.END)
                    self.iv_entries['u1'][i].insert(0, self.iv_saved_data['u1'][i])
                
                # U2
                if i < len(self.iv_saved_data.get('u2', [])):
                    self.iv_entries['u2'][i].delete(0, tk.END)
                    self.iv_entries['u2'][i].insert(0, self.iv_saved_data['u2'][i])
                
                # U3
                if i < len(self.iv_saved_data.get('u3', [])):
                    self.iv_entries['u3'][i].delete(0, tk.END)
                    self.iv_entries['u3'][i].insert(0, self.iv_saved_data['u3'][i])
                
                # U4
                if i < len(self.iv_saved_data.get('u4', [])):
                    self.iv_entries['u4'][i].delete(0, tk.END)
                    self.iv_entries['u4'][i].insert(0, self.iv_saved_data['u4'][i])
                
                # Uh
                if i < len(self.iv_saved_data.get('uh', [])):
                    self.iv_entries['uh'][i].config(state='normal')
                    self.iv_entries['uh'][i].delete(0, tk.END)
                    self.iv_entries['uh'][i].insert(0, self.iv_saved_data['uh'][i])
                    self.iv_entries['uh'][i].config(state='readonly')
            
            # 恢复曲线
            if self.iv_saved_data.get('ih_values') and self.iv_saved_data.get('uh_values'):
                self.update_iv_plot(self.iv_saved_data['ih_values'], self.iv_saved_data['uh_values'])
            
            # ===== 关键：恢复后重新保存，确保数据持久化 =====
            self.save_iv_data_from_table()
            
        except Exception as e:
            print(f"恢复IV数据失败: {e}")
            
    def restore_sensitivity_data(self):
        """恢复灵敏度数据到表格和曲线"""
        if not hasattr(self, 'sens_saved_data') or not self.sens_saved_data:
            return
        
        try:
            # ===== 恢复参数显示 =====
            if hasattr(self, 'sens_Ih_label') and 'constant_Ih' in self.sens_saved_data:
                try:
                    val = self.sens_saved_data['constant_Ih']
                    if isinstance(val, (int, float)):
                        self.sens_Ih_label.config(text=f"{val:.3f}")
                        self.sens_current_Ih = val
                    else:
                        self.sens_Ih_label.config(text=str(val))
                        try:
                            self.sens_current_Ih = float(val)
                        except:
                            self.sens_current_Ih = 0
                except Exception:
                    self.sens_Ih_label.config(text="0")
                    self.sens_current_Ih = 0
            
            # 检查是否有数据
            has_data = False
            for key in ['b', 'u1', 'u2', 'u3', 'u4']:
                if self.sens_saved_data.get(key) and any(v for v in self.sens_saved_data[key] if v):
                    has_data = True
                    break
            
            if not has_data:
                # 没有数据时清空表格
                for i in range(11):
                    self.sens_entries['b'][i].delete(0, tk.END)
                    self.sens_entries['u1'][i].delete(0, tk.END)
                    self.sens_entries['u2'][i].delete(0, tk.END)
                    self.sens_entries['u3'][i].delete(0, tk.END)
                    self.sens_entries['u4'][i].delete(0, tk.END)
                    self.sens_entries['uh'][i].config(state='normal')
                    self.sens_entries['uh'][i].delete(0, tk.END)
                    self.sens_entries['uh'][i].config(state='readonly')
                # ===== 保存空数据 =====
                self.save_sensitivity_data_from_table()
                return
            
            # 恢复表格数据
            for i in range(11):
                if i < len(self.sens_saved_data.get('b', [])):
                    self.sens_entries['b'][i].delete(0, tk.END)
                    self.sens_entries['b'][i].insert(0, self.sens_saved_data['b'][i])
                    
                    for key in ['u1', 'u2', 'u3', 'u4']:
                        self.sens_entries[key][i].delete(0, tk.END)
                        if i < len(self.sens_saved_data.get(key, [])):
                            self.sens_entries[key][i].insert(0, self.sens_saved_data[key][i])
                    
                    self.sens_entries['uh'][i].config(state='normal')
                    self.sens_entries['uh'][i].delete(0, tk.END)
                    if i < len(self.sens_saved_data.get('uh', [])):
                        self.sens_entries['uh'][i].insert(0, self.sens_saved_data['uh'][i])
                    self.sens_entries['uh'][i].config(state='readonly')
            
            # 恢复曲线
            if hasattr(self, 'sens_saved_data') and self.sens_saved_data.get('b_values') and self.sens_saved_data.get('uh_values'):
                self.update_sens_plot(self.sens_saved_data['b_values'], self.sens_saved_data['uh_values'])
            
            # ===== 关键：恢复后重新保存，确保数据持久化 =====
            self.save_sensitivity_data_from_table()
            
        except Exception as e:
            print(f"恢复灵敏度数据失败: {e}")

    def sens_select_row(self, row_index):
        """选中灵敏度表格的指定行（行号从1开始）"""
        idx = row_index - 1  # 用户可见行号转列表索引
        
        # 清除之前的高亮
        if self.sens_selected_row >= 0:
            old_idx = self.sens_selected_row - 1
            if 0 <= old_idx < len(self.sens_entries['b']):
                for key in ['b', 'u1', 'u2', 'u3', 'u4', 'uh']:
                    try:
                        self.sens_entries[key][old_idx].config(bg='white')
                    except:
                        pass
        
        # 高亮新选中的行
        if 0 <= idx < len(self.sens_entries['b']):
            self.sens_selected_row = row_index  # 存储用户可见行号
            for key in ['b', 'u1', 'u2', 'u3', 'u4', 'uh']:
                try:
                    self.sens_entries[key][idx].config(bg='lightblue')
                except:
                    pass

    def delete_sens_selected_row(self):
        """删除灵敏度表格选中的行"""
        if self.sens_selected_row < 0:
            messagebox.showwarning("警告", "请先点击任意单元格选中要删除的行！")
            return
        
        idx = self.sens_selected_row - 1
        
        # 检查该行是否有数据
        has_data = False
        for key in ['b', 'u1', 'u2', 'u3', 'u4']:
            if self.sens_entries[key][idx].get().strip():
                has_data = True
                break
        
        if not has_data:
            messagebox.showwarning("警告", f"第{self.sens_selected_row}行没有数据！")
            return
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除第{self.sens_selected_row}行的数据吗？"):
            return
        
        # 清空所有列的数据
        for key in ['b', 'u1', 'u2', 'u3', 'u4']:
            self.sens_entries[key][idx].delete(0, tk.END)
        
        # 清空只读列
        self.sens_entries['uh'][idx].config(state='normal')
        self.sens_entries['uh'][idx].delete(0, tk.END)
        self.sens_entries['uh'][idx].config(state='readonly')
        
        # 清除高亮
        for key in ['b', 'u1', 'u2', 'u3', 'u4', 'uh']:
            self.sens_entries[key][idx].config(bg='white')
        
        self.sens_selected_row = -1
        
        # 重新计算并更新曲线
        self.calculate_sensitivity()
        messagebox.showinfo("删除成功", f"已删除第{idx+1}行数据")
        
    def create_sensitivity_page(self, parent):
        """创建灵敏度页面（只创建一次）"""
        # 主框架
        main_frame = tk.Frame(parent, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 按钮框架
        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.pack(pady=6)
        
        buttons = [
            ("计算", self.calculate_sensitivity),
            ("删除选中行", self.delete_sens_selected_row),
            ("导出数据", self.export_sensitivity_data),
            ("导入数据", self.import_sensitivity_data),
            ("清空数据", self.clear_sensitivity_data)
        ]
        
        for text, command in buttons:
            btn = tk.Button(button_frame, text=text, command=command,
                        width=11, bg='lightblue')
            btn.pack(side=tk.LEFT, padx=3)

        # 表格容器（带滚动条）
        table_container = tk.Frame(main_frame, bg='white')
        table_container.pack(pady=5, fill=tk.X)
        
        # 创建画布和滚动条
        self.sens_canvas = tk.Canvas(table_container, height=150, bg='white')
        scrollbar = tk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.sens_canvas.yview)
        self.sens_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sens_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        

        # 在画布中创建表格框架
        self.sens_table_frame = tk.Frame(self.sens_canvas, bg='white')
        self.sens_table_window_id = self.sens_canvas.create_window(
            (0, 0), window=self.sens_table_frame, anchor=tk.NW
        )
        
        def on_sens_canvas_resize(event):
            self.sens_canvas.itemconfig(self.sens_table_window_id, width=event.width)
        self.sens_canvas.bind('<Configure>', on_sens_canvas_resize)
        
        # ===== 提示标签放在表头上面（第0行） =====
        hint_label = tk.Label(self.sens_table_frame, text="💡 点击任意单元格选中该行 | B列点击获取毫特计值 | U列点击获取电压值", 
                            font=("Arial", 8), fg='blue', bg='white')
        hint_label.grid(row=0, column=0, columnspan=6, pady=2)
        
        # 创建表格（6列12行）
        headers = ["B/mT", "U1/mV", "U2/mV", "U3/mV", "U4/mV", "Uh/mV"]
        
        for col, header in enumerate(headers):
            label = tk.Label(self.sens_table_frame, text=header, relief=tk.RIDGE,
                        width=18, bg='lightgray', font=("Arial", 8, "bold"))
            label.grid(row=1, column=col, padx=1, pady=1, sticky='ew')
            self.sens_table_frame.columnconfigure(col, weight=1)
        
        self.sens_selected_row = -1
        
        # 初始化数据存储
        self.sens_entries = {
            'b': [], 'u1': [], 'u2': [], 'u3': [], 'u4': [], 'uh': []
        }
        
        def make_sens_row_selector(row_index):
            def select_row(event):
                self.sens_select_row(row_index)
            return select_row

        # 创建11行数据（行2-12，行0是提示，行1是表头）
        for row in range(2, 13):
            user_row = row - 1  # 用户可见行号：1, 2, 3, ..., 11
            idx = row - 2       # 列表索引：0, 1, 2, ..., 10
            
            entry_b = tk.Entry(self.sens_table_frame, width=18, justify='center', font=("Arial", 8))
            entry_b.grid(row=row, column=0, padx=1, pady=1, sticky='ew')
            entry_b.bind("<Button-1>", lambda e, entry=entry_b: self.sens_auto_fill_b_entry(entry))
            entry_b.bind("<Button-1>", make_sens_row_selector(user_row), add="+")
            self.sens_entries['b'].append(entry_b)
            
            entry_u1 = tk.Entry(self.sens_table_frame, width=16, justify='center', font=("Arial", 8))
            entry_u1.grid(row=row, column=1, padx=1, pady=1, sticky='ew')
            entry_u1.bind("<Button-1>", lambda e, entry=entry_u1: self.sens_auto_fill_voltage_entry(entry))
            entry_u1.bind("<Button-1>", make_sens_row_selector(user_row), add="+")
            self.sens_entries['u1'].append(entry_u1)
            
            entry_u2 = tk.Entry(self.sens_table_frame, width=16, justify='center', font=("Arial", 8))
            entry_u2.grid(row=row, column=2, padx=1, pady=1, sticky='ew')
            entry_u2.bind("<Button-1>", lambda e, entry=entry_u2: self.sens_auto_fill_voltage_entry(entry))
            entry_u2.bind("<Button-1>", make_sens_row_selector(user_row), add="+")
            self.sens_entries['u2'].append(entry_u2)
            
            entry_u3 = tk.Entry(self.sens_table_frame, width=16, justify='center', font=("Arial", 8))
            entry_u3.grid(row=row, column=3, padx=1, pady=1, sticky='ew')
            entry_u3.bind("<Button-1>", lambda e, entry=entry_u3: self.sens_auto_fill_voltage_entry(entry))
            entry_u3.bind("<Button-1>", make_sens_row_selector(user_row), add="+")
            self.sens_entries['u3'].append(entry_u3)
            
            entry_u4 = tk.Entry(self.sens_table_frame, width=16, justify='center', font=("Arial", 8))
            entry_u4.grid(row=row, column=4, padx=1, pady=1, sticky='ew')
            entry_u4.bind("<Button-1>", lambda e, entry=entry_u4: self.sens_auto_fill_voltage_entry(entry))
            entry_u4.bind("<Button-1>", make_sens_row_selector(user_row), add="+")
            self.sens_entries['u4'].append(entry_u4)
            
            entry_uh = tk.Entry(self.sens_table_frame, width=16, justify='center',
                            state='readonly', readonlybackground='white', font=("Arial", 8))
            entry_uh.grid(row=row, column=5, padx=1, pady=1, sticky='ew')
            entry_uh.bind("<Button-1>", make_sens_row_selector(user_row))
            self.sens_entries['uh'].append(entry_uh)
        
        self.sens_table_frame.update_idletasks()
        self.sens_canvas.configure(scrollregion=self.sens_canvas.bbox("all"))
        
        # ===== 在表格和曲线图之间添加参数显示 =====
        param_frame = tk.Frame(main_frame, bg='white')
        param_frame.pack(pady=5, fill=tk.X)
        
        # Ih 显示
        tk.Label(param_frame, text="恒流源电流 Ih =", font=("Arial", 9), bg='white').pack(side=tk.LEFT, padx=5)
        self.sens_Ih_label = tk.Label(param_frame, text="0", font=("Arial", 9, "bold"), fg='green', bg='white')
        self.sens_Ih_label.pack(side=tk.LEFT)
        tk.Label(param_frame, text="mA", font=("Arial", 9), bg='white').pack(side=tk.LEFT)
        
        # 分隔符
        tk.Label(param_frame, text="  |  ", font=("Arial", 9), bg='white').pack(side=tk.LEFT)
        
        # 灵敏度显示（放在 Ih 右边）
        tk.Label(param_frame, text="砷化镓霍尔元件灵敏度 Kh =", font=("Arial", 9), bg='white').pack(side=tk.LEFT, padx=5)
        self.sens_kh_label = tk.Label(param_frame, text="0.0", font=("Arial", 9, "bold"), fg='red', bg='white')
        self.sens_kh_label.pack(side=tk.LEFT)
        tk.Label(param_frame, text="mV/(mA·T)", font=("Arial", 9), bg='white').pack(side=tk.LEFT)

        # 曲线图
        plot_frame = tk.Frame(main_frame, bg='white')
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=2)
        
        self.sens_fig, self.sens_ax = plt.subplots(figsize=(5, 2))
        self.sens_fig.subplots_adjust(bottom=0.2, left=0.1, right=0.95, top=0.88)
        self.sens_canvas_plot = FigureCanvasTkAgg(self.sens_fig, master=plot_frame)
        self.sens_canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.sens_ax.set_xlabel('B (mT)', fontsize=9)
        self.sens_ax.set_ylabel('Uh (mV)', fontsize=9)
        self.sens_ax.set_title('Uh-B关系曲线（霍尔灵敏度）', fontsize=10)
        self.sens_ax.grid(True)
        
        # 如果有保存的数据，恢复显示
        if hasattr(self, 'sens_saved_data') and self.sens_saved_data.get('b_values') and self.sens_saved_data.get('uh_values'):
            self.update_sens_plot(self.sens_saved_data['b_values'], self.sens_saved_data['uh_values'])
        else:
            self.sens_ax.set_ylim(1, -1)
            self.sens_canvas_plot.draw()
        
    def sens_auto_fill_b(self, row_index):
        """灵敏度界面：点击B列单元格自动获取毫特计值"""
        try:
            # 获取当前毫特计值
            millitesla_str = self.millitesla_var.get()
            b_value = float(millitesla_str)
            
            entry = self.sens_entries['b'][row_index]
            entry.delete(0, tk.END)
            entry.insert(0, f"{b_value:.1f}")
        except ValueError:
            messagebox.showwarning("警告", "无法获取当前毫特计值！")

    def sens_auto_fill_b_entry(self, entry_widget):
        """灵敏度界面：点击B列单元格自动获取毫特计值"""
        try:
            millitesla_str = self.millitesla_var.get()
            b_value = float(millitesla_str)
            
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, f"{b_value:.1f}")
        except ValueError:
            messagebox.showwarning("警告", "无法获取当前毫特计值！")

    def sens_auto_fill_voltage_entry(self, entry_widget):
        """灵敏度界面：点击U1-U4列单元格自动获取电压值"""
        try:
            voltage_str = self.voltage_var.get()
            voltage = float(voltage_str)
            
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, f"{voltage:.1f}")
        except ValueError:
            messagebox.showwarning("警告", "无法获取当前电压值！")

    def calculate_sensitivity(self, use_saved_param=False):
        """计算灵敏度数据"""
        try:
            if use_saved_param and hasattr(self, 'sens_imported_Ih'):
                current_Ih = self.sens_imported_Ih
            else:
                current_Ih = self.constant_current / 50.0
                current_Ih = round(current_Ih, 3)
            
            # 更新显示标签
            if hasattr(self, 'sens_Ih_label'):
                self.sens_Ih_label.config(text=f"{current_Ih:.3f}")
            
            # 保存参数
            self.sens_current_Ih = current_Ih

            b_values = []
            uh_values = []
            
            # 保存原始数据
            self.sens_saved_data = {
                'b': [],
                'u1': [],
                'u2': [],
                'u3': [],
                'u4': [],
                'uh': [],
                'b_values': [],
                'uh_values': []
            }
            
            # 先清除Uh列，准备重新计算
            for i in range(11):
                self.sens_entries['uh'][i].config(state='normal')
                self.sens_entries['uh'][i].delete(0, tk.END)
                self.sens_entries['uh'][i].config(state='readonly')
            
            for i in range(11):
                b_str = self.sens_entries['b'][i].get().strip()
                u1_str = self.sens_entries['u1'][i].get().strip()
                u2_str = self.sens_entries['u2'][i].get().strip()
                u3_str = self.sens_entries['u3'][i].get().strip()
                u4_str = self.sens_entries['u4'][i].get().strip()
                
                # 保存原始数据
                self.sens_saved_data['b'].append(b_str)
                self.sens_saved_data['u1'].append(u1_str)
                self.sens_saved_data['u2'].append(u2_str)
                self.sens_saved_data['u3'].append(u3_str)
                self.sens_saved_data['u4'].append(u4_str)
                
                # 如果有B值且至少有一个U值，才计算
                if b_str and (u1_str or u2_str or u3_str or u4_str):
                    b = float(b_str) if b_str else 0
                    u1 = float(u1_str) if u1_str else 0
                    u2 = float(u2_str) if u2_str else 0
                    u3 = float(u3_str) if u3_str else 0
                    u4 = float(u4_str) if u4_str else 0
                    
                    uh = (u1 + u3 - u2 - u4) / 4
                    
                    b_values.append(b)
                    uh_values.append(uh)
                    
                    self.sens_entries['uh'][i].config(state='normal')
                    self.sens_entries['uh'][i].delete(0, tk.END)
                    self.sens_entries['uh'][i].insert(0, f"{uh:.3f}")
                    self.sens_entries['uh'][i].config(state='readonly')
                    self.sens_saved_data['uh'].append(f"{uh:.3f}")
                else:
                    self.sens_entries['uh'][i].config(state='normal')
                    self.sens_entries['uh'][i].delete(0, tk.END)
                    self.sens_entries['uh'][i].config(state='readonly')
                    self.sens_saved_data['uh'].append("")
            
            # 保存曲线数据
            self.sens_saved_data['b_values'] = b_values
            self.sens_saved_data['uh_values'] = uh_values
            self.sens_saved_data['constant_Ih'] = current_Ih
            
            # 更新曲线图
            self.update_sens_plot(b_values, uh_values)
            
            # ===== 计算完成后保存数据 =====
            self.save_sensitivity_data_from_table()
            
            messagebox.showinfo("计算完成", "灵敏度计算完成！")
        except ValueError as e:
            messagebox.showerror("错误", f"输入数据格式错误：{e}")
        except Exception as e:
            messagebox.showerror("错误", f"计算失败：{e}")


    def update_sens_plot(self, b_values, uh_values):
        """更新灵敏度曲线图"""
        if not hasattr(self, 'sens_ax') or self.sens_ax is None:
            return
        
        self.sens_ax.clear()
        
        # 过滤有效数据 - 只要有B值且Uh有值就保留（包括B=0的点）
        filtered_data = []
        for b, uh in zip(b_values, uh_values):
            if b is not None and uh is not None:
                filtered_data.append((b, uh))
        
        slope = 0
        intercept = 0
        
        if filtered_data:
            b_valid = [d[0] for d in filtered_data]
            uh_valid = [d[1] for d in filtered_data]
            
            # 绘制散点图
            self.sens_ax.scatter(b_valid, uh_valid, color='blue', s=50, label='实验数据')
            
            # ===== 包含所有数据点（包括B=0）进行线性拟合 =====
            if len(filtered_data) >= 2:
                b_fit = np.array([d[0] for d in filtered_data])
                uh_fit = np.array([d[1] for d in filtered_data])
                
                # 普通线性拟合，包含截距
                coeffs = np.polyfit(b_fit, uh_fit, 1)
                slope = coeffs[0]
                intercept = coeffs[1]
                
                # 绘制拟合直线
                x_min, x_max = min(b_fit), max(b_fit)
                x_margin = max(0.5, (x_max - x_min) * 0.1) if x_max > x_min else 1.0
                x_line = np.array([x_min - x_margin, x_max + x_margin])
                y_line = slope * x_line + intercept
                self.sens_ax.plot(x_line, y_line, 'r-', 
                                label=f'拟合: Uh={slope:.4f}*B+{intercept:.4f}')
                
                # 计算灵敏度 Kh = 斜率 / Ih * 1000
                if hasattr(self, 'sens_current_Ih') and self.sens_current_Ih != 0:
                    kh = (slope * 1000) / self.sens_current_Ih
                else:
                    kh = 0.0
                
                # 显示公式
                formula_text = f'Uh = {slope:.4f} * B + {intercept:.4f}'
                self.sens_ax.text(0.05, 0.95, formula_text, transform=self.sens_ax.transAxes,
                            fontsize=10, verticalalignment='top',
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                self.sens_ax.legend()
                
                # 更新Kh显示
                try:
                    if hasattr(self, 'sens_kh_label') and self.sens_kh_label is not None:
                        self.sens_kh_label.config(text=f"{kh:.1f}")
                except (tk.TclError, RuntimeError):
                    pass
            else:
                try:
                    if hasattr(self, 'sens_kh_label') and self.sens_kh_label is not None:
                        self.sens_kh_label.config(text="0.0")
                except (tk.TclError, RuntimeError):
                    pass
        
        self.sens_ax.set_xlabel('B (mT)')
        self.sens_ax.set_ylabel('Uh (mV)')
        self.sens_ax.set_title('Uh-B关系曲线（霍尔灵敏度）')
        self.sens_ax.grid(True)
        
        # ===== 增大边距，确保边缘点可见 =====
        if filtered_data:
            b_values_list = [d[0] for d in filtered_data]
            uh_values_list = [d[1] for d in filtered_data]
            b_min, b_max = min(b_values_list), max(b_values_list)
            uh_min, uh_max = min(uh_values_list), max(uh_values_list)
            
            b_range = b_max - b_min
            uh_range = uh_max - uh_min
            
            # 边距：至少保留25%的边距
            b_margin = max(0.5, b_range * 0.25) if b_range > 0 else 1.0
            uh_margin = max(0.5, uh_range * 0.25) if uh_range > 0 else 1.0
            
            # 确保包含0点
            b_min = min(b_min, 0) - b_margin
            b_max = max(b_max, 0) + b_margin
            uh_min = min(uh_min, 0) - uh_margin
            uh_max = max(uh_max, 0) + uh_margin
            
            # 如果范围太小，设置一个合理的最小范围
            if abs(b_max - b_min) < 0.1:
                b_min = -1.0
                b_max = 1.0
            if abs(uh_max - uh_min) < 0.1:
                uh_min = -0.5
                uh_max = 0.5
            
            # 反转y轴，使纵轴从0开始向上减小
            self.sens_ax.set_xlim(b_min, b_max)
            self.sens_ax.set_ylim(uh_max, uh_min)
        else:
            self.sens_ax.set_ylim(1, -1)
        
        if hasattr(self, 'sens_canvas_plot') and self.sens_canvas_plot:
            try:
                self.sens_canvas_plot.draw()
            except (tk.TclError, RuntimeError):
                pass

    def export_sensitivity_data(self):
        """导出灵敏度数据到CSV"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv")]
        )
        
        if file_path:
            try:
                # 获取当前Kh值
                kh_text = self.sens_kh_label.cget('text') if hasattr(self, 'sens_kh_label') else "0.00"
                
                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write("=== 实验参数 ===\n")
                    f.write(f"砷化镓霍尔灵敏度Kh,{kh_text}\n")
                    # ===== 添加恒流源电流 =====
                    if hasattr(self, 'sens_current_Ih'):
                        f.write(f"恒流源电流 Ih,{self.sens_current_Ih:.3f},mA\n")
                    f.write("\n")
                    f.write("B(mT),U1(mV),U2(mV),U3(mV),U4(mV),Uh(mV)\n")
                    for i in range(11):
                        b = self.sens_entries['b'][i].get().strip()
                        u1 = self.sens_entries['u1'][i].get().strip()
                        u2 = self.sens_entries['u2'][i].get().strip()
                        u3 = self.sens_entries['u3'][i].get().strip()
                        u4 = self.sens_entries['u4'][i].get().strip()
                        uh = self.sens_entries['uh'][i].get().strip()
                        if b or u1 or u2 or u3 or u4:
                            f.write(f"{b},{u1},{u2},{u3},{u4},{uh}\n")
                messagebox.showinfo("导出成功", f"数据已导出到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出数据时出错:\n{str(e)}")

    def import_sensitivity_data(self):
        """导入灵敏度数据从CSV"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                
                kh_value = None
                constant_Ih = None
                data_start = 0
                
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    if line_stripped:
                        if line_stripped.startswith("砷化镓霍尔灵敏度Kh"):
                            parts = line_stripped.split(',')
                            if len(parts) >= 2:
                                try:
                                    kh_value = float(parts[1].strip())
                                except:
                                    pass
                        elif '恒流源电流 Ih' in line_stripped:
                            parts = line_stripped.split(',')
                            if len(parts) >= 2:
                                try:
                                    constant_Ih = float(parts[1].strip())
                                except:
                                    pass
                        elif line_stripped.startswith("B(mT)") or line_stripped.startswith("B"):
                            data_start = i + 1
                            break
                
                if data_start == 0:
                    for i, line in enumerate(lines):
                        line_stripped = line.strip()
                        if line_stripped and 'B' in line_stripped and 'U1' in line_stripped:
                            data_start = i + 1
                            break
                
                # ===== 保存导入的参数 =====
                self.sens_imported_Ih = constant_Ih if constant_Ih is not None else 0
                
                # 更新Kh显示
                if kh_value is not None and hasattr(self, 'sens_kh_label'):
                    self.sens_kh_label.config(text=f"{kh_value:.4f}")
                
                # 读取数据
                data_lines = []
                for line in lines[data_start:]:
                    line_stripped = line.strip()
                    if line_stripped and '===' not in line_stripped:
                        data_lines.append(line_stripped)
                
                # 先清空
                for i in range(11):
                    self.sens_entries['b'][i].delete(0, tk.END)
                    self.sens_entries['u1'][i].delete(0, tk.END)
                    self.sens_entries['u2'][i].delete(0, tk.END)
                    self.sens_entries['u3'][i].delete(0, tk.END)
                    self.sens_entries['u4'][i].delete(0, tk.END)
                    self.sens_entries['uh'][i].config(state='normal')
                    self.sens_entries['uh'][i].delete(0, tk.END)
                    self.sens_entries['uh'][i].config(state='readonly')
                
                for i, line in enumerate(data_lines[:11]):
                    parts = line.strip().split(',')
                    if len(parts) >= 6:
                        try:
                            float(parts[0].strip())
                        except ValueError:
                            continue
                        
                        self.sens_entries['b'][i].delete(0, tk.END)
                        self.sens_entries['b'][i].insert(0, parts[0].strip())
                        
                        self.sens_entries['u1'][i].delete(0, tk.END)
                        self.sens_entries['u1'][i].insert(0, parts[1].strip())
                        
                        self.sens_entries['u2'][i].delete(0, tk.END)
                        self.sens_entries['u2'][i].insert(0, parts[2].strip())
                        
                        self.sens_entries['u3'][i].delete(0, tk.END)
                        self.sens_entries['u3'][i].insert(0, parts[3].strip())
                        
                        self.sens_entries['u4'][i].delete(0, tk.END)
                        self.sens_entries['u4'][i].insert(0, parts[4].strip())
                        
                        self.sens_entries['uh'][i].config(state='normal')
                        self.sens_entries['uh'][i].delete(0, tk.END)
                        self.sens_entries['uh'][i].insert(0, parts[5].strip())
                        self.sens_entries['uh'][i].config(state='readonly')
                
                # ===== 使用导入的参数重新计算 =====
                self.calculate_sensitivity(use_saved_param=True)
                
                # 清除导入参数标记
                self.sens_imported_Ih = None
                
                messagebox.showinfo("导入成功", "数据导入完成！")
            except Exception as e:
                messagebox.showerror("导入失败", f"导入数据时出错:\n{str(e)}")

    def clear_sensitivity_data(self):
        """清空灵敏度数据"""
        if not messagebox.askyesno("确认清空", "确定要清空所有灵敏度数据吗？"):
            return
        
        for i in range(11):
            self.sens_entries['b'][i].delete(0, tk.END)
            self.sens_entries['u1'][i].delete(0, tk.END)
            self.sens_entries['u2'][i].delete(0, tk.END)
            self.sens_entries['u3'][i].delete(0, tk.END)
            self.sens_entries['u4'][i].delete(0, tk.END)
            
            self.sens_entries['uh'][i].config(state='normal')
            self.sens_entries['uh'][i].delete(0, tk.END)
            self.sens_entries['uh'][i].config(state='readonly')
        
        # 清空曲线图
        if hasattr(self, 'sens_ax') and self.sens_ax is not None:
            self.sens_ax.clear()
            self.sens_ax.set_xlabel('B (mT)')
            self.sens_ax.set_ylabel('Uh (mV)')
            self.sens_ax.set_title('Uh-B关系曲线（霍尔灵敏度）')
            self.sens_ax.grid(True)
            if hasattr(self, 'sens_canvas_plot') and self.sens_canvas_plot:
                self.sens_canvas_plot.draw()
        
        # ===== 清空参数显示 =====
        if hasattr(self, 'sens_Ih_label'):
            self.sens_Ih_label.config(text="0")
        
        # 清除保存的参数
        self.sens_current_Ih = 0

        # 重置Kh显示
        if hasattr(self, 'sens_kh_label'):
            self.sens_kh_label.config(text="0.00")
        
        # ===== 保存空数据 =====
        self.save_sensitivity_data_from_table()
        
        messagebox.showinfo("清空数据", "数据已清空！")

    def start_demagnetize(self):
        """开始自动退磁"""
        if self.is_demagnetizing:
            return
        
        # 检查是否已经退磁过（从(0,0)开始）
        if self.demagnetize_complete:
            # 已经退磁过，从(0,0)开始
            self.demag_data = []
            self.demag_step = 0
            self.current_direction = 1
            self.reset_hysteresis_state(use_remanence=False)
            self._hyst_turn_points = []
            start_B = 0.0
        else:
            # 首次退磁，从剩磁开始 (-50 到 -60 mT)
            self.demag_data = []
            self.demag_step = 0
            self.current_direction = 1
            self.reset_hysteresis_state(use_remanence=True)
            start_B = self.degauss_before_offset
        
        self.is_demagnetizing = True
        self.demag_btn.config(state='disabled', text="退磁中...")
        
        # 添加起点
        self.demag_data.append((0, start_B))
        self._update_demag_ui_quick(0, start_B)

        # 使用统一的更新方法
        self._update_demag_axes()
        if hasattr(self, 'canvas_plot') and self.canvas_plot:
            self.canvas_plot.draw()

        # 启动退磁
        self.root.after(50, self._demagnetize_step)

    def _demagnetize_step(self):
        """执行一步退磁"""
        if not self.is_demagnetizing:
            return

        max_current = 600 - self.demag_step * 100
        if max_current <= 0:
            self._finish_demagnetize()
            return

        polarity = 1 if self.current_direction == 1 else -1
        step_size = 50
        steps = int(max_current / step_size)

        # ===== 使用完整磁滞模型 =====
        # 位置因子：霍尔元件在磁场中的位置影响
        # 位置0为中心，±20mm范围内线性衰减
        position_factor = 1.0 - abs(self.hall_position) / 20.0 * 0.3
        position_factor = max(0.7, min(1.0, position_factor))
        
        # 上升（从当前值到峰值）
        for i in range(1, steps + 1):
            current_val = i * step_size * polarity
            
            # ===== 使用 get_B_from_magnetic_model 获取完整磁滞回线值 =====
            B_raw = self.get_B_from_magnetic_model(current_val)  # ← 修正方法名
            
            # 应用位置衰减
            B_positioned = B_raw * position_factor
            
            # 使用退磁前偏移作为随机偏移（首次退磁），退磁完成后为0
            random_offset = self.degauss_before_offset if not self.demagnetize_complete else 0.0
            B_val = B_positioned + random_offset + self.millitesla_offset
            B_val += random.uniform(-0.3, 0.3)
            
            self.demag_data.append((current_val, B_val))
            self._update_demag_ui(current_val, B_val)

        # 下降（从峰值到0）
        for i in range(steps - 1, -1, -1):
            current_val = i * step_size * polarity
            B_raw = self.get_B_from_magnetic_model(current_val)  # ← 修正方法名
            
            B_positioned = B_raw * position_factor
            random_offset = self.degauss_before_offset if not self.demagnetize_complete else 0.0
            B_val = B_positioned + random_offset + self.millitesla_offset
            B_val += random.uniform(-0.3, 0.3)
            self.demag_data.append((current_val, B_val))
            self._update_demag_ui(current_val, B_val)

        # 切换方向并更新按钮
        self.current_direction *= -1
        self.update_direction_button()
        self.update_arrows()  # ← 添加这行
        
        self.demag_step += 1
        if self.is_demagnetizing:
            self.root.after(30, self._demagnetize_step)
    
    def _finish_demagnetize(self):
        """完成退磁 - 结束在(0,0)"""
        self.is_demagnetizing = False
        self.demagnetize_complete = True
        self.demag_btn.config(state='normal', text="自动退磁")
        
        # 电流归零
        self.excitation_current = 0
        self.current_var.set("0")
        self.excitation_scale.set(0)
        
        # 重置方向为正向并更新按钮
        self.current_direction = 1
        self.update_direction_button()
        
        # 退磁终点为(0,0)
        final_B = 0.0
        
        if self.demag_data:
            last_point = self.demag_data[-1]
            if last_point[0] != 0 or abs(last_point[1]) > 0.1:
                self.demag_data.append((0, final_B))
                self._update_demag_ui_quick(0, final_B)
        
        self._degauss_end_B = final_B
        
        # 重置磁滞状态到0
        self.reset_hysteresis_state(use_remanence=False)
        
        # 清除退磁前偏移（退磁完成，偏移消除）
        self.degauss_before_offset = 0.0
        
        # 更新显示（使用统一方法）
        self.update_millitesla_display()
        self._update_demag_axes()
        if hasattr(self, 'canvas_plot') and self.canvas_plot:
            self.canvas_plot.draw()
        
        messagebox.showinfo("退磁完成", "退磁操作完成！")


    def update_demag_plot_new(self):
        """更新退磁曲线图（新版）- 调用统一方法"""
        if not hasattr(self, 'ax') or self.ax is None:
            return
        self._update_demag_axes()
        if hasattr(self, 'canvas_plot') and self.canvas_plot:
            self.canvas_plot.draw()

    def _update_demag_ui_quick(self, current_val, b_val):
        """快速更新退磁UI"""
        try:
            self.excitation_current = abs(current_val)
            self.current_var.set(str(abs(current_val)))

            # 显示当前B值（b_val已经包含偏移）
            self.millitesla_var.set(f"{b_val:.1f}")  # ← 直接使用 b_val
            self.excitation_scale.set(abs(current_val))

            # 每5个点更新一次曲线（使用统一方法）
            if not hasattr(self, '_update_counter'):
                self._update_counter = 0
            self._update_counter += 1
            if self._update_counter % 5 == 0 or current_val == 0:
                self._update_demag_axes()
                if hasattr(self, 'canvas_plot') and self.canvas_plot:
                    self.canvas_plot.draw()

            self.root.update_idletasks()
            self.root.update()
            time.sleep(0.005)
        except Exception:
            pass

    def _final_return_to_zero(self):
        """最后一步：从当前电流回到0，退磁完成后回到原点"""
        # 获取当前电流值
        current_I = self.demag_state.get('I', 0.0)
        
        # 固定步长
        step_size = 100
        direction = -1 if current_I > 0 else 1
        steps = int(abs(current_I) / step_size)
        
        for i in range(steps + 1):
            current_val = current_I + i * step_size * direction
            
            if (direction > 0 and current_val > 0) or (direction < 0 and current_val < 0):
                current_val = 0.0
            
            # 计算B值，最终回到0
            B_val = self._calculate_degauss_B(current_val, 0, 1)
            self.demag_data.append((current_val, B_val))
            self._update_degauss_ui(current_val, B_val, delay=0.005)
            
            if current_val == 0:
                break
        
        # 确保最后一个点回到原点 (0, 0)
        if self.demag_data and abs(self.demag_data[-1][1]) > 0.1:
            self.demag_data.append((0, 0))
            self._update_degauss_ui(0, 0, delay=0.005)
        
        # 退磁完成 - 消除退磁前偏移
        self.demagnetize_complete = True
        self.is_demagnetizing = False
        self.demag_btn.config(state='normal', text="自动退磁")
        
        # 清除退磁前偏移
        self.degauss_before_offset = 0.0
        
        # 更新显示
        self.update_millitesla_display()
        self.update_voltage_display()
        self.update_demag_plot()
        
        messagebox.showinfo("退磁完成", "退磁操作完成！请将毫特计和电压表调零。")

    def _calculate_degauss_B(self, I, amplitude, polarity):
        """
        计算退磁过程中的B值 - 嵌套磁滞回线模型
        """
        # 材料参数
        B_SAT = 314.0
        I_SAT = 600.0
       
        def poly_upper(x):
            return float(np.polyval(self.POLY_UPPER, x))
        
        def poly_lower(x):
            return float(np.polyval(self.POLY_LOWER, x))
            
        # 获取状态
        state = self.demag_state
        last_I = state['I']
        dI = I - last_I
        
        if abs(dI) < 0.5:
            return state['B']
        
        new_direction = 1 if dI > 0 else -1
        
        # ===== 检测方向变化（转折点） =====
        if state['direction'] != 0 and new_direction != state['direction']:
            state['turn_points'].append((state['I'], state['B']))
            state['amplitude'] = abs(state['I'])
            
            if state['branch'] == 'initial':
                state['branch'] = 'upper'
                state['is_initial_rise'] = False
            elif state['branch'] == 'upper':
                state['branch'] = 'lower'
            elif state['branch'] == 'lower':
                state['branch'] = 'upper'
            
            if len(state['turn_points']) > 30:
                state['turn_points'] = state['turn_points'][-30:]
        
        state['direction'] = new_direction
        
        # 获取当前转折点
        if state['turn_points']:
            turn_I, turn_B = state['turn_points'][-1]
        else:
            # 初始状态：从y轴负半轴开始
            turn_I, turn_B = 0.0, self.degauss_before_offset
        
        amp = max(state['amplitude'], 1.0)
        scale = amp / I_SAT
        
        # ===== 计算B值 =====
        if state['branch'] == 'initial':
            abs_I = abs(I)
            if abs_I < 0.5:
                B_new = self.degauss_before_offset  # 起点在y轴负半轴
            else:
                I_norm = min(abs_I / amplitude, 1.0)
                B_peak = poly_upper(amplitude) * scale
                B0 = self.degauss_before_offset
                B1 = B_peak
                Bm = (B0 + B1) / 2 + (B1 - B0) * 0.2
                t = I_norm
                B_new = B0 * (1-t)**2 + 2 * Bm * t * (1-t) + B1 * t**2
        else:
            # 嵌套回线 - 保持原有逻辑
            I_mapped = I / scale if scale > 0.01 else 0
            I_mapped = np.clip(I_mapped, -I_SAT, I_SAT)
            
            if state['branch'] == 'upper':
                B_std = poly_upper(I_mapped)
            else:
                B_std = poly_lower(I_mapped)
            
            B_boundary = B_std * scale
            
            turn_I_mapped = turn_I / scale if scale > 0.01 else 0
            turn_I_mapped = np.clip(turn_I_mapped, -I_SAT, I_SAT)
            
            if state['branch'] == 'upper':
                B_turn_std = poly_upper(turn_I_mapped)
            else:
                B_turn_std = poly_lower(turn_I_mapped)
            
            B_boundary_at_turn = B_turn_std * scale
            offset = turn_B - B_boundary_at_turn
            
            travel = abs(I - turn_I)
            total_range = 2 * amp if amp > 0 else 1
            rel_pos = min(travel / total_range, 1.0)
            
            decay_slow = 1.0 - rel_pos * 0.6
            decay_fast = (1.0 - rel_pos) ** 2
            mix_weight = min(1.0, rel_pos * 2.0)
            offset_factor = (1 - mix_weight) * decay_slow + mix_weight * decay_fast
            offset_factor = max(0.0, min(1.0, offset_factor))
            
            B_new = B_boundary + offset * offset_factor
        
        # 限制在合理范围内
        if scale > 0.01:
            B_upper = poly_upper(I) * scale
            B_lower = poly_lower(I) * scale
        else:
            B_upper = poly_upper(I)
            B_lower = poly_lower(I)
        B_new = np.clip(B_new, min(B_lower, -150), max(B_upper, 150))
        
        # 更新状态
        state['I'] = I
        state['B'] = B_new
        
        return B_new

    def _update_degauss_ui(self, current_val, b_val, delay=0.005):
        """更新退磁过程中的UI"""
        # 更新左侧仪表显示
        self.excitation_current = abs(current_val)
        self.current_var.set(str(abs(current_val)))
        
        # 更新毫特计显示（使用退磁前偏移）
        display_offset = self.millitesla_offset + self.degauss_before_offset
        displayed_b = b_val + display_offset
        if hasattr(self, 'millitesla_var'):
            self.millitesla_var.set(f"{displayed_b:.1f}")
        
        # 更新电压表显示
        measured_voltage = 0
        if self.measure_mode == "UR":
            measured_voltage = self.constant_current * (-2)
        else:
            # ===== UH模式 =====
            ih_ratio = self.constant_current / 50.0
            constant_part = 0.6 * ih_ratio

            # 判断霍尔电流与励磁电流方向是否一致
            excitation_is_forward = (self.current_direction == 1)
            direction_match = (self.hall_current_direction == excitation_is_forward)

            # 方向相同时为负，方向不同时为正
            if direction_match:
                constant_part = -constant_part
            else:
                constant_part = constant_part

            if self.excitation_current != 0:
                excitation_part = self.constant_current * (-2) * 0.4937 / 240.0 * self.excitation_current
                
                if direction_match:
                    excitation_part = excitation_part
                else:
                    excitation_part = -excitation_part
                
                if self.current_direction == -1:
                    excitation_part = excitation_part * 0.97
                
                measured_voltage = excitation_part + constant_part
            else:
                measured_voltage = constant_part
        
        displayed_voltage = measured_voltage  # 删除 + self.fixed_voltage_offset
        if hasattr(self, 'voltage_var'):
            self.voltage_var.set(f"{displayed_voltage:.1f}")
        
        # 更新进度条
        self.excitation_scale.set(abs(current_val))
        
        # 更新退磁曲线图
        self._update_demag_axes()
        if hasattr(self, 'canvas_plot') and self.canvas_plot:
            self.canvas_plot.draw()
        
        # 刷新界面
        self.root.update_idletasks()
        self.root.update()
        if delay > 0:
            time.sleep(delay)

    def _update_demag_ui(self, current_val, b_val):
        """更新退磁过程中的UI"""
        # 更新左侧仪表显示
        self.excitation_current = abs(current_val)
        self.current_var.set(str(abs(current_val)))
        
        # 更新毫特计显示
        displayed_b = b_val
        if hasattr(self, 'millitesla_var'):
            self.millitesla_var.set(f"{displayed_b:.1f}")
        
        # 更新电压表显示
        measured_voltage = 0
        if self.measure_mode == "UR":
            measured_voltage = self.constant_current * (-2)
        else:
            # ===== UH模式 =====
            ih_ratio = self.constant_current / 50.0
            constant_part = 0.6 * ih_ratio

            # 判断霍尔电流与励磁电流方向是否一致
            excitation_is_forward = (self.current_direction == 1)
            direction_match = (self.hall_current_direction == excitation_is_forward)

            # 方向相同时为负，方向不同时为正
            if direction_match:
                constant_part = -constant_part
            else:
                constant_part = constant_part

            if self.excitation_current != 0:
                excitation_part = self.constant_current * (-2) * 0.4937 / 240.0 * self.excitation_current
                
                if direction_match:
                    excitation_part = excitation_part
                else:
                    excitation_part = -excitation_part
                
                if self.current_direction == -1:
                    excitation_part = excitation_part * 0.97
                
                measured_voltage = excitation_part + constant_part
            else:
                measured_voltage = constant_part
                    
        displayed_voltage = measured_voltage  # 删除 + self.fixed_voltage_offset
        if hasattr(self, 'voltage_var'):
            self.voltage_var.set(f"{displayed_voltage:.1f}")
        
        # 更新进度条
        self.excitation_scale.set(abs(current_val))
        
        # 更新退磁曲线图
        self._update_demag_axes()
        if hasattr(self, 'canvas_plot') and self.canvas_plot:
            self.canvas_plot.draw()
        
        # 刷新界面
        self.root.update_idletasks()
        self.root.update()
        time.sleep(0.02)