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

# 在程序开头添加获取资源路径的函数
def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和打包后的exe"""
    try:
        # 打包后exe的临时文件夹路径
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境的当前目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

def create_image_viewer():
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
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pa·dx=5, pady=5)
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
        
        # 计算截距函数
        def calculate_intercept():
            """根据选中的数据点拟合曲线并计算x轴截距"""
            selected = tree.selection()
            if len(selected) < 2:
                messagebox.showwarning("警告", "请至少选择两行数据进行拟合")
                return
            
            try:
                # 获取选中的数据点
                data_x = []
                data_y = []
                
                for item in selected:
                    values = tree.item(item, "values")
                    voltage = float(values[0])
                    current = float(values[1])
                    data_x.append(voltage)
                    data_y.append(current)
                
                # 将数据转换为numpy数组以便计算
                x = np.array(data_x)
                y = np.array(data_y)
                
                # 线性拟合 y = kx + b
                if len(x) >= 2:
                    # 计算线性回归系数
                    coeffs = np.polyfit(x, y, 1)  # 1次多项式拟合
                    k = coeffs[0]  # 斜率
                    b = coeffs[1]  # 截距
                    
                    # 计算x轴截距（y=0时的x值）
                    if abs(k) > 1e-10:  # 避免除以零
                        x_intercept = -b / k
                    else:
                        x_intercept = float('inf')  # 平行于x轴，无截距
                    
                    # 绘制拟合曲线
                    plot_fitted_line(x, y, k, b, x_intercept)
                    
                    # 显示结果
                    result_text = f"拟合直线方程: y = {k:.4f}x + {b:.4f}\n"
                    result_text += f"x轴截距: {x_intercept:.4f} V"
                    
                    messagebox.showinfo("拟合结果", result_text)
                else:
                    messagebox.showerror("错误", "数据点不足，无法进行拟合")
                    
            except Exception as e:
                messagebox.showerror("错误", f"计算截距时出错: {str(e)}")

        def plot_fitted_line(x_data, y_data, k, b, x_intercept):
            """绘制原始数据和拟合直线"""
            ax.clear()
            ax.set_title("伏安特性曲线")
            ax.set_xlabel("电压 (V)")
            ax.set_ylabel("电流 (mA)")
            ax.grid(True)
            
            # 绘制所有数据点
            if data_points:
                voltages = [point[0] for point in data_points]
                currents = [point[1] for point in data_points]
                
                # 所有数据的散点图（灰色）
                ax.scatter(voltages, currents, color='gray', alpha=0.5, zorder=3, label='所有数据点')
                
                # 所有数据的连线（浅蓝色）
                ax.plot(voltages, currents, 'b-', alpha=0.3, zorder=2, label='原始曲线')
            
            # 绘制选中的数据点（红色）
            ax.scatter(x_data, y_data, color='red', s=50, zorder=5, label='选中的数据点')
            
            # 绘制拟合直线
            x_min, x_max = min(x_data), max(x_data)
            x_fit = np.linspace(x_min - 0.1 * (x_max - x_min), 
                            x_max + 0.1 * (x_max - x_min), 100)
            y_fit = k * x_fit + b
            ax.plot(x_fit, y_fit, 'g--', linewidth=2, zorder=4, label=f'拟合直线: y={k:.4f}x+{b:.4f}')
            
            # 标记x轴截距点
            if abs(x_intercept) < float('inf'):
                ax.scatter([x_intercept], [0], color='orange', s=100, 
                        marker='x', zorder=6, label=f'x轴截距: {x_intercept:.4f}V')
                ax.axvline(x=x_intercept, color='orange', linestyle=':', alpha=0.5)
            
            # 添加图例
            ax.legend(loc='best', fontsize=9)
            
            # 设置坐标轴范围
            ax.set_xlim(min(min(x_data), x_intercept if abs(x_intercept) < float('inf') else min(x_data)) - 0.1,
                        max(max(x_data), x_intercept if abs(x_intercept) < float('inf') else max(x_data)) + 0.1)
            
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
            ("计算截距", calculate_intercept),  # 新增按钮
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
    voltmeter_label.grid(row=2, column=0, pady=(5, 3), sticky=tk.W)

    voltmeter_var = tk.StringVar(value="2V")

    # 创建电压表档位按钮框架
    voltmeter_frame = ttk.Frame(control_frame)
    voltmeter_frame.grid(row=3, column=0, pady=(0, 3), sticky=tk.W)

    # 电压表档位按钮
    voltmeter_buttons = []
    voltmeter_ranges = ['2V', '20V']

    for i, range_text in enumerate(voltmeter_ranges):
        btn = ttk.Radiobutton(voltmeter_frame, text=range_text, variable=voltmeter_var, 
                            value=range_text, command=on_voltmeter_change)
        btn.grid(row=0, column=i, padx=(0, 3))
        voltmeter_buttons.append(btn)
    
    # 电压调节滑块
    voltage_label = ttk.Label(control_frame, text="可调稳压电源 (0-15V)")
    voltage_label.grid(row=4, column=0, pady=(0, 3), sticky=tk.W)  # 减少垂直间距
    
    voltage_var = tk.DoubleVar(value=0.0)
    
    # 电源方向选择
    power_direction_label = ttk.Label(control_frame, text="电源方向:")
    power_direction_label.grid(row=7, column=0, pady=(10, 3), sticky=tk.W)

    power_direction_var = tk.StringVar(value="+")  # 默认正向

    # 创建方向选择按钮框架
    direction_frame = ttk.Frame(control_frame)
    direction_frame.grid(row=8, column=0, pady=(0, 3), sticky=tk.W)

    # 背景图选择变化时的回调函数
    def on_bg_change():
        """元件选择变化时更新电源方向状态"""
        selected_bg = bg_var.get()
        
        # 如果选择的是稳压管，启用反向按钮
        if selected_bg in ["稳压管2.1V", "稳压管4.3V", "稳压管6.8V"]:
            reverse_btn.config(state=tk.NORMAL)
        else:
            # 如果当前是反向，自动切换到正向
            if power_direction_var.get() == "-":
                power_direction_var.set("+")
                # 更新按钮状态
                for btn in button_widgets:
                    btn.config(state=tk.NORMAL)
            reverse_btn.config(state=tk.DISABLED)
        
        load_image()  # 原有的图片加载逻辑
        
    # # 修改所有元件选择按钮的命令
    # for i, (text, value) in enumerate(component_buttons):
    #     row = i // 2
    #     col = i % 2
        
    #     btn = ttk.Radiobutton(
    #         buttons_frame, 
    #         text=text, 
    #         variable=bg_var, 
    #         value=value,
    #         command=on_bg_change  # 修改这里
    #     )
    #     btn.grid(row=row, column=col, padx=2, pady=2, sticky=tk.W)
    #     button_widgets.append(btn)
    
    # 电源方向选择变化时的回调函数
    def on_direction_change():
        """电源方向变化时更新元件选择状态"""
        direction = power_direction_var.get()
        
        # 如果选择反向，只允许选择稳压管
        if direction == "-":
            for btn in button_widgets:
                btn_text = btn.cget("text")
                # 只启用稳压管相关的按钮
                if btn_text in ["2.1V稳压管", "4.3V稳压管", "6.8V稳压管"]:
                    btn.config(state=tk.NORMAL)
                else:
                    btn.config(state=tk.DISABLED)
            
            # 如果当前选择的是非稳压管，自动切换到第一个稳压管
            current_bg = bg_var.get()
            if current_bg not in ["稳压管2.1V", "稳压管4.3V", "稳压管6.8V"]:
                bg_var.set("稳压管2.1V")
                on_bg_change()
        else:
            # 正向时启用所有按钮
            for btn in button_widgets:
                btn.config(state=tk.NORMAL)
        
        on_bg_change()


    # 正向按钮
    forward_btn = ttk.Radiobutton(direction_frame, text="正向(+)", 
                                variable=power_direction_var, value="+",
                                command=on_direction_change)
    forward_btn.grid(row=0, column=0, padx=(0, 5))

    # 反向按钮
    reverse_btn = ttk.Radiobutton(direction_frame, text="反向(-)", 
                                variable=power_direction_var, value="-",
                                command=on_direction_change)
    reverse_btn.grid(row=0, column=1)

    # 电压滑块框架
    voltage_frame = ttk.Frame(control_frame)
    voltage_frame.grid(row=5, column=0, pady=(0, 3), sticky=(tk.W, tk.E))  # 减少垂直间距
    voltage_frame.columnconfigure(0, weight=1)
    
    voltage_scale = ttk.Scale(
        voltage_frame, 
        from_=0, 
        to=15, 
        orient=tk.HORIZONTAL,
        variable=voltage_var,
        length=150  # 减小滑块长度
    )
    voltage_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    # 长按功能相关变量
    voltage_press_id = None
    resistance_press_id = None
    press_delay = 300  # 首次延迟300ms
    press_interval = 100  # 长按时每100ms执行一次

    def start_voltage_up(event=None):
        """开始电压增加长按"""
        global voltage_press_id
        voltage_up()
        voltage_press_id = root.after(press_delay, repeat_voltage_up)

    def repeat_voltage_up():
        """重复电压增加"""
        global voltage_press_id
        voltage_up()
        voltage_press_id = root.after(press_interval, repeat_voltage_up)

    def start_voltage_down(event=None):
        """开始电压减少长按"""
        global voltage_press_id
        voltage_down()
        voltage_press_id = root.after(press_delay, repeat_voltage_down)

    def repeat_voltage_down():
        """重复电压减少"""
        global voltage_press_id
        voltage_down()
        voltage_press_id = root.after(press_interval, repeat_voltage_down)

    def stop_voltage_press(event=None):
        """停止电压长按"""
        global voltage_press_id
        if voltage_press_id:
            root.after_cancel(voltage_press_id)
            voltage_press_id = None

    def start_resistance_up(event=None):
        """开始电阻增加长按"""
        global resistance_press_id
        resistance_up()
        resistance_press_id = root.after(press_delay, repeat_resistance_up)

    def repeat_resistance_up():
        """重复电阻增加"""
        global resistance_press_id
        resistance_up()
        resistance_press_id = root.after(press_interval, repeat_resistance_up)

    def start_resistance_down(event=None):
        """开始电阻减少长按"""
        global resistance_press_id
        resistance_down()
        resistance_press_id = root.after(press_delay, repeat_resistance_down)

    def repeat_resistance_down():
        """重复电阻减少"""
        global resistance_press_id
        resistance_down()
        resistance_press_id = root.after(press_interval, repeat_resistance_down)

    def stop_resistance_press(event=None):
        """停止电阻长按"""
        global resistance_press_id
        if resistance_press_id:
            root.after_cancel(resistance_press_id)
            resistance_press_id = None

    # 电压微调按钮
    def voltage_up():
        current = voltage_var.get()
        if current < 15:
            voltage_var.set(round(current + 0.01, 2))
            update_voltage_display()
            update_display_values()
            draw_temp_dot(power_supply_dot_position_xi, "voltage")
    
    def voltage_down():
        current = voltage_var.get()
        if current > 0:
            voltage_var.set(round(current - 0.01, 2))
            update_voltage_display()
            update_display_values()
            draw_temp_dot(power_supply_dot_position_xi, "voltage")
    
    voltage_up_btn = ttk.Button(voltage_frame, text="+", width=2)
    voltage_up_btn.grid(row=0, column=1, padx=(3, 0))
    # 添加长按绑定
    voltage_up_btn.bind("<ButtonPress-1>", start_voltage_up)
    voltage_up_btn.bind("<ButtonRelease-1>", stop_voltage_press)

    voltage_down_btn = ttk.Button(voltage_frame, text="-", width=2)
    voltage_down_btn.grid(row=0, column=2, padx=(3, 0))
    # 添加长按绑定
    voltage_down_btn.bind("<ButtonPress-1>", start_voltage_down)
    voltage_down_btn.bind("<ButtonRelease-1>", stop_voltage_press)
    
    # 电压值显示和输入
    voltage_display_frame = ttk.Frame(control_frame)
    voltage_display_frame.grid(row=6, column=0, pady=(0, 10), sticky=tk.W)  # 减少垂直间距
    
    voltage_value = ttk.Label(voltage_display_frame, text="0.00 V")
    voltage_value.grid(row=0, column=0, padx=(0, 5))  # 减少水平间距
    
    voltage_entry = ttk.Entry(voltage_display_frame, width=6)  # 减小输入框宽度
    voltage_entry.grid(row=0, column=1)
    voltage_entry.insert(0, "0.00")
    
    
    def set_voltage_from_entry():
        try:
            value = float(voltage_entry.get())
            if 0 <= value <= 15:
                voltage_var.set(round(value, 2))
                update_voltage_display()
                update_display_values()
                draw_temp_dot(power_supply_dot_position, "voltage")
            else:
                messagebox.showerror("错误", "电压值必须在0-15V之间")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
        
    
    voltage_set_btn = ttk.Button(voltage_display_frame, text="设置", width=4, command=set_voltage_from_entry)  # 减小按钮宽度
    voltage_set_btn.grid(row=0, column=2, padx=(3, 0))  # 减少水平间距
    
    def update_voltage_display():
        voltage_value.config(text=f"{voltage_var.get():.2f} V")
        voltage_entry.delete(0, tk.END)
        voltage_entry.insert(0, f"{voltage_var.get():.2f}")
    
    
    
    # 电阻调节滑块
    resistance_label = ttk.Label(control_frame, text="可变电阻调节 (0-10KΩ)")
    resistance_label.grid(row=9, column=0, pady=(10, 3), sticky=tk.W)  # 减少垂直间距
    
    resistance_var = tk.IntVar(value=0)
    
    # 电阻滑块框架
    resistance_frame = ttk.Frame(control_frame)
    resistance_frame.grid(row=10, column=0, pady=(0, 3), sticky=(tk.W, tk.E))  # 减少垂直间距
    resistance_frame.columnconfigure(0, weight=1)
    
    resistance_scale = ttk.Scale(
        resistance_frame, 
        from_=0, 
        to=10000, 
        orient=tk.HORIZONTAL,
        variable=resistance_var,
        length=150  # 减小滑块长度
    )
    resistance_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    # 电阻微调按钮
    def resistance_up():
        current = resistance_var.get()
        if current < 10000:
            resistance_var.set(current + 1)
            update_resistance_display()
            update_display_values()
            draw_temp_dot(resistance_dot_position, "resistance")
    
    def resistance_down():
        current = resistance_var.get()
        if current > 0:
            resistance_var.set(current - 1)
            update_resistance_display()
            update_display_values()
            draw_temp_dot(resistance_dot_position, "resistance")
    
    resistance_up_btn = ttk.Button(resistance_frame, text="+", width=2)
    resistance_up_btn.grid(row=0, column=1, padx=(3, 0))
    # 添加长按绑定
    resistance_up_btn.bind("<ButtonPress-1>", start_resistance_up)
    resistance_up_btn.bind("<ButtonRelease-1>", stop_resistance_press)

    resistance_down_btn = ttk.Button(resistance_frame, text="-", width=2)
    resistance_down_btn.grid(row=0, column=2, padx=(3, 0))
    # 添加长按绑定
    resistance_down_btn.bind("<ButtonPress-1>", start_resistance_down)
    resistance_down_btn.bind("<ButtonRelease-1>", stop_resistance_press)
    
    # 电阻值显示和输入
    resistance_display_frame = ttk.Frame(control_frame)
    resistance_display_frame.grid(row=11, column=0, pady=(0, 15), sticky=tk.W)  # 减少垂直间距
    
    resistance_value = ttk.Label(resistance_display_frame, text="0 Ω")
    resistance_value.grid(row=0, column=0, padx=(0, 5))  # 减少水平间距
    
    resistance_entry = ttk.Entry(resistance_display_frame, width=6)  # 减小输入框宽度
    resistance_entry.grid(row=0, column=1)
    resistance_entry.insert(0, "0")
    
    def set_resistance_from_entry():
        try:
            value = int(resistance_entry.get())
            if 0 <= value <= 10000:
                resistance_var.set(value)
                update_resistance_display()
                update_display_values()
                draw_temp_dot(resistance_dot_position, "resistance")
            else:
                messagebox.showerror("错误", "电阻值必须在0-10000Ω之间")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的整数")
    
    resistance_set_btn = ttk.Button(resistance_display_frame, text="设置", width=4, command=set_resistance_from_entry)  # 减小按钮宽度
    resistance_set_btn.grid(row=0, column=2, padx=(3, 0))  # 减少水平间距
    
    def update_resistance_display():
        resistance = resistance_var.get()
        if resistance >= 1000:
            display_text = f"{resistance/1000:.2f} KΩ"
        else:
            display_text = f"{resistance} Ω"
        resistance_value.config(text=display_text)
        resistance_entry.delete(0, tk.END)
        resistance_entry.insert(0, str(resistance))
    
    # 滑块值变化时的回调函数
    def on_voltage_change(event):
        voltage_var.set(round(voltage_scale.get(), 2))
        update_voltage_display()
        update_display_values()
        draw_temp_dot(power_supply_dot_position, "voltage")
    
    def on_resistance_change(event):
        resistance_var.set(int(resistance_scale.get()))
        update_resistance_display()
        update_display_values()
        draw_temp_dot(resistance_dot_position, "resistance")
    
    voltage_scale.bind("<B1-Motion>", on_voltage_change)
    voltage_scale.bind("<ButtonRelease-1>", on_voltage_change)
    resistance_scale.bind("<B1-Motion>", on_resistance_change)
    resistance_scale.bind("<ButtonRelease-1>", on_resistance_change)
    
    # 选择待测元件区域
    bg_label = ttk.Label(control_frame, text="选择待测元件:")
    bg_label.grid(row=12, column=0, pady=(15, 3), sticky=tk.W)

    # 背景图选择变量
    bg_var = tk.StringVar(value="电阻")  # 默认选择电阻

    # 创建按钮组的容器框架
    buttons_frame = ttk.Frame(control_frame)
    buttons_frame.grid(row=13, column=0, pady=(5, 10), sticky=(tk.W, tk.E))

    # 定义所有按钮及其对应的值
    component_buttons = [
        ("电阻", "电阻"),
        ("二极管", "二极管"),
        ("2.1V稳压管", "稳压管2.1V"),
        # ("2.1V稳压管-", "稳压管2.1V反向"),
        ("4.3V稳压管", "稳压管4.3V"),
        # ("4.3V稳压管-", "稳压管4.3V反向"),
        ("6.8V稳压管", "稳压管6.8V"),
        # ("6.8V稳压管-", "稳压管6.8V反向"),
        ("红色LED", "红色LED"),
        ("黄色LED", "黄色LED"),
        ("绿色LED", "绿色LED"),
        ("小灯泡", "小灯泡")
    ]

    

    # 创建按钮
    button_widgets = []
    for i, (text, value) in enumerate(component_buttons):
        row = i // 2  # 每行4个按钮
        col = i % 2
        
        btn = ttk.Radiobutton(
            buttons_frame, 
            text=text, 
            variable=bg_var, 
            value=value,
            command=on_bg_change  # 选择变化时触发背景图更新
        )
        btn.grid(row=row, column=col, padx=2, pady=2, sticky=tk.W)
        button_widgets.append(btn)

    # 配置按钮框架的列权重，使按钮均匀分布
    for i in range(2):
        buttons_frame.columnconfigure(i, weight=1)
    
    # 当前图片路径
    current_image_path = ""
    
    # 电压和电流显示框
    voltage_display_box = None
    current_display_box = None
    
    # 二极管特性曲线数据
    diode_data = None
    zener_21V_data = None
    zener_43V_data = None
    zener_68V_data = None
    zener_21V_reverse_data = None
    zener_43V_reverse_data = None
    zener_68V_reverse_data = None
    red_led_data = None
    yellow_led_data = None
    green_led_data = None
    little_led_data = None
    
    # 加载特性曲线数据
    def load_characteristic_data():
        nonlocal diode_data, zener_21V_data, zener_43V_data, zener_68V_data
        nonlocal zener_21V_reverse_data, zener_43V_reverse_data, zener_68V_reverse_data
        nonlocal red_led_data, yellow_led_data, green_led_data, little_led_data
        try:
        # 使用 resource_path 获取数据目录
            data_dir = resource_path("data")
            
            # 加载普通二极管数据
            diode_path = os.path.join(data_dir, "普通二极管伏安特性曲线.xlsx")
            df_diode = pd.read_excel(diode_path)
            diode_data = df_diode.values
            
            # 加载2.1V稳压管数据
            zener_21V_path = os.path.join(data_dir, "2.1V稳压二极管伏安特性曲线.xlsx")
            df_zener_21V = pd.read_excel(zener_21V_path)
            zener_21V_data = df_zener_21V.values

            # 加载2.1V稳压管反向数据
            zener_21V_reverse_path = os.path.join(data_dir, "2.1V稳压二极管反向伏安特性曲线.xlsx")
            df_zener_21V_reverse = pd.read_excel(zener_21V_reverse_path)
            zener_21V_reverse_data = df_zener_21V_reverse.values
            
            # 加载4.3V稳压管数据
            zener_43V_path = os.path.join(data_dir, "4.3V稳压二极管伏安特性曲线.xlsx")
            df_zener_43V = pd.read_excel(zener_43V_path)
            zener_43V_data = df_zener_43V.values

            # 加载4.3V稳压管反向数据
            zener_43V_reverse_path = os.path.join(data_dir, "4.3V稳压二极管反向伏安特性曲线.xlsx")
            df_zener_43V_reverse = pd.read_excel(zener_43V_reverse_path)
            zener_43V_reverse_data = df_zener_43V_reverse.values
            
            # 加载6.8V稳压管数据
            zener_68V_path = os.path.join(data_dir, "6.8V稳压二极管伏安特性曲线.xlsx")
            df_zener_68V = pd.read_excel(zener_68V_path)
            zener_68V_data = df_zener_68V.values

            # 加载6.8V稳压管反向数据
            zener_68V_reverse_path = os.path.join(data_dir, "6.8V稳压二极管反向伏安特性曲线.xlsx")
            df_zener_68V_reverse = pd.read_excel(zener_68V_reverse_path)
            zener_68V_reverse_data = df_zener_68V_reverse.values

            # 加载红色LED数据
            red_led_path = os.path.join(data_dir, "红色发光二极管伏安特性曲线.xlsx")
            df_red_led = pd.read_excel(red_led_path)
            red_led_data = df_red_led.values
            
            # 加载黄色LED数据
            yellow_led_path = os.path.join(data_dir, "黄色发光二极管伏安特性曲线.xlsx")
            df_yellow_led = pd.read_excel(yellow_led_path)
            yellow_led_data = df_yellow_led.values
            
            # 加载绿色LED数据
            green_led_path = os.path.join(data_dir, "绿色发光二极管伏安特性曲线.xlsx")
            df_green_led = pd.read_excel(green_led_path)
            green_led_data = df_green_led.values

            #加载小灯泡数据
            little_led_path = os.path.join(data_dir, "小灯泡伏安特性曲线.xlsx")
            df_little_led = pd.read_excel(little_led_path)
            little_led_data = df_little_led.values
            
        except Exception as e:
            messagebox.showerror("错误", f"加载特性曲线数据失败: {str(e)}")
    
    # 通过线性插值获取电压值
    def get_voltage_from_data(current, data):
        if data is None:
            return 0
        
        # 确保电流是正值
        current = abs(current)
        
        # 找到当前值所在的区间
        for i in range(len(data) - 1):
            if data[i, 1] <= current <= data[i+1, 1]:
                # 线性插值
                x0, y0 = data[i, 1], data[i, 0]
                x1, y1 = data[i+1, 1], data[i+1, 0]
                
                if x1 == x0:  # 避免除以零
                    return y0
                
                return y0 + (y1 - y0) * (current - x0) / (x1 - x0)
        
        # 如果超出范围，返回边界值
        if current < data[0, 1]:
            return data[0, 0]
        else:
            return data[-1, 0]
    
    # 计算电流值的函数
    def calculate_current():
        selected_bg = bg_var.get()
        direction = power_direction_var.get()
        if selected_bg=="稳压管2.1V":
            if direction=="+":
                selected_bg = "稳压管2.1V正向"
            else:
                selected_bg = "稳压管2.1V反向"
        if selected_bg=="稳压管4.3V":
            if direction=="+":
                selected_bg = "稳压管4.3V正向"
            else:
                selected_bg = "稳压管4.3V反向"
        if selected_bg=="稳压管6.8V":
            if direction=="+":
                selected_bg = "稳压管6.8V正向"
            else:
                selected_bg = "稳压管6.8V反向"       
        ammeter_resistance = ammeter_resistance_map[ammeter_var.get()]
        
        if selected_bg == "电阻":
            # 电流 = voltage_var / (1.2 + resistance_var/1000 + 电流表内阻)
            current = voltage_var.get() / (1.2 + resistance_var.get()/1000 + ammeter_resistance/1000)
        elif selected_bg in ["二极管", "稳压管2.1V正向", "稳压管4.3V正向", "稳压管6.8V正向"]:
            if voltage_var.get() < 0.629:
                current = 0
            else:
                # 计算电流
                current = (voltage_var.get()-0.629) / (1.1 + resistance_var.get()/1000 + ammeter_resistance/1000)
        elif selected_bg in ["稳压管2.1V反向"]:
            if voltage_var.get() < 2.1:
                current = 0
            else:
                current = (voltage_var.get()-2.1) / (1.1 + resistance_var.get()/1000 + ammeter_resistance/1000)
        elif selected_bg in ["稳压管4.3V反向"]:
            if voltage_var.get() < 4.3:
                current = 0
            else:
                current = (voltage_var.get()-4.3) / (1.1 + resistance_var.get()/1000 + ammeter_resistance/1000)
        elif selected_bg in ["稳压管6.8V反向"]:
            if voltage_var.get() < 6.8:
                current = 0
            else:
                current = (voltage_var.get()-6.8) / (1.1 + resistance_var.get()/1000 + ammeter_resistance/1000)
        elif selected_bg in ["红色LED"]:
            if voltage_var.get() < 1.75:
                current = 0
            else:
                # 计算电流
                current = (voltage_var.get()-1.75) / (1.1 + resistance_var.get()/1000 + ammeter_resistance/1000)
        elif selected_bg in ["黄色LED"]:
            if voltage_var.get() < 1.8:
                current = 0
            else:
                # 计算电流
                current = (voltage_var.get()-1.8) / (1.1 + resistance_var.get()/1000 + ammeter_resistance/1000)
        elif selected_bg in ["绿色LED"]:
            if voltage_var.get() < 2.7:
                current = 0
            else:
                # 计算电流
                current = (voltage_var.get()-2.7) / (1.1 + resistance_var.get()/1000 + ammeter_resistance/1000)
        elif selected_bg in ["小灯泡"]:
                # 计算电流
                current = (voltage_var.get()) / (0.126 + ammeter_resistance/1000)
        else:
            # 对于其他器件，暂时显示0
            current = 0
        
        return current
    
    # 计算电压值的函数
    def calculate_voltage(current):
        selected_bg = bg_var.get()
        direction = power_direction_var.get()
        if selected_bg=="稳压管2.1V":
            if direction=="+":
                selected_bg = "稳压管2.1V正向"
            else:
                selected_bg = "稳压管2.1V反向"
        if selected_bg=="稳压管4.3V":
            if direction=="+":
                selected_bg = "稳压管4.3V正向"
            else:
                selected_bg = "稳压管4.3V反向"
        if selected_bg=="稳压管6.8V":
            if direction=="+":
                selected_bg = "稳压管6.8V正向"
            else:
                selected_bg = "稳压管6.8V反向"       
        if selected_bg == "电阻":
            # 电压 = 电流 / 10
            voltage = current / 10
        elif selected_bg == "二极管":
            # 从二极管特性曲线获取电压
            if current <= 0.01:
                # if voltage_var.get() < 0.4:
                #     voltage = 0
                # else:
                #     voltage = (voltage_var.get()-0.4)/(0.64-0.4)*0.392
                voltage = voltage_var.get()/0.64*0.392
            else:
                voltage = get_voltage_from_data(current, diode_data)
        elif selected_bg  == "稳压管2.1V正向":
            # 从2.1V稳压管特性曲线获取电压
            if current <= 0.06:
                # if voltage_var.get() < 0.5:
                #     voltage = 0
                # else:
                #     voltage = (voltage_var.get()-0.5)/(0.71-0.5)*0.62
                voltage = voltage_var.get()/0.71*0.62/0.611*0.6
            else:
                voltage = get_voltage_from_data(current, zener_21V_data)
        elif selected_bg == "稳压管2.1V反向":
            # 从2.1V稳压管特性曲线获取电压
            if current <= 0.03:
                # if voltage_var.get() < 1:
                #     voltage = 0
                # else:
                #     voltage = (voltage_var.get()-1)/(1.4-1)*0.62*1.01/1.75/1.011*1.002
                voltage = voltage_var.get()/(1.4)*0.62*1.01/1.75/1.011*1.002/0.54
            else:
                voltage = get_voltage_from_data(current, zener_21V_reverse_data)
        elif selected_bg == "稳压管4.3V正向":
            # 从4.3V稳压管特性曲线获取电压
            if current <= 0.06:
                # if voltage_var.get() < 0.5:
                #     voltage = 0
                # else:
                #     voltage = (voltage_var.get()-0.5)/(0.71-0.5)*0.62
                voltage = voltage_var.get()/0.71*0.62/0.611*0.6
            else:
                voltage = get_voltage_from_data(current, zener_43V_data)
        elif selected_bg == "稳压管4.3V反向":
            # 从4.3V稳压管特性曲线获取电压
            if current <= 0.03:
                # if voltage_var.get() < 2:
                #     voltage = 0
                # else:
                #     voltage = (voltage_var.get()-2)/(2.8-2)*0.62/1.81*2.06
                voltage = voltage_var.get()/(2.8)*0.62/1.81*2.06/1.09*2.04
            else:
                voltage = get_voltage_from_data(current, zener_43V_reverse_data)
        elif selected_bg == "稳压管6.8V正向":
            # 从6.8V稳压管特性曲线获取电压
            if current <= 0.06:
                # if voltage_var.get() < 0.5:
                #     voltage = 0
                # else:
                #     voltage = (voltage_var.get()-0.5)/(0.71-0.5)*0.62
                voltage = voltage_var.get()/0.71*0.62/0.611*0.6
            else:
                voltage = get_voltage_from_data(current, zener_68V_data)
        elif selected_bg == "稳压管6.8V反向":
            # 从6.8V稳压管特性曲线获取电压
            if current <= 0.035:
                # if voltage_var.get() < 4:
                #     voltage = 0
                # else:
                #     voltage = (voltage_var.get()-4)/(5.6-4)*0.62/1.1*3.26
                voltage = voltage_var.get()/(5.6)*0.62/1.1*3.26/2.24*3.22
            else:
                voltage = get_voltage_from_data(current, zener_68V_reverse_data)
        elif selected_bg == "红色LED":
            # 从红色LED特性曲线获取电压
            if current <= 0.06:
                # if voltage_var.get() < 1.5:
                #     voltage = 0
                # else:
                #     voltage = (voltage_var.get()-1.5)/(1.7-1.5)*0.62*1.6
                voltage = (voltage_var.get())/(1.7)*0.62*1.6/1.06*1.56
            else:
                voltage = get_voltage_from_data(current, red_led_data)
        elif selected_bg == "黄色LED":
            # 从黄色LED特性曲线获取电压
            if current <= 0.06:
                # if voltage_var.get() < 1.5:
                #     voltage = 0
                # else:
                    # voltage = (voltage_var.get()-1.5)/(1.7-1.5)*0.62*1.6*1.719/1.835
                voltage = (voltage_var.get())/(1.7)*0.62*1.6*1.719/1.835/1.02*1.69
            else:
                voltage = get_voltage_from_data(current, yellow_led_data)
        elif selected_bg == "绿色LED":
            # 从绿色LED特性曲线获取电压
            if current <= 0.02:
                # if voltage_var.get() < 2:
                #     voltage = 0
                # else:
                #     voltage = (voltage_var.get()-2)/(2.7-2)*0.62*1.6*3*2.21/1.36*2.21/4.97
                voltage = (voltage_var.get())/(2.7)*0.62*1.6*3*2.21/1.36*2.21/4.97/2.17*2.19
            else:
                voltage = get_voltage_from_data(current, green_led_data)
        elif selected_bg == "小灯泡":
            # 从小灯泡特性曲线获取电压
                voltage = get_voltage_from_data(current, little_led_data)
        else:
            # 对于其他器件，暂时显示0
            voltage = 0
        
        return voltage
    
    # 更新显示值的函数
    def update_display_values():
        nonlocal voltage_display_box, current_display_box
        
        # 清除之前的显示框
        if voltage_display_box:
            canvas.delete(voltage_display_box)
        if current_display_box:
            canvas.delete(current_display_box)
        
        # 计算电压和电流值
        current = calculate_current()
        voltage = calculate_voltage(current)

        selected_bg = bg_var.get()
        direction = power_direction_var.get()
        if selected_bg=="稳压管2.1V":
            if direction=="+":
                selected_bg = "稳压管2.1V正向"
            else:
                selected_bg = "稳压管2.1V反向"
        if selected_bg=="稳压管4.3V":
            if direction=="+":
                selected_bg = "稳压管4.3V正向"
            else:
                selected_bg = "稳压管4.3V反向"
        if selected_bg=="稳压管6.8V":
            if direction=="+":
                selected_bg = "稳压管6.8V正向"
            else:
                selected_bg = "稳压管6.8V反向"       

        if selected_bg in ["稳压管2.1V反向", "稳压管4.3V反向", "稳压管6.8V反向"]:
            current = -current  # 电流取反
            voltage = -voltage  # 电压取反

        
        # 检查是否超过档位限制
        max_current_map = {
            '200uA': 200,
            '2mA': 2,
            '20mA': 20,
            '200mA': 200
        }
        max_voltage_map = {
            '2V': 2,
            '20V': 20
        }
        
        max_current = max_current_map[ammeter_var.get()]
        max_voltage = max_voltage_map[voltmeter_var.get()]
        
        # 格式化显示文本
        voltage_display_text = ""
        current_display_text = ""
        
        # 如果是200uA档位，显示值乘以1000
        if ammeter_var.get() == '200uA':
            display_current = current * 1000  # 转换为uA单位
            if abs(display_current) <= max_current:
                current_display_text = f"{display_current:.1f}"
            elif display_current < -max_current:
                current_display_text = "-1  ."
            elif display_current > max_current:
                current_display_text = "1  ."
            current_text = current_display_text
        elif ammeter_var.get() == '2mA':
            if abs(current) <= max_current:
                current_display_text = f"{current:.3f}" 
            elif current < -max_current:
                current_display_text = "-1."
            elif current > max_current:
                current_display_text = "1."
            current_text = current_display_text
        elif ammeter_var.get() == '20mA':
            if abs(current) <= max_current:
                current_display_text = f"{current:.2f}"
            elif current < -max_current:
                current_display_text = "-1 ."
            elif current > max_current:
                current_display_text = "1 ."
            current_text = current_display_text
        elif ammeter_var.get() == '200mA':
            if abs(current) <= max_current:
                current_display_text = f"{current:.1f}"
            elif current < -max_current:
                current_display_text = "-1."
            elif current > max_current:
                current_display_text = "1."
            current_text = current_display_text
        if voltmeter_var.get() == '2V':
            if abs(voltage) <= max_voltage:
                voltage_display_text = f"{voltage:.3f}"
            elif voltage < -max_voltage:
                voltage_display_text = "-1."
            elif voltage > max_voltage:
                voltage_display_text = "1."
            voltage_text = voltage_display_text
        else: 
            voltage_display_text = f"{voltage:.2f}" if abs(voltage) <= max_voltage else "error"
            voltage_text = voltage_display_text
        
        # 创建显示框
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        # 电压显示框
        voltage_display_box = canvas.create_rectangle(
            80-10, 120+200, 
            180-10, 160+200, 
            fill="white", outline="black", width=2
        )
        canvas.create_text(
            130-10, 140+200, 
            text=voltage_text, 
            anchor=tk.CENTER, 
            font=("Arial", 20, "bold")
        )   
        # 电流显示框
        current_display_box = canvas.create_rectangle(
            80-10, 120, 
            180-10, 160, 
            fill="white", outline="black", width=2
        )
        canvas.create_text(
            130-10, 140, 
            text=current_text, 
            anchor=tk.CENTER, 
            font=("Arial", 20, "bold")
        )
        
        return voltage, current, voltage_display_text, current_display_text
    
    
    
    # ammeter_options.bind("<<ComboboxSelected>>", on_ammeter_change)
    # voltmeter_options.bind("<<ComboboxSelected>>", on_voltmeter_change)
    
    # 加载图片的函数
    def load_image(image_path=None):
        nonlocal current_image_path, voltage_display_box, current_display_box
        
        # 清除之前的显示框
        if voltage_display_box:
            canvas.delete(voltage_display_box)
            voltage_display_box = None
        if current_display_box:
            canvas.delete(current_display_box)
            current_display_box = None
        
        # 如果没有提供路径，使用当前选择的背景图
        if image_path is None:

            # 添加data子目录
            background_dir = resource_path("background")
            
            # 根据选择构建图片路径
            selected_bg = bg_var.get()
            direction = power_direction_var.get()
            if selected_bg=="稳压管2.1V":
                if direction=="+":
                    selected_bg = "稳压管2.1V正向"
                else:
                    selected_bg = "稳压管2.1V反向"
            if selected_bg=="稳压管4.3V":
                if direction=="+":
                    selected_bg = "稳压管4.3V正向"
                else:
                    selected_bg = "稳压管4.3V反向"
            if selected_bg=="稳压管6.8V":
                if direction=="+":
                    selected_bg = "稳压管6.8V正向"
                else:
                    selected_bg = "稳压管6.8V反向"       
            if selected_bg == "电阻":
                image_name = "电阻连线.png"
            elif selected_bg == "二极管":
                image_name = "二极管正向连线.png"
            elif selected_bg == "稳压管2.1V正向":
                image_name = "稳压管2.1V正向连线.png"
            elif selected_bg == "稳压管2.1V反向":
                image_name = "稳压管2.1V反向连线.png"
            elif selected_bg == "稳压管4.3V正向":   
                image_name = "稳压管4.3V正向连线.png"
            elif selected_bg == "稳压管4.3V反向":
                image_name = "稳压管4.3V反向连线.png"
            elif selected_bg == "稳压管6.8V正向":
                image_name = "稳压管6.8V正向连线.png"
            elif selected_bg == "稳压管6.8V反向":
                image_name = "稳压管6.8V反向连线.png"
            elif selected_bg == "红色LED":
                image_name = "LED红连线.png"
            elif selected_bg == "绿色LED":
                image_name = "LED绿连线.png"
            elif selected_bg == "黄色LED":
                image_name = "LED黄连线.png"
            elif selected_bg == "小灯泡":
                image_name = "小灯泡连线.png"
            else:  # 自定义背景图
                # 如果已经选择了自定义图片，使用它
                if current_image_path and "自定义" in current_image_path:
                    image_path = current_image_path
                else:
                    # 打开文件对话框选择图片
                    file_path = filedialog.askopenfilename(
                        title="选择背景图片",
                        filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
                    )
                    if file_path:
                        image_path = file_path
                        current_image_path = image_path
                    else:
                        # 如果没有选择文件，使用默认背景图（电阻）
                        image_name = "电阻连线.png"
                        bg_var.set("电阻")  # 设置为电阻选项
                
            # 如果没有自定义路径，使用程序目录中的图片
            if image_path is None:
                image_path = os.path.join(background_dir, image_name)
        
        try:
            # 打开并调整图片大小
            original_image = Image.open(image_path)
            # 调整图片大小以适应画布
            canvas.update()  # 确保画布尺寸已更新
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:  # 确保画布有有效尺寸
                # 保持图片宽高比
                img_ratio = original_image.width / original_image.height
                canvas_ratio = canvas_width / canvas_height
                
                if img_ratio > canvas_ratio:
                    # 图片更宽，以宽度为基准
                    new_width = canvas_width
                    new_height = int(canvas_width / img_ratio)
                else:
                    # 图片更高，以高度为基准
                    new_height = canvas_height
                    new_width = int(canvas_height * img_ratio)
                
                image = original_image.resize((new_width, new_height), Image.LANCZOS)
            else:
                # 如果画布尺寸无效，使用默认尺寸
                image = original_image.resize((400, 400), Image.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            
            # 在画布上显示图片
            canvas.delete("all")  # 清除之前的图片
            canvas.image = photo  # 保持引用避免被垃圾回收
            canvas.create_image(canvas_width//2, canvas_height//2, anchor=tk.CENTER, image=photo)
            
            # 更新当前图片路径
            current_image_path = image_path
            
            # 添加电压和电流显示框
            update_display_values()
            draw_indicator_dots()
            
        except FileNotFoundError:
            # 如果图片不存在，显示错误信息
            error_text = f"找不到图片文件:\n{image_path}"
            canvas.delete("all")
            canvas.create_text(canvas.winfo_width()//2, canvas.winfo_height()//2, 
                              text=error_text, fill="red", 
                              font=("Arial", 12), justify=tk.CENTER)
        except Exception as e:
            # 其他错误
            error_text = f"加载图片时出错:\n{str(e)}"
            canvas.delete("all")
            canvas.create_text(canvas.winfo_width()//2, canvas.winfo_height()//2, 
                              text=error_text, fill="red", 
                              font=("Arial", 12), justify=tk.CENTER)
    
    
    
    
    # 窗口调整大小时重新加载图片
    def on_resize(event):
        load_image()
    
    canvas.bind("<Configure>", on_resize)
    
    # 初始加载二极管数据
    load_characteristic_data()
    
    # 初始加载图片
    root.after(100, load_image)  # 短暂延迟确保窗口已创建
    # 初始化时调用一次方向变化回调
    root.after(100, on_direction_change)  # 短暂延迟后执行
    # 修改打开数据记录面板的按钮功能
    # data_panel_btn = ttk.Button(control_frame, text="数据记录面板", command=lambda: data_window.lift())
    # data_panel_btn.grid(row=11, column=0, pady=(15, 5), sticky=tk.W)
    
    # 运行主循环
    root.mainloop()

    # def on_closing():
    #     # 取消所有长按定时器
    #     global voltage_press_id, resistance_press_id
    #     if voltage_press_id:
    #         root.after_cancel(voltage_press_id)
    #     if resistance_press_id:
    #         root.after_cancel(resistance_press_id)
    #     root.destroy()]

    # root.protocol("WM_DELETE_WINDOW", on_closing)

if __name__ == "__main__":
    create_image_viewer()