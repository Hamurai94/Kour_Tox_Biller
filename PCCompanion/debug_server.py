#!/usr/bin/env python3
"""
Debug version of the art remote server to see what's happening
"""

import asyncio
import websockets
import json
import logging
import pyautogui
import platform

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("🔍 DEBUG ART REMOTE SERVER")
print("=" * 50)

# Configure pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

# Clip Studio Paint shortcuts for macOS (as default)
shortcuts = {
    'undo': ['cmd', 'z'],
    'redo': ['cmd', 'y'],  # CSP uses Cmd+Y for redo
    'zoom_in': ['cmd', '+'],
    'zoom_out': ['cmd', '-'],
    'rotate_left': ['cmd', 'shift', '['],
    'rotate_right': ['cmd', 'shift', ']'],
    'tool_brush': ['b'],
    'tool_eraser': ['e'],
    'tool_pan': ['h'],  # CSP uses H for hand/pan tool
    'tool_select': ['m'],  # CSP uses M for selection tool
    'layer_new': ['cmd', 'shift', 'n'],
    'layer_delete': ['delete'],
    'brush_size_up': [']'],
    'brush_size_down': ['['],
    'save': ['cmd', 's'],
}

async def handle_client(websocket):
    logger.info(f"🔌 Client connected: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            try:
                logger.info(f"📨 RAW MESSAGE: {message}")
                data = json.loads(message)
                logger.info(f"📋 PARSED DATA: {data}")
                
                action = data.get('action')
                value = data.get('value')
                
                logger.info(f"🎯 ACTION: {action}")
                logger.info(f"💾 VALUE: {value}")
                
                if action == 'zoom':
                    direction = value.get('direction', 'in') if value else 'in'
                    logger.info(f"🔍 ZOOM {direction}")
                    if direction == 'in':
                        logger.info("⚡ Executing zoom in...")
                        pyautogui.hotkey(*shortcuts['zoom_in'])
                    else:
                        logger.info("⚡ Executing zoom out...")
                        pyautogui.hotkey(*shortcuts['zoom_out'])
                        
                elif action == 'rotate':
                    degrees = value.get('degrees', 0) if value else 0
                    logger.info(f"🔄 ROTATE {degrees} degrees")
                    # CSP canvas rotation: Hold R + drag mouse
                    logger.info("⚡ Executing canvas rotation...")
                    pyautogui.keyDown('r')
                    if degrees > 0:
                        pyautogui.drag(50, 0, duration=0.1)  # Drag right to rotate clockwise
                    else:
                        pyautogui.drag(-50, 0, duration=0.1)  # Drag left to rotate counter-clockwise
                    pyautogui.keyUp('r')
                        
                elif action == 'tool':
                    # Handle tool switching
                    tool_name = value.get('name') if isinstance(value, dict) else None
                    if not tool_name and isinstance(value, str):
                        # Parse string format like "{name=brush}"
                        if 'name=' in value:
                            tool_name = value.split('name=')[1].strip('{}')
                    
                    logger.info(f"🛠️ TOOL SWITCH: {tool_name}")
                    if tool_name == 'brush':
                        logger.info("⚡ Switching to brush tool...")
                        pyautogui.press('b')
                    elif tool_name == 'eraser':
                        logger.info("⚡ Switching to eraser tool...")
                        pyautogui.press('e')
                    elif tool_name == 'pan':
                        logger.info("⚡ Switching to pan tool...")
                        pyautogui.press('h')
                    elif tool_name == 'select':
                        logger.info("⚡ Switching to selection tool...")
                        pyautogui.press('m')
                    else:
                        logger.warning(f"❓ Unknown tool: {tool_name}")
                        
                elif action == 'brush_size':
                    # Handle brush size changes
                    delta = value.get('delta') if isinstance(value, dict) else None
                    if not delta and isinstance(value, str):
                        # Parse string format like "{delta=5}"
                        if 'delta=' in value:
                            delta = int(value.split('delta=')[1].strip('{}'))
                    
                    logger.info(f"🖌️ BRUSH SIZE: {delta}")
                    if delta and delta > 0:
                        logger.info("⚡ Increasing brush size...")
                        pyautogui.press(']')
                    elif delta and delta < 0:
                        logger.info("⚡ Decreasing brush size...")
                        pyautogui.press('[')
                        
                elif action in shortcuts:
                    logger.info(f"⚡ Executing {action}: {shortcuts[action]}")
                    pyautogui.hotkey(*shortcuts[action])
                    
                else:
                    logger.warning(f"❓ Unknown action: {action}")
                
                # Send confirmation
                response = {"status": "executed", "action": action}
                await websocket.send(json.dumps(response))
                logger.info(f"✅ Response sent: {response}")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON Error: {e}")
                logger.error(f"❌ Raw message was: {message}")
            except Exception as e:
                logger.error(f"❌ Error handling message: {e}")
                import traceback
                traceback.print_exc()
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("👋 Client disconnected")

async def main():
    logger.info("🚀 Starting debug server on 0.0.0.0:8765")
    logger.info(f"🖥️  Platform: {platform.system()}")
    logger.info("📱 Connect your Android app now!")
    
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        logger.info("✅ Debug server running!")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Debug server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
