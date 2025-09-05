# 🎨 Art Remote Control - Take Home Package

## What You Have
A complete **cross-platform digital art remote control** that works on both Windows and macOS!

## 📦 Files to Copy to Your Home Computer

**Copy this entire `ArtRemoteControl` folder** to your home computer.

## 🚀 Quick Start at Home

### Windows:
1. Double-click `quick_start_windows.bat`
2. Open your phone's browser and go to the IP address shown
3. Start creating! 🎨

### macOS:
1. Double-click `quick_start_mac.sh` (or run `./quick_start_mac.sh` in Terminal)
2. Grant accessibility permissions when prompted
3. Open your phone's browser and go to the IP address shown
4. Start creating! 🎨

### Universal (Works on Both):
1. Run `python3 start_server.py`
2. The script will detect your OS and run the appropriate setup
3. Open the web interface on your phone

## 📱 How to Use

1. **Start the server** on your PC/Mac using any method above
2. **Connect your phone** to the same WiFi network as your computer
3. **Open your phone's browser** and navigate to the address shown in the terminal
4. **Start controlling** Krita or Clip Studio Paint remotely!

## 🎯 Supported Apps
- **Krita** (Free digital painting software)
- **Clip Studio Paint** (Professional illustration software)

## 🔧 Controls Available
- **Undo/Redo** - Essential for any art workflow
- **Zoom In/Out/Fit** - Navigate your canvas easily  
- **Rotate Left/Right** - Perfect for drawing at different angles
- **Brush Size +/-** - Adjust your brush on the fly
- **Eyedropper** - Pick colors from your artwork
- **Hand Tool** - Pan around your canvas
- **Save** - Never lose your work

## 🌐 Web Interface Features
- **Touch-optimized** for phone screens
- **Real-time connection** status
- **Visual feedback** on button presses
- **Auto-reconnect** functionality
- **Responsive design** works on any phone size

## 🔧 Troubleshooting

### If the server won't start:
- Make sure Python 3.8+ is installed
- Try running the setup script again
- Check that no other app is using ports 8765 or 8080

### If your phone can't connect:
- Make sure both devices are on the same WiFi network
- Try using your computer's IP address instead of "localhost"
- Check your firewall settings

### Finding your computer's IP address:
- **Windows**: Open Command Prompt, type `ipconfig`
- **macOS**: Open Terminal, type `ifconfig | grep inet`
- Look for something like `192.168.1.100`

## 📁 Project Structure
```
ArtRemoteControl/
├── PCCompanion/
│   ├── art_remote_server_cross_platform.py  # Main server
│   ├── web_remote.html                       # Web interface
│   └── requirements_cross_platform.txt      # Dependencies
├── start_server.py                           # Universal launcher
├── quick_start_windows.bat                   # Windows setup
├── quick_start_mac.sh                        # macOS setup
└── README.md                                 # Full documentation
```

## 🎉 You're All Set!

This is a **professional-grade art remote control** that you built yourself! No subscriptions, no limitations - just pure creative control at your fingertips.

**Enjoy your weekend art sessions!** 🎨✨

