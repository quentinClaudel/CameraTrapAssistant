@echo off
title Camera Trap Assistant - Run from Source
setlocal

set "APP_NAME=CameraTrap Assistant"
set "PROJECT_ROOT=%~dp0"
set "DEV_DIR=%PROJECT_ROOT%dev"
set "CTA_DIR=%PROJECT_ROOT%CameraTrapAssistant"
set "VENV_PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"

echo ======================================================
echo   %APP_NAME% - Run from Source
echo ======================================================
echo.

if not exist "%CTA_DIR%" (
    echo CameraTrapAssistant folder not found.
    pause
    exit /b 1
)

if not exist "%VENV_PYTHON%" (
    echo Source environment not found. Running setup...
    echo.
    call "%DEV_DIR%\setup.bat"
    if errorlevel 1 (
        echo Source environment setup failed.
        pause
        exit /b 1
    )
)

echo Source environment found. Launching application...
echo.
call "%DEV_DIR%\run.bat"
