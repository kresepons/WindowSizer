import os
import win32gui
import win32process
import psutil
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt

# 尝试导入QtWinExtras
try:
    from PyQt5.QtWinExtras import QtWin
    QTWIN_AVAILABLE = True
except ImportError:
    QTWIN_AVAILABLE = False


class WindowManager:
    """窗口管理类，负责所有窗口相关的操作"""
    
    def __init__(self):
        self.window_icon_cache = {}  # 缓存窗口图标
    
    def get_window_list(self):
        """获取所有窗口列表"""
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                rect = win32gui.GetWindowRect(hwnd)
                if rect[2] - rect[0] > 100 and rect[3] - rect[1] > 100:  # 过滤掉太小的窗口
                    # 获取窗口类名
                    class_name = win32gui.GetClassName(hwnd)
                    
                    # 获取进程信息
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        process = psutil.Process(pid)
                        process_name = process.name()
                    except:
                        process_name = "Unknown"
                    
                    # 获取窗口图标
                    icon = self.get_window_icon(hwnd, class_name, process_name)
                    
                    windows.append({
                        "hwnd": hwnd,
                        "title": win32gui.GetWindowText(hwnd),
                        "class_name": class_name,
                        "process_name": process_name,
                        "pid": pid,
                        "rect": rect,
                        "icon": icon
                    })
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows
    
    def get_window_icon(self, hwnd, class_name, process_name):
        """获取窗口的系统原生图标"""
        # 先尝试从缓存获取
        cache_key = f"{hwnd}_{process_name}"
        if cache_key in self.window_icon_cache:
            return self.window_icon_cache[cache_key]
        
        icon = None
        hicon = 0
        
        # 尝试从窗口获取图标
        try:
            # 方法1: 获取大图标
            hicon = win32gui.SendMessage(hwnd, 0x007F, 1, 0)  # WM_GETICON, ICON_BIG
            
            if not hicon:
                # 方法2: 获取小图标
                hicon = win32gui.SendMessage(hwnd, 0x007F, 0, 0)  # WM_GETICON, ICON_SMALL
            
            if not hicon:
                # 方法3: 从类获取图标
                try:
                    hicon = win32gui.GetClassLong(hwnd, -14)  # GCL_HICON
                except:
                    pass
            
            if not hicon:
                # 方法4: 尝试获取小类图标
                try:
                    hicon = win32gui.GetClassLong(hwnd, -34)  # GCL_HICONSM
                except:
                    pass
            
            # 如果获取到了图标句柄，转换为QIcon
            if hicon:
                icon = self._hicon_to_qicon(hicon)
                if icon and not icon.isNull():
                    self.window_icon_cache[cache_key] = icon
                    return icon
        except Exception:
            pass  # 静默忽略错误
        
        # 方法5: 尝试从进程可执行文件获取图标
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            exe_path = process.exe()
            
            if exe_path and os.path.exists(exe_path):
                # 使用shell32.dll提取图标
                import ctypes
                from ctypes import wintypes
                
                shell32 = ctypes.windll.shell32
                # ExtractIconEx原型: UINT ExtractIconEx(LPCTSTR lpszFile, int nIconIndex, HICON *phiconLarge, HICON *phiconSmall, UINT nIcons)
                large_icons = (wintypes.HICON * 1)()
                small_icons = (wintypes.HICON * 1)()
                
                num_icons = shell32.ExtractIconExW(exe_path, 0, large_icons, small_icons, 1)
                
                if num_icons > 0 and large_icons[0]:
                    hicon = large_icons[0]
                    icon = self._hicon_to_qicon(hicon)
                    # 销毁图标句柄
                    win32gui.DestroyIcon(large_icons[0])
                    if small_icons[0]:
                        win32gui.DestroyIcon(small_icons[0])
                    
                    if icon and not icon.isNull():
                        self.window_icon_cache[cache_key] = icon
                        return icon
        except Exception:
            pass  # 静默忽略错误
        
        # 如果所有方法都失败，返回空图标
        return QIcon()
    
    def _hicon_to_qicon(self, hicon):
        """将Windows图标句柄转换为QIcon"""
        # 优先使用QtWin（如果可用）
        if QTWIN_AVAILABLE:
            try:
                pixmap = QtWin.fromHICON(hicon)
                if not pixmap.isNull():
                    return QIcon(pixmap)
            except Exception:
                pass  # 静默忽略错误
        
        # 备用方法: 使用win32ui
        try:
            import win32ui
            import win32con
            
            # 创建设备上下文
            desktop_dc = win32gui.GetDC(0)
            hdc = win32ui.CreateDCFromHandle(desktop_dc)
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, 32, 32)
            
            # 创建兼容DC
            hdc_compatible = hdc.CreateCompatibleDC()
            hdc_compatible.SelectObject(hbmp)
            
            # 绘制图标
            hdc_compatible.DrawIcon((0, 0), hicon)
            
            # 获取位图数据
            bmpinfo = hbmp.GetInfo()
            bmpstr = hbmp.GetBitmapBits(True)
            
            # 创建QImage
            img = QImage(bmpstr, bmpinfo['bmWidth'], bmpinfo['bmHeight'], QImage.Format_RGB32)
            
            # 清理资源
            win32gui.DeleteObject(hbmp.GetHandle())
            hdc_compatible.DeleteDC()
            win32gui.ReleaseDC(0, desktop_dc)
            
            if not img.isNull():
                return QIcon(QPixmap.fromImage(img))
        except Exception:
            pass  # 静默忽略错误
        
        # 所有方法都失败
        return QIcon()
    

    
    def resize_window(self, hwnd, x, y, width, height):
        """调整窗口大小和位置。返回 (success, error_message)"""
        try:
            import win32con
            # 使用 SWP_NOZORDER | SWP_NOACTIVATE 避免干扰窗口层级和激活状态
            flags = win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            win32gui.SetWindowPos(hwnd, None, x, y, width, height, flags)
            return True, None
        except Exception as e:
            # 检查是否为权限错误
            error_msg = str(e)
            if "5" in error_msg or "拒绝访问" in error_msg or "Access is denied" in error_msg:
                return False, "权限不足：目标窗口可能以管理员权限运行，请以管理员身份运行 WindowSizer"
            else:
                return False, f"调整窗口失败：{error_msg}"
    
    def get_window_rect(self, hwnd):
        """获取窗口矩形区域"""
        try:
            return win32gui.GetWindowRect(hwnd)
        except:
            return None
    
    def is_window_valid(self, hwnd):
        """检查窗口是否仍然有效"""
        try:
            return win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd)
        except:
            return False
    
    def get_window_info(self, hwnd):
        """获取窗口详细信息"""
        try:
            if not self.is_window_valid(hwnd):
                return None
                
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except:
                process_name = "Unknown"
            
            return {
                "hwnd": hwnd,
                "title": title,
                "class_name": class_name,
                "process_name": process_name,
                "pid": pid,
                "rect": rect
            }
        except Exception:
            return None