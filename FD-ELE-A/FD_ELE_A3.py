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
import pandas as pd
import json
import csv

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def resource_path(relative_path):
    """获取资源的绝对路径，兼容打包后的环境"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class MagneticMaterialExperiment:
    """测量铁磁材料的磁滞回线和磁化曲线 - 完整功能版"""

    # ==================== 样品参数 ====================
    SAMPLE_PARAMS = {
        'mold_steel': {
            'name': '模具钢',
            'type': '半硬磁材料',
            'Bs_mT': 320,
            'Hc_Am': 500,
            'Br_mT': 77,
            'l_bar_cm': 23.8,
            'l_gap_cm': 0.2,
            'N': 2000,
            'section_cm2': 4.0,
            'description': '宽磁滞回线，剩磁大，退磁较难',
            # ===== 新增：磁滞回线形状参数 =====
            'hyst_width_factor': 1.0,      # 回线宽度因子（相对于纯铁）
            'slope_after_zero': 1.8        # 过零后斜率增大倍数
        },
        'pure_iron': {
            'name': '电工纯铁',
            'type': '软磁材料',
            'Bs_mT': 800,
            'Hc_Am': 80,
            'Br_mT': 25,
            'l_bar_cm': 23.8,
            'l_gap_cm': 0.2,
            'N': 2000,
            'section_cm2': 4.0,
            'description': '窄磁滞回线，剩磁小，易退磁',
            'hyst_width_factor': 0.35,     # 回线宽度因子
            'slope_after_zero': 0.8        # 过零后斜率增大倍数
        }
    }

    # ==================== 实测数据拟合的多项式系数 ====================

    # ==================== 模具钢 - 宽磁滞回线，过零后斜率快速增大 ====================
    # 修改低次项系数使过零后斜率更大
    POLY_UPPER_MOLD = np.array([
        2.5182118055383348e-18, 1.3492625796343097e-16,
        -1.5030302285583753e-12, 4.885604896961923e-13,
        -1.8965117198829675e-07, -0.0002329886887901997,
        0.6697405093359231-0.05,  # 增大一次项系数，使过零后斜率更大
        78.22103482201453
    ])

    POLY_LOWER_MOLD = np.array([
        -3.701890964829607e-19, -6.574835216815333e-16,
        4.734415967183772e-13, 3.881612891836147e-10,
        -5.806655033947451e-07, 0.00014502345362569802,
        0.6873778445089721-0.05,  # 增大一次项系数，使过零后斜率更大
        -73.26564770910605
    ])

    # 纯铁 - 窄磁滞回线（系数整体缩小，使回线更窄）
    POLY_UPPER_IRON = np.array([
        2.5182118055383348e-18, 1.3492625796343097e-16,
        -1.5030302285583753e-12, 4.885604896961923e-13,
        -1.8965117198829675e-07, -0.0002329886887901997,
        1, 78.22103482201453
    ])

    POLY_LOWER_IRON = np.array([
        -3.701890964829607e-19, -6.574835216815333e-16,
        4.734415967183772e-13, 3.881612891836147e-10,
        -5.806655033947451e-07, 0.00014502345362569802,
        1, -73.26564770910605
    ])

    # 初始磁化曲线
    POLY_VIRGIN = np.array([
        -1.10625264e-12, 4.12158156e-09, -5.29945015e-06,
        2.63182417e-03, 1.04967057e-01, 0.0
    ])

    # ==================== 位置耦合实测数据 ====================
    POSITION_DATA = [
        (-10.0, 158.5), (-9.0, 161.3), (-8.0, 161.7), (-7.0, 161.6),
        (-6.0, 161.6), (-5.0, 161.6), (-4.0, 161.6), (-3.0, 161.7),
        (-2.0, 161.4), (-1.0, 161.5), (0.0, 161.7),
        (1.0, 161.8), (2.0, 161.9), (3.0, 161.9), (4.0, 161.9),
        (5.0, 161.8), (6.0, 161.6), (7.0, 161.6),
        (8.0, 152.7), (9.0, 109.3), (10.0, 69.9)
    ]
    UNIFORM_MIN = -9.0
    UNIFORM_MAX = 7.0

    def __init__(self, parent):
        self.parent = parent
        self.root = parent.winfo_toplevel()
        # ==================== 实验状态 ====================
        self.current_display = "sample_select"
        self.selected_sample = None
        self.is_zeroed = False
        self._first_enter_degauss = True  # 标记是否第一次进入退磁界面

        # ==================== 控件值 ====================
        self.hall_position = 0  # mm
        self.excitation_current = 0  # mA
        self.current_direction = 1  # 1:正向, -1:反向
        self.millitesla_offset = 0  # 用户调零偏移

        # ===== 控件列表（用于禁用/启用） =====
        self.control_widgets = []
        # ===== 箭头标签引用 =====
        self.arrow_experiment = None      # 实验指示箭头（固定向左）
        self.arrow_excitation = None      # 励磁电流方向指示

        # ==================== B-X数据 ====================
        self.bx_data = None
        self.bx_x_values = []
        self.bx_b_values = []

        # ==================== 样品剩磁（含随机误差，不含偏移） ====================
        self.sample_br_with_error = {}
        self.random_offset = 0.0  # 随机偏移，仅用于显示
        self._base_Bs = 315.0
        self._B_scale_factor = 1.0

        # ==================== 样品剩磁（含随机误差，不含偏移） ====================
        self.sample_br_initial = {}         # 初始剩磁（固定不变，用于参数显示）
  

        # ==================== 磁滞状态（当前使用） ====================
        self._hyst_branch = 'virgin'
        self._hyst_last_I = 0.0
        self._hyst_last_B = 0.0
        self._hyst_direction = 0
        self._hyst_turn_points = []
        self._hyst_loop_amp = 600.0
        self._hyst_max_amp = 0.0
        self._hyst_exceed_error = False
        self._hyst_turn_stack = []  # 添加这行
        self._hyst_B_offset = 0.0   # 添加这行

        # ===== 每个样品独立的磁滞状态存储 =====
        self._hyst_state_for_sample = {
            'mold_steel': {
                'branch': 'virgin',
                'last_I': 0.0,
                'last_B': 0.0,
                'direction': 0,
                'turn_points': [],
                'loop_amp': 600.0,
                'max_amp': 0.0
            },
            'pure_iron': {
                'branch': 'virgin',
                'last_I': 0.0,
                'last_B': 0.0,
                'direction': 0,
                'turn_points': [],
                'loop_amp': 600.0,
                'max_amp': 0.0
            }
        }

        # ===== 每个样品独立的退磁状态 =====
        self.demagnetize_complete = {
            'mold_steel': False,
            'pure_iron': False
        }

        # ==================== 退磁数据 ====================
        self.demag_data = []
        self.demag_step = 0
        self.is_demagnetizing = False
        self._degauss_end_B = 0.0

        # ==================== 数据管理 ====================
        self.tableA = []  # X/mm, B/mT
        self.tableB = []  # I/mA, B/mT, H/A_m

        # ==================== 初始化 ====================
        self.init_data()
        self.init_sample_br_with_error()  # 生成基础剩磁和随机偏移

        # ==================== 创建UI ====================
        self.main_frame = tk.Frame(self.parent, bg='white')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_ui()

        # millitesla_offset 初始为0，用户需要通过调零旋钮归零
        self.update_millitesla_display()
        print(f"程序启动完成，随机偏移(仅显示): {self.random_offset:.2f}mT")
        print("请选择样品，然后通过调零旋钮将毫特计归零")

        # 长按定时器
        self.hold_timer = None

    def _set_controls_state(self, state):
        """设置控件状态"""
        for widget in self.control_widgets:
            try:
                if widget.winfo_exists():
                    # 对于 Button，使用 tk.DISABLED 和 tk.NORMAL
                    if isinstance(widget, tk.Button):
                        if state == 'disabled':
                            widget.config(state=tk.DISABLED)
                        else:
                            widget.config(state=tk.NORMAL)
                    else:
                        widget.config(state=state)
            except:
                pass

    def _save_current_hyst_state(self):
        """保存当前样品的磁滞状态"""
        if self.selected_sample is None:
            return
        
        self._hyst_state_for_sample[self.selected_sample] = {
            'branch': self._hyst_branch,
            'last_I': self._hyst_last_I,
            'last_B': self._hyst_last_B,
            'direction': self._hyst_direction,
            'turn_points': self._hyst_turn_points.copy(),
            'loop_amp': self._hyst_loop_amp,
            'max_amp': self._hyst_max_amp
        }

    def _load_hyst_state(self, sample_type):
        """加载指定样品的磁滞状态"""
        state = self._hyst_state_for_sample.get(sample_type, {})
        
        self._hyst_branch = state.get('branch', 'virgin')
        self._hyst_last_I = state.get('last_I', 0.0)
        self._hyst_last_B = state.get('last_B', 0.0)
        self._hyst_direction = state.get('direction', 0)
        self._hyst_turn_points = state.get('turn_points', []).copy()
        self._hyst_loop_amp = state.get('loop_amp', 600.0)
        self._hyst_max_amp = state.get('max_amp', 0.0)

    # ==================== 数据加载 ====================
    def init_data(self):
        """初始化数据"""
        self.bx_data = None
        self.bx_x_values = []
        self.bx_b_values = []

    def load_bx_data(self):
        """从Excel文件加载B-X数据"""
        try:
            file_path = os.path.join("data", "B-X(300mA).xlsx")
            if not os.path.exists(file_path):
                try:
                    base_path = sys._MEIPASS
                    file_path = os.path.join(base_path, "data", "B-X(300mA).xlsx")
                except Exception:
                    pass

            if os.path.exists(file_path):
                self.bx_data = pd.read_excel(file_path)
                columns = self.bx_data.columns.tolist()
                if len(columns) >= 2:
                    self.bx_x_values = self.bx_data.iloc[:, 0].tolist()
                    self.bx_b_values = self.bx_data.iloc[:, 1].tolist()
                    print(f"B-X数据加载成功: {len(self.bx_x_values)} 个数据点")
                else:
                    self.bx_data = None
            else:
                print(f"B-X数据文件未找到: {file_path}")
                self.bx_data = None
        except Exception as e:
            print(f"加载B-X数据失败: {e}")
            self.bx_data = None

    def get_b_value_from_bx(self, x_position):
        """根据X位置查询对应的B值（线性插值）"""
        if self.bx_data is None or len(self.bx_x_values) == 0:
            return 250.0

        x_min = min(self.bx_x_values)
        x_max = max(self.bx_x_values)

        if x_position <= x_min:
            return self.bx_b_values[self.bx_x_values.index(x_min)]
        if x_position >= x_max:
            return self.bx_b_values[self.bx_x_values.index(x_max)]

        for i in range(len(self.bx_x_values) - 1):
            x1 = self.bx_x_values[i]
            x2 = self.bx_x_values[i + 1]
            if x1 <= x_position <= x2:
                y1 = self.bx_b_values[i]
                y2 = self.bx_b_values[i + 1]
                t = (x_position - x1) / (x2 - x1) if (x2 - x1) != 0 else 0
                return y1 + t * (y2 - y1)

        return self.bx_b_values[0] if self.bx_b_values else 250.0

    def init_sample_br_with_error(self):
        """初始化样品剩磁 - 直接在 -15 到 -40 mT 随机生成"""
        # 生成随机偏移 (-2mT ~ 2mT) - 不衰减
        self.random_offset = random.uniform(-2.0, 2.0)
        
        for sample_key, params in self.SAMPLE_PARAMS.items():
            # 直接在 -20 到 -40 mT 随机生成剩磁（取负值）
            base_remanence = random.uniform(-40.0, -20.0)
            self.sample_br_with_error[sample_key] = base_remanence
            self.sample_br_initial[sample_key] = base_remanence   # 保存初始值
            
            # 显示用剩磁（基础剩磁 + 随机偏移）
            displayed_remanence = base_remanence + self.random_offset
            
            print(f"{params['name']} 基础剩磁: {base_remanence:.2f} mT, 显示含偏移: {displayed_remanence:.2f} mT")
        
        print(f"随机偏移(不衰减): {self.random_offset:.2f}mT")

    # ==================== 物理模型 ====================
    def poly_upper(self, I):
        """上支曲线（下降支）- 根据样品选择不同的多项式"""
        if self.selected_sample == 'mold_steel':
            return float(np.polyval(self.POLY_UPPER_MOLD, I))
        else:
            return float(np.polyval(self.POLY_UPPER_IRON, I))

    def poly_lower(self, I):
        """下支曲线（上升支）- 根据样品选择不同的多项式"""
        if self.selected_sample == 'mold_steel':
            return float(np.polyval(self.POLY_LOWER_MOLD, I))
        else:
            return float(np.polyval(self.POLY_LOWER_IRON, I))

    def poly_virgin(self, I):
        """初始磁化曲线 - 确保从0开始单调上升"""
        if abs(I) < 1.0:
            return 0.0
        # 计算原始值
        val = float(np.polyval(self.POLY_VIRGIN, abs(I))) * (1 if I >= 0 else -1)
        # 对于小电流，如果为负值，强制为正（物理上磁化曲线从0开始单调上升）
        if abs(I) < 200 and val < 0:
            # 使用线性近似：从0线性上升到50mA处的值
            if I >= 0:
                return abs(I) * 0.02  # 简单线性近似
            else:
                return -abs(I) * 0.02
        return val

    def get_position_coupling(self, position_mm):
        """获取位置耦合系数"""
        if self.UNIFORM_MIN <= position_mm <= self.UNIFORM_MAX:
            for i, (x, b) in enumerate(self.POSITION_DATA):
                if abs(x - position_mm) < 0.01:
                    return b / 161.7
                elif i > 0 and self.POSITION_DATA[i-1][0] < position_mm < x:
                    x0, b0 = self.POSITION_DATA[i-1]
                    x1, b1 = x, b
                    t = (position_mm - x0) / (x1 - x0) if (x1 - x0) != 0 else 0
                    return (b0 + t * (b1 - b0)) / 161.7
            return 1.0

        if position_mm < self.UNIFORM_MIN:
            if position_mm <= -15.0:
                return 0.0
            t = (position_mm - self.UNIFORM_MIN) / (-15.0 - self.UNIFORM_MIN)
            return max(0.0, 1.0 * (1.0 - t))

        if position_mm > self.UNIFORM_MAX:
            if position_mm >= 15.0:
                return 0.0
            for i, (x, b) in enumerate(self.POSITION_DATA):
                if abs(x - position_mm) < 0.01:
                    return b / 161.7
                elif i > 0 and self.POSITION_DATA[i-1][0] < position_mm < x:
                    x0, b0 = self.POSITION_DATA[i-1]
                    x1, b1 = x, b
                    t = (position_mm - x0) / (x1 - x0) if (x1 - x0) != 0 else 0
                    return (b0 + t * (b1 - b0)) / 161.7
            delta = 15.0 - position_mm
            return (delta / 8.0) ** 2

        return 1.0

    def get_B_from_model(self, I_mA):
        """基于实测数据拟合的磁滞模型"""
        I_SAT = 600.0
        dI = I_mA - self._hyst_last_I

        if abs(dI) < 0.5:
            return self._hyst_last_B

        new_direction = 1 if dI > 0 else -1
        abs_I = abs(I_mA)

        if abs_I > self._hyst_max_amp:
            self._hyst_max_amp = abs_I
            self._hyst_loop_amp = abs_I

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

        if self._hyst_branch == 'virgin':
            B_new = self.poly_virgin(I_mA)
        else:
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

        B_upper = self.poly_upper(I_mA) * self._B_scale_factor
        B_lower = self.poly_lower(I_mA) * self._B_scale_factor
        B_new = np.clip(B_new, min(B_lower, B_upper), max(B_upper, B_lower))

        self._hyst_last_I = I_mA
        self._hyst_last_B = B_new

        return B_new

    def reset_hysteresis_state(self):
        """重置磁滞状态"""
        self._hyst_branch = 'virgin'
        self._hyst_last_I = 0.0
        # 使用当前样品的基础剩磁作为初始值
        br = self.sample_br_with_error.get(self.selected_sample, 0) if self.selected_sample else 0
        self._hyst_last_B = br
        self._hyst_direction = 0
        self._hyst_turn_points = []
        self._hyst_loop_amp = 600.0
        self._hyst_max_amp = 0.0
        self._hyst_exceed_error = False

    def calculate_magnetic_field(self, I_mA, position_mm, ambient_offset=0, use_hysteresis=False):
        """
        计算磁场强度
        
        毫特计值 = 基础剩磁×位置衰减 + 随机偏移(不衰减) + 用户调零偏移
        """
        # 1. 使用磁滞模型计算B值（基础剩磁）
        if use_hysteresis:
            B_raw = self.get_B_from_model(I_mA)
        else:
            # 使用磁滞回线模型
            B_raw = self.get_B_from_magnetic_model(I_mA)

        # 2. 位置衰减因子：±8mm内不衰减，超出后指数衰减到0
        position_factor = self.get_remanence_position_factor(position_mm)
        
        # 基础磁场随位置衰减
        B_positioned = B_raw * position_factor

        # 3. 随机偏移（不衰减，始终存在）+ 用户调零偏移
        B_final = B_positioned + self.random_offset + ambient_offset

        return B_final

    def get_remanence_position_factor(self, position_mm):
        """
        计算剩磁随位置变化的衰减因子（指数衰减，速度逐渐变缓）
        
        位置在 -8 到 +8 之间：不衰减（因子为1.0）
        位置超出 ±8 范围：开始指数衰减，到 ±20 时衰减到 0
        """
        abs_pos = abs(position_mm)
        
        # 在 -8 到 +8 之间：不衰减
        if abs_pos <= 8:
            return 1.0
        # 超出 ±8：指数衰减，从8mm到20mm
        elif abs_pos <= 20:
            # 从8mm开始衰减，到20mm衰减到0
            # 使用指数衰减：factor = exp(-k * (x - 8))
            # 当 x=20 时，factor ≈ 0.01，然后截断到0
            k = 0.5  # 衰减系数，控制衰减速度
            factor = np.exp(-k * (abs_pos - 8))
            # 确保在20mm处接近0
            return max(0.0, factor)
        else:
            # 超过20mm，衰减到0
            return 0.0
    
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

        br = self.sample_br_with_error.get(self.selected_sample, 0) if self.selected_sample else 0

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

        # ===== virgin分支 =====
        if self._hyst_branch == 'virgin':
            if abs_I < 1.0:
                B_new = br
            else:
                B_virgin_from_zero = self.poly_virgin(I_mA) * self._B_scale_factor
                B_target = br + B_virgin_from_zero
                
                transition_end = 50.0
                if abs_I < transition_end:
                    progress = abs_I / transition_end
                    smooth_progress = 3 * progress**2 - 2 * progress**3
                    B_new = br + (B_target - br) * smooth_progress
                else:
                    B_new = B_target
            
            B_upper = self.poly_upper(I_mA) * self._B_scale_factor
            B_lower = self.poly_lower(I_mA) * self._B_scale_factor
            B_new = np.clip(B_new, min(B_lower, B_upper), max(B_upper, B_lower))

            self._hyst_last_I = I_mA
            self._hyst_last_B = B_new
            return B_new

        # ===== 主回线分支（upper/lower） =====
        scale = amp / I_SAT
        I_scaled = np.clip(I_mA / scale, -I_SAT, I_SAT)

        if self._hyst_branch == 'upper':
            B_boundary = self.poly_upper(I_scaled) * self._B_scale_factor * scale
        else:
            B_boundary = self.poly_lower(I_scaled) * self._B_scale_factor * scale

        if self._hyst_turn_points:
            turn_I_scaled = turn_I / scale if scale > 0.01 else 0
            turn_I_scaled = np.clip(turn_I_scaled, -I_SAT, I_SAT)

            if self._hyst_branch == 'upper':
                B_boundary_at_turn = self.poly_upper(turn_I_scaled) * self._B_scale_factor * scale
            else:
                B_boundary_at_turn = self.poly_lower(turn_I_scaled) * self._B_scale_factor * scale

            offset = turn_B - B_boundary_at_turn
            travel = abs(I_mA - turn_I)
            offset_factor = np.exp(-0.005 * travel)
            B_new = B_boundary + offset * offset_factor
        else:
            B_new = B_boundary

        # ============================================================
        # ===== 新增：过零后斜率变为2倍（仅模具钢） =====
        # ============================================================
        sample_type = self.selected_sample
        
        # 只对模具钢应用2倍斜率
        if sample_type == 'mold_steel':
            # 判断是否跨过零点
            prev_I = self._hyst_last_I
            crossed_zero = (prev_I * I_mA < 0) or (abs(prev_I) < 1 and abs_I > 1)
            
            if crossed_zero and abs_I < 100:
                # 计算零点处的B值（在当前回线上）
                I_600_zero = 0
                if self._hyst_branch == 'upper':
                    B_600_zero = self.poly_upper(0) * self._B_scale_factor * scale
                    B_600_current = self.poly_upper(I_scaled) * self._B_scale_factor * scale
                else:
                    B_600_zero = self.poly_lower(0) * self._B_scale_factor * scale
                    B_600_current = self.poly_lower(I_scaled) * self._B_scale_factor * scale
                
                # 考虑偏移
                B_zero = B_600_zero
                if self._hyst_turn_points:
                    # 计算转折点对应的零点B值
                    if self._hyst_branch == 'upper':
                        B_turn_zero = self.poly_upper(0) * self._B_scale_factor * scale
                    else:
                        B_turn_zero = self.poly_lower(0) * self._B_scale_factor * scale
                    offset_at_zero = turn_B - B_turn_zero
                    B_zero = B_zero + offset_at_zero
                
                # 标准斜率（从零点到当前点）
                std_slope = (B_600_current - B_600_zero) / abs_I if abs_I > 1 else 0
                
                # 用2倍斜率从零点开始计算
                sign = 1 if I_mA > 0 else -1
                B_new_calculated = B_zero + std_slope * 2.0 * abs_I * sign
                
                # 限制不能超过原B值太多
                if abs(B_new_calculated) < abs(B_new) * 1.5:
                    B_new = B_new_calculated

        # ============================================================

        # 边界限制
        B_upper = self.poly_upper(I_mA) * self._B_scale_factor
        B_lower = self.poly_lower(I_mA) * self._B_scale_factor
        B_new = np.clip(B_new, min(B_lower, B_upper), max(B_upper, B_lower))

        self._hyst_last_I = I_mA
        self._hyst_last_B = B_new

        return B_new

    def physical_I_to_H(self, I_mA):
        """电流转磁场强度 H = N*I/L"""
        I_A = I_mA / 1000.0
        N = 2000
        L = 0.238
        return (N * I_A) / L

    # ==================== UI创建 ====================
    def create_ui(self):
        """创建UI界面"""
        self.create_main_layout()
        self.create_left_area()
        self.create_right_top_area()
        self.create_right_bottom_area()

    def create_main_layout(self):
        """创建主布局"""
        main_content = tk.Frame(self.main_frame)
        main_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.left_frame = tk.Frame(main_content, width=400, bg='white')
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))

        right_frame = tk.Frame(main_content)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.right_top_frame = tk.Frame(right_frame, height=180, bg='lightyellow')
        self.right_top_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.right_bottom_frame = tk.Frame(right_frame, bg='white')
        self.right_bottom_frame.pack(fill=tk.BOTH, expand=True)

    def create_left_area(self):
        """创建左侧实验装置区域"""
        self.canvas = tk.Canvas(self.left_frame, width=680, height=700, bg='white')
        self.canvas.pack()

        try:
            hall_img_path = resource_path("background/霍尔效应.jpg")
            pil_hall = Image.open(hall_img_path)
            pil_hall = pil_hall.resize((680, 700), Image.Resampling.LANCZOS)
            self.hall_image = ImageTk.PhotoImage(pil_hall)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.hall_image)
        except Exception as e:
            print(f"无法加载霍尔效应图片: {e}")
            self.canvas.create_rectangle(0, 0, 680, 700, fill='lightgray')
            self.canvas.create_text(340, 350, text="霍尔效应图片加载失败", font=("Arial", 14))

        self.create_textboxes_on_image()

        self.hall_element_x = 153
        self.hall_element_y = 367
        self.hall_element_length = 260
        self.canvas.create_line(self.hall_element_x, self.hall_element_y,
                            self.hall_element_x + self.hall_element_length, self.hall_element_y,
                            fill='red', width=3, tags="hall_element")
        
        # ===== 创建箭头指示标签 =====
        self.create_arrow_indicators()

    def create_arrow_indicators(self):
        """在图片上创建箭头指示标签"""
        
        # ===== 1. 实验指示箭头（固定向左） =====
        # 位置：在图片右侧空白区域
        self.arrow_experiment = self.canvas.create_text(
            160, 610,          # 位置在图片右侧
            text="←",          # 固定向左
            font=("Arial", 32, "bold"),
            fill="#FF6B00",    # 橙色
            tags="arrow_experiment"
        )
        
        # ===== 2. 励磁电流方向指示 =====
        # 位置：电流表附近，显示向左或向右的箭头
        self.arrow_excitation = self.canvas.create_text(
            80, 295,         # 电流表下方位置
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
                if self.current_direction == 1:
                    # 正向 → 显示向左的箭头（电流从左向右流）
                    self.canvas.itemconfig(self.arrow_excitation, text="←")
                else:
                    # 反向 → 显示向右的箭头（电流从右向左流）
                    self.canvas.itemconfig(self.arrow_excitation, text="→")
            
            # 实验指示箭头固定向左，不需要更新
                    
        except (tk.TclError, RuntimeError):
            # 箭头可能还未创建，忽略错误
            pass

    def create_textboxes_on_image(self):
        """在图片上创建文本框"""
        self.current_var = tk.StringVar(value="0")
        current_entry = tk.Entry(self.left_frame, textvariable=self.current_var,
                                width=8, font=("Arial", 10), justify='center',
                                state='readonly', readonlybackground='white')
        self.canvas.create_window(265, 535, window=current_entry, anchor=tk.NW)

        self.millitesla_var = tk.StringVar(value="—")
        self.millitesla_entry = tk.Entry(self.left_frame, textvariable=self.millitesla_var,
                                    width=8, font=("Arial", 10), justify='center',
                                    state='readonly', readonlybackground='white')
        self.canvas.create_window(410, 535, window=self.millitesla_entry, anchor=tk.NW)

    def create_hold_button(self, parent, text, command, repeat_delay=300, repeat_interval=50):
        """创建支持长按的按钮"""
        button = tk.Button(parent, text=text, width=2)

        def on_press(event):
            # ===== 检查按钮是否被禁用 =====
            if button['state'] == tk.DISABLED:
                return
            command()
            self.cancel_hold_timer()
            self.hold_timer = self.root.after(repeat_delay, lambda: self.start_repeat(command, repeat_interval))

        def on_release(event):
            # ===== 检查按钮是否被禁用 =====
            if button['state'] == tk.DISABLED:
                return
            self.cancel_hold_timer()

        button.bind("<ButtonPress-1>", on_press)
        button.bind("<ButtonRelease-1>", on_release)
        button.bind("<Leave>", on_release)
        return button

    def cancel_hold_timer(self):
        if self.hold_timer is not None:
            self.root.after_cancel(self.hold_timer)
            self.hold_timer = None

    def start_repeat(self, command, interval):
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
        self.control_widgets.append(self.position_scale)
        
        self.btn_minus_pos = self.create_hold_button(pos_frame, "-", lambda: self.adjust_position(-1))
        self.btn_minus_pos.pack(side=tk.LEFT, padx=1)
        self.control_widgets.append(self.btn_minus_pos)
        
        self.btn_plus_pos = self.create_hold_button(pos_frame, "+", lambda: self.adjust_position(1))
        self.btn_plus_pos.pack(side=tk.LEFT, padx=1)
        self.control_widgets.append(self.btn_plus_pos)

        # 第2行：励磁电流
        current_frame = tk.Frame(main_frame, bg='lightyellow')
        current_frame.grid(row=1, column=0, padx=10, pady=5, sticky='w')
        tk.Label(current_frame, text="励磁电流(mA):", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.excitation_scale = tk.Scale(current_frame, from_=0, to=600, orient=tk.HORIZONTAL,
                                        length=200, command=self.update_excitation_current)
        self.excitation_scale.pack(side=tk.LEFT, padx=5)
        self.control_widgets.append(self.excitation_scale)
        
        # ===== 保存为实例变量 =====
        self.btn_minus_cur = self.create_hold_button(current_frame, "-", lambda: self.adjust_excitation(-1))
        self.btn_minus_cur.pack(side=tk.LEFT, padx=1)
        self.control_widgets.append(self.btn_minus_cur)
        
        self.btn_plus_cur = self.create_hold_button(current_frame, "+", lambda: self.adjust_excitation(1))
        self.btn_plus_cur.pack(side=tk.LEFT, padx=1)
        self.control_widgets.append(self.btn_plus_cur)

        self.direction_btn = tk.Button(current_frame, text="正向",
                                    command=self.toggle_direction,
                                    width=6, bg='lightblue')
        self.direction_btn.pack(side=tk.LEFT, padx=10)
        self.control_widgets.append(self.direction_btn)

        # 第2行第2列：毫特计调零
        moff_frame = tk.Frame(main_frame, bg='lightyellow')
        moff_frame.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        tk.Label(moff_frame, text="毫特计调零(mT):", bg='lightyellow',
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.millitesla_offset_scale = tk.Scale(moff_frame, from_=-50, to=50, orient=tk.HORIZONTAL,
                                            length=200, resolution=0.1, showvalue=0,
                                            command=self.update_millitesla_offset)
        self.millitesla_offset_scale.pack(side=tk.LEFT, padx=5)
        self.control_widgets.append(self.millitesla_offset_scale)
        
        self.btn_minus_moff = self.create_hold_button(moff_frame, "-", lambda: self.adjust_millitesla_offset(-0.1))
        self.btn_minus_moff.pack(side=tk.LEFT, padx=1)
        self.control_widgets.append(self.btn_minus_moff)
        
        self.btn_plus_moff = self.create_hold_button(moff_frame, "+", lambda: self.adjust_millitesla_offset(0.1))
        self.btn_plus_moff.pack(side=tk.LEFT, padx=1)
        self.control_widgets.append(self.btn_plus_moff)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

    def create_right_bottom_area(self):
        """创建右下数据记录区域"""
        # 阶段控制
        stage_frame = tk.Frame(self.right_bottom_frame, bg='lightgray')
        stage_frame.pack(fill=tk.X, padx=5, pady=5)

        self.stage_buttons = {}
        stage_names = [("样品选择", 0), ("B-X关系", 1), ("退磁", 2), ("磁滞回线", 3)]

        for name, idx in stage_names:
            btn = tk.Button(stage_frame, text=name, command=lambda i=idx: self.switch_stage(i),
                           width=10)
            btn.pack(side=tk.LEFT, padx=2)
            self.stage_buttons[idx] = btn

        self.stage_info_label = tk.Label(stage_frame, text="", bg='lightgray', font=("Arial", 9))
        self.stage_info_label.pack(side=tk.LEFT, padx=10)

        # 内容框架
        self.content_frame = tk.Frame(self.right_bottom_frame, bg='white')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 默认显示样品选择
        self.switch_stage(0)

    def switch_stage(self, stage):
        """切换实验阶段"""
        # 如果正在退磁，先停止
        if self.is_demagnetizing:
            self.is_demagnetizing = False
            if hasattr(self, '_degauss_timer'):
                try:
                    self.root.after_cancel(self._degauss_timer)
                except:
                    pass
                self._degauss_timer = None
            if hasattr(self, 'demag_btn'):
                try:
                    self.demag_btn.config(state='normal', text="自动退磁")
                except:
                    pass
            if hasattr(self, 'demag_status_label'):
                try:
                    self.demag_status_label.config(text="已停止", fg='orange')
                except:
                    pass
        
        # 保存当前样品的磁滞状态
        self._save_current_hyst_state()
        
        # 检查是否已选择样品（阶段0除外）
        if stage != 0 and self.selected_sample is None:
            messagebox.showwarning("警告", "请先在样品选择界面选择样品！")
            stage = 0
        
        # 进入退磁或磁滞回线界面需要先调零（仅第一次进入退磁界面时检查）
        if stage == 2 and self._first_enter_degauss:
            # if self.excitation_current != 0:
            #     messagebox.showwarning("警告", "请先将励磁电流调为0！")
            #     return
            try:
                current_display = float(self.millitesla_var.get().replace("—", "0"))
                if abs(current_display) > 0.2:
                    messagebox.showwarning("警告", f"请先调零！当前毫特计显示: {current_display:.1f}mT")
                    return
            except:
                pass
            self._first_enter_degauss = False
        elif stage == 2 and not self._first_enter_degauss:
            pass
        
        if stage == 3 and self._first_enter_degauss:
            # if self.excitation_current != 0:
            #     messagebox.showwarning("警告", "请先将励磁电流调为0！")
            #     return
            try:
                current_display = float(self.millitesla_var.get().replace("—", "0"))
                if abs(current_display) > 0.5:
                    messagebox.showwarning("警告", f"请先调零！当前毫特计显示: {current_display:.1f}mT")
                    return
            except:
                pass
        elif stage == 3 and not self._first_enter_degauss:
            pass
        

        # ===== 根据阶段启用/禁用控件 =====
        if stage == 2:  # 退磁界面
            # 禁用所有控件
            self._set_controls_state('disabled')
            # ===== 励磁电流相关控件保持可用 =====
            # 励磁电流进度条
            try:
                self.excitation_scale.config(state='normal')
            except:
                pass
            # 励磁电流微调按钮（- 和 +）
            if hasattr(self, 'btn_minus_cur'):
                try:
                    self.btn_minus_cur.config(state='normal')
                except:
                    pass
            if hasattr(self, 'btn_plus_cur'):
                try:
                    self.btn_plus_cur.config(state='normal')
                except:
                    pass
            # 方向按钮
            try:
                self.direction_btn.config(state='normal')
            except:
                pass
        else:
            self._set_controls_state('normal')
        
        # 更新按钮高亮
        for idx, btn in self.stage_buttons.items():
            btn.config(bg='lightblue' if idx == stage else 'SystemButtonFace')

        # 清空内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if stage == 0:
            self._create_sample_select_ui()
            self.current_display = "sample_select"
        elif stage == 1:
            self._create_bx_ui()
            self.current_display = "bx_relation"
        elif stage == 2:
            self._create_demagnetize_ui()
            self.current_display = "demagnetize"
        elif stage == 3:
            self._create_hysteresis_ui()
            self.current_display = "hysteresis"

        self.stage_info_label.config(text=["选择实验样品", "测量B-X关系", "退磁处理", "测量磁滞回线"][stage])

    # ==================== 样品选择界面 ====================
    def _create_sample_select_ui(self):
        """创建样品选择界面"""
        content_frame = self.content_frame

        tk.Label(content_frame, text="请选择实验样品：", font=("Arial", 14, "bold"),
                bg='white').pack(pady=10)

        btn_frame = tk.Frame(content_frame, bg='white')
        btn_frame.pack(pady=10)

        self.btn_mold_steel = tk.Button(btn_frame, text="模具钢\n(半硬磁材料)",
                                        command=lambda: self._select_sample('mold_steel'),
                                        width=15, height=3, font=("Arial", 12))
        self.btn_mold_steel.pack(side=tk.LEFT, padx=20)

        self.btn_pure_iron = tk.Button(btn_frame, text="电工纯铁\n(软磁材料)",
                                    command=lambda: self._select_sample('pure_iron'),
                                    width=15, height=3, font=("Arial", 12))
        self.btn_pure_iron.pack(side=tk.LEFT, padx=20)

        # 参数显示
        self.params_frame = tk.Frame(content_frame, bg='lightgray', relief=tk.RIDGE, bd=2)
        self.params_frame.pack(pady=10, padx=20, fill=tk.X)

        self.params_labels = {}
        # ===== 删除了 'Bs_mT', 'Hc_Am', 'Br_mT' =====
        param_names = [
            ('name', '样品名称'), 
            ('type', '材料类型'),
            ('l_bar_cm', '平均磁路长度'),
            ('l_gap_cm', '间隙宽度'), 
            ('N', '线圈匝数'),
            ('section_cm2', '截面积'), 
            ('description', '特点')
        ]

        for i, (key, label_text) in enumerate(param_names):
            row = i // 2
            col = i % 2
            frame = tk.Frame(self.params_frame, bg='lightgray')
            frame.grid(row=row, column=col, padx=20, pady=3, sticky='w')
            tk.Label(frame, text=f"{label_text}:", font=("Arial", 9),
                    bg='lightgray').pack(side=tk.LEFT)
            self.params_labels[key] = tk.Label(frame, text="--", font=("Arial", 9, "bold"),
                                            fg='blue', bg='lightgray')
            self.params_labels[key].pack(side=tk.LEFT, padx=5)

        # 恢复之前选择的样品状态
        self._restore_sample_selection()

    def _restore_sample_selection(self):
        """恢复之前选择的样品状态"""
        if self.selected_sample is not None:
            # 更新按钮高亮
            self.btn_mold_steel.config(bg='lightblue' if self.selected_sample == 'mold_steel' else 'SystemButtonFace')
            self.btn_pure_iron.config(bg='lightblue' if self.selected_sample == 'pure_iron' else 'SystemButtonFace')
            
            # 更新参数显示
            params = self.SAMPLE_PARAMS.get(self.selected_sample, {})
            self._update_params_display(params)
            
            # 恢复B值缩放因子
            if self.selected_sample == 'mold_steel':
                self._B_scale_factor = 1.0
            else:
                self._B_scale_factor = 800.0 / 315.0
            
            # 更新毫特计显示
            self.update_millitesla_display()
            print(f"恢复样品选择: {params.get('name', self.selected_sample)}")

    def start_demagnetize(self):
        """开始自动退磁 - 每个样品独立"""
        if self.is_demagnetizing:
            return
        
        sample_type = self.selected_sample
        if sample_type is None:
            messagebox.showwarning("警告", "请先选择样品！")
            return
        
        # 检查该样品是否已经退磁过
        if self.demagnetize_complete.get(sample_type, False):
            # 该样品已退磁过，从(0,0)开始
            self.demag_data = []
            self.demag_step = 0
            self.current_direction = 1
            # 重置磁滞状态到0（不使用剩磁）
            self.reset_hysteresis_state(use_remanence=False)
            self._hyst_turn_points = []
            start_B = 0.0
        else:
            # 该样品首次退磁，从剩磁开始
            self.demag_data = []
            self.demag_step = 0
            self.current_direction = 1
            # 重置磁滞状态，使用当前剩磁
            self.reset_hysteresis_state(use_remanence=True)
            br = self.sample_br_with_error.get(sample_type, 0)
            start_B = br + self.random_offset
        
        self.is_demagnetizing = True
        self.demag_btn.config(state='disabled', text="退磁中...")
        self.demag_status_label.config(text="退磁进行中...", fg='orange')
        
        # 添加起点
        self.demag_data.append((0, start_B))
        self._update_demag_ui(0, start_B)

        # 清空并重新设置曲线图
        self.demag_ax.clear()
        self.demag_ax.set_xlabel('H (A/m)')
        self.demag_ax.set_ylabel('B (mT)')
        self.demag_ax.set_title('退磁曲线')
        self.demag_ax.grid(True)
        self.demag_ax.set_xlim(-7000, 7000)
        self.demag_ax.set_ylim(-400, 400)
        self.demag_ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        self.demag_ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        
        # 标记起点
        self.demag_ax.scatter(0, start_B, color='green', s=50, label='起点')
        self.demag_ax.legend()
        self.demag_canvas.draw()

        self._degauss_timer = self.root.after(50, self._demagnetize_step)

    def _select_sample(self, sample_type):
        """选择样品 - 切换时保存当前状态，加载目标状态"""
        # 保存当前样品的磁滞状态
        self._save_current_hyst_state()
        
        self.selected_sample = sample_type
        params = self.SAMPLE_PARAMS.get(sample_type, {})
        self._update_params_display(params)

        # ===== 根据样品类型设置B值缩放因子 =====
        if sample_type == 'mold_steel':
            self._B_scale_factor = 1.0
            # 模具钢使用原始多项式（宽回线）
            # poly_upper/poly_lower 会根据 selected_sample 自动选择
        else:
            self._B_scale_factor = 800.0 / 315.0
            # 纯铁使用缩小后的多项式（窄回线）

        # 加载目标样品的磁滞状态
        self._load_hyst_state(sample_type)
        
        # 如果加载的状态中 last_B 为0，使用剩磁初始化
        if abs(self._hyst_last_B) < 0.01:
            br = self.sample_br_with_error.get(sample_type, 0)
            self._hyst_last_B = br
            self._hyst_branch = 'virgin'
            self._hyst_last_I = 0.0
            self._hyst_turn_points = []
        
        # 重置回线形状参数
        self._hyst_loop_amp = 600.0
        self._hyst_max_amp = 0.0
        self._hyst_exceed_error = False

        # # 切换样品时重置第一次进入退磁界面的标记
        # self._first_enter_degauss = True

        # 更新按钮高亮
        self.btn_mold_steel.config(bg='lightblue' if sample_type == 'mold_steel' else 'SystemButtonFace')
        self.btn_pure_iron.config(bg='lightblue' if sample_type == 'pure_iron' else 'SystemButtonFace')

        self.update_millitesla_display()
        
    def _update_params_display(self, params):
        """更新参数显示"""
        if params is None:
            for key in self.params_labels:
                self.params_labels[key].config(text="--")
            return

        for key in self.params_labels:
            value = params.get(key, "--")
            if key == 'description':
                self.params_labels[key].config(text=value, font=("Arial", 8, "italic"), fg='gray')
            elif isinstance(value, (int, float)):
                if key == 'N':
                    self.params_labels[key].config(text=f"{value} 匝")
                elif key in ['l_bar_cm', 'l_gap_cm']:
                    self.params_labels[key].config(text=f"{value} cm")
                elif key == 'section_cm2':
                    self.params_labels[key].config(text=f"{value} cm²")
                else:
                    self.params_labels[key].config(text=str(value))
            else:
                self.params_labels[key].config(text=value)

    # ==================== B-X关系界面 ====================
    def _create_bx_ui(self):
        """创建B-X关系界面"""
        # 确保已选择样品
        if self.selected_sample is None:
            messagebox.showwarning("警告", "请先在样品选择界面选择样品！")
            self.switch_stage(0)
            return
        
        # 强制初始化磁滞状态
        self.reset_hysteresis_state(use_remanence=True)

        content_frame = self.content_frame


        main_container = tk.Frame(content_frame, bg='white')
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ===== 按钮框架（移到曲线图下方） =====
        btn_frame = tk.Frame(main_container, bg='white')
        btn_frame.pack(pady=10)

        buttons = [
            ("记录数据", self.on_record_current),
            ("删除选中行", self.on_delete_row),
            ("清空数据", self.on_clear_table),
            ("导出数据", self.on_export_csv),
            ("导入数据", self.on_import_bx_csv)
        ]

        for text, command in buttons:
            btn = tk.Button(btn_frame, text=text, command=command,
                          width=11, bg='lightblue')  # 全部改为 lightblue
            btn.pack(side=tk.LEFT, padx=3)
            
        # 表格区域
        table_frame = tk.Frame(main_container, bg='white')
        table_frame.pack(fill=tk.X, pady=(0, 5))

        # 表格和滚动条容器
        table_container = tk.Frame(table_frame, bg='white')
        table_container.pack(fill=tk.X, pady=2)

        self.bx_table = ttk.Treeview(table_container, columns=('X/mm', 'B/mT'), show='headings', height=6)
        self.bx_table.heading('X/mm', text='X/mm')
        self.bx_table.heading('B/mT', text='B/mT')
        self.bx_table.column('X/mm', width=100, anchor='center')
        self.bx_table.column('B/mT', width=120, anchor='center')
        self.bx_table.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 滚动条在表格右边
        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.bx_table.yview)
        self.bx_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 曲线图（放在按钮上方）
        plot_frame = tk.Frame(main_container, bg='white')
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.bx_fig, self.bx_ax = plt.subplots(figsize=(5, 3.5))
        self.bx_fig.subplots_adjust(bottom=0.18, left=0.12, right=0.95, top=0.92)
        
        self.bx_canvas = FigureCanvasTkAgg(self.bx_fig, master=plot_frame)
        self.bx_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.bx_ax.set_xlabel('X (mm)', fontsize=10)
        self.bx_ax.set_ylabel('B (mT)', fontsize=10)
        self.bx_ax.set_title('B-X关系曲线', fontsize=11)
        self.bx_ax.grid(True)
        self.bx_ax.set_xlim(-25, 25)
        self.bx_ax.set_ylim(-10, 10)

        

        self._refresh_table('A')
        self._update_bx_plot()

    # ==================== 退磁界面 ====================
    def _create_demagnetize_ui(self):
        """创建退磁界面"""
        # 确保已选择样品
        if self.selected_sample is None:
            messagebox.showwarning("警告", "请先在样品选择界面选择样品！")
            self.switch_stage(0)
            return
        
        content_frame = self.content_frame

        btn_frame = tk.Frame(content_frame, bg='white')
        btn_frame.pack(pady=10)

        self.demag_btn = tk.Button(btn_frame, text="自动退磁", command=self.start_demagnetize,
                                width=15, height=2, bg='orange', font=("Arial", 12))
        self.demag_btn.pack(side=tk.LEFT, padx=10)

        self.demag_status_label = tk.Label(btn_frame, text="就绪", font=("Arial", 10),
                                        fg='green', bg='white')
        self.demag_status_label.pack(side=tk.LEFT, padx=10)

        # 退磁曲线图
        plot_frame = tk.Frame(content_frame, bg='white')
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.demag_fig, self.demag_ax = plt.subplots(figsize=(5, 3.5))
        self.demag_canvas = FigureCanvasTkAgg(self.demag_fig, master=plot_frame)
        self.demag_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.demag_ax.set_xlabel('H (A/m)')
        self.demag_ax.set_ylabel('B (mT)')
        self.demag_ax.set_title('退磁曲线')
        self.demag_ax.grid(True)
        self.demag_ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        self.demag_ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        
        # ===== 恢复退磁数据（如果有），自适应显示范围 =====
        if self.demag_data:
            h_data = [d[0] * 10 for d in self.demag_data]  # I(mA) * 10 ≈ H(A/m)
            b_data = [d[1] for d in self.demag_data]
            
            # 计算数据范围
            h_min, h_max = min(h_data), max(h_data)
            b_min, b_max = min(b_data), max(b_data)
            
            # 计算边距：至少保留15%的边距，且不小于500和20
            h_range = h_max - h_min
            b_range = b_max - b_min
            h_margin = max(500, h_range * 0.15)
            b_margin = max(20, b_range * 0.15)
            
            # 确保包含原点(0,0)
            h_min = min(h_min, 0) - h_margin
            h_max = max(h_max, 0) + h_margin
            b_min = min(b_min, 0) - b_margin
            b_max = max(b_max, 0) + b_margin
            
            # 设置显示范围
            self.demag_ax.set_xlim(h_min, h_max)
            self.demag_ax.set_ylim(b_min, b_max)
            
            # 绘制退磁曲线
            self.demag_ax.plot(h_data, b_data, 'b-', linewidth=1.5, alpha=0.8)
            
            # 标记起点（绿色）
            if len(h_data) > 0:
                self.demag_ax.scatter(h_data[0], b_data[0], color='green', s=40, label='起点')
            
            # 标记当前点（红色）
            self.demag_ax.scatter(h_data[-1], b_data[-1], color='red', s=30, label='当前点')
            
            # 标记原点（灰色十字）
            self.demag_ax.scatter(0, 0, color='gray', marker='+', s=100, linewidths=2)
            
            self.demag_ax.legend(loc='upper right', fontsize=8)
        else:
            # 没有数据时使用默认范围
            self.demag_ax.set_xlim(-7000, 7000)
            self.demag_ax.set_ylim(-400, 400)
        
        self.demag_canvas.draw()

    def reset_hysteresis_state(self, use_remanence=True):
        """
        重置磁滞状态
        
        Parameters:
            use_remanence: 是否使用基础剩磁作为初始值
                        True: 使用当前样品的基础剩磁
                        False: 使用0（用于已退磁状态）
        """
        self._hyst_branch = 'virgin'
        self._hyst_last_I = 0.0
        self._hyst_turn_points = []  # 清空转折点
        
        if use_remanence:
            br = self.sample_br_with_error.get(self.selected_sample, 0) if self.selected_sample else 0
            self._hyst_last_B = br
        else:
            self._hyst_last_B = 0.0
        
        self._hyst_direction = 0
        self._hyst_loop_amp = 600.0
        self._hyst_max_amp = 0.0
        self._hyst_exceed_error = False

    def _is_on_hysteresis_branch(self):
        """
        判断当前是否在磁滞回线的上升支上
        
        返回 True 表示已经到达磁滞回线上升支
        """
        # 条件1：分支已经是 lower（上升支）
        if self._hyst_branch == 'lower':
            return True
        
        # 条件2：已经发生过转折（从上升变为下降）
        # 检查转折点列表中是否有记录
        if len(self._hyst_turn_points) > 0:
            # 检查最近一次转折是否是从上升变为下降
            # 如果转折点电流为正，说明到达了正峰值
            last_turn_I = self._hyst_turn_points[-1][0] if self._hyst_turn_points else 0
            if last_turn_I > 100:  # 峰值超过100mA
                return True
        
        # 条件3：当前电流较大且方向为上升，且曾经到达过峰值
        if self._hyst_direction > 0 and self._hyst_max_amp > 100:
            return True
        
        return False

    def _calculate_demag_b_value(self, current_val):
        """
        计算退磁过程中的B值（与update_millitesla_display保持一致）
        
        返回：B值（已包含随机偏移和调零偏移）
        """
        br = self.sample_br_with_error.get(self.selected_sample, 0) if self.selected_sample else 0
        is_second_degauss = self.demagnetize_complete.get(self.selected_sample, False)
        on_hysteresis = self._is_on_hysteresis_branch()
        
        current_abs = abs(current_val)
        B_target_clean = self.get_B_from_magnetic_model(current_val)
        
        if current_abs >= 150 or on_hysteresis:
            B_val = B_target_clean
        else:
            progress_in_transition = current_abs / 150.0
            smooth_progress = 3 * progress_in_transition**2 - 2 * progress_in_transition**3
            
            if is_second_degauss:
                B_val = B_target_clean * smooth_progress
            else:
                B_val = br + (B_target_clean - br) * smooth_progress
        
        # 添加随机偏移和调零偏移
        B_val = B_val + self.random_offset + self.millitesla_offset
        B_val += random.uniform(-0.3, 0.3)
        
        return B_val

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

        # 上升（从当前值到峰值）
        for i in range(1, steps + 1):
            current_val = i * step_size * polarity
            B_raw = self.get_B_from_magnetic_model(current_val)
            B_val = B_raw + self.random_offset + self.millitesla_offset
            B_val += random.uniform(-0.3, 0.3)
            self.demag_data.append((current_val, B_val))
            self._update_demag_ui(current_val, B_val)

        # 下降（从峰值到0）
        for i in range(steps - 1, -1, -1):
            current_val = i * step_size * polarity
            B_raw = self.get_B_from_magnetic_model(current_val)
            B_val = B_raw + self.random_offset + self.millitesla_offset
            B_val += random.uniform(-0.3, 0.3)
            self.demag_data.append((current_val, B_val))
            self._update_demag_ui(current_val, B_val)

        # 切换方向并更新按钮和箭头
        self.current_direction *= -1
        self.update_direction_button()
        self.update_arrows()  # ← 添加这行
        
        self.demag_step += 1
        if self.is_demagnetizing:
            self.root.after(30, self._demagnetize_step)

    def update_direction_button(self):
        """更新方向按钮的显示"""
        if hasattr(self, 'direction_btn'):
            if self.current_direction == 1:
                self.direction_btn.config(text="正向", bg='lightblue')
            else:
                self.direction_btn.config(text="反向", bg='lightcoral')

    def _update_demag_ui(self, current_val, b_val):
        """更新退磁UI"""
        # 检查控件是否存在
        if not hasattr(self, 'current_var') or not hasattr(self, 'millitesla_var'):
            return
        if not hasattr(self, 'excitation_scale'):
            return
        
        try:
            # 更新电流显示
            abs_current = abs(current_val)
            self.excitation_current = abs_current
            self.current_var.set(str(abs_current))
            
            # ===== 强制更新进度条（即使被禁用） =====
            self.excitation_scale.set(abs_current)

            # 更新毫特计显示
            self.millitesla_var.set(f"{b_val:.1f}")

            # 更新退磁曲线图
            if self.demag_data and hasattr(self, 'demag_ax') and hasattr(self, 'demag_canvas'):
                # ... 曲线更新代码保持不变 ...
                h_data = [d[0] * 10 for d in self.demag_data]
                b_data = [d[1] for d in self.demag_data]
                
                self.demag_ax.clear()
                self.demag_ax.set_xlabel('H (A/m)')
                self.demag_ax.set_ylabel('B (mT)')
                self.demag_ax.set_title('退磁曲线')
                self.demag_ax.grid(True)
                
                if h_data:
                    h_min, h_max = min(h_data), max(h_data)
                    b_min, b_max = min(b_data), max(b_data)
                    h_range = h_max - h_min
                    b_range = b_max - b_min
                    h_margin = max(500, h_range * 0.15)
                    b_margin = max(20, b_range * 0.15)
                    h_min = min(h_min, 0) - h_margin
                    h_max = max(h_max, 0) + h_margin
                    b_min = min(b_min, 0) - b_margin
                    b_max = max(b_max, 0) + b_margin
                    self.demag_ax.set_xlim(h_min, h_max)
                    self.demag_ax.set_ylim(b_min, b_max)
                else:
                    self.demag_ax.set_xlim(-7000, 7000)
                    self.demag_ax.set_ylim(-400, 400)
                
                self.demag_ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
                self.demag_ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
                self.demag_ax.plot(h_data, b_data, 'b-', linewidth=1.5, alpha=0.8)
                
                if len(h_data) > 0:
                    self.demag_ax.scatter(h_data[0], b_data[0], color='green', s=40, label='起点')
                self.demag_ax.scatter(h_data[-1], b_data[-1], color='red', s=30, label='当前点')
                self.demag_ax.scatter(0, 0, color='gray', marker='+', s=100, linewidths=2)
                self.demag_ax.legend(loc='upper right', fontsize=8)
                self.demag_canvas.draw()

            # 强制刷新UI
            self.root.update_idletasks()
            self.root.update()
            time.sleep(0.01)
        except Exception as e:
            if "invalid command name" in str(e) or "NoneType" in str(e):
                self.is_demagnetizing = False
                if hasattr(self, 'demag_btn'):
                    try:
                        self.demag_btn.config(state='normal', text="自动退磁")
                    except:
                        pass
            else:
                raise

    def _finish_demagnetize(self):
        """完成退磁 - 结束在(0,0)"""
        self.is_demagnetizing = False
        
        if hasattr(self, '_degauss_timer'):
            try:
                self.root.after_cancel(self._degauss_timer)
            except:
                pass
            self._degauss_timer = None
        
        sample_type = self.selected_sample
        
        if sample_type is not None:
            # ===== 只在退磁完成时设为0 =====
            self.sample_br_with_error[sample_type] = 0.0
            self.demagnetize_complete[sample_type] = True
        
        # 下面的代码缩进不对！应该与 if 平级，而不是在 if 内部
        self.demag_btn.config(state='normal', text="自动退磁")
        self.demag_status_label.config(text="退磁完成！", fg='green')
        # ... 其余代码

        # 电流归零
        self.excitation_current = 0
        self.current_var.set("0")
        self.excitation_scale.set(0)
        
        final_B = 0.0
        
        if self.demag_data:
            last_point = self.demag_data[-1]
            if last_point[0] != 0 or abs(last_point[1]) > 0.1:
                self.demag_data.append((0, final_B))
                self._update_demag_ui(0, final_B)
        
        self._degauss_end_B = final_B
        
        # 重置磁滞状态到0（不使用剩磁）
        self.reset_hysteresis_state(use_remanence=False)
        
        # ===== 修复：将样品的磁滞状态存储也更新为0 =====
        if sample_type is not None:
            self._hyst_state_for_sample[sample_type]['last_B'] = 0.0
            self._hyst_state_for_sample[sample_type]['branch'] = 'virgin'
            self._hyst_state_for_sample[sample_type]['last_I'] = 0.0
            self._hyst_state_for_sample[sample_type]['turn_points'] = []
        
        # 更新毫特计显示
        self.update_millitesla_display()

        sample_name = self.SAMPLE_PARAMS.get(sample_type, {}).get('name', sample_type) if sample_type else "样品"
        messagebox.showinfo("退磁完成", f"{sample_name} 退磁操作完成！")

    # ==================== 磁滞回线界面 ====================
    def _create_hysteresis_ui(self):
        """创建磁滞回线界面"""
        # 确保已选择样品
        if self.selected_sample is None:
            messagebox.showwarning("警告", "请先在样品选择界面选择样品！")
            self.switch_stage(0)
            return
        
        content_frame = self.content_frame

         # ===== 按钮框架（移到曲线图下方） =====
        btn_frame = tk.Frame(content_frame, bg='white')
        btn_frame.pack(pady=10)

        buttons = [
            ("记录数据", self.on_record_current),
            ("删除选中行", self.on_delete_row),
            ("清空数据", self.on_clear_hysteresis),
            ("导出数据", self.on_export_hysteresis_csv),
            ("导入数据", self.on_import_hysteresis_csv)
        ]

        for text, command in buttons:
            btn = tk.Button(btn_frame, text=text, command=command,
                          width=12, bg='lightblue')  # 全部改为 lightblue
            btn.pack(side=tk.LEFT, padx=5)

        # 状态标签放在按钮右侧
        self.hyst_status_label = tk.Label(btn_frame, text="就绪", font=("Arial", 10),
                                        fg='green', bg='white')
        self.hyst_status_label.pack(side=tk.LEFT, padx=10)

        # 表格
        table_frame = tk.Frame(content_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 0))

        # 表格和滚动条容器
        table_container = tk.Frame(table_frame, bg='white')
        table_container.pack(fill=tk.BOTH, expand=True)

        self.hyst_table = ttk.Treeview(table_container, columns=('I/mA', 'B/mT', 'H/A_m'),
                                    show='headings', height=8)
        self.hyst_table.heading('I/mA', text='I/mA')
        self.hyst_table.heading('B/mT', text='B/mT')
        self.hyst_table.heading('H/A_m', text='H/(A/m)')
        self.hyst_table.column('I/mA', width=80, anchor='center')
        self.hyst_table.column('B/mT', width=100, anchor='center')
        self.hyst_table.column('H/A_m', width=100, anchor='center')
        self.hyst_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 滚动条在表格右边
        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.hyst_table.yview)
        self.hyst_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 曲线图（放在按钮上方）
        plot_frame = tk.Frame(content_frame, bg='white')
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 0))

        self.hyst_fig, self.hyst_ax = plt.subplots(figsize=(5, 3))
        self.hyst_fig.subplots_adjust(bottom=0.18, left=0.12, right=0.95, top=0.92)
        
        self.hyst_canvas = FigureCanvasTkAgg(self.hyst_fig, master=plot_frame)
        self.hyst_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.hyst_ax.set_xlabel('H (A/m)', fontsize=10)
        self.hyst_ax.set_ylabel('B (mT)', fontsize=10)
        self.hyst_ax.set_title('磁滞回线', fontsize=11)
        self.hyst_ax.grid(True)
        self.hyst_ax.set_xlim(-6500, 6500)
        self.hyst_ax.set_ylim(-400, 400)
        self.hyst_ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        self.hyst_ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

        

        self._refresh_table('B')
        self._update_hysteresis_plot()

    def on_import_bx_csv(self):
        """导入B-X关系数据从CSV"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        try:
            import csv
            new_data = []
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # 跳过表头（如果第一行包含表头）
                start_row = 0
                if rows and any(col in rows[0][0].lower() for col in ['x', 'mm', 'b', 'mt']):
                    start_row = 1
                
                for row in rows[start_row:]:
                    if len(row) >= 2:
                        try:
                            x = float(row[0].strip())
                            b = float(row[1].strip())
                            new_data.append({'X/mm': x, 'B/mT': b})
                        except ValueError:
                            continue
            
            if not new_data:
                messagebox.showwarning("警告", "CSV文件中没有有效数据！")
                return
            
            # 替换当前数据
            self.tableA = new_data
            self._refresh_table('A')
            self._update_bx_plot()
            self.status_label_update(f"导入成功: {len(new_data)} 条数据")
            messagebox.showinfo("导入成功", f"成功导入 {len(new_data)} 条B-X数据！")
            
        except Exception as e:
            messagebox.showerror("导入失败", f"导入失败: {e}")

    def on_import_hysteresis_csv(self):
        """导入磁滞回线数据从CSV（格式：I/mA, B/mT, H/A_m）"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        try:
            import csv
            new_data = []
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # 跳过表头（如果第一行包含表头）
                start_row = 0
                if rows:
                    header_lower = rows[0][0].lower() if rows[0] else ""
                    if any(col in header_lower for col in ['i', 'ma', 'b', 'mt', 'h', 'a/m']):
                        start_row = 1
                
                for row in rows[start_row:]:
                    if len(row) >= 3:
                        try:
                            i = float(row[0].strip())
                            b = float(row[1].strip())
                            h = float(row[2].strip())
                            new_data.append({'I/mA': i, 'B/mT': b, 'H/A_m': h})
                        except ValueError:
                            continue
            
            if not new_data:
                messagebox.showwarning("警告", "CSV文件中没有有效数据！")
                return
            
            # 替换当前数据
            self.tableB = new_data
            self._refresh_table('B')
            self._update_hysteresis_plot()
            self.hyst_status_label.config(text=f"导入成功: {len(new_data)} 条数据", fg='green')
            messagebox.showinfo("导入成功", f"成功导入 {len(new_data)} 条磁滞回线数据！")
            
        except Exception as e:
            messagebox.showerror("导入失败", f"导入失败: {e}")
            self.hyst_status_label.config(text="导入失败", fg='red')
            
    def on_export_hysteresis_csv(self):
        """导出磁滞回线数据为CSV（格式：I整数，B一位小数，H整数）"""
        if not self.tableB:
            messagebox.showwarning("警告", "没有数据可导出！请先记录磁滞回线数据。")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # 写入表头，包含样品信息
                sample_name = self.SAMPLE_PARAMS.get(self.selected_sample, {}).get('name', self.selected_sample)
                writer.writerow(['磁滞回线数据'])
                writer.writerow([f'样品: {sample_name}'])
                writer.writerow([])  # 空行
                # ===== 表头格式与表格一致 =====
                writer.writerow(['I/mA', 'B/mT', 'H/(A/m)'])
                for row in self.tableB:
                    # ===== 格式与表格显示完全一致 =====
                    writer.writerow([
                        f"{int(round(row.get('I/mA', 0)))}",      # I: 整数
                        f"{row.get('B/mT', 0):.1f}",              # B: 1位小数
                        f"{int(round(row.get('H/A_m', 0)))}"      # H: 整数
                    ])
            messagebox.showinfo("导出成功", f"磁滞回线数据已导出到:\n{file_path}")
            self.hyst_status_label.config(text=f"已导出: {os.path.basename(file_path)}", fg='green')
        except Exception as e:
            messagebox.showerror("导出失败", f"导出失败: {e}")
            self.hyst_status_label.config(text="导出失败", fg='red')
                
    def on_clear_hysteresis(self):
        """清空磁滞回线数据"""
        if messagebox.askyesno("确认清空", "确定要清空所有磁滞回线数据吗？"):
            self.tableB = []
            # ===== 重置磁滞状态 =====
            # 重置为virgin状态，使用当前剩磁
            self._hyst_branch = 'virgin'
            self._hyst_last_I = 0.0
            br = self.sample_br_with_error.get(self.selected_sample, 0) if self.selected_sample else 0
            self._hyst_last_B = br
            self._hyst_direction = 0
            self._hyst_turn_stack = []
            self._hyst_loop_amp = 600.0
            self._hyst_max_amp = 0.0
            self._hyst_B_offset = 0.0
            self._hyst_exceed_error = False
            
            self._refresh_table('B')
            self._update_hysteresis_plot()
            self.hyst_status_label.config(text="已清空", fg='orange')

    def _update_hysteresis_plot(self):
        """更新磁滞回线图 - 自适应坐标轴"""
        if not hasattr(self, 'hyst_ax'):
            return
        
        self.hyst_ax.clear()
        self.hyst_ax.set_xlabel('H (A/m)')
        self.hyst_ax.set_ylabel('B (mT)')
        self.hyst_ax.set_title('磁滞回线')
        self.hyst_ax.grid(True)
        self.hyst_ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        self.hyst_ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

        if self.tableB:
            hs = [row.get('H/A_m', 0) for row in self.tableB]
            bs = [row.get('B/mT', 0) for row in self.tableB]
            if hs and bs:
                # 绘制曲线
                self.hyst_ax.plot(hs, bs, 'r-', linewidth=2, alpha=0.8)
                self.hyst_ax.scatter(hs[0], bs[0], color='blue', s=30, label='起点')
                if len(hs) > 1:
                    self.hyst_ax.scatter(hs[-1], bs[-1], color='green', s=30, label='终点')
                self.hyst_ax.legend()
                
                # ===== 自适应坐标轴范围 =====
                h_min, h_max = min(hs), max(hs)
                b_min, b_max = min(bs), max(bs)
                
                h_range = h_max - h_min
                b_range = b_max - b_min
                h_margin = max(100, h_range * 0.15) if h_range > 0 else 500
                b_margin = max(20, b_range * 0.15) if b_range > 0 else 50
                
                # 确保包含原点
                h_min = min(h_min, 0) - h_margin
                h_max = max(h_max, 0) + h_margin
                b_min = min(b_min, 0) - b_margin
                b_max = max(b_max, 0) + b_margin
                
                self.hyst_ax.set_xlim(h_min, h_max)
                self.hyst_ax.set_ylim(b_min, b_max)

        if hasattr(self, 'hyst_canvas'):
            self.hyst_canvas.draw()

    # ==================== 数据记录 ====================
    def on_record_current(self):
        """记录当前数据"""
        if self.selected_sample is None:
            messagebox.showwarning("警告", "请先选择样品！")
            return

        stage = self.current_display

        if stage == "bx_relation":
            # 记录到表A (B-X关系)
            x_val = self.hall_position
            b_val = float(self.millitesla_var.get().replace("—", "0"))
            self.tableA.append({'X/mm': x_val, 'B/mT': b_val})
            self._refresh_table('A')
            self._update_bx_plot()
            self.status_label_update(f"已记录: X={x_val}mm, B={b_val:.1f}mT")

        elif stage == "hysteresis":
            # 记录到表B (磁滞回线)
            I_signed = self.excitation_current if self.current_direction == 1 else -self.excitation_current
            b_val = float(self.millitesla_var.get().replace("—", "0"))
            H_val = self.physical_I_to_H(I_signed)

            self.tableB.append({'I/mA': I_signed, 'B/mT': b_val, 'H/A_m': H_val})
            self._refresh_table('B')
            self._update_hysteresis_plot()
            self.status_label_update(f"已记录: I={I_signed:.1f}mA, B={b_val:.1f}mT, H={H_val:.0f}A/m")
        else:
            # 样品选择界面不记录数据
            messagebox.showinfo("提示", "请在B-X关系或磁滞回线界面记录数据")

    def on_delete_row(self):
        """删除选中行"""
        stage = self.current_display
        if stage == "bx_relation":
            selection = self.bx_table.selection()
            if selection:
                idx = self.bx_table.index(selection[0])
                del self.tableA[idx]
                self._refresh_table('A')
                self._update_bx_plot()
        elif stage == "hysteresis":
            selection = self.hyst_table.selection()
            if selection:
                idx = self.hyst_table.index(selection[0])
                del self.tableB[idx]
                self._refresh_table('B')
                self._update_hysteresis_plot()

    def on_clear_table(self):
        """清空表格"""
        stage = self.current_display
        if messagebox.askyesno("确认清空", "确定要清空数据吗？"):
            if stage == "bx_relation":
                self.tableA = []
                self._refresh_table('A')
                self._update_bx_plot()
            elif stage == "hysteresis":
                self.tableB = []
                self._refresh_table('B')
                self._update_hysteresis_plot()

    def on_export_csv(self):
        """导出CSV"""
        stage = self.current_display
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            if stage == "bx_relation":
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['X/mm', 'B/mT'])
                    for row in self.tableA:
                        writer.writerow([row.get('X/mm', ''), row.get('B/mT', '')])
            elif stage == "hysteresis":
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['I/mA', 'B/mT', 'H/(A/m)'])
                    for row in self.tableB:
                        writer.writerow([row.get('I/mA', ''), row.get('B/mT', ''), row.get('H/A_m', '')])
            else:
                messagebox.showinfo("提示", "请在B-X关系或磁滞回线界面导出数据")
                return
            messagebox.showinfo("导出成功", f"数据已导出到: {file_path}")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出失败: {e}")

    def _refresh_table(self, table_type):
        """刷新表格显示"""
        if table_type == 'A':
            # B-X关系表格
            if hasattr(self, 'bx_table'):
                for item in self.bx_table.get_children():
                    self.bx_table.delete(item)
                for row in self.tableA:
                    self.bx_table.insert('', tk.END, values=[
                        row.get('X/mm', ''),
                        f"{row.get('B/mT', 0):.1f}"
                    ])
        else:
            # 磁滞回线表格
            if hasattr(self, 'hyst_table'):
                for item in self.hyst_table.get_children():
                    self.hyst_table.delete(item)
                for row in self.tableB:
                    # ===== 格式：I保留整数，B保留1位小数，H保留整数 =====
                    self.hyst_table.insert('', tk.END, values=[
                        f"{int(round(row.get('I/mA', 0)))}",           # I: 整数
                        f"{row.get('B/mT', 0):.1f}",                   # B: 1位小数
                        f"{int(round(row.get('H/A_m', 0)))}"           # H: 整数
                    ])

    def _update_bx_plot(self):
        """更新B-X曲线图"""
        if not hasattr(self, 'bx_ax'):
            return
        
        self.bx_ax.clear()
        self.bx_ax.set_xlabel('X (mm)', fontsize=10)
        self.bx_ax.set_ylabel('B (mT)', fontsize=10)
        self.bx_ax.set_title('B-X关系曲线', fontsize=11)
        self.bx_ax.grid(True)

        if self.tableA:
            xs = [row.get('X/mm', 0) for row in self.tableA]
            bs = [row.get('B/mT', 0) for row in self.tableA]
            # 按X排序
            sorted_data = sorted(zip(xs, bs), key=lambda x: x[0])
            if sorted_data:
                xs_sorted, bs_sorted = zip(*sorted_data)
                self.bx_ax.plot(xs_sorted, bs_sorted, 'bo-', linewidth=2, markersize=6)
                
                # ===== 自适应显示范围 =====
                x_min, x_max = min(xs_sorted), max(xs_sorted)
                b_min, b_max = min(bs_sorted), max(bs_sorted)
                x_range = x_max - x_min
                b_range = b_max - b_min
                x_margin = max(1, x_range * 0.15)
                b_margin = max(1, b_range * 0.15)
                self.bx_ax.set_xlim(x_min - x_margin, x_max + x_margin)
                self.bx_ax.set_ylim(b_min - b_margin, b_max + b_margin)
        else:
            # 无数据时显示默认范围
            self.bx_ax.set_xlim(-25, 25)
            self.bx_ax.set_ylim(-10, 10)

        if hasattr(self, 'bx_canvas'):
            self.bx_canvas.draw()

    def status_label_update(self, message):
        """更新状态显示"""
        # 只更新当前存在的标签
        if hasattr(self, 'demag_status_label') and self.demag_status_label.winfo_exists():
            try:
                self.demag_status_label.config(text=message, fg='blue')
            except:
                pass
        
        if hasattr(self, 'hyst_status_label') and self.hyst_status_label.winfo_exists():
            try:
                self.hyst_status_label.config(text=message, fg='blue')
            except:
                pass
        
        # 也更新状态栏（如果有）
        if hasattr(self, 'stage_info_label') and self.stage_info_label.winfo_exists():
            try:
                self.stage_info_label.config(text=message[:50])  # 限制长度
            except:
                pass

    # ==================== 控制函数 ====================
    def adjust_position(self, delta):
        new_val = self.hall_position + delta
        new_val = max(-20, min(20, new_val))
        self.hall_position = new_val
        self.position_scale.set(new_val)
        self._update_hall_element_position()
        self.update_millitesla_display()

    def update_position(self, value):
        self.hall_position = int(float(value))
        self._update_hall_element_position()
        self.update_millitesla_display()

    def _update_hall_element_position(self):
        offset_x = self.hall_position * 1.76
        new_x = 151 - offset_x
        self.canvas.coords("hall_element", new_x, self.hall_element_y,
                          new_x + self.hall_element_length, self.hall_element_y)

    def adjust_excitation(self, delta):
        new_val = self.excitation_current + delta
        new_val = max(0, min(600, new_val))
        self.excitation_current = new_val
        self.excitation_scale.set(new_val)
        self.current_var.set(str(new_val))
        self.update_millitesla_display()
        self.update_arrows()  # ← 添加这行

    def update_excitation_current(self, value):
        self.excitation_current = int(float(value))
        self.current_var.set(str(self.excitation_current))
        self.update_millitesla_display()
        self.update_arrows()  # ← 添加这行

    def toggle_direction(self):
        self.current_direction *= -1
        self.direction_btn.config(text="正向" if self.current_direction == 1 else "反向",
                                 bg='lightblue' if self.current_direction == 1 else 'lightcoral')
        self.update_millitesla_display()
        self.update_arrows()

    def adjust_millitesla_offset(self, delta):
        """调节毫特计偏移（调零）"""
        new_val = self.millitesla_offset + delta
        new_val = max(-50, min(50, new_val))
        self.millitesla_offset = new_val
        self.millitesla_offset_scale.set(new_val)
        self.update_millitesla_display()
        
        # 如果偏移接近0，提示调零完成
        if abs(new_val) < 0.05:
            self.status_label_update("调零完成！")
        else:
            self.status_label_update(f"调零中: {new_val:.1f}mT")

    def update_millitesla_offset(self, value):
        self.millitesla_offset = float(value)
        self.update_millitesla_display()

    def update_millitesla_display(self):
        """更新毫特计显示"""
        if self.selected_sample is None:
            self.millitesla_var.set("—")
            return

        # ===== 退磁过程中：直接从 demag_data 获取最新值 =====
        if self.current_display == "demagnetize" and self.demag_data:
            # 直接使用 demag_data 中存储的值（已包含所有分量）
            B_val = self.demag_data[-1][1]
            self.millitesla_var.set(f"{B_val:.1f}")
            return
        
        # ===== 退磁过程中，但还没有数据时 =====
        if self.current_display == "demagnetize":
            I_signed = self.excitation_current if self.current_direction == 1 else -self.excitation_current
            B_raw = self.get_B_from_magnetic_model(I_signed)
            B_val = B_raw + self.random_offset + self.millitesla_offset
            self.millitesla_var.set(f"{B_val:.1f}")
            return

        # ===== 其他界面 =====
        I_signed = self.excitation_current if self.current_direction == 1 else -self.excitation_current
        B_raw = self.get_B_from_magnetic_model(I_signed)
        position_factor = self.get_remanence_position_factor(self.hall_position)
        measured_b = B_raw * position_factor + self.random_offset + self.millitesla_offset
        self.millitesla_var.set(f"{measured_b:.1f}")

    def get_B_for_hysteresis(self, I_mA):
        """
        磁滞回线模式B值计算 - 根据样品类型调整回线形状
        
        模具钢：宽磁滞回线，过零后斜率快速增大
        纯铁：窄磁滞回线，过零后斜率变化较小
        """
        I_SAT = 600.0
        
        def poly_upper(I):
            return float(np.polyval(self.POLY_UPPER, I))
        
        def poly_lower(I):
            return -poly_upper(-I)
        
        # 初始化状态
        if not hasattr(self, '_hyst_initialized') or not self._hyst_initialized:
            self._hyst_last_I = 0.0
            self._hyst_last_B = 0.0
            self._hyst_direction = 0
            self._hyst_branch = 'virgin'
            self._hyst_loop_amp = I_SAT
            self._hyst_max_amp = 0.0
            self._hyst_turn_stack = []
            self._hyst_B_offset = 0.0
            self._hyst_initialized = True
        
        dI = I_mA - self._hyst_last_I
        
        # 微小变化不更新
        if abs(dI) < 0.5:
            return self._hyst_last_B * self._B_scale_factor
        
        new_direction = 1 if dI > 0 else -1
        abs_I = abs(I_mA)
        
        # 检查是否超过换向时的最大电流值（非virgin分支时不允许超过）
        if self._hyst_branch != 'virgin' and abs_I > self._hyst_max_amp:
            self._hyst_exceed_error = True
            return self._hyst_last_B * self._B_scale_factor
        
        # 更新最大幅度（仅在virgin分支时允许）
        if abs_I > self._hyst_max_amp:
            self._hyst_max_amp = abs_I
            self._hyst_loop_amp = abs_I
        
        # 检测方向变化（转折点）
        if self._hyst_direction != 0 and new_direction != self._hyst_direction:
            turn_I = self._hyst_last_I
            turn_B = self._hyst_last_B
            
            # 压入转折点
            self._hyst_turn_stack.append((turn_I, turn_B, self._hyst_loop_amp))
            
            # 新回线幅度 = 转折点的电流绝对值
            self._hyst_loop_amp = abs(turn_I)
            
            # 分支切换
            if self._hyst_branch == 'virgin':
                self._hyst_branch = 'upper' if new_direction < 0 else 'lower'
            elif new_direction > 0:
                self._hyst_branch = 'lower'
            else:
                self._hyst_branch = 'upper'
            
            # 限制栈大小
            if len(self._hyst_turn_stack) > 50:
                self._hyst_turn_stack = self._hyst_turn_stack[-50:]
        
        self._hyst_direction = new_direction
        
        amp = max(self._hyst_loop_amp, 1.0)
        
        # 获取最近转折点
        if self._hyst_turn_stack:
            turn_I, turn_B, _ = self._hyst_turn_stack[-1]
        else:
            turn_I, turn_B = 0.0, self._hyst_B_offset
        
        # 检查是否回到之前的转折点（闭合小回线）
        closure_target = None
        if len(self._hyst_turn_stack) > 1:
            prev_turn_I, prev_turn_B, _ = self._hyst_turn_stack[-2]
            if (new_direction > 0 and I_mA >= prev_turn_I) or \
            (new_direction < 0 and I_mA <= prev_turn_I):
                closure_target = prev_turn_B
        
        # ===== 获取样品参数 =====
        sample_params = self.SAMPLE_PARAMS.get(self.selected_sample, {})
        width_factor = sample_params.get('hyst_width_factor', 0.7)
        slope_factor = sample_params.get('slope_after_zero', 1.2)
        
        # 计算B值
        if self._hyst_branch == 'virgin':
            # Virgin曲线
            if abs_I < 1.0:
                B_new = self._hyst_B_offset
            else:
                sign = 1 if I_mA >= 0 else -1
                B_new = self._hyst_B_offset + sign * float(np.polyval(self.POLY_VIRGIN, abs_I))
        else:
            # ===== 主回线阶段 - 根据样品类型调整 =====
            scale = amp / I_SAT
            
            if amp >= 300:
                # 300mA及以上：从转折点开始，沿缩放曲线移动
                I_600 = I_mA / scale if scale > 0.01 else I_mA
                I_600 = np.clip(I_600, -I_SAT, I_SAT)
                
                if self._hyst_branch == 'upper':
                    B_600 = poly_upper(I_600)
                    B_turn_600 = poly_upper(I_SAT)
                else:
                    B_600 = poly_lower(I_600)
                    B_turn_600 = poly_lower(-I_SAT)
                
                delta_B = (B_600 - B_turn_600) * scale
                B_new = turn_B + delta_B
                
                # ===== 过零后斜率直接变为2倍（仅模具钢） =====
                sample_type = self.selected_sample
                
                if sample_type == 'mold_steel':
                    prev_I = self._hyst_last_I
                    crossed_zero = (prev_I * I_mA < 0) or (abs(prev_I) < 1 and abs_I > 1)
                    
                    if crossed_zero and abs_I < 80:
                        I_600_zero = 0
                        if self._hyst_branch == 'upper':
                            B_600_zero = poly_upper(0)
                            B_600_current = poly_upper(I_600)
                        else:
                            B_600_zero = poly_lower(0)
                            B_600_current = poly_lower(I_600)
                        
                        B_zero = B_600_zero * scale
                        if self._hyst_turn_stack:
                            _, turn_B, _ = self._hyst_turn_stack[-1]
                            if self._hyst_branch == 'upper':
                                B_turn_zero = poly_upper(0) * scale
                            else:
                                B_turn_zero = poly_lower(0) * scale
                            offset = turn_B - B_turn_zero
                            B_zero = B_zero + offset
                        
                        std_slope = (B_600_current - B_600_zero) * scale / abs_I if abs_I > 0 else 0
                        B_new = B_zero + std_slope * 2.0 * abs_I * (1 if I_mA > 0 else -1)
                
                # ===== 回线宽度调整 =====
                if abs_I > 50:
                    width_boost = 1.0 + (width_factor - 0.5) * 2.0
                    if 50 < abs_I < 500:
                        middle_factor = (abs_I - 50) / 450.0
                        width_adjust = 1.0 + (width_boost - 1.0) * middle_factor * 0.5
                        B_new = B_new * width_adjust
            else:
                # 300mA以下：小回线处理
                I_600 = I_mA / scale if scale > 0.01 else I_mA
                I_600 = np.clip(I_600, -I_SAT, I_SAT)
                
                if self._hyst_branch == 'upper':
                    B_600 = poly_upper(I_600)
                    B_start_600 = poly_upper(I_SAT)
                    B_end_600 = poly_upper(-I_SAT)
                else:
                    B_600 = poly_lower(I_600)
                    B_start_600 = poly_lower(-I_SAT)
                    B_end_600 = poly_lower(I_SAT)
                
                # 计算曲线行程比例
                total_delta = B_end_600 - B_start_600
                current_delta = B_600 - B_start_600
                progress = current_delta / total_delta if abs(total_delta) > 0.01 else 0
                
                # 目标：从turn_B线性过渡到-turn_B
                B_new = turn_B + progress * (-turn_B - turn_B)
        
        # 如果到达闭合点，直接使用闭合目标B值
        if closure_target is not None:
            B_new = closure_target
            if len(self._hyst_turn_stack) > 1:
                self._hyst_turn_stack.pop()
                _, _, prev_amp = self._hyst_turn_stack[-1]
                self._hyst_loop_amp = prev_amp
        
        # 存储内部值
        self._hyst_last_I = I_mA
        self._hyst_last_B = B_new
        
        # 应用样品缩放
        return B_new * self._B_scale_factor
        
    def check_hysteresis_exceed_error(self):
        """检查是否发生超限错误"""
        return getattr(self, '_hyst_exceed_error', False)

    def on_show(self):
        """当实验被显示时调用"""
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.update_millitesla_display()
        self.update_arrows()  # ← 添加这行