#!/usr/bin/env python3
import asyncio
import websockets
import json
import pyautogui

print("🚀 Art Remote Server - MULTI-PROFILE EDITION")
print("📱 Ready for your Android app on port 8765!")

# Application Profiles with correct default shortcuts
APP_PROFILES = {
    'krita': {
        'name': 'Krita',
        'shortcuts': {
            # Basic Commands
            'undo': ['cmd', 'z'],
            'redo': ['cmd', 'shift', 'z'],
            'save': ['cmd', 's'],
            
            # Navigation
            'zoom_in': ['cmd', '+'],
            'zoom_out': ['cmd', '-'],
            'zoom_fit': ['cmd', '0'],
            'rotate_left': ['cmd', '['],
            'rotate_right': ['cmd', ']'],
            'rotate_reset': ['cmd', 'shift', '0'],
            
            # Tools
            'tool_brush': ['b'],
            'tool_eraser': ['e'],
            'tool_pan': ['space'],
            'tool_select': ['r'],
            'tool_eyedropper': ['ctrl'],
            'tool_hand': ['h'],
            
            # Layers
            'layer_new': ['cmd', 'shift', 'n'],
            'layer_delete': ['delete'],
            'layer_duplicate': ['cmd', 'j'],
            'layer_merge_down': ['cmd', 'e'],
            
            # Brush
            'brush_size_up': [']'],
            'brush_size_down': ['['],
            'brush_opacity_up': ['o'],
            'brush_opacity_down': ['shift', 'o'],
        }
    },
    
    'clipstudio': {
        'name': 'Clip Studio Paint EX',
        'shortcuts': {
            # Basic Commands
            'undo': ['cmd', 'z'],
            'redo': ['cmd', 'y'],  # CSP uses Cmd+Y instead of Cmd+Shift+Z
            'save': ['cmd', 's'],
            
            # Navigation
            'zoom_in': ['cmd', '+'],
            'zoom_out': ['cmd', '-'],
            'zoom_fit': ['cmd', '0'],
            'rotate_left': ['cmd', 'shift', '['],  # CSP uses Shift modifier
            'rotate_right': ['cmd', 'shift', ']'],
            'rotate_reset': ['cmd', 'shift', '0'],
            
            # Tools
            'tool_brush': ['b'],
            'tool_eraser': ['e'],
            'tool_pan': ['h'],  # CSP uses H instead of Space
            'tool_select': ['m'],  # CSP uses M instead of R
            'tool_eyedropper': ['i'],  # CSP uses I
            'tool_hand': ['h'],
            
            # Layers
            'layer_new': ['cmd', 'shift', 'n'],
            'layer_delete': ['delete'],
            'layer_duplicate': ['cmd', 'j'],
            'layer_merge_down': ['cmd', 'e'],
            
            # Brush
            'brush_size_up': [']'],
            'brush_size_down': ['['],
            'brush_opacity_up': ['shift', ']'],  # CSP different opacity controls
            'brush_opacity_down': ['shift', '['],
        }
    }
}

# Current active profile
current_profile = 'krita'  # Default to Krita

async def handle_client(websocket):
    print(f"✅ Android app connected: {websocket.remote_address}")
    
    # Send available profiles to the Android app
    await websocket.send(json.dumps({
        "type": "profiles",
        "profiles": {key: profile['name'] for key, profile in APP_PROFILES.items()},
        "current": current_profile
    }))
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get('action')
                value = data.get('value')
                
                print(f"📱 Command: {action} (Profile: {APP_PROFILES[current_profile]['name']})")
                
                # Handle profile switching
                if action == 'set_profile':
                    global current_profile
                    profile_key = value
                    if profile_key in APP_PROFILES:
                        current_profile = profile_key
                        profile_name = APP_PROFILES[current_profile]['name']
                        print(f"🎨 Switched to profile: {profile_name}")
                        await websocket.send(json.dumps({
                            "status": "profile_changed", 
                            "profile": profile_key,
                            "name": profile_name
                        }))
                    continue
                
                # Get current shortcuts
                shortcuts = APP_PROFILES[current_profile]['shortcuts']
                
                # Handle zoom commands
                if action == 'zoom':
                    direction = value.get('direction', 'in') if value else 'in'
                    intensity = value.get('intensity', 1.0) if value else 1.0
                    steps = max(1, int(intensity * 2))
                    
                    if direction == 'in':
                        for _ in range(steps):
                            pyautogui.hotkey(*shortcuts['zoom_in'])
                            await asyncio.sleep(0.02)
                    elif direction == 'out':
                        for _ in range(steps):
                            pyautogui.hotkey(*shortcuts['zoom_out'])
                            await asyncio.sleep(0.02)
                    elif direction == 'fit':
                        pyautogui.hotkey(*shortcuts['zoom_fit'])
                    
                    await websocket.send(json.dumps({"status": "executed", "action": action}))
                    
                # Handle rotate commands
                elif action == 'rotate':
                    degrees = value if value else 0
                    steps = max(1, int(abs(degrees) / 10))
                    
                    if degrees > 0:
                        for _ in range(steps):
                            pyautogui.hotkey(*shortcuts['rotate_right'])
                            await asyncio.sleep(0.02)
                    elif degrees < 0:
                        for _ in range(steps):
                            pyautogui.hotkey(*shortcuts['rotate_left'])
                            await asyncio.sleep(0.02)
                    elif degrees == 0:  # Reset rotation
                        pyautogui.hotkey(*shortcuts['rotate_reset'])
                    
                    await websocket.send(json.dumps({"status": "executed", "action": action}))
                    
                # Handle button commands
                elif action in shortcuts:
                    keys = shortcuts[action]
                    pyautogui.hotkey(*keys)
                    print(f"🎨 Executed: {' + '.join(keys)}")
                    await websocket.send(json.dumps({"status": "executed", "action": action}))
                    
                else:
                    print(f"❓ Unknown action: {action}")
                    await websocket.send(json.dumps({"status": "unknown", "action": action}))
                    
            except json.JSONDecodeError:
                print("❌ Invalid JSON received")
                await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON"}))
            except Exception as e:
                print(f"❌ Error: {e}")
                await websocket.send(json.dumps({"status": "error", "message": str(e)}))
                
    except websockets.exceptions.ConnectionClosed:
        print("👋 Android app disconnected")

async def main():
    print("✅ Starting WebSocket server on port 8765...")
    print(f"🎨 Available profiles: {', '.join([p['name'] for p in APP_PROFILES.values()])}")
    print(f"🎯 Current profile: {APP_PROFILES[current_profile]['name']}")
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        print("🎨 Ready for art commands!")
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
