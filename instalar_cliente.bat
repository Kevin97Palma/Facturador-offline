@echo off
echo ============================================
echo  INSTALACION - FACTURADOR CLIENTE
echo ============================================
echo.

cd /d "%~dp0"

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado.
    pause
    exit /b 1
)

echo Instalando dependencias cliente...
python -m pip install --upgrade pip
python -m pip install PyQt5==5.15.10 requests==2.32.3 python-escpos==3.1 pywin32==306

if errorlevel 1 (
    echo ERROR al instalar dependencias.
    pause
    exit /b 1
)

echo.
echo Configurando modo cliente...
python -c "import json; cfg={}; cfg['mode']='cliente'; cfg['server_url']='http://SERVIDOR_IP:5000'; open('config.json','w').write(json.dumps(cfg,indent=2))"

echo.
echo ============================================
echo  INSTALACION COMPLETADA
echo  Edite config.json y cambie SERVIDOR_IP
echo  por la IP del equipo servidor.
echo ============================================
pause
