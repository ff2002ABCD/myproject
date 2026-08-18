@echo off
cd /d "%~dp0"

echo 清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo 开始用 spec 文件打包...
pyinstaller FD-TC-D.spec

echo 打包完成！
echo 文件大小：
dir dist\FD-TC-D.exe
pause