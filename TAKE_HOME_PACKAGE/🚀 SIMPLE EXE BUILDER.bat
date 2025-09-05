@echo off
title Art Remote Control - Simple EXE Builder
color 0A
cls

echo.
echo ===============================================
echo    🚀 Art Remote Control EXE Builder
echo ===============================================
echo.
echo This will create ArtRemoteServer-Windows.exe
echo.
echo Press ENTER to start, or close this window to cancel
pause >nul

cls
echo.
echo Step 1: Checking Python...
echo.

python --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python found!
    set PYTHON_CMD=python
    goto :install
)

py --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python found!
    set PYTHON_CMD=py
    goto :install
)

echo ❌ Python not found!
echo Install Python from python.org and try again
echo.
pause
exit /b 1

:install
echo.
echo Step 2: Installing packages...
echo.

echo Installing PyInstaller...
%PYTHON_CMD% -m pip install pyinstaller

echo Installing websockets...
%PYTHON_CMD% -m pip install websockets

echo Installing pyautogui...
%PYTHON_CMD% -m pip install pyautogui

echo Installing psutil...
%PYTHON_CMD% -m pip install psutil

echo Installing pynput...
%PYTHON_CMD% -m pip install pynput

echo Installing Pillow...
%PYTHON_CMD% -m pip install Pillow

echo Installing keyboard...
%PYTHON_CMD% -m pip install keyboard

echo.
echo ✅ All packages installed!
echo.
echo Press ENTER to build EXE...
pause >nul

:build
cls
echo.
echo Step 3: Building EXE file...
echo.
echo This takes 2-3 minutes...
echo.

%PYTHON_CMD% -m PyInstaller --onefile --console --name=ArtRemoteServer-Windows art_remote_server_cross_platform.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Build failed! Try running as Administrator
    echo.
    pause
    exit /b 1
)

:success
cls
echo.
echo ===============================================
echo    🎉 SUCCESS!
echo ===============================================
echo.
echo Your EXE file is ready:
echo.
echo Location: %CD%\dist\ArtRemoteServer-Windows.exe
echo.
echo ✅ This file can run on ANY Windows computer
echo ✅ No Python installation needed for customers
echo.
echo Test it by double-clicking the EXE file!
echo.
echo Press any key to close this window...
pause >nul
