#!/usr/bin/env python3
import asyncio
import websockets
import json
import pyautogui
import logging
import platform

print("🎨 Art Remote Control Server - WORKING VERSION")
print("=" * 50)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Platform-specific shortcuts (macOS)
shortcuts = {
    'undo': ['cmd', 'z'],
    'redo': ['cmd', 'shift', 'z'],
    'zoom_in': ['cmd', '+'],
    'zoom_out': ['cmd', '-'],
    'rotate_left': ['cmd', '['],
    'rotate_right': ['cmd', ']'],
    'tool_brush': ['b'],
    'tool_eraser': ['e'],
    'tool_pan': ['space'],
    'tool_select': ['r'],
    'layer_new': ['cmd', 'shift', 'n'],
    'layer_delete': ['delete'],
    'brush_size_up': [']'],
    'brush_size_down': ['['],
    'save': ['cmd', 's'],
}

async def handle_client(websocket, path):
    logger.info(f"✅ Android app connected: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get('action')
                value = data.get('value')
                
                logger.info(f"📱 Received command: {action}")
                
                if action == 'zoom':
                    direction = value.get('direction', 'in') if value else 'in'
                    intensity = value.get('intensity', 1.0) if value else 1.0
                    steps = max(1, int(intensity * 2))
                    
                    if direction == 'in':
                        for _ in range(steps):
                            pyautogui.hotkey(*shortcuts['zoom_in'])
                            await asyncio.sleep(0.02)
                    else:
                        for _ in range(steps):
                            pyautogui.hotkey(*shortcuts['zoom_out'])
                            await asyncio.sleep(0.02)
                    
                    await websocket.send(json.dumps({"status": "executed", "action": action}))
                    
                elif action == 'rotate':
                    degrees = value if value else 0
                    steps = max(1, int(abs(degrees) / 10))
                    
                    if degrees > 0:
                        for _ in range(steps):
                            pyautogui.hotkey(*shortcuts['rotate_right'])
                            await asyncio.sleep(0.02)
                    else:
                        for _ in range(steps):
                            pyautogui.hotkey(*shortcuts['rotate_left'])
                            await asyncio.sleep(0.02)
                    
                    await websocket.send(json.dumps({"status": "executed", "action": action}))
                    
                elif action in shortcuts:
                    keys = shortcuts[action]
                    pyautogui.hotkey(*keys)
                    logger.info(f"🎨 Executed: {' + '.join(keys)}")
                    await websocket.send(json.dumps({"status": "executed", "action": action}))
                    
                else:
                    logger.warning(f"❓ Unknown action: {action}")
                    await websocket.send(json.dumps({"status": "unknown", "action": action}))
                    
            except json.JSONDecodeError:
                logger.error("❌ Invalid JSON received")
                await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON"}))
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                await websocket.send(json.dumps({"status": "error", "message": str(e)}))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("👋 Android app disconnected")

# Start the server
async def main():
    logger.info("🚀 Starting Art Remote Control Server...")
    logger.info(f"📱 Platform: {platform.system()}")
    logger.info("🔌 Server will listen on 0.0.0.0:8765")
    logger.info("📲 Connect your Android app now!")
    
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        logger.info("✅ WebSocket server is running!")
        logger.info("🎨 Ready for art commands from your Android app!")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")