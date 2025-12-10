import os
import sys
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox, 
                            QGroupBox, QGridLayout, QMenu, QAction, QSystemTrayIcon, 
                            QTabWidget, QFileDialog, QFrame, QStyle, 
                            QRadioButton, QButtonGroup, QListWidgetItem, QShortcut, QScrollArea, QSizePolicy)
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QCursor, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QSettings, QPoint, QSize, QRect, QPropertyAnimation, QEasingCurve

# 工具函数：计算颜色亮度（0-100%）
def calculate_luminance(color_hex):
    """计算颜色的相对亮度（0-100%），用于确定合适的文字颜色"""
    # 移除可能的#符号
    color_hex = color_hex.lstrip('#')
    # 转换为RGB值（0-255）
    r = int(color_hex[0:2], 16)
    g = int(color_hex[2:4], 16)
    b = int(color_hex[4:6], 16)
    # 使用相对亮度公式计算
    # L = 0.299*R + 0.587*G + 0.114*B
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255 * 100
    return luminance

# 工具函数：根据背景色自动确定文字颜色
def get_contrast_text_color(background_color):
    """根据背景色亮度自动返回合适的文字颜色（黑色或白色）"""
    luminance = calculate_luminance(background_color)
    # 亮度大于50%使用黑色，否则使用白色
    return "#000000" if luminance > 50 else "#ffffff"


