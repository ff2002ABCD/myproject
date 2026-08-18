#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
physics_model.py - 基于实测数据的磁滞回线模型

核心思路：
1. 将参考数据分为多个分支（初始磁化、上升支、下降支）
2. 使用多项式拟合每个分支的 I→B 关系
3. 根据电流变化方向自动切换分支
4. 支持位置耦合校正

磁滞回线分支定义：
- virgin: 初始磁化曲线 (从退磁状态开始)
- upper_desc: 上半支下降 (从+Imax下降到-Imax)
- lower_asc: 下半支上升 (从-Imax上升到+Imax)
"""

import json
import os
import csv
import numpy as np
from typing import Dict, List, Tuple, Optional, Any


class HysteresisModel:
    """
    基于实测数据拟合的磁滞回线模型
    
    特点：
    - 分支感知：区分上升和下降分支
    - 多项式拟合：对每个分支进行高阶多项式拟合
    - 状态追踪：记录当前电流和分支状态
    """
    
    def __init__(self):
        # 分支数据存储
        self.branches = {
            'virgin': [],           # 初始磁化曲线
            'upper_desc': [],       # 上半支下降 (正饱和→负饱和)
            'lower_asc': [],        # 下半支上升 (负饱和→正饱和)
        }
        
        # 多项式拟合系数 (I → B) - 基于用户提供的实测数据拟合
        # 7阶多项式，RMSE < 1.4 mT
        self.poly_coeffs = {
            'virgin': np.array([1.8103182434899675e-16, -4.429965422739932e-13, 
                               4.1662120828552727e-10, -1.874175883611441e-07, 
                               3.862677128459556e-05, -0.0019637946434151294, 
                               0.27267985411708406, -0.0030290958318955176]),
            'upper_desc': np.array([5.4753904689923116e-18, 1.3313449333710615e-15, 
                                   -2.906763320825185e-12, -4.948538820487565e-10, 
                                   -1.3824996914010433e-08, -0.00018404897400839921, 
                                   0.6655637952227657, 77.67844033650414]),
            'lower_asc': np.array([4.194076360663361e-19, -9.0699031747940404e-16, 
                                  1.3739504966688314e-13, 4.4342519922611645e-10, 
                                  -5.343831994695859e-07, 0.0001468818272131054, 
                                  0.6839865157198922, -73.20644931848031]),
        }
        
        # 拟合阶数
        self.poly_degree = 7
        
        # 状态追踪
        self._I_prev = 0.0          # 上一次电流值 (mA)
        self._B_prev = 0.0          # 上一次磁场值 (mT)
        self._current_branch = 'virgin'  # 当前分支
        self._direction = 0         # 电流变化方向: +1上升, -1下降, 0未知
        self._initialized = False   # 是否已从退磁状态初始化
        
        # 全局剩磁状态（未退磁样品的剩磁）
        # 剩磁范围：-50mT 到 0（符合退磁模型要求）
        import random
        self._global_remanence = random.uniform(-50.0, 0.0)  # 全局剩磁 (mT)
        self._initial_remanence = self._global_remanence  # 保存启动时的剩磁用于电源重启
        self._has_degaussed = False  # 是否已完成退磁
        self._degauss_end_value = 0.0  # 退磁终点值
        
        # 饱和电流阈值
        self.I_sat_positive = 600.0  # mA
        self.I_sat_negative = -600.0  # mA
        
        # 分支切换阈值
        self._direction_threshold = 0.5  # mA，电流变化超过此值才判断方向
        self._direction_confirm_count = 0
        self._direction_confirm_required = 2
        
        # 样品类型和B值缩放因子
        # 当前模型基于模具钢实测数据(Bs≈315mT)，纯铁需要缩放到800mT
        self._sample_type = 'mold_steel'  # 默认模具钢
        self._B_scale_factor = 1.0  # B值缩放因子
        self._sample_Bs = {
            'mold_steel': 315.0,   # 模具钢饱和值 (mT) - 基准
            'pure_iron': 800.0     # 电工纯铁饱和值 (mT)
        }
        
        # 方向对称性支持（方法1：检测第一次电流变化方向）
        # 如果用户从负方向开始操作，整个坐标系翻转以保持对称性
        self._degauss_initial_direction = None  # 退磁模式的初始方向
        self._hyst_initial_direction = None     # 磁滞回线模式的初始方向
        
        # 加载参考数据
        self._load_reference_data()
    
    def _load_reference_data(self):
        """从 CSV 文件加载参考数据并分割为各分支"""
        csv_path = os.path.join(os.path.dirname(__file__), "reference_bh_curve.csv")
        
        if not os.path.exists(csv_path):
            print(f"Warning: Reference data file not found: {csv_path}")
            return
        
        try:
            data = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    I = float(row['I/mA'])
                    B = float(row['B/mT'])
                    H = float(row['H/(A/m)'])
                    data.append((I, B, H))
            
            if len(data) < 10:
                print("Warning: Not enough reference data points")
                return
            
            # 分割数据为各分支
            self._split_branches(data)
            
            # 对每个分支进行多项式拟合
            self._fit_all_branches()
            
            print(f"Loaded {len(data)} reference points, fitted {len([k for k,v in self.poly_coeffs.items() if v is not None])} branches")
            
        except Exception as e:
            print(f"Error loading reference data: {e}")
    
    def _split_branches(self, data: List[Tuple[float, float, float]]):
        """
        将完整的磁滞回线数据分割为各分支
        
        数据顺序（根据图2）：
        1. 初始磁化: 0 → +600 mA (行1-13)
        2. 上半支下降: +600 → 0 → -600 mA (行13-37)
        3. 下半支上升: -600 → 0 → +600 mA (行37-62)
        """
        n = len(data)
        
        # 找到关键转折点
        # 第一个正峰值（约600mA）
        peak_pos_idx = 0
        for i, (I, B, H) in enumerate(data):
            if I > 550:
                peak_pos_idx = i
                break
        
        # 第一个负峰值（约-600mA）
        peak_neg_idx = 0
        for i, (I, B, H) in enumerate(data):
            if I < -550:
                peak_neg_idx = i
                break
        
        # 分割数据
        # 初始磁化曲线: 从0到第一个正峰值
        self.branches['virgin'] = data[0:peak_pos_idx+1]
        
        # 上半支下降: 从正峰值到负峰值
        self.branches['upper_desc'] = data[peak_pos_idx:peak_neg_idx+1]
        
        # 下半支上升: 从负峰值到末尾（回到正峰值）
        self.branches['lower_asc'] = data[peak_neg_idx:]
        
        print(f"Branch split: virgin={len(self.branches['virgin'])}, "
              f"upper_desc={len(self.branches['upper_desc'])}, "
              f"lower_asc={len(self.branches['lower_asc'])}")
    
    def _fit_all_branches(self):
        """对所有分支进行多项式拟合"""
        for branch_name, branch_data in self.branches.items():
            if len(branch_data) < 3:
                continue
            
            I_arr = np.array([d[0] for d in branch_data])
            B_arr = np.array([d[1] for d in branch_data])
            
            # 使用多项式拟合
            try:
                # 根据数据点数量调整拟合阶数
                degree = min(self.poly_degree, len(branch_data) - 1)
                coeffs = np.polyfit(I_arr, B_arr, degree)
                self.poly_coeffs[branch_name] = coeffs
                
                # 计算拟合误差
                B_fit = np.polyval(coeffs, I_arr)
                rmse = np.sqrt(np.mean((B_arr - B_fit) ** 2))
                print(f"Branch '{branch_name}': degree={degree}, RMSE={rmse:.3f} mT")
                
            except Exception as e:
                print(f"Error fitting branch '{branch_name}': {e}")
    
    def initialize_with_remanence(self):
        """
        初始化模型为设备开启状态（有随机剩磁）- 仅在程序启动时调用一次
        
        剩磁范围：-50mT 到 0（符合退磁模型要求）
        """
        import random
        # 新的剩磁范围：-50mT 到 0
        self._initial_remanence = random.uniform(-50.0, 0.0)
        self._global_remanence = self._initial_remanence
        self._I_prev = 0.0
        self._B_prev = self._global_remanence
        self._current_branch = 'virgin'
        self._direction = 0
        self._initialized = False  # 未退磁状态
        self._has_degaussed = False  # 是否已完成退磁
        self._degauss_end_value = 0.0  # 退磁终点值
        self._direction_confirm_count = 0
        self._remanent_B = self._global_remanence
        self._peak_I_history = []
        self._cycle_count = 0
        self._last_peak_B = 0.0
        # 重置退磁模型状态
        self._dg_initialized = False
        # 重置方向对称性状态
        self._degauss_initial_direction = None
        self._hyst_initial_direction = None
    
    def restore_to_power_on_state(self):
        """恢复到电源开启状态（电源按钮点击时调用）"""
        # 如果已经退磁，恢复到退磁终点值
        if getattr(self, '_has_degaussed', False):
            degauss_value = getattr(self, '_degauss_end_value', 0.0)
            self._global_remanence = degauss_value
            self._initialized = True
        else:
            # 未退磁，恢复到启动时的随机剩磁
            self._global_remanence = getattr(self, '_initial_remanence', 0.0)
            self._initialized = False
        
        self._I_prev = 0.0
        self._B_prev = self._global_remanence
        self._current_branch = 'virgin'
        self._direction = 0
        self._direction_confirm_count = 0
        self._remanent_B = self._global_remanence
        self._peak_I_history = []
        self._cycle_count = 0
        self._last_peak_B = 0.0
        
        # 重置退磁模型状态变量
        self._dg_initialized = False
        self._dg_last_I = 0.0
        self._dg_branch = 'lower'
        self._dg_is_first = True
        self._dg_direction = 0
        self._dg_peak_I = 0.0
        
        # 重置方向对称性状态
        self._degauss_initial_direction = None
        self._hyst_initial_direction = None
        
        # 重置阶段3磁滞回线状态
        # 如果已退磁，使用退磁终点值；否则使用初始剩磁
        if getattr(self, '_has_degaussed', False):
            hyst_offset = getattr(self, '_degauss_end_value', 0.0)
        else:
            hyst_offset = getattr(self, '_initial_remanence', 0.0)
        self.reset_hysteresis_state(hyst_offset)
    
    def reset(self, degauss_end_B: float = 0.0):
        """重置模型状态（模拟退磁完成后的状态）
        
        Parameters:
            degauss_end_B: 退磁终点的B值（已缩放），默认为0
        """
        # 将缩放后的B值转换回未缩放值用于内部存储
        # 这样后续计算可以正确应用缩放因子
        unscaled_B = degauss_end_B / self._B_scale_factor if self._B_scale_factor != 0 else degauss_end_B
        
        self._I_prev = 0.0
        self._B_prev = unscaled_B
        self._current_branch = 'virgin'
        self._direction = 0
        self._initialized = True  # 设置为已初始化，避免返回随机剩磁
        self._direction_confirm_count = 0
        # 退磁相关状态
        self._remanent_B = unscaled_B  # 剩磁设为退磁终点值（未缩放）
        self._peak_I_history = []  # 历史峰值电流
        self._cycle_count = 0  # 退磁周期计数
        self._last_peak_B = 0.0  # 上一个峰值对应的B
        # 更新全局剩磁为退磁终点值（未缩放）
        self._global_remanence = unscaled_B
        # 标记已完成退磁
        self._has_degaussed = True
        self._degauss_end_value = unscaled_B
        # 重置磁滞回线状态，传入退磁终点B值作为起点偏移（未缩放）
        self.reset_hysteresis_state(unscaled_B)
    
    def get_B_for_degauss(self, I_mA: float, degauss_amplitude: float) -> float:
        """
        退磁模式下的B值计算 - 基于改进的Preisach模型
        
        核心设计（V2）：
        1. 使用实测数据多项式拟合
        2. 转折点历史记录实现嵌套回线
        3. 初始磁化曲线与后续回线形成交点
        4. 回线逐渐收敛到原点
        
        初始剩磁范围：-50mT 到 0（可通过_global_remanence设置）
        
        方向对称性支持：
        - 检测第一次电流变化方向
        - 如果负方向启动，翻转坐标系保持对称性
        """
        # 方向对称性检测（方法1：检测第一次电流变化）
        if self._degauss_initial_direction is None and abs(I_mA) > 1.0:
            self._degauss_initial_direction = 1 if I_mA > 0 else -1
            # 如果负方向启动，翻转内部剩磁状态
            if self._degauss_initial_direction == -1:
                if hasattr(self, '_dg_Br_init'):
                    self._dg_Br_init = -self._dg_Br_init
                if hasattr(self, '_dg_B_prev'):
                    self._dg_B_prev = -self._dg_B_prev
        
        # 如果负方向启动，翻转坐标系
        if self._degauss_initial_direction == -1:
            I_transformed = -I_mA
            B_result = self._get_B_for_degauss_internal(I_transformed, degauss_amplitude)
            return -B_result
        else:
            return self._get_B_for_degauss_internal(I_mA, degauss_amplitude)
    
    def _get_B_for_degauss_internal(self, I_mA: float, degauss_amplitude: float) -> float:
        """退磁模式内部计算（不含方向对称处理）"""
        # 材料参数
        B_SAT = 314.0
        I_SAT = 600.0
        
        # 多项式系数（基于实测数据）
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
        
        def poly_upper(I):
            return float(np.polyval(POLY_UPPER, I))
        
        def poly_lower(I):
            return float(np.polyval(POLY_LOWER, I))
        
        def scaled_upper(I, amp):
            if amp < 1.0:
                return 0.0
            scale = amp / I_SAT
            I_mapped = np.clip(I / scale, -I_SAT, I_SAT)
            return poly_upper(I_mapped) * scale
        
        def scaled_lower(I, amp):
            if amp < 1.0:
                return 0.0
            scale = amp / I_SAT
            I_mapped = np.clip(I / scale, -I_SAT, I_SAT)
            return poly_lower(I_mapped) * scale
        
        # 初始化状态
        if not hasattr(self, '_dg_initialized') or not self._dg_initialized:
            # 确保初始剩磁在合理范围内（基准范围是模具钢的-50到0）
            init_rem = self._global_remanence
            if init_rem > 0:
                init_rem = -abs(init_rem) * 0.5  # 转换为负值
            init_rem = np.clip(init_rem, -50.0, 0.0)
            # 内部存储未缩放的值，只在返回时缩放
            
            self._dg_I_prev = 0.0
            self._dg_B_prev = init_rem  # 存储未缩放值
            self._dg_Br_init = init_rem  # 存储未缩放值
            self._dg_direction = 0
            self._dg_turn_points = []
            self._dg_current_amplitude = I_SAT
            self._dg_is_initial_rise = True
            self._dg_branch = 'initial'
            self._dg_initialized = True
        
        dI = I_mA - self._dg_I_prev
        
        if abs(dI) < 0.5:
            return self._dg_B_prev * self._B_scale_factor  # 返回时应用缩放
        
        new_direction = 1 if dI > 0 else -1
        
        # 检测方向变化（转折点）
        if self._dg_direction != 0 and new_direction != self._dg_direction:
            self._dg_turn_points.append((self._dg_I_prev, self._dg_B_prev, self._dg_current_amplitude))
            self._dg_current_amplitude = abs(self._dg_I_prev)
            
            if self._dg_is_initial_rise and new_direction < 0:
                self._dg_is_initial_rise = False
                self._dg_branch = 'upper'
            elif new_direction > 0:
                self._dg_branch = 'lower'
            else:
                self._dg_branch = 'upper'
            
            if len(self._dg_turn_points) > 30:
                self._dg_turn_points = self._dg_turn_points[-30:]
        
        self._dg_direction = new_direction
        
        # 获取转折点
        if self._dg_turn_points:
            turn_I, turn_B, _ = self._dg_turn_points[-1]
        else:
            turn_I, turn_B = 0.0, self._dg_Br_init
        
        amp = max(self._dg_current_amplitude, 1.0)
        
        # 计算B值
        if self._dg_is_initial_rise:
            # 初始磁化曲线 - 使用贝塞尔曲线，支持提前换向
            # 获取目标峰值（支持early reversal）
            target_peak = getattr(self, '_dg_target_peak', None)
            peak = target_peak if target_peak is not None else I_SAT
            peak = max(peak, 50.0)
            
            I_norm = min(I_mA / peak, 1.0)
            
            # 终点B值与V4.2缩放曲线匹配
            scale = peak / I_SAT
            B_at_peak = poly_upper(I_SAT) * scale
            
            t = I_norm
            B0 = self._dg_Br_init
            B1 = B_at_peak
            
            # 中间控制点
            B_mid_upper = poly_upper(peak * 0.5)
            B_mid_lower = poly_lower(peak * 0.5)
            B_mid_center = (B_mid_upper + B_mid_lower) / 2
            Bm = B_mid_center + (B1 - B0) * 0.3
            
            # 二次贝塞尔插值
            B_new = B0 * (1-t)**2 + 2 * Bm * t * (1-t) + B1 * t**2
        else:
            # 嵌套回线 - V4.2：缩放曲线 + 偏移衰减确保转折点连续
            scale = amp / I_SAT
            I_normalized = I_mA / scale if scale > 0.01 else 0
            I_normalized = np.clip(I_normalized, -I_SAT, I_SAT)
            
            if self._dg_branch == 'upper':
                B_boundary = poly_upper(I_normalized) * scale
            else:
                B_boundary = poly_lower(I_normalized) * scale
            
            # 计算转折点处边界曲线的B值
            turn_I_normalized = turn_I / scale if scale > 0.01 else 0
            turn_I_normalized = np.clip(turn_I_normalized, -I_SAT, I_SAT)
            
            if self._dg_branch == 'upper':
                B_boundary_at_turn = poly_upper(turn_I_normalized) * scale
            else:
                B_boundary_at_turn = poly_lower(turn_I_normalized) * scale
            
            # 计算偏移量并应用衰减
            offset = turn_B - B_boundary_at_turn
            travel = abs(I_mA - turn_I)
            decay_rate = 0.005
            offset_factor = np.exp(-decay_rate * travel)
            
            B_new = B_boundary + offset * offset_factor
        
        # 边界限制
        B_upper_max = scaled_upper(I_mA, amp)
        B_lower_min = scaled_lower(I_mA, amp)
        B_new = np.clip(B_new, min(B_lower_min, poly_lower(I_mA)), 
                       max(B_upper_max, poly_upper(I_mA)))
        
        # 存储未缩放的B值用于内部计算
        self._dg_I_prev = I_mA
        self._dg_B_prev = B_new  # 存储未缩放值
        
        # 只在返回时应用样品类型的B值缩放因子
        return B_new * self._B_scale_factor
    
    def _simple_degauss_model(self, I_abs: float, amplitude: float, polarity: int) -> float:
        """简化退磁模型（当没有磁滞回线数据时使用）"""
        B_sat = 320.0
        scale = amplitude / self.I_sat_positive
        B_max = B_sat * scale
        I_norm = I_abs / amplitude if amplitude > 0.1 else 0.0
        
        if self._degauss_phase == 'rising':
            B_base = B_max * np.tanh(2.5 * I_norm)
        else:
            B_base = B_max * np.tanh(2.5 * I_norm) * 0.85
        
        remanence_contrib = self._degauss_remanent * (1.0 - I_norm)
        return (B_base + remanence_contrib) * polarity
    
    def reset_degauss_state(self):
        """重置退磁相关状态"""
        self._I_prev = 0.0
        self._B_prev = 0.0
        self._direction = 0
        
        # 重置方向对称性状态
        self._degauss_initial_direction = None
        self._degauss_original_remanence = self._global_remanence  # 保存原始剩磁
        
        # 确保初始剩磁在 -50mT 到 0 范围内
        init_rem = self._global_remanence
        if init_rem > 0:
            init_rem = -abs(init_rem)  # 转换为负值
        init_rem = np.clip(init_rem, -50.0, 0.0)
        
        # 退磁专用状态 - 完整初始化
        self._dg_I_prev = 0.0
        self._dg_B_prev = init_rem
        self._dg_Br_init = init_rem
        self._dg_direction = 0
        self._dg_turn_points = []
        self._dg_current_amplitude = 600.0  # I_SAT
        self._dg_is_initial_rise = True
        self._dg_branch = 'initial'
        self._dg_initialized = True
        self._dg_target_peak = None
        self._dg_last_I = 0.0
        self._dg_is_first = True
        self._dg_peak_I = 0.0
        self._dg_in_initial_path = True
    
    def set_dg_target_peak(self, peak_I: float):
        """设置退磁目标峰值电流（支持提前换向）"""
        self._dg_target_peak = abs(peak_I)
    
    def _determine_branch(self, I_mA: float) -> str:
        """
        根据电流值和变化方向确定当前分支
        
        分支切换逻辑（基于实测数据）：
        - virgin: 初始从0上升到+600 (只在第一次使用)
        - upper_desc: 从+600下降到-600 (I=0时B≈77mT)
        - lower_asc: 从-600上升到+600 (I=0时B≈-73mT)
        """
        dI = I_mA - self._I_prev
        
        # 判断方向变化
        if abs(dI) > self._direction_threshold:
            new_direction = 1 if dI > 0 else -1
            
            if new_direction != self._direction:
                self._direction_confirm_count += 1
                if self._direction_confirm_count >= self._direction_confirm_required:
                    old_direction = self._direction
                    self._direction = new_direction
                    self._direction_confirm_count = 0
                    
                    # 只在饱和区域附近切换分支，避免中间位置跳变
                    if self._direction > 0:
                        # 电流开始上升
                        if self._I_prev < -400:
                            # 从负饱和区域开始上升 → 下半支上升
                            self._current_branch = 'lower_asc'
                            self._initialized = True
                        elif not self._initialized and self._I_prev < 50:
                            # 初始上升 → 初始磁化
                            self._current_branch = 'virgin'
                            self._initialized = True
                    else:
                        # 电流开始下降
                        if self._I_prev > 400:
                            # 从正饱和区域开始下降 → 上半支下降
                            self._current_branch = 'upper_desc'
                            self._initialized = True
            else:
                self._direction_confirm_count = 0
        
        return self._current_branch
    
    def get_B(self, I_mA: float) -> float:
        """
        根据电流值获取磁场强度
        
        Parameters:
            I_mA: 电流值 (mA)，带符号
        
        Returns:
            B: 磁感应强度 (mT)
        """
        # 确定当前分支
        branch = self._determine_branch(I_mA)
        
        # 获取该分支的拟合系数
        coeffs = self.poly_coeffs.get(branch)
        
        if coeffs is None:
            # 如果没有拟合数据，尝试使用其他分支或返回0
            # 优先使用 lower_asc（完整的上升支）
            coeffs = self.poly_coeffs.get('lower_asc')
            if coeffs is None:
                coeffs = self.poly_coeffs.get('upper_desc')
            if coeffs is None:
                coeffs = self.poly_coeffs.get('virgin')
            if coeffs is None:
                # 完全没有数据，返回线性近似
                B = I_mA * 0.5  # 粗略近似
                self._I_prev = I_mA
                self._B_prev = B
                return B
        
        # 使用多项式计算 B
        B_poly = float(np.polyval(coeffs, I_mA))
        
        # 在I=0时显示初始剩磁
        # 条件：未初始化 且 电流接近0
        if abs(I_mA) < 1.0 and not self._initialized:
            # I=0时直接显示全局剩磁
            B = self._global_remanence
        elif abs(I_mA) < 10.0 and not self._initialized:
            # 小电流区域平滑过渡
            weight = (10.0 - abs(I_mA)) / 10.0
            B = B_poly * (1 - weight) + self._global_remanence * weight
        else:
            B = B_poly
        
        # 更新状态
        self._I_prev = I_mA
        self._B_prev = B
        
        return B
    
    def get_B_for_hysteresis(self, I_mA: float) -> float:
        """
        阶段3磁滞回线测量的B值计算 - 支持任意幅度闭合+对称
        
        核心设计：
        1. Virgin曲线使用实测POLY_VIRGIN多项式（有S形）
        2. 回线使用对称的上下分支：lower(I) = -upper(-I)
        3. 300mA以下特殊处理确保对称
        4. 转折点记录实现嵌套回线
        
        方向对称性支持：
        - 检测第一次电流变化方向
        - 如果负方向启动，翻转坐标系保持对称性
        
        Parameters:
            I_mA: 电流值 (mA)，带符号
        
        Returns:
            B: 磁感应强度 (mT)
        """
        # 直接调用内部计算，内部已处理正负方向
        return self._get_B_for_hysteresis_internal(I_mA)
    
    def _get_B_for_hysteresis_internal(self, I_mA: float) -> float:
        """磁滞回线内部计算（不含方向对称处理）"""
        I_SAT = 600.0
        
        # 多项式系数（基于实测数据）- 标准600mA回线
        POLY_UPPER = np.array([
            2.5182118055383348e-18, 1.3492625796343097e-16,
            -1.5030302285583753e-12, 4.885604896961923e-13,
            -1.8965117198829675e-07, -0.0002329886887901997,
            0.6697405093359231, 78.22103482201453
        ])
        
        # 初始磁化曲线多项式（基于实测数据拟合）
        POLY_VIRGIN = np.array([
            -1.10625264e-12, 4.12158156e-09, -5.29945015e-06,
            2.63182417e-03, 1.04967057e-01, 0.0  # 强制过原点
        ])
        
        def poly_upper(I):
            """上分支（下降）: 从+Imax到-Imax"""
            return float(np.polyval(POLY_UPPER, I))
        
        def poly_lower(I):
            """下分支（上升）: 从-Imax到+Imax - 强制关于原点对称"""
            # lower(I) = -upper(-I)，确保磁滞回线关于原点对称
            return -poly_upper(-I)
        
        # 初始化状态
        if not hasattr(self, '_hyst_initialized') or not self._hyst_initialized:
            self._hyst_last_I = 0.0
            self._hyst_last_B = getattr(self, '_hyst_B_offset', 0.0)
            self._hyst_direction = 0
            self._hyst_branch = 'virgin'
            self._hyst_loop_amp = I_SAT      # 当前回线幅度
            self._hyst_max_amp = 0.0         # 已达到的最大幅度
            self._hyst_turn_stack = []       # 转折点栈：[(I, B, amp), ...]
            self._hyst_initialized = True
            if not hasattr(self, '_hyst_B_offset'):
                self._hyst_B_offset = 0.0
        
        dI = I_mA - self._hyst_last_I
        
        # 微小变化不更新
        if abs(dI) < 0.5:
            return self._hyst_last_B * self._B_scale_factor  # 返回时应用缩放
        
        new_direction = 1 if dI > 0 else -1
        abs_I = abs(I_mA)
        
        # 检查是否超过换向时的最大电流值（非virgin分支时不允许超过）
        if self._hyst_branch != 'virgin' and abs_I > self._hyst_max_amp:
            # 超过最大幅度，返回之前的B值并设置错误标志
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
            turn_amp = abs(turn_I)
            
            # 压入转折点
            self._hyst_turn_stack.append((turn_I, turn_B, self._hyst_loop_amp))
            
            # 新回线幅度 = 转折点的电流绝对值
            self._hyst_loop_amp = turn_amp
            
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
        
        # 检查是否回到之前的转折点（闭合小回线）- 不要提前弹出
        closure_target = None
        if len(self._hyst_turn_stack) > 1:
            prev_turn_I, prev_turn_B, prev_amp = self._hyst_turn_stack[-2]
            if (new_direction > 0 and I_mA >= prev_turn_I) or \
               (new_direction < 0 and I_mA <= prev_turn_I):
                closure_target = prev_turn_B
        
        # 计算B值
        if self._hyst_branch == 'virgin':
            # Virgin曲线：根据电流方向确定B的符号
            if abs_I < 1.0:
                B_new = self._hyst_B_offset
            else:
                # 根据电流方向确定B的符号
                sign = 1 if I_mA >= 0 else -1
                B_new = self._hyst_B_offset + sign * float(np.polyval(POLY_VIRGIN, abs_I))
        else:
            # 主回线阶段：根据幅度分情况处理
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
            else:
                # 300mA以下：特殊处理确保对称
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
                
                # 目标：从turn_B线性过渡到-turn_B（确保对称）
                B_new = turn_B + progress * (-turn_B - turn_B)
        
        # 如果到达闭合点，直接使用闭合目标B值
        if closure_target is not None:
            B_new = closure_target
            if len(self._hyst_turn_stack) > 1:
                self._hyst_turn_stack.pop()
                _, _, prev_amp = self._hyst_turn_stack[-1]
                self._hyst_loop_amp = prev_amp
        
        # 存储未缩放的B值用于内部计算
        self._hyst_last_I = I_mA
        self._hyst_last_B = B_new  # 存储未缩放值
        
        # 只在返回时应用样品类型的B值缩放因子
        return B_new * self._B_scale_factor
    
    def set_hysteresis_offset(self, B_offset: float):
        """设置阶段4磁滞回线的起点偏移（手动退磁完成后的残余磁场）"""
        self._hyst_B_offset = B_offset
    
    def reset_hysteresis_state(self, B_offset: float = 0.0):
        """重置阶段3磁滞回线状态，可设置起点偏移"""
        self._hyst_initialized = False
        self._hyst_last_I = 0.0
        self._hyst_last_B = B_offset
        self._hyst_direction = 0
        self._hyst_branch = 'virgin'
        self._hyst_loop_amp = 600.0       # 重置为满量程
        self._hyst_max_amp = 0.0          # 重置最大幅度
        self._hyst_turn_stack = []        # 清空转折点栈
        self._hyst_B_offset = B_offset    # 起点偏移（退磁后的残余磁场）
        self._hyst_exceed_error = False   # 重置超限错误标志
        # 同时更新全局剩磁，使get_B也使用退磁终点的值
        self._global_remanence = B_offset
        self._initialized = True  # 标记为已初始化，避免使用随机剩磁
        # 重置方向对称性状态
        self._hyst_initial_direction = None
    
    def check_hysteresis_exceed_error(self) -> bool:
        """检查是否发生超限错误（换向后电流超过最大幅度）"""
        return getattr(self, '_hyst_exceed_error', False)
    
    def clear_hysteresis_exceed_error(self):
        """清除超限错误标志"""
        self._hyst_exceed_error = False
    
    def get_branch_info(self) -> Dict[str, Any]:
        """获取当前分支信息（用于调试）"""
        # 优先返回磁滞回线状态（阶段3使用）
        if hasattr(self, '_hyst_branch'):
            return {
                'current_branch': self._hyst_branch,
                'direction': getattr(self, '_hyst_direction', 0),
                'I_prev': getattr(self, '_hyst_last_I', 0.0),
                'B_prev': getattr(self, '_hyst_last_B', 0.0),
                'initialized': getattr(self, '_hyst_initialized', False),
            }
        return {
            'current_branch': self._current_branch,
            'direction': self._direction,
            'I_prev': self._I_prev,
            'B_prev': self._B_prev,
            'initialized': self._initialized,
        }
    
    def set_sample_type(self, sample_type: str):
        """设置样品类型，更新B值缩放因子
        
        Parameters:
            sample_type: 'mold_steel' (模具钢) 或 'pure_iron' (电工纯铁)
        """
        if sample_type not in self._sample_Bs:
            print(f"Warning: Unknown sample type '{sample_type}', using mold_steel")
            sample_type = 'mold_steel'
        
        self._sample_type = sample_type
        base_Bs = self._sample_Bs['mold_steel']  # 基准饱和值 (模具钢)
        target_Bs = self._sample_Bs[sample_type]
        self._B_scale_factor = target_Bs / base_Bs
        
        print(f"Sample type set to '{sample_type}': Bs={target_Bs}mT, scale={self._B_scale_factor:.3f}")
    
    def get_sample_type(self) -> str:
        """获取当前样品类型"""
        return self._sample_type
    
    def get_B_scale_factor(self) -> float:
        """获取当前B值缩放因子"""
        return self._B_scale_factor


class PositionCouplingModel:
    """
    探针位置耦合模型
    
    根据表1数据，探针在不同位置时测得的磁场不同。
    在均匀区（-9.0mm到+7.0mm）磁场基本恒定，
    在边缘区域磁场会衰减。
    """
    
    # 表1数据：X/mm -> B/mT (I=600mA时的实测数据)
    TABLE1_DATA = [
        (-10.0, 158.5), (-9.0, 161.3), (-8.0, 161.7), (-7.0, 161.6),
        (-6.0, 161.6), (-5.0, 161.6), (-4.0, 161.6), (-3.0, 161.7),
        (-2.0, 161.4), (-1.0, 161.5), (0.0, 161.7),
        (1.0, 161.8), (2.0, 161.9), (3.0, 161.9), (4.0, 161.9),
        (5.0, 161.8), (6.0, 161.6), (7.0, 161.6),
        (8.0, 152.7), (9.0, 109.3), (10.0, 69.9)
    ]
    
    # 均匀区范围
    UNIFORM_MIN = -9.0  # mm
    UNIFORM_MAX = 7.0   # mm
    
    def __init__(self):
        self.position_data = self.TABLE1_DATA.copy()
        self.B_center = 161.7  # 中心位置的参考磁场值 (mT)
        
        # 计算均匀区的平均磁场作为参考
        center_data = [(x, b) for x, b in self.position_data 
                       if self.UNIFORM_MIN <= x <= self.UNIFORM_MAX]
        if center_data:
            self.B_center = np.mean([b for x, b in center_data])
        
        # 预计算耦合系数 = B(x) / B_center
        X_arr = np.array([d[0] for d in self.position_data])
        coupling_arr = np.array([d[1] / self.B_center for d in self.position_data])
        
        # 分段拟合：均匀区用常数1.0，边缘区用多项式
        # 左边缘 (x < -9)
        left_mask = X_arr < self.UNIFORM_MIN
        if np.sum(left_mask) >= 2:
            self.left_coeffs = np.polyfit(X_arr[left_mask], coupling_arr[left_mask], 1)
        else:
            self.left_coeffs = None
        
        # 右边缘 (x > 7)
        right_mask = X_arr > self.UNIFORM_MAX
        if np.sum(right_mask) >= 2:
            self.right_coeffs = np.polyfit(X_arr[right_mask], coupling_arr[right_mask], 2)
        else:
            self.right_coeffs = None
        
        print(f"Position coupling initialized: uniform region [{self.UNIFORM_MIN}, {self.UNIFORM_MAX}] mm, B_center={self.B_center:.1f} mT")
    
    def get_coupling(self, position_mm: float) -> float:
        """
        获取指定位置的耦合系数
        
        Parameters:
            position_mm: 探针位置 (mm)，相对于中心
        
        Returns:
            coupling: 耦合系数 (0.0 ~ 1.0+)
        """
        # 均匀区：耦合系数约为1.0
        if self.UNIFORM_MIN <= position_mm <= self.UNIFORM_MAX:
            # 在均匀区内加入微小波动（模拟真实测量）
            # 根据表1数据，均匀区内波动约±0.3%
            base_coupling = 1.0
            # 根据位置插值获取更精确的值
            for i, (x, b) in enumerate(self.position_data):
                if x == position_mm:
                    return b / self.B_center
                elif i > 0 and self.position_data[i-1][0] < position_mm < x:
                    x0, b0 = self.position_data[i-1]
                    x1, b1 = x, b
                    # 线性插值
                    t = (position_mm - x0) / (x1 - x0)
                    return (b0 + t * (b1 - b0)) / self.B_center
            return base_coupling
        
        # 左边缘衰减 (x < -9)，在-15mm处衰减到0
        if position_mm < self.UNIFORM_MIN:
            # 从-9mm(coupling≈1.0)线性衰减到-15mm(coupling=0)
            # -10mm时约0.98，按表1数据
            if position_mm <= -15.0:
                return 0.0
            # 使用表1数据点-10mm(158.5/161.7=0.98)进行插值
            # 从-9mm到-15mm线性衰减
            t = (position_mm - self.UNIFORM_MIN) / (-15.0 - self.UNIFORM_MIN)
            coupling = 1.0 * (1.0 - t)
            return max(0.0, coupling)
        
        # 右边缘衰减 (x > 7) - 急剧下降，在+15mm处衰减到0
        if position_mm > self.UNIFORM_MAX:
            if position_mm >= 15.0:
                return 0.0
            # 根据表1数据：7->161.6(1.0), 8->152.7(0.94), 9->109.3(0.68), 10->69.9(0.43)
            # 使用二次衰减模型，在15mm处衰减到0
            # 拟合: coupling = a*(15-x)^2, 当x=7时coupling=1.0 -> a = 1/64
            delta = 15.0 - position_mm
            coupling = (delta / 8.0) ** 2
            # 但要匹配表1数据，使用分段处理
            if position_mm <= 10.0:
                # 使用表1数据插值
                for i, (x, b) in enumerate(self.position_data):
                    if x == position_mm:
                        return b / self.B_center
                    elif i > 0 and self.position_data[i-1][0] < position_mm < x:
                        x0, b0 = self.position_data[i-1]
                        x1, b1 = x, b
                        t = (position_mm - x0) / (x1 - x0)
                        return (b0 + t * (b1 - b0)) / self.B_center
                # 如果超出表1范围，使用最后一个点外推
                coupling = (69.9 / self.B_center) * ((15.0 - position_mm) / 5.0)
            else:
                # 10mm到15mm：从0.43线性衰减到0
                coupling = (69.9 / self.B_center) * ((15.0 - position_mm) / 5.0)
            return max(0.0, coupling)
        
        return 1.0


# ============== 全局模型实例 ==============

_hysteresis_model: Optional[HysteresisModel] = None
_position_model: Optional[PositionCouplingModel] = None


def get_hysteresis_model() -> HysteresisModel:
    """获取磁滞模型单例"""
    global _hysteresis_model
    if _hysteresis_model is None:
        _hysteresis_model = HysteresisModel()
    return _hysteresis_model


def get_position_model() -> PositionCouplingModel:
    """获取位置耦合模型单例"""
    global _position_model
    if _position_model is None:
        _position_model = PositionCouplingModel()
    return _position_model


def reset_models(degauss_end_B: float = 0.0):
    """重置所有模型状态
    
    Parameters:
        degauss_end_B: 退磁终点的B值，默认为0
    """
    global _hysteresis_model
    if _hysteresis_model:
        _hysteresis_model.reset(degauss_end_B)


def reset_model_state():
    """重置模型状态（别名，兼容旧代码）"""
    reset_models()


def initialize_models_with_remanence():
    """初始化模型为设备开启状态（有随机剩磁）- 仅在程序启动时调用"""
    # 先获取模型（如果不存在会创建），然后初始化为有剩磁状态
    hyst_model = get_hysteresis_model()
    if hyst_model:
        hyst_model.initialize_with_remanence()


def restore_to_power_on_state():
    """恢复到电源开启状态（电源按钮点击时调用）"""
    hyst_model = get_hysteresis_model()
    if hyst_model:
        hyst_model.restore_to_power_on_state()


# ============== 主要接口函数 ==============

def get_B_from_I(I_mA: float, position_mm: float = 0.0, 
                 ambient_offset_mT: float = 0.0,
                 apply_position_coupling: bool = True,
                 degauss_mode: bool = False,
                 degauss_amplitude: float = 600.0) -> float:
    """
    根据电流和探针位置获取磁场强度
    
    这是主要的对外接口函数。
    
    Parameters:
        I_mA: 电流值 (mA)，带符号（正/负方向）
        position_mm: 探针位置 (mm)，相对于中心
        ambient_offset_mT: 环境磁场偏移 (mT)
        apply_position_coupling: 是否应用位置耦合校正
        degauss_mode: 是否处于退磁模式
        degauss_amplitude: 退磁模式下的当前幅度 (mA)
    
    Returns:
        B_mT: 磁感应强度 (mT)
    """
    # 获取磁滞模型
    hyst_model = get_hysteresis_model()
    
    # 根据模式选择计算方法
    # 如果未退磁，始终使用退磁模式的模型（带剩磁的S形曲线）
    use_degauss_model = degauss_mode or not getattr(hyst_model, '_has_degaussed', False)
    
    if use_degauss_model:
        # 使用退磁模式的模型，amplitude设为600（满量程）以显示完整剩磁效果
        amp = degauss_amplitude if degauss_mode else 600.0
        B_raw = hyst_model.get_B_for_degauss(I_mA, amp)
    else:
        B_raw = hyst_model.get_B(I_mA)
    
    # 应用位置耦合
    if apply_position_coupling:
        pos_model = get_position_model()
        coupling = pos_model.get_coupling(position_mm)
        B_coupled = B_raw * coupling
    else:
        B_coupled = B_raw
    
    # 添加环境偏移
    B_final = B_coupled + ambient_offset_mT
    
    return B_final


def get_B_for_hysteresis(I_mA: float) -> float:
    """阶段3磁滞回线测量的B值计算（模块级接口）
    
    Parameters:
        I_mA: 电流值 (mA)，带符号
    
    Returns:
        B: 磁感应强度 (mT)
    """
    hyst_model = get_hysteresis_model()
    return hyst_model.get_B_for_hysteresis(I_mA)


def get_current_branch() -> str:
    """获取当前磁滞分支名称"""
    hyst_model = get_hysteresis_model()
    return hyst_model._current_branch


def get_branch_info() -> Dict[str, Any]:
    """获取当前分支详细信息"""
    hyst_model = get_hysteresis_model()
    return hyst_model.get_branch_info()


def check_hysteresis_exceed_error() -> bool:
    """检查是否发生超限错误（换向后电流超过最大幅度）"""
    hyst_model = get_hysteresis_model()
    return hyst_model.check_hysteresis_exceed_error()


def clear_hysteresis_exceed_error():
    """清除超限错误标志"""
    hyst_model = get_hysteresis_model()
    hyst_model.clear_hysteresis_exceed_error()


def set_sample_type(sample_type: str):
    """设置样品类型（模块级接口）
    
    Parameters:
        sample_type: 'mold_steel' (模具钢) 或 'pure_iron' (电工纯铁)
    """
    hyst_model = get_hysteresis_model()
    hyst_model.set_sample_type(sample_type)


def get_sample_type() -> str:
    """获取当前样品类型"""
    hyst_model = get_hysteresis_model()
    return hyst_model.get_sample_type()


# ============== 兼容旧接口 ==============

class JilesAthertonModel:
    """
    兼容旧代码的包装类
    
    内部使用新的 HysteresisModel
    """
    
    def __init__(self, **kwargs):
        self._hyst_model = get_hysteresis_model()
        self._ambient_offset = 0.0
        self.sensor_noise_std_mT = kwargs.get('sensor_noise_std_mT', 0.0)
    
    def reset(self):
        self._hyst_model.reset()
    
    def set_ambient_offset(self, offset_mT: float):
        self._ambient_offset = float(offset_mT)
    
    def get_ambient_offset(self) -> float:
        return self._ambient_offset
    
    def get_raw_B(self, H: float) -> float:
        """
        兼容旧接口：从 H 获取 B
        
        注意：新模型直接使用 I→B，这里做一个近似转换
        H ≈ I * 5 (A/m per mA，基于线圈参数)
        """
        # 反向估算 I from H
        I_mA = H / 5.0  # 近似转换
        B_mT = self._hyst_model.get_B(I_mA)
        B_T = B_mT / 1000.0  # 转换为 Tesla
        return B_T


def physical_I_to_H(I_mA: float) -> float:
    """
    物理近似：I → H
    
    基于线圈参数：N=2000匝, L=0.238m (样品实际参数)
    H = N * I / L
    """
    I_A = I_mA / 1000.0
    N = 2000
    L = 0.238  # 23.8 cm
    return (N * I_A) / L  # ≈ 8.4 * I_mA


def I_to_H(I_mA: float, params: Dict[str, Any] = None) -> float:
    """兼容旧接口"""
    return physical_I_to_H(I_mA)


def probe_coupling(position_mm: float) -> float:
    """获取探针位置耦合系数"""
    pos_model = get_position_model()
    return pos_model.get_coupling(position_mm)


def get_measured_B(model, H: float, probe_position_mm: float,
                  ambient_offset_mT: float, sensor_noise_std_mT: float = 0.0) -> float:
    """
    兼容旧接口：获取测量的 B 值
    
    新实现直接使用 I→B 模型
    """
    # 从 H 反推 I
    I_mA = H / 5.0  # 近似
    
    # 使用新模型
    B_mT = get_B_from_I(I_mA, probe_position_mm, ambient_offset_mT, True)
    
    # 添加噪声
    if sensor_noise_std_mT > 0:
        B_mT += np.random.normal(0, sensor_noise_std_mT)

    return B_mT


# ============== 保留的旧函数（用于标定等）==============

def local_refine(branch_key: str, samples: List[Tuple[float, float, float]],
                 seconds: float = 1.0) -> Tuple[Optional[Dict[str, float]], float, float]:
    """在线微调（保留接口，新模型暂不使用）"""
    return None, float('inf'), float('inf')


def write_jiles_params_to_config(params: Dict[str, float], branch_key: str):
    """保存参数到配置（保留接口）"""
    pass


def fit_jiles_from_samples(samples: List[Tuple[float, float, float]],
                          budget_seconds: float = 600.0) -> Tuple[Dict[str, float], float]:
    """从样本拟合参数（保留接口）"""
    return {}, float('inf')


# ============== 测试代码 ==============

if __name__ == "__main__":
    print("Testing HysteresisModel...")
    
    model = get_hysteresis_model()
    model.reset()
    
    # 测试初始磁化曲线
    print("\n=== Initial magnetization (0 → 600 mA) ===")
    for I in [0, 100, 200, 300, 400, 500, 600]:
        B = get_B_from_I(float(I), 0.0, 0.0)
        info = get_branch_info()
        print(f"I={I:6.1f} mA → B={B:7.2f} mT, branch={info['current_branch']}")
    
    # 测试下降支
    print("\n=== Descending (600 → -600 mA) ===")
    for I in [600, 400, 200, 0, -200, -400, -600]:
        B = get_B_from_I(float(I), 0.0, 0.0)
        info = get_branch_info()
        print(f"I={I:6.1f} mA → B={B:7.2f} mT, branch={info['current_branch']}")
    
    # 测试上升支
    print("\n=== Ascending (-600 → 600 mA) ===")
    for I in [-600, -400, -200, 0, 200, 400, 600]:
        B = get_B_from_I(float(I), 0.0, 0.0)
        info = get_branch_info()
        print(f"I={I:6.1f} mA → B={B:7.2f} mT, branch={info['current_branch']}")
    
    # 测试位置耦合
    print("\n=== Position coupling ===")
    pos_model = get_position_model()
    for x in [-10, -5, 0, 5, 8, 10]:
        c = pos_model.get_coupling(float(x))
        print(f"X={x:3d} mm → coupling={c:.4f}")
