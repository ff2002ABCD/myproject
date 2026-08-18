import sys
import os
import math
import csv
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

def get_resource_path(relative_path):
    """获取资源的绝对路径，支持打包后的环境"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class DataGroup:
    """每组数据的容器"""
    def __init__(self, voltage=0.0):
        self.voltage = voltage
        self.points = []  # [(x, y), ...]
        self.color = None
        self.show_lines = False  # 是否显示该组的连线

class ExperimentData:
    """每个实验的数据管理器"""
    def __init__(self):
        self.data_groups = {}  # {group_id: DataGroup}
        self.current_group_id = 0
        self.color_index = 0
        self.colors = [
            '#FF0000', '#00FF00', '#0000FF', '#FF00FF', '#00FFFF',
            '#FF8800', '#88FF00', '#0088FF', '#FF0088', '#8800FF',
            '#FF4444', '#44FF44', '#4444FF', '#FFFF00', '#FF44FF'
        ]
    
    def add_data_group(self, voltage=0.0):
        group_id = len(self.data_groups)
        group = DataGroup(voltage)
        group.color = self.get_next_color()
        group.show_lines = False
        self.data_groups[group_id] = group
        self.current_group_id = group_id
        return group_id

    def get_next_color(self):
        color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1
        return color
    
    def clear_current_group(self):
        if self.current_group_id in self.data_groups:
            self.data_groups[self.current_group_id].points = []
    
    def clear_all(self):
        self.data_groups.clear()
        self.color_index = 0
        self.current_group_id = 0
    
    def get_all_data(self):
        export_data = []
        for group_id, group in self.data_groups.items():
            export_data.append({
                'group_id': group_id,
                'voltage': group.voltage,
                'points': group.points.copy()
            })
        return export_data

class ElectricFieldCanvas(QLabel):
    """用于绘制电场线和探针的自定义画布"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setFixedSize(600, 500)
        self.setAlignment(Qt.AlignCenter)
            
        # 绘图相关
        self.pixmap = None
        
        # 两个实验的独立数据
        self.line_data = ExperimentData()
        self.coaxial_data = ExperimentData()
        self.current_data = self.line_data
        
        # 探针
        self.probe_pos = QPoint(300, 250)
        self.probe_radius = 10
        
        # 模式
        self.point_radius = 5
        
        # 电压数据
        self.voltage_data = None
        self.field_type = "line"
        
        # 背景图片路径
        self.background_path_line = get_resource_path("background/导电玻璃2.jpg")
        self.background_path_coaxial = get_resource_path("background/导电玻璃1.jpg")
        self.load_background()
        
        self.setMouseTracking(True)
    
    def get_current_data(self):
        if self.field_type == "line":
            return self.line_data
        else:
            return self.coaxial_data
    
    def switch_field_type(self, field_type):
        if field_type == "line":
            self.current_data = self.line_data
        else:
            self.current_data = self.coaxial_data
        
        if len(self.current_data.data_groups) == 0:
            self.current_data.add_data_group(0.0)
        
        self.field_type = field_type
        self.load_background()
        self.update_voltage()
        self.update()
        self.main_window.on_data_switched()
        self.main_window.update_group_voltage()

    def load_background(self):
        if self.field_type == "line":
            bg_path = self.background_path_line
        else:
            bg_path = self.background_path_coaxial
            
        if os.path.exists(bg_path):
            self.pixmap = QPixmap(bg_path)
            self.pixmap = self.pixmap.scaled(600, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            self.pixmap = QPixmap(600, 500)
            self.pixmap.fill(Qt.white)
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(Qt.gray, 1, Qt.DashLine))
            for i in range(0, 600, 50):
                painter.drawLine(i, 0, i, 500)
            for i in range(0, 500, 50):
                painter.drawLine(0, i, 600, i)
            painter.setPen(QPen(Qt.black, 2))
            painter.drawText(250, 250, f"请放入{os.path.basename(bg_path)}")
            painter.end()
        self.update()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            if self.pixmap:
                x = max(0, min(pos.x(), self.pixmap.width()))
                y = max(0, min(pos.y(), self.pixmap.height()))
                self.record_point(x, y)
    
    def mouseMoveEvent(self, event):
        pos = event.pos()
        if self.pixmap:
            x = max(0, min(pos.x(), self.pixmap.width()))
            y = max(0, min(pos.y(), self.pixmap.height()))
            self.probe_pos = QPoint(x, y)
            self.update()
            self.update_voltage()
    
    def record_point(self, x, y):
        data = self.get_current_data()
        if data.current_group_id not in data.data_groups:
            return
        
        group = data.data_groups[data.current_group_id]
        group.points.append((x, y))
        
        self.main_window.update_table()
        self.update()
    
    def draw_all_lines(self):
        data = self.get_current_data()
        for group_id in data.data_groups:
            data.data_groups[group_id].show_lines = True
        self.update()

    def update_voltage(self):
        if not self.pixmap:
            return
        
        px = self.probe_pos.x()
        py = self.probe_pos.y()
        source_voltage = self.main_window.voltage
        
        if self.field_type == "line":
            x1, y1 = 222, 235
            x2, y2 = 412, 235
            r1 = math.sqrt((px - x1)**2 + (py - y1)**2)
            r2 = math.sqrt((px - x2)**2 + (py - y2)**2)
            electrode_radius = 18
            R = 190
            
            if r1 <= electrode_radius:
                voltage = source_voltage
            elif r2 <= electrode_radius:
                voltage = 0.0
            else:
                r1_eff = r1
                r2_eff = r2
                
                try:
                    ln_r1 = math.log(r1_eff)
                    ln_r2 = math.log(r2_eff)
                    ln_r0 = math.log(electrode_radius)
                    ln_R = math.log(R)
                    
                    voltage_ratio = (ln_r2 - ln_r1) / (ln_R - ln_r0)
                    voltage_ratio = (voltage_ratio + 1) / 2
                    voltage_ratio = max(0, min(1, voltage_ratio))
                    
                    voltage = source_voltage * voltage_ratio
                    
                    if source_voltage == 0:
                        voltage = 0.0
                except:
                    voltage = 0.0
        else:
            cx, cy = 315, 235
            dx = px - cx
            dy = py - cy
            r = math.sqrt(dx*dx + dy*dy)
            
            r1 = 18
            r2 = 152
            v1 = source_voltage
            v2 = 0.0
            
            if r <= r1:
                voltage = v1
            elif r >= r2:
                voltage = v2
            else:
                try:
                    voltage = v1 * math.log(r2 / r) / math.log(r2 / r1)
                    voltage = max(0, min(v1, voltage))
                except:
                    voltage = 0.0
                
        self.main_window.update_voltage_display(voltage)
    
    def paintEvent(self, event):
        if not self.pixmap:
            return
        
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)
        
        data = self.get_current_data()
        
        for group_id, group in data.data_groups.items():
            if not group.points:
                continue
            color = QColor(group.color)
            
            if group.show_lines and len(group.points) > 1:
                painter.setPen(QPen(color, 2))
                for i in range(len(group.points) - 1):
                    painter.drawLine(
                        int(group.points[i][0]), int(group.points[i][1]),
                        int(group.points[i+1][0]), int(group.points[i+1][1])
                    )
            
            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(color))
            for x, y in group.points:
                painter.drawEllipse(QPoint(int(x), int(y)), self.point_radius, self.point_radius)
                
        painter.setPen(QPen(Qt.blue, 1))
        painter.setBrush(QBrush(Qt.transparent))
        painter.drawEllipse(self.probe_pos, self.probe_radius, self.probe_radius)
        cx, cy = self.probe_pos.x(), self.probe_pos.y()
        painter.drawLine(cx - self.probe_radius + 2, cy, cx + self.probe_radius - 2, cy)
        painter.drawLine(cx, cy - self.probe_radius + 2, cx, cy + self.probe_radius - 2)
        painter.setBrush(QBrush(Qt.blue))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.probe_pos, 2, 2)
    
    def add_data_group(self, voltage=0.0):
        data = self.get_current_data()
        group_id = data.add_data_group(voltage)
        return group_id
    
    def clear_current_group(self):
        data = self.get_current_data()
        data.clear_current_group()
        group_id = data.current_group_id
        if group_id in data.data_groups:
            data.data_groups[group_id].show_lines = False
        self.update()
    
    def clear_all_groups(self):
        data = self.get_current_data()
        data.clear_all()
        self.update()
    
    def get_all_data_for_export(self):
        data = self.get_current_data()
        return data.get_all_data()
    
    def get_current_group_id(self):
        data = self.get_current_data()
        return data.current_group_id
    
    def set_current_group_id(self, group_id):
        data = self.get_current_data()
        data.current_group_id = group_id
    
    def get_group_voltage(self, group_id):
        data = self.get_current_data()
        if group_id in data.data_groups:
            return data.data_groups[group_id].voltage
        return 0.0
    
    def set_group_voltage(self, group_id, voltage):
        data = self.get_current_data()
        if group_id in data.data_groups:
            data.data_groups[group_id].voltage = voltage

