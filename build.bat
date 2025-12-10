@echo off
chcp 65001 >nul
echo ========================================
echo WindowSizer 自动打包脚本
echo ========================================
echo.

echo [1/5] 检查 PyInstaller 是否已安装...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller 未安装，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo 错误：PyInstaller 安装失败！
        pause
        exit /b 1
    )
) else (
    echo PyInstaller 已安装
)
echo.

echo [2/5] 检查依赖库是否已安装...
python -c "import PyQt5, win32gui, psutil" 2>nul
if errorlevel 1 (
    echo 依赖库缺失，正在安装...
    pip install PyQt5 pywin32 psutil
    if errorlevel 1 (
        echo 错误：依赖库安装失败！
        pause
        exit /b 1
    )
) else (
    echo 依赖库已安装
)
echo.

echo [3/5] 清理旧的打包文件...
if exist "dist" (
    rmdir /s /q dist
    echo 已删除 dist 目录
)
if exist "build" (
    rmdir /s /q build
    echo 已删除 build 目录
)
if exist "WindowSizer.spec" (
    del /q WindowSizer.spec
    echo 已删除旧的 spec 文件
)
echo.

echo [4/5] 开始打包...
pyinstaller build.spec
if errorlevel 1 (
    echo 错误：打包失败！
    pause
    exit /b 1
)
echo.

echo [5/5] 打包完成！
echo.
echo ========================================
echo 打包结果：
echo ========================================
if exist "dist\WindowSizer.exe" (
    echo ✓ EXE 文件已生成：dist\WindowSizer.exe
    for %%A in (dist\WindowSizer.exe) do echo ✓ 文件大小：%%~zA 字节
) else (
    echo ✗ EXE 文件生成失败！
    pause
    exit /b 1
)
echo.

echo ========================================
echo 后续步骤：
echo ========================================
echo 1. 测试 EXE 文件：dist\WindowSizer.exe
echo 2. 检查所有功能是否正常
echo 3. 如需发布，请参考 BUILD.md 文档
echo ========================================
echo.
pause
