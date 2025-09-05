# 🎨 Digital Art Remote Control

A custom Android app inspired by the TourBox design for wirelessly controlling **Krita** and **Clip Studio Paint** from your Android device.

![TourBox Inspired](https://img.shields.io/badge/Inspired%20by-TourBox-blue)
![Platform](https://img.shields.io/badge/Platform-Android%20%2B%20Windows%20%2B%20macOS-green)
![Language](https://img.shields.io/badge/Language-Kotlin%20%2B%20Python-orange)

## ✨ Features

### 🎯 Core Controls (TourBox Inspired)
- **Circular Zoom Dial** - Smooth zoom in/out with gesture control
- **Rotation Dial** - Canvas rotation with haptic feedback  
- **Undo/Redo Buttons** - One-touch access to essential commands
- **Custom Button Grid** - 8 assignable buttons for your workflow

### 🚀 Advanced Features
- **App Auto-Detection** - Automatically detects Krita or Clip Studio Paint
- **Haptic Feedback** - Tactile response for better control
- **Real-time Connection** - WebSocket communication for instant response
- **Custom Profiles** - Different button layouts per application
- **Material Design 3** - Modern, intuitive interface

## 📱 Android App

### Core Controls Layout
```
┌─────────────────────────────────┐
│  [UNDO]           [REDO]        │
│                                 │
│    ○ ZOOM        ○ ROTATE       │
│   (Dial)        (Dial)          │
│                                 │
│ [BRUSH] [ERASE] [LAYER+] [SIZE+]│
│ [PAN]   [SELECT][LAYER-] [SIZE-]│
└─────────────────────────────────┘
```

### Default Button Assignments
| Button | Krita | Clip Studio Paint |
|--------|-------|-------------------|
| Brush | B | B |
| Eraser | E | E |
| Pan Tool | Space | H |
| Select | R | M |
| New Layer | Ctrl+Shift+N | Ctrl+Shift+N |
| Delete Layer | Delete | Delete |
| Brush Size + | ] | ] |
| Brush Size - | [ | [ |

## 🖥️ PC Companion

### Features
- **System Tray App** - Runs quietly in background
- **Auto App Detection** - Knows when Krita/CSP is active
- **WebSocket Server** - Handles Android app connections
- **Customizable Shortcuts** - Modify key bindings per app
- **GUI Control Panel** - Easy start/stop and monitoring

### Supported Applications
- ✅ **Krita** (Full support)
- ✅ **Clip Studio Paint EX** (Full support)
- 🔄 **Photoshop** (Planned)
- 🔄 **Procreate** (Via iPad version)

## 🚀 Quick Start

### 1. Universal Setup (Windows/macOS)
```bash
# Universal launcher (recommended)
python3 start_server.py

# Or platform-specific:
# Windows: quick_start_windows.bat
# macOS: ./quick_start_mac.sh
```

### 2. Android Setup
1. Open **Android Studio**
2. Import the `AndroidApp` project
3. Build and install on your device
4. Connect to same WiFi as your PC

### 3. Connection
1. Start PC companion server
2. Note your PC's IP address (shown in server GUI)
3. Open Android app and enter IP address
4. Tap "Connect" and start creating! 🎨

## 🛠️ Development Setup

### Prerequisites
- **Android Studio** (Latest version)
- **Python 3.9+** (For PC/Mac companion)
- **Windows 10/11** or **macOS 10.14+** (For companion)

### Android Development
```bash
# Clone and open in Android Studio
cd AndroidApp
./gradlew build
```

### PC/Mac Companion Development
```bash
cd PCCompanion
python3 -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate

pip install -r requirements_cross_platform.txt
python3 art_remote_server_cross_platform.py
```

## 🎨 Customization

### Adding Custom Shortcuts
Edit `art_remote_server_cross_platform.py`:
```python
'shortcuts': {
    'my_custom_action': ['ctrl', 'alt', 'c'],
    # Add more shortcuts here
}
```

### Modifying Button Layout
Edit `RemoteControlScreen.kt`:
```kotlin
val buttonConfigs = listOf(
    ButtonConfig("My Tool", Icons.Default.Brush, "my_custom_action"),
    // Customize buttons here
)
```

## 📡 Communication Protocol

### Command Structure
```json
{
    "action": "zoom",
    "value": {
        "direction": "in",
        "intensity": 1.5
    },
    "app": "krita"
}
```

### Supported Actions
- `zoom` - Canvas zoom control
- `rotate` - Canvas rotation
- `undo` / `redo` - History navigation  
- `tool_*` - Tool switching
- `layer_*` - Layer operations
- `brush_*` - Brush adjustments

## 🔧 Troubleshooting

### Connection Issues
1. **Check WiFi** - Both devices on same network
2. **Firewall** - Allow Python through Windows Firewall
3. **IP Address** - Verify PC IP in server GUI
4. **Port 8765** - Ensure port is not blocked

### App Detection Issues
1. **Run as Admin** - PC companion may need elevated privileges
2. **Application Focus** - Ensure Krita/CSP window is active
3. **Process Names** - Check if app process names match configuration

## 🎯 Roadmap

### Phase 1: Foundation ✅
- [x] Basic Android UI
- [x] PC companion server  
- [x] WebSocket communication
- [x] Core controls (zoom, rotate, undo/redo)

### Phase 2: Enhancement 🔄
- [ ] Custom button configuration UI
- [ ] Multiple device connections
- [ ] Gesture recognition improvements
- [ ] Performance optimization

### Phase 3: Advanced Features 🔮
- [ ] Pressure sensitivity support
- [ ] Macro recording/playback
- [ ] Cloud sync for settings
- [ ] iOS version

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💡 Inspiration

This project was inspired by the excellent **TourBox** hardware controller, bringing similar functionality to a customizable Android app that works with your existing devices.

---

**Built with ❤️ for digital artists who want freedom from subscription services!**
