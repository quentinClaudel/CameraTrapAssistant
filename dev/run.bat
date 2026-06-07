@echo off
title Camera Trap Assistant - Source Launcher
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "CTA_DIR=%PROJECT_ROOT%\CameraTrapAssistant"
set "VENV_PYTHONW=%PROJECT_ROOT%\.venv\Scripts\pythonw.exe"
set "MAIN_PY=%CTA_DIR%\src\main.py"

if not exist "%MAIN_PY%" (
    echo Error: Main application file not found at %MAIN_PY%
    pause
    exit /b 1
)

if not exist "%VENV_PYTHONW%" (
    echo Error: The isolated source environment is not installed.
    echo Run dev\setup.bat first.
    pause
    exit /b 1
)

start "" "%VENV_PYTHONW%" "%MAIN_PY%"
exit /b 0
