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
from auth import SimpleAuth, AuthenticatedConnection
import argparse

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
    def __init__(self, host='127.0.0.1', port=8765, http_port=8080, require_auth=True):
        # Security: Default to localhost only, not 0.0.0.0
        self.host = host
        self.port = port
        self.http_port = http_port
        self.require_auth = require_auth
        self.clients = set()
        self.authenticated_clients = {}  # websocket -> AuthenticatedConnection
        self.current_app = None
        self.is_running = False
        self.platform = platform.system()
        self.http_server = None
        self.csp_favorites = {}  # Store dynamic F-key assignments
        
        # Initialize authentication system
        if self.require_auth:
            self.auth = SimpleAuth()
            logger.info("🔐 Authentication system initialized")
            auth_info = self.auth.get_connection_info()
            logger.info(f"🔑 Connection PIN: {auth_info['pin']}")
        else:
            self.auth = None
            logger.warning("⚠️ Authentication disabled - server is open to all connections!")
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
        
        # Cross-platform art application configurations
        logger.info("🔍 DEBUG: Building app_configs...")
        self.app_configs = {
            'krita': {
                'process_names': {
                    'Windows': ['krita.exe'],
                    'Darwin': ['krita', 'Krita']
                },
                'window_titles': ['krita'],
                'shortcuts': {
                    'Windows': {  # COMPLETE KRITA PROFILE FOR WINDOWS
                        # Basic Commands
                        'undo': ['ctrl', 'z'],
                        'redo': ['ctrl', 'shift', 'z'],  # Krita uses Shift+Z, not Y
                        'save': ['ctrl', 's'],
                        
                        # Navigation - Krita specific
                        'zoom_in': ['ctrl', '+'],
                        'zoom_out': ['ctrl', '-'],
                        'zoom_fit': ['ctrl', '0'],
                        'rotate_left': ['ctrl', '['],  # NO SHIFT (different from CSP)
                        'rotate_right': ['ctrl', ']'],  # NO SHIFT (different from CSP)
                        'reset_rotation': ['5'],
                        'reset_zoom': ['1'],
                        
                        # Tools - Krita specific shortcuts (FIXED)
                        'tool_brush': ['b'],  # Freehand Brush
                        'tool_pencil': ['n'],  # Pencil tool (different from CSP)
                        'tool_airbrush': ['a'],  # Airbrush (separate tool)
                        'tool_eraser': ['e'],
                        'tool_select': ['ctrl', 'r'],  # Rectangle Select Tool (needs Ctrl)
                        'tool_pan': ['h'],  # Hand tool (not space hold)
                        'tool_eyedropper': ['p'],  # Color picker tool
                        'tool_clone': ['c'],  # Clone tool
                        'tool_healing': ['h'],  # Healing brush
                        'tool_transform': ['ctrl', 't'],
                        
                        # Layers - Krita
                        'layer_new': ['ctrl', 'shift', 'n'],
                        'layer_delete': ['delete'],
                        'layer_duplicate': ['ctrl', 'j'],
                        'layer_merge_down': ['ctrl', 'e'],
                        'layer_up': ['page_up'],
                        'layer_down': ['page_down'],
                        'layer_folder': ['ctrl', 'g'],
                        
                        # Brush Controls - Krita specific
                        'brush_size_up': [']'],
                        'brush_size_down': ['['],
                        'brush_opacity_up': ['o'],  # O key (different from CSP)
                        'brush_opacity_down': ['shift', 'o'],
                        'brush_flow_up': ['shift', ']'],
                        'brush_flow_down': ['shift', '['],
                        
                        # View
                        'toggle_fullscreen': ['tab'],
                        'mirror_view': ['m'],
                        'grid_toggle': ['shift', ';']
                    },
                    'Darwin': {  # macOS - COMPLETE KRITA PROFILE
                        # Basic Commands
                        'undo': ['cmd', 'z'],
                        'redo': ['cmd', 'shift', 'z'],  # Krita uses Shift+Z, not Y
                        'save': ['cmd', 's'],
                        
                        # Navigation - Krita specific
                        'zoom_in': ['cmd', '+'],
                        'zoom_out': ['cmd', '-'],
                        'zoom_fit': ['cmd', '0'],
                        'rotate_left': ['4'],  # Krita default: 4 key
                        'rotate_right': ['6'],  # Krita default: 6 key
                        'reset_rotation': ['5'],
                        'reset_zoom': ['1'],
                        
                        # Tools - Krita specific shortcuts (FIXED)
                        'tool_brush': ['b'],  # Freehand Brush
                        'tool_pencil': ['n'],  # Pencil tool (different from CSP)
                        'tool_airbrush': ['a'],  # Airbrush (separate tool)
                        'tool_eraser': ['e'],
                        'tool_select': ['ctrl', 'r'],  # Rectangle Select Tool (needs Ctrl)
                        'tool_pan': ['h'],  # Hand tool (not space hold)
                        'tool_eyedropper': ['p'],  # Color picker tool
                        'tool_clone': ['c'],  # Clone tool
                        'tool_healing': ['h'],  # Healing brush
                        'tool_transform': ['cmd', 't'],
                        
                        # Layers - Krita
                        'layer_new': ['cmd', 'shift', 'n'],
                        'layer_delete': ['delete'],
                        'layer_duplicate': ['cmd', 'j'],
                        'layer_merge_down': ['cmd', 'e'],
                        'layer_up': ['page_up'],
                        'layer_down': ['page_down'],
                        'layer_folder': ['cmd', 'g'],
                        
                        # Brush Controls - Krita specific
                        'brush_size_up': [']'],
                        'brush_size_down': ['['],
                        'brush_opacity_up': ['o'],  # O key (different from CSP)
                        'brush_opacity_down': ['shift', 'o'],
                        'brush_flow_up': ['shift', ']'],
                        'brush_flow_down': ['shift', '['],
                        
                        # View
                        'toggle_fullscreen': ['tab'],
                        'mirror_view': ['m'],
                        'grid_toggle': ['shift', ';']
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
        
        # DEBUG: Check if Krita Darwin shortcuts are loaded
        logger.info("🔍 DEBUG: Checking app_configs after build...")
        krita_config = self.app_configs.get('krita', {})
        darwin_shortcuts = krita_config.get('shortcuts', {}).get('Darwin', {})
        logger.info(f"🔍 DEBUG: Krita Darwin shortcuts loaded: {len(darwin_shortcuts)} items")
        if darwin_shortcuts:
            logger.info(f"🔍 DEBUG: Sample Darwin shortcuts: {list(darwin_shortcuts.keys())[:5]}")
        else:
            logger.error("🚨 CRITICAL: Darwin shortcuts are EMPTY!")
        
        logger.info(f"Initialized Art Remote Server for {self.platform}")
        
        # Load CSP shortcuts on startup
        self.load_csp_shortcuts()
        
        # Load Krita brush presets and REAL shortcuts
        self.load_krita_presets()
        self.load_krita_shortcuts()
        self.load_krita_brush_mappings()
        
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
    
    def load_krita_presets(self):
        """Load Krita brush presets from DATABASE - THE BREAKTHROUGH!"""
        try:
            from krita_database_parser import KritaDatabaseParser
            
            parser = KritaDatabaseParser()
            db_path = parser.find_database()
            
            if db_path:
                logger.info("🎨 Krita database found - loading ALL brush presets...")
                self.krita_palette = parser.build_complete_krita_palette()
                logger.info(f"✅ BREAKTHROUGH: Loaded {self.krita_palette['total_brushes']} Krita brush presets from database!")
                logger.info(f"📁 Categories: {list(self.krita_palette['categories'].keys())}")
            else:
                logger.info("⚠️ Krita database not found - using basic tool set")
                self.krita_palette = self._create_basic_krita_palette()
                
        except Exception as e:
            logger.error(f"Error loading Krita database: {e}")
            logger.info("📋 Falling back to basic palette")
            self.krita_palette = self._create_basic_krita_palette()
    
    def _create_basic_krita_palette(self):
        """Create basic Krita palette when presets can't be loaded"""
        return {
            'app': 'krita',
            'version': '1.0',
            'total_brushes': 8,
            'quick_access': [
                {'name': 'Basic Brush', 'icon': '🖌️', 'category': 'Basic'},
                {'name': 'Pencil', 'icon': '✏️', 'category': 'Basic'},
                {'name': 'Airbrush', 'icon': '💨', 'category': 'Basic'},
                {'name': 'Ink Pen', 'icon': '🖊️', 'category': 'Basic'},
                {'name': 'Watercolor', 'icon': '💧', 'category': 'Basic'},
                {'name': 'Oil Paint', 'icon': '🎨', 'category': 'Basic'},
                {'name': 'Charcoal', 'icon': '🖤', 'category': 'Basic'},
                {'name': 'Eraser', 'icon': '🧽', 'category': 'Basic'}
            ],
            'tools': {
                'brush': {
                    'name': 'Brush Engine',
                    'icon': '🖌️',
                    'shortcut': 'B',
                    'subcategories': {
                        'Basic': [
                            {'name': 'Basic Brush', 'icon': '🖌️'},
                            {'name': 'Pencil', 'icon': '✏️'},
                            {'name': 'Airbrush', 'icon': '💨'},
                            {'name': 'Ink Pen', 'icon': '🖊️'}
                        ]
                    }
                }
            }
        }
    
    def load_krita_shortcuts(self):
        """Load REAL Krita shortcuts from user's config"""
        try:
            from krita_shortcut_parser import KritaShortcutParser
            
            parser = KritaShortcutParser()
            real_shortcuts = parser.get_krita_profile_for_server()
            
            # DEBUG: Check what the parser returns
            logger.info(f"🔍 DEBUG: Parser returned shortcuts: {real_shortcuts}")
            logger.info(f"🔍 DEBUG: Darwin shortcuts from parser: {real_shortcuts.get('Darwin', 'NOT_FOUND')}")
            
            # Update the Krita config with REAL shortcuts
            if 'krita' in self.app_configs:
                # DON'T OVERWRITE - merge instead!
                logger.info("🚨 CRITICAL: NOT overwriting app_configs - keeping original!")
                # self.app_configs['krita']['shortcuts'] = real_shortcuts
                logger.info(f"✅ Kept original Krita shortcuts with {len(self.app_configs['krita']['shortcuts']['Darwin'])} Darwin shortcuts")
                
                # Log the actual shortcuts we're using
                platform_shortcuts = real_shortcuts.get(platform.system(), {})
                for action, keys in platform_shortcuts.items():
                    logger.info(f"🎯 Krita {action}: {' + '.join(keys)}")
            else:
                logger.warning("⚠️ Krita config not found in app_configs")
                
        except Exception as e:
            logger.error(f"Error loading Krita shortcuts: {e}")
            logger.info("📋 Using built-in Krita defaults")
    
    def load_krita_brush_mappings(self):
        """Load ULTIMATE Krita brush mappings - ALL 276 BRUSHES!"""
        try:
            from krita_ultimate_shortcut_generator import KritaUltimateShortcutGenerator
            
            generator = KritaUltimateShortcutGenerator()
            self.krita_brush_map = generator.get_complete_brush_map()
            
            logger.info(f"💥 NUCLEAR: Loaded shortcuts for {len(self.krita_brush_map)} brushes!")
            
            # Log breakdown by category
            by_category = {}
            for shortcut, brush_info in self.krita_brush_map.items():
                category = brush_info['category']
                if category not in by_category:
                    by_category[category] = 0
                by_category[category] += 1
            
            for category, count in by_category.items():
                logger.info(f"📁 {category}: {count} brushes with shortcuts")
                
        except Exception as e:
            logger.error(f"Error loading ultimate brush mappings: {e}")
            self.krita_brush_map = {}
    
    async def handle_krita_brush_selection(self, tool_name: str, subtool_name: str, subtool_uuid: str):
        """Handle Krita brush selection - SIMPLE NON-INVASIVE APPROACH!"""
        try:
            logger.info(f"🎨 SMART KRITA BRUSH SELECTION: {subtool_name}")
            
            # Use the smart brush switcher for actual preset switching
            from krita_smart_brush_switcher import KritaSmartBrushSwitcher
            
            switcher = KritaSmartBrushSwitcher()
            
            # Extract the actual brush name (remove icons and prefixes)
            clean_brush_name = subtool_uuid
            for icon in ["🖌️", "🎨", "💧", "📦", "💨", "✏️", "🧽", "✨"]:
                clean_brush_name = clean_brush_name.replace(icon, "").strip()
            
            logger.info(f"🔍 Cleaned brush name: '{clean_brush_name}'")
            
            # Try CORRECTED F6 docker approach first, fallback to smart emulation
            logger.info(f"🔍 Trying F6 docker approach for: {clean_brush_name}")
            
            try:
                # Try the corrected docker approach with F6
                success = await switcher.switch_to_brush_by_name(clean_brush_name)
                
                if success:
                    logger.info(f"✅ F6 Docker success: {clean_brush_name}")
                else:
                    logger.info(f"⚠️ F6 Docker failed, using smart emulation for: {clean_brush_name}")
                    self._smart_brush_emulation(clean_brush_name, subtool_uuid)
                    
            except Exception as e:
                logger.warning(f"❌ F6 Docker error: {e}")
                logger.info(f"🔄 Falling back to smart emulation for: {clean_brush_name}")
                self._smart_brush_emulation(clean_brush_name, subtool_uuid)
                
            logger.info(f"✅ Brush switching complete for: {clean_brush_name}")
            
        except Exception as e:
            logger.error(f"❌ Error in smart brush selection: {e}")
            # Fallback to tool category switching
            self._fallback_tool_switch(subtool_uuid)
    
    def _fallback_tool_switch(self, subtool_uuid: str):
        """Fallback to simple tool category switching"""
        try:
            name_lower = subtool_uuid.lower()
            
            if 'pencil' in name_lower:
                logger.info("✏️ Fallback: Switching to Pencil tool")
                pyautogui.press('n')  # Pencil tool
            elif 'eraser' in name_lower:
                logger.info("🧽 Fallback: Switching to Eraser tool") 
                pyautogui.press('e')  # Eraser tool
            elif 'airbrush' in name_lower or 'spray' in name_lower:
                logger.info("💨 Fallback: Switching to Airbrush tool")
                pyautogui.press('a')  # Airbrush tool
            elif 'ink' in name_lower or 'pen' in name_lower:
                logger.info("🖊️ Fallback: Switching to Brush tool (for ink)")
                pyautogui.press('b')  # Brush tool
            else:
                logger.info("🖌️ Fallback: Switching to default Brush tool")
                pyautogui.press('b')  # Default brush tool
                
        except Exception as e:
            logger.error(f"❌ Error in fallback tool switch: {e}")
    
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
        """Register a new client connection with authentication"""
        logger.info(f"Client connecting from {websocket.remote_address}")
        
        # Create authenticated connection wrapper
        if self.require_auth:
            auth_conn = AuthenticatedConnection(websocket, self.auth)
            
            # Send authentication challenge
            await websocket.send(json.dumps({
                'type': 'auth_required',
                'message': 'Authentication required',
                'methods': ['token', 'pin']
            }))
            
            # Wait for authentication
            auth_timeout = 30  # 30 second timeout
            auth_successful = False
            
            try:
                # Wait for auth message with timeout
                auth_message = await asyncio.wait_for(websocket.recv(), timeout=auth_timeout)
                auth_data = json.loads(auth_message)
                
                if auth_data.get('type') == 'authenticate':
                    auth_successful = await auth_conn.authenticate(auth_data)
                else:
                    await websocket.send(json.dumps({
                        'type': 'auth_response',
                        'success': False,
                        'message': 'Expected authentication message'
                    }))
                    
            except asyncio.TimeoutError:
                logger.warning(f"Authentication timeout for {websocket.remote_address}")
                await websocket.send(json.dumps({
                    'type': 'auth_response',
                    'success': False,
                    'message': 'Authentication timeout'
                }))
                return
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                return
            
            if not auth_successful:
                logger.warning(f"Authentication failed for {websocket.remote_address}")
                await websocket.close(code=1008, reason="Authentication failed")
                return
            
            # Store authenticated connection
            self.authenticated_clients[websocket] = auth_conn
            
        # Add to clients list only after authentication
        self.clients.add(websocket)
        logger.info(f"✅ Client authenticated and connected from {websocket.remote_address}")
        
        # Send current app info to newly connected client
        self.detect_current_app()
        await asyncio.sleep(0.1)  # Give detection time to complete
        await self.send_app_info(websocket)
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Client connection error: {e}")
        finally:
            # Clean up
            if websocket in self.clients:
                self.clients.remove(websocket)
            if websocket in self.authenticated_clients:
                del self.authenticated_clients[websocket]
    
    async def handle_message(self, websocket, message):
        """Handle incoming messages from Android app"""
        try:
            # Check authentication if required
            if self.require_auth and websocket not in self.authenticated_clients:
                logger.warning("Received message from unauthenticated client")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Authentication required'
                }))
                return
            
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
                await self.execute_app_shortcut('undo')
            elif action == 'redo':
                await self.execute_app_shortcut('redo')
            elif action == 'tool':
                # Handle tool switching
                tool_name = value.get('name') if isinstance(value, dict) else None
                if not tool_name and isinstance(value, str):
                    # Parse string format like "{name=brush}"
                    if 'name=' in value:
                        tool_name = value.split('name=')[1].strip('{}')
                
                logger.info(f"🛠️ TOOL SWITCH: {tool_name} for {self.current_app}")
                
                # Use app-specific shortcuts
                tool_action = f"tool_{tool_name}"
                await self.execute_app_shortcut(tool_action)
                    
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
                        
                elif tool_name.startswith('krita_') and self.current_app == 'krita':
                    # Handle Krita brush selection - THE NEW SYSTEM!
                    await self.handle_krita_brush_selection(tool_name, subtool_name, subtool_uuid)
                    
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
                logger.info("📚 Moving to layer above...")
                await self.execute_app_shortcut('layer_up')
                
            elif action == 'layer_down':
                logger.info("📚 Moving to layer below...")
                await self.execute_app_shortcut('layer_down')
                
            elif action == 'trackpad_pan':
                # Handle trackpad panning from phone gestures
                await self.handle_trackpad_pan(value)
                
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
                # Use app-specific rotation shortcuts
                logger.info("↺ Rotating canvas left...")
                await self.execute_app_shortcut('rotate_left')
                
            elif action == 'rotate_right':
                # Use app-specific rotation shortcuts  
                logger.info("↻ Rotating canvas right...")
                await self.execute_app_shortcut('rotate_right')
                
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
                logger.info("➕ Creating new raster layer...")
                await self.execute_app_shortcut('layer_new')
                
            elif action == 'layer_folder':
                logger.info("📁 Creating new folder...")
                await self.execute_app_shortcut('layer_folder')
                
            elif action == 'layer_merge':
                logger.info("🔗 Merging layer...")
                await self.execute_app_shortcut('layer_merge_down')
                
            elif action == 'layer_delete':
                logger.info("🗑️ Deleting layer...")
                await self.execute_app_shortcut('layer_delete')
                
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
                # Use app-specific shortcuts for all tool, layer, and brush actions
                await self.execute_app_shortcut(action)
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
                
                logger.info(f"🔍 ACTIVE APP: {app_name}, Bundle ID: {bundle_id}")
                
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
    
    async def send_app_info(self, websocket):
        """Send current detected app info to client for UI adaptation"""
        try:
            app_config = self.app_configs.get(self.current_app, {})
            platform_shortcuts = app_config.get('shortcuts', {}).get(platform.system(), {})
            
            app_info = {
                "action": "app_detected",
                "app": self.current_app,
                "app_name": self.current_app.replace('_', ' ').title() if self.current_app else None,
                "supported_tools": [action for action in platform_shortcuts.keys() if action.startswith('tool_')],
                "has_favorites": self.current_app == 'clip_studio_paint'  # Only CSP has F-key favorites
            }
            
            # Add Krita-specific brush data using NATIVE Krita structure
            if self.current_app == 'krita' and hasattr(self, 'krita_palette'):
                # Build data in the format the Android app expects
                krita_categories_dict = {}
                
                if 'categories' in self.krita_palette:
                    # Native Krita order (most important first)
                    native_order = ['Basic', 'Pencils', 'Paint', 'Ink', 'Watercolor', 'Digital', 'Airbrush', 'Erasers', 'Effects', 'Other']
                    
                    for category_name in native_order:
                        if category_name in self.krita_palette['categories']:
                            brushes = self.krita_palette['categories'][category_name]
                            
                            # Convert brushes to Android format
                            brush_list = []
                            for brush in brushes:
                                brush_list.append({
                                    'uuid': brush['name'],
                                    'name': f"{self._get_krita_category_icon(category_name)} {brush['name']}",
                                    'category': category_name
                                })
                            
                            # Add category with its brushes
                            krita_categories_dict[category_name] = brush_list
                
                app_info["krita_brushes"] = {
                    "categories": krita_categories_dict,
                    "total_brushes": sum(len(brushes) for brushes in krita_categories_dict.values())
                }
                
                total_brushes = sum(len(brushes) for brushes in krita_categories_dict.values())
                logger.info(f"🎨 Prepared {total_brushes} brushes in {len(krita_categories_dict)} native Krita categories")
            
            await websocket.send(json.dumps(app_info))
            logger.info(f"📤 Sent app info to client: {self.current_app}")
        except Exception as e:
            logger.error(f"Error sending app info: {e}")
    
    def _get_krita_category_icon(self, category):
        """Get appropriate icon for Krita native categories"""
        icons = {
            'Basic': '🖌️',
            'Pencils': '✏️', 
            'Paint': '🎨',
            'Ink': '🖊️',
            'Watercolor': '💧',
            'Digital': '💻',
            'Airbrush': '💨',
            'Erasers': '🧽',
            'Effects': '✨',
            'Other': '📦'
        }
        return icons.get(category, '🖌️')
    
    def _smart_brush_emulation(self, brush_name: str, subtool_uuid: str):
        """Smart brush emulation using tool + size + opacity - NO DOCKER!"""
        try:
            import time
            name_lower = brush_name.lower()
            
            # Step 1: Switch to appropriate tool
            if 'pencil' in name_lower or '2b' in name_lower or '4b' in name_lower:
                logger.info("✏️ Smart: Pencil tool + pencil settings")
                pyautogui.press('n')  # Pencil tool
                time.sleep(0.2)
                self._set_smart_brush_size('pencil', name_lower)
                
            elif 'eraser' in name_lower:
                logger.info("🧽 Smart: Eraser tool + eraser settings") 
                pyautogui.press('e')  # Eraser tool
                time.sleep(0.2)
                self._set_smart_brush_size('eraser', name_lower)
                
            elif 'airbrush' in name_lower or 'spray' in name_lower:
                logger.info("💨 Smart: Airbrush tool + airbrush settings")
                pyautogui.press('a')  # Airbrush tool
                time.sleep(0.2)
                self._set_smart_brush_size('airbrush', name_lower)
                
            elif 'ink' in name_lower or 'pen' in name_lower:
                logger.info("🖊️ Smart: Brush tool + ink settings")
                pyautogui.press('b')  # Brush tool
                time.sleep(0.2)
                self._set_smart_brush_size('ink', name_lower)
                
            elif 'wet' in name_lower or 'watercolor' in name_lower:
                logger.info("💧 Smart: Brush tool + watercolor settings")
                pyautogui.press('b')  # Brush tool  
                time.sleep(0.2)
                self._set_smart_brush_size('watercolor', name_lower)
                
            else:
                logger.info("🖌️ Smart: Default brush + adaptive settings")
                pyautogui.press('b')  # Default brush tool
                time.sleep(0.2)
                self._set_smart_brush_size('default', name_lower)
                
        except Exception as e:
            logger.error(f"❌ Error in smart brush emulation: {e}")
            
    def _set_smart_brush_size(self, brush_type: str, brush_name: str):
        """Set intelligent brush size based on type and name"""
        try:
            import time
            
            # Determine target size based on brush type and name
            if brush_type == 'pencil':
                if '2b' in brush_name:
                    target_presses = 3   # Small pencil
                elif '4b' in brush_name: 
                    target_presses = 5   # Medium pencil
                else:
                    target_presses = 4   # Default pencil
                    
            elif brush_type == 'airbrush':
                if 'soft' in brush_name:
                    target_presses = 12  # Large soft
                elif 'linear' in brush_name:
                    target_presses = 7   # Medium linear
                else:
                    target_presses = 9   # Default airbrush
                    
            elif brush_type == 'ink':
                target_presses = 5  # Precise ink
                
            elif brush_type == 'watercolor':
                target_presses = 10  # Flowing watercolor
                
            elif brush_type == 'eraser':
                if 'circle' in brush_name:
                    target_presses = 8   # Standard eraser
                else:
                    target_presses = 6   # Precise eraser
                    
            else:
                target_presses = 6  # Default medium
            
            # Reset size to small first (multiple [ presses)
            for _ in range(8):
                pyautogui.press('[')
                time.sleep(0.02)
            
            # Then increase to target size
            for _ in range(target_presses):
                pyautogui.press(']')
                time.sleep(0.02)
                
            logger.info(f"📏 Smart sized {brush_type} brush ({target_presses} increases)")
            
        except Exception as e:
            logger.error(f"❌ Error setting smart brush size: {e}")
    
    async def handle_trackpad_pan(self, value):
        """Handle trackpad panning gestures from phone"""
        try:
            # Parse the pan delta values
            if isinstance(value, dict):
                delta_x = float(value.get('deltaX', 0))
                delta_y = float(value.get('deltaY', 0))
            elif isinstance(value, str):
                # Parse string format if needed
                import re
                x_match = re.search(r'deltaX[=:]([+-]?\d*\.?\d+)', value)
                y_match = re.search(r'deltaY[=:]([+-]?\d*\.?\d+)', value)
                delta_x = float(x_match.group(1)) if x_match else 0
                delta_y = float(y_match.group(1)) if y_match else 0
            else:
                return
                
            logger.info(f"📱 Trackpad pan: X={delta_x:.1f}, Y={delta_y:.1f}")
            
            # Convert phone gestures to mouse movement
            # Use middle mouse drag for panning (common in art apps)
            
            # Get current mouse position
            current_x, current_y = pyautogui.position()
            
            # Calculate new position (scale the delta)
            scale_factor = 3  # Adjust sensitivity
            new_x = current_x + (delta_x * scale_factor)
            new_y = current_y + (delta_y * scale_factor)
            
            # Perform middle mouse drag for smooth panning
            pyautogui.mouseDown(button='middle')
            pyautogui.moveTo(new_x, new_y, duration=0.1)
            pyautogui.mouseUp(button='middle')
            
            logger.info(f"🖱️ Mouse pan: ({current_x}, {current_y}) → ({new_x:.0f}, {new_y:.0f})")
            
        except Exception as e:
            logger.error(f"❌ Error in trackpad pan: {e}")
    
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
    
    async def execute_app_shortcut(self, action):
        """Execute shortcut based on currently detected app"""
        logger.info(f"🔍 DEBUG: execute_app_shortcut called with action='{action}', current_app='{self.current_app}', platform='{platform.system()}'")
        
        if not self.current_app:
            logger.warning(f"No app detected, cannot execute {action}")
            return
            
        app_config = self.app_configs.get(self.current_app)
        if not app_config:
            logger.warning(f"No config found for app: {self.current_app}")
            logger.info(f"🔍 DEBUG: Available app configs: {list(self.app_configs.keys())}")
            return
            
        platform_shortcuts = app_config['shortcuts'].get(platform.system())
        if not platform_shortcuts:
            logger.warning(f"No shortcuts found for {self.current_app} on {platform.system()}")
            logger.info(f"🔍 DEBUG: Available platforms for {self.current_app}: {list(app_config['shortcuts'].keys())}")
            logger.info(f"🔍 DEBUG: Shortcuts config type: {type(platform_shortcuts)}")
            logger.info(f"🔍 DEBUG: Shortcuts config content: {platform_shortcuts}")
            return
            
        shortcut = platform_shortcuts.get(action)
        if not shortcut:
            logger.warning(f"No shortcut found for action '{action}' in {self.current_app}")
            logger.info(f"🔍 DEBUG: Available actions for {self.current_app} on {platform.system()}: {list(platform_shortcuts.keys())}")
            return
            
        logger.info(f"🎯 Executing {self.current_app} shortcut: {action} -> {shortcut}")
        
        try:
            if len(shortcut) == 1:
                pyautogui.press(shortcut[0])
            else:
                pyautogui.hotkey(*shortcut)
        except Exception as e:
            logger.error(f"Error executing shortcut {shortcut}: {e}")
    
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
    def __init__(self, require_auth=True, host='127.0.0.1'):
        self.server = CrossPlatformArtRemoteServer(host=host, require_auth=require_auth)
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
        
        # Authentication info
        if self.server.require_auth:
            auth_info = self.server.auth.get_connection_info()
            ttk.Label(main_frame, text="🔐 Connection PIN:", 
                     font=('Arial', 10, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(10, 0))
            pin_label = ttk.Label(main_frame, text=auth_info['pin'], 
                                 font=('Arial', 12, 'bold'), foreground="blue")
            pin_label.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
            
            # Add copy button for token (for advanced users)
            def copy_token():
                self.root.clipboard_clear()
                self.root.clipboard_append(auth_info['token'])
                self.root.update()  # Required for clipboard to work
                
            ttk.Button(main_frame, text="Copy Full Token", 
                      command=copy_token).grid(row=5, column=1, sticky=tk.W, padx=(10, 0))
            
            current_app_row = 6
        else:
            ttk.Label(main_frame, text="⚠️ No Authentication", 
                     foreground="red").grid(row=4, column=0, columnspan=2, pady=(10, 0))
            current_app_row = 5
        
        # Current app
        self.app_var = tk.StringVar(value="None detected")
        ttk.Label(main_frame, text="Current App:").grid(row=current_app_row, column=0, sticky=tk.W)
        self.app_label = ttk.Label(main_frame, textvariable=self.app_var)
        self.app_label.grid(row=current_app_row, column=1, sticky=tk.W, padx=(10, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=current_app_row+1, column=0, columnspan=2, pady=(20, 0))
        
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Art Remote Control Server')
    parser.add_argument('--no-auth', action='store_true', 
                       help='Disable authentication (INSECURE - for development only)')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host to bind to (default: 127.0.0.1 for security)')
    parser.add_argument('--allow-network', action='store_true',
                       help='Allow connections from network (sets host to 0.0.0.0)')
    
    args = parser.parse_args()
    
    # Security warnings
    if args.no_auth:
        print("⚠️  WARNING: Authentication disabled - server is open to all connections!")
        print("⚠️  This should ONLY be used for development!")
        
    if args.allow_network:
        args.host = '0.0.0.0'
        print(f"⚠️  WARNING: Server will accept connections from entire network ({args.host})")
        if args.no_auth:
            print("⚠️  CRITICAL: Network access + no auth = MAJOR SECURITY RISK!")
    
    print(f"🎨 Art Remote Control Server - {platform.system()} Edition")
    print("=" * 60)
    print(f"🔐 Authentication: {'DISABLED' if args.no_auth else 'ENABLED'}")
    print(f"🌐 Host: {args.host}")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Run the server GUI
    try:
        gui = CrossPlatformServerGUI(require_auth=not args.no_auth, host=args.host)
        gui.run()
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
