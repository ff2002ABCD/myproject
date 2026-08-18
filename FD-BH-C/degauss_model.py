# -*- coding: utf-8 -*-
"""
degauss_model.py - 退磁阶段物理模型 (V2)

核心设计思路：
1. 基于改进的Preisach理论：使用转折点历史和幅度跟踪
2. 初始剩磁范围：-50mT 到 0（根据用户需求）
3. 支持任意电流值换向（不必到600mA）
4. 初始磁化曲线与后续退磁回线有交点
5. 嵌套回线螺旋收敛到原点

物理特征（对应说明书图5）：
- 退磁过程：0→+600→0→-500→0→+400→... (幅度递减100mA)
- 每次换向形成新的小回线，回线逐渐缩小
- 初始磁化曲线从剩磁点出发，穿过后续回线形成交点
- 最终收敛到原点附近

关键改进：
- 使用实测数据的7阶多项式拟合
- 回线缩放使用"同心缩放"模式
- 初始曲线特殊处理确保与后续回线相交
"""

import numpy as np
from typing import List, Tuple, Optional
import random


class DegaussPhysicsModel:
    """
    退磁阶段物理模型 V3
    
    特点：
    1. 使用实测数据7阶多项式拟合
    2. 转折点历史记录 - 实现嵌套回线
    3. 初始剩磁可配置 (-50mT ~ 0)
    4. 任意换向点支持
    5. 初始磁化曲线与后续回线相交
    6. 回线形状更圆滑（叶片形）
    
    标准退磁流程（按说明书图5）：
    - 0→+600mA→0→-500mA→0→+400mA→...
    - 每次最大电流减小100mA
    - 剩磁<100mT时减小量更小
    """
    
    # 材料参数（基于实测数据）
    B_SAT = 314.0        # 饱和磁感应强度 (mT)
    I_SAT = 600.0        # 饱和电流 (mA)
    H_SAT = 2943.0       # 饱和磁场强度 (A/m) - 对应600mA
    
    # 实测数据的7阶多项式系数
    # 上支（下降支）：从+600到-600，I=0时B≈+77mT
    POLY_UPPER = np.array([
        2.5182118055383348e-18, 1.3492625796343097e-16,
        -1.5030302285583753e-12, 4.885604896961923e-13,
        -1.8965117198829675e-07, -0.0002329886887901997,
        0.6697405093359231, 78.22103482201453
    ])
    
    # 下支（上升支）：从-600到+600，I=0时B≈-73mT
    POLY_LOWER = np.array([
        -3.701890964829607e-19, -6.574835216815333e-16,
        4.734415967183772e-13, 3.881612891836147e-10,
        -5.806655033947451e-07, 0.00014502345362569802,
        0.6873778445089721, -73.26564770910605
    ])
    
    # 标准回线特征值
    B_UPPER_0 = 78.0   # 上支在I=0时的B值
    B_LOWER_0 = -73.0  # 下支在I=0时的B值
    
    def __init__(self, initial_remanence: Optional[float] = None):
        """
        初始化退磁模型
        
        Parameters:
            initial_remanence: 初始剩磁值 (mT)，范围 -50 到 0
                              如果为None，则随机生成
        """
        # 设置初始剩磁
        if initial_remanence is None:
            self._Br_init = random.uniform(-50.0, 0.0)
        else:
            self._Br_init = np.clip(initial_remanence, -50.0, 0.0)
        
        # 当前状态
        self._I = 0.0
        self._B = self._Br_init
        self._direction = 0
        
        # 转折点历史 (I, B, amplitude) - 增加幅度信息
        self._turn_points: List[Tuple[float, float, float]] = []
        
        # 当前回线幅度
        self._current_amplitude = self.I_SAT
        
        # 初始磁化标志
        self._is_initial_rise = True
        self._first_peak_I = 0.0
        self._first_peak_B = 0.0
        
        # 分支状态
        self._branch = 'initial'  # 'initial', 'upper', 'lower'
    
    def reset(self, initial_remanence: Optional[float] = None):
        """重置模型状态"""
        if initial_remanence is None:
            self._Br_init = random.uniform(-50.0, 0.0)
        else:
            self._Br_init = np.clip(initial_remanence, -50.0, 0.0)
        
        self._I = 0.0
        self._B = self._Br_init
        self._direction = 0
        self._turn_points = []
        self._current_amplitude = self.I_SAT
        self._is_initial_rise = True
        self._first_peak_I = 0.0
        self._first_peak_B = 0.0
        self._branch = 'initial'
    
    def _poly_upper(self, I: float) -> float:
        """使用多项式计算上支B值"""
        return float(np.polyval(self.POLY_UPPER, I))
    
    def _poly_lower(self, I: float) -> float:
        """使用多项式计算下支B值"""
        return float(np.polyval(self.POLY_LOWER, I))
    
    def _scaled_upper(self, I: float, amplitude: float, center_offset: float = 0.0) -> float:
        """
        缩放后的上支曲线
        
        核心思想：同心缩放，保持曲线形状
        scale = amplitude / 600
        B = B_std(I/scale) * scale + center_offset * (1 - scale)
        """
        if amplitude < 1.0:
            return center_offset
        
        scale = amplitude / self.I_SAT
        I_mapped = I / scale
        I_mapped = np.clip(I_mapped, -self.I_SAT, self.I_SAT)
        
        B_std = self._poly_upper(I_mapped)
        return B_std * scale + center_offset * (1 - scale)
    
    def _scaled_lower(self, I: float, amplitude: float, center_offset: float = 0.0) -> float:
        """缩放后的下支曲线"""
        if amplitude < 1.0:
            return center_offset
        
        scale = amplitude / self.I_SAT
        I_mapped = I / scale
        I_mapped = np.clip(I_mapped, -self.I_SAT, self.I_SAT)
        
        B_std = self._poly_lower(I_mapped)
        return B_std * scale + center_offset * (1 - scale)
    
    def _initial_curve(self, I: float, target_peak: float = None) -> float:
        """
        初始磁化曲线（从剩磁点开始，对应说明书图中A→A'曲线）
        
        支持提前换向：如果用户在400mA就换向，曲线终点值会与
        V5缩放曲线的起点值匹配，确保平滑连接。
        
        Parameters:
            I: 当前电流值 (mA)
            target_peak: 目标峰值电流 (mA)，None表示使用I_SAT
        """
        if I <= 0:
            return self._Br_init
        
        # 确定目标峰值（支持提前换向）
        peak = target_peak if target_peak is not None else self.I_SAT
        peak = max(peak, 50.0)  # 防止除零
        
        # 归一化：0到1
        I_norm = min(I / peak, 1.0)
        
        # 关键：终点B值必须与V5缩放曲线在峰值处的值一致
        # V5在峰值处：B = poly_upper(peak/scale * 600) * scale
        # 其中 scale = peak/600，所以 B = poly_upper(600) * (peak/600)
        scale = peak / self.I_SAT
        B_at_peak = self._poly_upper(self.I_SAT) * scale
        
        # 使用贝塞尔曲线，确保两端平滑连接
        t = I_norm
        B0 = self._Br_init  # 起点
        B1 = B_at_peak      # 终点（与V5缩放曲线匹配）
        
        # 中间控制点
        I_mid = peak * 0.5
        B_mid_upper = self._poly_upper(I_mid)
        B_mid_lower = self._poly_lower(I_mid)
        B_mid_center = (B_mid_upper + B_mid_lower) / 2
        
        # 控制点位置
        Bm = B_mid_center + (B1 - B0) * 0.3
        
        # 二次贝塞尔插值
        B = B0 * (1-t)**2 + 2 * Bm * t * (1-t) + B1 * t**2
        
        return B
    
    def set_target_peak(self, peak_I: float):
        """设置目标峰值电流（用于提前换向场景）"""
        self._target_peak = peak_I
    
    def I_to_H(self, I_mA: float) -> float:
        """将电流(mA)转换为磁场强度H(A/m)"""
        return I_mA * self.H_SAT / self.I_SAT
    
    def H_to_I(self, H: float) -> float:
        """将磁场强度H(A/m)转换为电流(mA)"""
        return H * self.I_SAT / self.H_SAT
    
    def get_B(self, I_mA: float) -> float:
        """
        根据电流计算磁场强度 - V4改进版
        
        关键改进：
        1. 到达峰值后直接沿主回线走，无过渡突变
        2. 后续回线不相交，每个回线在前一个内部
        3. 使用连续状态跟踪确保平滑
        
        Parameters:
            I_mA: 电流值 (mA)
        
        Returns:
            B: 磁感应强度 (mT)
        """
        dI = I_mA - self._I
        
        # 忽略微小变化
        if abs(dI) < 0.5:
            return self._B
        
        new_direction = 1 if dI > 0 else -1
        
        # 检测方向变化（转折点）
        if self._direction != 0 and new_direction != self._direction:
            # 第一次下降：从初始上升切换到主回线
            if self._is_initial_rise and new_direction < 0:
                self._is_initial_rise = False
                self._first_peak_I = self._I
                self._first_peak_B = self._B
                # 关键：第一次换向时，幅度应该等于实际峰值
                self._current_amplitude = abs(self._I)
                self._branch = 'upper'
            else:
                # 后续换向
                self._current_amplitude = abs(self._I)
                if new_direction > 0:
                    self._branch = 'lower'
                else:
                    self._branch = 'upper'
            
            # 记录转折点（使用更新后的幅度）
            self._turn_points.append((self._I, self._B, self._current_amplitude))
            
            if len(self._turn_points) > 30:
                self._turn_points = self._turn_points[-30:]
        
        self._direction = new_direction
        
        # 获取最近的转折点
        if self._turn_points:
            turn_I, turn_B, turn_amp = self._turn_points[-1]
        else:
            turn_I, turn_B, turn_amp = 0.0, self._Br_init, self.I_SAT
        
        amp = max(self._current_amplitude, 1.0)
        
        # 根据状态选择曲线
        if self._is_initial_rise:
            # 初始上升曲线（A→A'）
            # 使用目标峰值（如果已设置）来确保提前换向时平滑连接
            target = getattr(self, '_target_peak', None)
            B_new = self._initial_curve(I_mA, target)
        else:
            # 嵌套回线 - V4.1：缩放曲线 + 转折点约束
            # 核心思想：沿缩放后的边界曲线走，但确保从转折点连续过渡
            
            scale = amp / self.I_SAT
            
            # 将当前电流映射到满幅范围
            I_normalized = I_mA / scale if scale > 0.01 else 0
            I_normalized = np.clip(I_normalized, -self.I_SAT, self.I_SAT)
            
            if self._branch == 'upper':
                # 下降时沿上支
                B_boundary = self._poly_upper(I_normalized) * scale
            else:
                # 上升时沿下支
                B_boundary = self._poly_lower(I_normalized) * scale
            
            # 关键修复：确保从转折点连续过渡
            # 计算转折点处边界曲线的B值
            turn_I_normalized = turn_I / scale if scale > 0.01 else 0
            turn_I_normalized = np.clip(turn_I_normalized, -self.I_SAT, self.I_SAT)
            
            if self._branch == 'upper':
                B_boundary_at_turn = self._poly_upper(turn_I_normalized) * scale
            else:
                B_boundary_at_turn = self._poly_lower(turn_I_normalized) * scale
            
            # 计算偏移量：转折点实际B值与边界曲线的差值
            offset = turn_B - B_boundary_at_turn
            
            # 应用偏移量，并随着远离转折点逐渐衰减
            travel = abs(I_mA - turn_I)
            decay_rate = 0.005  # 衰减速率
            offset_factor = np.exp(-decay_rate * travel)
            
            # 最终B值 = 边界曲线 + 衰减偏移
            B_new = B_boundary + offset * offset_factor
        
        # 边界限制
        B_upper_abs = self._poly_upper(I_mA)
        B_lower_abs = self._poly_lower(I_mA)
        B_new = np.clip(B_new, B_lower_abs, B_upper_abs)
        
        # 更新状态
        self._I = I_mA
        self._B = B_new
        
        return B_new
    
    def get_state(self) -> dict:
        """获取当前状态（用于调试）"""
        return {
            'I': self._I,
            'B': self._B,
            'direction': self._direction,
            'Br_init': self._Br_init,
            'branch': self._branch,
            'amplitude': self._current_amplitude,
            'is_initial_rise': self._is_initial_rise,
            'turn_points_count': len(self._turn_points)
        }


