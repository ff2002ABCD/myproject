#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_manager.py

数据管理模块，管理多种实验数据：
- 表A: 间隙 X vs B（均匀区测量）
- 表B: I,B,H（磁滞回线测量）
- 退磁曲线: B vs t（时间序列，无表格显示）
- 初始磁化曲线: I,B,H（首次磁化）

支持 CSV 导入/导出、会话保存/加载（JSON）。
"""
from typing import List, Dict, Tuple
import csv
import json
import os
import time


class DataManager:
    def __init__(self):
        # store rows as list of dicts
        self.tableA: List[Dict] = []  # rows with keys: 'X/mm','B/mT','remark'
        self.tableB: List[Dict] = []  # rows with keys: 'I/mA','B/mT','H/A_m','remark'
        
        # 新增数据存储
        self.degauss_curve: List[Dict] = []  # 退磁曲线: {'t': 时间, 'B': 磁场, 'I': 电流}
        self.initial_mag_curve: List[Dict] = []  # 初始磁化曲线: {'I/mA', 'B/mT', 'H/A_m'}
        
        # 实验状态
        self.experiment_stage = 1  # 当前实验阶段 1-5
        self.degauss_start_time = 0  # 退磁开始时间
        self.last_recorded_I = 0.0  # 上次记录的电流值（用于单调性检测）
        self.monotonic_violation = False  # 是否违反单调性

    def add_row(self, table: str, row: Dict):
        if table == 'A':
            self.tableA.append(row)
        elif table == 'B':
            self.tableB.append(row)
        else:
            raise ValueError("Unknown table")

    def delete_row(self, table: str, index: int):
        if table == 'A':
            del self.tableA[index]
        elif table == 'B':
            del self.tableB[index]

    def get_table(self, table: str) -> List[Dict]:
        if table == 'A':
            return self.tableA
        elif table == 'B':
            return self.tableB
        else:
            raise ValueError("Unknown table")

    def clear_table(self, table: str):
        if table == 'A':
            self.tableA = []
        elif table == 'B':
            self.tableB = []

    def export_csv(self, table: str, path: str) -> int:
        rows = self.get_table(table)
        # Build headers: prefer canonical set but include both H variants and any extra keys present
        if table == 'A':
            base_headers = ['X/mm', 'B/mT', 'remark']
        else:
            # include both common H column variants so exported CSV contains H regardless of internal key name
            base_headers = ['I/mA', 'B/mT', 'H/(A/m)', 'H/A_m', 'remark']
        # collect additional keys present in rows (preserve deterministic order)
        extra_keys = []
        for r in rows:
            for k in r.keys():
                if k not in base_headers and k not in extra_keys:
                    extra_keys.append(k)
        headers = base_headers + extra_keys
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for r in rows:
                # ensure keys present; support both H key variants when only one exists
                out = {}
                for h in headers:
                    if h == 'H/A_m':
                        out[h] = r.get('H/A_m', r.get('H/(A/m)', r.get('H', '')))
                    elif h == 'H/(A/m)':
                        out[h] = r.get('H/(A/m)', r.get('H/A_m', r.get('H', '')))
                    else:
                        out[h] = r.get(h, '')
                writer.writerow(out)
        return len(rows)

    def import_csv(self, path: str) -> Tuple[str, int]:
        """
        自动检测 CSV 类型并导入到表A或表B。
        返回 (table_name, count)
        """
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = [h.strip() for h in reader.fieldnames] if reader.fieldnames else []
            # detection
            hlower = [h.lower() for h in headers]
            if any('x' in h or 'position' in h for h in hlower) and any('b' in h for h in hlower):
                target = 'A'
            elif any('i' in h for h in hlower) and any('h' in h for h in hlower):
                target = 'B'
            else:
                # fallback: if columns include I and B assume B
                if 'i' in ''.join(hlower) and 'b' in ''.join(hlower):
                    target = 'B'
                else:
                    target = 'A'
            count = 0
            for row in reader:
                if target == 'A':
                    mapped = {
                        'X/mm': row.get(headers[0], '').strip() if headers else '',
                        'B/mT': row.get(headers[1], '').strip() if len(headers) > 1 else '',
                        'remark': row.get(headers[2], '').strip() if len(headers) > 2 else ''
                    }
                    self.tableA.append(mapped)
                else:
                    mapped = {
                        'I/mA': row.get(headers[0], '').strip() if headers else '',
                        'B/mT': row.get(headers[1], '').strip() if len(headers) > 1 else '',
                        'H/A_m': row.get(headers[2], '').strip() if len(headers) > 2 else '',
                        'remark': row.get(headers[3], '').strip() if len(headers) > 3 else ''
                    }
                    self.tableB.append(mapped)
                count += 1
        return target, count

    def save_session(self, path: str):
        payload = {
            'tableA': self.tableA,
            'tableB': self.tableB,
            'degauss_curve': self.degauss_curve,
            'initial_mag_curve': self.initial_mag_curve,
            'experiment_stage': self.experiment_stage,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def load_session(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        self.tableA = payload.get('tableA', [])
        self.tableB = payload.get('tableB', [])
        self.degauss_curve = payload.get('degauss_curve', [])
        self.initial_mag_curve = payload.get('initial_mag_curve', [])

    # ==================== 退磁曲线相关 ====================
    
    def start_degauss(self):
        """开始退磁，清空退磁曲线并记录开始时间"""
        self.degauss_curve = []
        self.degauss_start_time = time.time()
    
    def add_degauss_point(self, I_mA: float, B_mT: float, H_Am: float = None):
        """
        添加退磁曲线数据点
        退磁曲线是 B-H 曲线，I_mA 可以是带符号的值
        
        Parameters:
            I_mA: 电流值 (mA)，可以是正或负
            B_mT: 磁感应强度 (mT)
            H_Am: 磁场强度 (A/m)，如果为None则根据I计算
        """
        t = time.time() - self.degauss_start_time
        # 如果没有提供H值，根据I计算（简单线性关系）
        if H_Am is None:
            # H = N * I / L，假设 N=1000, L=0.1m
            H_Am = I_mA * 10.0  # 简化计算
        self.degauss_curve.append({
            't': t, 
            'I': float(I_mA),  # 保留符号
            'B': float(B_mT), 
            'H': float(H_Am)   # 保留符号
        })
    
    def get_degauss_curve(self) -> List[Dict]:
        """获取退磁曲线数据"""
        return self.degauss_curve
        
    def clear_degauss_curve(self):
        """清空退磁曲线"""
        self.degauss_curve = []

    # ==================== 初始磁化曲线相关 ====================
    
    def add_initial_mag_point(self, I_mA: float, B_mT: float, H_Am: float) -> bool:
        """
        添加初始磁化曲线数据点
        返回 True 表示成功，False 表示违反单调性
        """
        # 检查电流单调性（必须单调增加）
        if self.initial_mag_curve:
            last_I = self.initial_mag_curve[-1].get('I/mA', 0)
            if I_mA < last_I - 0.1:  # 允许0.1mA的误差
                self.monotonic_violation = True
                return False
        
        self.initial_mag_curve.append({
            'I/mA': I_mA,
            'B/mT': B_mT,
            'H/A_m': H_Am
        })
        self.last_recorded_I = I_mA
        self.monotonic_violation = False
        return True
    
    def get_initial_mag_curve(self) -> List[Dict]:
        """获取初始磁化曲线数据"""
        return self.initial_mag_curve
    
    def clear_initial_mag_curve(self):
        """清空初始磁化曲线"""
        self.initial_mag_curve = []
        self.last_recorded_I = 0.0
        self.monotonic_violation = False

    # ==================== 实验阶段管理 ====================
    
    def set_stage(self, stage: int):
        """设置当前实验阶段 (1-5)"""
        self.experiment_stage = max(1, min(5, stage))
    
    def get_stage(self) -> int:
        """获取当前实验阶段"""
        return self.experiment_stage
    
    def reset_experiment(self):
        """重置实验（退磁后重新开始）"""
        self.clear_initial_mag_curve()
        self.clear_table('B')
        self.monotonic_violation = False








