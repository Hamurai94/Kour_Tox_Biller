#!/usr/bin/env python3
"""
Digital Art Remote Control - Cross-Platform Server
Receives commands from Android app and controls Krita/Clip Studio Paint on Windows and macOS
"""

import asyncio
import websockets
import json
import logging
import pyautogui
import psutil
import sys
import platform
import time
import threading
import http.server
import socketserver
import os
import sqlite3
from pathlib import Path

# Platform-specific imports
if platform.system() == "Darwin":  # macOS
    import AppKit
    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
elif platform.system() == "Windows":  # Windows
    import win32gui
    import win32con

# GUI imports - try tkinter first, fallback to basic console
try:
    import tkinter as tk
    from tkinter import ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("GUI not available, running in console mode")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CrossPlatformArtRemoteServer:
    def __init__(self, host='0.0.0.0', port=8765, http_port=8080):
        self.host = host
        self.port = port
        self.http_port = http_port
        self.clients = set()
        self.current_app = None
        self.is_running = False
        self.platform = platform.system()
        self.http_server = None
        self.csp_favorites = {}  # Store dynamic F-key assignments
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
        
        # Cross-platform art application configurations
        self.app_configs = {
            'krita': {
                'process_names': {
                    'Windows': ['krita.exe'],
                    'Darwin': ['krita', 'Krita']
                },
                'window_titles': ['krita'],
                'shortcuts': {
                    'Windows': {
                        'undo': ['ctrl', 'z'],
                        'redo': ['ctrl', 'shift', 'z'],
                        'zoom_in': ['ctrl', '+'],
                        'zoom_out': ['ctrl', '-'],
                        'rotate_left': ['ctrl', '['],
                        'rotate_right': ['ctrl', ']'],
                        'tool_brush': ['b'],
                        'tool_eraser': ['e'],
                        'tool_pan': ['space'],
                        'tool_select': ['r'],
                        'layer_new': ['ctrl', 'shift', 'n'],
                        'layer_delete': ['delete'],
                        'brush_size_up': [']'],
                        'brush_size_down': ['[']
                    },
                    'Darwin': {  # macOS - Windows key = cmd key
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
                        'layer_new': ['ctrl', 'shift', 'n'],
                        'layer_delete': ['delete'],
                        'brush_size_up': [']'],
                        'brush_size_down': ['[']
                    }
                }
            },
            'clip_studio_paint': {
                'process_names': {
                    'Windows': ['CLIPStudioPaint.exe', 'CLIPStudio.exe'],
                    'Darwin': ['CLIP STUDIO PAINT', 'ClipStudioPaint']
                },
                'window_titles': ['clip studio', 'clipstudio'],
                'shortcuts': {
                    'Windows': {
                        'undo': ['ctrl', 'z'],
                        'redo': ['ctrl', 'y'],
                        'zoom_in': ['ctrl', '+'],
                        'zoom_out': ['ctrl', '-'],
                        'rotate_left': ['ctrl', 'shift', '['],
                        'rotate_right': ['ctrl', 'shift', ']'],
                        'tool_brush': ['b'],
                        'tool_pen': ['p'],
                        'tool_pencil': ['c'],
                        'tool_airbrush': ['a'],
                        'tool_decoration': ['d'],
                        'tool_blend': ['j'],
                        'tool_liquify': ['q'],
                        'tool_eraser': ['e'],
                        'tool_pan': ['h'],
                        'tool_select': ['m'],
                        'layer_new': ['ctrl', 'shift', 'n'],
                        'layer_delete': ['delete'],
                        'brush_size_up': [']'],
                        'brush_size_down': ['[']
                    },
                    'Darwin': {
                        'undo': ['ctrl', 'z'],
                        'redo': ['ctrl', 'y'],
                        'zoom_in': ['ctrl', '+'],
                        'zoom_out': ['ctrl', '-'],
                        'rotate_left': ['ctrl', 'shift', '['],
                        'rotate_right': ['ctrl', 'shift', ']'],
                        'tool_brush': ['b'],
                        'tool_pen': ['p'],
                        'tool_pencil': ['c'],
                        'tool_airbrush': ['a'],
                        'tool_decoration': ['d'],
                        'tool_blend': ['j'],
                        'tool_liquify': ['q'],
                        'tool_eraser': ['e'],
                        'tool_pan': ['h'],
                        'tool_select': ['m'],
                        'layer_new': ['ctrl', 'shift', 'n'],
                        'layer_delete': ['delete'],
                        'brush_size_up': [']'],
                        'brush_size_down': ['[']
                    }
                }
            }
        }
        
        logger.info(f"Initialized Art Remote Server for {self.platform}")
        
        # Load CSP shortcuts on startup
        self.load_csp_shortcuts()
        
    def load_csp_shortcuts(self):
        """ULTIMATE CSP shortcut loader - reads BOTH databases!"""
        try:
            # Database paths - cross-platform
            if platform.system() == 'Darwin':
                menu_db = Path.home() / "Library/CELSYS/CLIPStudioPaintVer1_5_0/Shortcut/default.khc"
                tool_db = Path.home() / "Library/CELSYS/CLIPStudioPaintVer1_5_0/Tool/EditImageTool.todb"
            else:  # Windows
                # Windows CSP paths
                csp_base = Path.home() / "AppData/Roaming/CELSys/CLIPStudioPaintVer1_5_0"
                menu_db = csp_base / "Shortcut/default.khc"
                tool_db = csp_base / "Tool/EditImageTool.todb"
            
            ultimate_shortcuts = {}
            
            # Step 1: Parse menu shortcuts
            if menu_db.exists():
                logger.info("📋 Loading menu shortcuts...")
                conn = sqlite3.connect(str(menu_db))
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT menucommandtype, menucommand, shortcut, modifier 
                    FROM shortcutmenu 
                    WHERE shortcut LIKE 'F%' AND shortcut IS NOT NULL
                """)
                
                for row in cursor.fetchall():
                    command_type, command, key, modifier = row
                    
                    ultimate_shortcuts[key] = {
                        'command': command,
                        'description': self.get_command_description(command),
                        'icon': self.get_command_icon(command),
                        'source': 'menu',
                        'modifier': modifier
                    }
                    
                    logger.info(f"📋 {key}: {ultimate_shortcuts[key]['icon']} {ultimate_shortcuts[key]['description']}")
                
                conn.close()
            
            # Step 2: Parse custom tool shortcuts - THE BREAKTHROUGH!
            if tool_db.exists():
                logger.info("🎨 Loading custom tool shortcuts...")
                conn = sqlite3.connect(str(tool_db))
                cursor = conn.cursor()
                
                # F-key encoding: NodeShortCutKey = 36 + F_number
                f_key_offset = 36
                
                cursor.execute("""
                    SELECT NodeName, NodeShortCutKey 
                    FROM Node 
                    WHERE NodeShortCutKey BETWEEN ? AND ?
                """, (f_key_offset + 1, f_key_offset + 12))
                
                for row in cursor.fetchall():
                    node_name, shortcut_key = row
                    
                    # Calculate F-key number
                    f_number = shortcut_key - f_key_offset
                    f_key = f"F{f_number}"
                    
                    ultimate_shortcuts[f_key] = {
                        'command': f'custom_tool_{shortcut_key}',
                        'description': node_name,
                        'icon': self.get_tool_icon(node_name),
                        'source': 'tool',
                        'tool_name': node_name,
                        'shortcut_key': shortcut_key
                    }
                    
                    logger.info(f"🎨 {f_key}: {ultimate_shortcuts[f_key]['icon']} {node_name}")
                
                conn.close()
            
            self.csp_favorites = ultimate_shortcuts
            
            logger.info(f"🚀 ULTIMATE LOADING COMPLETE: {len(ultimate_shortcuts)} F-key assignments!")
                
        except Exception as e:
            logger.error(f"❌ Error loading ultimate shortcuts: {e}")
    
    def get_tool_icon(self, tool_name: str) -> str:
        """Get icon for custom tools based on name"""
        name_lower = tool_name.lower()
        
        if 'watercolor' in name_lower:
            return '💧'
        elif 'brush' in name_lower:
            return '🖌️'
        elif 'pen' in name_lower:
            return '🖊️'
        elif 'pencil' in name_lower:
            return '✏️'
        elif 'eraser' in name_lower:
            return '🧽'
        elif 'airbrush' in name_lower:
            return '🎨'
        else:
            return '🔧'
    
    def get_command_description(self, command: str) -> str:
        """Convert CSP command names to readable descriptions"""
        descriptions = {
            'cut': 'Cut',
            'copy': 'Copy',
            'paste': 'Paste', 
            'undo': 'Undo',
            'redo': 'Redo',
            'helponlinehowto': 'Help/Tutorial',
            'subtoolprevioussubtool': 'Previous Sub-tool',
            'subtoolnextsubtool': 'Next Sub-tool',
            'selectinvert': 'Invert Selection'
        }
        return descriptions.get(command, command.replace('_', ' ').title())
    
    def get_command_icon(self, command: str) -> str:
        """Get appropriate icon for CSP commands"""
        icons = {
            'cut': '✂️',
            'copy': '📋', 
            'paste': '📥',
            'undo': '↶',
            'redo': '↷',
            'helponlinehowto': '❓',
            'subtoolprevioussubtool': '⬅️',
            'subtoolnextsubtool': '➡️',
            'selectinvert': '🔄'
        }
        return icons.get(command, '🔧')
        
    async def register_client(self, websocket, path):
        """Register a new client connection"""
        self.clients.add(websocket)
        logger.info(f"Client connected from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        finally:
            self.clients.remove(websocket)
    
    async def handle_message(self, websocket, message):
        """Handle incoming messages from Android app"""
        try:
            data = json.loads(message)
            logger.info(f"Received command: {data}")
            
            action = data.get('action')
            value = data.get('value')
            
            # Detect current art application (with error handling)
            try:
                self.detect_current_app()
            except Exception as e:
                logger.warning(f"App detection failed: {e}")
                # Continue anyway - we can still execute shortcuts
            
            if action == 'zoom':
                await self.handle_zoom(value)
            elif action == 'rotate':
                await self.handle_rotate(value)
            elif action == 'undo':
                await self.execute_shortcut('undo')
            elif action == 'redo':
                await self.execute_shortcut('redo')
            elif action == 'tool':
                # Handle tool switching
                tool_name = value.get('name') if isinstance(value, dict) else None
                if not tool_name and isinstance(value, str):
                    # Parse string format like "{name=brush}"
                    if 'name=' in value:
                        tool_name = value.split('name=')[1].strip('{}')
                
                logger.info(f"🛠️ TOOL SWITCH: {tool_name}")
                if tool_name == 'brush':
                    pyautogui.press('b')
                elif tool_name == 'eraser':
                    pyautogui.press('e')
                elif tool_name == 'pan':
                    pyautogui.press('h')
                elif tool_name == 'select':
                    pyautogui.press('m')
                else:
                    logger.warning(f"❓ Unknown tool: {tool_name}")
                    
            elif action == 'scroll':
                # Handle scroll-based zoom (like mouse wheel)
                direction = value.get('direction') if isinstance(value, dict) else None
                if not direction and isinstance(value, str):
                    if 'direction=up' in value:
                        direction = 'up'
                    elif 'direction=down' in value:
                        direction = 'down'
                
                logger.info(f"🖱️ SCROLL {direction}")
                if direction == 'up':
                    logger.info("⚡ Scrolling up (zoom in)...")
                    pyautogui.scroll(3)  # Positive scroll = zoom in
                elif direction == 'down':
                    logger.info("⚡ Scrolling down (zoom out)...")
                    pyautogui.scroll(-3)  # Negative scroll = zoom out
                    
            elif action == 'select_brush' or action == 'select_subtool' or action == 'select_tool':
                # Handle CSP tool/brush selection
                if isinstance(value, dict):
                    tool_name = value.get('tool', 'Unknown')
                    subtool_name = value.get('subtool_name', value.get('tool_name', value.get('name', 'Unknown')))
                    subtool_uuid = value.get('subtool_uuid', value.get('uuid', ''))
                elif isinstance(value, str):
                    # Parse string format like "{tool=pen, tool_name=Pen}"
                    tool_name = 'Unknown'
                    subtool_name = 'Unknown'
                    subtool_uuid = ''
                    
                    # Extract tool name
                    if 'tool=' in value:
                        tool_part = value.split('tool=')[1].split(',')[0].split('}')[0].strip()
                        tool_name = tool_part
                        
                    # Extract tool_name for subtool_name
                    if 'tool_name=' in value:
                        name_part = value.split('tool_name=')[1].split(',')[0].split('}')[0].strip()
                        subtool_name = name_part
                        
                    # Extract UUID if present
                    if 'subtool_uuid=' in value:
                        uuid_part = value.split('subtool_uuid=')[1].split(',')[0].split('}')[0].strip()
                        subtool_uuid = uuid_part
                else:
                    tool_name = 'Unknown'
                    subtool_name = 'Unknown'
                    subtool_uuid = ''
                
                logger.info(f"🎨 SELECTING CSP TOOL: {tool_name} -> {subtool_name}")
                logger.info(f"🆔 UUID: {subtool_uuid}")
                
                # Handle different tool types
                if tool_name.lower() == 'favorites':
                    # Handle favorite sub-tools (F1-F12)
                    # Extract F-key from subtool_uuid (e.g., "F5")
                    f_key = subtool_uuid
                    
                    if f_key.startswith('F') and f_key[1:].isdigit():
                        logger.info(f"⭐ Pressing favorite shortcut: {f_key} -> {subtool_name}")
                        # Press the actual F-key
                        pyautogui.press(f_key.lower())  # f1, f2, f3, etc.
                    else:
                        logger.warning(f"❓ Invalid F-key format: {subtool_uuid}")
                        
                else:
                    # Handle main tool groups (existing logic)
                    csp_shortcut_map = {
                        'pen_group': 'p',           # Cycles Pen/Pencil
                        'brush_group': 'b',         # Cycles Brush/Airbrush/Decoration  
                        'blend_group': 'j',         # Cycles Blend/Liquify
                        'eraser': 'e',
                        'selection': 'm',
                        'fill': 'g',                # Cycles Fill/Gradient
                        'eyedropper': 'i'
                    }
                    
                    # Get the appropriate shortcut key
                    shortcut_key = csp_shortcut_map.get(tool_name.lower())
                    
                    if shortcut_key:
                        logger.info(f"🔧 Pressing CSP shortcut: {shortcut_key} (for {tool_name})")
                        pyautogui.press(shortcut_key)
                    else:
                        logger.warning(f"❓ No shortcut mapped for tool: {tool_name}")
                
                # Add a small delay to ensure tool switch completes
                await asyncio.sleep(0.1)
                
                # For specific sub-tools, we could potentially:
                # 1. Use keyboard shortcuts to cycle through sub-tools (if CSP supports it)
                # 2. Use screen automation to click on specific brushes
                # 3. Use CSP's automation features (if available)
                # For now, switching to the main tool category is a good start
                
            elif action == 'layer_up':
                # Change to layer above (Alt + ])
                logger.info("📚 Moving to layer above...")
                pyautogui.hotkey('alt', ']')
                
            elif action == 'layer_down':
                # Change to layer below (Alt + [)
                logger.info("📚 Moving to layer below...")
                pyautogui.hotkey('alt', '[')
                
            elif action == 'canvas_pan':
                # Handle canvas panning with Hand tool
                direction = value.get('direction') if isinstance(value, dict) else None
                if not direction and isinstance(value, str):
                    if 'direction=left' in value:
                        direction = 'left'
                    elif 'direction=right' in value:
                        direction = 'right'
                
                logger.info(f"🖐️ Canvas pan {direction}")
                # Switch to hand tool temporarily, then back
                pyautogui.press('h')  # Switch to hand tool
                await asyncio.sleep(0.1)
                # Simulate drag movement
                if direction == 'left':
                    pyautogui.drag(-100, 0, duration=0.2)
                elif direction == 'right':
                    pyautogui.drag(100, 0, duration=0.2)
                    
            elif action == 'rotate_left':
                # CSP rotate left: - (minus key)
                logger.info("↺ Rotating canvas left...")
                pyautogui.press('-')
                
            elif action == 'rotate_right':
                # CSP rotate right: Try actual caret character
                logger.info("↻ Rotating canvas right...")
                # Method 1: Try typing actual ^ character
                pyautogui.typewrite('^')
                # Method 2: Alternative - try shift+6 with delay
                # await asyncio.sleep(0.05)
                # pyautogui.hotkey('shift', '6')
                
            elif action == 'reset_canvas':
                # Reset canvas view (Ctrl + @)
                logger.info("🏠 Resetting canvas view...")
                pyautogui.hotkey('cmd', '2')  # Ctrl+@ on Mac might be Cmd+2
                
            elif action == 'get_favorites':
                # Re-scan CSP shortcuts in case user made changes
                logger.info("📤 Android app requested F-key favorites...")
                logger.info("🔄 Re-scanning CSP shortcuts for latest changes...")
                self.load_csp_shortcuts()  # Refresh from database
                logger.info(f"🔍 Available CSP favorites: {list(self.csp_favorites.keys())}")
                
                # Build favorites data with all F1-F12
                favorites_data = {}
                for i in range(1, 13):
                    f_key = f"F{i}"
                    if f_key in self.csp_favorites:
                        fav_data = self.csp_favorites[f_key]
                        favorites_data[f_key] = {
                            'assigned': True,
                            'icon': fav_data['icon'],
                            'description': fav_data['description'],
                            'command': fav_data['command']
                        }
                        logger.info(f"✅ {f_key}: {fav_data['icon']} {fav_data['description']}")
                    else:
                        favorites_data[f_key] = {
                            'assigned': False,
                            'icon': '➕',
                            'description': f'Available F{i}',
                            'command': None
                        }
                        logger.info(f"➕ {f_key}: Available")
                
                # Send to client
                response = {
                    "action": "favorites_data",
                    "favorites": favorites_data,
                    "total_assigned": len(self.csp_favorites)
                }
                
                logger.info(f"📤 Sending favorites response: {json.dumps(response, indent=2)}")
                await websocket.send(json.dumps(response))
                logger.info("✅ Favorites data sent to Android app!")
                return  # Don't send the standard confirmation
                
            elif action == 'brush_size':
                # Handle brush size changes
                delta = value.get('delta') if isinstance(value, dict) else None
                if not delta and isinstance(value, str):
                    # Parse string format like "{delta=5}"
                    if 'delta=' in value:
                        delta = int(value.split('delta=')[1].strip('{}'))
                
                logger.info(f"🖌️ BRUSH SIZE: {delta}")
                if delta and delta > 0:
                    pyautogui.press(']')
                elif delta and delta < 0:
                    pyautogui.press('[')
                    
            elif action == 'layer_new':
                # CSP New Raster Layer: Ctrl + Shift + N (from official docs)
                logger.info("➕ Creating new raster layer...")
                if platform.system() == 'Darwin':
                    pyautogui.hotkey('cmd', 'shift', 'n')
                else:
                    pyautogui.hotkey('ctrl', 'shift', 'n')
                
            elif action == 'layer_folder':
                # CSP Create folder and insert layer: Ctrl + G (from official docs)
                logger.info("📁 Creating new folder...")
                if platform.system() == 'Darwin':
                    pyautogui.hotkey('cmd', 'g')
                else:
                    pyautogui.hotkey('ctrl', 'g')
                
            elif action == 'layer_merge':
                # CSP Merge Layer: E key
                logger.info("🔗 Merging layer...")
                pyautogui.press('e')
                
            elif action == 'layer_delete':
                # CSP Delete Layer: Delete key
                logger.info("🗑️ Deleting layer...")
                pyautogui.press('delete')
                
            elif action == 'layer_goto_first':
                # Go to first layer - simulate multiple layer down presses
                logger.info("🏠 Going to Layer 1...")
                for _ in range(20):  # Press [ many times to get to bottom layer
                    pyautogui.press('[')
                    await asyncio.sleep(0.05)
                    
            elif action == 'layer':
                # Handle legacy layer actions for backward compatibility
                layer_action = value.get('action') if isinstance(value, dict) else None
                if not layer_action and isinstance(value, str):
                    if 'action=new' in value:
                        layer_action = 'new'
                    elif 'action=delete' in value:
                        layer_action = 'delete'
                
                if layer_action == 'new':
                    logger.info("➕ Creating new layer (legacy)...")
                    pyautogui.press('n')
                elif layer_action == 'delete':
                    logger.info("🗑️ Deleting layer (legacy)...")
                    pyautogui.press('delete')
                    
            elif action.startswith('tool_') or action.startswith('layer_') or action.startswith('brush_'):
                await self.execute_shortcut(action)
            else:
                logger.warning(f"Unknown action: {action}")
            
            # Send confirmation back to client to keep connection alive
            try:
                response = {"status": "received", "action": action}
                await websocket.send(json.dumps(response))
            except Exception as e:
                logger.warning(f"Failed to send response: {e}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # Send error response
            try:
                error_response = {"status": "error", "message": str(e)}
                await websocket.send(json.dumps(error_response))
            except:
                pass  # Connection might be dead
    
    def detect_current_app(self):
        """Detect which art application is currently active - cross-platform"""
        try:
            if self.platform == "Darwin":  # macOS
                self._detect_current_app_macos()
            elif self.platform == "Windows":
                self._detect_current_app_windows()
            else:
                logger.warning(f"Unsupported platform: {self.platform}")
                
        except Exception as e:
            logger.error(f"Error detecting current app: {e}")
            self.current_app = None
    
    def _detect_current_app_macos(self):
        """Detect current app on macOS"""
        try:
            # Get the frontmost (active) application
            workspace = AppKit.NSWorkspace.sharedWorkspace()
            active_app = workspace.frontmostApplication()
            
            if active_app:
                app_name = active_app.localizedName().lower()
                bundle_id = active_app.bundleIdentifier()
                
                logger.debug(f"Active app: {app_name}, Bundle ID: {bundle_id}")
                
                # Check for Krita
                if 'krita' in app_name or (bundle_id and 'krita' in bundle_id.lower()):
                    self.current_app = 'krita'
                    return
                
                # Check for Clip Studio Paint
                if 'clip studio' in app_name or 'clipstudio' in app_name:
                    self.current_app = 'clip_studio_paint'
                    return
            
            # Fallback: check running processes
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name'].lower()
                if 'krita' in proc_name:
                    self.current_app = 'krita'
                    return
                elif 'clipstudio' in proc_name or 'clip' in proc_name:
                    self.current_app = 'clip_studio_paint'
                    return
                    
            self.current_app = None
            
        except Exception as e:
            logger.error(f"Error in macOS app detection: {e}")
            self.current_app = None
    
    def _detect_current_app_windows(self):
        """Detect current app on Windows"""
        try:
            # Get the active window
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd).lower()
            
            # Check for Krita
            if 'krita' in window_title:
                self.current_app = 'krita'
                return
            
            # Check for Clip Studio Paint
            if 'clip studio' in window_title or 'clipstudio' in window_title:
                self.current_app = 'clip_studio_paint'
                return
            
            # Fallback: check running processes
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name'].lower()
                if 'krita' in proc_name:
                    self.current_app = 'krita'
                    return
                elif 'clipstudio' in proc_name or 'clip' in proc_name:
                    self.current_app = 'clip_studio_paint'
                    return
                    
            self.current_app = None
            
        except Exception as e:
            logger.error(f"Error in Windows app detection: {e}")
            self.current_app = None
    
    async def handle_zoom(self, value):
        """Handle zoom commands"""
        if not value:
            return
            
        # Handle string format like "{direction=in, amount=1.5}"
        if isinstance(value, str):
            direction = 'in'
            if 'direction=out' in value:
                direction = 'out'
        else:
            direction = value.get('direction', 'in')
        
        logger.info(f"🔍 ZOOM {direction}")
        
        if direction == 'in':
            logger.info("⚡ Executing zoom in...")
            pyautogui.hotkey('cmd', '+')
        else:
            logger.info("⚡ Executing zoom out...")
            pyautogui.hotkey('cmd', '-')
    
    async def handle_rotate(self, degrees):
        """Handle canvas rotation"""
        if degrees is None:
            return
            
        # Handle string format like "{degrees=15.0}" or actual number
        rotation_value = 0
        if isinstance(degrees, str):
            if 'degrees=' in degrees:
                try:
                    rotation_value = float(degrees.split('degrees=')[1].strip('{}'))
                except:
                    rotation_value = 15.0
        else:
            rotation_value = degrees
            
        logger.info(f"🔄 ROTATE {rotation_value} degrees")
        
        if rotation_value > 0:
            logger.info("⚡ Rotating canvas clockwise...")
            # CSP rotate right: ^ (shift+6 on US keyboard)
            pyautogui.hotkey('shift', '6')
        else:
            logger.info("⚡ Rotating canvas counter-clockwise...")
            # CSP rotate left: - (minus key)
            pyautogui.press('-')
    
    async def execute_shortcut(self, action):
        """Execute keyboard shortcut for the given action - cross-platform"""
        if not self.current_app or self.current_app not in self.app_configs:
            logger.warning(f"No supported app detected. Current: {self.current_app}")
            return
            
        app_config = self.app_configs[self.current_app]
        platform_shortcuts = app_config['shortcuts'].get(self.platform)
        
        if not platform_shortcuts or action not in platform_shortcuts:
            logger.warning(f"Action '{action}' not configured for {self.current_app} on {self.platform}")
            return
        
        try:
            keys = platform_shortcuts[action]
            logger.info(f"Executing {action}: {' + '.join(keys)} on {self.platform}")
            
            # Execute the key combination
            pyautogui.hotkey(*keys)
            
        except Exception as e:
            logger.error(f"Error executing shortcut {action}: {e}")
    
    def start_http_server(self):
        """Start HTTP server to serve web interface"""
        class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                # Set the directory to serve files from
                super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
            
            def do_GET(self):
                if self.path == '/' or self.path == '/remote':
                    self.path = '/web_remote.html'
                return super().do_GET()
        
        try:
            self.http_server = socketserver.TCPServer(("", self.http_port), CustomHTTPRequestHandler)
            server_thread = threading.Thread(target=self.http_server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            logger.info(f"HTTP server started on port {self.http_port}")
            logger.info(f"Web interface available at: http://localhost:{self.http_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            return False
    async def start_server(self):
        """Start the WebSocket server and HTTP server"""
        logger.info(f"Starting Cross-Platform Art Remote Server on {self.host}:{self.port}")
        self.is_running = True
        
        # Start HTTP server for web interface
        self.start_http_server()
        
        # Use the modern websockets pattern - handler takes only websocket parameter
        async def websocket_handler(websocket):
            await self.register_client(websocket, "/")
        
        async with websockets.serve(websocket_handler, self.host, self.port):
            logger.info("WebSocket server started successfully!")
            logger.info(f"🌐 Open http://localhost:{self.http_port} on your phone to control your PC!")
            await asyncio.Future()  # Run forever
    
    def stop_server(self):
        """Stop the server"""
        self.is_running = False
        logger.info("Server stopped")

# Cross-platform GUI class
class CrossPlatformServerGUI:
    def __init__(self):
        self.server = CrossPlatformArtRemoteServer()
        self.server_thread = None
        self.platform = platform.system()
        
        if GUI_AVAILABLE:
            self._create_gui()
        else:
            self._run_console_mode()
        
    def _create_gui(self):
        """Create GUI interface"""
        self.root = tk.Tk()
        self.root.title(f"Art Remote Control Server ({self.platform})")
        self.root.geometry("450x350")
        
        # Server status
        self.status_var = tk.StringVar(value="Stopped")
        self._create_widgets()
        
    def _create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title with platform info
        title_text = f"🎨 Art Remote Control Server\n{self.platform} Edition"
        title_label = ttk.Label(main_frame, text=title_text, 
                               font=('Arial', 14, 'bold'), justify='center')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status
        ttk.Label(main_frame, text="Status:").grid(row=1, column=0, sticky=tk.W)
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                foreground="red")
        status_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Platform info
        ttk.Label(main_frame, text="Platform:").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(main_frame, text=self.platform).grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Server info
        ttk.Label(main_frame, text="Address:").grid(row=3, column=0, sticky=tk.W)
        ttk.Label(main_frame, text=f"{self.server.host}:{self.server.port}").grid(
            row=3, column=1, sticky=tk.W, padx=(10, 0))
        
        # Current app
        self.app_var = tk.StringVar(value="None detected")
        ttk.Label(main_frame, text="Current App:").grid(row=4, column=0, sticky=tk.W)
        self.app_label = ttk.Label(main_frame, textvariable=self.app_var)
        self.app_label.grid(row=4, column=1, sticky=tk.W, padx=(10, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        
        self.start_button = ttk.Button(button_frame, text="Start Server", 
                                      command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Server", 
                                     command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Platform-specific shortcuts info
        info_frame = ttk.LabelFrame(main_frame, text="Keyboard Shortcuts", padding="5")
        info_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0), sticky=(tk.W, tk.E))
        
        if self.platform == "Darwin":
            shortcut_text = "macOS: Uses ⌘ (Cmd) key for most shortcuts"
        else:
            shortcut_text = "Windows: Uses Ctrl key for most shortcuts"
            
        ttk.Label(info_frame, text=shortcut_text, font=('Arial', 9)).pack()
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=7, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_frame, height=6, width=50)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        # Start app detection timer
        self.update_app_status()
        
    def _run_console_mode(self):
        """Run in console mode if GUI not available"""
        print(f"🎨 Art Remote Control Server - {self.platform} Edition")
        print("=" * 50)
        print("GUI not available, running in console mode")
        print(f"Server will start on {self.server.host}:{self.server.port}")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        # Start server directly
        try:
            asyncio.run(self.server.start_server())
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        except Exception as e:
            print(f"Server error: {e}")
    
    def start_server(self):
        """Start the server in a separate thread"""
        if not GUI_AVAILABLE:
            return
            
        if self.server_thread is None or not self.server_thread.is_alive():
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            
            self.status_var.set("Running")
            self.app_label.configure(foreground="green")
            self.start_button.configure(state=tk.DISABLED)
            self.stop_button.configure(state=tk.NORMAL)
            
            self.log("Server started successfully!")
    
    def stop_server(self):
        """Stop the server"""
        if not GUI_AVAILABLE:
            return
            
        self.server.stop_server()
        
        self.status_var.set("Stopped")
        self.app_label.configure(foreground="red")
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        
        self.log("Server stopped")
    
    def run_server(self):
        """Run the server in asyncio event loop"""
        try:
            asyncio.run(self.server.start_server())
        except Exception as e:
            if GUI_AVAILABLE:
                self.log(f"Server error: {e}")
    
    def update_app_status(self):
        """Update the current app status"""
        if not GUI_AVAILABLE:
            return
            
        self.server.detect_current_app()
        app_name = self.server.current_app or "None detected"
        self.app_var.set(app_name.replace('_', ' ').title())
        
        # Schedule next update
        self.root.after(2000, self.update_app_status)
    
    def log(self, message):
        """Add message to log"""
        if not GUI_AVAILABLE:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")
            return
            
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def run(self):
        """Run the GUI or console interface"""
        if GUI_AVAILABLE:
            self.root.mainloop()
        # Console mode runs automatically in __init__

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = ['websockets', 'pyautogui', 'psutil', 'pynput']
    
    # Platform-specific packages
    if platform.system() == "Darwin":
        required_packages.append('pyobjc-framework-Cocoa')
        required_packages.append('pyobjc-framework-Quartz')
    elif platform.system() == "Windows":
        required_packages.append('pywin32')
    
    missing_packages = []
    
    try:
        import websockets
        import pyautogui
        import psutil
        import pynput
        
        if platform.system() == "Darwin":
            import AppKit
            import Quartz
        elif platform.system() == "Windows":
            import win32gui
            
    except ImportError as e:
        package_name = str(e).split("'")[1] if "'" in str(e) else "unknown"
        missing_packages.append(package_name)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print(f"Please install: pip install {' '.join(required_packages)}")
        return False
    
    return True

if __name__ == "__main__":
    print(f"🎨 Art Remote Control Server - {platform.system()} Edition")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Run the server GUI
    try:
        gui = CrossPlatformServerGUI()
        gui.run()
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
