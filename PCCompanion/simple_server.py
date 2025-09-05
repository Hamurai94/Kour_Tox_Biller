#!/usr/bin/env python3
import asyncio
import websockets
import json
import http.server
import socketserver
import threading
import os

class SimpleArtRemoteServer:
    def __init__(self):
        self.clients = set()
        
    async def register_client(self, websocket, path):
        self.clients.add(websocket)
        print(f"✅ Client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                print(f"📨 Received: {message}")
                # Just echo back for now
                await websocket.send(json.dumps({"status": "received", "action": message}))
        except Exception as e:
            print(f"❌ Connection error: {e}")
        finally:
            self.clients.remove(websocket)
            print("👋 Client disconnected")

def start_http_server():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
        def do_GET(self):
            if self.path == '/' or self.path == '/remote':
                self.path = '/web_remote.html'
            return super().do_GET()
    
    httpd = socketserver.TCPServer(("", 8081), Handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    print("🌐 HTTP server started on port 8081")
    
async def main():
    server = SimpleArtRemoteServer()
    start_http_server()
    
    print("🚀 Simple Art Remote Server starting...")
    print("📱 Open http://192.168.2.5:8081 on your phone")
    
    async with websockets.serve(server.register_client, "0.0.0.0", 8766):
        print("✅ WebSocket server running on port 8766")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
