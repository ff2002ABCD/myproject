import sys
import time
import os
import pandas as pd
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGroupBox, QLabel, QDial, QComboBox, QFrame, QPushButton, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF
from PyQt5.QtCore import QPoint, QPointF
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QButtonGroup
from PyQt5.QtWidgets import QMessageBox

class DataPointDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_points = []  # 确保在这里初始化data_points
        self.setMinimumHeight(100)
        self.cursor_pos = None
        self.setMouseTracking(True)  # 启用鼠标跟踪
        
        # 添加导出按钮
        self.export_btn = QPushButton("导出数据", self)
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setFixedSize(100, 30)
        self.export_btn.move(10, 10)  # 放置在左上角
        self.export_btn.hide()  # 初始隐藏
        
        # View control variables
        self.x_min = 0      # Current visible x-axis minimum
        self.x_max = 26     # Current visible x-axis maximum (26 seconds)
        self.y_min = -50    # Current visible y-axis minimum
        self.y_max = 200    # Current visible y-axis maximum
        self.selection_rect = None
        self.selection_start = None
        self.last_pan_pos = None  # For right-click panning
        self.show_tooltip = True  # Always show tooltip on hover
        
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
            # 创建DataFrame
            df = pd.DataFrame(self.data_points, columns=['时间(S)', '拉力(mV)'])
            
            # 保存为Excel
            df.to_excel(file_path, index=False)
            
            # 提示用户保存成功
            QMessageBox.information(self, "导出成功", f"数据已成功导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出数据时出错:\n{str(e)}")
    
    def set_data_points(self, points):
        """设置数据点"""
        self.data_points = points
        self.export_btn.show()  # 显示导出按钮
        self.reset_view()
        self.update()
              
    def reset_view(self):
        """Reset view to default ranges"""
        self.x_min = 0
        self.x_max = 26
        self.y_min = -50
        self.y_max = 200

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        self.cursor_pos = event.pos()
        
        # Handle right-click panning
        if event.buttons() & Qt.RightButton and self.last_pan_pos:
            delta = event.pos() - self.last_pan_pos
            self.pan_view(delta.x(), delta.y())
            self.last_pan_pos = event.pos()
            
        # Handle selection rectangle
        if event.buttons() & Qt.LeftButton and self.selection_start:
            self.selection_rect = QRectF(self.selection_start, QPointF(event.pos()))
            
        self.update()
        super().mouseMoveEvent(event)

    def pan_view(self, dx, dy):
        """Pan the view by the specified pixel amounts"""
        width = self.width()
        height = self.height()
        
        axis_start_x = 50
        axis_end_x = width - 20
        axis_width = axis_end_x - axis_start_x
        axis_y_top = 20
        axis_y_bottom = height - 20
        
        # Calculate data range per pixel
        x_pixels_per_unit = axis_width / (self.x_max - self.x_min)
        y_pixels_per_unit = (axis_y_bottom - axis_y_top) / (self.y_max - self.y_min)
        
        # Convert pixel delta to data delta
        x_delta = dx / x_pixels_per_unit
        y_delta = dy / y_pixels_per_unit
        
        # Apply panning with boundary checks
        new_x_min = self.x_min - x_delta
        new_x_max = self.x_max - x_delta
        new_y_min = self.y_min + y_delta
        new_y_max = self.y_max + y_delta
        
        # Don't pan beyond data boundaries
        if new_x_min >= 0 and new_x_max <= 26:
            self.x_min = new_x_min
            self.x_max = new_x_max
            
        if new_y_min >= -100 and new_y_max <= 300:  # With some buffer
            self.y_min = new_y_min
            self.y_max = new_y_max

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # Start selection rectangle
            self.selection_start = QPointF(event.pos())
            self.selection_rect = QRectF(self.selection_start, self.selection_start)
        elif event.button() == Qt.RightButton:
            # Start panning
            self.last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.selection_start:
            # Finish selection rectangle
            if self.selection_rect and self.selection_rect.width() > 5 and self.selection_rect.height() > 5:
                self.zoom_to_selection()
            self.selection_start = None
            self.selection_rect = None
        elif event.button() == Qt.RightButton:
            # Stop panning
            self.last_pan_pos = None
            self.setCursor(Qt.ArrowCursor)
            
        self.update()
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """鼠标滚轮事件 - 以坐标轴中央为中心缩放（X轴和Y轴都基于中心点缩放）"""
        # 计算坐标轴中心点（X轴和Y轴各自的中点）
        axis_center_x = (self.x_min + self.x_max) / 2
        axis_center_y = (self.y_min + self.y_max) / 2
        
        # 确定缩放方向（向上滚动缩小范围/放大，向下滚动扩大范围/缩小）
        zoom_in = event.angleDelta().y() > 0
        zoom_factor = 0.9 if zoom_in else 1.1  # 缩小范围用0.9，扩大范围用1.1
        
        # 计算新的X轴范围（以X轴中心点为中心）
        new_x_range = (self.x_max - self.x_min) * zoom_factor
        self.x_min = max(0, axis_center_x - new_x_range/2)
        self.x_max = min(26, axis_center_x + new_x_range/2)
        
        # 计算新的Y轴范围（以Y轴中心点为中心）
        new_y_range = (self.y_max - self.y_min) * zoom_factor
        self.y_min = max(-100, axis_center_y - new_y_range/2)
        self.y_max = min(300, axis_center_y + new_y_range/2)
        
        # 防止过度缩放（设置最小范围限制）
        if self.x_max - self.x_min < 0.1:  # X轴最小时间范围0.1秒
            self.x_min = axis_center_x - 0.05
            self.x_max = axis_center_x + 0.05
        
        if self.y_max - self.y_min < 1:  # Y轴最小拉力范围1mV
            self.y_min = axis_center_y - 0.5
            self.y_max = axis_center_y + 0.5
        
        self.update()  # 更新视图

    def zoom_to_selection(self):
        """Zoom to the selected rectangle in data coordinates"""
        if not self.selection_rect:
            return
            
        width = self.width()
        height = self.height()
        
        # Coordinate system parameters
        axis_start_x = 50
        axis_end_x = width - 20
        axis_width = axis_end_x - axis_start_x
        axis_y_top = 20
        axis_y_bottom = height - 20
        
        # Convert selection rectangle to data coordinates
        sel_x1 = self.selection_rect.left()
        sel_x2 = self.selection_rect.right()
        sel_y1 = self.selection_rect.top()
        sel_y2 = self.selection_rect.bottom()
        
        # Calculate data ranges from pixel coordinates
        x1_data = self.x_min + (sel_x1 - axis_start_x) / axis_width * (self.x_max - self.x_min)
        x2_data = self.x_min + (sel_x2 - axis_start_x) / axis_width * (self.x_max - self.x_min)
        y1_data = self.y_max - (sel_y1 - axis_y_top) / (axis_y_bottom - axis_y_top) * (self.y_max - self.y_min)
        y2_data = self.y_max - (sel_y2 - axis_y_top) / (axis_y_bottom - axis_y_top) * (self.y_max - self.y_min)
        
        # Set new ranges (swap if needed to keep min < max)
        self.x_min = min(x1_data, x2_data)
        self.x_max = max(x1_data, x2_data)
        self.y_min = min(y1_data, y2_data)
        self.y_max = max(y1_data, y2_data)
        
        # Ensure we don't zoom too much
        if self.x_max - self.x_min < 0.1:  # Minimum 0.1 second range
            x_center = (self.x_min + self.x_max) / 2
            self.x_min = x_center - 0.05
            self.x_max = x_center + 0.05
            
        if self.y_max - self.y_min < 1:  # Minimum 1 mV range
            y_center = (self.y_min + self.y_max) / 2
            self.y_min = y_center - 0.5
            self.y_max = y_center + 0.5
            
        self.update()

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.cursor_pos = None
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        if not hasattr(self, 'data_points') or not self.data_points:
            return
            
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
        
        # 绘制背景和坐标轴
        painter.fillRect(0, 0, width, height, QColor(240, 240, 240))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(axis_start_x, axis_y_bottom, axis_end_x, axis_y_bottom)  # X轴
        painter.drawLine(axis_start_x, axis_y_top, axis_start_x, axis_y_bottom)   # Y轴
        
        # 绘制X轴主刻度和标签
        x_range = self.x_max - self.x_min
        if x_range <= 2:
            major_interval = 0.2
        elif x_range <= 5:
            major_interval = 0.5
        elif x_range <= 10:
            major_interval = 1
        else:
            major_interval = 2
            
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
            y_interval = 2
        elif y_range <= 50:
            y_interval = 5
        elif y_range <= 100:
            y_interval = 10
        else:
            y_interval = 20
            
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
        
        # 绘制鼠标光标和数值提示 (always show when hovering)
        if self.cursor_pos and self.show_tooltip:
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
        
        # Draw selection rectangle
        if self.selection_rect:
            painter.setPen(QPen(QColor(0, 0, 255), 1, Qt.DashLine))
            painter.setBrush(QBrush(QColor(100, 100, 255, 50)))
            painter.drawRect(self.selection_rect)

