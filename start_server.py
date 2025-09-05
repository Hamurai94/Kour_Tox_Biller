#!/usr/bin/env python3
"""
Universal launcher for Art Remote Control Server
Automatically detects platform and runs appropriate setup
"""

import platform
import subprocess
import sys
import os

def main():
    current_platform = platform.system()
    
    print(f"🎨 Art Remote Control - Universal Launcher")
    print(f"Platform detected: {current_platform}")
    print("=" * 50)
    
    if current_platform == "Darwin":  # macOS
        print("🍎 Running macOS setup...")
        if os.path.exists("quick_start_mac.sh"):
            try:
                # Make executable and run
                subprocess.run(["chmod", "+x", "quick_start_mac.sh"], check=True)
                subprocess.run(["./quick_start_mac.sh"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running macOS setup: {e}")
                # Fallback to direct Python execution
                run_direct()
        else:
            run_direct()
            
    elif current_platform == "Windows":  # Windows
        print("🪟 Running Windows setup...")
        if os.path.exists("quick_start_windows.bat"):
            try:
                subprocess.run(["quick_start_windows.bat"], shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running Windows setup: {e}")
                # Fallback to direct Python execution
                run_direct()
        else:
            run_direct()
            
    else:  # Linux or other
        print(f"🐧 Platform {current_platform} detected - using generic setup...")
        run_direct()

def run_direct():
    """Direct Python execution fallback"""
    print("Running server directly...")
    try:
        # Change to PCCompanion directory
        os.chdir("PCCompanion")
        
        # Try to run the cross-platform server
        if os.path.exists("art_remote_server_cross_platform.py"):
            subprocess.run([sys.executable, "art_remote_server_cross_platform.py"], check=True)
        else:
            print("❌ Server script not found!")
            print("Please ensure you're running from the ArtRemoteControl directory")
            
    except subprocess.CalledProcessError as e:
        print(f"Error running server: {e}")
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
