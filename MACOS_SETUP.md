# 🍎 macOS Setup Guide - Art Remote Control

## 📋 Prerequisites for macOS

### System Requirements
- **macOS 10.14+** (Mojave or later)
- **Python 3.9+** 
- **Xcode Command Line Tools** (for compiling native dependencies)
- **Krita** or **Clip Studio Paint** installed

### Key Differences from Windows
- Uses **⌘ (Cmd)** key instead of **Ctrl** for shortcuts
- Requires **Accessibility permissions** for automation
- Uses **PyObjC** framework for native macOS integration
- Different process detection methods

## 🚀 Quick Setup

### Option 1: One-Click Setup (Recommended)
```bash
# Make sure you're in the ArtRemoteControl directory
./quick_start_mac.sh
```

### Option 2: Universal Launcher
```bash
python3 start_server.py
```

### Option 3: Manual Setup
```bash
cd PCCompanion

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements_cross_platform.txt

# Run server
python3 art_remote_server_cross_platform.py
```

## 🔐 macOS Permissions Setup

### Step 1: Accessibility Permissions
macOS requires explicit permission for apps to control other applications.

1. **Open System Preferences** → **Security & Privacy** → **Privacy** tab
2. Select **Accessibility** from the left sidebar
3. Click the **lock icon** and enter your password
4. Click **+** to add an application
5. Navigate to and select one of:
   - **Python** (if installed via python.org)
   - **Terminal** (if running from Terminal)
   - **Your Python executable** in the virtual environment

### Step 2: Screen Recording (Optional)
For advanced features, you may need Screen Recording permissions:

1. **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Screen Recording**
3. Add **Python** or **Terminal** as above

### Step 3: Verify Permissions
Run this test to check if permissions are working:
```bash
cd PCCompanion
python3 -c "
import pyautogui
try:
    size = pyautogui.size()
    print(f'✅ Permissions OK - Screen size: {size}')
except Exception as e:
    print(f'❌ Permission issue: {e}')
"
```

## 🎨 macOS-Specific Shortcuts

### Default Krita Shortcuts (macOS)
| Action | Shortcut |
|--------|----------|
| Undo | ⌘Z |
| Redo | ⌘⇧Z |
| Zoom In | ⌘+ |
| Zoom Out | ⌘- |
| Rotate Left | ⌘[ |
| Rotate Right | ⌘] |
| Brush Tool | B |
| Eraser | E |
| Pan | Space |
| Select | R |
| New Layer | ⌘⇧N |

### Default Clip Studio Paint Shortcuts (macOS)
| Action | Shortcut |
|--------|----------|
| Undo | ⌘Z |
| Redo | ⌘Y |
| Zoom In | ⌘+ |
| Zoom Out | ⌘- |
| Rotate Left | ⌘⇧[ |
| Rotate Right | ⌘⇧] |
| Brush Tool | B |
| Eraser | E |
| Pan | H |
| Select | M |
| New Layer | ⌘⇧N |

## 🛠️ Troubleshooting macOS

### ❌ "Permission Denied" or Automation Errors
**Solution:**
1. Check Accessibility permissions (see Step 1 above)
2. Restart the server after granting permissions
3. Try running with `sudo` (not recommended for regular use)

### ❌ "No module named 'AppKit'" Error
**Solution:**
```bash
pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz
```

### ❌ App Detection Not Working
**Possible Issues:**
- Application not in focus
- Different app bundle name than expected
- Security restrictions

**Solutions:**
1. Click on Krita/CSP window to ensure it's active
2. Check Activity Monitor for exact process name
3. Run server with admin privileges: `sudo python3 art_remote_server_cross_platform.py`

### ❌ Homebrew Python vs System Python Issues
If you have multiple Python installations:

```bash
# Use Homebrew Python (recommended)
/usr/local/bin/python3 start_server.py

# Or use pyenv if installed
pyenv local 3.9.0  # or your preferred version
python3 start_server.py
```

### ❌ "Command not found: python3"
**Solution:**
```bash
# Install Python via Homebrew
brew install python

# Or create alias in ~/.zshrc or ~/.bash_profile
echo 'alias python3=/usr/bin/python3' >> ~/.zshrc
source ~/.zshrc
```

## 🔧 Advanced macOS Configuration

### Custom App Detection
Edit `art_remote_server_cross_platform.py` to add custom app detection:

```python
# Add custom bundle IDs for better app detection
'bundle_ids': ['org.kde.krita', 'jp.co.celsys.clip_studio_paint']
```

### Performance Optimization
```bash
# Reduce system animation delays for faster response
defaults write NSGlobalDomain NSAutomaticWindowAnimationsEnabled -bool false
defaults write NSGlobalDomain NSWindowResizeTime -float 0.001
```

### Network Configuration
```bash
# Find your Mac's IP address
ifconfig | grep "inet " | grep -v 127.0.0.1

# Or use the GUI
System Preferences → Network → Wi-Fi → Advanced → TCP/IP
```

## 📱 Android Connection to Mac

1. **Start the server** on your Mac using any method above
2. **Note the IP address** shown in the server GUI
3. **Open Art Remote** on your Android device
4. **Enter Mac IP address** (usually starts with 192.168.x.x)
5. **Tap Connect** and start creating! 🎨

## 🔒 Security Notes for macOS

- **Firewall**: macOS may ask to allow incoming connections - click **Allow**
- **Gatekeeper**: If you get security warnings, go to **System Preferences** → **Security & Privacy** → **General** and click **Allow**
- **Network**: Only works on trusted local networks
- **Permissions**: Server needs Accessibility permissions to control other apps

## ⚡ Performance Tips

1. **Close unnecessary apps** to reduce system load
2. **Use wired connection** if WiFi is unstable
3. **Keep Mac plugged in** to prevent CPU throttling
4. **Update macOS** for latest security and performance improvements

---

**🎉 Once setup is complete, you'll have the same powerful remote control experience on macOS as Windows!**
