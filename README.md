# WindowSizer - 窗口大小调整工具

<p align="center">
  <img src="resources/app_icon.png" alt="WindowSizer Logo" width="128" height="128">
</p>

<p align="center">
  <strong>一个功能强大的Windows窗口管理工具，让你轻松保存和应用窗口的大小和位置配置</strong>
</p>

---

## 📌 目录

- [功能特性](#-功能特性)
- [系统要求](#-系统要求)
- [安装方法](#-安装方法)
- [使用指南](#-使用指南)
- [配置文件](#-配置文件)
- [快捷键](#-快捷键)
- [项目结构](#-项目结构)
- [技术栈](#-技术栈)
- [常见问题](#-常见问题)

---

## ✨ 功能特性

### 核心功能

- 💾 **配置管理**
  - 保存任意窗口的位置、大小配置
  - 支持配置重命名、启用/禁用
  - 自动保存程序图标
  - 导入/导出配置文件

- 🎨 **主题系统**
  - 内置浅色/深色主题，适配Windows 11
  - 支持自定义主题创建
  - 可视化主题编辑器
  - 主题导入/导出/删除

- ⚙️ **系统集成**
  - 系统托盘集成，最小化到托盘
  - 开机自启动支持
  - 自定义配置文件保存路径
  - 进程唯一性检查

- 🚀 **快速操作**
  - 一键应用单个配置
  - 一键应用所有配置
  - 自动应用配置（后台监测）
  - 快捷键支持

---

## 💻 系统要求

- **操作系统**: Windows 10/11
- **Python版本**: Python 3.7+（仅源码运行需要）
- **屏幕分辨率**: 推荐1920x1080或更高

---

## 📦 安装方法

### 方法1：使用打包好的EXE文件（推荐）

1. 下载 `WindowSizer.exe`
2. 双击运行即可，无需安装Python环境

### 方法2：从源码运行

1. **克隆或下载项目**
   ```bash
   git clone https://github.com/yourusername/WindowSizer.git
   cd WindowSizer
   ```

2. **安装依赖库**
   ```bash
   pip install PyQt5 pywin32 psutil
   ```

3. **运行程序**
   ```bash
   python run.py
   ```
   或
   ```bash
   python main.py
   ```

---

## 📖 使用指南

### 第一步：创建窗口配置

1. **打开程序**，点击主界面的“新增配置”按钮
2. **选择目标窗口**：从窗口列表中选择你想要管理的窗口
3. **调整位置和大小**：
   - 可以手动输入X/Y位置和宽度/高度
   - 或者直接拖拽窗口到想要的位置和大小
4. **点击“保存配置”**

### 第二步：应用配置

- **应用单个配置**：在配置列表中选中配置，点击“应用配置”
- **一键应用所有**：点击“一键应用”按钮，自动应用所有启用的配置
- **自动应用**：在设置中启用“自动应用配置”，程序会后台监测并自动应用配置

### 第三步：配置管理

- **重命名配置**：点击配置列表中的“重命名”按钮
- **启用/禁用配置**：勾选或取消配置列表中的复选框
- **删除配置**：选中配置后点击“删除配置”按钮

### 主题自定义

1. **切换到“主题”标签页**
2. **选择内置主题**：浅色/深色主题
3. **创建自定义主题**：
   - 点击“添加新主题”
   - 设置主题名称和颜色
   - 点击颜色方块选择颜色
   - 保存主题

---

## 📁 配置文件

### window_configs.json

存储所有窗口配置信息：

```json
[
  {
    "title": "窗口标题",
    "process": "进程名.exe",
    "x": 100,
    "y": 100,
    "width": 1920,
    "height": 1080,
    "enabled": true,
    "custom_name": "自定义名称",
    "icon_file": "process.png"
  }
]
```

### ui_config.json

存储UI配置和主题设置：

```json
{
  "themes_folder": "themes",
  "default_theme": "light",
  "icon_paths": {
    "app_icon": "resources/icon.png",
    "tray_icon": "resources/icon.png"
  }
}
```

### 主题文件（themes/）

每个主题为一个JSON文件：

```json
{
  "name": "主题名称",
  "background": "#f3f3f3",
  "window": "#ffffff",
  "border": "#d1d1d1",
  "button": "#005fb8",
  "button_hover": "#0078d4"
}
```

---

## ⌨️ 快捷键

| 快捷键 | 功能 |
|----------|------|
| `Ctrl + S` | 保存当前配置 |
| `Ctrl + A` | 应用当前配置 |
| `Ctrl + Shift + A` | 一键应用所有配置 |
| `F5` | 刷新窗口列表 |
| `Ctrl + M` | 显示/隐藏主窗口 |

---

## 📜 项目结构

```
WindowSizer/
├── main.py                # 主程序入口，整合所有模块
├── ui.py                  # UI界面管理，布局和主题系统
├── window_manager.py      # 窗口操作核心功能
├── config_manager.py      # 配置持久化管理
├── run.py                 # 启动脚本
├── resources/             # 资源文件夹
│   ├── app_icon.ico       # 应用程序图标（ICO格式）
│   ├── icon.png           # 程序主图标
│   ├── btn_*.png          # 各种按钮图标
│   └── power.png          # 退出图标
├── themes/                # 主题文件夹
│   ├── light.json         # 浅色主题
│   └── dark.json          # 深色主题
├── config_icons/          # 程序图标缓存文件夹
├── window_configs.json    # 窗口配置数据
├── config.json            # 应用设置
└── ui_config.json         # UI配置和主题设置
```

---

## 🛠️ 技术栈

- **开发语言**: Python 3.7+
- **GUI框架**: PyQt5
- **Windows API**: pywin32
- **进程管理**: psutil
- **配置存储**: JSON

---

## ❓ 常见问题

### 1. 程序启动后看不到窗口？

- 程序启动后会最小化到系统托盘，右键点击托盘图标选择“显示/隐藏主界面”
- 可在设置中修改关闭行为为“完全关闭”

### 2. 配置不生效？

- 确保配置已启用（配置列表中的复选框已勾选）
- 检查目标窗口是否存在，窗口标题和进程名是否匹配
- 尝试手动点击“应用配置”按钮

### 3. 如何备份配置？

- 点击设置页面的“导出配置”按钮，选择保存位置
- 或者直接复制 `window_configs.json` 文件

### 4. 如何卸载程序？

- **EXE版本**：直接删除程序文件夹
- **源码版本**：删除项目文件夹
- 配置文件默认存储在程序目录下，一并删除即可

### 5. 支持多显示器吗？

- 是的，WindowSizer 完全支持多显示器配置
- 可以为不同显示器上的窗口创建不同的配置

---

## 💬 联系方式

- **网站**: [https://yourwebsite.com](https://yourwebsite.com)
- **问题反馈**: [GitHub Issues](https://github.com/yourusername/WindowSizer/issues)
- **邮箱**: your.email@example.com

---

## 📝 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🚀 更新记录

### v1.0.0 (2025-01-15)

- ✅ 初始发布
- ✅ 窗口配置管理功能
- ✅ 主题系统支持
- ✅ 系统托盘集成
- ✅ 开机自启动
- ✅ 配置导入/导出
- ✅ 快捷键支持

---

<p align="center">
  <strong>感谢使用 WindowSizer！</strong>
</p>