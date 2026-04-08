import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import filedialog
import os
import sys
from PIL import Image, ImageTk
import pandas as pd
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def resource_path(relative_path):
    """获取资源的绝对路径，支持开发环境和PyInstaller打包后环境"""
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class ThreeLayerImageViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("FD-ICH-C 新型螺线管磁场测量实验仪")
        
       # 获取程序所在目录或打包后的临时目录
        try:
            # PyInstaller打包后的环境
            self.program_dir = sys._MEIPASS
        except AttributeError:
            # 开发环境
            self.program_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 设置数据目录
        self.data_dir = os.path.join(self.program_dir, "data")
        print(f"程序所在目录: {self.program_dir}")
        print(f"数据目录: {self.data_dir}")
        
        # 检查数据目录是否存在，如果不存在则创建
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"创建数据目录: {self.data_dir}")
        
        # 设置窗口大小
        self.scale_factor=3/4  # 缩放比例
        self.window_width = int(1000*self.scale_factor)  # 窗口宽度
        self.window_height = int(600*self.scale_factor) # 窗口高度
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.resizable(False, False)  # 禁止调整窗口大小

         # 设置表格支持多选
        self.setup_treeview_multiselect()
        # 初始化变量
        self.bottom_image = None
        self.middle_image = None
        self.top_image = None
        self.bottom_photo = None
        self.middle_photo = None
        self.top_photo = None
        self.middle_x_pos = 0
        self.middle_y_pos = 0
        self.move_step = 20  # 每次移动的像素数
        self.sensor_x_pos = 0  # 移动传感器X位置
        self.current_position = 0  # 当前位置
        self.calibration_params = {}  # 传感器定标参数
        self.measurement_params = {}  # 磁场分布测量参数
        self.measurement_calculated = False  # 磁场分布计算标志

        # 移动范围限制
        self.min_x_pos = -1008*self.scale_factor  # 最小X位置
        self.max_x_pos = 0      # 最大X位置
        self.position_locked = False  # 位置锁定状态
        self.current_locked = False  # 电流锁定状态
        self.measurement_buttons_created = False  # 添加按钮创建标志
        
        # 长按相关变量
        self.left_pressed = False
        self.right_pressed = False
        self.repeat_delay = 100  # 首次重复前的延迟(ms)
        self.repeat_interval = 50  # 重复间隔(ms)

        # 添加红线相关变量
        self.red_line_x = 613*self.scale_factor  # 红线初始X位置（画布中心）
        self.red_line_y1 = 30*self.scale_factor  # 红线起始Y位置
        self.red_line_y2 = 130*self.scale_factor  # 红线结束Y位置
        self.red_line_id = None  # 红线的画布ID

        # 添加电压和电流文本框变量
        self.voltage_text = "0.0"  # 电压文本
        self.current_text = "0"  # 电流文本
        self.voltage_box_id = None  # 电压文本框ID
        self.current_box_id = None  # 电流文本框ID
        
        # 添加旋钮变量
        self.current_knob_value = 0  # 电流旋钮值 (0-500)
        self.voltage_knob_value = 0  # 电压旋钮值 (-10到10)
        self.current_knob_id = None  # 电流旋钮ID
        self.voltage_knob_id = None  # 电压旋钮ID
        
        # 添加换向开关变量
        self.direction_var = tk.StringVar(value="正向")  # 默认正向
        
        # 添加箭头相关变量
        self.arrow_id = None  # 箭头的画布ID

        # 添加表格引用变量
        self.calibration_tree = None
        self.measurement_tree = None

        self.current_scale = None  # 保存电流调节进度条引用
        
        # 缩放比例（基于底层图片）
        self.scale_ratio = 1.0
        
        # 图片文件名
        self.bottom_filename = "实验面板图.png"
        self.middle_filename = "刻度图.png"
        self.top_filename = "顶层.png"
        
        # Excel数据文件
        self.excel_filename = "螺线管U-X(250MA).xlsx"
        self.excel_data = None  # 存储Excel数据
        
        # 画布尺寸
        self.canvas_width = 720 *self.scale_factor
        self.canvas_height = 500 *self.scale_factor
        
        # 添加随机初始电压偏移 (-10到10)
        self.random_voltage_offset = random.uniform(-10, 10)
        print(f"随机初始电压偏移: {self.random_voltage_offset:.1f} V")
        
        # Excel数据随机波动因子（0.5%）
        self.excel_random_factor = 1 + random.uniform(-0.005, 0.005)
        print(f"Excel数据随机波动因子: {self.excel_random_factor:.4f}")
        
        # 实验数据存储
        self.calibration_data = []  # 传感器定标数据
        self.measurement_data = []  # 磁场分布测量数据
        self.calibration_line_plotted = False  # 标记是否已经绘制连线

        # 打印调试信息
        self.print_debug_info()
        
        # 加载Excel数据
        self.load_excel_data()
        
        # 创建界面
        self.create_widgets()
        
        # 自动加载图片
        self.auto_load_images()
        self.update_voltage_from_position()
        
        # 创建数据记录面板
        self.create_experiment_panel()
    
    def setup_treeview_multiselect(self):
        """设置表格支持多选"""
        # 在创建表格后调用这个方法
        pass  # 实际设置会在各自的setup方法中完成

    def get_data_directory(self):
        """获取数据目录的路径，优先使用程序所在目录的data文件夹"""
        # 首先检查程序所在目录的data文件夹
        program_data_dir = os.path.join(self.program_dir, "data")
        if os.path.exists(program_data_dir):
            return program_data_dir
        
        # 然后检查打包环境的data文件夹
        try:
            packaged_data_dir = os.path.join(sys._MEIPASS, "data")
            if os.path.exists(packaged_data_dir):
                return packaged_data_dir
        except:
            pass
        
        # 最后检查当前工作目录的data文件夹
        work_data_dir = os.path.join(os.getcwd(), "data")
        if os.path.exists(work_data_dir):
            return work_data_dir
        
        # 如果都找不到，创建程序所在目录的data文件夹
        os.makedirs(program_data_dir, exist_ok=True)
        return program_data_dir
    
    def get_data_path(self, filename):
        """获取数据文件的完整路径"""
        return os.path.join(self.data_dir, filename)
    
    def fix_current(self):
        """固定电流"""
        self.current_locked = True
        # 禁用电流调节
        self.enable_current_controls(False)
        
        # 更新按钮文本
        self.update_measurement_buttons()
        
        # 更新曲线标题
        self.update_plot(self.step_var.get())
        messagebox.showinfo("信息", "电流已固定，电流调节已禁用")


    def enable_current_controls(self, enabled):
        """启用或禁用电流控制"""
        state = tk.NORMAL if enabled else tk.DISABLED
        
        # 禁用/启用主界面的电流调节进度条
        if self.current_scale:
            self.current_scale.config(state=state)
        
        # 禁用/启用数据记录面板中的电流控制（如果有）
        # 这里可以根据需要添加对其他电流控件的控制

    def unlock_current(self):
        """解锁电流调节"""
        self.current_locked = False
        # 启用电流调节
        self.enable_current_controls(True)
        
        # 更新按钮文本
        self.update_measurement_buttons()
        
        # 更新曲线标题
        self.update_plot(self.step_var.get())
        messagebox.showinfo("信息", "电流调节已解锁")

    def update_measurement_buttons(self):
        """更新磁场分布测量的按钮文本和命令"""
        if hasattr(self, 'button_frame'):
            for widget in self.button_frame.winfo_children():
                if isinstance(widget, tk.Button):
                    if self.current_locked and widget.cget("text") == "固定电流调节":
                        widget.config(text="解锁电流调节", command=self.unlock_current)
                    elif not self.current_locked and widget.cget("text") == "解锁电流调节":
                        widget.config(text="固定电流调节", command=self.fix_current)

    def unlock_position(self):
        """解锁位置刻度"""
        self.position_locked = False
        # 启用移动按钮
        self.enable_movement_buttons(True)
        # 新增：启用重置按钮
        self.enable_reset_button(True)
        # 更新按钮文本
        for widget in self.button_frame.winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") == "解锁位置刻度":
                widget.config(text="固定位置刻度", command=self.fix_position)
        messagebox.showinfo("信息", "位置刻度已解锁，传感器移动已启用")
        


    def create_experiment_panel(self):
        """创建数据记录面板窗口"""
        self.experiment_window = tk.Toplevel(self.root)
        self.experiment_window.title("数据记录面板")
        self.experiment_window.geometry("850x820")
        self.experiment_window.resizable(True, True)
        
        # 禁止关闭窗口
        self.experiment_window.protocol("WM_DELETE_WINDOW", lambda: None)
        # 第一区域：实验步骤选择
        step_frame = tk.LabelFrame(self.experiment_window, text="实验步骤选择", padx=5, pady=5)
        step_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.step_var = tk.StringVar(value="sensor_calibration")
        
        tk.Radiobutton(step_frame, text="传感器定标", variable=self.step_var, 
                      value="sensor_calibration", command=self.update_experiment_panel).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(step_frame, text="测量通电螺线管中的磁场分布", variable=self.step_var, 
                      value="field_measurement", command=self.update_experiment_panel).pack(side=tk.LEFT, padx=10)
        
        # 第二区域：曲线图显示
        self.plot_frame = tk.LabelFrame(self.experiment_window, text="曲线图", padx=5, pady=5)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建图表
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas_plot = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 第三区域：数据显示
        self.data_frame = tk.LabelFrame(self.experiment_window, text="数据", padx=5, pady=5)
        self.data_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 第四区域：按钮区域
        self.button_frame = tk.Frame(self.experiment_window)
        self.button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 初始化面板
        self.update_experiment_panel()
    
    def update_experiment_panel(self):
        """根据选择的实验步骤更新面板内容"""
        step = self.step_var.get()
        
        # 清除第三区域和第四区域
        for widget in self.data_frame.winfo_children():
            widget.destroy()
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        
        # 更新曲线图
        self.update_plot(step)
        
        # 实验步骤切换时自动解锁位置刻度和电流调节
        if self.position_locked:
            self.unlock_position()  # 调用解锁方法
        if self.current_locked:
            self.unlock_current()   # 调用电流解锁方法
        else:
            # 确保电流控制处于启用状态
            self.enable_current_controls(True)
        
        if step == "sensor_calibration":
            self.setup_sensor_calibration_ui()
            self.measurement_buttons_created = False  # 重置标志
        else:
            self.setup_field_measurement_ui()
    
    # 在update_plot方法中，修改传感器定标部分的代码
    def update_plot(self, step):
        """更新曲线图"""
        self.ax.clear()

        if step == "sensor_calibration":
            # 传感器定标曲线
            if self.position_locked:
                self.ax.set_title(f'传感器定标曲线（位置刻度X={(round(self.sensor_x_pos * 20) / 20):.2f}cm）')
            else:
                self.ax.set_title('传感器定标曲线')
            
            if self.calibration_data:
                currents = [d['current'] for d in self.calibration_data]
                voltages = [d['voltage'] for d in self.calibration_data]
                self.ax.plot(currents, voltages, 'bo', label='测量数据点')
                
                # 如果已经计算了斜率，绘制拟合直线
                if self.calibration_line_plotted and len(currents) > 1:
                    # 使用numpy进行线性拟合
                    k, b = np.polyfit(currents, voltages, 1)
                    
                    # 计算相关系数R
                    correlation_matrix = np.corrcoef(currents, voltages)
                    R = correlation_matrix[0, 1]
                    
                    # 生成拟合直线的点
                    x_fit = np.linspace(min(currents), max(currents), 100)
                    y_fit = k * x_fit + b
                    self.ax.plot(x_fit, y_fit, 'r-', label=f'拟合直线 (k={k:.4f})')
                    
                    # 在图上显示拟合公式和相关系数
                    formula_text = f'U = {k:.4f} × Im + {b:.2f}\nR = {R:.4f}'
                    # 将公式放在图的右上角
                    self.ax.text(0.95, 0.05, formula_text, transform=self.ax.transAxes,
                            fontsize=10, verticalalignment='bottom', horizontalalignment='right',
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                    
                    self.ax.legend()
                
                self.ax.set_xlabel('螺线管通电电流 Im (mA)')
                self.ax.set_ylabel('霍尔电势差 U (mV)')
            else:
                self.ax.set_xlabel('螺线管通电电流 Im (mA)')
                self.ax.set_ylabel('霍尔电势差 U (mV)')
                self.ax.set_title('传感器定标曲线 (暂无数据)')
        else:
            # 磁场分布曲线
            if self.measurement_data:
                # 按位置排序数据
                sorted_data = sorted(self.measurement_data, key=lambda x: x['position'])
                positions = [d['position'] for d in sorted_data]
                field_strengths = [d['field_strength'] for d in sorted_data]
                
                # 始终绘制数据点
                self.ax.plot(positions, field_strengths, 'ro', label='测量数据点')
                
                # 只有在计算后才绘制连线
                if hasattr(self, 'measurement_calculated') and self.measurement_calculated:
                    self.ax.plot(positions, field_strengths, 'r-', label='磁场分布曲线')
                
                self.ax.set_xlabel('位置刻度 X (cm)')
                self.ax.set_ylabel('磁感应强度 B (mT)')
                
                # 根据电流锁定状态设置标题
                if self.current_locked:
                    self.ax.set_title(f'磁场分布曲线（励磁电流Im={self.current_knob_value:.0f}mA）')
                else:
                    self.ax.set_title('磁场分布曲线')
                
                # 添加图例
                self.ax.legend()
            else:
                self.ax.set_xlabel('位置刻度 X (cm)')
                self.ax.set_ylabel('磁感应强度 B (mT)')
                self.ax.set_title('磁场分布曲线 (暂无数据)')
        
        self.ax.grid(True)
        self.canvas_plot.draw()
    
    def on_calibration_tree_right_click(self, event):
        """传感器定标表格右键点击事件"""
        # 获取点击的行
        item = self.calibration_tree.identify_row(event.y)
        if item:
            # 检查点击的行是否已经在选择中
            selected_items = self.calibration_tree.selection()
            if item not in selected_items:
                # 如果点击的行不在当前选择中，清除原有选择并选择当前行
                self.calibration_tree.selection_set(item)
            # 显示右键菜单
            self.calibration_tree_menu.post(event.x_root, event.y_root)
        else:
            # 如果点击在空白处，清除选择
            self.calibration_tree.selection_remove(self.calibration_tree.selection())

    def on_measurement_tree_right_click(self, event):
        """磁场分布测量表格右键点击事件"""
        # 获取点击的行
        item = self.measurement_tree.identify_row(event.y)
        if item:
            # 检查点击的行是否已经在选择中
            selected_items = self.measurement_tree.selection()
            if item not in selected_items:
                # 如果点击的行不在当前选择中，清除原有选择并选择当前行
                self.measurement_tree.selection_set(item)
            # 显示右键菜单
            self.measurement_tree_menu.post(event.x_root, event.y_root)
        else:
            # 如果点击在空白处，清除选择
            self.measurement_tree.selection_remove(self.measurement_tree.selection())

    def delete_selected_calibration_row(self):
        """删除选中的传感器定标数据行"""
        selected_items = self.calibration_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的数据行")
            return
        
        # 确认删除
        result = messagebox.askyesno("确认删除", "确定要删除选中的数据行吗？此操作不可撤销！")
        if not result:
            return
        
        # 获取选中行的索引（从后往前删除，避免索引变化）
        selected_indices = []
        for item in selected_items:
            index = self.calibration_tree.index(item)
            selected_indices.append(index)
        
        # 按索引从大到小排序，从后往前删除
        selected_indices.sort(reverse=True)
        
        # 从数据列表中删除对应的数据
        for index in selected_indices:
            if 0 <= index < len(self.calibration_data):
                deleted_data = self.calibration_data.pop(index)
                print(f"删除传感器定标数据: Im={deleted_data['current']}mA, U={deleted_data['voltage']}mV")
        
        # 确保数据保持排序
        self.sort_calibration_data()
        
        # 更新表格和图表
        self.update_calibration_table()
        self.update_plot(self.step_var.get())
        
        messagebox.showinfo("信息", f"已删除 {len(selected_items)} 行数据")

    def delete_selected_measurement_row(self):
        """删除选中的磁场分布测量数据行"""
        selected_items = self.measurement_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的数据行")
            return
        
        # 确认删除
        result = messagebox.askyesno("确认删除", "确定要删除选中的数据行吗？此操作不可撤销！")
        if not result:
            return
        
        # 获取选中行的位置信息（用于确认）
        positions_to_delete = []
        for item in selected_items:
            values = self.measurement_tree.item(item, 'values')
            if values:
                positions_to_delete.append(values[0])  # 位置信息在第一个列
        
        # 从数据列表中删除对应的数据
        deleted_count = 0
        for position in positions_to_delete:
            # 找到对应位置的数据并删除
            for i, data in enumerate(self.measurement_data):
                if abs(data['position'] - float(position)) < 0.01:  # 使用小的容差值
                    deleted_data = self.measurement_data.pop(i)
                    print(f"删除磁场分布测量数据: X={deleted_data['position']:.2f}cm")
                    deleted_count += 1
                    break
        
        # 更新表格和图表
        self.update_measurement_table()
        self.update_plot(self.step_var.get())
        
        messagebox.showinfo("信息", f"已删除 {deleted_count} 行数据")

    def setup_sensor_calibration_ui(self):
        """设置传感器定标UI"""
        # 清除第三区域和第四区域
        for widget in self.data_frame.winfo_children():
            widget.destroy()
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        
        # 创建左右两个框架
        left_frame = tk.Frame(self.data_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_frame = tk.Frame(self.data_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # 左侧：数据表格 - 只创建一次
        columns = ("current", "voltage")
        self.calibration_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=10,
                                        selectmode="extended")  # 支持多选
        self.calibration_tree.heading("current", text="螺线管通电电流 Im (mA)")
        self.calibration_tree.heading("voltage", text="霍尔电势差 U (mV)")
        self.calibration_tree.column("current", width=150)
        self.calibration_tree.column("voltage", width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.calibration_tree.yview)
        self.calibration_tree.configure(yscrollcommand=scrollbar.set)
        
        self.calibration_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 添加右键菜单
        self.calibration_tree_menu = tk.Menu(self.calibration_tree, tearoff=0)
        self.calibration_tree_menu.add_command(label="删除选中行", command=self.delete_selected_calibration_row)
        
        # 绑定右键点击事件
        self.calibration_tree.bind("<Button-3>", self.on_calibration_tree_right_click)
        
        # 填充数据
        self.update_calibration_table()
        
        # 右侧：参数输入
        params = [
            ("螺线管长度L（mm）:", "L", "260"),
            ("线圈匝数N:", "N", "3000"),
            ("平均直径D（mm）:", "D", "35"),
            ("真空磁导率μ₀（H/m）:", "mu0", f"{4 * 3.1415926 * 10**-7}"),
            ("曲线斜率k:", "k", ""),
            ("灵敏度K:", "K", "")
        ]
        
        self.calibration_entries = {}
        for i, (label, key, default) in enumerate(params):
            frame = tk.Frame(right_frame)
            frame.pack(fill=tk.X, pady=2)
            
            tk.Label(frame, text=label, width=20, anchor=tk.W).pack(side=tk.LEFT)
            entry = tk.Entry(frame, width=15)
            
            # 恢复之前的值或使用默认值
            if key in self.calibration_params:
                entry.insert(0, self.calibration_params[key])
            else:
                entry.insert(0, default)
                
            entry.pack(side=tk.RIGHT)
            self.calibration_entries[key] = entry
        
        # 按钮区域
        buttons = [
            ("固定位置刻度", self.fix_position),
            ("记录数据", self.record_calibration_data),
            ("计算", self.calculate_calibration),
            ("删除选中行", self.delete_selected_calibration_row),  # 新增删除按钮
            ("清空数据", self.clear_calibration_data),
            ("导入数据", self.import_calibration_data),  # 新增导入数据按钮
            ("导出数据", self.export_calibration_data)
        ]
        
        for text, command in buttons:
            btn = tk.Button(self.button_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=5)

    def import_calibration_data(self):
        """从Excel或CSV导入传感器定标数据"""
        file_path = filedialog.askopenfilename(
            title="选择传感器定标数据文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 根据文件扩展名选择读取方式
            if file_path.lower().endswith(('.xlsx', '.xls')):
                # 读取Excel文件
                df = pd.read_excel(file_path)
            elif file_path.lower().endswith('.csv'):
                # 读取CSV文件
                df = pd.read_csv(file_path)
            else:
                messagebox.showerror("错误", "不支持的文件格式，请选择Excel(.xlsx/.xls)或CSV(.csv)文件")
                return
            
            # 检查数据列是否符合要求
            required_columns = ['螺线管通电电流 Im (mA)', '霍尔电势差 U (mV)']
            if not all(col in df.columns for col in required_columns):
                # 尝试自动识别列名
                if len(df.columns) >= 2:
                    # 假设第一列是电流，第二列是电压
                    df.columns = ['螺线管通电电流 Im (mA)', '霍尔电势差 U (mV)'] + list(df.columns[2:])
                else:
                    messagebox.showerror("错误", "文件需要包含至少2列数据：螺线管通电电流和霍尔电势差")
                    return
            
            # 清空现有数据
            self.calibration_data = []
            
            # 导入数据
            imported_count = 0
            for index, row in df.iterrows():
                try:
                    current = float(row['螺线管通电电流 Im (mA)']) if pd.notna(row['螺线管通电电流 Im (mA)']) else 0
                    voltage = float(row['霍尔电势差 U (mV)']) if pd.notna(row['霍尔电势差 U (mV)']) else 0
                    
                    # 检查数据有效性
                    if current < 0 or current > 500:  # 电流范围检查
                        print(f"跳过无效电流值: {current}mA")
                        continue
                    
                    self.calibration_data.append({
                        'current': current,
                        'voltage': voltage
                    })
                    imported_count += 1
                    
                except (ValueError, TypeError) as e:
                    print(f"跳过第 {index + 1} 行数据: {e}")
                    continue
            
            # 按电流排序
            self.sort_calibration_data()
            
            # 更新表格和图表
            self.update_calibration_table()
            self.update_plot(self.step_var.get())
            
            # 重置计算标志
            self.calibration_line_plotted = False
            
            messagebox.showinfo("信息", f"成功导入 {imported_count} 条传感器定标数据")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入数据失败: {str(e)}")

    def update_calibration_table(self):
        """更新传感器定标表格数据（已排序）"""
        if self.calibration_tree:
            # 清空现有数据
            for item in self.calibration_tree.get_children():
                self.calibration_tree.delete(item)
            
            # 确保数据已排序
            self.sort_calibration_data()
            
            # 填充新数据
            for data in self.calibration_data:
                self.calibration_tree.insert("", tk.END, values=(data['current'], data['voltage']))
    
    def setup_field_measurement_ui(self):
        """设置磁场分布测量UI"""
        # 清除第三区域和第四区域
        for widget in self.data_frame.winfo_children():
            widget.destroy()
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        
        # 创建左右两个框架
        left_frame = tk.Frame(self.data_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_frame = tk.Frame(self.data_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # 左侧：数据表格
        columns = ("position", "u1", "u2", "u_diff", "field_strength")
        self.measurement_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=10,
                                        selectmode="extended")  # 支持多选
        self.measurement_tree.heading("position", text="位置刻度X (cm)")
        self.measurement_tree.heading("u1", text="正向电压U1 (mV)")
        self.measurement_tree.heading("u2", text="反向电压U2 (mV)")
        self.measurement_tree.heading("u_diff", text="平均电压U (mV)")
        self.measurement_tree.heading("field_strength", text="磁感应强度B (mT)")
        
        for col in columns:
            self.measurement_tree.column(col, width=100)

        # 添加右键菜单
        self.measurement_tree_menu = tk.Menu(self.measurement_tree, tearoff=0)
        self.measurement_tree_menu.add_command(label="删除选中行", command=self.delete_selected_measurement_row)
        
        # 绑定右键点击事件
        self.measurement_tree.bind("<Button-3>", self.on_measurement_tree_right_click)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.measurement_tree.yview)
        self.measurement_tree.configure(yscrollcommand=scrollbar.set)
        
        self.measurement_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充数据
        self.update_measurement_table()
        
        # 右侧：参数显示
        params = [
            ("螺线管长度L（mm）:", "L", "260"),
            ("线圈匝数N:", "N", "3000"),
            ("平均直径D（mm）:", "D", "35"),
            ("真空磁导率μ₀（H/m）:", "mu0", f"{4 * 3.1415926 * 10**-7}"),
            ("灵敏度K:", "K", ""),
            ("磁感应强度理论值B₀ (mT):", "B0", "")
            # ("磁感应强度实测平均值B₀' (mT):", "B0_avg", ""),
            # ("误差:", "error", "")
        ]
        
        self.measurement_entries = {}
        for i, (label, key, default) in enumerate(params):
            frame = tk.Frame(right_frame)
            frame.pack(fill=tk.X, pady=2)
            
            tk.Label(frame, text=label, width=25, anchor=tk.W).pack(side=tk.LEFT)
            entry = tk.Entry(frame, width=15)
            
            # 恢复之前的值或使用默认值
            if key in self.measurement_params:
                entry.insert(0, self.measurement_params[key])
            else:
                entry.insert(0, default)
                
            # 如果是灵敏度K，尝试从传感器定标结果中获取
            if key == "K" and "K" in self.calibration_params:
                entry.delete(0, tk.END)
                entry.insert(0, self.calibration_params["K"])
                
            entry.pack(side=tk.RIGHT)
            self.measurement_entries[key] = entry
        
        # 按钮区域
        if self.current_locked:
            current_btn_text = "解锁电流调节"
            current_btn_command = self.unlock_current
        else:
            current_btn_text = "固定电流调节"
            current_btn_command = self.fix_current
        
        buttons = [
            (current_btn_text, current_btn_command),
            ("记录数据", self.record_measurement_data),
            ("计算", self.calculate_measurement),
            ("删除选中行", self.delete_selected_measurement_row),  # 新增删除按钮
            ("清空数据", self.clear_measurement_data),
            ("导入数据", self.import_measurement_data),  # 新增导入数据按钮
            ("导出数据", self.export_measurement_data)
        ]
        
        for text, command in buttons:
            btn = tk.Button(self.button_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=5)

    def import_measurement_data(self):
        """从Excel或CSV导入磁场分布测量数据"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 根据文件扩展名选择读取方式
            if file_path.lower().endswith(('.xlsx', '.xls')):
                # 读取Excel文件
                df = pd.read_excel(file_path)
            elif file_path.lower().endswith('.csv'):
                # 读取CSV文件
                df = pd.read_csv(file_path)
            else:
                messagebox.showerror("错误", "不支持的文件格式，请选择Excel(.xlsx/.xls)或CSV(.csv)文件")
                return
            
            # 检查列数是否符合要求（至少5列）
            if len(df.columns) < 5:
                messagebox.showerror("错误", "文件需要至少5列数据：位置、正向电压、反向电压、电压差、磁感应强度")
                return
            
            # 清空现有数据
            self.measurement_data = []
            
            # 导入数据
            for index, row in df.iterrows():
                # 取前5列数据
                position = float(row.iloc[0]) if pd.notna(row.iloc[0]) else 0
                u1 = float(row.iloc[1]) if pd.notna(row.iloc[1]) else 0
                u2 = float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0
                u_diff = float(row.iloc[3]) if pd.notna(row.iloc[3]) else abs(u1 - u2)  # 如果没有电压差列，自动计算
                field_strength = float(row.iloc[4]) if pd.notna(row.iloc[4]) else 0
                
                self.measurement_data.append({
                    'position': position,
                    'u1': u1,
                    'u2': u2,
                    'u_diff': u_diff,
                    'field_strength': field_strength
                })
            
            # 更新表格和图表
            self.update_measurement_table()
            self.update_plot(self.step_var.get())
            
            messagebox.showinfo("信息", f"成功导入 {len(self.measurement_data)} 条数据")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入数据失败: {str(e)}")

    def create_measurement_buttons(self):
        """创建磁场分布测量的按钮"""
        # 清除按钮区域的现有内容
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        
        if self.current_locked:
            current_btn_text = "解锁电流调节"
            current_btn_command = self.unlock_current
        else:
            current_btn_text = "固定电流调节"
            current_btn_command = self.fix_current
        
        buttons = [
            (current_btn_text, current_btn_command),
            ("计算", self.calculate_measurement),
            ("记录数据", self.record_measurement_data),
            ("清空数据", self.clear_measurement_data),
            ("导出数据", self.export_measurement_data)
        ]
        
        for text, command in buttons:
            btn = tk.Button(self.button_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=5)

    def update_measurement_table(self):
        """更新磁场分布测量表格数据"""
        if self.measurement_tree:
            # 清空现有数据
            for item in self.measurement_tree.get_children():
                self.measurement_tree.delete(item)
            
            # 按位置排序数据
            sorted_data = sorted(self.measurement_data, key=lambda x: x['position'])
            
            # 填充新数据
            for data in sorted_data:
                self.measurement_tree.insert("", tk.END, values=(
                    f"{data['position']:.2f}",  # 位置保留2位小数
                    f"{data['u1']:.1f}",        # 电压保留1位小数
                    f"{data['u2']:.1f}",        # 电压保留1位小数
                    f"{data['u_diff']:.1f}",    # 电压差保留1位小数
                    f"{data['field_strength']:.3f}"  # 磁感应强度保留3位小数
                ))
    
    def fix_position(self):
        """固定位置刻度"""
        # 检查位置是否在8到23范围内
        if not (8 <= self.sensor_x_pos <= 23):
            messagebox.showerror("错误", f"位置刻度必须在8到23cm范围内，当前位置: {(round(self.sensor_x_pos * 20) / 20):.2f}cm")
            return
        self.position_locked = True
        # 禁用移动按钮
        self.enable_movement_buttons(False)
        # 新增：禁用重置按钮
        self.enable_reset_button(False)
        # 更新按钮文本
        for widget in self.button_frame.winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") == "固定位置刻度":
                widget.config(text="解锁位置刻度", command=self.unlock_position)
        messagebox.showinfo("信息", "位置刻度已固定，传感器移动已禁用")
        
        # 更新曲线标题
        self.update_plot(self.step_var.get())

    def calculate_calibration(self):
        """计算传感器定标参数"""
        try:
            # 保存当前参数值
            for key, entry in self.calibration_entries.items():
                self.calibration_params[key] = entry.get()
            
            # 获取输入参数
            L = float(self.calibration_entries["L"].get())
            N = float(self.calibration_entries["N"].get())
            D = float(self.calibration_entries["D"].get())
            mu0 = float(self.calibration_entries["mu0"].get())
            
            # 计算曲线斜率k
            if self.calibration_data:
                # 确保数据已排序
                self.sort_calibration_data()
                
                currents = [d['current'] for d in self.calibration_data]
                voltages = [d['voltage'] for d in self.calibration_data]
                
                # 简单线性拟合计算斜率
                if len(currents) > 1:
                    k = np.polyfit(currents, voltages, 1)[0]
                    self.calibration_entries["k"].delete(0, tk.END)
                    self.calibration_entries["k"].insert(0, f"{k:.6f}")
                    self.calibration_params["k"] = f"{k:.6f}"
                    
                    # 计算灵敏度K = sqrt(L² + D²) / (μ₀ * N * k)
                    K = np.sqrt(L**2 + D**2) / (mu0 * N) * k / 1000
                    self.calibration_entries["K"].delete(0, tk.END)
                    self.calibration_entries["K"].insert(0, f"{K:.6f}")
                    self.calibration_params["K"] = f"{K:.6f}"
                    
                    # 设置标志，表示已经计算并可以绘制连线
                    self.calibration_line_plotted = True
                    
                    # 更新图表显示连线
                    self.update_plot(self.step_var.get())
                else:
                    messagebox.showwarning("警告", "至少需要2个数据点才能计算斜率")
            else:
                messagebox.showwarning("警告", "没有数据可用于计算")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值")

    def record_calibration_data(self):
        """记录传感器定标数据，如果电流重复则覆盖之前的数据"""
        # 检查位置是否已固定
        if not self.position_locked:
            messagebox.showerror("错误", "请先固定位置刻度后再记录数据")
            return
        current = self.current_knob_value
        voltage = float(self.voltage_text)
        
        # 检查该电流是否已经存在
        existing_index = -1
        for i, data in enumerate(self.calibration_data):
            if abs(data['current'] - current) < 0.01:  # 使用小的容差值比较浮点数
                existing_index = i
                break
        
        if existing_index >= 0:
            # 如果该电流已有记录，更新电压值
            old_voltage = self.calibration_data[existing_index]['voltage']
            self.calibration_data[existing_index]['voltage'] = voltage
            messagebox.showinfo("信息", f"已更新电流 {current}mA 的数据: U={old_voltage}mV → {voltage}mV")
        else:
            # 如果该电流没有记录，添加新记录
            self.calibration_data.append({
                'current': current,
                'voltage': voltage
            })
            messagebox.showinfo("信息", f"已记录新数据: Im={current}mA, U={voltage}mV")
        
        # 按电流从小到大排序
        self.sort_calibration_data()
        
        # 更新表格和图表
        self.update_calibration_table()
        self.update_plot(self.step_var.get())

    def sort_calibration_data(self):
        """按电流从小到大排序传感器定标数据"""
        self.calibration_data.sort(key=lambda x: x['current'])
    
    def clear_calibration_data(self):
        """清空传感器定标数据（带确认）"""
        # 添加确认对话框
        if not self.calibration_data:
            messagebox.showinfo("信息", "当前没有数据需要清空")
            return
        
        result = messagebox.askyesno("确认清空", "确定要清空所有传感器定标数据吗？此操作不可撤销！")
        if not result:
            return
        
        self.calibration_data = []
        self.calibration_line_plotted = False  # 重置连线标志

        # 清空曲线斜率和灵敏度
        if hasattr(self, 'calibration_entries') and 'k' in self.calibration_entries:
            self.calibration_entries['k'].delete(0, tk.END)
        if hasattr(self, 'calibration_entries') and 'K' in self.calibration_entries:
            self.calibration_entries['K'].delete(0, tk.END)
        
        # 同时清空参数字典中的值
        self.calibration_params.pop('k', None)
        self.calibration_params.pop('K', None)

        # 更新表格和图表
        self.update_calibration_table()
        self.update_plot(self.step_var.get())
        messagebox.showinfo("信息", "已清空所有传感器定标数据")
    
    def export_calibration_data(self):
        """导出传感器定标数据"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            title="导出传感器定标数据"
        )
        
        if file_path:
            try:
                df = pd.DataFrame(self.calibration_data)
                df = df.rename(columns={
                    'current': '螺线管通电电流 Im (mA)',
                    'voltage': '霍尔电势差 U (mV)'
                })
                
                # 根据文件扩展名选择保存格式
                if file_path.lower().endswith(('.xlsx', '.xls')):
                    df.to_excel(file_path, index=False)
                else:
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')  # 使用utf-8-sig支持中文
                
                messagebox.showinfo("信息", f"数据已导出到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def calculate_measurement(self):
        """计算磁场分布测量参数"""
        try:
            if self.measurement_data:
                # 设置计算标志，用于绘制连线
                self.measurement_calculated = True
                
                # 计算平均值等统计量
                field_strengths = [d['field_strength'] for d in self.measurement_data]
                avg_field_strength = np.mean(field_strengths) if field_strengths else 0
                
                # 理论磁感应强度 B0 = μ₀ * N * I / sqrt(L² + D²)
                if all(key in self.calibration_params for key in ['L', 'N', 'mu0', 'D']):
                    try:
                        L = float(self.calibration_params['L']) / 1000  # 转换为米
                        D = float(self.calibration_params['D']) / 1000  # 转换为米
                        N = float(self.calibration_params['N'])
                        mu0 = float(self.calibration_params['mu0'])
                        I = self.current_knob_value / 1000  # 转换为安培
                        
                        # 修改计算逻辑：使用 sqrt(L² + D²) 代替 L
                        theoretical_value = (mu0 * N * I) / np.sqrt(L**2 + D**2) * 1000  # 转换为mT
                        print(f'L: {L}, D: {D}, N: {N}, mu0: {mu0}, I: {I}, theoretical_value: {theoretical_value}')
                    except ValueError:
                        theoretical_value = avg_field_strength * 1.1  # 备用计算
                else:
                    theoretical_value = avg_field_strength * 1.1  # 示例计算
                
                # 更新UI
                if 'B0' in self.measurement_entries:
                    self.measurement_entries['B0'].delete(0, tk.END)
                    self.measurement_entries['B0'].insert(0, f"{theoretical_value:.3f}")
                
                if 'B0_avg' in self.measurement_entries:
                    self.measurement_entries['B0_avg'].delete(0, tk.END)
                    self.measurement_entries['B0_avg'].insert(0, f"{avg_field_strength:.3f}")
                
                # 计算误差
                error = abs(theoretical_value - avg_field_strength) / theoretical_value * 100 if theoretical_value != 0 else 0
                if 'error' in self.measurement_entries:
                    self.measurement_entries['error'].delete(0, tk.END)
                    self.measurement_entries['error'].insert(0, f"{error:.2f}%")
                
                # 更新图表显示连线
                self.update_plot(self.step_var.get())
                
                # messagebox.showinfo("信息", f"计算完成！\n理论值: {theoretical_value:.3f} mT\n平均值: {avg_field_strength:.3f} mT\n误差: {error:.2f}%")
            else:
                messagebox.showwarning("警告", "没有数据可用于计算")
        except Exception as e:
            messagebox.showerror("错误", f"计算失败: {str(e)}")
    
    def record_measurement_data(self):
        """记录磁场分布测量数据"""
        # 检查电流是否已固定
        if not self.current_locked:
            messagebox.showerror("错误", "请先固定电流后再记录数据")
            return
        position = round(self.sensor_x_pos * 20) / 20  # 四舍五入到0.05的倍数
        current_voltage = float(self.voltage_text)
        direction = self.direction_var.get()
        
        # 检查该位置是否已经记录过数据
        existing_index = -1
        for i, data in enumerate(self.measurement_data):
            if abs(data['position'] - position) < 0.01:  # 使用小的容差值比较浮点数
                existing_index = i
                break
        
        if existing_index >= 0:
            # 如果该位置已有记录，更新对应方向的电压值
            if direction == "正向":
                self.measurement_data[existing_index]['u1'] = current_voltage
            else:  # 反向
                self.measurement_data[existing_index]['u2'] = current_voltage
            
            # 重新计算平均电压和磁感应强度
            existing_data = self.measurement_data[existing_index]
            u_diff = abs(existing_data['u1'] - existing_data['u2'])/2
            
            # 获取灵敏度K（从定标结果）
            K = 1.0  # 默认值
            if hasattr(self, 'measurement_entries') and 'K' in self.measurement_entries:
                try:
                    K = float(self.measurement_entries['K'].get())
                except ValueError:
                    pass
            
            # 计算磁感应强度 B = U / K
            field_strength = u_diff / K if K != 0 else 0
            
            # 更新数据
            self.measurement_data[existing_index]['u_diff'] = u_diff
            self.measurement_data[existing_index]['field_strength'] = field_strength
            
            messagebox.showinfo("信息", f"已更新位置 X={position:.2f}cm 的{direction}电压数据")
        else:
            # 如果该位置没有记录，创建新记录
            if direction == "正向":
                u1 = current_voltage
                u2 = 0
            else:  # 反向
                u1 = 0
                u2 = current_voltage
            
            u_diff = abs(u1 - u2)
            
            # 获取灵敏度K（从定标结果）
            K = 1.0  # 默认值
            if hasattr(self, 'measurement_entries') and 'K' in self.measurement_entries:
                try:
                    K = float(self.measurement_entries['K'].get())
                except ValueError:
                    pass
            
            # 计算磁感应强度 B = U / K
            field_strength = u_diff / K if K != 0 else 0
            
            self.measurement_data.append({
                'position': position,
                'u1': u1,
                'u2': u2,
                'u_diff': u_diff,
                'field_strength': field_strength
            })
            
            messagebox.showinfo("信息", f"已记录新位置 X={position:.2f}cm 的{direction}电压数据")
        
        # 更新表格和图表
        self.update_measurement_table()
        self.update_plot(self.step_var.get())

    def clear_measurement_data(self):
        """清空磁场分布测量数据（带确认）"""
        # 添加确认对话框
        if not self.measurement_data:
            messagebox.showinfo("信息", "当前没有数据需要清空")
            return
        
        result = messagebox.askyesno("确认清空", "确定要清空所有磁场分布测量数据吗？此操作不可撤销！")
        if not result:
            return
        
        self.measurement_data = []
        self.measurement_calculated = False  # 重置计算标志
        # 只更新表格数据，不重新创建UI
        self.update_measurement_table()
        self.update_plot(self.step_var.get())
        messagebox.showinfo("信息", "已清空所有磁场分布测量数据")
    
    def export_measurement_data(self):
        """导出磁场分布测量数据"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                # 创建DataFrame并重命名列
                df = pd.DataFrame(self.measurement_data)
                df = df.rename(columns={
                    'position': '位置刻度X (cm)',
                    'u1': '正向电压U1 (mV)',
                    'u2': '反向电压U2 (mV)',
                    'u_diff': '平均电压U (mV)',
                    'field_strength': '磁感应强度B (mT)'
                })
                
                # 根据文件扩展名选择保存格式
                if file_path.lower().endswith(('.xlsx', '.xls')):
                    df.to_excel(file_path, index=False)
                else:
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')  # 使用utf-8-sig支持中文
                
                messagebox.showinfo("信息", f"数据已导出到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def load_excel_data(self):
        """加载Excel数据文件（改进版）"""
        excel_path = self.get_data_path(self.excel_filename)
        print(f"尝试加载Excel文件: {excel_path}")
        
        if not os.path.exists(excel_path):
            print(f"Excel文件不存在: {excel_path}")
            messagebox.showwarning("警告", f"找不到Excel文件: {self.excel_filename}\n请将文件放在 {self.data_dir} 目录下")
            return
        
        try:
            self.excel_data = pd.read_excel(excel_path)
            # 给Excel数据整体添加0.5%的随机波动
            for col in self.excel_data.columns[1:]:
                self.excel_data[col] = self.excel_data[col] * self.excel_random_factor
            print("Excel文件加载成功，并添加了0.5%的整体随机波动")
        except Exception as e:
            print(f"加载Excel文件失败: {str(e)}")
            messagebox.showerror("错误", f"加载Excel文件失败: {str(e)}")
    
    def get_voltage_from_position(self, position, direction):
        """根据传感器位置和方向获取对应的电压值（使用线性插值）"""
        if self.excel_data is None or len(self.excel_data) == 0:
            return 0.0
        
        try:
            # 获取位置列数据
            positions = self.excel_data.iloc[:, 0].values
            
            # 找到最接近的两个位置点
            diffs = np.abs(positions - position)
            sorted_indices = np.argsort(diffs)
            
            # 获取两个最接近的点
            idx1 = sorted_indices[0]
            idx2 = sorted_indices[1]
            
            # 确保idx1 < idx2（位置从小到大）
            if positions[idx1] > positions[idx2]:
                idx1, idx2 = idx2, idx1
            
            pos1 = positions[idx1]
            pos2 = positions[idx2]
            
            if direction == "正向":
                voltage1 = self.excel_data.iloc[idx1, 1]  # 第二列
                voltage2 = self.excel_data.iloc[idx2, 1]  # 第二列
            else:  # 反向
                voltage1 = self.excel_data.iloc[idx1, 2]  # 第三列
                voltage2 = self.excel_data.iloc[idx2, 2]  # 第三列
            
            # 线性插值计算基础电压
            if pos1 == pos2:
                base_voltage = voltage1
            else:
                # 线性插值公式: y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                base_voltage = voltage1 + (voltage2 - voltage1) * (position - pos1) / (pos2 - pos1)
            
            # 计算基础电压：Excel电压 × 电流旋钮值/250 + 电压旋钮值 + 随机初始偏移
            base_calculated_voltage = base_voltage * (self.current_knob_value / 250) + self.voltage_knob_value + self.random_voltage_offset
            
            # 给最终结果添加0.2%的随机波动
            final_random_factor = 1 + random.uniform(-0.002, 0.002)
            final_voltage = base_calculated_voltage * final_random_factor
            
            print(f"传感器位置: {position:.2f}, 插值位置: {pos1:.2f}-{pos2:.2f}, 方向: {direction}")
            print(f"插值电压: {voltage1:.1f}-{voltage2:.1f}, 基础电压: {base_voltage:.1f}")
            print(f"电流旋钮: {self.current_knob_value}, 电压旋钮: {self.voltage_knob_value:.1f}")
            print(f"随机偏移: {self.random_voltage_offset:.1f}, 基础计算电压: {base_calculated_voltage:.1f}")
            print(f"最终随机因子: {final_random_factor:.4f}, 最终电压: {final_voltage:.1f}")
            
            return final_voltage
        except Exception as e:
            print(f"获取电压值失败: {str(e)}")
            return 0.0
    
    def set_voltage(self, voltage):
        """设置电压值"""
        self.voltage_text = f"{voltage:.1f}"  # 显示3位小数
        self.update_canvas()
        print(f"电压已设置为: {voltage:.1f} V")

    def set_current(self, current):
        """设置电流值"""
        self.current_text = f"{current}"
        self.update_canvas()
        print(f"电流已设置为: {current}A")
    
    def set_current_knob(self, value):
        """设置电流旋钮值"""
        self.current_knob_value = float(value)
        # 电流旋钮改变时更新电压显示
        self.update_voltage_from_position()
        print(f"电流旋钮已设置为: {value}")
    
    def set_voltage_knob(self, value):
        """设置电压旋钮值"""
        self.voltage_knob_value = float(value)
        # 电压旋钮改变时更新电压显示
        self.update_voltage_from_position()
        print(f"电压旋钮已设置为: {value}")
    
    def set_direction(self, direction):
        """设置换向开关方向"""
        self.direction_var.set(direction)
        # 方向改变时更新电压显示
        self.update_voltage_from_position()
        # 更新箭头方向
        self.update_arrow_direction()
        print(f"换向开关已设置为: {direction}")
    
    def update_voltage_from_position(self):
        """根据当前传感器位置和方向更新电压显示"""
        if self.excel_data is not None:
            voltage = self.get_voltage_from_position(self.sensor_x_pos, self.direction_var.get())
            self.set_voltage(voltage)

    def print_debug_info(self):
        """打印调试信息"""
        print(f"程序所在目录: {self.program_dir}")
        print(f"数据目录: {self.data_dir}")
        print("数据目录中的文件列表:")
        if os.path.exists(self.data_dir):
            for file in os.listdir(self.data_dir):
                print(f"  {file}")
        else:
            print("  数据目录不存在")
        print(f"寻找的文件: {self.bottom_filename}, {self.middle_filename}, {self.top_filename}, {self.excel_filename}")
        
        # 检查文件是否存在
        for filename in [self.bottom_filename, self.middle_filename, self.top_filename, self.excel_filename]:
            file_path = os.path.join(self.data_dir, filename)
            exists = os.path.exists(file_path)
            print(f"{filename} 存在: {exists}")
            if exists:
                print(f"  {filename} 完整路径: {file_path}")
    
    def create_widgets(self):
        # 创建主框架，包含画布和控制面板
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)  # 减小边距
        
        # 创建画布
        self.canvas = tk.Canvas(main_frame, bg="lightgray", width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(side=tk.LEFT, padx=(0, 5))  # 减小右边距
        
        # 创建右侧控制面板 - 使用更小的尺寸
        control_frame = tk.Frame(main_frame, width=200)  # 固定宽度
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        control_frame.pack_propagate(False)  # 防止内部控件改变框架大小
        
        # 使用更小的字体
        small_font = ("Arial", 9)
        small_bold_font = ("Arial", 9, "bold")
        
        # 方向控制按钮 - 使用更小的按钮
        tk.Label(control_frame, text="移动传感器:", fg="blue", font=small_bold_font).pack(anchor=tk.W, pady=(5, 2))
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(pady=3)
        
        # 更小的按钮
        self.left_btn = tk.Button(btn_frame, text="←左移", width=6, font=small_font, height=1)
        self.left_btn.grid(row=0, column=0, padx=2, pady=1)
        self.left_btn.bind("<ButtonPress-1>", self.on_left_press)
        self.left_btn.bind("<ButtonRelease-1>", self.on_left_release)
        
        self.right_btn = tk.Button(btn_frame, text="右移→", width=6, font=small_font, height=1)
        self.right_btn.grid(row=0, column=2, padx=2, pady=1)
        self.right_btn.bind("<ButtonPress-1>", self.on_right_press)
        self.right_btn.bind("<ButtonRelease-1>", self.on_right_release)
        
        self.reset_btn = tk.Button(btn_frame, text="重置", width=6, command=self.reset_position, font=small_font, height=1)
        self.reset_btn.grid(row=0, column=1, padx=2, pady=1)
        
       # 替换原来的步长设置代码（step_frame部分）
        step_frame = tk.Frame(control_frame)
        step_frame.pack(pady=3, fill=tk.X)

        tk.Label(step_frame, text="移动倍率:", font=small_font).pack(anchor=tk.W)  # 添加"移动倍率："文本
        step_inner_frame = tk.Frame(step_frame)
        step_inner_frame.pack(fill=tk.X, pady=1)

        # 使用Combobox代替Entry
        self.move_step_var = tk.StringVar(value=str(self.move_step))
        step_combo = ttk.Combobox(step_frame, textvariable=self.move_step_var, 
                                values=["1", "5", "20"], width=5, font=small_font, state="readonly")
        step_combo.pack(side=tk.LEFT, padx=(0, 3))
        step_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_step())
        
        # 旋钮控制区域 - 更小的滑块
        knob_frame = tk.Frame(control_frame)
        knob_frame.pack(pady=3, fill=tk.X)
        
        tk.Label(knob_frame, text="旋钮调节:", fg="green", font=small_bold_font).pack(anchor=tk.W)
        
        # 电流旋钮控制 - 更小的滑块
        current_knob_frame = tk.Frame(knob_frame)
        current_knob_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(current_knob_frame, text="点击灰色区域细调\n电流调节 (0 - 500):", font=small_font).pack(anchor=tk.W)
        self.current_knob_var = tk.DoubleVar(value=self.current_knob_value)
        self.current_scale = tk.Scale(current_knob_frame, from_=0, to=500, orient=tk.HORIZONTAL,  # 保存引用
                                variable=self.current_knob_var, command=self.on_current_knob_change,
                                length=150, showvalue=True, resolution=1,  # 减小长度
                                sliderlength=15, font=small_font)  # 减小滑块长度
        self.current_scale.pack(fill=tk.X)
        
        # 电压旋钮控制 - 更小的滑块
        voltage_knob_frame = tk.Frame(knob_frame)
        voltage_knob_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(voltage_knob_frame, text="霍尔电压调零 (-10 -10):", font=small_font).pack(anchor=tk.W)
        self.voltage_knob_var = tk.DoubleVar(value=self.voltage_knob_value)
        voltage_scale = tk.Scale(voltage_knob_frame, from_=-10, to=10, orient=tk.HORIZONTAL,
                            variable=self.voltage_knob_var, command=self.on_voltage_knob_change,
                            length=150, showvalue=True, resolution=0.1,  # 减小长度
                            sliderlength=15, font=small_font)  # 减小滑块长度
        voltage_scale.pack(fill=tk.X)
        
        # 换向开关区域 - 更小的单选按钮
        direction_frame = tk.Frame(control_frame)
        direction_frame.pack(pady=3, fill=tk.X)
        
        tk.Label(direction_frame, text="换向开关:", fg="purple", font=small_bold_font).pack(anchor=tk.W)
        
        direction_btn_frame = tk.Frame(direction_frame)
        direction_btn_frame.pack(fill=tk.X, pady=1)
        
        # 更小的单选按钮
        forward_btn = tk.Radiobutton(direction_btn_frame, text="正向", variable=self.direction_var, 
                                value="正向", command=lambda: self.set_direction("正向"),
                                font=small_font)
        forward_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        reverse_btn = tk.Radiobutton(direction_btn_frame, text="反向", variable=self.direction_var, 
                                value="反向", command=lambda: self.set_direction("反向"),
                                font=small_font)
        reverse_btn.pack(side=tk.LEFT)
        
        # 状态标签 - 使用更小的字体
        self.status_label = tk.Label(self.root, text="正在加载图片...", bd=1, relief=tk.SUNKEN, 
                                anchor=tk.W, font=small_font)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)
    
    def enable_reset_button(self, enabled):
        """启用或禁用重置按钮"""
        if hasattr(self, 'reset_btn'):
            state = tk.NORMAL if enabled else tk.DISABLED
            self.reset_btn.config(state=state)

    def on_left_press(self, event):
        """左移按钮按下事件"""
        self.left_pressed = True
        self.move_left()  # 立即移动一次
        # 设置定时器用于连续移动
        self.root.after(self.repeat_delay, self.repeat_left_move)
    
    def on_left_release(self, event):
        """左移按钮释放事件"""
        self.left_pressed = False
    
    def on_right_press(self, event):
        """右移按钮按下事件"""
        self.right_pressed = True
        self.move_right()  # 立即移动一次
        # 设置定时器用于连续移动
        self.root.after(self.repeat_delay, self.repeat_right_move)
    
    def on_right_release(self, event):
        """右移按钮释放事件"""
        self.right_pressed = False
    
    def repeat_left_move(self):
        """重复左移"""
        if self.left_pressed:
            self.move_left()
            self.root.after(self.repeat_interval, self.repeat_left_move)
    
    def repeat_right_move(self):
        """重复右移"""
        if self.right_pressed:
            self.move_right()
            self.root.after(self.repeat_interval, self.repeat_right_move)
    
    def on_current_knob_change(self, value):
        """电流旋钮变化回调"""
        self.set_current_knob(value)
        self.set_current(value)
    
    def on_voltage_knob_change(self, value):
        """电压旋钮变化回调"""
        self.set_voltage_knob(value)
    
    def load_single_image(self, layer, file_path):
        """加载单个图片"""
        try:
            print(f"尝试加载 {layer} 图片: {file_path}")
            image = Image.open(file_path)
            
            if layer == "bottom":
                self.scale_ratio = self.calculate_scale_ratio(image)
                self.bottom_image = self.resize_image(image, self.scale_ratio)
                self.bottom_photo = ImageTk.PhotoImage(self.bottom_image)
                self.status_label.config(text=f"已加载底层: {os.path.basename(file_path)}")
                print(f"底层图片加载成功，尺寸: {self.bottom_image.size}")
                
            elif layer == "middle":
                self.middle_image = self.resize_image(image, self.scale_ratio)
                self.middle_photo = ImageTk.PhotoImage(self.middle_image)
                self.middle_x_pos = 0
                self.middle_y_pos = 0
                self.status_label.config(text=f"已加载中间层: {os.path.basename(file_path)}")
                self.enable_movement_buttons(True)
                print(f"中间层图片加载成功，尺寸: {self.middle_image.size}")
                
            elif layer == "top":
                self.top_image = self.resize_image(image, self.scale_ratio)
                self.top_photo = ImageTk.PhotoImage(self.top_image)
                self.status_label.config(text=f"已加载顶层: {os.path.basename(file_path)}")
                print(f"顶层图片加载成功，尺寸: {self.top_image.size}")
            
            self.update_canvas()
            
        except Exception as e:
            error_msg = f"加载{layer}图片失败: {str(e)}"
            print(error_msg)
            self.status_label.config(text=error_msg)
            messagebox.showerror("错误", error_msg)
    
    def auto_load_images(self):
        """自动从数据目录加载图片（改进版）"""
        print("开始自动加载图片...")
        success_count = 0
        
        # 获取文件路径
        bottom_path = self.get_data_path(self.bottom_filename)
        middle_path = self.get_data_path(self.middle_filename)
        top_path = self.get_data_path(self.top_filename)
        
        print(f"底层图片路径: {bottom_path}")
        print(f"中间层图片路径: {middle_path}")
        print(f"顶层图片路径: {top_path}")
        
        # 检查文件是否存在
        for path, filename in [(bottom_path, self.bottom_filename), 
                              (middle_path, self.middle_filename), 
                              (top_path, self.top_filename)]:
            if not os.path.exists(path):
                print(f"找不到文件: {path}")
                self.status_label.config(text=f"找不到文件: {filename}")
        
        # 加载底层图片
        if os.path.exists(bottom_path):
            try:
                print(f"加载底层图片: {bottom_path}")
                image = Image.open(bottom_path)
                self.scale_ratio = self.calculate_scale_ratio(image)
                self.bottom_image = self.resize_image(image, self.scale_ratio)
                self.bottom_photo = ImageTk.PhotoImage(self.bottom_image)
                success_count += 1
                self.status_label.config(text=f"已加载底层: {self.bottom_filename}")
                print(f"底层图片加载成功，尺寸: {self.bottom_image.size}")
            except Exception as e:
                error_msg = f"加载底层图片失败: {str(e)}"
                print(error_msg)
                self.status_label.config(text=error_msg)
        else:
            error_msg = f"找不到底层图片: {bottom_path}"
            print(error_msg)
            self.status_label.config(text=error_msg)
        
        # 加载中间层图片
        if os.path.exists(middle_path):
            try:
                print(f"加载中间层图片: {middle_path}")
                image = Image.open(middle_path)
                self.middle_image = self.resize_image(image, self.scale_ratio)
                self.middle_photo = ImageTk.PhotoImage(self.middle_image)
                self.middle_x_pos = 0
                self.middle_y_pos = 0
                success_count += 1
                self.status_label.config(text=f"已加载中间层: {self.middle_filename}")
                self.enable_movement_buttons(True)
                print(f"中间层图片加载成功，尺寸: {self.middle_image.size}")
            except Exception as e:
                error_msg = f"加载中间层图片失败: {str(e)}"
                print(error_msg)
                self.status_label.config(text=error_msg)
        else:
            error_msg = f"找不到中间层图片: {middle_path}"
            print(error_msg)
            self.status_label.config(text=error_msg)
        
        # 加载顶层图片
        if os.path.exists(top_path):
            try:
                print(f"加载顶层图片: {top_path}")
                image = Image.open(top_path)
                self.top_image = self.resize_image(image, self.scale_ratio)
                self.top_photo = ImageTk.PhotoImage(self.top_image)
                success_count += 1
                self.status_label.config(text=f"已加载顶层: {self.top_filename}")
                print(f"顶层图片加载成功，尺寸: {self.top_image.size}")
            except Exception as e:
                error_msg = f"加载顶层图片失败: {str(e)}"
                print(error_msg)
                self.status_label.config(text=error_msg)
        else:
            error_msg = f"找不到顶层图片: {top_path}"
            print(error_msg)
            self.status_label.config(text=error_msg)
        
        # 更新画布
        self.update_canvas()
        
        # 显示加载结果
        if success_count == 3:
            final_msg = f"成功加载所有图片! 缩放比例: {int(self.scale_ratio * 100)}%"
        else:
            final_msg = f"加载完成 (成功: {success_count}/3)"
        
        print(final_msg)
        self.status_label.config(text=final_msg)
    
    def calculate_scale_ratio(self, image):
        """计算图片缩放比例以适应画布"""
        img_width, img_height = image.size
        canvas_width, canvas_height = self.canvas_width, self.canvas_height
        
        print(f"原始图片尺寸: {img_width}x{img_height}")
        print(f"画布尺寸: {canvas_width}x{canvas_height}")
        
        # 计算缩放比例
        width_ratio = canvas_width / img_width
        height_ratio = canvas_height / img_height
        scale_ratio = min(width_ratio, height_ratio)
        
        print(f"计算出的缩放比例: {scale_ratio:.2f} ({int(scale_ratio * 100)}%)")
        return scale_ratio
    
    def resize_image(self, image, scale_ratio):
        """按比例缩放图片"""
        if scale_ratio >= 1.0:  # 如果图片比画布小，不进行放大
            print(f"图片较小，不进行放大 (比例: {scale_ratio:.2f})")
            return image
        
        new_width = int(image.width * scale_ratio)
        new_height = int(image.height * scale_ratio)
        print(f"缩放图片: {image.width}x{image.height} -> {new_width}x{new_height}")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def update_canvas(self):
        # 清除画布
        self.canvas.delete("all")
        
        # 计算画布中心
        canvas_center_x = self.canvas_width // 2
        canvas_center_y = self.canvas_height // 2
        
        # 绘制底层（居中显示）
        if self.bottom_photo:
            bottom_img_width, bottom_img_height = self.bottom_image.size
            bottom_x = (self.canvas_width - bottom_img_width) // 2
            bottom_y = (self.canvas_height - bottom_img_height) // 2
            self.canvas.create_image(bottom_x, bottom_y, anchor=tk.NW, image=self.bottom_photo)
        
        # 绘制中间层（可移动，居中开始）
        if self.middle_photo:
            middle_img_width, middle_img_height = self.middle_image.size
            middle_x = canvas_center_x - middle_img_width // 2 + self.middle_x_pos+(28*30+8)*self.scale_factor
            middle_y = canvas_center_y - middle_img_height // 2 + self.middle_y_pos-170*self.scale_factor
            self.canvas.create_image(middle_x, middle_y, anchor=tk.NW, image=self.middle_photo)
        
        # 绘制顶层（居中显示）
        if self.top_photo:
            top_img_width, top_img_height = self.top_image.size
            top_x = canvas_center_x - top_img_width // 2-63*self.scale_factor
            top_y = canvas_center_y - top_img_height // 2-170*self.scale_factor
            self.canvas.create_image(top_x, top_y, anchor=tk.NW, image=self.top_photo)
        
        # 绘制红线（在顶层之上）
        self.red_line_id = self.canvas.create_line(
            self.red_line_x, self.red_line_y1, 
            self.red_line_x, self.red_line_y2, 
            fill="red", width=1
        )

        # 绘制电压和电流文本框（在顶层之上）
        if self.top_photo:
            # 计算文本框位置（在顶层图片的右上角）
            top_img_width, top_img_height = self.top_image.size
            top_x = canvas_center_x - top_img_width // 2
            top_y = canvas_center_y - top_img_height // 2
            
            # 电压文本框（显示3位小数）
            self.canvas.create_text(
                top_x + top_img_width - (65+15)*self.scale_factor, top_y + (25 +110)*self.scale_factor,
                text=self.voltage_text,
                fill="blue", font=("Arial", 20, "bold")
            )
            
            # 电流文本框
            self.canvas.create_text(
                top_x + top_img_width - (65+250+10)*self.scale_factor, top_y + (65 +70)*self.scale_factor,
                text=self.current_text,
                fill="red", font=("Arial", 20, "bold")
            )
            
        # 绘制箭头（在顶层之上）
        self.draw_arrow()
        
        # === 新增：在背景图上显示传感器位置 ===
        if self.top_photo:
            # 计算显示传感器位置的位置（在背景图的合适位置）
            top_img_width, top_img_height = self.top_image.size
            canvas_center_x = self.canvas_width // 2
            canvas_center_y = self.canvas_height // 2
            
            # 传感器位置文本 - 放在背景图的左上角或右上角
            # 这里选择放在背景图的右上角，避免覆盖重要信息
            pos_x = canvas_center_x + top_img_width // 2 - 100 * self.scale_factor +120
            pos_y = canvas_center_y - top_img_height // 2 + 30 * self.scale_factor -160
            
            # 显示传感器位置（保留2位小数）
            position_display = f"位置: {self.sensor_x_pos:.2f} cm"
            
            # 创建一个带背景框的文本，使其更清晰可见
            text_id = self.canvas.create_text(
                pos_x, pos_y,
                text=position_display,
                fill="green",  # 使用绿色显示，与电压蓝色、电流红色区分
                font=("Arial", 14, "bold"),
                anchor=tk.E  # 右对齐
            )

        # 如果没有加载任何图片，显示提示信息
        if not any([self.bottom_photo, self.middle_photo, self.top_photo]):
            self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2, 
                                  text="没有加载图片\n请检查图片文件是否存在", 
                                  fill="red", font=("Arial", 16), justify=tk.CENTER)
            
        # 显示中间层位置信息和各层状态
        info_text = f"中间层位置: X={self.middle_x_pos}, Y={self.middle_y_pos}"
        self.sensor_x_pos = 30/1006*(-self.middle_x_pos)/22.46*30*30/30.1
        info_text += f" | 传感器位置: X={self.sensor_x_pos:.2f}"
        info_text += f" | 缩放比例: {int(self.scale_ratio * 100)}%"
        info_text += f" | 电流旋钮: {self.current_knob_value:.0f} | 电压旋钮: {self.voltage_knob_value:.1f}"
        info_text += f" | 换向开关: {self.direction_var.get()}"
        info_text += f" | 随机偏移: {self.random_voltage_offset:.1f} V"
        info_text += f" | Excel随机因子: {self.excel_random_factor:.4f}"
        
        if self.bottom_image:
            info_text += f" | 底层: {self.bottom_image.size}"
        if self.middle_image:
            info_text += f" | 中间层: {self.middle_image.size}"
        if self.top_image:
            info_text += f" | 顶层: {self.top_image.size}"
            
        # self.canvas.create_text(10, 10, text=info_text, anchor=tk.NW, fill="black", 
        #                        font=("Arial", 10), width=self.canvas_width-20)
    
    def draw_arrow(self):
        """绘制箭头，方向根据换向开关状态决定"""
        # 计算箭头位置（在顶层图片的换向开关位置）
        if self.top_photo:
            top_img_width, top_img_height = self.top_image.size
            canvas_center_x = self.canvas_width // 2
            canvas_center_y = self.canvas_height // 2
            
            # 箭头位置（相对于顶层图片）
            arrow_x = canvas_center_x - top_img_width // 2 + 50 * self.scale_ratio +92
            arrow_y = canvas_center_y - top_img_height // 2 + 50 * self.scale_ratio +65
            
            # 清除之前的箭头
            if self.arrow_id:
                self.canvas.delete(self.arrow_id)
            
            # 根据方向绘制箭头
            if self.direction_var.get() == "正向":
                # 向上箭头
                self.arrow_id = self.canvas.create_polygon(
                    arrow_x, arrow_y + 15 * self.scale_ratio,  # 底部左边
                    arrow_x - 10 * self.scale_ratio, arrow_y + 15 * self.scale_ratio,  # 底部左边
                    arrow_x, arrow_y - 15 * self.scale_ratio,  # 顶部
                    arrow_x + 10 * self.scale_ratio, arrow_y + 15 * self.scale_ratio,  # 底部右边
                    arrow_x, arrow_y + 15 * self.scale_ratio,  # 底部左边
                    fill="red", outline="black", width=2
                )
            else:
                # 向下箭头
                self.arrow_id = self.canvas.create_polygon(
                    arrow_x, arrow_y - 15 * self.scale_ratio,  # 顶部左边
                    arrow_x - 10 * self.scale_ratio, arrow_y - 15 * self.scale_ratio,  # 顶部左边
                    arrow_x, arrow_y + 15 * self.scale_ratio,  # 底部
                    arrow_x + 10 * self.scale_ratio, arrow_y - 15 * self.scale_ratio,  # 顶部右边
                    arrow_x, arrow_y - 15 * self.scale_ratio,  # 顶部左边
                    fill="red", outline="black", width=2
                )
    
    def update_arrow_direction(self):
        """更新箭头方向"""
        self.draw_arrow()
    
    def move_left(self):
        """向左移动，限制在有效范围内"""
        if self.position_locked:
            return  # 如果位置已锁定，不执行移动
        new_pos = self.middle_x_pos - self.move_step
        if new_pos >= self.min_x_pos:  # 检查是否超出左边界
            self.middle_x_pos = new_pos
            self.update_canvas()
            # 移动后更新电压显示
            self.update_voltage_from_position()
        else:
            self.middle_x_pos= self.min_x_pos
            self.update_canvas()
            # 移动后更新电压显示
            self.update_voltage_from_position()
            # # 如果超出范围，停止连续移动
            # self.left_pressed = False
            # print("已达到左边界，无法继续左移")
        
    def move_right(self):
        """向右移动，限制在有效范围内"""
        if self.position_locked:
            return  # 如果位置已锁定，不执行移动
        new_pos = self.middle_x_pos + self.move_step
        if new_pos <= self.max_x_pos:  # 检查是否超出右边界
            self.middle_x_pos = new_pos
            self.update_canvas()
            # 移动后更新电压显示
            self.update_voltage_from_position()
        else:
            self.middle_x_pos = self.max_x_pos
            self.update_canvas()
            # 移动后更新电压显示
            self.update_voltage_from_position()
            # 如果超出范围，停止连续移动
            # self.right_pressed = False
            # print("已达到右边界，无法继续右移")
        
    def reset_position(self):
        self.middle_x_pos = 0
        self.middle_y_pos = 0
        self.update_canvas()
        # 重置后更新电压显示
        self.update_voltage_from_position()
        self.status_label.config(text="中间层位置已重置到中心")
    
    def apply_step(self):
        try:
            new_step = int(self.move_step_var.get())
            if new_step in [1, 5, 20]:  # 只允许这三个值
                self.move_step = new_step
                self.status_label.config(text=f"移动步长已设置为: {self.move_step} 像素")
            else:
                messagebox.showwarning("警告", "请从1、5、20中选择步长")
                # 重置为之前的有效值
                self.move_step_var.set(str(self.move_step))
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的步长")
            # 重置为之前的有效值
            self.move_step_var.set(str(self.move_step))
    
    def enable_movement_buttons(self, enabled):
        # 如果位置已锁定，强制禁用按钮
        if self.position_locked:
            state = tk.DISABLED
        else:
            state = tk.NORMAL if enabled else tk.DISABLED
        
        self.left_btn.config(state=state)
        self.right_btn.config(state=state)

if __name__ == "__main__":
    root = tk.Tk()
    app = ThreeLayerImageViewer(root)
    root.mainloop()  