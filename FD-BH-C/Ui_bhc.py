#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
import json
import os
import time
import csv
import sys  # 添加缺失的导入

def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容PyInstaller打包后的环境"""
    try:
        # PyInstaller创建的临时文件夹路径
        base_path = sys._MEIPASS
    except AttributeError:
        # 普通Python环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
from PyQt5.QtWidgets import QFileDialog
from data_manager import DataManager
from plot_widget import PlotWidget
from experiment_controller import ExperimentController
try:
    import physics_model
except Exception:
    physics_model = None
try:
    import branch_model_manager
except Exception:
    branch_model_manager = None


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1132, 774)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # 左侧面板与背景图
        self.leftPanel = QtWidgets.QWidget(self.centralwidget)
        self.leftPanel.setGeometry(QtCore.QRect(0, -80, 701,854))
        self.leftPanel.setObjectName("leftPanel")
        self.backgroundLabel = QtWidgets.QLabel(self.leftPanel)
        self.backgroundLabel.setGeometry(QtCore.QRect(0, 90, 701, 721))
        self.backgroundLabel.setText("")
        try:
            self.backgroundLabel.setPixmap(QtGui.QPixmap(resource_path("1.jpg")))
        except Exception:
            pass
        self.backgroundLabel.setScaledContents(True)
        self.backgroundLabel.setObjectName("backgroundLabel")

        # 电流显示 - 五位显示，前导0填充（000.0）
        self.LCD_Current = QtWidgets.QLCDNumber(self.leftPanel)
        self.LCD_Current.setGeometry(QtCore.QRect(80, 630, 161, 51))
        self.LCD_Current.setStyleSheet("QLCDNumber { background: transparent; border: none; }")
        self.LCD_Current.setDigitCount(5)
        self.LCD_Current.setObjectName("LCD_Current")

        # 磁场显示 - 五位显示（000.0），显示为 mT
        self.LCD_Tesla = QtWidgets.QLCDNumber(self.leftPanel)
        self.LCD_Tesla.setGeometry(QtCore.QRect(350, 630, 161, 51))
        self.LCD_Tesla.setStyleSheet("QLCDNumber { background: transparent; border: none; }")
        self.LCD_Tesla.setDigitCount(6)
        self.LCD_Tesla.setObjectName("LCD_Tesla")
        self.LCD_Tesla.display("---.-")  # 初始状态：未选择样品时显示空白

        # 控件：旋钮与滑块
        self.Knob_Current = QtWidgets.QDial(self.leftPanel)
        self.Knob_Current.setGeometry(QtCore.QRect(220, 710, 61, 61))
        self.Knob_Current.setMinimum(0)
        self.Knob_Current.setMaximum(6000)  # 0..600.0 mA (value/10)
        self.Knob_Current.setSingleStep(1)
        self.Knob_Current.setNotchesVisible(False)
        self.Knob_Current.setObjectName("Knob_Current")

        self.Knob_Tesla = QtWidgets.QDial(self.leftPanel)
        self.Knob_Tesla.setGeometry(QtCore.QRect(480, 710, 61, 61))
        self.Knob_Tesla.setMinimum(-50)  # -5.0 mT (value/10)
        self.Knob_Tesla.setMaximum(50)   # +5.0 mT (value/10)
        self.Knob_Tesla.setSingleStep(1)
        self.Knob_Tesla.setNotchesVisible(False)
        self.Knob_Tesla.setObjectName("Knob_Tesla")

        # 滑条左侧 - 按钮
        self.ProbeMinusBtn = QtWidgets.QPushButton(self.leftPanel)
        self.ProbeMinusBtn.setGeometry(QtCore.QRect(230, 390, 25, 31))
        self.ProbeMinusBtn.setText("-")
        self.ProbeMinusBtn.setObjectName("ProbeMinusBtn")
        self.ProbeMinusBtn.setAutoRepeat(True)  # 长按连续触发
        self.ProbeMinusBtn.setAutoRepeatDelay(300)
        self.ProbeMinusBtn.setAutoRepeatInterval(50)
        
        self.ProbeSlider = QtWidgets.QSlider(self.leftPanel)
        self.ProbeSlider.setGeometry(QtCore.QRect(260, 390, 151, 31))
        self.ProbeSlider.setMinimum(-15)
        self.ProbeSlider.setMaximum(15)
        self.ProbeSlider.setSingleStep(1)
        self.ProbeSlider.setOrientation(QtCore.Qt.Horizontal)
        self.ProbeSlider.setObjectName("ProbeSlider")
        # 初始探针位置设为 0 mm
        self.ProbeSlider.setValue(0)
        
        # 滑条右侧 + 按钮
        self.ProbePlusBtn = QtWidgets.QPushButton(self.leftPanel)
        self.ProbePlusBtn.setGeometry(QtCore.QRect(416, 390, 25, 31))
        self.ProbePlusBtn.setText("+")
        self.ProbePlusBtn.setObjectName("ProbePlusBtn")
        self.ProbePlusBtn.setAutoRepeat(True)  # 长按连续触发
        self.ProbePlusBtn.setAutoRepeatDelay(300)
        self.ProbePlusBtn.setAutoRepeatInterval(50)
        
        # 黑色细线UI（随滑条移动，固定右端266，左端长度变化）
        # 右端固定在leftPanel坐标(266,444)
        self.ProbeIndicatorLine = QtWidgets.QFrame(self.leftPanel)
        self.ProbeIndicatorLine.setGeometry(QtCore.QRect(166, 444, 100, 2))  # 初始位置：滑条0mm时长度100
        self.ProbeIndicatorLine.setStyleSheet("background-color: black;")
        self.ProbeIndicatorLine.setFrameShape(QtWidgets.QFrame.HLine)

        # 实时位置显示框（不保留小数部分），放在滑条上方
        self.ProbePosBox = QtWidgets.QLineEdit(self.leftPanel)
        self.ProbePosBox.setGeometry(QtCore.QRect(260, 360, 151, 25))
        self.ProbePosBox.setObjectName("ProbePosBox")
        self.ProbePosBox.setReadOnly(True)
        self.ProbePosBox.setAlignment(QtCore.Qt.AlignCenter)
        self.ProbePosBox.setText("0 mm")
        # 透明背景、无边框显示
        self.ProbePosBox.setStyleSheet("background: transparent; border: none;")
        self.ProbePosBox.setFrame(False)

        # 微调按钮（电流：左减右加，放在旋钮下方）
        self.CurrentMinus = QtWidgets.QPushButton(self.leftPanel)
        self.CurrentMinus.setGeometry(QtCore.QRect(200, 785, 41, 28))
        self.CurrentMinus.setObjectName("CurrentMinus")
        self.CurrentMinus.setText("-")
        # Use manual repeat via fine_timer; disable QPushButton's built-in auto-repeat to avoid duplicate events.
        self.CurrentMinus.setAutoRepeat(False)

        self.CurrentPlus = QtWidgets.QPushButton(self.leftPanel)
        self.CurrentPlus.setGeometry(QtCore.QRect(260, 785, 41, 28))
        self.CurrentPlus.setObjectName("CurrentPlus")
        self.CurrentPlus.setText("+")
        self.CurrentPlus.setAutoRepeat(False)

        # 微调按钮（特斯拉：左减右加，放在旋钮下方）
        self.TeslaMinus = QtWidgets.QPushButton(self.leftPanel)
        self.TeslaMinus.setGeometry(QtCore.QRect(460, 785, 41, 28))
        self.TeslaMinus.setObjectName("TeslaMinus")
        self.TeslaMinus.setText("-")
        self.TeslaMinus.setAutoRepeat(False)

        self.TeslaPlus = QtWidgets.QPushButton(self.leftPanel)
        self.TeslaPlus.setGeometry(QtCore.QRect(520, 785, 41, 28))
        self.TeslaPlus.setObjectName("TeslaPlus")
        self.TeslaPlus.setText("+")
        self.TeslaPlus.setAutoRepeat(False)

        # 电源和方向切换
        self.PowerSwitch = QtWidgets.QPushButton(self.leftPanel)
        self.PowerSwitch.setGeometry(QtCore.QRect(610, 707, 35, 56))
        self.PowerSwitch.setObjectName("PowerSwitch")
        self.PowerSwitch.setText("")
        self.PowerSwitch.setFlat(True)
        self.PowerSwitch.setStyleSheet("background: transparent; border: none; color: transparent;")

        self.DirectionToggle = QtWidgets.QPushButton(self.leftPanel)
        self.DirectionToggle.setGeometry(QtCore.QRect(220, 290, 41, 41))
        self.DirectionToggle.setCheckable(True)
        self.DirectionToggle.setObjectName("DirectionToggle")
        self.DirectionToggle.setText("↑")
        self.DirectionToggle.setChecked(True)

        # 右侧面板
        self.rightPanel = QtWidgets.QWidget(self.centralwidget)
        self.rightPanel.setGeometry(QtCore.QRect(710, 0, 420, 750))
        
        # ==================== 实验阶段控制区 ====================
        self.stageGroupBox = QtWidgets.QGroupBox(self.rightPanel)
        self.stageGroupBox.setGeometry(QtCore.QRect(5, 5, 410, 110))
        self.stageGroupBox.setTitle("实验阶段")
        
        # 阶段按钮（横向排列）- 4个阶段: 0=选样品, 1=B-X, 2=退磁, 3=回线
        self.stageBtnGroup = QtWidgets.QButtonGroup(self.rightPanel)
        stage_names = ["0.样品", "1.B-X", "2.退磁", "3.回线"]
        self.stageButtons = []
        for i, name in enumerate(stage_names):
            btn = QtWidgets.QPushButton(self.stageGroupBox)
            btn.setGeometry(QtCore.QRect(5 + i * 80, 20, 76, 26))
            btn.setText(name)
            btn.setCheckable(True)
            btn.setObjectName("stageBtn_%d" % i)
            self.stageBtnGroup.addButton(btn, i)
            self.stageButtons.append(btn)
        self.stageButtons[0].setChecked(True)
        
        # 阶段说明标签
        self.stageInfoLabel = QtWidgets.QLabel(self.stageGroupBox)
        self.stageInfoLabel.setGeometry(QtCore.QRect(5, 48, 400, 30))
        self.stageInfoLabel.setWordWrap(True)
        self.stageInfoLabel.setStyleSheet("color: #666; font-size: 11px;")
        self.stageInfoLabel.setText("阶段1：移动探针，记录不同位置的B值，找到均匀区")
        
        # 阶段操作按钮
        self.stagePrevBtn = QtWidgets.QPushButton(self.stageGroupBox)
        self.stagePrevBtn.setGeometry(QtCore.QRect(5, 82, 75, 24))
        self.stagePrevBtn.setText("< 上一阶段")
        self.stagePrevBtn.setEnabled(False)
        
        self.stageNextBtn = QtWidgets.QPushButton(self.stageGroupBox)
        self.stageNextBtn.setGeometry(QtCore.QRect(85, 82, 75, 24))
        self.stageNextBtn.setText("下一阶段 >")
        
        # 退磁按钮（阶段2专用）- 自动退磁
        self.startDegaussBtn = QtWidgets.QPushButton(self.stageGroupBox)
        self.startDegaussBtn.setGeometry(QtCore.QRect(170, 82, 75, 24))
        self.startDegaussBtn.setText("自动退磁")
        self.startDegaussBtn.setVisible(False)
        
        # 手动退磁按钮（阶段2专用）
        self.manualDegaussBtn = QtWidgets.QPushButton(self.stageGroupBox)
        self.manualDegaussBtn.setGeometry(QtCore.QRect(250, 82, 75, 24))
        self.manualDegaussBtn.setText("手动记录")
        self.manualDegaussBtn.setVisible(False)
        self.manualDegaussBtn.setCheckable(True)  # 可切换状态
        
        # 清空退磁曲线按钮
        self.clearDegaussBtn = QtWidgets.QPushButton(self.stageGroupBox)
        self.clearDegaussBtn.setGeometry(QtCore.QRect(330, 82, 75, 24))
        self.clearDegaussBtn.setText("清空曲线")
        self.clearDegaussBtn.setVisible(False)
        
        # 阶段3专用按钮：清空回线数据
        self.clearHysteresisBtn = QtWidgets.QPushButton(self.stageGroupBox)
        self.clearHysteresisBtn.setGeometry(QtCore.QRect(170, 82, 75, 24))
        self.clearHysteresisBtn.setText("清空数据")
        self.clearHysteresisBtn.setVisible(False)
        
        # ==================== 样品选择区域（阶段0专用）====================
        self.sampleSelectWidget = QtWidgets.QWidget(self.rightPanel)
        self.sampleSelectWidget.setGeometry(QtCore.QRect(5, 120, 410, 600))
        self.sampleSelectWidget.setVisible(True)  # 初始显示
        
        # 样品选择标题
        self.sampleTitleLabel = QtWidgets.QLabel(self.sampleSelectWidget)
        self.sampleTitleLabel.setGeometry(QtCore.QRect(10, 10, 390, 30))
        self.sampleTitleLabel.setText("请选择实验样品：")
        self.sampleTitleLabel.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # 样品1：模具钢
        self.sampleMoldSteelBtn = QtWidgets.QPushButton(self.sampleSelectWidget)
        self.sampleMoldSteelBtn.setGeometry(QtCore.QRect(10, 50, 180, 50))
        self.sampleMoldSteelBtn.setText("模具钢\n(半硬磁材料)")
        self.sampleMoldSteelBtn.setCheckable(True)
        self.sampleMoldSteelBtn.setStyleSheet("""
            QPushButton { font-size: 14px; text-align: center; }
            QPushButton:checked { background-color: #4CAF50; color: white; }
        """)
        
        # 样品2：电工纯铁
        self.samplePureIronBtn = QtWidgets.QPushButton(self.sampleSelectWidget)
        self.samplePureIronBtn.setGeometry(QtCore.QRect(210, 50, 180, 50))
        self.samplePureIronBtn.setText("电工纯铁\n(软磁材料)")
        self.samplePureIronBtn.setCheckable(True)
        self.samplePureIronBtn.setStyleSheet("""
            QPushButton { font-size: 14px; text-align: center; }
            QPushButton:checked { background-color: #2196F3; color: white; }
        """)
        
        # 样品参数显示区
        self.sampleParamsGroup = QtWidgets.QGroupBox(self.sampleSelectWidget)
        self.sampleParamsGroup.setGeometry(QtCore.QRect(10, 110, 390, 280))
        self.sampleParamsGroup.setTitle("样品参数")
        
        # 参数标签
        param_labels = [
            ("名称：", "sampleName"),
            ("类型：", "sampleType"),
            ("饱和磁感应强度 Bs：", "sampleBs"),
            ("矫顽力 Hc：", "sampleHc"),
            ("剩磁 Br：", "sampleBr"),
            ("平均磁路长度 l̄：", "sampleL"),
            ("间隙宽度 lg：", "sampleLg"),
            ("线圈匝数 N：", "sampleN"),
            ("截面积 S：", "sampleS"),
            ("特点：", "sampleDesc"),
        ]
        
        self.sampleParamLabels = {}
        self.sampleParamValues = {}
        for i, (label_text, key) in enumerate(param_labels):
            label = QtWidgets.QLabel(self.sampleParamsGroup)
            label.setGeometry(QtCore.QRect(10, 25 + i * 24, 150, 22))
            label.setText(label_text)
            label.setStyleSheet("font-size: 12px;")
            self.sampleParamLabels[key] = label
            
            value = QtWidgets.QLabel(self.sampleParamsGroup)
            value.setGeometry(QtCore.QRect(160, 25 + i * 24, 220, 22))
            value.setText("--")
            value.setStyleSheet("font-size: 12px; font-weight: bold; color: #333;")
            self.sampleParamValues[key] = value
        
        # 样品对比说明
        self.sampleCompareLabel = QtWidgets.QLabel(self.sampleSelectWidget)
        self.sampleCompareLabel.setGeometry(QtCore.QRect(10, 400, 390, 150))
        self.sampleCompareLabel.setWordWrap(True)
        self.sampleCompareLabel.setStyleSheet("font-size: 11px; color: #666; background: #f5f5f5; padding: 10px; border-radius: 5px;")
        self.sampleCompareLabel.setText(
            "【两种样品对比】\n\n"
            "▪ 模具钢（半硬磁）：磁滞回线宽肥，矫顽力大(~500 A/m)，\n"
            "  剩磁高(~77 mT)，退磁较难，适合永磁应用\n\n"
            "▪ 电工纯铁（软磁）：磁滞回线窄瘦，矫顽力小(~80 A/m)，\n"
            "  剩磁低(~25 mT)，易退磁，适合变压器/电机铁芯"
        )
        
        # 连接样品选择按钮信号
        self.sampleMoldSteelBtn.clicked.connect(lambda: self.on_sample_selected('mold_steel'))
        self.samplePureIronBtn.clicked.connect(lambda: self.on_sample_selected('pure_iron'))
        
        # ==================== Tab区域 ====================
        self.rightTabWidget = QtWidgets.QTabWidget(self.rightPanel)
        self.rightTabWidget.setGeometry(QtCore.QRect(5, 120, 410, 600))
        self.rightTabWidget.setVisible(False)  # 初始隐藏（阶段0不显示）
        
        # 数据表Tab
        self.tabDataTable = QtWidgets.QWidget()
        self.DataTable = QtWidgets.QTableWidget(self.tabDataTable)
        self.DataTable.setGeometry(QtCore.QRect(5, 40, 395, 525))
        self.DataTable.setRowCount(0)
        self.DataTable.setColumnCount(5)
        
        # 表格控制按钮
        self.SwitchTableButton = QtWidgets.QPushButton(self.tabDataTable)
        self.SwitchTableButton.setGeometry(QtCore.QRect(5, 8, 65, 26))
        self.SwitchTableButton.setText("切换表")
        self.SwitchTableButton.setVisible(False)  # 初始隐藏（阶段1不需要）
        self.SwitchTableButton.clicked.connect(self.on_switch_table)
        
        self.RecordCurrent = QtWidgets.QPushButton(self.tabDataTable)
        self.RecordCurrent.setGeometry(QtCore.QRect(5, 8, 65, 26))  # 初始位置往左
        self.RecordCurrent.setText("记录当前")
        self.RecordCurrent.clicked.connect(self.on_record_current)
        
        self.DeleteRowButton = QtWidgets.QPushButton(self.tabDataTable)
        self.DeleteRowButton.setGeometry(QtCore.QRect(75, 8, 60, 26))  # 初始位置往左
        self.DeleteRowButton.setText("删除行")
        self.DeleteRowButton.clicked.connect(self.on_delete_current_row)
        
        self.ClearTableButton = QtWidgets.QPushButton(self.tabDataTable)
        self.ClearTableButton.setGeometry(QtCore.QRect(140, 8, 55, 26))  # 初始位置往左
        self.ClearTableButton.setText("清空")
        self.ClearTableButton.clicked.connect(self.on_clear_table)
        
        self.ExportCSVButton = QtWidgets.QPushButton(self.tabDataTable)
        self.ExportCSVButton.setGeometry(QtCore.QRect(200, 8, 65, 26))  # 初始位置往左
        self.ExportCSVButton.setText("导出CSV")
        self.ExportCSVButton.clicked.connect(self.on_export_csv)
        
        self.rightTabWidget.addTab(self.tabDataTable, "数据表")
        
        # 曲线图Tab
        self.tabPlotImage = QtWidgets.QWidget()
        self.PlotContainer = QtWidgets.QWidget(self.tabPlotImage)
        self.PlotContainer.setGeometry(QtCore.QRect(5, 5, 395, 560))
        self.plot_widget = PlotWidget(self.PlotContainer)
        self.plot_widget.setGeometry(QtCore.QRect(0, 0, 395, 560))
        self.rightTabWidget.addTab(self.tabPlotImage, "曲线图")
        
        # 连接Tab切换信号，自动刷新曲线图
        self.rightTabWidget.currentChanged.connect(self.on_tab_changed)
        
        # 隐藏旧的按钮（兼容性）
        self.AutoMeasureButton = QtWidgets.QPushButton()
        self.AutoMeasureButton.setVisible(False)
        self.ExportPNGButton = QtWidgets.QPushButton()
        self.ExportPNGButton.setVisible(False)
        self.CalibrateButton = QtWidgets.QPushButton()
        self.CalibrateButton.setVisible(False)
        self.RunDegaussButton = QtWidgets.QPushButton()
        self.RunDegaussButton.setVisible(False)
        
        # 调试选项（隐藏，始终显示原始B）
        self.ShowRawCheck = QtWidgets.QCheckBox(self.rightPanel)
        self.ShowRawCheck.setGeometry(QtCore.QRect(280, 5, 130, 20))
        self.ShowRawCheck.setText("显示原始B")
        self.ShowRawCheck.setChecked(True)
        self.ShowRawCheck.setVisible(False)  # 隐藏checkbox
        self.ShowRawCheck.toggled.connect(self.on_toggle_raw_display)
        self.debug_show_raw = True
        
        # instantiate single model (Jiles–Atherton) from config if available
        try:
            cfg_path = resource_path("physics_model_config.json")
            cfg = {}
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                except Exception:
                    cfg = {}
            j = cfg.get('jiles', None)
            if j:
                try:
                    self.model = physics_model.JilesAthertonModel(Ms=j.get('Ms', 1e5), a=j.get('a', 1e3),
                                                                 alpha=j.get('alpha', 1e-5), k=j.get('k', 50.0),
                                                                 c=j.get('c', 0.5))
                except Exception:
                    self.model = physics_model.JilesAthertonModel()
            else:
                try:
                    self.model = physics_model.JilesAthertonModel()
                except Exception:
                    self.model = None
            # sync ambient offset if model supports it
            try:
                if self.model and hasattr(self.model, 'get_ambient_offset'):
                    self.ambient_offset_mT = float(self.model.get_ambient_offset())
            except Exception:
                pass
        except Exception:
            self.model = None

        # 状态栏
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        MainWindow.setCentralWidget(self.centralwidget)

        # 初始运行状态
        self.current_value = 0.0
        self.tesla_value = 0.0  # internal in Tesla
        self.tesla_positive = True
        self.power_on = True
        # branch detection state (user-adjustment based)
        self._last_I = float(self.current_value)
        self._dir_confirm_count = 0
        self._current_branch = 0  # -1 (down), 0 (unknown), +1 (up)
        # tuning params
        self._dir_threshold_mA = 0.5
        self._dir_confirm_required = 2
        # auto-measure timing (seconds) - aggressive defaults to complete sweep fast
        self._auto_step_sleep = 0.0005  # per-knob-step delay
        self._auto_sample_sleep = 0.001  # after reaching target, small settle delay
        self.probe_position_mm = 0.0
        self.probe_display_mm = 0.0
        self.probe_physical_mm = 0.0
        # manual override window (seconds since epoch) to allow fine/buttons/direction to temporarily
        # override model output (prevents immediate overwrite by model update)
        self.manual_override_until = 0.0
        self.last_displayed_mT = 0.0
        # zeroing (调零) session state
        self.in_zeroing_session = False
        self.zero_enter_mm = 10.0
        self.zero_current_tol_mA = 0.1
        self.zero_session_timeout_s = 30.0
        self.zero_session_start_ts = 0.0
        # 调零完成标志：只有调零完成后才能进入后续阶段和记录数据
        self.is_zeroed = False
        # ambient offset for zeroing (mT)
        self.ambient_offset_mT = 0.0
        
        # 预生成两种样品的剩磁值（启动时固定，切换样品时不变）
        # 注意：剩磁范围需要与退磁模型一致（-50 ~ 0 mT）
        import random
        self._sample_remanence = {
            'mold_steel': random.uniform(-50.0, -30.0),  # 模具钢：高剩磁（负值）
            'pure_iron': random.uniform(-25.0, -5.0)     # 电工纯铁：低剩磁（负值）
        }
        # last ambient value used to sync the Tesla knob (avoid knob jumping on every update)
        self._last_knob_tesla_sync_mT = None
        # tolerance for considering B as zero during zeroing (mT)
        self.zero_tol_mT = 0.05
        # data manager for tables
        self.data_manager = DataManager()
        
        # 实验阶段控制器
        self.exp_controller = ExperimentController()
        self.exp_controller.stage_changed.connect(self.on_stage_changed)
        self.exp_controller.warning_triggered.connect(self.on_exp_warning)
        self.exp_controller.error_triggered.connect(self.on_exp_error)
        
        # 连接阶段按钮信号
        self.stageBtnGroup.buttonClicked.connect(self.on_stage_button_clicked)
        self.stagePrevBtn.clicked.connect(self.on_stage_prev)
        self.stageNextBtn.clicked.connect(self.on_stage_next)
        self.startDegaussBtn.clicked.connect(self.on_start_degauss)
        self.manualDegaussBtn.clicked.connect(self.on_manual_degauss_toggle)
        self.clearDegaussBtn.clicked.connect(self.on_clear_degauss)
        self.clearHysteresisBtn.clicked.connect(self.on_clear_hysteresis_data)
        
        # 手动退磁状态
        self._manual_degauss_recording = False
        self._manual_degauss_timer = None
        
        # physics model: prefer model loaded from config (Jiles), otherwise create Jiles-Atherton by default
        try:
            if not hasattr(self, 'model') or self.model is None:
                # default to Jiles-Atherton model for higher-fidelity magnetization
                try:
                    self.model = physics_model.JilesAthertonModel()
                except Exception:
                    # fallback: if J-A unavailable, try Preisach as a last resort
                    try:
                        self.model = physics_model.PreisachModel(n=32, H_max=3500.0, weight_sigma=0.5, sensor_noise_std_mT=0.2)
                    except Exception:
                        self.model = None
            # if model supports ambient offset, sync it
            try:
                if hasattr(self.model, 'set_ambient_offset'):
                    self.model.set_ambient_offset(self.ambient_offset_mT)
            except Exception:
                pass
        except Exception:
            self.model = None
        # load I->H fit params from config if available, else use default linear fit from validation
        try:
            cfg_path = resource_path("physics_model_config.json")
            cfg = {}
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                except Exception:
                    cfg = {}
            self.IH_params = cfg.get('I_to_H', {'model': 'linear', 'k': 4680.127014415431, 'b': 90.5112616071001})
        except Exception:
            self.IH_params = {'model': 'linear', 'k': 4680.127014415431, 'b': 90.5112616071001}

        # Branch model manager (handles up/down per-branch params and online micro-refit)
        try:
            self.branch_manager = branch_model_manager.BranchModelManager(online_window=12, online_refit_batch=6, local_seconds=1.5)
        except Exception:
            self.branch_manager = None

        # 微调按钮长按定时器
        self.fine_timer = QtCore.QTimer()
        self.fine_timer.timeout.connect(self.on_fine_timer_timeout)
        self.fine_pressed_button = None
        self.fine_press_time = 0
        self.fine_acceleration = 1

        # 连接信号
        try:
            self.Knob_Current.valueChanged.connect(self.on_current_knob_changed)
        except Exception:
            pass
        try:
            self.Knob_Tesla.valueChanged.connect(self.on_tesla_knob_changed)
        except Exception:
            pass
        try:
            self.DirectionToggle.clicked.connect(self.on_direction_clicked)
        except Exception:
            pass
        try:
            self.PowerSwitch.clicked.connect(self.on_power_clicked)
        except Exception:
            pass

        # 微调按钮信号连接
        try:
            self.CurrentPlus.pressed.connect(lambda: self.on_fine_button_pressed('current', 1))
            self.CurrentPlus.released.connect(lambda: self.on_fine_button_released('current', 1))
            self.CurrentMinus.pressed.connect(lambda: self.on_fine_button_pressed('current', -1))
            self.CurrentMinus.released.connect(lambda: self.on_fine_button_released('current', -1))
            self.TeslaPlus.pressed.connect(lambda: self.on_fine_button_pressed('tesla', 1))
            self.TeslaPlus.released.connect(lambda: self.on_fine_button_released('tesla', 1))
            self.TeslaMinus.pressed.connect(lambda: self.on_fine_button_pressed('tesla', -1))
            self.TeslaMinus.released.connect(lambda: self.on_fine_button_released('tesla', -1))
        except Exception:
            pass

        # 滑条信号连接
        try:
            self.ProbeSlider.valueChanged.connect(self.on_probe_slider_changed)
        except Exception:
            pass
        
        # 滑条+/-按钮信号连接
        try:
            self.ProbeMinusBtn.clicked.connect(self.on_probe_minus_clicked)
            self.ProbePlusBtn.clicked.connect(self.on_probe_plus_clicked)
        except Exception:
            pass
        
        # F2坐标查看模式
        self._coord_mode = False
        self._coord_label = QtWidgets.QLabel(MainWindow)
        self._coord_label.setStyleSheet("background: yellow; color: black; padding: 2px;")
        self._coord_label.setVisible(False)
        self._coord_label.raise_()
        self._main_window = MainWindow
        
        # 使用QShortcut绑定F2快捷键
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        self._f2_shortcut = QShortcut(QKeySequence(QtCore.Qt.Key_F2), MainWindow)
        self._f2_shortcut.activated.connect(self._toggle_coord_mode)
        
        # 鼠标移动定时器
        self._coord_timer = QtCore.QTimer()
        self._coord_timer.timeout.connect(self._update_coord_display)

        # 初始显示：初始化 probe 显示并更新所有显示
        try:
            self.on_probe_slider_changed(self.ProbeSlider.value())
        except Exception:
            pass
        try:
            self.update_displays()
        except Exception:
            pass
        # 检查是否满足自动调零条件（在微调后触发）
        try:
            self.check_auto_zero()
        except Exception:
            pass
        # 初始化表格编辑与当前表（默认 A）
        try:
            self._current_table = 'A'
            self.DataTable.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.EditKeyPressed | QtWidgets.QAbstractItemView.SelectedClicked)
            self.refresh_data_table('A')
            try:
                self.DataTable.itemChanged.connect(self.on_table_item_changed)
            except Exception:
                pass
        except Exception:
            pass
        # Ensure top-buttons visibility/state matches initial table A view:
        try:
            # For table A we only want: 切换表, 记录当前, 删除当前, 清空表格
            try:
                self.AutoMeasureButton.setVisible(False)
            except Exception:
                pass
            try:
                self.ExportPNGButton.setVisible(False)
            except Exception:
                pass
            try:
                self.CalibrateButton.setVisible(False)
            except Exception:
                pass
            try:
                self.RunDegaussButton.setVisible(False)
            except Exception:
                pass
            try:
                self.DeleteRowButton.setVisible(True)
                self.ClearTableButton.setVisible(True)
            except Exception:
                pass
        except Exception:
            pass
        
        # 初始化阶段0的UI状态（样品选择）
        try:
            self.on_stage_changed(0)
        except Exception:
            pass

    # --- Callbacks and helpers ---
    def _toggle_coord_mode(self):
        """F2切换坐标查看模式"""
        from PyQt5.QtGui import QCursor
        self._coord_mode = not self._coord_mode
        if self._coord_mode:
            self._coord_label.setVisible(True)
            self._coord_timer.start(50)  # 50ms更新一次
            self.statusbar.showMessage("坐标模式已开启 - 移动鼠标查看坐标，再按F2关闭")
        else:
            self._coord_label.setVisible(False)
            self._coord_timer.stop()
            self.statusbar.showMessage("坐标模式已关闭")
    
    def _update_coord_display(self):
        """更新坐标显示"""
        from PyQt5.QtGui import QCursor
        try:
            pos = QCursor.pos()
            window_pos = self._main_window.mapFromGlobal(pos)
            # leftPanel坐标（考虑leftPanel的y偏移-80）
            left_panel_pos_x = window_pos.x()
            left_panel_pos_y = window_pos.y() + 80  # leftPanel y偏移是-80
            self._coord_label.setText(f"窗口:({window_pos.x()},{window_pos.y()}) leftPanel:({left_panel_pos_x},{left_panel_pos_y})")
            self._coord_label.adjustSize()
            self._coord_label.move(window_pos.x() + 15, window_pos.y() + 15)
        except Exception:
            pass
    
    def on_current_knob_changed(self, value):
        # Knob value 0..6000 -> 0.0..600.0 mA
        self.current_value = float(value) / 10.0
        # User changed current -> cancel any short manual override so model output updates immediately.
        try:
            # cancel manual override if active
            if hasattr(self, 'manual_override_until') and time.time() < float(self.manual_override_until):
                self.manual_override_until = 0.0
        except Exception:
            pass
        self.update_displays()

    def on_tesla_knob_changed(self, value):
        """
        右侧旋钮用于调节随机磁场偏移（调零用）
        范围: -5.0 到 +5.0 mT (value/10)
        
        调零条件：电流=0且探针在±15mm位置（样品外）
        满足条件时，旋钮直接调节偏移值
        不满足条件时，显示提示但仍允许调节（方便用户操作）
        """
        try:
            # 旋钮值 -50..50 -> -5.0..+5.0 mT
            offset_mT = float(value) / 10.0
            
            # 检查是否满足调零条件：电流=0，探针在样品外（|X| >= 11mm）
            can_zero = (self.current_value < 0.1 and abs(self.probe_display_mm) >= 11)
            
            # 始终更新偏移值（允许用户随时调节）
            self.ambient_offset_mT = offset_mT
            
            # 同步到物理模型
            if hasattr(self, 'model') and self.model and hasattr(self.model, 'set_ambient_offset'):
                self.model.set_ambient_offset(offset_mT)
            
            # 更新显示
            self.update_displays()
            
            # 根据条件显示不同提示
            if can_zero:
                if abs(offset_mT) < 0.05:
                    self.is_zeroed = True  # 标记调零完成
                    self.statusbar.showMessage("调零完成！偏移已归零，可以开始实验")
                else:
                    self.statusbar.showMessage("调零中: 偏移 = %.1f mT (目标: 0.0 mT)" % offset_mT)
            else:
                # 不满足调零条件时的提示
                if self.current_value >= 0.1:
                    self.statusbar.showMessage("提示: 调零需要先将电流调至0 | 当前偏移: %.1f mT" % offset_mT)
                elif abs(self.probe_display_mm) < 11:
                    self.statusbar.showMessage("提示: 调零需要将探针移到±15mm位置 | 当前偏移: %.1f mT" % offset_mT)
        except Exception:
            pass

    def format_current_display(self, value: float) -> str:
        value = max(0.0, min(600.0, float(value)))
        return f"{value:05.1f}"

    def format_tesla_display(self, value: float) -> str:
        value_T = float(value)
        value_mT = value_T * 1000.0
        clamped = max(-2000.0, min(2000.0, value_mT))
        abs_mT = abs(clamped)
        rounded_abs_mT = round(abs_mT, 1)
        if rounded_abs_mT == 0.0:
            abs_mT = 0.0
            sign = ""
        else:
            sign = "-" if clamped < 0 else ""
        formatted = f"{abs_mT:05.1f}"
        return f"{sign}{formatted}"

    def on_fine_button_pressed(self, target, direction):
        self.fine_pressed_button = (target, direction)
        self.fine_press_time = 0
        self.fine_acceleration = 1
        try:
            self.apply_fine_step(target, direction, self.fine_acceleration)
        except Exception:
            pass
        try:
            self.fine_timer.start(100)
        except Exception:
            pass

    def on_fine_button_released(self, target, direction):
        try:
            if self.fine_pressed_button == (target, direction):
                self.fine_pressed_button = None
                try:
                    self.fine_timer.stop()
                except Exception:
                    pass
        except Exception:
            pass

    def on_fine_timer_timeout(self):
        if not getattr(self, 'fine_pressed_button', None):
            return
        try:
            self.fine_press_time += 100
            if self.fine_press_time >= 1500:
                self.fine_acceleration = 50
            elif self.fine_press_time >= 500:
                self.fine_acceleration = 10
            else:
                self.fine_acceleration = 1
            target, direction = self.fine_pressed_button
            try:
                self.apply_fine_step(target, direction, self.fine_acceleration)
            except Exception:
                pass
        except Exception:
            pass

    def apply_fine_step(self, target, direction, acceleration):
        try:
            if target == 'current':
                step = 0.1 * acceleration * direction  # mA
                self.current_value = max(0.0, min(600.0, self.current_value + step))
                knob_value = int(round(self.current_value * 10))
                try:
                    self.Knob_Current.blockSignals(True)
                    self.Knob_Current.setValue(knob_value)
                    self.Knob_Current.blockSignals(False)
                except Exception:
                    pass
                self.update_displays()
            elif target == 'tesla':
                # 微调按钮用于调节随机偏移（调零用）
                step_mT = 0.1 * acceleration * direction
                
                # 检查是否满足调零条件
                can_zero = (self.current_value < 0.1 and abs(self.probe_display_mm) >= 11)
                
                # 始终允许调节偏移值
                new_offset = self.ambient_offset_mT + step_mT
                new_offset = max(-5.0, min(5.0, new_offset))
                self.ambient_offset_mT = new_offset
                
                # 同步到物理模型
                if hasattr(self, 'model') and self.model and hasattr(self.model, 'set_ambient_offset'):
                    self.model.set_ambient_offset(new_offset)
                
                # 更新旋钮显示
                knob_value = int(round(new_offset * 10))
                try:
                    self.Knob_Tesla.blockSignals(True)
                    self.Knob_Tesla.setValue(knob_value)
                    self.Knob_Tesla.blockSignals(False)
                except Exception:
                    pass
                
                # 更新显示
                self.update_displays()
                
                # 根据条件显示提示
                if can_zero:
                    if abs(new_offset) < 0.05:
                        self.is_zeroed = True  # 标记调零完成
                        self.statusbar.showMessage("调零完成！偏移已归零，可以开始实验")
                    else:
                        self.statusbar.showMessage("调零中: 偏移 = %.1f mT (目标: 0.0 mT)" % new_offset)
                else:
                    if self.current_value >= 0.1:
                        self.statusbar.showMessage("提示: 调零需要先将电流调至0 | 当前偏移: %.1f mT" % new_offset)
                    elif abs(self.probe_display_mm) < 11:
                        self.statusbar.showMessage("提示: 调零需要将探针移到±15mm位置 | 当前偏移: %.1f mT" % new_offset)
        except Exception:
            pass

    def update_displays(self):
        """
        更新LCD显示：电流和磁场
        使用新的基于实测数据拟合的磁滞模型
        
        调零逻辑：
        - 当电流=0且探针在±15mm位置时，LCD只显示偏移值（用于调零）
        - 其他情况下，LCD显示完整的磁场值（包含偏移）
        """
        # 电源关闭时不更新任何LCD显示
        if not self.power_on:
            return
        
        # 检查是否已选择样品，未选择时不更新磁场LCD
        sample_selected = getattr(self.exp_controller, '_selected_sample', None) is not None
        
        # 检查是否正在退磁
        is_degaussing = getattr(self, '_manual_degauss_recording', False) or \
                       (getattr(self, '_degauss_timer', None) and getattr(self, '_degauss_timer').isActive())
        
        # 更新电流显示（始终允许，即使在退磁模式）
        try:
            self.LCD_Current.display(self.format_current_display(self.current_value))
        except Exception:
            pass
        
        # 更新磁场显示
        # 在退磁模式下，跳过B值自动计算，由退磁函数单独处理
        if is_degaussing:
            return
        
        # 未选择样品时，磁场LCD显示空白
        if not sample_selected:
            try:
                self.LCD_Tesla.display("---.-")
            except Exception:
                pass
            return
        
        try:
            # 检查是否处于调零状态：电流接近0且探针在样品外（|X| >= 11mm）
            is_zeroing_position = (self.current_value < 0.1 and abs(self.probe_display_mm) >= 11)
            
            if is_zeroing_position:
                # 调零状态：LCD只显示偏移值
                display_mT = self.ambient_offset_mT
                self.last_displayed_mT = display_mT
            else:
                # 正常测量状态：计算完整磁场
                # 计算带符号的电流值 (mA)
                I_signed = self.current_value if self.tesla_positive else -self.current_value
                
                # 使用物理模型获取 B 值
                if physics_model is not None:
                    try:
                        # 阶段3使用磁滞回线模型
                        stage = self.exp_controller.current_stage
                        if stage == 3:
                            measured_mT = physics_model.get_B_for_hysteresis(I_signed)
                            # 检查是否超过换向后的最大电流
                            if physics_model.check_hysteresis_exceed_error():
                                self.statusbar.showMessage("操作错误: 换向后电流不能超过之前的最大值！请重启设备", 5000)
                                physics_model.clear_hysteresis_exceed_error()
                        else:
                            # 其他阶段使用 I→B 映射
                            measured_mT = physics_model.get_B_from_I(
                                I_signed, 
                                self.probe_display_mm, 
                                self.ambient_offset_mT,
                                apply_position_coupling=True
                            )
                    except Exception:
                        # 回退到简单计算
                        measured_mT = I_signed * 0.3 + self.ambient_offset_mT
                else:
                    # 没有物理模型时使用简单线性关系
                    measured_mT = I_signed * 0.3 + self.ambient_offset_mT
                
                # 保存原始测量值
                self.last_displayed_mT = float(measured_mT)
                
                # LCD显示测量值（不减去偏移，与样品参数面板Br一致）
                display_mT = measured_mT
            
            # 更新内部状态
            self.tesla_value = abs(display_mT) / 1000.0
            
            # 范围检查
            if abs(display_mT) > 2000.0:
                try:
                    self.statusbar.showMessage("警告: 磁场 (%.1f mT) 超出范围，已限制到 2000 mT" % display_mT)
                except Exception:
                    pass
                display_mT = 2000.0 if display_mT > 0 else -2000.0
            
            # 格式化并显示
            display_T = display_mT / 1000.0
            disp = self.format_tesla_display(display_T)
            self.LCD_Tesla.display(disp)
            
            # 更新状态栏
            try:
                if is_zeroing_position:
                    if abs(self.ambient_offset_mT) < 0.05:
                        self.statusbar.showMessage("调零完成！偏移已归零，可以开始实验")
                    else:
                        self.statusbar.showMessage("调零模式: 偏移 = %.1f mT (用右侧旋钮调至0)" % self.ambient_offset_mT)
                elif physics_model is not None and getattr(self, 'debug_show_raw', False):
                    # 调试模式显示分支信息
                    branch_info = physics_model.get_branch_info()
                    branch_name = branch_info.get('current_branch', 'unknown')
                    direction = branch_info.get('direction', 0)
                    dir_str = '↑' if direction > 0 else ('↓' if direction < 0 else '-')
                    I_signed = self.current_value if self.tesla_positive else -self.current_value
                    self.statusbar.showMessage("分支: %s %s | I=%.1f mA | B=%.1f mT" % (branch_name, dir_str, I_signed, self.last_displayed_mT))
            except Exception:
                pass
                
        except Exception:
            pass

    def on_record_current(self):
        """
        把当前测量（I, B）记录到当前表（默认表B），并自动计算 H（优先使用物理映射）。
        阶段3使用磁滞回线模型计算B值。
        """
        try:
            # 检查是否已调零（阶段1除外）
            stage = self.exp_controller.current_stage
            if stage > 1 and not self.is_zeroed:
                self.statusbar.showMessage("请先完成调零！将电流调至0，探针移到±15mm，用右侧旋钮将偏移调至0")
                return
            
            table = getattr(self, '_current_table', 'A')
            I_mA = float(self.current_value)
            
            # 阶段3：使用带符号电流和磁滞回线模型
            stage = self.exp_controller.current_stage
            if stage == 3:
                I_signed = I_mA if self.tesla_positive else -I_mA
                # 使用磁滞回线模型计算B值
                try:
                    raw_B_mT = physics_model.get_B_for_hysteresis(I_signed)
                except Exception:
                    raw_B_mT = float(getattr(self, 'last_displayed_mT', 0))
                # H = N * I / L = 2000 * (I/1000) / 0.238 ≈ 8.4 * I (基于样品线圈参数)
                H_val = 2000 * (I_signed / 1000.0) / 0.238
                I_mA = I_signed  # 使用带符号电流
                
                # 格式化数值：I和B为1位小数，H为整数，并处理-0.0的情况
                I_mA = round(I_mA, 1)
                raw_B_mT = round(raw_B_mT, 1)
                H_val = int(round(H_val))  # H值为整数
                if abs(I_mA) < 0.05:
                    I_mA = 0.0
                if abs(raw_B_mT) < 0.05:
                    raw_B_mT = 0.0
                if abs(H_val) < 1:
                    H_val = 0
                
                # 阶段3直接记录到表B
                row = {'I/mA': I_mA, 'B/mT': raw_B_mT, 'H/A_m': H_val}
                self.data_manager.add_row('B', row)
                self.refresh_data_table('B')
                if self.rightTabWidget.currentIndex() == 1:
                    self.refresh_plot_for_current_stage()
                self.statusbar.showMessage(f"已记录: I={I_mA:.1f}mA, B={raw_B_mT:.1f}mT, H={H_val:.0f}A/m")
                return
            else:
                # 其他阶段：使用原有逻辑
                try:
                    H_val = physics_model.physical_I_to_H(I_mA)
                except Exception:
                    H_val = physics_model.I_to_H(I_mA, {'model': 'linear', 'k': 0.0, 'b': 0.0})
                # Use the LCD displayed value for B (per user request)
                try:
                    raw_B_mT = float(getattr(self, 'last_displayed_mT', self.read_current_B_from_model_or_display()))
                except Exception:
                    raw_B_mT = float(self.read_current_B_from_model_or_display())
            if table == 'A':
                # record probe position and B (X as integer, B as 1 decimal)
                try:
                    x_val = int(round(self.probe_display_mm))
                except Exception:
                    x_val = int(round(self.probe_display_mm))
                # 格式化B值为1位小数
                raw_B_mT = round(raw_B_mT, 1)
                row = {'X/mm': x_val, 'B/mT': raw_B_mT}
                self.data_manager.add_row('A', row)
                self.refresh_data_table('A')
                # 自动刷新曲线图（如果当前在曲线图Tab）
                if self.rightTabWidget.currentIndex() == 1:
                    self.refresh_plot_for_current_stage()
                self.statusbar.showMessage("已记录当前到表A")
            else:
                # 格式化数值：I为1位小数，B为1位小数，H为整数
                I_mA = round(I_mA, 1)
                raw_B_mT = round(raw_B_mT, 1)
                H_val = int(round(H_val))  # H值为整数
                row = {'I/mA': I_mA, 'B/mT': raw_B_mT, 'H/A_m': H_val, 'remark': ''}
                self.data_manager.add_row('B', row)
                self.refresh_data_table('B')
                # 自动刷新曲线图（如果当前在曲线图Tab）
                if self.rightTabWidget.currentIndex() == 1:
                    self.refresh_plot_for_current_stage()
                self.statusbar.showMessage("已记录当前到表B")

                # Online micro-refinement for current branch
                try:
                    branch_label = 'up' if getattr(self, '_current_branch', 0) >= 0 else 'down'
                    samples = self.data_manager.get_table('B')
                    sample_list = []
                    for r in samples[-12:]:  # Last 12 samples for quick refinement
                        try:
                            I = float(r.get('I/mA', 0.0))
                            B = float(r.get('B/mT', 0.0))
                            H = float(r.get('H/A_m', 0.0)) if r.get('H/A_m', '') != '' else physics_model.physical_I_to_H(I)
                            sample_list.append((I, B, H))
                        except Exception:
                            continue

                    if len(sample_list) >= 6 and physics_model:  # Need at least 6 samples
                        import threading
                        def _refine_async():
                            try:
                                newp, before_err, after_err = physics_model.local_refine(f"jiles_{branch_label}", sample_list, seconds=1.0)
                                if newp and after_err < before_err * 0.95:  # At least 5% improvement
                                    # Save improved parameters
                                    physics_model.write_jiles_params_to_config(newp, f"jiles_{branch_label}")
                                    # Update UI display
                                    try:
                                        import time
                                        QtCore.QTimer.singleShot(0, self.update_displays)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        threading.Thread(target=_refine_async, daemon=True).start()
                except Exception:
                    pass
        except Exception:
            QtWidgets.QMessageBox.warning(None, "记录失败", "无法记录当前测量")

    def read_current_B_from_model_or_display(self) -> float:
        """
        返回当前原始磁场读数 (mT)，不减 ambient_offset_mT。
        """
        try:
            # Prefer asking model for measured B if available
            if hasattr(self, 'model') and self.model:
                try:
                    # compute H from current using I->H params
                    try:
                        H_val = physics_model.I_to_H(self.current_value, getattr(self, 'IH_params', {'model':'linear','k':4680.127,'b':90.511}))
                    except NotImplementedError:
                        # Inform user mapping missing and fall back to display value
                        try:
                            self.statusbar.showMessage("I->H mapping not implemented; using displayed B")
                        except Exception:
                            pass
                        raise
                    H_signed = H_val if self.tesla_positive else -H_val
                    return float(physics_model.get_measured_B(self.model, H_signed, self.probe_display_mm, self.ambient_offset_mT, getattr(self.model, 'sensor_noise_std_mT', 0.0)))
                except NotImplementedError:
                    # fall back to displayed cached value
                    try:
                        return float(getattr(self, 'last_displayed_mT', 0.0))
                    except Exception:
                        return 0.0
                except Exception:
                    # any other model error -> fall back to displayed cached value
                    pass
            # fallback to using displayed cached value if present
            try:
                return float(getattr(self, 'last_displayed_mT', 0.0))
            except Exception:
                return 0.0
        except Exception:
            return 0.0

    def on_calibrate_clicked(self):
        """
        从当前表B读取样本并用 physics_model.fit_jiles_from_samples 拟合 J-A 参数。
        """
        try:
            rows = self.data_manager.get_table('B')
            if not rows:
                QtWidgets.QMessageBox.information(None, "标定", "表B为空，请先导入或记录样本数据。")
                return
            samples = []
            for r in rows:
                try:
                    I = float(r.get('I/mA', 0.0))
                    B = float(r.get('B/mT', 0.0))
                    H = float(r.get('H/A_m', 0.0)) if r.get('H/A_m', '') != '' else physics_model.physical_I_to_H(I)
                    samples.append((I, B, H))
                except Exception:
                    continue
            if not samples:
                QtWidgets.QMessageBox.information(None, "标定", "没有可用的数值样本。")
                return

            # Disable button and show progress
            try:
                self.CalibrateButton.setEnabled(False)
                self.statusbar.showMessage("开始离线标定（10分钟）...")
            except Exception:
                pass

            # Run offline fitting asynchronously
            import subprocess
            import threading

            def run_offline_fit():
                try:
                    # Run the offline fitter script
                    result = subprocess.run([
                        sys.executable, "fit_jiles_offline.py"
                    ], capture_output=True, text=True, timeout=660)  # 11 minute timeout

                    # Parse result - for now just reload config and update UI
                    try:
                        # Reload model from updated config
                        cfg_path = resource_path("physics_model_config.json")
                        if os.path.exists(cfg_path):
                            with open(cfg_path, "r", encoding="utf-8") as f:
                                cfg = json.load(f)
                            j = cfg.get('jiles', None)
                            if j:
                                self.model = physics_model.JilesAthertonModel(
                                    Ms=j.get('Ms', 1e5), a=j.get('a', 1e3),
                                    alpha=j.get('alpha', 1e-5), k=j.get('k', 50.0),
                                    c=j.get('c', 0.5)
                                )

                        # Update UI
                        def update_ui():
                            try:
                                self.update_displays()
                                self.statusbar.showMessage("离线标定完成，参数已更新")
                                self.CalibrateButton.setEnabled(True)
                            except Exception:
                                pass

                        QtCore.QTimer.singleShot(0, update_ui)

                    except Exception as e:
                        def show_error():
                            try:
                                QtWidgets.QMessageBox.warning(None, "标定完成但加载失败", f"标定可能已完成但无法加载新参数: {e}")
                                self.CalibrateButton.setEnabled(True)
                            except Exception:
                                pass
                        QtCore.QTimer.singleShot(0, show_error)

                except subprocess.TimeoutExpired:
                    def show_timeout():
                        try:
                            QtWidgets.QMessageBox.warning(None, "标定超时", "离线标定超时（超过11分钟），可能仍在后台运行")
                            self.CalibrateButton.setEnabled(True)
                        except Exception:
                            pass
                    QtCore.QTimer.singleShot(0, show_timeout)

                except Exception as e:
                    def show_error():
                        try:
                            QtWidgets.QMessageBox.warning(None, "标定失败", f"离线标定过程中发生错误: {e}")
                            self.CalibrateButton.setEnabled(True)
                        except Exception:
                            pass
                    QtCore.QTimer.singleShot(0, show_error)

            # Start the fitting thread
            fitting_thread = threading.Thread(target=run_offline_fit, daemon=True)
            fitting_thread.start()

        except Exception:
            QtWidgets.QMessageBox.warning(None, "标定失败", "标定过程中发生错误，请检查样本数据格式。")

    # ==================== 缺失的回调函数 ====================

    def on_direction_clicked(self):
        """切换磁场方向（正/负）"""
        try:
            self.tesla_positive = self.DirectionToggle.isChecked()
            self.DirectionToggle.setText("↑" if self.tesla_positive else "↓")
            self.update_displays()
        except Exception:
            pass

    def on_power_clicked(self):
        """电源开关 - 第一次点击关闭(隐藏LCD)，第二次点击重启"""
        try:
            # 检查当前电源状态
            if self.power_on:
                # 当前是开启状态 -> 关闭设备
                self.power_on = False
                
                # 隐藏所有LCD显示
                self.LCD_Tesla.display("")
                self.LCD_Current.display("")
                
                # 显示关闭提示
                self.statusbar.showMessage("设备已关闭，再次点击电源开关重启")
            else:
                # 当前是关闭状态 -> 重启设备
                self.power_on = True
                
                # 重启设备：将电流归零
                self.current_value = 0.0
                
                # 更新电流旋钮显示
                try:
                    self.Knob_Current.blockSignals(True)
                    self.Knob_Current.setValue(0)
                    self.Knob_Current.blockSignals(False)
                except Exception:
                    pass
                
                # 重置physics_model模块级别的状态
                # 使用restore_to_power_on_state恢复到电源开启状态
                # 如果已退磁则恢复到退磁终点值，否则恢复到启动时的随机剩磁
                if physics_model is not None:
                    try:
                        if hasattr(physics_model, 'restore_to_power_on_state'):
                            physics_model.restore_to_power_on_state()
                    except Exception:
                        pass
                
                # 重置分支检测状态
                self._last_I = 0.0
                self._dir_confirm_count = 0
                self._current_branch = 0
                
                # 更新显示
                self.update_displays()
                
                # 显示重启提示
                self.statusbar.showMessage("设备已重启：电流归0，模型已重置")
        except Exception:
            pass

    def on_probe_slider_changed(self, value):
        """探针滑条变化回调"""
        try:
            # 滑条值直接是 -10 到 +10 的整数 mm
            self.probe_display_mm = int(value)
            # 物理有效范围限制在 ±10 mm
            self.probe_physical_mm = max(-10, min(10, self.probe_display_mm))
            # 更新显示
            self.ProbePosBox.setText("%d mm" % self.probe_display_mm)
            
            # 更新黑色细线位置（右端固定266，左端随滑条移动）
            # 滑条值(mm)直接对应位置：0mm→x=113, -10mm→x=97, 10mm→x=132
            # 分段线性：负值斜率1.6，正值斜率1.9
            if value < 0:
                line_left_x = int(113 + value * 1.6)  # -10时: 113-16=97
            else:
                line_left_x = int(113 + value * 1.9)  # 10时: 113+19=132
            line_right_x = 266  # 右端固定x坐标
            line_y = 444  # leftPanel内的y坐标
            line_length = max(0, line_right_x - line_left_x)
            if line_length > 0:
                self.ProbeIndicatorLine.setGeometry(QtCore.QRect(line_left_x, line_y, line_length, 2))
                self.ProbeIndicatorLine.setVisible(True)
            else:
                self.ProbeIndicatorLine.setVisible(False)
            
            self.update_displays()
        except Exception:
            pass

    def on_probe_minus_clicked(self):
        """探针滑条 - 按钮回调"""
        try:
            current_val = self.ProbeSlider.value()
            if current_val > self.ProbeSlider.minimum():
                self.ProbeSlider.setValue(current_val - 1)
        except Exception:
            pass

    def on_probe_plus_clicked(self):
        """探针滑条 + 按钮回调"""
        try:
            current_val = self.ProbeSlider.value()
            if current_val < self.ProbeSlider.maximum():
                self.ProbeSlider.setValue(current_val + 1)
        except Exception:
            pass

    def on_toggle_raw_display(self, checked):
        """切换原始/校正磁场显示"""
        try:
            self.debug_show_raw = checked
            self.update_displays()
        except Exception:
            pass

    def on_switch_table(self):
        """切换表格 A/B"""
        try:
            if self._current_table == 'A':
                self._current_table = 'B'
                self.SwitchTableButton.setText("切换到表A")
                # 表B显示更多按钮
                self.AutoMeasureButton.setVisible(True)
                self.ExportPNGButton.setVisible(True)
                self.CalibrateButton.setVisible(True)
                self.RunDegaussButton.setVisible(True)
            else:
                self._current_table = 'A'
                self.SwitchTableButton.setText("切换到表B")
                # 表A隐藏部分按钮
                self.AutoMeasureButton.setVisible(False)
                self.ExportPNGButton.setVisible(False)
                self.CalibrateButton.setVisible(False)
                self.RunDegaussButton.setVisible(False)
            self.refresh_data_table(self._current_table)
            self.statusbar.showMessage(f"已切换到表{self._current_table}")
        except Exception:
            pass

    def refresh_data_table(self, table: str):
        """刷新表格显示"""
        try:
            self.DataTable.blockSignals(True)
            rows = self.data_manager.get_table(table)
            if table == 'A':
                # 表A: X/mm, B/mT
                self.DataTable.setColumnCount(2)
                self.DataTable.setHorizontalHeaderLabels(['X/mm', 'B/mT'])
                self.DataTable.setRowCount(len(rows))
                for i, row in enumerate(rows):
                    self.DataTable.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row.get('X/mm', ''))))
                    b_val = row.get('B/mT', '')
                    if isinstance(b_val, (int, float)):
                        b_val = f"{b_val:.1f}"
                    self.DataTable.setItem(i, 1, QtWidgets.QTableWidgetItem(str(b_val)))
            else:
                # 表B: I/mA, B/mT, H/(A/m)
                self.DataTable.setColumnCount(3)
                self.DataTable.setHorizontalHeaderLabels(['I/mA', 'B/mT', 'H/(A/m)'])
                self.DataTable.setRowCount(len(rows))
                for i, row in enumerate(rows):
                    i_val = row.get('I/mA', '')
                    if isinstance(i_val, (int, float)):
                        i_val = f"{i_val:.1f}"
                    self.DataTable.setItem(i, 0, QtWidgets.QTableWidgetItem(str(i_val)))
                    b_val = row.get('B/mT', '')
                    if isinstance(b_val, (int, float)):
                        b_val = f"{b_val:.1f}"
                    self.DataTable.setItem(i, 1, QtWidgets.QTableWidgetItem(str(b_val)))
                    h_val = row.get('H/A_m', row.get('H/(A/m)', ''))
                    if isinstance(h_val, (int, float)):
                        h_val = f"{h_val:.0f}"
                    self.DataTable.setItem(i, 2, QtWidgets.QTableWidgetItem(str(h_val)))
            # 让列宽自动填满表格
            header = self.DataTable.horizontalHeader()
            header.setStretchLastSection(True)
            for col in range(self.DataTable.columnCount()):
                header.setSectionResizeMode(col, QtWidgets.QHeaderView.Stretch)
            self.DataTable.blockSignals(False)
        except Exception:
            self.DataTable.blockSignals(False)

    def on_table_item_changed(self, item):
        """表格单元格编辑回调"""
        try:
            row = item.row()
            col = item.column()
            value = item.text()
            table = self._current_table
            rows = self.data_manager.get_table(table)
            if row < len(rows):
                if table == 'A':
                    keys = ['X/mm', 'B/mT']
                else:
                    keys = ['I/mA', 'B/mT', 'H/A_m', 'remark']
                if col < len(keys):
                    try:
                        if keys[col] != 'remark':
                            rows[row][keys[col]] = float(value)
                        else:
                            rows[row][keys[col]] = value
                    except ValueError:
                        rows[row][keys[col]] = value
        except Exception:
            pass

    def on_delete_current_row(self):
        """删除当前选中行"""
        try:
            row = self.DataTable.currentRow()
            if row >= 0:
                reply = QtWidgets.QMessageBox.question(
                    None, "确认删除", f"确定要删除第 {row+1} 行吗？",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.Yes:
                    self.data_manager.delete_row(self._current_table, row)
                    self.refresh_data_table(self._current_table)
                    self.statusbar.showMessage(f"已删除第 {row+1} 行")
        except Exception:
            pass

    def on_clear_table(self):
        """清空当前表格"""
        try:
            reply = QtWidgets.QMessageBox.question(
                None, "确认清空", f"确定要清空表{self._current_table}吗？此操作不可撤销！",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.data_manager.clear_table(self._current_table)
                self.refresh_data_table(self._current_table)
                self.statusbar.showMessage(f"已清空表{self._current_table}")
        except Exception:
            pass

    def on_auto_measure(self):
        """自动测量（占位）"""
        try:
            self.statusbar.showMessage("自动测量功能开发中...")
        except Exception:
            pass

    def on_export_png(self):
        """导出PNG图像"""
        try:
            if self.plot_widget:
                path, _ = QFileDialog.getSaveFileName(None, "导出PNG", "", "PNG Files (*.png)")
                if path:
                    self.plot_widget.export_png(path)
                    self.statusbar.showMessage(f"已导出到 {path}")
        except Exception:
            pass

    def on_run_degauss_and_measure(self):
        """退磁并测量（占位）"""
        try:
            self.statusbar.showMessage("退磁并测量功能开发中...")
        except Exception:
            pass

    def check_auto_zero(self):
        """检查自动调零条件（占位）"""
        pass

    def apply_random_field_offset(self, offset_mT: float):
        """应用随机磁场偏移"""
        try:
            self.ambient_offset_mT = float(offset_mT)
            self.update_displays()
        except Exception:
            pass

    def on_import_csv(self):
        """导入CSV文件"""
        try:
            path, _ = QFileDialog.getOpenFileName(None, "导入CSV", "", "CSV Files (*.csv)")
            if path:
                table, count = self.data_manager.import_csv(path)
                self._current_table = table
                self.refresh_data_table(table)
                self.statusbar.showMessage(f"已导入 {count} 行到表{table}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "导入失败", f"导入CSV失败: {e}")

    def on_export_csv(self):
        """导出CSV文件"""
        try:
            path, _ = QFileDialog.getSaveFileName(None, "导出CSV", "", "CSV Files (*.csv)")
            if path:
                count = self.data_manager.export_csv(self._current_table, path)
                self.statusbar.showMessage(f"已导出 {count} 行到 {path}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "导出失败", f"导出CSV失败: {e}")

    def on_save_session(self):
        """保存会话"""
        try:
            path, _ = QFileDialog.getSaveFileName(None, "保存会话", "", "JSON Files (*.json)")
            if path:
                self.data_manager.save_session(path)
                self.statusbar.showMessage(f"会话已保存到 {path}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "保存失败", f"保存会话失败: {e}")

    def on_load_session(self):
        """加载会话"""
        try:
            path, _ = QFileDialog.getOpenFileName(None, "加载会话", "", "JSON Files (*.json)")
            if path:
                self.data_manager.load_session(path)
                self.refresh_data_table(self._current_table)
                self.statusbar.showMessage("已加载会话 " + path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "加载失败", "加载会话失败: " + str(e))

    # ==================== 实验阶段控制回调 ====================
    
    def on_stage_changed(self, stage: int, name: str = ""):
        """阶段变化回调"""
        try:
            # 更新按钮状态 (阶段号从0开始)
            for i, btn in enumerate(self.stageButtons):
                btn.setChecked(i == stage)
            
            # 更新上一阶段/下一阶段按钮状态
            self.stagePrevBtn.setEnabled(stage > 0)  # 阶段0时禁用上一阶段
            self.stageNextBtn.setEnabled(stage < 3)  # 阶段3时禁用下一阶段
            
            # 更新说明文字
            stage_info = {
                0: "阶段0：选择实验样品（模具钢或电工纯铁）",
                1: "阶段1：移动探针，记录不同位置的B值，找到均匀区",
                2: "阶段2：点击[开始退磁]，观察B-H曲线趋近于原点",
                3: "阶段3：测量完整磁滞回线，记录I-B-H数据"
            }
            self.stageInfoLabel.setText(stage_info.get(stage, ""))
            
            # 根据阶段调整控件可见性
            self.startDegaussBtn.setVisible(stage == 2)
            self.manualDegaussBtn.setVisible(stage == 2)
            self.clearDegaussBtn.setVisible(stage == 2)  # 阶段2显示清空曲线按钮
            self.clearHysteresisBtn.setVisible(stage == 3)
            
            # 阶段0、1、3隐藏切换表按钮
            if stage == 0 or stage == 1 or stage == 3:
                self.SwitchTableButton.setVisible(False)
                # 把按钮往左移动
                self.RecordCurrent.setGeometry(QtCore.QRect(5, 8, 65, 26))
                self.DeleteRowButton.setGeometry(QtCore.QRect(75, 8, 60, 26))
                self.ClearTableButton.setGeometry(QtCore.QRect(140, 8, 55, 26))
                self.ExportCSVButton.setGeometry(QtCore.QRect(200, 8, 65, 26))
            else:
                self.SwitchTableButton.setVisible(True)
                # 恢复原位置
                self.RecordCurrent.setGeometry(QtCore.QRect(75, 8, 65, 26))
                self.DeleteRowButton.setGeometry(QtCore.QRect(145, 8, 60, 26))
                self.ClearTableButton.setGeometry(QtCore.QRect(210, 8, 55, 26))
                self.ExportCSVButton.setGeometry(QtCore.QRect(270, 8, 65, 26))
            
            # 阶段2隐藏数据表Tab，只显示曲线图
            if stage == 2:
                self.rightTabWidget.setTabVisible(0, False)  # 隐藏数据表Tab
                self.rightTabWidget.setCurrentIndex(1)  # 切换到曲线图Tab
            else:
                self.rightTabWidget.setTabVisible(0, True)  # 显示数据表Tab
            
            # 阶段1、2、3禁用电流旋钮交互（断开信号），只用+/-按钮控制
            if stage in (1, 2, 3):
                try:
                    self.Knob_Current.valueChanged.disconnect(self.on_current_knob_changed)
                except Exception:
                    pass
                self._knob_current_disabled = True
            else:
                # 其他阶段恢复电流旋钮交互（重新连接信号）
                if getattr(self, '_knob_current_disabled', False):
                    try:
                        self.Knob_Current.valueChanged.connect(self.on_current_knob_changed)
                    except Exception:
                        pass
                    self._knob_current_disabled = False
            
            # 如果离开阶段2，停止手动记录
            if stage != 2 and getattr(self, '_manual_degauss_recording', False):
                self._stop_manual_degauss_recording()
            
            # 更新数据管理器阶段
            self.data_manager.set_stage(stage)
            
            # 根据阶段调整界面显示
            if stage == 0:
                # 样品选择阶段：显示样品选择界面，隐藏Tab
                self.sampleSelectWidget.setVisible(True)
                self.rightTabWidget.setVisible(False)
                self.statusbar.showMessage("阶段0: 选择实验样品")
            elif stage == 1:
                # B-X关系显示数据表
                self.sampleSelectWidget.setVisible(False)
                self.rightTabWidget.setVisible(True)
                self.rightTabWidget.setCurrentIndex(0)  # 数据表tab
                self._current_table = 'A'  # 切换到表A
                self.refresh_data_table('A')
                self.statusbar.showMessage("阶段1: 测量B-X关系")
            elif stage == 2:
                # 退磁阶段显示曲线图
                self.sampleSelectWidget.setVisible(False)
                self.rightTabWidget.setVisible(True)
                self.rightTabWidget.setCurrentIndex(1)  # 曲线图tab
                self.refresh_plot_for_current_stage()
                self.statusbar.showMessage("阶段2: 退磁")
            elif stage == 3:
                # 磁滞回线显示数据表
                self.sampleSelectWidget.setVisible(False)
                self.rightTabWidget.setVisible(True)
                self.rightTabWidget.setCurrentIndex(0)  # 数据表tab
                self._current_table = 'B'  # 切换到表B
                self.refresh_data_table('B')
                
                # 使用退磁终点值初始化磁滞回线模型
                degauss_end_B = getattr(self, '_degauss_end_B', 0.0)
                if physics_model is not None:
                    try:
                        hyst_model = physics_model.get_hysteresis_model()
                        hyst_model.reset_hysteresis_state(degauss_end_B)
                        print(f"[阶段3] 磁滞回线模型已初始化，起点B={degauss_end_B:.1f}mT")
                    except Exception as e:
                        print(f"[阶段3] 初始化磁滞模型失败: {e}")
                
                self.statusbar.showMessage(f"阶段3: 测量磁滞回线 (起点B={degauss_end_B:.1f}mT)")
                self.refresh_plot_for_current_stage()
        except Exception:
            pass
    
    def on_stage_button_clicked(self, button):
        """阶段按钮点击"""
        try:
            stage = self.stageBtnGroup.id(button)
            if stage >= 0:
                # 从阶段0进入后续阶段需要先选择样品
                if stage > 0 and self.exp_controller.selected_sample is None:
                    self.statusbar.showMessage("请先选择样品！")
                    QtWidgets.QMessageBox.warning(None, "未选择样品", "请先在阶段0选择实验样品！")
                    return
                # 阶段1及以后需要先调零
                if stage > 1 and not self.is_zeroed:
                    self.statusbar.showMessage("请先完成调零！将电流调至0，探针移到±15mm，用右侧旋钮将偏移调至0")
                    QtWidgets.QMessageBox.warning(None, "未调零", "请先完成调零操作！\n\n调零方法：\n1. 将电流调至0\n2. 将探针移到±15mm位置\n3. 用右侧旋钮将偏移调至0")
                    return
                self.exp_controller.set_stage(stage)
        except Exception:
            pass
    
    def on_stage_prev(self):
        """上一阶段"""
        self.exp_controller.prev_stage()
    
    def on_stage_next(self):
        """下一阶段"""
        current_stage = self.exp_controller.current_stage
        # 从阶段0进入阶段1需要先选择样品
        if current_stage == 0:
            if self.exp_controller.selected_sample is None:
                self.statusbar.showMessage("请先选择样品！")
                QtWidgets.QMessageBox.warning(None, "未选择样品", "请先选择实验样品！")
                return
        # 从阶段1进入后续阶段需要先调零
        if current_stage == 1 and not self.is_zeroed:
            self.statusbar.showMessage("请先完成调零！将电流调至0，探针移到±15mm，用右侧旋钮将偏移调至0")
            QtWidgets.QMessageBox.warning(None, "未调零", "请先完成调零操作！\n\n调零方法：\n1. 将电流调至0\n2. 将探针移到±15mm位置\n3. 用右侧旋钮将偏移调至0")
            return
        self.exp_controller.next_stage()
    
    def on_sample_selected(self, sample_type: str):
        """样品选择回调"""
        try:
            # 更新按钮状态
            self.sampleMoldSteelBtn.setChecked(sample_type == 'mold_steel')
            self.samplePureIronBtn.setChecked(sample_type == 'pure_iron')
            
            # 通知控制器
            params = self.exp_controller.select_sample(sample_type)
            
            if params:
                # 获取预生成的剩磁值
                actual_remanence = self._sample_remanence.get(sample_type, 0.0)
                # 先设置样品类型以获取正确的B缩放因子
                if physics_model is not None:
                    physics_model.set_sample_type(sample_type)
                # 应用B缩放因子（纯铁需要缩放到800mT饱和值）
                B_scale_factor = 1.0
                if physics_model is not None:
                    hyst_model = physics_model.get_hysteresis_model()
                    if hyst_model:
                        B_scale_factor = hyst_model._B_scale_factor
                scaled_remanence = actual_remanence * B_scale_factor
                # 计算含环境偏移的实际显示值（与LCD一致）
                displayed_remanence = scaled_remanence + self.ambient_offset_mT
                
                # 更新参数显示
                self.sampleParamValues['sampleName'].setText(params.get('name', '--'))
                self.sampleParamValues['sampleType'].setText(params.get('type', '--'))
                self.sampleParamValues['sampleBs'].setText(f"{params.get('Bs_mT', '--')} mT")
                self.sampleParamValues['sampleHc'].setText(f"{params.get('Hc_Am', '--')} A/m")
                # 显示含环境偏移的剩磁值（与LCD显示一致）
                self.sampleParamValues['sampleBr'].setText(f"{displayed_remanence:.1f} mT (含误差)")
                self.sampleParamValues['sampleL'].setText(f"{params.get('l_bar_cm', '--')} cm")
                self.sampleParamValues['sampleLg'].setText(f"{params.get('l_gap_cm', '--')} cm")
                self.sampleParamValues['sampleN'].setText(f"{params.get('N', '--')} 匝")
                self.sampleParamValues['sampleS'].setText(f"{params.get('section_cm2', '--')} cm²")
                self.sampleParamValues['sampleDesc'].setText(params.get('description', '--'))
                
                # 应用样品参数到物理模型
                self._apply_sample_params(sample_type, params)
                
                self.statusbar.showMessage(f"已选择样品: {params.get('name', sample_type)}")
        except Exception as e:
            self.statusbar.showMessage(f"选择样品失败: {str(e)}")
    
    def _apply_sample_params(self, sample_type: str, params: dict):
        """将样品参数应用到物理模型"""
        try:
            # 使用预生成的剩磁值
            remanence = self._sample_remanence.get(sample_type, 0.0)
            
            if physics_model is not None:
                # 设置样品类型，更新B值缩放因子
                physics_model.set_sample_type(sample_type)
                
                hyst_model = physics_model.get_hysteresis_model()
                if hyst_model:
                    # 更新所有相关的剩磁变量
                    hyst_model._global_remanence = remanence
                    hyst_model._initial_remanence = remanence
                    hyst_model._B_prev = remanence
                    hyst_model._remanent_B = remanence
                    # 重置退磁状态以确保get_B_from_I使用正确的初始剩磁
                    hyst_model.reset_degauss_state()
            
            # 使用与update_displays完全相同的逻辑计算LCD值
            # 这样样品选择后和滑条移动后的显示值一致
            if physics_model is not None:
                # get_B_from_I返回: B_raw + ambient_offset
                measured_mT = physics_model.get_B_from_I(
                    0,  # I=0
                    self.probe_display_mm,
                    self.ambient_offset_mT,
                    apply_position_coupling=True
                )
            else:
                measured_mT = remanence + self.ambient_offset_mT
            
            self.last_displayed_mT = float(measured_mT)
            display_mT = measured_mT  # 与update_displays一致
            display_T = display_mT / 1000.0
            self.LCD_Tesla.display(self.format_tesla_display(display_T))
            
        except Exception:
            pass
    
    def on_exp_warning(self, msg: str):
        """实验警告"""
        try:
            self.statusbar.showMessage("警告: " + msg)
            QtWidgets.QMessageBox.warning(None, "警告", msg)
        except Exception:
            pass
    
    def on_exp_error(self, msg: str):
        """实验错误（需要退磁重来）"""
        try:
            self.statusbar.showMessage("错误: " + msg)
            reply = QtWidgets.QMessageBox.critical(
                None, "操作错误", 
                msg + "\n\n是否立即进入退磁阶段？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.exp_controller.set_stage(2)  # 进入退磁阶段
                self.data_manager.reset_experiment()
        except Exception:
            pass
    
    def on_start_degauss(self):
        """开始自动退磁 - 自动执行交变递减磁场过程"""
        try:
            # 如果正在手动记录，先停止
            if getattr(self, '_manual_degauss_recording', False):
                self._stop_manual_degauss_recording()
            
            self.exp_controller.start_degauss()
            self.data_manager.start_degauss()
            self.startDegaussBtn.setEnabled(False)
            self.startDegaussBtn.setText("退磁中...")
            self.manualDegaussBtn.setEnabled(False)
            
            # 清空曲线并开始实时绘制
            if self.plot_widget:
                self.plot_widget.clear_realtime()
            
            # 退磁参数初始化 - 根据样品类型调整
            # 电工纯铁是软磁材料，退磁更容易，需要更少的步骤
            sample_type = self.exp_controller._selected_sample or 'mold_steel'
            if sample_type == 'pure_iron':
                # 电工纯铁：软磁材料，退磁快
                self._degauss_max_I = 600.0
                self._degauss_decay_step = 150.0  # 每次减少更多
                self._degauss_max_steps = 12      # 更少的换向次数
                self._degauss_ramp_speed = 15.0   # 更快的变化速度
            else:
                # 模具钢：半硬磁材料，退磁慢
                self._degauss_max_I = 600.0
                self._degauss_decay_step = 100.0
                self._degauss_max_steps = 20
                self._degauss_ramp_speed = 12.0
            
            self._degauss_current_I = 0.0    # 当前电流绝对值
            self._degauss_polarity = 1       # 极性：1=正向, -1=负向
            self._degauss_step = 0           # 当前步骤（换向次数）
            self._degauss_phase = 'rise'     # 'rise'=0→峰值, 'fall'=峰值→0, 'switch'=换向
            
            # 重置物理模型状态（包括退磁专用状态）
            if physics_model is not None:
                try:
                    # 重置磁滞模型
                    hyst_model = physics_model.get_hysteresis_model()
                    if hyst_model:
                        hyst_model.reset_degauss_state()
                        # 记录初始剩磁点 (I=0, B=剩磁) - 使用缩放后的值保持一致
                        initial_B_raw = hyst_model._global_remanence
                        initial_B_raw = max(min(initial_B_raw, 0.0), -50.0)  # clip到基准范围
                        initial_B = initial_B_raw * hyst_model._B_scale_factor
                        self.data_manager.add_degauss_point(0.0, initial_B, 0.0)
                        # 更新LCD显示初始剩磁
                        self.last_displayed_mT = initial_B
                        self.LCD_Tesla.display(self.format_tesla_display(initial_B / 1000.0))
                except Exception:
                    pass
            
            # 启动退磁定时器（30ms更新一次，更平滑的曲线）
            self._degauss_timer = QtCore.QTimer()
            self._degauss_timer.timeout.connect(self._update_degauss)
            self._degauss_timer.start(30)
            
            self.statusbar.showMessage("自动退磁进行中... 交变递减磁场")
        except Exception:
            pass
    
    def on_manual_degauss_toggle(self):
        """切换手动退磁记录状态"""
        try:
            if self._manual_degauss_recording:
                # 停止记录
                self._stop_manual_degauss_recording()
            else:
                # 开始记录
                self._start_manual_degauss_recording()
        except Exception:
            pass
    
    def _start_manual_degauss_recording(self):
        """开始手动退磁记录"""
        try:
            self._manual_degauss_recording = True
            self.manualDegaussBtn.setText("停止记录")
            self.manualDegaussBtn.setChecked(True)
            self.startDegaussBtn.setEnabled(False)  # 禁用自动退磁
            
            # 清空之前的数据并开始新的记录
            self.data_manager.start_degauss()
            
            # 触发物理模型初始化初始剩磁（如果尚未初始化）
            # 通过调用一次退磁函数来初始化
            
            # 清空曲线
            if self.plot_widget:
                self.plot_widget.clear_realtime()
            
            # 初始化手动退磁追踪变量（获取当前电流值）
            current_I_signed = self.current_value if self.tesla_positive else -self.current_value
            self._manual_last_I = current_I_signed
            self._manual_direction = 0
            self._manual_peak_I_history = []
            self._manual_cycle_count = 0
            self._manual_current_amplitude = 600.0
            self._manual_point_count = 0
            self._manual_initial_remanence = None  # 记录初始剩磁
            
            # 重置物理模型退磁状态，确保从当前剩磁开始
            if physics_model is not None:
                try:
                    hyst_model = physics_model.get_hysteresis_model()
                    if hyst_model:
                        hyst_model.reset_degauss_state()
                        # 记录初始剩磁点 (I=0, B=剩磁) - 需要应用B缩放因子
                        initial_B_raw = hyst_model._global_remanence
                        B_scale_factor = hyst_model._B_scale_factor
                        initial_B = initial_B_raw * B_scale_factor
                        self._manual_initial_remanence = initial_B  # 保存缩放后的初始剩磁
                        self.data_manager.add_degauss_point(0.0, initial_B, 0.0)
                        # 更新LCD显示初始剩磁
                        self.last_displayed_mT = initial_B
                        self.LCD_Tesla.display(self.format_tesla_display(initial_B / 1000.0))
                except Exception:
                    pass
            
            # 启动定时器，定期记录当前值
            self._manual_degauss_timer = QtCore.QTimer()
            self._manual_degauss_timer.timeout.connect(self._record_manual_degauss_point)
            self._manual_degauss_timer.start(100)  # 100ms记录一次
            
            self.statusbar.showMessage("手动退磁记录中... 请按说明书操作：0→600→0，换向，0→500→0，... (当前幅度: 600.0 mA)")
        except Exception:
            pass
    
    def _stop_manual_degauss_recording(self):
        """停止手动退磁记录"""
        try:
            self._manual_degauss_recording = False
            self.manualDegaussBtn.setText("手动记录")
            self.manualDegaussBtn.setChecked(False)
            self.startDegaussBtn.setEnabled(True)  # 重新启用自动退磁
            
            # 停止定时器
            if self._manual_degauss_timer:
                self._manual_degauss_timer.stop()
                self._manual_degauss_timer = None
            
            # 显示最终结果
            final_B = self.last_displayed_mT
            # 保存退磁终点的B值供阶段3使用
            self._degauss_end_B = final_B
            
            # 检查是否在±10mT范围内算退磁成功
            DEGAUSS_SUCCESS_THRESHOLD = 10.0  # mT
            if abs(final_B) <= DEGAUSS_SUCCESS_THRESHOLD:
                # 退磁成功：调用reset_models标记已退磁
                if physics_model is not None:
                    try:
                        physics_model.reset_models(final_B)
                    except Exception:
                        pass
                self.statusbar.showMessage(f"手动退磁成功！B={final_B:.1f}mT（在±{DEGAUSS_SUCCESS_THRESHOLD:.0f}mT范围内）")
            else:
                # 退磁未完成
                self.statusbar.showMessage(f"手动退磁记录完成，但B={final_B:.1f}mT超出±{DEGAUSS_SUCCESS_THRESHOLD:.0f}mT范围，退磁未成功")
        except Exception:
            pass
    
    def _record_manual_degauss_point(self):
        """记录手动退磁过程中的数据点（改进版：支持换向检测和衰减）"""
        try:
            # 获取当前电流（带符号）
            I_signed = self.current_value if self.tesla_positive else -self.current_value
            
            # 初始化峰值跟踪
            if not hasattr(self, '_manual_tracked_peak'):
                self._manual_tracked_peak = I_signed
            
            # 检测电流变化方向（使用更小的阈值）
            dI = I_signed - self._manual_last_I
            new_direction = 0
            if dI > 1.0:  # 降低阈值到1mA
                new_direction = 1  # 上升
            elif dI < -1.0:
                new_direction = -1  # 下降
            
            # 更新峰值跟踪
            if self._manual_direction == 1:  # 上升中
                if I_signed > self._manual_tracked_peak:
                    self._manual_tracked_peak = I_signed
            elif self._manual_direction == -1:  # 下降中
                if I_signed < self._manual_tracked_peak:
                    self._manual_tracked_peak = I_signed
            
            # 换向检测：基于电流远离峰值的程度
            reversal_detected = False
            if self._manual_direction == 1 and new_direction == -1:
                # 从上升变为下降
                if abs(I_signed) < abs(self._manual_tracked_peak) - 10:  # 电流下降超过10mA
                    reversal_detected = True
                    peak_I = abs(self._manual_tracked_peak)
            elif self._manual_direction == -1 and new_direction == 1:
                # 从下降变为上升
                if abs(I_signed) < abs(self._manual_tracked_peak) - 10:
                    reversal_detected = True
                    peak_I = abs(self._manual_tracked_peak)
            
            if reversal_detected:
                self._manual_peak_I_history.append(peak_I)
                self._manual_cycle_count += 1
                
                # amplitude立即更新为当前峰值电流
                self._manual_current_amplitude = peak_I
                
                # 重置峰值跟踪
                self._manual_tracked_peak = I_signed
                
                self.statusbar.showMessage(
                    f"检测到换向 (第{self._manual_cycle_count}次) | 峰值电流: {peak_I:.1f} mA | 当前幅度: {self._manual_current_amplitude:.1f} mA"
                )
            
            # 更新方向
            if new_direction != 0:
                self._manual_direction = new_direction
            
            # 计数记录的点数
            self._manual_point_count += 1
            
            # 手动记录模式：使用退磁模式计算B值
            # 物理模型已经处理了初始路径的平滑过渡，不需要特殊处理
            if physics_model is not None:
                try:
                    # 使用退磁模式获取B值
                    B_mT = physics_model.get_B_from_I(
                        I_signed,
                        self.probe_display_mm,
                        self.ambient_offset_mT,
                        apply_position_coupling=False,
                        degauss_mode=True,
                        degauss_amplitude=self._manual_current_amplitude
                    )
                    # 更新LCD显示
                    self.last_displayed_mT = B_mT
                    display_T = B_mT / 1000.0
                    self.LCD_Tesla.display(self.format_tesla_display(display_T))
                    self.LCD_Current.display(self.format_current_display(self.current_value))
                except Exception:
                    # 回退到显示值
                    B_mT = self.last_displayed_mT
            else:
                B_mT = self.last_displayed_mT
            
            # 计算H值
            try:
                H_Am = physics_model.physical_I_to_H(abs(I_signed))
                if I_signed < 0:
                    H_Am = -H_Am
            except Exception:
                H_Am = I_signed * 10.0
            
            # 记录数据点
            self.data_manager.add_degauss_point(I_signed, B_mT, H_Am)
            
            # 更新曲线图
            if self.plot_widget:
                data = self.data_manager.get_degauss_curve()
                self.plot_widget.plot_degauss_curve(data)
            
            # 更新状态
            self._manual_last_I = I_signed
            
        except Exception as e:
            # 静默处理错误，避免干扰用户操作
            pass
    
    def on_clear_degauss(self):
        """清空退磁曲线"""
        try:
            # 停止任何正在进行的记录
            if getattr(self, '_manual_degauss_recording', False):
                self._stop_manual_degauss_recording()
            
            # 清空数据
            self.data_manager.clear_degauss_curve()
            
            # 清空曲线显示
            if self.plot_widget:
                self.plot_widget.clear_realtime()
                # 重新设置坐标轴
                if hasattr(self.plot_widget, 'pw'):
                    self.plot_widget.pw.clear()
                    pi = self.plot_widget.pw.getPlotItem()
                    if pi:
                        pi.setLabel('bottom', 'H (A/m)')
                        pi.setLabel('left', 'B (mT)')
            
            self.statusbar.showMessage("退磁曲线已清空")
        except Exception:
            pass
    
    def on_export_degauss_curve(self):
        """导出退磁曲线数据为CSV"""
        try:
            import csv
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                None, "导出退磁曲线", "", "CSV文件 (*.csv);;所有文件 (*)"
            )
            if not path:
                return
            
            curve_data = self.data_manager.get_degauss_curve()
            if not curve_data:
                self.statusbar.showMessage("没有退磁曲线数据可导出")
                return
            
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['I/mA', 'B/mT', 'H/(A/m)'])
                for pt in curve_data:
                    writer.writerow([pt.get('I', 0), pt.get('B', 0), pt.get('I', 0) * 5.0])
            
            self.statusbar.showMessage(f"退磁曲线已导出到 {path}")
        except Exception as e:
            self.statusbar.showMessage(f"导出失败: {str(e)}")
    
    def on_import_degauss_curve(self):
        """导入退磁曲线数据从CSV"""
        try:
            import csv
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                None, "导入退磁曲线", "", "CSV文件 (*.csv);;所有文件 (*)"
            )
            if not path:
                return
            
            # 清空现有数据
            self.data_manager.clear_degauss_curve()
            
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        I = float(row.get('I/mA', 0))
                        B = float(row.get('B/mT', 0))
                        H = float(row.get('H/(A/m)', I * 5.0))
                        self.data_manager.add_degauss_point(I, B, H)
                    except Exception:
                        continue
            
            # 刷新曲线显示
            self.refresh_plot_for_current_stage()
            
            curve_data = self.data_manager.get_degauss_curve()
            self.statusbar.showMessage(f"已导入 {len(curve_data)} 个数据点")
        except Exception as e:
            self.statusbar.showMessage(f"导入失败: {str(e)}")
    
    def _update_degauss(self):
        """
        更新退磁过程（按照说明书：0→峰值→0→换向）
        
        退磁原理：
        1. 电流从0上升到+峰值（上升支）
        2. 从+峰值下降到0（下降支）
        3. 换向，切换极性
        4. 从0上升到-峰值（上升支）
        5. 从-峰值下降到0（下降支）
        6. 换向并衰减幅度（600→500→400→...）
        7. 重复上述过程，直到幅度小于阈值
        
        B-H曲线应该呈嵌套的磁滞环，逐渐收敛到原点
        """
        try:
            # 根据阶段更新电流
            if self._degauss_phase == 'rise':
                # 上升阶段：0 → 峰值
                self._degauss_current_I += self._degauss_ramp_speed
                if self._degauss_current_I >= self._degauss_max_I:
                    self._degauss_current_I = self._degauss_max_I
                    self._degauss_phase = 'fall'
            
            elif self._degauss_phase == 'fall':
                # 下降阶段：峰值 → 0
                self._degauss_current_I -= self._degauss_ramp_speed
                if self._degauss_current_I <= 0:
                    self._degauss_current_I = 0
                    self._degauss_phase = 'switch'
            
            elif self._degauss_phase == 'switch':
                # 换向阶段：每次换向后都减少幅度
                self._degauss_polarity *= -1  # 切换极性
                self._degauss_step += 1
                
                # 每次换向后减少幅度（100mA以上每次减100mA，100mA以下每次减30mA）
                if self._degauss_max_I > 100.0:
                    self._degauss_decay_step = 100.0
                else:
                    self._degauss_decay_step = 30.0  # 小幅度时更精细的递减
                self._degauss_max_I -= self._degauss_decay_step
                
                # 检查是否完成（幅度小于10mA时停止）
                if self._degauss_max_I < 10.0 or self._degauss_step >= self._degauss_max_steps:
                    self._degauss_phase = 'done'
                else:
                    self._degauss_phase = 'rise'
            
            # 当前带符号的电流值
            I_signed = self._degauss_current_I * self._degauss_polarity
            
            # 更新UI显示的电流值
            self.current_value = abs(I_signed)
            self.tesla_positive = (I_signed >= 0)
            
            # 更新旋钮和方向按钮显示
            try:
                self.Knob_Current.blockSignals(True)
                self.Knob_Current.setValue(int(round(self.current_value * 10)))
                self.Knob_Current.blockSignals(False)
                self.DirectionToggle.setChecked(self.tesla_positive)
                self.DirectionToggle.setText("↑" if self.tesla_positive else "↓")
            except Exception:
                pass
            
            # 使用退磁模式计算B值（嵌套磁滞回线）
            if physics_model is not None:
                try:
                    B_mT = physics_model.get_B_from_I(
                        I_signed,
                        self.probe_display_mm,
                        self.ambient_offset_mT,
                        apply_position_coupling=False,
                        degauss_mode=True,
                        degauss_amplitude=self._degauss_max_I
                    )
                except Exception:
                    amplitude_ratio = self._degauss_max_I / 600.0
                    B_mT = I_signed * 0.5 * amplitude_ratio + self.ambient_offset_mT
            else:
                amplitude_ratio = self._degauss_max_I / 600.0
                B_mT = I_signed * 0.5 * amplitude_ratio + self.ambient_offset_mT
            
            # 更新LCD显示
            self.last_displayed_mT = B_mT
            display_T = B_mT / 1000.0
            self.LCD_Tesla.display(self.format_tesla_display(display_T))
            self.LCD_Current.display(self.format_current_display(self.current_value))
            
            # 计算H值 (A/m)
            try:
                H_Am = physics_model.physical_I_to_H(abs(I_signed))
                if I_signed < 0:
                    H_Am = -H_Am
            except Exception:
                H_Am = I_signed * 10.0  # 简化：H ≈ 10 * I
            
            # 保存最后的B值（用于退磁结束时）
            self._degauss_last_B = B_mT
            
            # 记录数据点
            self.data_manager.add_degauss_point(I_signed, B_mT, H_Am)
            self.exp_controller.update_degauss(B_mT)
            
            # 更新曲线图
            if self.plot_widget:
                data = self.data_manager.get_degauss_curve()
                self.plot_widget.plot_degauss_curve(data)
            
            # 更新状态栏
            self.statusbar.showMessage(
                f"退磁中... 第{self._degauss_step}次换向 | I={I_signed:.1f}mA | B={B_mT:.1f}mT | 幅度={self._degauss_max_I:.1f}mA"
            )
            
            # 检查是否完成
            if self._degauss_phase == 'done':
                self._finish_degauss()
                        
        except Exception as e:
            # 出错时停止
            try:
                self._degauss_timer.stop()
                self.startDegaussBtn.setEnabled(True)
                self.startDegaussBtn.setText("开始退磁")
                self.statusbar.showMessage(f"退磁出错: {e}")
            except Exception:
                pass
    
    def _finish_degauss(self):
        """完成自动退磁过程"""
        try:
            # 电流归零
            self.current_value = 0.0
            self._degauss_current_I = 0.0
            try:
                self.Knob_Current.blockSignals(True)
                self.Knob_Current.setValue(0)
                self.Knob_Current.blockSignals(False)
            except Exception:
                pass
            
            # 退磁完成后使用实际的最终B值（不强制归零）
            # 物理模型会返回退磁过程的实际终点B值
            final_B = getattr(self, '_degauss_last_B', self.ambient_offset_mT)
            self.last_displayed_mT = final_B
            # 保存退磁终点的B值供阶段3使用
            self._degauss_end_B = final_B
            display_T = final_B / 1000.0
            self.LCD_Tesla.display(self.format_tesla_display(display_T))
            self.LCD_Current.display(self.format_current_display(0.0))
            
            # 记录最后一个点（原点）
            self.data_manager.add_degauss_point(0.0, final_B, 0.0)
            if self.plot_widget:
                data = self.data_manager.get_degauss_curve()
                self.plot_widget.plot_degauss_curve(data)
            
            # 停止定时器
            self._degauss_timer.stop()
            
            # 恢复按钮状态
            self.startDegaussBtn.setEnabled(True)
            self.startDegaussBtn.setText("自动退磁")
            self.manualDegaussBtn.setEnabled(True)
            
            self.statusbar.showMessage(f"自动退磁完成！共{self._degauss_step}次换向，B≈{final_B:.1f}mT（已趋近原点）")
            
            # 重置物理模型为退磁后状态，传入退磁终点的B值
            if physics_model is not None:
                try:
                    physics_model.reset_models(final_B)
                except Exception:
                    pass
        except Exception:
            pass
    
    def on_tab_changed(self, index: int):
        """Tab切换回调，自动刷新曲线图"""
        try:
            # index 1 是曲线图Tab
            if index == 1:
                self.refresh_plot_for_current_stage()
        except Exception:
            pass
    
    def refresh_plot_for_current_stage(self):
        """根据当前实验阶段刷新曲线图"""
        try:
            stage = self.exp_controller.current_stage
            
            if stage == 1:
                # 阶段1: B-X曲线（使用表A数据）
                rows = self.data_manager.get_table('A')
                if rows:
                    self.plot_widget.update_table_data('A', rows)
                else:
                    # 清空曲线
                    if hasattr(self.plot_widget, 'pw'):
                        self.plot_widget.pw.clear()
                        pi = self.plot_widget.pw.getPlotItem()
                        if pi:
                            pi.setLabel('bottom', 'X (mm)')
                            pi.setLabel('left', 'B (mT)')
                            
            elif stage == 2:
                # 阶段2: 退磁曲线 B-H
                data = self.data_manager.get_degauss_curve()
                if data:
                    self.plot_widget.plot_degauss_curve(data)
                else:
                    if hasattr(self.plot_widget, 'pw'):
                        self.plot_widget.pw.clear()
                        pi = self.plot_widget.pw.getPlotItem()
                        if pi:
                            pi.setLabel('bottom', 'H (A/m)')
                            pi.setLabel('left', 'B (mT)')
                            
            elif stage == 3:
                # 阶段3: 磁滞回线 B-H（使用表B数据）
                rows = self.data_manager.get_table('B')
                if rows:
                    self.plot_widget.update_table_data('B', rows)
                else:
                    if hasattr(self.plot_widget, 'pw'):
                        self.plot_widget.pw.clear()
                        pi = self.plot_widget.pw.getPlotItem()
                        if pi:
                            pi.setLabel('bottom', 'H (A/m)')
                            pi.setLabel('left', 'B (mT)')
        except Exception:
            pass
    
    def on_record_current_with_check(self):
        """带单调性检查的记录（用于初始磁化曲线阶段）"""
        try:
            stage = self.exp_controller.current_stage
            I_mA = float(self.current_value)
            
            # 阶段3需要检查单调性
            if stage == 3:
                if not self.exp_controller.check_monotonic(I_mA):
                    return  # 违反单调性，不记录
            
            # 正常记录
            self.on_record_current()
        except Exception:
            pass
    
    def on_clear_hysteresis_data(self):
        """阶段3：清空磁滞回线数据并重置模型到退磁后状态"""
        try:
            reply = QtWidgets.QMessageBox.question(
                None, "确认清空",
                "确定要清空所有磁滞回线数据并重置模型吗？\n（将恢复到退磁刚完成的状态）",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                # 清空数据表
                self.data_manager.clear_table('B')
                self.refresh_data_table('B')
                self.refresh_plot_for_current_stage()
                
                # 重置磁滞回线模型到退磁后状态
                if physics_model is not None:
                    try:
                        # 使用之前退磁终点的B值，如果没有则使用0
                        degauss_end_B = getattr(self, '_degauss_end_B', 0.0)
                        physics_model.reset_models(degauss_end_B)
                        self.statusbar.showMessage(f"磁滞回线数据已清空，模型已重置（B偏移={degauss_end_B:.1f}mT）")
                    except Exception:
                        self.statusbar.showMessage("磁滞回线数据已清空")
                else:
                    self.statusbar.showMessage("磁滞回线数据已清空")
        except Exception:
            pass