# ... (rest of the code remains the same)

class SurfaceTensionDiagram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lift_position = 50  # 升降台位置 (0-100)
        self.weight_count = 0    # 砝码个数
        self.is_ring = False    # 是否显示圆环
        self.setMinimumSize(300, 300)
    
    def set_weight_count(self, count, is_ring=False):
        """设置砝码个数或圆环"""
        self.weight_count = count
        self.is_ring = is_ring
        self.update()
    
    def is_ring_in_water(self):
        """检测圆环是否浸入水中"""
        if not self.is_ring:
            return False
            
        # 计算圆环底部位置
        ring_bottom = int(self.height() * 0.2) + 40 + 30  # 传感器y + 连接线高度 + 圆环高度
        
        # 计算水面位置
        water_top = int(self.height() * (0.5 + 0.3 * (self.lift_position/100))) - 40  # 升降台y - 水高度
        
        return ring_bottom > water_top  # 圆环底部低于水面即为浸入

    def is_weight_in_water(self):
        """检测砝码是否浸入水中"""
        if self.weight_count < 1:
            return False
            
        # 计算砝码底部位置
        weight_bottom = int(self.height() * 0.2) + 40 + 30  # 传感器y + 连接线高度 + 砝码高度
        
        # 计算水面位置
        water_top = int(self.height() * (0.5 + 0.3 * (self.lift_position/100))) - 40  # 升降台y - 水高度
        
        return weight_bottom > water_top  # 砝码底部低于水面即为浸入

    def set_lift_position(self, position):
    # 当升降台位置重置到顶部时，清除接触状态
        if position <= 10:  # 假设5%位置是最高点
            if hasattr(self, 'has_contacted_water'):
                del self.has_contacted_water
        self.lift_position = position
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Convert all coordinates to integers
        left_x = int(width * 0.3)
        right_x = int(width * 0.7)
        base_left = int(width * 0.2)
        base_right = int(width * 0.8)
        top_y = int(height * 0.1)
        bottom_y = int(height * 0.8)
        
        # 绘制背景
        painter.fillRect(0, 0, width, height, QColor(240, 240, 240))
        
        # 绘制支架
        painter.setPen(QPen(Qt.black, 3))
        painter.drawLine(left_x, top_y, left_x, bottom_y)  # 左支架
        painter.drawLine(right_x, top_y, right_x, bottom_y)  # 右支架
        painter.drawLine(base_left, bottom_y, base_right, bottom_y)  # 底座
        
        # 绘制拉力传感器
        sensor_y = int(height * 0.2)
        sensor_width = int(width * 0.2)
        sensor_x = int(width * 0.4)
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(sensor_x, sensor_y, sensor_width, 20)  # 传感器主体
        painter.drawLine(int(width*0.5), sensor_y+20, int(width*0.5), sensor_y+40)  # 传感器连接线
        
        # 绘制砝码或圆环
        weight_y = sensor_y + 40
        weight_width = int(width * 0.1)
        weight_x = int(width * 0.45)
        
        # 绘制升降台
        lift_y = int(height * (0.544 + 0.17 * (self.lift_position/100)))
        lift_width = int(width * 0.6)
        lift_x = int(width * 0.2)
        painter.setBrush(QBrush(QColor(150, 150, 150)))
        painter.drawRect(lift_x, lift_y, lift_width, 15)
        
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
        if self.weight_count >= 1:
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.drawRect(weight_x, weight_y, weight_width, 30)
            
            # 计算浸入水中的高度（限制最多7像素）
            submerged_height = min(7, max(0, (weight_y + 30) - water_top))
            
            # 绘制浸入水中的部分
            if submerged_height > 0:
                painter.setBrush(QBrush(QColor(150, 150, 200)))
                painter.drawRect(weight_x, weight_y + (30 - submerged_height), 
                            weight_width, submerged_height)
                self.has_contacted_water = True  # 标记已接触过水面
                self.water_column_broken = False  # 重置断裂状态
            
            # # 只有当圆环曾经接触过水面且水柱未断裂时才显示水柱
            # if (hasattr(self, 'has_contacted_water') and self.has_contacted_water and 
            #     self.is_ring and not getattr(self, 'water_column_broken', False)):
                
            # 计算圆环底部与水面的距离
            distance = water_top - (weight_y + 30)
            
            if distance > 14:  # 水柱断裂
                self.water_column_broken = True
            elif 0 < distance <= 14:  # 显示水柱
                # 计算梯形水柱参数
                water_column_top = weight_y + 30
                water_column_height = min(14, distance)
                
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
        if self.weight_count >= 1:
            if self.is_ring:
                painter.drawText(weight_x, weight_y+0, "圆环")
            else:
                painter.drawText(weight_x, weight_y+0, f"砝码 x{self.weight_count}")
        painter.drawText(lift_x, lift_y-5, "升降台")
        painter.drawText(water_x, water_top-5, "液面")

class SurfaceTensionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.using_ring = False
        self.setWindowTitle("FD-NST-D 液体表面张力系数测量仪")
        self.setGeometry(100, 100, 800, 600)
        self.querying_data = False
        self.current_group = 1
        self.current_point_index = 0
        
        # 状态变量
        self.min_speed= 2.5
        self.lift_speed = self.min_speed
        # self.excel_data = self.load_excel_data()  # 加载Excel数据
        self.current_selection = 0
        self.interval = 0.1
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
        self.init_left_area()
        self.init_center_area()
        self.init_right_area()
        
        self.update_selection_arrow()
        
        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid gray;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QFrame {
                border: 1px solid #ccc;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton {
                min-width: 80px;
                margin: 5px;
            }
            QTextEdit {
                font-size: 24px;
                padding: 20px;
            }
            QDial {
                min-width: 120px;
                min-height: 120px;
            }
        """)

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
        self.left_display_frame.setLayout(self.left_display_layout)
        
        # 左侧显示框内容
        self.display_box = QGroupBox("系统状态")
        self.display_layout = QVBoxLayout()
        self.display_layout.setSpacing(0)  # 减少组件间距
        
        # 四个栏目
        self.items = [
            f"采集间隔：{self.interval}s",
            "传感器定标",
            "表面张力测量",
            "数据查询"
        ]
        
        # 存储所有的栏目标签
        self.item_labels = []
        
        for i, item in enumerate(self.items):
            label = QLabel(item)
            label.setStyleSheet("""
                font-size: 16px; 
                padding: 10px; 
                border-bottom: 1px solid #ccc;
            """)
            self.display_layout.addWidget(label)
            self.item_labels.append(label)
        
        # 传感器定标时显示的文本框
        self.force_display = QTextEdit()
        self.force_display.setText("当前拉力：0.0mV")
        self.force_display.setAlignment(Qt.AlignCenter)
        self.force_display.setReadOnly(True)
        self.force_display.hide()
        
        # 表面张力测量时显示的文本框 - 高度设置为1/3
        self.tension_display = QTextEdit()
        self.tension_display.setText("No.1 拉力：0mV")
        self.tension_display.setAlignment(Qt.AlignCenter)
        self.tension_display.setReadOnly(True)
        self.tension_display.hide()
        self.tension_display.setMaximumHeight(80)  # 限制最大高度
        
        # 数据点阵显示 - 高度设置为2/3
        self.data_display = DataPointDisplay()
        self.data_display.hide()
        self.data_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 创建测量模式的专用布局
        self.measurement_layout = QVBoxLayout()
        self.measurement_layout.addWidget(self.tension_display, 1)  # 1份高度
        self.measurement_layout.addWidget(self.data_display, 2)     # 2份高度
        self.measurement_layout.setContentsMargins(10, 10, 10, 10)  # 添加边距
        
        # 将测量布局放入一个容器中
        self.measurement_container = QWidget()
        self.measurement_container.setLayout(self.measurement_layout)
        self.measurement_container.setStyleSheet("background-color: #f0f0f0;")  # 设置背景色
        self.measurement_container.hide()
        
        # 修改这里：将栏目标签放入一个单独的容器中
        self.labels_container = QWidget()
        self.labels_container.setLayout(self.display_layout)
        
        self.display_box_layout = QVBoxLayout()
        self.display_box_layout.addWidget(self.labels_container)
        self.display_box_layout.addWidget(self.force_display)
        self.display_box_layout.addWidget(self.measurement_container)
        self.display_box.setLayout(self.display_box_layout)
        
        self.left_display_layout.addWidget(self.display_box)

        # 左侧控制按钮区域
        self.left_control_frame = QFrame()
        self.left_control_layout = QVBoxLayout()
        self.left_control_frame.setLayout(self.left_control_layout)
        
        # 砝码控制区域 - 增加高度
        self.weight_control = QGroupBox("悬挂物体控制")
        self.weight_layout = QHBoxLayout()

        self.add_weight_btn = QPushButton("增加砝码")
        self.add_weight_btn.clicked.connect(self.on_add_weight)
        self.add_weight_btn.setMinimumHeight(60)

        self.remove_weight_btn = QPushButton("减少砝码")
        self.remove_weight_btn.clicked.connect(self.on_remove_weight)
        self.remove_weight_btn.setMinimumHeight(60)

        # Create vertical layout container for weight info
        weight_info_layout = QVBoxLayout()
        self.weight_count_label = QLabel("砝码个数: 0")
        self.weight_count_label.setAlignment(Qt.AlignCenter)
        self.weight_count_label.setStyleSheet("font-size: 16px;")
        self.weight_hint_label = QLabel("每个砝码重0.5g")
        self.weight_hint_label.setAlignment(Qt.AlignCenter)
        self.weight_hint_label.setStyleSheet("font-size: 12px; color: #666;")

        # New buttons
        self.replace_with_ring_btn = QPushButton("替换为圆环")
        self.replace_with_ring_btn.clicked.connect(self.on_replace_with_ring)
        self.replace_with_ring_btn.setMinimumHeight(60)
        self.replace_with_ring_btn.show()  # 改为show()而不是hide()

        self.replace_with_weights_btn = QPushButton("替换为砝码")
        self.replace_with_weights_btn.clicked.connect(self.on_replace_with_weights)
        self.replace_with_weights_btn.setMinimumHeight(60)
        self.replace_with_weights_btn.hide()

        weight_info_layout.addWidget(self.weight_count_label)
        weight_info_layout.addWidget(self.weight_hint_label)

        self.weight_layout.addWidget(self.remove_weight_btn)
        self.weight_layout.addLayout(weight_info_layout)
        self.weight_layout.addWidget(self.add_weight_btn)
        self.weight_layout.addWidget(self.replace_with_ring_btn)
        self.weight_layout.addWidget(self.replace_with_weights_btn)
        self.weight_control.setLayout(self.weight_layout)
        
        # # 添加提示文本
        # self.weight_hint_label = QLabel("每个砝码重0.5g")
        # self.weight_hint_label.setAlignment(Qt.AlignCenter)
        # self.weight_hint_label.setStyleSheet("font-size: 12px; color: #666;")
        
        # weight_info_layout.addWidget(self.weight_count_label)
        # weight_info_layout.addWidget(self.weight_hint_label)
        
        # self.weight_layout.addWidget(self.remove_weight_btn)
        # self.weight_layout.addLayout(weight_info_layout)  # 使用布局容器替代单独的标签
        # self.weight_layout.addWidget(self.add_weight_btn)
        # self.weight_control.setLayout(self.weight_layout)
        
        # 导航按钮区域 - 增加高度
        self.nav_control = QGroupBox("导航控制")
        self.nav_layout = QVBoxLayout()
        
        self.up_btn = QPushButton("上移")
        self.up_btn.clicked.connect(self.on_up_clicked)
        self.up_btn.setMinimumHeight(60)  # 增加按钮高度
        
        self.down_btn = QPushButton("下移")
        self.down_btn.clicked.connect(self.on_down_clicked)
        self.down_btn.setMinimumHeight(60)  # 增加按钮高度
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.on_ok_clicked)
        self.ok_btn.setMinimumHeight(60)  # 增加按钮高度
        
        self.back_btn = QPushButton("返回")
        self.back_btn.clicked.connect(self.on_back_clicked)
        self.back_btn.setMinimumHeight(60)  # 增加按钮高度
        
        self.nav_layout.addWidget(self.up_btn)
        self.nav_layout.addWidget(self.down_btn)
        self.nav_layout.addWidget(self.ok_btn)
        self.nav_layout.addWidget(self.back_btn)
        self.nav_control.setLayout(self.nav_layout)
        
        self.left_control_layout.addWidget(self.weight_control)
        self.left_control_layout.addWidget(self.nav_control)
        
        # 将左右两部分添加到左侧区域布局
        self.left_area_layout.addWidget(self.left_display_frame, 2)  # 显示区域占2/3
        self.left_area_layout.addWidget(self.left_control_frame, 1)  # 控制区域占1/3

    def init_center_area(self):
        """初始化中间区域"""
        self.center_frame = QFrame()
        self.center_frame.setFrameShape(QFrame.StyledPanel)
        self.center_layout = QVBoxLayout()
        self.center_frame.setLayout(self.center_layout)
        
        # 添加液体选择区域
        self.liquid_control = QGroupBox("测量液体选择")
        self.liquid_layout = QHBoxLayout()
        
        # 创建液体选择按钮
        self.water_btn = QPushButton("纯水")
        self.water_btn.setCheckable(True)
        self.water_btn.setChecked(True)  # 默认选择纯水
        self.water_btn.clicked.connect(lambda: self.on_liquid_selected("water"))
        
        self.ethanol_btn = QPushButton("乙醇")
        self.ethanol_btn.setCheckable(True)
        self.ethanol_btn.clicked.connect(lambda: self.on_liquid_selected("ethanol"))
        
        self.glycerol_btn = QPushButton("甘油")
        self.glycerol_btn.setCheckable(True)
        self.glycerol_btn.clicked.connect(lambda: self.on_liquid_selected("glycerol"))
        
        # 将按钮添加到布局
        self.liquid_layout.addWidget(self.water_btn)
        self.liquid_layout.addWidget(self.ethanol_btn)
        self.liquid_layout.addWidget(self.glycerol_btn)
        self.liquid_control.setLayout(self.liquid_layout)
        
        # 添加到中心区域
        self.center_layout.addWidget(self.liquid_control)
        
        # 中间旋钮 - 范围-100到100，对应±100mV
        self.zero_dial = QDial()
        self.zero_dial.setRange(-100, 100)
        self.zero_dial.setValue(self.zero_dial_value)  # 使用保存的值初始化
        self.zero_dial.setNotchesVisible(True)
        self.zero_dial.setFixedSize(150, 150)
        self.zero_dial.valueChanged.connect(self.on_dial_changed)
        
        self.zero_label = QLabel("传感器调零\n(±100mV)")
        self.zero_label.setAlignment(Qt.AlignCenter)
        self.zero_label.setStyleSheet("font-size: 16px;")
        
        self.center_layout.addStretch(1)
        self.center_layout.addWidget(self.zero_dial, 0, Qt.AlignCenter)
        self.center_layout.addWidget(self.zero_label, 0, Qt.AlignCenter)
        self.center_layout.addStretch(1)

        # 设置按钮组，确保只有一个按钮被选中
        self.liquid_btn_group = QButtonGroup(self)
        self.liquid_btn_group.addButton(self.water_btn)
        self.liquid_btn_group.addButton(self.ethanol_btn)
        self.liquid_btn_group.addButton(self.glycerol_btn)
        self.liquid_btn_group.setExclusive(True)

        # 初始化液体类型和对应的数据文件
        self.current_liquid = "water"
        self.liquid_data_files = {
            "water": "纯水测量数据.xlsx",
            "ethanol": "乙醇测量数据.xlsx", 
            "glycerol": "甘油测量数据.xlsx"
        }
        self.excel_data = self.load_excel_data()  # 初始加载纯水数据

    def on_liquid_selected(self, liquid_type):
        """液体选择按钮点击事件"""
        self.current_liquid = liquid_type
        self.excel_data = self.load_excel_data()  # 重新加载对应液体的数据
        
        # 更新按钮状态
        self.water_btn.setChecked(liquid_type == "water")
        self.ethanol_btn.setChecked(liquid_type == "ethanol")
        self.glycerol_btn.setChecked(liquid_type == "glycerol")
        
        # 如果当前在测量模式，更新拉力显示
        if self.measuring_tension:
            self.update_tension_display()

    def init_right_area(self):
        """初始化右侧区域"""
        self.right_frame = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_frame.setLayout(self.right_layout)
        
        # 添加示意图
        self.diagram = SurfaceTensionDiagram()
        self.right_layout.addWidget(self.diagram)
        
        # 右上方文本 - 缩小字体和间距
        self.lift_text = QLabel("升降台控制")
        self.lift_text.setAlignment(Qt.AlignCenter)
        self.lift_text.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")  # 缩小字体和间距
        self.right_layout.addWidget(self.lift_text)
        
        # 右下方的控制区域
        self.control_frame = QFrame()
        self.control_layout = QVBoxLayout()
        self.control_frame.setLayout(self.control_layout)
        
        # 速率调节部分 - 缩小拨盘和标签
        speed_control = QHBoxLayout()
        self.speed_dial = QDial()
        self.speed_dial.setRange(1, 5)  # 保持5个刻度
        self.speed_dial.setValue(1)      # 默认设置为最小值1
        self.speed_dial.setNotchesVisible(True)
        self.speed_dial.setFixedSize(100, 120)
        self.speed_dial.valueChanged.connect(self.update_lift_speed)
        
        self.speed_label = QLabel("速率调节\n")
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.speed_label.setStyleSheet("font-size: 24px;")
        
        speed_control.addWidget(self.speed_dial)
        speed_control.addWidget(self.speed_label)
        self.control_layout.addLayout(speed_control)
        
        # 方向控制按钮 - 放大按钮
        self.direction_buttons = QHBoxLayout()

        # 设置更大的按钮样式
        button_style = """
            QPushButton {
                min-width: 80px;
                min-height: 20px;
                font-size: 18px;
                margin: 5px;
                padding: 10px;
            }
            QPushButton:checked {
                background-color: #a0a0ff;
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
        
        self.direction_buttons.addWidget(self.up_btn)
        self.direction_buttons.addWidget(self.stop_btn)
        self.direction_buttons.addWidget(self.down_btn)
        self.control_layout.addLayout(self.direction_buttons)
        
        self.right_layout.addWidget(self.control_frame)
        
        # 将三部分添加到主布局
        self.main_layout.addWidget(self.left_area, 3)
        self.main_layout.addWidget(self.center_frame, 1)
        self.main_layout.addWidget(self.right_frame, 2)

    def load_excel_data(self):
        """加载Excel拉力数据"""
        try:
            # 获取当前选择的液体对应的数据文件
            filename = self.liquid_data_files.get(self.current_liquid, "纯水测量数据.xlsx")
            
            # 方法1：自动查找同目录下的文件
            current_dir = os.path.dirname(os.path.abspath(__file__))
            excel_path = os.path.join(current_dir, filename)
            
            if os.path.exists(excel_path):
                print(f"加载 {filename} 文件: {os.path.abspath(excel_path)}")
            else:
                print(f"文件 {filename} 不存在，请检查路径。当前搜索路径:")
                print(f"- 工作目录: {os.getcwd()}")
                print(f"- 程序目录: {os.path.dirname(os.path.abspath(__file__))}")
            
            # 方法2：如果找不到，让用户选择文件
            if not os.path.exists(excel_path):
                excel_path = self.get_excel_path_from_dialog()
                if not excel_path:
                    return []
            
            df = pd.read_excel(excel_path)
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

    def on_replace_with_ring(self):
        """Replace weights with a ring (equivalent to 3 weights)"""
        self.weight_count = 3
        self.using_ring = True
        self.update_weight_controls()
        self.diagram.set_weight_count(self.weight_count, is_ring=True)
        
        # Update force display if needed
        if self.calibrating_sensor:
            self.update_force_display()
        elif self.measuring_tension:
            self.update_tension_display()

    def on_replace_with_weights(self):
        """Replace ring with standard weights"""
        self.weight_count = 0
        self.using_ring = False
        self.update_weight_controls()
        self.diagram.set_weight_count(self.weight_count, is_ring=False)
        
        # Update force display if needed
        if self.calibrating_sensor:
            self.update_force_display()
        elif self.measuring_tension:
            self.update_tension_display()

    def update_weight_controls(self):
        """Update the visibility of weight control buttons"""
        if self.using_ring:
            self.add_weight_btn.hide()
            self.remove_weight_btn.hide()
            self.weight_count_label.hide()
            self.weight_hint_label.hide()  # Add this line to hide the hint
            self.replace_with_ring_btn.hide()
            self.replace_with_weights_btn.show()
        else:
            self.add_weight_btn.show()
            self.remove_weight_btn.show()
            self.weight_count_label.show()
            self.weight_hint_label.show()  # Add this line to show the hint
            self.replace_with_ring_btn.show()
            self.replace_with_weights_btn.hide()
        
        self.weight_count_label.setText(f"砝码个数: {self.weight_count}")

    def update_lift_speed(self, speed_value):
        """更新升降台速度 - 新速度计算逻辑"""
        # 计算速度值：每2格增加1，最小1，最大5
        speed = speed_value*self.min_speed
        
        # 设置实际速度（保证至少为1），并乘以1.5倍速
        self.lift_speed = max(1, speed) 
        
        # 更新标签显示
        self.speed_label.setText(f"速率调节\n({int(self.lift_speed/self.min_speed)})")  # 显示原始值
        
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
        max_group = max((g[0] for g in self.data_groups), default=1)
        self.query_label = QLabel(f"选择组别：{self.current_group}/{max_group}")
        self.query_label.setStyleSheet("""
            font-size: 16px; 
            padding: 10px; 
            border-bottom: 1px solid #ccc;
            background-color: #a0ffa0;
            border-left: 4px solid green;
            font-weight: bold;
        """)
        
        # 清除原有布局并添加查询标签
        self.display_box_layout.insertWidget(0, self.query_label)
        
        # 隐藏其他显示
        self.force_display.hide()
        self.measurement_container.hide()
        
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
            # 隐藏组别选择标签
            self.query_label.hide()
            
            # 设置数据点 - 直接传递完整的数据点列表
            self.data_display.set_data_points(group_data[1])
            
            # 显示数据点阵和详细信息
            self.measurement_container.show()
            self.tension_display.show()
            self.data_display.show()
            
            # 显示第一个数据点
            self.current_point_index = 0
            self.update_query_point_display()

    def update_query_display(self):
        """更新查询界面显示（选择组别时）"""
        max_group = max((g[0] for g in self.data_groups), default=1)
        self.query_label.setText(f"选择组别：{self.current_group}/{max_group}")

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
        self.current_direction = direction
        
        # 更新按钮状态
        self.up_btn.setChecked(direction == 0)
        self.stop_btn.setChecked(direction == 1)
        self.down_btn.setChecked(direction == 2)
        
        if direction == 1:  # 停止
            self.lift_timer.stop()
        else:
            self.lift_timer.start(50)
            
    def animate_lift(self):
        """动画更新升降台位置"""
        current_pos = self.diagram.lift_position
        if self.current_direction == 0:  # 上升
            new_pos = max(0, current_pos - self.lift_speed * 0.05)  # 0.05是时间因子
        else:  # 下降
            new_pos = min(100, current_pos + self.lift_speed * 0.05)
            
        self.diagram.set_lift_position(new_pos)
        
        # 如果到达极限位置，自动停止
        if (self.current_direction == 0 and new_pos == 0) or \
        (self.current_direction == 2 and new_pos == 100):
            self.set_lift_direction(1)  # 设置为停止状态

    def update_selection_arrow(self):
        """更新箭头指示，高亮当前选中的栏目"""
        for i, label in enumerate(self.item_labels):
            if i == self.current_selection:
                if self.adjusting_interval and i == 0:  # 特别处理采集间隔调整状态
                    label.setStyleSheet("""
                        font-size: 16px; 
                        padding: 10px; 
                        border-bottom: 1px solid #ccc;
                        background-color: #a0d0ff;
                        border-left: 4px solid blue;
                        font-weight: bold;
                    """)
                elif self.querying_data and i == 3:  # 数据查询状态
                    label.setStyleSheet("""
                        font-size: 16px; 
                        padding: 10px; 
                        border-bottom: 1px solid #ccc;
                        background-color: #a0ffa0;
                        border-left: 4px solid green;
                        font-weight: bold;
                    """)
                else:
                    label.setStyleSheet("""
                        font-size: 16px; 
                        padding: 10px; 
                        border-bottom: 1px solid #ccc;
                        background-color: #e0e0e0;
                        border-left: 4px solid red;
                        font-weight: bold;
                    """)
            else:
                label.setStyleSheet("""
                    font-size: 16px; 
                    padding: 10px; 
                    border-bottom: 1px solid #ccc;
                """)
        
        if not self.adjusting_interval and not self.querying_data:
            self.items[0] = f"采集间隔：{self.interval:.1f}s"
            self.item_labels[0].setText(self.items[0])

    def update_interval_display(self):
        """更新采集间隔显示"""
        self.items[0] = f"采集间隔：{self.interval:.1f}s(0.1-2.0s)"
        self.item_labels[0].setText(self.items[0])

    def update_force_display(self):
        """更新拉力显示"""
        if self.using_ring:
            base_force = 3 * 20 + self.zero_dial.value()  # Ring counts as 3 weights
        else:
            base_force = self.weight_count * 20 + self.zero_dial.value()
        # 如果砝码浸入水中，增加45
        if (self.weight_count > 0 or self.using_ring):
            base_force += 0
        self.force_display.setText(f"当前拉力：{base_force:.1f}mV")

    def update_tension_display(self):
        """更新表面张力测量显示"""
        # 基础拉力值
        if self.using_ring:
            base_force = 3 * 20 + self.zero_dial.value()  # 圆环相当于3个砝码
        else:
            base_force = self.weight_count * 20 + self.zero_dial.value()
        
        # 获取当前速率调节值
        speed_factor = self.speed_dial.value()
        
        # 叠加Excel中的拉力数据
        global excel_force
        excel_force = 0
        if self.excel_data and self.data_points:
            # 获取最近的时间点（乘以速率调节因子）
            last_timestamp = (self.data_points[-1][1] if self.data_points else 0) * speed_factor
            # 找到最接近的时间点的数据
            closest_time, closest_force = min(self.excel_data, key=lambda x: abs(x[0] - last_timestamp))
            excel_force = closest_force
        
        # 圆环模式下始终叠加Excel数据，砝码模式下只在浸入水中时叠加
        if self.using_ring or (self.weight_count > 0 and self.diagram.is_weight_in_water()):
            total_force = base_force + excel_force
        else:
            total_force = base_force
        
        # 更新显示
        self.tension_display.setText(
            f"No.{self.measurement_count} 拉力：{total_force:.1f}mV\n"
        )

    def collect_data(self):
        """采集数据"""
        if len(self.data_points) >= 255:
            self.collection_timer.stop()
            return
            
        # 基础拉力值
        base_force = self.weight_count * 20 + self.zero_dial.value()
        if self.using_ring:
            base_force = 3 * 20 + self.zero_dial.value()  # 圆环相当于3个砝码
        
        # 获取当前速率调节值
        speed_factor = self.speed_dial.value()
        
        # 叠加Excel中的拉力数据
        timestamp = len(self.data_points) * self.interval * speed_factor  # 时间乘以速率因子
        excel_force = 0
        if self.excel_data:
            closest_time, closest_force = min(self.excel_data, key=lambda x: abs(x[0] - timestamp))
            excel_force = closest_force
        
        # 计算总拉力
        if self.using_ring or (self.weight_count > 0 and self.diagram.is_weight_in_water()):
            total_force = base_force + excel_force
        else:
            total_force = base_force
        
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
        self.measuring_tension = True
        self.data_points = []  # 清空数据点

        # 禁用升降台控制按钮和速率调节旋钮
        self.up_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.down_btn.setEnabled(False)
        self.speed_dial.setEnabled(False)
        
        # 隐藏所有栏目
        for label in self.item_labels:
            label.hide()
        
        # 显示测量容器（包含文本框和数据点阵）
        self.measurement_container.show()
        self.tension_display.show()
        self.data_display.show()
        self.update_tension_display()
        
        # 如果是圆环模式，自动调整升降台位置使水面淹没圆环底部7像素
        if self.using_ring:
            # 计算目标位置
            sensor_y = int(self.diagram.height() * 0.2)
            weight_y = sensor_y + 40  # 圆环顶部位置
            weight_height = 30  # 圆环高度
            water_height = 40  # 水高度
            
            # 计算需要的水面位置（圆环底部上方7像素）
            target_water_top = (weight_y + weight_height) - 7
            
            # 计算对应的升降台位置（0-100）
            # 水面位置公式: water_top = lift_y - water_height
            # 所以 lift_y = water_top + water_height
            lift_y = target_water_top + water_height
            
            # 将升降台位置转换为百分比 (0-100)
            # 原公式: lift_y = height * (0.544 + 0.17 * (position/100))
            # 所以 position = ((lift_y/height - 0.544) / 0.17) * 100
            height = self.diagram.height()
            target_position = ((lift_y/height - 0.544) / 0.17) * 100
            
            # 设置升降台位置并开始下降
            self.diagram.set_lift_position(target_position)
            self.set_lift_direction(2)  # 开始下降
        
        # 开始数据采集
        self.collection_timer.start(int(self.interval * 1000))  # 转换为毫秒
        
        # 更新界面
        self.update_selection_arrow()

    def exit_measurement_mode(self):
        """退出测量模式时保存数据"""
        self.measuring_tension = False
        self.collection_timer.stop()

        # 重新启用升降台控制按钮和速率调节旋钮
        self.up_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.down_btn.setEnabled(True)
        self.speed_dial.setEnabled(True)
        
        # 保存当前组数据 - 确保保存的是完整的数据点
        if self.data_points:
            self.data_groups.append((self.measurement_count, self.data_points.copy()))
            self.data_points = []
        
        # 恢复界面显示
        for label in self.item_labels:
            label.show()
        
        self.measurement_container.hide()
        self.update_selection_arrow()

    def on_dial_changed(self, value):
        """旋钮值变化时的处理 - 更新拉力显示"""
        if self.calibrating_sensor:
            self.update_force_display()
        elif self.measuring_tension:
            self.update_tension_display()

    def on_add_weight(self):
        """增加砝码"""
        if self.weight_count < 7:  # 限制最大砝码数量
            self.weight_count += 1
            self.weight_count_label.setText(f"砝码个数: {self.weight_count}")
            self.diagram.set_weight_count(self.weight_count)
            
            # 更新拉力显示
            if self.calibrating_sensor:
                self.update_force_display()
            elif self.measuring_tension:
                self.update_tension_display()

    def on_remove_weight(self):
        """减少砝码"""
        if self.weight_count > 0:  # 不能小于0
            self.weight_count -= 1
            self.weight_count_label.setText(f"砝码个数: {self.weight_count}")
            self.diagram.set_weight_count(self.weight_count)
            
            # 更新拉力显示
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
                # 完成一次测量，保存数据并准备下一次
                if self.data_points:  # 只有有数据时才保存
                    self.data_groups.append((self.measurement_count, self.data_points.copy()))
                    self.data_points = []
                    self.measurement_count += 1
                self.exit_measurement_mode()
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
            # 退出时不自动增加measurement_count
            self.exit_measurement_mode()
        else:
            print("返回操作")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SurfaceTensionApp()
    window.show() 
    sys.exit(app.exec_())