@echo off
echo Compilando Facturador.exe con PyInstaller...
cd /d "%~dp0"
python -m pip install pyinstaller
pyinstaller facturador.spec --clean
echo.
echo EXE generado en: dist\Facturador.exe
pause
