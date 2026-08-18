#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_widget.py

封装实时绘图控件，优先使用 pyqtgraph；若不可用则回退到 matplotlib。
提供接口：
 - PlotWidget(parent_widget)
 - update_table_data(table_name:str, rows: list[dict])
 - export_png(path)
"""
from typing import List, Dict
import os

try:
    import pyqtgraph as pg
    from pyqtgraph import PlotWidget as PGPlotWidget
    USE_PYQTGRAPH = True
except Exception:
    USE_PYQTGRAPH = False
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5 import QtWidgets, QtCore


class PlotWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.layout)
        if USE_PYQTGRAPH:
            self.pw = PGPlotWidget(parent=self)
            self.layout.addWidget(self.pw)
            self.curves = {}
            self.pw.showGrid(x=True, y=True)
            # set axis labels for pyqtgraph
            try:
                pi = self.pw.getPlotItem()
                if pi is not None:
                    try:
                        pi.setLabel('left', 'B (mT)')
                    except Exception:
                        pass
                    try:
                        pi.setLabel('bottom', 'H (A/m)')
                    except Exception:
                        pass
                    try:
                        # ensure axis text is visible against dark grid background
                        ax_bot = pi.getAxis('bottom')
                        ax_left = pi.getAxis('left')
                        try:
                            ax_bot.setTextPen('w')
                        except Exception:
                            pass
                        try:
                            ax_left.setTextPen('w')
                        except Exception:
                            pass
                        try:
                            ax_bot.setPen('w')
                        except Exception:
                            pass
                        try:
                            ax_left.setPen('w')
                        except Exception:
                            pass
                        try:
                            # ensure axis area is large enough so labels/ticks are visible
                            try:
                                ax_bot.setHeight(30)
                            except Exception:
                                pass
                            try:
                                ax_left.setWidth(60)
                            except Exception:
                                pass
                            # 减少边距，特别是左边的间距
                            try:
                                pi.layout.setContentsMargins(0, 5, 5, 25)
                            except Exception:
                                pass
                            # 减少左轴宽度
                            try:
                                ax_left.setWidth(45)
                            except Exception:
                                pass
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass
        else:
            self.fig = Figure(figsize=(5, 4))
            self.canvas = FigureCanvas(self.fig)
            self.layout.addWidget(self.canvas)
            self.ax = self.fig.add_subplot(111)

    def update_table_data(self, table_name: str, rows: List[Dict]):
        """
        table_name: 'A' or 'B'
        rows: list of dict rows
        """
        if USE_PYQTGRAPH:
            self.pw.clear()
            if table_name == 'A':
                # X/mm vs B/mT
                xs = []
                ys = []
                for r in rows:
                    try:
                        xs.append(float(r.get('X/mm', 0)))
                        ys.append(float(r.get('B/mT', 0)))
                    except Exception:
                        continue
                # sort by X to avoid incorrect connecting lines between out-of-order X values
                if xs and ys:
                    pairs = sorted(zip(xs, ys), key=lambda p: p[0])
                    xs_s, ys_s = zip(*pairs)
                    pi = self.pw.getPlotItem()
                    try:
                        pi.setLabel('bottom', 'X/mm')
                        pi.setLabel('left', 'B/mT')
                    except Exception:
                        pass
                    self.pw.plot(list(xs_s), list(ys_s), pen=pg.mkPen('b', width=2), symbol='o')
            else:
                # B vs H (if H exists)
                hs = []
                bs = []
                for r in rows:
                    try:
                        bs.append(float(r.get('B/mT', 0)))
                        # support both 'H/(A/m)' and legacy 'H/A_m'
                        h_raw = r.get('H/(A/m)', r.get('H/A_m', r.get('H', 0)))
                        # plot H as integer A/m (no decimals)
                        hs.append(int(round(float(h_raw))))
                    except Exception:
                        continue
                if hs and bs:
                    # For hysteresis (table B) we must preserve measurement order to show loop.
                    # Do NOT sort by H; use the sequence order provided in rows.
                    pi = self.pw.getPlotItem()
                    try:
                        pi.setLabel('bottom', 'H (A/m)')
                        pi.setLabel('left', 'B (mT)')
                    except Exception:
                        pass
                    # hs and bs are already in the table order; convert to lists and plot
                    self.pw.plot(list(hs), list(bs), pen=pg.mkPen('r', width=2), symbol='x')
        else:
            self.ax.clear()
            if table_name == 'A':
                xs = []
                ys = []
                for r in rows:
                    try:
                        xs.append(float(r.get('X/mm', 0)))
                        ys.append(float(r.get('B/mT', 0)))
                    except Exception:
                        continue
                if xs and ys:
                    pairs = sorted(zip(xs, ys), key=lambda p: p[0])
                    xs_s, ys_s = zip(*pairs)
                    self.ax.plot(list(xs_s), list(ys_s), '-o', color='b')
                    self.ax.set_xlabel('X/mm')
                    self.ax.set_ylabel('B/mT')
            else:
                hs = []
                bs = []
                for r in rows:
                    try:
                        bs.append(float(r.get('B/mT', 0)))
                        h_raw = r.get('H/(A/m)', r.get('H/A_m', r.get('H', 0)))
                        hs.append(int(round(float(h_raw))))
                    except Exception:
                        continue
                if hs and bs:
                    # Preserve sequence order for hysteresis plotting (do not sort)
                    self.ax.plot(list(hs), list(bs), '-x', color='r')
                    self.ax.set_xlabel('H (A/m)')
                    self.ax.set_ylabel('B (mT)')
            self.canvas.draw()

    def export_png(self, path: str):
        if USE_PYQTGRAPH:
            exporter = pg.exporters.ImageExporter(self.pw.plotItem)
            exporter.parameters()['width'] = 1200
            exporter.export(path)
        else:
            self.fig.savefig(path)

    # ==================== 新增绘图方法 ====================

    def plot_degauss_curve(self, data: List[Dict]):
        """
        绘制退磁曲线 B vs H (B-H曲线)
        退磁曲线应该呈嵌套的磁滞环，从外到内收敛到原点
        
        data: [{'t': 时间, 'B': 磁场, 'I': 电流, 'H': 磁场强度}, ...]
        """
        if USE_PYQTGRAPH:
            self.pw.clear()
            pi = self.pw.getPlotItem()
            try:
                    pi.setLabel('bottom', 'H (A/m)')
                    pi.setLabel('left', 'B (mT)')
            except Exception:
                    pass
            
            if not data:
                return
                
            hs = [d.get('H', 0) for d in data]
            bs = [d.get('B', 0) for d in data]
            
            if hs and bs:
                # 绘制完整的退磁轨迹（绿色渐变，越新越亮）
                n = len(hs)
                if n > 1:
                    # 分段绘制，颜色从暗绿到亮绿
                    segment_size = max(1, n // 20)  # 分成约20段
                    for i in range(0, n - 1, segment_size):
                        end_idx = min(i + segment_size + 1, n)
                        # 颜色从暗到亮
                        intensity = int(100 + 155 * (i / n))
                        color = (0, intensity, 0)
                        self.pw.plot(
                            hs[i:end_idx], 
                            bs[i:end_idx], 
                            pen=pg.mkPen(color, width=2),
                            symbol=None
                        )
                
                # 标记起点（红色）和当前点（黄色）
                if n >= 1:
                    self.pw.plot([hs[0]], [bs[0]], pen=None, symbol='o', 
                                symbolBrush='r', symbolSize=8)
                    self.pw.plot([hs[-1]], [bs[-1]], pen=None, symbol='o', 
                                symbolBrush='y', symbolSize=10)
                
                # 标记原点
                self.pw.plot([0], [0], pen=None, symbol='+', 
                            symbolPen=pg.mkPen('w', width=2), symbolSize=15)
        else:
            self.ax.clear()
            if not data:
                self.ax.set_xlabel('H (A/m)')
                self.ax.set_ylabel('B (mT)')
                self.canvas.draw()
                return
                
            hs = [d.get('H', 0) for d in data]
            bs = [d.get('B', 0) for d in data]
            
            if hs and bs:
                # 使用颜色映射显示时间演化
                import numpy as np
                n = len(hs)
                colors = plt.cm.Greens(np.linspace(0.3, 1.0, n))
                
                # 绘制线段
                for i in range(n - 1):
                    self.ax.plot(hs[i:i+2], bs[i:i+2], '-', color=colors[i], linewidth=2)
                
                # 标记起点和终点
                if n >= 1:
                    self.ax.plot(hs[0], bs[0], 'ro', markersize=8, label='起点')
                    self.ax.plot(hs[-1], bs[-1], 'yo', markersize=10, label='当前')
                    self.ax.plot(0, 0, 'w+', markersize=15, markeredgewidth=2, label='原点')
                
                self.ax.set_xlabel('H (A/m)')
                self.ax.set_ylabel('B (mT)')
                self.ax.legend(loc='upper left', fontsize=8)
                self.ax.grid(True, alpha=0.3)
            self.canvas.draw()

    def plot_initial_magnetization(self, data: List[Dict]):
        """
        绘制初始磁化曲线 B vs H
        data: [{'I/mA', 'B/mT', 'H/A_m'}, ...]
        """
        if USE_PYQTGRAPH:
            self.pw.clear()
            hs = []
            bs = []
            for d in data:
                try:
                    h = float(d.get('H/A_m', d.get('H/(A/m)', 0)))
                    b = float(d.get('B/mT', 0))
                    hs.append(h)
                    bs.append(b)
                except:
                    continue
            if hs and bs:
                pi = self.pw.getPlotItem()
                try:
                    pi.setLabel('bottom', 'H (A/m)')
                    pi.setLabel('left', 'B (mT)')
                except Exception:
                    pass
                # 初始磁化曲线用蓝色
                self.pw.plot(hs, bs, pen=pg.mkPen('c', width=2), symbol='o', symbolSize=6)
        else:
            self.ax.clear()
            hs = []
            bs = []
            for d in data:
                try:
                    h = float(d.get('H/A_m', d.get('H/(A/m)', 0)))
                    b = float(d.get('B/mT', 0))
                    hs.append(h)
                    bs.append(b)
                except:
                    continue
            if hs and bs:
                self.ax.plot(hs, bs, '-o', color='c', linewidth=2)
                self.ax.set_xlabel('H (A/m)')
                self.ax.set_ylabel('B (mT)')
            self.canvas.draw()

    def plot_hysteresis_with_initial(self, hysteresis_data: List[Dict], initial_data: List[Dict]):
        """
        同时绘制磁滞回线和初始磁化曲线（对比显示）
        """
        if USE_PYQTGRAPH:
            self.pw.clear()
            pi = self.pw.getPlotItem()
            try:
                pi.setLabel('bottom', 'H (A/m)')
                pi.setLabel('left', 'B (mT)')
            except Exception:
                pass
            
            # 绘制初始磁化曲线（青色）
            if initial_data:
                hs_i = []
                bs_i = []
                for d in initial_data:
                    try:
                        h = float(d.get('H/A_m', d.get('H/(A/m)', 0)))
                        b = float(d.get('B/mT', 0))
                        hs_i.append(h)
                        bs_i.append(b)
                    except:
                        continue
                if hs_i and bs_i:
                    self.pw.plot(hs_i, bs_i, pen=pg.mkPen('c', width=2), symbol='o', symbolSize=5, name='初始磁化')
            
            # 绘制磁滞回线（红色）
            if hysteresis_data:
                hs_h = []
                bs_h = []
                for d in hysteresis_data:
                    try:
                        h = float(d.get('H/A_m', d.get('H/(A/m)', 0)))
                        b = float(d.get('B/mT', 0))
                        hs_h.append(h)
                        bs_h.append(b)
                    except:
                        continue
                if hs_h and bs_h:
                    self.pw.plot(hs_h, bs_h, pen=pg.mkPen('r', width=2), symbol='x', symbolSize=5, name='磁滞回线')
        else:
            self.ax.clear()
            # 初始磁化曲线
            if initial_data:
                hs_i = []
                bs_i = []
                for d in initial_data:
                    try:
                        h = float(d.get('H/A_m', d.get('H/(A/m)', 0)))
                        b = float(d.get('B/mT', 0))
                        hs_i.append(h)
                        bs_i.append(b)
                    except:
                        continue
                if hs_i and bs_i:
                    self.ax.plot(hs_i, bs_i, '-o', color='c', linewidth=2, label='初始磁化')
            
            # 磁滞回线
            if hysteresis_data:
                hs_h = []
                bs_h = []
                for d in hysteresis_data:
                    try:
                        h = float(d.get('H/A_m', d.get('H/(A/m)', 0)))
                        b = float(d.get('B/mT', 0))
                        hs_h.append(h)
                        bs_h.append(b)
                    except:
                        continue
                if hs_h and bs_h:
                    self.ax.plot(hs_h, bs_h, '-x', color='r', linewidth=2, label='磁滞回线')
            
            self.ax.set_xlabel('H (A/m)')
            self.ax.set_ylabel('B (mT)')
            self.ax.legend()
            self.canvas.draw()

    def add_realtime_point(self, x: float, y: float, curve_name: str = 'realtime'):
        """
        实时添加数据点（用于退磁过程）
        """
        if USE_PYQTGRAPH:
            if curve_name not in self.curves:
                self.curves[curve_name] = {'x': [], 'y': [], 'plot': None}
            self.curves[curve_name]['x'].append(x)
            self.curves[curve_name]['y'].append(y)
            
            # 更新或创建曲线
            if self.curves[curve_name]['plot'] is not None:
                self.curves[curve_name]['plot'].setData(
                    self.curves[curve_name]['x'],
                    self.curves[curve_name]['y']
                )
            else:
                self.curves[curve_name]['plot'] = self.pw.plot(
                    self.curves[curve_name]['x'],
                    self.curves[curve_name]['y'],
                    pen=pg.mkPen('g', width=2)
                )

    def clear_realtime(self):
        """清除实时曲线数据"""
        self.curves = {}
        if USE_PYQTGRAPH:
            self.pw.clear()



