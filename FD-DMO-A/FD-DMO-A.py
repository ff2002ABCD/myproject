import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
import sys
import pandas as pd
import json
import math  # 添加这行

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


class MenuSystem:
    """菜单系统 - 管理主机界面上的菜单显示"""
    
    def __init__(self, parent, app, 
                 menu_x=50, menu_y=380, menu_width=500, menu_height=200,
                 btn_up_x=50, btn_up_y=600,
                 btn_down_x=120, btn_down_y=600,
                 btn_confirm_x=190, btn_confirm_y=600,
                 btn_back_x=260, btn_back_y=600,
                 btn_vol_up_x=50, btn_vol_up_y=635,
                 btn_vol_down_x=160, btn_vol_down_y=635):
        """
        初始化菜单系统
        """
        self.parent = parent
        self.app = app
        
        self.stop_voltage_params = {
            405: 0.70,
            450: 0.98,
            510: 1.32,
            532: 1.426,
            635: 1.778,
            650: 1.848,
            685: 1.874
        }

        # 菜单位置
        self.menu_x = menu_x
        self.menu_y = menu_y
        self.menu_width = menu_width
        self.menu_height = menu_height
        
        # 电压长按变量
        self.voltage_repeat_id = None
        self.voltage_direction = 0

        # 每个按钮单独位置
        self.btn_up_x = btn_up_x
        self.btn_up_y = btn_up_y
        self.btn_down_x = btn_down_x
        self.btn_down_y = btn_down_y
        self.btn_confirm_x = btn_confirm_x
        self.btn_confirm_y = btn_confirm_y
        self.btn_back_x = btn_back_x
        self.btn_back_y = btn_back_y
        self.btn_vol_up_x = btn_vol_up_x
        self.btn_vol_up_y = btn_vol_up_y
        self.btn_vol_down_x = btn_vol_down_x
        self.btn_vol_down_y = btn_vol_down_y
        
        # 初始化变量
        self.menu_items = []
        self.current_index = 0
        self.current_menu = "main"
        self.menu_labels = []  # 先初始化
        
        # 其他状态变量
        self.is_measuring = False
        self.measuring_timer = None
        self.measuring_data = {"U": [], "I": []}
        self.current_measure_wavelength = 405
        self.current_measure_type = None
        self.zero_offset = 0.0
        
        # 手动测量数据
        self.manual_iv_voltage = 0.0
        self.manual_iv_data = {"U": [], "I": []}
        self.manual_stop_voltage = 0.0
        self.manual_stop_data = {"U": [], "I": []}
        
        # 自动测量变量
        self.auto_iv_step = 0
        self.auto_iv_voltage = 0.0
        self.auto_stop_start_v = -2.0
        self.auto_stop_end_v = 0.0
        self.auto_stop_voltage = -2.0

        # 菜单数据结构
        self.menus = {
            "main": {
                "items": ["手动测量", "自动测量"],
                "actions": ["manual_select", "auto_select"]
            },
            "manual_select": {
                "items": ["测量伏安特性", "测量截止电压"],
                "actions": ["manual_iv", "manual_stop"]
            },
            "manual_iv": {
                "items": ["偏置电压: 0.0V", "光电流: 0.0×10^-10A"],
                "actions": [None, None],
                "is_measure": True
            },
            "manual_stop": {
                "items": ["偏置电压: 0.000V", "光电流: 0.0×10^-10A"],
                "actions": [None, None],
                "is_measure": True
            },
            "auto_select": {
                "items": ["测量伏安特性", "测量截止电压", "伏安特性数据查询", "截止电压数据查询"],
                "actions": ["auto_iv", "auto_stop", "auto_iv_query", "auto_stop_query"]
            },
            "auto_iv": {
                "items": ["请在调零后开始测量", "光电流: 0.0×10^-10A", "波长设置: 405nm", "测量"],
                "actions": [None, None, None, "auto_iv_start"]
            },
            "auto_iv_measuring": {
                "items": ["自动测量中..."],
                "actions": [None],
                "is_measuring": True
            },
            "auto_iv_save": {
                "items": ["是否保存数据?", "保存", "不保存"],
                "actions": [None, "auto_iv_save_yes", "auto_iv_save_no"]
            },
            "auto_stop": {
                "items": ["请在调零后开始测量", "光电流: 0.0×10^-10A", "波长设置: 405nm", "起始电压: -2.0V", "终止电压: 0.0V", "测量"],
                "actions": [None, None, None, "edit_start_voltage", "edit_end_voltage", "auto_stop_start"]
            },
            "auto_stop_measuring": {
                "items": ["自动测量中..."],
                "actions": [None],
                "is_measuring": True
            },
            "auto_stop_save": {
                "items": ["是否保存数据?", "保存", "不保存"],
                "actions": [None, "auto_stop_save_yes", "auto_stop_save_no"]
            },
            "auto_iv_query": {
                "items": ["选择波长: 405nm"],
                "actions": ["auto_iv_query_confirm"]
            },
            "auto_stop_query": {
                "items": ["选择波长: 405nm"],
                "actions": ["auto_stop_query_confirm"]
            }
        }
        
        # 所有波长列表
        self.wavelengths = ["405nm", "450nm", "510nm", "532nm", "635nm", "650nm", "685nm"]
        self.wavelength_values = [405, 450, 510, 532, 635, 650, 685]
        self.query_wavelength_index = 0
        
        # 存储不同波长的伏安特性数据
        self.iv_data = {}  # {wavelength: {"U": [], "I": []}}
        # 存储不同波长的截止电压数据
        self.stop_data = {}  # {wavelength: {"U": [], "I": []}}
        
        # 当前测量状态
        self.is_measuring = False
        self.measuring_timer = None
        self.measuring_data = {"U": [], "I": []}
        self.current_measure_wavelength = 405
        self.current_measure_type = None  # "iv" or "stop"
        
        # 伏安特性手动测量状态
        self.manual_iv_voltage = 0.0
        self.manual_iv_data = {"U": [], "I": []}
        
        # 截止电压手动测量状态
        self.manual_stop_voltage = 0.0
        self.manual_stop_data = {"U": [], "I": []}
        
        # 调零状态
        self.zero_offset = 0.0
        
        # 创建菜单显示
        self.create_menu_overlay()
    
    def voltage_up_press(self, event):
        """电压加号长按开始"""
        # 先执行一次点击
        self.voltage_up()
        # 然后开始长按重复
        self.voltage_direction = 1
        self.voltage_repeat_id = self.parent.after(300, self.start_voltage_repeat)

    def voltage_down_press(self, event):
        """电压减号长按开始"""
        # 先执行一次点击
        self.voltage_down()
        # 然后开始长按重复
        self.voltage_direction = -1
        self.voltage_repeat_id = self.parent.after(300, self.start_voltage_repeat)

    def voltage_release(self, event):
        """电压长按释放"""
        self.voltage_direction = 0
        if self.voltage_repeat_id:
            self.parent.after_cancel(self.voltage_repeat_id)
            self.voltage_repeat_id = None

    def start_voltage_repeat(self):
        """开始电压长按重复"""
        if self.voltage_direction == 1:
            self.voltage_up()
        elif self.voltage_direction == -1:
            self.voltage_down()
        else:
            return
        # 每100ms重复一次
        self.voltage_repeat_id = self.parent.after(100, self.start_voltage_repeat)

    def edit_start_voltage(self):
        """编辑起始电压"""
        # 弹出输入对话框
        import tkinter.simpledialog as sd
        current = self.menu_items[3].split(": ")[1].replace("V", "")
        result = sd.askstring("输入起始电压", "请输入起始电压 (-2.0 ~ -0.1):", 
                            initialvalue=current, parent=self.parent)
        if result:
            try:
                val = float(result)
                val = max(-2.0, min(-0.1, val))
                self.menu_items[3] = f"起始电压: {val:.1f}V"
                # 检查终止电压是否合法
                end_val = float(self.menu_items[4].split(": ")[1].replace("V", ""))
                if end_val <= val + 0.1:
                    end_val = val + 0.1
                    self.menu_items[4] = f"终止电压: {end_val:.1f}V"
                self.update_measure_display()
            except ValueError:
                messagebox.showerror("错误", "请输入有效数字")

    def edit_end_voltage(self):
        """编辑终止电压"""
        import tkinter.simpledialog as sd
        current = self.menu_items[4].split(": ")[1].replace("V", "")
        start_val = float(self.menu_items[3].split(": ")[1].replace("V", ""))
        result = sd.askstring("输入终止电压", f"请输入终止电压 (>{start_val:.1f}V, <=0):", 
                            initialvalue=current, parent=self.parent)
        if result:
            try:
                val = float(result)
                val = max(start_val + 0.1, min(0.0, val))
                self.menu_items[4] = f"终止电压: {val:.1f}V"
                self.update_measure_display()
            except ValueError:
                messagebox.showerror("错误", "请输入有效数字")

    def create_menu_overlay(self):
        """在主机背景图上创建菜单覆盖层"""
        # 创建菜单 - 改小尺寸
        self.menu_frame = tk.Frame(self.parent, bg='#ffffff', bd=1, relief=tk.RAISED)
        self.menu_frame.place(x=self.menu_x, y=self.menu_y, 
                            width=self.menu_width, height=self.menu_height)
        
        # 菜单显示区域 - 减小内边距
        self.menu_display = tk.Frame(self.menu_frame, bg='#ffffff')
        self.menu_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 初始化菜单标签列表
        self.menu_labels = []
        
        # 每个按钮单独放置
        btn_up = tk.Button(self.parent, text="", font=("Microsoft YaHei", 6), 
                        bg='#545454', fg='#545454', width=1,height=1,relief="flat",
                        command=self.menu_up)
        btn_up.place(x=239, y=98)
        
        btn_down = tk.Button(self.parent, text="", font=("Microsoft YaHei", 6),
                            bg='#545454', fg='#545454', width=1,height=1,relief="flat",
                            command=self.menu_down)
        btn_down.place(x=239, y=149)
        
        btn_confirm = tk.Button(self.parent, text="",font=("Microsoft YaHei", 6),
                            bg='#545454', fg='#545454', width=1,height=1,relief="flat",
                            command=self.menu_confirm)
        btn_confirm.place(x=294, y=98)
        
        btn_back = tk.Button(self.parent, text="", font=("Microsoft YaHei", 6),
                            bg='#545454', fg='#545454', width=1,height=1,relief="flat",
                            command=self.menu_back)
        btn_back.place(x=294, y=149)
        
        # 电压增加按钮
        btn_vol_up = tk.Button(self.parent, text="+", font=("Microsoft YaHei", 7),
                            bg='#545454', fg='white', width=1,height=1,relief="flat")
        btn_vol_up.place(x=350, y=155)
        btn_vol_up.bind("<ButtonPress-1>", self.voltage_up_press)
        btn_vol_up.bind("<ButtonRelease-1>", self.voltage_release)
        
        # 电压减小按钮
        btn_vol_down = tk.Button(self.parent, text="-", font=("Microsoft YaHei", 7),
                                bg='#545454', fg='white', width=1,height=1,relief="flat")
        btn_vol_down.place(x=400, y=155)
        btn_vol_down.bind("<ButtonPress-1>", self.voltage_down_press)
        btn_vol_down.bind("<ButtonRelease-1>", self.voltage_release)
        
        # 长按定时器
        self.voltage_repeat_id = None
        self.voltage_direction = 0
        
        # 显示主菜单
        self.show_menu("main")
            
    def show_menu(self, menu_name):
        """显示指定菜单"""
        self.current_menu = menu_name
        menu = self.menus.get(menu_name)
        if not menu:
            return
        
        # 进入手动测量界面时清空数据
        if menu_name == "manual_iv":
            self.manual_iv_voltage = 0.0
            self.manual_iv_data = {"U": [], "I": []}
            self.clear_table_display()
            # 显示记录数据按钮
            if hasattr(self, 'btn_record'):
                self.btn_record.place(x=360, y=180)
        elif menu_name == "manual_stop":
            self.manual_stop_voltage = 0.0
            self.manual_stop_data = {"U": [], "I": []}
            self.clear_table_display()

        items = menu["items"]
        self.menu_items = items
        
        # 对于 auto_iv，固定高亮最后一项（测量）
        if menu_name == "auto_iv":
            self.current_index = len(items) - 1
        # 对于 auto_stop，如果有起始/终止电压，高亮起始电压（第4项，索引3）
        elif menu_name == "auto_stop":
            self.current_index = 3  # 高亮"起始电压"
        else:
            self.current_index = 0
        
        # 清空显示区域
        for label in self.menu_labels:
            label.destroy()
        self.menu_labels = []
        
        # 创建菜单项 - 白底黑字
        for i, item in enumerate(items):
            # 如果是 auto_iv 或 auto_stop 的"测量"按钮，电源关闭时显示灰色
            if menu_name == "auto_iv" and i == len(items) - 1:
                if self.app.power_on:
                    bg_color = '#e94560'
                    fg_color = '#ffffff'
                else:
                    bg_color = '#cccccc'
                    fg_color = '#666666'
            elif menu_name == "auto_stop" and i == len(items) - 1:
                if self.app.power_on:
                    bg_color = '#e94560'
                    fg_color = '#ffffff'
                else:
                    bg_color = '#cccccc'
                    fg_color = '#666666'
            elif i == self.current_index:
                bg_color = '#d3d3d3'
                fg_color = '#000000'
            else:
                bg_color = '#ffffff'
                fg_color = '#000000'
                
            label = tk.Label(self.menu_display, text=item, font=("Microsoft YaHei", 7),
                        bg=bg_color, fg=fg_color, anchor='w', padx=15, pady=0)
            label.pack(fill=tk.X, pady=0)
            self.menu_labels.append(label)
                
        # 如果是测量界面，高亮第一行（电压）
        if menu.get("is_measure"):
            self.update_measure_display()
            
        # 如果是自动测量查询界面
        if menu_name in ["auto_iv_query", "auto_stop_query"]:
            self.update_query_display()
        
    def clear_table_display(self):
        """清空表格显示"""
        # 只有伏安特性模式才清空
        if self.app.current_table_mode != "iv":
            return
        
        for row in self.app.table_entries:
            row[0].delete(0, tk.END)
            row[1].delete(0, tk.END)
        self.app.update_plot()

    def update_measure_display(self):
        """更新测量界面的显示"""
        if self.current_menu == "manual_iv":
            self.menu_items[0] = f"偏置电压: {self.manual_iv_voltage:.1f}V"
            wavelength_str = self.app.wavelength_var.get()
            wavelength = int(wavelength_str.replace('nm', ''))
            current_value = self.calculate_current(self.manual_iv_voltage, wavelength)
            
            range_str = self.app.current_range_var.get()
            exponent = int(range_str.split('^')[-1])
            scale_factor = 10 ** (-10 - exponent)
            current_display = current_value * scale_factor
            
            self.menu_items[1] = f"光电流: {current_display:.1f}×{range_str}A"
            
            if len(self.menu_labels) >= 2:
                self.menu_labels[0].config(text=self.menu_items[0])
                self.menu_labels[1].config(text=self.menu_items[1])
                    
        elif self.current_menu == "manual_stop":
            self.menu_items[0] = f"偏置电压: {self.manual_stop_voltage:.3f}V"
            wavelength_str = self.app.wavelength_var.get()
            wavelength = int(wavelength_str.replace('nm', ''))
            current_value = self.calculate_current(self.manual_stop_voltage, wavelength)
            
            range_str = self.app.current_range_var.get()
            exponent = int(range_str.split('^')[-1])
            scale_factor = 10 ** (-10 - exponent)
            current_display = current_value * scale_factor
            
            self.menu_items[1] = f"光电流: {current_display:.1f}×{range_str}A"
            
            if len(self.menu_labels) >= 2:
                self.menu_labels[0].config(text=self.menu_items[0])
                self.menu_labels[1].config(text=self.menu_items[1])
        
        elif self.current_menu in ["auto_iv", "auto_stop"]:
            # 自动测量界面：更新波长和光电流
            self.update_auto_wavelength_display()
                        
    def update_query_display(self):
        """更新查询界面的显示"""
        wavelength = self.wavelengths[self.query_wavelength_index]
        self.menu_items[0] = f"选择波长: {wavelength}"
        if self.menu_labels:
            self.menu_labels[0].config(text=self.menu_items[0])
            
    def calculate_current(self, voltage, wavelength, mode="iv"):
        """
        根据电压和波长计算光电流（返回10^-10A单位的数值）
        mode: 保留参数用于兼容，实际由电源状态决定
        """
        # 根据电源状态选择计算方法
        if self.app.power_on:
            # 电源开启：使用伏安特性模式（负电压时自动切换到截止电压模式）
            return self.calculate_current_iv(voltage, wavelength)
        else:
            # 电源关闭：使用截止电压模式
            return self.calculate_current_stop(voltage, wavelength)

    def calculate_current_iv(self, voltage, wavelength):
        """伏安特性模式 - 计算光电流"""
        # 当电压小于等于0时，使用截止电压模式的计算方法
        if voltage <= 0:
            return self.calculate_current_stop(voltage, wavelength)
        
        if not self.app.table_data:
            return 0
        
        wavelength_factor = self.get_wavelength_factor(wavelength)
        max_current = min(87.0 * wavelength_factor, 100)
        
        k = 0.05 + (wavelength - 350) / 500 * 0.15
        k = max(0.03, min(0.25, k))
        
        voltage_offset = 0.5
        exp_voltage = max(0, voltage + voltage_offset)
        
        current = max_current * (1 - math.exp(-k * exp_voltage))
        
        # 偏振片影响
        polarizer_angle = self.app.polarizer_angle
        angle_diff = polarizer_angle - 180
        polarizer_factor = 1 + abs(angle_diff) * (-1.0) * 0.001
        polarizer_factor = max(0, polarizer_factor)
        current = current * polarizer_factor
        
        current = current + self.zero_offset
        
        return current

    def calculate_current_stop(self, voltage, wavelength):
        """截止电压模式 - 计算光电流"""
        # 截止电压模式：电压-2V时电流为-75.0×10^-13A
        # 电压每增大x，光电流增大75.0×10^-13A
        base_current = -75.0 * 1e-13  # -75.0×10^-13 A
        base_voltage = -2.0  # 基准电压
        
        # 获取该波长对应的x值（电压变化量）
        x = self.stop_voltage_params.get(wavelength, 0.98)
        
        # 计算相对于基准电压的变化量
        delta_v = voltage - base_voltage
        
        # 如果电压小于基准电压，电流保持不变（-75.0×10^-13A）
        if delta_v < 0:
            current = base_current
        else:
            # 电压每增大x，电流增大75.0×10^-13A
            steps = delta_v / x
            current = base_current + steps * 75.0 * 1e-13
        
        # 转换为10^-10A单位
        current = current / 1e-10
        
        # 调零偏移
        current = current + self.zero_offset
        
        # 偏振片影响
        polarizer_angle = self.app.polarizer_angle
        angle_diff = polarizer_angle - 180
        polarizer_factor = 1 + abs(angle_diff) * (-1.0) * 0.001
        polarizer_factor = max(0, polarizer_factor)
        current = current * polarizer_factor
        
        return current

    def get_wavelength_factor(self, wavelength):
        """
        根据波长计算调整系数
        波长越大，电流上升越快，饱和越快
        """
        base_wavelength = 450
        
        # 使用更平滑的曲线
        ratio = (wavelength - base_wavelength) / base_wavelength
        
        if wavelength >= base_wavelength:
            # 长波长：系数从1.0到1.6
            factor = 1.0 + ratio * 1.0
        else:
            # 短波长：系数从0.6到1.0
            factor = 1.0 + ratio * 0.7
                
        # 限制范围
        factor = max(0.4, min(1.6, factor))
        return factor
        
    def menu_up(self):
        """向上导航"""
        if self.is_measuring:
            return
            
        if self.current_menu in ["manual_iv", "manual_stop"]:
            return
            
        # auto_iv 禁止切换高亮
        if self.current_menu == "auto_iv":
            return
            
        # auto_stop 可以在起始电压、终止电压、测量之间切换
        if self.current_menu == "auto_stop":
            if self.menu_labels:
                # 只在索引3(起始电压)、4(终止电压)、5(测量)之间切换
                valid_indices = [3, 4, 5]
                current_pos = valid_indices.index(self.current_index)
                current_pos = (current_pos - 1) % len(valid_indices)
                self.current_index = valid_indices[current_pos]
                self.update_menu_highlight()
            return
            
        if self.current_menu in ["auto_iv_query", "auto_stop_query"]:
            self.query_wavelength_index = (self.query_wavelength_index - 1) % len(self.wavelengths)
            self.update_query_display()
            return
            
        if self.menu_labels:
            self.current_index = (self.current_index - 1) % len(self.menu_labels)
            self.update_menu_highlight()

    def menu_down(self):
        """向下导航"""
        if self.is_measuring:
            return
            
        if self.current_menu in ["manual_iv", "manual_stop"]:
            return
            
        # auto_iv 禁止切换高亮
        if self.current_menu == "auto_iv":
            return
            
        # auto_stop 可以在起始电压、终止电压、测量之间切换
        if self.current_menu == "auto_stop":
            if self.menu_labels:
                valid_indices = [3, 4, 5]
                current_pos = valid_indices.index(self.current_index)
                current_pos = (current_pos + 1) % len(valid_indices)
                self.current_index = valid_indices[current_pos]
                self.update_menu_highlight()
            return
            
        if self.current_menu in ["auto_iv_query", "auto_stop_query"]:
            self.query_wavelength_index = (self.query_wavelength_index + 1) % len(self.wavelengths)
            self.update_query_display()
            return
            
        if self.menu_labels:
            self.current_index = (self.current_index + 1) % len(self.menu_labels)
            self.update_menu_highlight()

    def update_menu_highlight(self):
        """更新菜单高亮"""
        for i, label in enumerate(self.menu_labels):
            if i == self.current_index:
                # 高亮选中项 - 浅灰色背景
                label.config(bg='#d3d3d3', fg='#000000')
            else:
                # 测量按钮保持红色
                if self.current_menu == "auto_iv" and i == len(self.menu_labels) - 1:
                    label.config(bg='#e94560', fg='#ffffff')
                elif self.current_menu == "auto_stop" and i == len(self.menu_labels) - 1:
                    label.config(bg='#e94560', fg='#ffffff')
                else:
                    # 普通项 - 白色背景，黑色文字
                    label.config(bg='#ffffff', fg='#000000')
                    
    def menu_confirm(self):
        """确定按钮"""
        if self.is_measuring:
            return
            
        menu = self.menus.get(self.current_menu)
        if not menu:
            return
            
        actions = menu.get("actions", [])
        action = actions[self.current_index] if self.current_index < len(actions) else None
        
        if action:
            # 检查是否是测量开始命令
            if action == "auto_iv_start":
                # 检查电源状态
                if not self.app.power_on:
                    messagebox.showwarning("提示", "电源已关闭，请先开启电源")
                    return
                self.start_auto_iv_measurement()
            elif action == "auto_stop_start":
                # 检查电源状态
                if not self.app.power_on:
                    messagebox.showwarning("提示", "电源已关闭，请先开启电源")
                    return
                self.start_auto_stop_measurement()
            elif action == "auto_iv_save_yes":
                self.save_iv_data()
            elif action == "auto_iv_save_no":
                self.show_menu("auto_select")
            elif action == "auto_stop_save_yes":
                self.save_stop_data()
            elif action == "auto_stop_save_no":
                self.show_menu("auto_select")
            elif action == "auto_iv_query_confirm":
                self.load_iv_query_data()
            elif action == "auto_stop_query_confirm":
                self.load_stop_query_data()
            elif action == "edit_start_voltage":
                self.edit_start_voltage()
            elif action == "edit_end_voltage":
                self.edit_end_voltage()
            elif action in ["manual_select", "auto_select", "manual_iv", "manual_stop"]:
                self.show_menu(action)
            elif action == "auto_iv":
                self.show_menu("auto_iv")
                # 进入自动测量界面时更新波长显示
                self.update_auto_wavelength_display()
                self.update_measure_display()
            elif action == "auto_stop":
                self.show_menu("auto_stop")
                # 进入自动测量界面时更新波长显示
                self.update_auto_wavelength_display()
                self.update_measure_display()
            elif action == "auto_iv_query":
                self.query_wavelength_index = 0
                self.show_menu("auto_iv_query")
            elif action == "auto_stop_query":
                self.query_wavelength_index = 0
                self.show_menu("auto_stop_query")

    def update_auto_wavelength_display(self):
        """更新自动测量界面中的波长显示和光电流"""
        wavelength_str = self.app.wavelength_var.get()
        wavelength = int(wavelength_str.replace('nm', ''))
        
        # 更新波长显示
        if self.current_menu == "auto_iv":
            self.menu_items[2] = f"波长设置: {wavelength_str}"
            if len(self.menu_labels) >= 3:
                self.menu_labels[2].config(text=self.menu_items[2])
        elif self.current_menu == "auto_stop":
            self.menu_items[2] = f"波长设置: {wavelength_str}"
            if len(self.menu_labels) >= 3:
                self.menu_labels[2].config(text=self.menu_items[2])
        
        # 更新光电流（电压为0时的电流）
        self.update_auto_current_display()
    
    def update_auto_current_display(self):
        """更新自动测量界面中的光电流显示"""
        if self.current_menu not in ["auto_iv", "auto_stop"]:
            return
        
        # 获取当前波长
        wavelength_str = self.app.wavelength_var.get()
        wavelength = int(wavelength_str.replace('nm', ''))
        
        # 电压为0时的电流
        current_value = self.calculate_current(0, wavelength)
        
        range_str = self.app.current_range_var.get()
        exponent = int(range_str.split('^')[-1])
        scale_factor = 10 ** (-10 - exponent)
        current_display = current_value * scale_factor
        
        self.menu_items[1] = f"光电流: {current_display:.1f}×{range_str}A"
        if len(self.menu_labels) >= 2:
            self.menu_labels[1].config(text=self.menu_items[1])

    def menu_back(self):
        """返回按钮"""
        if self.is_measuring:
            return
            
        # 返回上一级菜单
        if self.current_menu == "manual_select":
            self.show_menu("main")
        elif self.current_menu in ["manual_iv", "manual_stop"]:
            # 重置电压，数据已在进入时清空，直接返回
            self.manual_iv_voltage = 0.0
            self.manual_stop_voltage = 0.0
            # 清空表格
            self.clear_table_display()
            self.show_menu("manual_select")
        elif self.current_menu == "auto_select":
            self.show_menu("main")
        elif self.current_menu in ["auto_iv", "auto_stop", "auto_iv_query", "auto_stop_query"]:
            self.show_menu("auto_select")
        elif self.current_menu == "auto_iv_save":
            self.show_menu("auto_select")
        elif self.current_menu == "auto_stop_save":
            self.show_menu("auto_select")
        else:
            self.show_menu("main")
            
    def voltage_up(self):
        """增大电压"""
        if self.is_measuring:
            return
            
        if self.current_menu == "manual_iv":
            if self.manual_iv_voltage < 50:
                self.manual_iv_voltage = min(50, self.manual_iv_voltage + 0.5)
                self.update_measure_display()
                    
        elif self.current_menu == "manual_stop":
            if self.manual_stop_voltage < 0:
                self.manual_stop_voltage = min(0, self.manual_stop_voltage + 0.1)
                self.update_measure_display()

    def voltage_down(self):
        """减小电压"""
        if self.is_measuring:
            return
            
        if self.current_menu == "manual_iv":
            if self.manual_iv_voltage > -5:
                self.manual_iv_voltage = max(-5, self.manual_iv_voltage - 0.5)
                self.update_measure_display()
                    
        elif self.current_menu == "manual_stop":
            if self.manual_stop_voltage > -5:
                self.manual_stop_voltage = max(-5, self.manual_stop_voltage - 0.1)
                self.update_measure_display()

    def record_data(self):
        """记录当前数据到表格"""
        # 只在手动测量界面有效
        if self.current_menu == "manual_iv":
            wavelength_str = self.app.wavelength_var.get()
            wavelength = int(wavelength_str.replace('nm', ''))
            current = self.calculate_current(self.manual_iv_voltage, wavelength)
            self.add_or_update_data(self.manual_iv_data, self.manual_iv_voltage, current)
            self.update_measure_display()
            # 只有伏安特性模式才更新表格
            if self.app.current_table_mode == "iv":
                self.update_table_with_data(self.manual_iv_data)
                messagebox.showinfo("提示", f"数据已记录: {self.manual_iv_voltage:.1f}V, {current:.3f}")
                
        elif self.current_menu == "manual_stop":
            wavelength_str = self.app.wavelength_var.get()
            wavelength = int(wavelength_str.replace('nm', ''))
            current = self.calculate_current(self.manual_stop_voltage, wavelength)
            self.add_or_update_data(self.manual_stop_data, self.manual_stop_voltage, current)
            self.update_measure_display()
            # 只有伏安特性模式才更新表格
            if self.app.current_table_mode == "iv":
                self.update_table_with_data(self.manual_stop_data)
                messagebox.showinfo("提示", f"数据已记录: {self.manual_stop_voltage:.3f}V, {current:.3f}")
        else:
            messagebox.showwarning("提示", "请在手动测量界面记录数据")


    def add_or_update_data(self, data, voltage, current):
        """
        添加或更新数据
        如果电压已存在则更新，否则追加
        """
        u_list = data["U"]
        i_list = data["I"]
        
        # 检查电压是否已存在（允许0.01的误差）
        for i, u in enumerate(u_list):
            if abs(u - voltage) < 0.01:
                i_list[i] = current
                return
        
        u_list.append(voltage)
        i_list.append(current)
        
        # 按电压排序
        sorted_pairs = sorted(zip(u_list, i_list))
        data["U"] = [p[0] for p in sorted_pairs]
        data["I"] = [p[1] for p in sorted_pairs]
        
    def update_table_with_data(self, data):
        """更新表格显示"""
        # 只有伏安特性模式才更新
        if self.app.current_table_mode != "iv":
            return
        
        u_list = data["U"]
        i_list = data["I"]
        
        # 获取当前量程
        range_str = self.app.current_range_var.get()
        exponent = int(range_str.split('^')[-1])
        scale_factor = 10 ** (-10 - exponent)
        
        # 清除表格
        for row in self.app.table_entries:
            row[0].delete(0, tk.END)
            row[1].delete(0, tk.END)
        
        # 填充数据 - 使用 len(self.app.table_entries) 而不是固定60
        max_rows = len(self.app.table_entries)
        for i in range(min(len(u_list), max_rows)):
            self.app.table_entries[i][0].insert(0, f"{u_list[i]:.3f}")
            if i < len(i_list):
                current_display = i_list[i] * scale_factor
                # 显示负值
                self.app.table_entries[i][1].insert(0, f"{current_display:.3f}")
        
        self.app.update_plot()
            
    def start_auto_iv_measurement(self):
        """开始自动测量伏安特性"""
        # 检查电源状态
        if not self.app.power_on:
            messagebox.showwarning("提示", "电源已关闭，请先开启电源")
            return
        
        # 自动测量时强制开启电源
        if not self.app.power_on:
            self.app.power_on = True
            self.app.power_btn.config(text="电源", bg='#00ff00', fg='black')
        
        self.is_measuring = True
        self.current_measure_type = "iv"
        self.measuring_data = {"U": [], "I": []}
        
        # 获取当前波长
        wavelength_str = self.app.wavelength_var.get()
        self.current_measure_wavelength = int(wavelength_str.replace('nm', ''))
        
        # 显示测量中
        self.show_menu("auto_iv_measuring")
        
        # 开始测量
        self.auto_iv_step = 0
        self.auto_iv_voltage = -1.0
        self.auto_measure_iv()
        
    def auto_measure_iv(self):
        """自动测量伏安特性 - 逐步执行"""
        if self.auto_iv_voltage > 50:
            self.is_measuring = False
            self.show_menu("auto_iv_save")
            return
            
        current = self.calculate_current(self.auto_iv_voltage, self.current_measure_wavelength)
        self.add_or_update_data(self.measuring_data, self.auto_iv_voltage, current)
        
        self.update_table_with_data(self.measuring_data)
        
        # 更新菜单显示
        if self.menu_labels:
            if self.current_menu == "auto_iv_measuring":
                self.menu_items[0] = f"自动测量中... {self.auto_iv_voltage:.1f}V"
                self.menu_labels[0].config(text=self.menu_items[0])
            else:
                self.menu_items[0] = f"自动测量中... {self.auto_iv_voltage:.1f}V"
                range_str = self.app.current_range_var.get()
                exponent = int(range_str.split('^')[-1])
                scale_factor = 10 ** (-10 - exponent)
                current_display = current * scale_factor
                if len(self.menu_items) > 1:
                    self.menu_items[1] = f"光电流: {current_display:.1f}×{range_str}A"
                if self.menu_labels:
                    self.menu_labels[0].config(text=self.menu_items[0])
                    if len(self.menu_labels) > 1 and len(self.menu_items) > 1:
                        self.menu_labels[1].config(text=self.menu_items[1])
        
        self.auto_iv_voltage += 0.5
        self.auto_iv_voltage = round(self.auto_iv_voltage, 1)
        
        self.measuring_timer = self.app.root.after(100, self.auto_measure_iv)
        
    def start_auto_stop_measurement(self):
        """开始自动测量截止电压"""
        # 检查电源状态
        if not self.app.power_on:
            messagebox.showwarning("提示", "电源已关闭，请先开启电源")
            return
        
        # 自动测量时强制开启电源
        if not self.app.power_on:
            self.app.power_on = True
            self.app.power_btn.config(text="电源", bg='#00ff00', fg='black')
        
        self.is_measuring = True
        self.current_measure_type = "stop"
        self.measuring_data = {"U": [], "I": []}
        
        # 获取当前波长
        wavelength_str = self.app.wavelength_var.get()
        self.current_measure_wavelength = int(wavelength_str.replace('nm', ''))
        
        # 获取起始和终止电压
        try:
            start_v = float(self.menu_items[3].split(": ")[1].replace("V", ""))
            end_v = float(self.menu_items[4].split(": ")[1].replace("V", ""))
        except:
            start_v = -2.0
            end_v = 0.0
            
        # 验证电压范围
        start_v = max(-2.0, min(-0.1, start_v))
        end_v = max(start_v + 0.1, min(0.0, end_v))
        
        self.auto_stop_start_v = start_v
        self.auto_stop_end_v = end_v
        self.auto_stop_voltage = start_v
        
        # 显示测量中
        self.show_menu("auto_stop_measuring")
        
        # 开始测量
        self.auto_measure_stop()
        
    def auto_measure_stop(self):
        """自动测量截止电压 - 逐步执行"""
        if self.auto_stop_voltage > self.auto_stop_end_v + 0.01:
            self.is_measuring = False
            self.show_menu("auto_stop_save")
            return
            
        current = self.calculate_current(self.auto_stop_voltage, self.current_measure_wavelength, "stop")
        self.add_or_update_data(self.measuring_data, self.auto_stop_voltage, current)
        
        # 只有伏安特性模式才更新表格
        if self.app.current_table_mode == "iv":
            self.update_table_with_data(self.measuring_data)
        
        # 更新菜单显示
        if self.menu_labels:
            if self.current_menu == "auto_stop_measuring":
                self.menu_items[0] = f"自动测量中... {self.auto_stop_voltage:.2f}V"
                self.menu_labels[0].config(text=self.menu_items[0])
            else:
                self.menu_items[0] = f"自动测量中... {self.auto_stop_voltage:.2f}V"
                range_str = self.app.current_range_var.get()
                exponent = int(range_str.split('^')[-1])
                scale_factor = 10 ** (-10 - exponent)
                current_display = current * scale_factor
                if len(self.menu_items) > 1:
                    self.menu_items[1] = f"光电流: {current_display:.1f}×{range_str}A"
                if self.menu_labels:
                    self.menu_labels[0].config(text=self.menu_items[0])
                    if len(self.menu_labels) > 1 and len(self.menu_items) > 1:
                        self.menu_labels[1].config(text=self.menu_items[1])
        
        self.auto_stop_voltage += 0.1
        self.auto_stop_voltage = round(self.auto_stop_voltage, 2)
        
        self.measuring_timer = self.app.root.after(100, self.auto_measure_stop)
        
    def save_iv_data(self):
        """保存伏安特性数据"""
        wavelength = self.current_measure_wavelength
        self.iv_data[wavelength] = {
            "U": self.measuring_data["U"].copy(),
            "I": self.measuring_data["I"].copy()
        }
        messagebox.showinfo("成功", f"波长 {wavelength}nm 的伏安特性数据已保存")
        self.show_menu("auto_select")
        
    def save_stop_data(self):
        """保存截止电压数据"""
        wavelength = self.current_measure_wavelength
        self.stop_data[wavelength] = {
            "U": self.measuring_data["U"].copy(),
            "I": self.measuring_data["I"].copy()
        }
        messagebox.showinfo("成功", f"波长 {wavelength}nm 的截止电压数据已保存")
        self.show_menu("auto_select")
        
    def load_iv_query_data(self):
        """加载查询的伏安特性数据"""
        wavelength_str = self.wavelengths[self.query_wavelength_index]
        wavelength = int(wavelength_str.replace('nm', ''))
        
        if wavelength in self.iv_data:
            data = self.iv_data[wavelength]
            self.update_table_with_data(data)
            messagebox.showinfo("成功", f"已加载波长 {wavelength}nm 的伏安特性数据")
        else:
            messagebox.showwarning("提示", f"未找到波长 {wavelength}nm 的伏安特性数据")
            
        self.show_menu("auto_select")
        
    def load_stop_query_data(self):
        """加载查询的截止电压数据"""
        wavelength_str = self.wavelengths[self.query_wavelength_index]
        wavelength = int(wavelength_str.replace('nm', ''))
        
        if wavelength in self.stop_data:
            data = self.stop_data[wavelength]
            self.update_table_with_data(data)
            messagebox.showinfo("成功", f"已加载波长 {wavelength}nm 的截止电压数据")
        else:
            messagebox.showwarning("提示", f"未找到波长 {wavelength}nm 的截止电压数据")
            
        self.show_menu("auto_select")


