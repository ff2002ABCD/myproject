cd /d "C:\Users\chnxjang\Desktop\past project\FD-UI-D\project"
pyinstaller --onefile --windowed --add-data "data/*;data" --add-data "background/*;background" FD-UI-D.py
pause