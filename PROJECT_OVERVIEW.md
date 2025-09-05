# 🎨 Digital Art Remote Control

## Project Overview
Custom Android application inspired by TourBox design for controlling Krita and Clip Studio Paint remotely.

## Architecture

### Android App (Kotlin)
- **UI:** TourBox-inspired interface with circular dial, customizable buttons
- **Communication:** WebSocket client for real-time PC communication
- **Features:** Gesture recognition, haptic feedback, customizable layouts

### PC Companion (Python)
- **Server:** WebSocket server listening for Android commands
- **Automation:** Controls Krita/CSP using keyboard shortcuts and mouse automation
- **Detection:** Auto-detects active art application
- **Tray App:** Runs in system tray with minimal footprint

## Core Controls (TourBox Inspired)

### Primary Controls
- **Circular Dial:** Zoom in/out (scroll wheel simulation)
- **Side Dial:** Canvas rotation (Shift + scroll wheel)
- **Undo Button:** Ctrl+Z
- **Redo Button:** Ctrl+Y or Ctrl+Shift+Z

### Customizable Buttons (6-8 buttons)
- **Button 1-4:** Assignable shortcuts (brush size, layer controls, etc.)
- **Button 5-8:** Tool switching (brush, eraser, selection, etc.)

### Advanced Features
- **Long Press:** Secondary functions
- **Gesture Areas:** Swipe for canvas pan
- **Pressure Sensitivity:** If device supports it

## Development Phases

### Phase 1: Foundation ✅
- [x] Project structure
- [ ] Basic Android UI
- [ ] PC companion server
- [ ] Basic communication protocol

### Phase 2: Core Features
- [ ] Zoom/rotate controls
- [ ] Undo/redo functionality  
- [ ] Button customization system
- [ ] App detection (Krita/CSP)

### Phase 3: Advanced Features
- [ ] Gesture recognition
- [ ] Haptic feedback
- [ ] Custom profiles per app
- [ ] Macro recording

### Phase 4: Polish
- [ ] Material Design theming
- [ ] Settings persistence
- [ ] Network auto-discovery
- [ ] Performance optimization

## Technology Stack
- **Android:** Kotlin, Jetpack Compose, WebSocket client
- **PC:** Python 3.9+, WebSocket server, pyautogui, pynput
- **Communication:** JSON over WebSocket
- **UI:** Material Design 3 with custom TourBox-inspired components