class UIManager:
    """UI管理类，负责所有界面相关的操作"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
        # 获取程序所在目录（支持打包后的exe环境）
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 设置窗口图标（使用绝对路径）
        icon_path = os.path.join(self.base_dir, "resources", "icon.png")
        if os.path.exists(icon_path):
            self.main_window.setWindowIcon(QIcon(icon_path))
        
        # 主题相关
        self.themes = {}
        self.current_theme = "light"  # 默认主题
        
        # 确保主题文件夹存在（使用绝对路径）
        self.themes_folder = os.path.join(self.base_dir, "themes")
        if not os.path.exists(self.themes_folder):
            os.makedirs(self.themes_folder)
        
        # 初始化或更新默认主题文件
        self.initialize_default_themes()
        
        # 加载主题文件
        self.load_themes()
        
        # 初始化UI
        self.setup_ui()
        
    def get_contrast_color(self, bg_color):
        """根据背景色计算对比度高的文字颜色"""
        # 移除可能的#前缀
        if bg_color.startswith('#'):
            bg_color = bg_color[1:]
        
        # 将十六进制颜色转换为RGB
        r = int(bg_color[0:2], 16)
        g = int(bg_color[2:4], 16)
        b = int(bg_color[4:6], 16)
        
        # 计算亮度 (使用相对亮度公式)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # 如果亮度大于0.5，使用黑色；否则使用白色
        return "#000000" if luminance > 0.5 else "#FFFFFF"
    
    def get_variant_color(self, base_color, lightness_factor=0.95):
        """根据基础色生成轻微变体色，用于高亮状态"""
        # 移除可能的#前缀
        if base_color.startswith('#'):
            base_color = base_color[1:]
        
        # 将十六进制颜色转换为RGB
        r = int(base_color[0:2], 16)
        g = int(base_color[2:4], 16)
        b = int(base_color[4:6], 16)
        
        # 调整亮度，使变体色与基础色更加接近
        if r + g + b > 384:  # 浅色，调暗
            r = int(r * lightness_factor)
            g = int(g * lightness_factor)
            b = int(b * lightness_factor)
        else:  # 深色，调亮
            r = min(255, int(r + (255 - r) * (1 - lightness_factor)))
            g = min(255, int(g + (255 - g) * (1 - lightness_factor)))
            b = min(255, int(b + (255 - b) * (1 - lightness_factor)))
        
        # 转换回十六进制
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def get_theme_stylesheet(self, theme):
        """根据主题生成样式表"""
        t = self.themes[theme]
        
        # 使用新的标准化颜色类别
        background = t.get('background', '#f0f0f0')
        window = t.get('window', '#ffffff')
        highlight_background = t.get('highlight_background', '#ffffff')
        border = t.get('border', '#cccccc')
        button = t.get('button', '#cccccc')
        button_hover = t.get('button_hover', '#eeeeee')
        
        # 自动计算所有元素的文字颜色
        text_color = self.get_contrast_color(background)
        window_text_color = self.get_contrast_color(window)
        button_text_color = self.get_contrast_color(button)
        
        # 使用highlight_background作为高亮状态的背景色
        tab_selected = highlight_background
        
        # 为标签页计算自动对比度文字颜色
        tab_text_color = self.get_contrast_color(window)
        tab_selected_text_color = self.get_contrast_color(tab_selected)
        
        # 背景图片相关属性，使用默认值确保向后兼容
        background_image = t.get('background_image', '')
        background_repeat = t.get('background_repeat', 'no-repeat')
        background_position = t.get('background_position', 'center')
        background_size = t.get('background_size', 'auto')
        background_opacity = t.get('background_opacity', 1.0)
        fallback_background = t.get('fallback_background', background)
        
        # 背景图片样式（使用双大括号转义）
        background_style = f"background-color: {background};"
        if background_image and os.path.exists(background_image):
            background_style = f"""background-color: {background};
                background-image: url({background_image});
                background-repeat: {background_repeat};
                background-position: {background_position};
                background-size: {background_size};"""
        elif fallback_background:
            background_style = f"background-color: {fallback_background};"
        
        # 使用f-string直接构建样式表，避免.format()的问题
        stylesheet = f"""
            QMainWindow {{
                {background_style}
                font-family: Arial, sans-serif;
                font-size: 10pt;
                color: {text_color};
            }}
            QWidget {{
                background-color: {window};
                color: {window_text_color};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {border};
                border-radius: 4px;
                margin-top: 10px;
                margin-right: 10px;
                background-color: {window};
                color: {window_text_color};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {window_text_color};
            }}
            QPushButton {{
                background-color: {button};
                color: {button_text_color};
                border: none;
                padding: 6px 14px;
                text-align: center;
                font-size: 10pt;
                margin: 2px 1px;
                border-radius: 6px;
                font-weight: normal;
                min-height: 18px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QPushButton:pressed {{
                background-color: {button_hover};
                padding-top: 9px;
                padding-bottom: 7px;
            }}
            QPushButton:disabled {{
                background-color: {window};
                color: #666666;
            }}
            QLabel {{
                font-size: 10pt;
                color: {window_text_color};
            }}
            QLineEdit, QSpinBox {{
                border: 1px solid {border};
                border-radius: 3px;
                padding: 4px;
                font-size: 10pt;
                background-color: #ffffff;
                color: #000000;
            }}
            QListWidget {{
                border: 1px solid {border};
                border-radius: 4px;
                background-color: {window};
                color: {window_text_color};
            }}
            QListWidget::item {{
                height: 25px;
                color: {window_text_color};
            }}
            QTabWidget::pane {{
                border: 1px solid {border};
                background-color: {window};
            }}
            QTabBar::tab {{
                background-color: {window};
                border: 1px solid {border};
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: {tab_text_color};
            }}
            QTabBar::tab:selected {{
                background-color: {tab_selected};
                border-bottom-color: {border};
                color: {tab_selected_text_color};
            }}
            QScrollArea {{
                background-color: {background};
                border: none;
            }}
            QCheckBox, QRadioButton {{
                color: {window_text_color};
            }}
            QMenu {{
                background-color: {window};
                color: {window_text_color};
                border: 1px solid {border};
            }}
            QMenu::item {{
                color: {window_text_color};
            }}
            QMenu::item:selected {{
                background-color: {button_hover};
                color: {window_text_color};
            }}
            QMenu::item:disabled {{
                color: #666666;
            }}
        """
        
        return stylesheet
    
    def apply_theme(self):
        """应用当前主题"""
        # 检查当前主题是否存在，如果不存在则回退到默认主题
        if self.current_theme not in self.themes:
            self.current_theme = "light"
            self.save_theme_setting()
        stylesheet = self.get_theme_stylesheet(self.current_theme)
        self.main_window.setStyleSheet(stylesheet)
    
    def change_theme(self, theme_name):
        """切换主题"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.apply_theme()
            self.save_theme_setting()
            
            # 更新主窗口中的颜色设置
            self.update_main_window_colors()
    
    def load_theme_setting(self):
        """加载保存的主题设置"""
        settings = QSettings("WindowSizer", "Settings")
        self.current_theme = settings.value("theme", "light")
    
    def save_theme_setting(self):
        """保存主题设置"""
        settings = QSettings("WindowSizer", "Settings")
        settings.setValue("theme", self.current_theme)
    
    def initialize_default_themes(self):
        """初始化默认主题文件"""
        # 默认主题定义
        default_themes = {
            "light": {
                "name": "浅色主题",
                "background": "#f3f3f3",  # 应用程序背景色 - Win11浅色背景
                "window": "#ffffff",  # 窗口背景色 - 纯白
                "highlight_background": "#f9f9f9",  # 高亮背景色
                "border": "#d1d1d1",  # 边框颜色 - Win11浅色边框
                "button": "#005fb8",  # 按钮背景色 - Win11蓝色
                "button_hover": "#0078d4",  # 按钮悬停背景色 - Win11高亮蓝
                "background_image": "",  # 背景图片路径
                "background_repeat": "no-repeat",
                "background_position": "center",
                "background_size": "auto",
                "background_opacity": 1.0,
                "fallback_background": "#f3f3f3"
            },
            "dark": {
                "name": "深色主题",
                "background": "#202020",  # 应用程序背景色 - Win11深色背景
                "window": "#2b2b2b",  # 窗口背景色 - Win11深色窗口
                "highlight_background": "#3b3b3b",  # 高亮背景色
                "border": "#3f3f3f",  # 边框颜色 - Win11深色边框
                "button": "#0078d4",  # 按钮背景色 - Win11蓝色
                "button_hover": "#1890e8",  # 按钮悬停背景色 - Win11高亮蓝
                "background_image": "",
                "background_repeat": "no-repeat",
                "background_position": "center",
                "background_size": "auto",
                "background_opacity": 1.0,
                "fallback_background": "#202020"
            }
        }
        
        # 保存默认主题到文件
        for theme_name, theme_data in default_themes.items():
            self.save_theme_to_file(theme_name, theme_data)
    
    def save_theme_to_file(self, theme_name, theme_data):
        """将主题保存到文件"""
        theme_file = os.path.join(self.themes_folder, f"{theme_name}.json")
        with open(theme_file, 'w', encoding='utf-8') as f:
            json.dump(theme_data, f, ensure_ascii=False, indent=4)
    
    def load_themes(self):
        """从文件加载主题"""
        self.themes = {}
        
        # 遍历主题文件夹中的所有json文件
        for file_name in os.listdir(self.themes_folder):
            if file_name.endswith(".json"):
                theme_name = os.path.splitext(file_name)[0]
                theme_file = os.path.join(self.themes_folder, file_name)
                try:
                    with open(theme_file, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        self.themes[theme_name] = theme_data
                except Exception:
                    pass  # 静默忽略加载失败的主题文件
        
        # 确保至少有一个主题
        if not self.themes:
            self.initialize_default_themes()
            self.load_themes()
    
    def setup_ui(self):
        """初始化UI界面，采用紧凑布局设计"""
        # 设置窗口标题
        self.main_window.setWindowTitle("WindowSizer")
        
        # 加载保存的主题
        self.load_theme_setting()
        
        # 应用主题样式
        self.apply_theme()
        
        # 创建中心部件
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 连接标签页切换信号
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # 创建主页面
        self.create_main_tab()
        
        # 创建设置标签页
        self.create_settings_tab()
        
        # 创建主题标签页
        self.create_theme_tab()
        
        # 为标签页添加图标
        home_icon_path = os.path.join(self.base_dir, "resources", "btn_home.png")
        if os.path.exists(home_icon_path):
            self.tab_widget.setTabIcon(0, QIcon(home_icon_path))
        
        settings_icon_path = os.path.join(self.base_dir, "resources", "btn_settings.png")
        if os.path.exists(settings_icon_path):
            self.tab_widget.setTabIcon(1, QIcon(settings_icon_path))
        
        themes_icon_path = os.path.join(self.base_dir, "resources", "btn_themes.png")
        if os.path.exists(themes_icon_path):
            self.tab_widget.setTabIcon(2, QIcon(themes_icon_path))
        
        # 设置窗口快捷键
        self.set_shortcuts()
        
        # 初始化系统托盘图标
        self.init_tray()
    
    def create_main_tab(self):
        """创建主页面，采用参考界面的紧凑布局"""
        main_tab = QWidget()
        main_layout = QHBoxLayout(main_tab)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 左侧面板
        left_panel = QWidget()
        left_panel.setMinimumWidth(390)  # 设置最小宽度，允许适当扩展
        left_panel.setMaximumWidth(450)  # 设置最大宽度，防止过度拉伸
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)
        
        # 窗口信息区域
        info_group = QGroupBox("窗口信息")
        info_layout = QGridLayout(info_group)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setSpacing(4)
        
        # 设置列宽，确保标签列宽度固定，内容列自适应
        info_layout.setColumnStretch(0, 0)  # 标签列不拉伸
        info_layout.setColumnStretch(1, 1)  # 内容列拉伸
        info_layout.setColumnStretch(2, 0)  # 标签列不拉伸
        info_layout.setColumnStretch(3, 1)  # 内容列拉伸
        
        # 标题
        title_label = QLabel("标题:")
        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_layout.addWidget(title_label, 0, 0)
        self.title_label = QLabel("-")
        self.title_label.setWordWrap(True)
        # 固定标题标签高度为两行文本（约50px），并限制最大宽度防止撑开布局
        self.title_label.setFixedHeight(50)
        self.title_label.setMaximumWidth(320)
        info_layout.addWidget(self.title_label, 0, 1, 1, 3)
        
        # 类名
        class_label = QLabel("类名:")
        class_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_layout.addWidget(class_label, 1, 0)
        self.class_label = QLabel("-")
        self.class_label.setMinimumHeight(25)
        info_layout.addWidget(self.class_label, 1, 1, 1, 3)
        
        # 进程
        process_label = QLabel("进程:")
        process_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_layout.addWidget(process_label, 2, 0)
        self.process_label = QLabel("-")
        self.process_label.setMinimumHeight(25)
        info_layout.addWidget(self.process_label, 2, 1)
        
        # PID
        pid_label = QLabel("PID:")
        pid_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_layout.addWidget(pid_label, 2, 2)
        self.pid_label = QLabel("-")
        self.pid_label.setMinimumWidth(60)
        self.pid_label.setMinimumHeight(25)
        info_layout.addWidget(self.pid_label, 2, 3)
        
        left_layout.addWidget(info_group)
        
        # 位置和尺寸配置 - 重构为水平布局，分为位置和尺寸两个区块
        config_group = QGroupBox("位置和尺寸")
        config_main_layout = QVBoxLayout(config_group)
        config_main_layout.setContentsMargins(8, 8, 8, 8)
        config_main_layout.setSpacing(4)
        
        # 创建水平布局容器，将位置和尺寸放在同一行
        config_horizontal_layout = QHBoxLayout()
        config_horizontal_layout.setSpacing(15)
        
        # === 位置区块 ===
        position_widget = QWidget()
        position_layout = QHBoxLayout(position_widget)
        position_layout.setContentsMargins(0, 0, 0, 0)
        position_layout.setSpacing(5)
        
        # 位置标签
        position_title = QLabel("位置")
        position_title.setStyleSheet("font-weight: bold;")
        position_layout.addWidget(position_title)
        
        # X坐标
        x_label = QLabel("X:")
        x_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        position_layout.addWidget(x_label)
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-10000, 10000)
        self.x_spin.setMinimumWidth(70)
        self.x_spin.setMinimumHeight(25)
        position_layout.addWidget(self.x_spin)
        
        # Y坐标
        y_label = QLabel("Y:")
        y_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        position_layout.addWidget(y_label)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-10000, 10000)
        self.y_spin.setMinimumWidth(70)
        self.y_spin.setMinimumHeight(25)
        position_layout.addWidget(self.y_spin)
        
        config_horizontal_layout.addWidget(position_widget)
        
        # === 尺寸区块 ===
        size_widget = QWidget()
        size_layout = QHBoxLayout(size_widget)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(5)
        
        # 尺寸标签
        size_title = QLabel("尺寸")
        size_title.setStyleSheet("font-weight: bold;")
        size_layout.addWidget(size_title)
        
        # 宽度
        width_label = QLabel("宽:")
        width_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        size_layout.addWidget(width_label)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(10, 5000)
        self.width_spin.setMinimumWidth(70)
        self.width_spin.setMinimumHeight(25)
        size_layout.addWidget(self.width_spin)
        
        # 高度
        height_label = QLabel("高:")
        height_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        size_layout.addWidget(height_label)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(10, 5000)
        self.height_spin.setMinimumWidth(70)
        self.height_spin.setMinimumHeight(25)
        size_layout.addWidget(self.height_spin)
        
        config_horizontal_layout.addWidget(size_widget)
        config_horizontal_layout.addStretch()
        
        config_main_layout.addLayout(config_horizontal_layout)
        
        left_layout.addWidget(config_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(3)
        
        # 保存配置按钮
        self.save_btn = QPushButton("保存配置")
        self.save_btn.setMinimumHeight(26)
        # 添加图标
        save_icon_path = os.path.join(self.base_dir, "resources", "btn_save.png")
        if os.path.exists(save_icon_path):
            self.save_btn.setIcon(QIcon(save_icon_path))
            self.save_btn.setIconSize(QSize(16, 16))
        self.save_btn.clicked.connect(self.main_window.save_config)
        button_layout.addWidget(self.save_btn)
        
        # 删除配置按钮
        self.delete_btn = QPushButton("删除配置")
        self.delete_btn.setMinimumHeight(26)
        # 添加图标
        delete_icon_path = os.path.join(self.base_dir, "resources", "btn_delete.png")
        if os.path.exists(delete_icon_path):
            self.delete_btn.setIcon(QIcon(delete_icon_path))
            self.delete_btn.setIconSize(QSize(16, 16))
        self.delete_btn.clicked.connect(self.main_window.delete_config)
        button_layout.addWidget(self.delete_btn)
        
        # 新增配置按钮
        self.add_config_btn = QPushButton("新增配置")
        self.add_config_btn.setMinimumHeight(26)
        # 添加图标
        add_icon_path = os.path.join(self.base_dir, "resources", "btn_add.png")
        if os.path.exists(add_icon_path):
            self.add_config_btn.setIcon(QIcon(add_icon_path))
            self.add_config_btn.setIconSize(QSize(16, 16))
        self.add_config_btn.clicked.connect(self.main_window.toggle_window_list)
        button_layout.addWidget(self.add_config_btn)
        
        left_layout.addLayout(button_layout)
        
        # 配置列表，添加垂直滚动条
        self.config_list = QListWidget()
        self.config_list.itemClicked.connect(self.main_window.on_config_selected)
        self.config_list.setMinimumHeight(150)
        self.config_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        left_layout.addWidget(self.config_list)
        
        # 应用全部配置按钮
        self.apply_all_btn = QPushButton("应用全部配置")
        self.apply_all_btn.setMinimumHeight(28)
        # 添加图标
        apply_icon_path = os.path.join(self.base_dir, "resources", "btn_apply.png")
        if os.path.exists(apply_icon_path):
            self.apply_all_btn.setIcon(QIcon(apply_icon_path))
            self.apply_all_btn.setIconSize(QSize(18, 18))
        self.apply_all_btn.clicked.connect(self.main_window.apply_all_configs)
        left_layout.addWidget(self.apply_all_btn)
        
        # 创建右侧面板容器，用于实现动画效果
        self.right_panel_container = QWidget()
        self.right_panel_container.setMinimumWidth(0)  # 初始最小宽度为0
        self.right_panel_container.setMaximumWidth(0)  # 初始最大宽度为0（隐藏状态）
        self.right_panel_container.setMinimumHeight(200)  # 设置最小高度
        self.right_panel_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_container_layout = QVBoxLayout(self.right_panel_container)
        right_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)
        
        # 窗口列表区域
        window_group = QGroupBox("窗口列表")
        window_layout = QVBoxLayout(window_group)
        window_layout.setContentsMargins(5, 5, 5, 5)
        
        # 窗口列表面板
        self.window_list_panel = QWidget()
        self.window_list_layout = QVBoxLayout(self.window_list_panel)
        self.window_list_layout.setContentsMargins(0, 0, 0, 0)
        self.window_list_layout.setSpacing(3)
        
        # 窗口列表，添加垂直滚动条
        self.window_list = QListWidget()
        self.window_list.itemClicked.connect(self.main_window.on_window_selected)
        self.window_list.setStyleSheet("QListWidget::item { height: 25px; }")
        self.window_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.window_list_layout.addWidget(self.window_list)
        
        # 刷新按钮
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFixedSize(80, 28)
        # 设置刷新图标
        refresh_icon_path = os.path.join(self.base_dir, "resources", "btn_refresh.png")
        if os.path.exists(refresh_icon_path):
            refresh_btn.setIcon(QIcon(refresh_icon_path))
            refresh_btn.setIconSize(QSize(16, 16))
        else:
            # 使用内置图标
            refresh_btn.setIcon(self.main_window.style().standardIcon(self.main_window.style().SP_BrowserReload))
        refresh_btn.setToolTip("刷新窗口列表")
        refresh_btn.clicked.connect(self.main_window.refresh_window_list)
        refresh_layout.addWidget(refresh_btn)
        self.window_list_layout.addLayout(refresh_layout)
        
        # 默认显示窗口列表面板
        self.window_list_panel.show()
        window_layout.addWidget(self.window_list_panel)
        right_layout.addWidget(window_group)
        
        # 将右侧面板添加到容器中
        right_container_layout.addWidget(right_panel)
        
        # 将左右面板添加到主布局
        main_layout.addWidget(left_panel, 0)  # 左侧面板不拉伸（固定占用空间）
        main_layout.addWidget(self.right_panel_container, 1)  # 右侧面板可以拉伸填充剩余空间
        
        # 创建右侧面板动画
        self.right_panel_animation = QPropertyAnimation(self.right_panel_container, b"maximumWidth")
        self.right_panel_animation.setDuration(300)  # 动画持续时间
        self.right_panel_animation.setEasingCurve(QEasingCurve.InOutQuad)  # 缓动曲线
        self.right_panel_animation.setStartValue(0)
        self.right_panel_animation.setEndValue(16777215)  # 设置为最大值，允许无限扩展填充可用空间
        
        # 右侧面板初始状态
        self.right_panel_visible = False
        
        # 添加标签页
        self.tab_widget.addTab(main_tab, "主页面")
    
    def create_settings_tab(self):
        """创建设置标签页"""
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(10, 10, 10, 30)
        settings_layout.setSpacing(10)
        
        # 设置页面最大宽度
        settings_tab.setMaximumWidth(400)
        
        # 第一行：开机自启动
        self.startup_checkbox = QCheckBox("开启自启动")
        self.startup_checkbox.setChecked(self.main_window.is_startup_enabled())
        self.startup_checkbox.stateChanged.connect(self.main_window.toggle_startup)
        settings_layout.addWidget(self.startup_checkbox)
        
        # 第二行：自动应用配置、托盘图标双击应用
        second_row_layout = QHBoxLayout()
        second_row_layout.setSpacing(15)
        
        self.auto_apply_checkbox = QCheckBox("自动应用配置")
        self.auto_apply_checkbox.setChecked(self.main_window.auto_apply_config)
        self.auto_apply_checkbox.stateChanged.connect(self.main_window.on_auto_apply_changed)
        second_row_layout.addWidget(self.auto_apply_checkbox)
        
        self.double_click_apply_checkbox = QCheckBox("托盘图标双击应用")
        self.double_click_apply_checkbox.setChecked(self.main_window.double_click_apply)
        self.double_click_apply_checkbox.stateChanged.connect(self.main_window.on_double_click_apply_changed)
        second_row_layout.addWidget(self.double_click_apply_checkbox)
        
        second_row_layout.addStretch()
        settings_layout.addLayout(second_row_layout)
        
        # 第三行：关闭到托盘、完全关闭
        third_row_layout = QHBoxLayout()
        third_row_layout.setSpacing(15)
        
        # 创建单选按钮组
        self.close_behavior_group = QButtonGroup()
        
        # 关闭到最小化选项
        self.minimize_on_close_radio = QRadioButton("关闭到托盘")
        self.close_behavior_group.addButton(self.minimize_on_close_radio, 0)
        third_row_layout.addWidget(self.minimize_on_close_radio)
        
        # 直接关闭选项
        self.exit_on_close_radio = QRadioButton("完全关闭")
        self.close_behavior_group.addButton(self.exit_on_close_radio, 1)
        third_row_layout.addWidget(self.exit_on_close_radio)
        
        # 连接信号
        self.close_behavior_group.buttonClicked.connect(self.main_window.save_close_behavior_setting)
        
        third_row_layout.addStretch()
        settings_layout.addLayout(third_row_layout)
        
        # 第四行：配置文件路径
        fourth_row_group = QGroupBox("配置文件路径")
        fourth_row_layout = QVBoxLayout(fourth_row_group)
        fourth_row_layout.setContentsMargins(8, 8, 8, 8)
        fourth_row_layout.setSpacing(5)
        
        # 显示当前路径（绝对路径 + 文件名）
        current_path = self.main_window.config_manager.get_config_path()
        config_file_full_path = os.path.join(current_path, "window_configs.json")
        self.config_path_label = QLabel(f"{config_file_full_path}")
        self.config_path_label.setWordWrap(True)
        self.config_path_label.setStyleSheet("font-size: 9pt; color: #666;")
        fourth_row_layout.addWidget(self.config_path_label)
        
        # 选择路径按钮（文件夹选择）
        select_path_btn = QPushButton("选择文件夹")
        select_path_btn.setMinimumHeight(26)
        select_path_btn.clicked.connect(self.select_config_path)
        fourth_row_layout.addWidget(select_path_btn)
        
        settings_layout.addWidget(fourth_row_group)
        
        # 第五行：导入配置、导出配置
        fifth_row_layout = QHBoxLayout()
        fifth_row_layout.setSpacing(8)
        
        import_btn = QPushButton("导入配置")
        import_btn.setMinimumHeight(26)
        # 添加图标
        import_icon_path = os.path.join(self.base_dir, "resources", "btn_import.png")
        if os.path.exists(import_icon_path):
            import_btn.setIcon(QIcon(import_icon_path))
            import_btn.setIconSize(QSize(16, 16))
        import_btn.clicked.connect(self.main_window.import_configs)
        fifth_row_layout.addWidget(import_btn, 1)
        
        export_btn = QPushButton("导出配置")
        export_btn.setMinimumHeight(26)
        # 添加图标
        export_icon_path = os.path.join(self.base_dir, "resources", "btn_export.png")
        if os.path.exists(export_icon_path):
            export_btn.setIcon(QIcon(export_icon_path))
            export_btn.setIconSize(QSize(16, 16))
        export_btn.clicked.connect(self.main_window.export_configs)
        fifth_row_layout.addWidget(export_btn, 1)
        
        settings_layout.addLayout(fifth_row_layout)
        
        # 最后：关于
        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout(about_group)
        about_layout.setContentsMargins(8, 8, 8, 8)
        about_layout.setSpacing(5)
        
        # 程序名称和版本
        name_label = QLabel("WindowSizer v1.0")
        name_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        about_layout.addWidget(name_label)
        
        # 程序描述
        desc_label = QLabel("窗口大小调整工具")
        about_layout.addWidget(desc_label)
        
        # 程序网站链接
        from PyQt5.QtWidgets import QTextBrowser
        website_browser = QTextBrowser()
        website_browser.setMaximumHeight(30)
        website_browser.setOpenExternalLinks(True)
        website_browser.setHtml('<a href="https://github.com/kresepons/WindowSizer">访问项目主页</a>')
        website_browser.setStyleSheet("border: none; background-color: transparent;")
        about_layout.addWidget(website_browser)
        
        settings_layout.addWidget(about_group)
        
        # 添加底部空白
        settings_layout.addStretch(1)
        
        # 添加标签页
        self.tab_widget.addTab(settings_tab, "设置")
    
    def init_tray(self):
        """初始化系统托盘"""
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self.main_window)
        
        # 设置托盘图标提示文本
        self.tray_icon.setToolTip("WindowSizer - 窗口大小调整工具")
        
        # 检查图标文件是否存在，不存在则使用默认图标
        icon_path = os.path.join(self.base_dir, "resources", "icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.main_window.style().standardIcon(self.main_window.style().SP_ComputerIcon))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 显示/隐藏主界面
        show_action = QAction("显示/隐藏主界面", self.main_window)
        # 添加图标（使用16x16尺寸）
        home_icon_path = os.path.join(self.base_dir, "resources", "btn_home.png")
        if os.path.exists(home_icon_path):
            icon = QIcon(home_icon_path)
            # 为QAction设置图标
            show_action.setIcon(icon)
        show_action.triggered.connect(self.main_window.toggle_window_visibility)
        tray_menu.addAction(show_action)
        
        # 退出程序
        quit_action = QAction("退出程序", self.main_window)
        # 添加图标（使用16x16尺寸）
        power_icon_path = os.path.join(self.base_dir, "resources", "power.png")
        if os.path.exists(power_icon_path):
            icon = QIcon(power_icon_path)
            quit_action.setIcon(icon)
        quit_action.triggered.connect(self.main_window.quit_program)
        tray_menu.addAction(quit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 双击托盘图标事件
        self.tray_icon.activated.connect(self.main_window.on_tray_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def set_shortcuts(self):
        """设置键盘快捷键"""
        # 保存配置 (Ctrl+S)
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self.main_window)
        save_shortcut.activated.connect(self.main_window.save_config)
        
        # 应用配置 (Ctrl+A)
        apply_shortcut = QShortcut(QKeySequence("Ctrl+A"), self.main_window)
        apply_shortcut.activated.connect(self.main_window.apply_config)
        
        # 一键应用所有 (Ctrl+Shift+A)
        apply_all_shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), self.main_window)
        apply_all_shortcut.activated.connect(self.main_window.apply_all_configs)
        
        # 刷新窗口列表 (F5)
        refresh_shortcut = QShortcut(QKeySequence("F5"), self.main_window)
        refresh_shortcut.activated.connect(self.main_window.refresh_window_list)
        
        # 显示/隐藏主界面 (Ctrl+M)
        toggle_shortcut = QShortcut(QKeySequence("Ctrl+M"), self.main_window)
        toggle_shortcut.activated.connect(self.main_window.toggle_window_visibility)
    

    
    def create_theme_tab(self):
        """创建主题标签页"""
        theme_tab = QWidget()
        theme_layout = QVBoxLayout(theme_tab)
        theme_layout.setContentsMargins(10, 10, 10, 30)  # 增加底部空白
        theme_layout.setSpacing(8)  # 调整间距
        
        # 主题选择设置
        theme_group = QGroupBox("主题选项")
        theme_group_layout = QVBoxLayout(theme_group)
        theme_group_layout.setContentsMargins(8, 8, 8, 8)
        theme_group_layout.setSpacing(8)
        
        # 主题选择单选按钮组
        self.theme_group = QButtonGroup()
        
        # 主题选择布局
        self.theme_selection_layout = QVBoxLayout()
        self.theme_selection_layout.setObjectName("theme_selection_layout")  # 设置对象名以便查找
        self.theme_selection_layout.setSpacing(5)
        
        # 浅色主题选项
        self.light_theme_radio = QRadioButton("浅色主题")
        self.theme_group.addButton(self.light_theme_radio, 0)
        self.theme_selection_layout.addWidget(self.light_theme_radio)
        
        # 深色主题选项
        self.dark_theme_radio = QRadioButton("深色主题")
        self.theme_group.addButton(self.dark_theme_radio, 1)
        self.theme_selection_layout.addWidget(self.dark_theme_radio)

        
        theme_group_layout.addLayout(self.theme_selection_layout)
        
        # 主题预览区域
        preview_group = QGroupBox("主题预览")
        self.theme_preview_layout = QGridLayout(preview_group)
        self.theme_preview_layout.setContentsMargins(8, 8, 8, 8)
        self.theme_preview_layout.setSpacing(5)
        
        # 当前主题显示
        self.theme_preview_label = QLabel("当前主题: " + self.themes[self.current_theme]["name"])
        self.theme_preview_layout.addWidget(self.theme_preview_label, 0, 0, 1, 3)
        
        # 创建水平布局用于横向排列色块
        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(5)
        
        # 添加主题色块，仅保留色块，正方形形状，横向排列
        # 只显示实际在样式表中使用的颜色属性
        used_color_keys = ['background', 'window', 'highlight_background', 'border', 'button', 'button_hover']
        for key in used_color_keys:
            if key in self.themes[self.current_theme]:
                value = self.themes[self.current_theme][key]
                color_display = QWidget()
                # 设置正方形形状
                color_display.setFixedSize(30, 30)
                color_display.setStyleSheet(f"background-color: {value}; border: 1px solid #ccc; border-radius: 3px;")
                colors_layout.addWidget(color_display)
        
        # 添加伸缩项，使色块靠左排列
        colors_layout.addStretch()
        
        # 将色块布局添加到主题预览布局的第1行
        self.theme_preview_layout.addLayout(colors_layout, 1, 0, 1, 3)
        
        theme_group_layout.addWidget(preview_group)
        
        # 自定义主题区域
        custom_theme_group = QGroupBox("自定义主题")
        custom_theme_layout = QVBoxLayout(custom_theme_group)
        custom_theme_layout.setContentsMargins(8, 8, 8, 8)
        custom_theme_layout.setSpacing(8)
        
        # 添加按钮布局（水平排列）
        theme_buttons_layout = QHBoxLayout()
        theme_buttons_layout.setSpacing(8)
        
        # 添加新主题按钮
        add_theme_btn = QPushButton("添加新主题")
        add_theme_btn.clicked.connect(self.add_custom_theme)
        theme_buttons_layout.addWidget(add_theme_btn)
        
        # 删除主题按钮
        delete_theme_btn = QPushButton("删除主题")
        delete_theme_btn.clicked.connect(self.delete_custom_theme)
        theme_buttons_layout.addWidget(delete_theme_btn)
        
        custom_theme_layout.addLayout(theme_buttons_layout)
        
        # 颜色自定义区域（初始隐藏）
        self.custom_colors_widget = QWidget()
        self.custom_colors_widget.setVisible(False)
        custom_colors_layout = QGridLayout(self.custom_colors_widget)
        custom_colors_layout.setContentsMargins(0, 8, 0, 8)
        custom_colors_layout.setSpacing(5)
        
        # 颜色选择项
        self.color_inputs = {}  # 存储颜色输入框的引用
        self.color_buttons = {}  # 存储颜色按钮的引用
        color_labels = [
            ("主题名称", "name"),
            ("应用程序背景色", "background"),
            ("窗口背景色", "window"),
            ("边框颜色", "border"),
            ("按钮背景色", "button"),
            ("按钮悬停背景色", "button_hover")
        ]
        
        for i, (label_text, key) in enumerate(color_labels):
            row = i // 2
            col = (i % 2) * 3
            
            # 标签
            label = QLabel(label_text + ":")
            custom_colors_layout.addWidget(label, row, col)
            
            if key == "name":
                # 主题名称使用文本输入框
                name_input = QLineEdit()
                name_input.setFixedSize(100, 25)
                name_input.setPlaceholderText("自定义主题")
                self.color_inputs[key] = name_input
                custom_colors_layout.addWidget(name_input, row, col + 1)
            else:
                # 颜色选择使用纯色方框（与预览大小一致）
                color_btn = QPushButton()
                color_btn.setFixedSize(30, 30)
                color_btn.setProperty("color_key", key)
                color_btn.setProperty("color_value", "#ffffff")  # 默认白色
                color_btn.setStyleSheet("background-color: #ffffff; border: 1px solid #ccc; border-radius: 3px;")
                color_btn.clicked.connect(self.select_color)
                self.color_buttons[key] = color_btn  # 保存按钮引用
                custom_colors_layout.addWidget(color_btn, row, col + 1)
        
        # 保存自定义主题按钮
        save_custom_btn = QPushButton("保存自定义主题")
        save_custom_btn.clicked.connect(self.save_custom_theme)
        custom_colors_layout.addWidget(save_custom_btn, len(color_labels)//2 + 1, 0, 1, 6)
        
        custom_theme_layout.addWidget(self.custom_colors_widget)
        
        theme_group_layout.addWidget(custom_theme_group)
        
        # 连接主题切换信号
        self.theme_group.buttonClicked.connect(self.on_theme_changed)
        
        # 设置当前选中的主题
        if self.current_theme == "light":
            self.light_theme_radio.setChecked(True)
        elif self.current_theme == "dark":
            self.dark_theme_radio.setChecked(True)
        
        theme_layout.addWidget(theme_group)
        
        # 添加底部空白
        theme_layout.addStretch(1)
        
        # 添加标签页
        self.tab_widget.addTab(theme_tab, "主题")
    
    def toggle_right_panel(self):
        """切换右侧面板的显示/隐藏，带有平滑过渡动画"""
        if self.right_panel_visible:
            # 隐藏右侧面板
            self.right_panel_animation.setDirection(QPropertyAnimation.Backward)
            self.right_panel_visible = False
        else:
            # 显示右侧面板
            self.right_panel_animation.setDirection(QPropertyAnimation.Forward)
            self.right_panel_visible = True
        
        # 启动动画
        self.right_panel_animation.start()
    
    def animate_window_width(self, target_width):
        """平滑调整窗口宽度"""
        # 获取当前窗口的几何信息
        current_geometry = self.main_window.geometry()
        
        # 创建窗口几何动画，存储为实例变量防止被垃圾回收
        if not hasattr(self, 'window_width_animation'):
            self.window_width_animation = QPropertyAnimation(self.main_window, b"geometry")
        
        self.window_width_animation.stop()  # 停止任何正在运行的动画
        self.window_width_animation.setDuration(300)  # 300ms动画时长
        self.window_width_animation.setEasingCurve(QEasingCurve.InOutQuad)  # 缓动曲线
        
        # 设置起始和结束几何信息
        start_geometry = QRect(
            current_geometry.x(),
            current_geometry.y(),
            current_geometry.width(),
            current_geometry.height()
        )
        
        end_geometry = QRect(
            current_geometry.x(),
            current_geometry.y(),
            target_width,
            current_geometry.height()
        )
        
        self.window_width_animation.setStartValue(start_geometry)
        self.window_width_animation.setEndValue(end_geometry)
        self.window_width_animation.start()
    
    def on_tab_changed(self, index):
        """处理标签页切换事件"""
        # 当切换到设置或主题页面时，调整窗口宽度为400px
        if index == 1 or index == 2:
            # 如果右侧面板是开着的，先关闭它
            if self.right_panel_visible:
                self.right_panel_animation.setDirection(QPropertyAnimation.Backward)
                self.right_panel_visible = False
                self.right_panel_animation.start()
                # 更新按钮文本
                self.add_config_btn.setText("新增配置")
            # 调整窗口宽度为400
            self.animate_window_width(400)
    
    def on_theme_changed(self):
        """处理主题切换事件"""
        # 获取选中的主题
        checked_button = self.theme_group.checkedButton()
        if checked_button == self.light_theme_radio:
            self.change_theme("light")
        elif checked_button == self.dark_theme_radio:
            self.change_theme("dark")
        else:
            # 处理自定义主题
            for theme_name, theme_data in self.themes.items():
                if theme_data.get("name") == checked_button.text():
                    self.change_theme(theme_name)
                    break
        
        # 更新主题预览
        self.update_theme_preview()
    
    def update_theme_preview(self):
        """更新主题预览区域"""
        # 更新当前主题显示
        self.theme_preview_label.setText("当前主题: " + self.themes[self.current_theme]["name"])
        
        # 清除除了预览标签之外的所有预览项
        # 从索引1开始，保留第0个位置的预览标签
        for i in reversed(range(1, self.theme_preview_layout.count())):
            item = self.theme_preview_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
        
        # 创建水平布局用于横向排列色块
        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(5)
        
        # 添加主题色块，仅保留色块，正方形形状，横向排列
        # 只显示实际在样式表中使用的颜色属性
        used_color_keys = ['background', 'window', 'highlight_background', 'border', 'button', 'button_hover']
        for key in used_color_keys:
            if key in self.themes[self.current_theme]:
                value = self.themes[self.current_theme][key]
                color_display = QWidget()
                # 设置正方形形状
                color_display.setFixedSize(30, 30)
                color_display.setStyleSheet(f"background-color: {value}; border: 1px solid #ccc; border-radius: 3px;")
                colors_layout.addWidget(color_display)
        
        # 添加伸缩项，使色块靠左排列
        colors_layout.addStretch()
        
        # 将色块布局添加到主题预览布局的第1行
        self.theme_preview_layout.addLayout(colors_layout, 1, 0, 1, 3)
    
    def add_custom_theme(self):
        """添加自定义主题"""
        # 显示自定义颜色区域
        self.custom_colors_widget.setVisible(True)
        
        # 填充默认值
        default_theme = {
            "name": "自定义主题",
            "background": "#f0f0f0",
            "window": "#ffffff",
            "highlight_background": "#ffffff",
            "border": "#d0d0d0",
            "button": "#4CAF50",
            "button_hover": "#45a049",
            "background_image": "",
            "background_repeat": "no-repeat",
            "background_position": "center",
            "background_size": "auto",
            "background_opacity": 1.0,
            "fallback_background": "#f0f0f0"
        }
        
        # 更新颜色按钮显示
        for key, value in default_theme.items():
            if key == "name" and key in self.color_inputs:
                # 主题名称特殊处理
                self.color_inputs[key].setText(value)
            elif key in self.color_buttons and value:
                # 设置按钮背景色为纯色方框
                btn = self.color_buttons[key]
                btn.setStyleSheet(f"background-color: {value}; border: 1px solid #ccc; border-radius: 3px;")
                btn.setProperty("color_value", value)
    
    def select_color(self):
        """选择颜色"""
        sender = self.main_window.sender()
        color_key = sender.property("color_key")
        
        # 获取当前颜色值
        current_color_value = sender.property("color_value")
        if not current_color_value:
            current_color_value = "#ffffff"  # 默认白色
        
        # 创建颜色选择对话框
        from PyQt5.QtWidgets import QColorDialog
        from PyQt5.QtGui import QColor
        color = QColorDialog.getColor(QColor(current_color_value))
        
        if color.isValid():
            color_name = color.name().upper()
            # 更新按钮显示为纯色方框
            sender.setStyleSheet(f"background-color: {color_name}; border: 1px solid #ccc; border-radius: 3px;")
            sender.setProperty("color_value", color_name)  # 保存颜色值
    
    def save_custom_theme(self):
        """保存自定义主题"""
        # 获取自定义主题数据
        theme_data = {}
        
        # 获取主题名称
        if "name" in self.color_inputs:
            theme_name = self.color_inputs["name"].text().strip()
        else:
            theme_name = "自定义主题"
        
        if not theme_name:
            theme_name = "自定义主题"
        
        theme_data["name"] = theme_name
        
        # 获取其他颜色值
        color_keys = ["background", "window", "border", "button", "button_hover"]
        
        for key in color_keys:
            if key in self.color_buttons:
                btn = self.color_buttons[key]
                color_value = btn.property("color_value")
                theme_data[key] = color_value if color_value else "#ffffff"
        
        # 添加其他必要字段
        theme_data["highlight_background"] = theme_data.get("window", "#ffffff")
        theme_data["background_image"] = ""
        theme_data["background_repeat"] = "no-repeat"
        theme_data["background_position"] = "center"
        theme_data["background_size"] = "auto"
        theme_data["background_opacity"] = 1.0
        theme_data["fallback_background"] = theme_data.get("background", "#f0f0f0")
        
        # 生成唯一的主题文件名
        base_name = theme_name.replace(" ", "_").lower()
        theme_filename = base_name
        counter = 1
        while os.path.exists(os.path.join(self.themes_folder, f"{theme_filename}.json")):
            theme_filename = f"{base_name}_{counter}"
            counter += 1
        
        # 保存主题文件
        theme_file = os.path.join(self.themes_folder, f"{theme_filename}.json")
        try:
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, ensure_ascii=False, indent=4)
            
            # 加载新主题
            self.themes[theme_filename] = theme_data
            
            # 创建新的单选按钮
            radio_button = QRadioButton(theme_name)
            self.theme_group.addButton(radio_button, len(self.themes))
            
            # 插入到主题选择布局中
            if hasattr(self, 'theme_selection_layout'):
                self.theme_selection_layout.addWidget(radio_button)
            
            # 连接信号
            radio_button.toggled.connect(lambda checked, name=theme_filename: self.on_custom_theme_selected(name) if checked else None)
            
            # 选中新主题
            radio_button.setChecked(True)
            
            # 隐藏自定义区域
            self.custom_colors_widget.setVisible(False)
        except Exception as e:
            pass
    
    def update_main_window_colors(self):
        """根据当前主题更新主窗口的颜色设置"""
        # 确保UI元素存在
        if not hasattr(self, 'title_label'):
            return
            
        # 获取当前主题
        if self.current_theme in self.themes:
            current_theme = self.themes[self.current_theme]
        else:
            current_theme = self.themes["light"]  # 默认使用浅色主题
        
        # 获取主题颜色
        window = current_theme.get('window', '#ffffff')
        window_text_color = self.get_contrast_color(window)
        
        # 设置主窗口颜色
        self.title_label.setStyleSheet(f"color: {window_text_color};")
        self.class_label.setStyleSheet(f"color: {window_text_color};")
        self.process_label.setStyleSheet(f"color: {window_text_color};")
        self.pid_label.setStyleSheet(f"color: {window_text_color};")
        
        # 设置输入框颜色
        input_stylesheet = f"color: {window_text_color}; background-color: {window};"
        self.x_spin.setStyleSheet(input_stylesheet)
        self.y_spin.setStyleSheet(input_stylesheet)
        self.width_spin.setStyleSheet(input_stylesheet)
        self.height_spin.setStyleSheet(input_stylesheet)
    
    def on_custom_theme_selected(self, theme_name):
        """处理自定义主题选择"""
        self.change_theme(theme_name)
        self.update_theme_preview()
    
    def select_config_path(self):
        """选择配置文件路径"""
        from PyQt5.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self.main_window, "选择配置文件保存路径")
        if path:
            if self.main_window.config_manager.set_config_path(path):
                self.config_path_label.setText(f"当前路径： {path}")
                # 重新加载配置列表
                self.main_window.load_config_list()
    
    def delete_custom_theme(self):
        """删除自定义主题"""
        # 获取当前选中的主题
        if self.current_theme in ["light", "dark"]:
            # 不能删除默认主题
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_window, "警告", "无法删除默认主题")
            return
        
        # 确认删除
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.main_window, 
            "确认删除", 
            f"确定要删除主题 '{self.themes[self.current_theme]['name']}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除主题文件
            theme_file = os.path.join(self.themes_folder, f"{self.current_theme}.json")
            try:
                if os.path.exists(theme_file):
                    os.remove(theme_file)
                
                # 从主题列表中移除
                del self.themes[self.current_theme]
                
                # 移除对应的单选按钮
                for button in self.theme_group.buttons():
                    if button.text() == self.themes.get(self.current_theme, {}).get("name", ""):
                        self.theme_selection_layout.removeWidget(button)
                        button.deleteLater()
                        self.theme_group.removeButton(button)
                        break
                
                # 切换到默认主题
                self.current_theme = "light"
                self.light_theme_radio.setChecked(True)
                self.apply_theme()
                self.save_theme_setting()
                self.update_theme_preview()
                
            except Exception as e:
                QMessageBox.critical(self.main_window, "错误", f"删除主题失败: {e}")