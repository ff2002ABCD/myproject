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
        self.setFixedSize(840, 400)
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
            if self.parent.measuring_tension:
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
            if self.parent.measuring_tension:
                self.parent.update_tension_display()

    def on_record_data(self):
        """记录数据到折线图窗口"""
        if not self.show_measure_control:  # 仅在传感器定标模式下处理
            # 获取当前砝码个数（0~6对应0.5g~3.5g）
            weight_count = self.parent.weight_count-3
            if weight_count < 1 or weight_count > 7:
                QMessageBox.warning(self, "错误", "砝码个数必须在1-7之间！")
                return

            # 从主窗口的 tension_display 中解析当前拉力值（单位：mV）
            force_text = self.parent.tension_display.text().strip()
            try:
                voltage_mV = float(force_text)
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
                    if self.parent.measuring_tension:
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
                    if self.parent.measuring_tension:
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
        
        # 创建升降台控制区域
        self.lift_control_group = QGroupBox("升降台控制")
        self.init_lift_controls()
        
        # 将示意图和控制区域放入水平布局
        diagram_control_layout = QHBoxLayout()
        diagram_control_layout.addWidget(self.lift_control_group)
        diagram_control_layout.addWidget(self.diagram)
        
        layout.addLayout(diagram_control_layout)
        self.diagram_group.setLayout(layout)
        
        # 调试验证
        print(f"Diagram parent: {self.diagram.parent()}")  # 应显示diagram_group
        print(f"Diagram visible: {self.diagram.isVisible()}")  # 应为True

    def init_lift_controls(self):
        """初始化升降台控制区域"""
        lift_layout = QVBoxLayout()
        
        # # 速率调节旋钮
        # self.speed_dial = QDial()
        # self.speed_dial.setRange(1, 5)
        # self.speed_dial.setValue(1)
        # self.speed_dial.setNotchesVisible(True)
        # self.speed_dial.valueChanged.connect(self.update_lift_speed)
        
        # 方向控制按钮
        button_style = """
            QPushButton {
                font-size: 16px;
                min-width: 60px;
                min-height: 30px;
                padding: 2px;
            }
        """
        
        self.up_btn = QPushButton("上升")
        self.up_btn.setCheckable(True)
        self.up_btn.setStyleSheet(button_style)
        self.up_btn.clicked.connect(lambda: self.set_lift_direction(0))
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setCheckable(True)
        self.stop_btn.setChecked(True)
        self.stop_btn.setStyleSheet(button_style)
        self.stop_btn.clicked.connect(lambda: self.set_lift_direction(1))
        
        self.down_btn = QPushButton("下降")
        self.down_btn.setCheckable(True)
        self.down_btn.setStyleSheet(button_style)
        self.down_btn.clicked.connect(lambda: self.set_lift_direction(2))
        
        # 添加控件到布局
        # lift_layout.addWidget(QLabel("速率调节"), 0, Qt.AlignCenter)
        # lift_layout.addWidget(self.speed_dial, 0, Qt.AlignCenter)
        lift_layout.addWidget(self.up_btn)
        lift_layout.addWidget(self.stop_btn)
        lift_layout.addWidget(self.down_btn)
        
        self.lift_control_group.setLayout(lift_layout)
        
        # 初始化升降台状态
        self.current_direction = 1  # 1=停止
        self.lift_speed = 1.5
        self.lift_timer = QTimer()
        self.lift_timer.timeout.connect(self.animate_lift)

    def update_lift_speed(self, speed_value):
        """更新升降台速度"""
        self.lift_speed = speed_value * 1.5  # 每档1.5倍速
        
        # 如果当前正在移动，则更新速度
        if self.current_direction != 1:  # 如果不是停止状态
            self.lift_timer.start(50)  # 重新启动定时器以应用新速度

    def set_lift_direction(self, direction):
        """设置升降台方向 (0=上升, 1=停止, 2=下降)"""
        self.current_direction = direction
        
        # 更新按钮状态
        self.up_btn.setChecked(direction == 0)
        self.stop_btn.setChecked(direction == 1)
        self.down_btn.setChecked(direction == 2)
        
        if direction == 0: #上升
            self.diagram.is_oscillation_exist = False

        if direction == 1:  # 停止
            self.lift_timer.stop()
        else:
            self.lift_timer.start(50)

    def animate_lift(self):
        """升降台动画"""
        current_pos = self.diagram.lift_position
        
        if self.current_direction == 0:  # 上升
            new_pos = max(0, current_pos - self.lift_speed * 0.05)
        else:  # 下降
            new_pos = min(100, current_pos + self.lift_speed * 0.05)
            
        self.diagram.set_lift_position(new_pos)
        
        # 到达极限位置时自动停止
        if (self.current_direction == 0 and new_pos == 0) or \
        (self.current_direction == 2 and new_pos == 100):
            self.set_lift_direction(1)


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
        # self.enlarged_window.update_data(self.data_points)
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

    
    def set_data_points(self, points):
        """设置数据点"""
        self.data_points = points
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


