import sys
import os
import win32gui
import win32con
import win32api
import win32process
import psutil
import time
import subprocess
import json
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox, 
                            QGroupBox, QGridLayout, QMenu, QAction, QSystemTrayIcon, 
                            QTabWidget, QFileDialog, QFrame, QStyle, 
                            QRadioButton, QButtonGroup, QListWidgetItem, QShortcut)
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QCursor, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QSettings, QPoint, QSize, QRect

# 导入自定义模块
from ui import UIManager
from window_manager import WindowManager
from config_manager import ConfigManager


def is_admin():
    """检查当前进程是否以管理员权限运行"""
    import ctypes
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def get_base_dir():
    """获取程序所在目录（支持打包后的exe环境）"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        return os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        return os.path.dirname(os.path.abspath(__file__))


class WindowSizer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 初始化变量
        self.current_window = None
        self.double_click_apply = False  # 双击图标一键应用开关状态
        self.auto_apply_config = False  # 自动应用配置开关状态
        self.close_behavior = "minimize"  # 默认关闭到最小化
        
        # 初始化管理器
        self.window_manager = WindowManager()
        self.config_manager = ConfigManager()
        self.ui_manager = UIManager(self)
        
        # 加载设置
        self.load_settings()
        
        # 初始化UI
        self.setWindowTitle("WindowSizer - 窗口大小调整工具")
        self.setMinimumWidth(400)  # 设置最小宽度
        self.setMaximumWidth(800)  # 设置最大宽度
        self.resize(400, 600)  # 设置初始尺寸
        self.setMinimumHeight(600)
        
        # 设置窗口图标
        base_dir = get_base_dir()
        icon_path = os.path.join(base_dir, "resources", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 加载配置
        self.load_config_list()
        
        # 启动窗口状态监测
        self.start_window_monitor()
        
        # 延迟检查管理员权限（等待窗口显示后）
        QTimer.singleShot(1000, self.check_admin_permission)
    
    def on_tray_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            # 检查是否启用了双击图标一键应用功能
            if self.double_click_apply:
                # 应用所有配置
                self.apply_all_configs()
                # 显示托盘通知
                self.ui_manager.tray_icon.showMessage(
                    "WindowSizer",
                    "正在应用所有配置...",
                    QSystemTrayIcon.Information,
                    2000
                )
            else:
                # 切换窗口可见性
                self.toggle_window_visibility()
    
    def toggle_window_visibility(self):
        """切换窗口可见性"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def check_admin_permission(self):
        """检查管理员权限"""
        if not is_admin():
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.information(
                self,
                "权限提示",
                "WindowSizer 未以管理员权限运行。\n\n"
                "某些以管理员权限运行的程序窗口可能无法调整。\n\n"
                "如需管理所有窗口，请右键点击 WindowSizer 选择：\n"
                "'以管理员身份运行'",
                QMessageBox.Ok
            )
    
    def refresh_window_list(self):
        """刷新窗口列表"""
        # 清空当前列表
        self.ui_manager.window_list.clear()
        
        # 获取所有窗口
        windows = self.window_manager.get_window_list()
        
        # 添加到列表
        for window in windows:
            item = QListWidgetItem(window["title"])
            item.setData(Qt.UserRole, window)
            
            # 设置图标
            if window["icon"] and not window["icon"].isNull():
                item.setIcon(window["icon"])
            
            self.ui_manager.window_list.addItem(item)
        

    
    def toggle_window_list(self):
        """切换窗口列表面板的显示/隐藏"""
        if self.ui_manager.right_panel_visible:
            self.ui_manager.toggle_right_panel()
            self.ui_manager.add_config_btn.setText("新增配置")
            # 返回配置时窗口宽度调整为400像素
            self.ui_manager.animate_window_width(400)
        else:
            # 新增配置时窗口宽度调整为800像素
            self.ui_manager.animate_window_width(800)
            self.ui_manager.toggle_right_panel()
            self.ui_manager.add_config_btn.setText("返回配置")
            # 刷新窗口列表
            self.refresh_window_list()
    
    def on_window_selected(self, item):
        """处理窗口选择事件"""
        window = item.data(Qt.UserRole)
        if window:
            self.current_window = window
            
            # 更新窗口信息显示
            self.ui_manager.title_label.setText(window["title"])
            self.ui_manager.process_label.setText(window["process_name"])
            self.ui_manager.pid_label.setText(str(window["pid"]))
            self.ui_manager.class_label.setText(window["class_name"])
            
            # 更新位置和尺寸
            rect = window["rect"]
            self.ui_manager.x_spin.setValue(rect[0])
            self.ui_manager.y_spin.setValue(rect[1])
            self.ui_manager.width_spin.setValue(rect[2] - rect[0])
            self.ui_manager.height_spin.setValue(rect[3] - rect[1])
            
            # 检查是否已有配置
            config = self.config_manager.get_config_by_window_info(window["title"], window["process_name"])
    
    
    def save_config(self):
        """保存当前窗口配置"""
        if not self.current_window:
            return
        
        # 获取配置信息
        config = {
            "title": self.current_window["title"],
            "process": self.current_window["process_name"],
            "x": self.ui_manager.x_spin.value(),
            "y": self.ui_manager.y_spin.value(),
            "width": self.ui_manager.width_spin.value(),
            "height": self.ui_manager.height_spin.value()
        }
        
        # 验证配置
        is_valid, message = self.config_manager.validate_config(config)
        if not is_valid:
            return
        
        # 检查是否已存在相同的配置
        existing_config = self.config_manager.get_config_by_window_info(config["title"], config["process"])
        if existing_config:
            # 更新现有配置：保留custom_name、enabled、icon_file等字段
            index = self.config_manager.configs.index(existing_config)
            # 保留原有的自定义名称、激活状态和图标文件
            if "custom_name" in existing_config:
                config["custom_name"] = existing_config["custom_name"]
            if "enabled" in existing_config:
                config["enabled"] = existing_config["enabled"]
            if "icon_file" in existing_config:
                config["icon_file"] = existing_config["icon_file"]
            if "created_at" in existing_config:
                config["created_at"] = existing_config["created_at"]
            
            if self.config_manager.update_config(index, config):
                self.load_config_list()
        else:
            # 添加新配置，传递窗口图标和类名
            icon = self.current_window.get("icon", None)
            class_name = self.current_window.get("class_name", None)
            success, message = self.config_manager.add_config(config, icon, class_name)
            if success:
                self.load_config_list()
    def apply_config(self):
        """应用当前配置到窗口"""
        if not self.current_window:
            return
        
        # 获取当前配置
        config = {
            "title": self.current_window["title"],
            "process": self.current_window["process_name"],
            "x": self.ui_manager.x_spin.value(),
            "y": self.ui_manager.y_spin.value(),
            "width": self.ui_manager.width_spin.value(),
            "height": self.ui_manager.height_spin.value()
        }
        
        # 应用配置
        success, error_msg = self.window_manager.resize_window(
            self.current_window["hwnd"], 
            config["x"], config["y"], 
            config["width"], config["height"]
        )
        
        if not success:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "配置应用失败",
                f"无法应用配置到窗口：\n\n{error_msg}\n\n"
                f"窗口：{config['title']}\n"
                f"进程：{config['process']}"
            )
    def delete_config(self):
        """删除当前选中的配置"""
        current_item = self.ui_manager.config_list.currentItem()
        if not current_item:
            return
        
        # 获取配置索引
        config_index = current_item.data(Qt.UserRole)
        if config_index is None or config_index < 0 or config_index >= len(self.config_manager.configs):
            return
        
        # 直接删除配置
        if self.config_manager.delete_config(config_index):
            self.load_config_list()
            
            # 清空配置详情
            self.ui_manager.title_label.setText("-")
            self.ui_manager.process_label.setText("-")
            self.ui_manager.pid_label.setText("-")
            self.ui_manager.class_label.setText("-")
            self.ui_manager.x_spin.setValue(0)
            self.ui_manager.y_spin.setValue(0)
            self.ui_manager.width_spin.setValue(800)
            self.ui_manager.height_spin.setValue(600)

    
    def apply_all_configs(self):
        """应用所有配置"""
        configs = self.config_manager.get_all_configs()
        if not configs:
            return
        
        # 在后台线程中应用所有配置
        threading.Thread(target=self._apply_all_configs, args=(configs,), daemon=True).start()

    
    def auto_apply_configs(self):
        """自动应用配置到匹配的窗口"""
        configs = self.config_manager.get_all_configs()
        if not configs:
            return
        
        # 获取当前所有窗口
        windows = self.window_manager.get_window_list()
        
        for config in configs:
            # 跳过未激活的配置
            if not config.get("enabled", True):
                continue
                
            try:
                # 查找匹配的窗口
                for window in windows:
                    if (window["title"] == config["title"] and 
                        window["process_name"] == config["process"]):
                        # 检查窗口是否已经应用了正确的配置
                        current_rect = self.window_manager.get_window_rect(window["hwnd"])
                        if current_rect:
                            current_width = current_rect[2] - current_rect[0]
                            current_height = current_rect[3] - current_rect[1]
                            
                            # 如果配置与当前窗口状态不同，则应用配置
                            if (current_rect[0] != config["x"] or 
                                current_rect[1] != config["y"] or 
                                current_width != config["width"] or 
                                current_height != config["height"]):
                                # 应用配置（忽略错误，自动应用时不显示弹窗）
                                self.window_manager.resize_window(
                                    window["hwnd"], 
                                    config["x"], config["y"], 
                                    config["width"], config["height"]
                                )
                
                # 添加延迟以避免同时操作多个窗口导致问题
                time.sleep(0.05)
            except Exception:
                pass
    
    def _apply_all_configs(self, configs):
        """在后台线程中应用所有配置"""
        success_count = 0
        fail_count = 0
        
        for config in configs:
            # 跳过未激活的配置
            if not config.get("enabled", True):
                continue
                
            try:
                # 查找匹配的窗口
                windows = self.window_manager.get_window_list()
                matched_window = None
                
                for window in windows:
                    if (window["title"] == config["title"] and 
                        window["process_name"] == config["process"]):
                        matched_window = window
                        break
                
                if matched_window:
                    # 应用配置
                    success, error_msg = self.window_manager.resize_window(
                        matched_window["hwnd"], 
                        config["x"], config["y"], 
                        config["width"], config["height"]
                    )
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
                else:
                    fail_count += 1
                
                # 添加延迟以避免同时操作多个窗口导致问题
                time.sleep(0.1)
            except Exception:
                fail_count += 1
        
        # 在主线程中显示结果

    
    def load_config_list(self):
        """加载配置列表"""
        # 获取所有配置
        configs = self.config_manager.get_all_configs()
        
        # 清空列表
        self.ui_manager.config_list.clear()
        
        # 添加到列表
        for i, config in enumerate(configs):
            # 创建列表项
            item = QListWidgetItem()
            item.setData(Qt.UserRole, i)
            
            # 创建自定义widget
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(2, 2, 2, 2)
            item_layout.setSpacing(5)
            
            # 激活复选框（最左边）
            enabled_checkbox = QCheckBox()
            enabled_checkbox.setChecked(config.get("enabled", True))
            enabled_checkbox.stateChanged.connect(lambda state, idx=i: self.on_config_enabled_changed(idx, state))
            enabled_checkbox.setFixedWidth(20)
            item_layout.addWidget(enabled_checkbox)
            
            # 图标
            icon_label = QLabel()
            icon_label.setFixedSize(24, 24)
            
            # 尝试从保存的文件加载图标（支持多级回退匹配）
            icon_loaded = False
            if "icon_file" in config:
                # 使用配置中保存的图标文件名，同时提供进程名、类名、标题用于回退
                icon = self.config_manager.load_icon(
                    icon_filename=config["icon_file"],
                    process_name=config["process"],
                    class_name=config.get("class_name"),
                    window_title=config["title"]
                )
                if icon and not icon.isNull():
                    icon_label.setPixmap(icon.pixmap(24, 24))
                    icon_loaded = True
            
            # 如果没有保存的图标，尝试从当前运行的窗口获取
            if not icon_loaded:
                windows = self.window_manager.get_window_list()
                for window in windows:
                    if (window["title"] == config["title"] and 
                        window["process_name"] == config["process"]):
                        if window["icon"] and not window["icon"].isNull():
                            icon_label.setPixmap(window["icon"].pixmap(24, 24))
                        break
            
            item_layout.addWidget(icon_label)
            
            # 配置名称标签（优先使用自定义名称）
            display_name = config.get("custom_name", f"{config['title']} - {config['process']}")
            name_label = QLabel(display_name)
            name_label.setStyleSheet("QLabel { border: none; background: transparent; }")
            # 不设置伸缩因子，让标签自然占据空间
            item_layout.addWidget(name_label)
            
            # 添加伸缩项，将重命名按钮推到最右边
            item_layout.addStretch()
            
            # 重命名按钮（最右边，固定位置）
            rename_btn = QPushButton("重命名")
            rename_btn.setFixedSize(55, 24)  # 调整宽度和高度
            rename_btn.setStyleSheet("QPushButton { font-size: 9pt; padding: 2px 4px; }")  # 缩小字号并调整内边距
            rename_btn.clicked.connect(lambda checked, idx=i: self.rename_config(idx))
            item_layout.addWidget(rename_btn)
            
            # 设置项目高度
            item.setSizeHint(item_widget.sizeHint())
            
            self.ui_manager.config_list.addItem(item)
            self.ui_manager.config_list.setItemWidget(item, item_widget)
    
    def on_config_selected(self, item):
        """处理配置选择事件"""
        # 获取配置索引
        config_index = item.data(Qt.UserRole)
        if config_index is None or config_index < 0 or config_index >= len(self.config_manager.configs):
            return
        
        # 获取配置
        config = self.config_manager.get_config_by_index(config_index)
        if not config:
            return
        
        # 更新配置详情
        self.ui_manager.title_label.setText(config["title"])
        self.ui_manager.process_label.setText(config["process"])
        self.ui_manager.pid_label.setText("-")
        self.ui_manager.class_label.setText(config.get("class_name", "-"))
        
        # 更新位置和尺寸
        self.ui_manager.x_spin.setValue(config["x"])
        self.ui_manager.y_spin.setValue(config["y"])
        self.ui_manager.width_spin.setValue(config["width"])
        self.ui_manager.height_spin.setValue(config["height"])
        
        # 查找匹配的窗口
        windows = self.window_manager.get_window_list()
        matched_window = None
        
        for window in windows:
            if (window["title"] == config["title"] and 
                window["process_name"] == config["process"]):
                matched_window = window
                break
        
        if matched_window:
            self.current_window = matched_window
            self.ui_manager.pid_label.setText(str(matched_window["pid"]))
            self.ui_manager.class_label.setText(matched_window["class_name"])

        else:
            self.current_window = None

    
    def on_config_enabled_changed(self, config_index, state):
        """处理配置激活状态变化"""
        if 0 <= config_index < len(self.config_manager.configs):
            config = self.config_manager.configs[config_index]
            config["enabled"] = (state == Qt.Checked)
            self.config_manager.save_configs()
    
    def rename_config(self, config_index):
        """重命名配置"""
        if config_index < 0 or config_index >= len(self.config_manager.configs):
            return
        
        from PyQt5.QtWidgets import QInputDialog
        config = self.config_manager.configs[config_index]
        
        # 弹出对话框让用户输入新名称
        new_name, ok = QInputDialog.getText(
            self, 
            "重命名配置", 
            "请输入新名称:",
            text=config.get("custom_name", config["title"])
        )
        
        if ok and new_name.strip():
            old_icon_file = config.get("icon_file")
            config["custom_name"] = new_name.strip()
            
            # 如果有图标文件，需要重新命名图标文件
            if old_icon_file:
                old_icon_path = os.path.join(self.config_manager.icons_folder, old_icon_file)
                if os.path.exists(old_icon_path):
                    # 生成新的图标文件名
                    safe_name = self.config_manager.sanitize_filename(new_name.strip())
                    new_icon_filename = f"{safe_name}.png"
                    new_icon_path = os.path.join(self.config_manager.icons_folder, new_icon_filename)
                    
                    # 重命名图标文件
                    try:
                        if old_icon_path != new_icon_path:
                            # 如果新文件已存在，先删除
                            if os.path.exists(new_icon_path):
                                os.remove(new_icon_path)
                            os.rename(old_icon_path, new_icon_path)
                            config["icon_file"] = new_icon_filename
                    except Exception:
                        pass  # 如果重命名失败，保留原图标文件名
            
            self.config_manager.save_configs()
            self.load_config_list()

    
    def get_executable_path(self):
        """获取可执行文件的完整路径
        
        Returns:
            str: 可执行文件的绝对路径
        """
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            return os.path.abspath(sys.executable)
        else:
            # 如果是开发环境，返回python.exe和main.py的组合
            # 注意：开发环境下不应该启用开机自启动，但为了测试目的，这里返回主脚本路径
            return os.path.abspath(sys.argv[0])
    
    def is_startup_enabled(self):
        """检查是否已启用开机自启动"""
        try:
            # 检查注册表
            key = win32api.RegOpenKey(
                win32con.HKEY_CURRENT_USER, 
                "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 
                0, win32con.KEY_READ
            )
            
            try:
                value, _ = win32api.RegQueryValueEx(key, "WindowSizer")
                win32api.RegCloseKey(key)
                # 只检查注册表项是否存在，不需要精确匹配路径
                # 因为路径可能包含双引号和参数
                return bool(value)
            except:
                win32api.RegCloseKey(key)
                return False
        except:
            return False
    
    def toggle_startup(self, state):
        """切换开机自启动状态"""
        enabled = state == Qt.Checked
        
        try:
            # 打开注册表
            key = win32api.RegOpenKey(
                win32con.HKEY_CURRENT_USER, 
                "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 
                0, win32con.KEY_SET_VALUE
            )
            
            if enabled:
                # 获取可执行文件路径
                exe_path = self.get_executable_path()
                
                # 检查是否为开发环境
                if not getattr(sys, 'frozen', False):
                    # 开发环境下的警告
                    from PyQt5.QtWidgets import QMessageBox
                    reply = QMessageBox.warning(
                        self,
                        "开发环境警告",
                        "检测到您在开发环境下运行 WindowSizer。\n\n"
                        "开机自启动功能仅适用于打包后的 exe 程序。\n\n"
                        "是否仍要继续设置？（仅用于测试）",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        # 用户取消，恢复复选框状态
                        self.ui_manager.startup_checkbox.setChecked(False)
                        win32api.RegCloseKey(key)
                        return
                
                # 添加到启动项
                # 如果是exe，直接使用exe路径
                # 如果是开发环境，使用python.exe + 脚本路径
                if getattr(sys, 'frozen', False):
                    startup_cmd = f'"{exe_path}"'
                else:
                    startup_cmd = f'"{sys.executable}" "{exe_path}"'
                
                win32api.RegSetValueEx(
                    key, "WindowSizer", 0, win32con.REG_SZ, startup_cmd
                )
                
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "设置成功",
                    f"已启用开机自启动。\n\n"
                    f"启动命令：{startup_cmd}"
                )
            else:
                # 从启动项移除
                try:
                    win32api.RegDeleteValue(key, "WindowSizer")
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self,
                        "设置成功",
                        "已禁用开机自启动。"
                    )
                except:
                    # 注册表项不存在，也认为成功
                    pass
            
            win32api.RegCloseKey(key)
        except Exception as e:
            # 显示错误信息
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "设置失败",
                f"无法设置开机自启动：\n\n{str(e)}\n\n"
                f"请检查是否有权限修改注册表。"
            )
            # 恢复复选框状态
            self.ui_manager.startup_checkbox.setChecked(self.is_startup_enabled())

    
    def import_configs(self):
        """导入配置"""
        success, message = self.config_manager.import_configs()
        if success:
            self.load_config_list()
    def export_configs(self):
        """导出配置"""
        success, message = self.config_manager.export_configs()
        if success:
            pass
    def load_settings(self):
        """加载所有设置"""
        settings = QSettings("WindowSizer", "Settings")
        
        # 加载关闭行为设置
        close_behavior_value = settings.value("close_behavior", "minimize")
        # 处理旧版本保存的数字值
        if isinstance(close_behavior_value, int):
            self.close_behavior = "minimize" if close_behavior_value == 0 else "exit"
        else:
            self.close_behavior = close_behavior_value
        
        # 加载双击图标一键应用设置
        self.double_click_apply = settings.value("double_click_apply", False, type=bool)
        
        # 加载自动应用配置设置
        self.auto_apply_config = settings.value("auto_apply_config", False, type=bool)
        
        # 更新UI
        self.update_settings_ui()
    
    def save_settings(self):
        """保存所有设置"""
        settings = QSettings("WindowSizer", "Settings")
        
        # 保存关闭行为设置为字符串
        settings.setValue("close_behavior", self.close_behavior)
        
        # 保存双击图标一键应用设置
        settings.setValue("double_click_apply", self.double_click_apply)
        
        # 保存自动应用配置设置
        settings.setValue("auto_apply_config", self.auto_apply_config)
    
    def update_settings_ui(self):
        """更新设置界面UI"""
        # 更新关闭行为设置
        if self.close_behavior == "minimize":
            self.ui_manager.minimize_on_close_radio.setChecked(True)
        else:
            self.ui_manager.exit_on_close_radio.setChecked(True)
        
        # 更新双击图标一键应用开关
        self.ui_manager.double_click_apply_checkbox.setChecked(self.double_click_apply)
        
        # 更新自动应用配置开关
        self.ui_manager.auto_apply_checkbox.setChecked(self.auto_apply_config)
    
    def save_close_behavior_setting(self):
        """保存关闭行为设置"""
        # 获取当前选中的按钮
        selected_button = self.ui_manager.close_behavior_group.checkedButton()
        if selected_button:
            if selected_button == self.ui_manager.minimize_on_close_radio:
                self.close_behavior = "minimize"
            else:
                self.close_behavior = "exit"
            
            # 保存所有设置
            self.save_settings()
    
    def on_double_click_apply_changed(self, state):
        """处理双击图标一键应用开关变化"""
        self.double_click_apply = state == Qt.Checked
        self.save_settings()
    
    def on_auto_apply_changed(self, state):
        """处理自动应用配置开关变化"""
        self.auto_apply_config = state == Qt.Checked
        self.save_settings()
        
        # 如果开启自动应用，启动监测；否则停止
        if self.auto_apply_config:
            # 启动自动应用逻辑
            pass
        else:
            # 停止自动应用逻辑
            pass
    def quit_program(self):
        """退出程序"""
        QApplication.quit()
    
    def start_window_monitor(self):
        """启动窗口状态监测"""
        self.window_monitor_timer = QTimer(self)
        self.window_monitor_timer.timeout.connect(self.check_window_status)
        self.window_monitor_timer.start(5000)  # 每5秒检查一次
    
    def check_window_status(self):
        """检查窗口状态，实现自动应用配置功能"""
        # 检查当前窗口是否仍然有效
        if self.current_window and not self.window_manager.is_window_valid(self.current_window["hwnd"]):

            self.current_window = None
            return
        
        # 如果启用了自动应用配置，检查所有配置的窗口
        if self.auto_apply_config:
            self.auto_apply_configs()
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        if self.close_behavior == "minimize":
            # 最小化到系统托盘
            event.ignore()
            self.hide()
        else:
            # 直接退出，确保完全终止所有进程
            event.accept()
            QApplication.quit()


