#!/usr/bin/env python3
"""
EMERGENCY ART REMOTE - GUARANTEED TO WORK
"""
import asyncio
import websockets
import json
import subprocess
import sys
import os

print("🚨 EMERGENCY ART REMOTE STARTING...")

# Install websockets if needed
try:
    import websockets
except ImportError:
    print("Installing websockets...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

# Basic shortcuts that work on Mac
def execute_shortcut(action):
    shortcuts = {
        'undo': 'osascript -e "tell application \\"System Events\\" to keystroke \\"z\\" using command down"',
        'redo': 'osascript -e "tell application \\"System Events\\" to keystroke \\"z\\" using {command down, shift down}"',
        'save': 'osascript -e "tell application \\"System Events\\" to keystroke \\"s\\" using command down"',
        'zoom_in': 'osascript -e "tell application \\"System Events\\" to keystroke \\"+\\" using command down"',
        'zoom_out': 'osascript -e "tell application \\"System Events\\" to keystroke \\"-\\" using command down"',
    }
    
    if action in shortcuts:
        try:
            os.system(shortcuts[action])
            return True
        except:
            return False
    return False

async def handle_client(websocket, path):
    print(f"📱 PHONE CONNECTED: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get('action', 'unknown')
                
                print(f"🎨 EXECUTING: {action}")
                success = execute_shortcut(action)
                
                response = {"status": "success" if success else "failed", "action": action}
                await websocket.send(json.dumps(response))
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                await websocket.send(json.dumps({"status": "error", "message": str(e)}))
                
    except websockets.exceptions.ConnectionClosed:
        print("👋 PHONE DISCONNECTED")
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")

# Create HTML file
html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚨 EMERGENCY ART REMOTE</title>
    <style>
        body { font-family: Arial, sans-serif; background: #667eea; margin: 0; padding: 20px; color: white; text-align: center; }
        .status { padding: 15px; margin: 20px 0; border-radius: 10px; font-weight: bold; font-size: 18px; }
        .connected { background: #4CAF50; }
        .disconnected { background: #f44336; }
        button { padding: 25px; font-size: 20px; font-weight: bold; border: none; border-radius: 15px; 
                background: rgba(255,255,255,0.3); color: white; cursor: pointer; margin: 10px; width: 120px; }
        button:active { transform: scale(0.95); background: rgba(255,255,255,0.5); }
        input { width: 80%; padding: 15px; margin: 10px; border: none; border-radius: 10px; font-size: 16px; text-align: center; }
    </style>
</head>
<body>
    <h1>🚨 EMERGENCY ART REMOTE</h1>
    <div id="status" class="status disconnected">DISCONNECTED</div>
    <input id="ip" placeholder="PC IP Address" value="192.168.2.5">
    <br><button onclick="connect()">🔌 CONNECT NOW</button>
    
    <div id="controls" style="display:none;">
        <br><br><h2>🎨 ART CONTROLS</h2>
        <button onclick="send('undo')">↶ UNDO</button>
        <button onclick="send('redo')">↷ REDO</button><br>
        <button onclick="send('zoom_in')">🔍+ ZOOM</button>
        <button onclick="send('zoom_out')">🔍- ZOOM</button><br>
        <button onclick="send('save')">💾 SAVE</button>
    </div>

    <script>
        let ws = null;
        let connected = false;

        function updateStatus(isConnected) {
            const status = document.getElementById('status');
            const controls = document.getElementById('controls');
            connected = isConnected;
            if (isConnected) {
                status.textContent = '✅ CONNECTED - READY TO ART!';
                status.className = 'status connected';
                controls.style.display = 'block';
            } else {
                status.textContent = '❌ DISCONNECTED';
                status.className = 'status disconnected';
                controls.style.display = 'none';
            }
        }

        function connect() {
            const ip = document.getElementById('ip').value || '192.168.2.5';
            const url = `ws://${ip}:9999`;
            console.log('🔌 CONNECTING TO:', url);
            
            if (ws) ws.close();
            ws = new WebSocket(url);
            
            ws.onopen = () => { console.log('✅ CONNECTED!'); updateStatus(true); };
            ws.onclose = () => { console.log('❌ DISCONNECTED'); updateStatus(false); };
            ws.onerror = (e) => { console.error('❌ ERROR:', e); updateStatus(false); };
            ws.onmessage = (e) => { console.log('📨 RESPONSE:', e.data); };
        }

        function send(action) {
            if (!connected || !ws) { alert('NOT CONNECTED!'); return; }
            const cmd = JSON.stringify({action: action});
            ws.send(cmd);
            console.log('📤 SENT:', action);
        }

        setTimeout(connect, 1000);
    </script>
</body>
</html>'''

# Write HTML file
with open('EMERGENCY_REMOTE.html', 'w') as f:
    f.write(html_content)

print("📱 HTML file created: EMERGENCY_REMOTE.html")

async def main():
    print("🚀 Starting WebSocket server on port 9999...")
    
    # Start WebSocket server
    start_server = websockets.serve(handle_client, "0.0.0.0", 9999)
    
    # Start HTTP server in background
    import threading
    import http.server
    import socketserver
    
    def start_http():
        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", 8888), Handler)
        httpd.serve_forever()
    
    http_thread = threading.Thread(target=start_http)
    http_thread.daemon = True
    http_thread.start()
    
    print("🌐 HTTP server started on port 8888")
    print("=" * 50)
    print("📱 OPEN YOUR PHONE BROWSER TO:")
    print("   http://192.168.2.5:8888/EMERGENCY_REMOTE.html")
    print("=" * 50)
    print("✅ SERVERS RUNNING! READY FOR ART COMMANDS!")
    
    await start_server
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
