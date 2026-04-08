import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')
import sys

# 新增：设置中文字体
import matplotlib.font_manager as fm
import platform

# 根据操作系统设置中文字体
if platform.system() == 'Windows':
    chinese_font = 'SimHei'  # 黑体
elif platform.system() == 'Darwin':  # macOS
    chinese_font = 'Arial Unicode MS'
else:  # Linux
    chinese_font = 'DejaVu Sans'
    
# 设置matplotlib默认字体
plt.rcParams['font.sans-serif'] = [chinese_font, 'DejaVu Sans']  # 使用中文字体，回退到DejaVu Sans
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def get_resource_path(relative_path):
    """获取资源的绝对路径，支持打包后的环境"""
    try:
        # 打包后的临时文件夹路径
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

class HeatingExperiment:
    def __init__(self, root):
        self.root = root
        self.root.title("加热实验装置")
        self.root.geometry("1560x686")
        self.root.resizable(False, False)  # 禁止调整宽度和高度
        self.power_on = False  # 电源状态，默认为打开
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 风扇状态变量
        self.fan_on = False  # 风扇状态，默认为关闭
        self.base_acceleration_factor = 10  # 基础加速倍率
        self.current_acceleration_factor = self.base_acceleration_factor  # 当前加速倍率

        # 查询数据变量初始化
        self.query_time_data = np.array([])
        self.query_heater_data = np.array([])
        self.query_cooler_data = np.array([])
        
        # 状态变量
        self.heater_position = "取下"  # 取下/上/中
        self.rubber_position = "取下"  # 取下/中
        self.air_position = "取下"     # 新增：空气样品状态
        
        # 指示灯状态
        self.indicator_id = None  # 指示灯定时器ID
        # 参数设置
        self.target_temperature = 30  # 目标温度
        self.interval_time = 10       # 间隔时间
        
        # 新增定时器相关变量
        self.elapsed_time = 0  # 从基准时间开始经过的时间（秒）
        self.elapsed_timer_id = None  # 经过时间定时器ID
        self.last_update_time = 0  # 上次更新时间戳

        # 温度记录相关变量
        self.heater_temp = 25      # 加热盘温度
        self.cooler_temp = 25       # 散热盘温度
        self.record_count = 0         # 记录次数
        self.heating_status = "停止"  # 加热状态
        self.temperature_recording = False  # 是否在温度记录界面
        self.timer_id = None          # 定时器ID
        self.heater_base_time = 0     # 加热盘基准时间（0时刻）
        self.cooler_base_time = 0     # 散热盘基准时间（0时刻）

        # 温度数据
        self.time_data = []           # 时间数据
        self.heater_temp_data = []    # 加热盘温度数据
        self.cooler_temp_data = []    # 散热盘温度数据

        # 修改 matplotlib 工具栏的默认文本
        self.patch_matplotlib_toolbar()
        
        # 实验状态
        self.experiment_status = "散热"  # 实验区域状态
        
        # 参数设置界面状态
        self.parameter_mode = "normal"  # normal/setting_temp/setting_interval
        
        # 存储选择界面
        self.storage_selection_mode = False
        self.storage_options = ["有样品加热", "无样品加热", "散热"]
        self.current_storage_selection = 0
        
        # 长按功能变量
        self.after_id_up = None
        self.after_id_down = None
        self.long_press_delay = 500  # 长按触发延迟（毫秒）
        self.long_press_interval = 100  # 长按连续触发间隔（毫秒）
        
        # 确保保存目录存在
        current_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(current_dir, "saved_data")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 加载图片
        self.load_images()
        
        # 创建界面
        self.create_widgets()
        
        # 更新界面状态
        self.update_interface()

        # 创建图表区域
        # 创建统一的图表区域
        self.create_unified_chart()
        # 强制更新界面布局
        self.root.update_idletasks()  # 添加这一行
    
    def patch_matplotlib_toolbar(self):
        """修改 matplotlib 工具栏的默认文本"""
        import matplotlib.backends.backend_tkagg as tkagg
        
        # 修改工具栏项目定义
        tkagg.NavigationToolbar2Tk.toolitems = [
            ('主页', '重置原始视图', 'home', 'home'),
            ('后退', '后退到前一视图', 'back', 'back'),
            ('前进', '前进到后一视图', 'forward', 'forward'),
            (None, None, None, None),
            ('平移', '平移轴域，左键平移，右键缩放', 'move', 'pan'),
            ('缩放', '缩放轴域，左键框选缩放，右键框选缩放x轴', 'zoom_to_rect', 'zoom'),
            (None, None, None, None),
            ('保存', '保存图表', 'filesave', 'save_figure'),
        ]

    def init_chart_interaction_simple(self):
        """简化的图表鼠标交互 - 只保留数据提示功能"""
        self.cursor_annotations = []
        
        if not hasattr(self, 'chart_canvas') or not self.chart_canvas:
            return
        
        try:
            # 只连接鼠标移动事件用于数据显示
            self.chart_canvas.mpl_connect('motion_notify_event', self.on_chart_mouse_move_simple)
            
        except Exception as e:
            print(f"初始化图表鼠标交互失败: {e}")

    def on_chart_mouse_move_simple(self, event):
        """简化的鼠标移动事件 - 只显示数据提示"""
        if not hasattr(self, 'chart_ax') or not hasattr(self, 'chart_canvas') or event.inaxes != self.chart_ax:
            # 清除光标提示
            self.clear_chart_cursor_annotations()
            return
        
        # 只显示数据点信息
        self.show_chart_cursor_info(event)
        
    def create_unified_chart(self):
        """创建统一的图表（程序初始化时调用）"""
        # 清空图表容器
        for widget in self.chart_container.winfo_children():
            widget.destroy()
        
        # 创建matplotlib图形
        self.chart_fig, self.chart_ax = plt.subplots(figsize=(6, 4), dpi=80)
        
        # 设置默认标题和标签
        self.chart_ax.set_xlabel('时间 (秒)')
        self.chart_ax.set_ylabel('温度 (℃)')
        self.chart_ax.set_title('温度曲线')
        self.chart_ax.grid(True)
        
        # 初始化空的数据线
        self.heater_line, = self.chart_ax.plot([], [], 'r-', label='加热盘', linewidth=2)
        self.cooler_line, = self.chart_ax.plot([], [], 'b-', label='散热盘', linewidth=2)
        self.chart_ax.legend()
        
        # 创建canvas
        self.chart_canvas = FigureCanvasTkAgg(self.chart_fig, self.chart_container)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 启用 matplotlib 自带的导航工具栏
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        self.toolbar = NavigationToolbar2Tk(self.chart_canvas, self.chart_container)
        self.toolbar.update()
        
        # 精确设置每个按钮的中文提示
        self.set_precise_chinese_tooltips()
        
        # 初始化鼠标交互（只保留数据提示功能）
        self.init_chart_interaction_simple()

    def set_precise_chinese_tooltips(self):
        """精确设置工具栏按钮的中文提示"""
        # 获取工具栏的所有按钮
        buttons = {}
        for child in self.toolbar.winfo_children():
            if hasattr(child, '_NavigationToolbar2Tk__text'):
                text = child._NavigationToolbar2Tk__text
                buttons[text] = child
        
        # 设置中文提示
        tooltip_mapping = {
            'Home': '回到原始视图',
            'Back': '后退到上一视图', 
            'Forward': '前进到下一视图',
            'Pan': '左键拖拽平移，右键拖拽缩放',
            'Zoom': '框选区域缩放',
            'Subplots': '配置子图参数',
            'Save': '保存图表'
        }
        
        for eng_text, chn_tooltip in tooltip_mapping.items():
            if eng_text in buttons:
                buttons[eng_text].configure(tooltip=chn_tooltip)

    def init_chart_interaction(self):
        """初始化图表的鼠标交互功能"""
        # 存储鼠标状态
        self.zoom_rect = None
        self.zoom_start = None
        self.cursor_annotations = []
        
        # 移除自定义的中键平移变量
        
        if not hasattr(self, 'chart_canvas') or not self.chart_canvas:
            return
        
        try:
            # 创建框选矩形
            self.zoom_rect = plt.Rectangle((0,0), 0, 0, fill=False, edgecolor='red', linewidth=2, alpha=0.5)
            self.chart_ax.add_patch(self.zoom_rect)
            self.zoom_rect.set_visible(False)
            
            # 启用 matplotlib 自带的平移和缩放功能
            from matplotlib.widgets import Cursor
            self.chart_canvas.mpl_connect('button_press_event', self.on_chart_mouse_press)
            self.chart_canvas.mpl_connect('button_release_event', self.on_chart_mouse_release)
            self.chart_canvas.mpl_connect('motion_notify_event', self.on_chart_mouse_move)
            self.chart_canvas.mpl_connect('scroll_event', self.on_chart_mouse_scroll)
            
            # 设置 matplotlib 导航工具
            self.chart_fig.canvas.toolbar.update()  # 确保工具栏更新
            
        except Exception as e:
            print(f"初始化图表鼠标交互失败: {e}")

    def on_chart_mouse_press(self, event):
        """统一图表鼠标按下事件"""
        if not hasattr(self, 'chart_ax') or not hasattr(self, 'chart_canvas') or event.inaxes != self.chart_ax:
            return
        
        # 左键：开始框选（保留自定义框选功能）
        if event.button == 1:  # 左键
            self.zoom_start = (event.xdata, event.ydata)
            if self.zoom_rect:
                self.zoom_rect.set_visible(True)
                self.zoom_rect.set_xy((event.xdata, event.ydata))
                self.zoom_rect.set_width(0)
                self.zoom_rect.set_height(0)
                self.chart_canvas.draw_idle()

    def on_chart_mouse_release(self, event):
        """统一图表鼠标释放事件"""
        if not hasattr(self, 'chart_ax') or not hasattr(self, 'chart_canvas') or event.inaxes != self.chart_ax:
            return
        
        # 左键：结束框选并缩放
        if event.button == 1 and self.zoom_start:  # 左键
            x0, y0 = self.zoom_start
            x1, y1 = event.xdata, event.ydata
            
            if x0 != x1 and y0 != y1:  # 确保框选了有效区域
                # 设置新的坐标轴范围
                self.chart_ax.set_xlim(min(x0, x1), max(x0, x1))
                self.chart_ax.set_ylim(min(y0, y1), max(y0, y1))
            
            # 隐藏框选矩形
            if self.zoom_rect:
                self.zoom_rect.set_visible(False)
            self.zoom_start = None
            self.chart_canvas.draw_idle()
        
        # 右键和中键：matplotlib 会自动处理，不需要额外代码

    def on_chart_mouse_move(self, event):
        """统一图表鼠标移动事件"""
        if not hasattr(self, 'chart_ax') or not hasattr(self, 'chart_canvas') or event.inaxes != self.chart_ax:
            # 清除光标提示
            self.clear_chart_cursor_annotations()
            return
        
        # 左键拖拽：更新框选矩形
        if self.zoom_start and event.button == 1:
            x0, y0 = self.zoom_start
            x1, y1 = event.xdata, event.ydata
            if self.zoom_rect:
                self.zoom_rect.set_width(x1 - x0)
                self.zoom_rect.set_height(y1 - y0)
                self.chart_canvas.draw_idle()
        
        # 移除自定义的中键平移处理，使用 matplotlib 自带功能
        
        # 普通移动：显示数据点信息
        else:
            self.show_chart_cursor_info(event)

    def on_chart_mouse_scroll(self, event):
        """统一图表鼠标滚轮事件 - 以画面中心为中心缩放"""
        if not hasattr(self, 'chart_ax') or not hasattr(self, 'chart_canvas') or event.inaxes != self.chart_ax:
            return
        
        # 缩放因子
        scale_factor = 0.9 if event.button == 'up' else 1.1
        
        # 获取当前坐标轴范围
        xlim = self.chart_ax.get_xlim()
        ylim = self.chart_ax.get_ylim()
        
        # 计算画面中心点
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        
        # 计算新的坐标轴范围
        new_x_width = (xlim[1] - xlim[0]) * scale_factor
        new_y_width = (ylim[1] - ylim[0]) * scale_factor
        
        new_xlim = (x_center - new_x_width / 2, x_center + new_x_width / 2)
        new_ylim = (y_center - new_y_width / 2, y_center + new_y_width / 2)
        
        self.chart_ax.set_xlim(new_xlim)
        self.chart_ax.set_ylim(new_ylim)
        self.chart_canvas.draw_idle()

    def show_chart_cursor_info(self, event):
        """显示统一图表光标所在位置的数据点信息"""
        # 清除之前的提示
        self.clear_chart_cursor_annotations()
        
        # 根据当前模式获取数据
        time_data, heater_data, cooler_data = self.get_current_chart_data()
        
        # 修复：正确检查 numpy 数组是否为空
        if time_data is None or len(time_data) == 0:
            return
        
        # 找到最接近的时间点
        time_diff = np.abs(time_data - event.xdata)
        closest_idx = np.argmin(time_diff)
        
        # 修复：正确计算数据范围
        if len(time_data) > 1:
            data_range = max(time_data) - min(time_data)
        else:
            data_range = 1  # 防止除以零
        
        if time_diff[closest_idx] > data_range / 50:
            return  # 如果距离太远，不显示
        
        time_val = time_data[closest_idx]
        heater_val = heater_data[closest_idx] if len(heater_data) > closest_idx else 0
        cooler_val = cooler_data[closest_idx] if len(cooler_data) > closest_idx else 0
        
        # 创建提示文本
        info_text = f'时间: {time_val:.1f}s\n加热盘: {heater_val:.1f}℃\n散热盘: {cooler_val:.1f}℃'
        
        # 在数据点处添加标记
        heater_point = self.chart_ax.plot(time_val, heater_val, 'ro', markersize=6, alpha=0.7)[0]
        cooler_point = self.chart_ax.plot(time_val, cooler_val, 'bo', markersize=6, alpha=0.7)[0]
        
        # 添加文本注释
        annotation = self.chart_ax.annotate(info_text,
                            xy=(time_val, (heater_val + cooler_val) / 2),
                            xytext=(10, 10),
                            textcoords='offset points',
                            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        # 存储引用以便清除
        self.cursor_annotations.extend([heater_point, cooler_point, annotation])
        self.chart_canvas.draw_idle()

    def clear_chart_cursor_annotations(self):
        """清除统一图表光标提示"""
        for annotation in self.cursor_annotations:
            try:
                annotation.remove()
            except:
                pass
        self.cursor_annotations.clear()

    def get_current_chart_data(self):
        """根据当前模式获取图表数据"""
        if self.parameter_mode == "temperature_recording":
            # 温度记录模式：使用实时记录的数据
            # 确保返回 numpy 数组
            return (
                np.array(self.time_data) if self.time_data else np.array([]),
                np.array(self.heater_temp_data) if self.heater_temp_data else np.array([]),
                np.array(self.cooler_temp_data) if self.cooler_temp_data else np.array([])
            )
        elif self.parameter_mode == "data_query":
            # 数据查询模式：使用查询的数据
            if hasattr(self, 'query_time_data') and self.query_time_data is not None:
                return (
                    self.query_time_data,
                    self.query_heater_data,
                    self.query_cooler_data
                )
            else:
                return np.array([]), np.array([]), np.array([])
        else:
            # 其他模式：返回空数组
            return np.array([]), np.array([]), np.array([])
    
    def on_closing(self):
        """窗口关闭时的清理操作"""
        print("正在退出程序，清理资源...")
        print(f"最终状态 - 风扇: {'开启' if self.fan_on else '关闭'}, 加速倍率: {self.current_acceleration_factor}倍")
        self.cleanup()
        self.root.quit()  # 改为 quit() 而不是 destroy()
        self.root.destroy()  # 然后再调用 destroy()
    
    def cleanup(self):
        """清理所有定时器和资源"""
        # 停止所有定时器
        self.stop_all_timers()
        
        # 停止经过时间定时器
        self.stop_elapsed_timer()
        
        # 停止长按定时器
        self.stop_long_press()
        
        # 停止指示灯定时器
        self.stop_indicator()

        # 删除数据查询的Excel文件
        self.delete_query_excel_files()
        
        # 确保所有 after 调用都被取消
        try:
            # 获取所有待处理的 after 事件并取消
            after_ids = self.root.tk.call('after', 'info')
            for after_id in after_ids:
                self.root.after_cancel(after_id)
        except:
            pass

    def cleanup_matplotlib(self):
        """清理 matplotlib 资源"""
        try:
            # 关闭所有 matplotlib 图形
            plt.close('all')
            
            # 清理图表相关的资源
            if hasattr(self, 'chart_fig'):
                plt.close(self.chart_fig)
            if hasattr(self, 'fig'):
                plt.close(self.fig)
            if hasattr(self, 'query_fig'):
                plt.close(self.query_fig)
                
            # 断开所有 matplotlib 事件
            if hasattr(self, 'chart_canvas') and self.chart_canvas:
                try:
                    self.chart_canvas.mpl_disconnect('button_press_event')
                    self.chart_canvas.mpl_disconnect('button_release_event')
                    self.chart_canvas.mpl_disconnect('motion_notify_event')
                    self.chart_canvas.mpl_disconnect('scroll_event')
                except:
                    pass
                    
        except Exception as e:
            print(f"清理 matplotlib 资源时出错: {e}")

    
    def delete_query_excel_files(self):
        """删除数据查询生成的Excel文件"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            save_dir = os.path.join(current_dir, "saved_data")
            
            # 要删除的文件列表
            files_to_delete = [
                "saved_with_sample_heating.xlsx",
                "saved_without_sample_heating.xlsx", 
                "saved_cooling.xlsx"
            ]
            
            deleted_files = []
            
            for filename in files_to_delete:
                filepath = os.path.join(save_dir, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    deleted_files.append(filename)
                    print(f"已删除文件: {filename}")
            
            if deleted_files:
                print(f"程序退出时已删除 {len(deleted_files)} 个数据文件")
            else:
                print("没有找到需要删除的数据文件")
                
        except Exception as e:
            print(f"删除数据文件时出错: {e}")

    def load_images(self):
        """从background文件夹加载图片"""
        try:
            # 使用资源路径获取函数
            background_dir = get_resource_path("background")
            
            # 加载图片并调整大小
            heater_img = Image.open(os.path.join(background_dir, "加热盘.jpg"))
            cooler_img = Image.open(os.path.join(background_dir, "散热盘.jpg"))
            rubber_img = Image.open(os.path.join(background_dir, "橡胶样品.jpg"))
            experiment_img = Image.open(os.path.join(background_dir, "FD-TC-D实验仪.png"))  # 新增
            
            # 调整图片大小以适应界面
            self.heater_photo = ImageTk.PhotoImage(heater_img.resize((280, 70*2)))
            self.cooler_photo = ImageTk.PhotoImage(cooler_img.resize((280, 150*2)))
            self.rubber_photo = ImageTk.PhotoImage(rubber_img.resize((280, 7*2)))
            self.experiment_photo = ImageTk.PhotoImage(experiment_img.resize((750, 300)))  # 新增，调整大小
            
        except Exception as e:
            print(f"图片加载错误: {e}")
            # 创建默认图片作为备用
            self.create_default_images()
    
    def create_default_images(self):
        """创建默认图片（如果图片加载失败）"""
        # 这里创建简单的彩色矩形作为默认图片
        self.heater_photo = tk.PhotoImage(width=200, height=150)
        self.heater_photo.put("red", to=(0, 0, 280, 140))
        
        self.cooler_photo = tk.PhotoImage(width=200, height=150)
        self.cooler_photo.put("blue", to=(0, 0, 280, 300))
        
        self.rubber_photo = tk.PhotoImage(width=200, height=100)
        self.rubber_photo.put("gray", to=(0, 0, 280, 14))

         # 新增实验仪默认图片
        self.experiment_photo = tk.PhotoImage(width=800, height=200)
        self.experiment_photo.put("green", to=(0, 0, 500, 300))
    
    def create_widgets(self):
        """创建界面组件"""
        # 主画布框架 - 修改为三列布局
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重 - 三列布局
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)  # 左侧实验区域
        main_frame.columnconfigure(1, weight=1)  # 中间实验仪区域
        main_frame.columnconfigure(2, weight=1)  # 右侧数据计算区域
        main_frame.rowconfigure(0, weight=1)
        
        # 左侧实验区域框架
        left_frame = ttk.Frame(main_frame, width=450)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        
        # 中间实验仪区域框架
        middle_frame = ttk.Frame(main_frame, width=750)
        middle_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.rowconfigure(0, weight=1)
        
        # 右侧数据计算区域框架
        right_frame = ttk.Frame(main_frame, width=350)
        right_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        left_frame.grid_propagate(False)  # 禁止自动调整大小
        middle_frame.grid_propagate(False)  # 禁止自动调整大小
        right_frame.grid_propagate(False)  # 禁止自动调整大小

        # 在左侧框架中放置原有的三个区域
        self.top_frame = ttk.Frame(left_frame, height=140)
        self.top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.top_frame.grid_propagate(False)
        self.top_frame.columnconfigure(0, weight=1)
        
        self.middle_frame = ttk.Frame(left_frame, height=14)
        self.middle_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        self.middle_frame.columnconfigure(0, weight=1)
        
        self.bottom_frame = ttk.Frame(left_frame, height=300)
        self.bottom_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        self.bottom_frame.grid_propagate(False)
        self.bottom_frame.columnconfigure(0, weight=1)
        
        # 控制区域放在左侧框架底部
        self.control_frame = ttk.LabelFrame(left_frame, text="控制区域", padding="10")
        self.control_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # 状态提示栏
        self.status_label = ttk.Label(self.control_frame, text="实验状态：散热", 
                                    foreground="blue", font=('Arial', 10, 'bold'))
        self.status_label.grid(row=2, column=0, columnspan=3, pady=5)
        
        # 在中间框架中放置实验仪图片和按钮
        self.create_experiment_panel(middle_frame)
        
        # 在右侧框架中创建数据计算区域
        self.create_calculation_panel(right_frame)
        
        # 原有的散热盘图片和控制按钮代码保持不变...
        self.cooler_label = ttk.Label(self.bottom_frame, image=self.cooler_photo)
        self.cooler_label.grid(row=0, column=0, pady=0)
        
        self.control_frame.columnconfigure(0, weight=1, minsize=130)
        self.control_frame.columnconfigure(1, weight=1, minsize=130)
        self.control_frame.columnconfigure(2, weight=1, minsize=130)
        self.control_frame.rowconfigure(0, weight=1, minsize=35)
        self.control_frame.rowconfigure(1, weight=1, minsize=35)
        self.control_frame.rowconfigure(2, weight=1, minsize=25)
        
        # 第一行按钮
        self.rubber_button = ttk.Button(self.control_frame, text="放置橡胶样品", 
                                    command=self.toggle_rubber)
        self.rubber_button.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        
        self.air_button = ttk.Button(self.control_frame, text="隔出空气隙", 
                                command=self.toggle_air)
        self.air_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        
        self.heater_button = ttk.Button(self.control_frame, text="放置加热器", 
                                    command=self.toggle_heater)
        self.heater_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NSEW)
        
        # 第二行按钮
        self.reset_temp_button = ttk.Button(self.control_frame, text="重置温度", 
                                    command=self.reset_temperature)
        self.reset_temp_button.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NSEW)
        
        # # 恢复图表按钮
        # self.recover_chart_button = ttk.Button(self.control_frame, text="恢复图表", 
        #                                 command=self.recreate_unified_chart)
        # self.recover_chart_button.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NSEW)
    
    def recreate_unified_chart(self):
        """完全重新创建统一图表（解决卡住问题）"""
        try:
            print("重新创建图表...")
            
            # 1. 彻底清理现有图表
            self.destroy_chart_completely()
            
            # 2. 重新创建图表容器
            for widget in self.chart_container.winfo_children():
                widget.destroy()
            
            # 3. 创建全新的matplotlib图形
            self.chart_fig, self.chart_ax = plt.subplots(figsize=(6, 4), dpi=80)
            
            # 4. 设置默认标题和标签
            self.chart_ax.set_xlabel('时间 (秒)')
            self.chart_ax.set_ylabel('温度 (℃)')
            self.chart_ax.set_title('温度曲线')
            self.chart_ax.grid(True)
            
            # 5. 初始化空的数据线
            self.heater_line, = self.chart_ax.plot([], [], 'r-', label='加热盘', linewidth=2)
            self.cooler_line, = self.chart_ax.plot([], [], 'b-', label='散热盘', linewidth=2)
            self.chart_ax.legend()
            
            # 6. 创建全新的canvas
            self.chart_canvas = FigureCanvasTkAgg(self.chart_fig, self.chart_container)
            self.chart_canvas.draw()
            self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 7. 重新创建工具栏
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            self.toolbar = NavigationToolbar2Tk(self.chart_canvas, self.chart_container)
            self.toolbar.update()
            self.set_precise_chinese_tooltips()
            
            # 8. 重新初始化交互
            self.init_chart_interaction_simple()
            
            # 9. 根据当前模式恢复数据
            self.restore_chart_data()
            
            print("图表重新创建完成")
            
        except Exception as e:
            print(f"重新创建图表失败: {e}")
            # 如果失败，尝试更基础的恢复
            self.emergency_chart_recovery()

    def destroy_chart_completely(self):
        """完全销毁图表资源"""
        try:
            # 断开所有事件
            self.disconnect_all_chart_events()
            
            # 清理工具栏
            if hasattr(self, 'toolbar'):
                try:
                    self.toolbar.destroy()
                except:
                    pass
                self.toolbar = None
            
            # 清理canvas
            if hasattr(self, 'chart_canvas'):
                try:
                    if hasattr(self.chart_canvas, 'get_tk_widget'):
                        self.chart_canvas.get_tk_widget().destroy()
                    self.chart_canvas = None
                except:
                    pass
            
            # 关闭图形
            if hasattr(self, 'chart_fig'):
                try:
                    plt.close(self.chart_fig)
                except:
                    pass
                self.chart_fig = None
                self.chart_ax = None
                self.heater_line = None
                self.cooler_line = None
            
            # 强制垃圾回收
            import gc
            gc.collect()
            
        except Exception as e:
            print(f"销毁图表资源失败: {e}")

    def disconnect_all_chart_events(self):
        """断开所有图表事件"""
        canvases = []
        if hasattr(self, 'chart_canvas') and self.chart_canvas:
            canvases.append(self.chart_canvas)
        if hasattr(self, 'canvas') and self.canvas:
            canvases.append(self.canvas)
        if hasattr(self, 'query_canvas') and self.query_canvas:
            canvases.append(self.query_canvas)
        
        for canvas in canvases:
            try:
                # 使用更彻底的事件断开方法
                if hasattr(canvas, 'callbacks'):
                    canvas.callbacks.callbacks.clear()
                if hasattr(canvas, '_button_press_id'):
                    canvas.mpl_disconnect(canvas._button_press_id)
                if hasattr(canvas, '_button_release_id'):
                    canvas.mpl_disconnect(canvas._button_release_id)
                if hasattr(canvas, '_motion_notify_id'):
                    canvas.mpl_disconnect(canvas._motion_notify_id)
                if hasattr(canvas, '_scroll_id'):
                    canvas.mpl_disconnect(canvas._scroll_id)
            except:
                pass

    def restore_chart_data(self):
        """恢复图表数据"""
        try:
            # 根据当前模式获取数据
            time_data, heater_data, cooler_data = self.get_current_chart_data()
            
            if len(time_data) > 0:
                # 更新数据线
                self.heater_line.set_data(time_data, heater_data)
                self.cooler_line.set_data(time_data, cooler_data)
                
                # 调整坐标轴范围
                if len(time_data) > 1:
                    self.chart_ax.set_xlim(0, max(time_data) * 1.1)
                    all_temps = np.concatenate([heater_data, cooler_data])
                    if len(all_temps) > 0:
                        temp_min = min(all_temps)
                        temp_max = max(all_temps)
                        temp_range = temp_max - temp_min
                        self.chart_ax.set_ylim(temp_min - temp_range * 0.1, temp_max + temp_range * 0.1)
                
                # 强制重绘
                self.chart_canvas.draw_idle()
                
        except Exception as e:
            print(f"恢复图表数据失败: {e}")

    def emergency_chart_recovery(self):
        """紧急图表恢复"""
        try:
            print("执行紧急图表恢复...")
            
            # 完全清空容器
            for widget in self.chart_container.winfo_children():
                try:
                    widget.destroy()
                except:
                    pass
            
            # 创建简单的替代显示
            emergency_label = tk.Label(self.chart_container, text="图表初始化中...", 
                                    bg='white', font=('Arial', 14))
            emergency_label.pack(expand=True, fill=tk.BOTH)
            
            # 延迟重新创建
            self.root.after(1000, self.recreate_unified_chart)
            
        except Exception as e:
            print(f"紧急恢复失败: {e}")

    def create_calculation_panel(self, parent):
        """创建右侧数据计算区域面板"""
        # 数据计算区域主框架
        self.calculation_frame = ttk.LabelFrame(parent, text="数据计算区域", padding="10")
        self.calculation_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.calculation_frame.columnconfigure(0, weight=1)
        
        # 创建计算区域内容
        self.create_calculation_area()

    def reset_temperature(self):
        """重置加热器和散热器温度到初始值"""
        # 重置温度值
        self.heater_temp = 25
        self.cooler_temp = 25
        
        # 如果正在温度记录界面，更新显示
        if hasattr(self, 'heater_temp_label') and self.temperature_recording:
            self.update_temperature_display()
        
        # 重置基准时间
        self.get_base_times_from_current_temperature()
        
        # 显示重置成功消息
        print("温度已重置到初始值: 25℃")
        
        # 可选：显示一个短暂的消息提示
        self.show_temp_reset_message()

    def show_temp_reset_message(self):
        """显示温度重置成功的临时消息"""
        # 保存原始状态文本
        original_text = self.status_label.cget("text")
        
        # 显示重置成功消息
        self.status_label.config(text="温度已重置到 25℃", foreground="green")
        
        # 2秒后恢复原始状态
        self.root.after(2000, lambda: self.status_label.config(
            text=original_text, foreground="blue"))
    
    def create_experiment_panel(self, parent):
        """创建中间实验仪控制面板"""
        # 实验仪容器
        container = tk.Frame(parent, width=700, height=300)
        container.grid(row=0, column=0, pady=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        container.grid_propagate(False)
        
        # 图表容器
        self.chart_container = tk.Frame(parent, width=700, height=300, bg='white')
        self.chart_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.chart_container.grid_propagate(False)

        # 实验仪图片作为背景
        experiment_label = tk.Label(container, image=self.experiment_photo)
        experiment_label.place(x=0, y=0, width=750, height=300)
        
        # 在图片上叠加显示框（右侧区域）- 使用白色背景
        self.display_frame = tk.Frame(container, bg='white', relief='solid', bd=0)
        self.display_frame.place(x=120, y=80, width=180, height=120)
        
        # 在图片上叠加按钮（底部区域）
        button_y = 120  # 按钮的垂直位置
        
        # 新增：指示灯（在向上按钮左侧）
        self.indicator_label = tk.Label(container, text="●", 
                                    font=('Arial', 20), 
                                    fg='gray', bg='#d6d9de')
        self.indicator_label.place(x=57+3, y=button_y+20, width=20, height=20)

        # 向上按钮 - 深灰色
        self.up_button = tk.Button(container, text="", 
                            bg='#333333', fg='#333333', relief='flat', width=8, height=1)
        self.up_button.place(x=375, y=button_y, width=20, height=20)
        self.up_button.bind("<ButtonPress-1>", lambda e: self.start_long_press_up())
        self.up_button.bind("<ButtonRelease-1>", lambda e: self.stop_long_press())
        
        # 向下按钮 - 深灰色
        self.down_button = tk.Button(container, text="", 
                                bg='#333333', fg='#333333', relief='flat', width=8, height=1)
        self.down_button.place(x=375, y=button_y+70, width=20, height=20)
        self.down_button.bind("<ButtonPress-1>", lambda e: self.start_long_press_down())
        self.down_button.bind("<ButtonRelease-1>", lambda e: self.stop_long_press())
        
        # 确定按钮 - 深灰色
        self.ok_button = tk.Button(container, text="", command=self.confirm_selection, 
                            bg='#333333', fg='#333333',relief='flat', width=8, height=1)
        self.ok_button.place(x=450, y=button_y , width=20, height=20)
        
        # 返回按钮 - 深灰色
        self.back_button = tk.Button(container, text="", command=self.go_back, 
                                bg='#333333', fg='#333333',relief='flat', width=8, height=1)
        self.back_button.place(x=450, y=button_y +70, width=20, height=20)
        
        # 新增：风扇开关按钮（在返回按钮右侧）
        self.fan_button = tk.Button(container, text="→", command=self.toggle_fan, 
                                bg='#D6D9DE', fg='red', relief='flat', width=8, height=1,
                                font=('Arial', 20, 'bold'))
        self.fan_button.place(x=550, y=button_y +70, width=30, height=20)  # 在返回按钮右侧
        
        # 新增：电源开关按钮（在确定返回按钮右方）
        self.power_on_button = tk.Button(container, text="O", command=self.turn_off_power,
                                    bg='#CC667F', fg='black', relief='flat', width=8, height=1)
        self.power_on_button.place(x=618+45, y=button_y+ 62, width=20, height=20)
        
        self.power_off_button = tk.Button(container, text="I", command=self.turn_on_power,
                                    bg='#CC667f', fg='black', relief='flat', width=8, height=1)
        self.power_off_button.place(x=618+45, y=button_y +35, width=20, height=20)

        if not self.power_on:
            self.hide_experiment_panel()
        else:
            self.initialize_experiment_panel()

        # 更新电源按钮状态
        self.update_power_buttons()
    
        # 在显示框内创建菜单项
        self.menu_items = ["温度记录", "参数设置", "数据查询"]
        self.current_selection = 0  # 当前选中的菜单项索引
        
        self.menu_labels = []
        menu_start_y = 10
        for i, item in enumerate(self.menu_items):
            # 使用白色背景的标签
            label = tk.Label(self.display_frame, text=item, bg='white', padx=10, pady=5, 
                            font=('Arial', 12,'bold'), anchor='w', width=15)
            label.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=2)
            label.bind("<Button-1>", lambda e, idx=i: self.select_menu_item(idx))
            self.menu_labels.append(label)
        
        # 初始高亮第一项
        self.highlight_selected_menu()

    def toggle_fan(self):
        """切换风扇开关状态"""
        # 如果在温度记录界面，禁止切换风扇
        if self.temperature_recording:
            print("温度记录进行中，禁止切换风扇")
            return
        self.fan_on = not self.fan_on
        
        if self.fan_on:
            self.fan_button.config(text="←")  # 绿色表示开启
            print("风扇已开启")

        else:
            self.fan_button.config(text="→")  # 灰色表示关闭
            print("风扇已关闭")
        
        # 更新状态显示
        self.update_fan_status_display()
        self.update_experiment_status()
        # 只有在温度记录界面才更新温度显示
        if self.temperature_recording and hasattr(self, 'heater_temp_label'):
            self.update_temperature_display()
        # self.get_base_times_from_current_temperature()

    def update_fan_status_display(self):
        """更新风扇状态显示"""
        # 如果有温度记录界面，可以在这里更新风扇状态显示
        if hasattr(self, 'heating_status_label') and self.temperature_recording:
            # 可以在温度记录界面添加风扇状态显示
            pass

    def update_indicator(self):
        """更新指示灯状态"""
        if (self.heating_status == "加热" and 
            self.heater_temp < self.target_temperature +0.2 and
            self.power_on):  # 只有在电源打开时才更新
            # 亮起指示灯（红色）
            self.indicator_label.config(fg='red', text="●")
        else:
            # 熄灭指示灯（灰色）
            self.indicator_label.config(fg='gray', text="●")
        
        # 设置定时器持续更新指示灯状态
        self.indicator_id = self.root.after(500, self.update_indicator)  # 每500毫秒更新一次

    def start_indicator(self):
        """启动指示灯定时器"""
        if not self.indicator_id:
            self.update_indicator()

    def stop_indicator(self):
        """停止指示灯定时器"""
        if self.indicator_id:
            self.root.after_cancel(self.indicator_id)
            self.indicator_id = None
        # 确保指示灯熄灭
        self.indicator_label.config(fg='gray', text="●")

    def turn_on_power(self):
        """打开电源"""
        self.power_on = True
        self.update_power_buttons()
        self.initialize_experiment_panel()
        # 启动指示灯
        self.start_indicator()
        self.heater_button.config(state="enabled")
        self.reset_temp_button.config(state="enabled")
        if self.rubber_position == "中":
            self.air_button.config(state="disabled")
        else:
            self.air_button.config(state="normal")
        
        if self.air_position == "中":
            self.rubber_button.config(state="disabled")
        else:
            self.rubber_button.config(state="normal")
        print("电源已打开")

    def turn_off_power(self):
        """关闭电源"""
        self.power_on = False
        self.update_power_buttons()
        self.hide_experiment_panel()
        # 停止指示灯
        self.stop_indicator()
        self.heater_button.config(state="enabled")
        self.reset_temp_button.config(state="enabled")
        if self.rubber_position == "中":
            self.air_button.config(state="disabled")
        else:
            self.air_button.config(state="normal")
        
        if self.air_position == "中":
            self.rubber_button.config(state="disabled")
        else:
            self.rubber_button.config(state="normal")
        print("电源已关闭")

    def update_power_buttons(self):
        """更新电源按钮状态"""
        if self.power_on:
            # 电源打开时，关闭电源按钮显示为红色，打开电源按钮显示为灰色
            self.power_on_button.config(state='normal')
            self.power_off_button.config(state='disabled')
        else:
            # 电源关闭时，打开电源按钮显示为绿色，关闭电源按钮显示为灰色
            self.power_on_button.config(state='disabled')
            self.power_off_button.config(state='normal')

    def initialize_experiment_panel(self):
        """初始化实验仪到主界面"""
        # 显示显示框
        self.display_frame.place(x=120, y=80, width=200, height=120)
        
        # 重置到主菜单
        self.parameter_mode = "normal"
        self.temperature_recording = False
        self.storage_selection_mode = False
        
        # 停止所有定时器
        self.stop_all_timers()
        
        # 显示主菜单
        self.show_main_menu()
        
        # 启用操作按钮
        self.ok_button.config(state='normal')
        self.back_button.config(state='normal')
        self.up_button.config(state='normal')
        self.down_button.config(state='normal')

    def hide_experiment_panel(self):
        """隐藏实验仪显示框"""
        # 隐藏显示框
        self.display_frame.place_forget()
        
        # 停止所有定时器
        self.stop_all_timers()
        
        # 禁用操作按钮
        self.ok_button.config(state='disabled')
        self.back_button.config(state='disabled')
        self.up_button.config(state='disabled')
        self.down_button.config(state='disabled')
        
        # 清空显示框内容
        for widget in self.display_frame.winfo_children():
            widget.destroy()
        
        # 注意：不移除图表容器中的温度曲线，保留图表显示
        # 清空图表容器的代码已移除

    def create_calculation_area(self):
        """创建数据计算区域内容"""
        # 计算冷却速率部分
        cooling_frame = ttk.LabelFrame(self.calculation_frame, text="计算冷却速率", padding="5")
        cooling_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        cooling_frame.columnconfigure(0, weight=1)
        
        # 第一行：温度范围
        temp_range_frame = ttk.Frame(cooling_frame)
        temp_range_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(temp_range_frame, text="温度范围（℃）：").grid(row=0, column=0, sticky=tk.W)
        self.cooling_temp1 = ttk.Entry(temp_range_frame, width=6)
        self.cooling_temp1.grid(row=0, column=1, padx=2)
        ttk.Label(temp_range_frame, text="-").grid(row=0, column=2)
        self.cooling_temp2 = ttk.Entry(temp_range_frame, width=6)
        self.cooling_temp2.grid(row=0, column=3, padx=2)
        
        # 第二行：冷却速率和计算按钮
        cooling_rate_frame = ttk.Frame(cooling_frame)
        cooling_rate_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(cooling_rate_frame, text="冷却速率（℃/s）：").grid(row=0, column=0, sticky=tk.W)
        self.cooling_rate_var = tk.StringVar(value="")
        ttk.Label(cooling_rate_frame, textvariable=self.cooling_rate_var, width=8).grid(row=0, column=1)
        ttk.Button(cooling_rate_frame, text="计算", command=self.calculate_cooling_rate, width=8).grid(row=0, column=2, padx=(10,0))
        
        # 计算导热系数部分
        conductivity_frame = ttk.LabelFrame(self.calculation_frame, text="计算导热系数", padding="5")
        conductivity_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        conductivity_frame.columnconfigure(0, weight=1)
        
        # 第一行：散热盘参数
        row1_frame = ttk.Frame(conductivity_frame)
        row1_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(row1_frame, text="散热盘厚度（mm）：", width=16).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(row1_frame, text="10.11", width=8).grid(row=0, column=1)
        
        # 第二行：散热盘半径
        row2_frame = ttk.Frame(conductivity_frame)
        row2_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(row2_frame, text="散热盘半径（mm）：", width=16).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(row2_frame, text="65.10", width=8).grid(row=0, column=1)
        
        # 第三行：样品厚度
        row3_frame = ttk.Frame(conductivity_frame)
        row3_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(row3_frame, text="样品厚度（mm）：", width=16).grid(row=0, column=0, sticky=tk.W)
        # 修改样品厚度选项，明确标识材料
        self.sample_thickness_var = tk.StringVar(value="7.96 (橡胶)")
        
        # 创建下拉选项，明确标识材料类型
        thickness_options = ["7.96 (橡胶)", "1.00 (空气)"]
        
        thickness_combo = ttk.Combobox(row3_frame, textvariable=self.sample_thickness_var, 
                                    values=thickness_options, width=12, state="readonly")
        thickness_combo.grid(row=0, column=1)

        # 第四行：样品直径
        row4_frame = ttk.Frame(conductivity_frame)
        row4_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(row4_frame, text="样品直径（mm）：", width=16).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(row4_frame, text="128.76", width=8).grid(row=0, column=1)
        
        # 第五行：散热盘质量
        row5_frame = ttk.Frame(conductivity_frame)
        row5_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(row5_frame, text="散热盘质量（g）：", width=16).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(row5_frame, text="363.22", width=8).grid(row=0, column=1)
        
        # 第六行：散热盘比热容
        row6_frame = ttk.Frame(conductivity_frame)
        row6_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(row6_frame, text="散热盘比热容：", width=16).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(row6_frame, text="880 J/(Kg*K)", width=12).grid(row=0, column=1)
        
        # 第七行：加热盘稳态温度
        row7_frame = ttk.Frame(conductivity_frame)
        row7_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(row7_frame, text="加热盘稳态温度（℃）：", width=18).grid(row=0, column=0, sticky=tk.W)
        self.heater_steady_temp = ttk.Entry(row7_frame, width=8)
        self.heater_steady_temp.grid(row=0, column=1)
        
        # 第八行：散热盘稳态温度
        row8_frame = ttk.Frame(conductivity_frame)
        row8_frame.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(row8_frame, text="散热盘稳态温度（℃）：", width=18).grid(row=0, column=0, sticky=tk.W)
        self.cooler_steady_temp = ttk.Entry(row8_frame, width=8)
        self.cooler_steady_temp.grid(row=0, column=1)
        
        # 第九行：导热系数和计算按钮
        row9_frame = ttk.Frame(conductivity_frame)
        row9_frame.grid(row=8, column=0, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(row9_frame, text="导热系数：", width=10).grid(row=0, column=0, sticky=tk.W)
        self.conductivity_var = tk.StringVar(value="")
        ttk.Label(row9_frame, textvariable=self.conductivity_var, width=10).grid(row=0, column=1)
        ttk.Label(row9_frame, text="W/(m*K)").grid(row=0, column=2)
        ttk.Button(row9_frame, text="计算", command=self.calculate_conductivity, width=8).grid(row=0, column=3, padx=(10,0))
        
        # 导出实验数据按钮
        export_button = ttk.Button(self.calculation_frame, text="导出实验数据", 
                                command=self.export_experiment_data, width=20)
        export_button.grid(row=2, column=0, pady=10)

        # 导入实验数据按钮 - 新增
        import_button = ttk.Button(self.calculation_frame, text="导入实验数据", 
                                command=self.import_experiment_data, width=20)
        import_button.grid(row=3, column=0, pady=(0, 10))

    def import_experiment_data(self):
        """导入实验数据从Excel文件（增强版，支持计算结果）"""
        try:
            from tkinter import filedialog
            import tkinter.messagebox as messagebox
            
            # 弹出打开文件对话框
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="选择要导入的实验数据文件"
            )
            
            if not file_path:
                return
            
            # 读取Excel文件
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            # 检查必要的sheet是否存在
            required_sheets = ['有样品加热', '无样品加热', '散热曲线']
            available_sheets = [sheet for sheet in required_sheets if sheet in sheet_names]
            
            if not available_sheets:
                messagebox.showerror("导入错误", "Excel文件中没有找到实验数据工作表")
                return
            
            # 获取保存目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            save_dir = os.path.join(current_dir, "saved_data")
            
            # 确保保存目录存在
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            imported_count = 0
            import_details = []
            
            # 首先尝试导入计算结果（如果有）
            if '计算结果' in sheet_names:
                try:
                    calc_df = pd.read_excel(file_path, sheet_name='计算结果')
                    self.import_calculation_results(calc_df)
                    import_details.append("计算结果: 成功导入计算参数")
                except Exception as e:
                    import_details.append(f"计算结果: 导入失败 - {str(e)}")
            
            # 导入各个工作表的数据
            for sheet_name in available_sheets:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # 检查数据格式
                    if '时间(s)' not in df.columns or '加热盘温度(℃)' not in df.columns or '散热盘温度(℃)' not in df.columns:
                        if '提示' not in df.columns:  # 跳过提示工作表
                            import_details.append(f"{sheet_name}: 数据格式不正确")
                        continue
                    
                    # 根据工作表名称确定保存文件名
                    if sheet_name == '有样品加热':
                        filename = "saved_with_sample_heating.xlsx"
                    elif sheet_name == '无样品加热':
                        filename = "saved_without_sample_heating.xlsx"
                    elif sheet_name == '散热曲线':
                        filename = "saved_cooling.xlsx"
                    else:
                        continue
                    
                    # 保存数据
                    save_path = os.path.join(save_dir, filename)
                    df.to_excel(save_path, index=False)
                    imported_count += 1
                    import_details.append(f"{sheet_name}: 成功导入 {len(df)} 条数据")
                    
                except Exception as e:
                    import_details.append(f"{sheet_name}: 导入失败 - {str(e)}")
            
            # 显示导入结果
            if imported_count > 0 or '计算结果' in sheet_names:
                result_message = f"导入完成！\n\n导入详情:\n" + "\n".join(import_details)
                messagebox.showinfo("导入成功", result_message)
                
                # 如果当前在数据查询界面，刷新显示
                if self.parameter_mode == "data_query":
                    self.show_query_temperature_curve()
            else:
                messagebox.showerror("导入失败", "未能成功导入任何数据\n\n" + "\n".join(import_details))
                
        except Exception as e:
            tk.messagebox.showerror("导入错误", f"导入实验数据时发生错误：{str(e)}")

    def import_calculation_results(self, calc_df):
        """导入计算结果数据"""
        try:
            # 将DataFrame转换为字典便于查找
            calc_dict = dict(zip(calc_df['参数'], calc_df['数值']))
            
            # 导入样品材料和厚度
            if '样品材料' in calc_dict and '样品厚度(mm)' in calc_dict:
                material = calc_dict['样品材料']
                thickness = calc_dict['样品厚度(mm)']
                
                if material == '橡胶':
                    self.sample_thickness_var.set(f"{thickness} (橡胶)")
                elif material == '空气':
                    self.sample_thickness_var.set(f"{thickness} (空气)")
                else:
                    self.sample_thickness_var.set(f"{thickness} ({material})")
            
            # 导入冷却速率相关参数
            if '冷却速率温度范围(℃)' in calc_dict:
                temp_range = calc_dict['冷却速率温度范围(℃)']
                if '-' in temp_range:
                    temps = temp_range.split('-')
                    if len(temps) == 2:
                        self.cooling_temp1.delete(0, tk.END)
                        self.cooling_temp1.insert(0, temps[0])
                        self.cooling_temp2.delete(0, tk.END)
                        self.cooling_temp2.insert(0, temps[1])
            
            if '冷却速率(℃/s)' in calc_dict:
                self.cooling_rate_var.set(calc_dict['冷却速率(℃/s)'])
            
            # 导入样品厚度
            if '样品厚度(mm)' in calc_dict:
                self.sample_thickness_var.set(calc_dict['样品厚度(mm)'])
            
            # 导入稳态温度
            if '加热盘稳态温度(℃)' in calc_dict:
                self.heater_steady_temp.delete(0, tk.END)
                self.heater_steady_temp.insert(0, calc_dict['加热盘稳态温度(℃)'])
            
            if '散热盘稳态温度(℃)' in calc_dict:
                self.cooler_steady_temp.delete(0, tk.END)
                self.cooler_steady_temp.insert(0, calc_dict['散热盘稳态温度(℃)'])
            
            # 导入导热系数
            if '导热系数(W/(m*K))' in calc_dict:
                self.conductivity_var.set(calc_dict['导热系数(W/(m*K))'])
                
        except Exception as e:
            print(f"导入计算结果时发生错误: {e}")

    def calculate_cooling_rate(self):
        """计算冷却速率 - 简化版本"""
        try:
            # 获取用户输入的温度
            temp1 = float(self.cooling_temp1.get())
            temp2 = float(self.cooling_temp2.get())
            
            if temp1 <= temp2:
                tk.messagebox.showerror("输入错误", "第一个温度应大于第二个温度")
                return
            
            # 读取散热曲线数据
            current_dir = os.path.dirname(os.path.abspath(__file__))
            save_dir = os.path.join(current_dir, "saved_data")
            filepath = os.path.join(save_dir, "saved_cooling.xlsx")
            
            if not os.path.exists(filepath):
                tk.messagebox.showerror("数据不足", "未找到散热曲线数据")
                return
            
            # 读取数据
            df = pd.read_excel(filepath)
            time_data = df['时间(s)'].values
            cooler_temp_data = df['散热盘温度(℃)'].values
            
            # 查找时间点
            def find_time_for_temperature(target_temp, time_array, temp_array, tolerance=0.5):
                valid_indices = np.where(np.abs(temp_array - target_temp) <= tolerance)[0]
                if len(valid_indices) == 0:
                    return None
                closest_idx = valid_indices[np.argmin(np.abs(temp_array[valid_indices] - target_temp))]
                return time_array[closest_idx]
            
            time1 = find_time_for_temperature(temp1, time_data, cooler_temp_data)
            time2 = find_time_for_temperature(temp2, time_data, cooler_temp_data)
            
            if time1 is None or time2 is None:
                tk.messagebox.showerror("数据不足", "在散热曲线上找不到指定的温度范围")
                return
            
            # 确保时间顺序正确
            if time1 > time2:
                time1, time2 = time2, time1
            
            # 选择时间范围内的所有点
            time_mask = (time_data >= time1) & (time_data <= time2)
            selected_times = time_data[time_mask]
            selected_temps = cooler_temp_data[time_mask]
            
            if len(selected_times) < 2:
                tk.messagebox.showerror("数据不足", "在选定时间范围内数据点不足")
                return
            
            # 线性拟合
            slope, intercept = np.polyfit(selected_times, selected_temps, 1)
            cooling_rate = -slope  # 冷却速率是斜率的相反数
            
            # 计算拟合质量
            fitted_temps = slope * selected_times + intercept
            r_squared = 1 - np.var(selected_temps - fitted_temps) / np.var(selected_temps)
            
            self.cooling_rate_var.set(f"{cooling_rate:.4f}")
            
            # 简单结果显示
            tk.messagebox.showinfo("计算完成", 
                f"冷却速率计算完成！\n\n"
                f"使用数据点: {len(selected_times)} 个\n"
                f"时间范围: {time1:.1f}s ~ {time2:.1f}s\n"
                f"冷却速率: {cooling_rate:.4f} ℃/s")
            
        except ValueError:
            tk.messagebox.showerror("输入错误", "请输入有效的温度数值")
        except Exception as e:
            tk.messagebox.showerror("计算错误", f"计算冷却速率时发生错误：{str(e)}")

    def calculate_conductivity(self):
        """计算导热系数"""
        try:
            # 获取用户输入
            heater_temp = float(self.heater_steady_temp.get())
            cooler_temp = float(self.cooler_steady_temp.get())
            
            # 解析样品厚度和材料类型
            thickness_text = self.sample_thickness_var.get()
            if "(橡胶)" in thickness_text:
                sample_thickness = 7.96 / 1000  # 转换为米
                material_type = "橡胶"
            elif "(空气)" in thickness_text:
                sample_thickness = 1.00 / 1000  # 转换为米
                material_type = "空气"
            else:
                # 默认处理
                sample_thickness = float(thickness_text.split()[0]) / 1000
                material_type = "未知材料"
            
            # 获取冷却速率（如果已经计算过）
            cooling_rate_str = self.cooling_rate_var.get()
            if not cooling_rate_str:
                tk.messagebox.showerror("计算错误", "请先计算冷却速率")
                return
                    
            cooling_rate = float(cooling_rate_str)  # ℃/s
            
            # 验证输入
            if heater_temp <= cooler_temp:
                tk.messagebox.showerror("输入错误", "加热盘温度应大于散热盘温度")
                return
            
            # 固定参数（转换为国际单位制）
            cooler_thickness = 10.11 / 1000  # 转换为米
            cooler_radius = 65.10 / 1000     # 转换为米
            sample_diameter = 128.76 / 1000  # 转换为米
            cooler_mass = 363.22 / 1000      # 转换为千克
            cooler_specific_heat = 880       # J/(Kg*K)
            
            # 计算导热系数
            numerator = (cooler_mass * cooler_specific_heat * 
                        (cooler_radius + 2 * cooler_thickness) * 
                        4 * sample_thickness * cooling_rate)
            
            denominator = (2 * cooler_radius + 2 * cooler_thickness) * \
                        (heater_temp - cooler_temp) * \
                        3.1416 * (sample_diameter ** 2)
            
            conductivity = numerator / denominator
            
            # 显示计算详情，包含材料类型
            self.show_conductivity_details(cooler_mass, cooler_specific_heat, cooler_radius,
                                        cooler_thickness, sample_thickness, cooling_rate,
                                        heater_temp, cooler_temp, sample_diameter, conductivity, material_type)
            
            self.conductivity_var.set(f"{conductivity:.4f}")
            
        except ValueError:
            tk.messagebox.showerror("输入错误", "请输入有效的数值")
        except ZeroDivisionError:
            tk.messagebox.showerror("计算错误", "温度差不能为零")
        except Exception as e:
            tk.messagebox.showerror("计算错误", f"计算导热系数时发生错误：{str(e)}")

    def show_conductivity_details(self, mass, specific_heat, radius, thickness, 
                                sample_thickness, cooling_rate, heater_temp, 
                                cooler_temp, diameter, conductivity, material_type):
        """显示导热系数计算详情"""
        detail_text = (
            f"导热系数计算详情：\n\n"
            f"输入参数：\n"
            f"• 样品材料: {material_type}\n"
            f"• 样品厚度: {sample_thickness*1000:.2f} mm\n"
            f"• 散热盘质量: {mass*1000:.2f} g\n"
            f"• 散热盘比热容: {specific_heat} J/(kg·K)\n"
            f"• 散热盘半径: {radius*1000:.1f} mm\n"
            f"• 散热盘厚度: {thickness*1000:.2f} mm\n"
            f"• 冷却速率: {cooling_rate:.4f} ℃/s\n"
            f"• 加热盘稳态温度: {heater_temp:.1f} ℃\n"
            f"• 散热盘稳态温度: {cooler_temp:.1f} ℃\n"
            f"• 样品直径: {diameter*1000:.2f} mm\n\n"
            f"计算过程：\n"
            f"分子 = 散热盘质量 × 比热容 × (散热盘半径 + 2×散热盘厚度) × 4 × 样品厚度 × 冷却速率\n"
            f"     = {mass:.4f} × {specific_heat} × ({radius:.4f} + 2×{thickness:.4f}) × 4 × {sample_thickness:.4f} × {cooling_rate:.4f}\n\n"
            f"分母 = (2×散热盘半径 + 2×散热盘厚度) × 温度差 × π × 样品直径²\n"
            f"     = (2×{radius:.4f} + 2×{thickness:.4f}) × {heater_temp-cooler_temp:.1f} × 3.1416 × {diameter**2:.6f}\n\n"
            f"导热系数 = 分子 / 分母\n"
            f"         = {conductivity:.4f} W/(m·K)"
        )
        tk.messagebox.showinfo(f"{material_type}导热系数计算详情", detail_text)

    def export_experiment_data(self):
        """导出实验数据到Excel文件"""
        try:
            from tkinter import filedialog
            
            # 弹出保存文件对话框
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="保存实验数据"
            )
            
            if not file_path:
                return
            
            # 解析当前选择的样品材料
            thickness_text = self.sample_thickness_var.get()
            if "(橡胶)" in thickness_text:
                material_type = "橡胶"
            elif "(空气)" in thickness_text:
                material_type = "空气"
            else:
                material_type = "未知"
            
            # 创建Excel写入器
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 第一页：计算结果
                calculation_data = {
                    '参数': [
                        '样品材料', '样品厚度(mm)',
                        '冷却速率温度范围(℃)', '冷却速率(℃/s)',
                        '散热盘厚度(mm)', '散热盘半径(mm)',
                        '样品直径(mm)', '散热盘质量(g)',
                        '散热盘比热容(J/(Kg*K))', '加热盘稳态温度(℃)',
                        '散热盘稳态温度(℃)', '导热系数(W/(m*K))'
                    ],
                    '数值': [
                        material_type, thickness_text.split()[0],  # 提取数值部分
                        f"{self.cooling_temp1.get()}-{self.cooling_temp2.get()}",
                        self.cooling_rate_var.get(),
                        '10.11', '65.10', '128.76', '363.22', '880',
                        self.heater_steady_temp.get(), self.cooler_steady_temp.get(),
                        self.conductivity_var.get()
                    ]
                }
                pd.DataFrame(calculation_data).to_excel(writer, sheet_name='计算结果', index=False)
                
                # 读取并保存其他数据页
                current_dir = os.path.dirname(os.path.abspath(__file__))
                save_dir = os.path.join(current_dir, "saved_data")
                
                # 有样品加热数据
                with_sample_path = os.path.join(save_dir, "saved_with_sample_heating.xlsx")
                if os.path.exists(with_sample_path):
                    df_with_sample = pd.read_excel(with_sample_path)
                    # 温度数据保留一位小数
                    if '加热盘温度(℃)' in df_with_sample.columns:
                        df_with_sample['加热盘温度(℃)'] = df_with_sample['加热盘温度(℃)'].round(1)
                    if '散热盘温度(℃)' in df_with_sample.columns:
                        df_with_sample['散热盘温度(℃)'] = df_with_sample['散热盘温度(℃)'].round(1)
                    df_with_sample.to_excel(writer, sheet_name='有样品加热', index=False)
                else:
                    pd.DataFrame({'提示': ['暂无数据']}).to_excel(writer, sheet_name='有样品加热', index=False)
                
                # 无样品加热数据
                without_sample_path = os.path.join(save_dir, "saved_without_sample_heating.xlsx")
                if os.path.exists(without_sample_path):
                    df_without_sample = pd.read_excel(without_sample_path)
                    # 温度数据保留一位小数
                    if '加热盘温度(℃)' in df_without_sample.columns:
                        df_without_sample['加热盘温度(℃)'] = df_without_sample['加热盘温度(℃)'].round(1)
                    if '散热盘温度(℃)' in df_without_sample.columns:
                        df_without_sample['散热盘温度(℃)'] = df_without_sample['散热盘温度(℃)'].round(1)
                    df_without_sample.to_excel(writer, sheet_name='无样品加热', index=False)
                else:
                    pd.DataFrame({'提示': ['暂无数据']}).to_excel(writer, sheet_name='无样品加热', index=False)
                
                # 散热数据
                cooling_path = os.path.join(save_dir, "saved_cooling.xlsx")
                if os.path.exists(cooling_path):
                    df_cooling = pd.read_excel(cooling_path)
                    # 温度数据保留一位小数
                    if '加热盘温度(℃)' in df_cooling.columns:
                        df_cooling['加热盘温度(℃)'] = df_cooling['加热盘温度(℃)'].round(1)
                    if '散热盘温度(℃)' in df_cooling.columns:
                        df_cooling['散热盘温度(℃)'] = df_cooling['散热盘温度(℃)'].round(1)
                    df_cooling.to_excel(writer, sheet_name='散热曲线', index=False)
                else:
                    pd.DataFrame({'提示': ['暂无数据']}).to_excel(writer, sheet_name='散热曲线', index=False)
            
            tk.messagebox.showinfo("导出成功", f"实验数据已导出到：{file_path}")
            
        except Exception as e:
            tk.messagebox.showerror("导出错误", f"导出实验数据时发生错误：{str(e)}")

    def start_long_press_up(self):
        """开始长按向上按钮"""
        # 先立即执行一次
        self.move_up()
        # 设置长按定时器
        self.after_id_up = self.root.after(self.long_press_delay, self.long_press_up)

    def start_long_press_down(self):
        """开始长按向下按钮"""
        # 先立即执行一次
        self.move_down()
        # 设置长按定时器
        self.after_id_down = self.root.after(self.long_press_delay, self.long_press_down)

    def long_press_up(self):
        """长按向上连续触发"""
        if self.parameter_mode in ["setting_temp", "setting_interval"]:
            self.move_up()
            self.after_id_up = self.root.after(self.long_press_interval, self.long_press_up)

    def long_press_down(self):
        """长按向下连续触发"""
        if self.parameter_mode in ["setting_temp", "setting_interval"]:
            self.move_down()
            self.after_id_down = self.root.after(self.long_press_interval, self.long_press_down)

    def stop_long_press(self):
        """停止长按"""
        if self.after_id_up:
            try:
                self.root.after_cancel(self.after_id_up)
                self.after_id_up = None
            except:
                pass
        if self.after_id_down:
            try:
                self.root.after_cancel(self.after_id_down)
                self.after_id_down = None
            except:
                pass

    def move_up(self):
        """向上移动选择"""
        if not self.power_on:
            return
        if self.storage_selection_mode:
            # 存储选择模式
            if self.current_storage_selection > 0:
                self.current_storage_selection -= 1
            else:
                self.current_storage_selection = len(self.storage_options) - 1
            self.highlight_storage_selection()
        elif self.parameter_mode == "normal":
            # 主菜单模式 - 循环索引
            if self.current_selection > 0:
                self.current_selection -= 1
            else:
                self.current_selection = len(self.menu_items) - 1  # 到达顶部时回到底部
            self.highlight_selected_menu()
        elif self.parameter_mode == "parameter_menu":
            # 参数菜单模式，在参数项之间切换
            if self.current_param_selection > 0:
                self.current_param_selection -= 1
            else:
                self.current_param_selection = 1  # 到达顶部时回到底部（只有2个参数项，索引0和1）
            self.highlight_selected_parameter()
        elif self.parameter_mode == "setting_temp":
            # 温度设置模式
            if self.target_temperature < 80:
                self.target_temperature += 1
                self.update_parameter_display()
                # 更新指示灯状态
                self.update_indicator()
        elif self.parameter_mode == "setting_interval":
            # 间隔时间设置模式
            if self.interval_time < 60:
                self.interval_time += 5
                self.update_parameter_display()
        elif self.parameter_mode == "data_query":
            # 数据查询模式
            if self.current_query_selection > 0:
                self.current_query_selection -= 1
            else:
                self.current_query_selection = len(self.query_options) - 1
            self.highlight_selected_query()
            self.show_query_temperature_curve()


    def move_down(self):
        """向下移动选择"""
        if not self.power_on:
            return
        if self.storage_selection_mode:
            # 存储选择模式
            if self.current_storage_selection < len(self.storage_options) - 1:
                self.current_storage_selection += 1
            else:
                self.current_storage_selection = 0
            self.highlight_storage_selection()
        elif self.parameter_mode == "normal":
            # 主菜单模式 - 循环索引
            if self.current_selection < len(self.menu_items) - 1:
                self.current_selection += 1
            else:
                self.current_selection = 0  # 到达底部时回到顶部
            self.highlight_selected_menu()
        elif self.parameter_mode == "parameter_menu":
            # 参数菜单模式，在参数项之间循环切换
            if self.current_param_selection < 1:  # 只有两个参数项，索引0和1
                self.current_param_selection += 1
            else:
                self.current_param_selection = 0  # 到达底部时回到顶部
            self.highlight_selected_parameter()
        elif self.parameter_mode == "setting_temp":
            # 温度设置模式
            if self.target_temperature > 0:
                self.target_temperature -= 1
                self.update_parameter_display()
                # 更新指示灯状态
                self.update_indicator()
        elif self.parameter_mode == "setting_interval":
            # 间隔时间设置模式
            if self.interval_time > 5:
                self.interval_time -= 5
                self.update_parameter_display()
        elif self.parameter_mode == "data_query":
            # 数据查询模式
            if self.current_query_selection < len(self.query_options) - 1:
                self.current_query_selection += 1
            else:
                self.current_query_selection = 0
            self.highlight_selected_query()
            self.show_query_temperature_curve()

    def confirm_selection(self):
        """确定按钮功能"""
        if not self.power_on:
            return
        if self.storage_selection_mode:
            # 存储选择模式
            self.save_data_and_exit()
        elif self.temperature_recording:
            # 温度记录模式
            self.toggle_heating()
        elif self.parameter_mode == "normal":
            # 主菜单模式
            selected_item = self.menu_items[self.current_selection]
            print(f"确定选择: {selected_item}")
            # 这里可以添加具体的功能实现
            if selected_item == "温度记录":
                self.recreate_unified_chart()
                self.show_temperature_records()
            elif selected_item == "参数设置":
                self.show_parameter_settings()
            elif selected_item == "数据查询":
                self.show_data_query()
        elif self.parameter_mode in ["setting_temp", "setting_interval"]:
            # 参数设置模式，退出设置状态，回到参数菜单
            self.parameter_mode = "parameter_menu"
            self.update_parameter_display()
        elif self.parameter_mode == "parameter_menu":
            # 参数设置菜单模式
            if self.current_param_selection == 0:
                # 进入温度设置
                self.parameter_mode = "setting_temp"
                self.update_parameter_display()
            elif self.current_param_selection == 1:
                # 进入间隔时间设置
                self.parameter_mode = "setting_interval"
                self.update_parameter_display()

    def stop_all_timers(self):
        """停止所有定时器"""
        print("停止所有定时器...")
        
        # 停止温度更新定时器
        if self.timer_id:
            try:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None
                print("温度更新定时器已停止")
            except:
                pass
        
        # 停止经过时间定时器
        if self.elapsed_timer_id:
            try:
                self.root.after_cancel(self.elapsed_timer_id)
                self.elapsed_timer_id = None
                print("经过时间定时器已停止")
            except:
                pass

        # 停止长按定时器
        self.stop_long_press()
        
        # 停止加热状态
        self.heating_status = "停止"
        
        # 停止所有 tkinter after 调用
        try:
            # 获取所有活跃的 after 调用并取消它们
            after_ids = self.root.tk.call('after', 'info')
            for after_id in after_ids:
                try:
                    self.root.after_cancel(after_id)
                except:
                    pass
            print(f"已取消 {len(after_ids)} 个活跃的 after 调用")
        except Exception as e:
            print(f"取消 after 调用时出错: {e}")

    def go_back(self):
        """返回按钮功能"""
        if not self.power_on:
            return
        # 清理鼠标事件
        if hasattr(self, 'query_canvas') and self.query_canvas:
            try:
                if hasattr(self, 'cid_press'):
                    self.query_canvas.mpl_disconnect(self.cid_press)
                if hasattr(self, 'cid_release'):
                    self.query_canvas.mpl_disconnect(self.cid_release)
                if hasattr(self, 'cid_motion'):
                    self.query_canvas.mpl_disconnect(self.cid_motion)
                if hasattr(self, 'cid_scroll'):
                    self.query_canvas.mpl_disconnect(self.cid_scroll)
            except:
                pass

        # 清理温度记录图表鼠标事件
        if hasattr(self, 'canvas') and self.canvas:
            try:
                if hasattr(self, 'temp_cid_press'):
                    self.canvas.mpl_disconnect(self.temp_cid_press)
                if hasattr(self, 'temp_cid_release'):
                    self.canvas.mpl_disconnect(self.temp_cid_release)
                if hasattr(self, 'temp_cid_motion'):
                    self.canvas.mpl_disconnect(self.temp_cid_motion)
                if hasattr(self, 'temp_cid_scroll'):
                    self.canvas.mpl_disconnect(self.temp_cid_scroll)
            except:
                pass

        self.stop_all_timers()
        if self.storage_selection_mode:
            # 存储选择模式，返回温度记录界面
            self.storage_selection_mode = False
            self.temperature_recording = False
            self.parameter_mode = "normal"  # 新增：重置参数模式
            self.reset_temperature_recording()  # 重置温度记录状态
            self.show_main_menu()  # 返回主菜单
        elif self.temperature_recording:
            self.temperature_recording = False  # 退出温度记录界面
            self.heating_status = "停止"  # 立即停止加热状态
            self.update_experiment_status()  # 更新实验状态
            self.update_temperature_display()  # 更新温度显示
            self.update_indicator()  # 更新指示灯状态
            print("温度记录界面返回：加热状态已停止")
            # 温度记录模式，进入存储选择界面
            self.enter_storage_selection()
        elif self.parameter_mode == "normal":
            # 主菜单模式
            print("返回上一级")
            # 这里可以添加返回逻辑
        elif self.parameter_mode in ["setting_temp", "setting_interval"]:
            # 参数设置模式，退出设置状态，回到参数菜单
            self.parameter_mode = "parameter_menu"
            self.update_parameter_display()
        elif self.parameter_mode == "parameter_menu":
            # 参数设置菜单模式，返回主菜单
            self.parameter_mode = "normal"
            self.show_main_menu()
        elif self.parameter_mode == "data_query":
            # 数据查询模式，返回主菜单
            self.parameter_mode = "normal"
            self.show_main_menu()

    def select_menu_item(self, index):
        """直接点击菜单项选择"""
        if self.parameter_mode == "normal":
            self.current_selection = index
            self.highlight_selected_menu()

    def highlight_selected_menu(self):
        """高亮显示当前选中的菜单项"""
        for i, label in enumerate(self.menu_labels):
            if i == self.current_selection:
                label.configure(background="lightblue", foreground="black")
            else:
                label.configure(background="white", foreground="black")

    def show_temperature_records(self):
        """显示温度记录功能"""
        if self.experiment_status == "请放置加热器或取下样品":
            tk.messagebox.showerror("错误", "请放置加热器或取下样品")
            return
        if self.fan_on:
            if self.experiment_status == "有样品加热（空气）,请进入温度记录界面按确定加热" or self.experiment_status == "无样品加热,请进入温度记录界面按确定加热":
                tk.messagebox.showerror("错误", "请关闭风扇")
                return

        self.temperature_recording = True
        self.parameter_mode = "temperature_recording"
        
        # 禁用左侧控制按钮
        self.rubber_button.config(state="disabled")
        self.air_button.config(state="disabled")
        self.heater_button.config(state="disabled")
        self.reset_temp_button.config(state="disabled")
        self.fan_button.config(state="disabled")
        
        # 清空显示框
        for widget in self.display_frame.winfo_children():
            widget.destroy()
        
        # 创建温度记录显示
        self.temp_display_frame = tk.Frame(self.display_frame, bg='white')
        self.temp_display_frame.pack(fill=tk.BOTH, expand=True)
        
        # 改为四行布局，每行一个参数
        # 第一行：加热盘温度
        heater_frame = tk.Frame(self.temp_display_frame, bg='white')
        heater_frame.pack(fill=tk.X, pady=2)
        
        self.heater_temp_label = tk.Label(heater_frame, text=f"加热盘：{self.heater_temp:.1f}℃", 
                                        bg='white', font=('Arial', 10, 'bold'))
        self.heater_temp_label.pack(side=tk.LEFT, padx=10)
        
        # 第二行：散热盘温度
        cooler_frame = tk.Frame(self.temp_display_frame, bg='white')
        cooler_frame.pack(fill=tk.X, pady=2)
        
        self.cooler_temp_label = tk.Label(cooler_frame, text=f"散热盘：{self.cooler_temp:.1f}℃", 
                                        bg='white', font=('Arial', 10, 'bold'))
        self.cooler_temp_label.pack(side=tk.LEFT, padx=10)
        
        # 第三行：记录次数
        record_frame = tk.Frame(self.temp_display_frame, bg='white')
        record_frame.pack(fill=tk.X, pady=2)
        
        self.record_count_label = tk.Label(record_frame, text=f"记录次数：{self.record_count}", 
                                        bg='white', font=('Arial', 10, 'bold'))
        self.record_count_label.pack(side=tk.LEFT, padx=10)
        
        # 第四行：加热状态
        status_frame = tk.Frame(self.temp_display_frame, bg='white')
        status_frame.pack(fill=tk.X, pady=2)
        
        self.heating_status_label = tk.Label(status_frame, text=f"加热状态：{self.heating_status}", 
                                            bg='white', font=('Arial', 10, 'bold'))
        self.heating_status_label.pack(side=tk.LEFT, padx=10)
        
        # 更新图表标题
        self.update_chart_title("温度记录 - 实时温度曲线")
        
        # 清空之前的数据
        self.time_data = []
        self.heater_temp_data = []
        self.cooler_temp_data = []
        self.record_count = 0
        
        # 开始温度记录
        self.start_temperature_recording()

    def create_temperature_chart(self):
        """创建温度图表 - 移动到实验仪区域下方"""
        # 清空图表容器
        for widget in self.chart_container.winfo_children():
            widget.destroy()
        
        # 创建matplotlib图形 - 调整大小以适应新位置
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=80)
        
        # 使用中文标签
        self.ax.set_xlabel('时间 (秒)')
        self.ax.set_ylabel('温度 (℃)')
        self.ax.set_title('温度曲线')
        self.ax.grid(True)
        
        # 初始化空的数据，使用中文图例
        self.heater_line, = self.ax.plot([], [], 'r-', label='加热盘')
        self.cooler_line, = self.ax.plot([], [], 'b-', label='散热盘')
        self.ax.legend()
        
        # 创建canvas - 放在新的图表容器中
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        

    def toggle_heating(self):
        """切换加热状态"""
        if self.experiment_status == "散热":
            tk.messagebox.showerror("错误", "未放置加热器不能加热")
            return
        if self.heating_status == "停止":
            self.heating_status = "加热"
            # 切换加热状态时重新获取基准时间  
        else:
            self.heating_status = "停止"
            # 切换停止状态时重新获取基准时间
        
        self.update_experiment_status()
        self.update_temperature_display()
        self.get_base_times_from_current_temperature()
        # 立即更新指示灯状态
        self.update_indicator()

    def start_temperature_recording(self):
        """开始温度记录"""
        # 重置记录数据
        self.time_data = []
        self.heater_temp_data = []
        self.cooler_temp_data = []
        self.record_count = 0
        
        # 更新实验状态
        self.update_experiment_status()

        # 分别获取加热盘和散热盘的基准时间
        self.get_base_times_from_current_temperature()
        
        # 启动经过时间定时器
        self.reset_elapsed_timer()

        # 开始定时器 - 关键修改：使用当前加速倍率
        acceleration_factor = self.current_acceleration_factor
        new_interval = max(100, self.interval_time * 1000 // acceleration_factor)
        self.timer_id = self.root.after(new_interval, self.update_temperature)


    def stop_temperature_recording(self):
        """停止温度记录"""
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def update_temperature(self):
        """更新温度数据"""
        if self.temperature_recording:  # 只要在温度记录界面就记录数据
            # 根据实验状态获取温度数据
            self.get_temperature_from_file()
            
            # 更新记录（保持原来的横坐标计算方式）
            current_time = (self.record_count) * self.interval_time
            self.time_data.append(current_time)
            self.heater_temp_data.append(self.heater_temp)
            self.cooler_temp_data.append(self.cooler_temp)
            self.record_count += 1
            
            # 更新图表
            self.update_chart()
            
            # 关键修改：使用当前加速倍率计算定时器间隔
            acceleration_factor = self.current_acceleration_factor
            new_interval = max(100, self.interval_time * 1000 // acceleration_factor)
            self.timer_id = self.root.after(new_interval, self.update_temperature)
        
        self.update_temperature_display()
        # 更新指示灯状态
        self.update_indicator()
        
    def get_base_times_from_current_temperature(self):
        """根据当前温度分别获取加热盘和散热盘的基准时间（正确的插值计算）"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "data")
        
        # 根据实验状态选择文件
        filename = ""
        if self.experiment_status == "散热":
            if not self.fan_on:
                filename = "散热曲线.xlsx"
            else:
                filename = "散热曲线（风扇打开）.xlsx"
        elif self.experiment_status == "有样品加热（橡胶）":
            if not self.fan_on:
                filename = "有样品加热（橡胶）.xlsx"
            else:
                filename = "有样品加热（橡胶）（风扇打开）.xlsx"
        elif self.experiment_status == "有样品加热（空气）":
            filename = "有样品加热（空气）.xlsx"
        elif self.experiment_status == "无样品加热":
            filename = "无样品加热.xlsx"
        else:
            filename = "散热曲线.xlsx"
            print(f"实验状态为'{self.experiment_status}'，默认使用散热曲线")
        
        filepath = os.path.join(data_dir, filename)
        
        try:
            # 读取Excel文件
            df = pd.read_excel(filepath)
            time_col = df.iloc[:, 0].values
            heater_col = df.iloc[:, 1].values
            cooler_col = df.iloc[:, 2].values
            
            if self.experiment_status in ["有样品加热（橡胶）,请进入温度记录界面按确定加热", "有样品加热（空气）,请进入温度记录界面按确定加热", "无样品加热,请进入温度记录界面按确定加热"]:
                for i in range(len(time_col)):
                    time_col[i]*=1.2

            if self.experiment_status=="散热":
                for i in range(len(time_col)):
                    time_col[i]*=0.67

            # 根据实验状态调整温度数据用于基准时间计算
            if self.experiment_status in ["有样品加热（橡胶）", "有样品加热（空气）", "无样品加热"]:
                # 应用相同的温度调整公式到整个温度数组
                original_min_temp = 21.4
                original_max_temp = 80.0
                
                # 调整加热盘温度数据
                heater_adjust_ratios = (heater_col - original_min_temp) / (original_max_temp - original_min_temp)
                heater_col_adjusted = heater_adjust_ratios * (self.target_temperature - original_min_temp) + original_min_temp
                
                # 调整散热盘温度数据
                cooler_adjust_ratios = (cooler_col - original_min_temp) / (original_max_temp - original_min_temp)
                cooler_col_adjusted = cooler_adjust_ratios * (self.target_temperature - original_min_temp) + original_min_temp
                
                print(f"基准时间计算 - 使用调整后的温度数据 (目标温度: {self.target_temperature}℃)")
                print(f"原始温度范围: {heater_col[0]:.1f}℃-{heater_col[-1]:.1f}℃")
                print(f"调整后温度范围: {heater_col_adjusted[0]:.1f}℃-{heater_col_adjusted[-1]:.1f}℃")
            else:
                # 散热状态使用原始温度数据
                heater_col_adjusted = heater_col
                cooler_col_adjusted = cooler_col
                print(f"基准时间计算 - 使用原始温度数据")
            
            def find_base_time(current_temp, time_array, temp_array):
                """根据当前温度找到对应的基准时间"""
                # 如果温度数据是单调递增的（加热过程）
                if temp_array[-1] > temp_array[0]:
                    # 加热过程：温度随时间增加
                    if current_temp <= temp_array[0]:
                        return time_array[0]
                    elif current_temp >= temp_array[-1]:
                        return time_array[-1]
                    else:
                        # 找到当前温度所在的位置
                        for i in range(len(temp_array) - 1):
                            if temp_array[i] <= current_temp <= temp_array[i + 1]:
                                # 线性插值计算时间
                                ratio = (current_temp - temp_array[i]) / (temp_array[i + 1] - temp_array[i])
                                base_time = time_array[i] + ratio * (time_array[i + 1] - time_array[i])
                                return base_time
                
                # 如果温度数据是单调递减的（散热过程）
                elif temp_array[-1] < temp_array[0]:
                    # 散热过程：温度随时间降低
                    if current_temp >= temp_array[0]:
                        return time_array[0]
                    elif current_temp <= temp_array[-1]:
                        return time_array[-1]
                    else:
                        # 找到当前温度所在的位置
                        for i in range(len(temp_array) - 1):
                            if temp_array[i] >= current_temp >= temp_array[i + 1]:
                                # 线性插值计算时间
                                ratio = (current_temp - temp_array[i]) / (temp_array[i + 1] - temp_array[i])
                                base_time = time_array[i] + ratio * (time_array[i + 1] - time_array[i])
                                return base_time
                
                # 如果数据不是单调的，使用最近邻方法
                temp_diffs = np.abs(temp_array - current_temp)
                closest_idx = np.argmin(temp_diffs)
                return time_array[closest_idx]
            
            # 分别计算加热盘和散热盘的基准时间，使用调整后的温度数据
            self.heater_base_time = find_base_time(self.heater_temp, time_col, heater_col_adjusted)
            self.cooler_base_time = find_base_time(self.cooler_temp, time_col, cooler_col_adjusted)
            
            print(f"实验状态: {self.experiment_status}")
            print(f"数据文件: {filename}")
            print(f"加热盘 - 当前温度: {self.heater_temp:.1f}℃, 基准时间: {self.heater_base_time:.1f}秒")
            print(f"散热盘 - 当前温度: {self.cooler_temp:.1f}℃, 基准时间: {self.cooler_base_time:.1f}秒")
            
            # 重置经过时间定时器
            self.reset_elapsed_timer()
            
        except Exception as e:
            print(f"获取基准时间错误: {e}")
            # 设置默认基准时间
            self.heater_base_time = 0
            self.cooler_base_time = 0
            self.reset_elapsed_timer()
    
    def reset_elapsed_timer(self):
        """重置经过时间定时器"""
        # 停止现有的定时器
        if self.elapsed_timer_id:
            self.root.after_cancel(self.elapsed_timer_id)
            self.elapsed_timer_id = None
        
        # 重置经过时间
        self.elapsed_time = 0
        self.last_update_time = self.root.tk.call('clock', 'milliseconds')
        
        # 如果正在温度记录界面，启动新的定时器
        if self.temperature_recording:
            self.start_elapsed_timer()

    def start_elapsed_timer(self):
        """启动经过时间定时器"""
        if self.elapsed_timer_id:
            self.root.after_cancel(self.elapsed_timer_id)
        
        current_time = self.root.tk.call('clock', 'milliseconds')
        time_diff = current_time - self.last_update_time
        
        # 更新经过时间（毫秒转换为秒）
        self.elapsed_time += time_diff / 1000.0
        self.last_update_time = current_time
        
        # 关键修改：使用当前加速倍率计算定时器间隔
        acceleration_factor = self.current_acceleration_factor
        new_interval = max(10, 100 // acceleration_factor)
        self.elapsed_timer_id = self.root.after(new_interval, self.start_elapsed_timer)

    def stop_elapsed_timer(self):
        """停止经过时间定时器"""
        if self.elapsed_timer_id:
            self.root.after_cancel(self.elapsed_timer_id)
            self.elapsed_timer_id = None

    def get_temperature_from_file(self):
        """从文件获取温度数据"""
        # 使用资源路径获取函数
        data_dir = get_resource_path("data")
        
        # 根据实验状态选择文件
        filename = ""
        if self.experiment_status == "散热" or self.experiment_status == "有样品加热（橡胶）,请进入温度记录界面按确定加热" or self.experiment_status == "有样品加热（空气）,请进入温度记录界面按确定加热" or self.experiment_status == "无样品加热,请进入温度记录界面按确定加热":

            if not self.fan_on:
                filename = "散热曲线.xlsx"
            else:
                filename = "散热曲线（风扇打开）.xlsx"
                if self.experiment_status != "散热":
                    filename = "散热曲线.xlsx"
        elif self.experiment_status == "有样品加热（橡胶）":
            if not self.fan_on:
                filename = "有样品加热（橡胶）.xlsx"
            else:
                filename = "有样品加热（橡胶）（风扇打开）.xlsx"
        elif self.experiment_status == "有样品加热（空气）":
            filename = "有样品加热（空气）.xlsx"
        elif self.experiment_status == "无样品加热":
            filename = "无样品加热.xlsx"
        else:
            # 错误操作，温度保持不变
            return
        
        filepath = os.path.join(data_dir, filename)
        
        try:
            # 读取Excel文件
            df = pd.read_excel(filepath)
            time_col = df.iloc[:, 0].values
            heater_col = df.iloc[:, 1].values
            cooler_col = df.iloc[:, 2].values
            
            if self.experiment_status in ["有样品加热（橡胶）,请进入温度记录界面按确定加热", "有样品加热（空气）,请进入温度记录界面按确定加热", "无样品加热,请进入温度记录界面按确定加热"]:
                for i in range(len(time_col)):
                    time_col[i]*=1.2

            if self.experiment_status=="散热":
                for i in range(len(time_col)):
                    time_col[i]*=0.67

            # 使用经过时间计算查询时间（分别使用各自的基准时间）
            # 关键修改：使用当前加速倍率（根据风扇状态）
            acceleration_factor = self.current_acceleration_factor
            heater_query_time = self.heater_base_time + (self.elapsed_time * acceleration_factor)
            cooler_query_time = self.cooler_base_time + (self.elapsed_time * acceleration_factor)
            
            print(f"经过时间: {self.elapsed_time:.1f}s (加速{acceleration_factor}倍后: {self.elapsed_time * acceleration_factor:.1f}s)")
            print(f"风扇状态: {'开启' if self.fan_on else '关闭'}")
            print(f"加热盘查询时间: {heater_query_time:.1f}s (基准: {self.heater_base_time:.1f}s)")
            print(f"散热盘查询时间: {cooler_query_time:.1f}s (基准: {self.cooler_base_time:.1f}s)")

            # 加热盘温度插值（使用加热盘查询时间）
            if heater_query_time <= time_col[-1] and heater_query_time >= time_col[0]:
                heater_temp_raw = np.interp(heater_query_time, time_col, heater_col)
            elif heater_query_time < time_col[0]:
                heater_temp_raw = heater_col[0]  # 使用第一个值
            else:
                heater_temp_raw = heater_col[-1]  # 使用最后一个值
            
            # 散热盘温度插值（使用散热盘查询时间）
            if cooler_query_time <= time_col[-1] and cooler_query_time >= time_col[0]:
                cooler_temp_raw = np.interp(cooler_query_time, time_col, cooler_col)
            elif cooler_query_time < time_col[0]:
                cooler_temp_raw = cooler_col[0]  # 使用第一个值
            else:
                cooler_temp_raw = cooler_col[-1]  # 使用最后一个值
            
            # 根据实验状态和目标温度调整温度值
            if self.experiment_status in ["有样品加热（橡胶）", "有样品加热（空气）", "无样品加热"]:
                # 应用温度调整公式：修正后的温度 = (表格原始温度 - 21.4) / (80 - 21.4) * (目标温度 - 21.4) + 21.4
                original_min_temp = 21.4
                original_max_temp = 80.0

                # 计算调整后的温度
                heater_adjust_ratio = (heater_temp_raw - original_min_temp) / (original_max_temp - original_min_temp)
                cooler_adjust_ratio = (cooler_temp_raw - original_min_temp) / (original_max_temp - original_min_temp)
                
                self.heater_temp = heater_adjust_ratio * (self.target_temperature - original_min_temp) + original_min_temp
                self.cooler_temp = cooler_adjust_ratio * (self.target_temperature - original_min_temp) + original_min_temp
                
                print(f"原始温度 - 加热盘: {heater_temp_raw:.1f}℃, 散热盘: {cooler_temp_raw:.1f}℃")
                print(f"调整后温度 - 加热盘: {self.heater_temp:.1f}℃, 散热盘: {self.cooler_temp:.1f}℃")
                print(f"目标温度: {self.target_temperature}℃, 调整比例 - 加热盘: {heater_adjust_ratio:.3f}, 散热盘: {cooler_adjust_ratio:.3f}")
            else:
                # 散热状态，使用原始温度
                self.heater_temp = heater_temp_raw
                self.cooler_temp = cooler_temp_raw
                print(f"散热状态使用原始温度 - 加热盘: {self.heater_temp:.1f}℃, 散热盘: {self.cooler_temp:.1f}℃")
                
            print("---")
            
            
        except Exception as e:
            print(f"读取温度数据错误: {e}")
            # 如果读取失败，温度保持不变

    def update_chart(self):
        """更新温度记录的图表"""
        if len(self.time_data) > 0 and self.parameter_mode == "temperature_recording":
            # 使用统一的数据更新方法
            self.update_chart_data(self.time_data, self.heater_temp_data, self.cooler_temp_data)

    def update_temperature_display(self):
        """更新温度显示"""
        # 只有在温度记录界面且相关标签存在时才更新
        if (self.temperature_recording and 
            hasattr(self, 'heater_temp_label') and 
            self.heater_temp_label.winfo_exists()):
            
            self.heater_temp_label.config(text=f"加热盘：{self.heater_temp:.1f}℃")
            self.cooler_temp_label.config(text=f"散热盘：{self.cooler_temp:.1f}℃")
            self.record_count_label.config(text=f"记录次数：{self.record_count}")
            self.heating_status_label.config(text=f"加热状态：{self.heating_status}")

    def enter_storage_selection(self):
        """进入存储选择界面"""
        self.storage_selection_mode = True
        self.current_storage_selection = 0
        
        # 清空显示框
        for widget in self.display_frame.winfo_children():
            widget.destroy()
        
        # 创建存储选择界面
        storage_frame = tk.Frame(self.display_frame, bg='white')
        storage_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = tk.Label(storage_frame, text="选择存储位置", 
                              bg='white', font=('Arial', 10, 'bold'))
        title_label.pack(pady=2)
        
        # 存储选项
        self.storage_labels = []
        for i, option in enumerate(self.storage_options):
            label = tk.Label(storage_frame, text=option, bg='white', padx=10, pady=2,
                            font=('Arial', 10, 'bold'), anchor='w', width=15)
            label.pack(fill=tk.X, pady=2)
            label.bind("<Button-1>", lambda e, idx=i: self.select_storage_item(idx))
            self.storage_labels.append(label)
        
        self.highlight_storage_selection()

    def select_storage_item(self, index):
        """选择存储项"""
        self.current_storage_selection = index
        self.highlight_storage_selection()

    def highlight_storage_selection(self):
        """高亮存储选择"""
        for i, label in enumerate(self.storage_labels):
            if i == self.current_storage_selection:
                label.configure(background="lightblue", foreground="black")
            else:
                label.configure(background="white", foreground="black")

    def save_data_and_exit(self):
        """保存数据并退出"""
        selected_option = self.storage_options[self.current_storage_selection]
        print(f"保存数据到: {selected_option}")
        
        # 实际保存数据到文件
        self.save_experiment_data(selected_option)
        
        # 停止所有定时器
        self.stop_all_timers()
        # 重置温度记录状态
        self.reset_temperature_recording()
        
        # 返回主界面
        self.storage_selection_mode = False
        self.temperature_recording = False
        self.show_main_menu()
        self.parameter_mode = "normal"  # 新增：重置参数模式
        
        # 确保图表状态正确重置
        self.ensure_chart_consistency()

    def ensure_chart_consistency(self):
        """确保图表状态一致性"""
        try:
            if hasattr(self, 'chart_canvas') and self.chart_canvas:
                # 强制重绘图表
                self.chart_canvas.draw_idle()
                # 刷新图表显示
                self.chart_canvas.flush_events()
        except Exception as e:
            print(f"确保图表一致性时出错: {e}")

    def save_experiment_data(self, data_type):
        """保存实验数据到文件"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(current_dir, "saved_data")
        
        # 确保保存目录存在
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 根据数据类型确定文件名
        filename = ""
        if data_type == "有样品加热":
            filename = "saved_with_sample_heating.xlsx"
        elif data_type == "无样品加热":
            filename = "saved_without_sample_heating.xlsx"
        elif data_type == "散热":
            filename = "saved_cooling.xlsx"
        
        if filename:
            filepath = os.path.join(save_dir, filename)
            
            try:
                # 创建DataFrame保存数据，温度保留一位小数
                df = pd.DataFrame({
                    '时间(s)': self.time_data,
                    '加热盘温度(℃)': [round(temp, 1) for temp in self.heater_temp_data],
                    '散热盘温度(℃)': [round(temp, 1) for temp in self.cooler_temp_data]
                })
                
                # 保存到Excel文件
                df.to_excel(filepath, index=False)
                print(f"数据已保存到: {filepath}")
                
            except Exception as e:
                print(f"保存数据错误: {e}")

    def reset_temperature_recording(self):
        """重置温度记录"""
        # self.heater_temp = 25.0
        # self.cooler_temp = 25.0
        self.record_count = 0
        self.heating_status = "停止"
        self.time_data = []
        self.heater_temp_data = []
        self.cooler_temp_data = []
        
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        
        # 启用左侧控制按钮
        # self.rubber_button.config(state="normal")
        # self.air_button.config(state="normal")
        # self.heater_button.config(state="normal")

        # 停止经过时间定时器
        self.stop_elapsed_timer()
        self.elapsed_time = 0

        # # 重置风扇状态到关闭
        # if self.fan_on:
        #     self.fan_on = False
        #     self.current_acceleration_factor = self.base_acceleration_factor
        #     self.fan_button.config(text="→", bg='#333333')
        #     print("温度记录重置，风扇状态已恢复为关闭")


    def show_parameter_settings(self):
        """显示参数设置功能"""
        self.parameter_mode = "parameter_menu"
        self.current_param_selection = 0
        self.update_parameter_display()

    def show_data_query(self):
        """显示数据查询功能"""
        self.parameter_mode = "data_query"
        
        # 清空显示框
        for widget in self.display_frame.winfo_children():
            widget.destroy()
        
        # 创建数据查询界面
        self.data_query_frame = tk.Frame(self.display_frame, bg='white')
        self.data_query_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = tk.Label(self.data_query_frame, text="数据查询", 
                            bg='white', font=('Arial', 10, 'bold'))
        title_label.pack(pady=2)
        
        # 数据查询选项
        self.query_options = ["有样品加热", "无样品加热", "散热"]
        self.current_query_selection = 0
        
        self.query_labels = []
        for i, option in enumerate(self.query_options):
            label = tk.Label(self.data_query_frame, text=option, bg='white', padx=10, pady=2, 
                            font=('Arial', 10, 'bold'), anchor='w', width=15)
            label.pack(fill=tk.X, pady=2)
            label.bind("<Button-1>", lambda e, idx=i: self.select_query_item(idx))
            self.query_labels.append(label)
        
        # 高亮当前选中的查询项
        self.highlight_selected_query()
        
        self.recreate_unified_chart()
        # 显示对应的温度曲线
        self.show_query_temperature_curve()

    def select_query_item(self, index):
        """选择数据查询项"""
        self.current_query_selection = index
        self.highlight_selected_query()
        
        self.show_query_temperature_curve()

    def highlight_selected_query(self):
        """高亮显示当前选中的数据查询项"""
        for i, label in enumerate(self.query_labels):
            if i == self.current_query_selection:
                label.configure(background="lightblue", foreground="black")
            else:
                label.configure(background="white", foreground="black")

    def show_query_temperature_curve(self):
        """显示查询的温度曲线"""
        selected_option = self.query_options[self.current_query_selection]
        
        # 更新图表标题
        interval = self.load_and_display_query_data(selected_option)
        if interval != "未知":
            self.update_chart_title(f"数据查询 - {selected_option} (采集间隔: {interval})")
        else:
            self.update_chart_title(f"数据查询 - {selected_option}")

    def update_chart_title(self, title):
        """更新图表标题"""
        if hasattr(self, 'chart_ax') and self.chart_ax:
            self.chart_ax.set_title(title)
            if hasattr(self, 'chart_canvas') and self.chart_canvas:
                self.chart_canvas.draw_idle()


    def load_and_display_query_data(self, data_type):
        """加载并显示查询的保存数据到统一图表"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(current_dir, "saved_data")
        
        # 根据数据类型确定文件名
        filename = ""
        if data_type == "有样品加热":
            filename = "saved_with_sample_heating.xlsx"
        elif data_type == "无样品加热":
            filename = "saved_without_sample_heating.xlsx"
        elif data_type == "散热":
            filename = "saved_cooling.xlsx"
        
        filepath = os.path.join(save_dir, filename)
        
        # 检查文件是否存在
        if os.path.exists(filepath):
            try:
                # 读取保存的Excel文件
                df = pd.read_excel(filepath)
                time_data = df['时间(s)'].values
                heater_temp_data = df['加热盘温度(℃)'].values
                cooler_temp_data = df['散热盘温度(℃)'].values
                
                # 保存查询数据供鼠标交互使用
                self.query_time_data = time_data
                self.query_heater_data = heater_temp_data
                self.query_cooler_data = cooler_temp_data
                
                # 计算采集间隔
                interval = self.calculate_sampling_interval(time_data)
                
                # 更新统一图表的数据
                self.update_chart_data(time_data, heater_temp_data, cooler_temp_data)
                
                return interval
                
            except Exception as e:
                print(f"读取保存数据错误: {e}")
                # 清空查询数据，使用空数组
                self.query_time_data = np.array([])
                self.query_heater_data = np.array([])
                self.query_cooler_data = np.array([])
                # 清空图表数据
                self.update_chart_data([], [], [])
                return "未知"
        else:
            # 文件不存在，清空数据，使用空数组
            self.query_time_data = np.array([])
            self.query_heater_data = np.array([])
            self.query_cooler_data = np.array([])
            self.update_chart_data([], [], [])
            return "未知"

    def update_chart_data(self, time_data, heater_data, cooler_data):
        """更新图表数据"""
        if not hasattr(self, 'chart_ax') or not hasattr(self, 'heater_line'):
            return
        
        # 确保数据是 numpy 数组
        time_data = np.array(time_data) if time_data is not None else np.array([])
        heater_data = np.array(heater_data) if heater_data is not None else np.array([])
        cooler_data = np.array(cooler_data) if cooler_data is not None else np.array([])
        
        # 更新数据线
        self.heater_line.set_data(time_data, heater_data)
        self.cooler_line.set_data(time_data, cooler_data)
        
        # 调整坐标轴范围
        if len(time_data) > 1:
            self.chart_ax.set_xlim(0, max(time_data))
            all_temps = np.concatenate([heater_data, cooler_data])
            self.chart_ax.set_ylim(min(all_temps) - 5, max(all_temps) + 5)
        else:
            # 没有数据时设置默认范围
            self.chart_ax.set_xlim(0, 100)
            self.chart_ax.set_ylim(0, 100)
        
        # 强制刷新图表 - 新增部分
        try:
            self.chart_canvas.draw_idle()
            self.chart_canvas.flush_events()  # 强制处理事件队列
        except Exception as e:
            print(f"图表刷新错误: {e}")
            # 如果刷新失败，尝试重新创建图表
            # self.recreate_chart_if_needed()

    def calculate_sampling_interval(self, time_data):
        """计算数据采集间隔 - 直接用前两行时间相减"""
        if len(time_data) >= 2:
            interval = time_data[1] - time_data[0]
            return f"{int(interval)}秒"
        else:
            return "未知"

    def create_empty_chart(self, data_type, message):
        """创建空图表"""
        # 清空图表容器
        for widget in self.chart_container.winfo_children():
            widget.destroy()
        
        # 创建matplotlib图形
        fig, ax = plt.subplots(figsize=(6, 4), dpi=80)
        
        # 设置图表标题和标签（中文）
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('温度 (℃)')
        ax.set_title(f'{data_type} - {message}')
        ax.grid(True)
        
        # 显示提示信息
        ax.text(0.5, 0.5, message, transform=ax.transAxes, 
            ha='center', va='center', fontsize=12,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        
        # 设置坐标轴范围
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        
        # 创建canvas
        canvas = FigureCanvasTkAgg(fig, self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def update_parameter_display(self):
        """更新参数设置显示"""
        # 清空显示框
        for widget in self.display_frame.winfo_children():
            widget.destroy()
        
        if self.parameter_mode == "parameter_menu":
            # 显示参数设置菜单
            param_items = [
                f"目标温度：{self.target_temperature}℃",
                f"间隔时间：{self.interval_time}秒"
            ]
            
            self.param_labels = []
            for i, item in enumerate(param_items):
                label = tk.Label(self.display_frame, text=item, bg='white', padx=10, pady=5, 
                                font=('Arial', 12, 'bold'), anchor='w', width=15)
                label.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=2)
                label.bind("<Button-1>", lambda e, idx=i: self.select_parameter_item(idx))
                self.param_labels.append(label)
            
            # 高亮当前选中的参数项
            self.highlight_selected_parameter()
            
        elif self.parameter_mode == "setting_temp":
            # 显示温度设置界面
            temp_label = tk.Label(self.display_frame, text=f"目标温度：{self.target_temperature}℃", 
                                 bg='lightgreen', padx=10, pady=5, font=('Arial', 12, 'bold'), 
                                 anchor='w', width=15)
            temp_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
            
            interval_label = tk.Label(self.display_frame, text=f"间隔时间：{self.interval_time}秒", 
                                     bg='white', padx=10, pady=5, font=('Arial', 12, 'bold'), 
                                     anchor='w', width=15)
            interval_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
            
        elif self.parameter_mode == "setting_interval":
            # 显示间隔时间设置界面
            temp_label = tk.Label(self.display_frame, text=f"目标温度：{self.target_temperature}℃", 
                                 bg='white', padx=10, pady=5, font=('Arial', 12, 'bold'), 
                                 anchor='w', width=15)
            temp_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
            
            interval_label = tk.Label(self.display_frame, text=f"间隔时间：{self.interval_time}秒", 
                                     bg='lightgreen', padx=10, pady=5, font=('Arial', 12, 'bold'), 
                                     anchor='w', width=15)
            interval_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        else:
            # 正常模式，显示主菜单
            self.show_main_menu()

    def show_main_menu(self):
        """显示主菜单"""
        # 确保停止所有定时器
        if not self.power_on:
            return
        self.stop_all_timers()
        # 清空显示框
        for widget in self.display_frame.winfo_children():
            widget.destroy()
        
        # 重新创建主菜单
        self.menu_labels = []
        for i, item in enumerate(self.menu_items):
            label = tk.Label(self.display_frame, text=item, bg='white', padx=10, pady=5, 
                            font=('Arial', 12,'bold'), anchor='w', width=15)
            label.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=2)
            label.bind("<Button-1>", lambda e, idx=i: self.select_menu_item(idx))
            self.menu_labels.append(label)
        
        # 高亮当前选中的菜单项
        self.highlight_selected_menu()

    def select_parameter_item(self, index):
        """选择参数设置项"""
        self.current_param_selection = index
        self.highlight_selected_parameter()

    def highlight_selected_parameter(self):
        """高亮显示当前选中的参数项"""
        for i, label in enumerate(self.param_labels):
            if i == self.current_param_selection:
                label.configure(background="lightblue", foreground="black")
            else:
                label.configure(background="white", foreground="black")

    def toggle_rubber(self):
        """切换橡胶样品的放置状态"""
        if self.rubber_position == "取下":
            # 检查是否可以放置橡胶样品（空气样品不能在中区域）
            if self.air_position != "中":
                self.rubber_position = "中"
                self.show_rubber_in_middle()
                self.middle_frame.config(height=14)  # 高度减小2/3
                self.top_frame.config(height=150)  # 高度减小2/3
                self.rubber_button.config(text="取下橡胶样品")
                
                # 自动调整加热器位置
                self.auto_adjust_heater_position()
            else:
                # 如果空气样品在中区域，不能放置橡胶样品
                tk.messagebox.showwarning("操作失败", "空气样品在中区域时不能放置橡胶样品！")
        else:
            self.rubber_position = "取下"
            self.hide_rubber()
            self.rubber_button.config(text="放置橡胶样品")
            
            # 自动调整加热器位置
            self.auto_adjust_heater_position()
        
        self.update_experiment_status()
        self.get_base_times_from_current_temperature()

    def toggle_air(self):
        """切换空气样品的放置状态"""
        if self.air_position == "取下":
            # 检查是否可以隔出空气隙（橡胶样品不能在中区域）
            if self.rubber_position != "中":
                self.air_position = "中"
                self.show_air_in_middle()
                self.middle_frame.config(height=14)  # 高度减小2/3
                self.top_frame.config(height=150)  # 高度减小2/3
                self.air_button.config(text="除去空气隙")
                self.rubber_button.config(state=tk.DISABLED)  # 禁用橡胶样品按钮
                # 自动调整加热器位置
                self.auto_adjust_heater_position()
            else:
                # 如果橡胶样品在中区域，不能隔出空气隙
                tk.messagebox.showwarning("操作失败", "橡胶样品在中区域时不能隔出空气隙！")
        else:
            self.air_position = "取下"
            
            self.hide_air()
            self.middle_frame.config(height=14)
            self.air_button.config(text="隔出空气隙")
            
            # 自动调整加热器位置
            self.auto_adjust_heater_position()
        
        self.update_experiment_status()
        self.get_base_times_from_current_temperature()

    def toggle_heater(self):
        """切换加热器的放置状态"""
        if self.heater_position == "取下":
            # 检查是否可以放置加热器（必须有样品或明确选择无样品）
            if self.rubber_position == "中" or self.air_position == "中":
                # 有样品时，加热器放在上区域
                self.heater_position = "上"
                self.show_heater_on_top()
                self.heater_button.config(text="取下加热器")
            else:
                # 无样品时，加热器放在中区域
                self.heater_position = "中"
                self.show_heater_in_middle()
                self.heater_button.config(text="取下加热器")
        else:
            self.heater_position = "取下"
            self.hide_heater()
            self.heater_button.config(text="放置加热器")
        
        self.update_experiment_status()
        self.get_base_times_from_current_temperature()

    def auto_adjust_heater_position(self):
        """自动调整加热器位置"""
        if self.heater_position != "取下":
            if self.rubber_position == "中" or self.air_position == "中":
                # 有样品时，加热器应该在上区域
                if self.heater_position != "上":
                    self.heater_position = "上"
                    self.show_heater_on_top()
            else:
                # 无样品时，加热器应该在中区域
                if self.heater_position != "中":
                    self.heater_position = "中"
                    self.show_heater_in_middle()

    def show_rubber_in_middle(self):
        """在中区域显示橡胶样品"""
        # 移除中区域原有的所有标签
        for widget in self.middle_frame.winfo_children():
            widget.destroy()
        
        # 在中区域显示橡胶样品图片
        self.rubber_label = ttk.Label(self.middle_frame, image=self.rubber_photo)
        self.rubber_label.grid(row=0, column=0, pady=0)
        self.rubber_label.is_rubber = True

    def show_air_in_middle(self):
        """在中区域显示空气样品（用不同颜色表示）"""
        # 移除中区域原有的所有标签
        for widget in self.middle_frame.winfo_children():
            widget.destroy()
        
        self.middle_frame.config(height=14)
        # 创建空气样品表示（使用Frame和颜色）
        # air_frame = tk.Frame(self.middle_frame, bg='lightblue', height=14, width=280)
        # air_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # air_frame.grid_propagate(False)

    def hide_rubber(self):
        """隐藏橡胶样品"""
        # 移除中区域原有的所有标签
        for widget in self.middle_frame.winfo_children():
            widget.destroy()

    def hide_air(self):
        """隐藏空气样品"""
        # 移除中区域原有的所有标签
        for widget in self.middle_frame.winfo_children():
            if hasattr(widget, 'is_air') and widget.is_air:
                widget.destroy()

    def show_heater_on_top(self):
        """在上区域显示加热器"""
        # 移除所有区域的加热器
        self.hide_heater()
        self.top_frame.config(height=140)
        if self.rubber_position == "中":
            self.middle_frame.config(height=14)
        else:
            self.middle_frame.config(height=10)
        # 在上区域创建新的加热器标签
        heater_label = ttk.Label(self.top_frame, image=self.heater_photo)
        heater_label.grid(row=0, column=0, pady=0)
        heater_label.is_heater = True

    def show_heater_in_middle(self):
        """在中区域显示加热器"""
        # 移除所有区域的加热器
        self.hide_heater()
        self.top_frame.config(height=14)
        # 在中区域创建新的加热器标签
        heater_label = ttk.Label(self.middle_frame, image=self.heater_photo)
        heater_label.grid(row=0, column=0, pady=0)
        heater_label.is_heater = True

    def hide_heater(self):
        """隐藏所有区域的加热器"""
        for widget in self.top_frame.winfo_children():
            if hasattr(widget, 'is_heater') and widget.is_heater:
                widget.destroy()
        
        for widget in self.middle_frame.winfo_children():
            if hasattr(widget, 'is_heater') and widget.is_heater:
                widget.destroy()

    def update_experiment_status(self):
        """更新实验区域状态"""
        # 根据当前状态判断实验区域状态
        print(f"heater_position: {self.heater_position}, rubber_position: {self.rubber_position}, air_position: {self.air_position}, heating_status: {self.heating_status}")
        if self.heating_status == "停止" and self.heater_position == "取下" and self.rubber_position == "取下" and self.air_position == "取下":
            self.experiment_status = "散热"
        elif self.rubber_position == "中" and self.heater_position == "上" and self.heating_status == "加热":
            self.experiment_status = "有样品加热（橡胶）"
        elif self.air_position == "中" and self.heater_position == "上" and self.heating_status == "加热":
            self.experiment_status = "有样品加热（空气）"
        elif self.rubber_position == "中" and self.heater_position == "上" and self.heating_status == "停止":
            self.experiment_status = "有样品加热（橡胶）,请进入温度记录界面按确定加热"
        elif self.air_position == "中" and self.heater_position == "上" and self.heating_status == "停止":
            self.experiment_status = "有样品加热（空气）,请进入温度记录界面按确定加热"
        elif self.heater_position == "中" and self.heating_status == "加热":
            self.experiment_status = "无样品加热"
        elif self.heater_position == "中" and self.heating_status == "停止":
            self.experiment_status = "无样品加热,请进入温度记录界面按确定加热"
        elif self.heater_position == "取下":
            if self.air_position == "中" or self.rubber_position == "中":
                self.experiment_status = "请放置加热器或取下样品"
        else:
            self.experiment_status = "无状态"

        if not self.temperature_recording:
            self.fan_button.config(state="normal")
            self.heater_button.config(state="enabled")
            self.reset_temp_button.config(state="enabled")
            if self.rubber_position == "中":
                self.air_button.config(state="disabled")
            else:
                self.air_button.config(state="normal")
            
            if self.air_position == "中":
                self.rubber_button.config(state="disabled")
            else:
                self.rubber_button.config(state="normal")

        # 更新状态提示
        self.status_label.config(text=f"实验状态：{self.experiment_status}")

    def update_interface(self):
        """更新界面显示"""
        # 更新按钮文本
        self.rubber_button.config(text="取下橡胶样品" if self.rubber_position == "中" else "放置橡胶样品")
        self.air_button.config(text="除去空气隙" if self.air_position == "中" else "隔出空气隙")
        self.heater_button.config(text="取下加热器" if self.heater_position != "取下" else "放置加热器")

        # 更新实验区域显示
        self.update_experiment_display()
        
        # 更新实验状态
        self.update_experiment_status()

    def update_experiment_display(self):
        """更新实验区域显示"""
        # 清空所有区域
        for widget in self.top_frame.winfo_children():
            widget.destroy()
        for widget in self.middle_frame.winfo_children():
            widget.destroy()
        
        # 根据状态重新显示
        if self.heater_position == "上":
            self.show_heater_on_top()
        
        if self.rubber_position == "中":
            self.show_rubber_in_middle()
        elif self.air_position == "中":
            self.show_air_in_middle()
        elif self.heater_position == "中":
            self.show_heater_in_middle()

def main():
    root = tk.Tk()
    
    def on_closing():
        print("主窗口关闭事件触发")
        root.quit()
        root.destroy()
        # 强制退出进程
        import os
        os._exit(0)
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        app = HeatingExperiment(root)
        root.mainloop()
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        print("程序退出")
        # 确保进程结束
        import os
        os._exit(0)

if __name__ == "__main__":
    main()