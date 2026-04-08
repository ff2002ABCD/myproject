# coding=utf-8
from tkinter import filedialog, messagebox, StringVar
from tkinter import Tk, ttk
import serial
import serial.tools.list_ports
import matplotlib
matplotlib.use('TkAgg')  # 明确指定使用TkAgg后端
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox, RadioButtons
from collections import deque
import struct
import numpy as np
import csv
import os
import time
import tkinter as tk

import matplotlib.backends.backend_tkagg as tkagg
# 修改工具栏配置
tkagg.NavigationToolbar2Tk.toolitems = [
    ('Home', '重置原始视图', 'home', 'home'),
    ('Back', '后退到前一视图', 'back', 'back'),
    
    (None, None, None, None),
    ('Pan', '平移视图', 'move', 'pan'),
    ('Zoom', '缩放视图', 'zoom_to_rect', 'zoom'),
    (None, None, None, None),
    ('Save', '保存图像', 'filesave', 'save_figure'),
]

# 设置Matplotlib
plt.rcParams['font.family'] = 'SimHei'
plt.rcParams['axes.unicode_minus'] = False

# 全局配置
SERIAL_PORT = ''  # 初始为空，由用户输入
BAUD_RATE = 115200
MAX_POINTS = 100000
UPDATE_INTERVAL = 100  # 毫秒

class SerialPortDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel()
        self.top.title("选择串口")
        self.top.geometry("400x200")
        # 添加这行确保窗口关闭时调用 on_cancel
        self.top.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # 获取可用串口列表
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        
        if not port_list:
            port_list = ["未检测到可用串口"]
        
        # 创建标签
        ttk.Label(self.top, text="请选择要连接的串口:").pack(pady=10)
        
        # 创建下拉框
        self.port_var = StringVar()
        self.port_combobox = ttk.Combobox(
            self.top, 
            textvariable=self.port_var,
            values=port_list,
            state="readonly"
        )
        self.port_combobox.pack(pady=10)
        
        # 默认选择第一个串口
        if port_list and port_list[0] != "未检测到可用串口":
            self.port_combobox.current(0)
        
        # 创建连接按钮
        connect_btn = ttk.Button(
            self.top, 
            text="连接",
            command=self.on_connect
        )
        connect_btn.pack(pady=10)
        
        # 创建取消按钮
        cancel_btn = ttk.Button(
            self.top, 
            text="取消",
            command=self.on_cancel
        )
        cancel_btn.pack(pady=5)
        
        self.selected_port = None
        self.parent = parent

        self.top.transient(parent.root)
        self.top.grab_set()
    
    def on_connect(self):
        port = self.port_var.get()
        if port and port != "未检测到可用串口":
            self.selected_port = port
            self.top.destroy()
            self.parent.connect_serial(port)
    
    def on_cancel(self):
        self.top.destroy()
        self.selected_port = None

