@echo off
cd /d "%~dp0"
python app.py
if errorlevel 1 (
    echo.
    echo ERROR al iniciar la aplicacion. Verifique los logs.
    pause
)
