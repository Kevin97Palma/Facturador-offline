@echo off
setlocal EnableDelayedExpansion
title Facturador — Build

echo.
echo  =====================================================
echo   FACTURADOR ELECTRONICO — COMPILACION AUTOMATICA
echo  =====================================================
echo.

cd /d "%~dp0"

:: ─── 1. Verificar Python ──────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no encontrado. Instale Python 3.11+ desde python.org
    pause & exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python %PYVER%

:: ─── 2. Instalar/actualizar dependencias ─────────────────────────────────────
echo.
echo  [1/4] Instalando dependencias...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo  [ERROR] Fallo la instalacion de dependencias
    pause & exit /b 1
)
echo  [OK] Dependencias instaladas

:: ─── 3. Limpiar build anterior ───────────────────────────────────────────────
echo.
echo  [2/4] Limpiando build anterior...
if exist "build"         rmdir /s /q "build"
if exist "dist\Facturador" rmdir /s /q "dist\Facturador"

:: ─── 4. PyInstaller ──────────────────────────────────────────────────────────
echo.
echo  [3/4] Compilando con PyInstaller (puede tardar 2-5 minutos)...
python -m PyInstaller facturador.spec --clean --noconfirm
if errorlevel 1 (
    echo  [ERROR] PyInstaller fallo. Revise los mensajes de arriba.
    pause & exit /b 1
)
echo  [OK] EXE generado en: dist\Facturador\Facturador.exe

:: ─── 5. Inno Setup (opcional) ─────────────────────────────────────────────────
echo.
echo  [4/4] Buscando Inno Setup para crear instalador...

set INNO=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set INNO="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set INNO="C:\Program Files\Inno Setup 6\ISCC.exe"

if %INNO%=="" (
    echo  [AVISO] Inno Setup no encontrado.
    echo          Para crear el instalador .exe descargue Inno Setup 6 de:
    echo          https://jrsoftware.org/isdl.php
    echo          Luego ejecute:  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    echo.
    echo  El EXE portable ya esta listo en: dist\Facturador\
    goto :done
)

echo  [OK] Inno Setup encontrado. Generando instalador...
%INNO% installer.iss
if errorlevel 1 (
    echo  [ERROR] Inno Setup fallo.
    goto :done
)
echo  [OK] Instalador generado: dist\Facturador_Setup_v1.0.0.exe

:done
echo.
echo  =====================================================
echo   BUILD COMPLETADO
echo.
echo   Archivos generados:
if exist "dist\Facturador\Facturador.exe" (
    echo     EXE portable  : dist\Facturador\Facturador.exe
)
if exist "dist\Facturador_Setup_v1.0.0.exe" (
    echo     Instalador    : dist\Facturador_Setup_v1.0.0.exe
)
echo.
echo   Credenciales iniciales:
echo     Usuario   : admin@sistema.com
echo     Contrasena: Admin2024#
echo  =====================================================
echo.
pause
