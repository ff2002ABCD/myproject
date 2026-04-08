import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
# 设置matplotlib使用中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 使用黑体，如果不存在则使用DejaVu Sans
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def create_image_viewer():
    # 创建主窗口
    # 创建主窗口
    root = tk.Tk()
    root.title("FD-UI-D 线性与非线性元件伏安特性测量实验仪")
    root.geometry("1100x574")
    root.resizable(False, False)  # 禁止调整窗口大小
    
    # 定义 create_data_panel 函数
    def create_data_panel():
        data_window = tk.Toplevel(root)
        data_window.title("数据记录面板")
        data_window.geometry(f"437x675")
        
        # 禁止关闭窗口
        data_window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # 配置权重使窗口可调整大小
        data_window.columnconfigure(0, weight=1)
        data_window.rowconfigure(0, weight=1)
        data_window.rowconfigure(1, weight=1)
        data_window.rowconfigure(2, weight=0)  # 底部按钮区域不扩展
        
        # 创建上中下三个区域
        top_frame = ttk.LabelFrame(data_window, text="伏安特性曲线", padding="5")
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        top_frame.columnconfigure(0, weight=1)
        top_frame.rowconfigure(0, weight=1)
        
        middle_frame = ttk.LabelFrame(data_window, text="数据表格", padding="5")
        middle_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.rowconfigure(0, weight=1)
        
        bottom_frame = ttk.Frame(data_window, padding="5")
        bottom_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # 创建曲线图
        fig = plt.Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_title("伏安特性曲线")
        ax.set_xlabel("电压 (V)")
        ax.set_ylabel("电流 (mA)")
        ax.grid(True)
        
        canvas_fig = FigureCanvasTkAgg(fig, top_frame)
        canvas_fig.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建数据表格
        columns = ("电压 (V)", "电流 (mA)")
        tree = ttk.Treeview(middle_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(middle_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置权重
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.rowconfigure(0, weight=1)
        
        # 存储数据点
        data_points = []
        
        # 数据记录函数
        def record_data():
            # 获取显示值和显示文本
            voltage, current, voltage_display, current_display = update_display_values()
            
            # 如果显示错误，不记录数据
            if  voltage_display=="-1." or  voltage_display=="1." or current_display=="-1." or current_display=="1." or current_display=="-1." or current_display=="1 ." or current_display=="-1 ." or current_display=="1  ." or current_display=="-1  .":
                messagebox.showwarning("警告", "当前数值超出量程，无法记录")
                return
            
            # 转换为mA单位
            current_ma = current
            
            # 根据显示精度确定小数位数
            def get_decimal_places(display_text):
                if '.' in display_text:
                    return len(display_text.split('.')[1])
                return 0
            
            voltage_decimal = get_decimal_places(voltage_display)
            current_decimal = get_decimal_places(current_display)

            ammeter_range = ammeter_var.get()
            if ammeter_range == '200uA':
                current_decimal = 3   # 强制设置为3位小数
            
            # 格式化数据
            voltage_formatted = round(voltage, voltage_decimal)
            current_formatted = round(current_ma, current_decimal)
            
            # 检查是否已存在相同电压的数据点
            for i, (v, c) in enumerate(data_points):
                if abs(v - voltage_formatted) < 0.001:  # 考虑浮点数精度
                    # 更新现有数据点
                    data_points[i] = (voltage_formatted, current_formatted)
                    
                    # 更新表格
                    for item in tree.get_children():
                        if abs(float(tree.item(item, "values")[0]) - voltage_formatted) < 0.001:
                            tree.item(item, values=(f"{voltage_formatted:.{voltage_decimal}f}", 
                                                f"{current_formatted:.{current_decimal}f}"))
                            break
                    
                    # 重新绘制曲线
                    plot_data()
                    return
            
            # 添加新数据点
            data_points.append((voltage_formatted, current_formatted))
            
            # 按电压排序
            data_points.sort(key=lambda x: x[0])
            
            # 更新表格
            update_table()
            
            # 绘制曲线
            plot_data()
        
        def update_table():
            # 清空表格
            for item in tree.get_children():
                tree.delete(item)
            
            # 添加数据，保持原有精度
            for voltage, current in data_points:
                # 根据数值确定小数位数
                voltage_str = f"{voltage:.3f}" if isinstance(voltage, float) and voltage != int(voltage) else f"{voltage:.0f}"
                current_str = f"{current:.3f}" if isinstance(current, float) and current != int(current) else f"{current:.0f}"
                tree.insert("", tk.END, values=(voltage_str, current_str))
        
        # 绘制曲线函数
        def plot_data():
            ax.clear()
            ax.set_title("伏安特性曲线")
            ax.set_xlabel("电压 (V)")
            ax.set_ylabel("电流 (mA)")
            ax.grid(True)
            
            if data_points:
                voltages = [point[0] for point in data_points]
                currents = [point[1] for point in data_points]
                
                # 散点图
                ax.scatter(voltages, currents, color='red', zorder=5)
                
                # 连线（按电压从小到大）
                ax.plot(voltages, currents, 'b-', zorder=4)
            
            canvas_fig.draw()
        
        # 计算函数（已包含在plot_data中）
        def calculate_data():
            plot_data()
        
        # 删除选中行函数
        def delete_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("警告", "请先选择要删除的行")
                return
            
            for item in selected:
                values = tree.item(item, "values")
                voltage = float(values[0])
                
                # 从数据点中删除
                for i, (v, c) in enumerate(data_points):
                    if abs(v - voltage) < 0.001:
                        data_points.pop(i)
                        break
                
                # 从表格中删除
                tree.delete(item)
            
            # 重新绘制曲线
            plot_data()
        
        # 清空数据函数
        def clear_data():
            if not data_points:
                return
            
            if messagebox.askyesno("确认", "确定要清空所有数据吗？"):
                data_points.clear()
                for item in tree.get_children():
                    tree.delete(item)
                plot_data()
        
        # 导入数据函数
        def import_data():
            file_path = filedialog.askopenfilename(
                title="选择Excel文件",
                filetypes=[("Excel文件", "*.xlsx *.xls")]
            )
            
            if not file_path:
                return
            
            try:
                df = pd.read_excel(file_path)
                
                # 检查列名
                if "电压 (V)" not in df.columns or "电流 (mA)" not in df.columns:
                    messagebox.showerror("错误", "Excel文件必须包含'电压 (V)'和'电流 (mA)'列")
                    return
                
                # 清空现有数据
                data_points.clear()
                
                # 导入新数据
                for _, row in df.iterrows():
                    voltage = row["电压 (V)"]
                    current = row["电流 (mA)"]
                    data_points.append((voltage, current))
                
                # 按电压排序
                data_points.sort(key=lambda x: x[0])
                
                # 更新表格
                update_table()
                
                # 绘制曲线
                plot_data()
                
                messagebox.showinfo("成功", "数据导入成功")
                
            except Exception as e:
                messagebox.showerror("错误", f"导入数据失败: {str(e)}")
        
        # 导出数据函数
        def export_data():
            if not data_points:
                messagebox.showwarning("警告", "没有数据可导出")
                return
            
            file_path = filedialog.asksaveasfilename(
                title="保存Excel文件",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx")]
            )
            
            if not file_path:
                return
            
            try:
                df = pd.DataFrame(data_points, columns=["电压 (V)", "电流 (mA)"])
                df.to_excel(file_path, index=False)
                messagebox.showinfo("成功", "数据导出成功")
                
            except Exception as e:
                messagebox.showerror("错误", f"导出数据失败: {str(e)}")
        
        # 创建按钮
        buttons = [
            ("数据记录", record_data),
            # ("计算", calculate_data),
            ("删除选中行", delete_selected),
            ("清空数据", clear_data),
            ("导入数据", import_data),
            ("导出数据", export_data)
        ]
        
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(bottom_frame, text=text, command=command)
            btn.grid(row=0, column=i, padx=5)
        
        # 配置底部按钮区域的权重
        for i in range(len(buttons)):
            bottom_frame.columnconfigure(i, weight=1)
            
        return data_window
    
    # 创建数据记录面板
    data_window = create_data_panel()
    
    # 设置更小的默认字体
    default_font = ("Arial", 9)
    root.option_add("*Font", default_font)
    
    # 主框架
    main_frame = ttk.Frame(root, padding="5")  # 减少内边距
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # 配置网格权重，使内容随窗口调整大小
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=6)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(0, weight=1)
    
    # 图片显示区域
    img_frame = ttk.LabelFrame(main_frame, text="实验仪器面板", padding="3")  # 减少内边距
    img_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))  # 减少右边距
    img_frame.columnconfigure(0, weight=1)
    img_frame.rowconfigure(0, weight=1)
    
    # 创建画布用于显示图片
    canvas = tk.Canvas(img_frame, bg='white')
    canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # 控制面板区域
    control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="5")  # 减少内边距
    control_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
    control_frame.columnconfigure(0, weight=1)
    
    # 档位选择变化时的回调函数
    def on_ammeter_change():
        update_display_values()
        draw_indicator_dots()
    
    def on_voltmeter_change():
        update_display_values()
        draw_indicator_dots()

    ammeter_dot_positions = {
        '200uA': (50+41, 208),   # 示例坐标，需要根据实际背景图调整
        '2mA': (50+65, 208),
        '20mA': (50+89, 208),
        '200mA': (50+113, 208)
    }

    # 电压表档位红点位置 (x, y)
    voltmeter_dot_positions = {
        '2V': (50+64, 410),    # 示例坐标，需要根据实际背景图调整
        '20V': (50+90, 410)
    }

    # 红点大小
    dot_radius = 5  # 红点半径

    def draw_indicator_dots():
        """绘制电流表和电压表的档位指示红点"""
        # 清除之前的红点
        canvas.delete("indicator_dot")
        
        # 获取当前档位
        ammeter_range = ammeter_var.get()
        voltmeter_range = voltmeter_var.get()
        
        # 绘制电流表红点
        if ammeter_range in ammeter_dot_positions:
            x, y = ammeter_dot_positions[ammeter_range]
            canvas.create_oval(x-dot_radius, y-dot_radius, 
                            x+dot_radius, y+dot_radius,
                            fill="red", outline="red", tags="indicator_dot")
        
        # 绘制电压表红点
        if voltmeter_range in voltmeter_dot_positions:
            x, y = voltmeter_dot_positions[voltmeter_range]
            canvas.create_oval(x-dot_radius, y-dot_radius, 
                            x+dot_radius, y+dot_radius,
                            fill="red", outline="red", tags="indicator_dot")

    # 在代码开头添加红点位置定义和样式
    # 可调稳压电源红点位置 (根据实际背景图调整)
    power_supply_dot_position = (200+100, 300+158)  # 示例坐标
    power_supply_dot_position_xi =(200+175, 300+158)  # 示例坐标

    # 可变电阻红点位置 (根据实际背景图调整)
    resistance_dot_position = (250+385, 350+88)    # 示例坐标

    # 临时红点样式
    temp_dot_radius = 6          # 红点半径
    temp_dot_color = "red"       # 红点颜色
    temp_dot_duration = 200      # 显示持续时间(ms)

    def draw_temp_dot(position, dot_type):
        """绘制临时红点并在指定时间后消失"""
        x, y = position
        
        # 绘制红点
        dot = canvas.create_oval(x-temp_dot_radius, y-temp_dot_radius,
                                x+temp_dot_radius, y+temp_dot_radius,
                                fill=temp_dot_color, outline=temp_dot_color,
                                tags=f"temp_dot_{dot_type}")
        
        # 设置定时器让红点消失
        root.after(temp_dot_duration, lambda: canvas.delete(dot))

    # 电流表档位选择 - 修改为按钮
    ammeter_label = ttk.Label(control_frame, text="电流表档位:")
    ammeter_label.grid(row=0, column=0, pady=(0, 3), sticky=tk.W)

    ammeter_var = tk.StringVar(value="200uA")

    # 创建电流表档位按钮框架
    ammeter_frame = ttk.Frame(control_frame)
    ammeter_frame.grid(row=1, column=0, pady=(0, 3), sticky=tk.W)

    # 电流表档位按钮``
    ammeter_buttons = []
    ammeter_ranges = ['200uA', '2mA', '20mA', '200mA']

    for i, range_text in enumerate(ammeter_ranges):
        btn = ttk.Radiobutton(ammeter_frame, text=range_text, variable=ammeter_var, 
                            value=range_text, command=on_ammeter_change)
        btn.grid(row=0, column=i, padx=(0, 3))
        ammeter_buttons.append(btn)
    
    # 电流表内阻映射
    ammeter_resistance_map = {
        '200uA': 10000,  # 10KΩ
        '2mA': 1000,     # 1KΩ
        '20mA': 100,     # 100Ω
        '200mA': 10      # 10Ω
    }

    # 电压表档位选择 - 修改为按钮
    voltmeter_label = ttk.Label(control_frame, text="电压表档位:")
    voltmeter_label.grid(row=2, column=0, pady=(3, 3), sticky=tk.W)

    voltmeter_var = tk.StringVar(value="2V")

    # 创建电压表档位按钮框架
    voltmeter_frame = ttk.Frame(control_frame)
    voltmeter_frame.grid(row=3, column=0, pady=(0, 3), sticky=tk.W)

    voltmeter_buttons = []
    voltmeter_ranges = ['2V', '20V']

    for i, range_text in enumerate(voltmeter_ranges):
        btn = ttk.Radiobutton(voltmeter_frame, text=range_text, variable=voltmeter_var, 
                            value=range_text, command=on_voltmeter_change)
        btn.grid(row=0, column=i, padx=(0, 3))
        voltmeter_buttons.append(btn)
    
    # 电压表内阻映射
    voltmeter_resistance_map = {
        '2V': 1000,   # 1KΩ
        '20V': 10000  # 10KΩ
    }

    # 可调稳压电源控制
    power_label = ttk.Label(control_frame, text="可调稳压电源:")
    power_label.grid(row=4, column=0, pady=(10, 3), sticky=tk.W)

    power_var = tk.DoubleVar(value=0.0)
    power_scale = ttk.Scale(control_frame, from_=0.0, to=20.0, orient=tk.HORIZONTAL,
                        variable=power_var, command=lambda x: update_display_values())
    power_scale.grid(row=5, column=0, pady=(0, 3), sticky=(tk.W, tk.E))

    power_value_label = ttk.Label(control_frame, text="0.0 V")
    power_value_label.grid(row=6, column=0, pady=(0, 3), sticky=tk.W)

    # 电源方向选择
    power_direction_label = ttk.Label(control_frame, text="电源方向:")
    power_direction_label.grid(row=7, column=0, pady=(10, 3), sticky=tk.W)

    power_direction_var = tk.StringVar(value="+")  # 默认为正向

    # 创建电源方向选择按钮框架
    power_direction_frame = ttk.Frame(control_frame)
    power_direction_frame.grid(row=8, column=0, pady=(0, 3), sticky=tk.W)

    # 正向按钮
    direction_plus_btn = ttk.Radiobutton(power_direction_frame, text="+", 
                                       variable=power_direction_var, value="+",
                                       command=update_display_values)
    direction_plus_btn.grid(row=0, column=0, padx=(0, 5))

    # 负向按钮
    direction_minus_btn = ttk.Radiobutton(power_direction_frame, text="-", 
                                        variable=power_direction_var, value="-",
                                        command=update_display_values)
    direction_minus_btn.grid(row=0, column=1)

    # 可变电阻控制
    resistance_label = ttk.Label(control_frame, text="可变电阻:")
    resistance_label.grid(row=9, column=0, pady=(10, 3), sticky=tk.W)

    resistance_var = tk.DoubleVar(value=0.0)
    resistance_scale = ttk.Scale(control_frame, from_=0.0, to=100.0, orient=tk.HORIZONTAL,
                            variable=resistance_var, command=lambda x: update_display_values())
    resistance_scale.grid(row=10, column=0, pady=(0, 3), sticky=(tk.W, tk.E))

    resistance_value_label = ttk.Label(control_frame, text="0.0 Ω")
    resistance_value_label.grid(row=11, column=0, pady=(0, 3), sticky=tk.W)

    # 待测元件选择
    component_label = ttk.Label(control_frame, text="待测元件:")
    component_label.grid(row=12, column=0, pady=(10, 3), sticky=tk.W)

    # 修改元件选项，去掉稳压管的+/-符号
    component_options = ["电阻", "二极管", "稳压管", "白炽灯", "小灯泡"]
    component_var = tk.StringVar(value="电阻")

    component_combo = ttk.Combobox(control_frame, textvariable=component_var, 
                                values=component_options, state="readonly")
    component_combo.grid(row=13, column=0, pady=(0, 3), sticky=(tk.W, tk.E))
    component_combo.bind("<<ComboboxSelected>>", lambda e: update_display_values())

    # 稳压管选择
    zener_label = ttk.Label(control_frame, text="稳压管类型:")
    zener_label.grid(row=14, column=0, pady=(10, 3), sticky=tk.W)

    zener_options = ["2.1V", "4.3V", "6.8V"]
    zener_var = tk.StringVar(value="2.1V")

    zener_combo = ttk.Combobox(control_frame, textvariable=zener_var, 
                            values=zener_options, state="readonly")
    zener_combo.grid(row=15, column=0, pady=(0, 3), sticky=(tk.W, tk.E))
    zener_combo.bind("<<ComboboxSelected>>", lambda e: update_display_values())

    # 显示区域
    display_label = ttk.Label(control_frame, text="测量显示:")
    display_label.grid(row=16, column=0, pady=(10, 3), sticky=tk.W)

    display_frame = ttk.Frame(control_frame)
    display_frame.grid(row=17, column=0, pady=(0, 10), sticky=(tk.W, tk.E))

    voltage_label = ttk.Label(display_frame, text="电压: 0.000 V")
    voltage_label.grid(row=0, column=0, sticky=tk.W)

    current_label = ttk.Label(display_frame, text="电流: 0.000 mA")
    current_label.grid(row=1, column=0, sticky=tk.W)

    # 控制按钮
    button_frame = ttk.Frame(control_frame)
    button_frame.grid(row=18, column=0, pady=(10, 0), sticky=(tk.W, tk.E))

    # 添加重置按钮
    reset_button = ttk.Button(button_frame, text="重置", command=reset_system)
    reset_button.grid(row=0, column=0, padx=(0, 5))

    # 添加退出按钮
    exit_button = ttk.Button(button_frame, text="退出", command=root.quit)
    exit_button.grid(row=0, column=1)

    # 配置控制面板的列权重
    control_frame.columnconfigure(0, weight=1)
    for i in range(19):  # 0到18行
        control_frame.rowconfigure(i, weight=0)

    # 加载图片
    def load_image():
        try:
            # 获取当前脚本所在目录
            if getattr(sys, 'frozen', False):
                # 如果是打包后的可执行文件
                base_path = sys._MEIPASS
            else:
                # 如果是脚本文件
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            image_path = os.path.join(base_path, "FD-UI-D.png")
            
            # 加载图片
            image = Image.open(image_path)
            
            # 调整图片大小以适应窗口
            max_width = 800
            max_height = 550
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            return ImageTk.PhotoImage(image)
            
        except Exception as e:
            print(f"加载图片失败: {e}")
            return None

    # 显示图片
    image = load_image()
    if image:
        canvas.create_image(0, 0, anchor=tk.NW, image=image)
        canvas.config(scrollregion=canvas.bbox(tk.ALL))
        canvas.image = image  # 保持引用

    # 更新显示值的函数
    def update_display_values():
        # 获取当前设置
        power_voltage = power_var.get()
        resistance_value = resistance_var.get()
        ammeter_range = ammeter_var.get()
        voltmeter_range = voltmeter_var.get()
        component = component_var.get()
        zener_type = zener_var.get()
        power_direction = power_direction_var.get()
        
        # 更新电源电压显示
        power_value_label.config(text=f"{power_voltage:.1f} V")
        
        # 更新电阻值显示
        resistance_value_label.config(text=f"{resistance_value:.1f} Ω")
        
        # 检查电源方向和元件选择的约束
        if power_direction == "-" and component != "稳压管":
            # 电源方向为负时，只能选择稳压管
            messagebox.showerror("错误", "电源方向为负时，只能选择稳压管")
            power_direction_var.set("+")
            return None, None, None, None
        
        if component != "稳压管" and power_direction == "-":
            # 选择非稳压管元件时，电源方向不能为负
            messagebox.showerror("错误", "选择非稳压管元件时，电源方向不能为负")
            power_direction_var.set("+")
            return None, None, None, None
        
        # 根据电源方向调整电源电压
        effective_power_voltage = power_voltage if power_direction == "+" else -power_voltage
        
        # 根据元件类型计算实际电压和电流
        if component == "电阻":
            # 简单电阻模型
            R_component = 100  # 假设电阻为100Ω
            total_resistance = resistance_value + R_component + ammeter_resistance_map[ammeter_range]
            current = effective_power_voltage / total_resistance if total_resistance != 0 else 0
            voltage = current * R_component
            
        elif component == "二极管":
            # 二极管模型 (简单PN结模型)
            R_component = 1e6  # 反向电阻很大
            if effective_power_voltage > 0.7:  # 正向偏置
                # 正向导通，有0.7V压降
                voltage = 0.7
                current = (effective_power_voltage - 0.7) / (resistance_value + ammeter_resistance_map[ammeter_range])
            else:  # 反向偏置
                current = 0
                voltage = 0
                
        elif component == "稳压管":
            # 根据电源方向确定稳压管的工作模式
            if power_direction == "+":
                # 正向相当于二极管
                if effective_power_voltage > 0.7:  # 正向偏置
                    voltage = 0.7
                    current = (effective_power_voltage - 0.7) / (resistance_value + ammeter_resistance_map[ammeter_range])
                else:  # 反向偏置或不导通
                    current = 0
                    voltage = 0
            else:  # 电源方向为负
                # 反向击穿稳压
                zener_voltage = float(zener_type[:-1])  # 从"2.1V"中提取2.1
                if abs(effective_power_voltage) > zener_voltage:  # 击穿稳压
                    voltage = -zener_voltage  # 负电压
                    current = -(abs(effective_power_voltage) - zener_voltage) / (resistance_value + ammeter_resistance_map[ammeter_range])
                else:  # 未击穿
                    current = 0
                    voltage = 0
                    
        elif component == "白炽灯":
            # 白炽灯模型 (非线性电阻)
            R_component = 10 + effective_power_voltage * 2  # 随电压增加而增加
            total_resistance = resistance_value + R_component + ammeter_resistance_map[ammeter_range]
            current = effective_power_voltage / total_resistance if total_resistance != 0 else 0
            voltage = current * R_component
            
        elif component == "小灯泡":
            # 小灯泡模型
            R_component = 5 + effective_power_voltage * 1  # 随电压增加而增加
            total_resistance = resistance_value + R_component + ammeter_resistance_map[ammeter_range]
            current = effective_power_voltage / total_resistance if total_resistance != 0 else 0
            voltage = current * R_component
        
        # 根据档位确定显示精度
        def get_display_value(actual_value, meter_range, is_voltmeter=False):
            range_max = float(meter_range[:-1]) if meter_range.endswith('V') else float(meter_range[:-2])
            
            if is_voltmeter:
                # 电压表处理
                if meter_range == '2V':
                    display_value = round(actual_value, 3)
                    display_text = f"{display_value:.3f}"
                else:  # 20V
                    display_value = round(actual_value, 2)
                    display_text = f"{display_value:.2f}"
            else:
                # 电流表处理
                if meter_range == '200uA':
                    display_value = actual_value * 1000  # A to mA
                    display_value = round(display_value, 3)
                    display_text = f"{display_value:.3f}"
                elif meter_range == '2mA':
                    display_value = actual_value * 1000  # A to mA
                    display_value = round(display_value, 2)
                    display_text = f"{display_value:.2f}"
                elif meter_range == '20mA':
                    display_value = actual_value * 1000  # A to mA
                    display_value = round(display_value, 1)
                    display_text = f"{display_value:.1f}"
                else:  # 200mA
                    display_value = actual_value * 1000  # A to mA
                    display_value = round(display_value, 0)
                    display_text = f"{display_value:.0f}"
            
            # 检查是否超量程
            if abs(display_value) > range_max * 1.2:  # 允许20%的过载
                return "超量程", "超量程"
            
            return display_value, display_text
        
        # 获取显示值和显示文本
        voltage_display, voltage_text = get_display_value(voltage, voltmeter_range, is_voltmeter=True)
        current_display, current_text = get_display_value(current, ammeter_range, is_voltmeter=False)
        
        # 更新显示标签
        voltage_label.config(text=f"电压: {voltage_text} V")
        current_label.config(text=f"电流: {current_text} mA")
        
        # 返回实际值和显示文本
        return voltage, current, voltage_text, current_text

    # 重置系统函数
    def reset_system():
        power_var.set(0.0)
        resistance_var.set(0.0)
        ammeter_var.set("200uA")
        voltmeter_var.set("2V")
        component_var.set("电阻")
        zener_var.set("2.1V")
        power_direction_var.set("+")
        update_display_values()
        draw_indicator_dots()

    # 初始化显示
    update_display_values()
    draw_indicator_dots()

    # 运行主循环
    root.mainloop()

# 启动程序
if __name__ == "__main__":
    create_image_viewer()