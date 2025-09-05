#!/bin/bash
# Art Remote Control Server - ROBUST macOS Launcher
# This script handles common Python installation issues

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

echo ""
echo "========================================================"
echo "🎨 Art Remote Control Server - macOS Edition"
echo "========================================================"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Find Python installation
echo "🔍 Looking for Python installation..."
PYTHON_CMD=""

# Try different Python commands
for cmd in python3 python python3.11 python3.12 python3.13; do
    if command_exists $cmd; then
        PYTHON_CMD=$cmd
        echo "✅ Found Python: $cmd"
        break
    fi
done

# If no Python found, try Homebrew paths
if [ -z "$PYTHON_CMD" ]; then
    echo "🔍 Checking Homebrew Python installations..."
    for path in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
        if [ -f "$path" ]; then
            PYTHON_CMD=$path
            echo "✅ Found Python: $path"
            break
        fi
    done
fi

# If still no Python, show installation help
if [ -z "$PYTHON_CMD" ]; then
    echo ""
    echo "❌ Python not found!"
    echo ""
    echo "📥 Install Python with Homebrew:"
    echo "   brew install python"
    echo ""
    echo "📥 Or download from: https://www.python.org/downloads/"
    echo ""
    echo "Press Enter to exit..."
    read
    exit 1
fi

echo ""
echo "🐍 Using Python: $PYTHON_CMD"
$PYTHON_CMD --version
echo ""

# Create virtual environment with error handling
echo "📦 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating new virtual environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        echo "💡 Try: $PYTHON_CMD -m pip install virtualenv"
        echo "Press Enter to exit..."
        read
        exit 1
    fi
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    echo "🔧 Recreating virtual environment..."
    rm -rf venv
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
fi

echo "✅ Virtual environment activated"
echo ""

# Install requirements
echo "📋 Installing Python dependencies..."
echo "(This may take 2-3 minutes the first time)"
echo ""

# Upgrade pip first
pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo "⚠️ Pip upgrade failed, continuing anyway..."
fi

# Install requirements
pip install -r requirements_cross_platform.txt
if [ $? -ne 0 ]; then
    echo "❌ Dependency installation failed"
    echo ""
    echo "🔧 Trying individual package installation..."
    pip install websockets pyautogui psutil pynput Pillow keyboard pyobjc-framework-Cocoa pyobjc-framework-Quartz
    if [ $? -ne 0 ]; then
        echo "❌ Package installation failed"
        echo "Press Enter to exit..."
        read
        exit 1
    fi
fi

echo "✅ Dependencies installed successfully"
echo ""

# Run the server
echo "🚀 Starting Art Remote Control Server..."
echo "📍 Server will show your IP address when ready"
echo "🔌 Connect your Android app to that IP:8765"
echo ""
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

python3 art_remote_server_cross_platform.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Server failed to start"
    echo "💡 Check the error messages above"
    echo "Press Enter to exit..."
    read
    exit 1
fi

echo ""
echo "👋 Server stopped"
echo "Press Enter to exit..."
read
