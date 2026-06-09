@echo off
echo Iniciando servidor API Facturador en puerto 5000...
cd /d "%~dp0"
python -c "from server.main import run_server; run_server('0.0.0.0', 5000)"
pause
