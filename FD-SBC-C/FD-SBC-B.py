import sys
import os
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk

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

class SolarCellExperiment:
    def __init__(self, root):
        self.root = root
        self.root.title("太阳能电池基本特性实验")
        self.root.geometry("1300x810")
        
        # 实验数据存储
        # 默认数据: 电压(V), Ur(mV), I(mA)
        self.default_data = [
            (-5.00, -2.3, -0.023), (-4.00, -1.8, -0.018), (-3.00, -1.3, -0.013),
            (-2.00, -0.9, -0.009), (-1.00, -0.5, -0.005), (0, 0, 0),
            (0.50, 0.5, 0.005), (1.00, 1.3, 0.013), (1.50, 2.7, 0.027),
            (2.00, 4.9, 0.049), (2.50, 8.6, 0.086), (3.00, 15.0, 0.150),
            (3.50, 26.8, 0.268), (3.75, 36.4, 0.364), (4.00, 49.3, 0.493),
            (4.20, 64.5, 0.645), (4.40, 84.1, 0.841), (4.60, 112.8, 1.128),
            (4.80, 149.7, 1.497), (4.84, 160.2, 1.602)
        ]
        
        self.data = self.default_data.copy()
        self.current_direction = "反向"  # 当前电源方向
        self.current_voltage = 0.0  # 当前电源电压
        
        # 创建主框架
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 顶部选项卡
        self.create_tabs(main_frame)
        
        left_frame = ttk.Frame(main_frame, width=600)  # 设置固定宽度350像素
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))  # expand改为False
        left_frame.pack_propagate(False)  # 防止内容自动调整框架大小
        
        # 左上区域：实验装置
        self.create_experiment_device(left_frame)
        
        # 左下区域：实验操作
        self.create_experiment_controls(left_frame)
        
        # 右侧区域：数据记录区域
        self.create_data_recording_area(main_frame)
        
        # 初始化曲线图
        self.update_plot()
        self.update_fit_params()
    
    def create_tabs(self, parent):
        """创建选项卡"""
        self.tab_control = ttk.Notebook(parent)
        self.tab_control.pack(side=tk.TOP, fill=tk.X)
        
        # 创建各个选项卡
        tabs = ["无光照伏安特性", "光照伏安特性", "光强与短路电流", "光强与开路电压", "光强与距离","串联电阻与并联电阻"]
        self.tabs = {}
        for tab_name in tabs:
            frame = ttk.Frame(self.tab_control)
            self.tab_control.add(frame, text=tab_name)
            self.tabs[tab_name] = frame
        
        # 绑定选项卡切换事件
        self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # 默认选择第一个选项卡
        self.tab_control.select(self.tabs["无光照伏安特性"])
    
    def on_tab_changed(self, event):
        """选项卡切换时的回调函数（其他功能待定）"""
        selected = self.tab_control.tab(self.tab_control.select(), "text")
        # 此处可添加其他选项卡的功能，目前留作待定
        pass
    
    def create_experiment_device(self, parent):
        """左上区域：实验装置"""
        device_frame = ttk.LabelFrame(parent, text="实验装置", padding=5)
        device_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 加载图片 - 使用PIL支持JPG
        try:
            img_path = get_resource_path("background/反向.jpg")
            pil_img = Image.open(img_path)
            
            # 固定图片大小
            fixed_width = 600
            fixed_height = 400
            pil_img = pil_img.resize((fixed_width, fixed_height), Image.Resampling.LANCZOS)
            self.device_img = ImageTk.PhotoImage(pil_img)
            
            # 使用Frame固定大小
            self.device_container = ttk.Frame(device_frame, width=fixed_width, height=fixed_height)
            self.device_container.pack()
            self.device_container.pack_propagate(False)  # 防止自动调整大小
            
            # 图片标签
            self.device_img_label = ttk.Label(self.device_container, image=self.device_img)
            self.device_img_label.place(x=0, y=0, width=fixed_width, height=fixed_height)
            
            # 四个文本框（无黑色边框，背景透明效果）
            self.text1_var = tk.StringVar(value="0")
            text1 = tk.Entry(self.device_container, textvariable=self.text1_var, 
                            font=("Arial", 14, "bold"), width=6, justify="center",
                            bg="lightyellow", fg="red", relief=tk.FLAT, bd=0)  # 去掉边框
            text1.place(x=47, y=85)
            
            self.text2_var = tk.StringVar(value="0")
            text2 = tk.Entry(self.device_container, textvariable=self.text2_var,
                            font=("Arial", 14, "bold"), width=6, justify="center",
                            bg="lightyellow", fg="red", relief=tk.FLAT, bd=0)  # 去掉边框
            text2.place(x=370, y=85)
            
            self.text3_var = tk.StringVar(value="0")
            text3 = tk.Entry(self.device_container, textvariable=self.text3_var,
                            font=("Arial", 14, "bold"), width=6, justify="center",
                            bg="lightyellow", fg="red", relief=tk.FLAT, bd=0)  # 去掉边框
            text3.place(x=200, y=85)
            
            self.text4_var = tk.StringVar(value="0")
            text4 = tk.Entry(self.device_container, textvariable=self.text4_var,
                            font=("Arial", 14, "bold"), width=6, justify="center",
                            bg="lightyellow", fg="red", relief=tk.FLAT, bd=0)  # 去掉边框
            text4.place(x=370, y=194)
            
        except Exception as e:
            ttk.Label(device_frame, text=f"无法加载图片: background/反向.jpg\n{str(e)}").pack()
    
    def create_experiment_controls(self, parent):
        """左下区域：实验操作"""
        controls_frame = ttk.LabelFrame(parent, text="实验操作", padding=5)
        controls_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # 卤素灯图片 - 使用PIL支持JPG
        try:
            lamp_img_path = get_resource_path("background/卤素灯.jpg")
            pil_lamp_img = Image.open(lamp_img_path)
            # 调整图片大小以适应窗口（可选）
            pil_lamp_img.thumbnail((400, 200), Image.Resampling.LANCZOS)
            self.lamp_img = ImageTk.PhotoImage(pil_lamp_img)
            lamp_label = ttk.Label(controls_frame, image=self.lamp_img)
            lamp_label.pack(pady=5)
        except Exception as e:
            ttk.Label(controls_frame, text=f"无法加载图片: background/卤素灯.jpg\n{str(e)}").pack(pady=5)
        
        # 放置探测器按钮
        self.detector_btn = ttk.Button(controls_frame, text="放置探测器", command=self.place_detector)
        self.detector_btn.pack(pady=5, fill=tk.X)

        # 放置太阳能电池按钮
        self.solar_cell_btn = ttk.Button(controls_frame, text="放置太阳能电池", command=self.place_solar_cell)
        self.solar_cell_btn.pack(pady=5, fill=tk.X)
        
        # 切换电源方向按钮
        self.direction_btn = ttk.Button(controls_frame, text=f"切换电源方向 当前：{self.current_direction}", 
                                        command=self.toggle_power_direction)
        self.direction_btn.pack(pady=5, fill=tk.X)
        
        # 电源电压滑块
        voltage_frame = ttk.Frame(controls_frame)
        voltage_frame.pack(pady=5, fill=tk.X)
        ttk.Label(voltage_frame, text="电源电压:").pack(side=tk.LEFT)
        self.voltage_label = ttk.Label(voltage_frame, text="0.00 V")
        self.voltage_label.pack(side=tk.RIGHT)
        
        self.voltage_slider = ttk.Scale(controls_frame, from_=0, to=5, orient=tk.HORIZONTAL,
                                        command=self.on_voltage_change)
        self.voltage_slider.pack(pady=5, fill=tk.X)
    
    def place_solar_cell(self):
        """放置太阳能电池按钮功能"""
        messagebox.showinfo("提示", "太阳能电池已放置")

    def place_detector(self):
        """放置探测器按钮功能"""
        messagebox.showinfo("提示", "探测器已放置")
    
    def toggle_power_direction(self):
        """切换电源方向"""
        if self.current_direction == "反向":
            self.current_direction = "正向"
        else:
            self.current_direction = "反向"
        self.direction_btn.config(text=f"切换电源方向 当前：{self.current_direction}")
        messagebox.showinfo("提示", f"电源方向已切换为{self.current_direction}")
    
    def on_voltage_change(self, value):
        """电压滑块改变时的回调"""
        self.current_voltage = float(value)
        self.voltage_label.config(text=f"{self.current_voltage:.2f} V")
        # 此处可添加电压改变时对实验的影响，目前留作待定
    
    def create_data_recording_area(self, parent):
        """右侧区域：数据记录区域"""
        right_frame = ttk.LabelFrame(parent, text="数据记录区域", padding=5)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建表格容器（带滚动条）
        table_frame = ttk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Canvas和滚动条实现纵向滚动
        canvas = tk.Canvas(table_frame)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 创建Treeview表格
        columns = ("U", "Ur", "I", "U2", "Ur2", "I2")
        self.tree = ttk.Treeview(scrollable_frame, columns=columns, show="headings", height=12)
        
        # 设置表头
        self.tree.heading("U", text="U/V")
        self.tree.heading("Ur", text="Ur/mV")
        self.tree.heading("I", text="I/mA")
        self.tree.heading("U2", text="U/V")
        self.tree.heading("Ur2", text="Ur/mV")
        self.tree.heading("I2", text="I/mA")
        
        # 设置列宽
        for col in columns:
            self.tree.column(col, width=100, anchor="center")
        
        # 填充数据（前10行和后10行）
        self.populate_table()
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 绑定双击编辑事件
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
        # 曲线图
        plot_frame = ttk.LabelFrame(right_frame, text="I-U 特性曲线", padding=5)
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.fig = Figure(figsize=(5, 3.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        # 调整底部边距，为横坐标标题留出空间
        self.fig.subplots_adjust(bottom=0.15)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 参数显示区域
        params_frame = ttk.Frame(right_frame)
        params_frame.pack(fill=tk.X, pady=5)
        
        self.fit_label = ttk.Label(params_frame, text="非线性拟合: I=0.00345e^(1.26U)  R²=0.9967", font=("Arial", 10))
        self.fit_label.pack()
        
        # 按钮区域
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="计算", command=self.calculate).pack(side=tk.LEFT, padx=10, ipadx=15, ipady=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="清空数据", command=self.clear_data).pack(side=tk.LEFT, padx=10, ipadx=15, ipady=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="导出数据", command=self.export_data).pack(side=tk.LEFT, padx=10, ipadx=15, ipady=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="导入数据", command=self.import_data).pack(side=tk.LEFT, padx=10, ipadx=15, ipady=5, expand=True, fill=tk.X)
    
    def populate_table(self):
        """填充表格数据"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 显示前10行和后10行（共20行，加上表头共21行）
        num_rows = len(self.data)
        mid = num_rows // 2
        
        for i in range(mid):
            if i < len(self.data) and i + mid < len(self.data):
                u1, ur1, i1 = self.data[i]
                u2, ur2, i2 = self.data[i + mid]
                self.tree.insert("", tk.END, values=(f"{u1:.2f}", f"{ur1:.1f}", f"{i1:.3f}",
                                                      f"{u2:.2f}", f"{ur2:.1f}", f"{i2:.3f}"))
            elif i < len(self.data):
                u1, ur1, i1 = self.data[i]
                self.tree.insert("", tk.END, values=(f"{u1:.2f}", f"{ur1:.1f}", f"{i1:.3f}", "", "", ""))
    
    def on_tree_double_click(self, event):
        """双击表格单元格进行编辑"""
        item = self.tree.selection()[0]
        column = self.tree.identify_column(event.x)
        col_index = int(column.replace("#", "")) - 1
        
        if col_index >= 6:
            return
        
        # 获取当前值
        values = list(self.tree.item(item, "values"))
        if col_index < len(values):
            current_value = values[col_index]
        else:
            current_value = ""
        
        # 创建编辑框
        x, y, width, height = self.tree.bbox(item, column)
        entry = tk.Entry(self.tree, width=int(width/10))
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.focus()
        
        def save_edit(event=None):
            new_value = entry.get()
            entry.destroy()
            try:
                # 更新数据
                values[col_index] = new_value
                self.tree.item(item, values=values)
                
                # 更新内部数据存储
                self.update_data_from_table()
            except:
                pass
        
        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
    
    def update_data_from_table(self):
        """从表格更新内部数据存储"""
        new_data = []
        items = self.tree.get_children()
        
        for item in items:
            values = self.tree.item(item, "values")
            # 左半部分
            if values[0] and values[0] != "":
                try:
                    u = float(values[0])
                    ur = float(values[1]) if values[1] else 0
                    i = float(values[2]) if values[2] else 0
                    new_data.append((u, ur, i))
                except:
                    pass
            # 右半部分
            if values[3] and values[3] != "":
                try:
                    u = float(values[3])
                    ur = float(values[4]) if values[4] else 0
                    i = float(values[5]) if values[5] else 0
                    new_data.append((u, ur, i))
                except:
                    pass
        
        if new_data:
            # 按电压排序
            new_data.sort(key=lambda x: x[0])
            self.data = new_data
            self.update_plot()
            self.update_fit_params()
    
    def update_plot(self):
        """更新曲线图"""
        self.ax.clear()
        
        if not self.data:
            self.ax.set_title("无数据")
            self.canvas.draw()
            return
        
        # 提取电压和电流
        voltages = [d[0] for d in self.data]
        currents = [d[2] for d in self.data]
        
        # 按电压排序并连线
        sorted_indices = np.argsort(voltages)
        sorted_voltages = np.array(voltages)[sorted_indices]
        sorted_currents = np.array(currents)[sorted_indices]
        
        # 绘制数据点
        self.ax.scatter(sorted_voltages, sorted_currents, color='blue', s=30, zorder=5, label='实验数据点')
        # 绘制连线
        self.ax.plot(sorted_voltages, sorted_currents, 'r-', linewidth=1.5, label='连线')
        
        self.ax.set_xlabel("电压 U / V")
        self.ax.set_ylabel("电流 I / mA")
        self.ax.set_title("I-U 特性曲线")
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        
        self.canvas.draw()
    
    def calculate(self):
        """计算按钮功能：非线性拟合"""
        if len(self.data) < 3:
            messagebox.showwarning("警告", "数据点不足，无法进行拟合")
            return
        
        # 提取电压和电流（仅取正电压部分进行指数拟合）
        voltages = []
        currents = []
        for u, _, i in self.data:
            if u > 0 and i > 0:
                voltages.append(u)
                currents.append(i)
        
        if len(voltages) < 3:
            messagebox.showwarning("警告", "正电压区域有效数据点不足")
            return
        
        # 定义指数函数: I = a * exp(b * U)
        def exp_func(x, a, b):
            return a * np.exp(b * x)
        
        try:
            # 进行曲线拟合
            popt, pcov = curve_fit(exp_func, voltages, currents, p0=(0.00345, 1.26))
            a, b = popt
            
            # 计算R²
            residuals = currents - exp_func(np.array(voltages), a, b)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((currents - np.mean(currents))**2)
            r_squared = 1 - (ss_res / ss_tot)
            
            # 更新拟合参数显示
            self.fit_label.config(text=f"非线性拟合: I={a:.5f}e^({b:.4f}U)  R²={r_squared:.4f}")
            
            # 绘制拟合曲线
            self.update_plot()
            
            # 在图上添加拟合曲线
            u_fit = np.linspace(min(voltages), max(voltages), 100)
            i_fit = exp_func(u_fit, a, b)
            self.ax.plot(u_fit, i_fit, 'g--', linewidth=1.5, label=f'拟合曲线: I={a:.5f}e^({b:.4f}U)')
            self.ax.legend()
            self.canvas.draw()
            
            messagebox.showinfo("计算完成", f"拟合参数:\nI = {a:.5f} * exp({b:.4f} * U)\nR² = {r_squared:.4f}")
            
        except Exception as e:
            messagebox.showerror("拟合错误", f"拟合失败: {str(e)}")
    
    def update_fit_params(self):
        """更新拟合参数显示（默认显示初始值）"""
        # 保持默认显示，等用户点击计算时更新
        self.fit_label.config(text="非线性拟合: I=0.00345e^(1.26U)  R²=0.9967")
    
    def clear_data(self):
        """清空数据"""
        if messagebox.askyesno("确认", "确定要清空所有数据吗？"):
            self.data = []
            self.populate_table()
            self.update_plot()
            self.update_fit_params()
            messagebox.showinfo("提示", "数据已清空")
    
    def export_data(self):
        """导出数据到CSV文件"""
        if not self.data:
            messagebox.showwarning("警告", "没有数据可导出")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", 
                                                  filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")])
        if file_path:
            df = pd.DataFrame(self.data, columns=["电压 U/V", "Ur/mV", "电流 I/mA"])
            df.to_csv(file_path, index=False)
            messagebox.showinfo("导出成功", f"数据已导出到:\n{file_path}")
    
    def import_data(self):
        """从CSV文件导入数据"""
        file_path = filedialog.askopenfilename(filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")])
        if file_path:
            try:
                df = pd.read_csv(file_path)
                if len(df.columns) >= 3:
                    new_data = []
                    for _, row in df.iterrows():
                        u = float(row.iloc[0])
                        ur = float(row.iloc[1])
                        i = float(row.iloc[2])
                        new_data.append((u, ur, i))
                    new_data.sort(key=lambda x: x[0])
                    self.data = new_data
                    self.populate_table()
                    self.update_plot()
                    self.update_fit_params()
                    messagebox.showinfo("导入成功", f"已导入 {len(self.data)} 条数据")
                else:
                    messagebox.showerror("导入错误", "文件格式不正确，需要至少三列数据")
            except Exception as e:
                messagebox.showerror("导入错误", f"导入失败: {str(e)}")

def main():
    root = tk.Tk()
    app = SolarCellExperiment(root)
    root.mainloop()

if __name__ == "__main__":
    main()