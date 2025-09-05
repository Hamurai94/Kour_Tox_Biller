# 🚀 Setup Guide - Art Remote Control

## 📋 Prerequisites

### For Android Development
- **Android Studio** (Latest stable version)
- **Android SDK** (API level 24+)
- **Android device** (Android 7.0+) or emulator
- **USB cable** or wireless debugging enabled

### For PC Companion
- **Windows 10/11** (Primary support)
- **Python 3.9+** 
- **Administrator privileges** (for system automation)
- **Krita** or **Clip Studio Paint** installed

## 🖥️ PC Companion Setup

### Step 1: Install Python Dependencies
```bash
# Navigate to PC companion directory
cd PCCompanion

# Create virtual environment (recommended)
python -m venv art_remote_env
art_remote_env\Scripts\activate  # Windows
# or
source art_remote_env/bin/activate  # macOS/Linux

# Install required packages
pip install -r requirements.txt
```

### Step 2: Test Installation
```bash
python art_remote_server.py
```

You should see a GUI window with "Art Remote Control Server" title.

### Step 3: Configure Windows Firewall
1. When first running, Windows may ask to allow Python through firewall
2. **Allow access** for both private and public networks
3. If missed, manually add exception:
   - Windows Security → Firewall & network protection
   - Allow an app through firewall
   - Add Python.exe from your virtual environment

### Step 4: Find Your PC's IP Address
```bash
# In Command Prompt or PowerShell
ipconfig

# Look for "IPv4 Address" under your active network adapter
# Usually something like: 192.168.1.100
```

## 📱 Android App Setup

### Step 1: Open in Android Studio
1. Launch **Android Studio**
2. Choose **"Open an Existing Project"**
3. Navigate to `ArtRemoteControl/AndroidApp`
4. Click **"OK"** and wait for project sync

### Step 2: Configure Build
1. Ensure **API level 24+** is installed in SDK Manager
2. Sync project with Gradle files
3. Resolve any dependency issues (Android Studio will guide you)

### Step 3: Build and Install
```bash
# Via Android Studio
1. Connect your Android device via USB
2. Enable "Developer Options" and "USB Debugging"
3. Click "Run" button (green play icon)
4. Select your device from the list

# Via Command Line (alternative)
cd AndroidApp
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

## 🔗 First Connection

### Step 1: Start PC Server
1. Run `art_remote_server.py`
2. Click **"Start Server"** in the GUI
3. Note the IP address shown (e.g., 0.0.0.0:8765)
4. Status should show "Running" in green

### Step 2: Connect Android App
1. Open **Art Remote** app on your Android device
2. Enter your PC's IP address (from Step 4 of PC setup)
3. Tap **"Connect"**
4. Status should change to "Connected" with green indicator

### Step 3: Test Basic Functions
1. Open **Krita** or **Clip Studio Paint** on your PC
2. Create a new document
3. On Android app, try:
   - Tap **"Undo"** button (should undo last action)
   - Use **zoom dial** (should zoom canvas)
   - Tap **"Brush"** button (should select brush tool)

## 🛠️ Troubleshooting

### ❌ "Connection Failed" on Android
**Possible Causes:**
- PC and Android not on same WiFi network
- Windows Firewall blocking connection
- Incorrect IP address entered
- PC server not running

**Solutions:**
1. Verify both devices on same network
2. Check Windows Firewall settings
3. Try connecting to `192.168.1.XXX:8765` (replace XXX with PC's IP)
4. Restart PC server

### ❌ "No App Detected" in PC Server
**Possible Causes:**
- Krita/CSP not running
- App window not in focus
- Process name not recognized

**Solutions:**
1. Ensure art app is running and active window
2. Click on art app window to focus it
3. Check if process name matches configuration
4. Try running PC server as Administrator

### ❌ Commands Not Working
**Possible Causes:**
- Art app doesn't have focus
- Different keyboard shortcuts in your version
- Keyboard layout differences

**Solutions:**
1. Click on art app before using remote
2. Check shortcut keys match your app version
3. Customize shortcuts in `art_remote_server.py`

### ❌ Android Build Errors
**Common Issues:**
```bash
# Gradle sync failed
./gradlew clean
./gradlew build

# Missing SDK components
# Install via Android Studio SDK Manager

# Dependency conflicts
# Update gradle and dependencies to latest versions
```

## ⚙️ Advanced Configuration

### Custom Shortcuts
Edit `PCCompanion/art_remote_server.py`:
```python
'shortcuts': {
    'undo': ['ctrl', 'z'],
    'my_custom_action': ['ctrl', 'shift', 'x'],
    # Add your shortcuts here
}
```

### Custom Buttons
Edit `AndroidApp/.../RemoteControlScreen.kt`:
```kotlin
val buttonConfigs = listOf(
    ButtonConfig("My Tool", Icons.Default.Build, "my_custom_action"),
    // Customize button layout here
)
```

### Network Settings
Change server port in `art_remote_server.py`:
```python
def __init__(self, host='0.0.0.0', port=8765):  # Change port here
```

And in Android app's `WebSocketClient.kt`:
```kotlin
private const val DEFAULT_PORT = 8765  // Match PC server port
```

## 🔒 Security Notes

1. **Local Network Only** - App designed for local WiFi use
2. **No Authentication** - Anyone on your network can connect
3. **Firewall Rules** - Only allow on trusted networks
4. **Admin Privileges** - PC companion needs admin rights for automation

## 📞 Support

If you encounter issues:

1. **Check Logs** - Both Android (Logcat) and PC (GUI log area) show detailed error messages
2. **Network Test** - Use `telnet <PC_IP> 8765` to test basic connectivity
3. **Process Check** - Verify art app processes are running as expected
4. **Version Check** - Ensure you're using compatible versions of all components

---

**🎉 Once setup is complete, you'll have a powerful, customizable remote control for your digital art workflow!**
