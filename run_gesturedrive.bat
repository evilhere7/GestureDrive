@echo off
setlocal
title GestureDrive — Virtual Racing Wheel
color 0A

echo ===================================================================
echo                    GESTUREDRIVE LAUNCHER
echo          Virtual AI Steering Wheel for Racing Games
echo ===================================================================
echo.

:: Check for python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.11+ from https://python.org and check "Add to PATH".
    echo.
    pause
    exit /b 1
)

echo Select Launch Mode:
echo   [1] Launch GestureDrive (Default)
echo   [2] Launch in Simulation Mode (Safe - Visual Only, No Key Injection)
echo   [3] Launch directly in Racing HUD Mode
echo   [4] Run Camera Hardware Diagnostic
echo   [5] Run Full Test Suite (pytest)
echo.
set /p choice="Enter choice [1-5] (default is 1): "

if "%choice%"=="2" (
    echo Starting GestureDrive in Simulation Mode...
    python main.py --simulation
) else if "%choice%"=="3" (
    echo Starting GestureDrive in Racing Mode...
    python main.py --racing
) else if "%choice%"=="4" (
    echo Running Camera Diagnostic...
    python test_camera.py
) else if "%choice%"=="5" (
    echo Running Test Suite...
    python -m pytest tests/ -v
) else (
    echo Starting GestureDrive...
    python main.py
)

if errorlevel 1 (
    echo.
    echo [NOTE] Application exited with code %errorlevel%.
)

pause
