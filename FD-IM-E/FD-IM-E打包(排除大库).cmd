@echo off
cd /d "%~dp0"
pyinstaller -F --clean --noconfirm --noconsole ^
    --exclude-module torch ^
    --exclude-module torchvision ^
    --exclude-module tensorflow ^
    --exclude-module scipy ^
    --exclude-module matplotlib ^
    --exclude-module PyQt5 ^
    --exclude-module boto3 ^
    --exclude-module botocore ^
    --exclude-module Django ^
    --exclude-module flask ^
    --exclude-module opencv-python ^
    --exclude-module pygame ^
    --hidden-import openpyxl ^
    --hidden-import pandas ^
    --hidden-import numpy ^
    --add-data "background;background" ^
    FD-IM-E.py
pause