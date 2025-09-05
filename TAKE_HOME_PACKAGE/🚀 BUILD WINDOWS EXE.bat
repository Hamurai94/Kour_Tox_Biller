@echo off
title Building Windows EXE - Art Remote Control
color 0A
echo.
echo ===============================================
echo 🚀 Building Windows Standalone Executable
echo ===============================================
echo.
echo This will create ArtRemoteServer-Windows.exe
echo No Python installation required for end users!
echo.
echo Press any key to continue...
pause >nul
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Python not found. Please install Python 3.11+ from python.org
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

REM Install PyInstaller and dependencies
echo 📦 Installing build tools...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install pyinstaller
%PYTHON_CMD% -m pip install -r requirements_cross_platform.txt

if %errorlevel% neq 0 (
    echo.
    echo ❌ FAILED TO INSTALL DEPENDENCIES!
    echo.
    echo Possible solutions:
    echo 1. Install Python from python.org
    echo 2. Check internet connection
    echo 3. Run as Administrator
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

REM Build the executable
echo 🔨 Building standalone executable...
%PYTHON_CMD% -m PyInstaller --onefile --windowed ^
    --name=ArtRemoteServer-Windows ^
    --add-data="requirements_cross_platform.txt;." ^
    --hidden-import=websockets ^
    --hidden-import=pyautogui ^
    --hidden-import=psutil ^
    --hidden-import=pynput ^
    --hidden-import=PIL ^
    --hidden-import=keyboard ^
    --hidden-import=sqlite3 ^
    --hidden-import=pathlib ^
    art_remote_server_cross_platform.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ BUILD FAILED!
    echo.
    echo Common issues:
    echo 1. Missing dependencies - run script as Administrator
    echo 2. Antivirus blocking - temporarily disable
    echo 3. Disk space - need at least 500MB free
    echo.
    echo Check the error messages above for details
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo.
echo ===============================================
echo ✅ SUCCESS! EXE FILE CREATED!
echo ===============================================
echo.
echo 📁 Your executable is at: dist\ArtRemoteServer-Windows.exe
echo.
echo 🎯 This .exe file can run on ANY Windows computer without Python!
echo 💰 Perfect for distribution to customers!
echo.
echo 📋 What to do next:
echo   1. Test the .exe file by double-clicking it
echo   2. Copy ArtRemoteServer-Windows.exe to other computers  
echo   3. No Python installation needed on target computers
echo.
echo BUILD COMPLETE! Window will stay open so you can see this message.
echo.
echo Press any key to exit...
pause >nul
