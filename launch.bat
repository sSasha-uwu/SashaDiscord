@echo off
setlocal enabledelayedexpansion
set PATH=%PATH%;%USERPROFILE%\.local\bin
set PYTHONPATH=.

for /f "tokens=1,* delims==" %%a in (project\pyproject.toml) do (
    if "%%a"=="name " (
        set PROJECT_NAME=%%b
        set PROJECT_NAME=!PROJECT_NAME:"=!
    )
)

title %PROJECT_NAME%

uv help >nul 2>&1

if %ERRORLEVEL% neq 0 (
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
)

uv self update

uv sync --project project

uv run --project project project/main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo.
    powershell Write-Host 'An unexpected error occurred in %PROJECT_NAME%. Send a screenshot of your console and your log files to @sasha_uwu on discord for assistance.' -ForegroundColor Red
    pause
    exit /b %ERRORLEVEL%
)

pause