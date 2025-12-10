"""
WindowSizer 窗口诊断工具
用于诊断特定进程的窗口配置问题
"""

import win32gui
import win32process
import win32con
import psutil
import ctypes

def diagnose_window_by_pid(target_pid):
    """诊断指定PID的窗口"""
    print(f"\n{'='*60}")
    print(f"诊断 PID: {target_pid}")
    print(f"{'='*60}")
    
    # 获取进程信息
    try:
        process = psutil.Process(target_pid)
        print(f"进程名称: {process.name()}")
        print(f"可执行文件: {process.exe()}")
        print(f"进程状态: {process.status()}")
    except Exception as e:
        print(f"无法获取进程信息: {e}")
        return
    
    # 查找该进程的所有窗口
    def enum_callback(hwnd, windows):
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid == target_pid:
            windows.append(hwnd)
        return True
    
    windows = []
    win32gui.EnumWindows(enum_callback, windows)
    
    print(f"\n找到 {len(windows)} 个窗口句柄")
    
    for i, hwnd in enumerate(windows, 1):
        print(f"\n窗口 {i}:")
        print(f"  句柄 (HWND): {hwnd}")
        
        # 窗口标题
        try:
            title = win32gui.GetWindowText(hwnd)
            print(f"  标题: {title if title else '(无标题)'}")
        except Exception as e:
            print(f"  标题: 获取失败 - {e}")
        
        # 窗口类名
        try:
            class_name = win32gui.GetClassName(hwnd)
            print(f"  类名: {class_name}")
        except Exception as e:
            print(f"  类名: 获取失败 - {e}")
        
        # 窗口可见性
        try:
            is_visible = win32gui.IsWindowVisible(hwnd)
            print(f"  可见: {is_visible}")
        except Exception as e:
            print(f"  可见: 获取失败 - {e}")
        
        # 窗口位置和大小
        try:
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            print(f"  位置: x={rect[0]}, y={rect[1]}")
            print(f"  大小: width={width}, height={height}")
            print(f"  矩形: {rect}")
        except Exception as e:
            print(f"  位置/大小: 获取失败 - {e}")
        
        # 窗口样式
        try:
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            print(f"  样式 (GWL_STYLE): 0x{style:08X}")
            print(f"  扩展样式 (GWL_EXSTYLE): 0x{ex_style:08X}")
            
            # 检查特殊样式
            if style & win32con.WS_POPUP:
                print(f"    - WS_POPUP (弹出窗口)")
            if style & win32con.WS_CHILD:
                print(f"    - WS_CHILD (子窗口)")
            if style & win32con.WS_MAXIMIZE:
                print(f"    - WS_MAXIMIZE (最大化)")
            if style & win32con.WS_MINIMIZE:
                print(f"    - WS_MINIMIZE (最小化)")
            if ex_style & win32con.WS_EX_TOPMOST:
                print(f"    - WS_EX_TOPMOST (总在最前)")
            if ex_style & win32con.WS_EX_TOOLWINDOW:
                print(f"    - WS_EX_TOOLWINDOW (工具窗口)")
        except Exception as e:
            print(f"  样式: 获取失败 - {e}")
        
        # 父窗口
        try:
            parent = win32gui.GetParent(hwnd)
            if parent:
                print(f"  父窗口: {parent}")
            else:
                print(f"  父窗口: 无")
        except Exception as e:
            print(f"  父窗口: 获取失败 - {e}")
        
        # 测试设置窗口位置
        print(f"\n  测试调整窗口位置...")
        try:
            # 获取当前位置
            current_rect = win32gui.GetWindowRect(hwnd)
            test_x = current_rect[0]
            test_y = current_rect[1]
            test_width = current_rect[2] - current_rect[0]
            test_height = current_rect[3] - current_rect[1]
            
            # 尝试设置相同的位置（不应该有变化）
            result = win32gui.SetWindowPos(
                hwnd, None, 
                test_x, test_y, 
                test_width, test_height, 
                0
            )
            
            # 验证设置是否成功
            new_rect = win32gui.GetWindowRect(hwnd)
            if new_rect == current_rect:
                print(f"    ✓ SetWindowPos 调用成功")
            else:
                print(f"    ⚠ 窗口位置已改变")
                print(f"      原位置: {current_rect}")
                print(f"      新位置: {new_rect}")
            
            # 测试使用不同的标志
            print(f"\n  测试不同的SetWindowPos标志...")
            flags_to_test = [
                (0, "SWP_NOZORDER"),
                (win32con.SWP_NOACTIVATE, "SWP_NOACTIVATE"),
                (win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE, "SWP_NOZORDER | SWP_NOACTIVATE"),
            ]
            
            for flags, desc in flags_to_test:
                try:
                    win32gui.SetWindowPos(
                        hwnd, None,
                        test_x, test_y,
                        test_width, test_height,
                        flags
                    )
                    print(f"    ✓ {desc}: 成功")
                except Exception as e:
                    print(f"    ✗ {desc}: 失败 - {e}")
                    
        except Exception as e:
            print(f"    ✗ SetWindowPos 失败: {e}")

def main():
    """主函数"""
    print("WindowSizer 窗口诊断工具")
    print("="*60)
    
    # 需要诊断的PID
    target_pids = [53276, 57340]
    
    for pid in target_pids:
        try:
            diagnose_window_by_pid(pid)
        except Exception as e:
            print(f"\n诊断 PID {pid} 时出错: {e}")
    
    print(f"\n{'='*60}")
    print("诊断完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
