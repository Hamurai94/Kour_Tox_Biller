#!/usr/bin/env python3
"""
Build Windows standalone executable using PyInstaller
Run this script to create ArtRemoteServer-Windows.exe
"""

import subprocess
import sys
import os
from pathlib import Path

def build_windows_executable():
    """Build standalone Windows executable"""
    
    print("🚀 Building Windows standalone executable...")
    print("📦 This will create ArtRemoteServer-Windows.exe")
    print("")
    
    # PyInstaller command for Windows
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed", 
        "--name=ArtRemoteServer-Windows",
        "--icon=icon.ico",  # Add icon if available
        "--add-data=requirements_cross_platform.txt;.",
        "--hidden-import=websockets",
        "--hidden-import=pyautogui", 
        "--hidden-import=psutil",
        "--hidden-import=pynput",
        "--hidden-import=sqlite3",
        "--hidden-import=tkinter",
        "art_remote_server_cross_platform.py"
    ]
    
    try:
        # Run PyInstaller
        print("⚙️ Running PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Build successful!")
        print(f"📁 Executable created: {Path('dist/ArtRemoteServer-Windows.exe').absolute()}")
        print("")
        print("🎯 Next steps:")
        print("1. Copy ArtRemoteServer-Windows.exe to take-home folder")
        print("2. Test on Windows machine")
        print("3. Remove Python-requiring files from package")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"📋 Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller not found!")
        print("📦 Install with: pip install pyinstaller")
        return False

if __name__ == "__main__":
    build_windows_executable()