if __name__ == "__main__":
    # 确保resources文件夹存在
    if not os.path.exists("resources"):
        os.makedirs("resources")
    
    # 检查进程唯一性
    import tempfile
    import atexit
    
    # 创建一个锁文件来防止多个实例同时运行
    lock_file_path = os.path.join(tempfile.gettempdir(), "WindowSizer.lock")
    lock_file = None
    
    try:
        # 尝试创建锁文件
        if os.path.exists(lock_file_path):
            # 如果锁文件已存在，检查是否为失效锁
            try:
                # 尝试读取锁文件中的PID
                with open(lock_file_path, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # 检查进程是否还在运行
                if psutil.pid_exists(old_pid):
                    try:
                        process = psutil.Process(old_pid)
                        # 检查是否为同一程序
                        if "WindowSizer" in process.name() or "python" in process.name().lower():
                            sys.exit(0)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # 进程不存在或无权限访问，删除失效锁
                        os.remove(lock_file_path)
            except:
                # 锁文件损坏，删除它
                try:
                    os.remove(lock_file_path)
                except:
                    pass
        
        # 创建新的锁文件
        lock_file = open(lock_file_path, 'w')
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        
        # 注册退出时删除锁文件
        def cleanup_lock():
            try:
                if lock_file:
                    lock_file.close()
                if os.path.exists(lock_file_path):
                    os.remove(lock_file_path)
            except:
                pass
        
        atexit.register(cleanup_lock)
        
    except Exception:
        pass
    
    app = QApplication(sys.argv)
    
    # 设置应用图标
    base_dir = get_base_dir()
    app_icon_path = os.path.join(base_dir, "resources", "icon.png")
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))
    
    window = WindowSizer()
    window.show()
    
    sys.exit(app.exec_())