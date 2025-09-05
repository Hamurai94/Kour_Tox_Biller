#!/bin/bash

echo "🎨 Art Remote Control - macOS Quick Start"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found! Please install Python 3.9+ first."
    echo "Install via Homebrew: brew install python"
    echo "Or download from: https://python.org"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

echo "Setting up PC Companion for macOS..."
cd PCCompanion

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing cross-platform dependencies..."
pip install -r requirements_cross_platform.txt

echo ""
echo "🚀 Starting Art Remote Server for macOS..."
echo "=========================================="
echo ""
echo "📱 Next steps:"
echo "1. Note your Mac's IP address from the server GUI"
echo "2. Open Art Remote app on your Android device"  
echo "3. Enter the IP address and connect"
echo "4. Start creating! 🎨"
echo ""
echo "💡 Tip: You may need to grant accessibility permissions"
echo "   Go to: System Preferences > Security & Privacy > Privacy > Accessibility"
echo "   Add Python or Terminal to the allowed apps"
echo ""

# Check for accessibility permissions
echo "Checking macOS permissions..."
python3 -c "
import sys
try:
    import pyautogui
    # Test if we can get screen size (requires accessibility permissions)
    screen_size = pyautogui.size()
    print('✅ Accessibility permissions OK')
except Exception as e:
    print('⚠️  May need accessibility permissions - check System Preferences')
    print(f'   Error: {e}')
"

echo ""
python3 art_remote_server_cross_platform.py
