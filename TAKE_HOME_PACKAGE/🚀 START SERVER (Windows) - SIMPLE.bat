@echo off
title Art Remote Control Server
echo.
echo 🎨 Art Remote Control Server
echo ================================
echo.

REM Try different Python commands
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Python found!
    goto :run_server
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Python found via py launcher!
    set PYTHON_CMD=py
    goto :run_server
)

echo ❌ Python not found!
echo.
echo Please install Python 3.11+ from:
echo https://python.org/downloads
echo.
echo Make sure to check "Add Python to PATH" during installation
pause
exit /b 1

:run_server
echo.
echo 🚀 Starting Art Remote Control Server...
echo 📱 Connect your Android app to this computer's IP
echo 🔧 Server will run on port 8765
echo.
echo ⚠️  Note: If CSP is not installed, server runs in basic mode
echo.

if defined PYTHON_CMD (
    %PYTHON_CMD% art_remote_server_cross_platform.py
) else (
    python art_remote_server_cross_platform.py
)

if %errorlevel% neq 0 (
    echo.
    echo ❌ Server crashed! 
    echo 💡 Try installing missing packages:
    echo    pip install websockets pyautogui psutil pynput
    echo.
)

pause
