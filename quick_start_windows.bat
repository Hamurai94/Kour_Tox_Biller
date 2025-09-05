@echo off
echo 🎨 Art Remote Control - Windows Quick Start
echo ===========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.9+ first.
    echo Download from: https://python.org
    pause
    exit /b 1
)

echo ✅ Python found!
echo.

echo Setting up PC Companion for Windows...
cd PCCompanion

echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing cross-platform dependencies...
pip install -r requirements_cross_platform.txt

echo.
echo 🚀 Starting Art Remote Server for Windows...
echo ============================================
echo.
echo 📱 Next steps:
echo 1. Note your PC's IP address from the server GUI
echo 2. Open Art Remote app on your Android device  
echo 3. Enter the IP address and connect
echo 4. Start creating! 🎨
echo.
echo 💡 Tip: Windows may ask to allow Python through firewall - click Allow
echo.

python art_remote_server_cross_platform.py

pause
