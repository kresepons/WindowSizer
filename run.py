#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WindowSizer 启动脚本
用于启动重构后的 WindowSizer 应用程序
"""

import sys
import os

# 添加当前目录到 Python 路径，以便导入自定义模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入并运行主程序
from main import WindowSizer
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    # 确保resources文件夹存在
    if not os.path.exists("resources"):
        os.makedirs("resources")
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭所有窗口时不退出程序
    
    # 设置应用程序图标
    from PyQt5.QtGui import QIcon
    app_icon_path = "resources/app_icon.png"
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))
    
    window = WindowSizer()
    window.show()
    
    sys.exit(app.exec_())