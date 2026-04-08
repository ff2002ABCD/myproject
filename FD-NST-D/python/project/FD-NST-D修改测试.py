import sys
import win32api
import win32con
import random
import time
import os
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
                            QLineEdit, QFileDialog, QSpacerItem,QTabWidget,QRadioButton, QStackedLayout,
                            QTableWidget, QTableWidgetItem,  QSizePolicy,QButtonGroup,QMessageBox,
                            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QGroupBox, QLabel, QDial, QComboBox, QFrame, QPushButton, QTextEdit,QDialog,
                            QGridLayout,QGraphicsTextItem)
from PyQt5.QtCore import Qt, QTimer, QRectF,QSize,QPoint, QPointF,pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF,QFont,QPixmap, QPalette
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis,QScatterSeries

class CalibrationChartWindow(QDialog):
    sensitivity_calculated = pyqtSignal(float)  # 新增信号
    def __init__(self, parent=None):
        super().__init__(parent)
        self.equation_annotation = None  
        self.setWindowTitle("输出电压——传感器受力关系图")
        self.resize(700, 500)
        # self.setFixedSize(700, 500)
        # 设置为普通对话框（不强制置顶）
        self.setWindowFlags(Qt.Dialog)  # 仅保留对话框基本特性
        # 设置窗口位置（相对于父窗口的固定偏移）
        if parent:
            self.move(parent.pos().x() + 100, parent.pos().y() + 100)
        else:
            # 如果没有父窗口，居中显示
            screen_geometry = QApplication.desktop().availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
        
        self.setWindowFlags(
            self.windowFlags() & 
            ~Qt.WindowContextHelpButtonHint &  
            ~Qt.WindowCloseButtonHint &
            ~Qt.WindowStaysOnTopHint  # 显式禁用置顶
        )
        
        # 禁用问号按钮和关闭按钮
        self.setWindowFlags(
            self.windowFlags() & 
            ~Qt.WindowContextHelpButtonHint &  
            ~Qt.WindowCloseButtonHint          
        )
        
        # 存储校准数据
        self.calibration_data = []
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 1. 创建图表部分
        self.chart = QChart()
        self.chart.setTitle("输出电压——传感器受力关系图")
        self.chart.setBackgroundBrush(QBrush(Qt.white))
        self.chart.setAnimationOptions(QChart.AllAnimations)
        
        # 先创建折线系列（会先添加到底层）
        self.series = QLineSeries()
        self.series.setName("校准曲线")
        self.series.setColor(QColor(0, 0, 255, 255))
        self.chart.addSeries(self.series)
        
        # 后创建散点系列（会添加到上层）
        self.scatter_series = QScatterSeries()
        self.scatter_series.setName("校准数据点")
        self.scatter_series.setMarkerSize(10.0)
        self.scatter_series.setColor(QColor(255, 0, 0, 255))
        self.scatter_series.setBorderColor(QColor(0, 0, 0, 255))
        self.chart.addSeries(self.scatter_series)
        
        # 设置坐标轴
        self.axisX = QValueAxis()
        self.axisX.setTitleText("传感器受力/N")
        self.axisX.setRange(0, 5)  # 初始范围0-5N
        self.axisX.setLabelFormat("%.5f")
        self.axisX.setTitleBrush(QBrush(Qt.black))
        font = self.axisX.titleFont()
        font.setPointSize(8)  # 可以适当调整字体大小
        self.axisX.setTitleFont(font)
        self.chart.addAxis(self.axisX, Qt.AlignBottom)
        
        self.axisY = QValueAxis()
        self.axisY.setTitleText("输出电压/mV")
        self.axisY.setRange(0, 500)  # 初始范围0-500mV
        self.axisY.setLabelFormat("%.0f")
        # 增加标题边距
        self.axisY.setTitleBrush(QBrush(Qt.black))
        font = self.axisY.titleFont()
        font.setPointSize(8)  # 可以适当调整字体大小
        self.axisY.setTitleFont(font)
        self.chart.addAxis(self.axisY, Qt.AlignLeft)
        
        # 将系列绑定到坐标轴
        for series in [self.series, self.scatter_series]:
            series.attachAxis(self.axisX)
            series.attachAxis(self.axisY)
        
        # 创建图表视图
        chart_view = QChartView(self.chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        main_layout.addWidget(chart_view)
        
        # 2. 添加四行文本控件
        self.create_text_controls(main_layout)
        
        self.setLayout(main_layout)

    def update_voltage_data(self, mass_g, voltage_mV):
        """更新电压数据 - 只添加到散点系列"""
        try:
            gravity = float(self.gravity_edit.text())
        except ValueError:
            gravity = 9.8
            self.gravity_edit.setText("9.8")
        
        force_N = (mass_g / 1000) * gravity
        
        # 更新对应砝码位置的电压显示
        mass_index = int(mass_g / 0.5) - 1
        if 0 <= mass_index < len(self.voltage_labels):
            self.voltage_labels[mass_index].setText(f"{voltage_mV:.1f}")
        
        # 存储数据点（避免重复）
        for i, (f, v) in enumerate(self.calibration_data):
            if abs(f - force_N) < 1e-6:
                self.calibration_data[i] = (force_N, voltage_mV)
                break
        else:
            self.calibration_data.append((force_N, voltage_mV))
        
        # 按力的大小排序
        self.calibration_data.sort(key=lambda x: x[0])
        
        # 更新散点图（自动忽略0 mV的点）
        self.update_scatter_chart()

    def update_scatter_chart(self):
        """只更新散点图并自动调整坐标轴"""
        self.scatter_series.clear()
        
        visible_points = []
        for force_N, voltage_mV in self.calibration_data:
            if voltage_mV != 0:
                self.scatter_series.append(force_N, voltage_mV)
                visible_points.append((force_N, voltage_mV))
        
        if visible_points:
            # 计算X轴和Y轴的范围
            x_values = [p[0] for p in visible_points]
            y_values = [p[1] for p in visible_points]
            
            min_x, max_x = min(x_values), max(x_values)
            min_y, max_y = min(y_values), max(y_values)
            
            # 添加10%的边距
            x_range = max_x - min_x
            y_range = max_y - min_y
            
            # 设置坐标轴范围，确保最小值不为负
            self.axisX.setRange(max(0, min_x - 0.1*x_range), max_x + 0.1*x_range)
            self.axisY.setRange(max(0, min_y - 0.1*y_range), max_y + 0.1*y_range)

    def update_chart(self):
        """根据校准数据更新折线图"""
        self.series.clear()
        
        # 添加数据点到图表
        for force_N, voltage_mV in self.calibration_data:
            if voltage_mV != 0:  # 只添加非零电压点
                self.series.append(force_N, voltage_mV)
        
        # 自动调整坐标轴范围
        self.adjust_axes()
        
        # # 计算灵敏度和相关系数（至少有2个点时才计算）
        # if len(self.calibration_data) >= 2:
        #     x = np.array([point[0] for point in self.calibration_data])
        #     y = np.array([point[1] for point in self.calibration_data])
            
        #     # 线性拟合：y = slope * x + intercept
        #     slope, intercept = np.polyfit(x, y, 1)
        #     self.sensitivity_label.setText(f"{slope:.2f}")
            
        #     # 计算相关系数
        #     correlation = np.corrcoef(x, y)[0, 1]
        #     self.correlation_label.setText(f"{correlation:.4f}")

    def create_text_controls(self, layout):
        """创建下方的四行文本控件"""
        
        # 第一行：物体质量
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("物体质量(g)"))
        self.mass_labels = []
        for mass in ["0.5", "1", "1.5", "2", "2.5", "3", "3.5"]:
            label = QLabel(f"{mass:}")  # 显示1位小数
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border: 1px solid black; padding: 5px;")
            self.mass_labels.append(label)
            row1.addWidget(label)
        layout.addLayout(row1)
        
        # 第二行：输出电压（改为只读标签）
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("输出电压(mV)"))
        self.voltage_labels = []  # 改为QLabel列表
        for _ in range(7):
            label = QLabel("0")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                border: 1px solid black; 
                padding: 5px;
                background-color: #f0f0f0;
            """)
            self.voltage_labels.append(label)
            row2.addWidget(label)
        layout.addLayout(row2)
        
        # 第三行：灵敏度和重力加速度
        row3 = QHBoxLayout()
        
        # 左侧：灵敏度
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("灵敏度(mV/N):"))
        self.sensitivity_label = QLabel("0.00")
        self.sensitivity_label.setStyleSheet("border: 1px solid black; padding: 5px; min-width: 80px;")
        sensitivity_layout.addWidget(self.sensitivity_label)
        row3.addLayout(sensitivity_layout)
        
        # 右侧：重力加速度
        gravity_layout = QHBoxLayout()
        gravity_layout.addWidget(QLabel("本地区重力加速度(m/s²):"))
        self.gravity_edit = QLineEdit("9.8")
        self.gravity_edit.setStyleSheet("border: 1px solid black; padding: 5px; min-width: 80px;")
        self.gravity_edit.textChanged.connect(self.on_gravity_changed)  # 绑定文本变化事件
        gravity_layout.addWidget(self.gravity_edit)
        row3.addLayout(gravity_layout)
        
        layout.addLayout(row3)
        
        # 第四行：相关系数和计算按钮
        row4 = QHBoxLayout()
        
        # 左侧：相关系数
        correlation_layout = QHBoxLayout()
        correlation_layout.addWidget(QLabel("相关系数:"))
        self.correlation_label = QLabel("0.00")
        self.correlation_label.setStyleSheet("border: 1px solid black; padding: 5px; min-width: 80px;")
        correlation_layout.addWidget(self.correlation_label)
        correlation_layout.addStretch()  # 添加弹性空间使内容靠左
        row4.addLayout(correlation_layout)
        
        # # 右侧：计算按钮
        self.calculate_btn = QPushButton("计算")
        self.calculate_btn.setFixedSize(100, 50)
        self.calculate_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                min-width: 80px;
                min-height: 30px;
                padding: 2px;
                margin: 0px;
            }
        """)
        self.calculate_btn.clicked.connect(self.on_calculate)
        row4.addWidget(self.calculate_btn)
        
        layout.addLayout(row4)
    
    def on_gravity_changed(self):
        """重力加速度修改时清空所有数据"""
        # 清空数据存储
        self.calibration_data.clear()
        
        # 清空折线图
        self.series.clear()
        
        # 清空电压显示框
        for label in self.voltage_labels:
            label.setText("0")
        
        # 重置灵敏度和相关系数
        self.sensitivity_label.setText("0.00")
        self.correlation_label.setText("0.00")
        
        # 重置坐标轴范围
        self.axisX.setRange(0, 10)
        self.axisY.setRange(0, 1000)

    def on_calculate(self):
        """计算按钮点击事件：计算灵敏度和相关系数，并显示拟合公式"""
        filtered_data = [(f, v) for f, v in self.calibration_data if v != 0]
        if len(filtered_data) < 2:
            QMessageBox.warning(self, "错误", "需要至少2个有效数据点！")
            return

        try:
            g = float(self.gravity_edit.text())
        except ValueError:
            g = 9.8
            self.gravity_edit.setText("9.8")

        # 准备数据
        forces = []
        voltages = []
        for i in range(7):
            mass_g = 0.5 * (i + 1)
            force_N = (mass_g / 1000) * g
            voltage_text = self.voltage_labels[i].text()
            try:
                voltage_mV = float(voltage_text)
            except ValueError:
                QMessageBox.warning(self, "错误", f"第{i+1}个电压值无效！")
                return
            if voltage_mV != 0:
                forces.append(force_N)
                voltages.append(voltage_mV)

        # 线性拟合
        x = np.array(forces)
        y = np.array(voltages)
        slope, intercept = np.polyfit(x, y, 1)
        correlation = np.corrcoef(x, y)[0, 1]

        # 在计算完成后发射信号
        self.sensitivity_calculated.emit(slope)  # 发射计算出的灵敏度值

        # 生成公式文本
        if(intercept > 0):
            equation_text = f"y = {slope:.2f} x + {intercept:.2f} (R²={correlation**2:.4f})"
        else:
            equation_text = f"y = {slope:.2f} x - {-intercept:.2f} (R²={correlation**2:.4f})"

        # 更新显示
        self.sensitivity_label.setText(f"{slope:.2f}")
        self.correlation_label.setText(f"{correlation:.4f}")
        
        # 清除旧公式（如果有）
        if hasattr(self, 'equation_item'):
            self.chart.scene().removeItem(self.equation_item)
        
        # 添加新公式
        self.equation_item = QGraphicsTextItem(equation_text)
        self.equation_item.setPos(130, 130)  # 调整位置
        font = self.equation_item.font()
        font.setPointSize(12)
        font.setBold(True)
        self.equation_item.setFont(font)
        self.equation_item.setDefaultTextColor(QColor(0, 0, 0))
        self.chart.scene().addItem(self.equation_item)

        # 更新曲线
        self.series.clear()
        for force, voltage in zip(forces, voltages):
            self.series.append(force, voltage)
        self.adjust_axes()

        
    
    def adjust_axes(self):
        """调整坐标轴范围"""
        if self.series.count() > 0:
            points = self.series.pointsVector()
            x_values = [point.x() for point in points]
            y_values = [point.y() for point in points]
            
            min_x, max_x = min(x_values), max(x_values)
            min_y, max_y = min(y_values), max(y_values)
            
            # 添加10%的边距
            x_range = max_x - min_x
            y_range = max_y - min_y
            self.axisX.setRange(min_x - 0.1*x_range, max_x + 0.1*x_range)
            self.axisY.setRange(min_y - 0.1*y_range, max_y + 0.1*y_range)
        
    def add_data_point(self, force_N, voltage_mV):
        """添加一个数据点到图表"""
        self.series.append(force_N, voltage_mV)
        self.adjust_axes()
        
    def add_data_points(self, points):
        """批量添加数据点"""
        for force_N, voltage_mV in points:
            self.series.append(force_N, voltage_mV)
        self.adjust_axes()

print("当前工作目录:", os.getcwd())
print("脚本所在目录:", os.path.dirname(os.path.abspath(__file__)))

