import os
import json
import time
import re
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QSettings


class ConfigManager:
    """配置管理类，负责所有配置相关的操作"""
    
    @staticmethod
    def sanitize_filename(filename):
        """将字符串转换为合法的文件名
        
        Args:
            filename: 原始文件名字符串
            
        Returns:
            合法的文件名字符串
        """
        # 移除或替换Windows文件名中的非法字符: < > : " / \ | ? *
        # 同时移除控制字符和其他特殊字符
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        # 移除首尾空格和点
        sanitized = sanitized.strip('. ')
        # 限制长度（Windows路径限制，留出余量）
        max_length = 100
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        # 如果结果为空，返回默认名称
        return sanitized if sanitized else 'unnamed'
    
    def __init__(self):
        self.configs = []
        # 从设置中加载配置文件路径
        settings = QSettings("WindowSizer", "Settings")
        self.config_path = settings.value("config_path", ".")
        # 确保配置目录存在
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
        self.config_file = os.path.join(self.config_path, "window_configs.json")
        # 创建图标保存文件夹
        self.icons_folder = os.path.join(self.config_path, "config_icons")
        if not os.path.exists(self.icons_folder):
            os.makedirs(self.icons_folder)
        self.load_configs()
    
    def set_config_path(self, path):
        """设置配置文件路径"""
        if not path or not os.path.exists(path):
            return False
        self.config_path = path
        self.config_file = os.path.join(self.config_path, "window_configs.json")
        # 创建图标保存文件夹
        self.icons_folder = os.path.join(self.config_path, "config_icons")
        if not os.path.exists(self.icons_folder):
            os.makedirs(self.icons_folder)
        # 保存路径到设置
        settings = QSettings("WindowSizer", "Settings")
        settings.setValue("config_path", path)
        # 重新加载配置
        self.load_configs()
        return True
    
    def get_config_path(self):
        """获取配置文件路径"""
        return self.config_path
    
    def load_configs(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.configs = json.load(f)
            else:
                self.configs = []
        except Exception:
            self.configs = []
    
    def save_configs(self):
        """保存配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.configs, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def add_config(self, config, icon=None, class_name=None):
        """添加配置
        
        Args:
            config: 配置字典，必须包含 title, process, x, y, width, height
            icon: QIcon对象（可选）
            class_name: 窗口类名（可选，用于区分同一进程的不同窗口）
            
        Returns:
            (success, message) 元组
        """
        # 检查是否已存在相同的配置
        for existing_config in self.configs:
            if (existing_config.get("title") == config.get("title") and 
                existing_config.get("process") == config.get("process")):
                return False, "已存在相同窗口的配置"
        
        # 添加时间戳
        config["created_at"] = time.time()
        config["updated_at"] = time.time()
        
        # 保存图标（使用配置名称命名）
        if icon and not icon.isNull():
            # 获取配置名称（优先使用自定义名称，否则使用默认名称）
            config_name = config.get("custom_name", f"{config['title']} - {config['process']}")
            icon_filename = self.save_icon(
                config_name, 
                icon, 
                class_name=class_name,
                window_title=config.get("title")
            )
            if icon_filename:
                config["icon_file"] = icon_filename
        
        # 默认激活状态
        config["enabled"] = True
        
        self.configs.append(config)
        if self.save_configs():
            return True, "配置添加成功"
        else:
            self.configs.pop()  # 回滚
            return False, "保存配置失败"
    
    def update_config(self, index, config):
        """更新配置"""
        if 0 <= index < len(self.configs):
            # 更新时间戳
            config["updated_at"] = time.time()
            
            self.configs[index] = config
            return self.save_configs()
        return False
    
    def delete_config(self, index):
        """删除配置"""
        if 0 <= index < len(self.configs):
            self.configs.pop(index)
            return self.save_configs()
        return False
    
    def get_config_by_index(self, index):
        """根据索引获取配置"""
        if 0 <= index < len(self.configs):
            return self.configs[index]
        return None
    
    def get_config_by_window_info(self, title, process):
        """根据窗口信息获取配置"""
        for config in self.configs:
            if config.get("title") == title and config.get("process") == process:
                return config
        return None
    
    def get_all_configs(self):
        """获取所有配置"""
        return self.configs.copy()
    
    def import_configs(self, file_path=None):
        """导入配置"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                None, "导入配置", "", "JSON文件 (*.json)")
            if not file_path:
                return False, "未选择文件"
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                imported_configs = json.load(f)
            
            if not isinstance(imported_configs, list):
                return False, "配置文件格式不正确"
            
            # 备份当前配置
            backup_configs = self.configs.copy()
            
            # 合并配置，避免重复
            for imported_config in imported_configs:
                # 检查是否已存在相同的配置
                exists = False
                for existing_config in self.configs:
                    if (existing_config.get("title") == imported_config.get("title") and 
                        existing_config.get("process") == imported_config.get("process")):
                        exists = True
                        break
                
                if not exists:
                    # 重置时间戳
                    imported_config["created_at"] = time.time()
                    imported_config["updated_at"] = time.time()
                    self.configs.append(imported_config)
            
            if self.save_configs():
                return True, f"成功导入 {len(imported_configs)} 个配置"
            else:
                self.configs = backup_configs  # 回滚
                return False, "保存配置失败"
        except Exception as e:
            self.configs = backup_configs  # 回滚
            return False, f"导入配置失败: {e}"
    
    def export_configs(self, file_path=None):
        """导出配置"""
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                None, "导出配置", "window_configs.json", "JSON文件 (*.json)")
            if not file_path:
                return False, "未选择保存位置"
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.configs, f, ensure_ascii=False, indent=2)
            return True, f"配置已导出到 {file_path}"
        except Exception as e:
            return False, f"导出配置失败: {e}"
    
    def get_configs_count(self):
        """获取配置数量"""
        return len(self.configs)
    
    def filter_configs(self, keyword):
        """过滤配置"""
        if not keyword:
            return self.configs
        
        keyword = keyword.lower()
        filtered = []
        
        for config in self.configs:
            title = config.get("title", "").lower()
            process = config.get("process", "").lower()
            
            if keyword in title or keyword in process:
                filtered.append(config)
        
        return filtered
    
    def get_configs_page(self, configs, page, page_size):
        """获取分页配置"""
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        return configs[start_index:end_index]
    
    def get_page_count(self, configs, page_size):
        """获取总页数"""
        return (len(configs) + page_size - 1) // page_size if configs else 1
    
    def validate_config(self, config):
        """验证配置是否有效"""
        required_fields = ["title", "process", "x", "y", "width", "height"]
        
        for field in required_fields:
            if field not in config:
                return False, f"缺少必要字段: {field}"
        
        # 验证数值字段
        try:
            x = int(config["x"])
            y = int(config["y"])
            width = int(config["width"])
            height = int(config["height"])
            
            if width <= 0 or height <= 0:
                return False, "宽度和高度必须大于0"
        except ValueError:
            return False, "位置和尺寸必须是数字"
        
        return True, "配置有效"
    
    def get_config_history(self, config_index):
        """获取配置历史记录（如果有的话）"""
        # 这里可以实现配置历史记录功能
        # 暂时返回空列表
        return []
    
    def backup_configs(self):
        """备份配置"""
        backup_file = f"{self.config_file}.backup.{int(time.time())}"
        try:
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(self.configs, f, ensure_ascii=False, indent=2)
            return backup_file
        except Exception:
            return None
    
    def restore_configs(self, backup_file):
        """从备份恢复配置"""
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                self.configs = json.load(f)
            return self.save_configs()
        except Exception:
            return False
    
    def save_icon(self, config_name, icon, class_name=None, window_title=None):
        """保存程序图标到本地文件夹
        
        Args:
            config_name: 配置名称（必选，用于命名图标文件）
            icon: QIcon对象（必选）
            class_name: 窗口类名（可选）
            window_title: 窗口标题（可选）
            
        Returns:
            图标文件名，保存失败返回None
        """
        try:
            # 使用配置名称作为图标文件名
            safe_name = self.sanitize_filename(config_name)
            icon_filename = f"{safe_name}.png"
            
            icon_path = os.path.join(self.icons_folder, icon_filename)
            
            # 将QIcon转换为QPixmap并保存
            pixmap = icon.pixmap(32, 32)  # 使用32x32的图标
            if not pixmap.isNull():
                pixmap.save(icon_path, "PNG")
                return icon_filename
        except Exception:
            pass
        return None
    
    def load_icon(self, icon_filename=None, process_name=None, class_name=None, window_title=None):
        """从本地文件加载图标，支持多级回退匹配
        
        Args:
            icon_filename: 直接指定的图标文件名（最高优先级）
            process_name: 进程名（用于回退匹配）
            class_name: 窗口类名（用于精确匹配）
            window_title: 窗口标题（用于精确匹配）
            
        Returns:
            QIcon对象，加载失败返回None
            
        匹配优先级：
            1. 直接指定的icon_filename
            2. 进程名_窗口类名.png
            3. 进程名_窗口标题关键字.png
            4. 进程名.png（通用图标）
        """
        try:
            from PyQt5.QtGui import QIcon
            
            # 尝试加载图标的文件名列表（按优先级排序）
            filenames_to_try = []
            
            # 优先级1：直接指定的图标文件名
            if icon_filename:
                filenames_to_try.append(icon_filename)
            
            # 如果提供了进程名，构建回退匹配列表
            if process_name:
                base_name = process_name.replace('.exe', '')
                
                # 优先级2：进程名_窗口类名
                if class_name:
                    safe_class_name = self.sanitize_filename(class_name)
                    filenames_to_try.append(f"{base_name}_{safe_class_name}.png")
                
                # 优先级3：进程名_窗口标题关键字
                if window_title:
                    title_key = window_title[:30] if len(window_title) > 30 else window_title
                    safe_title_key = self.sanitize_filename(title_key)
                    filenames_to_try.append(f"{base_name}_{safe_title_key}.png")
                
                # 优先级4：进程名通用图标
                filenames_to_try.append(f"{base_name}.png")
            
            # 依次尝试加载每个文件
            for filename in filenames_to_try:
                icon_path = os.path.join(self.icons_folder, filename)
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        return icon
        except Exception:
            pass
        return None