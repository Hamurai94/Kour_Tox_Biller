#!/usr/bin/env python3
"""
KRITA SHORTCUT PARSER - THE REAL SOLUTION!
Reads Krita's actual shortcut configuration files
Just like we cracked CSP's database, now we read Krita's REAL shortcuts!

Based on Krita docs: https://docs.krita.org/en/reference_manual/preferences/shortcut_settings.html
Shortcuts stored in: ~/.config/krita/kritashortcutsrc (Linux/macOS)
                     %APPDATA%/krita/kritashortcutsrc (Windows)
"""

import os
import logging
import configparser
from pathlib import Path
from typing import Dict, List, Optional
import platform

logger = logging.getLogger(__name__)

class KritaShortcutParser:
    def __init__(self):
        self.shortcut_paths = self._get_krita_shortcut_paths()
        self.parsed_shortcuts = {}
        
    def _get_krita_shortcut_paths(self) -> List[Path]:
        """Get possible Krita shortcut file locations"""
        system = platform.system()
        
        paths = []
        
        if system == 'Darwin':  # macOS
            # Try multiple possible locations
            paths.extend([
                Path.home() / ".config/krita/kritashortcutsrc",
                Path.home() / "Library/Preferences/kritashortcutsrc",
                Path.home() / "Library/Application Support/krita/kritashortcutsrc",
                Path.home() / ".local/share/krita/kritashortcutsrc"
            ])
        elif system == 'Windows':
            paths.extend([
                Path.home() / "AppData/Roaming/krita/kritashortcutsrc",
                Path.home() / "AppData/Local/krita/kritashortcutsrc",
                Path.home() / ".config/krita/kritashortcutsrc"
            ])
        else:  # Linux
            paths.extend([
                Path.home() / ".config/krita/kritashortcutsrc",
                Path.home() / ".local/share/krita/kritashortcutsrc"
            ])
            
        return paths
    
    def find_shortcut_file(self) -> Optional[Path]:
        """Find the actual Krita shortcut configuration file"""
        for path in self.shortcut_paths:
            if path.exists():
                logger.info(f"📁 Found Krita shortcuts: {path}")
                return path
                
        logger.warning("❌ No Krita shortcut file found")
        return None
    
    def parse_shortcuts(self) -> Dict[str, str]:
        """Parse Krita's actual configured shortcuts"""
        shortcut_file = self.find_shortcut_file()
        
        if not shortcut_file:
            logger.warning("⚠️ Using default Krita shortcuts")
            return self._get_default_krita_shortcuts()
            
        try:
            logger.info("🔍 Parsing Krita shortcut configuration...")
            
            config = configparser.ConfigParser()
            config.read(shortcut_file)
            
            shortcuts = {}
            
            # Parse the INI-style shortcut file
            for section_name in config.sections():
                section = config[section_name]
                
                # Look for shortcut definitions
                for key, value in section.items():
                    if key.startswith('_k_friendly_name'):
                        action_name = value
                    elif key.startswith('default'):
                        shortcut_combo = value
                        
                        # Map common actions to our system
                        action_mapping = {
                            'zoom in': 'zoom_in',
                            'zoom out': 'zoom_out', 
                            'rotate left': 'rotate_left',
                            'rotate right': 'rotate_right',
                            'rectangle select': 'tool_select',
                            'freehand brush': 'tool_brush',
                            'eraser': 'tool_eraser',
                            'hand': 'tool_pan',
                            'pencil': 'tool_pencil',
                            'new layer': 'layer_new',
                            'delete layer': 'layer_delete'
                        }
                        
                        for krita_action, our_action in action_mapping.items():
                            if krita_action.lower() in action_name.lower():
                                shortcuts[our_action] = self._parse_shortcut_combo(shortcut_combo)
                                logger.info(f"📋 {our_action}: {shortcuts[our_action]} ({action_name})")
                                break
            
            logger.info(f"✅ Parsed {len(shortcuts)} Krita shortcuts")
            return shortcuts
            
        except Exception as e:
            logger.error(f"Error parsing Krita shortcuts: {e}")
            return self._get_default_krita_shortcuts()
    
    def _parse_shortcut_combo(self, combo_string: str) -> List[str]:
        """Parse shortcut combo string into key list"""
        if not combo_string or combo_string.lower() == 'none':
            return []
            
        # Handle common formats: "Ctrl+R", "Ctrl+Shift+N", etc.
        parts = combo_string.lower().replace(' ', '').split('+')
        
        # Convert to our format
        keys = []
        for part in parts:
            if part in ['ctrl', 'control']:
                keys.append('ctrl')
            elif part in ['cmd', 'command', 'meta']:
                keys.append('cmd')
            elif part == 'shift':
                keys.append('shift')
            elif part == 'alt':
                keys.append('alt')
            else:
                keys.append(part)
                
        return keys
    
    def _get_default_krita_shortcuts(self) -> Dict[str, List[str]]:
        """Fallback: Default Krita shortcuts from documentation"""
        logger.info("📋 Using documented Krita defaults")
        
        # Based on Krita documentation and testing
        return {
            # Navigation
            'zoom_in': ['ctrl', '+'] if platform.system() != 'Darwin' else ['cmd', '+'],
            'zoom_out': ['ctrl', '-'] if platform.system() != 'Darwin' else ['cmd', '-'],
            'rotate_left': ['4'],  # Default Krita rotation
            'rotate_right': ['6'],  # Default Krita rotation
            'reset_rotation': ['5'],
            
            # Tools (from Krita defaults)
            'tool_brush': ['b'],
            'tool_eraser': ['e'], 
            'tool_select': ['ctrl', 'r'] if platform.system() != 'Darwin' else ['cmd', 'r'],  # Rectangle select
            'tool_pan': ['h'],  # Hand tool
            'tool_pencil': ['n'],
            'tool_airbrush': ['a'],
            
            # Layers
            'layer_new': ['ctrl', 'shift', 'n'] if platform.system() != 'Darwin' else ['cmd', 'shift', 'n'],
            'layer_delete': ['delete'],
            'layer_duplicate': ['ctrl', 'j'] if platform.system() != 'Darwin' else ['cmd', 'j'],
            
            # Brush size
            'brush_size_up': [']'],
            'brush_size_down': ['[']
        }
    
    def get_krita_profile_for_server(self) -> Dict:
        """Get complete Krita profile for the server"""
        shortcuts = self.parse_shortcuts()
        
        # Convert to server format
        profile = {
            'Windows': {},
            'Darwin': {}
        }
        
        for action, keys in shortcuts.items():
            # Adapt for both platforms
            windows_keys = [k.replace('cmd', 'ctrl') for k in keys]
            macos_keys = [k.replace('ctrl', 'cmd') for k in keys]
            
            profile['Windows'][action] = windows_keys
            profile['Darwin'][action] = macos_keys
            
        return profile

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    parser = KritaShortcutParser()
    shortcuts = parser.parse_shortcuts()
    
    print(f"✅ Found {len(shortcuts)} Krita shortcuts")
    for action, keys in shortcuts.items():
        print(f"  {action}: {' + '.join(keys)}")
        
    profile = parser.get_krita_profile_for_server()
    print(f"🎯 Built server profile with {len(profile['Darwin'])} actions")
