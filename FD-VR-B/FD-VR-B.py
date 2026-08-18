import sys
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def get_resource_path(relative_path):
    """获取资源的绝对路径，支持打包后的环境"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class ResonanceExperimentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("受迫振动与共振实验")
        self.root.geometry("1400x800")
        
        # 数据存储
        self.frequencies = []  # 频率列表
        self.amplitudes = []   # 振幅列表
        self.table_vars = {}   # 表格数据存储
        
        # 创建界面
        self.setup_ui()
        
        # 初始化表格数据
        self.init_table_data()
        
    def setup_ui(self):
        """创建界面布局"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧面板（左上+左下）
        left_panel = ttk.Frame(main_frame, width=700)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        left_panel.pack_propagate(False)
        
        # 左上区域 - 实验装置
        self.setup_experiment_device(left_panel)
        
        # 左下区域 - 实验操作
        self.setup_experiment_control(left_panel)
        
        # 右侧区域 - 数据记录区域
        self.setup_data_recording(main_frame)
        
    def setup_experiment_device(self, parent):
        """左上区域：实验装置"""
        device_frame = ttk.LabelFrame(parent, text="实验装置", padding=5)
        device_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 加载图片
        try:
            img_path = get_resource_path("background/主机.jpg")
            from PIL import Image, ImageTk
            pil_img = Image.open(img_path)
            pil_img = pil_img.resize((700, 450), Image.Resampling.LANCZOS)
            self.device_img = ImageTk.PhotoImage(pil_img)
            img_label = ttk.Label(device_frame, image=self.device_img)
            img_label.pack()
        except Exception as e:
            print(f"图片加载错误: {e}")
            img_label = ttk.Label(device_frame, text="[主机.jpg 图片加载失败]\n请检查 background/主机.jpg 文件", 
                                  background="#ddd", width=50, height=15)
            img_label.pack()
        
        # 在图片上叠加文本框（使用Frame模拟叠加）
        overlay_frame = tk.Frame(device_frame, bg='white', bd=1)
        overlay_frame.place(relx=0.14, rely=0.67, anchor='center', width=100, height=50)
        
        # 频率和振幅显示
        self.freq_display_var = tk.StringVar(value="频率：250.35 Hz")
        self.amp_display_var = tk.StringVar(value="振幅：1166 mV")
        
        freq_label = tk.Label(overlay_frame, textvariable=self.freq_display_var, 
                              font=("Microsoft YaHei", 8), bg='white')
        freq_label.pack(pady=(5, 0))
        amp_label = tk.Label(overlay_frame, textvariable=self.amp_display_var,
                             font=("Microsoft YaHei", 8), bg='white')
        amp_label.pack()
        
    def setup_experiment_control(self, parent):
        """左下区域：实验操作"""
        control_frame = ttk.LabelFrame(parent, text="实验操作", padding=10)
        control_frame.pack(fill=tk.BOTH, expand=True)
        
        # 振动频率滑块
        ttk.Label(control_frame, text="振动频率 (246-254 Hz):").pack(anchor=tk.W, pady=(0, 5))  # 修改范围文字
        self.freq_slider = ttk.Scale(control_frame, from_=246, to=254,  # 修改滑块范围
                                    orient=tk.HORIZONTAL, length=350)
        self.freq_slider.pack(fill=tk.X, pady=(0, 5))
        
        self.freq_value_var = tk.StringVar(value="250.35 Hz")
        freq_value_label = ttk.Label(control_frame, textvariable=self.freq_value_var, 
                                    font=("Microsoft YaHei", 10))
        freq_value_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 绑定滑块事件 - 改为小数点后2位
        def on_freq_change(val):
            freq = round(float(val), 2)  # 改为保留2位小数
            self.freq_value_var.set(f"{freq:.2f} Hz")  # 显示2位小数
            self.freq_display_var.set(f"频率：{freq:.2f} Hz")  # 显示2位小数
        self.freq_slider.configure(command=on_freq_change)
        self.freq_slider.set(250.35)
        on_freq_change(250.35)
        
        # 双臂质量滑块（保持不变）
        ttk.Label(control_frame, text="双臂质量 (0-100 g):").pack(anchor=tk.W, pady=(10, 5))
        self.mass_slider = ttk.Scale(control_frame, from_=0, to=100, 
                                    orient=tk.HORIZONTAL, length=350)
        self.mass_slider.pack(fill=tk.X, pady=(0, 5))
        
        self.mass_value_var = tk.StringVar(value="0.00 g")
        mass_value_label = ttk.Label(control_frame, textvariable=self.mass_value_var,
                                    font=("Microsoft YaHei", 10))
        mass_value_label.pack(anchor=tk.W)
        
        def on_mass_change(val):
            mass = round(float(val), 2)
            self.mass_value_var.set(f"{mass:.2f} g")
        self.mass_slider.configure(command=on_mass_change)
        self.mass_slider.set(0)
        on_mass_change(0)
        
    def setup_data_recording(self, parent):
        """右侧区域：数据记录区域"""
        data_frame = ttk.LabelFrame(parent, text="数据记录区域", padding=5)
        data_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 选项卡
        self.notebook = ttk.Notebook(data_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 第一个选项卡：振幅与频率的关系
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="振幅与频率的关系")
        
        # 第二个选项卡（功能待定）
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="音叉的共振频率与双臂质量的关系")
        ttk.Label(self.tab2, text="功能开发中...", font=("Microsoft YaHei", 16)).pack(expand=True)
        
        # 初始化第一个选项卡的内容
        self.setup_tab1()
        
    def setup_tab1(self):
        """设置第一个选项卡的内容"""
        # 表格框架
        table_frame = ttk.Frame(self.tab1)
        table_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建Canvas和滚动条实现横向滚动
        canvas = tk.Canvas(table_frame, height=60)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.configure(xscrollcommand=h_scrollbar.set)
        
        canvas.pack(side=tk.TOP, fill=tk.X, expand=True)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 表格内部框架
        self.table_inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.table_inner, anchor='nw')
        
        # 创建表头行和数据输入框
        self.create_table_headers()
        
        # 绑定配置事件
        def configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        self.table_inner.bind('<Configure>', configure_canvas)
        
        # 曲线图
        self.setup_plot()
        
        # 参数显示区域
        self.setup_params_display()
        
        # 按钮区域
        self.setup_buttons()
        
    def create_table_headers(self):
        """创建表格表头和数据输入框"""
        # 第一列固定为表头
        header_freq = ttk.Label(self.table_inner, text="f/Hz", borderwidth=1, relief='solid',
                                font=("Microsoft YaHei", 9), width=12)
        header_freq.grid(row=0, column=0, padx=1, pady=1, sticky='ew')
        
        header_amp = ttk.Label(self.table_inner, text="Ar/mV", borderwidth=1, relief='solid',
                               font=("Microsoft YaHei", 9), width=12)
        header_amp.grid(row=1, column=0, padx=1, pady=1, sticky='ew')
        
        # 创建40列数据输入框
        for col in range(40):
            # 频率列（第0行）
            freq_entry = ttk.Entry(self.table_inner, width=12, justify='center')
            freq_entry.grid(row=0, column=col+1, padx=1, pady=1)
            self.table_vars[(0, col)] = freq_entry
            
            # 振幅列（第1行）
            amp_entry = ttk.Entry(self.table_inner, width=12, justify='center')
            amp_entry.grid(row=1, column=col+1, padx=1, pady=1)
            self.table_vars[(1, col)] = amp_entry
    
    def init_table_data(self):
        """初始化表格数据 - 使用提供的实验数据"""
        # 清空现有数据
        for (row, col), entry in self.table_vars.items():
            entry.delete(0, tk.END)
        
        # 使用您提供的实验数据
        # 频率数据（共40个点）
        frequencies = [
            246.00, 246.50, 247.00, 247.50, 248.00, 248.50, 249.00, 249.10, 249.20,
            249.30, 249.40, 249.50, 249.60, 249.70, 249.80, 249.90, 250.00, 250.10,
            250.15, 250.20, 250.25, 250.30, 250.35, 250.40, 250.50, 250.60, 250.70,
            250.80, 250.90, 251.00, 251.10, 251.20, 251.30, 251.40, 251.50, 252.00,
            252.50, 253.00, 253.50
        ]
        
        # 振幅数据（对应上面的频率）
        amplitudes = [
            78, 85, 92, 103, 118, 138, 172, 180, 191,
            202, 216, 232, 249, 274, 302, 341, 390, 466,
            527, 634, 818, 998, 1166, 1122, 1034, 944, 845,
            755, 663, 584, 508, 445, 391, 343, 305, 183,
            137, 110, 95
        ]
        
        # 填充到表格（共39个数据点，表格有40列）
        for col in range(len(frequencies)):
            if col < 40:
                if (0, col) in self.table_vars:
                    self.table_vars[(0, col)].insert(0, f"{frequencies[col]:.2f}")
                if (1, col) in self.table_vars:
                    self.table_vars[(1, col)].insert(0, f"{amplitudes[col]:.0f}")
        
    def setup_plot(self):
        """设置曲线图"""
        # 创建matplotlib图形
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('频率 f/Hz')
        self.ax.set_ylabel('振幅 Ar/mV')
        self.ax.set_title('振幅与频率关系曲线')
        self.ax.grid(True, alpha=0.3)
        
        # 嵌入到tkinter
        plot_frame = ttk.Frame(self.tab1)
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas_widget.draw()
        self.canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具栏
        toolbar = NavigationToolbar2Tk(self.canvas_widget, plot_frame)
        toolbar.update()
        
    def setup_params_display(self):
        """设置参数显示区域"""
        param_frame = ttk.LabelFrame(self.tab1, text="参数计算", padding=10)
        param_frame.pack(fill=tk.X, pady=10)
        
        # 创建参数显示标签
        params = [
            ("共振点（f0）:", "resonance_freq", "0.00 Hz"),
            ("共振点电压:", "resonance_voltage", "0.00 mV"),
            ("半功率电压:", "half_power_voltage", "0.00 mV"),
            ("f1:", "f1", "0.00 Hz"),
            ("f2:", "f2", "0.00 Hz"),
            ("品质因数Q:", "q_factor", "0.00")
        ]
        
        self.param_vars = {}
        for i, (label_text, key, default) in enumerate(params):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(param_frame, text=label_text, font=("Microsoft YaHei", 9)).grid(
                row=row, column=col, padx=5, pady=5, sticky='e')
            
            var = tk.StringVar(value=default)
            self.param_vars[key] = var
            ttk.Label(param_frame, textvariable=var, font=("Microsoft YaHei", 9, "bold"),
                      foreground="blue").grid(row=row, column=col+1, padx=5, pady=5, sticky='w')
            
    def setup_buttons(self):
        """设置按钮区域"""
        button_frame = ttk.Frame(self.tab1)
        button_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("计算", self.calculate_params),
            ("清空数据", self.clear_data),
            ("导出数据", self.export_data),
            ("导入数据", self.import_data)
        ]
        
        for text, command in buttons:
            btn = ttk.Button(button_frame, text=text, command=command, width=12)
            btn.pack(side=tk.LEFT, padx=5)
            
    def read_table_data(self):
        """从表格读取数据"""
        self.frequencies = []
        self.amplitudes = []
        
        for col in range(40):
            freq_entry = self.table_vars.get((0, col))
            amp_entry = self.table_vars.get((1, col))
            
            if freq_entry and amp_entry:
                freq_str = freq_entry.get().strip()
                amp_str = amp_entry.get().strip()
                
                if freq_str and amp_str:
                    try:
                        freq = float(freq_str)
                        amp = float(amp_str)
                        if 246 <= freq <= 254:  # 修改为246-254范围
                            self.frequencies.append(freq)
                            self.amplitudes.append(amp)
                    except ValueError:
                        pass
        
        # 按频率排序
        if self.frequencies:
            sorted_pairs = sorted(zip(self.frequencies, self.amplitudes))
            self.frequencies, self.amplitudes = zip(*sorted_pairs)
            self.frequencies = list(self.frequencies)
            self.amplitudes = list(self.amplitudes)
    
    def calculate_params(self):
        """计算参数并更新曲线图"""
        self.read_table_data()
        
        if len(self.frequencies) < 3:
            messagebox.showwarning("警告", "数据点不足，请至少输入3个有效数据点\n频率范围应在240-260Hz之间")
            return
        
        # 更新曲线图
        self.update_plot()
        
        # 寻找共振点（振幅最大点）
        max_amp_idx = np.argmax(self.amplitudes)
        f0 = self.frequencies[max_amp_idx]
        A0 = self.amplitudes[max_amp_idx]
        
        # 计算半功率电压
        half_power_volt = A0 / np.sqrt(2)
        
        # 寻找半功率点对应的频率f1和f2
        f1 = None
        f2 = None
        
        # 在共振点左侧寻找f1（振幅接近half_power_volt）
        for i in range(max_amp_idx - 1, -1, -1):
            if self.amplitudes[i] <= half_power_volt:
                # 线性插值
                if i + 1 <= max_amp_idx:
                    f1 = self.interpolate_frequency(
                        self.frequencies[i], self.amplitudes[i],
                        self.frequencies[i + 1], self.amplitudes[i + 1],
                        half_power_volt
                    )
                break
        
        # 在共振点右侧寻找f2
        for i in range(max_amp_idx + 1, len(self.frequencies)):
            if self.amplitudes[i] <= half_power_volt:
                if i - 1 >= max_amp_idx:
                    f2 = self.interpolate_frequency(
                        self.frequencies[i - 1], self.amplitudes[i - 1],
                        self.frequencies[i], self.amplitudes[i],
                        half_power_volt
                    )
                break
        
        # 计算品质因数Q
        if f1 is not None and f2 is not None and f2 > f1:
            Q = f0 / (f2 - f1)
        else:
            Q = 0
        
        # 更新显示
        self.param_vars['resonance_freq'].set(f"{f0:.2f} Hz")
        self.param_vars['resonance_voltage'].set(f"{A0:.2f} mV")
        self.param_vars['half_power_voltage'].set(f"{half_power_volt:.2f} mV")
        self.param_vars['f1'].set(f"{f1:.2f} Hz" if f1 else "未找到")
        self.param_vars['f2'].set(f"{f2:.2f} Hz" if f2 else "未找到")
        self.param_vars['q_factor'].set(f"{Q:.2f}")
        
        # 在图上标记共振点和半功率点
        self.mark_points_on_plot(f0, A0, f1, f2, half_power_volt)
    
    def interpolate_frequency(self, f1, A1, f2, A2, target_A):
        """线性插值求频率"""
        if A2 - A1 == 0:
            return f1
        ratio = (target_A - A1) / (A2 - A1)
        return f1 + ratio * (f2 - f1)
    
    def update_plot(self):
        """更新曲线图"""
        self.ax.clear()
        if self.frequencies:
            self.ax.plot(self.frequencies, self.amplitudes, 'b-o', linewidth=2, markersize=6)
        self.ax.set_xlabel('频率 f/Hz')
        self.ax.set_ylabel('振幅 Ar/mV')
        self.ax.set_title('振幅与频率关系曲线')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(246, 254)  # 修改为246-254范围
        self.canvas_widget.draw()
    
    def mark_points_on_plot(self, f0, A0, f1, f2, half_power_volt):
        """在图上标记特殊点"""
        # 标记共振点
        self.ax.plot(f0, A0, 'r*', markersize=15, label=f'共振点 ({f0:.2f}Hz, {A0:.0f}mV)')
        
        # 标记半功率线
        self.ax.axhline(y=half_power_volt, color='g', linestyle='--', alpha=0.7, 
                        label=f'半功率电压 ({half_power_volt:.1f}mV)')
        
        if f1:
            self.ax.plot(f1, half_power_volt, 'go', markersize=8, label=f'f1={f1:.2f}Hz')
        if f2:
            self.ax.plot(f2, half_power_volt, 'go', markersize=8, label=f'f2={f2:.2f}Hz')
        
        self.ax.legend(loc='best', fontsize=8)
        self.canvas_widget.draw()
    
    def clear_data(self):
        """清空表格数据"""
        for (row, col), entry in self.table_vars.items():
            entry.delete(0, tk.END)
        
        # 清空曲线图
        self.ax.clear()
        self.ax.set_xlabel('频率 f/Hz')
        self.ax.set_ylabel('振幅 Ar/mV')
        self.ax.set_title('振幅与频率关系曲线')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(240, 260)
        self.canvas_widget.draw()
        
        # 重置参数显示
        self.param_vars['resonance_freq'].set("0.00 Hz")
        self.param_vars['resonance_voltage'].set("0.00 mV")
        self.param_vars['half_power_voltage'].set("0.00 mV")
        self.param_vars['f1'].set("0.00 Hz")
        self.param_vars['f2'].set("0.00 Hz")
        self.param_vars['q_factor'].set("0.00")
        
        self.frequencies = []
        self.amplitudes = []
    
    def export_data(self):
        """导出数据到JSON文件"""
        self.read_table_data()
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            data = {
                "frequencies": [round(f, 2) for f in self.frequencies],  # 保留2位小数
                "amplitudes": [round(a, 0) for a in self.amplitudes],    # 保留2位小数
                "frequency_range": [246, 254]  # 修改范围
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", f"数据已导出到 {file_path}")
        
    def import_data(self):
        """从JSON文件导入数据"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 清空表格
                for (row, col), entry in self.table_vars.items():
                    entry.delete(0, tk.END)
                
                # 填充数据
                freqs = data.get("frequencies", [])
                amps = data.get("amplitudes", [])
                
                for i, (f, a) in enumerate(zip(freqs, amps)):
                    if i < 40:
                        if (0, i) in self.table_vars:
                            self.table_vars[(0, i)].insert(0, f"{f:.2f}")
                        if (1, i) in self.table_vars:
                            self.table_vars[(1, i)].insert(0, f"{a:.0f}")
                
                messagebox.showinfo("成功", f"成功导入 {len(freqs)} 个数据点")
                
                # 自动计算并更新曲线
                self.calculate_params()
                
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {str(e)}")


def main():
    root = tk.Tk()
    app = ResonanceExperimentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()