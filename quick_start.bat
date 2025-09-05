it t@echo off
echo 🎨 Art Remote Control - Quick Start
echo =====================================
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

echo Setting up PC Companion...
cd PCCompanion

echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo 🚀 Starting Art Remote Server...
echo =====================================
echo.
echo 📱 Next steps:
echo 1. Note your PC's IP address from the server GUI
echo 2. Open Art Remote app on your Android device  
echo 3. Enter the IP address and connect
echo 4. Start creating! 🎨
echo.

python art_remote_server.py

pause
