@echo off
chcp 65001 > nul
echo ========================================
echo    FD-MGS-A 光谱分析系统 打包工具
echo ========================================
echo.

REM 检查Python版本
echo [1/6] 检查Python版本...
python --version
if %errorlevel% neq 0 (
    echo ❌ 错误：未找到Python，请确保Python 3.8.9已安装并添加到PATH
    pause
    exit /b 1
)
echo ✓ Python已找到
echo.

REM 检查依赖包
echo [2/6] 检查依赖包安装情况...
python -c "import PyQt5" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ PyQt5未安装，正在安装依赖...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo ✓ PyQt5已安装
)

python -c "import serial" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ pyserial未安装，正在安装...
    pip install pyserial -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    echo ✓ pyserial已安装
)

python -c "import matplotlib" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ matplotlib未安装，正在安装...
    pip install matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    echo ✓ matplotlib已安装
)

python -c "import numpy" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ numpy未安装，正在安装...
    pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    echo ✓ numpy已安装
)
echo.

REM 检查PyInstaller
echo [3/6] 检查PyInstaller...
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ PyInstaller未安装，正在安装...
    pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo ❌ PyInstaller安装失败
        pause
        exit /b 1
    )
) else (
    echo ✓ PyInstaller已安装
)
echo.

REM 清理旧的构建文件
echo [4/6] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo ✓ 清理完成
echo.

REM 开始打包
echo [5/6] 开始打包（这可能需要几分钟）...
echo ------------------------------------------------
pyinstaller --clean FD_MGS_A.spec
if %errorlevel% neq 0 (
    echo ❌ 打包失败！
    echo.
    echo 可能的原因：
    echo 1. Python版本不兼容（需要3.8.9）
    echo 2. 依赖包版本冲突
    echo 3. 内存不足
    echo.
    pause
    exit /b 1
)
echo ✓ 打包完成
echo.

REM 检查生成的文件
echo [6/6] 验证生成的文件...
if exist "dist\FD-MGS-A.exe" (
    echo ✓ EXE文件已生成成功
    echo.
    echo ========================================
    echo ✅ 打包完成！
    echo ========================================
    echo.
    echo 生成的文件位置：
    echo   %CD%\dist\FD-MGS-A.exe
    echo.
    
    REM 获取文件大小
    for %%A in ("dist\FD-MGS-A.exe") do (
        set size=%%~zA
        set /a sizeMB=%%~zA/1024/1024
    )
    echo 文件大小：约 %sizeMB% MB
    echo.
    
    REM 复制必要文件到dist目录
    echo 正在复制必要文件到dist目录...
    copy "README.md" "dist\" > nul 2>&1
    copy "问题修复总结.txt" "dist\" > nul 2>&1
    echo ✓ 文件复制完成
    echo.
    
    echo 使用说明：
    echo 1. 直接运行 dist\FD-MGS-A.exe 即可启动程序
    echo 2. 可以将整个dist文件夹复制到其他电脑使用
    echo 3. 目标电脑无需安装Python或任何依赖
    echo.
    
    REM 询问是否运行
    echo 是否立即运行程序进行测试？
    choice /C YN /M "请选择 (Y=是, N=否)"
    if %errorlevel% equ 1 (
        echo.
        echo 正在启动程序...
        start "" "dist\FD-MGS-A.exe"
    )
) else (
    echo ❌ 错误：未找到生成的EXE文件
    echo 请检查build目录中的错误日志
)

echo.
echo 按任意键退出...
pause > nul


