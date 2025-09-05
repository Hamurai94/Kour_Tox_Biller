#!/usr/bin/env python3
"""
TourBox Killer - Cross-Platform Server
Modern WebSocket server with GUI interface for Mac and PC
"""

import asyncio
import websockets
import json
import threading
import webbrowser
from pathlib import Path
import socket
import sys
import time
from datetime import datetime

# Cross-platform imports
try:
    import pynput
    from pynput import keyboard, mouse
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
    print("Warning: pynput not available - some features may be limited")

try:
    import pyautogui
    HAS_PYAUTOGUI = True
    # Disable pyautogui failsafe for smooth operation
    pyautogui.FAILSAFE = False
except ImportError:
    HAS_PYAUTOGUI = False
    print("Warning: pyautogui not available - some features may be limited")

class TourBoxKillerServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.is_running = False
        self.stats = {
            "start_time": None,
            "connections": 0,
            "messages_sent": 0,
            "messages_received": 0
        }
        
    async def register_client(self, websocket):
        """Register a new client connection"""
        self.clients.add(websocket)
        self.stats["connections"] += 1
        print(f"✅ Client connected. Total clients: {len(self.clients)}")
        
    async def unregister_client(self, websocket):
        """Unregister a client connection"""
        self.clients.discard(websocket)
        print(f"❌ Client disconnected. Total clients: {len(self.clients)}")
        
    async def handle_client(self, websocket, path):
        """Handle individual client connections"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.process_message(message, websocket)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
            
    async def process_message(self, message, websocket):
        """Process incoming messages from clients"""
        try:
            data = json.loads(message)
            self.stats["messages_received"] += 1
            
            action_type = data.get("type", "unknown")
            print(f"🎮 Action: {action_type}")
            
            # Execute the action
            result = await self.execute_action(data)
            
            # Send response back to client
            response = {
                "status": "success" if result else "error",
                "action": action_type,
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(response))
            self.stats["messages_sent"] += 1
            
        except json.JSONDecodeError:
            error_response = {"status": "error", "message": "Invalid JSON"}
            await websocket.send(json.dumps(error_response))
        except Exception as e:
            error_response = {"status": "error", "message": str(e)}
            await websocket.send(json.dumps(error_response))
            
    async def execute_action(self, data):
        """Execute the requested action"""
        action_type = data.get("type")
        
        if not HAS_PYAUTOGUI and not HAS_PYNPUT:
            print("⚠️  No automation libraries available")
            return False
            
        try:
            if action_type == "zoom":
                return self.handle_zoom(data)
            elif action_type == "rotate":
                return self.handle_rotate(data)
            elif action_type == "undo":
                return self.handle_undo()
            elif action_type == "redo":
                return self.handle_redo()
            elif action_type == "tool":
                return self.handle_tool_switch(data)
            elif action_type == "brush_size":
                return self.handle_brush_size(data)
            elif action_type == "layer":
                return self.handle_layer(data)
            else:
                print(f"❓ Unknown action: {action_type}")
                return False
                
        except Exception as e:
            print(f"❌ Error executing {action_type}: {e}")
            return False
            
    def handle_zoom(self, data):
        """Handle zoom in/out actions"""
        direction = data.get("direction", "in")
        amount = data.get("amount", 1)
        
        if HAS_PYNPUT:
            # Use Ctrl + Plus/Minus for zoom
            if direction == "in":
                keyboard.Controller().press(keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl)
                keyboard.Controller().press(keyboard.KeyCode.from_char('+'))
                keyboard.Controller().release(keyboard.KeyCode.from_char('+'))
                keyboard.Controller().release(keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl)
            else:
                keyboard.Controller().press(keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl)
                keyboard.Controller().press(keyboard.KeyCode.from_char('-'))
                keyboard.Controller().release(keyboard.KeyCode.from_char('-'))
                keyboard.Controller().release(keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl)
            return True
        return False
        
    def handle_rotate(self, data):
        """Handle canvas rotation"""
        direction = data.get("direction", "clockwise")
        # Implement rotation logic (app-specific)
        # This would need to be customized for each art application
        print(f"🔄 Rotating {direction}")
        return True
        
    def handle_undo(self):
        """Handle undo action"""
        if HAS_PYNPUT:
            keyboard.Controller().press(keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl)
            keyboard.Controller().press(keyboard.KeyCode.from_char('z'))
            keyboard.Controller().release(keyboard.KeyCode.from_char('z'))
            keyboard.Controller().release(keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl)
            return True
        return False
        
    def handle_redo(self):
        """Handle redo action"""
        if HAS_PYNPUT:
            keyboard.Controller().press(keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl)
            keyboard.Controller().press(keyboard.Key.shift)
            keyboard.Controller().press(keyboard.KeyCode.from_char('z'))
            keyboard.Controller().release(keyboard.KeyCode.from_char('z'))
            keyboard.Controller().release(keyboard.Key.shift)
            keyboard.Controller().release(keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl)
            return True
        return False
        
    def handle_tool_switch(self, data):
        """Handle tool switching"""
        tool = data.get("tool", "brush")
        # Tool switching shortcuts (customize for your art app)
        tool_shortcuts = {
            "brush": "b",
            "eraser": "e", 
            "pan": "h",
            "select": "v"
        }
        
        if tool in tool_shortcuts and HAS_PYNPUT:
            key = tool_shortcuts[tool]
            keyboard.Controller().press(keyboard.KeyCode.from_char(key))
            keyboard.Controller().release(keyboard.KeyCode.from_char(key))
            return True
        return False
        
    def handle_brush_size(self, data):
        """Handle brush size changes"""
        direction = data.get("direction", "increase")
        # Use bracket keys for brush size (common in art apps)
        if HAS_PYNPUT:
            key = ']' if direction == "increase" else '['
            keyboard.Controller().press(keyboard.KeyCode.from_char(key))
            keyboard.Controller().release(keyboard.KeyCode.from_char(key))
            return True
        return False
        
    def handle_layer(self, data):
        """Handle layer operations"""
        action = data.get("action", "new")
        if action == "new" and HAS_PYNPUT:
            # Ctrl+Shift+N for new layer (common shortcut)
            keyboard.Controller().press(keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl)
            keyboard.Controller().press(keyboard.Key.shift)
            keyboard.Controller().press(keyboard.KeyCode.from_char('n'))
            keyboard.Controller().release(keyboard.KeyCode.from_char('n'))
            keyboard.Controller().release(keyboard.Key.shift)
            keyboard.Controller().release(keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl)
            return True
        return False
        
    def get_local_ip(self):
        """Get the local IP address"""
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
            
    async def start_server(self):
        """Start the WebSocket server"""
        self.stats["start_time"] = datetime.now()
        self.is_running = True
        
        print("🚀 Starting TourBox Killer Server...")
        print(f"📡 Server: ws://{self.get_local_ip()}:{self.port}")
        print(f"🌐 Web UI: http://{self.get_local_ip()}:{self.port + 1}")
        print("=" * 50)
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever
            
    def create_web_ui(self):
        """Create the web-based UI HTML"""
        local_ip = self.get_local_ip()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TourBox Killer Server</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .logo {{
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .status {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .status-card {{
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 15px;
            flex: 1;
            min-width: 200px;
            text-align: center;
        }}
        
        .status-value {{
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .status-label {{
            opacity: 0.8;
            font-size: 0.9rem;
        }}
        
        .connection-info {{
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }}
        
        .connection-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
        
        .connection-row:last-child {{
            margin-bottom: 0;
        }}
        
        .qr-section {{
            text-align: center;
            margin-top: 20px;
        }}
        
        .indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }}
        
        .online {{
            background: #4ade80;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .footer {{
            text-align: center;
            margin-top: 30px;
            opacity: 0.7;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎮 TourBox Killer</div>
            <div class="subtitle">Cross-Platform Art Remote Server</div>
        </div>
        
        <div class="status">
            <div class="status-card">
                <div class="status-value" id="clients">0</div>
                <div class="status-label">Connected Clients</div>
            </div>
            <div class="status-card">
                <div class="status-value" id="uptime">00:00:00</div>
                <div class="status-label">Uptime</div>
            </div>
            <div class="status-card">
                <div class="status-value" id="messages">0</div>
                <div class="status-label">Messages Processed</div>
            </div>
        </div>
        
        <div class="connection-info">
            <h3 style="margin-bottom: 15px;">
                <span class="indicator online"></span>Server Status: Online
            </h3>
            <div class="connection-row">
                <strong>WebSocket URL:</strong>
                <code>ws://{local_ip}:{self.port}</code>
            </div>
            <div class="connection-row">
                <strong>Local IP:</strong>
                <code>{local_ip}</code>
            </div>
            <div class="connection-row">
                <strong>Port:</strong>
                <code>{self.port}</code>
            </div>
            <div class="connection-row">
                <strong>Platform:</strong>
                <code>{sys.platform}</code>
            </div>
        </div>
        
        <div class="qr-section">
            <p><strong>📱 Connect your Android app to:</strong></p>
            <p style="font-size: 1.2rem; margin: 10px 0; font-family: monospace; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px;">
                ws://{local_ip}:{self.port}
            </p>
        </div>
        
        <div class="footer">
            <p>🔥 Replacing expensive hardware with code since 2025</p>
        </div>
    </div>
    
    <script>
        // Update stats periodically
        function updateStats() {{
            // This would connect to a stats endpoint if we had one
            // For now, just update the uptime
            const startTime = new Date().getTime() - 1000; // Placeholder
            const now = new Date().getTime();
            const uptime = Math.floor((now - startTime) / 1000);
            
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            const seconds = uptime % 60;
            
            document.getElementById('uptime').textContent = 
                String(hours).padStart(2, '0') + ':' +
                String(minutes).padStart(2, '0') + ':' +
                String(seconds).padStart(2, '0');
        }}
        
        setInterval(updateStats, 1000);
        updateStats();
    </script>
</body>
</html>
        """
        
        return html_content

def main():
    print("🎮 TourBox Killer Server")
    print("=" * 30)
    
    # Create server instance
    server = TourBoxKillerServer()
    
    # Create and save web UI
    ui_content = server.create_web_ui()
    ui_path = Path("server_ui.html")
    ui_path.write_text(ui_content)
    
    # Open web UI in browser
    ui_url = f"file://{ui_path.absolute()}"
    print(f"🌐 Opening web UI: {ui_url}")
    webbrowser.open(ui_url)
    
    # Start the server
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()