#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FD-MGS-A 光栅图像显示系统启动脚本
Windows中推荐使用: py run.py
Linux/Mac中使用: python3 run.py
也支持: python run.py
"""

import sys
import os

def main():
    """主启动函数"""
    try:
        print("=== 开始启动过程 ===")
        # 确保当前目录在Python路径中
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        print("=== 导入模块 ===")
        # 导入并运行主程序
        from FD_MGS_A_Main import MainWindow
        from PyQt5.QtWidgets import QApplication
        
        print("=== 创建QApplication ===")
        # 创建应用程序
        app = QApplication(sys.argv)
        
        print("正在启动 FD-MGS-A 光谱分析系统...")
        print("版本: v2.1")
        print("功能特性:")
        print("✓ 3648像素光谱数据采集")
        print("✓ 实时光谱图显示和缩放功能")
        print("✓ 光谱标定功能（支持6种标准峰）")
        print("✓ 积分时间设置（15种选项）")
        print("✓ 数据保存/加载和标定导出/导入")
        print("✓ 连续/单次采集模式")
        print("✓ 拖拽缩放和自动Y轴缩放")
        print("=" * 50)
        
        try:
            print("=== 创建MainWindow ===")
            window = MainWindow()
            print("=== 显示窗口 ===")
            window.show()
            
            # 显示欢迎信息
            from PyQt5.QtCore import QTimer
            def show_welcome():
                if hasattr(window, 'ui') and hasattr(window.ui, 'statusbar'):
                    window.ui.statusbar.showMessage("FD-MGS-A v2.1 已就绪 - 请连接串口或点击'显示演示'查看示例", 5000)
            
            QTimer.singleShot(1000, show_welcome)
            
            print("=== 进入主循环 ===")
            sys.exit(app.exec_())

        except Exception as e:
            print(f"程序启动失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有依赖包已正确安装")
        print("可以运行: pip install -r requirements.txt")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 