class PhotoelectricEffectApp:
    def __init__(self, root):
        self.root = root
        self.root.title("光电效应实验系统")
        self.root.geometry("1600x850")
        
        # 初始化数据
        self.init_data()
        
        # 长按相关变量
        self.zero_repeat_id = None
        self.zero_direction = 0
        
        # 偏振片相关变量
        self.polarizer_angle = 180  # 初始角度180度
        self.polarizer_repeat_id = None
        self.polarizer_direction = 0
        
        # 电源状态: True=开启(伏安特性模式), False=关闭(截止电压模式)
        self.power_on = True

        # 数据保存变量
        self.saved_iv_data = []
        self.saved_h_data = []

        # 创建界面
        self.create_notebook()
        self.create_left_frame()
        self.create_top_right_frame()
        
        # 先创建菜单系统
        self.menu_system = MenuSystem(
            self.left_frame, 
            self,
            menu_x=48, menu_y=65, menu_width=170, menu_height=120
        )
        
        # 再创建底部右侧区域
        self.create_bottom_right_frame()
            

    def zero_plus_click(self):
        """加号点击 - 增加0.1"""
        current = float(self.zero_label.cget("text"))
        if current >= 10:
            return
        new_val = min(10, current + 0.1)
        self.zero_label.config(text=f"{new_val:.1f}")
        self.zero_slider.set(new_val)
        # 更新菜单显示
        self.update_menu_display_after_zero()

    def zero_minus_click(self):
        """减号点击 - 减少0.1"""
        current = float(self.zero_label.cget("text"))
        if current <= -10:
            return
        new_val = max(-10, current - 0.1)
        self.zero_label.config(text=f"{new_val:.1f}")
        self.zero_slider.set(new_val)
        # 更新菜单显示
        self.update_menu_display_after_zero()

    def update_menu_display_after_zero(self):
        """调零后更新菜单显示"""
        if hasattr(self, 'menu_system'):
            ms = self.menu_system
            
            # 获取当前量程 - 直接使用 self.current_range_var
            range_str = self.current_range_var.get()
            exponent = int(range_str.split('^')[-1])
            
            # 实际调零值 = 显示值 × 10^exponent / 1e-10 (转换为10^-10A单位)
            display_value = float(self.zero_label.cget("text"))
            actual_zero = display_value * (10 ** exponent) / 1e-10
            ms.zero_offset = actual_zero
            
            # 更新菜单中的电流显示
            if ms.current_menu in ["manual_iv", "manual_stop", "auto_iv", "auto_stop"]:
                ms.update_measure_display()
            
            # 只有伏安特性模式才更新表格
            if self.current_table_mode == "iv":
                # 更新手动测量表格数据
                if ms.current_menu in ["manual_iv", "manual_stop"]:
                    if ms.current_menu == "manual_iv":
                        data = ms.manual_iv_data
                    else:
                        data = ms.manual_stop_data
                    if data["U"]:
                        ms.update_table_with_data(data)
                
                # 更新自动测量中的显示
                elif ms.current_menu in ["auto_iv_measuring", "auto_stop_measuring"]:
                    self.update_auto_measuring_display()

    def zero_plus_press(self, event):
        """加号长按开始"""
        # 先执行一次点击
        self.zero_plus_click()
        # 然后开始长按重复
        self.zero_direction = 1
        self.zero_repeat_id = self.root.after(300, self.start_zero_repeat)  # 300ms延迟后开始重复

    def zero_minus_press(self, event):
        """减号长按开始"""
        # 先执行一次点击
        self.zero_minus_click()
        # 然后开始长按重复
        self.zero_direction = -1
        self.zero_repeat_id = self.root.after(300, self.start_zero_repeat)  # 300ms延迟后开始重复

    def zero_release(self, event):
        """长按释放"""
        self.zero_direction = 0
        if self.zero_repeat_id:
            self.root.after_cancel(self.zero_repeat_id)
            self.zero_repeat_id = None

    def start_zero_repeat(self):
        """开始长按重复"""
        if self.zero_direction == 1:
            self.zero_plus_click()
        elif self.zero_direction == -1:
            self.zero_minus_click()
        else:
            return
        # 每100ms重复一次
        self.zero_repeat_id = self.root.after(100, self.start_zero_repeat)

    def init_data(self):
        """初始化实验数据"""
        # 表格数据 - 保留作为基础数据用于计算
        self.table_data = [
            (-1.5,0),(-1.0, 1.5), (-0.5, 2.8), (0.0, 3.5), (0.5, 5.9), (1.0, 9.5),
            (1.5, 13.7), (2.0, 17.8), (2.5, 21.6), (3.0, 25.2), (3.5, 28.7),
            (4.0, 31.9), (4.5, 34.9), (5.0, 37.5), (5.5, 39.7), (6.0, 41.6),
            (6.5, 43.2), (7.0, 44.8), (7.5, 46.2), (8.0, 47.6), (8.5, 48.9),
            (9.0, 50.2), (9.5, 51.6), (10.0, 53.0), (10.5, 54.6), (11.0, 56.1),
            (11.5, 57.5), (12.0, 59.0), (12.5, 60.2), (13.0, 61.4), (13.5, 62.7),
            (14.0, 63.9), (14.5, 65.1), (15.0, 66.2), (15.5, 67.3), (16.0, 68.3),
            (16.5, 69.3), (17.0, 70.3), (17.5, 71.3), (18.0, 72.2), (18.5, 73.2),
            (19.0, 74.1), (19.5, 75.1), (20.0, 76.0), (20.5, 76.8), (21.0, 77.6),
            (21.5, 78.4), (22.0, 79.2), (22.5, 79.9), (23.0, 80.6), (23.5, 81.3),
            (24.0, 81.9), (24.5, 82.5), (25.0, 83.2), (25.5, 83.9), (26.0, 84.5),
            (26.5, 85.0), (27.0, 85.6), (27.5, 86.1), (28.0, 86.5), (28.5, 87.0)
        ]
        
        # 参数设置
        self.aperture = 4  # 光阑直径(mm)
        self.wavelength = 450  # 波长(nm)
        self.current_range = 10  # 默认10^-10A
        self.voltage = 0  # 当前电压
        
        # 初始化显示数据为空（用于表格和曲线显示）
        self.display_data = {"U": [], "I": []}
        
    def create_notebook(self):
        """创建选项卡"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tabs = ["测量光电管的伏安特性", "测量普朗克常数h"]
        self.frames = {}
        
        for tab in tabs:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=tab)
            self.frames[tab] = frame
        
        # 绑定选项卡切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # 普朗克常数数据
        self.h_data = [
            {"wavelength": 405, "freq": 7.41, "voltage": ""},
            {"wavelength": 450, "freq": 6.67, "voltage": ""},
            {"wavelength": 510, "freq": 5.88, "voltage": ""},
            {"wavelength": 532, "freq": 5.64, "voltage": ""},
            {"wavelength": 635, "freq": 4.72, "voltage": ""},
            {"wavelength": 650, "freq": 4.62, "voltage": ""},
            {"wavelength": 685, "freq": 4.38, "voltage": ""}
        ]
        
        # 当前显示的表格类型: "iv" 或 "h"
        self.current_table_mode = "iv"
    
    def save_table_data(self):
        """保存当前表格数据"""
        if self.current_table_mode == "iv":
            # 保存伏安特性数据
            self.saved_iv_data = []
            for row in self.table_entries:
                try:
                    u = float(row[0].get()) if row[0].get().strip() else None
                    i = float(row[1].get()) if row[1].get().strip() else None
                    self.saved_iv_data.append([u, i])
                except ValueError:
                    self.saved_iv_data.append([None, None])
        else:
            # 保存普朗克常数数据
            self.saved_h_data = []
            for i, row in enumerate(self.table_entries):
                if i < len(self.h_data):
                    try:
                        voltage = float(row[2].get()) if row[2].get().strip() else None
                        self.saved_h_data.append(voltage)
                    except ValueError:
                        self.saved_h_data.append(None)
                else:
                    break

    def restore_iv_data(self):
        """恢复伏安特性数据"""
        if hasattr(self, 'saved_iv_data'):
            # 确保表格行数足够
            max_rows = len(self.table_entries)
            for i, row in enumerate(self.table_entries):
                if i < len(self.saved_iv_data):
                    u_val = self.saved_iv_data[i][0]
                    i_val = self.saved_iv_data[i][1]
                    if u_val is not None:
                        row[0].insert(0, str(u_val))
                    if i_val is not None:
                        row[1].insert(0, str(i_val))
            self.update_iv_plot()

    def restore_h_data(self):
        """恢复普朗克常数数据"""
        if hasattr(self, 'saved_h_data'):
            # 填充默认数据（防止saved_h_data为空时没有数据）
            self.fill_h_default_data()
            
            # 然后用保存的数据覆盖
            for i, row in enumerate(self.table_entries):
                if i < len(self.saved_h_data) and i < len(self.h_data):
                    if self.saved_h_data[i] is not None:
                        row[2].delete(0, tk.END)
                        row[2].insert(0, str(self.saved_h_data[i]))
                        self.h_data[i]["voltage"] = str(self.saved_h_data[i])
            self.update_h_plot()

    def fill_h_default_data(self):
        """填充普朗克常数默认数据"""
        for i, data in enumerate(self.h_data):
            if i < len(self.table_entries):
                self.table_entries[i][0].delete(0, tk.END)
                self.table_entries[i][1].delete(0, tk.END)
                self.table_entries[i][0].insert(0, str(data["wavelength"]))
                self.table_entries[i][1].insert(0, f"{data['freq']:.2f}")
                # 如果已有电压数据则填充
                if data["voltage"]:
                    self.table_entries[i][2].insert(0, data["voltage"])

    def on_tab_changed(self, event):
        """选项卡切换时的处理"""
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        
        # 保存当前数据
        self.save_table_data()
        
        if current_tab == "测量光电管的伏安特性":
            self.current_table_mode = "iv"
            # 显示波长，隐藏附加电流
            self.wavelength_label.pack(side=tk.LEFT, padx=20)
            self.wavelength_entry.pack(side=tk.LEFT, padx=5)
            self.wavelength_unit_label.pack(side=tk.LEFT, padx=5)
            self.bias_current_label.pack_forget()
            self.bias_current_entry.pack_forget()
            self.bias_current_unit_label.pack_forget()
            # 显示记录数据按钮 - 放在计算按钮前面
            if hasattr(self, 'btn_record_data') and hasattr(self, 'btn_calculate'):
                self.btn_record_data.pack_forget()
                self.btn_record_data.pack(side=tk.LEFT, padx=5, before=self.btn_calculate)
            # 先重建表格再恢复数据
            self.rebuild_iv_table()
            self.restore_iv_data()
            self.update_iv_plot()
        elif current_tab == "测量普朗克常数h":
            self.current_table_mode = "h"
            # 显示附加电流，隐藏波长
            self.bias_current_label.pack(side=tk.LEFT, padx=5)
            self.bias_current_entry.pack(side=tk.LEFT, padx=5)
            self.bias_current_unit_label.pack(side=tk.LEFT, padx=2)
            self.wavelength_label.pack_forget()
            self.wavelength_entry.pack_forget()
            self.wavelength_unit_label.pack_forget()
            # 隐藏记录数据按钮
            if hasattr(self, 'btn_record_data'):
                self.btn_record_data.pack_forget()
            # 先重建表格再填充默认数据
            self.update_h_table_headers()
            # 填充默认数据
            self.fill_h_default_data()
            # 再恢复保存的数据
            self.restore_h_data()
        
    def update_iv_table(self):
        """更新伏安特性表格"""
        # 清除表格
        for row in self.table_entries:
            row[0].delete(0, tk.END)
            row[1].delete(0, tk.END)
            if len(row) > 2:
                row[2].delete(0, tk.END)
        
        # 重新创建表格
        self.rebuild_iv_table()
        self.update_iv_plot()

    def update_h_table(self):
        """更新普朗克常数表格"""
        # 清除表格
        for row in self.table_entries:
            row[0].delete(0, tk.END)
            row[1].delete(0, tk.END)
            if len(row) > 2:
                row[2].delete(0, tk.END)
        
        # 更新表头
        self.update_h_table_headers()
        
        # 填充数据
        for i, data in enumerate(self.h_data):
            if i < len(self.table_entries):
                self.table_entries[i][0].insert(0, str(data["wavelength"]))
                self.table_entries[i][1].insert(0, f"{data['freq']:.2f}")
                if data["voltage"]:
                    self.table_entries[i][2].insert(0, data["voltage"])
        
        # 更新图表
        self.update_h_plot()

    def rebuild_iv_table(self):
        """重新构建伏安特性表格"""
        # 清除表格框架中的内容
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        # 重新创建滚动条和表格
        canvas = tk.Canvas(self.table_frame)
        scrollbar = tk.Scrollbar(self.table_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 创建表头
        headers = ["Uak/V", "I/10^-10A"]
        for col, header in enumerate(headers):
            tk.Label(scrollable_frame, text=header, font=("Microsoft YaHei", 10, "bold"),
                    relief=tk.RIDGE, width=20, height=2).grid(row=0, column=col, padx=1, pady=1)
        
        # 创建表格条目
        self.table_entries = []
        for row in range(1, 121):
            row_entries = []
            for col in range(2):
                entry = tk.Entry(scrollable_frame, width=20, justify="center")
                entry.grid(row=row, column=col, padx=1, pady=1)
                row_entries.append(entry)
            self.table_entries.append(row_entries)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def update_h_table_headers(self):
        """更新普朗克常数表格表头"""
        # 清除表格框架中的内容
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        # 重新创建滚动条和表格
        canvas = tk.Canvas(self.table_frame)
        scrollbar = tk.Scrollbar(self.table_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 创建表头 - 三列
        headers = ["λ/nm", "υ/10^14Hz", "U0/V"]
        for col, header in enumerate(headers):
            tk.Label(scrollable_frame, text=header, font=("Microsoft YaHei", 10, "bold"),
                    relief=tk.RIDGE, width=15, height=2).grid(row=0, column=col, padx=1, pady=1)
        
        # 创建表格条目 - 3列
        self.table_entries = []
        for row in range(1, len(self.h_data) + 1):
            row_entries = []
            for col in range(3):
                entry = tk.Entry(scrollable_frame, width=15, justify="center")
                entry.grid(row=row, column=col, padx=1, pady=1)
                row_entries.append(entry)
            self.table_entries.append(row_entries)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 保存canvas引用用于更新
        self.h_canvas = canvas
        self.h_scrollable_frame = scrollable_frame

    def update_h_plot(self):
        """更新普朗克常数曲线图"""
        self.ax.clear()
        
        # 获取数据
        freq_data = []
        voltage_data = []
        for i, data in enumerate(self.h_data):
            try:
                if i < len(self.table_entries):
                    voltage_str = self.table_entries[i][2].get().strip()
                    if voltage_str:
                        voltage = float(voltage_str)
                        freq_data.append(data["freq"])
                        voltage_data.append(voltage)
            except ValueError:
                continue
        
        result_text = ""
        
        if freq_data and voltage_data:
            # 绘制散点图
            self.ax.scatter(freq_data, voltage_data, color='red', s=50, zorder=5)
            
            # 线性拟合
            if len(freq_data) >= 2:
                coeffs = np.polyfit(freq_data, voltage_data, 1)
                poly = np.poly1d(coeffs)
                freq_fit = np.linspace(min(freq_data), max(freq_data), 100)
                voltage_fit = poly(freq_fit)
                self.ax.plot(freq_fit, voltage_fit, 'b--', linewidth=2)
                
                # 计算普朗克常数 h = k * e
                # 注意：e 应该取负值（电子电荷为负）
                # 频率单位是 10^14 Hz，斜率 k 的单位是 V/(10^14Hz)
                # 实际斜率 = k / 10^14 (V/Hz)
                k = coeffs[0]  # 斜率，单位 V/(10^14Hz)
                e = -1.602176634e-19  # 元电荷，单位 C（负值）
                h = k * e / 1e14  # 普朗克常数，单位 J·s
                
                # 理论值
                h_theory = 6.62607015e-34  # J·s
                
                # 构建结果文本 - 显示在h值下面
                result_text = f'U0 = {k:.4f}υ + {coeffs[1]:.4f}\n'
                result_text += f'h = {h:.3e} J·s\n'
                result_text += f'h理论值 = {h_theory:.3e} J·s\n'
                result_text += f'相对误差 = {abs(h - h_theory)/h_theory*100:.2f}%'
                
                # 在图表右上角显示h值和结果
                self.ax.text(0.95, 0.85, result_text,
                            transform=self.ax.transAxes, fontsize=9,
                            horizontalalignment='right', verticalalignment='top',
                            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
                            linespacing=1.5)
            else:
                result_text = "数据点不足，至少需要2个数据点进行拟合"
                self.ax.text(0.5, 0.5, result_text, 
                            transform=self.ax.transAxes, ha='center', va='center',
                            fontsize=12, color='gray')
            
            self.ax.set_xlabel('频率 υ (10^14 Hz)', fontsize=11, fontproperties='Microsoft YaHei')
            self.ax.set_ylabel('截止电压 U0 (V)', fontsize=11, fontproperties='Microsoft YaHei')
            self.ax.set_title('截止电压与光波频率测量曲线', fontsize=12, fontproperties='Microsoft YaHei', pad=10)
            self.ax.grid(True, alpha=0.3)
            
            self.fig.tight_layout()
        else:
            self.ax.text(0.5, 0.5, '请输入截止电压数据', 
                        transform=self.ax.transAxes, ha='center', va='center',
                        fontsize=14, color='gray')
            self.ax.set_xlabel('频率 υ (10^14 Hz)', fontsize=11, fontproperties='Microsoft YaHei')
            self.ax.set_ylabel('截止电压 U0 (V)', fontsize=11, fontproperties='Microsoft YaHei')
            self.ax.set_title('截止电压与光波频率测量曲线', fontsize=12, fontproperties='Microsoft YaHei', pad=10)
            result_text = "请输入截止电压数据以计算普朗克常数"
        
        # 更新结果文本框
        if hasattr(self, 'result_text'):
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', result_text)
            self.result_text.config(state=tk.DISABLED)
        
        self.canvas.draw()

    def create_left_frame(self):
        """创建左侧区域 - 实验主机"""
        self.left_frame = tk.LabelFrame(self.root, text="实验主机", font=("Microsoft YaHei", 12, "bold"))
        self.left_frame.place(x=10, y=60, width=700, height=800)
        
        # 图片容器 - 纵向排列
        image_frame = tk.Frame(self.left_frame)
        image_frame.pack(pady=10)
        
        # 加载图片 - 纵向排列
        try:
            host_img_path = get_resource_path("background/主机.jpg")
            host_back_path = get_resource_path("background/主机背面.jpg")
            
            from PIL import Image, ImageTk
            
            img1 = Image.open(host_img_path)
            img1 = img1.resize((680, 210), Image.Resampling.LANCZOS)
            self.host_img = ImageTk.PhotoImage(img1)
            label1 = tk.Label(image_frame, image=self.host_img)
            label1.pack(pady=5)
            
            # 主机背面图
            img2 = Image.open(host_back_path)
            img2 = img2.resize((680, 210), Image.Resampling.LANCZOS)
            self.host_back_img = ImageTk.PhotoImage(img2)
            label2 = tk.Label(image_frame, image=self.host_back_img)
            label2.pack(pady=5)
            
            # 在主机背面图上叠加电源开关按钮
            self.create_power_button(image_frame)
            
        except Exception as e:
            tk.Label(image_frame, text="主机.jpg\n(图片加载失败)", font=("Microsoft YaHei", 10), fg="gray").pack(pady=5)
            tk.Label(image_frame, text="主机背面.jpg\n(图片加载失败)", font=("Microsoft YaHei", 10), fg="gray").pack(pady=5)
        
    # ... 其余代码不变 ...
        # 光电流调零 - 增加微调按钮
        zero_frame = tk.LabelFrame(self.left_frame, text="光电流调零", font=("Microsoft YaHei", 10))
        zero_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 调零旋钮
        tk.Label(zero_frame, text="调零旋钮:").pack(side=tk.LEFT, padx=5)
        self.zero_slider = tk.Scale(zero_frame, from_=-20, to=20, resolution=0.1,
                                orient=tk.HORIZONTAL, length=200, command=self.on_zero_change)
        self.zero_slider.pack(side=tk.LEFT, padx=5)
        self.zero_label = tk.Label(zero_frame, text="0.0", width=6)
        self.zero_label.pack(side=tk.LEFT, padx=5)
        
        # 微调按钮 - 加号（移除command，只使用事件绑定）
        self.btn_zero_plus = tk.Button(zero_frame, text="+", font=("Microsoft YaHei", 10, "bold"),
                                     width=2, height=1)
        self.btn_zero_plus.pack(side=tk.LEFT, padx=2)
        self.btn_zero_plus.bind("<ButtonPress-1>", self.zero_plus_press)
        self.btn_zero_plus.bind("<ButtonRelease-1>", self.zero_release)
        
        # 微调按钮 - 减号（移除command，只使用事件绑定）
        self.btn_zero_minus = tk.Button(zero_frame, text="-", font=("Microsoft YaHei", 10, "bold"),
                                         width=2, height=1)
        self.btn_zero_minus.pack(side=tk.LEFT, padx=2)
        self.btn_zero_minus.bind("<ButtonPress-1>", self.zero_minus_press)
        self.btn_zero_minus.bind("<ButtonRelease-1>", self.zero_release)
        
        # 长按定时器
        self.zero_repeat_id = None
        self.zero_direction = 0
        
        # ... 其余代码不变 ...
        
        # 电流量程选项卡
        range_frame = tk.LabelFrame(self.left_frame, text="电流量程", font=("Microsoft YaHei", 10))
        range_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ranges = ["10^-8", "10^-9", "10^-10", "10^-11", "10^-12", "10^-13"]
        self.current_range_var = tk.StringVar(value="10^-10")
        for i, r in enumerate(ranges):
            rb = tk.Radiobutton(range_frame, text=r, variable=self.current_range_var, 
                                value=r, command=self.on_range_change)
            rb.grid(row=0, column=i, padx=5, pady=5)
        
        # 波长选项卡
        wavelength_frame = tk.LabelFrame(self.left_frame, text="入射光波长", font=("Microsoft YaHei", 10))
        wavelength_frame.pack(fill=tk.X, padx=10, pady=5)
        
        wavelengths = ["405nm", "450nm", "510nm", "532nm", "635nm", "650nm", "685nm"]
        self.wavelength_var = tk.StringVar(value="450nm")
        for i, w in enumerate(wavelengths):
            rb = tk.Radiobutton(wavelength_frame, text=w, variable=self.wavelength_var,
                                value=w, command=self.on_wavelength_change)
            rb.grid(row=0, column=i, padx=5, pady=5)

    def create_power_button(self, parent):
        """在主机背面图上创建电源开关按钮"""
        # 电源开关按钮 - 直接放在主机背面图右下角
        self.power_btn = tk.Button(parent, text="电源", font=("Microsoft YaHei", 9, "bold"),
                                bg='#00ff00', fg='black', width=6, height=1,
                                command=self.toggle_power)
        self.power_btn.place(x=474, y=390)
        
        # 更新菜单显示
        self.update_power_display()

    def toggle_power(self):
        """切换电源开关"""
        self.power_on = not self.power_on
        
        if self.power_on:
            self.power_btn.config(text="电源", bg='#00ff00', fg='black')
        else:
            self.power_btn.config(text="电源", bg='#ff0000', fg='white')
        
        # 更新菜单中的电流显示
        self.update_power_display()

    def update_power_display(self):
        """电源状态变化后更新显示"""
        if hasattr(self, 'menu_system'):
            ms = self.menu_system
            # 更新菜单中的电流显示
            if ms.current_menu in ["manual_iv", "manual_stop", "auto_iv", "auto_stop"]:
                ms.update_measure_display()
            
            # 更新手动测量表格数据
            if ms.current_menu in ["manual_iv", "manual_stop"]:
                if ms.current_menu == "manual_iv":
                    data = ms.manual_iv_data
                else:
                    data = ms.manual_stop_data
                if data["U"]:
                    ms.update_table_with_data(data)
            
            # 更新自动测量中的显示
            elif ms.current_menu in ["auto_iv_measuring", "auto_stop_measuring"]:
                self.update_auto_measuring_display()
                
    def on_zero_change(self, value):
        """调零旋钮变化"""
        # 显示值（用户看到的数值）
        display_value = float(value)
        self.zero_label.config(text=f"{display_value:.1f}")
        
        # 获取当前量程 - 直接使用 self.current_range_var
        range_str = self.current_range_var.get()
        exponent = int(range_str.split('^')[-1])
        
        # 实际调零值 = 显示值 × 10^exponent
        # 但电流计算中 base 是 10^-10A 单位，所以需要转换
        # 显示值 × 10^exponent 是实际电流值，需要转换为 10^-10A 单位
        actual_zero = display_value * (10 ** exponent) / 1e-10
        
        if hasattr(self, 'menu_system'):
            ms = self.menu_system
            ms.zero_offset = actual_zero
            
            # 更新菜单中的电流显示
            if ms.current_menu in ["manual_iv", "manual_stop", "auto_iv", "auto_stop"]:
                ms.update_measure_display()
            
            # 只有伏安特性模式才更新表格
            if self.current_table_mode == "iv":
                # 更新手动测量表格数据
                if ms.current_menu in ["manual_iv", "manual_stop"]:
                    if ms.current_menu == "manual_iv":
                        data = ms.manual_iv_data
                    else:
                        data = ms.manual_stop_data
                    if data["U"]:
                        ms.update_table_with_data(data)
                
                # 更新自动测量中的显示
                elif ms.current_menu in ["auto_iv_measuring", "auto_stop_measuring"]:
                    self.update_auto_measuring_display()
    
    def update_auto_measuring_display(self):
        """更新自动测量中的电流显示"""
        # 只有伏安特性模式才更新
        if self.current_table_mode != "iv":
            return
        
        if not hasattr(self, 'menu_system'):
            return
        
        ms = self.menu_system
        if ms.current_menu == "auto_iv_measuring":
            voltage = ms.auto_iv_voltage
        elif ms.current_menu == "auto_stop_measuring":
            voltage = ms.auto_stop_voltage
        else:
            return
        
        wavelength_str = self.wavelength_var.get()
        wavelength = int(wavelength_str.replace('nm', ''))
        current = ms.calculate_current(voltage, wavelength)
        
        range_str = self.current_range_var.get()
        exponent = int(range_str.split('^')[-1])
        scale_factor = 10 ** (-10 - exponent)
        current_display = current * scale_factor
        
        ms.menu_items[1] = f"光电流: {current_display:.1f}×{range_str}A"
        if len(ms.menu_labels) >= 2:
            ms.menu_labels[1].config(text=ms.menu_items[1])

    def create_top_right_frame(self):
        """创建右上区域 - 实验装置"""
        top_right_frame = tk.LabelFrame(self.root, text="实验装置", font=("Microsoft YaHei", 12, "bold"))
        top_right_frame.place(x=720, y=40, width=460, height=300)
        
        # 创建左右布局容器
        device_container = tk.Frame(top_right_frame)
        device_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧：装置图片
        left_container = tk.Frame(device_container)
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        try:
            device_img_path = get_resource_path("background/装置.jpg")
            from PIL import Image, ImageTk
            img = Image.open(device_img_path)
            img = img.resize((290, 240), Image.Resampling.LANCZOS)
            self.device_img = ImageTk.PhotoImage(img)
            tk.Label(left_container, image=self.device_img).pack(pady=5)
        except Exception as e:
            tk.Label(left_container, text="装置.jpg\n(图片加载失败)", 
                    font=("Microsoft YaHei", 14), fg="gray").pack(expand=True)
        
        # 右侧：偏振片控制
        right_container = tk.Frame(device_container, width=200)
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        right_container.pack_propagate(False)  # 固定宽度
        
        # 偏振片控制
        polarizer_frame = tk.LabelFrame(right_container, text="偏振片角度", font=("Microsoft YaHei", 10))
        polarizer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 角度显示
        angle_display_frame = tk.Frame(polarizer_frame)
        angle_display_frame.pack(pady=10)
        tk.Label(angle_display_frame, text="角度:", font=("Microsoft YaHei", 12)).pack(side=tk.LEFT, padx=5)
        self.polarizer_label = tk.Label(angle_display_frame, text="180°", font=("Microsoft YaHei", 14, "bold"), 
                                        width=8, fg='#2d6a4f')
        self.polarizer_label.pack(side=tk.LEFT, padx=5)
        
        # 角度滑块 - 竖直方向
        slider_frame = tk.Frame(polarizer_frame)
        slider_frame.pack(pady=5)
        self.polarizer_slider = tk.Scale(slider_frame, from_=360, to=0, resolution=1,
                                        orient=tk.VERTICAL, length=120,
                                        command=self.on_polarizer_change)
        self.polarizer_slider.set(180)
        self.polarizer_slider.pack(side=tk.LEFT, padx=5)
        
        # 角度数值显示
        angle_value_frame = tk.Frame(slider_frame)
        angle_value_frame.pack(side=tk.LEFT, padx=10)
        
        # 微调按钮 - 加号
        self.btn_polarizer_plus = tk.Button(angle_value_frame, text="+", font=("Microsoft YaHei", 12, "bold"),
                                            width=3, height=1)
        self.btn_polarizer_plus.pack(pady=2)
        self.btn_polarizer_plus.bind("<ButtonPress-1>", self.polarizer_plus_press)
        self.btn_polarizer_plus.bind("<ButtonRelease-1>", self.polarizer_release)
        
        # 角度值显示（数字）
        # self.polarizer_value_label = tk.Label(angle_value_frame, text="180", font=("Microsoft YaHei", 16, "bold"),
        #                                     fg='#0f3460', width=4)
        # self.polarizer_value_label.pack(pady=2)
        
        # 微调按钮 - 减号
        self.btn_polarizer_minus = tk.Button(angle_value_frame, text="-", font=("Microsoft YaHei", 12, "bold"),
                                             width=3, height=1)
        self.btn_polarizer_minus.pack(pady=2)
        self.btn_polarizer_minus.bind("<ButtonPress-1>", self.polarizer_minus_press)
        self.btn_polarizer_minus.bind("<ButtonRelease-1>", self.polarizer_release)
    
    def on_polarizer_change(self, value):
        """偏振片角度变化"""
        angle = int(float(value))
        self.polarizer_angle = angle
        self.polarizer_label.config(text=f"{angle}°")
        # self.polarizer_value_label.config(text=str(angle))
        # 更新菜单中的电流显示
        self.update_menu_display_after_polarizer()

    def polarizer_plus_click(self):
        """偏振片加号点击 - 增加1度"""
        current = self.polarizer_angle
        if current >= 360:
            return
        new_val = min(360, current + 1)
        self.polarizer_angle = new_val
        self.polarizer_label.config(text=f"{new_val}°")
        # self.polarizer_value_label.config(text=str(new_val))
        self.polarizer_slider.set(new_val)
        self.update_menu_display_after_polarizer()

    def polarizer_minus_click(self):
        """偏振片减号点击 - 减少1度"""
        current = self.polarizer_angle
        if current <= 0:
            return
        new_val = max(0, current - 1)
        self.polarizer_angle = new_val
        self.polarizer_label.config(text=f"{new_val}°")
        # self.polarizer_value_label.config(text=str(new_val))
        self.polarizer_slider.set(new_val)
        self.update_menu_display_after_polarizer()

    def polarizer_plus_press(self, event):
        """偏振片加号长按开始"""
        self.polarizer_plus_click()
        self.polarizer_direction = 1
        self.polarizer_repeat_id = self.root.after(300, self.start_polarizer_repeat)

    def polarizer_minus_press(self, event):
        """偏振片减号长按开始"""
        self.polarizer_minus_click()
        self.polarizer_direction = -1
        self.polarizer_repeat_id = self.root.after(300, self.start_polarizer_repeat)

    def polarizer_release(self, event):
        """偏振片长按释放"""
        self.polarizer_direction = 0
        if self.polarizer_repeat_id:
            self.root.after_cancel(self.polarizer_repeat_id)
            self.polarizer_repeat_id = None

    def start_polarizer_repeat(self):
        """开始偏振片长按重复"""
        if self.polarizer_direction == 1:
            self.polarizer_plus_click()
        elif self.polarizer_direction == -1:
            self.polarizer_minus_click()
        else:
            return
        self.polarizer_repeat_id = self.root.after(100, self.start_polarizer_repeat)

    def update_menu_display_after_polarizer(self):
        """偏振片角度变化后更新菜单显示"""
        if hasattr(self, 'menu_system'):
            ms = self.menu_system
            # 更新菜单中的电流显示
            if ms.current_menu in ["manual_iv", "manual_stop", "auto_iv", "auto_stop"]:
                ms.update_measure_display()
            
            # 只有伏安特性模式才更新表格
            if self.current_table_mode == "iv":
                # 更新手动测量表格数据
                if ms.current_menu in ["manual_iv", "manual_stop"]:
                    if ms.current_menu == "manual_iv":
                        data = ms.manual_iv_data
                    else:
                        data = ms.manual_stop_data
                    if data["U"]:
                        ms.update_table_with_data(data)
                
                # 更新自动测量中的显示
                elif ms.current_menu in ["auto_iv_measuring", "auto_stop_measuring"]:
                    self.update_auto_measuring_display()

    def create_bottom_right_frame(self):
        """创建右下区域 - 数据记录区域"""
        bottom_right_frame = tk.LabelFrame(self.root, text="数据记录区域", font=("Microsoft YaHei", 12, "bold"))
        bottom_right_frame.place(x=720, y=340, width=860, height=590)
        
        # 参数显示和编辑（包含所有按钮）
        param_frame = tk.Frame(bottom_right_frame)
        param_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 第一行：参数输入
        param_row = tk.Frame(param_frame)
        param_row.pack(side=tk.LEFT)
        
        tk.Label(param_row, text="光阑直径:", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=5)
        self.aperture_entry = tk.Entry(param_row, width=10)
        self.aperture_entry.insert(0, "4")
        self.aperture_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(param_row, text="mm", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=5)
        
        # 附加电流 - 默认隐藏
        self.bias_current_label = tk.Label(param_row, text="附加电流:", font=("Microsoft YaHei", 10))
        self.bias_current_entry = tk.Entry(param_row, width=12)
        self.bias_current_entry.insert(0, "-75.0")
        self.bias_current_unit_label = tk.Label(param_row, text="×10^-13A", font=("Microsoft YaHei", 10))
        # 初始隐藏
        self.bias_current_label.pack_forget()
        self.bias_current_entry.pack_forget()
        self.bias_current_unit_label.pack_forget()
        
        # 波长 - 默认显示
        self.wavelength_label = tk.Label(param_row, text="波长:", font=("Microsoft YaHei", 10))
        self.wavelength_label.pack(side=tk.LEFT, padx=20)
        self.wavelength_entry = tk.Entry(param_row, width=10)
        self.wavelength_entry.insert(0, "450")
        self.wavelength_entry.pack(side=tk.LEFT, padx=5)
        self.wavelength_unit_label = tk.Label(param_row, text="nm", font=("Microsoft YaHei", 10))
        self.wavelength_unit_label.pack(side=tk.LEFT, padx=5)
        
        # 第二行：操作按钮
        button_row = tk.Frame(param_frame)
        button_row.pack(side=tk.LEFT, padx=10)
        
        # 先创建计算按钮（作为锚点）
        self.btn_calculate = tk.Button(button_row, text="计算", font=("Microsoft YaHei", 10),
                                    width=8, command=self.calculate_plot)
        self.btn_calculate.pack(side=tk.LEFT, padx=5)
        
        # 记录数据按钮 - 放在计算按钮前面（使用before参数）
        self.btn_record_data = tk.Button(button_row, text="记录数据", font=("Microsoft YaHei", 10),
                                         width=8,
                                        command=lambda: self.menu_system.record_data() if hasattr(self, 'menu_system') else None)
        self.btn_record_data.pack(side=tk.LEFT, padx=5, before=self.btn_calculate)
        
        # 其他按钮放在计算按钮后面
        tk.Button(button_row, text="清空数据", font=("Microsoft YaHei", 10),
                width=8, command=self.clear_data).pack(side=tk.LEFT, padx=5)
        tk.Button(button_row, text="导出数据", font=("Microsoft YaHei", 10),
                width=8, command=self.export_data).pack(side=tk.LEFT, padx=5)
        tk.Button(button_row, text="导入数据", font=("Microsoft YaHei", 10),
                width=8, command=self.import_data).pack(side=tk.LEFT, padx=5)
        
        # 创建左右分屏（表格和曲线图）
        paned_window = tk.PanedWindow(bottom_right_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧表格框架
        self.table_frame = tk.Frame(paned_window)
        paned_window.add(self.table_frame, width=400)
        
        # 创建滚动条和表格（初始为伏安特性）
        self.rebuild_iv_table()
        
        # 右侧曲线图框架
        plot_frame = tk.Frame(paned_window)
        paned_window.add(plot_frame, width=360)
        
        # 创建图形
        self.fig, self.ax = plt.subplots(figsize=(4,4))
        self.fig.subplots_adjust(left=0.3, right=0.95, top=0.85, bottom=0.25)
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=False)
        
        # 结果显示区域（使用Text控件支持多行）
        result_frame = tk.Frame(bottom_right_frame)
        result_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.result_text = tk.Text(result_frame, font=("Microsoft YaHei", 10), 
                                height=4, width=80, bg='#f0f0f0', 
                                fg='blue', relief=tk.SUNKEN, bd=1)
        self.result_text.pack(fill=tk.X, pady=2)
        self.result_text.config(state=tk.DISABLED)
        
        self.update_plot()
                
    def on_wavelength_change(self):
        """波长变化"""
        wavelength_str = self.wavelength_var.get()
        self.wavelength = int(wavelength_str.replace('nm', ''))
        self.wavelength_entry.delete(0, tk.END)
        self.wavelength_entry.insert(0, str(self.wavelength))
        
        # 更新菜单中的波长显示和电流值
        if hasattr(self, 'menu_system'):
            ms = self.menu_system
            ms.update_measure_display()
            
            # 如果当前在自动测量界面，更新波长设置显示
            if ms.current_menu == "auto_iv":
                # 更新波长显示
                ms.menu_items[2] = f"波长设置: {wavelength_str}"
                if len(ms.menu_labels) >= 3:
                    ms.menu_labels[2].config(text=ms.menu_items[2])
            elif ms.current_menu == "auto_stop":
                # 更新波长显示
                ms.menu_items[2] = f"波长设置: {wavelength_str}"
                if len(ms.menu_labels) >= 3:
                    ms.menu_labels[2].config(text=ms.menu_items[2])
            
            # 只有伏安特性模式才更新表格
            if self.current_table_mode == "iv":
                # 如果当前在手动测量界面，也更新表格数据
                if ms.current_menu in ["manual_iv", "manual_stop"]:
                    if ms.current_menu == "manual_iv":
                        data = ms.manual_iv_data
                    else:
                        data = ms.manual_stop_data
                    if data["U"]:
                        ms.update_table_with_data(data)
            
    def update_params(self):
        """更新参数"""
        try:
            self.aperture = int(self.aperture_entry.get())
            self.wavelength = int(self.wavelength_entry.get())
            messagebox.showinfo("成功", "参数已更新")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值")
            
    def update_plot(self):
        """更新曲线图"""
        if self.current_table_mode == "iv":
            self.update_iv_plot()
        else:
            self.update_h_plot()
    
    def update_iv_plot(self):
        """更新伏安特性曲线图"""
        self.ax.clear()
        
        range_str = self.current_range_var.get()
        exponent = int(range_str.split('^')[-1])
        
        u_data = []
        i_data = []
        for row in self.table_entries:
            try:
                if len(row) >= 2:
                    u_str = row[0].get().strip()
                    i_str = row[1].get().strip()
                    if u_str and i_str:
                        u = float(u_str)
                        i = float(i_str)
                        u_data.append(u)
                        i_data.append(i)
            except ValueError:
                continue
        
        if u_data and i_data:
            sorted_pairs = sorted(zip(u_data, i_data))
            u_sorted, i_sorted = zip(*sorted_pairs)
            
            self.ax.plot(u_sorted, i_sorted, 'b-', linewidth=2, marker='o', markersize=4)
            self.ax.set_xlabel('电压 Uak (V)', fontsize=11, fontproperties='Microsoft YaHei')
            if exponent == -8:
                ylabel = '电流 I (10^-8 A)'
            elif exponent == -9:
                ylabel = '电流 I (10^-9 A)'
            elif exponent == -10:
                ylabel = '电流 I (10^-10 A)'
            elif exponent == -11:
                ylabel = '电流 I (10^-11 A)'
            elif exponent == -12:
                ylabel = '电流 I (10^-12 A)'
            elif exponent == -13:
                ylabel = '电流 I (10^-13 A)'
            else:
                ylabel = '电流 I (A)'
            self.ax.set_ylabel(ylabel, fontsize=11, fontproperties='Microsoft YaHei')
            self.ax.set_title('伏安特性曲线', fontsize=12, fontproperties='Microsoft YaHei', pad=10)
            self.ax.grid(True, alpha=0.3)
            
            if min(i_sorted) < 0:
                self.ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            
            self.fig.tight_layout()
        else:
            self.ax.text(0.5, 0.5, '暂无数据\n请进行测量', 
                        transform=self.ax.transAxes, ha='center', va='center',
                        fontsize=14, color='gray')
            self.ax.set_xlabel('电压 Uak (V)', fontsize=11, fontproperties='Microsoft YaHei')
            self.ax.set_ylabel('电流 I (A)', fontsize=11, fontproperties='Microsoft YaHei')
            self.ax.set_title('伏安特性曲线', fontsize=12, fontproperties='Microsoft YaHei', pad=10)
        
        self.canvas.draw()

    def calculate_plot(self):
        """计算并重绘曲线图"""
        self.update_plot()
        messagebox.showinfo("提示", "曲线已更新")
        
    def clear_data(self):
        """清空当前数据（清空显示和存储数据）"""
        if messagebox.askyesno("确认", "确定要清空所有数据吗？"):
            # 清空表格显示
            for row in self.table_entries:
                row[0].delete(0, tk.END)
                row[1].delete(0, tk.END)
            
            # 清空菜单系统中存储的所有数据
            if hasattr(self, 'menu_system'):
                ms = self.menu_system
                ms.manual_iv_data = {"U": [], "I": []}
                ms.manual_stop_data = {"U": [], "I": []}
                ms.measuring_data = {"U": [], "I": []}
                ms.iv_data = {}
                ms.stop_data = {}
                ms.manual_iv_voltage = 0.0
                ms.manual_stop_voltage = 0.0
            
            # 更新曲线图
            self.update_plot()
            messagebox.showinfo("提示", "数据已清空")
            
    def export_data(self):
        """导出数据"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        if file_path:
            data = []
            for row in self.table_entries:
                try:
                    u = float(row[0].get())
                    i = float(row[1].get())
                    data.append([u, i])
                except ValueError:
                    data.append(["", ""])
            
            df = pd.DataFrame(data, columns=["Uak/V", "I/10^-10A"])
            if file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
            else:
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            messagebox.showinfo("成功", f"数据已导出到 {file_path}")

    def import_data(self):
        """导入数据"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                if file_path.endswith('.xlsx'):
                    df = pd.read_excel(file_path)
                else:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                
                max_rows = len(self.table_entries)
                for idx, row in df.iterrows():
                    if idx < max_rows:
                        self.table_entries[idx][0].delete(0, tk.END)
                        self.table_entries[idx][0].insert(0, str(row[0]))
                        self.table_entries[idx][1].delete(0, tk.END)
                        self.table_entries[idx][1].insert(0, str(row[1]))
                
                self.update_plot()
                messagebox.showinfo("成功", "数据已导入")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {str(e)}")
                
    def on_range_change(self):
        """电流量程变化"""
        range_str = self.current_range_var.get()
        exponent = int(range_str.split('^')[-1])
        self.current_range = 10 ** exponent
        
        # 更新菜单中的电流显示
        if hasattr(self, 'menu_system'):
            self.menu_system.update_measure_display()
            
            # 只有伏安特性模式才更新表格
            if self.current_table_mode == "iv":
                # 如果当前在手动测量界面，也更新表格数据
                if self.menu_system.current_menu in ["manual_iv", "manual_stop"]:
                    if self.menu_system.current_menu == "manual_iv":
                        data = self.menu_system.manual_iv_data
                    else:
                        data = self.menu_system.manual_stop_data
                    if data["U"]:
                        self.menu_system.update_table_with_data(data)
                
                # 如果当前在自动测量中，也更新菜单显示
                if self.menu_system.current_menu in ["auto_iv_measuring", "auto_stop_measuring"]:
                    if hasattr(self.menu_system, 'measuring_data') and self.menu_system.measuring_data["U"]:
                        if self.menu_system.current_measure_type == "iv":
                            voltage = self.menu_system.auto_iv_voltage
                        else:
                            voltage = self.menu_system.auto_stop_voltage
                        wavelength_str = self.wavelength_var.get()
                        wavelength = int(wavelength_str.replace('nm', ''))
                        current = self.menu_system.calculate_current(voltage, wavelength)
                        
                        range_str = self.current_range_var.get()
                        exponent = int(range_str.split('^')[-1])
                        scale_factor = 10 ** (-10 - exponent)
                        current_display = current * scale_factor
                        
                        self.menu_system.menu_items[1] = f"光电流: {current_display:.1f}×{range_str}A"
                        if len(self.menu_system.menu_labels) >= 2:
                            self.menu_system.menu_labels[1].config(text=self.menu_system.menu_items[1])


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoelectricEffectApp(root)
    root.mainloop()