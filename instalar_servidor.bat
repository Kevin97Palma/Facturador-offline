@echo off
echo ============================================
echo  INSTALACION - FACTURADOR SERVIDOR
echo ============================================
echo.

cd /d "%~dp0"

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH.
    echo Descargue Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Instalando dependencias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR al instalar dependencias.
    pause
    exit /b 1
)

echo.
echo Inicializando base de datos...
python -c "from server.database.db import init_db; from server.main import create_app; app = create_app()"

echo.
echo ============================================
echo  INSTALACION COMPLETADA
echo  Usuario inicial: admin@sistema.com
echo  Contrasena: Admin2024#
echo ============================================
echo.
pause
