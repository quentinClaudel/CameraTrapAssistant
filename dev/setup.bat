@echo off
title Camera Trap Assistant - Source Environment Setup
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "CTA_DIR=%PROJECT_ROOT%\CameraTrapAssistant"
set "VENV_DIR=%PROJECT_ROOT%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "REQUIREMENTS_FILE=%CTA_DIR%\requirements.txt"

echo ======================================================
echo   Camera Trap Assistant - Source Environment Setup
echo ======================================================
echo.
echo This helper is for running the source checkout.
echo Public releases use an isolated packaged runtime.
echo.

if not exist "%REQUIREMENTS_FILE%" (
    echo Error: Requirements file not found at %REQUIREMENTS_FILE%
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3.10 or newer was not found.
    echo Install Python from https://www.python.org/downloads/ and try again.
    exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo Error: Python 3.10 or newer is required.
    python --version
    exit /b 1
)

if not exist "%VENV_PYTHON%" (
    echo Creating isolated environment at %VENV_DIR%...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Error: Could not create the virtual environment.
        exit /b 1
    )
)

echo Installing dependencies into the project environment...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 (
    echo Error: Failed to update pip in the virtual environment.
    exit /b 1
)

"%VENV_PYTHON%" -m pip install -r "%REQUIREMENTS_FILE%"
if errorlevel 1 (
    echo Error: Failed to install dependencies.
    exit /b 1
)

"%VENV_PYTHON%" -c "import sys; sys.path.insert(0, r'%CTA_DIR%\src'); from utils.model_manager import validate_models, format_model_problems; problems = validate_models(); print(format_model_problems(problems)) if problems else print('Model integrity checks passed.'); raise SystemExit(bool(problems))"
if errorlevel 1 (
    echo.
    echo Model validation failed. Source archives may contain Git LFS pointers.
    echo Use Git LFS or install an official packaged release.
    exit /b 1
)

echo Source environment ready.
exit /b 0