class DegaussSequenceGenerator:
    """
    退磁序列生成器
    
    生成标准的退磁电流序列：
    - 0 → +600 → 0 → -500 → 0 → +400 → ...
    - 每次幅度减小100mA（或自定义衰减）
    - 剩磁<100mT时衰减更慢
    """
    
    def __init__(self, initial_amplitude: float = 600.0,
                 decay_step: float = 100.0,
                 min_amplitude: float = 10.0):
        self.initial_amplitude = initial_amplitude
        self.decay_step = decay_step
        self.min_amplitude = min_amplitude
    
    def generate(self, points_per_half: int = 50) -> List[float]:
        """
        生成退磁电流序列
        
        Returns:
            电流值列表 (mA)
        """
        sequence = []
        amplitude = self.initial_amplitude
        polarity = 1  # 先正向
        
        # 初始上升 0 → +amplitude
        for I in np.linspace(0, amplitude, points_per_half):
            sequence.append(float(I))
        
        while amplitude >= self.min_amplitude:
            # 下降到负峰值
            next_amp = max(amplitude - self.decay_step, self.min_amplitude)
            for I in np.linspace(amplitude * polarity, -next_amp * polarity, points_per_half * 2):
                sequence.append(float(I))
            
            amplitude = next_amp
            polarity *= -1
            
            if amplitude <= self.min_amplitude:
                break
            
            # 上升到正峰值
            next_amp = max(amplitude - self.decay_step, self.min_amplitude)
            for I in np.linspace(-amplitude * polarity, next_amp * polarity, points_per_half * 2):
                sequence.append(float(I))
            
            amplitude = next_amp
            polarity *= -1
        
        # 最终回到0
        if sequence:
            for I in np.linspace(sequence[-1], 0, points_per_half // 2):
                sequence.append(float(I))
        
        return sequence


def simulate_degauss_process(initial_remanence: float = -25.0,
                            first_peak: float = 600.0,
                            decay_mode: str = 'standard') -> Tuple[List[float], List[float]]:
    """
    模拟完整的退磁过程（按说明书图5的标准流程）
    
    标准流程：
    1. 0 → +600mA（初始磁化）
    2. +600 → 0 → -500mA
    3. -500 → 0 → +400mA
    4. 每次幅度减小100mA，交替正负
    5. 剩磁<100mT时减小量更小
    
    Parameters:
        initial_remanence: 初始剩磁 (mT)，范围 -50 到 0
        first_peak: 第一个峰值电流 (mA)
        decay_mode: 衰减模式 'standard' 或 'slow'
    
    Returns:
        (I_list, B_list): 电流和磁场序列
    """
    model = DegaussPhysicsModel(initial_remanence)
    
    I_list = []
    B_list = []
    
    points_per_segment = 80
    
    # 生成幅度序列（按说明书：600, 500, 400, 300, 200, 100, 然后更小步进）
    if decay_mode == 'standard':
        amplitudes = []
        amp = first_peak
        step = 100.0
        while amp > 0:
            amplitudes.append(amp)
            if amp <= 100:
                step = 20.0  # 剩磁小时用更小步进
            amp -= step
            if amp < 10:
                break
    else:
        # 慢速衰减（用于精细退磁）
        amplitudes = list(np.linspace(first_peak, 10, 15))
    
    # 确保有足够的幅度点
    if len(amplitudes) < 2:
        amplitudes = [first_peak, first_peak * 0.5, first_peak * 0.25]
    
    # 第1步：初始上升 0 → +first_peak
    for I in np.linspace(0, first_peak, points_per_segment):
        B = model.get_B(float(I))
        I_list.append(float(I))
        B_list.append(B)
    
    # 第2步开始：交替退磁
    # 当前位置在 +first_peak
    current_I = first_peak
    
    for i in range(1, len(amplitudes)):
        next_amp = amplitudes[i]
        
        # 交替正负：奇数次到负，偶数次到正
        if i % 2 == 1:
            target_I = -next_amp  # 第1次到负
        else:
            target_I = next_amp   # 第2次到正
        
        # 从当前位置到目标
        for I in np.linspace(current_I, target_I, points_per_segment):
            B = model.get_B(float(I))
            I_list.append(float(I))
            B_list.append(B)
        
        current_I = target_I
    
    # 最终回到0
    for I in np.linspace(current_I, 0, points_per_segment // 2):
        B = model.get_B(float(I))
        I_list.append(float(I))
        B_list.append(B)
    
    return I_list, B_list


def simulate_manual_degauss(initial_remanence: float = -25.0,
                           peak_sequence: List[float] = None,
                           points_per_segment: int = 100) -> Tuple[List[float], List[float]]:
    """
    模拟手动退磁过程
    
    Parameters:
        initial_remanence: 初始剩磁 (mT)，范围 -50 到 0
        peak_sequence: 换向点序列，如 [600, -500, 400, -300, ...]
        points_per_segment: 每段的点数
    
    Returns:
        I_list, B_list: 电流和磁场列表
    """
    model = DegaussPhysicsModel(initial_remanence)
    
    # 设置第一个峰值作为目标（支持提前换向）
    if peak_sequence:
        model.set_target_peak(abs(peak_sequence[0]))
    points_per_segment = 60
    
    I_list = []
    B_list = []
    current_I = 0.0
    
    for target_I in peak_sequence:
        for I in np.linspace(current_I, target_I, points_per_segment):
            B = model.get_B(float(I))
            I_list.append(float(I))
            B_list.append(B)
        current_I = target_I
    
    # 回到0
    for I in np.linspace(current_I, 0, points_per_segment // 2):
        B = model.get_B(float(I))
        I_list.append(float(I))
        B_list.append(B)
    
    return I_list, B_list


# ============== 测试代码 ==============

def I_to_H(I_mA: float) -> float:
    """将电流I(mA)转换为磁场强度H(A/m)"""
    # H = N*I/L, 对于600mA对应2943 A/m
    return I_mA * 2943.0 / 600.0


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    print("Testing DegaussPhysicsModel - B-H Curves...")
    
    # ============ B-H 曲线（用户要求）============
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle('退磁过程 B-H 曲线', fontsize=14, fontweight='bold')
    
    # 测试1：标准退磁流程 (剩磁=-25mT)
    ax = axes[0, 0]
    I_list, B_list = simulate_manual_degauss(
        initial_remanence=-25.0,
        peak_sequence=[600, -500, 400, -300, 200, -150, 100, -70, 50, -30, 20, -10]
    )
    H_list = [I_to_H(I) for I in I_list]
    ax.plot(H_list, B_list, 'b-', linewidth=0.8)
    ax.plot(H_list[0], B_list[0], 'ro', markersize=8, label=f'Start B={B_list[0]:.1f}mT')
    ax.plot(H_list[-1], B_list[-1], 'gs', markersize=8, label=f'End B={B_list[-1]:.1f}mT')
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)
    ax.set_xlabel('H (A/m)')
    ax.set_ylabel('B (mT)')
    ax.set_title('Standard Degauss (Br=-25mT)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 测试2：接近0剩磁
    ax = axes[0, 1]
    I_list, B_list = simulate_manual_degauss(
        initial_remanence=-5.0,
        peak_sequence=[600, -500, 400, -300, 200, -150, 100, -70, 50, -30, 20]
    )
    H_list = [I_to_H(I) for I in I_list]
    ax.plot(H_list, B_list, 'b-', linewidth=0.8)
    ax.plot(H_list[0], B_list[0], 'ro', markersize=8, label=f'Start B={B_list[0]:.1f}mT')
    ax.plot(H_list[-1], B_list[-1], 'gs', markersize=8, label=f'End B={B_list[-1]:.1f}mT')
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)
    ax.set_xlabel('H (A/m)')
    ax.set_ylabel('B (mT)')
    ax.set_title('Degauss (Br=-5mT, near zero)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 测试3：最大负剩磁 -50mT
    ax = axes[1, 0]
    I_list, B_list = simulate_manual_degauss(
        initial_remanence=-50.0,
        peak_sequence=[600, -500, 400, -300, 200, -150, 100, -70, 50, -30, 20]
    )
    H_list = [I_to_H(I) for I in I_list]
    ax.plot(H_list, B_list, 'b-', linewidth=0.8)
    ax.plot(H_list[0], B_list[0], 'ro', markersize=8, label=f'Start B={B_list[0]:.1f}mT')
    ax.plot(H_list[-1], B_list[-1], 'gs', markersize=8, label=f'End B={B_list[-1]:.1f}mT')
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)
    ax.set_xlabel('H (A/m)')
    ax.set_ylabel('B (mT)')
    ax.set_title('Degauss (Br=-50mT, max negative)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 测试4：用户提前换向 (400mA就开始)
    ax = axes[1, 1]
    I_list, B_list = simulate_manual_degauss(
        initial_remanence=-30.0,
        peak_sequence=[400, -350, 300, -250, 200, -150, 100, -70, 50, -30]
    )
    H_list = [I_to_H(I) for I in I_list]
    ax.plot(H_list, B_list, 'b-', linewidth=0.8)
    ax.plot(H_list[0], B_list[0], 'ro', markersize=8, label=f'Start B={B_list[0]:.1f}mT')
    ax.plot(H_list[-1], B_list[-1], 'gs', markersize=8, label=f'End B={B_list[-1]:.1f}mT')
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)
    ax.set_xlabel('H (A/m)')
    ax.set_ylabel('B (mT)')
    ax.set_title('Early Reversal (Br=-30mT, Hmax≈1962 A/m)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('degauss_model_test.png', dpi=150)
    print("图像已保存到 degauss_model_test.png")
    plt.show()
