# 🔥 CRITICAL DEVELOPMENT NOTES FOR FUTURE ITERATIONS

## 📋 **CORE ARCHITECTURE UNDERSTANDING:**

### **🎯 APP DETECTION SYSTEM:**
- **Process detection**: Uses `psutil.process_iter()` and `AppKit.NSWorkspace` (macOS)
- **Window title checking**: Fallback method for app detection
- **Dynamic switching**: Server automatically adapts shortcuts based on detected app
- **Client notification**: Server sends `app_detected` message to Android with tool lists

### **⌨️ PLATFORM-SPECIFIC SHORTCUTS:**
- **Windows keyboard on Mac**: Windows key = Cmd key (critical for user's setup)
- **CSP vs Krita differences**: 
  - CSP: `Cmd+Shift+[/]` for rotation, `M` for select, `H` for pan
  - Krita: `Cmd+[/]` for rotation (NO SHIFT), `R` for select, `Space` for pan
- **Layer shortcuts**: Both use `Cmd+Shift+N` but CSP has more complex folder creation

### **🗄️ DATABASE INTEGRATION SECRETS:**

#### **CSP (REVOLUTIONARY BREAKTHROUGH):**
- **Dual database system**: `default.khc` (menu shortcuts) + `EditImageTool.todb` (custom tools)
- **F-key encoding**: `NodeShortCutKey = 36 + F_number` (world's first discovery!)
- **SQLite queries**: Cross-reference multiple tables for complete mapping
- **Dynamic F-key detection**: Real-time reading of user's custom assignments

#### **Krita (NEW BREAKTHROUGH):**
- **Brush preset system**: `.kpp` files in `~/Library/Application Support/krita/paintoppresets/`
- **ZIP archive format**: Each .kpp is a ZIP with XML inside
- **Category detection**: Parse file names for automatic categorization
- **No F-key system**: Krita uses different brush selection method

### **🔧 CRITICAL IMPLEMENTATION PATTERNS:**

#### **Error Handling:**
- **Always check file existence** before parsing databases
- **Graceful fallback**: Provide basic functionality when advanced features fail
- **Platform detection**: Use `platform.system()` for cross-platform paths
- **Import protection**: Try/catch around optional imports (like Krita parser)

#### **Android State Management:**
- **StateFlow pattern**: Use `MutableStateFlow` for reactive UI updates
- **Message parsing**: Handle both JSON objects and string formats from server
- **Dynamic UI**: Switch tool lists based on `detectedApp` state
- **Crash prevention**: Remove dangerous `onDismiss()` calls, use safe navigation

#### **Server Communication:**
- **JSON message format**: `{"action": "...", "value": "..."}`
- **String value parsing**: Handle `{name=brush}` format from Android
- **Connection management**: Send confirmation responses to keep connection alive
- **Background execution**: Use `await asyncio.sleep()` for timing-sensitive operations

## 🚨 **CRITICAL BUGS TO WATCH FOR:**

### **Android Issues:**
- **Back button crashes**: Never use `onDismiss()` - use `selectedTool = null` instead
- **Button layout**: Use `.weight(1f)` in Row/Column for proper sizing
- **Import errors**: Always add missing imports (like `Color`, `Path`)
- **Message parsing**: Check both dict and string formats for server values

### **Server Issues:**
- **CSP path differences**: Windows uses `AppData/Roaming/CELSys`, macOS uses `Library/CELSYS`
- **Shortcut timing**: Some shortcuts need `await asyncio.sleep()` delays
- **App detection timing**: Detection can be flaky - implement periodic re-checking
- **Database locks**: CSP databases can be locked when CSP is running

### **Cross-Platform Gotchas:**
- **Keyboard mapping**: Windows keyboard on Mac changes key behavior
- **File paths**: Use `Path.home()` and `/` separators, not hardcoded paths
- **Process names**: Different on each platform (`krita` vs `krita.exe`)
- **Shortcut differences**: Same action, different keys per platform

## 💰 **BUSINESS/COMPETITIVE ADVANTAGES:**

### **vs CSP Companion Mode:**
- **No subscription required**: One-time purchase vs monthly fee
- **Universal compatibility**: Works with multiple software, not just CSP
- **Advanced features**: Database integration, dynamic tool detection
- **Cross-platform**: Android + PC/Mac vs CSP's limited platform support

### **vs Hardware Remotes (TourBox, etc.):**
- **Software-based**: No expensive hardware required
- **Unlimited customization**: Can add any software support
- **Real-time adaptation**: Reads actual user settings
- **Cost effective**: $10-20 app vs $200+ hardware

### **Revolutionary Features:**
- **World's first CSP database cracker**: Reads internal SQLite databases
- **Dynamic F-key detection**: Real-time user shortcut reading
- **Multi-app adaptation**: Same interface, different software
- **Brush preset integration**: Reads actual installed brushes

## 🔧 **DEPLOYMENT BEST PRACTICES:**

### **APK Management:**
- **Single latest APK**: Remove old versions to avoid confusion
- **Clear naming**: Use descriptive names like `TourBoxKiller-KRITA-REVOLUTION.apk`
- **Version in take-home**: Always update `TourBoxKiller-LATEST.apk` in package
- **Test before distribution**: Verify APK installs and connects

### **Server Distribution:**
- **Standalone executables**: Use PyInstaller for consumer distribution
- **No Python requirement**: Customers shouldn't need technical setup
- **Multiple build scripts**: Provide options for different Windows setups
- **Error handling**: Scripts should pause and show errors, not flash

### **Cross-Platform Testing:**
- **Windows EXE building**: Requires actual Windows machine or VM
- **macOS .app bundles**: Use PyInstaller with `--windowed` flag
- **Path verification**: Test config file detection on each platform
- **Shortcut verification**: Test actual key combinations in target software

## 🎯 **FUTURE EXPANSION ROADMAP:**

### **Phase 1: Core Stability**
- **Fix remaining CSP shortcuts**: Rotate right, layer creation timing
- **Krita brush selection**: Implement actual brush switching
- **Error recovery**: Better handling of disconnections and app switching

### **Phase 2: Advanced Features**
- **Photoshop integration**: Research PS's tool system
- **Blender support**: 3D software has different paradigms
- **Custom profiles**: User-defined shortcut mappings
- **Gesture recognition**: Advanced touch controls

### **Phase 3: Monetization**
- **Freemium model**: Basic controls free, advanced features paid
- **Professional features**: Macro recording, batch operations
- **Enterprise licensing**: Multi-seat licenses for studios
- **Hardware integration**: Support actual TourBox hardware as premium feature

## 🧪 **TESTING PROTOCOLS:**

### **Before Each Release:**
1. **Test app switching**: CSP → Krita → back to CSP
2. **Verify shortcuts**: Each tool button in both software
3. **Check database parsing**: F-keys in CSP, brush presets in Krita
4. **Platform testing**: macOS and Windows compatibility
5. **Connection stability**: Disconnect/reconnect scenarios
6. **UI responsiveness**: App badge updates, tool list switching

### **User Testing Scenarios:**
- **Artist workflow**: Actual drawing tasks, not just button pressing
- **Software switching**: Working in both CSP and Krita in same session
- **Custom shortcuts**: Users with modified CSP F-key assignments
- **Different hardware**: Various Android devices, different keyboards

## 🔐 **SECURITY & LEGAL:**
- **No reverse engineering claims**: We read public config files, not proprietary code
- **Clean room implementation**: Our UI and logic are original
- **Open source components**: Clearly license any borrowed code
- **User data privacy**: Don't transmit user's brush presets or artwork data

## 📊 **PERFORMANCE OPTIMIZATION:**
- **Database caching**: Don't re-read CSP databases on every connection
- **Lazy loading**: Only parse brush presets when needed
- **Connection pooling**: Reuse WebSocket connections efficiently
- **Memory management**: Clear unused brush data when switching apps

---

**These notes represent 6 months of development condensed into actionable knowledge. Future iterations should reference this document to avoid repeating solved problems and to maintain the revolutionary edge we've built.**
