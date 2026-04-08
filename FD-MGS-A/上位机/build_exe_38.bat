@echo off
chcp 65001 >nul
echo ========================================
echo FD-MGS-A 光谱分析系统 - 打包脚本
echo 使用 Python 3.8.9 (32位)
echo ========================================
echo.

REM 设置Python 3.8.9的路径
set PYTHON38=C:\Users\34487\AppData\Local\Programs\Python\Python38-32\python.exe

REM 检查Python是否存在
if not exist "%PYTHON38%" (
    echo [错误] 未找到 Python 3.8.9
    echo 请检查路径: %PYTHON38%
    echo.
    echo 如果Python安装在其他位置，请修改此批处理文件中的PYTHON38变量
    pause
    exit /b 1
)

echo [1/3] 检查Python版本...
"%PYTHON38%" --version
echo.

echo [2/3] 运行打包脚本...
"%PYTHON38%" build_exe.py
if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 生成的文件位置: dist\FD-MGS-A.exe
echo.
pause












