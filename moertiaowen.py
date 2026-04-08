"""
莫尔条纹分析与暗条纹识别程序 - 带中心线拟合功能（增强版）
功能：
1. 自动识别暗条纹并拟合中心线
2. 支持基于欧氏距离的可调节临近条纹合并功能
3. 计算条纹间距和曲率
4. 生成详细的可视化报告
5. 基于最多点条纹拟合整体方向，所有条纹使用统一方向
6. 标记每条条纹上的所有检测点
7. 基于网格标定功能换算实际距离（使用calibo.py方法）
"""

import cv2
import numpy as np
from scipy import signal
from scipy.signal import find_peaks
from scipy.interpolate import UnivariateSpline
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import threading

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class GridCalibrator:
    """基于calibo.py方法的网格标定器 - 检测黑色网格的水平和垂直间距"""
    
    def __init__(self, root=None):
        self.root = root
        self.image = None
        self.original_image = None
        self.horizontal_info = None
        self.vertical_info = None
        self.calibration_success = False
        
        # 标定参数
        self.threshold = 127  # 二值化阈值
        self.min_line_width = 50  # 最小线宽
        
        # 实际网格尺寸（用户输入）
        self.grid_size_cm = 1.0
        self.grid_real_width_cm = 1.0  # 网格实际宽度（厘米）
        self.grid_real_height_cm = 1.0  # 网格实际高度（厘米）
        
        # 转换比例
        self.pixel_to_cm_ratio_h = None  # 水平方向转换比例 (cm/像素)
        self.pixel_to_cm_ratio_v = None  # 垂直方向转换比例 (cm/像素)
        self.pixel_to_cm_ratio = None    # 平均转换比例 (cm/像素)
        
    def set_image(self, image):
        """设置要标定的图像"""
        self.image = image.copy()
        self.original_image = image.copy()
        
    def set_grid_size(self, size_cm):
        """设置网格实际尺寸（厘米）"""
        self.grid_size_cm = size_cm
        self.grid_real_width_cm = size_cm
        self.grid_real_height_cm = size_cm
        
    def set_params(self, threshold=127, min_line_width=10):
        """设置标定参数"""
        self.threshold = threshold
        self.min_line_width = min_line_width
        
    def detect_horizontal_spacing(self, binary):
        """检测水平方向的条纹间距（参考calibo.py）"""
        h, w = binary.shape
        
        # 对每一行进行投影
        row_projections = np.sum(binary, axis=1)
        
        # 找到有黑色线条的行
        line_rows = []
        min_line_width = self.min_line_width
        
        i = 0
        while i < h:
            if row_projections[i] > min_line_width * 255:  # 找到线条
                start = i
                while i < h and row_projections[i] > min_line_width * 255:
                    i += 1
                end = i - 1
                # 计算线条的中心位置
                center = (start + end) // 2
                line_rows.append(center)
            else:
                i += 1
        
        # 计算间距
        spacings = []
        for i in range(1, len(line_rows)):
            spacing = line_rows[i] - line_rows[i-1]
            spacings.append(spacing)
        
        return {
            'positions': line_rows,
            'spacings': spacings,
            'count': len(line_rows),
            'avg_spacing': np.mean(spacings) if spacings else 0,
            'min_spacing': np.min(spacings) if spacings else 0,
            'max_spacing': np.max(spacings) if spacings else 0,
            'std_spacing': np.std(spacings) if spacings else 0
        }
    
    def detect_vertical_spacing(self, binary):
        """检测垂直方向的条纹间距（参考calibo.py）"""
        h, w = binary.shape
        
        # 对每一列进行投影
        col_projections = np.sum(binary, axis=0)
        
        # 找到有黑色线条的列
        line_cols = []
        min_line_width = self.min_line_width
        
        i = 0
        while i < w:
            if col_projections[i] > min_line_width * 255:  # 找到线条
                start = i
                while i < w and col_projections[i] > min_line_width * 255:
                    i += 1
                end = i - 1
                # 计算线条的中心位置
                center = (start + end) // 2
                line_cols.append(center)
            else:
                i += 1
        
        # 计算间距
        spacings = []
        for i in range(1, len(line_cols)):
            spacing = line_cols[i] - line_cols[i-1]
            spacings.append(spacing)
        
        return {
            'positions': line_cols,
            'spacings': spacings,
            'count': len(line_cols),
            'avg_spacing': np.mean(spacings) if spacings else 0,
            'min_spacing': np.min(spacings) if spacings else 0,
            'max_spacing': np.max(spacings) if spacings else 0,
            'std_spacing': np.std(spacings) if spacings else 0
        }
    
    def calibrate(self, progress_callback=None):
        """
        执行网格标定
        返回: (success, message, pixel_to_cm_ratio)
        """
        if self.image is None:
            return False, "请先加载图像", None
        
        try:
            if progress_callback:
                progress_callback(20, "转换为灰度图...")
            
            # 转换为OpenCV格式
            if isinstance(self.image, np.ndarray):
                img_cv = self.image.copy()
                if len(img_cv.shape) == 3:
                    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
                else:
                    gray = img_cv
            else:
                # PIL图像
                img_cv = cv2.cvtColor(np.array(self.image), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            if progress_callback:
                progress_callback(40, "二值化处理...")
            
            # 二值化处理（黑色线条变为白色）
            _, binary = cv2.threshold(gray, self.threshold, 255, cv2.THRESH_BINARY_INV)
            
            # 形态学操作，连接断开的线条
            kernel = np.ones((3, 3), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            if progress_callback:
                progress_callback(60, "检测水平条纹间距...")
            
            # 检测水平和垂直方向的线条
            self.horizontal_info = self.detect_horizontal_spacing(binary)
            self.vertical_info = self.detect_vertical_spacing(binary)
            
            if progress_callback:
                progress_callback(80, "检测垂直条纹间距...")
            
            # 检查检测结果
            if self.horizontal_info['count'] < 2 and self.vertical_info['count'] < 2:
                return False, "未能检测到足够的网格线条，请调整阈值或最小线宽参数", None
            
            # 计算转换比例
            # 水平方向：实际网格宽度 / 水平平均间距
            if self.horizontal_info['count'] >= 2 and self.horizontal_info['avg_spacing'] > 0:
                # 实际网格宽度 = 网格数量 * 网格单元尺寸
                # 这里假设检测到的线条间距对应的是网格单元尺寸
                grid_cells_h = self.horizontal_info['count'] - 1
                if grid_cells_h > 0:
                    total_width_px = self.horizontal_info['avg_spacing'] * grid_cells_h
                    self.pixel_to_cm_ratio_h = self.grid_real_width_cm / total_width_px
                else:
                    self.pixel_to_cm_ratio_h = self.grid_real_width_cm / self.horizontal_info['avg_spacing']
            
            # 垂直方向
            if self.vertical_info['count'] >= 2 and self.vertical_info['avg_spacing'] > 0:
                grid_cells_v = self.vertical_info['count'] - 1
                if grid_cells_v > 0:
                    total_height_px = self.vertical_info['avg_spacing'] * grid_cells_v
                    self.pixel_to_cm_ratio_v = self.grid_real_height_cm / total_height_px
                else:
                    self.pixel_to_cm_ratio_v = self.grid_real_height_cm / self.vertical_info['avg_spacing']
            
            # 取平均值作为最终转换比例
            ratios = []
            if self.pixel_to_cm_ratio_h is not None:
                ratios.append(self.pixel_to_cm_ratio_h)
            if self.pixel_to_cm_ratio_v is not None:
                ratios.append(self.pixel_to_cm_ratio_v)
            
            if ratios:
                self.pixel_to_cm_ratio = np.mean(ratios)
            else:
                return False, "无法计算转换比例", None
            
            self.calibration_success = True
            
            # 生成标定结果信息
            result_msg = f"""
网格标定成功！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
水平方向: 检测到 {self.horizontal_info['count']} 条线条
          平均间距: {self.horizontal_info['avg_spacing']:.2f} 像素
垂直方向: 检测到 {self.vertical_info['count']} 条线条
          平均间距: {self.vertical_info['avg_spacing']:.2f} 像素
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
网格实际尺寸: {self.grid_size_cm} x {self.grid_size_cm} cm
转换比例: 1 像素 = {self.pixel_to_cm_ratio:.6f} cm
          或 1 cm = {1/self.pixel_to_cm_ratio:.2f} 像素
"""
            
            return True, result_msg, self.pixel_to_cm_ratio
            
        except Exception as e:
            return False, f"标定失败: {str(e)}", None
    
    def get_pixel_to_cm_ratio(self):
        """获取像素到厘米的转换比例"""
        return self.pixel_to_cm_ratio if self.calibration_success else None
    
    def convert_pixel_to_cm(self, pixel_distance):
        """将像素距离转换为厘米"""
        if self.pixel_to_cm_ratio is None:
            return None
        return pixel_distance * self.pixel_to_cm_ratio
    
    def convert_cm_to_pixel(self, cm_distance):
        """将厘米距离转换为像素"""
        if self.pixel_to_cm_ratio is None:
            return None
        return cm_distance / self.pixel_to_cm_ratio
    
    def get_horizontal_info(self):
        """获取水平方向检测信息"""
        return self.horizontal_info
    
    def get_vertical_info(self):
        """获取垂直方向检测信息"""
        return self.vertical_info
    
    def draw_calibration_overlay(self, image):
        """在图像上绘制标定检测结果（支持中文显示）"""
        if not self.calibration_success:
            return image
        
        result = image.copy()
        h, w = result.shape[:2] if len(result.shape) > 2 else (result.shape[0], result.shape[1])
        
        # 尝试使用PIL绘制中文
        try:
            from PIL import ImageDraw, ImageFont
            import PIL
            
            # 转换为PIL图像
            if len(result.shape) == 3:
                result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            else:
                result_rgb = cv2.cvtColor(result, cv2.COLOR_GRAY2RGB)
            
            pil_img = Image.fromarray(result_rgb)
            draw = ImageDraw.Draw(pil_img)
            
            # 尝试加载中文字体
            font = None
            font_paths = [
                "C:/Windows/Fonts/simhei.ttf",  # Windows 黑体
                "C:/Windows/Fonts/msyh.ttc",    # Windows 微软雅黑
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
            ]
            for path in font_paths:
                if os.path.exists(path):
                    try:
                        font = ImageFont.truetype(path, 16)
                        break
                    except:
                        continue
            
            if font is None:
                # 使用默认字体
                font = ImageFont.load_default()
            
            # 绘制水平线条位置
            if self.horizontal_info and self.horizontal_info['positions']:
                for i, pos in enumerate(self.horizontal_info['positions']):
                    draw.line([(0, pos), (w, pos)], fill=(0, 255, 0), width=2)
                    # 标注间距
                    if i > 0 and i < len(self.horizontal_info['positions']):
                        spacing = self.horizontal_info['positions'][i] - self.horizontal_info['positions'][i-1]
                        mid_y = self.horizontal_info['positions'][i-1] + spacing // 2
                        draw.text((10, mid_y - 10), f"{spacing:.0f}像素", 
                                fill=(0, 255, 0), font=font)
            
            # 绘制垂直线条位置
            if self.vertical_info and self.vertical_info['positions']:
                for i, pos in enumerate(self.vertical_info['positions']):
                    draw.line([(pos, 0), (pos, h)], fill=(0, 255, 255), width=2)
                    # 标注间距
                    if i > 0 and i < len(self.vertical_info['positions']):
                        spacing = self.vertical_info['positions'][i] - self.vertical_info['positions'][i-1]
                        mid_x = self.vertical_info['positions'][i-1] + spacing // 2
                        draw.text((mid_x - 30, 20), f"{spacing:.0f}像素", 
                                fill=(0, 255, 255), font=font)
            
            # 添加标定信息文字
            info_text = f"网格标定: {self.grid_size_cm}cm | 比例: {self.pixel_to_cm_ratio:.5f}cm/像素"
            draw.text((10, h - 30), info_text, fill=(255, 255, 255), font=font)
            
            # 转换回OpenCV格式
            result = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            print(f"PIL绘制失败，使用OpenCV绘制（中文可能显示异常）: {e}")
            # 降级使用OpenCV绘制（仅英文/数字）
            # 绘制水平线条位置
            if self.horizontal_info and self.horizontal_info['positions']:
                for i, pos in enumerate(self.horizontal_info['positions']):
                    cv2.line(result, (0, pos), (w, pos), (0, 255, 0), 2)
                    if i > 0 and i < len(self.horizontal_info['positions']):
                        spacing = self.horizontal_info['positions'][i] - self.horizontal_info['positions'][i-1]
                        mid_y = self.horizontal_info['positions'][i-1] + spacing // 2
                        cv2.putText(result, f"{spacing:.0f}px", (10, mid_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # 绘制垂直线条位置
            if self.vertical_info and self.vertical_info['positions']:
                for i, pos in enumerate(self.vertical_info['positions']):
                    cv2.line(result, (pos, 0), (pos, h), (0, 255, 255), 2)
                    if i > 0 and i < len(self.vertical_info['positions']):
                        spacing = self.vertical_info['positions'][i] - self.vertical_info['positions'][i-1]
                        mid_x = self.vertical_info['positions'][i-1] + spacing // 2
                        cv2.putText(result, f"{spacing:.0f}px", (mid_x, 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            # 添加标定信息文字（使用英文）
            info_text = f"Grid Calibration: {self.grid_size_cm}cm | Ratio: {self.pixel_to_cm_ratio:.5f}cm/px"
            cv2.putText(result, info_text, (10, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return result


class StripeCenterLine:
    """条纹中心线类，存储每条条纹的中心线信息"""
    
    def __init__(self, index, points):
        self.index = index
        self.points = np.array(points)
        if len(self.points) > 0:
            self.x_coords = self.points[:, 0]
            self.y_coords = self.points[:, 1]
            # 计算中心点坐标（所有点的平均值）
            self.center_x = np.mean(self.x_coords)
            self.center_y = np.mean(self.y_coords)
            # 方向线参数（统一方向）
            self.direction_line = None  # 方向线参数 (斜率, 截距)
            self.direction_angle = 0    # 方向角度（度）
        else:
            self.x_coords = np.array([])
            self.y_coords = np.array([])
            self.center_x = 0
            self.center_y = 0
            self.direction_line = None
            self.direction_angle = 0
        
        self.poly_fit = None
        self.poly_func = None
        self.spline_fit = None
        self.fit_degree = 3
        
        self.length = 0
        self.curvature = 0
        self.orientation = 0
        
        if len(self.points) >= 2:
            self._calculate_properties()
        
    def _calculate_properties(self):
        """计算中心线属性"""
        if len(self.points) < 2:
            return
            
        # 计算长度
        self.length = np.sum(np.sqrt(np.diff(self.x_coords)**2 + 
                                     np.diff(self.y_coords)**2))
        
        # 计算方向（平均角度）
        if len(self.x_coords) > 1:
            dx = np.diff(self.x_coords)
            dy = np.diff(self.y_coords)
            angles = np.arctan2(dy, dx)
            # 过滤异常角度
            angles = angles[~np.isnan(angles)]
            if len(angles) > 0:
                self.orientation = np.mean(angles) * 180 / np.pi
        
    def fit_straight_line(self):
        """使用最小二乘法拟合直线 y = kx + b"""
        if len(self.points) >= 2:
            try:
                A = np.vstack([self.x_coords, np.ones(len(self.x_coords))]).T
                k, b = np.linalg.lstsq(A, self.y_coords, rcond=None)[0]
                self.direction_line = (k, b)
                self.direction_angle = np.arctan(k) * 180 / np.pi
                return self.direction_line
            except Exception as e:
                print(f"直线拟合失败: {str(e)}")
                self.direction_line = None
                return None
        return None
        
    def get_points_on_direction_line(self, x_range=None):
        """获取方向线上的点"""
        if self.direction_line is None:
            return None
        k, b = self.direction_line
        if x_range is None:
            x_range = np.linspace(min(self.x_coords), max(self.x_coords), 100)
        y_range = k * x_range + b
        return np.column_stack((x_range, y_range))
        
    def fit_polynomial(self, degree=3):
        """多项式拟合中心线"""
        if len(self.points) < degree + 1:
            degree = max(1, len(self.points) - 1)
            if degree < 1:
                return
            
        self.fit_degree = degree
        try:
            # 拟合多项式 y = f(x)
            self.poly_fit = np.polyfit(self.x_coords, self.y_coords, degree)
            self.poly_func = np.poly1d(self.poly_fit)
            
            # 计算曲率
            if degree >= 2 and len(self.x_coords) > 2:
                first_deriv = np.polyder(self.poly_func, 1)
                second_deriv = np.polyder(self.poly_func, 2)
                
                x_range = np.linspace(min(self.x_coords), max(self.x_coords), 100)
                curvatures = np.abs(second_deriv(x_range)) / \
                            (1 + first_deriv(x_range)**2)**1.5
                self.curvature = np.mean(curvatures)
                
        except Exception as e:
            print(f"多项式拟合失败: {str(e)}")
            self.poly_fit = None
            
    def fit_spline(self, smoothing=0.1):
        """样条拟合中心线"""
        if len(self.points) < 4:
            return
            
        try:
            sort_idx = np.argsort(self.x_coords)
            x_sorted = self.x_coords[sort_idx]
            y_sorted = self.y_coords[sort_idx]
            
            self.spline_fit = UnivariateSpline(x_sorted, y_sorted, s=smoothing)
            
        except Exception as e:
            print(f"样条拟合失败: {str(e)}")
            
    def get_y_at_x(self, x):
        """获取给定x坐标处的y值"""
        if isinstance(x, (int, float)):
            x = np.array([x])
        
        if self.poly_fit is not None:
            return self.poly_func(x)
        elif len(self.points) > 0:
            return np.interp(x, self.x_coords, self.y_coords)
        else:
            return None
            
    def get_points_on_line(self, num_points=100):
        """生成中心线上的均匀采样点"""
        if len(self.points) == 0:
            return np.array([])
            
        if self.spline_fit is not None:
            x_range = np.linspace(min(self.x_coords), max(self.x_coords), num_points)
            y_range = self.spline_fit(x_range)
            return np.column_stack((x_range, y_range))
        elif self.poly_fit is not None:
            x_range = np.linspace(min(self.x_coords), max(self.x_coords), num_points)
            y_range = self.poly_func(x_range)
            return np.column_stack((x_range, y_range))
        else:
            return self.points


class MoireAnalyzer:
    """莫尔条纹分析核心类"""
    
    def __init__(self, image_path=None, merge_distance=15, spacing_merge_distance=25, 
                 min_points_per_stripe=5, grid_size_cm=1.0, progress_callback=None):
        """
        初始化莫尔条纹分析器
        
        Args:
            image_path: 图像文件路径
            merge_distance: 合并临近条纹的距离阈值（像素），基于中心点欧氏距离
            min_points_per_stripe: 过滤条纹的最小点数阈值
            grid_size_cm: 网格的实际尺寸（厘米），默认为1cm
        """
        self.progress_callback = progress_callback  # 进度回调函数
        self.image_path = image_path
        self.merge_distance = merge_distance  # 基于中心点距离合并的阈值
        self.spacing_merge_distance = spacing_merge_distance  # 基于条纹间距合并的阈值
        self.min_points_per_stripe = min_points_per_stripe  # 最小点数阈值
        self.grid_size_cm = grid_size_cm  # 网格实际尺寸（厘米）
        
        self.original_image = None
        self.gray_image = None
        self.processed = None
        self.stripe_image = None
        self.binary_stripe = None
        self.stripe_center_lines = []
        self.stripe_spacing = []
        self.stripe_spacing_cm = []  # 实际距离（厘米）
        self.avg_spacing = 0
        self.avg_spacing_cm = 0  # 平均间距（厘米）
        self.spacing_std = 0
        self.spacing_std_cm = 0  # 间距标准差（厘米）
        self.debug_info = {}  # 存储调试信息
        self.global_direction = None  # 全局方向 (斜率, 截距)
        self.global_angle = 0  # 全局方向角度
        
        # 网格标定器（使用calibo.py方法）
        self.calibrator = GridCalibrator()
        self.calibration_applied = False  # 是否已应用标定
        
    def update_progress(self, value, message=""):
        if self.progress_callback:
            self.progress_callback(value, message)

    def load_and_preprocess(self):
        """加载图像并进行预处理"""
        if self.image_path is None:
            raise ValueError("未指定图像路径")
            
        self.original_image = cv2.imread(self.image_path)
        if self.original_image is None:
            raise ValueError(f"无法读取图像: {self.image_path}")
        
        self.gray_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        
        # 去除噪声
        denoised = cv2.bilateralFilter(self.gray_image, 9, 75, 75)
        
        # 自适应直方图均衡化
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # 高斯滤波
        self.processed = cv2.GaussianBlur(enhanced, (3, 3), 0)
        
        return self.processed
    
    def apply_calibration(self, calibrator):
        """应用标定器的转换比例"""
        ratio = calibrator.get_pixel_to_cm_ratio()
        if ratio is not None:
            self.calibrator = calibrator
            self.calibration_applied = True
            self.grid_size_cm = calibrator.grid_size_cm
            print(f"已应用网格标定: 1像素 = {ratio:.6f}cm")
            return True
        return False
    
    def extract_stripes_by_fft(self):
        """使用傅里叶变换提取莫尔条纹"""
        rows, cols = self.processed.shape
        
        # 傅里叶变换
        f = np.fft.fft2(self.processed)
        fshift = np.fft.fftshift(f)
        
        # 自动检测莫尔条纹的主频率
        mask = np.ones((rows, cols), dtype=np.uint8)
        center_radius = min(rows, cols) // 25
        cv2.circle(mask, (cols//2, rows//2), center_radius, 0, -1)
        
        masked_spectrum = np.abs(fshift) * mask
        
        # 找到前几个最大的峰值
        flat_spectrum = masked_spectrum.flatten()
        top_indices = np.argsort(flat_spectrum)[-5:]  # 取前5个峰值
        top_positions = [np.unravel_index(idx, masked_spectrum.shape) for idx in top_indices]
        
        # 选择距离中心最合适的峰值（排除中心附近的）
        best_idx = None
        min_dist_to_center = float('inf')
        center = (rows//2, cols//2)
        
        for pos in top_positions:
            dist = np.sqrt((pos[0] - center[0])**2 + (pos[1] - center[1])**2)
            if dist > center_radius and dist < min_dist_to_center:
                min_dist_to_center = dist
                best_idx = pos
        
        if best_idx is None:
            best_idx = top_positions[0] if top_positions else (rows//4, cols//4)
        
        # 提取主频率分量
        bandpass = np.zeros((rows, cols), dtype=np.uint8)
        filter_radius = max(5, min(rows, cols) // 50)
        
        cv2.circle(bandpass, (best_idx[1], best_idx[0]), filter_radius, 1, -1)
        sym_idx = (rows - best_idx[0], cols - best_idx[1])
        cv2.circle(bandpass, (sym_idx[1], sym_idx[0]), filter_radius, 1, -1)
        
        # 应用滤波器
        fshift_filtered = fshift * bandpass
        f_ishift = np.fft.ifftshift(fshift_filtered)
        
        # 逆变换
        img_filtered = np.abs(np.fft.ifft2(f_ishift))
        
        # 归一化
        self.stripe_image = cv2.normalize(img_filtered, None, 0, 255, 
                                          cv2.NORM_MINMAX).astype(np.uint8)
        
        # 增强条纹对比度
        self.stripe_image = cv2.equalizeHist(self.stripe_image)
        
        # 保存调试信息
        self.debug_info['fft_peak'] = best_idx
        self.debug_info['filter_radius'] = filter_radius
        
        return self.stripe_image
    
    def _merge_nearby_center_lines(self, lines, distance_threshold):
        """基于中心点欧氏距离合并临近的中心线
        
        Args:
            lines: 中心线列表
            distance_threshold: 合并距离阈值（像素），基于中心点之间的欧氏距离
            
        Returns:
            合并后的中心线列表
        """
        if len(lines) <= 1:
            return lines
        
        # 计算每条中心线的中心点
        centers = []
        for line in lines:
            center = (np.mean(line.x_coords), np.mean(line.y_coords))
            centers.append(center)
        
        # 使用层次聚类合并相近的中心线
        n_lines = len(lines)
        merged_groups = []
        used = [False] * n_lines
        
        for i in range(n_lines):
            if used[i]:
                continue
            
            # 当前组
            current_group = [i]
            used[i] = True
            
            # 不断扩展组，直到没有新成员加入
            changed = True
            while changed:
                changed = False
                for j in range(n_lines):
                    if used[j]:
                        continue
                    
                    # 检查当前组的中心点与候选点的距离
                    for group_idx in current_group:
                        center1 = centers[group_idx]
                        center2 = centers[j]
                        distance = np.sqrt((center1[0] - center2[0])**2 + 
                                          (center1[1] - center2[1])**2)
                        
                        if distance <= distance_threshold:
                            current_group.append(j)
                            used[j] = True
                            changed = True
                            break
                    
                    if changed:
                        break
            
            merged_groups.append(current_group)
        
        # 合并每组内的所有点
        merged_lines = []
        for group in merged_groups:
            if len(group) == 1:
                # 只有一条中心线，直接保留
                merged_lines.append(lines[group[0]])
            else:
                # 多条中心线，合并所有点
                all_points = []
                for idx in group:
                    all_points.extend(lines[idx].points)
                
                # 按x坐标排序
                all_points_sorted = sorted(all_points, key=lambda p: p[0])
                
                # 创建新的中心线
                merged_line = StripeCenterLine(len(merged_lines), all_points_sorted)
                
                # 拟合
                if len(all_points_sorted) >= 4:
                    merged_line.fit_polynomial(degree=min(3, len(all_points_sorted)-1))
                    merged_line.fit_spline(smoothing=0.5)
                elif len(all_points_sorted) >= 2:
                    merged_line.fit_polynomial(degree=1)
                
                merged_lines.append(merged_line)
        
        # 重新编号
        for i, line in enumerate(merged_lines):
            line.index = i
        
        return merged_lines
    
    def _filter_stripes_by_points(self, lines):
        """过滤点数较少的条纹"""
        filtered = [line for line in lines if len(line.points) >= self.min_points_per_stripe]
        # 重新编号
        for i, line in enumerate(filtered):
            line.index = i
        print(f"点数过滤: 过滤前 {len(lines)} 条, 过滤后 {len(filtered)} 条 (最小点数要求: {self.min_points_per_stripe})")
        return filtered
    
    def _fit_global_direction(self, lines):
        """使用点数最多的条纹拟合全局方向"""
        if not lines:
            return None
        
        # 找出点数最多的条纹
        max_points_line = max(lines, key=lambda line: len(line.points))
        print(f"使用条纹 #{max_points_line.index + 1} (点数: {len(max_points_line.points)}) 拟合全局方向")
        
        # 拟合直线
        direction = max_points_line.fit_straight_line()
        if direction is not None:
            self.global_direction = direction
            self.global_angle = max_points_line.direction_angle
            print(f"全局方向: 斜率={self.global_direction[0]:.4f}, 角度={self.global_angle:.2f}°")
            
            # 为所有条纹设置统一的方向线（过各自中心点）
            for line in lines:
                # 过中心点且平行于全局方向
                k = self.global_direction[0]
                # 计算过中心点的直线截距: y = kx + b => b = y - kx
                b = line.center_y - k * line.center_x
                line.direction_line = (k, b)
                line.direction_angle = self.global_angle
            
            return direction
        return None
    
    def _calculate_parallel_lines_distance(self, line1, line2):
        """计算两条平行线之间的距离
        
        Args:
            line1: 第一条线的 (斜率, 截距)
            line2: 第二条线的 (斜率, 截距)
            
        Returns:
            两条平行线之间的垂直距离
        """
        k1, b1 = line1
        k2, b2 = line2
        
        # 对于平行线，斜率相等
        # 距离公式: |b2 - b1| / sqrt(1 + k^2)
        distance = abs(b2 - b1) / np.sqrt(1 + k1**2)
        return distance
    
    def find_stripe_center_lines_improved(self):
        """改进的条纹中心线检测方法"""
        if self.stripe_image is None:
            raise ValueError("请先提取条纹图像")
        
        rows, cols = self.stripe_image.shape
        
        # 方法1：使用全局投影法确定条纹数量和大致位置
        vertical_projection = np.mean(self.stripe_image, axis=1)
        
        # 平滑投影曲线
        window_size = min(51, rows // 5)
        if window_size % 2 == 0:
            window_size += 1
        
        if window_size >= 3:
            smoothed_projection = signal.savgol_filter(vertical_projection, window_size, 3)
        else:
            smoothed_projection = vertical_projection
        
        # 寻找局部最小值（暗条纹位置）
        neg_projection = -smoothed_projection
        height_threshold = np.max(neg_projection) * 0.3
        distance = max(rows // 30, 10)
        
        peaks, properties = find_peaks(neg_projection, 
                                       height=height_threshold,
                                       distance=distance,
                                       prominence=np.std(neg_projection) * 0.5)
        
        self.debug_info['projection_peaks'] = len(peaks)
        self.debug_info['projection_peak_positions'] = peaks.tolist() if len(peaks) > 0 else []
        
        if len(peaks) < 2:
            print(f"警告: 投影法只检测到 {len(peaks)} 条条纹")
            # 如果检测不到，降低阈值重试
            peaks, _ = find_peaks(neg_projection, 
                                 height=np.max(neg_projection) * 0.1,
                                 distance=distance)
            self.debug_info['projection_peaks_retry'] = len(peaks)
        
        # 方法2：逐行精细检测
        stripe_centers_per_row = []
        
        # 根据投影法确定的条纹位置，确定每行的搜索区域
        search_regions = []
        if len(peaks) > 0:
            # 在峰值附近建立搜索区域
            for peak in peaks:
                region_start = max(0, peak - distance)
                region_end = min(rows, peak + distance)
                search_regions.append((region_start, region_end))
        else:
            # 如果没有检测到，使用整个图像
            search_regions.append((0, rows))
        
        for y in range(rows):
            # 检查是否在搜索区域内
            in_region = False
            for start, end in search_regions:
                if start <= y <= end:
                    in_region = True
                    break
            
            if not in_region and len(search_regions) > 0:
                continue
                
            row = self.stripe_image[y, :].astype(np.float32)
            
            # 平滑行数据
            row_window = min(21, cols // 10)
            if row_window >= 3 and row_window % 2 == 0:
                row_window += 1
            
            if row_window >= 3:
                smoothed_row = signal.savgol_filter(row, row_window, 2)
            else:
                smoothed_row = row
            
            # 寻找局部最小值（暗条纹中心）
            diff = np.diff(smoothed_row)
            zero_crossings = np.where(np.diff(np.sign(diff)) > 0)[0]
            
            # 过滤：只保留强度足够低的位置
            min_threshold = np.percentile(smoothed_row, 30)  # 30%分位数
            valid_minima = []
            for idx in zero_crossings:
                if idx + 1 < len(smoothed_row):
                    if smoothed_row[idx] < min_threshold:
                        valid_minima.append(idx)
            
            # 去重和合并相近的点
            if len(valid_minima) > 0:
                # 聚类相近的点
                merged_minima = []
                current_group = [valid_minima[0]]
                for i in range(1, len(valid_minima)):
                    if valid_minima[i] - current_group[-1] < distance // 2:
                        current_group.append(valid_minima[i])
                    else:
                        # 取组内平均值
                        merged_minima.append(int(np.mean(current_group)))
                        current_group = [valid_minima[i]]
                if current_group:
                    merged_minima.append(int(np.mean(current_group)))
                
                stripe_centers_per_row.append((y, merged_minima))
        
        self.debug_info['row_detection_points'] = sum(len(centers) for _, centers in stripe_centers_per_row)
        
        # 聚类点形成条纹
        if not stripe_centers_per_row:
            print("错误: 未检测到任何条纹中心点")
            return []
        
        # 构建所有点
        all_points = []
        for y, x_positions in stripe_centers_per_row:
            for x in x_positions:
                all_points.append((x, y))
        
        points_array = np.array(all_points)
        if len(points_array) == 0:
            return []
        
        # 改进的聚类算法：基于距离和连通性
        # 按y坐标排序
        sorted_by_y = sorted(all_points, key=lambda p: p[1])
        points_array = np.array(sorted_by_y)
        
        if len(points_array) > 1:
            # 计算相邻点之间的距离
            distances = []
            for i in range(len(points_array) - 1):
                dist = np.sqrt((points_array[i+1][0] - points_array[i][0])**2 + 
                              (points_array[i+1][1] - points_array[i][1])**2)
                distances.append(dist)
            
            # 动态阈值：使用距离的中位数
            if distances:
                median_dist = np.median(distances)
                clustering_threshold = median_dist * 2.5
            else:
                clustering_threshold = rows // 15
        else:
            clustering_threshold = rows // 15
        
        # 聚类
        clusters = []
        current_cluster = []
        
        for i, point in enumerate(points_array):
            if not current_cluster:
                current_cluster.append(point)
            else:
                # 计算与上一个点的距离
                last_point = current_cluster[-1]
                dist = np.sqrt((point[0] - last_point[0])**2 + (point[1] - last_point[1])**2)
                
                if dist <= clustering_threshold:
                    current_cluster.append(point)
                else:
                    if len(current_cluster) >= 3:  # 至少3个点
                        clusters.append(current_cluster)
                    current_cluster = [point]
        
        # 添加最后一个簇
        if len(current_cluster) >= 3:
            clusters.append(current_cluster)
        
        self.debug_info['clusters_found_before'] = len(clusters)
        
        # 创建中心线对象
        temp_center_lines = []
        for i, cluster in enumerate(clusters):
            # 按x排序
            cluster_sorted = sorted(cluster, key=lambda p: p[0])
            if len(cluster_sorted) >= 2:
                center_line = StripeCenterLine(i, cluster_sorted)
                
                # 拟合中心线
                if len(cluster_sorted) >= 4:
                    center_line.fit_polynomial(degree=min(3, len(cluster_sorted)-1))
                    center_line.fit_spline(smoothing=0.5)
                elif len(cluster_sorted) >= 2:
                    center_line.fit_polynomial(degree=1)
                
                temp_center_lines.append(center_line)
        
        # 按y坐标的平均值排序
        if temp_center_lines:
            temp_center_lines.sort(key=lambda line: np.mean(line.y_coords))
            for i, line in enumerate(temp_center_lines):
                line.index = i
        
        # 基于中心点欧氏距离合并临近的中心线（第一次合并）
        if self.merge_distance <= 0:
            merged_lines = temp_center_lines
        else:
            merged_lines = self._merge_nearby_center_lines(temp_center_lines, self.merge_distance)
        
        # ========== 基于条纹间距进行二次合并 ==========
        if self.spacing_merge_distance > 0 and len(merged_lines) >= 2:
            # 先拟合全局方向（使用点数最多的条纹）
            max_points_line = max(merged_lines, key=lambda line: len(line.points))
            direction = max_points_line.fit_straight_line()
            
            if direction is not None:
                k = direction[0]
                
                # 计算每条线的截距
                stripe_info = []
                for line in merged_lines:
                    b = line.center_y - k * line.center_x
                    stripe_info.append((b, line))
                
                # 按截距排序
                stripe_info.sort(key=lambda x: x[0])
                
                # 计算所有相邻条纹的间距
                all_distances = []
                for i in range(1, len(stripe_info)):
                    prev_b, _ = stripe_info[i-1]
                    curr_b, _ = stripe_info[i]
                    distance = abs(curr_b - prev_b) / np.sqrt(1 + k**2)
                    all_distances.append(distance)
                
                if all_distances:
                    min_distance = np.min(all_distances)
                    dynamic_threshold = self.spacing_merge_distance
                    print(f"基于条纹间距二次合并: 最小间距={min_distance:.2f}, 使用阈值={dynamic_threshold:.2f}")
                    
                    # 合并间距小于阈值的相邻条纹
                    spacing_merged_groups = []
                    current_group = [stripe_info[0][1]]
                    
                    for i in range(1, len(stripe_info)):
                        prev_b, prev_line = stripe_info[i-1]
                        curr_b, curr_line = stripe_info[i]
                        distance = abs(curr_b - prev_b) / np.sqrt(1 + k**2)
                        
                        if distance <= dynamic_threshold:
                            current_group.append(curr_line)
                            print(f"  合并条纹 {prev_line.index+1} 和 {curr_line.index+1} (间距={distance:.2f} <= {dynamic_threshold:.2f})")
                        else:
                            if len(current_group) > 0:
                                spacing_merged_groups.append(current_group)
                            current_group = [curr_line]
                            print(f"  保留条纹 {prev_line.index+1} (间距={distance:.2f} > {dynamic_threshold:.2f})")
                    
                    if len(current_group) > 0:
                        spacing_merged_groups.append(current_group)
                    
                    # 重新合并点
                    spacing_merged_lines = []
                    for group in spacing_merged_groups:
                        if len(group) == 1:
                            spacing_merged_lines.append(group[0])
                        else:
                            all_points = []
                            for line in group:
                                all_points.extend(line.points)
                            all_points_sorted = sorted(all_points, key=lambda p: p[0])
                            merged_line = StripeCenterLine(len(spacing_merged_lines), all_points_sorted)
                            if len(all_points_sorted) >= 4:
                                merged_line.fit_polynomial(degree=min(3, len(all_points_sorted)-1))
                                merged_line.fit_spline(smoothing=0.5)
                            elif len(all_points_sorted) >= 2:
                                merged_line.fit_polynomial(degree=1)
                            spacing_merged_lines.append(merged_line)
                    
                    print(f"基于间距二次合并: {len(merged_lines)} 条 -> {len(spacing_merged_lines)} 条")
                    merged_lines = spacing_merged_lines
        
        # 过滤点数较少的条纹
        self.stripe_center_lines = self._filter_stripes_by_points(merged_lines)
        
        # 拟合全局方向（使用点数最多的条纹）
        if self.stripe_center_lines:
            self._fit_global_direction(self.stripe_center_lines)
        
        self.debug_info['clusters_found_after'] = len(self.stripe_center_lines)
        
        # 计算条纹间距（平行线间的距离）- 在合并完成后重新计算
        if len(self.stripe_center_lines) >= 2 and self.global_direction is not None:
            self.stripe_spacing = []
            k = self.global_direction[0]
            
            # 计算每条线在法线方向上的位置（截距）
            intercepts = []
            for line in self.stripe_center_lines:
                b = line.center_y - k * line.center_x
                intercepts.append(b)
            
            # 按截距排序
            sorted_indices = np.argsort(intercepts)
            sorted_intercepts = [intercepts[i] for i in sorted_indices]
            
            # 计算相邻平行线之间的距离（像素）
            print("\n===== 合并后的条纹间距 =====")
            for i in range(len(sorted_intercepts) - 1):
                distance = abs(sorted_intercepts[i+1] - sorted_intercepts[i]) / np.sqrt(1 + k**2)
                self.stripe_spacing.append(distance)
                print(f"条纹对 {i+1}: 间距 = {distance:.2f} 像素")
            
            if self.stripe_spacing:
                self.avg_spacing = np.mean(self.stripe_spacing)
                self.spacing_std = np.std(self.stripe_spacing)
                print(f"平均条纹间距: {self.avg_spacing:.2f} 像素\n")
                
                # 转换为实际距离（厘米）- 使用标定器的转换比例
                if self.calibration_applied and self.calibrator.get_pixel_to_cm_ratio() is not None:
                    ratio = self.calibrator.get_pixel_to_cm_ratio()
                    self.stripe_spacing_cm = [d * ratio for d in self.stripe_spacing]
                    self.avg_spacing_cm = self.avg_spacing * ratio
                    self.spacing_std_cm = self.spacing_std * ratio
                    print(f"实际条纹间距: 平均={self.avg_spacing_cm:.4f}cm")
                else:
                    self.stripe_spacing_cm = []
                    self.avg_spacing_cm = 0
                    self.spacing_std_cm = 0
                
                print(f"检测结果: 合并前 {len(temp_center_lines)} 条 -> 合并后 {len(merged_lines)} 条 -> 点数过滤后 {len(self.stripe_center_lines)} 条条纹")
                print(f"合并距离阈值: {self.merge_distance} 像素")
                print(f"最小点数阈值: {self.min_points_per_stripe}")
                print(f"全局方向角度: {self.global_angle:.2f}°")
                
                return self.stripe_center_lines
    
    def refine_center_lines_with_gradient(self):
        """使用梯度信息细化中心线"""
        if not self.stripe_center_lines:
            return
        
        # 计算梯度
        grad_x = cv2.Sobel(self.stripe_image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(self.stripe_image, cv2.CV_64F, 0, 1, ksize=3)
        
        for line in self.stripe_center_lines:
            refined_points = []
            
            for point in line.points:
                x, y = int(point[0]), int(point[1])
                
                # 边界检查
                if x < 0 or x >= self.stripe_image.shape[1] or y < 0 or y >= self.stripe_image.shape[0]:
                    refined_points.append((x, y))
                    continue
                
                # 在局部区域内寻找梯度最大的点
                search_radius = 3
                x_min = max(0, x - search_radius)
                x_max = min(self.stripe_image.shape[1], x + search_radius + 1)
                y_min = max(0, y - search_radius)
                y_max = min(self.stripe_image.shape[0], y + search_radius + 1)
                
                if x_min < x_max and y_min < y_max:
                    local_grad = np.sqrt(grad_x[y_min:y_max, x_min:x_max]**2 + 
                                        grad_y[y_min:y_max, x_min:x_max]**2)
                    
                    # 找到梯度最大的点
                    max_idx = np.unravel_index(np.argmax(local_grad), local_grad.shape)
                    refined_x = x_min + max_idx[1]
                    refined_y = y_min + max_idx[0]
                    refined_points.append((refined_x, refined_y))
                else:
                    refined_points.append((x, y))
            
            # 更新中心线点
            if len(refined_points) >= 2:
                line.points = np.array(refined_points)
                line.x_coords = line.points[:, 0]
                line.y_coords = line.points[:, 1]
                
                # 重新拟合
                if len(line.points) >= 4:
                    line.fit_polynomial(degree=min(3, len(line.points)-1))
                    line.fit_spline(smoothing=0.5)
                elif len(line.points) >= 2:
                    line.fit_polynomial(degree=1)
                
                line._calculate_properties()
                
                # 更新方向线（保持平行于全局方向）
                if self.global_direction is not None:
                    k = self.global_direction[0]
                    b = line.center_y - k * line.center_x
                    line.direction_line = (k, b)
                    line.direction_angle = self.global_angle
    
    def calculate_quality_metrics(self):
        """计算条纹质量指标"""
        if len(self.stripe_center_lines) < 2:
            return {'uniformity': 0, 'contrast': 0, 'visibility': 0, 
                    'parallelism': 0, 'overall_score': 0}
        
        # 均匀性指标
        if self.avg_spacing > 0:
            spacing_cv = self.spacing_std / self.avg_spacing
        else:
            spacing_cv = 1
        uniformity = max(0, 1 - spacing_cv)
        
        # 对比度指标
        if self.stripe_image is not None:
            contrast = np.std(self.stripe_image) / np.mean(self.stripe_image) if np.mean(self.stripe_image) > 0 else 0
            contrast = min(1, contrast / 2)
        else:
            contrast = 0
        
        # 可见性指标
        if self.avg_spacing > 0 and self.stripe_image is not None:
            visibility = len(self.stripe_center_lines) / (self.stripe_image.shape[0] / self.avg_spacing)
            visibility = min(1, visibility)
        else:
            visibility = 0
        
        # 平行度指标（所有条纹与全局方向的角度差）
        if self.global_angle != 0:
            angle_diffs = [abs(line.direction_angle - self.global_angle) for line in self.stripe_center_lines]
            parallelism = max(0, 1 - np.mean(angle_diffs) / 45)
        else:
            parallelism = 0
        
        metrics = {
            'uniformity': uniformity,
            'contrast': contrast,
            'visibility': visibility,
            'parallelism': parallelism,
            'overall_score': (uniformity + contrast + visibility + parallelism) / 4
        }
        
        return metrics
    
    def run_analysis(self):
        steps = [
            (10, "加载并预处理图像...", self.load_and_preprocess),
            (30, "FFT提取条纹...", self.extract_stripes_by_fft),
            (50, "检测条纹中心线...", self.find_stripe_center_lines_improved),
            (80, "细化中心线...", self.refine_center_lines_with_gradient),
        ]
        
        for progress, msg, func in steps:
            self.update_progress(progress, msg)
            func()
        
        self.update_progress(100, "分析完成!")
        
        return {
            'center_lines': self.stripe_center_lines,
            'spacing': self.stripe_spacing,
            'spacing_cm': self.stripe_spacing_cm,
            'avg_spacing': self.avg_spacing,
            'avg_spacing_cm': self.avg_spacing_cm,
            'std_spacing': self.spacing_std,
            'std_spacing_cm': self.spacing_std_cm,
            'count': len(self.stripe_center_lines),
            'metrics': self.calculate_quality_metrics(),
            'debug_info': self.debug_info,
            'global_angle': self.global_angle,
            'calibration_applied': self.calibration_applied,
            'pixel_to_cm_ratio': self.calibrator.get_pixel_to_cm_ratio() if self.calibration_applied else None,
            'grid_size_cm': self.grid_size_cm
        }


class CalibrationDialog:
    """网格标定对话框"""
    
    def __init__(self, parent, image):
        self.parent = parent
        self.image = image
        self.calibrator = None
        self.result = None
        
    def show(self):
        """显示标定对话框"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("网格标定 - 请设置标定参数")
        dialog.geometry("500x500")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # 参数设置区域
        param_frame = tk.LabelFrame(dialog, text="标定参数", padx=10, pady=5)
        param_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # 二值化阈值
        tk.Label(param_frame, text="二值化阈值:").grid(row=0, column=0, sticky=tk.W, pady=5)
        threshold_var = tk.IntVar(value=127)
        threshold_scale = tk.Scale(param_frame, from_=0, to=255, 
                                   orient=tk.HORIZONTAL, variable=threshold_var,
                                   length=200)
        threshold_scale.grid(row=0, column=1, padx=5, pady=5)
        
        # 最小线宽
        tk.Label(param_frame, text="过滤噪点:").grid(row=1, column=0, sticky=tk.W, pady=5)
        min_line_var = tk.IntVar(value=50)
        min_line_scale = tk.Scale(param_frame, from_=5, to=100, 
                                  orient=tk.HORIZONTAL, variable=min_line_var,
                                  length=200)
        min_line_scale.grid(row=1, column=1, padx=5, pady=5)
        
        # 网格实际尺寸
        tk.Label(param_frame, text="网格实际尺寸(cm):").grid(row=2, column=0, sticky=tk.W, pady=5)
        grid_size_var = tk.DoubleVar(value=1.0)
        grid_size_entry = tk.Entry(param_frame, textvariable=grid_size_var, width=10)
        grid_size_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 图片显示区域
        image_frame = tk.LabelFrame(dialog, text="标定图像预览", padx=10, pady=5)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 显示原图
        img_preview = self.image.copy()
        if len(img_preview.shape) == 3:
            img_preview = cv2.cvtColor(img_preview, cv2.COLOR_BGR2RGB)
        h, w = img_preview.shape[:2]
        max_h = 300
        if h > max_h:
            scale = max_h / h
            new_w = int(w * scale)
            img_preview = cv2.resize(img_preview, (new_w, max_h))
        
        photo = ImageTk.PhotoImage(Image.fromarray(img_preview))
        image_label = tk.Label(image_frame, image=photo)
        image_label.image = photo
        image_label.pack(pady=5)
        
        # 结果显示区域
        result_frame = tk.LabelFrame(dialog, text="标定结果", padx=10, pady=5)
        result_frame.pack(fill=tk.X, padx=10, pady=5)
        
        result_text = tk.Text(result_frame, height=8, width=55)
        result_text.pack()
        
        # 进度条
        progress = ttk.Progressbar(dialog, mode='determinate')
        progress.pack(fill=tk.X, padx=10, pady=5)
        
        def update_progress(value, message):
            progress['value'] = value
            dialog.update_idletasks()
        
        def run_calibration():
            """执行标定"""
            try:
                calibrator = GridCalibrator()
                calibrator.set_image(self.image)
                calibrator.set_grid_size(grid_size_var.get())
                calibrator.set_params(threshold=threshold_var.get(), 
                                    min_line_width=min_line_var.get())
                
                success, msg, ratio = calibrator.calibrate(progress_callback=update_progress)
                
                # 确保进度条完成
                progress['value'] = 100
                dialog.update_idletasks()
                
                result_text.delete(1.0, tk.END)
                result_text.insert(1.0, msg)
                
                if success:
                    self.calibrator = calibrator
                    self.result = calibrator
                    
                    # 显示预览（带检测线条）
                    overlay_img = calibrator.draw_calibration_overlay(self.image.copy())
                    if len(overlay_img.shape) == 3:
                        overlay_img = cv2.cvtColor(overlay_img, cv2.COLOR_BGR2RGB)
                    h, w = overlay_img.shape[:2]
                    if h > max_h:
                        scale = max_h / h
                        new_w = int(w * scale)
                        overlay_img = cv2.resize(overlay_img, (new_w, max_h))
                    
                    preview_photo = ImageTk.PhotoImage(Image.fromarray(overlay_img))
                    image_label.config(image=preview_photo)
                    image_label.image = preview_photo
                    
                    # 启用确认按钮
                    confirm_btn.config(state=tk.NORMAL)
                else:
                    confirm_btn.config(state=tk.DISABLED)
                    
            except Exception as e:
                result_text.delete(1.0, tk.END)
                result_text.insert(1.0, f"标定失败: {str(e)}")
                confirm_btn.config(state=tk.DISABLED)
        
        def confirm():
            """确认使用标定结果"""
            if self.calibrator and self.calibrator.calibration_success:
                dialog.destroy()
        
        # 按钮区域
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        calibrate_btn = tk.Button(button_frame, text="开始标定", command=run_calibration,
                                  bg="#4CAF50", fg="white", font=("Arial", 10), padx=20)
        calibrate_btn.pack(side=tk.LEFT, padx=5)
        
        confirm_btn = tk.Button(button_frame, text="确认使用", command=confirm,
                                bg="#2196F3", fg="white", font=("Arial", 10), padx=20,
                                state=tk.DISABLED)
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="取消", command=dialog.destroy,
                               bg="#f44336", fg="white", font=("Arial", 10), padx=20)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()
        return self.result


class MoireGUI:
    """莫尔条纹分析图形界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("莫尔条纹分析系统")
        self.root.geometry("1400x800")
        
        self.root.configure(bg='#f0f0f0')
        
        self.current_image_path = None
        self.analyzer = None
        self.analysis_results = None
        self.calibrator = None  # 网格标定器
        self.merge_distance = 30  # 默认合并距离（像素）
        self.min_points = 300  # 默认最小点数
        self.spacing_merge_distance = 25  # 默认间距合并距离
        self.grid_size_cm = 1.0  # 默认网格尺寸（厘米）
        self.progress_value = 0
        self.create_widgets()
    
    def update_progress(self, value, message):
        """更新进度条和状态栏"""
        # 确保在主线程中更新UI
        self.root.after(0, lambda: self._update_progress_ui(value, message))

    def _update_progress_ui(self, value, message):
        """实际更新UI的方法"""
        self.progress['value'] = value
        self.status_bar.config(text=message)
        self.root.update_idletasks()

    def create_widgets(self):
        """创建界面组件"""
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bg='#2c3e50', height=90)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        # 标题
        title_label = tk.Label(toolbar, text="莫尔条纹分析系统", 
                               font=('Arial', 12, 'bold'),
                               bg='#2c3e50', fg='white')
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # 控制面板框架
        control_frame = tk.Frame(toolbar, bg='#2c3e50')
        control_frame.pack(side=tk.RIGHT, padx=20)
        
        # 网格标定状态显示
        calib_frame = tk.Frame(control_frame, bg='#2c3e50')
        calib_frame.pack(side=tk.LEFT, padx=10)
        
        self.calib_status_label = tk.Label(calib_frame, text="⚫ 未标定", 
                                           bg='#2c3e50', fg='#ff6b6b',
                                           font=('Arial', 9, 'bold'))
        self.calib_status_label.pack(side=tk.LEFT)
        
        # 合并距离控制
        merge_frame = tk.Frame(control_frame, bg='#2c3e50')
        merge_frame.pack(side=tk.LEFT, padx=10)
        
        merge_label = tk.Label(merge_frame, text="按欧式距离合并(像素):", 
                               bg='#2c3e50', fg='white',
                               font=('Arial', 10))
        merge_label.pack(side=tk.LEFT)
        
        self.merge_var = tk.IntVar(value=30)
        self.merge_scale = tk.Scale(merge_frame, from_=5, to=50, 
                                    orient=tk.HORIZONTAL,
                                    length=120,
                                    variable=self.merge_var,
                                    bg='#2c3e50', fg='white',
                                    highlightbackground='#2c3e50',
                                    troughcolor='#95a5a6')
        self.merge_scale.pack(side=tk.LEFT, padx=5)
        
        self.merge_value_label = tk.Label(merge_frame, text="30", 
                                          bg='#2c3e50', fg='white',
                                          font=('Arial', 10, 'bold'))
        self.merge_value_label.pack(side=tk.LEFT)
        
        # 间距合并距离控制
        spacing_merge_frame = tk.Frame(control_frame, bg='#2c3e50')
        spacing_merge_frame.pack(side=tk.LEFT, padx=10)

        spacing_merge_label = tk.Label(spacing_merge_frame, text="按条纹间距合并(像素):", 
                                    bg='#2c3e50', fg='white',
                                    font=('Arial', 10))
        spacing_merge_label.pack(side=tk.LEFT)

        self.spacing_merge_var = tk.IntVar(value=25)
        self.spacing_merge_scale = tk.Scale(spacing_merge_frame, from_=0, to=100, 
                                            orient=tk.HORIZONTAL,
                                            length=100,
                                            variable=self.spacing_merge_var,
                                            bg='#2c3e50', fg='white',
                                            highlightbackground='#2c3e50',
                                            troughcolor='#95a5a6')
        self.spacing_merge_scale.pack(side=tk.LEFT, padx=5)

        self.spacing_merge_value_label = tk.Label(spacing_merge_frame, text="25", 
                                                bg='#2c3e50', fg='white',
                                                font=('Arial', 10, 'bold'))
        self.spacing_merge_value_label.pack(side=tk.LEFT)

        # 最小点数控制
        points_frame = tk.Frame(control_frame, bg='#2c3e50')
        points_frame.pack(side=tk.LEFT, padx=10)
        
        points_label = tk.Label(points_frame, text="每组条纹最小点数:", 
                                bg='#2c3e50', fg='white',
                                font=('Arial', 10))
        points_label.pack(side=tk.LEFT)
        
        self.points_var = tk.IntVar(value=300)
        self.points_scale = tk.Scale(points_frame, from_=100, to=500, 
                                     orient=tk.HORIZONTAL,
                                     length=100,
                                     variable=self.points_var,
                                     bg='#2c3e50', fg='white',
                                     highlightbackground='#2c3e50',
                                     troughcolor='#95a5a6')
        self.points_scale.pack(side=tk.LEFT, padx=5)
        
        self.points_value_label = tk.Label(points_frame, text="300", 
                                           bg='#2c3e50', fg='white',
                                           font=('Arial', 10, 'bold'))
        self.points_value_label.pack(side=tk.LEFT)
        
        # 按钮框架
        button_frame = tk.Frame(control_frame, bg='#2c3e50')
        button_frame.pack(side=tk.LEFT, padx=10)
        
        self.select_btn = tk.Button(button_frame, text="📁 选择图片", 
                                    command=self.select_image,
                                    font=('Arial', 10),
                                    bg='#3498db', fg='white',
                                    padx=15, pady=5,
                                    cursor='hand2')
        self.select_btn.pack(side=tk.LEFT, padx=3)
        
        self.calibrate_btn = tk.Button(button_frame, text="📐 网格标定", 
                                       command=self.calibrate_grid,
                                       font=('Arial', 10),
                                       bg='#9b59b6', fg='white',
                                       padx=15, pady=5,
                                       cursor='hand2',
                                       state=tk.DISABLED)
        self.calibrate_btn.pack(side=tk.LEFT, padx=3)
        
        self.analyze_btn = tk.Button(button_frame, text="🔬 开始分析", 
                                     command=self.start_analysis,
                                     font=('Arial', 10),
                                     bg='#27ae60', fg='white',
                                     padx=15, pady=5,
                                     cursor='hand2',
                                     state=tk.DISABLED)
        self.analyze_btn.pack(side=tk.LEFT, padx=3)
        
        self.save_btn = tk.Button(button_frame, text="💾 保存报告", 
                                  command=self.save_report,
                                  font=('Arial', 10),
                                  bg='#f39c12', fg='white',
                                  padx=15, pady=5,
                                  cursor='hand2',
                                  state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=3)
        
        # 主内容区域
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, 
                                    bg='#f0f0f0', sashwidth=5)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：图像显示区域
        left_frame = tk.Frame(main_paned, bg='white', relief=tk.RAISED, bd=1)
        main_paned.add(left_frame, width=800)
        
        self.image_label = tk.Label(left_frame, text="请选择图片", 
                                    font=('Arial', 14),
                                    bg='white', fg='gray')
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 右侧：结果面板
        right_frame = tk.Frame(main_paned, bg='#ecf0f1', relief=tk.RAISED, bd=1)
        main_paned.add(right_frame, width=400)
        
        result_title = tk.Label(right_frame, text="分析结果", 
                                font=('Arial', 16, 'bold'),
                                bg='#ecf0f1', fg='#2c3e50')
        result_title.pack(pady=10)
        
        # 创建带滚动条的结果文本框
        text_frame = tk.Frame(right_frame, bg='#ecf0f1')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text = tk.Text(text_frame, height=20, width=40,
                                   font=('Courier', 10),
                                   yscrollcommand=scrollbar.set,
                                   bg='white', fg='black')
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.result_text.yview)
        
        # 进度条
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
        # 状态栏
        self.status_bar = tk.Label(self.root, text="就绪", 
                                   bg='#95a5a6', fg='white',
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 绑定控件事件
        self.spacing_merge_scale.config(command=self.on_spacing_merge_change)
        self.merge_scale.config(command=self.on_merge_distance_change)
        self.points_scale.config(command=self.on_min_points_change)
    
    def on_spacing_merge_change(self, value):
        """间距合并距离改变时的回调函数"""
        self.spacing_merge_distance = int(float(value))
        self.spacing_merge_value_label.config(text=str(self.spacing_merge_distance))

    def on_merge_distance_change(self, value):
        """合并距离改变时的回调函数"""
        self.merge_distance = int(float(value))
        self.merge_value_label.config(text=str(self.merge_distance))
        
    def on_min_points_change(self, value):
        """最小点数改变时的回调函数"""
        self.min_points = int(float(value))
        self.points_value_label.config(text=str(self.min_points))
    
    def update_calibration_status(self):
        """更新标定状态显示"""
        if self.calibrator and self.calibrator.calibration_success:
            ratio = self.calibrator.get_pixel_to_cm_ratio()
            self.calib_status_label.config(
                text=f"✓ 已标定: {ratio:.5f}cm/px", 
                fg='#2ecc71'
            )
            self.grid_size_cm = self.calibrator.grid_size_cm
        else:
            self.calib_status_label.config(text="⚫ 未标定", fg='#ff6b6b')
        
    def select_image(self):
        """选择图片文件"""
        file_types = [
            ("图像文件", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择莫尔条纹图片",
            filetypes=file_types
        )
        
        if filename:
            self.current_image_path = filename
            self.status_bar.config(text=f"已选择: {os.path.basename(filename)}")
            self.display_image(filename)
            
            # 如果有之前的标定结果，询问是否保留
            if self.calibrator and self.calibrator.calibration_success:
                use_existing = messagebox.askyesno(
                    "保留标定结果",
                    f"检测到已有网格标定结果\n\n"
                    f"转换比例: 1像素 = {self.calibrator.pixel_to_cm_ratio:.6f} cm\n"
                    f"网格尺寸: {self.calibrator.grid_size_cm} cm\n\n"
                    f"是否继续使用此标定结果进行条纹分析？\n\n"
                    f"• 是：使用现有标定结果（适用于相同拍摄距离）\n"
                    f"• 否：重新进行网格标定",
                    icon='question'
                )
                if use_existing:
                    # 保留现有标定结果
                    self.update_calibration_status()
                    self.status_bar.config(text=f"已选择: {os.path.basename(filename)} (保留标定结果)")
                    # 启用按钮
                    self.calibrate_btn.config(state=tk.NORMAL)
                    self.analyze_btn.config(state=tk.NORMAL)
                    self.result_text.delete(1.0, tk.END)
                    self.save_btn.config(state=tk.DISABLED)
                    return
                else:
                    # 用户选择重新标定，清除旧标定结果
                    self.calibrator = None
                    self.update_calibration_status()
            
            # 没有标定结果或用户选择重新标定
            self.calibrate_btn.config(state=tk.NORMAL)
            self.analyze_btn.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.save_btn.config(state=tk.DISABLED)
            
    def display_image(self, image_path):
        """在界面中显示图片"""
        try:
            img = Image.open(image_path)
            display_width = 780
            display_height = 580
            img.thumbnail((display_width, display_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo
        except Exception as e:
            messagebox.showerror("错误", f"无法显示图片: {str(e)}")
    
    def calibrate_grid(self):
        """执行网格标定"""
        if not self.current_image_path:
            messagebox.showwarning("警告", "请先选择图片")
            return
        
        try:
            # 加载图像用于标定
            img = cv2.imread(self.current_image_path)
            if img is None:
                messagebox.showerror("错误", "无法加载图像")
                return
            
            # 显示标定对话框
            dialog = CalibrationDialog(self.root, img)
            calibrator = dialog.show()
            
            if calibrator and calibrator.calibration_success:
                self.calibrator = calibrator
                self.grid_size_cm = calibrator.grid_size_cm
                self.update_calibration_status()
                messagebox.showinfo("标定成功", 
                                   f"网格标定完成！\n"
                                   f"水平方向: {calibrator.horizontal_info['count']}条线条, "
                                   f"平均间距: {calibrator.horizontal_info['avg_spacing']:.1f}像素\n"
                                   f"垂直方向: {calibrator.vertical_info['count']}条线条, "
                                   f"平均间距: {calibrator.vertical_info['avg_spacing']:.1f}像素\n"
                                   f"转换比例: 1像素 = {calibrator.pixel_to_cm_ratio:.6f}cm")
            elif calibrator:
                messagebox.showwarning("标定失败", "未能成功标定网格，请调整参数后重试")
                
        except Exception as e:
            messagebox.showerror("错误", f"标定过程中出错: {str(e)}")
            
    def start_analysis(self):
        """开始分析"""
        if not self.current_image_path:
            messagebox.showwarning("警告", "请先选择图片")
            return
        
        # 禁用按钮
        self.select_btn.config(state=tk.DISABLED)
        self.calibrate_btn.config(state=tk.DISABLED)
        self.analyze_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        
        # 重置进度条
        self.progress['value'] = 0
        self.progress['maximum'] = 100
        
        status_msg = f"正在分析中，合并距离={self.merge_distance}像素，最小点数={self.min_points}..."
        if self.calibrator and self.calibrator.calibration_success:
            status_msg += f" (已应用标定: {self.calibrator.pixel_to_cm_ratio:.6f}cm/px)"
        self.status_bar.config(text=status_msg)
        
        thread = threading.Thread(target=self.run_analysis_thread)
        thread.daemon = True
        thread.start()
        
    def run_analysis_thread(self):
        try:
            # 创建分析器
            self.analyzer = MoireAnalyzer(
                self.current_image_path, 
                merge_distance=self.merge_distance,
                spacing_merge_distance=self.spacing_merge_distance,
                min_points_per_stripe=self.min_points,
                grid_size_cm=self.grid_size_cm,
                progress_callback=self.update_progress
            )
            
            # 应用标定结果（如果有）
            if self.calibrator and self.calibrator.calibration_success:
                self.analyzer.apply_calibration(self.calibrator)
                print("已应用网格标定结果")
            
            self.analysis_results = self.analyzer.run_analysis()
            self.root.after(0, self.update_results)
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
            
    def update_results(self):
        """更新结果显示"""
        try:
            self.progress['value'] = 100
            self.result_text.delete(1.0, tk.END)
            results = self.analysis_results
            
            result_str = f"""
    ╔════════════════════════════════════════════════════════════╗
    ║        莫尔条纹分析结果报告        ║
    ╚════════════════════════════════════════════════════════════╝

    📊 基本统计
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    检测到的暗条纹数量: {results['count']} 条
    合并距离阈值: {self.merge_distance} 像素
    最小点数阈值: {self.min_points} 点/条纹
    整体条纹方向角度: {results.get('global_angle', 0):.2f}°

    🔲 网格标定信息
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            if results.get('calibration_applied', False):
                ratio = results.get('pixel_to_cm_ratio', 0)
                result_str += f"""    标定状态: ✓ 已标定
    网格实际尺寸: {results.get('grid_size_cm', 1.0)} cm
    转换比例: 1 像素 = {ratio:.6f} cm
"""
            else:
                result_str += f"""    标定状态: ✗ 未标定
    将使用像素单位进行测量（未进行实际距离换算）
    提示：请先点击"网格标定"按钮进行标定
"""
            
            result_str += f"""
    📏 间距分析（平行线间垂直距离）
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            if results.get('calibration_applied', False):
                result_str += f"""    平均间距: {results['avg_spacing']:.2f} 像素 = {results.get('avg_spacing_cm', 0):.4f} cm
    间距标准差: {results['std_spacing']:.2f} 像素 = {results.get('std_spacing_cm', 0):.4f} cm
"""
                if len(results.get('spacing_cm', [])) > 0:
                    result_str += f"    最小间距: {np.min(results['spacing_cm']):.4f} cm\n"
                    result_str += f"    最大间距: {np.max(results['spacing_cm']):.4f} cm\n"
                    if results['avg_spacing'] > 0:
                        result_str += f"    间距变异系数: {results['std_spacing']/results['avg_spacing']:.4f}\n"
            else:
                result_str += f"""    平均间距: {results['avg_spacing']:.2f} 像素
    间距标准差: {results['std_spacing']:.2f} 像素
"""
                if len(results['spacing']) > 0:
                    result_str += f"    最小间距: {np.min(results['spacing']):.2f} 像素\n"
                    result_str += f"    最大间距: {np.max(results['spacing']):.2f} 像素\n"
                    if results['avg_spacing'] > 0:
                        result_str += f"    间距变异系数: {results['std_spacing']/results['avg_spacing']:.4f}\n"
            
            result_str += f"""
    ⭐ 质量评估
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    条纹均匀性: {results['metrics']['uniformity']:.3f}
    条纹对比度: {results['metrics']['contrast']:.3f}
    条纹可见性: {results['metrics']['visibility']:.3f}
    条纹平行度: {results['metrics']['parallelism']:.3f}
    综合质量评分: {results['metrics']['overall_score']:.3f}

    🔧 调试信息
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    逐行检测点数: {results['debug_info'].get('row_detection_points', 0)}
    合并前条纹数: {results['debug_info'].get('clusters_found_before', 0)}
    点数过滤后条纹数: {results['debug_info'].get('clusters_found_after', 0)}

    📐 条纹详细信息
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            for line in results['center_lines'][:10]:
                result_str += f"""
    条纹 #{line.index + 1}:
    点数: {len(line.points)}
    中心点: ({line.center_x:.1f}, {line.center_y:.1f})
    长度: {line.length:.2f} 像素"""
                if results.get('calibration_applied', False):
                    length_cm = results.get('pixel_to_cm_ratio', 0) * line.length if results.get('pixel_to_cm_ratio') else 0
                    result_str += f" = {length_cm:.4f} cm"
                result_str += "\n"
            
            if len(results['center_lines']) > 10:
                result_str += f"\n  ... 还有 {len(results['center_lines'])-10} 条条纹\n"
            
            self.result_text.insert(1.0, result_str)
            
            self.show_visualization()
            
            # 恢复按钮状态
            self.select_btn.config(state=tk.NORMAL)
            self.calibrate_btn.config(state=tk.NORMAL)
            self.analyze_btn.config(state=tk.NORMAL)
            self.save_btn.config(state=tk.NORMAL)
            self.status_bar.config(text="分析完成")
            
            if results['count'] > 0:
                if results.get('calibration_applied', False):
                    messagebox.showinfo("完成", f"分析完成！检测到 {results['count']} 条暗条纹\n"
                                        f"整体方向: {results.get('global_angle', 0):.1f}°\n"
                                        f"平均间距: {results.get('avg_spacing_cm', 0):.4f} cm")
                else:
                    messagebox.showinfo("完成", f"分析完成！检测到 {results['count']} 条暗条纹\n"
                                        f"整体方向: {results.get('global_angle', 0):.1f}°\n"
                                        f"平均间距: {results['avg_spacing']:.2f} 像素")
            else:
                messagebox.showwarning("警告", "未检测到暗条纹，请检查图片质量或尝试调整参数")
            
        except Exception as e:
            self.show_error(f"更新结果时出错: {str(e)}")
            
    def show_visualization(self):
        """显示可视化图表"""
        if self.analyzer is None:
            return
            
        try:
            viz_window = tk.Toplevel(self.root)
            viz_window.title("莫尔条纹分析可视化")
            viz_window.geometry("1600x900")
            
            # 创建主框架
            main_frame = tk.Frame(viz_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 创建matplotlib图形，改为2x2布局
            fig, axes = plt.subplots(2, 2, figsize=(18, 11))
            fig.subplots_adjust(bottom=0.05, top=0.95, left=0.05, right=0.95, hspace=0.3, wspace=0.3)
            
            # 标题
            title = f'莫尔条纹分析报告\n{os.path.basename(self.current_image_path)}\n整体方向: {self.analyzer.global_angle:.2f}°'
            if self.analyzer.calibration_applied and self.analyzer.calibrator.get_pixel_to_cm_ratio():
                ratio = self.analyzer.calibrator.get_pixel_to_cm_ratio()
                title += f'\n网格标定: {ratio:.6f}cm/像素'
            
            fig.suptitle(title, fontsize=14, fontweight='bold')
            
            # 1. 原始图像（带标定结果）
            axes[0, 0].imshow(cv2.cvtColor(self.analyzer.original_image, cv2.COLOR_BGR2RGB))
            if self.analyzer.calibration_applied and self.analyzer.calibrator.calibration_success:
                # 绘制标定检测的线条
                h_info = self.analyzer.calibrator.get_horizontal_info()
                v_info = self.analyzer.calibrator.get_vertical_info()
                if h_info and h_info['positions']:
                    for pos in h_info['positions']:
                        axes[0, 0].axhline(y=pos, color='g', linewidth=1, alpha=0.7)
                if v_info and v_info['positions']:
                    for pos in v_info['positions']:
                        axes[0, 0].axvline(x=pos, color='y', linewidth=1, alpha=0.7)
            axes[0, 0].set_title('原始图像' + (' (绿色/黄色线条为标定检测结果)' if self.analyzer.calibration_applied else ''))
            axes[0, 0].axis('off')
            
            # 2. 提取的条纹图像
            axes[0, 1].imshow(self.analyzer.stripe_image, cmap='gray')
            axes[0, 1].set_title('提取的莫尔条纹')
            axes[0, 1].axis('off')
            
            # 3. 拟合的平行线 + 所有检测点
            axes[1, 0].imshow(cv2.cvtColor(self.analyzer.original_image, cv2.COLOR_BGR2RGB))
            if len(self.analyzer.stripe_center_lines) > 0:
                colors = plt.cm.rainbow(np.linspace(0, 1, len(self.analyzer.stripe_center_lines)))
                
                h, w = self.analyzer.original_image.shape[:2]
                
                for i, line in enumerate(self.analyzer.stripe_center_lines):
                    # 绘制该条纹上的所有检测点
                    axes[1, 0].scatter(line.x_coords, line.y_coords, 
                                    c=[colors[i]], s=15, alpha=0.6, 
                                    marker='o', edgecolors='black', linewidth=0.5, zorder=4)
                    
                    # 绘制中心点
                    axes[1, 0].scatter(line.center_x, line.center_y, 
                                    c=[colors[i]], s=100, marker='*', 
                                    edgecolors='black', linewidth=1.5, zorder=5)
                    
                    # 绘制方向线
                    if line.direction_line is not None:
                        k, b = line.direction_line
                        
                        x_center = line.center_x
                        y_center = line.center_y
                        
                        if abs(k) < 1e10:
                            angle = np.arctan(k)
                            dx = np.cos(angle)
                            dy = np.sin(angle)
                        else:
                            dx = 0
                            dy = 1
                        
                        far_dist = max(w, h)
                        x1 = x_center - far_dist * dx
                        y1 = y_center - far_dist * dy
                        x2 = x_center + far_dist * dx
                        y2 = y_center + far_dist * dy
                        
                        line_points = [(x1, y1), (x2, y2)]
                        
                        boundaries = [
                            (0, 0, w, 0),
                            (0, h, w, h),
                            (0, 0, 0, h),
                            (w, 0, w, h)
                        ]
                        
                        def line_intersection(p1, p2, p3, p4):
                            x1, y1 = p1
                            x2, y2 = p2
                            x3, y3 = p3
                            x4, y4 = p4
                            
                            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
                            if abs(denom) < 1e-10:
                                return None
                            
                            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
                            u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
                            
                            if 0 <= t <= 1 and 0 <= u <= 1:
                                x = x1 + t * (x2 - x1)
                                y = y1 + t * (y2 - y1)
                                return (x, y)
                            return None
                        
                        intersections = []
                        for boundary in boundaries:
                            inter = line_intersection(line_points[0], line_points[1], 
                                                    (boundary[0], boundary[1]), 
                                                    (boundary[2], boundary[3]))
                            if inter is not None:
                                if boundary[0] == boundary[2]:
                                    if boundary[1] <= inter[1] <= boundary[3] or boundary[3] <= inter[1] <= boundary[1]:
                                        intersections.append(inter)
                                else:
                                    if boundary[0] <= inter[0] <= boundary[2] or boundary[2] <= inter[0] <= boundary[0]:
                                        intersections.append(inter)
                        
                        if len(intersections) >= 2:
                            def dist_to_center(p):
                                return (p[0] - line.center_x)**2 + (p[1] - line.center_y)**2
                            intersections.sort(key=dist_to_center)
                            
                            if len(intersections) >= 2:
                                left_point = intersections[0]
                                right_point = intersections[1]
                                
                                axes[1, 0].plot([left_point[0], right_point[0]], 
                                            [left_point[1], right_point[1]], 
                                            color=colors[i], linewidth=2, linestyle='-',
                                            alpha=0.8, zorder=3)
                        else:
                            segment_len = min(w, h) * 0.8
                            if abs(k) < 1e10:
                                angle = np.arctan(k)
                                dx_line = np.cos(angle)
                                dy_line = np.sin(angle)
                            else:
                                dx_line = 0
                                dy_line = 1
                            
                            x_start = line.center_x - segment_len * dx_line
                            y_start = line.center_y - segment_len * dy_line
                            x_end = line.center_x + segment_len * dx_line
                            y_end = line.center_y + segment_len * dy_line
                            
                            axes[1, 0].plot([x_start, x_end], [y_start, y_end], 
                                        color=colors[i], linewidth=2, linestyle='-',
                                        alpha=0.8, zorder=3)
                
                # 绘制拟合全局方向的源条纹
                if self.analyzer.global_direction is not None:
                    max_points_line = max(self.analyzer.stripe_center_lines, 
                                        key=lambda l: len(l.points))
                    axes[1, 0].scatter(max_points_line.x_coords, max_points_line.y_coords, 
                                    c='red', s=30, alpha=0.8, marker='o', 
                                    edgecolors='yellow', linewidth=1, zorder=6,
                                    label=f'方向参考条纹 (点数:{len(max_points_line.points)})')
                    axes[1, 0].scatter(max_points_line.center_x, max_points_line.center_y, 
                                    c='red', s=150, marker='*', 
                                    edgecolors='yellow', linewidth=2, zorder=7)
                    
            axes[1, 0].set_title(f'统一方向平行线拟合 (共{len(self.analyzer.stripe_center_lines)}条)\n●检测点  ★中心点  —方向线')
            axes[1, 0].axis('off')
            axes[1, 0].legend(loc='upper right', fontsize=8)
            
            # 4. 条纹间距分布
            if len(self.analyzer.stripe_spacing) > 0:
                # 根据是否标定选择单位
                if self.analyzer.calibration_applied and len(self.analyzer.stripe_spacing_cm) > 0:
                    spacing_data = self.analyzer.stripe_spacing_cm
                    xlabel = '条纹间隔序号'
                    ylabel = '平行线间距 (cm)'
                    avg_value = self.analyzer.avg_spacing_cm
                    std_value = self.analyzer.spacing_std_cm
                    title = '条纹间距分布（实际距离）'
                    label_text = f'平均: {avg_value:.4f}cm'
                    fill_text = f'标准差: {std_value:.4f}cm'
                else:
                    spacing_data = self.analyzer.stripe_spacing
                    xlabel = '条纹间隔序号'
                    ylabel = '平行线间距 (像素)'
                    avg_value = self.analyzer.avg_spacing
                    std_value = self.analyzer.spacing_std
                    title = '条纹间距分布（像素单位）'
                    label_text = f'平均: {avg_value:.1f}px'
                    fill_text = f'标准差: {std_value:.1f}px'
                
                axes[1, 1].bar(range(len(spacing_data)), spacing_data, 
                            color='coral', alpha=0.7)
                axes[1, 1].axhline(y=avg_value, color='red', 
                                linestyle='--', linewidth=2, label=label_text)
                axes[1, 1].fill_between(range(len(spacing_data)), 
                                    avg_value - std_value,
                                    avg_value + std_value,
                                    alpha=0.2, color='red', label=fill_text)
                axes[1, 1].set_xlabel(xlabel)
                axes[1, 1].set_ylabel(ylabel)
                axes[1, 1].set_title(title)
                axes[1, 1].legend()
                axes[1, 1].grid(True, alpha=0.3)
                
                # 在柱状图上添加数值标签
                for idx, spacing in enumerate(spacing_data):
                    axes[1, 1].text(idx, spacing + (0.02 if max(spacing_data) > 0 else 0), 
                                f'{spacing:.3f}' if self.analyzer.calibration_applied else f'{spacing:.1f}', 
                                ha='center', va='bottom', fontsize=8)
            else:
                axes[1, 1].text(0.5, 0.5, '无条纹间距数据', 
                            transform=axes[1, 1].transAxes, 
                            ha='center', va='center', fontsize=14)
                axes[1, 1].set_title('条纹间距分布')
            
            plt.tight_layout()
            
            # 创建包含canvas和按钮的框架
            canvas_frame = tk.Frame(main_frame)
            canvas_frame.pack(fill=tk.BOTH, expand=True)
            
            # 嵌入matplotlib图形
            canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # 按钮框架
            button_frame = tk.Frame(main_frame, bg='#ecf0f1', height=50)
            button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)
            button_frame.pack_propagate(False)
            
            spacer = tk.Frame(button_frame, bg='#ecf0f1')
            spacer.pack(side=tk.LEFT, expand=True)
            
            save_fig_btn = tk.Button(button_frame, text="💾 保存图表", 
                                    command=lambda: self.save_figure(fig),
                                    font=('Arial', 10, 'bold'),
                                    bg='#27ae60', fg='white',
                                    padx=25, pady=8,
                                    cursor='hand2')
            save_fig_btn.pack(side=tk.RIGHT, padx=10)
            
            close_btn = tk.Button(button_frame, text="✖ 关闭", 
                                command=viz_window.destroy,
                                font=('Arial', 10, 'bold'),
                                bg='#e74c3c', fg='white',
                                padx=25, pady=8,
                                cursor='hand2')
            close_btn.pack(side=tk.RIGHT, padx=5)
            
            def on_configure(event):
                canvas_frame.update_idletasks()
                canvas.get_tk_widget().config(width=canvas_frame.winfo_width(), 
                                            height=canvas_frame.winfo_height())
            
            canvas_frame.bind('<Configure>', on_configure)
            
            viz_window.lift()
            viz_window.focus_force()
            
        except Exception as e:
            print(f"显示可视化时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def save_figure(self, fig):
        """保存当前图表"""
        save_dir = filedialog.askdirectory(title="选择保存位置")
        if save_dir:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(save_dir, f'calibrated_analysis_{timestamp}.png')
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            messagebox.showinfo("成功", f"图表已保存到:\n{filepath}")
            
    def save_report(self):
        """保存分析报告"""
        if self.analysis_results is None:
            return
            
        save_dir = filedialog.askdirectory(title="选择保存位置")
        if not save_dir:
            return
            
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result_dir = os.path.join(save_dir, f'moire_results_{timestamp}')
            os.makedirs(result_dir, exist_ok=True)
            
            # 保存文本报告
            report_path = os.path.join(result_dir, 'analysis_report.txt')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(self.result_text.get(1.0, tk.END))
            
            # 保存中心线数据（包含实际距离）
            self.save_centerline_data(result_dir)
            
            # 保存可视化图像
            self.save_visualization_images(result_dir)
            
            messagebox.showinfo("成功", f"报告已保存到:\n{result_dir}")
            self.status_bar.config(text=f"报告已保存: {result_dir}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存报告失败: {str(e)}")
            
    def save_centerline_data(self, save_dir):
        """保存中心线数据到CSV文件（包含实际距离）"""
        import csv
        
        # 保存每条中心线的点数据
        for line in self.analyzer.stripe_center_lines:
            csv_path = os.path.join(save_dir, f'centerline_{line.index+1:03d}.csv')
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['x', 'y'])
                for point in line.points:
                    writer.writerow([point[0], point[1]])
        
        # 保存汇总数据
        summary_path = os.path.join(save_dir, 'centerline_summary.csv')
        with open(summary_path, 'w', newline='') as f:
            writer = csv.writer(f)
            if self.analyzer.calibration_applied and self.analyzer.calibrator.get_pixel_to_cm_ratio():
                ratio = self.analyzer.calibrator.get_pixel_to_cm_ratio()
                writer.writerow(['条纹编号', '点数', '中心点X', '中心点Y', '长度(像素)', '长度(cm)', '方向角度(度)'])
                for line in self.analyzer.stripe_center_lines:
                    length_cm = ratio * line.length if line.length > 0 else 0
                    writer.writerow([line.index+1, len(line.points),
                                    f'{line.center_x:.2f}', f'{line.center_y:.2f}',
                                    f'{line.length:.2f}', f'{length_cm:.4f}',
                                    f'{line.direction_angle:.2f}'])
            else:
                writer.writerow(['条纹编号', '点数', '中心点X', '中心点Y', '长度(像素)', '方向角度(度)'])
                for line in self.analyzer.stripe_center_lines:
                    writer.writerow([line.index+1, len(line.points),
                                    f'{line.center_x:.2f}', f'{line.center_y:.2f}',
                                    f'{line.length:.2f}', 
                                    f'{line.direction_angle:.2f}'])
        
        # 保存间距数据
        spacing_path = os.path.join(save_dir, 'spacing_data.csv')
        with open(spacing_path, 'w', newline='') as f:
            writer = csv.writer(f)
            if self.analyzer.calibration_applied and len(self.analyzer.stripe_spacing_cm) > 0:
                writer.writerow(['序号', '间距(像素)', '间距(cm)'])
                for i, (px, cm) in enumerate(zip(self.analyzer.stripe_spacing, self.analyzer.stripe_spacing_cm)):
                    writer.writerow([i+1, f'{px:.2f}', f'{cm:.4f}'])
            else:
                writer.writerow(['序号', '间距(像素)'])
                for i, px in enumerate(self.analyzer.stripe_spacing):
                    writer.writerow([i+1, f'{px:.2f}'])
                
    def save_visualization_images(self, save_dir):
        """保存可视化图像（包含所有检测点和标定信息）"""
        try:
            # 创建带方向线和所有检测点的图像
            marked_image = self.analyzer.original_image.copy()
            h, w = marked_image.shape[:2]
            
            # 绘制标定检测的网格线条
            if self.analyzer.calibration_applied and self.analyzer.calibrator.calibration_success:
                h_info = self.analyzer.calibrator.get_horizontal_info()
                v_info = self.analyzer.calibrator.get_vertical_info()
                if h_info and h_info['positions']:
                    for pos in h_info['positions']:
                        cv2.line(marked_image, (0, pos), (w, pos), (0, 255, 0), 1)
                if v_info and v_info['positions']:
                    for pos in v_info['positions']:
                        cv2.line(marked_image, (pos, 0), (pos, h), (0, 255, 255), 1)
            
            # 为每条条纹分配颜色
            colors = plt.cm.rainbow(np.linspace(0, 1, len(self.analyzer.stripe_center_lines)))
            
            for i, line in enumerate(self.analyzer.stripe_center_lines):
                color = tuple(int(c * 255) for c in colors[i][:3])
                
                # 绘制该条纹上的所有检测点
                for point in line.points:
                    cv2.circle(marked_image, (int(point[0]), int(point[1])), 3, color, -1)
                
                # 标记中心点
                cv2.drawMarker(marked_image, (int(line.center_x), int(line.center_y)), 
                              color, cv2.MARKER_STAR, 12, 2)
                
                # 绘制方向线
                if line.direction_line is not None:
                    k, b = line.direction_line
                    x1, x2 = 0, w
                    y1 = int(k * x1 + b)
                    y2 = int(k * x2 + b)
                    cv2.line(marked_image, (x1, y1), (x2, y2), color, 2)
            
            # 高亮显示用于拟合方向的源条纹
            if self.analyzer.global_direction is not None:
                max_points_line = max(self.analyzer.stripe_center_lines, 
                                     key=lambda l: len(l.points))
                for point in max_points_line.points:
                    cv2.circle(marked_image, (int(point[0]), int(point[1])), 5, (0, 0, 255), -1)
                cv2.drawMarker(marked_image, (int(max_points_line.center_x), int(max_points_line.center_y)), 
                              (0, 0, 255), cv2.MARKER_STAR, 15, 3)
            
            cv2.imwrite(os.path.join(save_dir, 'calibrated_visualization.jpg'), marked_image)
            
            # 保存条纹间距分布图
            fig, ax = plt.subplots(figsize=(10, 6))
            if len(self.analyzer.stripe_spacing) > 0:
                if self.analyzer.calibration_applied and len(self.analyzer.stripe_spacing_cm) > 0:
                    spacing_data = self.analyzer.stripe_spacing_cm
                    ylabel = '平行线间距 (cm)'
                    title = '条纹间距分布（实际距离）'
                else:
                    spacing_data = self.analyzer.stripe_spacing
                    ylabel = '平行线间距 (像素)'
                    title = '条纹间距分布（像素单位）'
                
                ax.bar(range(len(spacing_data)), spacing_data, color='coral', alpha=0.7)
                if self.analyzer.calibration_applied:
                    ax.axhline(y=self.analyzer.avg_spacing_cm, color='red', 
                              linestyle='--', label=f'平均: {self.analyzer.avg_spacing_cm:.4f}cm')
                else:
                    ax.axhline(y=self.analyzer.avg_spacing, color='red', 
                              linestyle='--', label=f'平均: {self.analyzer.avg_spacing:.1f}px')
                ax.set_xlabel('条纹间隔序号')
                ax.set_ylabel(ylabel)
                ax.set_title(title)
                ax.legend()
                ax.grid(True, alpha=0.3)
                plt.savefig(os.path.join(save_dir, 'spacing_distribution.png'), 
                           dpi=150, bbox_inches='tight')
                plt.close()
            
        except Exception as e:
            print(f"保存图像时出错: {str(e)}")
            
    def show_error(self, error_msg):
        """显示错误信息"""
        self.progress['value'] = 0
        self.select_btn.config(state=tk.NORMAL)
        self.calibrate_btn.config(state=tk.NORMAL)
        self.analyze_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.DISABLED)
        self.status_bar.config(text=f"错误: {error_msg}")
        messagebox.showerror("分析错误", error_msg)
        
    def run(self):
        """运行GUI应用"""
        self.root.mainloop()


if __name__ == "__main__":
    app = MoireGUI()
    app.run()
