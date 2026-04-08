@echo off
cd /d "%~dp0"
pyinstaller --onefile --windowed --add-data "background;background" --add-data "data;data" FD-TC-D.py
pause