class EnlargedDataDisplay(QWidget):
    def __init__(self, parent_display, parent=None):
        super().__init__(parent)
        self.setWindowTitle("力敏传感器电压采集图")
        self.setMinimumSize(800, 500)
        self.resize(1157, 550)  # 覆盖最小大小限制，直接设定初始尺寸
        self.setFixedHeight(500)
        self.parent_display = parent_display
        self.data_points = []
        # self.set_default_view()  # 设置默认视图范围
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
        # self.setMouseTracking(True)
        # self.setAttribute(Qt.WA_AlwaysShowToolTips)  # 强制工具提示显示
        
        # # 增强工具提示样式
        # self.tooltip_label = QLabel(self)
        # self.tooltip_label.setStyleSheet("""
        #     background-color: rgba(255, 255, 225, 220);
        #     border: 2px solid #555;
        #     border-radius: 5px;
        #     padding: 8px;
        #     font-size: 16px;
        #     font-weight: bold;
        #     min-width: 200px;
        # """)
        # self.tooltip_label.hide()
        

        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # 1. 图表绘制区域 (使用自定义Widget)
        # self.chart_widget = QWidget()
        # self.chart_widget.setMinimumHeight(400)  # 固定最小高度
        # self.main_layout.addWidget(self.chart_widget, stretch=3)  # 占据3份空间
        
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
        button_layout.setContentsMargins(0, 0, 0, 170)
        button_layout.setSpacing(5)
        
        # 创建三个液体按钮
        self.water_btn = QPushButton("纯水")
        self.ethanol_btn = QPushButton("乙醇")
        self.glycerol_btn = QPushButton("甘油")
        
        # 设置按钮样式
        button_style = """
            QPushButton {
                font-size: 16px;
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

        # # 导出按钮
        # export_btn = QPushButton("导出数据")
        # export_btn.setFixedWidth(80)
        # export_btn.clicked.connect(self.parent_display.export_data)  # 使用父窗口的导出方法
        
        # 添加到布局
        layout.addWidget(avg_label)
        layout.addWidget(self.avg_value)
        layout.addSpacing(20)
        layout.addWidget(error_label)
        layout.addWidget(self.error_value)
        layout.addSpacing(20)
        layout.addWidget(calc_btn)
        # layout.addWidget(export_btn) 
        layout.addStretch()

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
        # 设置固定窗口大小（取消缩放）
        self.setFixedSize(852, 326)  # 初始大小
        # 设置窗口标志，禁用最大化按钮和窗口大小调整
        self.setWindowFlags(self.windowFlags() & 
                          ~Qt.WindowMaximizeButtonHint & 
                          ~Qt.WindowMinimizeButtonHint)
        # self.setFixedSize(784, 415)  # 固定宽度1084，高度600
        self.setGeometry(0, 0, 400, 270)
        self.querying_data = False
        current_group_data=None
        self.current_group = 1
        self.current_point_index = 0
        self.background_image = "FD-NST-A面板图.png"    # 图片路径
        self.set_background(self.background_image)
        self.control_window = ControlWindow(self, show_measure_control=False)  # 默认显示传感器定标模式
        self.control_window.show()

        # 状态变量
        self.last_sensitivity = 0.0  # 添加这个变量来存储最新的灵敏度值
        self.random_force= random.uniform(-10, 10)
        self.min_speed= 1.5
        self.lift_speed = self.min_speed
        # self.excel_data = self.load_excel_data()  # 加载Excel数据
        self.current_selection = 0
        self.interval = 0.33
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
        # self.lift_timer.timeout.connect(self.animate_lift)
        self.current_direction = 1
        self.collection_timer = QTimer()
        self.collection_timer.timeout.connect(self.collect_data)
        
        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QHBoxLayout()
        main_widget.setLayout(self.main_layout)
        
        # 初始化界面区域
        self.init_left_area()
        self.init_center_area()
        self.init_right_area()

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

        # self.enter_measurement_mode()

    def closeEvent(self, event):
        """使用Qt内置方法关闭所有窗口"""
        QApplication.closeAllWindows()
        super().closeEvent(event)

    def add_random_variation(self, value):
        """为测量值添加0-0.5%的随机波动"""
        variation = random.uniform(-0.005, 0.005)  # -0.5%到+0.5%
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

    def init_left_area(self):
        """初始化左侧区域"""
        # 左侧区域（分为左右两部分）
        self.left_area = QWidget()
        self.left_area_layout = QHBoxLayout()
        self.left_area.setLayout(self.left_area_layout)

       # 左侧显示框
        self.left_display_frame = QFrame()
        self.left_display_frame.setFrameShape(QFrame.StyledPanel)
        self.left_display_layout = QVBoxLayout()
        self.left_display_layout.setSpacing(2)  # 将间距设置为0
        self.left_display_layout.setContentsMargins(0, 0, 0, 0)  # 设置整体边距
        self.left_display_frame.setLayout(self.left_display_layout)
        
        # 左侧显示框内容
        self.display_box = QGroupBox("")
        # 设置大小
        self.display_box.setFixedSize(310, 250)  # 固定大小
        # self.display_box.resize(280,200)
        
        #无边框
        self.display_box.setStyleSheet("""
            QGroupBox {
                border: 0px solid transparent;  /* 无边框 */
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 3px;
            }
        """)
        self.display_layout = QVBoxLayout()

        self.tension_display = QLabel("0")
        self.tension_display.setAlignment(Qt.AlignCenter)
        self.tension_display.hide()
        self.tension_display.setFixedHeight(80)  # 固定高度
        self.tension_display.setStyleSheet("""
            QLabel {
                font-size: 60px;
                padding: 0px;
                margin: -300px 0 0 0;  /* 上边距负值使标签上移 */
                border: 0px;
                background-color: transparent;  /* 透明背景 */
                color: black;  /* 确保文字颜色可见 */
            }
        """)

        
        # 数据点阵显示 - 高度设置为2/3
        self.data_display = DataPointDisplay()
        self.data_display.hide()
        self.data_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 创建测量模式的专用布局
        self.measurement_layout = QVBoxLayout()
        self.measurement_layout.addWidget(self.tension_display, 2)  # 1份高度
        self.measurement_layout.setContentsMargins(0, 0, 0, 200)  # 添加边距
        
        # 将测量布局放入一个容器中
        self.measurement_container = QWidget()
        self.measurement_container.setLayout(self.measurement_layout)
        # self.measurement_container.setStyleSheet("background-color: #f0f0f0;")  # 设置背景色
        self.measurement_container.hide()
        
        # 修改这里：将栏目标签放入一个单独的容器中
        self.labels_container = QWidget()
        
        self.display_box_layout = QVBoxLayout()
        self.display_box_layout.addWidget(self.measurement_container)
        self.display_box.setLayout(self.display_box_layout)
        
        self.left_display_layout.addWidget(self.display_box)

        # 左侧控制按钮区域
        self.left_control_frame = QFrame()
        self.left_control_layout = QVBoxLayout()
        self.left_control_frame.setLayout(self.left_control_layout)
        
         # 中间旋钮 - 范围-100到100，对应±10mV
        self.zero_dial = QDial()
        self.zero_dial.setRange(-100, 100)
        self.zero_dial.setValue(self.zero_dial_value)  # 使用保存的值初始化
        self.zero_dial.setNotchesVisible(True)
        self.zero_dial.setFixedSize(50, 50)
        self.zero_dial.valueChanged.connect(self.on_dial_changed)
        
        self.zero_label = QLabel("")
        self.zero_label.setAlignment(Qt.AlignCenter)
        self.zero_label.setStyleSheet("font-size: 16px;")
        
        self.left_control_layout.addStretch(29)
        self.left_control_layout.addWidget(self.zero_dial, 2, Qt.AlignCenter)
        self.left_control_layout.addWidget(self.zero_label, 2, Qt.AlignCenter)
        self.left_control_layout.addStretch(2) 
        
        # 将左右两部分添加到左侧区域布局
        self.left_area_layout.addWidget(self.left_display_frame, 510)  # 显示区域占2/3
        self.left_area_layout.addWidget(self.left_control_frame, 268)  # 控制区域占1/3

    def init_center_area(self):
        """初始化中间区域"""
        self.center_frame = QFrame()
        self.center_frame.setFrameShape(QFrame.StyledPanel)
        self.center_layout = QVBoxLayout()
        self.center_frame.setLayout(self.center_layout)
        
       

    def init_right_area(self):
        """初始化右侧区域（现在只保留调零旋钮）"""
        self.right_frame = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_frame.setLayout(self.right_layout)

        # 添加测量控制按钮
        self.measurement_control_group = QGroupBox()
        self.measurement_control_group.setStyleSheet("""
            QGroupBox {
                border: 0px;  /* 完全移除边框 */
                margin: 0px;
                padding: 0px;
            }
        """)
        measurement_layout = QVBoxLayout()
        
        # 上方按钮 - 进入测量模式
        self.enter_measure_btn = QPushButton("")
        # self.enter_measure_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # self.enter_measure_btn.setFixedWidth(50)
        self.enter_measure_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                min-width: 100px;
                width: 40px;
                min-height: 40px;
                padding: 5px;
                background-color: transparent;
                color: white;
            }
        """)
        self.enter_measure_btn.clicked.connect(self.enter_measurement_mode)
        
        # 下方按钮 - 退出测量模式
        self.exit_measure_btn = QPushButton("")
        self.exit_measure_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                min-width: 100px;
                width: 40px;
                min-height: 40px;
                padding: 0px;
                background-color: transparent;
                color: white;
            }
        """)

        # self.enter_measure_btn.setFixedWidth(40)  # 强制宽度为 80px
        # self.exit_measure_btn.setFixedWidth(40)   # 强制宽度为 80px
        self.exit_measure_btn.clicked.connect(self.exit_measurement_mode)
        
        # 将按钮添加到布局
        measurement_layout.addStretch(12)
        measurement_layout.addWidget(self.enter_measure_btn, alignment=Qt.AlignRight)
        measurement_layout.addWidget(self.exit_measure_btn, alignment=Qt.AlignRight)
        measurement_layout.addStretch(4)  # 添加弹性空间使按钮靠上
        
        self.measurement_control_group.setLayout(measurement_layout)
        self.right_layout.addWidget(self.measurement_control_group)

        # 将三部分添加到主布局
        self.main_layout.addWidget(self.left_area, 750)
        self.main_layout.addWidget(self.center_frame, 150)
        self.main_layout.addWidget(self.right_frame, 390)
    
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

    def add_weight_error(self, base_force):
        """为砝码添加±0.5mV固定误差"""
        if self.weight_count > 0 and not self.using_ring:
            # 每个砝码添加随机误差
            error_per_weight = random.uniform(-0.5, 0.5)
            return base_force + error_per_weight * (self.weight_count-3) 
        return base_force

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
        # speed_factor = self.speed_dial.value()
        
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
        print(f"has_contacted: {has_contacted}, is_broken: {is_broken}, is_oscillation_exist: {diagram.is_oscillation_exist}")
        if has_contacted and (not is_broken or diagram.is_oscillation_exist):
            total_force = base_force + excel_force
        else:
            total_force = base_force
        
        # 添加随机波动
        total_force = self.add_random_variation(total_force)

        # 更新显示
        self.tension_display.setText(
            f"{total_force:.1f}"
        )

    def collect_data(self):
        """采集数据"""
        diagram = self.control_window.diagram
        if not diagram:
            return
        # if len(self.data_points) >= 255:
        #     self.collection_timer.stop()
        #     return
            
        # 基础拉力值
        if self.using_ring:
            base_force = self.zero_dial.value()/10 + (self.weight_count-3) * 15 +self.random_force # 圆环相当于3个砝码
        else:
            base_force = -180 + self.zero_dial.value()/10 + self.random_force
        
        base_force = self.add_weight_error(base_force)
        # 获取当前速率调节值
        # speed_factor = self.speed_dial.value()
        
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
        
        # # 禁用液体选择按钮
        # if hasattr(self, 'control_window'):
        #     self.control_window.set_liquid_buttons_enabled(False)
            
        self.measuring_tension = True
        self.data_points = []  # 清空数据点
        
        # 显示测量容器（包含文本框和数据点阵）
        self.measurement_container.show()
        self.tension_display.show()
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
        
        self.measurement_container.hide()

    def on_dial_changed(self, value):
        """旋钮值变化时的处理 - 更新拉力显示"""
        if self.measuring_tension:
            self.update_tension_display()

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
    # set_screen_resolution(1600, 900)
    app = QApplication(sys.argv)
    window = SurfaceTensionApp()
    window.show() 
    # 在应用程序退出时恢复原始分辨率
    # app.aboutToQuit.connect(restore_original_resolution)
    sys.exit(app.exec_())