class ControlWindow(QDialog):
    def __init__(self, parent=None, show_measure_control=False):
        super().__init__(parent)
        
        self.setWindowTitle("实验控制面板")
        self.setFixedSize(750, 400)
        self.parent = parent
        self.show_measure_control = show_measure_control
        self.setWindowFlags(Qt.Window)  # 关键修改：使用普通窗口标志
        self.calibration_chart = CalibrationChartWindow(self)  # 创建折线图窗口
        self.diagram = SurfaceTensionDiagram(show_water=show_measure_control)
        self.diagram.show_water = False  # 这行应该已经由上面的参数设置
         # 连接灵敏度计算信号
        self.calibration_chart.sensitivity_calculated.connect(self.update_sensitivity_in_enlarged_view)
        
        # 默认显示折线图窗口（传感器定标模式）
        if not show_measure_control:
            self.calibration_chart.show()  # 显示折线图窗口
        
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint & ~Qt.WindowCloseButtonHint)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowStaysOnTopHint  # 禁止控制面板置顶
        )
        # 主布局
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # 1. 左侧 - 步骤选择区域
        self.init_step_selection()
        main_layout.addWidget(self.step_selection_group)
        
        # 2. 中间 - 控制区域容器（将包含砝码控制或液体选择）
        self.control_area_container = QWidget()
        self.control_area_layout = QVBoxLayout()
        self.control_area_container.setLayout(self.control_area_layout)
        
        # 初始化两种控制面板但只显示一个
        self.init_weight_control()
        self.init_liquid_control()
        
        if not show_measure_control:
            self.weight_control_group.show()
            self.liquid_control_group.hide()
        else:
            self.weight_control_group.hide()
            self.liquid_control_group.show()
        
        main_layout.addWidget(self.control_area_container)
    
        # 3. 右侧 - 动画示意图
        self.diagram_group = QGroupBox("实验示意图")
        self.init_diagram()
        main_layout.addWidget(self.diagram_group)

        if not show_measure_control:
            self.parent.using_ring = False
            self.parent.weight_count = 0
            self.diagram.set_weight_count(0, is_ring=False)
        else:
            self.parent.using_ring = True
            self.parent.weight_count = 3
            self.diagram.set_weight_count(3, is_ring=True)

    def update_sensitivity_in_enlarged_view(self, sensitivity):
        self.parent.last_sensitivity = sensitivity
        if hasattr(self.parent.data_display, 'enlarged_window') and self.parent.data_display.enlarged_window:
            self.parent.data_display.enlarged_window.set_sensitivity(sensitivity)
            self.parent.data_display.enlarged_window.update()  # 强制更新界面

    def init_step_selection(self):
        """初始化步骤选择区域"""
        self.step_selection_group = QGroupBox("实验步骤选择")
        layout = QVBoxLayout()
        
        self.step1_radio = QRadioButton("传感器定标")
        self.step1_radio.setChecked(not self.show_measure_control)
        self.step1_radio.toggled.connect(self.on_step_changed)
        self.step1_radio.setStyleSheet("font-size: 16px;")  # 添加这行设置字体大小

        self.step2_radio = QRadioButton("表面张力测量")
        self.step2_radio.setChecked(self.show_measure_control)
        self.step2_radio.toggled.connect(self.on_step_changed)
        self.step2_radio.setStyleSheet("font-size: 16px;")  # 添加这行设置字体大小
        
        layout.addWidget(self.step1_radio)
        layout.addWidget(self.step2_radio)
        layout.addStretch()
        
        self.step_selection_group.setLayout(layout)
    
    def set_liquid_buttons_enabled(self, enabled):
        """设置液体选择按钮的启用状态"""
        self.water_btn.setEnabled(enabled)
        self.ethanol_btn.setEnabled(enabled)
        self.glycerol_btn.setEnabled(enabled)

    def on_step_changed(self):
        """步骤选择变化时的处理"""
        if self.step1_radio.isChecked():  # 传感器定标模式
            self.show_measure_control = False
            self.diagram.show_water = False
            self.weight_control_group.show()
            self.liquid_control_group.hide()
            self.diagram.set_weight_count(0, is_ring=False)
            self.parent.using_ring = False
            self.parent.weight_count = 0
            
            # 重置圆环按钮状态
            self.take_off_ring_btn.hide()
            self.put_ring_btn.show()
            
            # 清零砝码个数显示
            self.weight_count_label.setText("砝码个数: 0")

            # 显示折线图窗口
            if self.calibration_chart:
                self.calibration_chart.show()
            
            # 隐藏放大窗口
            if hasattr(self.parent.data_display, 'enlarged_window') and self.parent.data_display.enlarged_window:
                self.parent.data_display.enlarged_window.hide()
            
            # # 隐藏测量模式的数据显示
            # self.parent.measurement_container.hide()
            # self.parent.data_display.hide()
            
        else:  # 表面张力测量模式
            self.show_measure_control = True
            self.diagram.show_water = True
            self.weight_control_group.hide()
            self.liquid_control_group.show()
            self.diagram.set_weight_count(3, is_ring=True)
            self.parent.using_ring = True
            self.parent.weight_count = 3
            
            # 隐藏折线图窗口
            if self.calibration_chart:
                self.calibration_chart.hide()
            
            # 显示放大窗口
            if hasattr(self.parent.data_display, 'enlarged_window'):
                if not self.parent.data_display.enlarged_window:
                    self.parent.data_display.show_enlarged_view()
                else:
                    self.parent.data_display.enlarged_window.show()
                    self.parent.data_display.enlarged_window.raise_()

    def init_weight_control(self):
        """初始化砝码/圆环控制区域"""
        self.weight_control_group = QGroupBox("悬挂物体控制")
        layout = QVBoxLayout()
        
        BUTTON_STYLE = """
            QPushButton {
                font-size: 16px;
                min-width: 80px;
                min-height: 30px;
                padding: 2px;
                margin: 0px;
            }
        """ 

        self.put_ring_btn = QPushButton("悬挂圆环")
        self.put_ring_btn.clicked.connect(self.on_put_ring)
        self.put_ring_btn.setStyleSheet(BUTTON_STYLE)
        
        self.take_off_ring_btn = QPushButton("取下圆环")
        self.take_off_ring_btn.clicked.connect(self.on_take_off_ring)
        self.take_off_ring_btn.setStyleSheet(BUTTON_STYLE)
        self.take_off_ring_btn.hide()
        
        self.add_weight_btn = QPushButton("增加砝码")
        self.add_weight_btn.clicked.connect(self.on_add_weight)
        self.add_weight_btn.setStyleSheet(BUTTON_STYLE)
        
        self.remove_weight_btn = QPushButton("减少砝码")
        self.remove_weight_btn.clicked.connect(self.on_remove_weight)
        self.remove_weight_btn.setStyleSheet(BUTTON_STYLE)

        self.record_data_btn = QPushButton("记录数据")
        self.record_data_btn.clicked.connect(self.on_record_data)
        self.record_data_btn.setStyleSheet(BUTTON_STYLE)

        
        self.weight_count_label = QLabel("砝码个数: 0")
        self.weight_count_label.setStyleSheet("font-size: 16px;")
        self.weight_hint_label = QLabel("每个砝码重0.5g")
        self.weight_hint_label.setStyleSheet("font-size: 16px;")
        
        layout.addWidget(self.put_ring_btn)
        layout.addWidget(self.take_off_ring_btn)
        layout.addWidget(self.add_weight_btn)
        layout.addWidget(self.remove_weight_btn)
        layout.addWidget(self.record_data_btn)
        layout.addWidget(self.weight_count_label)
        layout.addWidget(self.weight_hint_label)
        
        self.weight_control_group.setLayout(layout)
        self.control_area_layout.addWidget(self.weight_control_group)

    def init_liquid_control(self):
        """初始化液体选择区域"""
        self.liquid_control_group = QGroupBox("测量液体选择")
        layout = QVBoxLayout()
        
        button_style = """
            QPushButton {
                font-size: 16px;
                min-width: 80px;
                min-height: 30px;
                padding: 2px;
                margin: 0px;
            }
        """
        
        self.water_btn = QPushButton("纯水")
        self.water_btn.setCheckable(True)
        self.water_btn.setChecked(True)
        self.water_btn.setStyleSheet(button_style)
        self.water_btn.clicked.connect(lambda: self.on_liquid_selected("water"))
        
        self.ethanol_btn = QPushButton("乙醇")
        self.ethanol_btn.setCheckable(True)
        self.ethanol_btn.setStyleSheet(button_style)
        self.ethanol_btn.clicked.connect(lambda: self.on_liquid_selected("ethanol"))
        
        self.glycerol_btn = QPushButton("甘油")
        self.glycerol_btn.setCheckable(True)
        self.glycerol_btn.setStyleSheet(button_style)
        self.glycerol_btn.clicked.connect(lambda: self.on_liquid_selected("glycerol"))
        
        layout.addWidget(self.water_btn)
        layout.addWidget(self.ethanol_btn)
        layout.addWidget(self.glycerol_btn)
        
        self.liquid_btn_group = QButtonGroup(self)
        self.liquid_btn_group.addButton(self.water_btn)
        self.liquid_btn_group.addButton(self.ethanol_btn)
        self.liquid_btn_group.addButton(self.glycerol_btn)
        self.liquid_btn_group.setExclusive(True)
        
        self.liquid_control_group.setLayout(layout)
        self.control_area_layout.addWidget(self.liquid_control_group)

    def on_put_ring(self):
        """挂上圆环"""
        if self.parent:
            self.parent.using_ring = True
            self.take_off_ring_btn.show()
            self.put_ring_btn.hide()
            # self.weight_status_label.setText("悬挂物体状态: 已挂上圆环")
            # 直接更新示意图
            self.diagram.set_weight_count(3, is_ring=True)
            self.parent.weight_count = 3
            # # 隐藏砝码相关控件
            # self.add_weight_btn.hide()
            # self.remove_weight_btn.hide()
            # self.weight_count_label.hide()
            # self.weight_hint_label.hide()
            
            # 更新拉力显示
            if self.parent.calibrating_sensor:
                self.parent.update_force_display()
            elif self.parent.measuring_tension:
                self.parent.update_tension_display()

    def on_take_off_ring(self):
        """放下圆环"""
        if self.parent:
            self.parent.using_ring = False
            self.take_off_ring_btn.hide()
            # self.weight_status_label.setText("悬挂物体状态: 未挂上圆环")
            self.weight_count_label.setText(f"砝码个数: 0")
            self.parent.weight_count = 0
            # 直接更新示意图
            self.diagram.set_weight_count(0, is_ring=False)
            
            # 恢复显示砝码相关控件
            self.put_ring_btn.show()
            self.add_weight_btn.show()
            self.remove_weight_btn.show()
            self.weight_count_label.show()
            self.weight_hint_label.show()

            # 更新拉力显示
            if self.parent.calibrating_sensor:
                self.parent.update_force_display()
            elif self.parent.measuring_tension:
                self.parent.update_tension_display()

    def on_record_data(self):
        """记录数据到折线图窗口"""
        if not self.show_measure_control:  # 仅在传感器定标模式下处理
            # 获取当前砝码个数（0~6对应0.5g~3.5g）
            weight_count = self.parent.weight_count-3
            if weight_count < 1 or weight_count > 7:
                QMessageBox.warning(self, "错误", "砝码个数必须在1-7之间！")
                return

            # 从主窗口的 force_display 中解析当前拉力值（单位：mV）
            force_text = self.parent.force_display.toPlainText()
            try:
                voltage_mV = float(force_text.split("：")[1].replace("mV", "").strip())
            except (IndexError, ValueError):
                QMessageBox.warning(self, "错误", "无法解析当前拉力值！")
                return

            # 计算当前砝码质量（g）
            mass_g = weight_count * 0.5  # 1个砝码=0.5g, 2个=1.0g, ..., 7个=3.5g

            # 调用折线图窗口更新数据
            self.calibration_chart.update_voltage_data(mass_g, voltage_mV)
        

    def on_add_weight(self):
        """增加砝码"""
        if self.parent:
            if self.parent.using_ring == True:
                if self.parent.weight_count < 10:  # 限制最大砝码数量
                    self.parent.weight_count += 1
                    self.weight_count_label.setText(f"砝码个数: {self.parent.weight_count-3}")
                    # 直接更新示意图的砝码数量
                    self.diagram.set_weight_count(self.parent.weight_count, is_ring=True)
                    
                    # 更新拉力显示
                    if self.parent.calibrating_sensor:
                        self.parent.update_force_display()
                    elif self.parent.measuring_tension:
                        self.parent.update_tension_display()

    def on_remove_weight(self):
        """减少砝码"""
        if self.parent:
            if self.parent.using_ring == True:
                if self.parent.weight_count > 3:  # 不能小于0
                    self.parent.weight_count -= 1
                    self.weight_count_label.setText(f"砝码个数: {self.parent.weight_count-3}")
                    # 直接更新示意图的砝码数量
                    self.diagram.set_weight_count(self.parent.weight_count, is_ring=True)
                    
                    # 更新拉力显示
                    if self.parent.calibrating_sensor:
                        self.parent.update_force_display()
                    elif self.parent.measuring_tension:
                        self.parent.update_tension_display()

    
    def on_liquid_selected(self, liquid_type):
        """液体选择按钮点击事件"""
        if self.parent:
            self.parent.current_liquid = liquid_type
            self.parent.excel_data = self.parent.load_excel_data()  # 重新加载对应液体的数据
            
            # 如果当前在测量模式，更新拉力显示
            if self.parent.measuring_tension:
                self.parent.update_tension_display()


    def init_diagram(self):
        """初始化动画示意图区域"""
        layout = QVBoxLayout()
        
        # 创建示意图控件
        self.diagram = SurfaceTensionDiagram()
        self.diagram.setMinimumSize(300, 300)
        
        # 添加到布局
        layout.addWidget(self.diagram)
        self.diagram_group.setLayout(layout)
        
        # 调试验证
        print(f"Diagram parent: {self.diagram.parent()}")  # 应显示diagram_group
        print(f"Diagram visible: {self.diagram.isVisible()}")  # 应为True

    # def mousePressEvent(self, event):
    #     """鼠标点击事件 - 将控制面板置于最上层"""
    #     super().mousePressEvent(event)

class ArrowWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.direction = 1  # 1=停止(左), 0=上升(上), 2=下降(下)
            self.setFixedSize(20, 20)  # 固定箭头区域大小
            
        def set_direction(self, direction):
            self.direction = direction
            self.update()
            
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 设置箭头颜色
            painter.setBrush(QBrush(QColor(0, 120, 215)))
            painter.setPen(QPen(Qt.black, 1))
            
            # 根据方向绘制不同箭头
            if self.direction == 0:  # 上升(上)
                points = [
                    QPointF(30, 10),
                    QPointF(50, 40),
                    QPointF(40, 40),
                    QPointF(40, 50),
                    QPointF(20, 50),
                    QPointF(20, 40),
                    QPointF(10, 40)
                ]
            elif self.direction == 2:  # 下降(下)
                points = [
                    QPointF(30, 50),
                    QPointF(50, 20),
                    QPointF(40, 20),
                    QPointF(40, 10),
                    QPointF(20, 10),
                    QPointF(20, 20),
                    QPointF(10, 20)
                ]
            else:  # 停止(左)
                points = [
                    QPointF(10, 30),
                    QPointF(40, 50),
                    QPointF(40, 40),
                    QPointF(50, 40),
                    QPointF(50, 20),
                    QPointF(40, 20),
                    QPointF(40, 10)
                ]
                
            painter.drawPolygon(QPolygonF(points))

class DataPointDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_points = []  # 确保在这里初始化data_points
        self.parent_window = parent  # 保存父窗口引用
        # self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cursor_pos = None
        self.setMouseTracking(True)  # 启用鼠标跟踪
        self.show_tooltip = True  # 始终显示工具提示
        
        # 添加放大按钮
        self.enlarge_btn = QPushButton("放大", self)
        self.enlarge_btn.clicked.connect(self.show_enlarged_view)
        self.enlarge_btn.setFixedSize(40, 25)
        self.enlarge_btn.move(180, 10)  # 放置在左上角
        self.enlarge_btn.hide()  # 初始隐藏
        
        # 放大窗口实例
        self.enlarged_window = None

        # View control variables
        self.x_min = 0      # Current visible x-axis minimum
        self.x_max = 520    # Current visible x-axis maximum (26 seconds)
        self.y_min = -50    # Current visible y-axis minimum
        self.y_max = 200    # Current visible y-axis maximum
        self.selection_rect = None
        self.selection_start = None
        self.last_pan_pos = None  # For right-click panning
        self.show_tooltip = True  # Always show tooltip on hover
        
         # 创建放大窗口但隐藏
        self.enlarged_window = EnlargedDataDisplay(self)
        self.enlarged_window.hide()  # 初始时隐藏
    
    def show_enlarged_view(self):
        """显示放大窗口"""
        if not hasattr(self, 'enlarged_window') or not self.enlarged_window:
            self.enlarged_window = EnlargedDataDisplay(self)
        
        # 确保数据点和视图范围同步
        self.enlarged_window.update_data(self.data_points)
        # self.enlarged_window.x_min = self.x_min
        # self.enlarged_window.x_max = self.x_max
        # self.enlarged_window.y_min = self.y_min
        # self.enlarged_window.y_max = self.y_max
        
        # 设置灵敏度值（从主窗口获取）
        if hasattr(self.parent(), 'last_sensitivity'):
            self.enlarged_window.set_sensitivity(self.parent().last_sensitivity)
        
        self.enlarged_window.show()
        self.enlarged_window.raise_()
        self.enlarged_window.activateWindow()
        self.enlarged_window.update()  # 强制重绘
    
    def set_data_points(self, points):
        """设置数据点"""
        self.data_points = points
        # self.export_btn.show()  # 显示导出按钮
        # self.enlarge_btn.show()
        self.reset_view()
        self.update()
        
        # 如果有放大窗口，更新它的数据和视图范围
        if hasattr(self, 'enlarged_window') and self.enlarged_window:
            self.enlarged_window.update_data(self.data_points)
        #     # 同步视图范围
        #     self.enlarged_window.x_min = self.x_min
        #     self.enlarged_window.x_max = self.x_max
        #     self.enlarged_window.y_min = self.y_min
        #     self.enlarged_window.y_max = self.y_max
        #     self.enlarged_window.update()

    def export_data(self):
        """导出数据到Excel文件"""
        if not self.data_points:
            return
            
        # 弹出文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "保存数据", 
            "", 
            "Excel文件 (*.xlsx);;所有文件 (*)"
        )
        
        if not file_path:
            return  # 用户取消
            
        # 确保文件扩展名正确
        if not file_path.endswith('.xlsx'):
            file_path += '.xlsx'
            
        try:
            # 方法1：直接修改列名顺序（推荐）
            # df = pd.DataFrame(self.data_points, columns=['拉力(mV)', '时间(S)'])
            
            # 方法2：调整数据顺序（可选）
            data = [(time, force) for force, time in self.data_points]
            df = pd.DataFrame(data, columns=['时间(S)', '拉力(mV)'])
            
            # 保存为Excel
            df.to_excel(file_path, index=False)
            
            # 提示用户保存成功
            QMessageBox.information(self, "导出成功", f"数据已成功导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出数据时出错:\n{str(e)}")
    
    def set_data_points(self, points):
        """设置数据点"""
        self.data_points = points
        # self.export_btn.show()  # 显示导出按钮
        # self.enlarge_btn.show()
        self.reset_view()
        self.update()
        
        # 如果有放大窗口，更新它的数据
        if hasattr(self, 'enlarged_window') and self.enlarged_window:
            self.enlarged_window.update_data(self.data_points)

    def get_current_group_data(self):
        """获取当前组数据"""
        # 方法1：直接通过父窗口引用访问
        if hasattr(self.parent_window, 'current_group_data'):
            return self.parent_window.current_group_data
        
        # 方法2：向上遍历父对象链，找到主窗口
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'current_group_data'):
                return parent.current_group_data
            parent = parent.parent()
        return None  # 未找到时返回None
       
    def reset_view(self):
        """Reset view to default ranges"""
        interval = 0.2  # 默认值
        
        # 尝试从当前组数据获取interval
        main_window = None
        parent = self.parent()
        
        # 向上查找父对象链，直到找到主窗口
        while parent is not None:
            if isinstance(parent, SurfaceTensionApp):
                main_window = parent
                break
            parent = parent.parent()
        
        interval= main_window.interval
        print('main_window.interval: ', main_window.interval)
        # 如果找到了主窗口并且有当前组数据
        if main_window is not None and hasattr(main_window, 'current_group_data'):
            if main_window.querying_data:
                current_group_data = main_window.current_group_data
                print(f'current_group_data: ', current_group_data)
                if current_group_data and len(current_group_data) >= 3:
                    interval = current_group_data[2]  # 使用组数据中保存的原始间隔值
        
        self.x_min = 0
        self.x_max = 26 * (interval / 0.1)  # 动态计算x轴范围
        self.y_min = -50
        self.y_max = 200

    # def mouseMoveEvent(self, event):
    #     """鼠标移动事件"""
    #     self.cursor_pos = event.pos()
        
    #     # 同步到放大窗口
    #     if hasattr(self, 'enlarged_window') and self.enlarged_window:
    #         # 转换坐标到放大窗口
    #         chart_rect = self.rect()
    #         enlarged_rect = self.enlarged_window.chart_widget.rect()
            
    #         # 计算相对位置
    #         rel_x = (self.cursor_pos.x() - chart_rect.left()) / chart_rect.width()
    #         rel_y = (self.cursor_pos.y() - chart_rect.top()) / chart_rect.height()
            
    #         # 设置放大窗口的光标位置
    #         self.enlarged_window.cursor_pos = QPoint(
    #             int(enlarged_rect.left() + rel_x * enlarged_rect.width()),
    #             int(enlarged_rect.top() + rel_y * enlarged_rect.height())
    #         )
    #         self.enlarged_window.update()
        
    #     self.update()

    # def pan_view(self, dx, dy):
    #     """Pan the view by the specified pixel amounts"""
    #     width = self.width()
    #     height = self.height()
        
    #     axis_start_x = 10
    #     axis_end_x = width - 5
    #     axis_width = axis_end_x - axis_start_x
    #     axis_y_top = 20
    #     axis_y_bottom = height - 20
        
    #     # Calculate data range per pixel
    #     x_pixels_per_unit = axis_width / (self.x_max - self.x_min)
    #     y_pixels_per_unit = (axis_y_bottom - axis_y_top) / (self.y_max - self.y_min)
        
    #     # Convert pixel delta to data delta
    #     x_delta = dx / x_pixels_per_unit
    #     y_delta = dy / y_pixels_per_unit
        
    #     # Apply panning with boundary checks
    #     new_x_min = self.x_min - x_delta
    #     new_x_max = self.x_max - x_delta
    #     new_y_min = self.y_min + y_delta
    #     new_y_max = self.y_max + y_delta
        
    #     # Don't pan beyond data boundaries
    #     if new_x_min >= 0 and new_x_max <= 520:
    #         self.x_min = new_x_min
    #         self.x_max = new_x_max
            
    #     if new_y_min >= -100 and new_y_max <= 300:  # With some buffer
    #         self.y_min = new_y_min
    #         self.y_max = new_y_max

    # def mousePressEvent(self, event):
    #     """鼠标按下事件"""
    #     if event.button() == Qt.LeftButton:
    #         # Start selection rectangle
    #         self.selection_start = QPointF(event.pos())
    #         self.selection_rect = QRectF(self.selection_start, self.selection_start)
    #     elif event.button() == Qt.RightButton:
    #         # Start panning
    #         self.last_pan_pos = event.pos()
    #         self.setCursor(Qt.ClosedHandCursor)
            
    #     super().mousePressEvent(event)

    # def mouseReleaseEvent(self, event):
    #     """鼠标释放事件"""
    #     if event.button() == Qt.LeftButton and self.selection_start:
    #         # Finish selection rectangle
    #         if self.selection_rect and self.selection_rect.width() > 5 and self.selection_rect.height() > 5:
    #             self.zoom_to_selection()
    #         self.selection_start = None
    #         self.selection_rect = None
    #     elif event.button() == Qt.RightButton:
    #         # Stop panning
    #         self.last_pan_pos = None
    #         self.setCursor(Qt.ArrowCursor)
            
    #     self.update()
    #     super().mouseReleaseEvent(event)

    # def wheelEvent(self, event):
    #     """鼠标滚轮事件 - 以坐标轴中央为中心缩放（X轴和Y轴都基于中心点缩放）"""
    #     # 计算坐标轴中心点（X轴和Y轴各自的中点）
    #     axis_center_x = (self.x_min + self.x_max) / 2
    #     axis_center_y = (self.y_min + self.y_max) / 2
        
    #     # 确定缩放方向（向上滚动缩小范围/放大，向下滚动扩大范围/缩小）
    #     zoom_in = event.angleDelta().y() > 0
    #     zoom_factor = 0.9 if zoom_in else 1.1  # 缩小范围用0.9，扩大范围用1.1
        
    #     # 计算新的X轴范围（以X轴中心点为中心）
    #     new_x_range = (self.x_max - self.x_min) * zoom_factor
    #     self.x_min = max(0, axis_center_x - new_x_range/2)
    #     self.x_max = min(520, axis_center_x + new_x_range/2)
        
    #     # 计算新的Y轴范围（以Y轴中心点为中心）
    #     new_y_range = (self.y_max - self.y_min) * zoom_factor
    #     self.y_min = max(-100, axis_center_y - new_y_range/2)
    #     self.y_max = min(300, axis_center_y + new_y_range/2)
        
    #     # 防止过度缩放（设置最小范围限制）
    #     if self.x_max - self.x_min < 0.1:  # X轴最小时间范围0.1秒
    #         self.x_min = axis_center_x - 0.05
    #         self.x_max = axis_center_x + 0.05
        
    #     if self.y_max - self.y_min < 1:  # Y轴最小拉力范围1mV
    #         self.y_min = axis_center_y - 0.5
    #         self.y_max = axis_center_y + 0.5
        
    #     self.update()  # 更新视图

    # def zoom_to_selection(self):
    #     """Zoom to the selected rectangle in data coordinates"""
    #     if not self.selection_rect:
    #         return
            
    #     width = self.width()
    #     height = self.height()
        
    #     # Coordinate system parameters
    #     axis_start_x = 70
    #     axis_end_x = width - 20
    #     axis_width = axis_end_x - axis_start_x
    #     axis_y_top = 20
    #     axis_y_bottom = height - 20
        
    #     # Convert selection rectangle to data coordinates
    #     sel_x1 = self.selection_rect.left()
    #     sel_x2 = self.selection_rect.right()
    #     sel_y1 = self.selection_rect.top()
    #     sel_y2 = self.selection_rect.bottom()
        
    #     # Calculate data ranges from pixel coordinates
    #     x1_data = self.x_min + (sel_x1 - axis_start_x) / axis_width * (self.x_max - self.x_min)
    #     x2_data = self.x_min + (sel_x2 - axis_start_x) / axis_width * (self.x_max - self.x_min)
    #     y1_data = self.y_max - (sel_y1 - axis_y_top) / (axis_y_bottom - axis_y_top) * (self.y_max - self.y_min)
    #     y2_data = self.y_max - (sel_y2 - axis_y_top) / (axis_y_bottom - axis_y_top) * (self.y_max - self.y_min)
        
    #     # Set new ranges (swap if needed to keep min < max)
    #     self.x_min = min(x1_data, x2_data)
    #     self.x_max = max(x1_data, x2_data)
    #     self.y_min = min(y1_data, y2_data)
    #     self.y_max = max(y1_data, y2_data)
        
    #     # Ensure we don't zoom too much
    #     if self.x_max - self.x_min < 0.1:  # Minimum 0.1 second range
    #         x_center = (self.x_min + self.x_max) / 2
    #         self.x_min = x_center - 0.05
    #         self.x_max = x_center + 0.05
            
    #     if self.y_max - self.y_min < 1:  # Minimum 1 mV range
    #         y_center = (self.y_min + self.y_max) / 2
    #         self.y_min = y_center - 0.5
    #         self.y_max = y_center + 0.5
            
    #     self.update()

    # def leaveEvent(self, event):
    #     """鼠标离开事件"""
    #     self.cursor_pos = None
    #     self.update()
    #     super().leaveEvent(event)

    def paintEvent(self, event):
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()


        # 坐标轴参数
        axis_start_x = 50
        axis_end_x = width - 20
        axis_width = axis_end_x - axis_start_x
        axis_y_top = 20
        axis_y_bottom = height - 20
        
        # 计算可见范围的比例
        x_scale = axis_width / (self.x_max - self.x_min)
        y_scale = (axis_y_bottom - axis_y_top) / (self.y_max - self.y_min)
        
        # 保存原始字体
        original_font = painter.font()
        
        # 设置固定大小的字体用于坐标轴标签
        axis_font = QFont(original_font)
        axis_font.setPointSize(10)  # 固定为10号字体
        painter.setFont(axis_font)

        # 绘制背景和坐标轴
        painter.fillRect(0, 0, width, height, QColor(240, 240, 240))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(axis_start_x, axis_y_bottom, axis_end_x, axis_y_bottom)  # X轴
        painter.drawLine(axis_start_x, axis_y_top, axis_start_x, axis_y_bottom)   # Y轴
        
        # 绘制X轴主刻度和标签
        x_range = self.x_max - self.x_min
        if x_range <= 30:  # 短时间范围（≤30秒）
            major_interval = 3  # 每2秒一个主刻度
        elif x_range <= 60:
            major_interval = 5  # 每5秒一个主刻度
        elif x_range <= 120:
            major_interval = 10  # 每10秒一个主刻度
        elif x_range <= 300:
            major_interval = 30  # 每30秒一个主刻度
        else:
            major_interval = 50  # 每20秒一个主刻度
            
        # 找到第一个大于等于x_min的刻度点
        first_tick = self.x_min - (self.x_min % major_interval)
        if first_tick < self.x_min:
            first_tick += major_interval
            
        # 绘制刻度
        for seconds in range(int(first_tick * 10), int(self.x_max * 10) + 1, int(major_interval * 10)):
            seconds = seconds / 10
            if seconds < self.x_min:
                continue
                
            x_pos = axis_start_x + int((seconds - self.x_min) * x_scale)
            
            # 绘制刻度线
            painter.drawLine(x_pos, axis_y_bottom, x_pos, axis_y_bottom - 8)
            
            # 绘制数字标签
            label_text = f"{seconds:.1f}" if major_interval < 1 else f"{seconds:.0f}"
            text_width = painter.fontMetrics().width(label_text)
            painter.drawText(
                int(x_pos - text_width/2),
                axis_y_bottom + 20,
                label_text
            )
        
        # 绘制Y轴刻度
        y_range = self.y_max - self.y_min
        if y_range <= 20:
            y_interval = 8
        elif y_range <= 50:
            y_interval = 20
        elif y_range <= 100:
            y_interval = 40
        else:
            y_interval = 80
            
        # 找到第一个大于等于y_min的刻度点
        first_tick = self.y_min - (self.y_min % y_interval)
        if first_tick < self.y_min:
            first_tick += y_interval
            
        # 绘制刻度
        for value in range(int(first_tick), int(self.y_max) + 1, y_interval):
            if value < self.y_min:
                continue
                
            y_pos = axis_y_bottom - int((value - self.y_min) * y_scale)
            painter.drawLine(axis_start_x, y_pos, axis_start_x + 5, y_pos)
            
            num_text = f"{value:.0f}" if value < 0 else f" {value:.0f}"
            text_width = 35
            painter.drawText(axis_start_x - text_width, y_pos - 10, 
                        text_width, 20, 
                        Qt.AlignRight | Qt.AlignVCenter, 
                        num_text)
        
        # 绘制数据点
        points = []
        for point in self.data_points:
            if isinstance(point, (tuple, list)) and len(point) == 2:
                force, timestamp = point
                # Only draw points in visible range
                if self.x_min <= timestamp <= self.x_max and self.y_min <= force <= self.y_max:
                    x = axis_start_x + int((timestamp - self.x_min) * x_scale)
                    y = axis_y_bottom - int((force - self.y_min) * y_scale)
                    points.append(QPointF(x, y))
        
        if len(points) > 1:
            painter.setPen(QPen(QColor(0, 0, 255), 1))
            for i in range(1, len(points)):
                painter.drawLine(points[i-1], points[i])
            
            painter.setPen(QPen(QColor(255, 0, 0), 3))
            for point in points:
                painter.drawPoint(point)
        
        # # 绘制鼠标光标和数值提示 (always show when hovering)
        # if self.cursor_pos and self.show_tooltip:
        #     # 计算对应的时间
        #     cursor_x = max(axis_start_x, min(axis_end_x, self.cursor_pos.x()))
        #     relative_x = (cursor_x - axis_start_x) / axis_width
        #     current_time = self.x_min + relative_x * (self.x_max - self.x_min)
            
        #     # 找到最接近的数据点
        #     closest_point = None
        #     min_distance = float('inf')
        #     for point in self.data_points:
        #         if isinstance(point, (tuple, list)) and len(point) == 2:
        #             force, timestamp = point
        #             distance = abs(timestamp - current_time)
        #             if distance < min_distance:
        #                 min_distance = distance
        #                 closest_point = point
            
        #     if closest_point:
        #         force, timestamp = closest_point
                
        #         # 绘制垂直线
        #         x_pos = axis_start_x + int((timestamp - self.x_min) * x_scale)
        #         painter.setPen(QPen(QColor(0, 128, 0), 1, Qt.DashLine))
        #         painter.drawLine(x_pos, axis_y_top, x_pos, axis_y_bottom)
                
        #         # 绘制水平线
        #         y_pos = axis_y_bottom - int((force - self.y_min) * y_scale)
        #         painter.drawLine(axis_start_x, y_pos, axis_end_x, y_pos)
                
        #         # 绘制数值提示框
        #         info_text = f"拉力: {force:.1f}mV\n时间: {timestamp:.2f}s"
        #         text_width = painter.fontMetrics().width(f"拉力: {force:.1f}mV")
        #         text_height = 40
                
        #         # 确定提示框位置（避免超出边界）
        #         box_x = self.cursor_pos.x() + 10 if self.cursor_pos.x() < width - text_width - 30 else self.cursor_pos.x() - text_width - 20
        #         box_y = max(20, min(height - text_height - 20, self.cursor_pos.y()))
                
        #         # 绘制背景框
        #         painter.setBrush(QBrush(QColor(255, 255, 225)))
        #         painter.setPen(QPen(QColor(0, 0, 0), 1))
        #         painter.drawRect(box_x, box_y, text_width + 10, text_height)
                
        #         # 绘制文本
        #         painter.setPen(QPen(QColor(0, 0, 0), 1))
        #         painter.drawText(box_x + 5, box_y + 15, f"拉力: {force:.1f}mV")
        #         painter.drawText(box_x + 5, box_y + 35, f"时间: {timestamp:.2f}s")
        
        # Draw selection rectangle
        if self.selection_rect:
            painter.setPen(QPen(QColor(0, 0, 255), 1, Qt.DashLine))
            painter.setBrush(QBrush(QColor(100, 100, 255, 50)))
            painter.drawRect(self.selection_rect)

        if hasattr(self, 'enlarged_window') and self.enlarged_window:
            # self.show_enlarged_view();
            self.enlarged_window.update_data(self.data_points)
            self.enlarged_window.raise_()
            # self.enlarged_window.x_min = self.x_min
            # self.enlarged_window.x_max = self.x_max
            # self.enlarged_window.y_min = self.y_min
            # self.enlarged_window.y_max = self.y_max
        #
        # 如果有放大窗口，同步视图范围
        # if hasattr(self, 'enlarged_window') and self.enlarged_window:
        #     self.enlarged_window.sync_with_parent()
        # self.enlarged_window.update()  # 强制重绘

