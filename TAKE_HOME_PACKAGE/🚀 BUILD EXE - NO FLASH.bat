@echo off
title Art Remote Control - EXE Builder
color 0A
cls

:start
echo.
echo ===============================================
echo    🚀 Art Remote Control EXE Builder
echo ===============================================
echo.
echo This will create a standalone Windows executable
echo that customers can use WITHOUT installing Python!
echo.
echo Current directory: %CD%
echo.
echo Press ENTER to start building, or CTRL+C to cancel
pause

cls
echo.
echo ===============================================
echo    Step 1: Checking Python Installation
echo ===============================================
echo.

python --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python found via 'python' command
    set PYTHON_CMD=python
    goto :install_deps
)

py --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python found via 'py' launcher
    set PYTHON_CMD=py
    goto :install_deps
)

echo ❌ Python not found!
echo.
echo Please install Python 3.11+ from: https://python.org/downloads
echo Make sure to check "Add Python to PATH" during installation
echo.
echo Press any key to exit...
pause >nul
exit /b 1

:install_deps
echo.
echo ===============================================
echo    Step 2: Installing Build Dependencies
echo ===============================================
echo.
echo Installing PyInstaller and required packages...
echo This may take a few minutes...
echo.

%PYTHON_CMD% -m pip install --upgrade pip --quiet
%PYTHON_CMD% -m pip install pyinstaller --quiet
%PYTHON_CMD% -m pip install -r "%~dp0requirements_cross_platform.txt" --quiet

if %errorlevel% neq 0 (
    echo.
    echo ❌ Failed to install dependencies!
    echo.
    echo Try running this script as Administrator
    echo Right-click the .bat file and select "Run as administrator"
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo ✅ Dependencies installed successfully!

:build_exe
echo.
echo ===============================================
echo    Step 3: Building Standalone Executable
echo ===============================================
echo.
echo Building ArtRemoteServer-Windows.exe...
echo This will take 2-3 minutes...
echo.

%PYTHON_CMD% -m PyInstaller --onefile --console --name=ArtRemoteServer-Windows --add-data="%~dp0requirements_cross_platform.txt;." --hidden-import=websockets --hidden-import=pyautogui --hidden-import=psutil --hidden-import=pynput --hidden-import=PIL --hidden-import=keyboard --hidden-import=sqlite3 --hidden-import=pathlib "%~dp0art_remote_server_cross_platform.py"

if %errorlevel% neq 0 (
    echo.
    echo ❌ Build failed!
    echo.
    echo Common solutions:
    echo 1. Run as Administrator
    echo 2. Temporarily disable antivirus
    echo 3. Free up disk space (need 500MB+)
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:success
cls
echo.
echo ===============================================
echo    🎉 SUCCESS! EXE FILE CREATED!
echo ===============================================
echo.
echo Your executable is ready at:
echo %CD%\dist\ArtRemoteServer-Windows.exe
echo.
echo File size: 
dir "dist\ArtRemoteServer-Windows.exe" | find "ArtRemoteServer-Windows.exe"
echo.
echo ✅ This .exe file can run on ANY Windows computer
echo ✅ No Python installation required for customers
echo ✅ Perfect for distribution and sales
echo.
echo Next steps:
echo 1. Test the .exe by double-clicking it
echo 2. Copy it to other computers to verify it works
echo 3. Distribute to customers!
echo.
echo This window will stay open so you can read this message.
echo Press any key when you're ready to close...
pause >nul
exit /b 0
