#!/usr/bin/env python3
"""
Digital Art Remote Control - PC Companion Server
Receives commands from Android app and controls Krita/Clip Studio Paint
"""

import asyncio
import websockets
import json
import logging
import pyautogui
import psutil
import sys
from typing import Dict, Any, Optional
import time
import tkinter as tk
from tkinter import ttk
import threading
from pynput import keyboard, mouse
import win32gui
import win32con

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArtRemoteServer:
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.current_app = None
        self.is_running = False
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01  # Small delay between commands
        
        # Art application configurations
        self.app_configs = {
            'krita': {
                'process_names': ['krita.exe', 'krita'],
                'shortcuts': {
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
                }
            },
            'clip_studio_paint': {
                'process_names': ['CLIPStudioPaint.exe', 'CLIPStudio.exe'],
                'shortcuts': {
                    'undo': ['ctrl', 'z'],
                    'redo': ['ctrl', 'y'],
                    'zoom_in': ['ctrl', '+'],
                    'zoom_out': ['ctrl', '-'],
                    'rotate_left': ['ctrl', 'shift', '['],
                    'rotate_right': ['ctrl', 'shift', ']'],
                    'tool_brush': ['b'],
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
            
            # Detect current art application
            self.detect_current_app()
            
            if action == 'zoom':
                await self.handle_zoom(value)
            elif action == 'rotate':
                await self.handle_rotate(value)
            elif action == 'undo':
                await self.execute_shortcut('undo')
            elif action == 'redo':
                await self.execute_shortcut('redo')
            elif action.startswith('tool_') or action.startswith('layer_') or action.startswith('brush_'):
                await self.execute_shortcut(action)
            else:
                logger.warning(f"Unknown action: {action}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def detect_current_app(self):
        """Detect which art application is currently active"""
        try:
            # Get the active window
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd).lower()
            
            # Check for Krita
            if 'krita' in window_title:
                self.current_app = 'krita'
            # Check for Clip Studio Paint
            elif 'clip studio' in window_title or 'clipstudio' in window_title:
                self.current_app = 'clip_studio_paint'
            else:
                # Fallback: check running processes
                for proc in psutil.process_iter(['name']):
                    proc_name = proc.info['name'].lower()
                    if 'krita' in proc_name:
                        self.current_app = 'krita'
                        break
                    elif 'clipstudio' in proc_name or 'clip' in proc_name:
                        self.current_app = 'clip_studio_paint'
                        break
                        
        except Exception as e:
            logger.error(f"Error detecting current app: {e}")
            self.current_app = None
    
    async def handle_zoom(self, value):
        """Handle zoom commands"""
        if not value:
            return
            
        direction = value.get('direction', 'in')
        intensity = value.get('intensity', 1.0)
        
        # Convert intensity to number of scroll steps
        steps = max(1, int(intensity * 3))
        
        if direction == 'in':
            for _ in range(steps):
                await self.execute_shortcut('zoom_in')
                await asyncio.sleep(0.05)
        else:
            for _ in range(steps):
                await self.execute_shortcut('zoom_out')
                await asyncio.sleep(0.05)
    
    async def handle_rotate(self, degrees):
        """Handle canvas rotation"""
        if degrees is None:
            return
            
        # Determine rotation direction and intensity
        steps = max(1, int(abs(degrees) / 5))  # 5 degrees per step
        
        if degrees > 0:
            for _ in range(steps):
                await self.execute_shortcut('rotate_right')
                await asyncio.sleep(0.05)
        else:
            for _ in range(steps):
                await self.execute_shortcut('rotate_left')
                await asyncio.sleep(0.05)
    
    async def execute_shortcut(self, action):
        """Execute keyboard shortcut for the given action"""
        if not self.current_app or self.current_app not in self.app_configs:
            logger.warning(f"No supported app detected. Current: {self.current_app}")
            return
            
        shortcuts = self.app_configs[self.current_app]['shortcuts']
        
        if action not in shortcuts:
            logger.warning(f"Action '{action}' not configured for {self.current_app}")
            return
        
        try:
            keys = shortcuts[action]
            logger.info(f"Executing {action}: {' + '.join(keys)}")
            
            # Execute the key combination
            pyautogui.hotkey(*keys)
            
        except Exception as e:
            logger.error(f"Error executing shortcut {action}: {e}")
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting Art Remote Server on {self.host}:{self.port}")
        self.is_running = True
        
        async with websockets.serve(self.register_client, self.host, self.port):
            logger.info("Server started successfully!")
            await asyncio.Future()  # Run forever
    
    def stop_server(self):
        """Stop the server"""
        self.is_running = False
        logger.info("Server stopped")

class ServerGUI:
    def __init__(self):
        self.server = ArtRemoteServer()
        self.server_thread = None
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title("Art Remote Control Server")
        self.root.geometry("400x300")
        
        # Server status
        self.status_var = tk.StringVar(value="Stopped")
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🎨 Art Remote Control Server", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status
        ttk.Label(main_frame, text="Status:").grid(row=1, column=0, sticky=tk.W)
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                foreground="red")
        status_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Server info
        ttk.Label(main_frame, text="Address:").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(main_frame, text=f"{self.server.host}:{self.server.port}").grid(
            row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Current app
        self.app_var = tk.StringVar(value="None detected")
        ttk.Label(main_frame, text="Current App:").grid(row=3, column=0, sticky=tk.W)
        self.app_label = ttk.Label(main_frame, textvariable=self.app_var)
        self.app_label.grid(row=3, column=1, sticky=tk.W, padx=(10, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        self.start_button = ttk.Button(button_frame, text="Start Server", 
                                      command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Server", 
                                     command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_frame, height=8, width=50)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Start app detection timer
        self.update_app_status()
        
    def start_server(self):
        """Start the server in a separate thread"""
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
            self.log(f"Server error: {e}")
    
    def update_app_status(self):
        """Update the current app status"""
        self.server.detect_current_app()
        app_name = self.server.current_app or "None detected"
        self.app_var.set(app_name.replace('_', ' ').title())
        
        # Schedule next update
        self.root.after(2000, self.update_app_status)
    
    def log(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    # Check if required packages are installed
    required_packages = ['websockets', 'pyautogui', 'psutil', 'pynput', 'pywin32']
    
    try:
        import websockets
        import pyautogui
        import psutil
        import pynput
        import win32gui
    except ImportError as e:
        print(f"Missing required package: {e}")
        print(f"Please install: pip install {' '.join(required_packages)}")
        sys.exit(1)
    
    # Run the server GUI
    gui = ServerGUI()
    gui.run()