class EnlargedDataDisplay(QWidget):
    def __init__(self, parent_display, parent=None):
        super().__init__(parent)
        self.setWindowTitle("力敏传感器电压采集图")
        self.setMinimumSize(800, 500)
        self.resize(1157, 550)  # 覆盖最小大小限制，直接设定初始尺寸
        # self.setFixedHeight(550)
        self.parent_display = parent_display
        self.data_points = []
        self.set_default_view()  # 设置默认视图范围
        # 在初始化代码中添加
        self.setAttribute(Qt.WA_AcceptTouchEvents, False)  # 避免触摸事件干扰
        self.setFocusPolicy(Qt.StrongFocus)  # 确保能接收键盘事件

        # # 确保灵敏度编辑框可以被访问
        # self.sensitivity_edit = self.create_label_edit_pair(layout, "灵敏度（mV/N）", "")

        # # 初始化视图范围与父显示一致
        self.x_min = parent_display.x_min if hasattr(parent_display, 'x_min') else 0
        self.x_max = parent_display.x_max if hasattr(parent_display, 'x_max') else 520
        self.y_min = parent_display.y_min if hasattr(parent_display, 'y_min') else -50
        self.y_max = parent_display.y_max if hasattr(parent_display, 'y_max') else 200

        # 初始化视图范围与父显示一致
        # self.sync_with_parent()
        # 鼠标交互相关变量
        self.cursor_pos = None
        self.selection_rect = None
        self.selection_start = None
        self.last_pan_pos = None
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)  # 强制工具提示显示
        
        # 增强工具提示样式
        self.tooltip_label = QLabel(self)
        self.tooltip_label.setStyleSheet("""
            background-color: rgba(255, 255, 225, 220);
            border: 2px solid #555;
            border-radius: 5px;
            padding: 8px;
            font-size: 16px;
            font-weight: bold;
            min-width: 200px;
        """)
        self.tooltip_label.hide()
        

        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # 1. 图表绘制区域 (使用自定义Widget)
        self.chart_widget = QWidget()
        self.chart_widget.setMinimumHeight(400)  # 固定最小高度
        self.main_layout.addWidget(self.chart_widget, stretch=3)  # 占据3份空间
        
        # 2. 信息显示区域
        self.info_widget = QWidget()
        self.main_layout.addWidget(self.info_widget, stretch=2)  # 占据2份空间
        
        # 初始化信息区域
        self.init_info_area()
    
    def set_sensitivity(self, sensitivity):
        """设置灵敏度值并更新UI"""
        self.sensitivity_edit.setText(f"{sensitivity:.2f}")
        self.update()  # 确保UI更新

    def pause_parent_timer(self):
        """暂停父窗口的定时器"""
        if hasattr(self.parent_display, 'collection_timer'):
            self.parent_display.collection_timer.stop()

    def resume_parent_timer(self):
        """恢复父窗口的定时器"""
        if hasattr(self.parent_display, 'collection_timer'):
            self.parent_display.collection_timer.start()

    def init_left_panel(self, layout):
        """初始化左侧信息面板"""
        # 创建6行输入框
        self.temperature_edit = self.create_label_edit_pair(layout, "环境温度（℃）", "25")
        self.inner_diameter_edit = self.create_label_edit_pair(layout, "圆环内径（cm）", "3.30")
        self.outer_diameter_edit = self.create_label_edit_pair(layout, "圆环外径（cm）", "3.50")
        self.sensitivity_edit = self.create_label_edit_pair(layout, "灵敏度（mV/N）", "")
        self.theoretical_tension_edit = self.create_label_edit_pair(layout, "表面张力理论值（N/m）", "")
        self.liquid_edit = self.create_label_edit_pair(layout, "被测液体", "")
        
        
        # 添加弹簧使输入框靠上
        layout.addStretch()

    def init_liquid_buttons(self):
        """在被测液体框右侧添加三个液体选择按钮"""
        # 获取液体编辑框的父布局
        liquid_row = self.liquid_edit.parent().layout()
        
        # 创建按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_container.setLayout(button_layout)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        
        # 创建三个液体按钮
        self.water_btn = QPushButton("纯水")
        self.ethanol_btn = QPushButton("乙醇")
        self.glycerol_btn = QPushButton("甘油")
        
        # 设置按钮样式
        button_style = """
            QPushButton {
                font-size: 12px;
                min-width: 50px;
                max-width: 50px;
                padding: 2px;
            }
        """
        self.water_btn.setStyleSheet(button_style)
        self.ethanol_btn.setStyleSheet(button_style)
        self.glycerol_btn.setStyleSheet(button_style)
        
        # 连接按钮信号
        self.water_btn.clicked.connect(lambda: self.set_liquid("water"))
        self.ethanol_btn.clicked.connect(lambda: self.set_liquid("ethanol"))
        self.glycerol_btn.clicked.connect(lambda: self.set_liquid("glycerol"))
        
        # 将按钮添加到布局
        button_layout.addWidget(self.water_btn)
        button_layout.addWidget(self.ethanol_btn)
        button_layout.addWidget(self.glycerol_btn)
        
        # 将按钮容器添加到液体编辑框所在的行布局
        liquid_row.addWidget(button_container)
    
    def set_liquid(self, liquid_type):
        """设置液体类型并填充理论值"""
        liquid_names = {
            "water": ("纯水", "0.07197"),
            "ethanol": ("乙醇", "0.0223"),
            "glycerol": ("甘油", "0.0579")
        }
        
        if liquid_type in liquid_names:
            name, tension = liquid_names[liquid_type]
            self.liquid_edit.setText(name)
            self.theoretical_tension_edit.setText(tension)

    def create_label_edit_pair(self, layout, label_text, default_value=""):
        """创建标签-输入框对"""
        row = QHBoxLayout()
        
        label = QLabel(label_text)
        label.setFixedWidth(180)  # 固定标签宽度
        edit = QLineEdit(default_value)
        edit.setFixedWidth(100)  # 固定输入框宽度
        
        row.addWidget(label)
        row.addWidget(edit)
        layout.addLayout(row)
        
        return edit

    def init_right_panel(self, layout):
        """初始化右侧信息面板"""
        # 上部分5/6 - 表格
        table_panel = QWidget()
        table_layout = QVBoxLayout()
        table_panel.setLayout(table_layout)
        
        # 创建表格
        self.create_result_table(table_layout)
        
        # 下部分1/6 - 计算结果
        calc_panel = QWidget()
        calc_layout = QHBoxLayout()
        calc_panel.setLayout(calc_layout)
        
        # 添加计算结果组件
        self.create_calculation_area(calc_layout)
        
        # 将上下部分添加到右侧布局
        layout.addWidget(table_panel, 5)
        layout.addWidget(calc_panel, 1)

    def init_info_area(self):
        """初始化信息显示区域"""
        layout = QHBoxLayout()
        self.info_widget.setLayout(layout)
        
        # 左侧1/3
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        self.init_left_panel(left_layout)
        self.init_liquid_buttons()
        
        # 右侧2/3
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        self.init_right_panel(right_layout)
        
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)

    def create_result_table(self, layout):
        """创建结果表格"""
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setRowCount(1)  # 初始1行
        
        # 设置表头
        headers = ["", "拉断前电压(mV)", "拉断后电压(mV)", "电压差(mV)", 
                "拉力差(N)", "表面张力实测值(N/m)"]
        self.table.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        self.table.setColumnWidth(0, 30)   # 标志列
        self.table.setColumnWidth(1, 140)  # 拉断前
        self.table.setColumnWidth(2, 140)  # 拉断后
        self.table.setColumnWidth(3, 100)  # 电压差(只读)
        self.table.setColumnWidth(4, 100)  # 拉力差(只读)
        self.table.setColumnWidth(5, 190)  # 实测值(只读)
        
        # 设置表格属性
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.DoubleClicked)  # 双击编辑
        
        # 设置第3-5列为只读
        for col in [3, 4, 5]:
            for row in range(self.table.rowCount()):
                item = QTableWidgetItem("")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, col, item)
        
        # 连接信号
        self.table.currentCellChanged.connect(self.on_current_cell_changed)
        self.table.cellChanged.connect(self.on_table_cell_changed)
        
        # 初始化第一行的标志
        self.update_row_indicators()
        
        layout.addWidget(self.table)

    def on_table_cell_changed(self, row, column):
        """表格单元格变化处理 - 只处理添加新行逻辑"""
        # 如果是最后一行且有数据，添加新行
        if row == self.table.rowCount() - 1:
            has_data = any(self.table.item(row, col) is not None 
                    and self.table.item(row, col).text().strip() != ""
                    for col in range(1, self.table.columnCount()))
            
            if has_data:
                self.table.setRowCount(self.table.rowCount() + 1)
                self.update_row_indicators()

    def on_current_cell_changed(self, current_row, current_col, previous_row, previous_col):
        """当前选中单元格变化时更新标志"""
        self.update_row_indicators()

    def update_row_indicators(self):
        """更新每行的标志符号"""
        last_row = self.table.rowCount() - 1
        
        for row in range(self.table.rowCount()):
            # 获取或创建标志单元格
            indicator_item = self.table.item(row, 0)
            if not indicator_item:
                indicator_item = QTableWidgetItem()
                indicator_item.setFlags(Qt.ItemIsEnabled)  # 不可编辑
                self.table.setItem(row, 0, indicator_item)
            
            # 当前选中行
            current_row = self.table.currentRow()
            
            # 设置标志文本
            if row == last_row:
                if row == current_row:
                    indicator_item.setText(">*")  # 既是当前行又是最后一行
                else:
                    indicator_item.setText("*")   # 最后一行
            else:
                if row == current_row:
                    indicator_item.setText(">")   # 当前行
                else:
                    indicator_item.setText("")    # 普通行

    def create_calculation_area(self, layout):
        """创建计算结果区域"""
        # 平均实测值
        avg_label = QLabel("表面张力平均实测值（N/m）:")
        self.avg_value = QLineEdit()
        self.avg_value.setReadOnly(True)
        self.avg_value.setFixedWidth(100)
        
        # 误差
        error_label = QLabel("误差:")
        self.error_value = QLineEdit()
        self.error_value.setReadOnly(True)
        self.error_value.setFixedWidth(100)
        
        # 计算按钮
        calc_btn = QPushButton("计算")
        calc_btn.setFixedWidth(80)
        calc_btn.clicked.connect(self.calculate_results)

        # 清空数据按钮
        clear_btn = QPushButton("清空数据")
        clear_btn.setFixedWidth(80)
        clear_btn.clicked.connect(self.clear_table_data)

        # 导出按钮
        export_btn = QPushButton("导出数据")
        export_btn.setFixedWidth(80)
        export_btn.clicked.connect(self.parent_display.export_data)  # 使用父窗口的导出方法
        
        # 添加到布局
        layout.addWidget(avg_label)
        layout.addWidget(self.avg_value)
        layout.addSpacing(20)
        layout.addWidget(error_label)
        layout.addWidget(self.error_value)
        layout.addSpacing(20)
        layout.addWidget(calc_btn)
        layout.addWidget(clear_btn)
        layout.addWidget(export_btn) 
        layout.addStretch()

    def clear_table_data(self):
        """清空表格数据"""
        # 确认对话框
        reply = QMessageBox.question(self, "确认清空", 
                                "确定要清空所有数据吗？此操作不可撤销。",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 清空表格内容但保留表头
            self.table.setRowCount(1)  # 重置为1行（保留空行）
            
            # 清空所有单元格内容
            for row in range(self.table.rowCount()):
                for col in range(1, self.table.columnCount()):  # 从第1列开始（跳过标志列）
                    self.table.setItem(row, col, QTableWidgetItem(""))
            
            # 清空计算结果
            self.avg_value.clear()
            self.error_value.clear()
            
            # 更新行指示器
            self.update_row_indicators()

            # 设置第3-5列为只读
            for col in [3, 4, 5]:
                for row in range(self.table.rowCount()):
                    item = QTableWidgetItem("")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row, col, item)
            
            QMessageBox.information(self, "完成", "数据已清空")

    def calculate_voltage_diff(self, row):
        """计算电压差"""
        try:
            before = float(self.table.item(row, 1).text())
            after = float(self.table.item(row, 2).text())
            diff = before - after
            self.table.setItem(row, 3, QTableWidgetItem(f"{diff:.2f}"))
        except:
            pass

    def calculate_tension(self, row):
        """计算表面张力"""
        try:
            # 获取输入值
            voltage_diff = float(self.table.item(row, 3).text())
            sensitivity = float(self.sensitivity_edit.text())
            inner_d = float(self.inner_diameter_edit.text()) / 100  # 转换为米
            outer_d = float(self.outer_diameter_edit.text()) / 100  # 转换为米
            
            # 计算拉力差 (N)
            force_diff = voltage_diff / sensitivity
            
            # 计算表面张力 (N/m)
            # 公式: γ = ΔF / (π(D+d))
            tension = force_diff / (3.1416 * (outer_d + inner_d))
            
            # 更新表格
            self.table.setItem(row, 4, QTableWidgetItem(f"{force_diff:.6f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{tension:.6f}"))
        except:
            pass

    def calculate_results(self):
        """计算按钮点击事件 - 计算所有行的值、平均值和误差"""
        try:
            # 先计算所有行的值
            for row in range(self.table.rowCount() - 1):  # 忽略最后空行
                self.calculate_row_values(row)
                
            # 然后计算平均值和误差
            self._calculate_average_and_error()
            
        except Exception as e:
            QMessageBox.warning(self, "计算错误", f"计算过程中发生错误:\n{str(e)}")

    def calculate_row_values(self, row):
        """计算单行的电压差、拉力差和表面张力"""
        try:
            # 计算电压差
            before = self.table.item(row, 1).text()
            after = self.table.item(row, 2).text()
            if before and after:
                voltage_diff = float(before) - float(after)
                item = QTableWidgetItem(f"{voltage_diff:.2f}")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 设置为只读
                self.table.setItem(row, 3, item)
                
                # 计算拉力差
                if self.sensitivity_edit.text():
                    sensitivity = float(self.sensitivity_edit.text())
                    force_diff = voltage_diff / sensitivity
                    item = QTableWidgetItem(f"{force_diff:.6f}")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 设置为只读
                    self.table.setItem(row, 4, item)
                    
                    # 计算表面张力
                    if (self.inner_diameter_edit.text() and 
                        self.outer_diameter_edit.text()):
                        inner_d = float(self.inner_diameter_edit.text()) / 100  # cm→m
                        outer_d = float(self.outer_diameter_edit.text()) / 100  # cm→m
                        tension = force_diff / (3.1416 * (outer_d + inner_d))
                        item = QTableWidgetItem(f"{tension:.6f}")
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 设置为只读
                        self.table.setItem(row, 5, item)
                        
        except ValueError:
            pass  # 忽略计算错误，留空单元格
    
    def _calculate_average_and_error(self):
        """计算平均值和误差(内部方法)"""
        tensions = []
        for row in range(self.table.rowCount() - 1):  # 忽略最后空行
            item = self.table.item(row, 5)
            if item and item.text():
                tensions.append(float(item.text()))
        
        if tensions:
            # 计算平均值
            avg = sum(tensions) / len(tensions)
            self.avg_value.setText(f"{avg:.6f}")
            
            # 计算误差
            if self.theoretical_tension_edit.text():
                theoretical = float(self.theoretical_tension_edit.text())
                error = abs(avg - theoretical) / theoretical * 100
                self.error_value.setText(f"{error:.2f}%")


    def update_data(self, data_points):
        """更新数据点"""
        self.data_points = data_points
        self.update()  # 触发重绘
    
    def set_default_view(self):
        """设置默认视图范围"""
        self.x_min = 0
        self.x_max = 512  # 默认26秒
        self.y_min = -50
        self.y_max = 200

    def sync_with_parent(self):
        """与父窗口同步视图范围"""
        if self.parent_display:
            self.x_min = self.parent_display.x_min
            self.x_max = self.parent_display.x_max
            self.y_min = self.parent_display.y_min
            self.y_max = self.parent_display.y_max
            self.update()
    
    # def sync_to_parent(self):
    #     """将视图范围同步到父窗口"""
    #     if self.parent_display:
    #         self.parent_display.x_min = self.x_min
    #         self.parent_display.x_max = self.x_max
    #         self.parent_display.y_min = self.y_min
    #         self.parent_display.y_max = self.y_max
    #         self.parent_display.update()
    
    def wheelEvent(self, event):
        """鼠标滚轮缩放"""
        # 计算坐标轴中心点
        axis_center_x = (self.x_min + self.x_max) / 2
        axis_center_y = (self.y_min + self.y_max) / 2
        
        # 确定缩放方向
        zoom_in = event.angleDelta().y() > 0
        zoom_factor = 0.9 if zoom_in else 1.1
        
        # 计算新的X轴范围
        new_x_range = (self.x_max - self.x_min) * zoom_factor
        self.x_min = max(0, axis_center_x - new_x_range/2)
        self.x_max = min(520, axis_center_x + new_x_range/2)
        
        # 计算新的Y轴范围
        new_y_range = (self.y_max - self.y_min) * zoom_factor
        self.y_min = max(-100, axis_center_y - new_y_range/2)
        self.y_max = min(300, axis_center_y + new_y_range/2)
        
        # 防止过度缩放
        if self.x_max - self.x_min < 0.1:
            self.x_min = axis_center_x - 0.05
            self.x_max = axis_center_x + 0.05
        
        if self.y_max - self.y_min < 1:
            self.y_min = axis_center_y - 0.5
            self.y_max = axis_center_y + 0.5
        
        # self.sync_to_parent()  # 同步到父窗口
        self.update()
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        chart_rect = self.chart_widget.geometry()
        if not chart_rect.contains(event.pos()):
            super().mousePressEvent(event)
            return

        # 右键按下 - 开始拖动平移
        if event.button() == Qt.RightButton:
            self.last_pan_pos = event.pos()
            # self.pause_parent_timer()
            self.setCursor(Qt.ClosedHandCursor)
        
        # 中键按下 - 开始选择区域
        elif event.button() == Qt.MiddleButton:
            self.selection_start = QPointF(event.pos())
            self.selection_rect = QRectF(self.selection_start, self.selection_start)
        
        # 左键按下 - 显示拉力时间信息框
        elif event.button() == Qt.LeftButton:
            self.cursor_pos = event.pos() - chart_rect.topLeft()
            self.update_tooltip()
        
        self.update()
        super().mousePressEvent(event)

    def handle_data_point_selection(self, pos):
        """处理数据查询模式下的数据点选择"""
        if not self.data_points:
            return
        
        width = self.chart_widget.width()
        height = self.chart_widget.height()
        
        # 坐标轴参数
        axis_start_x = 100
        axis_end_x = width - 40
        axis_width = axis_end_x - axis_start_x
        axis_y_top = 40
        axis_y_bottom = height - 80
        
        # 计算点击位置对应的时间
        click_x = max(axis_start_x, min(axis_end_x, pos.x()))
        relative_x = (click_x - axis_start_x) / axis_width
        clicked_time = self.x_min + relative_x * (self.x_max - self.x_min)
        
        # 找到最接近的数据点
        closest_index = -1
        min_distance = float('inf')
        
        for i, (_, timestamp) in enumerate(self.data_points):
            distance = abs(timestamp - clicked_time)
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
        # 更新当前选中的数据点索引
        if closest_index >= 0 and hasattr(self.parent_display, 'current_point_index'):
            self.parent_display.current_point_index = closest_index
            self.parent_display.update_query_point_display()
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        chart_rect = self.chart_widget.geometry()
        if not chart_rect.contains(event.pos()):
            self.selection_start = None
            self.selection_rect = None
            super().mouseMoveEvent(event)
            return

        # 右键拖动平移
        if event.buttons() & Qt.RightButton and hasattr(self, 'last_pan_pos'):
            delta = event.pos() - self.last_pan_pos
            self.pan_view(delta.x(), delta.y())
            self.last_pan_pos = event.pos()

        # 中键拖动选择区域
        elif event.buttons() & Qt.MiddleButton and self.selection_start:
            self.selection_rect = QRectF(self.selection_start, QPointF(event.pos()))
        
        # 左键移动时更新信息框位置
        elif event.buttons() & Qt.LeftButton:
            self.cursor_pos = event.pos() - chart_rect.topLeft()
            self.update_tooltip()
        
        self.update()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        chart_rect = self.chart_widget.geometry()
        if chart_rect.contains(event.pos()):
            if event.button() == Qt.MiddleButton and self.selection_start:
                if self.selection_rect and self.selection_rect.width() > 5 and self.selection_rect.height() > 5:
                    self.zoom_to_selection()
                self.selection_start = None
                self.selection_rect = None
            
            elif event.button() == Qt.RightButton:
                self.last_pan_pos = None
                # self.resume_parent_timer()
                self.setCursor(Qt.ArrowCursor)
            
            # 中键释放时不清除cursor_pos，保持信息框显示
            # 直到鼠标移动出图表区域或再次按下其他按钮
        
        self.update()
        super().mouseReleaseEvent(event)
    
    def pan_view(self, dx, dy):
        """平移视图"""
        width = self.width()
        height = self.height()
        
        axis_start_x = 100
        axis_end_x = width - 40
        axis_width = axis_end_x - axis_start_x
        axis_y_top = 40
        axis_y_bottom = height - 180
        
        # 计算数据范围每像素
        x_pixels_per_unit = axis_width / (self.x_max - self.x_min)
        y_pixels_per_unit = (axis_y_bottom - axis_y_top) / (self.y_max - self.y_min)
        
        # 转换为数据增量
        x_delta = dx / x_pixels_per_unit
        y_delta = dy / y_pixels_per_unit
        
        # 应用平移
        new_x_min = self.x_min - x_delta
        new_x_max = self.x_max - x_delta
        new_y_min = self.y_min + y_delta
        new_y_max = self.y_max + y_delta
        
        # 边界检查
        if new_x_min >= 0 and new_x_max <= 520:
            self.x_min = new_x_min
            self.x_max = new_x_max
            
        if new_y_min >= -100 and new_y_max <= 300:
            self.y_min = new_y_min
            self.y_max = new_y_max
    
    def zoom_to_selection(self):
        if not self.selection_rect:
            return
            
        chart_rect = self.chart_widget.geometry()
        axis_start_x = 100  # 与绘制时一致
        axis_end_x = chart_rect.width() - 40
        axis_width = axis_end_x - axis_start_x
        axis_y_top = 40
        axis_y_bottom = chart_rect.height()-180
        if chart_rect.height() > 400:
            axis_y_bottom = chart_rect.height()-90
        elif chart_rect.height() > 450:
            axis_y_bottom = chart_rect.height()-30
        
        # 转换选择矩形到图表坐标（减去图表区域偏移）
        sel_rect = self.selection_rect.translated(-chart_rect.topLeft())
        
        # 转换为数据坐标（考虑坐标轴偏移）
        x1_data = self.x_min + (sel_rect.left() - axis_start_x) / axis_width * (self.x_max - self.x_min)
        x2_data = self.x_min + (sel_rect.right() - axis_start_x) / axis_width * (self.x_max - self.x_min)
        y1_data = self.y_max - (sel_rect.top() - axis_y_top) / (axis_y_bottom - axis_y_top) * (self.y_max - self.y_min)
        y2_data = self.y_max - (sel_rect.bottom() - axis_y_top) / (axis_y_bottom - axis_y_top) * (self.y_max - self.y_min)
        
        # 设置新范围并同步到父窗口
        self.x_min, self.x_max = sorted([x1_data, x2_data])
        self.y_min, self.y_max = sorted([y1_data, y2_data])
        # self.sync_to_parent()  # 确保同步到父窗口
        self.update()
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        # self.cursor_pos = None
        # self.tooltip_label.hide()
        self.update()
        super().leaveEvent(event)

    def update_tooltip(self):
        """更新更详细的工具提示"""
        if not self.cursor_pos or not self.data_points:
            self.tooltip_label.hide()
            return
            
        width = self.chart_widget.width()
        height = self.chart_widget.height()
        
        # 坐标轴参数
        axis_start_x = 100
        axis_end_x = width - 40
        axis_width = axis_end_x - axis_start_x
        axis_y_top = 40
        axis_y_bottom = height - 80
        
        # 计算鼠标位置对应的时间
        cursor_x = max(axis_start_x, min(axis_end_x, self.cursor_pos.x()))
        relative_x = (cursor_x - axis_start_x) / axis_width
        current_time = self.x_min + relative_x * (self.x_max - self.x_min)
        
        # 找到最接近的数据点
        closest_point = None
        min_distance = float('inf')
        for point in self.data_points:
            if isinstance(point, (tuple, list)) and len(point) == 2:
                force, timestamp = point
                distance = abs(timestamp - current_time)
                if distance < min_distance:
                    min_distance = distance
                    closest_point = point
        
        if closest_point:
            force, timestamp = closest_point
            
            # # 设置更详细的提示文本
            # self.tooltip_label.setText(
            #     f"<b>详细测量数据</b><br>"
            #     f"拉力: <font color='blue'>{force:.1f} mV</font><br>"
            #     f"时间: <font color='green'>{timestamp:.2f} s</font><br>"
            #     f"坐标: ({timestamp:.2f}, {force:.1f})"
            # )
            
            # # 调整工具提示位置
            # self.tooltip_label.adjustSize()
            # tooltip_x = self.mapToGlobal(QPoint(0, 0)).x() + self.cursor_pos.x() + 20
            # tooltip_y = self.mapToGlobal(QPoint(0, 0)).y() + self.cursor_pos.y()
            
            # # 确保不超出屏幕
            # screen_rect = QApplication.desktop().availableGeometry(self)
            # if tooltip_x + self.tooltip_label.width() > screen_rect.right():
            #     tooltip_x = screen_rect.right() - self.tooltip_label.width() - 10
            # if tooltip_y + self.tooltip_label.height() > screen_rect.bottom():
            #     tooltip_y = screen_rect.bottom() - self.tooltip_label.height() - 10
                
            # self.tooltip_label.move(tooltip_x, tooltip_y)
            # self.tooltip_label.show()

    def paintEvent(self, event):
        if event.rect().intersects(self.chart_widget.geometry()):
            painter = QPainter(self)
            self.draw_chart(painter)
            
            # 仅在中键按下或移动时显示信息框
            if hasattr(self, 'cursor_pos') and self.cursor_pos and \
                hasattr(self, 'data_points') and self.data_points:
                # 计算对应的时间
                width = self.chart_widget.width()
                height = self.chart_widget.height()
                
                axis_start_x = 100
                axis_end_x = width - 40
                axis_width = axis_end_x - axis_start_x
                axis_y_top = 40
                axis_y_bottom = height - 80
                
                # 计算缩放因子（必须在这里计算）
                x_scale = axis_width / (self.x_max - self.x_min)
                y_scale = (axis_y_bottom - axis_y_top) / (self.y_max - self.y_min)
            
                cursor_x = max(axis_start_x, min(axis_end_x, self.cursor_pos.x()))
                relative_x = (cursor_x - axis_start_x) / axis_width
                current_time = self.x_min + relative_x * (self.x_max - self.x_min)
                
                # 找到最接近的数据点
                closest_point = None
                min_distance = float('inf')
                for point in self.data_points:
                    if isinstance(point, (tuple, list)) and len(point) == 2:
                        force, timestamp = point
                        distance = abs(timestamp - current_time)
                        if distance < min_distance:
                            min_distance = distance
                            closest_point = point
                
                if closest_point:
                    force, timestamp = closest_point
                    
                    # 绘制垂直线
                    x_pos = axis_start_x + int((timestamp - self.x_min) * x_scale)
                    painter.setPen(QPen(QColor(0, 128, 0), 1, Qt.DashLine))
                    painter.drawLine(x_pos, axis_y_top, x_pos, axis_y_bottom)
                    
                    # 仅在数据点可见时才绘制水平线
                    # if self.y_min <= force <= self.y_max:
                    #     y_pos = axis_y_bottom - int((force - self.y_min) * y_scale)
                    #     painter.drawLine(axis_start_x, y_pos, axis_end_x, y_pos)
                    
                    # 绘制数值提示框
                    info_text = f"拉力: {force:.1f}mV\n时间: {timestamp:.2f}s"
                    text_width = painter.fontMetrics().width(f"拉力: {force:.1f}mV")
                    text_height = 40
                    
                    # 确定提示框位置（避免超出边界）
                    box_x = self.cursor_pos.x() + 10 if self.cursor_pos.x() < width - text_width - 30 else self.cursor_pos.x() - text_width - 20
                    box_y = max(20, min(height - text_height - 20, self.cursor_pos.y()))
                    
                    # 绘制背景框
                    painter.setBrush(QBrush(QColor(255, 255, 225)))
                    painter.setPen(QPen(QColor(0, 0, 0), 1))
                    painter.drawRect(box_x, box_y, text_width + 10, text_height)
                    
                    # 绘制文本
                    painter.setPen(QPen(QColor(0, 0, 0), 1))
                    painter.drawText(box_x + 5, box_y + 15, f"拉力: {force:.1f}mV")
                    painter.drawText(box_x + 5, box_y + 35, f"时间: {timestamp:.2f}s")

    def draw_chart(self, painter):
        """实际的图表绘制逻辑"""
        chart_rect = self.chart_widget.geometry()
        width = chart_rect.width()
        height = chart_rect.height()
        print(f"draw_chart: {width} x {height}")
        # 坐标原点偏移到图表区域
        painter.translate(chart_rect.topLeft())

        # 绘制背景
        painter.fillRect(0, 0, width, height, QColor(240, 240, 240))

        # 坐标轴参数 - 放大尺寸
        axis_start_x = 100
        axis_end_x = width - 40
        axis_width = axis_end_x - axis_start_x
        axis_y_top = 40
        axis_y_bottom = height-180
        if height > 400:
            axis_y_bottom = height-90
        elif height > 450:
            axis_y_bottom = height-30
        
        # 计算缩放因子
        x_scale = axis_width / (self.x_max - self.x_min)
        y_scale = (axis_y_bottom - axis_y_top) / (self.y_max - self.y_min)
        
        # 绘制背景和坐标轴
        painter.fillRect(0, 0, width, height, QColor(240, 240, 240))
        painter.setPen(QPen(Qt.black, 2))  # 加粗坐标轴
        painter.drawLine(axis_start_x, axis_y_bottom, axis_end_x, axis_y_bottom)  # X轴
        painter.drawLine(axis_start_x, axis_y_top, axis_start_x, axis_y_bottom)   # Y轴
        
        # 设置更大的字体
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)
        
        # 绘制X轴标题
        x_axis_title = "时间/S"
        title_width = painter.fontMetrics().width(x_axis_title)
        title_height=height-120
        if height > 400:
            title_height=height-30
        elif height > 450:
            title_height=height
        painter.drawText(
            axis_start_x + (axis_width - title_width) // 2,
            title_height,
            x_axis_title
        )
        
        # 绘制Y轴标题
        y_axis_title = "输出电压/mV"
        title_width = painter.fontMetrics().width(y_axis_title)
        
        # 保存当前状态
        painter.save()
        # 旋转90度绘制Y轴标题
        painter.translate(30, (axis_y_top + axis_y_bottom) // 2)
        painter.rotate(-90)
        painter.drawText(-40, 10, y_axis_title)
        # 恢复状态
        painter.restore()

        # 绘制X轴主刻度和标签
        x_range = self.x_max - self.x_min
        if x_range <= 30:  # 短时间范围（≤30秒）
            major_interval = 2  # 每2秒一个主刻度
        elif x_range <= 60:
            major_interval = 5  # 每5秒一个主刻度
        elif x_range <= 120:
            major_interval = 10  # 每10秒一个主刻度
        elif x_range <= 300:
            major_interval = 30  # 每30秒一个主刻度
        else:
            major_interval = 50  # 每20秒一个主刻度
            
        # 找到第一个大于等于x_min的刻度点
        first_tick = self.x_min - (self.x_min % major_interval)
        if first_tick < self.x_min:
            first_tick += major_interval
            
        # 绘制刻度
        for seconds in range(int(first_tick * 10), int(self.x_max * 10) + 1, int(major_interval * 10)):
            seconds = seconds / 10
            if seconds < self.x_min:
                continue
                
            x_pos = axis_start_x + int((seconds - self.x_min) * x_scale)
            
            # 绘制刻度线
            painter.drawLine(x_pos, axis_y_bottom, x_pos, axis_y_bottom - 10)
            
            # 绘制数字标签
            label_text = f"{seconds:.1f}" if major_interval < 1 else f"{seconds:.0f}"
            text_width = painter.fontMetrics().width(label_text)
            painter.drawText(
                int(x_pos - text_width/2),
                axis_y_bottom + 25,  # 更大的间距
                label_text
            )
        
        # 绘制Y轴刻度
        y_range = self.y_max - self.y_min
        if y_range <= 20:
            y_interval = 4
        elif y_range <= 50:
            y_interval = 10
        elif y_range <= 100:
            y_interval = 20
        else:
            y_interval = 40
            
        # 找到第一个大于等于y_min的刻度点
        first_tick = self.y_min - (self.y_min % y_interval)
        if first_tick < self.y_min:
            first_tick += y_interval
            
        # 绘制刻度
        for value in range(int(first_tick), int(self.y_max) + 1, y_interval):
            if value < self.y_min:
                continue
                
            y_pos = axis_y_bottom - int((value - self.y_min) * y_scale)
            painter.drawLine(axis_start_x, y_pos, axis_start_x + 8, y_pos)  # 更长的刻度线
            
            num_text = f"{value:.0f}" if value < 0 else f" {value:.0f}"
            text_width = 50  # 更大的文本区域
            painter.drawText(axis_start_x - text_width, y_pos - 15, 
                        text_width, 30, 
                        Qt.AlignRight | Qt.AlignVCenter, 
                        num_text)
        
        # 绘制数据点
        points = []
        for point in self.data_points:
            if isinstance(point, (tuple, list)) and len(point) == 2:
                force, timestamp = point
                # 只绘制可见范围内的点
                if self.x_min <= timestamp <= self.x_max and self.y_min <= force <= self.y_max:
                    x = axis_start_x + int((timestamp - self.x_min) * x_scale)
                    y = axis_y_bottom - int((force - self.y_min) * y_scale)
                    points.append(QPointF(x, y))
        
        if len(points) > 1:
            # 绘制连线 - 使用更粗的线
            painter.setPen(QPen(QColor(0, 0, 255), 2))
            for i in range(1, len(points)):
                painter.drawLine(points[i-1], points[i])
            
            # 绘制数据点 - 使用更大的点
            painter.setPen(QPen(QColor(255, 0, 0), 5))
            for point in points:
                painter.drawPoint(point)

        # 绘制鼠标悬停提示
        if self.cursor_pos and self.data_points:
            # 计算对应的时间
            cursor_x = max(axis_start_x, min(axis_end_x, self.cursor_pos.x()))
            relative_x = (cursor_x - axis_start_x) / axis_width
            current_time = self.x_min + relative_x * (self.x_max - self.x_min)
            
            # 找到最接近的数据点
            closest_point = None
            min_distance = float('inf')
            for point in self.data_points:
                if isinstance(point, (tuple, list)) and len(point) == 2:
                    force, timestamp = point
                    distance = abs(timestamp - current_time)
                    if distance < min_distance:
                        min_distance = distance
                        closest_point = point
            
            if closest_point:
                force, timestamp = closest_point
                
                # 绘制垂直线
                x_pos = axis_start_x + int((timestamp - self.x_min) * x_scale)
                painter.setPen(QPen(QColor(0, 128, 0), 1, Qt.DashLine))
                painter.drawLine(x_pos, axis_y_top, x_pos, axis_y_bottom)
                
                # 绘制水平线
                y_pos = axis_y_bottom - int((force - self.y_min) * y_scale)
                painter.drawLine(axis_start_x, y_pos, axis_end_x, y_pos)
                
                # 绘制数值提示框
                info_text = f"拉力: {force:.1f}mV\n时间: {timestamp:.2f}s"
                text_width = painter.fontMetrics().width(f"拉力: {force:.1f}mV")
                text_height = 40
                
                # 确定提示框位置（避免超出边界）
                box_x = self.cursor_pos.x() + 10 if self.cursor_pos.x() < width - text_width - 30 else self.cursor_pos.x() - text_width - 20
                box_y = max(20, min(height - text_height - 20, self.cursor_pos.y()))
                
                # 绘制背景框
                painter.setBrush(QBrush(QColor(255, 255, 225)))
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawRect(box_x, box_y, text_width + 10, text_height)
                
                # 绘制文本
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawText(box_x + 5, box_y + 15, f"拉力: {force:.1f}mV")
                painter.drawText(box_x + 5, box_y + 35, f"时间: {timestamp:.2f}s")
        
        # 绘制选择矩形
        if self.selection_rect:
            painter.setPen(QPen(QColor(0, 0, 255), 1, Qt.DashLine))
            painter.setBrush(QBrush(QColor(100, 100, 255, 50)))
            painter.drawRect(self.selection_rect)

class SurfaceTensionDiagram(QWidget):
    def __init__(self, parent=None,show_water=False):
        super().__init__(parent)
        self.show_water = show_water  # 是否绘制水面
        self.lift_position = 50  # 升降台位置 (0-100)
        self.weight_count = 0    # 砝码个数
        self.is_ring = False    # 是否显示圆环
        self.is_oscillation_exist = False
        self.setMinimumSize(300, 300)
        self.has_contacted_water = False  # 添加这一行初始化
        self.water_column_broken = False  # 添加这一行初始化
    
    def set_weight_count(self, count, is_ring=False):
        """设置砝码个数或圆环"""
        self.weight_count = count
        self.is_ring = is_ring
        self.update()

    def is_ring_in_water(self):
        """检测圆环是否浸入水中"""
        if not self.is_ring:
            return False
            
        # 计算圆环底部位置 - 跟随传感器位置变化
        ring_bottom = int(325 * 0.2) - 40 + 60 + 30  # 传感器y(升高40) + 连接线高度(延长到60) + 圆环高度
        print(f"ring_bottom: {ring_bottom}")

        # 计算水面位置
        water_top = int(325 * (0.42 + 0.17 * (self.lift_position/100))) - 40  # 升降台y - 水高度
        print(f"water_top: {water_top}")
        return ring_bottom > water_top  # 圆环底部低于水面即为浸入


    def set_lift_position(self, position):
        # 当升降台位置重置到顶部时，清除接触状态
        if position <= 10:  # 假设5%位置是最高点
            if hasattr(self, 'has_contacted_water'):
                del self.has_contacted_water
        
        # 计算砝码/圆环底部位置
        sensor_y = int(325 * 0.2) - 40  # 升高后的传感器位置
        weight_bottom = sensor_y + 60 + 30  # 传感器y + 连接线高度 + 砝码/圆环高度
        
        # 计算升降台应该保持的距离范围
        min_y = weight_bottom + 37.5
        max_y = weight_bottom + 67
        
        # # 将输入位置映射到有效范围
        height = 325
        # print(f'self.height:',self.height())
        min_pos = int(((min_y/height - 0.42) / 0.17) * 100)
        max_pos = int(((max_y/height - 0.42) / 0.17) * 100)
        
        # # 限制位置在有效范围内
        # self.lift_position = max(0, min(100, position))
        # print(f"Lift position: {self.lift_position}")
        # print(f"Widget visible: {self.isVisible()}, enabled: {self.isEnabled()}")  # 应为 True, True
        self.lift_position = max(min_pos, min(max_pos, position))
        # self.lift_position = position
        # self.setAttribute(Qt.WA_OpaquePaintEvent)  # 允许直接绘制
        self.update()
        
    
    def get_show_measure_control(self):
        """获取父窗口链中的show_measure_control参数"""
        # 向上查找父窗口链，直到找到ControlWindow
        parent = self.parent()
        while parent:
            if isinstance(parent, ControlWindow):
                return parent.show_measure_control
            parent = parent.parent()
        return False  # 默认值
    
    def paintEvent(self, event):
        # print(f"Painting at position: {self.lift_position}")
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = 325
        
        # Convert all coordinates to integers
        left_x = int(width * 0.3)
        right_x = int(width * 0.7)
        base_left = int(width * 0.2)
        base_right = int(width * 0.8)
        top_y = int(height * 0.1)
        bottom_y = int(height * 0.7)
        
        # 绘制背景
        painter.fillRect(0, 0, width, height, QColor(240, 240, 240))
        
        # 绘制支架
        painter.setPen(QPen(Qt.black, 3))
        painter.drawLine(left_x, top_y, left_x, bottom_y)  # 左支架
        painter.drawLine(right_x, top_y, right_x, bottom_y)  # 右支架
        painter.drawLine(base_left, bottom_y, base_right, bottom_y)  # 底座
        
        # 绘制拉力传感器 - 升高40像素
        sensor_y = int(height * 0.2) - 40  # 修改这里，升高40像素
        sensor_width = int(width * 0.2)
        sensor_x = int(width * 0.4)
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(sensor_x, sensor_y, sensor_width, 20)  # 传感器主体
        painter.drawLine(int(width*0.5), sensor_y+20, int(width*0.5), sensor_y+60)  # 修改这里，连接线延长到60像素
        
        # 绘制砝码或圆环 - 位置相应调整
        weight_y = sensor_y + 60  # 修改这里，跟随传感器位置变化
        weight_width = int(width * 0.2)
        weight_x = int(width * 0.4)
        
        
        # 绘制升降台 - 修改位置计算以确保与砝码/圆环保持33-67像素距离
        weight_bottom = weight_y + 30  # 砝码/圆环底部位置
        # min_lift_y = weight_bottom + 33  # 最小距离33像素
        # max_lift_y = weight_bottom + 67  # 最大距离67像素

        lift_y = int(height * (0.42 + 0.17 * (self.lift_position/100)))
        lift_width = int(width * 0.6)
        lift_x = int(width * 0.2)
        painter.setBrush(QBrush(QColor(150, 150, 150)))
        painter.drawRect(lift_x, lift_y, lift_width, 15)
        
        if self.show_water:
            # 绘制水（蓝色方形）
            water_height = 40
            water_top = lift_y - water_height
            water_width = int(width * 0.4)
            water_x = int(width * 0.3)
            painter.setBrush(QBrush(QColor(100, 100, 255, 200)))
            painter.drawRect(water_x, water_top, water_width, water_height)
            
            # 绘制水面（顶部一条线）
            painter.setPen(QPen(QColor(50, 50, 200), 2))
            painter.drawLine(water_x, water_top, water_x + water_width, water_top)
        
        # 绘制砝码或圆环
        if self.weight_count >= 3:
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.drawRect(weight_x, weight_y, weight_width, 30)
            
            # 计算浸入水中的高度（限制最多7像素）
            if self.show_water:
                submerged_height = min(7, max(0, (weight_y + 30) - water_top))
                
                # 绘制浸入水中的部分
                if submerged_height > 0:
                    painter.setBrush(QBrush(QColor(150, 150, 200)))
                    painter.drawRect(weight_x, weight_y + (30 - submerged_height), 
                                weight_width, submerged_height)
                    self.has_contacted_water = True  # 标记已接触过水面
                    self.water_column_broken = False  # 重置断裂状态
            
                # 只有当圆环曾经接触过水面且水柱未断裂时才显示水柱
                if (hasattr(self, 'has_contacted_water') and self.has_contacted_water and 
                    self.is_ring and not getattr(self, 'water_column_broken', False)):
                    
                    # 计算圆环底部与水面的距离
                    distance = water_top - (weight_y + 30)
                    
                    if distance > 23:  # 水柱断裂
                        self.water_column_broken = True
                        self.is_oscillation_exist = True
                    elif 0 < distance <= 23:  # 显示水柱
                        # 计算梯形水柱参数
                        water_column_top = weight_y + 30
                        water_column_height = min(23, distance)
                        
                        # 上边沿与圆环同宽
                        top_width = weight_width
                        
                        # 下边沿比上边沿宽10%（但最小保持5像素）
                        width_increase = max(10, top_width * 0.1)  # 至少增加2像素
                        bottom_width = top_width + width_increase

                        # 计算梯形四个角点（居中显示）
                        points = [
                            QPointF(weight_x - width_increase/4, water_column_top),  # 上边左侧点（较窄）
                            QPointF(weight_x + weight_width + width_increase/4, water_column_top),  # 上边右侧点（较窄）
                            QPointF(weight_x + weight_width + width_increase/2, water_column_top + water_column_height),  # 下边右侧点（较宽）
                            QPointF(weight_x - width_increase/2, water_column_top + water_column_height)  # 下边左侧点（较宽）
                        ]
                        
                        # 绘制梯形水柱
                        painter.setBrush(QBrush(QColor(100, 100, 255, 180)))
                        painter.setPen(QPen(QColor(50, 50, 200, 180), 1))
                        painter.drawPolygon(QPolygonF(points))
        
        # 绘制标签
        painter.setPen(QPen(Qt.black, 1))
        painter.drawText(int(width*0.5)-30, sensor_y-5, "拉力传感器")
        show_measure_control = self.get_show_measure_control()
        if self.weight_count >= 3:
            painter.drawText(weight_x, weight_y+0, "圆环")
            if show_measure_control == False:
                painter.drawText(weight_x+60, weight_y+0, f"砝码 x{self.weight_count-3}")
        if(self.show_water):
            painter.drawText(lift_x, lift_y-5, "升降台")
            painter.drawText(water_x, water_top-5, "液面")

class SurfaceTensionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.using_ring = False
        
        self.setWindowTitle("FD-NST-D 液体表面张力系数测量仪")
        # 使用绝对布局，设置固定窗口大小
        self.setFixedSize(852, 326)  # 与背景图片大小一致
        
        # 设置窗口标志
        self.setWindowFlags(self.windowFlags() & 
                          ~Qt.WindowMaximizeButtonHint & 
                          ~Qt.WindowMinimizeButtonHint)
        
        # 直接设置窗口位置（如果需要）
        # self.setGeometry(100, 100, 852, 326)
        
        self.querying_data = False
        current_group_data = None
        self.current_group = 1
        self.current_point_index = 0
        self.background_image = "表面张力面板.png"
        
        # 在主窗口的__init__中添加
        # self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        # 设置初始大小和宽高比
        # self.initial_width = 1084
        # self.initial_height = 415
        # self.aspect_ratio = self.initial_width / self.initial_height
        # self.setMinimumSize(852, int(852 / self.aspect_ratio))
        # self.setMaximumSize(852, int(852 / self.aspect_ratio))

        # 设置窗口初始大小
        # self.resize(self.initial_width, self.initial_height)
        
        # 存储原始大小用于缩放计算
        # self.original_size = QSize(self.initial_width, self.initial_height)

        # # 替换原来的setFixedSize调用，改为以下两行：
        
        # self.original_size = QSize(852, 326)  # 存储原始大小用于缩放计算
        
        self.set_background(self.background_image)
        # self.control_window = ControlWindow(self)
        # self.control_window.show()
        # self.tab_window = TabWindow(self)
        # self.tab_window.show()
        self.control_window = ControlWindow(self, show_measure_control=False)  # 默认显示传感器定标模式
        self.control_window.show()
        # # 创建或显示校准图表
        # self.calibration_chart = CalibrationChartWindow(self)
        # # 程序启动时显示折线图窗口
        # self.calibration_chart.show()
        # if not self.calibration_chart:
        #     self.calibration_chart = CalibrationChartWindow(self)
        # self.calibration_chart.show()

        # 状态变量
        self.last_sensitivity = 0.0  # 添加这个变量来存储最新的灵敏度值
        self.random_force= random.uniform(-10, 10)
        self.min_speed= 1.5
        self.lift_speed = self.min_speed
        # self.excel_data = self.load_excel_data()  # 加载Excel数据
        self.current_selection = 0
        self.interval = 0.2
        self.current_measurement_interval = self.interval
        self.adjusting_interval = False
        self.calibrating_sensor = False
        self.measuring_tension = False
        self.zero_dial_value = 0
        self.weight_count = 0
        self.measurement_count = 1
        self.data_points = []
        self.data_groups = []
        
        # 定时器初始化
        self.lift_timer = QTimer()
        self.lift_timer.timeout.connect(self.animate_lift)
        self.current_direction = 1
        self.collection_timer = QTimer()
        self.collection_timer.timeout.connect(self.collect_data)
        
        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QHBoxLayout()
        main_widget.setLayout(self.main_layout)
        
        # 初始化界面区域
        self.init_ui_components()

        # self.init_buttons()  # 再初始化按钮
        
        self.update_selection_arrow()

        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                
                border: 1px solid gray;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QFrame {
                border: 0px solid #ccc;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton {
                min-width: 60px;
                margin: 5px;
            }
            QTextEdit {
                font-size: 16px;
                padding: 20px;
            }
            QDial {
                min-width: 70px;
                min-height: 80px;
            }
        """)

         # 初始化液体类型和对应的数据文件
        self.current_liquid = "water"
        self.liquid_data_files = {
            "water": "纯水测量数据.xlsx",
            "ethanol": "乙醇测量数据.xlsx", 
            "glycerol": "甘油测量数据.xlsx"
        }
        self.excel_data = self.load_excel_data()  # 初始加载纯水数据

        # 强制立即布局计算
        # self.layout().activate()
        # self.updateGeometry()

        # 或者添加延迟布局更新
        QTimer.singleShot(0, lambda: self.updateGeometry())

    def init_ui_components(self):
        """初始化所有UI控件（使用绝对位置）"""
        # ========== 左侧区域 ==========
        
        # 1. 左侧显示框（四个栏目）
        self.display_box = QGroupBox(self)
        self.display_box.setGeometry(20, 25, 270, 200)  # x, y, width, height
        self.display_box.setStyleSheet("""
            QGroupBox {
                border: 0px solid transparent;
                background: transparent;
            }
        """)
        
        # 四个栏目标签（使用绝对位置在display_box内）
        self.items = [
            f"采集间隔：{self.interval}s",
            "传感器定标",
            "表面张力测量",
            "数据查询"
        ]
        
        self.item_labels = []
        label_positions = [
            (10, 10, 250, 30),   # 标签1位置
            (10, 45, 250, 30),   # 标签2位置
            (10, 80, 250, 30),   # 标签3位置
            (10, 115, 250, 30)   # 标签4位置
        ]
        
        for i, (text, pos) in enumerate(zip(self.items, label_positions)):
            label = QLabel(text, self.display_box)
            label.setGeometry(pos[0], pos[1], pos[2], pos[3])
            label.setStyleSheet("""
                font-size: 15px;
                padding: 1px;
                border: 1px solid #ccc;
                background-color: white;
            """)
            self.item_labels.append(label)
        
        # 2. 拉力显示框（传感器定标时显示）
        self.force_display = QTextEdit(self.display_box)
        self.force_display.setGeometry(10, 150, 250, 40)
        self.force_display.setText("当前拉力：0.0mV")
        self.force_display.setAlignment(Qt.AlignCenter)
        self.force_display.setReadOnly(True)
        self.force_display.hide()
        
        # 3. 测量显示框（表面张力测量时显示）
        self.tension_display = QLabel("No.1 拉力：0mV", self.display_box)
        self.tension_display.setGeometry(10, 150, 250, 30)
        self.tension_display.setAlignment(Qt.AlignCenter)
        self.tension_display.hide()
        self.tension_display.setStyleSheet("""
            font-size: 16px;
            padding: 0px;
            margin: 0;
            border: 1px solid #ccc;
            background-color: white;
        """)
        
        # 4. 数据点阵显示
        self.data_display = DataPointDisplay(self.display_box)
        self.data_display.setGeometry(10, 185, 250, 10)  # 初始小高度，后续会调整
        self.data_display.hide()
        
        # ========== 中间区域（调零旋钮） ==========
        
        # 中间旋钮
        self.zero_dial = QDial(self)
        self.zero_dial.setGeometry(385, 125, 50, 50)  # 居中位置
        self.zero_dial.setRange(-100, 100)
        self.zero_dial.setValue(self.zero_dial_value)
        self.zero_dial.setNotchesVisible(True)
        self.zero_dial.valueChanged.connect(self.on_dial_changed)
        
        # 旋钮标签
        self.zero_label = QLabel("", self)
        self.zero_label.setGeometry(370, 180, 80, 30)
        self.zero_label.setAlignment(Qt.AlignCenter)
        self.zero_label.setStyleSheet("font-size: 16px;")
        
        # ========== 右侧区域 ==========
        
        # 1. 右侧旋钮（速度调节）
        self.speed_dial = QDial(self)
        self.speed_dial.setGeometry(560, 120, 50, 50)
        self.speed_dial.setRange(1, 5)
        self.speed_dial.setValue(1)
        self.speed_dial.setNotchesVisible(True)
        self.speed_dial.valueChanged.connect(self.update_lift_speed)
        
        # 2. 导航按钮（使用绝对位置）
        button_style = """
            QPushButton {
                background: transparent;
                min-width: 90px;
                min-height: 40px;
                font-size: 16px;
                border: 0px solid #ccc;
            }
        """
        
        # 向上按钮
        self.nav_up_btn = QPushButton("上", self)
        self.nav_up_btn.setGeometry(650, 40, 90, 40)
        self.nav_up_btn.setStyleSheet(button_style)
        self.nav_up_btn.clicked.connect(self.on_up_clicked)
        
        # 确定按钮
        self.nav_ok_btn = QPushButton("确定", self)
        self.nav_ok_btn.setGeometry(750, 40, 90, 40)
        self.nav_ok_btn.setStyleSheet(button_style)
        self.nav_ok_btn.clicked.connect(self.on_ok_clicked)
        
        # 向下按钮
        self.nav_down_btn = QPushButton("下", self)
        self.nav_down_btn.setGeometry(650, 100, 90, 40)
        self.nav_down_btn.setStyleSheet(button_style)
        self.nav_down_btn.clicked.connect(self.on_down_clicked)
        
        # 返回按钮
        self.nav_back_btn = QPushButton("返回", self)
        self.nav_back_btn.setGeometry(750, 100, 90, 40)
        self.nav_back_btn.setStyleSheet(button_style)
        self.nav_back_btn.clicked.connect(self.on_back_clicked)
        
        # 3. 升降台控制按钮和箭头
        # 向上按钮
        self.lift_up_btn = QPushButton("向上", self)
        self.lift_up_btn.setGeometry(650, 160, 90, 40)
        self.lift_up_btn.setCheckable(True)
        self.lift_up_btn.setStyleSheet(button_style)
        self.lift_up_btn.clicked.connect(lambda: self.set_lift_direction(0))
        
        # 停止按钮和箭头容器
        self.stop_btn_container = QWidget(self)
        self.stop_btn_container.setGeometry(650, 210, 190, 60)
        
        # 停止按钮
        self.stop_btn = QPushButton("停止", self.stop_btn_container)
        self.stop_btn.setGeometry(0, 0, 100, 40)
        self.stop_btn.setCheckable(True)
        self.stop_btn.setChecked(True)
        self.stop_btn.setStyleSheet(button_style)
        self.stop_btn.clicked.connect(lambda: self.set_lift_direction(1))
        
        # 箭头
        self.arrow_widget = ArrowWidget(self.stop_btn_container)
        self.arrow_widget.setGeometry(110, 0, 50, 50)
        
        # 向下按钮
        self.lift_down_btn = QPushButton("向下", self)
        self.lift_down_btn.setGeometry(750, 160, 90, 40)
        self.lift_down_btn.setCheckable(True)
        self.lift_down_btn.setStyleSheet(button_style)
        self.lift_down_btn.clicked.connect(lambda: self.set_lift_direction(2))

    def closeEvent(self, event):
        """使用Qt内置方法关闭所有窗口"""
        QApplication.closeAllWindows()
        super().closeEvent(event)

    def add_random_variation(self, value):
        """为测量值添加0-0.5%的随机波动"""
        variation = random.uniform(-0.002, 0.002)  # -0.2%到+0.2%
        return value * (1 + variation)

    def raise_window(self):
        """仅提升主窗口"""
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event):
        """点击主窗口时，将其置顶"""
        self.raise_()  # 将主窗口置于最上层
        self.activateWindow()  # 激活窗口（获取焦点）
        super().mousePressEvent(event)  # 调用父类方法处理其他事件

    # def init_left_area(self):
    #     """初始化左侧区域"""
    #     # 左侧区域（分为左右两部分）
    #     self.left_area = QWidget()
    #     self.left_area_layout = QHBoxLayout()
    #     self.left_area.setLayout(self.left_area_layout)

    #    # 左侧显示框
    #     self.left_display_frame = QFrame()
    #     self.left_display_frame.setFrameShape(QFrame.StyledPanel)
    #     self.left_display_layout = QVBoxLayout()
    #     self.left_display_layout.setSpacing(2)  # 将间距设置为0
    #     self.left_display_layout.setContentsMargins(20, 10, 0, 55)  # 设置整体边距
    #     self.left_display_frame.setLayout(self.left_display_layout)
        
    #     # 左侧显示框内容
    #     self.display_box = QGroupBox("")
    #     # 设置大小
    #     self.display_box.setFixedSize(270, 200)  # 固定大小
    #     # self.display_box.resize(280,200)
        
    #     #无边框
    #     self.display_box.setStyleSheet("""
    #         QGroupBox {
    #             border: 0px solid transparent;  /* 无边框 */
    #             margin-top: 10px;
    #         }
    #         QGroupBox::title {
    #             subcontrol-origin: margin;
    #             left: 0px;
    #             padding: 0 3px;
    #         }
    #     """)
    #     self.display_layout = QVBoxLayout()
    #     self.display_layout.setSpacing(0)  # 减少组件间距
        
    #     # 四个栏目
    #     self.items = [
    #         f"采集间隔：{self.interval}s",
    #         "传感器定标",
    #         "表面张力测量",
    #         "数据查询"
    #     ]
        
    #     # 存储所有的栏目标签
    #     self.item_labels = []
        
    #     for i, item in enumerate(self.items):
    #         label = QLabel(item)
    #         label.setStyleSheet("""
    #             font-size: 10px; 
    #             padding: 0px; 
    #             border-bottom: 0px solid #ccc;
    #         """)
    #         self.display_layout.addWidget(label)
    #         self.item_labels.append(label)
        
    #     # 传感器定标时显示的文本框
    #     self.force_display = QTextEdit()
    #     self.force_display.setText("当前拉力：0.0mV")
    #     self.force_display.setAlignment(Qt.AlignCenter)
    #     self.force_display.setReadOnly(True)
    #     self.force_display.hide()
        
    #     # 表面张力测量时显示的文本框 - 高度设置为1/3
    #     # self.tension_display = QTextEdit()
    #     # self.tension_display.setText("No.1 拉力：0mV")
    #     # self.tension_display.setAlignment(Qt.AlignCenter)
    #     # self.tension_display.setReadOnly(True)
    #     # self.tension_display.hide()
    #     # self.tension_display.setMaximumHeight(30)  # 限制最大高度
    #     # self.tension_display.setStyleSheet("""
    #     #     font-size: 16px;  /* 减小字体 */
    #     #     padding: 0px;     /* 减少内边距 */
    #     #     margin: 0;        /* 移除外边距 */
    #     # """)    
    #     # 改为使用 QLabel：
    #     self.tension_display = QLabel("No.1 拉力：0mV")
    #     self.tension_display.setAlignment(Qt.AlignCenter)
    #     self.tension_display.hide()
    #     self.tension_display.setFixedHeight(16)  # 固定高度
    #     self.tension_display.setStyleSheet("""
    #         font-size: 16px;
    #         padding: 0px;
    #         margin: 0;
    #         border: 0px solid #ccc;
    #         background-color: white;
    #     """)
    #     # 数据点阵显示 - 高度设置为2/3
    #     self.data_display = DataPointDisplay()
    #     self.data_display.hide()
    #     self.data_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        
    #     # 创建测量模式的专用布局
    #     self.measurement_layout = QVBoxLayout()
    #     self.measurement_layout.addWidget(self.tension_display, 1)  # 1份高度
    #     self.measurement_layout.addWidget(self.data_display, 6)     # 2份高度
    #     self.measurement_layout.setContentsMargins(0, 0, 0, 10)  # 添加边距
        
    #     # 将测量布局放入一个容器中
    #     self.measurement_container = QWidget()
    #     self.measurement_container.setLayout(self.measurement_layout)
    #     # self.measurement_container.setStyleSheet("background-color: #f0f0f0;")  # 设置背景色
    #     self.measurement_container.hide()
        
    #     # 修改这里：将栏目标签放入一个单独的容器中
    #     self.labels_container = QWidget()
    #     self.labels_container.setLayout(self.display_layout)
        
    #     self.display_box_layout = QVBoxLayout()
    #     self.display_box_layout.addWidget(self.labels_container)
    #     self.display_box_layout.addWidget(self.force_display)
    #     self.display_box_layout.addWidget(self.measurement_container)
    #     self.display_box.setLayout(self.display_box_layout)
    #     # 设置数据点阵的最小尺寸
    #     self.data_display.setMinimumSize(260, 80)  # 增大宽度和高度

        
    #     self.left_display_layout.addWidget(self.display_box)

    #     # 左侧控制按钮区域
    #     self.left_control_frame = QFrame()
    #     self.left_control_layout = QVBoxLayout()
    #     self.left_control_frame.setLayout(self.left_control_layout)
        
    #     # # 添加提示文本
    #     # self.weight_hint_label = QLabel("每个砝码重0.5g")
    #     # self.weight_hint_label.setAlignment(Qt.AlignCenter)
    #     # self.weight_hint_label.setStyleSheet("font-size: 12px; color: #666;")
        
    #     # weight_info_layout.addWidget(self.weight_count_label)
    #     # weight_info_layout.addWidget(self.weight_hint_label)
        
    #     # self.weight_layout.addWidget(self.remove_weight_btn)
    #     # self.weight_layout.addLayout(weight_info_layout)  # 使用布局容器替代单独的标签
    #     # self.weight_layout.addWidget(self.add_weight_btn)
    #     # self.weight_control.setLayout(self.weight_layout)
        
    #     # 修改导航按钮区域布局
    #     self.nav_control = QGroupBox("")
    #     self.nav_control.setStyleSheet("""
    #         QGroupBox {
    #             border: 0px solid transparent;
    #             margin-top: 10px;
    #         }
    #         QGroupBox::title {
    #             subcontrol-origin: margin;
    #             left: 10px;
    #             padding: 0 3px;
    #         }
    #     """)
        
    #      # 使用网格布局来精确控制按钮位置
    #     self.nav_layout = QGridLayout()
    #     self.nav_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
    #     self.nav_layout.setVerticalSpacing(45)  # 设置垂直间距为15像素
    #     self.nav_layout.setHorizontalSpacing(20)  # 设置水平间距
        
    #     # 创建按钮并设置样式
    #     button_style = """
    #         QPushButton {
    #             font-size: 16px;
    #             min-width: 45px;
    #             min-height: 60px;
    #             border: 0px solid #ccc;
    #         }
    #     """
        
    #     # 添加空白行来下移按钮
    #     # selayout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding), 0, 0)  # 第一行第一列
    #     # 向上按钮 - 左上角 (0,0)
    #     self.up_btn = QPushButton("")
    #     self.up_btn.setStyleSheet(button_style)
    #     self.up_btn.clicked.connect(self.on_up_clicked)
    #     self.nav_layout.addWidget(self.up_btn, 0, 0)  # 第一行第一列
        
    #     # 向下按钮 - 左下角 (1,0)
    #     self.down_btn = QPushButton("")
    #     self.down_btn.setStyleSheet(button_style)
    #     self.down_btn.clicked.connect(self.on_down_clicked)
    #     self.nav_layout.addWidget(self.down_btn, 1, 0)  # 第二行第一列
        
    #     # 确定按钮 - 右上角 (0,1)
    #     self.ok_btn = QPushButton("")
    #     self.ok_btn.setStyleSheet(button_style)
    #     self.ok_btn.clicked.connect(self.on_ok_clicked)
    #     self.nav_layout.addWidget(self.ok_btn, 0, 1)  # 第一行第二列
        
    #     # 返回按钮 - 右下角 (1,1)
    #     self.back_btn = QPushButton("")
    #     self.back_btn.setStyleSheet(button_style)
    #     self.back_btn.clicked.connect(self.on_back_clicked)
    #     self.nav_layout.addWidget(self.back_btn, 1, 1)  # 第二行第二列
        
    #     # 添加垂直间距使"向上"和"确定"按钮下移
    #     self.nav_layout.setRowMinimumHeight(0, 30)  # 第一行最小高度60像素
    #     self.nav_layout.setRowMinimumHeight(1, 30)  # 第二行保持原高度

    #     # 添加拉伸项使按钮靠边
    #     self.nav_layout.setContentsMargins(0, 40, 0, 60)  # 左 20px，上 10px，右 20px，下 10px
    #     # self.nav_layout.setSpacing(0)  # 按钮间距 10px
    #     self.nav_layout.setColumnStretch(0, 1)  # 第一列可拉伸
    #     self.nav_layout.setColumnStretch(1, 1)  # 第二列可拉伸
    #     self.nav_layout.setRowStretch(0, 1)    # 第一行可拉伸
    #     self.nav_layout.setRowStretch(1, 1)    # 第二行可拉伸
        
    #     self.nav_control.setLayout(self.nav_layout)
        
    #     # self.left_control_layout.addWidget(self.weight_control)
    #     self.left_control_layout.addWidget(self.nav_control)
        
    #     # 将左右两部分添加到左侧区域布局
    #     self.left_area_layout.addWidget(self.left_display_frame, 510)  # 显示区域占2/3
    #     self.left_area_layout.addWidget(self.left_control_frame, 268)  # 控制区域占1/3

    # def init_center_area(self):
    #     """初始化中间区域"""
    #     self.center_frame = QFrame()
    #     self.center_frame.setFrameShape(QFrame.StyledPanel)
    #     self.center_layout = QVBoxLayout()
    #     self.center_frame.setLayout(self.center_layout)
        
    #     # 中间旋钮 - 范围-100到100，对应±10mV
    #     self.zero_dial = QDial()
    #     self.zero_dial.setRange(-100, 100)
    #     self.zero_dial.setValue(self.zero_dial_value)  # 使用保存的值初始化
    #     self.zero_dial.setNotchesVisible(True)
    #     self.zero_dial.setFixedSize(50, 50)
    #     self.zero_dial.valueChanged.connect(self.on_dial_changed)
        
    #     self.zero_label = QLabel("")
    #     self.zero_label.setAlignment(Qt.AlignCenter)
    #     self.zero_label.setStyleSheet("font-size: 16px;")
        
    #     self.center_layout.setContentsMargins(0, 0, 5, 10)  # 移除主布局边距
    #     self.center_layout.addStretch(19)
    #     self.center_layout.addWidget(self.zero_dial, 2, Qt.AlignCenter)
    #     self.center_layout.addWidget(self.zero_label, 2, Qt.AlignCenter)
    #     self.center_layout.addStretch(2) 

    # # def on_liquid_selected(self, liquid_type):
    # #     """液体选择按钮点击事件"""
    # #     self.current_liquid = liquid_type
    # #     self.excel_data = self.load_excel_data()  # 重新加载对应液体的数据
        
    # #     # 更新按钮状态
    # #     self.water_btn.setChecked(liquid_type == "water")
    # #     self.ethanol_btn.setChecked(liquid_type == "ethanol")
    # #     self.glycerol_btn.setChecked(liquid_type == "glycerol")
        
    # #     # 如果当前在测量模式，更新拉力显示
    # #     if self.measuring_tension:
    # #         self.update_tension_display()
    

    # def init_right_area(self):
    #     """初始化右侧区域（旋钮在左，按钮和箭头在右）"""
    #     self.right_frame = QWidget()
    #     self.right_layout = QHBoxLayout()  # 主布局水平排列
    #     self.right_frame.setLayout(self.right_layout)
    #     self.right_layout.setContentsMargins(0, 0, 0, 0)  # 移除主布局边距
    #     self.right_layout.setSpacing(-60)  # 缩小左右区域间距为10px

    #     # ===== 1. 左侧区域 - 速率调节旋钮 =====
    #     left_control_panel = QWidget()
    #     left_layout = QVBoxLayout()
    #     left_control_panel.setLayout(left_layout)
    #     left_layout.setContentsMargins(22, 0, 2, 0)  # 增加右margin使旋钮右移

    #     # 旋钮和标签
    #     self.speed_dial = QDial()
    #     self.speed_dial.setRange(1, 5)
    #     self.speed_dial.setValue(1)
    #     self.speed_dial.setNotchesVisible(True)
    #     # self.speed_dial.setFixedSize(20, 20)
    #     self.speed_dial.valueChanged.connect(self.update_lift_speed)

    #     left_layout.addStretch(18)
    #     left_layout.addWidget(self.speed_dial, 0, Qt.AlignCenter)
    #     left_layout.addStretch(7)

    #     # ===== 2. 右侧区域 - 按钮和箭头合并 =====
    #     btn_arrow_panel = QWidget()
    #     btn_arrow_layout = QHBoxLayout()
    #     btn_arrow_panel.setLayout(btn_arrow_layout)
    #     btn_arrow_layout.setContentsMargins(0, 0, 30, 0)

    #     # 按钮面板（垂直布局）
    #     btn_panel = QWidget()
    #     btn_layout = QVBoxLayout()
    #     btn_panel.setLayout(btn_layout)
    #     btn_layout.setContentsMargins(0, 0, 0, 0)
    #     btn_layout.setSpacing(5)  # 增大按钮间距

    #     # 按钮样式（统一大小）上升下降停止
    #     button_style = """
    #         QPushButton {
    #             background: transparent;
    #             min-width: 90px;
    #             min-height: 40px;
    #             max-width: 90px;
    #             max-height: 40px;
    #             font-size: 16px;
    #             border: 0px solid #ccc;
    #         }
    #     """

    #     # 向上按钮
    #     self.up_btn = QPushButton("")
    #     self.up_btn.setCheckable(True)
    #     self.up_btn.setStyleSheet(button_style)
    #     self.up_btn.clicked.connect(lambda: self.set_lift_direction(0))

    #     # 停止按钮容器（使用覆盖布局）
    #     self.stop_btn_container = QWidget()
    #     self.stop_btn_container.setFixedSize(110, 60)  # 容器稍大以便放置箭头
        
    #     # 使用水平布局将按钮和箭头并排
    #     stop_layout = QHBoxLayout(self.stop_btn_container)
    #     stop_layout.setContentsMargins(0, 0, 0, 0)
        
    #     # 停止按钮（左对齐）
    #     self.stop_btn = QPushButton("")
    #     self.stop_btn.setCheckable(True)
    #     self.stop_btn.setChecked(True)
    #     self.stop_btn.setStyleSheet(button_style)
    #     self.stop_btn.clicked.connect(lambda: self.set_lift_direction(1))
    #     self.stop_btn.setFixedSize(100, 30)
        
    #     # 箭头（右对齐，向右移动）
    #     self.arrow_widget = ArrowWidget()
    #     self.arrow_widget.setFixedSize(50, 50)
    #     self.arrow_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        
    #     # 将按钮和箭头添加到水平布局
    #     stop_layout.addWidget(self.stop_btn)
    #     stop_layout.addWidget(self.arrow_widget)
    #     stop_layout.addSpacing(36)  # 调整为-160（原为140），这会向左移动箭头

    #     # 向下按钮
    #     self.down_btn = QPushButton("")
    #     self.down_btn.setCheckable(True)
    #     self.down_btn.setStyleSheet(button_style)
    #     self.down_btn.clicked.connect(lambda: self.set_lift_direction(2))

    #     # 添加到垂直布局
    #     btn_layout.addStretch(15)
    #     btn_layout.addWidget(self.up_btn, 0, Qt.AlignCenter)
    #     btn_layout.addWidget(self.stop_btn_container, 0, Qt.AlignCenter)
    #     btn_layout.addWidget(self.down_btn, 0, Qt.AlignCenter)
    #     btn_layout.addStretch(7)

    #     # 将按钮面板添加到主布局
    #     btn_arrow_layout.addWidget(btn_panel)

    #     # ===== 3. 将左右两部分添加到主布局 =====
    #     self.right_layout.addWidget(left_control_panel, 16)
    #     self.right_layout.addWidget(btn_arrow_panel, 23)

    #     # 将三部分添加到主布局
    #     self.main_layout.addWidget(self.left_area, 750)
    #     self.main_layout.addWidget(self.center_frame, 150)
        # self.main_layout.addWidget(self.right_frame, 390)
    
    def get_data_path(self, filename):
        """获取资源文件路径（适配打包和开发环境）"""
        try:
            # 判断是否是打包后的环境
            if getattr(sys, 'frozen', False):
                # 打包后的情况 - 使用sys._MEIPASS获取临时解压目录
                base_dir = sys._MEIPASS
            else:
                # 开发环境 - 使用脚本所在目录
                base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 构建data文件夹路径
            data_dir = os.path.join(base_dir, "data")
            
            # 检查文件是否存在
            full_path = os.path.join(data_dir, filename)
            if os.path.exists(full_path):
                return full_path
            
            # 文件不存在时的备选方案
            print(f"警告：文件 {filename} 在以下路径未找到: {full_path}")
            return filename  # 返回原文件名作为后备
            
        except Exception as e:
            print(f"获取资源路径出错: {e}")
            return filename

    def set_background(self, image_name):
        """设置背景图片（从data文件夹导入）"""
        full_image_path = self.get_data_path(image_name)
        
        if not os.path.exists(full_image_path):
            print(f"警告：背景图片不存在 - {full_image_path}")
            return

        palette = QPalette()
        try:
            pixmap = QPixmap(full_image_path)
            if pixmap.isNull():
                raise ValueError("无法加载图片文件")
                
            # 缩放图片以适应窗口大小
            scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            palette.setBrush(QPalette.Background, QBrush(scaled_pixmap))
            self.setPalette(palette)
        except Exception as e:
            print(f"加载背景图片出错: {e}")

    # def resizeEvent(self, event):
    #     """保持窗口宽高比不变的resize事件处理"""
    #     # 计算新尺寸
    #     new_width = event.size().width()
    #     new_height = event.size().height()
        
    #     # 计算期望的高度（基于宽度）
    #     expected_height = int(new_width / self.aspect_ratio)
        
    #     # 如果实际高度与期望高度不符，则调整
    #     if abs(new_height - expected_height) > 2:  # 允许2像素的误差
    #         # 保持宽度不变，调整高度
    #         self.resize(new_width, expected_height)
    #         return  # 直接返回，避免无限循环
            
    #     # 调用父类方法
    #     super().resizeEvent(event)
        
    #     # 更新背景和缩放内容
    #     self.set_background(self.background_image)
    #     self.scale_content()

    # def scale_content(self):
    #     """按比例缩放所有内容"""
    #     if not hasattr(self, 'original_size'):
    #         return
            
    #     # 计算缩放因子（基于宽度或高度）
    #     scale = self.width() / self.original_size.width()
        
    #     # 缩放display_box
    #     if hasattr(self, 'display_box'):
    #         original_display_size = self.display_box.property("original_size")
    #         if original_display_size is None:
    #             # 第一次记录原始大小
    #             self.display_box.setProperty("original_size", QSize(520, 320))
    #             original_display_size = QSize(520, 320)
            
    #         new_width = int(original_display_size.width() * scale*0.65)
    #         new_height = int(original_display_size.height() * scale*0.65)
    #         self.display_box.setFixedSize(new_width, new_height)

    #     # 缩放所有子控件
    #     for child in self.findChildren(QWidget):
    #         if child != self and not isinstance(child, ControlWindow):  # 不缩放自己和控制面板
    #             original_pos = child.property("original_pos")
    #             original_size = child.property("original_size")
                
    #             if original_pos is None:
    #                 # 第一次记录原始位置和大小
    #                 child.setProperty("original_pos", child.pos())
    #                 child.setProperty("original_size", child.size())
    #                 original_pos = child.pos()
    #                 original_size = child.size()
                
    #             # 计算新位置和大小
    #             new_x = int(original_pos.x() * scale)
    #             new_y = int(original_pos.y() * scale)
    #             new_width = int(original_size.width() * scale)
    #             new_height = int(original_size.height() * scale)
                
    #             # 应用新位置和大小
    #             child.move(new_x, new_y)
    #             child.resize(new_width, new_height)
                
    #             # 缩放字体大小
    #             font = child.font()
    #             original_font_size = child.property("original_font_size")
    #             if original_font_size is None:
    #                 child.setProperty("original_font_size", font.pointSize())
    #                 original_font_size = font.pointSize()
                
    #             new_font_size = int(original_font_size * scale)
    #             font.setPointSize(max(8, new_font_size))  # 设置最小字体大小
    #             child.setFont(font)

    def load_excel_data(self):
        """从data文件夹加载Excel拉力数据"""
        try:
            # 获取当前选择的液体对应的数据文件
            filename = self.liquid_data_files.get(self.current_liquid, "纯水测量数据.xlsx")
            
            # 获取完整文件路径
            excel_path = self.get_data_path(filename)
            
            if not os.path.exists(excel_path):
                print(f"文件 {filename} 不存在于data文件夹中，路径: {excel_path}")
                # 尝试让用户选择文件
                excel_path = self.get_excel_path_from_dialog()
                if not excel_path:
                    return []
            
            df = pd.read_excel(excel_path)
            # 为所有电压值添加0.5%以内的比例误差
            scale_error = 1 + random.uniform(-0.005, 0.005)
            df['电压(mV)'] = df['电压(mV)'] * scale_error
            return list(zip(df['时间(S)'], df['电压(mV)']))
            
        except Exception as e:
            print(f"加载Excel数据失败: {e}")
            return []

    def get_excel_path_from_dialog(self):
        """通过对话框获取Excel路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择拉力曲线数据文件",
            "",
            "Excel文件 (*.xlsx *.xls);;所有文件 (*)"
        )
        return file_path
    
    def update_weight_controls(self):
        """Update the visibility of weight control buttons"""
        if self.using_ring:
            self.add_weight_btn.hide()
            self.remove_weight_btn.hide()
            self.weight_count_label.hide()
            self.weight_hint_label.hide()  # Add this line to hide the hint
            # self.replace_with_ring_btn.hide()
            self.replace_with_weights_btn.show()
        else:
            self.add_weight_btn.show()
            self.remove_weight_btn.show()
            self.weight_count_label.show()
            self.weight_hint_label.show()  # Add this line to show the hint
            # self.replace_with_ring_btn.show()
            self.replace_with_weights_btn.hide()
        
        self.weight_count_label.setText(f"砝码个数: {self.weight_count}")

    def update_lift_speed(self, speed_value):
        """更新升降台速度 - 新速度计算逻辑"""
        # 计算速度值：每2格增加1，最小1，最大5
        speed = speed_value*self.min_speed
        
        # 设置实际速度（保证至少为1），并乘以1.5倍速
        self.lift_speed = max(1, speed) 
        
        # 更新标签显示
        # self.speed_label.setText(f"速率调节\n({int(self.lift_speed/self.min_speed)})")  # 显示原始值
        
        # 如果当前正在移动，则更新速度
        if self.current_direction != 1:  # 如果不是停止状态
            self.lift_timer.start(50)  # 重新启动定时器以应用新速度
       

    def enter_query_mode(self):
        """进入数据查询模式"""
        self.querying_data = True
        
        # 隐藏所有栏目
        for label in self.item_labels:
            label.hide()
        
        # 显示组别选择信息
        max_group = max((g[0] for g in self.data_groups), default=0)
        self.query_label = QLabel(f"选择组别：{self.current_group}/{max_group}")
        self.query_label.setStyleSheet("""
            font-size: 16px; 
            padding: 5px; 
            margin: 2px;            /* 添加外边距 */
            margin-top: 15px;  /* 增加上边距 */
            border-bottom: 0px solid #ccc;
            background-color: #a0ffa0;
            border-left: 4px solid green;
            font-weight: bold;
            min-width: 120px;       /* 设置最小宽度 */
            max-width: 200px;       /* 设置最大宽度 */
            min-height: 30px;       /* 设置最小高度 */
            max-height: 40px;       /* 设置最大高度 */
        """)
        
        # 清除原有布局并添加查询标签
        # self.display_box_layout.insertWidget(0, self.query_label)
        
        # 隐藏其他显示
        self.force_display.hide()
        # self.measurement_container.hide()
        
        # 设置当前选择为3（虽然不显示，但用于逻辑）
        self.current_selection = 3

    def exit_query_mode(self):
        """退出数据查询模式"""
        self.querying_data = False
        
        # 移除查询标签
        self.display_box_layout.removeWidget(self.query_label)
        self.query_label.deleteLater()
        
        # 显示所有栏目
        for label in self.item_labels:
            label.show()
        
        # 重置当前选择
        self.current_selection = 0
        self.update_selection_arrow()

    def load_group_data(self):
        """加载选定组的数据"""
        if not self.data_groups:
            return
            
        group_data = next((g for g in self.data_groups if g[0] == self.current_group), None)
        if group_data:
            # 保存当前组数据 (包含原始间隔值)
            # 确保组数据是三元组格式 (group_num, points, interval)
            if len(group_data) == 2:  # 如果是旧格式
                group_data = (group_data[0], group_data[1], 0.2)  # 添加默认间隔
            self.current_group_data = group_data
            
            # 隐藏组别选择标签
            self.query_label.hide()
            
            # 设置数据点
            self.data_display.set_data_points(group_data[1])
            
            # 显示数据点阵和详细信息
            # self.measurement_container.show()
            self.tension_display.show()
            self.data_display.show()
            
            # 显示第一个数据点
            self.current_point_index = 0
            self.update_query_point_display()

    def update_query_display(self):
        """更新查询界面显示（选择组别时）"""
        max_group = max((g[0] for g in self.data_groups), default=0)  # 默认改为0
        current_group = max(0, self.current_group)  # 确保不小于0
        self.query_label.setText(f"选择组别：{current_group}/{max_group}")


    def update_query_point_display(self):
        """更新查询界面显示（查看数据点时）"""
        group_data = next((g for g in self.data_groups if g[0] == self.current_group), None)
        if group_data and group_data[1]:
            point_count = len(group_data[1])
            force, timestamp = group_data[1][self.current_point_index]
            # 格式化时间为从0开始的秒数，保留2位小数
            time_str = f"{timestamp:.2f}s"
            self.tension_display.setText(
                f"No.{self.current_group} "
                f"点数：{point_count}\n"            
            )

    def set_lift_direction(self, direction):
        """设置升降台方向 (0=上升, 1=停止, 2=下降)"""
        diagram = self.control_window.diagram
        if not diagram:
            return
        self.current_direction = direction
        self.arrow_widget.set_direction(direction)  # 更新箭头方向
        
        # 更新按钮状态
        self.lift_up_btn.setChecked(direction == 0)
        self.stop_btn.setChecked(direction == 1)
        self.lift_down_btn.setChecked(direction == 2)
        
        if direction == 0: #上升
            diagram.is_oscillation_exist = False
        if direction == 1:  # 停止
            self.lift_timer.stop()
        else:
            self.lift_timer.start(50)
                
    def animate_lift(self):
        diagram = self.control_window.diagram
        if not diagram:
            return
        
        current_pos = diagram.lift_position
        if self.current_direction == 0:  # 上升
            new_pos = max(-84, current_pos - self.lift_speed * 0.05)
        else:  # 下降
            new_pos = min(100, current_pos + self.lift_speed * 0.05)
            
        diagram.set_lift_position(new_pos)
        
        if (self.current_direction == 0 and new_pos == 0) or \
        (self.current_direction == 2 and new_pos == 100):
            self.set_lift_direction(1)  # 自动停止

    def update_selection_arrow(self):
        """更新箭头指示，高亮当前选中的栏目"""
        for i, label in enumerate(self.item_labels):
            if i == self.current_selection:
                if self.adjusting_interval and i == 0:  # 特别处理采集间隔调整状态
                    label.setStyleSheet("""
                        font-size: 15px; 
                        padding: 1px; 
                        border-bottom: 0px solid #ccc;
                        background-color: #a0d0ff;
                        border-left: 4px solid blue;
                        max-height: 20px;
                    """)
                elif self.querying_data and i == 3:  # 数据查询状态
                    label.setStyleSheet("""
                        font-size: 15px; 
                        padding: 1px; 
                        border-bottom: 0px solid #ccc;
                        background-color: #a0ffa0;
                        border-left: 4px solid green;
                        max-height: 20px;
                    """)
                else:
                    label.setStyleSheet("""
                        font-size: 15px; 
                        padding: 1px; 
                        border-bottom: 0px solid #ccc;
                        background-color: #e0e0e0;
                        border-left: 4px solid red;
                        max-height: 20px;
                    """)
            else:
                label.setStyleSheet("""
                    font-size: 15px; 
                    padding: 1px; 
                    border-bottom: 0px solid #ccc;
                    border:1px solid #ccc;
                    max-height: 20px;
                """)
        
        if not self.adjusting_interval and not self.querying_data:
            self.items[0] = f"采集间隔：{self.interval:.1f}s"
            self.item_labels[0].setText(self.items[0])

    def update_interval_display(self):
        """更新采集间隔显示"""
        self.items[0] = f"采集间隔：{self.interval:.1f}s(范围0.1-2.0s)"
        self.item_labels[0].setText(self.items[0])

    def add_weight_error(self, base_force):
        """为砝码添加±0.5mV固定误差"""
        if self.weight_count > 0 and not self.using_ring:
            # 每个砝码添加随机误差
            error_per_weight = random.uniform(-0.5, 0.5)
            return base_force + error_per_weight * (self.weight_count-3) 
        return base_force

    def update_force_display(self):
        """更新拉力显示"""
        if self.using_ring:
            base_force = (self.weight_count-3) * 15 + self.zero_dial.value()/10 + self.random_force   
            # 添加砝码误差
            base_force = self.add_weight_error(base_force)
            # 添加随机波动
            base_force = self.add_random_variation(base_force)
        else:
            base_force = -180 + self.zero_dial.value()/10 + self.random_force
        self.force_display.setText(f"当前拉力：{base_force:.1f}mV")

    def update_tension_display(self):
        """更新表面张力测量显示"""
        # 基础拉力值
        diagram = self.control_window.diagram
        if not diagram:
            return
        if self.using_ring:
            base_force = (self.weight_count-3) * 15 + self.zero_dial.value()/10+ self.random_force
        else:
            base_force = -180 + self.zero_dial.value()/10 + self.random_force
        # 添加砝码误差
        base_force = self.add_weight_error(base_force)
        
        # 获取当前速率调节值
        speed_factor = self.speed_dial.value()
        
        # 叠加Excel中的拉力数据
        global excel_force
        excel_force = 0
        if self.excel_data and self.data_points:
            ring_bottom = int(325 * 0.2) - 40 + 60 + 30  # 传感器y(升高40) + 连接线高度(延长到60) + 圆环高度
            water_top = 325 * (0.42 + 0.17 * (diagram.lift_position/100)) - 40  # 升降台y - 水高度

            # 液面到excel数据结束点的距离
            distance = ring_bottom + 33 - water_top
            speed = 35/25.5

            last_timestamp = 25.5 - distance/speed

            # # 获取最近的时间点（乘以速率调节因子）
            # last_timestamp = (self.data_points[-1][1] if self.data_points else 0) 

            
            # 找到最接近的时间点的数据
            closest_time, closest_force = min(self.excel_data, key=lambda x: abs(x[0] - last_timestamp))
            excel_force = closest_force
        
        # 圆环模式下始终叠加Excel数据，砝码模式下只在浸入水中时叠加
        diagram = self.control_window.diagram
        has_contacted = diagram.has_contacted_water
        is_broken= diagram.water_column_broken
        if has_contacted and (not is_broken or diagram.is_oscillation_exist):
            total_force = base_force + excel_force
        else:
            total_force = base_force
        
        # 添加随机波动
        total_force = self.add_random_variation(total_force)

        # 更新显示
        self.tension_display.setText(
            f"No.{self.measurement_count} 拉力：{total_force:.1f}mV"
        )

    def collect_data(self):
        """采集数据"""
        diagram = self.control_window.diagram
        if not diagram:
            return
        if len(self.data_points) >= 255:
            self.collection_timer.stop()
            return
            
        # 基础拉力值
        if self.using_ring:
            base_force = self.zero_dial.value()/10 + (self.weight_count-3) * 15 +self.random_force # 圆环相当于3个砝码
        else:
            base_force = -180 + self.zero_dial.value()/10 + self.random_force
        
        base_force = self.add_weight_error(base_force)
        # 获取当前速率调节值
        speed_factor = self.speed_dial.value()
        
       # 叠加Excel中的拉力数据
        global excel_force
        excel_force = 0
        if self.excel_data:
            ring_bottom = 325 * 0.2 -40 + 60 + 30   # 传感器y(升高40) + 连接线高度(延长到60) + 圆环高度
            water_top = 325 * (0.42 + 0.17 * (diagram.lift_position/100)) - 40  # 升降台y - 水高度

            # 液面到excel数据结束点的距离
            distance = ring_bottom + 33 - water_top
            speed = 35/25.5

            timestamp = 25.5-distance/speed
            if timestamp < 0:
                timestamp = 0
            print(f"ring_bottom: {ring_bottom}, water_top: {water_top}, distance: {distance}, timestamp: {timestamp}")
            closest_time, closest_force = min(self.excel_data, key=lambda x: abs(x[0] - timestamp))
            excel_force = closest_force
            print(f"excel_force: {excel_force}")
        
        diagram = self.control_window.diagram
        has_contacted = diagram.has_contacted_water
        is_broken= diagram.water_column_broken
        # 计算总拉力
        if has_contacted and (not is_broken or diagram.is_oscillation_exist):
            total_force = base_force + excel_force
        else:
            total_force = base_force

        # 添加随机波动
        total_force = self.add_random_variation(total_force)
        
        # 存储为(force, timestamp)元组（存储原始时间，不乘以速率因子）
        self.data_points.append((round(total_force, 1), len(self.data_points) * self.interval))
        
        # 只在第一次采集时设置数据点，后续只更新数据
        if len(self.data_points) == 1:
            self.data_display.set_data_points(self.data_points)
        else:
            self.data_display.data_points = self.data_points
            self.data_display.update()
        
        self.update_tension_display()

    def enter_calibration_mode(self):
        """进入传感器定标模式"""
        self.calibrating_sensor = True
        
        # 隐藏所有栏目
        for label in self.item_labels:
            label.hide()
        
        # 显示拉力文本框
        self.force_display.setGeometry(10, 80, 250, 40)
        self.force_display.show()
        self.update_force_display()
        
        # 隐藏其他显示
        self.tension_display.hide()
        self.data_display.hide()
        
        # 更新界面
        self.update_selection_arrow()

    def exit_calibration_mode(self):
        """退出传感器定标模式"""
        self.calibrating_sensor = False
        self.zero_dial_value = self.zero_dial.value()  # 保存当前旋钮位置
        
        # 显示所有栏目
        for label in self.item_labels:
            label.show()
        
        # 隐藏拉力文本框
        self.force_display.hide()
        
        # 更新界面
        self.update_selection_arrow()

    def enter_measurement_mode(self):
        """进入表面张力测量模式"""
         # 确保放大窗口被创建并显示
        # if hasattr(self, 'data_display'):
        #     self.data_display.show_enlarged_view()
        # 保存当前的采集间隔值
        self.current_measurement_interval = self.interval  # 新增这行
        print(f"开始测量，记录间隔: {self.current_measurement_interval}")  # 调试用
        diagram = self.control_window.diagram
        if not diagram:
            return
        self.measuring_tension = True
        self.data_points = []  # 清空数据点
        # 关键设置：允许图表控件接收鼠标事件
        self.data_display.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.data_display.setMouseTracking(True)
        
        # 禁用液体选择按钮
        if hasattr(self, 'control_window'):
            self.control_window.set_liquid_buttons_enabled(False)
            
        self.measuring_tension = True
        self.data_points = []  # 清空数据点
        
        # 隐藏所有栏目
        for label in self.item_labels:
            label.hide()
        
        # 调整测量显示区域的大小和位置
        self.tension_display.setGeometry(10, 10, 250, 30)  # 固定位置
        self.tension_display.show()
        
        # 调整数据点阵显示区域
        self.data_display.setGeometry(10, 45, 250, 150)  # 更大的显示区域
        self.data_display.show()

        # 显示测量容器（包含文本框和数据点阵）
        # self.measurement_container.show()
        # self.tension_display.show()
        # self.data_display.show()
        self.update_tension_display()
        
        
        # 开始数据采集
        self.collection_timer.start(int(self.interval * 1000))  # 转换为毫秒

    def exit_measurement_mode(self):
        """退出测量模式时保存数据"""
        self.measuring_tension = False
        self.collection_timer.stop()

        # 重新启用液体选择按钮
        if hasattr(self, 'control_window'):
            self.control_window.set_liquid_buttons_enabled(True)
        
        print(f'退出测量 interval=', self.current_measurement_interval)
        # print(f'退出测量 data_points=', self.data_points)
        # 保存当前组数据 - 确保保存的是完整的数据点和间隔值
        if self.data_points:
            self.data_groups.append((
                self.measurement_count, 
                self.data_points.copy(), 
                self.current_measurement_interval  # 明确添加间隔值
            ))
            self.data_points = []
            self.measurement_count += 1
        
        # 恢复界面显示
        for label in self.item_labels:
            label.show()
        
        # self.measurement_container.hide()
        self.data_display.setGeometry(10, 185, 250, 10)  # 恢复小尺寸
        self.update_selection_arrow()

    def on_dial_changed(self, value):
        """旋钮值变化时的处理 - 更新拉力显示"""
        if self.calibrating_sensor:
            self.update_force_display()
        elif self.measuring_tension:
            self.update_tension_display()


    def on_up_clicked(self):
        if self.querying_data:
            if not self.measurement_container.isVisible():  # 在选择组别阶段
                max_group = max((g[0] for g in self.data_groups), default=1)
                self.current_group = min(self.current_group + 1, max_group)
                self.update_query_display()
            else:  # 在查看数据点阶段
                group_data = next((g for g in self.data_groups if g[0] == self.current_group), None)
                if group_data:
                    self.current_point_index = min(self.current_point_index + 1, len(group_data[1]) - 1)
                    self.update_query_point_display()
        elif self.adjusting_interval and self.current_selection == 0:
            self.interval = min(2.0, self.interval + 0.1)
            self.update_interval_display()
        elif not self.adjusting_interval and not self.calibrating_sensor and not self.measuring_tension and self.current_selection > 0:
            self.current_selection -= 1
            self.update_selection_arrow()

    def on_down_clicked(self):
        if self.querying_data:
            if not self.measurement_container.isVisible():  # 在选择组别阶段
                self.current_group = max(self.current_group - 1, 1)
                self.update_query_display()
            else:  # 在查看数据点阶段
                self.current_point_index = max(self.current_point_index - 1, 0)
                self.update_query_point_display()
        elif self.adjusting_interval and self.current_selection == 0:
            self.interval = max(0.1, self.interval - 0.1)
            self.update_interval_display()
        elif not self.adjusting_interval and not self.calibrating_sensor and not self.measuring_tension and self.current_selection < len(self.items) - 1:
            self.current_selection += 1
            self.update_selection_arrow()

    def on_ok_clicked(self):
        if self.current_selection == 0:
            if not self.adjusting_interval:
                self.adjusting_interval = True
                self.update_selection_arrow()
            else:
                self.adjusting_interval = False
                self.update_selection_arrow()
                print(f"采集间隔已设置为: {self.interval:.1f}秒")
        elif self.current_selection == 1:
            if not self.calibrating_sensor:
                self.enter_calibration_mode()
        elif self.current_selection == 2:
            if not self.measuring_tension:
                self.enter_measurement_mode()
            else:
                # 测量模式下按确定按钮不做任何操作
                pass
        elif self.current_selection == 3:  # 数据查询
            if not self.querying_data:
                self.enter_query_mode()
            else:
                if not self.measurement_container.isVisible():  # 在选择组别阶段
                    self.load_group_data()

    def on_back_clicked(self):
        if self.querying_data:
            if self.measurement_container.isVisible():  # 在查看数据点阶段
                # 返回组别选择
                self.measurement_container.hide()
                self.query_label.show()
            else:  # 在选择组别阶段
                self.exit_query_mode()
        elif self.adjusting_interval and self.current_selection == 0:
            self.adjusting_interval = False
            self.update_selection_arrow()
        elif self.calibrating_sensor:
            self.exit_calibration_mode()
        elif self.measuring_tension:
            self.exit_measurement_mode()
        else:
            print("返回操作")

 # 在程序开始时保存原始分辨率
original_width = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS).PelsWidth
original_height = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS).PelsHeight
def set_screen_resolution(width, height):
    try:
        devmode = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
        devmode.PelsWidth = width
        devmode.PelsHeight = height
        devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT
        win32api.ChangeDisplaySettings(devmode, 0)
        print(f"分辨率已修改为 {width}x{height}")
    except Exception as e:
        print(f"修改分辨率出错: {e}")

def restore_original_resolution():
    try:
        set_screen_resolution(original_width, original_height)
    except Exception as e:
        print(f"恢复原始分辨率出错: {e}")

if __name__ == "__main__":
    set_screen_resolution(1600, 900)
    app = QApplication(sys.argv)
    window = SurfaceTensionApp()
    window.show() 
    # 在应用程序退出时恢复原始分辨率
    app.aboutToQuit.connect(restore_original_resolution)
    sys.exit(app.exec_())