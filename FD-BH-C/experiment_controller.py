#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
experiment_controller.py

实验阶段控制器，管理5个实验阶段的状态机：
1. 测量 B-X 关系（找均匀区）
2. 样品退磁处理
3. 测量初始磁化曲线（电流必须单调增加）
4. 磁锻炼（自动10-20次换向）
5. 测量磁滞回线
"""
from PyQt5 import QtCore
from typing import Callable, Optional
import time


class ExperimentController(QtCore.QObject):
    """实验阶段控制器"""
    
    # 样品类型定义
    SAMPLE_MOLD_STEEL = 'mold_steel'      # 模具钢
    SAMPLE_PURE_IRON = 'pure_iron'         # 电工纯铁
    
    # 样品参数 (来自说明书)
    SAMPLE_PARAMS = {
        'mold_steel': {
            'name': '模具钢',
            'type': '半硬磁材料',
            'Bs_mT': 320,           # 饱和磁感应强度 (mT)
            'Hc_Am': 500,           # 矫顽力 (A/m)
            'Br_mT': 77,            # 剩磁 (mT)
            'l_bar_cm': 23.8,       # 平均磁路长度 (cm)
            'l_gap_cm': 0.2,        # 间隙宽度 (cm)
            'N': 2000,              # 线圈匝数
            'section_cm2': 4.0,     # 截面积 (cm²)
            'description': '宽磁滞回线，剩磁大，退磁较难'
        },
        'pure_iron': {
            'name': '电工纯铁',
            'type': '软磁材料',
            'Bs_mT': 800,           # 饱和磁感应强度 (mT) - 更高
            'Hc_Am': 80,            # 矫顽力 (A/m) - 更低
            'Br_mT': 25,            # 剩磁 (mT) - 更低
            'l_bar_cm': 23.8,       # 平均磁路长度 (cm)
            'l_gap_cm': 0.2,        # 间隙宽度 (cm)
            'N': 2000,              # 线圈匝数
            'section_cm2': 4.0,     # 截面积 (cm²)
            'description': '窄磁滞回线，剩磁小，易退磁'
        }
    }
    
    # 信号定义
    stage_changed = QtCore.pyqtSignal(int, str)  # (阶段号, 阶段名称)
    warning_triggered = QtCore.pyqtSignal(str)  # 警告消息
    error_triggered = QtCore.pyqtSignal(str)  # 错误消息（需要退磁重来）
    degauss_progress = QtCore.pyqtSignal(float, float)  # (时间, B值) 退磁进度
    training_progress = QtCore.pyqtSignal(int, int)  # (当前次数, 总次数) 磁锻炼进度
    
    # 阶段定义 (0=选样品, 1=B-X, 2=退磁, 3=锻炼, 4=回线)
    STAGE_SELECT_SAMPLE = 0   # 选择样品
    STAGE_BX_MEASURE = 1      # 测量 B-X 关系
    STAGE_DEGAUSS = 2         # 退磁处理
    STAGE_TRAINING = 3        # 磁锻炼
    STAGE_HYSTERESIS = 4      # 磁滞回线测量
    
    STAGE_NAMES = {
        0: "选择样品",
        1: "测量 B-X 关系",
        2: "退磁处理",
        3: "磁锻炼",
        4: "磁滞回线测量"
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_stage = self.STAGE_SELECT_SAMPLE  # 从选样品开始
        self._selected_sample = None  # 当前选择的样品
        self._last_I_mA = 0.0  # 上次记录的电流（用于单调性检测）
        self._monotonic_violation = False
        self._training_count = 0
        self._training_target = 15  # 默认15次磁锻炼
        self._is_training = False
        self._degauss_start_time = 0.0
        
    @property
    def current_stage(self) -> int:
        return self._current_stage
    
    @property
    def current_stage_name(self) -> str:
        return self.STAGE_NAMES.get(self._current_stage, "未知")
    
    def select_sample(self, sample_type: str):
        """选择样品类型"""
        if sample_type in self.SAMPLE_PARAMS:
            self._selected_sample = sample_type
            return self.SAMPLE_PARAMS[sample_type]
        return None
    
    @property
    def selected_sample(self) -> str:
        return self._selected_sample
    
    @property
    def selected_sample_params(self) -> dict:
        if self._selected_sample:
            return self.SAMPLE_PARAMS.get(self._selected_sample, {})
        return {}
    
    def set_stage(self, stage: int):
        """设置当前阶段"""
        if 0 <= stage <= 4:
            old_stage = self._current_stage
            self._current_stage = stage
            # 重置阶段相关状态
            if stage == self.STAGE_TRAINING:
                self._training_count = 0
                self._is_training = False
            elif stage == self.STAGE_DEGAUSS:
                self._degauss_start_time = time.time()
            
            self.stage_changed.emit(stage, self.STAGE_NAMES[stage])
    
    def next_stage(self):
        """进入下一阶段"""
        if self._current_stage < 4:
            self.set_stage(self._current_stage + 1)
    
    def prev_stage(self):
        """返回上一阶段"""
        if self._current_stage > 0:
            self.set_stage(self._current_stage - 1)
    
    def check_monotonic(self, I_mA: float) -> bool:
        """
        检查电流单调性（保留接口兼容性）
        返回 True 表示通过检查
        """
        return True
    
    def record_initial_mag_point(self, I_mA: float) -> bool:
        """
        记录数据点前的检查（保留接口兼容性）
        返回 True 表示可以记录
        """
        return True
    
    def start_degauss(self):
        """开始退磁"""
        self._degauss_start_time = time.time()
        if self._current_stage != self.STAGE_DEGAUSS:
            self.set_stage(self.STAGE_DEGAUSS)
    
    def update_degauss(self, B_mT: float):
        """更新退磁进度"""
        elapsed = time.time() - self._degauss_start_time
        self.degauss_progress.emit(elapsed, B_mT)
    
    def is_degauss_complete(self, B_mT: float, threshold: float = 0.5) -> bool:
        """检查退磁是否完成（B接近0）"""
        return abs(B_mT) < threshold
    
    def start_training(self, cycles: int = 15):
        """开始磁锻炼"""
        self._training_target = cycles
        self._training_count = 0
        self._is_training = True
        if self._current_stage != self.STAGE_TRAINING:
            self.set_stage(self.STAGE_TRAINING)
        self.training_progress.emit(0, cycles)
    
    def update_training(self, cycle: int):
        """更新磁锻炼进度"""
        self._training_count = cycle
        self.training_progress.emit(cycle, self._training_target)
    
    def is_training_complete(self) -> bool:
        """检查磁锻炼是否完成"""
        return self._training_count >= self._training_target
    
    def stop_training(self):
        """停止磁锻炼"""
        self._is_training = False
    
    @property
    def is_training_active(self) -> bool:
        return self._is_training
    
    def reset_for_retry(self):
        """重置状态以便重新开始（退磁后调用）"""
        self._last_I_mA = 0.0
        self._monotonic_violation = False
        self._training_count = 0
        self._is_training = False
    
    def can_proceed_to_hysteresis(self) -> bool:
        """检查是否可以进入磁滞回线测量"""
        # 必须完成磁锻炼
        if self._current_stage < self.STAGE_TRAINING:
            self.warning_triggered.emit("请先完成磁锻炼")
            return False
        return True
    
    def can_proceed_from_sample_select(self) -> bool:
        """检查是否可以从选样品阶段进入下一阶段"""
        if self._selected_sample is None:
            self.warning_triggered.emit("请先选择样品！")
            return False
        return True
    
    def get_stage_instructions(self) -> str:
        """获取当前阶段的操作说明"""
        instructions = {
            self.STAGE_SELECT_SAMPLE: (
                "【阶段0：选择样品】\n"
                "请选择实验使用的样品类型：\n"
                "- 模具钢：半硬磁材料，磁滞回线宽\n"
                "- 电工纯铁：软磁材料，磁滞回线窄\n"
                "选择后点击[下一阶段]"
            ),
            self.STAGE_BX_MEASURE: (
                "【阶段1：测量 B-X 关系】\n"
                "1. 设置固定电流值\n"
                "2. 移动探针位置，记录不同位置的B值\n"
                "3. 找到磁场均匀区（B变化最小的区域）\n"
                "4. 完成后点击[下一阶段]进入退磁"
            ),
            self.STAGE_DEGAUSS: (
                "【阶段2：退磁处理】\n"
                "1. 点击[开始退磁]按钮\n"
                "2. 观察B-H曲线趋近于原点\n"
                "3. 退磁完成后点击[下一阶段]"
            ),
            self.STAGE_TRAINING: (
                "【阶段3：磁锻炼】\n"
                "1. 点击[开始磁锻炼]按钮\n"
                "2. 系统将自动进行10-20次电流换向\n"
                "3. 等待磁锻炼完成\n"
                "4. 完成后点击[下一阶段]测量磁滞回线"
            ),
            self.STAGE_HYSTERESIS: (
                "【阶段4：磁滞回线测量】\n"
                "1. 从最大正向电流开始\n"
                "2. 逐步减小到最大负向电流\n"
                "3. 再逐步增加回最大正向电流\n"
                "4. 记录完整的I-B-H数据"
            )
        }
        return instructions.get(self._current_stage, "")
