#!/usr/bin/env python3
# -*- coding: utf-8 -*-
    
"""
FD-MGS-A 光谱分析系统
专门用于STM32光谱仪的数据采集和分析

主要功能:
1. 3648像素点光谱数据采集
2. 光谱图实时显示（像素位-光强度）
3. 光谱标定功能（波长-像素位线性拟合）
4. 积分时间设置
5. 数据保存和导出功能

作者: AI Assistant
日期: 2024年
"""

import sys
import time
import threading
import csv
import locale
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
import serial
import serial.tools.list_ports
from datetime import datetime
# from scipy import stats  # 不再需要 scipy
import json

# 配置matplotlib - 关闭字体警告并设置中文字体
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

# 设置matplotlib中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial', 'DejaVu Sans']

from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox, 
                           QFileDialog, QInputDialog, QTextEdit)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, QThread, Qt
from PyQt5.QtGui import QFont

from Ui_FD_MGS_A import Ui_MainWindow


class SpectrumPlotWidget(FigureCanvas):
    """光谱图绘制控件"""
    
    def __init__(self, parent=None):
        # 创建Figure和Canvas
        self.figure = Figure(figsize=(12, 6), dpi=80)
        super().__init__(self.figure)
        self.setParent(parent)
        
        # 创建子图
        self.axes = self.figure.add_subplot(111)
        # 调整子图边距以避免Y轴标签被遮挡
        self.figure.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.12)
        
        # 初始化图表设置
        self.setup_plot()
        
        # 数据存储
        self.spectrum_data = np.zeros(3648)  # 3648个像素点
        self.pixel_positions = np.arange(3648)  # 像素位置
        self.wavelengths = None  # 标定后的波长
        self.is_calibrated = False
        
        # 标定参数
        self.calibration_k = None
        self.calibration_b = None
        self.calibration_r2 = None
        
        # 标定相关
        self.calibration_mode = False
        self.parent_window = None  # 父窗口引用
        self.calibration_points_visual = []  # 图上的标定点标记
        
        # 缩放相关
        self.zoom_mode = False
        self.zoom_start_pos = None
        self.zoom_rect = None
        self.zoom_selection = None  # 存储选择的区间
        self._last_plot_mode = None

        # 鼠标坐标显示
        self.cursor_text = None  # 右上角提示
        self.crosshair_vline = None
        self.crosshair_hline = None
        
        # 连接鼠标事件
        self.mpl_connect('button_press_event', self.on_mouse_click)
        self.mpl_connect('button_release_event', self.on_mouse_release)
        self.mpl_connect('motion_notify_event', self.on_mouse_motion)
        self.mpl_connect('figure_enter_event', self.on_figure_enter)
        self.mpl_connect('figure_leave_event', self.on_figure_leave)
    
    def set_parent_window(self, parent_window):
        """设置父窗口引用"""
        self.parent_window = parent_window
    
    def set_calibration_mode(self, mode):
        """设置标定模式"""
        self.calibration_mode = mode
        if not mode:
            # 退出标定模式时清除标定点标记
            self.clear_calibration_points_visual()
    
    def on_mouse_click(self, event):
        """处理鼠标点击事件"""
        # 确保点击在图表区域内
        if event.inaxes != self.axes:
            return
        
        # 缩放模式优先处理（如果启用）
        if self.zoom_mode:
            if event.button == 1:  # 左键点击   
                self.zoom_start_pos = (event.xdata, event.ydata)
                # 清除之前的选择框
                if self.zoom_rect:
                    self.zoom_rect.remove()
                    self.zoom_rect = None
                self.draw()
                
        # 标定模式处理（仅当缩放模式未启用时）
        elif self.calibration_mode and self.parent_window:
            # 获取点击的x坐标（像素位置）
            click_x = event.xdata
            if click_x is None:
                return
                
            # 限制在有效范围内
            pixel_pos = int(round(click_x))
            pixel_pos = max(0, min(3647, pixel_pos))  # 限制在0-3647范围
            
            # 调用父窗口的方法处理标定点添加
            if hasattr(self.parent_window, 'on_spectrum_click'):
                self.parent_window.on_spectrum_click(pixel_pos)
        
    def on_mouse_release(self, event):
        """处理鼠标释放事件"""
        if not self.zoom_mode or not self.zoom_start_pos:
            return
        
        # 确保释放在图表区域内
        if event.inaxes != self.axes:
            return
        
        if event.button == 1 and event.xdata is not None:  # 左键释放
            # 计算选择区间
            x1, x2 = sorted([self.zoom_start_pos[0], event.xdata])
            
            # 确保区间有效
            if abs(x2 - x1) > 1:  # 最小选择宽度
                self.zoom_selection = (x1, x2)
                print(f"已选择区间: {x1:.1f} - {x2:.1f}，自动放大中...")
                
                # 松手后自动执行缩放
                self.auto_scale_y()
                print("区间缩放完成")
                
                # 缩放完成后自动退出放大模式，避免遗留选框
                if self.parent_window and hasattr(self.parent_window, "exit_zoom_mode"):
                    self.parent_window.exit_zoom_mode("缩放完成，已自动退出放大模式")
                else:
                    self.set_zoom_mode(False)
            else:
                # 清除无效的选择框
                if self.zoom_rect:
                    self.zoom_rect.remove()
                    self.zoom_rect = None
                self.zoom_selection = None
            
            self.zoom_start_pos = None
            self.draw()
    
    def on_mouse_motion(self, event):
        """处理鼠标移动事件"""
        # 坐标提示与十字线
        if event.inaxes == self.axes and event.xdata is not None and event.ydata is not None:
            self.update_cursor_overlay(event.xdata, event.ydata)
        else:
            self.update_cursor_overlay(None, None)
        
        # 缩放模式下拖拽绘制选框
        if not self.zoom_mode or not self.zoom_start_pos:
            return
        
        # 确保在图表区域内
        if event.inaxes != self.axes or event.xdata is None:
            return
        
        # 更新选择框
        if self.zoom_rect:
            self.zoom_rect.remove()
        
        x1, x2 = sorted([self.zoom_start_pos[0], event.xdata])
        y1, y2 = self.axes.get_ylim()
        
        # 创建选择框
        from matplotlib.patches import Rectangle
        self.zoom_rect = Rectangle((x1, y1), x2-x1, y2-y1, 
                                 linewidth=1, edgecolor='red', 
                                 facecolor='red', alpha=0.2)
        self.axes.add_patch(self.zoom_rect)
        self.draw()
    
    def set_zoom_mode(self, mode):
        """设置缩放模式"""
        self.zoom_mode = mode
        if not mode:
            # 退出缩放模式时清除选择框
            if self.zoom_rect:
                self.zoom_rect.remove()
                self.zoom_rect = None
            self.zoom_start_pos = None
            self.zoom_selection = None
            self.draw()

    def update_cursor_overlay(self, xdata, ydata):
        """更新右上角坐标提示与十字线"""
        # 无效坐标时隐藏提示和十字线
        if xdata is None or ydata is None:
            if self.cursor_text:
                self.cursor_text.set_visible(False)
            if self.crosshair_vline:
                self.crosshair_vline.set_visible(False)
            if self.crosshair_hline:
                self.crosshair_hline.set_visible(False)
            self.draw_idle()
            return
        
        # 对齐到曲线数据点：未标定按像素取整，已标定按波长找最近点
        if self.is_calibrated and self.wavelengths is not None:
            idx = int(np.argmin(np.abs(self.wavelengths - xdata)))
            idx = max(0, min(len(self.spectrum_data) - 1, idx))
            x_disp = float(self.wavelengths[idx])
            intensity = float(self.spectrum_data[idx])
            x_info = f"λ: {x_disp:.2f} nm"
        else:
            idx = int(round(xdata))
            idx = max(0, min(len(self.spectrum_data) - 1, idx))
            x_disp = idx
            intensity = float(self.spectrum_data[idx])
            x_info = f"像素: {idx}"
        
        text = f"{x_info}  |  强度: {int(round(intensity))}"
        
        # 提示文本（右上角）
        if not self.cursor_text:
            self.cursor_text = self.axes.text(
                0.99, 0.98, text,
                transform=self.axes.transAxes,
                ha='right', va='top',
                fontsize=9,
                bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7)
            )
        else:
            self.cursor_text.set_text(text)
            self.cursor_text.set_visible(True)
        
        # 十字线
        if not self.crosshair_vline:
            self.crosshair_vline = self.axes.axvline(x_disp, color='gray', linestyle='--', linewidth=0.8, alpha=0.6)
        else:
            self.crosshair_vline.set_xdata(x_disp)
            self.crosshair_vline.set_visible(True)
        
        if not self.crosshair_hline:
            self.crosshair_hline = self.axes.axhline(intensity, color='gray', linestyle='--', linewidth=0.8, alpha=0.6)
        else:
            self.crosshair_hline.set_ydata(intensity)
            self.crosshair_hline.set_visible(True)
        
        self.draw_idle()
    
    def on_figure_enter(self, event):
        """鼠标进入图表区域"""
        self.setCursor(Qt.CrossCursor)
    
    def on_figure_leave(self, event):
        """鼠标离开图表区域"""
        self.unsetCursor()
        self.update_cursor_overlay(None, None)
    
    def auto_scale_y(self):
        """自动缩放到选择区间或当前显示区间"""
        # 优先使用选择的区间，如果没有则使用当前显示范围
        if self.zoom_selection:
            x1, x2 = self.zoom_selection
            print(f"使用选择区间进行缩放: [{x1:.1f}, {x2:.1f}]")
        else:
            x1, x2 = self.axes.get_xlim()
            print(f"使用当前显示区间进行Y轴缩放: [{x1:.1f}, {x2:.1f}]")
        
        # 转换为像素索引
        if self.is_calibrated and self.wavelengths is not None:
            # 如果已标定，从波长转换为像素
            # 波长 = k * 像素 + b，所以 像素 = (波长 - b) / k
            if self.calibration_k and self.calibration_k != 0:
                pixel1 = int((x1 - self.calibration_b) / self.calibration_k)
                pixel2 = int((x2 - self.calibration_b) / self.calibration_k)
            else:
                pixel1, pixel2 = int(x1), int(x2)
        else:
            # 直接使用像素位置
            pixel1, pixel2 = int(x1), int(x2)
        
        # 确保索引在有效范围内
        pixel1 = max(0, min(len(self.spectrum_data)-1, pixel1))
        pixel2 = max(0, min(len(self.spectrum_data)-1, pixel2))
        pixel1, pixel2 = sorted([pixel1, pixel2])
        
        # 获取当前显示区间内的最大值和最小值
        if pixel2 > pixel1:
            current_data = self.spectrum_data[pixel1:pixel2+1]
            max_intensity = np.max(current_data)
            min_intensity = np.min(current_data)
            
            # 设置Y轴范围，增加一些边距
            margin = (max_intensity - min_intensity) * 0.1
            y_min = max(0, min_intensity - margin)  # 确保不低于0
            y_max = max_intensity + margin
            
            # 设置坐标轴范围
            self.axes.set_xlim(x1, x2)  # 设置X轴到选择区间
            self.axes.set_ylim(y_min, y_max)
            
            # 清除选择框（因为已经缩放到选择区间）
            if self.zoom_rect:
                self.zoom_rect.remove()
                self.zoom_rect = None
            self.zoom_selection = None
            
            self.draw()
            print(f"已缩放到区间 [{x1:.1f}, {x2:.1f}]，Y轴范围: [{y_min:.0f}, {y_max:.0f}]")
        else:
            print("当前显示区间无效")
    
    def reset_zoom(self):
        """重置缩放到默认范围，保持标定状态"""
        # 重置Y轴范围
        self.axes.set_ylim(0, 60000)
        
        # 根据标定状态设置X轴范围
        if self.is_calibrated and self.wavelengths is not None:
            # 如果已标定，使用波长范围
            self.axes.set_xlim(np.min(self.wavelengths), np.max(self.wavelengths))
            print(f"重置缩放到标定波长范围: [{np.min(self.wavelengths):.2f}, {np.max(self.wavelengths):.2f}] nm")
        else:
            # 如果未标定，使用像素范围
            self.axes.set_xlim(0, 3648)
            print("重置缩放到像素范围: [0, 3648]")
        
        # 清除选择状态
        if self.zoom_rect:
            self.zoom_rect.remove()
            self.zoom_rect = None
        self.zoom_selection = None
        self.zoom_start_pos = None
        
        self.draw()
        print("缩放重置完成，标定状态已保持")
    
    def add_calibration_point_visual(self, pixel, wavelength, point_number):
        """在图上添加标定点标记"""
        # 获取该像素位置的光强度
        if 0 <= pixel < len(self.spectrum_data):
            intensity = self.spectrum_data[pixel]
        else:
            intensity = 0
            
        # 选择X坐标（像素位或波长）
        if self.is_calibrated and self.wavelengths is not None:
            x_pos = self.calibration_k * pixel + self.calibration_b
        else:
            x_pos = pixel
            
        # 添加红色圆点标记
        point = self.axes.plot(x_pos, intensity, 'ro', markersize=8, markeredgecolor='darkred', markeredgewidth=2)[0]
        
        # 添加文本标注
        text = self.axes.annotate(f'{point_number}', 
                                xy=(x_pos, intensity), 
                                xytext=(x_pos, intensity + 3000),  # 文本在点上方
                                ha='center', va='bottom',
                                fontsize=12, fontweight='bold',
                                color='red',
                                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='red', alpha=0.8))
        
        self.calibration_points_visual.append((point, text))
        self.draw()
    
    def clear_calibration_points_visual(self):
        """清除图上的标定点标记"""
        # 创建一个副本来避免在迭代时修改列表
        points_to_clear = list(self.calibration_points_visual)
        
        for point, text in points_to_clear:
            # 安全移除点标记
            try:
                if point is not None:
                    if hasattr(point, 'remove'):
                        point.remove()
            except (ValueError, AttributeError, RuntimeError):
                pass  # 对象已被移除或不存在
            
            # 安全移除文本标记
            try:
                if text is not None:
                    if hasattr(text, 'remove'):
                        text.remove()
            except (ValueError, AttributeError, RuntimeError):
                pass  # 对象已被移除或不存在
        
        # 清空列表
        self.calibration_points_visual.clear()
        
        # 重绘图形
        try:
            self.draw()
        except Exception as e:
            print(f"重绘图形时发生错误: {e}")
    
    def update_calibration_points_visual(self, calibration_points):
        """更新图上的标定点标记"""
        self.clear_calibration_points_visual()
        for i, (pixel, wavelength) in enumerate(calibration_points):
            self.add_calibration_point_visual(pixel, wavelength, i + 1)
        
    def setup_plot(self):
        """设置图表基本参数"""
        self.axes.clear()
        self.axes.set_xlabel('Pixel Position', fontsize=12)
        self.axes.set_ylabel('Intensity', fontsize=12)
        self.axes.set_title('Spectrum Data Display', fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3)
        
        # 设置坐标轴范围
        self.axes.set_xlim(0, 3648)
        self.axes.set_ylim(0, 60000)
        
        # 设置刻度
        x_ticks = np.arange(0, 3649, 500)  # 500一档
        y_ticks = np.arange(0, 60001, 10000)  # 10000一档
        self.axes.set_xticks(x_ticks)
        self.axes.set_yticks(y_ticks)
        
        self.draw()
    
    def update_spectrum(self, data):
        """更新光谱数据"""
        if len(data) != 3648:
            print(f"警告: 数据长度不匹配，期望3648，收到{len(data)}")
            return
        
        self.spectrum_data = np.array(data)
        self.plot_spectrum()
    
    def plot_spectrum(self):
        """绘制光谱图"""
        prev_xlim = self.axes.get_xlim()
        prev_plot_mode = self._last_plot_mode
        auto_scale_enabled = bool(self.parent_window and getattr(self.parent_window, "auto_scale_enabled", False))

        self.axes.clear()
        # 清理光标提示和十字线引用，防止被清空后无法重建
        self.cursor_text = None
        self.crosshair_vline = None
        self.crosshair_hline = None
        
        # 选择X轴数据（像素位或波长）
        if self.is_calibrated and self.wavelengths is not None:
            x_data = self.wavelengths
            x_label = 'Wavelength (nm)'
            title = f'Spectrum Data (Calibrated, λ={self.calibration_k:.4f}x+{self.calibration_b:.2f})'
            current_plot_mode = "wavelength"
        else:
            x_data = self.pixel_positions
            x_label = 'Pixel Position'
            title = 'Spectrum Data (Pixel Mode)'
            current_plot_mode = "pixel"
        
        # 绘制光谱线
        self.axes.plot(x_data, self.spectrum_data, 'b-', linewidth=1.0, alpha=0.8)
        
        # 设置图表属性
        self.axes.set_xlabel(x_label, fontsize=12)
        self.axes.set_ylabel('Intensity', fontsize=12)
        self.axes.set_title(title, fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3)

        preserve_view = auto_scale_enabled and (prev_plot_mode == current_plot_mode)

        if self.is_calibrated and self.wavelengths is not None:
            min_x = float(np.min(self.wavelengths))
            max_x = float(np.max(self.wavelengths))
            if preserve_view and prev_xlim and len(prev_xlim) == 2:
                x1, x2 = prev_xlim
                x1 = max(min_x, float(x1))
                x2 = min(max_x, float(x2))
                if x2 > x1:
                    self.axes.set_xlim(x1, x2)
                else:
                    self.axes.set_xlim(min_x, max_x)
            else:
                self.axes.set_xlim(min_x, max_x)
        else:
            if preserve_view and prev_xlim and len(prev_xlim) == 2:
                x1, x2 = prev_xlim
                x1 = max(0.0, float(x1))
                x2 = min(3648.0, float(x2))
                if x2 > x1:
                    self.axes.set_xlim(x1, x2)
                else:
                    self.axes.set_xlim(0, 3648)
            else:
                self.axes.set_xlim(0, 3648)
            x_ticks = np.arange(0, 3649, 500)
            self.axes.set_xticks(x_ticks)

        self._last_plot_mode = current_plot_mode

        if auto_scale_enabled:
            self.auto_scale_y()
            return

        self.axes.set_ylim(0, 60000)
        y_ticks = np.arange(0, 60001, 10000)
        self.axes.set_yticks(y_ticks)
        self.draw()
    
    def apply_calibration(self, k, b, r2):
        """应用标定参数"""
        self.calibration_k = k
        self.calibration_b = b
        self.calibration_r2 = r2
        
        # 计算波长
        self.wavelengths = k * self.pixel_positions + b
        self.is_calibrated = True
        
        # 重新绘制
        self.plot_spectrum()
    
    def reset_calibration(self):
        """重置标定"""
        self.wavelengths = None
        self.is_calibrated = False
        self.calibration_k = None
        self.calibration_b = None
        self.calibration_r2 = None
        self.plot_spectrum()


