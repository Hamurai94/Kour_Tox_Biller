#!/usr/bin/env python3
"""
Test script for Art Remote Control Authentication System
"""

import asyncio
import json
from auth import SimpleAuth

async def test_authentication():
    """Test the authentication system"""
    print("🧪 Testing Art Remote Control Authentication System")
    
    # Create auth instance
    auth = SimpleAuth()
    info = auth.get_connection_info()
    
    print(f"✅ Generated PIN: {info['pin']}")
    print(f"✅ Generated Token: {info['token'][:16]}...")
    print(f"✅ QR Data: {info['qr_data']}")
    
    # Test validation
    print(f"✅ PIN validation: {auth.validate_pin(info['pin'])}")
    print(f"✅ Token validation: {auth.validate_token(info['token'])}")
    print(f"❌ Wrong PIN test: {auth.validate_pin('000000')}")
    print(f"❌ Wrong token test: {auth.validate_token('invalid_token')}")
    
    # Test authentication methods
    print("\n🔐 Testing authentication methods:")
    
    # Test token auth
    token_auth = {'token': info['token']}
    print(f"✅ Token auth result: {auth.is_authenticated(token_auth)}")
    
    # Test PIN auth
    pin_auth = {'pin': info['pin']}
    print(f"✅ PIN auth result: {auth.is_authenticated(pin_auth)}")
    
    # Test invalid auth
    invalid_auth = {'pin': '999999'}
    print(f"❌ Invalid auth result: {auth.is_authenticated(invalid_auth)}")
    
    print("\n🎉 Authentication system test completed!")

async def test_websocket_auth():
    """Test WebSocket authentication flow"""
    print("\n🌐 Testing WebSocket Authentication Flow")
    
    # This would connect to a running server
    # For now, just show the message format
    auth = SimpleAuth()
    info = auth.get_connection_info()
    
    # Example auth message from client
    auth_message = {
        "type": "authenticate",
        "pin": info['pin'],
        "client_info": {
            "platform": "Android",
            "app_version": "1.0",
            "device_name": "Test Device"
        }
    }
    
    print(f"📱 Example client auth message:")
    print(json.dumps(auth_message, indent=2))
    
    # Example server response
    server_response = {
        "type": "auth_response",
        "success": True,
        "message": "Authentication successful"
    }
    
    print(f"\n🖥️ Example server response:")
    print(json.dumps(server_response, indent=2))

if __name__ == "__main__":
    asyncio.run(test_authentication())
    asyncio.run(test_websocket_auth())
