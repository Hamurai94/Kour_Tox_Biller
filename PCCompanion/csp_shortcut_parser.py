#!/usr/bin/env python3
"""
CSP Shortcut Parser - Reads Clip Studio Paint's shortcut database
Extracts F-key assignments and tool shortcuts for dynamic favorites
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class CSPShortcutParser:
    def __init__(self):
        self.shortcut_db_paths = [
            Path.home() / "Library/CELSYS/CLIPStudioPaintVer1_5_0/Shortcut/default.khc",
            Path.home() / "Library/CELSYS/CLIPStudioCommon/Shortcut/default.khc",
            # Add Windows paths when needed
            # Path.home() / "Documents/CELSYS_EN/CLIPStudioPaint/Shortcut/default.khc"
        ]
        
        self.modifier_map = {
            0: "",           # No modifier
            1: "alt",        # Alt
            2: "shift",      # Shift  
            4: "cmd",        # Cmd/Ctrl
            5: "cmd+alt",    # Cmd+Alt
            6: "cmd+shift",  # Cmd+Shift
            3: "shift+alt"   # Shift+Alt
        }
    
    def find_shortcut_database(self) -> Optional[Path]:
        """Find the CSP shortcut database"""
        for path in self.shortcut_db_paths:
            if path.exists():
                logger.info(f"📁 Found shortcut database: {path}")
                return path
        
        logger.warning("❌ No CSP shortcut database found")
        return None
    
    def parse_shortcuts(self) -> Dict:
        """Parse all shortcuts from CSP database"""
        db_path = self.find_shortcut_database()
        if not db_path:
            return {}
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get all shortcuts
            cursor.execute("""
                SELECT menucommand, shortcut, modifier 
                FROM shortcutmenu 
                WHERE shortcut IS NOT NULL AND shortcut != ''
                ORDER BY shortcut
            """)
            
            shortcuts = {}
            f_key_assignments = {}
            
            for row in cursor.fetchall():
                menu_command, key, modifier = row
                modifier_text = self.modifier_map.get(modifier, f"mod_{modifier}")
                
                # Build full shortcut string
                if modifier_text:
                    full_shortcut = f"{modifier_text}+{key}"
                else:
                    full_shortcut = key
                
                shortcuts[menu_command] = {
                    'key': key,
                    'modifier': modifier,
                    'modifier_text': modifier_text,
                    'full_shortcut': full_shortcut
                }
                
                # Track F-key assignments specifically
                if key.startswith('F') and key[1:].isdigit():
                    f_key_assignments[key] = {
                        'command': menu_command,
                        'full_shortcut': full_shortcut,
                        'description': self.get_command_description(menu_command)
                    }
            
            conn.close()
            
            logger.info(f"✅ Parsed {len(shortcuts)} shortcuts")
            logger.info(f"🔑 Found {len(f_key_assignments)} F-key assignments")
            
            return {
                'all_shortcuts': shortcuts,
                'f_key_assignments': f_key_assignments,
                'total_shortcuts': len(shortcuts)
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing shortcuts: {e}")
            return {}
    
    def get_command_description(self, command: str) -> str:
        """Convert command names to human-readable descriptions"""
        descriptions = {
            'cut': 'Cut',
            'copy': 'Copy', 
            'paste': 'Paste',
            'undo': 'Undo',
            'redo': 'Redo',
            'selectall': 'Select All',
            'selectinvert': 'Invert Selection',
            'helponlinehowto': 'Help/Tutorial',
            'subtoolprevioussubtool': 'Previous Sub-tool',
            'subtoolnextsubtool': 'Next Sub-tool',
            'viewrotateleft': 'Rotate Canvas Left',
            'viewrotateright': 'Rotate Canvas Right',
            'viewzoomin': 'Zoom In',
            'viewzoomout': 'Zoom Out',
            'viewreset': 'Reset Canvas View'
        }
        
        return descriptions.get(command, command.replace('_', ' ').title())
    
    def get_f_key_favorites(self) -> Dict:
        """Get specifically the F1-F12 assignments for favorites"""
        shortcuts = self.parse_shortcuts()
        f_keys = shortcuts.get('f_key_assignments', {})
        
        # Filter and organize F1-F12
        favorites = {}
        for i in range(1, 13):  # F1-F12
            f_key = f"F{i}"
            if f_key in f_keys:
                favorites[f_key] = f_keys[f_key]
            else:
                favorites[f_key] = {
                    'command': None,
                    'full_shortcut': f_key,
                    'description': f'Unassigned F{i}'
                }
        
        return favorites
    
    def save_favorites_database(self, output_path: str):
        """Save F-key favorites to JSON for the Android app"""
        favorites = self.get_f_key_favorites()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(favorites, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Favorites database saved to: {output_path}")
        return favorites

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = CSPShortcutParser()
    
    print("🔑 Parsing CSP Shortcuts...")
    shortcuts = parser.parse_shortcuts()
    
    print(f"\n📊 Found {shortcuts.get('total_shortcuts', 0)} total shortcuts")
    
    f_keys = shortcuts.get('f_key_assignments', {})
    if f_keys:
        print(f"\n🎯 F-Key Assignments:")
        for key, data in sorted(f_keys.items()):
            print(f"  {key}: {data['description']} ({data['full_shortcut']})")
    
    # Save favorites for Android app
    favorites = parser.save_favorites_database('csp_favorites.json')
    print(f"\n💾 Saved {len(favorites)} F-key mappings to csp_favorites.json")
