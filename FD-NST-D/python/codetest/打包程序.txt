cd /d "C:\Users\chnxjang\Desktop\past project\FD-NST-D\python\codetest"
pyinstaller --onefile --add-data "data/*;data" --add-data "FD_NST_D.cp313-win_amd64.pyd;." FD-NST-D.py
pause