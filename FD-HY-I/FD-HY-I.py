import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import math
import random
from tkinter import filedialog

def get_resource_path(relative_path):
    """获取资源的绝对路径，支持打包后的环境"""
    try:
        # 打包后的临时文件夹路径
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)


class YangsModulusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("弯曲法测量横梁的杨氏模量")
        self.root.geometry("1300x850")  # 加宽窗口
        self.root.resizable(False, False)  # 禁止窗口调整大小
        self.crosshair_pos = 4.0  # 十字线位置 (mm)
        self.knife_edge_pos = 5.0  # 刀口架基线位置 (mm) - 实际显示位置
        self.knife_base_pos = 5.0  # 显微镜基准高度 (mm) - 用户通过进度条控制
        self.knife_offset = 0.0    # 砝码引起的位移偏移量 (mm)
        self.weight_count = 0  # 砝码数量 (0-12)
        self.total_weight = 0  # 总重量 (g)
        self.current_tab = "霍尔位置传感器静态特性测量"
        
        # 数据存储
        self.hall_data = [[0]*6 for _ in range(3)]  # 3行6列
        self.hall_table_entries = []
        
        self.brass_data = [[0]*6 for _ in range(2)]  # 2行6列
        self.brass_table_entries = []
        
        # 样品参数
        self.length = tk.DoubleVar(value=23.0)  # mm
        self.width = tk.DoubleVar(value=2.3)    # mm  
        self.thickness = tk.DoubleVar(value=0.995)  # mm

        # 样品类型
        self.sample_type = "黄铜"  # 可选: "黄铜", "铸铁"
        
        # 调零值
        self.zero_value = tk.IntVar(value=0)
        
        # 初始电压值（随机生成 -100 到 100）
        self.initial_voltage = random.randint(-100, 100)
        self.current_voltage = self.initial_voltage

        # 砝码对应的位移和电压增量（初始化时确定，每个砝码10g）
        # 原来每个砝码20g，现在改为10g，变化量减半
        self.weight_displacements = []  # 每个砝码对应的位移增量 (mm)
        self.weight_voltages = []       # 每个砝码对应的电压增量 (mV)
        for _ in range(12):  # 最多12个砝码 (120g)
            # 原来是0.24-0.26mm，现在减半为0.12-0.13mm
            self.weight_displacements.append(0.124)
            # 原来是71-75mV，现在减半为36-37mV
            self.weight_voltages.append(36.5)

        # 磁铁位置对电压的影响（范围-100到100，步进1mV）
        self.magnet_voltage_offset = 0  # 磁铁引起的电压偏移
        self.magnet_position = 0  # 磁铁当前位置 (-100到100)

        # 显微镜显示参数
        self.microscope_zoom = 1.0  # 放大倍数 (1.0, 2.0, 4.0)
        self.microscope_offset = 4.0  # 显示中心偏移 (mm)
        self.microscope_display_range = 8.0  # 当前显示范围 (mm)
        # 创建四个区域
        self.create_top_left()
        self.create_bottom_left()
        self.create_top_right()
        self.create_bottom_right()
        
        # 初始化画布绘制
        self.draw_microscope()
    
    
    def create_top_left(self):
        """左上区域：读数显微镜区域"""
        frame = tk.Frame(self.root, bg='white', relief=tk.RAISED, bd=2)
        frame.place(x=100, y=10, width=360, height=420)  # 稍微加高
        
        tk.Label(frame, text="读数显微镜", font=("Arial", 12, "bold"), 
                bg='white').pack(pady=5)
        
        # 显微镜画布 (直径300px)
        self.microscope_canvas = tk.Canvas(frame, width=320, height=300, 
                                            bg='lightgray', highlightthickness=1)
        self.microscope_canvas.pack(pady=5)
        
        # 显微镜控制栏
        control_frame = tk.Frame(frame, bg='white')
        control_frame.pack(pady=2)
        
        # # 缩小按钮
        # self.zoom_out_btn = tk.Button(control_frame, text="缩小", 
        #                             command=self.zoom_out,
        #                             font=("Arial", 8), width=4)
        # self.zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        # # 放大倍数显示
        # self.zoom_label = tk.Label(control_frame, text="1.0×", 
        #                             font=("Arial", 9, "bold"), fg='blue', bg='white')
        # self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        # # 放大按钮
        # self.zoom_in_btn = tk.Button(control_frame, text="放大", 
        #                             command=self.zoom_in,
        #                             font=("Arial", 8), width=4)
        # self.zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        # # 分隔
        # tk.Label(control_frame, text="  |  ", bg='white').pack(side=tk.LEFT)
        
        # # 右移按钮（上移）- 长按支持
        # self.move_right_btn = tk.Button(control_frame, text="上移", 
        #                                 command=self.move_right,
        #                                 font=("Arial", 8), width=3)
        # self.move_right_btn.pack(side=tk.LEFT, padx=2)
        # # 绑定长按事件
        # self.move_right_btn.bind("<ButtonPress-1>", lambda e: self.start_repeat(self.move_right,100))
        # self.move_right_btn.bind("<ButtonRelease-1>", lambda e: self.stop_repeat())

        # # 左移按钮（下移）- 长按支持
        # self.move_left_btn = tk.Button(control_frame, text="下移", 
        #                                 command=self.move_left,
        #                                 font=("Arial", 8), width=3)
        # self.move_left_btn.pack(side=tk.LEFT, padx=2)
        # # 绑定长按事件
        # self.move_left_btn.bind("<ButtonPress-1>", lambda e: self.start_repeat(self.move_left,100))
        # self.move_left_btn.bind("<ButtonRelease-1>", lambda e: self.stop_repeat())
        
        # # 重置视图按钮
        # self.reset_view_btn = tk.Button(control_frame, text="重置", 
        #                                 command=self.reset_view,
        #                                 font=("Arial", 8), width=4)
        # self.reset_view_btn.pack(side=tk.LEFT, padx=2)
        
        
        
    def draw_microscope(self):
        """绘制显微镜刻度、十字线和刀口架（支持放大和移动）"""
        self.microscope_canvas.delete("all")
        
        # 画布尺寸
        canvas_width = 320
        canvas_height = 300
        margin = 15
        draw_size = canvas_width - 2 * margin  # 290px
        
        # 绘制圆形显微镜
        self.microscope_canvas.create_oval(margin, margin, 
                                            canvas_width - margin, canvas_height - margin, 
                                            outline='black', width=3)
        
        # 显示范围计算
        base_range = 6.0  # 基础范围 0-8mm
        current_range = base_range / self.microscope_zoom  # 当前显示范围
        
        # 计算显示中心（保持在0-8mm范围内）
        center_pos = max(0.5 * current_range, min(6.0 - 0.5 * current_range, self.microscope_offset))
        self.microscope_offset = center_pos
        
        # 显示范围边界
        start_mm = max(0, center_pos - current_range / 2)
        end_mm = min(8, center_pos + current_range / 2)
        
        # 如果范围超出边界，调整
        if end_mm - start_mm < current_range:
            if start_mm == 0:
                end_mm = current_range
            elif end_mm == 6:
                start_mm = 6 - current_range
        
        # 像素映射: y从(margin+10)到(canvas_height-margin-10) 对应 start_mm 到 end_mm
        y_top = margin + 10
        y_bottom = canvas_height - margin - 10
        pixel_range = y_bottom - y_top  # 约260px
        
        def mm_to_y(mm_val):
            """将mm值转换为画布y坐标"""
            if end_mm - start_mm == 0:
                return y_top
            ratio = (mm_val - start_mm) / (end_mm - start_mm)
            return y_bottom - ratio * pixel_range
        
        # 确定刻度间隔
        if current_range <= 0.5:
            grid_step = 0.01
        elif current_range <= 1.0:
            grid_step = 0.02
        elif current_range <= 2.0:
            grid_step = 0.05
        elif current_range <= 4.0:
            grid_step = 0.1
        else:
            grid_step = 0.2
        
        # 确定数字标签间隔（根据放大倍数调整）
        if current_range <= 0.5:
            label_step = 0.05  # 显示0.05、0.10、0.15...
        elif current_range <= 1.0:
            label_step = 0.1   # 显示0.1、0.2、0.3...
        elif current_range <= 2.0:
            label_step = 0.2   # 显示0.2、0.4、0.6...
        elif current_range <= 4.0:
            label_step = 0.5   # 显示0.5、1.0、1.5...
        else:
            label_step = 1.0   # 显示1、2、3...
        
        # 绘制刻度线
        mm_val = math.ceil(start_mm / grid_step) * grid_step
        while mm_val <= end_mm + 0.001:
            y = mm_to_y(mm_val)
            
            # 判断是否为整数毫米
            is_integer = abs(mm_val - round(mm_val)) < 0.001
            
            if is_integer:
                # 主刻度线 (整数mm) - 加长
                self.microscope_canvas.create_line(140, y, 185, y, width=2)
            else:
                # 判断是否为标签刻度（根据label_step）
                # 检查 mm_val 是否是 label_step 的倍数
                remainder = abs(mm_val / label_step - round(mm_val / label_step))
                is_label_tick = remainder < 0.001
                
                if is_label_tick:
                    # 标签刻度线 - 中等长度
                    self.microscope_canvas.create_line(148, y, 180, y, width=1.5)
                else:
                    # 普通细分刻度 - 最短
                    self.microscope_canvas.create_line(155, y, 170, y, width=1)
            
            mm_val += grid_step
        
        # 绘制刻度尺边框
        self.microscope_canvas.create_line(160, y_top, 160, y_bottom, width=1)
        
        # 绘制数字标签（根据label_step显示更密的数字）
        label_val = math.ceil(start_mm / label_step) * label_step
        # 避免标签重叠：检查相邻标签之间的距离是否足够
        prev_y = None
        while label_val <= end_mm + 0.001:
            y = mm_to_y(label_val)
            
            # 检查与前一个标签是否太近（避免重叠）
            show_label = True
            if prev_y is not None and abs(y - prev_y) < 18:  # 最小间距18像素
                show_label = False
            
            if show_label:
                # 显示数字标签
                if label_val == int(label_val):
                    label_text = f"{int(label_val)}"
                else:
                    label_text = f"{label_val:.2f}" if label_step < 0.1 else f"{label_val:.1f}"
                self.microscope_canvas.create_text(130, y, text=label_text, 
                                                    font=("Arial", 7), anchor='e')
                prev_y = y
            
            label_val += label_step
        
        # 显示刻度间隔值（在刻度尺左侧下方）
        step_text = f"刻度: {grid_step:.2f}mm"
        if grid_step == int(grid_step):
            step_text = f"刻度: {int(grid_step)}.00mm"
        # self.microscope_canvas.create_text(100, y_bottom + 15, 
        #                                     text=step_text, 
        #                                     font=("Arial", 10), fill='darkgreen', anchor='e')
        
        # 绘制十字线
        if start_mm <= self.crosshair_pos <= end_mm:
            crosshair_y = mm_to_y(self.crosshair_pos)
            # 水平线
            self.microscope_canvas.create_line(margin + 5, crosshair_y, 
                                                canvas_width - margin - 5, crosshair_y, 
                                                fill='red', width=1)
            # 垂直线
            self.microscope_canvas.create_line(200, margin + 5, 200, canvas_height - margin - 5,
                                                fill='red', width=1)
            # 标注
            self.microscope_canvas.create_text(250, crosshair_y - 8, text="十字线", 
                                                fill='red', font=("Arial", 10))
        else:
            # 十字线在显示范围外，在边缘显示提示
            if self.crosshair_pos < start_mm:
                arrow_y = y_bottom
                self.microscope_canvas.create_text(250, arrow_y - 10, text="十字线↓", 
                                                    fill='red', font=("Arial", 10))
            else:
                arrow_y = y_top
                self.microscope_canvas.create_text(250, arrow_y + 10, text="十字线↑", 
                                                    fill='red', font=("Arial", 10))
        
        # 绘制刀口架基线
        if start_mm <= self.knife_edge_pos <= end_mm:
            knife_y = mm_to_y(self.knife_edge_pos)
            self.microscope_canvas.create_line(margin + 5, knife_y, 
                                                canvas_width - margin - 5, knife_y, 
                                                fill='blue', width=1)
            self.microscope_canvas.create_text(80, knife_y - 8, text="刀口架基线", 
                                                fill='blue', font=("Arial", 10))
        else:
            if self.knife_edge_pos < start_mm:
                arrow_y = y_bottom
                self.microscope_canvas.create_text(250, arrow_y - 10, text="刀口架基线↓", 
                                                    fill='blue', font=("Arial", 10))
            else:
                arrow_y = y_top
                self.microscope_canvas.create_text(250, arrow_y + 10, text="刀口架基线↑", 
                                                    fill='blue', font=("Arial", 10))
        
        # # 显示当前范围
        # self.microscope_canvas.create_text(280, y_top + 10, 
        #                                     text=f"范围:{current_range:.2f}mm", 
        #                                     font=("Arial", 7), fill='gray')
        
        # 显示放大倍数
        # self.microscope_canvas.create_text(280, y_top + 25, 
        #                                     text=f"{self.microscope_zoom:.1f}×", 
        #                                     font=("Arial", 7), fill='blue')

    def zoom_in(self):
        """放大视图"""
        if self.microscope_zoom < 16.0:
            self.microscope_zoom *= 2.0
            self.zoom_label.config(text=f"{self.microscope_zoom:.1f}×")
            self.draw_microscope()

    def zoom_out(self):
        """缩小视图"""
        if self.microscope_zoom > 1.0:
            self.microscope_zoom /= 2.0
            self.zoom_label.config(text=f"{self.microscope_zoom:.1f}×")
            self.draw_microscope()

    def move_left(self):
        """视图下移（显示范围下移）"""
        current_range = 6.0 / self.microscope_zoom
        step = current_range * 0.1
        new_offset = self.microscope_offset - step
        # 确保不超出边界
        min_offset = current_range / 2
        max_offset = 6.0 - current_range / 2
        if new_offset >= min_offset and new_offset <= max_offset:
            self.microscope_offset = new_offset
            self.draw_microscope()
        elif new_offset < min_offset:
            # 如果超出下边界，移动到最小位置
            self.microscope_offset = min_offset
            self.draw_microscope()

    def move_right(self):
        """视图上移（显示范围上移）"""
        current_range = 6.0 / self.microscope_zoom
        step = current_range * 0.1
        new_offset = self.microscope_offset + step
        # 确保不超出边界
        min_offset = current_range / 2
        max_offset = 6.0 - current_range / 2
        if new_offset >= min_offset and new_offset <= max_offset:
            self.microscope_offset = new_offset
            self.draw_microscope()
        elif new_offset > max_offset:
            # 如果超出上边界，移动到最大位置
            self.microscope_offset = max_offset
            self.draw_microscope()

    def reset_view(self):
        """重置视图"""
        self.microscope_zoom = 1.0
        self.microscope_offset = 4.0
        self.zoom_label.config(text="1.0×")
        self.draw_microscope()

    def create_bottom_left(self):
        """左下区域：实验操作区域"""
        frame = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        frame.place(x=10, y=390, width=680, height=450)
        
        tk.Label(frame, text="实验操作区域", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 创建左右分栏的容器
        content_frame = tk.Frame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：图片区域
        left_frame = tk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # 右侧：控制区域
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # 加载装置图片（放在左侧）
        img_path = get_resource_path("background/装置.jpg")
        try:
            img = Image.open(img_path)
            # 调整图片大小以适应左侧区域
            img = img.resize((300, 250), Image.Resampling.LANCZOS)
            self.device_img = ImageTk.PhotoImage(img)
            img_label = tk.Label(left_frame, image=self.device_img)
            img_label.pack(pady=10)
        except Exception as e:
            tk.Label(left_frame, text=f"无法加载图片:\n装置.jpg\n{e}", fg='red').pack(pady=20)
        
        # 样品选择
        sample_frame = tk.Frame(right_frame)
        sample_frame.pack(fill=tk.X, pady=5)

        tk.Label(sample_frame, text="样品选择:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 10))

        self.sample_var = tk.StringVar(value="黄铜")
        self.sample_combo = ttk.Combobox(sample_frame, textvariable=self.sample_var, 
                                        values=["黄铜", "铸铁"], state="readonly", width=10)
        self.sample_combo.pack(side=tk.LEFT)
        self.sample_combo.bind("<<ComboboxSelected>>", self.on_sample_changed)

        # # 显示当前样品
        # self.sample_display_label = tk.Label(sample_frame, text="当前: 黄铜", 
        #                                     font=("Arial", 9, "bold"), fg='darkgreen')
        # self.sample_display_label.pack(side=tk.LEFT, padx=(10, 0))

        # 十字线位置控制
        crosshair_container = tk.Frame(right_frame)
        crosshair_container.pack(fill=tk.X, pady=5)

        tk.Label(crosshair_container, text="十字线位置 (mm):", font=("Arial", 9)).pack(anchor='w')

        # 十字线进度条和微调按钮放在同一行
        crosshair_row = tk.Frame(crosshair_container)
        crosshair_row.pack(fill=tk.X)

        # 左微调按钮（长按支持）
        self.crosshair_minus_btn = tk.Button(crosshair_row, text="-", font=("Arial", 10, "bold"),
                                            width=2)
        self.crosshair_minus_btn.pack(side=tk.LEFT, padx=(0, 5))
        # 绑定长按事件
        self.crosshair_minus_btn.bind("<ButtonPress-1>", lambda e: self.start_repeat(self.crosshair_minus))
        self.crosshair_minus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_repeat())

        # 十字线进度条
        self.crosshair_slider = tk.Scale(crosshair_row, from_=0, to=6, resolution=0.01,
                                        orient=tk.HORIZONTAL, length=180,
                                        command=self.update_crosshair,
                                        showvalue=0)
        self.crosshair_slider.set(4.0)
        self.crosshair_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 右微调按钮（长按支持）
        self.crosshair_plus_btn = tk.Button(crosshair_row, text="+", font=("Arial", 10, "bold"),
                                            width=2)
        self.crosshair_plus_btn.pack(side=tk.LEFT, padx=(5, 0))
        # 绑定长按事件
        self.crosshair_plus_btn.bind("<ButtonPress-1>", lambda e: self.start_repeat(self.crosshair_plus))
        self.crosshair_plus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_repeat())

        # 显示当前值
        self.crosshair_value_label = tk.Label(crosshair_container, text="4.00 mm", 
                                            font=("Arial", 9), fg='red')
        self.crosshair_value_label.pack(anchor='e', pady=(0, 5))

        # 刀口架基线控制
        knife_container = tk.Frame(right_frame)
        knife_container.pack(fill=tk.X, pady=5)

        tk.Label(knife_container, text="显微镜高度:", font=("Arial", 9)).pack(anchor='w')

        # 刀口架基线进度条和微调按钮放在同一行
        knife_row = tk.Frame(knife_container)
        knife_row.pack(fill=tk.X)

        # 左微调按钮（长按支持）
        self.knife_minus_btn = tk.Button(knife_row, text="-", font=("Arial", 10, "bold"),
                                        width=2)
        self.knife_minus_btn.pack(side=tk.LEFT, padx=(0, 5))
        

        # 刀口架基线进度条
        self.knife_slider = tk.Scale(knife_row, from_=0, to=6, resolution=0.01,
                                    orient=tk.HORIZONTAL, length=180,
                                    command=self.update_knife_edge,
                                    showvalue=0)
        self.knife_slider.set(5.0)
        self.knife_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 右微调按钮（长按支持）
        self.knife_plus_btn = tk.Button(knife_row, text="+", font=("Arial", 10, "bold"),
                                        width=2)
        self.knife_plus_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # 绑定长按事件
        self.knife_minus_btn.bind("<ButtonPress-1>", lambda e: self.start_repeat(self.knife_minus))
        self.knife_minus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_repeat())
        # 绑定长按事件
        self.knife_plus_btn.bind("<ButtonPress-1>", lambda e: self.start_repeat(self.knife_plus))
        self.knife_plus_btn.bind("<ButtonRelease-1>", lambda e: self.stop_repeat())

        # # 显示当前值
        # self.knife_value_label = tk.Label(knife_container, text="5.00 mm", 
        #                                 font=("Arial", 9), fg='blue')
        # self.knife_value_label.pack(anchor='e', pady=(0, 5))
        
        # 移动磁铁进度条
        tk.Label(right_frame, text="下----------磁铁位置-----------上", font=("Arial", 9)).pack(anchor='w')
        self.magnet_slider = tk.Scale(right_frame, from_=100, to=-100, resolution=1,
                                    orient=tk.HORIZONTAL, length=220, 
                                    command=self.update_magnet_position,
                                    showvalue=0)
        self.magnet_slider.set(0)  # 设置初始位置为中间
        self.magnet_slider.pack(pady=5, fill=tk.X)
        
        # # 调零控件（放在移动磁铁进度条下方）
        # zero_container = tk.Frame(right_frame)
        # zero_container.pack(pady=10, fill=tk.X)
        
        # 调零控件标题
        tk.Label(right_frame, text="调零:", font=("Arial", 9), 
                 fg='black').pack(anchor='w')
        
        # 调零进度条和数值放在同一行
        zero_slider_frame = tk.Frame(right_frame)
        zero_slider_frame.pack(fill=tk.X, pady=0)
        
        self.zero_slider = tk.Scale(zero_slider_frame, from_=-100, to=100, resolution=1,
                                     orient=tk.HORIZONTAL, length=370,
                                     variable=self.zero_value,
                                     command=self.update_zero_value,
                                     showvalue=0)
        self.zero_slider.set(0)
        self.zero_slider.pack(pady=5, fill=tk.X)
        
        # # 显示当前调零值
        # self.zero_display_label = tk.Label(zero_slider_frame, text="0 mV", 
        #                                     font=("Arial", 9, "bold"), fg='red', width=8)
        # self.zero_display_label.pack(side=tk.LEFT)
        
        # 重置按钮
        # reset_btn = tk.Button(zero_container, text="重置", command=self.reset_zero,
        #                       font=("Arial", 8), bg='lightgray', width=8)
        # reset_btn.pack(pady=5)
        
        # 砝码控制按钮
        btn_frame = tk.Frame(right_frame)
        btn_frame.pack(pady=15)

        self.add_weight_btn = tk.Button(btn_frame, text="增加砝码 (+10g)", command=self.add_weight,
                                        font=("Arial", 10), bg='lightgreen', width=12)
        self.add_weight_btn.pack(side=tk.LEFT, padx=5)

        self.remove_weight_btn = tk.Button(btn_frame, text="减少砝码 (-10g)", command=self.remove_weight,
                                            font=("Arial", 10), bg='lightcoral', width=12)
        self.remove_weight_btn.pack(side=tk.LEFT, padx=5)

        self.weight_label = tk.Label(right_frame, text="砝码: 0g", font=("Arial", 10))
        self.weight_label.pack(pady=5)
    
    def start_repeat(self, callback, interval=50):
        """开始长按重复触发"""
        self.repeat_id = self.root.after(interval, self.repeat_callback, callback, interval)

    def stop_repeat(self):
        """停止长按重复触发"""
        if hasattr(self, 'repeat_id') and self.repeat_id is not None:
            self.root.after_cancel(self.repeat_id)
            self.repeat_id = None

    def repeat_callback(self, callback, interval):
        """长按重复回调"""
        callback()
        self.repeat_id = self.root.after(interval, self.repeat_callback, callback, interval)

    def crosshair_plus(self):
        """十字线位置增加0.01mm"""
        new_value = self.crosshair_pos + 0.01
        if new_value <= 8.0:
            self.crosshair_slider.set(new_value)
            self.update_crosshair(new_value)

    def crosshair_minus(self):
        """十字线位置减少0.01mm"""
        new_value = self.crosshair_pos - 0.01
        if new_value >= 0:
            self.crosshair_slider.set(new_value)
            self.update_crosshair(new_value)

    def knife_plus(self):
        """显微镜基准高度增加0.01mm"""
        new_value = self.knife_base_pos + 0.01
        if new_value <= 8.0:
            self.knife_slider.set(new_value)
            self.update_knife_edge(new_value)

    def knife_minus(self):
        """显微镜基准高度减少0.01mm"""
        new_value = self.knife_base_pos - 0.01
        if new_value >= 0:
            self.knife_slider.set(new_value)
            self.update_knife_edge(new_value)

    def update_magnet_position(self, value):
        """更新磁铁位置对电压的影响（步进1mV）"""
        self.magnet_position = int(float(value))
        self.magnet_voltage_offset = self.magnet_position
        
        # 更新电压显示
        self.current_voltage = self.initial_voltage + self.zero_value.get() + self.magnet_voltage_offset
        if hasattr(self, 'voltage_text'):
            self.host_canvas.itemconfig(self.voltage_text, text=str(int(round(self.current_voltage))))

    def update_crosshair(self, value):
        """更新十字线位置"""
        self.crosshair_pos = float(value)
        # 更新显示标签
        if hasattr(self, 'crosshair_value_label'):
            self.crosshair_value_label.config(text=f"{self.crosshair_pos:.2f} mm")
        self.draw_microscope()
    
        
    def update_knife_edge(self, value):
        """更新显微镜基准高度"""
        self.knife_base_pos = float(value)
        # 实际显示位置 = 基准高度 + 砝码偏移
        self.knife_edge_pos = self.knife_base_pos + self.knife_offset
        # 限制范围
        self.knife_edge_pos = max(0, min(8, self.knife_edge_pos))
        self.draw_microscope()
    
    def on_sample_changed(self, event):
        """样品切换事件"""
        new_sample = self.sample_var.get()
        
        # 如果切换前后样品相同，不做任何操作
        if new_sample == self.sample_type:
            return
        
        # 弹出确认对话框
        result = messagebox.askyesno(
            "确认切换样品",
            f"确定要切换到【{new_sample}】吗？\n\n"
            f"切换后将会清空当前样品数据，是否继续？",
            icon='warning'
        )
        
        if not result:
            # 用户取消，恢复下拉框显示为原来的样品
            self.sample_var.set(self.sample_type)
            return
        
        # 执行样品切换
        self.sample_type = new_sample
        # self.sample_display_label.config(text=f"当前: {self.sample_type}")
        
        # 根据样品类型更新厚度和理论值
        if self.sample_type == "黄铜":
            self.thickness.set(0.995)
            self.theory_value.set("1.055×10¹¹")
        else:  # 铸铁
            self.thickness.set(1.001)
            self.theory_value.set("1.851×10¹¹")
        
        # 更新样品参数显示（数据记录区域）
        if hasattr(self, 'sample_param_label'):
            self.sample_param_label.config(text=f"样品: {self.sample_type}")
        
        # 更新厚度显示
        if hasattr(self, 'a_display_label'):
            self.a_display_label.config(text=f"{self.thickness.get():.3f}")
        
        # 清空数据表格
        self.clear_brass_data()
        
        #重置砝码和电压到初始状态
        self.reset_experiment()
        
        messagebox.showinfo("提示", f"已切换到【{self.sample_type}】")

    def reset_experiment(self):
        """重置实验（砝码、电压、位移）"""
        # 重置砝码
        self.weight_count = 0
        self.total_weight = 0
        self.weight_label.config(text="砝码: 0g")
        
        # 重置砝码偏移
        self.knife_offset = 0.0
        
        # 重置刀口架基线位置（基准位置重置为5.0）
        self.knife_base_pos = 5.0
        self.knife_edge_pos = 5.0
        self.knife_slider.set(5.0)
        
        # 重新生成初始电压（-100到100）
        self.initial_voltage = random.randint(-100, 100)
        self.current_voltage = self.initial_voltage + self.zero_value.get() + self.magnet_voltage_offset
        
        # 更新电压显示
        if hasattr(self, 'voltage_text'):
            if abs(self.current_voltage - round(self.current_voltage)) < 0.01:
                self.host_canvas.itemconfig(self.voltage_text, text=str(int(round(self.current_voltage))))
            else:
                self.host_canvas.itemconfig(self.voltage_text, text=f"{self.current_voltage:.1f}")
        
        # 重新生成砝码对应的位移和电压增量
        self.weight_displacements = []
        self.weight_voltages = []
        
        if self.sample_type == "黄铜":
            for _ in range(12):
                self.weight_displacements.append(0.124)
                self.weight_voltages.append(36.5)
        else:  # 铸铁
            # 铸铁: 黄铜的 0.57 倍
            # 位移: 0.12-0.13 * 0.57 ≈ 0.0684-0.0741mm
            # 电压: 36-37 * 0.57 ≈ 20.5-21.1mV
            ratio = 0.57
            for _ in range(12):
                self.weight_displacements.append(0.124 * ratio)
                self.weight_voltages.append(36.5 * ratio)
        
        # 更新画布
        self.draw_microscope()

    def add_weight(self):
        """增加砝码 (+10g)"""
        if self.weight_count < 12:  # 最多12个砝码
            self.weight_count += 1
            self.total_weight = self.weight_count * 10  # 计算总重量
            
            # 砝码引起的位移偏移（累加）
            displacement = self.weight_displacements[self.weight_count - 1]
            self.knife_offset += displacement  # 累加偏移
            # 实际显示位置 = 基准高度 + 砝码偏移
            self.knife_edge_pos = self.knife_base_pos + self.knife_offset
            self.knife_edge_pos = max(0, min(8, self.knife_edge_pos))
            
            # 电压增加
            voltage_increment = self.weight_voltages[self.weight_count - 1]
            self.initial_voltage += voltage_increment
            self.current_voltage = self.initial_voltage + self.zero_value.get() + self.magnet_voltage_offset
            
            # 更新电压显示（显示整数）
            if hasattr(self, 'voltage_text'):
                self.host_canvas.itemconfig(self.voltage_text, text=str(int(round(self.current_voltage))))
            
            # 更新砝码显示
            self.weight_label.config(text=f"砝码: {self.total_weight}g")
            self.draw_microscope()
        else:
            messagebox.showwarning("警告", "已达到最大砝码数量(12个，120g)")
            
    def remove_weight(self):
        """减少砝码 (-10g)"""
        if self.weight_count > 0:
            # 移除最后一个砝码的偏移
            displacement = self.weight_displacements[self.weight_count - 1]
            self.knife_offset -= displacement
            # 实际显示位置 = 基准高度 + 砝码偏移
            self.knife_edge_pos = self.knife_base_pos + self.knife_offset
            self.knife_edge_pos = max(0, min(8, self.knife_edge_pos))
            
            voltage_increment = self.weight_voltages[self.weight_count - 1]
            self.initial_voltage -= voltage_increment
            self.current_voltage = self.initial_voltage + self.zero_value.get() + self.magnet_voltage_offset
            
            if hasattr(self, 'voltage_text'):
                self.host_canvas.itemconfig(self.voltage_text, text=str(int(round(self.current_voltage))))
            
            self.weight_count -= 1
            self.total_weight = self.weight_count * 10
            self.weight_label.config(text=f"砝码: {self.total_weight}g")
            self.draw_microscope()
        else:
            messagebox.showwarning("警告", "已经没有砝码了")
            
    def create_top_right(self):
        """右上区域：实验仪主机区域"""
        frame = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        frame.place(x=480, y=10, width=800, height=370)
        
        tk.Label(frame, text="实验仪主机", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 创建容器用于放置图片和电压显示
        image_container = tk.Frame(frame)
        image_container.pack(pady=10)
        
        # 加载主机图片
        img_path = get_resource_path("background/主机.jpg")
        try:
            img = Image.open(img_path)
            # 保持原始比例 700:240
            display_width = 750
            display_height = int(display_width * 240 / 700)
            img = img.resize((display_width, display_height), Image.Resampling.LANCZOS)
            self.host_img = ImageTk.PhotoImage(img)
            
            # 在Canvas上放置图片，这样可以叠加其他元素
            self.host_canvas = tk.Canvas(image_container, width=display_width, height=display_height,
                                          highlightthickness=0)
            self.host_canvas.pack()
            self.host_canvas.create_image(0, 0, anchor=tk.NW, image=self.host_img)
            
            # 在图片上添加电压显示框（白色背景，黑色边框）
            # 计算显示框位置（图片右上角）
            box_x = display_width - 600  # 距离右边120px
            box_y = 120  # 距离顶部20px
            
            # # 绘制电压显示框背景
            # self.voltage_box = self.host_canvas.create_rectangle(
            #     box_x, box_y, box_x + 100, box_y + 50,
            #     fill='white', outline='black', width=2
            # )
            
            # 添加电压显示标签
            self.voltage_text = self.host_canvas.create_text(
                box_x + 65, box_y + 20,
                text=str(self.current_voltage),
                font=("Arial",48, "bold"), fill='black'
            )
            
        except Exception as e:
            tk.Label(frame, text=f"无法加载图片: 主机.jpg\n{e}", fg='red').pack(pady=50)
    
    def update_zero_value(self, value):
        """更新调零值显示（1mV步进）"""
        zero_val = int(float(value))
        
        # 计算最终显示的电压值 = 初始电压 + 调零值 + 磁铁偏移
        final_voltage = self.initial_voltage + zero_val + self.magnet_voltage_offset
        self.current_voltage = final_voltage
        
        # 更新图片上的电压显示（显示整数）
        if hasattr(self, 'voltage_text'):
            self.host_canvas.itemconfig(self.voltage_text, text=str(int(round(final_voltage))))
        self.host_canvas.itemconfig(self.voltage_text, fill='black')

    def reset_zero(self):
        """重置调零值为0"""
        self.zero_slider.set(0)
        
        # 重置电压显示
        self.current_voltage = self.initial_voltage + self.magnet_voltage_offset
        if hasattr(self, 'voltage_text'):
            self.host_canvas.itemconfig(self.voltage_text, text=str(self.current_voltage))
            self.host_canvas.itemconfig(self.voltage_text, fill='black')
         
            
    def create_bottom_right(self):
        """右下区域：数据记录区域"""
        frame = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        frame.place(x=680, y=390, width=600, height=450)
        
        tk.Label(frame, text="数据记录", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 选项卡1: 霍尔位置传感器静态特性测量
        self.hall_frame = tk.Frame(self.notebook)
        self.notebook.add(self.hall_frame, text="霍尔位置传感器静态特性测量")
        self.create_hall_tab()
        
        # 选项卡2: 样品位移测量
        self.brass_frame = tk.Frame(self.notebook)
        self.notebook.add(self.brass_frame, text="样品位移测量")
        self.create_brass_tab()
        
        # 绑定选项卡切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
    def create_hall_tab(self):
        """创建霍尔传感器选项卡"""
        # 表格框架
        table_frame = tk.Frame(self.hall_frame)
        table_frame.pack(pady=10)
        
        # 创建3行7列表格
        headers = ["", "1", "2", "3", "4", "5", "6"]
        row_headers = ["M/g", "Z/mm", "U/mV"]
        
        self.hall_table_entries = []
        
        for i in range(4):  # 4行 (包括表头)
            row_entries = []
            for j in range(7):  # 7列
                if i == 0:  # 第一行表头
                    if j == 0:
                        label = tk.Label(table_frame, text=headers[j], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                    else:
                        label = tk.Label(table_frame, text=headers[j], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                    label.grid(row=i, column=j, padx=1, pady=1)
                elif i == 1:  # M/g
                    if j == 0:
                        label = tk.Label(table_frame, text=row_headers[i-1], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                        label.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(None)
                    else:
                        entry = tk.Entry(table_frame, width=10, justify='center')
                        entry.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(entry)
                elif i == 2:  # Z/mm
                    if j == 0:
                        label = tk.Label(table_frame, text=row_headers[i-1], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                        label.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(None)
                    else:
                        entry = tk.Entry(table_frame, width=10, justify='center')
                        entry.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(entry)
                elif i == 3:  # U/mV
                    if j == 0:
                        label = tk.Label(table_frame, text=row_headers[i-1], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                        label.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(None)
                    else:
                        entry = tk.Entry(table_frame, width=10, justify='center')
                        entry.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(entry)
            self.hall_table_entries.append(row_entries)
        
        # 按钮框架
        button_frame = tk.Frame(self.hall_frame)
        button_frame.pack(pady=5)
        
        # 计算按钮
        calc_btn = tk.Button(button_frame, text="计算灵敏度", 
                            command=self.calculate_hall_sensitivity,
                            font=("Arial", 10), bg='lightblue', width=10)
        calc_btn.pack(side=tk.LEFT, padx=5)
        
        # 清空数据按钮
        clear_btn = tk.Button(button_frame, text="清空数据", 
                            command=self.clear_hall_data,
                            font=("Arial", 10), bg='lightyellow', width=10)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出数据按钮
        export_btn = tk.Button(button_frame, text="导出数据", 
                            command=self.export_hall_data,
                            font=("Arial", 10), bg='lightgreen', width=10)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # 导入数据按钮
        import_btn = tk.Button(button_frame, text="导入数据", 
                            command=self.import_hall_data,
                            font=("Arial", 10), bg='lightcoral', width=10)
        import_btn.pack(side=tk.LEFT, padx=5)
        
        # 灵敏度显示
        sens_frame = tk.Frame(self.hall_frame)
        sens_frame.pack(pady=10)
        
        tk.Label(sens_frame, text="霍尔传感器灵敏度:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.hall_sensitivity = tk.StringVar(value="---")
        sens_label = tk.Label(sens_frame, textvariable=self.hall_sensitivity, 
                            font=("Arial", 10, "bold"), fg='blue')
        sens_label.pack(side=tk.LEFT, padx=10)
        tk.Label(sens_frame, text="mV/mm", font=("Arial", 10)).pack(side=tk.LEFT)

    def clear_hall_data(self):
        """清空霍尔传感器表格数据"""
        for i in range(1, 4):  # 第1-3行数据行
            for j in range(1, 7):  # 第1-6列
                # 注意：hall_table_entries[i] 的长度是7（包含索引0的None）
                # 但索引0是行标题，所以数据列从索引1开始
                if j < len(self.hall_table_entries[i]):
                    entry = self.hall_table_entries[i][j]
                    if entry:
                        entry.delete(0, tk.END)
        self.hall_sensitivity.set("---")
        messagebox.showinfo("提示", "霍尔传感器数据已清空")

    def export_hall_data(self):
        """导出霍尔传感器数据到CSV文件（包含灵敏度）"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="保存霍尔传感器数据"
        )
        
        if filename:
            try:
                data = []
                # 表头行：第一列是"项目"，后面是序号1-6
                header = ["项目", "1", "2", "3", "4", "5", "6"]
                data.append(header)
                
                # M/g行：从索引1开始读取（跳过索引0的None）
                mg_row = ["M/g"]
                for col in range(1, 7):  # 索引1到6
                    entry = self.hall_table_entries[1][col]
                    if entry:
                        value = entry.get().strip()
                        mg_row.append(value if value else "")
                    else:
                        mg_row.append("")
                data.append(mg_row)
                
                # Z/mm行：从索引1开始读取
                z_row = ["Z/mm"]
                for col in range(1, 7):
                    entry = self.hall_table_entries[2][col]
                    if entry:
                        value = entry.get().strip()
                        z_row.append(value if value else "")
                    else:
                        z_row.append("")
                data.append(z_row)
                
                # U/mV行：从索引1开始读取
                u_row = ["U/mV"]
                for col in range(1, 7):
                    entry = self.hall_table_entries[3][col]
                    if entry:
                        value = entry.get().strip()
                        u_row.append(value if value else "")
                    else:
                        u_row.append("")
                data.append(u_row)
                
                # 添加空行
                data.append([])
                
                # 灵敏度计算结果
                data.append(["计算结果", "值", "单位"])
                data.append(["霍尔传感器灵敏度", self.hall_sensitivity.get(), "mV/mm"])
                
                # 写入CSV文件
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerows(data)
                
                messagebox.showinfo("提示", f"数据已导出到:\n{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def import_hall_data(self):
        """导入霍尔传感器数据从CSV文件"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="选择霍尔传感器数据文件"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                
                if len(rows) >= 4:
                    # 清空现有数据（索引1-6）
                    for i in range(1, 4):  # 行1-3
                        for j in range(1, 7):  # 列1-6
                            if j < len(self.hall_table_entries[i]):
                                entry = self.hall_table_entries[i][j]
                                if entry:
                                    entry.delete(0, tk.END)
                    
                    # 导入M/g数据（第2行，索引1）
                    if len(rows) >= 2 and len(rows[1]) >= 7:
                        for j in range(1, 7):
                            if j < len(rows[1]) and rows[1][j].strip():
                                self.hall_table_entries[1][j].insert(0, rows[1][j])
                    
                    # 导入Z/mm数据（第3行，索引2）
                    if len(rows) >= 3 and len(rows[2]) >= 7:
                        for j in range(1, 7):
                            if j < len(rows[2]) and rows[2][j].strip():
                                self.hall_table_entries[2][j].insert(0, rows[2][j])
                    
                    # 导入U/mV数据（第4行，索引3）
                    if len(rows) >= 4 and len(rows[3]) >= 7:
                        for j in range(1, 7):
                            if j < len(rows[3]) and rows[3][j].strip():
                                self.hall_table_entries[3][j].insert(0, rows[3][j])
                    
                    messagebox.showinfo("提示", f"数据已从文件导入:\n{filename}")
                else:
                    messagebox.showwarning("警告", "文件格式不正确")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")

    def calculate_hall_sensitivity(self):
        """计算霍尔传感器灵敏度"""
        try:
            # 获取位移数据(Z)和电压数据(U)
            z_values = []
            u_values = []
            
            for col in range(6):
                z_entry = self.hall_table_entries[2][col]  # Z/mm行（第3行，索引2）
                u_entry = self.hall_table_entries[3][col]  # U/mV行（第4行，索引3）
                
                if z_entry and u_entry and z_entry.get().strip() and u_entry.get().strip():
                    z = float(z_entry.get())
                    u = float(u_entry.get())
                    z_values.append(z)
                    u_values.append(u)
            
            if len(z_values) >= 2:
                # 使用线性回归计算灵敏度
                n = len(z_values)
                sum_z = sum(z_values)
                sum_u = sum(u_values)
                sum_zu = sum(z * u for z, u in zip(z_values, u_values))
                sum_z2 = sum(z**2 for z in z_values)
                
                # 斜率 = (n*sum_zu - sum_z*sum_u) / (n*sum_z2 - sum_z^2)
                denominator = n * sum_z2 - sum_z ** 2
                if denominator != 0:
                    sensitivity = (n * sum_zu - sum_z * sum_u) / denominator
                    self.hall_sensitivity.set(f"{sensitivity:.3f}")
                else:
                    self.hall_sensitivity.set("计算错误")
            else:
                self.hall_sensitivity.set("数据不足")
        except Exception as e:
            messagebox.showerror("错误", f"数据格式错误: {e}")
            self.hall_sensitivity.set("错误")
            
    def create_brass_tab(self):
        """创建样品选项卡"""
        # 表格框架
        table_frame = tk.Frame(self.brass_frame)
        table_frame.pack(pady=10)
        
        # 创建2行7列表格
        headers = ["", "1", "2", "3", "4", "5", "6"]
        row_headers = ["M/g", "Z/mm"]
        
        self.brass_table_entries = []
        
        for i in range(3):  # 3行 (包括表头)
            row_entries = []
            for j in range(7):
                if i == 0:  # 表头行
                    label = tk.Label(table_frame, text=headers[j], width=10,
                                    bg='lightgray', relief=tk.RAISED)
                    label.grid(row=i, column=j, padx=1, pady=1)
                else:  # 数据行
                    if j == 0:
                        label = tk.Label(table_frame, text=row_headers[i-1], width=10,
                                        bg='lightgray', relief=tk.RAISED)
                        label.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(None)
                    else:
                        entry = tk.Entry(table_frame, width=10, justify='center')
                        entry.grid(row=i, column=j, padx=1, pady=1)
                        row_entries.append(entry)
            if i > 0:
                self.brass_table_entries.append(row_entries)
        
        # 样品信息显示
        info_frame = tk.Frame(self.brass_frame)
        info_frame.pack(pady=5, fill=tk.X, padx=10)
        
        # 当前样品显示
        self.sample_param_label = tk.Label(info_frame, text="样品: 黄铜", 
                                            font=("Arial", 10, "bold"), fg='darkgreen')
        self.sample_param_label.pack(side=tk.LEFT, padx=5)
        
        # 样品参数设置
        param_frame = tk.LabelFrame(self.brass_frame, text="样品参数设置", font=("Arial", 9))
        param_frame.pack(pady=10, padx=10, fill=tk.X)
        
        param_inner = tk.Frame(param_frame)
        param_inner.pack(pady=5)
        
        # 横梁长度 - 只读显示
        tk.Label(param_inner, text="横梁长度 d =", font=("Arial", 9)).grid(row=0, column=0, padx=5)
        d_label = tk.Label(param_inner, text="23.0", font=("Arial", 9), bg='lightgray', width=10, relief=tk.SUNKEN)
        d_label.grid(row=0, column=1, padx=2)
        tk.Label(param_inner, text="cm", font=("Arial", 9)).grid(row=0, column=2, padx=5)
        
        # 横梁宽度 - 只读显示
        tk.Label(param_inner, text="横梁宽度 b =", font=("Arial", 9)).grid(row=0, column=3, padx=5)
        b_label = tk.Label(param_inner, text="2.3", font=("Arial", 9), bg='lightgray', width=10, relief=tk.SUNKEN)
        b_label.grid(row=0, column=4, padx=2)
        tk.Label(param_inner, text="cm", font=("Arial", 9)).grid(row=0, column=5, padx=5)
        
        # 横梁厚度 - 只读显示
        tk.Label(param_inner, text="横梁厚度 a =", font=("Arial", 9)).grid(row=1, column=0, padx=5, pady=5)
        a_label = tk.Label(param_inner, text="0.995", font=("Arial", 9), bg='lightgray', width=10, relief=tk.SUNKEN)
        a_label.grid(row=1, column=1, padx=2)
        tk.Label(param_inner, text="mm", font=("Arial", 9)).grid(row=1, column=2, padx=5)
        
        # 按钮框架
        button_frame = tk.Frame(self.brass_frame)
        button_frame.pack(pady=5)
        
        # 计算按钮
        calc_btn = tk.Button(button_frame, text="计算杨氏模量", 
                            command=self.calculate_yang_modulus,
                            font=("Arial", 10), bg='lightgreen', width=12)
        calc_btn.pack(side=tk.LEFT, padx=5)
        
        # 清空数据按钮
        clear_btn = tk.Button(button_frame, text="清空数据", 
                            command=self.clear_brass_data,
                            font=("Arial", 10), bg='lightyellow', width=10)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出数据按钮
        export_btn = tk.Button(button_frame, text="导出数据", 
                            command=self.export_brass_data,
                            font=("Arial", 10), bg='lightgreen', width=10)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # 导入数据按钮
        import_btn = tk.Button(button_frame, text="导入数据", 
                            command=self.import_brass_data,
                            font=("Arial", 10), bg='lightcoral', width=10)
        import_btn.pack(side=tk.LEFT, padx=5)
        
        # 杨氏模量显示
        yang_frame = tk.Frame(self.brass_frame)
        yang_frame.pack(pady=10)

        tk.Label(yang_frame, text="样品的杨氏模量:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.yang_modulus = tk.StringVar(value="---")
        yang_label = tk.Label(yang_frame, textvariable=self.yang_modulus, 
                            font=("Arial", 10, "bold"), fg='red', width=15, anchor='w')
        yang_label.pack(side=tk.LEFT, padx=5)
        tk.Label(yang_frame, text="N/m²", font=("Arial", 10)).pack(side=tk.LEFT)
        
        # 理论值显示
        theory_frame = tk.Frame(self.brass_frame)
        theory_frame.pack(pady=5)

        tk.Label(theory_frame, text="理论值:", font=("Arial", 9)).pack(side=tk.LEFT)
        self.theory_value = tk.StringVar(value="1.055×10¹¹")
        theory_label = tk.Label(theory_frame, textvariable=self.theory_value, 
                                font=("Arial", 9, "bold"), fg='blue')
        theory_label.pack(side=tk.LEFT, padx=5)
        tk.Label(theory_frame, text="N/m²", font=("Arial", 9)).pack(side=tk.LEFT)

        # 误差显示（单独一栏）
        error_frame = tk.Frame(self.brass_frame)
        error_frame.pack(pady=5)

        tk.Label(error_frame, text="相对误差:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.error_percent = tk.StringVar(value="---")
        error_label = tk.Label(error_frame, textvariable=self.error_percent, 
                            font=("Arial", 10, "bold"), fg='orange', width=10, anchor='w')
        error_label.pack(side=tk.LEFT, padx=5)
        tk.Label(error_frame, text="%", font=("Arial", 10)).pack(side=tk.LEFT)

        

    def clear_brass_data(self):
        """清空样品表格数据"""
        for i in range(2):  # 2行数据行
            for j in range(1, 7):  # 第1-6列
                # brass_table_entries[i] 的长度是7（包含索引0的None）
                if j < len(self.brass_table_entries[i]):
                    entry = self.brass_table_entries[i][j]
                    if entry:
                        entry.delete(0, tk.END)
        self.yang_modulus.set("---")
        self.error_percent.set("---")
        messagebox.showinfo("提示", "样品数据已清空")

    def export_brass_data(self):
        """导出样品数据到CSV文件（包含计算结果）"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="保存样品数据"
        )
        
        if filename:
            try:
                data = []
                # 表头行
                header = ["项目", "1", "2", "3", "4", "5", "6"]
                data.append(header)
                
                # M/g行
                mg_row = ["M/g"]
                for col in range(1, 7):
                    if col < len(self.brass_table_entries[0]):
                        entry = self.brass_table_entries[0][col]
                        if entry:
                            value = entry.get().strip()
                            mg_row.append(value if value else "")
                        else:
                            mg_row.append("")
                    else:
                        mg_row.append("")
                data.append(mg_row)
                
                # Z/mm行
                z_row = ["Z/mm"]
                for col in range(1, 7):
                    if col < len(self.brass_table_entries[1]):
                        entry = self.brass_table_entries[1][col]
                        if entry:
                            value = entry.get().strip()
                            z_row.append(value if value else "")
                        else:
                            z_row.append("")
                    else:
                        z_row.append("")
                data.append(z_row)
                
                # 添加空行
                data.append([])
                
                # 样品信息
                data.append(["样品信息", "值"])
                data.append(["样品类型", self.sample_type])
                
                # 添加空行
                data.append([])
                
                # 样品参数
                data.append(["参数", "值", "单位"])
                data.append(["横梁长度 d", str(self.length.get()), "cm"])
                data.append(["横梁宽度 b", str(self.width.get()), "cm"])
                data.append(["横梁厚度 a", str(self.thickness.get()), "mm"])
                
                # 添加空行
                data.append([])
                
                # 计算结果
                data.append(["计算结果", "值", "单位"])
                data.append(["杨氏模量", self.yang_modulus.get(), "N/m²"])
                data.append(["理论值", self.theory_value.get(), "N/m²"])
                data.append(["相对误差", self.error_percent.get(), "%"])
                
                # 写入CSV文件
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerows(data)
                
                messagebox.showinfo("提示", f"数据已导出到:\n{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def import_brass_data(self):
        """导入样品数据从CSV文件（仅导入数据，不修改样品参数）"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="选择样品数据文件"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                
                if len(rows) >= 3:
                    # 清空现有数据（索引1-6）
                    for i in range(2):  # 2行数据行
                        for j in range(1, 7):  # 列1-6
                            if j < len(self.brass_table_entries[i]):
                                entry = self.brass_table_entries[i][j]
                                if entry:
                                    entry.delete(0, tk.END)
                    
                    # 导入M/g数据（第2行，索引1）
                    if len(rows) >= 2 and len(rows[1]) >= 7:
                        for j in range(1, 7):
                            if j < len(rows[1]) and rows[1][j].strip():
                                self.brass_table_entries[0][j].insert(0, rows[1][j])
                    
                    # 导入Z/mm数据（第3行，索引2）
                    if len(rows) >= 3 and len(rows[2]) >= 7:
                        for j in range(1, 7):
                            if j < len(rows[2]) and rows[2][j].strip():
                                self.brass_table_entries[1][j].insert(0, rows[2][j])
                    
                    # 不再导入样品参数，保持当前选择的样品类型和参数不变
                    messagebox.showinfo("提示", f"数据已从文件导入:\n{filename}\n")
                else:
                    messagebox.showwarning("警告", f"文件格式不正确，需要至少3行数据，当前有{len(rows)}行")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")
            
    def calculate_yang_modulus(self):
        """计算样品的杨氏模量（使用逐差法，支持任意组数）"""
        try:
            print("\n" + "="*60)
            print("【杨氏模量计算步骤 - 逐差法】")
            print("="*60)
            
            # 获取质量和位移数据
            masses = []  # g
            displacements = []  # mm
            
            for col in range(6):
                m_entry = self.brass_table_entries[0][col]
                z_entry = self.brass_table_entries[1][col]
                
                if m_entry and z_entry and m_entry.get().strip() and z_entry.get().strip():
                    m = float(m_entry.get())
                    z = float(z_entry.get())
                    masses.append(m)
                    displacements.append(z)
            
            n = len(masses)
            
            if n < 2:
                self.yang_modulus.set("数据不足(至少2组)")
                self.error_percent.set("---")
                print("错误: 数据不足，至少需要2组数据")
                print("="*60 + "\n")
                return
            
            # 单位转换
            d = self.length.get() / 100      # 23 cm = 0.23 m
            b = self.width.get() / 100       # 2.3 cm = 0.023 m
            a = self.thickness.get() / 1000  # 厚度根据样品类型变化
            g = 9.8
            
            # 根据样品类型设置理论值
            if self.sample_type == "黄铜":
                standard_value = 1.055e11  # 1.055 × 10^11 N/m²
                theory_display = "1.055×10¹¹"
            else:  # 铸铁
                standard_value = 1.851e11  # 1.851 × 10^11 N/m²
                theory_display = "1.851×10¹¹"
            
            # 显示理论值
            self.theory_value.set(theory_display)
            
            print(f"【样品参数】")
            print(f"  样品类型: {self.sample_type}")
            print(f"  横梁长度 d = {self.length.get():.1f} cm = {d:.4f} m")
            print(f"  横梁宽度 b = {self.width.get():.1f} cm = {b:.4f} m")
            print(f"  横梁厚度 a = {self.thickness.get():.3f} mm = {a:.6f} m")
            print(f"  重力加速度 g = {g} m/s²")
            print(f"  理论值 = {standard_value:.3e} N/m²")
            
            print(f"\n【原始实验数据】({n}组)")
            print(f"  {'序号':<6} {'M/g':<10} {'Z/mm':<10}")
            print(f"  {'-'*6} {'-'*10} {'-'*10}")
            for i in range(n):
                print(f"  {i+1:<6} {masses[i]:<10.1f} {displacements[i]:<10.3f}")
            
            # ========== 逐差法处理 ==========
            # 将数据分为前一半和后一半
            half = n // 2
            # 砝码间隔 = half 个砝码
            if n % 2 == 0:
                # 偶数：前half组和后half组配对
                delta_m = masses[half] - masses[0]  # g
                delta_z_list = []
                
                print(f"\n【逐差法处理】")
                print(f"  数据组数: {n} (偶数)")
                print(f"  将{n}组数据分为前{half}组和后{half}组进行逐差")
                print(f"  砝码间隔: {half}个砝码 = {delta_m:.0f} g")
                
                print(f"\n  {'组别':<8} {'前组M/g':<10} {'后组M/g':<10} {'前组Z/mm':<12} {'后组Z/mm':<12} {'ΔZ/mm':<10}")
                print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*12} {'-'*12} {'-'*10}")
                
                for i in range(half):
                    j = i + half
                    delta_z = displacements[j] - displacements[i]
                    delta_z_list.append(delta_z)
                    print(f"  {i+1}→{j+1:<4} {masses[i]:<10.1f} {masses[j]:<10.1f} {displacements[i]:<12.3f} {displacements[j]:<12.3f} {delta_z:<10.3f}")
                
                # 计算ΔZ的平均值
                avg_delta_z = sum(delta_z_list) / len(delta_z_list)
                
                print(f"\n  ΔZ平均值 = ({' + '.join([f'{z:.3f}' for z in delta_z_list])}) / {len(delta_z_list)} = {avg_delta_z:.4f} mm")
                
            else:
                # 奇数：去掉中间一组，剩余前后配对
                # 取前 half 组和后 half 组（跳过中间一组）
                delta_m = masses[half + 1] - masses[0]  # g
                delta_z_list = []
                
                print(f"\n【逐差法处理】")
                print(f"  数据组数: {n} (奇数)")
                print(f"  去掉中间第{half+1}组，用剩余{2*half}组数据进行逐差")
                print(f"  砝码间隔: {half+1}个砝码 = {delta_m:.0f} g")
                
                print(f"\n  {'组别':<8} {'前组M/g':<10} {'后组M/g':<10} {'前组Z/mm':<12} {'后组Z/mm':<12} {'ΔZ/mm':<10}")
                print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*12} {'-'*12} {'-'*10}")
                
                for i in range(half):
                    j = i + half + 1  # 跳过中间一组
                    delta_z = displacements[j] - displacements[i]
                    delta_z_list.append(delta_z)
                    print(f"  {i+1}→{j+1:<4} {masses[i]:<10.1f} {masses[j]:<10.1f} {displacements[i]:<12.3f} {displacements[j]:<12.3f} {delta_z:<10.3f}")
                
                # 计算ΔZ的平均值
                avg_delta_z = sum(delta_z_list) / len(delta_z_list)
                
                print(f"\n  ΔZ平均值 = ({' + '.join([f'{z:.3f}' for z in delta_z_list])}) / {len(delta_z_list)} = {avg_delta_z:.4f} mm")
            
            # 转换为米
            delta_z_m = avg_delta_z / 1000  # mm -> m
            delta_m_kg = delta_m / 1000     # g -> kg
            
            print(f"\n【杨氏模量计算】")
            print(f"  逐差法公式: E = (ΔF × d³) / (4 × b × a³ × ΔZ̄)")
            print(f"  其中:")
            print(f"    ΔF = Δm × g = {delta_m:.0f} × 10⁻³ kg × {g} m/s² = {delta_m_kg * g:.4f} N")
            print(f"    ΔZ̄ = {avg_delta_z:.4f} mm = {delta_z_m:.6f} m")
            print(f"    d³ = {d:.4f}³ = {d**3:.6f} m³")
            print(f"    a³ = {a:.6f}³ = {a**3:.9f} m³")
            print(f"    4 × b × a³ = 4 × {b:.4f} × {a**3:.9f} = {4*b*a**3:.9f} m⁴")
            
            # 计算杨氏模量
            delta_F = delta_m_kg * g
            E = (delta_F * d**3) / (4 * b * a**3 * delta_z_m)
            
            print(f"\n  E = ({delta_F:.4f} × {d**3:.6f}) / ({4*b*a**3:.9f} × {delta_z_m:.6f})")
            print(f"  E = {E:.3e} N/m²")
            
            # 计算相对误差
            relative_error = abs(E - standard_value) / standard_value * 100
            
            print(f"\n【计算结果】")
            print(f"  杨氏模量: E = {E:.3e} N/m²")
            print(f"  理论值: E₀ = {standard_value:.3e} N/m²")
            print(f"  相对误差: δ = |{E:.3e} - {standard_value:.3e}| / {standard_value:.3e} × 100% = {relative_error:.2f}%")
            
            # 显示结果
            self.yang_modulus.set(f"{E:.3e}")
            self.error_percent.set(f"{relative_error:.2f}")
            
            print("="*60 + "\n")
                
        except Exception as e:
            messagebox.showerror("错误", f"数据格式错误: {e}")
            self.yang_modulus.set("错误")
            self.error_percent.set("---")
            print(f"错误: {e}")
            print("="*60 + "\n")
            
    def on_tab_changed(self, event):
        """选项卡切换事件"""
        selected = self.notebook.tab(self.notebook.select(), "text")
        self.current_tab = selected


def main():
    root = tk.Tk()
    app = YangsModulusApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()