@echo off
cd /d "%~dp0"
pyinstaller --onefile --windowed --add-data "data/*;data" --add-data "background/*;background" FD-NCE-II.py
pause