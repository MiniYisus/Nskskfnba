@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo   NBA ANALYTICS 2026-27 - INSTALACION
echo ==========================================
where py >nul 2>nul
if %errorlevel%==0 (
    py -3.12 -m venv .venv 2>nul
)
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
    echo No se pudo crear el entorno virtual. Instala Python 3.12 y vuelve a intentar.
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto error
pip install -r requirements.txt
if errorlevel 1 goto error
if not exist ".env" copy .env.example .env >nul
python main.py init
if errorlevel 1 goto error
echo.
echo Instalacion terminada. Ejecuta test_sync.bat para una prueba controlada.
pause
exit /b 0
:error
echo.
echo Hubo un error durante la instalacion. Revisa el mensaje anterior.
pause
exit /b 1
