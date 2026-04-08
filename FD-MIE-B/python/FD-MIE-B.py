# coding=utf-8
import serial
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox
from collections import deque
import struct
from datetime import datetime
import matplotlib
import numpy as np

# 设置Matplotlib后端
matplotlib.use('TkAgg')
plt.rcParams['font.family'] = 'SimHei'  # 替换为你选择的字体

# 串口配置
SERIAL_PORT = 'COM11'
BAUD_RATE = 115200

plt.style.use('ggplot')
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111)
plt.subplots_adjust(left=0.1, right=0.95, bottom=0.1, top=0.95)

scatter = ax.scatter([], [], c='blue', alpha=0.6, edgecolors='w', s=40)
ax.set_xlim(0, 65535)
ax.set_ylim(0, 65535)
ax.set_xlabel('X Axis (uint16_t)')
ax.set_ylabel('Y Axis (uint16_t)')
ax.set_title(f'Real-time UINT16 Scatter Plot ({SERIAL_PORT})', pad=6)
ax.grid(True, linestyle='--', alpha=0.3)

# 数据缓冲区
MAX_POINTS = 100000
x_data = deque(maxlen=MAX_POINTS)
y_data = deque(maxlen=MAX_POINTS)

# 数据记录文件
log_file = open(f"scatter_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "w")
log_file.write("timestamp,x,y\n")

class SerialPlotter:
    def __init__(self):
        self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        self.running = True
        self.controls_visible = False
        self.auto_scale_enabled = True
        
    def update_plot(self):
        """定时器回调函数，更新散点图"""
        try:
            while self.ser.in_waiting >= 4:
                data = self.ser.read(4)
                if len(data) == 4:
                    x, y = struct.unpack('<HH', data)
                    x_data.append(x)
                    y_data.append(y)
                    
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    log_file.write(f"{timestamp},{x},{y}\n")
                    
                    if len(x_data) % 50 == 0:
                        print(f"[{timestamp}] Points: {len(x_data)} | Latest: X={x}, Y={y}")
            
            if x_data:
                scatter.set_offsets(np.column_stack((x_data, y_data)))
                
                if self.auto_scale_enabled:
                    self.auto_scale()
                
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
            
        except Exception as e:
            print(f"Error: {str(e)}")
            self.close()
            
    def auto_scale(self):
        """执行自动缩放并更新控件值"""
        if x_data:
            x_min, x_max = min(x_data), max(x_data)
            y_min, y_max = min(y_data), max(y_data)
            padding_x = max(50, (x_max - x_min) * 0.1)
            padding_y = max(50, (y_max - y_min) * 0.1)
            ax.set_xlim(max(0, x_min-padding_x), min(65535, x_max+padding_x))
            ax.set_ylim(max(0, y_min-padding_y), min(65535, y_max+padding_y))
            self.update_control_values()
            
    def update_control_values(self):
        """更新所有范围控件的值为当前坐标范围"""
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        
        for box in control_elements['text_boxes']:
            if box.label.get_text() == 'X min:':
                box.set_val(f"{max(0, int(x_min))}")
            elif box.label.get_text() == 'X max:':
                box.set_val(f"{min(65535, int(x_max))}")
            elif box.label.get_text() == 'Y min:':
                box.set_val(f"{max(0, int(y_min))}")
            elif box.label.get_text() == 'Y max:':
                box.set_val(f"{min(65535, int(y_max))}")
            
    def close(self):
        """清理资源"""
        if self.running:
            self.running = False
            log_file.close()
            self.ser.close()
            plt.close('all')
            print(f"\nData logging stopped. Total points: {len(x_data)}")

# 创建绘图器实例
plotter = SerialPlotter()

# 存储控件引用
control_elements = {
    'text_boxes': [],
    'buttons': [],
    'labels': [],
    'axes': []
}

def set_x_axis(min_val, max_val):
    try:
        min_val = max(0, float(min_val))
        max_val = min(65535, float(max_val))
        if min_val < max_val:
            ax.set_xlim(min_val, max_val)
            plotter.update_control_values()
            fig.canvas.draw_idle()
    except ValueError:
        pass

def set_y_axis(min_val, max_val):
    try:
        min_val = max(0, float(min_val))
        max_val = min(65535, float(max_val))
        if min_val < max_val:
            ax.set_ylim(min_val, max_val)
            plotter.update_control_values()
            fig.canvas.draw_idle()
    except ValueError:
        pass

def reset_axes(event):
    ax.set_xlim(0, 65535)
    ax.set_ylim(0, 65535)
    plotter.update_control_values()
    fig.canvas.draw_idle()

def toggle_auto_scale(event):
    plotter.auto_scale_enabled = not plotter.auto_scale_enabled
    auto_scale_button.color = 'lightgreen' if plotter.auto_scale_enabled else 'lightgray'
    auto_scale_button.hovercolor = 'green' if plotter.auto_scale_enabled else 'gray'
    auto_scale_button.label.set_text('Auto: ON' if plotter.auto_scale_enabled else 'Auto: OFF')
    fig.canvas.draw_idle()

def create_controls():
    axbox_xmin = plt.axes([0.25, 0.12, 0.1, 0.05], visible=False)
    x_min_text = TextBox(axbox_xmin, 'X min:', initial="0")
    x_min_text.on_submit(lambda text: set_x_axis(text, x_max_text.text))
    
    axbox_xmax = plt.axes([0.40, 0.12, 0.1, 0.05], visible=False)
    x_max_text = TextBox(axbox_xmax, 'X max:', initial="65535")
    x_max_text.on_submit(lambda text: set_x_axis(x_min_text.text, text))
    
    axbox_ymin = plt.axes([0.65, 0.12, 0.1, 0.05], visible=False)
    y_min_text = TextBox(axbox_ymin, 'Y min:', initial="0")
    y_min_text.on_submit(lambda text: set_y_axis(text, y_max_text.text))
    
    axbox_ymax = plt.axes([0.80, 0.12, 0.1, 0.05], visible=False)
    y_max_text = TextBox(axbox_ymax, 'Y max:', initial="65535")
    y_max_text.on_submit(lambda text: set_y_axis(y_min_text.text, text))
    
    x_label = plt.figtext(0.12, 0.14, "X Axis Range:", ha='left', visible=False)
    y_label = plt.figtext(0.52, 0.14, "Y Axis Range:", ha='left', visible=False)
    
    button_ax = plt.axes([0.4, 0.05, 0.2, 0.06], visible=False)
    reset_button = Button(button_ax, 'Reset to Full Range', color='lightgoldenrodyellow')
    reset_button.on_clicked(reset_axes)
    
    global auto_scale_button
    autoscale_ax = plt.axes([0.7, 0.05, 0.2, 0.06], visible=False)
    auto_scale_button = Button(autoscale_ax, 'Auto: ON', color='lightgreen')
    auto_scale_button.on_clicked(toggle_auto_scale)
    
    control_elements['text_boxes'] = [x_min_text, x_max_text, y_min_text, y_max_text]
    control_elements['buttons'] = [reset_button, auto_scale_button]
    control_elements['labels'] = [x_label, y_label]
    control_elements['axes'] = [axbox_xmin, axbox_xmax, axbox_ymin, axbox_ymax, button_ax, autoscale_ax]

create_controls()

toggle_ax = plt.axes([0.85, 0.00, 0.12, 0.04])
toggle_button = Button(toggle_ax, 'Show Controls', color='lightblue')

def toggle_controls(event):
    if plotter.controls_visible:
        for element in control_elements['text_boxes'] + control_elements['buttons'] + control_elements['labels']:
            if hasattr(element, 'set_visible'):
                element.set_visible(False)
            if hasattr(element, 'ax'):
                element.ax.set_visible(False)
        plt.subplots_adjust(bottom=0.08)
        toggle_button.label.set_text('Show Controls')
    else:
        for element in control_elements['text_boxes'] + control_elements['buttons'] + control_elements['labels']:
            if hasattr(element, 'set_visible'):
                element.set_visible(True)
            if hasattr(element, 'ax'):
                element.ax.set_visible(True)
        plt.subplots_adjust(bottom=0.25)
        toggle_button.label.set_text('Hide Controls')
    
    plotter.controls_visible = not plotter.controls_visible
    fig.canvas.draw_idle()

toggle_button.on_clicked(toggle_controls)

def on_close(event):
    plotter.close()

fig.canvas.mpl_connect('close_event', on_close)

timer = fig.canvas.new_timer(interval=25)
timer.add_callback(plotter.update_plot)
timer.start()

plt.tight_layout()
try:
    plt.show()
except KeyboardInterrupt:
    plotter.close()