class CoaxialParamsWidget(QWidget):
    """同轴电缆参数显示和等势线表格"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 参数显示区域
        params_group = QGroupBox("同轴电缆参数")
        params_layout = QGridLayout(params_group)
        
        # 固定参数
        params_layout.addWidget(QLabel("内圆柱直径 D1:"), 0, 0)
        params_layout.addWidget(QLabel("15 mm"), 0, 1)
        params_layout.addWidget(QLabel("内圆柱半径 R1:"), 1, 0)
        params_layout.addWidget(QLabel("7.5 mm"), 1, 1)
        params_layout.addWidget(QLabel("外圆环内直径 D2:"), 2, 0)
        params_layout.addWidget(QLabel("150 mm"), 2, 1)
        params_layout.addWidget(QLabel("外圆环内半径 R2:"), 3, 0)
        params_layout.addWidget(QLabel("75 mm"), 3, 1)
        
        # 动态参数（跟随电源电压）
        params_layout.addWidget(QLabel("内圆柱电位 V1:"), 4, 0)
        self.v1_label = QLabel("0.00 V")
        params_layout.addWidget(self.v1_label, 4, 1)
        params_layout.addWidget(QLabel("外圆环电位 V2:"), 5, 0)
        self.v2_label = QLabel("0.00 V")
        params_layout.addWidget(self.v2_label, 5, 1)
        
        layout.addWidget(params_group)
        
        # 等势线表格
        table_group = QGroupBox("等势线数据")
        table_layout = QVBoxLayout(table_group)

        self.equipotential_table = QTableWidget()
        self.equipotential_table.setColumnCount(4)
        self.equipotential_table.setHorizontalHeaderLabels([
            "实测电压\nVr/V", "等势线直径\nd/mm", "等势线半径\nr/mm", "半径理论值\nr'/mm"
        ])
        # 设置固定列宽
        self.equipotential_table.setColumnWidth(0, 80)
        self.equipotential_table.setColumnWidth(1, 90)
        self.equipotential_table.setColumnWidth(2, 90)
        self.equipotential_table.setColumnWidth(3, 90)
        self.equipotential_table.setMaximumHeight(250)
        self.equipotential_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # 初始化10行空数据
        self.equipotential_table.setRowCount(10)
        for i in range(10):
            for j in range(4):
                self.equipotential_table.setItem(i, j, QTableWidgetItem(""))
        
        table_layout.addWidget(self.equipotential_table)
        layout.addWidget(table_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self.calc_btn = QPushButton("计算")
        self.calc_btn.clicked.connect(self.calculate)
        self.export_btn = QPushButton("导出数据")
        self.export_btn.clicked.connect(self.export_data)
        self.import_btn = QPushButton("导入数据")
        self.import_btn.clicked.connect(self.import_data)
        
        btn_layout.addWidget(self.calc_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.import_btn)
        layout.addLayout(btn_layout)
        
        layout.addStretch()
    
    def update_params(self, voltage):
        """更新电压参数显示"""
        self.v1_label.setText(f"{voltage:.2f} V")
        self.v2_label.setText("0.00 V")
    
    def calculate(self):
        """计算等势线数据"""
        # 获取同轴电缆实验的数据组
        data = self.main_window.canvas.coaxial_data
        if not data.data_groups:
            QMessageBox.information(self, "提示", "没有数据，请先记录数据点！")
            return
        
        # 清空表格（保留表头）
        for i in range(10):
            for j in range(4):
                self.equipotential_table.setItem(i, j, QTableWidgetItem(""))
        
        # 同轴电缆参数
        r1 = 18  # 内圆柱半径（像素）
        r2 = 152  # 外圆环内半径（像素）
        scale = 0.5  # 1px = 0.5mm
        
        row = 0
        for group_id, group in data.data_groups.items():
            if row >= 10:
                break
            if not group.points:
                continue
            
            # 实测电压 = 组电压
            measured_voltage = group.voltage
            
            # 计算所有点到中心(315, 235)的距离平均值（像素）
            cx, cy = 315, 235
            total_r = 0
            count = 0
            for x, y in group.points:
                r = math.sqrt((x - cx)**2 + (y - cy)**2)
                total_r += r
                count += 1
            
            if count == 0:
                continue
            
            avg_r_px = total_r / count
            avg_r_mm = avg_r_px * scale
            avg_d_mm = avg_r_mm * 2
            
            # 计算半径理论值
            # voltage = v1 * ln(r2/r) / ln(r2/r1)
            # => ln(r2/r) = voltage * ln(r2/r1) / v1
            # => r2/r = exp(voltage * ln(r2/r1) / v1)
            # => r = r2 / exp(voltage * ln(r2/r1) / v1)
            v1 = self.main_window.voltage
            if v1 > 0 and measured_voltage >= 0:
                try:
                    theoretical_r_px = r2 / math.exp(measured_voltage * math.log(r2 / r1) / v1)
                    theoretical_r_mm = theoretical_r_px * scale
                    # 限制在合理范围内
                    if theoretical_r_mm < 0:
                        theoretical_r_mm = 0
                    elif theoretical_r_mm > 75:
                        theoretical_r_mm = 75
                except:
                    theoretical_r_mm = 0
            else:
                theoretical_r_mm = 0
            
            # 填入表格
            self.equipotential_table.setItem(row, 0, QTableWidgetItem(f"{measured_voltage:.2f}"))
            self.equipotential_table.setItem(row, 1, QTableWidgetItem(f"{avg_d_mm:.1f}"))
            self.equipotential_table.setItem(row, 2, QTableWidgetItem(f"{avg_r_mm:.1f}"))
            self.equipotential_table.setItem(row, 3, QTableWidgetItem(f"{theoretical_r_mm:.1f}"))
            
            row += 1
        
        if row == 0:
            QMessageBox.information(self, "提示", "没有有效数据组可计算！")
        else:
            QMessageBox.information(self, "成功", f"已计算 {row} 组等势线数据！")
    
    def export_data(self):
        """导出等势线数据到CSV"""
        # 检查是否有数据
        has_data = False
        for i in range(10):
            if self.equipotential_table.item(i, 0) and self.equipotential_table.item(i, 0).text():
                has_data = True
                break
        
        if not has_data:
            QMessageBox.information(self, "提示", "没有数据可导出！请先计算。")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存等势线数据", "同轴电缆_等势线数据.csv", "CSV文件 (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['实测电压 Vr/V', '等势线直径 d/mm', '等势线半径 r/mm', '半径理论值 r\'/mm'])
                    for i in range(10):
                        row_data = []
                        for j in range(4):
                            item = self.equipotential_table.item(i, j)
                            row_data.append(item.text() if item else "")
                        if any(row_data):
                            writer.writerow(row_data)
                QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出失败: {str(e)}")
    
    def import_data(self):
        """导入等势线数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入等势线数据", "", "CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                lines = list(reader)
            
            if len(lines) < 2:
                QMessageBox.warning(self, "错误", "CSV文件格式错误或为空！")
                return
            
            # 跳过表头
            data_rows = lines[1:] if len(lines) > 0 else []
            
            # 清空表格
            for i in range(10):
                for j in range(4):
                    self.equipotential_table.setItem(i, j, QTableWidgetItem(""))
            
            row = 0
            for data_row in data_rows:
                if row >= 10:
                    break
                if len(data_row) >= 4:
                    self.equipotential_table.setItem(row, 0, QTableWidgetItem(data_row[0].strip()))
                    self.equipotential_table.setItem(row, 1, QTableWidgetItem(data_row[1].strip()))
                    self.equipotential_table.setItem(row, 2, QTableWidgetItem(data_row[2].strip()))
                    self.equipotential_table.setItem(row, 3, QTableWidgetItem(data_row[3].strip()))
                    row += 1
            
            QMessageBox.information(self, "成功", f"成功导入 {row} 行数据！")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导入失败: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("静电场描绘实验")
        self.setGeometry(100, 100, 1100, 700)
        self.setFixedSize(1100, 700)
        self.voltage = 0.0
        self.is_output_mode = True
        self.field_type = "line"
        self.arrow_label = None
        self.power_btn = None
        
        # 长按微调相关
        self.long_press_timer = QTimer()
        self.long_press_timer.timeout.connect(self.long_press_repeat)
        self.long_press_delta = 0.0
        self.long_press_initial_delay = 500
        self.long_press_interval = 100
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # ===== 左侧区域 =====
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 顶部选项卡
        tab_layout = QHBoxLayout()
        self.line_btn = QPushButton("无限长带电直导线的静电场")
        self.line_btn.setCheckable(True)
        self.line_btn.setChecked(True)
        self.line_btn.clicked.connect(lambda: self.change_field_type("line"))
        
        self.coaxial_btn = QPushButton("无限长带电直同轴电缆的静电场")
        self.coaxial_btn.setCheckable(True)
        self.coaxial_btn.clicked.connect(lambda: self.change_field_type("coaxial"))
        
        tab_layout.addWidget(self.line_btn)
        tab_layout.addWidget(self.coaxial_btn)
        tab_layout.addStretch()
        left_layout.addLayout(tab_layout)
        
        # 画布
        self.canvas = ElectricFieldCanvas(self)
        left_layout.addWidget(self.canvas)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        self.draw_btn = QPushButton("连线")
        self.draw_btn.clicked.connect(self.draw_lines)

        self.export_btn = QPushButton("导出数据(CSV)")
        self.export_btn.clicked.connect(self.export_data)

        self.import_btn = QPushButton("导入数据")
        self.import_btn.clicked.connect(self.import_data)

        self.delete_row_btn = QPushButton("删除行")
        self.delete_row_btn.clicked.connect(self.delete_selected_row)

        self.clear_group_btn = QPushButton("清空当前表格")
        self.clear_group_btn.clicked.connect(self.clear_current_group)

        action_layout.addWidget(self.draw_btn)
        action_layout.addWidget(self.export_btn)
        action_layout.addWidget(self.import_btn)
        action_layout.addWidget(self.delete_row_btn)
        action_layout.addWidget(self.clear_group_btn)
        left_layout.addLayout(action_layout)
        
        # ===== 中间区域 =====
        middle_widget = QWidget()
        middle_widget.setFixedWidth(450)
        middle_layout = QVBoxLayout(middle_widget)
        
        # 主机图片容器
        host_container = QWidget()
        host_container.setFixedSize(430, 280)
        host_layout = QVBoxLayout(host_container)
        host_layout.setContentsMargins(0, 0, 0, 0)
        
        # 主机图片
        host_label = QLabel()
        host_label.setFixedSize(430, 280)
        host_path = get_resource_path("background/主机.jpg")
        if os.path.exists(host_path):
            host_pixmap = QPixmap(host_path)
            host_pixmap = host_pixmap.scaled(430, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            host_label.setPixmap(host_pixmap)
        else:
            host_label.setText("主机.jpg")
            host_label.setStyleSheet("border: 1px solid gray;")
        host_label.setAlignment(Qt.AlignCenter)
        host_layout.addWidget(host_label)
        
        # 电压显示
        self.voltage_display = QLabel("0.00", host_container)
        self.voltage_display.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: black;
                font-size: 40px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
            }
        """)
        self.voltage_display.setAlignment(Qt.AlignCenter)
        self.voltage_display.setFixedSize(150, 55)
        self.voltage_display.move(23, 90)
        
        # 箭头
        self.arrow_label = QLabel("←", host_container)
        self.arrow_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: red;
                font-size: 40px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
            }
        """)
        self.arrow_label.setAlignment(Qt.AlignCenter)
        self.arrow_label.adjustSize()
        self.arrow_label.move(85, 155)
        
        # 电源按钮
        self.power_btn = QPushButton("", host_container)
        self.power_btn.setFixedSize(40, 40)
        self.power_btn.setCheckable(True)
        self.power_btn.setChecked(False)
        self.power_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: transparent;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 30);
                border-radius: 20px;
            }
        """)
        self.power_btn.setToolTip("点击打开电压显示")
        self.power_btn.clicked.connect(self.toggle_power)
        self.power_btn.move(366, 143)
                
        middle_layout.addWidget(host_container)
        
        # 电压控制
        voltage_layout = QHBoxLayout()
        voltage_layout.addWidget(QLabel("电源电压:"))
        
        self.voltage_slider = QSlider(Qt.Horizontal)
        self.voltage_slider.setRange(0, 1500)
        self.voltage_slider.setValue(0)
        self.voltage_slider.valueChanged.connect(self.on_voltage_changed)
        voltage_layout.addWidget(self.voltage_slider)
        
        self.voltage_label = QLabel("0.00")
        self.voltage_label.setFixedWidth(60)
        voltage_layout.addWidget(self.voltage_label)
        
        self.minus_btn = QPushButton("-")
        self.minus_btn.pressed.connect(lambda: self.start_long_press(-0.01))
        self.minus_btn.released.connect(self.stop_long_press)
        self.minus_btn.setStyleSheet("QPushButton { font-size: 16px; padding: 5px 15px; }")

        self.plus_btn = QPushButton("+")
        self.plus_btn.pressed.connect(lambda: self.start_long_press(0.01))
        self.plus_btn.released.connect(self.stop_long_press)
        self.plus_btn.setStyleSheet("QPushButton { font-size: 16px; padding: 5px 15px; }")

        voltage_layout.addWidget(self.minus_btn)
        voltage_layout.addWidget(self.plus_btn)
        middle_layout.addLayout(voltage_layout)
        
        # 输出/测量切换
        self.output_btn = QPushButton("输出")
        self.output_btn.setCheckable(True)
        self.output_btn.setChecked(True)
        self.output_btn.clicked.connect(self.toggle_output_mode)
        self.output_btn.setStyleSheet("QPushButton { font-size: 16px; padding: 10px; }")
        middle_layout.addWidget(self.output_btn)
        
        # ===== 数据表格区域 =====
        table_group = QGroupBox("数据表格")
        table_layout = QVBoxLayout(table_group)
        
        # 组选择
        group_select_layout = QHBoxLayout()
        group_select_layout.addWidget(QLabel("选择组:"))
        self.group_combo = QComboBox()
        self.group_combo.currentIndexChanged.connect(self.on_group_changed)
        group_select_layout.addWidget(self.group_combo)
        
        # 添加组按钮
        self.add_group_btn = QPushButton("新建组")
        self.add_group_btn.clicked.connect(self.add_new_group)
        group_select_layout.addWidget(self.add_group_btn)
        group_select_layout.addStretch()
        table_layout.addLayout(group_select_layout)
        
        # 组电压输入
        voltage_input_layout = QHBoxLayout()
        voltage_input_layout.addWidget(QLabel("组电压(V):"))
        self.group_voltage_input = QLineEdit("0.00")
        self.group_voltage_input.setFixedWidth(80)
        self.group_voltage_input.editingFinished.connect(self.on_group_voltage_changed)
        voltage_input_layout.addWidget(self.group_voltage_input)
        voltage_input_layout.addStretch()
        table_layout.addLayout(voltage_input_layout)
        
        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["X (px)", "Y (px)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMaximumHeight(200)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        table_layout.addWidget(self.table)
        
        middle_layout.addWidget(table_group)
        middle_layout.addStretch()
        
        # ===== 右侧区域（同轴电缆参数和等势线表格） =====
        self.coaxial_params = CoaxialParamsWidget(self)
        self.coaxial_params.setFixedWidth(430)
        
        # 添加到主布局
        main_layout.addWidget(left_widget, 2)
        main_layout.addWidget(middle_widget, 1)
        main_layout.addWidget(self.coaxial_params, 1)
        
        # 初始化
        self.canvas.line_data.add_data_group(0.0)
        self.canvas.coaxial_data.add_data_group(0.0)
        self.canvas.current_data = self.canvas.line_data
        self.update_group_combo()
        self.update_table()
        
        # 电源默认关闭
        self.voltage_display.setVisible(False)
        self.arrow_label.setVisible(False)
        self.update_voltage_display(0.0)
        
        # 默认隐藏同轴电缆参数
        self.coaxial_params.setVisible(False)
    
    def start_long_press(self, delta):
        self.long_press_delta = delta
        self.adjust_voltage(delta)
        self.long_press_timer.start(self.long_press_initial_delay)

    def stop_long_press(self):
        self.long_press_timer.stop()

    def long_press_repeat(self):
        self.long_press_timer.setInterval(self.long_press_interval)
        self.adjust_voltage(self.long_press_delta)

    def delete_selected_row(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择要删除的行！")
            return
        
        data = self.canvas.get_current_data()
        group_id = data.current_group_id
        if group_id not in data.data_groups:
            return
        
        group = data.data_groups[group_id]
        
        rows_to_delete = sorted([row.row() for row in selected_rows], reverse=True)
        for row in rows_to_delete:
            if row < len(group.points):
                del group.points[row]
        
        self.update_table()
        self.canvas.update()

    def import_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入数据", "", "CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                lines = list(reader)
            
            if len(lines) < 2:
                QMessageBox.warning(self, "错误", "CSV文件格式错误或为空！")
                return
            
            header = lines[0]
            has_header = False
            if len(header) >= 4 and header[0] == '组号' and header[1] == '电压(V)':
                has_header = True
                data_rows = lines[1:]
            else:
                data_rows = lines
            
            group_data = {}
            voltage_data = {}
            max_group_id = 0
            
            for row in data_rows:
                if len(row) < 4:
                    continue
                try:
                    group_id = int(float(row[0])) - 1
                    voltage = float(row[1])
                    x = float(row[2])
                    y = float(row[3])
                    
                    if group_id not in group_data:
                        group_data[group_id] = []
                        voltage_data[group_id] = voltage
                    group_data[group_id].append((x, y))
                    
                    if group_id > max_group_id:
                        max_group_id = group_id
                except (ValueError, IndexError):
                    continue
            
            if not group_data:
                QMessageBox.warning(self, "错误", "无法解析数据，请确保格式为：组号,电压(V),X (px),Y (px)")
                return
            
            data = self.canvas.get_current_data()
            
            imported_count = 0
            new_groups = 0
            
            for group_id, points in group_data.items():
                if group_id not in data.data_groups:
                    voltage = voltage_data.get(group_id, 0.0)
                    new_group_id = data.add_data_group(voltage)
                    if new_group_id != group_id:
                        pass
                    new_groups += 1
                else:
                    if group_id in voltage_data:
                        data.data_groups[group_id].voltage = voltage_data[group_id]
                
                group = data.data_groups[group_id]
                for x, y in points:
                    group.points.append((x, y))
                    imported_count += 1
            
            first_group = min(group_data.keys())
            if first_group in data.data_groups:
                data.current_group_id = first_group
            
            self.update_group_combo()
            self.update_table()
            self.canvas.update()
            self.update_group_voltage()
            
            QMessageBox.information(
                self, "成功", 
                f"成功导入 {imported_count} 个数据点！\n"
                f"涉及 {len(group_data)} 个组，新建 {new_groups} 个组"
            )
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导入失败: {str(e)}")
            
    def update_group_voltage(self):
        group_id = self.canvas.get_current_group_id()
        voltage = self.canvas.get_group_voltage(group_id)
        self.group_voltage_input.setText(f"{voltage:.2f}")

    def on_data_switched(self):
        self.update_group_combo()
        self.update_table()
        self.update_voltage()
        # 显示/隐藏同轴电缆参数
        if self.field_type == "coaxial":
            self.coaxial_params.setVisible(True)
            self.coaxial_params.update_params(self.voltage)
        else:
            self.coaxial_params.setVisible(False)
    
    def update_group_combo(self):
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        data = self.canvas.get_current_data()
        for i in range(len(data.data_groups)):
            self.group_combo.addItem(f"组 {i + 1}")
        if data.data_groups:
            self.group_combo.setCurrentIndex(data.current_group_id)
        self.group_combo.blockSignals(False)
    
    def add_new_group(self):
        data = self.canvas.get_current_data()
        if len(data.data_groups) >= 10:
            QMessageBox.warning(self, "提示", "已达到最大组数限制（10组）！")
            return
        
        group_id = self.canvas.add_data_group()
        self.update_group_combo()
        self.group_combo.setCurrentIndex(group_id)
        self.update_table()
        self.group_voltage_input.setText("0.00")
    
    def on_group_changed(self, index):
        if index >= 0:
            self.canvas.set_current_group_id(index)
            voltage = self.canvas.get_group_voltage(index)
            self.group_voltage_input.setText(f"{voltage:.2f}")
            self.update_table()
            self.canvas.update()
    
    def on_group_voltage_changed(self):
        try:
            voltage = float(self.group_voltage_input.text())
            group_id = self.canvas.get_current_group_id()
            self.canvas.set_group_voltage(group_id, voltage)
        except:
            pass
    
    def update_table(self):
        self.table.setRowCount(0)
        data = self.canvas.get_current_data()
        group_id = data.current_group_id
        if group_id in data.data_groups:
            group = data.data_groups[group_id]
            for i, (x, y) in enumerate(group.points):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(f"{x:.0f}"))
                self.table.setItem(i, 1, QTableWidgetItem(f"{y:.0f}"))
    
    def update_voltage(self):
        if not self.is_output_mode:
            self.canvas.update_voltage()
    
    def draw_lines(self):
        self.canvas.draw_all_lines()
    
    def clear_current_group(self):
        data = self.canvas.get_current_data()
        group_id = data.current_group_id
        if group_id not in data.data_groups:
            return
        
        group = data.data_groups[group_id]
        if not group.points:
            QMessageBox.information(self, "提示", "当前表格没有数据可清空！")
            return
        
        reply = QMessageBox.question(
            self, "确认清空", 
            f"确定要清空当前组（组 {group_id + 1}）的所有数据点吗？\n当前共有 {len(group.points)} 个数据点。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.canvas.clear_current_group()
            self.update_table()
            QMessageBox.information(self, "成功", "当前表格已清空！")
    
    def toggle_power(self):
        if self.power_btn.isChecked():
            self.power_btn.setToolTip("点击关闭电压显示")
            self.voltage_display.setVisible(True)
            self.arrow_label.setVisible(True)
            if self.is_output_mode:
                self.voltage_display.setText(f"{self.voltage:.2f}")
            else:
                self.canvas.update_voltage()
        else:
            self.power_btn.setToolTip("点击打开电压显示")
            self.voltage_display.setVisible(False)
            self.arrow_label.setVisible(False)
    
    def change_field_type(self, field_type):
        if field_type == self.field_type:
            return
        
        self.canvas.switch_field_type(field_type)
        
        if field_type == "line":
            self.line_btn.setChecked(True)
            self.coaxial_btn.setChecked(False)
            # 直导线实验：显示较窄窗口
            self.setFixedSize(1100, 700)
            self.coaxial_params.setVisible(False)
        else:
            self.line_btn.setChecked(False)
            self.coaxial_btn.setChecked(True)
            # 同轴电缆实验：显示较宽窗口
            self.setFixedSize(1520, 700)
            self.coaxial_params.setVisible(True)
            self.coaxial_params.update_params(self.voltage)
        
        self.field_type = field_type
        
        self.update_group_combo()
        self.update_table()
        if not self.is_output_mode:
            self.canvas.update_voltage()
        
    def on_voltage_changed(self, value):
        voltage = round(value / 100.0, 2)
        self.voltage = voltage
        self.voltage_label.setText(f"{voltage:.2f}")
        if self.power_btn.isChecked():
            if self.is_output_mode:
                self.voltage_display.setText(f"{voltage:.2f}")
            else:
                self.canvas.update_voltage()
        # 更新同轴电缆参数中的V1
        if self.field_type == "coaxial":
            self.coaxial_params.update_params(voltage)
    
    def adjust_voltage(self, delta):
        new_voltage = round(self.voltage + delta, 2)
        if new_voltage < 0:
            new_voltage = 0
            if delta < 0:
                self.long_press_timer.stop()
        elif new_voltage > 15:
            new_voltage = 15
            if delta > 0:
                self.long_press_timer.stop()
        slider_value = int(round(new_voltage * 100))
        self.voltage_slider.setValue(slider_value)
    
    def toggle_output_mode(self):
        self.is_output_mode = not self.is_output_mode
        if self.is_output_mode:
            self.output_btn.setText("输出")
            self.output_btn.setChecked(True)
            self.voltage_slider.setEnabled(True)
            self.minus_btn.setEnabled(True)
            self.plus_btn.setEnabled(True)
            if self.power_btn.isChecked():
                self.voltage_display.setText(f"{self.voltage:.2f}")
            self.arrow_label.setText("←")
        else:
            self.output_btn.setText("测量")
            self.output_btn.setChecked(False)
            self.voltage_slider.setEnabled(False)
            self.minus_btn.setEnabled(False)
            self.plus_btn.setEnabled(False)
            if self.power_btn.isChecked():
                self.canvas.update_voltage()
            self.arrow_label.setText("→")
    
    def update_voltage_display(self, voltage):
        if not self.is_output_mode and self.power_btn.isChecked():
            self.voltage_display.setText(f"{voltage:.2f}")
    
    def export_data(self):
        all_data = self.canvas.get_all_data_for_export()
        if not all_data:
            QMessageBox.information(self, "提示", "没有数据可导出！")
            return
        
        exp_name = "直导线" if self.field_type == "line" else "同轴电缆"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存数据", f"{exp_name}_数据.csv", "CSV文件 (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['组号', '电压(V)', 'X (px)', 'Y (px)'])
                    for data in all_data:
                        for x, y in data['points']:
                            writer.writerow([
                                data['group_id'] + 1,
                                f"{data['voltage']:.2f}",
                                f"{x:.0f}",
                                f"{y:.0f}"
                            ])
                QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出失败: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())