class RealTimePlotter:
    def __init__(self):
        self.serial_port = SERIAL_PORT
        self.baud_rate = BAUD_RATE
        self.ser = None
        self.running = True
        self.auto_scale_enabled = True
        self.last_update_time = 0
        self.figures = {}
        self.status_text = None
        self.content_ax = None
        self.port_textbox = None
        self.connect_btn = None
        self.help_text = None
        self.root = None
        
        # 先创建控制面板
        self.create_tab_window()
        
        # 然后初始化图表（初始隐藏）
        self.init_figures()
        
        # 启动定时器
        self.timer = self.figures['F1']['fig'].canvas.new_timer(interval=UPDATE_INTERVAL)
        self.timer.add_callback(self.update_plots)
        self.timer.start()

    def init_figures(self):
        """初始化三个独立的图表（初始隐藏）"""
        # 创建图形并确保包含所有必要的键
        self.figures = {
            'F1': self.create_figure(
                plt.figure("动镜行程-光功率测量", figsize=(12, 5)),
                x_label='动镜行程 (nm)',
                title='动镜行程-光功率测量',
                color='blue',
                file='XP.CSV',
                marker=0x0A,
                x_lim=(-2147483648, 2147483647)
            ),
            'F2': self.create_figure(
                plt.figure("角度-光功率测量", figsize=(12, 5)),
                x_label='角度 (°)',
                title='角度-光功率测量',
                color='green',
                file='AP.CSV',
                marker=0x0B,
                x_lim=(-2147483648, 2147483647)
            ),
            'F3': self.create_figure(
                plt.figure("时间-光功率测量", figsize=(12, 5)),
                x_label='时间 (s)',
                title='时间-光功率测量',
                color='red',
                file='TP.CSV',
                marker=0x0C,
                x_lim=(-2147483648, 2147483647))
        }
        
        # 为每个图表创建控件并初始隐藏
        for key in self.figures:
            self.create_controls(key)
            plt.close(self.figures[key]['fig'])

    def create_tab_window(self):
        """创建控制面板窗口"""
        self.tab_fig = plt.figure("控制面板", figsize=(10, 4))
        self.tab_fig.subplots_adjust(left=0.05, right=0.95, top=0.8, bottom=0.2)
        
        # 创建选项卡按钮
        tab_ax = self.tab_fig.add_axes([0.05, 0.6, 0.9, 0.3])
        labels = ('动镜行程-光功率测量', '角度-光功率测量', '时间-光功率测量')  # 修改后的标签
        self.tab_buttons = RadioButtons(
            tab_ax,
            labels,
            active=0,
            activecolor='lightblue'
        )
        
        # 调整按钮间距 - 兼容不同matplotlib版本
        if hasattr(self.tab_buttons, 'circles'):  # 新版本
            for i, (circle, label) in enumerate(zip(self.tab_buttons.circles, self.tab_buttons.labels)):
                circle.set_radius(0.05)
                label.set_fontsize(10)
                circle.center = (0.1 + i*0.23, 0.5)
                label.set_position((0.1 + i*0.23, 0.5))
        elif hasattr(self.tab_buttons, 'rectangles'):  # 旧版本
            for i, (rect, label) in enumerate(zip(self.tab_buttons.rectangles, self.tab_buttons.labels)):
                rect.set_width(0.2)
                rect.set_x(0.05 + i*0.23)
                label.set_fontsize(10)
            
        self.tab_buttons.on_clicked(self.on_tab_changed)
        
        # 创建内容区域
        self.content_ax = self.tab_fig.add_axes([0.1, 0.1, 0.8, 0.7])
        self.content_ax.axis('off')
        
        # 显示串口设置界面
        self.show_serial_settings()
        
        # 显示控制面板
        plt.show(block=False)

    def show_serial_settings(self):
        """显示串口设置界面"""
        # 清除之前的内容
        if hasattr(self, 'port_textbox') and self.port_textbox:
            self.port_textbox.disconnect_events()
        if hasattr(self, 'connect_btn') and self.connect_btn:
            self.connect_btn.disconnect_events()
        if hasattr(self, 'status_text') and self.status_text:
            self.status_text.remove()
        if hasattr(self, 'help_text') and self.help_text:
            self.help_text.remove()
        
        # 串口号显示框（只读）
        #port_ax = self.tab_fig.add_axes([0.3, 0.6, 0.4, 0.1])
        #self.port_textbox = TextBox(port_ax, '当前串口:', initial=self.serial_port or "未连接")
        #self.port_textbox.set_active(False)  # Changed from text_disp.set_readonly(True)
        
        # 连接按钮
        connect_ax = self.tab_fig.add_axes([0.3, 0.4, 0.4, 0.1])
        self.connect_btn = Button(connect_ax, '选择串口', color='lightblue')
        self.connect_btn.on_clicked(self.show_serial_dialog)
        
        # 状态显示
        status_ax = self.tab_fig.add_axes([0.3, 0.2, 0.4, 0.1])
        status_ax.axis('off')
        self.status_text = status_ax.text(0.5, 0.5, '请点击"选择串口"按钮', 
                                        ha='center', va='center')
        
        # 操作提示
        help_ax = self.tab_fig.add_axes([0.1, 0.02, 0.8, 0.1])
        help_ax.axis('off')
        self.help_text = help_ax.text(0.5, 0.5, 
                                    '操作步骤: 1.点击"选择串口" 2.从列表中选择串口 3.点击连接 4.选择测量类型', 
                                    ha='center', va='center', fontsize=10)

    def show_serial_dialog(self, event=None):
        """显示串口选择对话框"""
        # 创建临时Tkinter窗口
        if not self.root:
            self.root = Tk()
            self.root.withdraw()
        
        # 创建并显示串口选择对话框
        dialog = SerialPortDialog(self)
        self.root.wait_window(dialog.top)

    def connect_serial(self, port=None):
        """连接串口"""
        if port is None:
            port = self.serial_port
            
        if not port:
            print("错误: 未选择串口")
            if self.status_text:
                self.status_text.set_text('错误: 未选择串口')
            self.tab_fig.canvas.draw_idle()
            return
            
        try:
            # 关闭现有连接
            if self.ser and self.ser.is_open:
                self.ser.close()
            
            # 建立新连接
            self.ser = serial.Serial(port, self.baud_rate, timeout=0.1)
            self.serial_port = port
            print(f"已连接到串口: {port}")
            
            # 更新UI显示
            if self.port_textbox:
                self.port_textbox.set_val(port)
            if self.status_text:
                self.status_text.set_text(f'已连接: {port}')
        except Exception as e:
            print(f"串口连接失败: {str(e)}")
            if self.status_text:
                self.status_text.set_text(f'连接失败: {str(e)}')
            self.ser = None
        
        self.tab_fig.canvas.draw_idle()

    def create_figure(self, fig, x_label, title, color, file, marker, x_lim):
        """创建并配置一个图表"""
        try:
            fig.canvas.manager.set_window_title(title)
        except:
            pass  # 忽略设置标题时的错误
        
        ax = fig.add_subplot(111, label=f"ax_{title}")
        scatter = ax.scatter([], [], c=color, alpha=0.6, s=40)
        
        ax.set_xlabel(x_label)
        ax.set_ylabel('光功率 (μW)')
        ax.set_title(title)
        ax.grid(True)
        ax.set_xlim(x_lim[0], x_lim[1])
        ax.set_ylim(-1000, 5000)
        
        return {
            'fig': fig,
            'ax': ax,
            'scatter': scatter,
            'x_data': deque(maxlen=MAX_POINTS),
            'y_data': deque(maxlen=MAX_POINTS),
            'file': file,
            'marker': marker,
            'x_lim': x_lim,
            'title': title,
            'x_label': x_label,
            'color': color,
            'controls_visible': True,
            'control_axes': [],
            'buttons': []
        }

    def update_serial_port(self, text):
        """更新串口号"""
        self.serial_port = text.strip()
        print(f"串口号更新为: {self.serial_port}")
        if self.status_text:
            self.status_text.set_text(f'串口号已设置: {self.serial_port}')
        self.tab_fig.canvas.draw_idle()

    def on_tab_changed(self, label):
        """处理选项卡切换"""
        # 清除当前内容区域
        self.content_ax.clear()
        self.content_ax.axis('off')
        
        # 根据选择显示不同内容
        if label == '串口设置':
            self.show_serial_settings()
        else:
            # 隐藏所有图表窗口
            for key in self.figures:
                if plt.fignum_exists(self.figures[key]['fig'].number):
                    plt.close(self.figures[key]['fig'])
            
            if label == '动镜行程-光功率测量':
                self.show_figure('F1')
            elif label == '角度-光功率测量':
                self.show_figure('F2')
            elif label == '时间-光功率测量':
                self.show_figure('F3')
        
        self.tab_fig.canvas.draw_idle()

    def show_figure(self, figure_key):
        """显示指定的图表窗口"""
        fig_data = self.figures.get(figure_key)
        if not fig_data:
            print(f"错误: 未找到图表 {figure_key}")
            return
            
        # 检查必要的键是否存在
        required_keys = ['fig', 'ax', 'title', 'scatter', 'file', 'marker', 'x_lim', 'x_label', 'color']
        for key in required_keys:
            if key not in fig_data:
                print(f"错误: 图表数据中缺少键 {key}")
                return
        
        # 如果窗口不存在或已关闭，重新创建
        if not plt.fignum_exists(fig_data['fig'].number):
            fig_data['fig'] = plt.figure(fig_data['fig'].number, figsize=(12, 5))
            fig_data = self.create_figure(
                fig_data['fig'],
                fig_data['x_label'],
                fig_data['title'],
                fig_data['color'],
                fig_data['file'],
                fig_data['marker'],
                fig_data['x_lim']
            )
            self.figures[figure_key] = fig_data
            self.create_controls(figure_key)
        
        # 显示窗口
        plt.figure(fig_data['fig'].number)
        try:
            plt.show(block=False)
        except Exception as e:
            print(f"显示窗口时出错: {str(e)}")
            return
        
        # 更新控制面板标题
        try:
            self.tab_fig.canvas.manager.set_window_title(f"控制面板 - {fig_data['title']}")
        except:
            pass
        
        # 在内容区域显示提示信息
        self.content_ax.text(0.5, 0.5, 
                           f'正在显示: {fig_data["title"]}\n串口状态: {"已连接" if self.ser and self.ser.is_open else "未连接"}',
                           ha='center', va='center', fontsize=12)
        self.tab_fig.canvas.draw_idle()

    def create_controls(self, figure_key):
        """为指定图表创建控制面板"""
        fig_data = self.figures[figure_key]
        
        # 初始底部边距
        fig_data['fig'].subplots_adjust(bottom=0.25)
        
        # 创建功能按钮
        buttons = [
            ([0.1, 0.05, 0.15, 0.06], '导出数据', fig_data['color'], 
             lambda e: self.export_data(figure_key)),
            ([0.3, 0.05, 0.15, 0.06], '导入数据', fig_data['color'],
             lambda e: self.import_data(figure_key)),
            ([0.5, 0.05, 0.15, 0.06], '清除数据', 'lightgoldenrodyellow',
             lambda e: self.clear_data(figure_key)),
            ([0.7, 0.05, 0.15, 0.06], '自动缩放: ON', 'lightgreen',
             lambda e: self.toggle_auto_scale(figure_key))
        ]
        
        # 添加按钮
        for pos, label, color, callback in buttons:
            ax = fig_data['fig'].add_axes(pos)
            btn = Button(ax, label, color=color)
            btn.on_clicked(callback)
            fig_data['control_axes'].append(ax)
            fig_data['buttons'].append(btn)
        
        # 添加切换按钮
        toggle_ax = fig_data['fig'].add_axes([0.85, 0.05, 0.1, 0.06])
        toggle_btn = Button(toggle_ax, '隐藏控件', color='lightgray')
        toggle_btn.on_clicked(lambda e: self.toggle_controls(figure_key))
        fig_data['toggle_button'] = toggle_btn

    def toggle_controls(self, figure_key):
        """切换控件可见性"""
        fig_data = self.figures[figure_key]
        fig_data['controls_visible'] = not fig_data['controls_visible']
        
        # 设置控件可见性
        for ax in fig_data['control_axes']:
            ax.set_visible(fig_data['controls_visible'])
        
        # 更新按钮文本
        fig_data['toggle_button'].label.set_text(
            '隐藏控件' if fig_data['controls_visible'] else '显示控件')
        
        # 调整布局
        fig_data['fig'].subplots_adjust(
            bottom=0.25 if fig_data['controls_visible'] else 0.15)
        
        fig_data['fig'].canvas.draw_idle()

    def clear_data(self, figure_key):
        """清除数据"""
        fig_data = self.figures[figure_key]
        fig_data['x_data'].clear()
        fig_data['y_data'].clear()
        fig_data['scatter'].set_offsets(np.column_stack(([], [])))
        
        # 重置视图
        fig_data['ax'].set_xlim(fig_data['x_lim'][0], fig_data['x_lim'][1])
        fig_data['ax'].set_ylim(-1000, 5000)
        fig_data['fig'].canvas.draw_idle()
        print(f"{figure_key} 数据已清除")

    def read_serial_data(self):
        """读取串口数据"""
        if not self.ser or not self.ser.is_open:
            return
        
        try:
            while self.ser.in_waiting >= 7:
                data = self.ser.read(7)
                if len(data) == 7:
                    marker = data[6]
                    x, y = struct.unpack('<ih', data[:6])
                    processed_y = round((2+6*y/65536)*1000, 1)
                    
                    for key in self.figures:
                        if marker == self.figures[key]['marker']:
                            if key == 'F2':  # 角度数据
                                x_val = round(x * 0.18, 2)
                            elif key == 'F3':  # 时间数据
                                x_val = round(x / 10, 1)
                            else:  # 动镜行程数据
                                x_val = x*5
                            self.figures[key]['x_data'].append(x_val)
                            self.figures[key]['y_data'].append(processed_y)
                            print(f"{key} 收到数据: X={x_val}, Y={processed_y}")
                            break
        except Exception as e:           
            self.close()

    def update_plots(self):
        """更新图表"""
        current_time = time.time() * 1000
        if current_time - self.last_update_time < UPDATE_INTERVAL:
            return
        
        self.read_serial_data()
        
        for key in self.figures:
            fig_data = self.figures[key]
            if fig_data['x_data']:
                fig_data['scatter'].set_offsets(
                    np.column_stack((fig_data['x_data'], fig_data['y_data'])))
                
                if self.auto_scale_enabled:
                    self.auto_scale(fig_data)
            
            fig_data['fig'].canvas.draw_idle()
        
        self.last_update_time = current_time
        return True
    
    def auto_scale(self, fig_data):
        """自动缩放"""
        if fig_data['x_data']:
            ax = fig_data['ax']
            x_min, x_max = min(fig_data['x_data']), max(fig_data['x_data'])
            y_min, y_max = min(fig_data['y_data']), max(fig_data['y_data'])
            
            x_padding = max(1, (x_max - x_min) * 0.1)
            y_padding = max(1, (y_max - y_min) * 0.1)
            
            ax.set_xlim(x_min-x_padding, x_max+x_padding)
            ax.set_ylim(y_min-y_padding, y_max+y_padding)

    def toggle_auto_scale(self, figure_key):
        """切换自动缩放"""
        self.auto_scale_enabled = not self.auto_scale_enabled
        fig_data = self.figures[figure_key]
        fig_data['buttons'][3].label.set_text(
            '自动缩放: ON' if self.auto_scale_enabled else '自动缩放: OFF')
        fig_data['fig'].canvas.draw_idle()
        print(f"自动缩放 {'启用' if self.auto_scale_enabled else '禁用'}")
        
    def export_data(self, figure_key):
        """导出数据"""
        fig_data = self.figures[figure_key]
        if not fig_data['x_data']:
            print(f"{figure_key}: 没有数据可导出")
            return
        
        # 创建Tkinter根窗口并隐藏
        root = Tk()
        root.withdraw()
        
        # 确保文件对话框在最上层
        root.attributes('-topmost', True)
        
        # 临时降低测量界面和控制面板的层级
        if plt.fignum_exists(fig_data['fig'].number):
            fig_manager = plt.get_current_fig_manager()
            fig_manager.window.attributes('-topmost', False)
        
        if hasattr(self, 'tab_fig') and plt.fignum_exists(self.tab_fig.number):
            tab_manager = plt.get_current_fig_manager()
            tab_manager.window.attributes('-topmost', False)
        
        # 弹出文件保存对话框
        file_path = filedialog.asksaveasfilename(
            parent=root,
            title='选择保存位置',
            defaultextension='.csv',
            filetypes=[('CSV文件', '*.csv'), ('所有文件', '*.*')],
            initialfile=fig_data['file']
        )
        
        # 恢复测量界面层级
        if plt.fignum_exists(fig_data['fig'].number):
            plt.figure(fig_data['fig'].number)
            plt.get_current_fig_manager().window.attributes('-topmost', True)
        
        # 关闭临时窗口
        root.destroy()
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='GB2312') as f:
                writer = csv.writer(f)
                writer.writerow(['', fig_data['ax'].get_xlabel(), '光功率(μW)'])
                for i, (x, y) in enumerate(zip(fig_data['x_data'], fig_data['y_data'])):
                    writer.writerow([i+1, x, y])
            print(f"{figure_key} 数据已导出到: {os.path.abspath(file_path)}")
        except Exception as e:
            print(f"导出失败: {str(e)}")

    def import_data(self, figure_key):
        """导入数据"""
        fig_data = self.figures[figure_key]
        
        # 创建Tkinter根窗口并隐藏
        root = Tk()
        root.withdraw()
        
        # 确保文件对话框在最上层
        root.attributes('-topmost', True)
        
        # 临时降低测量界面和控制面板的层级
        if plt.fignum_exists(fig_data['fig'].number):
            fig_manager = plt.get_current_fig_manager()
            fig_manager.window.attributes('-topmost', False)
        
        if hasattr(self, 'tab_fig') and plt.fignum_exists(self.tab_fig.number):
            tab_manager = plt.get_current_fig_manager()
            tab_manager.window.attributes('-topmost', False)
        
        # 弹出文件选择对话框
        file_path = filedialog.askopenfilename(
            parent=root,
            title='选择要导入的CSV文件',
            filetypes=[('CSV文件', '*.csv'), ('所有文件', '*.*')],
            initialfile=self.figures[figure_key]['file']
        )
        
        # 恢复测量界面层级
        if plt.fignum_exists(fig_data['fig'].number):
            plt.figure(fig_data['fig'].number)
            plt.get_current_fig_manager().window.attributes('-topmost', True)
        
        # 关闭临时窗口
        root.destroy()
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='GB2312') as f:
                reader = csv.reader(f)
                next(reader)  # 跳过标题行
                fig_data['x_data'].clear()
                fig_data['y_data'].clear()
                
                for row in reader:
                    if len(row) >= 3:
                        try:
                            fig_data['x_data'].append(float(row[1]))
                            fig_data['y_data'].append(float(row[2]))
                        except ValueError:
                            continue
                
                print(f"{figure_key} 已导入 {len(fig_data['x_data'])} 个数据点")
                self.auto_scale(fig_data)
                fig_data['fig'].canvas.draw_idle()
        except FileNotFoundError:
            print(f"文件未找到: {file_path}")
        except Exception as e:
            print(f"导入失败: {str(e)}")

    def close(self):
        """关闭程序"""
        if self.running:
            self.running = False
            if hasattr(self, 'timer'):
                self.timer.stop()
            if self.ser and self.ser.is_open:
                self.ser.close()
            plt.close('all')
            print("程序已关闭")

# 运行程序
if __name__ == "__main__":
    plotter = RealTimePlotter()
    try:
        plt.show()
    except KeyboardInterrupt:
        plotter.close()