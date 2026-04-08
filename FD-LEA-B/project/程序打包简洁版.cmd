@echo off
cd /d "%~dp0"
pyinstaller --onefile --windowed --add-data "background/*;background" FD-LEA-B.py
pause