# 🔐 Art Remote Control Authentication System

## Overview

The Art Remote Control now includes a **simple but secure authentication system** to prevent unauthorized access to your computer. This addresses the major security vulnerability of the previous version.

## 🔑 How It Works

### Server Side (PC/Mac)
1. **Automatic Setup**: Server generates a 6-digit PIN and secure token on first run
2. **Local Storage**: Credentials stored securely in `~/.artremote/auth.json`
3. **Challenge-Response**: Server challenges each connection for authentication
4. **Timeout Protection**: 30-second authentication timeout

### Client Side (Android)
1. **PIN Entry**: Simple 6-digit PIN for easy manual entry
2. **Token Support**: Full token for QR code setup (future feature)
3. **Persistent Storage**: Credentials saved in Android SharedPreferences
4. **Automatic Auth**: Seamless authentication on connection

## 🚀 Quick Setup

### 1. Start the Server
```bash
# Default (secure) - localhost only with authentication
python art_remote_server_cross_platform.py

# Allow network connections (still authenticated)
python art_remote_server_cross_platform.py --allow-network

# Development mode (NO AUTH - INSECURE!)
python art_remote_server_cross_platform.py --no-auth
```

### 2. Get Connection Info
The server GUI will display:
- **🔐 Connection PIN**: `123456` (example)
- **Copy Full Token**: Button to copy full token

### 3. Connect from Android
1. Open the Art Remote app
2. Enter the **PIN** shown on your computer
3. Enter your computer's **IP address**
4. Tap **Connect**

## 🔒 Security Features

### ✅ What's Protected
- **Token-based authentication**: 256-bit secure tokens
- **PIN fallback**: 6-digit PINs for easy entry
- **Local-only by default**: Server binds to `127.0.0.1`
- **Connection timeout**: 30-second auth timeout
- **Secure storage**: Hashed tokens, restricted file permissions
- **Input validation**: All commands validated before execution

### ⚠️ Security Considerations
- **Same network required**: Devices must be on same WiFi
- **PIN visibility**: PIN is visible on server screen
- **No encryption**: WebSocket traffic not encrypted (local network only)
- **Token storage**: Android stores credentials in app data

## 🛠️ Integration Guide

### Server Integration
```python
from auth import SimpleAuth, AuthenticatedConnection

# Create auth system
auth = SimpleAuth()

# Get connection info for display
info = auth.get_connection_info()
print(f"PIN: {info['pin']}")

# Validate authentication
if auth.is_authenticated({'pin': '123456'}):
    print("Authenticated!")
```

### Android Integration
```kotlin
// Store credentials
val auth = ArtRemoteAuth(context)
auth.storeCredentials(pin = "123456", host = "192.168.1.100")

// Create authenticated client
val client = AuthenticatedWebSocketClient(
    context = context,
    onConnected = { /* Connected successfully */ },
    onMessage = { message -> /* Handle message */ },
    onError = { error -> /* Handle error */ }
)

// Connect (authentication handled automatically)
client.connect()
```

## 🧪 Testing

### Test Authentication System
```bash
cd PCCompanion
python test_auth.py
```

### Test Server with Authentication
```bash
# Start server with auth (default)
python art_remote_server_cross_platform.py

# Start server without auth (testing only)
python art_remote_server_cross_platform.py --no-auth
```

## 🔧 Troubleshooting

### Connection Issues
1. **"Authentication required"**: Enter PIN from server screen
2. **"Authentication failed"**: Check PIN is correct
3. **"Connection timeout"**: Server may be unreachable
4. **"Invalid credentials"**: Try regenerating server credentials

### Server Issues
1. **No PIN displayed**: Check if authentication is enabled
2. **"Permission denied"**: Check file permissions on `~/.artremote/`
3. **"Port already in use"**: Another server instance may be running

### Reset Authentication
```bash
# Delete auth file to regenerate
rm ~/.artremote/auth.json
```

## 🚨 Security Warnings

### ⚠️ Development Mode
```bash
# This is INSECURE - only for development!
python art_remote_server_cross_platform.py --no-auth
```

### ⚠️ Network Mode
```bash
# This allows connections from entire network
python art_remote_server_cross_platform.py --allow-network
```

### ⚠️ Combined Risk
```bash
# This is EXTREMELY INSECURE - never use in production!
python art_remote_server_cross_platform.py --no-auth --allow-network
```

## 📋 Migration from Old Version

### Automatic Migration
- Old servers (no auth) will continue working with `--no-auth` flag
- New servers require authentication by default
- Android app will prompt for PIN on first connection

### Manual Migration
1. Update server to latest version
2. Start server (will generate PIN)
3. Update Android app
4. Enter PIN when prompted

## 🔮 Future Enhancements

- **QR Code Setup**: Scan QR code for automatic setup
- **TLS Encryption**: Encrypted WebSocket connections
- **Multi-device Support**: Multiple authenticated devices
- **Session Management**: Persistent sessions, token refresh
- **Role-based Access**: Different permission levels

---

**The authentication system provides a good balance of security and usability while maintaining the simplicity that makes Art Remote Control easy to use.**
