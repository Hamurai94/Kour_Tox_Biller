#!/usr/bin/env python3
"""
Art Remote Control - GUI Server
Simple GUI version with clear IP/port display and connection status
"""

import asyncio
import websockets
import json
import logging
import pyautogui
import psutil
import platform
import time
import threading
import socket
import tkinter as tk
from tkinter import ttk
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArtRemoteGUI:
    def __init__(self):
        self.server = None
        self.server_thread = None
        self.clients = set()
        self.current_app = None
        self.is_running = False
        self.host = '0.0.0.0'
        self.port = 8765
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
        
        # Art app shortcuts for macOS
        self.shortcuts = {
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
        
        self.create_gui()
        
    def get_local_ip(self):
        """Get the local IP address"""
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def create_gui(self):
        """Create the GUI interface"""
        self.root = tk.Tk()
        self.root.title("🎨 Art Remote Control Server")
        self.root.geometry("500x600")
        self.root.configure(bg='#2b2b2b')
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = tk.Label(main_frame, text="🎨 Art Remote Control Server", 
                              font=('Arial', 18, 'bold'), bg='#2b2b2b', fg='white')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Server Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Server Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Status indicator
        tk.Label(status_frame, text="Status:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        self.status_var = tk.StringVar(value="Stopped")
        self.status_label = tk.Label(status_frame, textvariable=self.status_var, 
                                    font=('Arial', 12), fg='red')
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # IP Address
        tk.Label(status_frame, text="IP Address:", font=('Arial', 12, 'bold')).grid(row=1, column=0, sticky=tk.W)
        self.ip_var = tk.StringVar(value=self.get_local_ip())
        tk.Label(status_frame, textvariable=self.ip_var, font=('Arial', 12), fg='blue').grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Port
        tk.Label(status_frame, text="Port:", font=('Arial', 12, 'bold')).grid(row=2, column=0, sticky=tk.W)
        self.port_var = tk.StringVar(value=str(self.port))
        tk.Label(status_frame, textvariable=self.port_var, font=('Arial', 12), fg='blue').grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Connected clients
        tk.Label(status_frame, text="Connected:", font=('Arial', 12, 'bold')).grid(row=3, column=0, sticky=tk.W)
        self.clients_var = tk.StringVar(value="0 clients")
        tk.Label(status_frame, textvariable=self.clients_var, font=('Arial', 12), fg='green').grid(row=3, column=1, sticky=tk.W, padx=(10, 0))
        
        # Current app
        tk.Label(status_frame, text="Art App:", font=('Arial', 12, 'bold')).grid(row=4, column=0, sticky=tk.W)
        self.app_var = tk.StringVar(value="None detected")
        tk.Label(status_frame, textvariable=self.app_var, font=('Arial', 12), fg='orange').grid(row=4, column=1, sticky=tk.W, padx=(10, 0))
        
        # Connection Instructions
        connect_frame = ttk.LabelFrame(main_frame, text="Connection Instructions", padding="10")
        connect_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        instructions = f"""1. Install the Android APK on your device
2. Connect your Android device to the same WiFi network
3. Open the Art Remote app on your Android device
4. Enter this IP address: {self.get_local_ip()}
5. Enter port: {self.port}
6. Tap Connect!"""
        
        tk.Label(connect_frame, text=instructions, font=('Arial', 10), 
                justify=tk.LEFT, anchor='w').grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 20))
        
        self.start_button = tk.Button(button_frame, text="🚀 Start Server", 
                                     command=self.start_server, font=('Arial', 14, 'bold'),
                                     bg='#4CAF50', fg='white', width=15, height=2)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = tk.Button(button_frame, text="⏹️ Stop Server", 
                                    command=self.stop_server, font=('Arial', 14, 'bold'),
                                    bg='#f44336', fg='white', width=15, height=2, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Activity Log
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        self.log_text = tk.Text(log_frame, height=12, width=60, bg='#1e1e1e', fg='#00ff00', 
                               font=('Monaco', 10))
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Start status updates
        self.update_status()
        self.log("🎨 Art Remote Control Server GUI Ready!")
        self.log(f"📍 Your IP Address: {self.get_local_ip()}")
        self.log(f"🔌 Server Port: {self.port}")
        
    def log(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        logger.info(message)
        
    def start_server(self):
        """Start the WebSocket server"""
        if not self.is_running:
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            
            self.status_var.set("Starting...")
            self.status_label.configure(fg='orange')
            self.start_button.configure(state=tk.DISABLED)
            self.stop_button.configure(state=tk.NORMAL)
            
            self.log("🚀 Starting WebSocket server...")
            
    def stop_server(self):
        """Stop the WebSocket server"""
        self.is_running = False
        if self.server:
            self.server.close()
            
        self.status_var.set("Stopped")
        self.status_label.configure(fg='red')
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.clients_var.set("0 clients")
        
        self.log("⏹️ Server stopped")
        
    def run_server(self):
        """Run the WebSocket server in asyncio event loop"""
        try:
            asyncio.run(self.start_websocket_server())
        except Exception as e:
            self.log(f"❌ Server error: {e}")
            self.root.after(0, self.stop_server)
            
    async def start_websocket_server(self):
        """Start the WebSocket server"""
        self.is_running = True
        
        async def handle_client(websocket, path):
            await self.register_client(websocket)
            
        try:
            async with websockets.serve(handle_client, self.host, self.port):
                self.root.after(0, lambda: self.status_var.set("Running"))
                self.root.after(0, lambda: self.status_label.configure(fg='green'))
                self.root.after(0, lambda: self.log("✅ WebSocket server started successfully!"))
                self.root.after(0, lambda: self.log(f"📱 Waiting for Android app connections..."))
                
                while self.is_running:
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Failed to start server: {e}"))
            self.root.after(0, self.stop_server)
            
    async def register_client(self, websocket):
        """Register a new client connection"""
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0]
        self.root.after(0, lambda: self.log(f"📱 Android app connected from {client_ip}"))
        self.root.after(0, lambda: self.clients_var.set(f"{len(self.clients)} clients"))
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            self.root.after(0, lambda: self.log(f"📱 Android app disconnected ({client_ip})"))
        finally:
            self.clients.remove(websocket)
            self.root.after(0, lambda: self.clients_var.set(f"{len(self.clients)} clients"))
            
    async def handle_message(self, websocket, message):
        """Handle incoming messages from Android app"""
        try:
            data = json.loads(message)
            action = data.get('action') or data.get('type')
            
            if action:
                self.root.after(0, lambda: self.log(f"🎮 Command: {action}"))
                await self.execute_command(action, data)
                
                # Send confirmation
                response = {"status": "executed", "action": action}
                await websocket.send(json.dumps(response))
                
        except json.JSONDecodeError:
            self.root.after(0, lambda: self.log("❌ Invalid JSON received"))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Error: {e}"))
            
    async def execute_command(self, action, data):
        """Execute the received command"""
        try:
            if action == 'zoom':
                direction = data.get('direction', 'in')
                if direction == 'in':
                    pyautogui.hotkey(*self.shortcuts['zoom_in'])
                else:
                    pyautogui.hotkey(*self.shortcuts['zoom_out'])
                    
            elif action == 'rotate':
                degrees = data.get('degrees', 0)
                if degrees > 0:
                    pyautogui.hotkey(*self.shortcuts['rotate_right'])
                else:
                    pyautogui.hotkey(*self.shortcuts['rotate_left'])
                    
            elif action in self.shortcuts:
                pyautogui.hotkey(*self.shortcuts[action])
                
            elif action.startswith('tool_'):
                tool = action.replace('tool_', '')
                if f'tool_{tool}' in self.shortcuts:
                    pyautogui.hotkey(*self.shortcuts[f'tool_{tool}'])
                    
            elif action.startswith('brush_size'):
                if 'up' in action or 'delta' in data and data['delta'] > 0:
                    pyautogui.hotkey(*self.shortcuts['brush_size_up'])
                else:
                    pyautogui.hotkey(*self.shortcuts['brush_size_down'])
                    
            elif action.startswith('layer'):
                if 'new' in action or data.get('action') == 'new':
                    pyautogui.hotkey(*self.shortcuts['layer_new'])
                elif 'delete' in action or data.get('action') == 'delete':
                    pyautogui.hotkey(*self.shortcuts['layer_delete'])
                    
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Command failed: {e}"))
            
    def detect_art_app(self):
        """Detect if Krita or Clip Studio Paint is running"""
        try:
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name'].lower()
                if 'krita' in proc_name:
                    return 'Krita'
                elif 'clipstudio' in proc_name or 'clip' in proc_name:
                    return 'Clip Studio Paint'
            return 'None detected'
        except Exception:
            return 'Detection failed'
            
    def update_status(self):
        """Update the GUI status periodically"""
        # Update detected app
        detected_app = self.detect_art_app()
        if detected_app != self.current_app:
            self.current_app = detected_app
            self.app_var.set(detected_app)
            if detected_app != 'None detected':
                self.log(f"🎨 Detected: {detected_app}")
                
        # Schedule next update
        self.root.after(3000, self.update_status)
        
    def run(self):
        """Run the GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    print("🎨 Starting Art Remote Control GUI Server...")
    gui = ArtRemoteGUI()
    gui.run()