class SerialWorker(QThread):
    """串口工作线程"""
    
    # 信号定义
    data_received = pyqtSignal(list)  # 接收到光谱数据
    status_changed = pyqtSignal(str)  # 状态变化
    error_occurred = pyqtSignal(str)  # 错误发生
    
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.is_running = False
        self.is_connected = False
        self.buffer_clear_requested = False  # 缓冲区清理请求标志
        self.is_receiving_data = False  # 是否正在接收数据的标志
        self.last_data_complete_time = 0  # 上次数据接收完成的时间戳
        
    def connect_serial(self, port, baudrate):
        """连接串口"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            
            self.is_connected = True
            self.status_changed.emit(f"已连接到 {port}")
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"串口连接失败: {str(e)}")
            return False
    
    def disconnect_serial(self):
        """断开串口"""
        try:
            self.is_running = False
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.is_connected = False
            print(f"[DEBUG] 串口断开成功")
            self.status_changed.emit("串口已断开")
        except Exception as e:
            print(f"[ERROR] 断开串口时出错: {str(e)}")
            self.error_occurred.emit(f"断开串口时出错: {str(e)}")
    
    def clear_buffer(self):
        """请求清理串口接收缓冲区，用于积分时间修改后清除旧数据"""
        try:
            if self.serial_port and self.serial_port.is_open:
                # 立即清理硬件缓冲区
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()
                # 设置软件缓冲区清理标志
                self.buffer_clear_requested = True
                print(f"[DEBUG] 串口缓冲区清理请求已发送，硬件缓冲区已清理")
                return True
        except Exception as e:
            print(f"[ERROR] 清理串口缓冲区失败: {str(e)}")
            return False
    
    def is_ready_for_next_capture(self):
        """检查是否准备好进行下一次采集"""
        # 如果正在接收数据，则不能发送新命令
        if self.is_receiving_data:
            print(f"[DEBUG] 仍在接收数据中，跳过本次采集命令")
            return False
        return True
    
    def send_command(self, command):
        """发送命令"""
        if not self.is_connected or not self.serial_port:
            print(f"[ERROR] 串口未连接，无法发送命令")
            self.error_occurred.emit("串口未连接")
            return False
        
        try:
            original_command = command
            if isinstance(command, int):
                command = bytes([command])
            elif isinstance(command, str):
                command = command.encode()
            
            print(f"[DEBUG] 发送命令: 0x{original_command:02X} -> {command.hex()}")
            bytes_written = self.serial_port.write(command)
            self.serial_port.flush()  # 确保数据立即发送
            print(f"[DEBUG] 命令发送成功，写入字节数: {bytes_written}")
            return True
        except Exception as e:
            print(f"[ERROR] 发送命令失败: {str(e)}")
            self.error_occurred.emit(f"发送命令失败: {str(e)}")
            return False
    
    def run(self):
        """主工作循环"""
        self.is_running = True
        buffer = bytearray()
        
        while self.is_running and self.is_connected:
            try:
                # 检查是否需要清理缓冲区
                if self.buffer_clear_requested:
                    old_buffer_size = len(buffer)
                    buffer.clear()
                    self.buffer_clear_requested = False
                    self.is_receiving_data = False  # 重置接收状态
                    print(f"[DEBUG] 软件缓冲区已清理，丢弃 {old_buffer_size} 字节旧数据，接收状态已重置")
                
                if self.serial_port and self.serial_port.in_waiting > 0:
                    # 读取数据
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    buffer.extend(data)
                    self.is_receiving_data = True  # 标记正在接收数据
                    print(f"[DEBUG] 接收到 {len(data)} 字节数据，缓冲区总长度: {len(buffer)}")
                    
                    # 检查是否收到完整的光谱数据包（3648字节）
                    if len(buffer) >= 3648:
                        # 改进的数据包同步算法：
                        # 1. 检查是否有过多数据（可能是多个数据包混合）
                        # 2. 寻找合理的数据包边界
                        # 3. 验证数据包的合理性
                        
                        # 如果缓冲区远超3648字节，说明可能有多个数据包混合
                        if len(buffer) > 3648 * 1.5:  # 超过1.5倍
                            print(f"[WARNING] 缓冲区数据过多 ({len(buffer)}字节)，可能有多个数据包混合")
                            # 只保留前3648字节，丢弃其余数据以重新同步
                            buffer = buffer[:3648]
                        
                        # 寻找数据包开始位置
                        start_pos = 0
                        
                        # 方法1：寻找合理的数据开始模式
                        # 如果第一个字节异常，尝试寻找正确的开始位置
                        if buffer[0] == 0x5E or buffer[0] == 0x5F:
                            # 寻找第一个非0x5E/0x5F的字节作为可能的数据开始
                            for i in range(min(100, len(buffer))):
                                if buffer[i] != 0x5E and buffer[i] != 0x5F:
                                    start_pos = i
                                    break
                            
                            if start_pos > 0:
                                print(f"[DEBUG] 检测到数据包头部异常，从位置 {start_pos} 开始")
                                # 移除异常的头部数据
                                buffer = buffer[start_pos:]
                        
                        # 检查调整后的缓冲区是否还有足够数据
                        if len(buffer) >= 3648:
                            # 提取3648字节的光谱数据
                            spectrum_data = list(buffer[:3648])
                            buffer = buffer[3648:]  # 移除已处理的数据
                            
                            print(f"[DEBUG] 接收到完整光谱数据包: 3648字节")
                            print(f"[DEBUG] 数据样本 (前10字节): {[hex(x) for x in spectrum_data[:10]]}")
                            print(f"[DEBUG] 数据样本 (后10字节): {[hex(x) for x in spectrum_data[-10:]]}")
                            
                            # 修复第一个字节问题：将第一个字节设置为与第二个字节相同
                            if len(spectrum_data) >= 2:
                                original_first = spectrum_data[0]
                                spectrum_data[0] = spectrum_data[1]  # 设置第一个字节等于第二个字节
                                print(f"[DEBUG] 第一个字节修复: {hex(original_first)} -> {hex(spectrum_data[0])}")
                            
                            # 检测和修复积分时间变更后前几个字节的异常数据
                            def detect_and_fix_initial_bytes_anomaly(data):
                                """
                                检测和修复积分时间变更后前几个字节的异常数据
                                """
                                if len(data) < 20:
                                    return data
                                
                                # 分析前20个字节，寻找异常模式
                                first_20 = data[:20]
                                
                                # 检测异常模式：前几个字节显著不同于后续稳定区域
                                # 使用第10-20字节作为参考区域（假设这部分相对稳定）
                                reference_start = 10
                                reference_end = 20
                                reference_values = data[reference_start:reference_end]
                                reference_mean = sum(reference_values) / len(reference_values)
                                reference_std = (sum((x - reference_mean) ** 2 for x in reference_values) / len(reference_values)) ** 0.5
                                
                                # 检测需要修复的字节数
                                anomaly_count = 0
                                threshold = 2.0  # 超过2个标准差认为是异常
                                
                                for i in range(min(10, len(data))):  # 检查前10个字节
                                    if abs(data[i] - reference_mean) > threshold * max(reference_std, 10):
                                        anomaly_count = max(anomaly_count, i + 1)
                                
                                # 如果发现异常，进行修复
                                if anomaly_count > 1:  # 如果有多个字节异常
                                    # 寻找第一个"正常"的字节作为修复基准
                                    repair_value = None
                                    for i in range(anomaly_count, min(anomaly_count + 10, len(data))):
                                        if abs(data[i] - reference_mean) <= threshold * max(reference_std, 10):
                                            repair_value = data[i]
                                            break
                                    
                                    if repair_value is not None:
                                        original_values = [hex(data[i]) for i in range(anomaly_count)]
                                        # 修复前N个异常字节
                                        for i in range(anomaly_count):
                                            data[i] = repair_value
                                        
                                        print(f"[DEBUG] 前{anomaly_count}个字节异常修复:")
                                        print(f"  原值: {original_values}")
                                        print(f"  修复为: {hex(repair_value)} (基于第{anomaly_count+1}-{reference_end}字节的稳定区域)")
                                        print(f"  参考均值: {reference_mean:.1f}, 标准差: {reference_std:.1f}")
                                    else:
                                        print(f"[WARNING] 检测到前{anomaly_count}个字节异常，但未找到合适的修复基准值")
                                
                                return data

                            # 应用异常字节修复
                            spectrum_data = detect_and_fix_initial_bytes_anomaly(spectrum_data)
                            
                            # 验证数据合理性
                            non_zero_count = sum(1 for x in spectrum_data[:100] if x != 0)
                            if non_zero_count < 10:  # 如果前100个字节中非零数据太少
                                print(f"[WARNING] 数据质量可疑，前100字节中只有 {non_zero_count} 个非零值")
                            
                            # 发送数据信号
                            self.data_received.emit(spectrum_data)
                            
                            # 标记数据接收完成
                            import time
                            self.is_receiving_data = False
                            self.last_data_complete_time = time.time()
                            print(f"[DEBUG] 数据接收完成，接收状态已重置")
                        else:
                            print(f"[DEBUG] 数据包同步后数据不足: {len(buffer)}/3648字节")
                
                self.msleep(10)  # 短暂休眠，避免CPU占用过高
                
            except Exception as e:
                print(f"[ERROR] 串口数据读取错误: {str(e)}")
                self.error_occurred.emit(f"数据读取错误: {str(e)}")
                break
        
        self.is_running = False


class CalibrationManager:
    """光谱标定管理器"""
    
    # 标准峰波长（nm）
    STANDARD_PEAKS = {
        "365.016nm": 365.016,
        "404.656nm": 404.656,
        "435.833nm": 435.833,
        "546.075nm": 546.075,
        "576.961nm": 576.961,
        "579.067nm": 579.067
    }
    
    def __init__(self):
        self.calibration_points = []  # [(pixel, wavelength), ...]
    
    def add_calibration_point(self, pixel, wavelength):
        """添加标定点，如果已存在相同波长的标定点则更新"""
        # 检查是否已存在相同波长的标定点
        for i, (existing_pixel, existing_wavelength) in enumerate(self.calibration_points):
            if abs(existing_wavelength - wavelength) < 0.001:  # 浮点数比较，允许小误差
                # 更新已存在的标定点
                self.calibration_points[i] = (pixel, wavelength)
                return i  # 返回更新后的索引
        # 如果不存在，添加新的标定点
        self.calibration_points.append((pixel, wavelength))
        return len(self.calibration_points) - 1  # 返回新添加的索引
    
    def remove_calibration_point(self, index):
        """移除标定点"""
        if 0 <= index < len(self.calibration_points):
            del self.calibration_points[index]
    
    def clear_calibration_points(self):
        """清空标定点"""
        self.calibration_points.clear()
    
    def get_calibration_points_count(self):
        """获取标定点数量"""
        return len(self.calibration_points)
    
    def calculate_calibration(self):
        """计算标定参数"""
        if len(self.calibration_points) < 2:
            raise ValueError("至少需要2个标定点")
        
        # 提取像素位和波长数据
        pixels = np.array([point[0] for point in self.calibration_points])
        wavelengths = np.array([point[1] for point in self.calibration_points])
        
        # 线性拟合: λ = k*x + b
        # 使用 numpy.polyfit 替代 scipy.stats.linregress
        coeffs = np.polyfit(pixels, wavelengths, 1)
        slope = coeffs[0]
        intercept = coeffs[1]
        
        # 计算 R² (决定系数)
        y_pred = slope * pixels + intercept
        ss_res = np.sum((wavelengths - y_pred) ** 2)
        ss_tot = np.sum((wavelengths - np.mean(wavelengths)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # 计算标准误差
        n = len(pixels)
        std_err = np.sqrt(ss_res / (n - 2)) if n > 2 else 0
        
        return {
            'k': slope,           # 标定系数
            'b': intercept,       # 标定截距
            'r2': r_squared,      # 决定系数
            'p_value': 0.0,       # p值（numpy 不直接提供，设为0）
            'std_err': std_err    # 标准误差
        }
    
    def get_calibration_points_text(self):
        """获取标定点的文本描述"""
        if not self.calibration_points:
            return "暂无标定点"
        
        text = f"标定点数量: {len(self.calibration_points)}\n"
        for i, (pixel, wavelength) in enumerate(self.calibration_points):
            text += f"{i+1}. 像素位 {pixel} → {wavelength:.3f} nm\n"
        
        return text


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        print("开始初始化MainWindow...")
        try:
            super().__init__()
            print("QMainWindow初始化完成")
            
            print("创建UI对象...")
            self.ui = Ui_MainWindow()
            print("设置UI...")
            self.ui.setupUi(self)
            print("UI设置完成")
        
            # 初始化变量
            self.current_spectrum_data = np.zeros(3648)
            self.is_continuous_capturing = False
            self.calibration_mode = False
            self.integration_time_just_changed = False  # 积分时间刚刚改变的标志
            self.auto_scale_enabled = False
            
            # 存储连接信息用于重连
            self.last_connected_port = None
            self.last_connected_baudrate = None
            
            # 初始化组件
            print("初始化组件...")
            self.init_components()
            print("组件初始化完成")
            
            print("初始化UI界面...")
            self.init_ui()
            print("UI界面初始化完成")
            
            print("连接信号...")
            self.connect_signals()
            print("信号连接完成")
        
            print("FD-MGS-A 光谱分析系统初始化完成")
        except Exception as e:
            print(f"MainWindow初始化失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def init_components(self):
        """初始化组件"""
                # 创建光谱图控件
        self.spectrum_widget = SpectrumPlotWidget()
        
        # 将光谱图控件添加到布局中 - 修复布局问题
        from PyQt5.QtWidgets import QVBoxLayout
        
        # 删除原有的占位符控件
        self.ui.spectrumPlotWidget.deleteLater()
        
        # 创建新的布局并添加光谱图控件
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 25, 15, 15)  # 增加左右边距避免Y轴标签被遮挡
        layout.addWidget(self.spectrum_widget)
        self.ui.spectrumGroupBox.setLayout(layout)
        
        # 创建串口工作线程
        self.serial_worker = SerialWorker()
        
        # 创建定时器（用于连续采集）
        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self.send_capture_command)
        
        # 创建标定管理器
        self.calibration_manager = CalibrationManager()
        
        # 设置光谱图控件的父窗口和标定模式
        self.spectrum_widget.set_parent_window(self)
        self.spectrum_widget.set_calibration_mode(self.calibration_mode)
    
    def init_ui(self):
        """初始化UI界面"""
        # 设置窗口图标和标题
        self.setWindowTitle("FD-MGS-A 光谱分析系统")
        
        # 初始化串口选项
        self.refresh_serial_ports()
        
        # 初始化波特率选项
        baudrates = ["256000"]
        self.ui.baudrateComboBox.addItems(baudrates)
        self.ui.baudrateComboBox.setCurrentText("256000")  # 默认256000
        
        # 设置积分时间默认选项（UI文件中已定义选项）
        self.ui.integrationComboBox.setCurrentText("10us")  # 默认10μs
        
        # 初始化标准峰选项
        self.ui.peakComboBox.addItems(list(CalibrationManager.STANDARD_PEAKS.keys()))
        
        # 设置初始状态
        self.ui.disconnectButton.setEnabled(False)
        self.ui.singleCaptureButton.setEnabled(False)
        self.ui.continuousCaptureButton.setEnabled(False)
        self.ui.stopCaptureButton.setEnabled(False)
        self.ui.setIntegrationButton.setEnabled(False)
        
        # 显示初始演示数据
        self.show_demo_spectrum()
        # 标定按钮始终可用，因为可以导入数据进行标定
        

        
        # 设置字体
        font = QFont("Microsoft YaHei", 9)
        self.setFont(font)
    
    def connect_signals(self):
        """连接信号和槽"""
        # 串口控制
        self.ui.refreshPortsButton.clicked.connect(self.refresh_serial_ports)
        self.ui.connectButton.clicked.connect(self.connect_serial)
        self.ui.disconnectButton.clicked.connect(self.disconnect_serial)
        
        
        # 曝光时间设置
        self.ui.setIntegrationButton.clicked.connect(self.set_integration_time)
        
        # 采集控制
        self.ui.singleCaptureButton.clicked.connect(self.single_capture)
        self.ui.continuousCaptureButton.clicked.connect(self.start_continuous_capture)
        self.ui.stopCaptureButton.clicked.connect(self.stop_capture)
        
        # 光谱标定
        self.ui.startCalibrationButton.clicked.connect(self.start_calibration)
        self.ui.clearCalibrationButton.clicked.connect(self.clear_calibration)
        self.ui.applyCalibrationButton.clicked.connect(self.import_calibration)
        self.ui.addCalibrationPointButton.clicked.connect(self.add_calibration_peak)
        

        
        # 图形控制（在数据采集组框中）
        self.ui.zoomModeButton.clicked.connect(self.toggle_zoom_mode)
        self.ui.autoScaleButton.clicked.connect(self.auto_scale_spectrum)
        self.ui.resetZoomButton.clicked.connect(self.reset_spectrum_zoom)
        
        # 串口工作线程信号
        self.serial_worker.data_received.connect(self.on_data_received)
        self.serial_worker.status_changed.connect(self.on_status_changed)
        self.serial_worker.error_occurred.connect(self.on_error_occurred)
        
        # 菜单动作
        self.ui.saveSpectrumAction.triggered.connect(self.save_spectrum_data)
        self.ui.loadSpectrumAction.triggered.connect(self.load_spectrum_data)
        self.ui.exportCalibrationAction.triggered.connect(self.export_calibration)
        self.ui.importCalibrationAction.triggered.connect(self.import_calibration_file)
        self.ui.aboutAction.triggered.connect(self.show_about)
    
    def refresh_serial_ports(self):
        """刷新串口列表"""
        self.ui.portComboBox.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.ui.portComboBox.addItem(f"{port.device} - {port.description}")
    
    def connect_serial(self):
        """连接串口"""
        if self.ui.portComboBox.count() == 0:
            QMessageBox.warning(self, "警告", "没有找到可用的串口")
            return
        
        # 获取选择的端口和波特率
        port_text = self.ui.portComboBox.currentText()
        port = port_text.split(" - ")[0] if " - " in port_text else port_text
        
        try:
            baudrate = int(self.ui.baudrateComboBox.currentText())
        except ValueError:
            QMessageBox.warning(self, "错误", "无效的波特率设置")
            return
        
        # 验证波特率
        if baudrate != 256000:
            QMessageBox.warning(self, "错误", "仅支持256000波特率")
            return
        
        # 尝试连接
        try:
            print(f"[DEBUG] 尝试连接串口: {port}, 波特率: {baudrate}")
            if self.serial_worker.connect_serial(port, baudrate):
                # 保存连接信息用于重连
                self.last_connected_port = port
                self.last_connected_baudrate = baudrate
                
                # 启动串口工作线程
                print(f"[DEBUG] 串口连接成功，启动工作线程")
                self.serial_worker.start()
                
                # 更新UI状态
                self.ui.connectButton.setEnabled(False)
                self.ui.disconnectButton.setEnabled(True)
                self.ui.singleCaptureButton.setEnabled(True)
                self.ui.continuousCaptureButton.setEnabled(True)
                self.ui.setIntegrationButton.setEnabled(True)
                # 标定按钮始终可用，不依赖串口连接状态
                
                self.ui.connectionStatusLabel.setText(f"状态: 已连接 ({port})")
                self.ui.connectionStatusLabel.setStyleSheet("color: green;")
                self.ui.currentPortLabel.setText(f"当前端口: {port}")
                print(f"[DEBUG] UI状态更新完成，串口连接就绪")
            else:
                print(f"[ERROR] 串口连接失败")
                QMessageBox.critical(self, "错误", "串口连接失败")
        except Exception as e:
            print(f"[ERROR] 串口连接异常: {str(e)}")
            QMessageBox.critical(self, "错误", f"连接失败: {str(e)}")
    
    def disconnect_serial(self):
        """断开串口"""
        # 停止采集
        self.stop_capture()
        
        # 断开串口
        self.serial_worker.disconnect_serial()
        self.serial_worker.quit()
        self.serial_worker.wait()
        
        # 更新UI状态
        self.ui.connectButton.setEnabled(True)
        self.ui.disconnectButton.setEnabled(False)

        self.ui.singleCaptureButton.setEnabled(False)
        self.ui.continuousCaptureButton.setEnabled(False)
        self.ui.stopCaptureButton.setEnabled(False)
        self.ui.setIntegrationButton.setEnabled(False)
        # 标定按钮始终可用，不依赖串口连接状态
        # addCalibrationPointButton 的状态由标定模式控制
        
        self.ui.connectionStatusLabel.setText("状态: 未连接")
        self.ui.connectionStatusLabel.setStyleSheet("color: red;")
        
        # 退出标定模式
        if self.calibration_mode:
            self.calibration_mode = False
            self.ui.startCalibrationButton.setText("开始标定")
    
    def set_integration_time(self):
        """设置曝光时间"""
        try:
            # 检查串口连接状态
            if not self.serial_worker.is_connected:
                QMessageBox.warning(self, "警告", "串口未连接，请先连接串口")
                return
            
            # 曝光时间命令映射（B1-BF指令）
            integration_commands = {
                "10us": 0xB1, "20us": 0xB2, "50us": 0xB3, "100us": 0xB4,
                "200us": 0xB5, "500us": 0xB6, "1ms": 0xB7, "2ms": 0xB8,
                "4ms": 0xB9, "8ms": 0xBA, "20ms": 0xBB, "50ms": 0xBC,
                "100ms": 0xBD, "200ms": 0xBE, "500ms": 0xBF
            }
            
            integration_time = self.ui.integrationComboBox.currentText()
            command = integration_commands.get(integration_time)
            
            print(f"[DEBUG] 设置曝光时间: {integration_time}, 命令: 0x{command:02X}")
            
            if command and self.serial_worker.send_command(command):
                # 发送成功后清理串口缓冲区，避免新旧数据混合
                print(f"[DEBUG] 积分时间设置成功，正在清理串口缓冲区...")
                self.serial_worker.clear_buffer()
                
                # 设置积分时间变更标志，用于单次采集检测
                self.integration_time_just_changed = True
                
                # 根据积分时间计算动态稳定时间
                settle_time = self._calculate_settle_time(integration_time)
                
                # 在稳定期间禁用采集按钮，防止用户操作
                self.ui.singleCaptureButton.setEnabled(False)
                self.ui.continuousCaptureButton.setEnabled(False)
                
                # 显示等待状态信息
                self.ui.statusbar.showMessage(f"积分时间设置为 {integration_time}，等待硬件稳定 ({settle_time}ms)...", settle_time + 500)
                
                # 使用动态延迟时间，让硬件有足够时间稳定
                QTimer.singleShot(settle_time, lambda: self._on_integration_time_settled(integration_time))
                
                print(f"[DEBUG] 曝光时间设置成功: {integration_time}，缓冲区已清理，禁用采集按钮，等待硬件稳定 {settle_time}ms...")
            else:
                QMessageBox.warning(self, "警告", "曝光时间设置失败")
                print(f"[DEBUG] 曝光时间设置失败: {integration_time}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"曝光时间设置操作失败: {str(e)}")
            print(f"[ERROR] 曝光时间设置异常: {str(e)}")
    
    def _calculate_settle_time(self, integration_time):
        """根据积分时间计算硬件稳定时间"""
        # 积分时间到数值的映射（微秒为单位）
        time_to_microseconds = {
            "10us": 10, "20us": 20, "50us": 50, "100us": 100,
            "200us": 200, "500us": 500, "1ms": 1000, "2ms": 2000,
            "4ms": 4000, "8ms": 8000, "20ms": 20000, "50ms": 50000,
            "100ms": 100000, "200ms": 200000, "500ms": 500000
        }
        
        microseconds = time_to_microseconds.get(integration_time, 1000)
        
        # 改进的动态稳定时间算法：
        # 1. 基础稳定时间：100ms（增加基础稳定时间）
        # 2. 积分时间影响：积分时间越长，稳定时间相对增加
        # 3. 分段计算，确保硬件完全稳定
        # 4. 考虑数据传输时间：3648字节@256000bps ≈ 114ms
        
        if microseconds <= 100:  # 10us-100us
            settle_time = 100
        elif microseconds <= 1000:  # 200us-1ms
            settle_time = 150
        elif microseconds <= 10000:  # 2ms-8ms
            settle_time = 200
        elif microseconds <= 50000:  # 20ms-50ms
            settle_time = 300
        elif microseconds <= 200000:  # 100ms-200ms
            settle_time = 400  # 增加到400ms，确保200ms积分时间有足够稳定时间
        else:  # 500ms
            settle_time = 600  # 增加到600ms
        
        print(f"[DEBUG] 积分时间 {integration_time} ({microseconds}us) -> 稳定时间 {settle_time}ms")
        return settle_time
    
    def _calculate_min_safe_interval(self, integration_time):
        """计算最小安全采集间隔"""
        # 积分时间到毫秒的映射
        time_to_milliseconds = {
            "10us": 0.01, "20us": 0.02, "50us": 0.05, "100us": 0.1,
            "200us": 0.2, "500us": 0.5, "1ms": 1, "2ms": 2,
            "4ms": 4, "8ms": 8, "20ms": 20, "50ms": 50,
            "100ms": 100, "200ms": 200, "500ms": 500
        }
        
        integration_ms = time_to_milliseconds.get(integration_time, 1)
        
        # 最小安全间隔 = 积分时间 + 数据传输时间 + 安全缓冲时间
        # 数据传输时间：3648字节 @ 256000bps ≈ 114ms（理论）+ 50ms（系统开销）= 164ms
        # 安全缓冲时间：至少100ms，确保系统有时间处理数据
        
        data_transfer_time = 164  # 数据传输时间（ms）
        safety_buffer = 150  # 安全缓冲时间（ms）
        
        min_interval = int(integration_ms + data_transfer_time + safety_buffer)
        
        # 确保最小间隔至少为300ms
        min_interval = max(300, min_interval)
        
        print(f"[DEBUG] 积分时间 {integration_time} ({integration_ms}ms) -> 最小安全间隔 {min_interval}ms")
        return min_interval
    
    def _on_integration_time_settled(self, integration_time):
        """积分时间设置稳定后的回调"""
        self.integration_time_just_changed = False
        settle_time = self._calculate_settle_time(integration_time)
        
        # 重新启用采集按钮，但只有在串口连接的情况下
        if self.serial_worker.is_connected:
            self.ui.singleCaptureButton.setEnabled(True)
            self.ui.continuousCaptureButton.setEnabled(True)
        
        self.ui.currentIntegrationLabel.setText(f"当前曝光时间: {integration_time}")
        self.ui.statusbar.showMessage(f"曝光时间设置为 {integration_time}，硬件已稳定 (用时{settle_time}ms)，采集按钮已恢复", 3000)
        print(f"[DEBUG] 积分时间硬件稳定完成: {integration_time}，稳定用时: {settle_time}ms，采集按钮已重新启用")
    
    def single_capture(self):
        """单次采集"""
        try:
            # 检查串口连接状态
            if not self.serial_worker.is_connected:
                QMessageBox.warning(self, "警告", "串口未连接，请先连接串口")
                return

            if self.is_continuous_capturing:
                self.stop_capture()
            
            # 检查积分时间是否刚刚改变
            if hasattr(self, 'integration_time_just_changed') and self.integration_time_just_changed:
                self.ui.statusbar.showMessage("积分时间刚刚修改，请稍等硬件稳定...", 2000)
                print(f"[DEBUG] 积分时间刚刚修改，跳过本次采集请求")
                return
            
            print(f"[DEBUG] 开始单次采集，发送命令 0xA2")
            self.ui.statusbar.showMessage("正在发送单次采集命令 0xA2...", 1000)
            
            if self.serial_worker.send_command(0xA2):
                self.ui.captureStatusLabel.setText("状态: 单次采集中...")
                self.ui.captureStatusLabel.setStyleSheet("color: orange;")
                print(f"[DEBUG] 单次采集命令 0xA2 发送成功")
                self.ui.statusbar.showMessage("单次采集命令已发送，等待数据...", 2000)
            else:
                QMessageBox.warning(self, "警告", "发送采集命令失败")
                print(f"[DEBUG] 单次采集命令 0xA2 发送失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"单次采集操作失败: {str(e)}")
            print(f"[ERROR] 单次采集异常: {str(e)}")
    
    def start_continuous_capture(self):
        """开始连续采集"""
        if self.is_continuous_capturing:
            return
        
        # 从下拉框获取间隔值
        interval_text = self.ui.intervalComboBox.currentText()
        delay_ms = int(interval_text.replace('ms', ''))
        
        # 计算当前积分时间对应的最小安全采集间隔
        integration_text = self.ui.integrationComboBox.currentText()
        min_safe_interval = self._calculate_min_safe_interval(integration_text)
        
        # 检查采集间隔是否足够
        if delay_ms < min_safe_interval:
            warning_msg = (f"⚠️ 警告：采集间隔 {delay_ms}ms 可能不足！\n\n"
                          f"当前积分时间：{integration_text}\n"
                          f"推荐最小采集间隔：{min_safe_interval}ms\n\n"
                          f"当前设置可能导致：\n"
                          f"1. 数据包重叠混乱\n"
                          f"2. 部分采集命令被跳过\n"
                          f"3. 数据质量下降\n\n"
                          f"是否仍要继续？")
            
            reply = QMessageBox.question(self, "采集间隔警告", warning_msg,
                                        QMessageBox.Yes | QMessageBox.No, 
                                        QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # 在开始定时器前，先清理串口缓冲区并确保串口线程处于就绪状态，
        # 防止旧数据或未完成的接收阻塞首次采集命令。
        try:
            self.serial_worker.clear_buffer()
        except Exception as e:
            print(f"[WARNING] 清理串口缓冲区失败: {e}")

        def _start_timer_after_clear():
            # 再次检查线程就绪状态
            if not self.serial_worker.is_ready_for_next_capture():
                # 如果仍然未就绪，再延迟一段时间重试一次
                print("[DEBUG] 串口仍未就绪，延迟100ms后重试启动连续采集")
                QTimer.singleShot(100, _start_timer_after_clear)
                return

            self.is_continuous_capturing = True
            # 启动定时器
            self.capture_timer.start(delay_ms)
            # 更新UI状态
            self.ui.continuousCaptureButton.setEnabled(False)
            self.ui.stopCaptureButton.setEnabled(True)
            self.ui.captureStatusLabel.setText(f"状态: 连续采集中 ({delay_ms}ms)")
            self.ui.captureStatusLabel.setStyleSheet("color: blue;")
            status_msg = f"开始连续采集，间隔{delay_ms}ms"
            if delay_ms < min_safe_interval:
                status_msg += f" [警告：低于推荐值{min_safe_interval}ms]"
            self.ui.statusbar.showMessage(status_msg, 3000)

        # 在清理后短延时再启动，确保 SerialWorker 能处理清理请求
        QTimer.singleShot(50, _start_timer_after_clear)
    
    def stop_capture(self):
        """停止采集"""
        # 停止连续采集定时器
        self.capture_timer.stop()
        self.is_continuous_capturing = False
        
        # 更新UI状态
        self.ui.continuousCaptureButton.setEnabled(True)
        self.ui.stopCaptureButton.setEnabled(False)
        self.ui.captureStatusLabel.setText("状态: 待机")
        self.ui.captureStatusLabel.setStyleSheet("color: green;")
        
        self.ui.statusbar.showMessage("停止采集", 1000)
    
    def send_capture_command(self):
        """发送采集命令（用于连续采集）"""
        # 检查是否准备好进行下一次采集
        if not self.serial_worker.is_ready_for_next_capture():
            print(f"[DEBUG] 上一次采集尚未完成，跳过本次采集命令")
            return
        
        if not self.serial_worker.send_command(0xA2):
            self.stop_capture()
            QMessageBox.warning(self, "警告", "发送采集命令失败，停止连续采集")
    
    def start_calibration(self):
        """开始/结束标定模式"""
        if not self.calibration_mode:
            # 进入标定模式
            self.calibration_mode = True
            self.ui.startCalibrationButton.setText("退出标定")
            self.spectrum_widget.set_calibration_mode(True)
            
            # 清空之前的标定点
            self.calibration_manager.clear_calibration_points()
            self.update_calibration_points_display()
            
            self.ui.statusbar.showMessage("标定模式：在光谱图上点击峰位置添加标定点，或手动输入像素位添加", 5000)
            
        else:
            # 退出标定模式
            self.calibration_mode = False
            self.ui.startCalibrationButton.setText("开始标定")
            self.spectrum_widget.set_calibration_mode(False)
            
            self.ui.statusbar.showMessage("退出标定模式", 2000)
    
    def on_spectrum_click(self, pixel_pos):
        """处理光谱图点击事件（标定模式下）"""
        if not self.calibration_mode:
            return
            
        # 弹出对话框让用户选择标准峰
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLabel, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("添加标定点")
        dialog.setModal(True)
        dialog.resize(300, 150)
        
        layout = QVBoxLayout()
        
        # 显示点击的像素位置
        pixel_label = QLabel(f"选择的像素位置: {pixel_pos}")
        layout.addWidget(pixel_label)
        
        # 标准峰选择
        peak_label = QLabel("选择对应的标准峰:")
        layout.addWidget(peak_label)
        
        peak_combo = QComboBox()
        for peak_name in CalibrationManager.STANDARD_PEAKS.keys():
            peak_combo.addItem(peak_name)
        layout.addWidget(peak_combo)
        
        # 按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        cancel_button = QPushButton("取消")
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # 连接按钮事件
        result = {'added': False}
        
        def on_add():
            peak_text = peak_combo.currentText()
            wavelength = CalibrationManager.STANDARD_PEAKS[peak_text]
            
            # 检查是否已存在相同波长的标定点
            existing_index = None
            for i, (existing_pixel, existing_wavelength) in enumerate(self.calibration_manager.calibration_points):
                if abs(existing_wavelength - wavelength) < 0.001:
                    existing_index = i
                    break
            
            # 添加或更新标定点
            point_index = self.calibration_manager.add_calibration_point(pixel_pos, wavelength)
            
            # 更新显示（会自动清除并重新绘制所有标定点）
            self.update_calibration_points_display()
            
            if existing_index is not None:
                self.ui.statusbar.showMessage(f"更新标定点: 像素位 {pixel_pos} → {wavelength:.3f} nm（覆盖了之前的标定点）", 3000)
            else:
                point_count = self.calibration_manager.get_calibration_points_count()
                self.ui.statusbar.showMessage(f"添加标定点 {point_count}: 像素位 {pixel_pos} → {wavelength:.3f} nm", 3000)
            
            result['added'] = True
            dialog.accept()
        
        def on_cancel():
            dialog.reject()
        
        add_button.clicked.connect(on_add)
        cancel_button.clicked.connect(on_cancel)
        
        dialog.exec_()
        
        return result['added']
    
    def clear_calibration(self):
        """清除所有标定点"""
        # 二次确认
        reply = QMessageBox.question(
            self, 
            "确认清除", 
            "确定要清除所有标定点吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # 先清除图上的标定点可视化标记
            self.spectrum_widget.clear_calibration_points_visual()
            
            # 清除标定管理器中的标定点
            self.calibration_manager.clear_calibration_points()
            
            # 重置光谱图的标定状态（会触发重绘）
            self.spectrum_widget.reset_calibration()
            
            # 更新标定点数量显示
            count = self.calibration_manager.get_calibration_points_count()
            self.ui.calibrationPointsLabel.setText(f"标定点数量: {count}")
            
            # 重置标定结果显示
            self.ui.calibrationResultLabel.setText("拟合系数 k: 未计算")
            self.ui.calibrationInterceptLabel.setText("拟合截距 b: 未计算")
            self.ui.calibrationR2Label.setText("相关系数 r²: 未计算")
            
            self.ui.statusbar.showMessage("已清除所有标定点", 2000)
        except Exception as e:
            print(f"清除标定时发生错误: {e}")
            self.ui.statusbar.showMessage(f"清除标定失败: {e}", 3000)
    
    def add_calibration_peak(self):
        """添加标定峰"""
        # 移除标定模式检查，允许随时添加标定点
        
        # 获取选择的标准峰
        peak_text = self.ui.peakComboBox.currentText()
        wavelength = CalibrationManager.STANDARD_PEAKS[peak_text]
        
        # 获取像素位输入框的值
        pixel = self.ui.pixelSpinBox.value()
        
        # 检查是否已存在相同波长的标定点
        existing_index = None
        for i, (existing_pixel, existing_wavelength) in enumerate(self.calibration_manager.calibration_points):
            if abs(existing_wavelength - wavelength) < 0.001:
                existing_index = i
                break
        
        # 添加或更新标定点
        point_index = self.calibration_manager.add_calibration_point(pixel, wavelength)
        
        # 更新显示（会自动清除并重新绘制所有标定点）
        self.update_calibration_points_display()
        
        if existing_index is not None:
            self.ui.statusbar.showMessage(f"更新标定点: 像素位 {pixel} → {wavelength:.3f} nm（覆盖了之前的标定点）", 3000)
        else:
            self.ui.statusbar.showMessage(f"添加标定点: 像素位 {pixel} → {wavelength:.3f} nm", 3000)
    
    
    def import_calibration(self):
        """导入标定（计算标定参数）"""
        if self.calibration_manager.get_calibration_points_count() < 2:
            QMessageBox.warning(self, "警告", "至少需要2个标定点才能进行拟合")
            return
        
        try:
            # 计算标定参数
            result = self.calibration_manager.calculate_calibration()
            
            k = result['k']
            b = result['b']
            r2 = result['r2']
            
            # 显示标定结果
            self.ui.calibrationResultLabel.setText(f"拟合系数 k: {k:.6f}")
            self.ui.calibrationInterceptLabel.setText(f"拟合截距 b: {b:.2f}")
            self.ui.calibrationR2Label.setText(f"相关系数 r²: {r2:.6f}")
            
            # 应用标定到光谱图
            self.spectrum_widget.apply_calibration(k, b, r2)
            
            # 退出标定模式
            self.calibration_mode = False
            self.ui.startCalibrationButton.setText("开始标定")
            
            QMessageBox.information(self, "成功", 
                f"光谱标定完成！\n"
                f"拟合方程: λ = {k:.6f}x + {b:.2f}\n"
                f"相关系数 r² = {r2:.6f}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"标定计算失败: {str(e)}")
    
    def update_calibration_points_display(self):
        """更新标定点显示"""
        count = self.calibration_manager.get_calibration_points_count()
        self.ui.calibrationPointsLabel.setText(f"标定点数量: {count}")
        
        # 更新标定列表文本框
        calibration_text = self.calibration_manager.get_calibration_points_text()
        self.ui.calibrationListTextEdit.setPlainText(calibration_text)
        
        # 同时更新图上的标定点显示
        self.spectrum_widget.update_calibration_points_visual(self.calibration_manager.calibration_points)
    
    def show_demo_spectrum(self):
        """显示演示光谱数据"""
        try:
            print("[DEBUG] 生成演示光谱数据...")
            
            # 生成3648个点的模拟光谱数据
            x = np.arange(3648)
            
            # 创建多个高斯峰的组合光谱
            spectrum = np.zeros(3648)
            
            # 添加几个典型的光谱峰
            peaks = [
                (500, 15000, 50),   # 位置, 高度, 宽度
                (1000, 25000, 80),
                (1500, 20000, 60),
                (2000, 35000, 100),
                (2500, 18000, 70),
                (3000, 12000, 40)
            ]
            
            for pos, height, width in peaks:
                spectrum += height * np.exp(-((x - pos) ** 2) / (2 * width ** 2))
            
            # 添加基线和噪声
            baseline = 2000 + 1000 * np.sin(x / 1000)  # 基线漂移
            noise = np.random.normal(0, 500, 3648)     # 随机噪声
            spectrum += baseline + noise
            
            # 确保数据在合理范围内
            spectrum = np.clip(spectrum, 0, 60000)
            
            # 存储演示数据
            self.current_spectrum_data = spectrum
            
            # 更新光谱图显示
            self.spectrum_widget.update_spectrum(spectrum)
            
            # 更新统计信息
            max_intensity = np.max(spectrum)
            avg_intensity = np.mean(spectrum)
            
            self.ui.dataLengthLabel.setText("数据长度: 3648 / 3648 (演示数据)")
            self.ui.maxIntensityLabel.setText(f"最大光强: {int(max_intensity)}")
            self.ui.avgIntensityLabel.setText(f"平均光强: {int(avg_intensity)}")
            self.ui.timestampLabel.setText(f"演示时间: {datetime.now().strftime('%H:%M:%S')}")
            
            # 更新状态显示
            self.ui.captureStatusLabel.setText("状态: 演示数据已加载")
            self.ui.captureStatusLabel.setStyleSheet("color: blue;")
            
            print(f"[DEBUG] 演示数据生成完成 - 最大值: {max_intensity:.1f}, 平均值: {avg_intensity:.1f}")
            
        except Exception as e:
            print(f"[ERROR] 生成演示数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def on_data_received(self, data):
        """处理接收到的光谱数据"""
        try:
            print(f"[DEBUG] 开始处理接收到的数据，长度: {len(data)}")
            
            # 验证数据长度
            if len(data) != 3648:
                error_msg = f"数据长度错误: {len(data)}/3648"
                print(f"[ERROR] {error_msg}")
                self.ui.statusbar.showMessage(error_msg, 3000)
                return
            
            print(f"[DEBUG] 数据长度验证通过: 3648字节")
            
            # 将原始数据 (0x00-0xFF) 转换为光强度 (0-60000)
            # 数据映射: 0x00(0) -> 0, 0xFF(255) -> 60000
            raw_data = np.array(data, dtype=np.float64)
            spectrum_data = raw_data * (60000.0 / 255.0)  # 线性映射
            self.current_spectrum_data = spectrum_data
            print(f"[DEBUG] 数据转换完成: {len(data)}字节 0x00-0xFF -> 0-60000光强度")
            print(f"[DEBUG] 原始数据范围: {int(np.min(raw_data))}-{int(np.max(raw_data))}")
            print(f"[DEBUG] 转换后范围: {int(np.min(spectrum_data))}-{int(np.max(spectrum_data))}")
            
            # 更新光谱图显示
            self.spectrum_widget.update_spectrum(spectrum_data)
            print(f"[DEBUG] 光谱图更新完成")
            
            # 计算统计信息
            max_intensity = np.max(spectrum_data)
            avg_intensity = np.mean(spectrum_data)
            
            print(f"[DEBUG] 统计信息 - 最大光强: {max_intensity}, 平均光强: {avg_intensity}")
            
            # 更新状态信息
            self.ui.dataLengthLabel.setText(f"数据长度: {len(data)} / 3648")
            self.ui.maxIntensityLabel.setText(f"最大光强: {int(max_intensity)}")
            self.ui.avgIntensityLabel.setText(f"平均光强: {int(avg_intensity)}")
            self.ui.timestampLabel.setText(f"采集时间: {datetime.now().strftime('%H:%M:%S')}")
            
            # 显示原始数据和转换后的光强度（前50个点）
            raw_data_text = "原始数据 -> 光强度 (前50点):\n"
            raw_data_text += "十六进制  十进制  光强度\n"
            raw_data_text += "------------------------\n"
            for i in range(min(50, len(data))):
                hex_val = data[i]
                intensity = int(spectrum_data[i])
                raw_data_text += f"0x{hex_val:02X}     {hex_val:3d}    {intensity:5d}\n"
            self.ui.statusTextEdit.setPlainText(raw_data_text)
            
            # 更新采集状态
            if not self.is_continuous_capturing:    
                self.ui.captureStatusLabel.setText("状态: 采集完成")
                self.ui.captureStatusLabel.setStyleSheet("color: green;")
            
            self.ui.statusbar.showMessage(f"接收到光谱数据，最大光强: {int(max_intensity)}", 2000)
            print(f"[DEBUG] 数据处理完成，界面更新成功")
            
        except Exception as e:
            error_msg = f"数据处理错误: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.ui.statusbar.showMessage(error_msg, 3000)
    
    def on_status_changed(self, status):
        """处理状态变化"""
        self.ui.connectionStatusLabel.setText(f"状态: {status}")
        self.ui.statusbar.showMessage(status, 2000)
    
    def on_error_occurred(self, error):
        """处理错误"""
        self.ui.statusbar.showMessage(f"错误: {error}", 5000)
        QMessageBox.warning(self, "通信错误", error)
    
    def save_spectrum_data(self):
        """保存光谱数据"""
        if len(self.current_spectrum_data) == 0:
            QMessageBox.warning(self, "警告", "没有光谱数据可保存")
            return
        
        # 固定保存为DATA.CSV
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存光谱数据", "DATA.csv", 
            "CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if filename:
            try:
                # 准备像素位数据（1-3648）- 从1开始计数
                pixels = np.arange(1, 3649)
                
                # 准备波长数据
                if self.spectrum_widget.is_calibrated:
                    # 已标定：计算波长并保留两位小数
                    wavelengths = self.spectrum_widget.wavelengths
                    wavelength_column = [f"{wl:.2f}" for wl in wavelengths]
                else:
                    # 未标定：波长列填0
                    wavelength_column = ["0"] * 3648
                
                # 准备光强度数据（5位整数）
                intensity_column = [f"{int(intensity):05d}" for intensity in self.current_spectrum_data]
                
                # 根据系统首选编码选择CSV编码，优先兼容旧版 Windows/Excel
                preferred_encoding = locale.getpreferredencoding(False).lower()
                if sys.platform.startswith('win') and preferred_encoding in ("gbk", "cp936", "gb2312"):
                    csv_encoding = preferred_encoding  # 旧版 Windows/Excel 使用本地编码避免乱码
                else:
                    csv_encoding = "utf-8-sig"        # 默认UTF-8带BOM，兼容新版本Excel

                # 写入CSV文件
                with open(filename, 'w', newline='', encoding=csv_encoding) as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # 写入表头
                    writer.writerow(['像素位', '波长（nm）', '光强度灰值'])
                    
                    # 写入数据行
                    for i in range(3648):
                        writer.writerow([
                            pixels[i],                    # 像素位（从1开始）
                            wavelength_column[i],         # 波长（nm）或0
                            intensity_column[i]           # 光强度灰值（5位整数）
                        ])
                
                QMessageBox.information(self, "成功", f"光谱数据已保存到: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def load_spectrum_data(self):
        """加载光谱数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "加载光谱数据", "", 
            "CSV文件 (*.csv);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if filename:
            try:
                # 尝试不同的编码方式加载数据
                data = None
                for encoding in ['utf-8', 'gbk', 'latin1']:
                    try:
                        with open(filename, 'r', encoding=encoding) as f:
                            # 读取第一行检查是否有标题
                            first_line = f.readline().strip()
                            f.seek(0)
                            
                            # 判断是否有标题行
                            has_header = not first_line.replace(',', '').replace('.', '').replace('-', '').isdigit()
                            skip_rows = 1 if has_header else 0
                            
                            data = np.loadtxt(f, delimiter=',', skiprows=skip_rows)
                            break
                    except (UnicodeDecodeError, ValueError):
                        continue
                
                if data is None:
                    QMessageBox.critical(self, "错误", "无法读取文件，请检查文件编码和格式")
                    return
                
                # 检查数据格式
                if len(data.shape) == 1:
                    # 只有一列数据，假设是光强度
                    if len(data) == 3648:
                        spectrum_data = data
                    else:
                        QMessageBox.warning(self, "警告", f"数据点数不匹配，期望3648个点，实际{len(data)}个点")
                        return
                elif data.shape[1] >= 3 and data.shape[0] == 3648:
                    # 三列及以上通常是"像素,波长,光强"的保存格式，取最后一列作为光强
                    spectrum_data = data[:, -1]
                elif data.shape[1] == 2 and data.shape[0] == 3648:
                    # 两列格式默认取第二列为光强
                    spectrum_data = data[:, 1]
                elif data.shape[1] == 1 and data.shape[0] == 3648:
                    # 只有一列数据
                    spectrum_data = data[:, 0]
                else:
                    QMessageBox.warning(self, "警告", f"文件格式不正确，期望(3648,1+)，实际{data.shape}")
                    return
                
                # 更新光谱数据
                self.current_spectrum_data = spectrum_data
                self.spectrum_widget.update_spectrum(self.current_spectrum_data)
                
                # 显示数据信息
                data_info = f"数据点数: {len(spectrum_data)}\n强度范围: {spectrum_data.min():.1f} - {spectrum_data.max():.1f}"
                QMessageBox.information(self, "成功", f"光谱数据已从文件加载\n{data_info}")
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")
    
    def export_calibration(self):
        """导出标定结果"""
        if not self.spectrum_widget.is_calibrated:
            QMessageBox.warning(self, "警告", "尚未进行光谱标定")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出标定结果", "CALIBO.TXT", 
            "标定文件 (*.TXT);;所有文件 (*.*)"
        )
        
        if filename:
            try:
                # 获取标定参数
                k = self.spectrum_widget.calibration_k
                b = self.spectrum_widget.calibration_b
                r2 = self.spectrum_widget.calibration_r2
                
                # 写入CALIBO.TXT格式: k=0.900907,b=264.11,r2=1.0000
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"k={k:.6f},b={b:.2f},r2={r2:.4f}")
                
                QMessageBox.information(self, "成功", f"标定结果已导出到: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def import_calibration_file(self):
        """导入标定结果文件"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "导入标定结果", "", 
            "标定文件 (*.TXT);;JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # 判断文件格式
                if filename.lower().endswith('.txt') or ('k=' in content and 'b=' in content and 'r2=' in content):
                    # CALIBO.TXT格式: k=0.900907,b=264.11,r2=1.0000
                    try:
                        # 解析参数
                        params = {}
                        for param in content.split(','):
                            key, value = param.split('=')
                            params[key.strip()] = float(value.strip())
                        
                        k = params.get('k', 0)
                        b = params.get('b', 0)
                        r2 = params.get('r2', 0)
                        
                    except (ValueError, KeyError) as e:
                        QMessageBox.warning(self, "警告", f"CALIBO.TXT文件格式错误: {str(e)}")
                        return
                else:
                    # JSON格式（兼容旧版本）
                    import json
                    calibration_data = json.loads(content)
                    k = calibration_data.get('calibration_coefficient_k', 0)
                    b = calibration_data.get('calibration_intercept_b', 0)
                    r2 = calibration_data.get('calibration_r_squared', 0)
                    points = calibration_data.get('calibration_points', [])
                
                # 验证数据有效性
                if k == 0:
                    QMessageBox.warning(self, "警告", "标定文件中的参数无效")
                    return
                
                # 应用标定参数
                self.spectrum_widget.apply_calibration(k, b, r2)
                
                # 更新显示
                self.ui.calibrationResultLabel.setText(f"拟合系数 k: {k:.6f}")
                self.ui.calibrationInterceptLabel.setText(f"拟合截距 b: {b:.2f}")
                self.ui.calibrationR2Label.setText(f"相关系数 r²: {r2:.6f}")
                
                QMessageBox.information(self, "成功", 
                    f"标定结果已导入！\n"
                    f"拟合方程: λ = {k:.6f}x + {b:.2f}\n"
                    f"相关系数 r² = {r2:.6f}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
    
    def show_about(self):
        """显示关于信息"""
        about_text = """
FD-MGS-A 光谱分析系统

专业的光谱仪数据采集和分析软件

主要功能:
• 3648像素光谱数据采集
• 实时光谱图显示
• 光谱标定功能（支持6种标准峰）
• 积分时间设置（15种选项）
• 数据保存/加载和标定导出/导入
• 连续/单次采集模式
• 拖拽缩放和自动Y轴缩放

适用于: STM32光谱仪系统
通信协议: 串口通信
数据格式: 16进制 (00-FF)

技术支持: 上海复旦天欣科教仪器有限公司
版本日期: 2025年
        """
        
        QMessageBox.about(self, "关于 FD-MGS-A", about_text)
    
    def toggle_zoom_mode(self):
        """切换缩放模式"""
        try:
            # 获取按钮状态
            zoom_enabled = self.ui.zoomModeButton.isChecked()
            
            # 设置光谱图的缩放模式
            self.spectrum_widget.set_zoom_mode(zoom_enabled)
            
            # 如果启用缩放模式，暂时禁用标定点击功能（但不清除已有标定点）
            if zoom_enabled and self.spectrum_widget.calibration_mode:
                # 不退出标定模式，只是在缩放时禁用标定点击
                self.ui.statusbar.showMessage("缩放模式已启用 - 标定模式暂时禁用，用鼠标拖拽选择横坐标区间", 3000)
            elif zoom_enabled:
                self.ui.statusbar.showMessage("缩放模式已启用 - 用鼠标拖拽选择横坐标区间", 3000)
            else:
                # 退出缩放模式时，如果之前有标定模式，提示可以继续标定
                if self.spectrum_widget.calibration_mode:
                    self.ui.statusbar.showMessage("缩放模式已关闭 - 标定模式重新激活，可以继续点击添加标定点", 3000)
                else:
                    self.ui.statusbar.showMessage("缩放模式已关闭", 2000)
                
        except Exception as e:
            print(f"切换缩放模式时发生错误: {e}")
            self.ui.statusbar.showMessage(f"切换缩放模式失败: {e}", 3000)
    
    def exit_zoom_mode(self, message="缩放模式已关闭"):
        """统一关闭缩放模式并同步按钮状态"""
        if self.ui.zoomModeButton.isChecked():
            self.ui.zoomModeButton.setChecked(False)
        self.spectrum_widget.set_zoom_mode(False)
        if message:
            self.ui.statusbar.showMessage(message, 3000)
    
    def auto_scale_spectrum(self):
        """自动缩放光谱图"""
        try:
            self.auto_scale_enabled = not self.auto_scale_enabled
            if self.auto_scale_enabled:
                self.ui.autoScaleButton.setText("自动缩放(已开启)")
                self.spectrum_widget.auto_scale_y()
                self.ui.statusbar.showMessage("自动缩放已开启（连续采集时保持）", 2500)
            else:
                self.ui.autoScaleButton.setText("自动缩放")
                self.ui.statusbar.showMessage("自动缩放已关闭", 2000)
        except Exception as e:
            print(f"自动缩放时发生错误: {e}")
            self.ui.statusbar.showMessage(f"自动缩放失败: {e}", 3000)
    
    def reset_spectrum_zoom(self):
        """重置光谱图缩放"""
        try:
            self.spectrum_widget.reset_zoom()
            if self.auto_scale_enabled:
                self.auto_scale_enabled = False
                self.ui.autoScaleButton.setText("自动缩放")
            # 如果缩放模式按钮被选中，取消选中
            if self.ui.zoomModeButton.isChecked():
                self.exit_zoom_mode("缩放已重置 - 自动退出放大模式")
                
            # 根据标定模式状态显示合适的消息
            if self.spectrum_widget.calibration_mode:
                self.ui.statusbar.showMessage("缩放已重置 - 标定模式已激活，可以点击添加标定点", 3000)
            else:
                self.ui.statusbar.showMessage("缩放已重置", 2000)
        except Exception as e:
            print(f"重置缩放时发生错误: {e}")
            self.ui.statusbar.showMessage(f"重置缩放失败: {e}", 3000)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止采集
        self.stop_capture()
        
        # 断开串口
        if self.serial_worker.is_connected:
            self.disconnect_serial()
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    print("正在启动 FD-MGS-A 光谱分析系统...")
    print("功能特性:")
    print("[+] 3648像素光谱数据采集")
    print("[+] 实时光谱图显示和缩放功能")
    print("[+] 光谱标定功能（支持6种标准峰）")
    print("[+] 积分时间设置（15种选项）")
    print("[+] 数据保存/加载和标定导出/导入")
    print("[+] 连续/单次采集模式")
    print("[+] 拖拽缩放和自动Y轴缩放")
    print("=" * 50)
    
    try:
        window = MainWindow()
        window.show()
        
        # 显示欢迎信息
        from PyQt5.QtCore import QTimer
        def show_welcome():
            if hasattr(window, 'ui') and hasattr(window.ui, 'statusbar'):
                window.ui.statusbar.showMessage("FD-MGS-A 已就绪 - 请连接串口或点击'显示演示'查看示例", 5000)
        
        QTimer.singleShot(1000, show_welcome)
        
        sys.exit(app.exec_())

    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 
