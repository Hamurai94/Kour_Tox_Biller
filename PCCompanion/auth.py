#!/usr/bin/env python3
"""
Simple Authentication System for Art Remote Control
Provides token-based authentication for WebSocket connections
"""

import secrets
import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SimpleAuth:
    """
    Simple token-based authentication system
    - Generates secure tokens on first run
    - Validates tokens for WebSocket connections
    - Stores auth data in local config file
    """
    
    def __init__(self, config_dir: Path = None):
        if config_dir is None:
            config_dir = Path.home() / '.artremote'
        
        self.config_dir = config_dir
        self.config_file = config_dir / 'auth.json'
        self.config_dir.mkdir(exist_ok=True)
        
        self.auth_data = self._load_or_create_auth()
    
    def _load_or_create_auth(self) -> Dict[str, Any]:
        """Load existing auth config or create new one"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                logger.info("Loaded existing authentication config")
                return data
            except Exception as e:
                logger.error(f"Failed to load auth config: {e}")
        
        # Create new auth config
        auth_data = self._generate_new_auth()
        self._save_auth(auth_data)
        logger.info("Created new authentication config")
        return auth_data
    
    def _generate_new_auth(self) -> Dict[str, Any]:
        """Generate new authentication tokens and config"""
        # Generate a secure random token (32 bytes = 256 bits)
        token = secrets.token_urlsafe(32)
        
        # Generate a simpler 6-digit PIN for easy manual entry
        pin = secrets.randbelow(900000) + 100000  # 6-digit number
        
        # Create token hash for storage (don't store plain token)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        return {
            'token': token,           # Full token for QR code/auto-setup
            'token_hash': token_hash, # Hashed version for validation
            'pin': str(pin),          # Simple PIN for manual entry
            'created': time.time(),
            'version': '1.0'
        }
    
    def _save_auth(self, auth_data: Dict[str, Any]):
        """Save auth data to config file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(auth_data, f, indent=2)
            # Set restrictive permissions (owner read/write only)
            self.config_file.chmod(0o600)
        except Exception as e:
            logger.error(f"Failed to save auth config: {e}")
    
    def get_connection_info(self) -> Dict[str, str]:
        """Get info needed for client connection"""
        return {
            'token': self.auth_data['token'],
            'pin': self.auth_data['pin'],
            'qr_data': self._generate_qr_data()
        }
    
    def _generate_qr_data(self) -> str:
        """Generate QR code data for easy setup"""
        # Simple format: artremote://connect?token=TOKEN&host=HOST&port=PORT
        # We'll fill in host/port when server starts
        return f"artremote://connect?token={self.auth_data['token']}"
    
    def validate_token(self, provided_token: str) -> bool:
        """Validate a provided token against stored hash"""
        if not provided_token:
            return False
        
        # Hash the provided token
        provided_hash = hashlib.sha256(provided_token.encode()).hexdigest()
        
        # Compare with stored hash
        return provided_hash == self.auth_data['token_hash']
    
    def validate_pin(self, provided_pin: str) -> bool:
        """Validate a provided PIN"""
        return provided_pin.strip() == self.auth_data['pin']
    
    def regenerate_auth(self) -> Dict[str, str]:
        """Generate new auth tokens (for security reset)"""
        self.auth_data = self._generate_new_auth()
        self._save_auth(self.auth_data)
        logger.info("Regenerated authentication tokens")
        return self.get_connection_info()
    
    def is_authenticated(self, auth_info: Dict[str, Any]) -> bool:
        """
        Check if connection is authenticated
        Accepts either token or PIN authentication
        """
        if not auth_info:
            return False
        
        # Check token authentication (preferred)
        if 'token' in auth_info:
            return self.validate_token(auth_info['token'])
        
        # Check PIN authentication (fallback)
        if 'pin' in auth_info:
            return self.validate_pin(auth_info['pin'])
        
        return False
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status for display"""
        return {
            'has_auth': True,
            'pin': self.auth_data['pin'],
            'created': self.auth_data['created'],
            'token_preview': self.auth_data['token'][:8] + '...',  # First 8 chars only
        }


class AuthenticatedConnection:
    """
    Wrapper for WebSocket connections with authentication
    """
    
    def __init__(self, websocket, auth: SimpleAuth):
        self.websocket = websocket
        self.auth = auth
        self.is_authenticated = False
        self.client_info = {}
    
    async def authenticate(self, auth_message: Dict[str, Any]) -> bool:
        """
        Authenticate the connection
        Returns True if successful, False otherwise
        """
        try:
            if self.auth.is_authenticated(auth_message):
                self.is_authenticated = True
                self.client_info = auth_message.get('client_info', {})
                
                # Send success response
                await self.websocket.send(json.dumps({
                    'type': 'auth_response',
                    'success': True,
                    'message': 'Authentication successful'
                }))
                
                logger.info(f"Client authenticated: {self.client_info}")
                return True
            else:
                # Send failure response
                await self.websocket.send(json.dumps({
                    'type': 'auth_response',
                    'success': False,
                    'message': 'Invalid authentication credentials'
                }))
                
                logger.warning("Authentication failed for client")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def require_auth(self):
        """Decorator-like method to check authentication"""
        if not self.is_authenticated:
            raise PermissionError("Connection not authenticated")


# Convenience functions for easy integration
_global_auth = None

def get_auth_instance(config_dir: Path = None) -> SimpleAuth:
    """Get global auth instance (singleton pattern)"""
    global _global_auth
    if _global_auth is None:
        _global_auth = SimpleAuth(config_dir)
    return _global_auth

def validate_connection_auth(auth_data: Dict[str, Any]) -> bool:
    """Quick validation function"""
    auth = get_auth_instance()
    return auth.is_authenticated(auth_data)

def get_connection_info() -> Dict[str, str]:
    """Get connection info for display"""
    auth = get_auth_instance()
    return auth.get_connection_info()


if __name__ == '__main__':
    # Test the auth system
    print("Testing Art Remote Control Authentication System")
    
    auth = SimpleAuth()
    info = auth.get_connection_info()
    
    print(f"Generated PIN: {info['pin']}")
    print(f"Generated Token: {info['token'][:16]}...")
    print(f"QR Data: {info['qr_data']}")
    
    # Test validation
    print(f"PIN validation test: {auth.validate_pin(info['pin'])}")
    print(f"Token validation test: {auth.validate_token(info['token'])}")
    print(f"Wrong PIN test: {auth.validate_pin('000000')}")
