@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Primero ejecuta setup_windows.bat
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat
python main.py sync
pause
