@echo off
title Camera Trap Assistant - Release Checker
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "CTA_DIR=%PROJECT_ROOT%\CameraTrapAssistant"
set "VERSION_JSON=%CTA_DIR%\version.json"
set "GITHUB_REPO=noebernigaud/CameraTrapAssistant"
set "GITHUB_API_URL=https://api.github.com/repos/%GITHUB_REPO%/releases/latest"
set "RELEASES_URL=https://github.com/%GITHUB_REPO%/releases"

echo ======================================================
echo   Camera Trap Assistant - Release Checker
echo ======================================================
echo.
echo Automatic replacement is disabled for safety.
echo This tool only checks for a newer official release.
echo.

set "CURRENT_VERSION=0.0.0"
if exist "%VERSION_JSON%" (
    for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "try { (Get-Content -Raw '%VERSION_JSON%' | ConvertFrom-Json).version } catch { '0.0.0' }"`) do set "CURRENT_VERSION=%%i"
)

for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "try { (Invoke-RestMethod -Uri '%GITHUB_API_URL%' -Headers @{'User-Agent'='CameraTrapAssistant'}).tag_name -replace '^v','' } catch { 'ERROR' }"`) do set "LATEST_VERSION=%%i"

if "%LATEST_VERSION%"=="ERROR" (
    echo Could not contact GitHub. No files were changed.
    echo Releases page: %RELEASES_URL%
    pause
    exit /b 1
)

echo Installed/source version: %CURRENT_VERSION%
echo Latest release:          %LATEST_VERSION%
echo.

for /f %%i in ('powershell -NoProfile -Command "try { if ([version]'%LATEST_VERSION%' -gt [version]'%CURRENT_VERSION%') { 'true' } else { 'false' } } catch { 'true' }"') do set "IS_NEWER=%%i"

if "%IS_NEWER%"=="true" (
    echo A newer release is available.
    set /p "OPEN_RELEASE=Open the official GitHub Releases page? (y/n): "
    if /i "%OPEN_RELEASE%"=="y" start "" "%RELEASES_URL%"
    if /i "%OPEN_RELEASE%"=="yes" start "" "%RELEASES_URL%"
) else (
    echo You have the latest published release.
)

echo.
echo No application files were modified.
pause
exit /b 0
