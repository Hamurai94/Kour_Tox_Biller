#!/usr/bin/env python3
"""
CSP ULTIMATE PARSER - THE BREAKTHROUGH!
Reads BOTH shortcut databases:
1. default.khc -> Menu shortcuts (F1-F4, F7)
2. EditImageTool.todb -> Custom tool shortcuts (F5 = Round watercolor!)

THIS IS THE SECRET SAUCE THAT DESTROYS HARDWARE REMOTES!
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class CSPUltimateParser:
    def __init__(self):
        self.base_path = Path.home() / "Library/CELSYS"
        self.menu_shortcuts_db = self.base_path / "CLIPStudioPaintVer1_5_0/Shortcut/default.khc"
        self.tool_shortcuts_db = self.base_path / "CLIPStudioPaintVer1_5_0/Tool/EditImageTool.todb"
        
        # F-key encoding: NodeShortCutKey = 36 + F_number
        self.f_key_offset = 36
        
    def parse_ultimate_shortcuts(self) -> Dict:
        """Parse BOTH shortcut databases for complete F-key mapping"""
        logger.info("🚀 ULTIMATE CSP SHORTCUT PARSING!")
        logger.info("=" * 60)
        
        ultimate_mapping = {}
        
        # Step 1: Parse menu shortcuts (F1-F4, F7, etc.)
        logger.info("📋 Step 1: Parsing menu shortcuts...")
        menu_shortcuts = self.parse_menu_shortcuts()
        
        # Step 2: Parse custom tool shortcuts (F5 = Round watercolor!)
        logger.info("🎨 Step 2: Parsing custom tool shortcuts...")
        tool_shortcuts = self.parse_tool_shortcuts()
        
        # Step 3: Combine both databases
        logger.info("🔗 Step 3: Building ultimate F-key mapping...")
        for i in range(1, 13):
            f_key = f"F{i}"
            
            if f_key in menu_shortcuts:
                ultimate_mapping[f_key] = menu_shortcuts[f_key]
                ultimate_mapping[f_key]['source'] = 'menu_shortcuts'
            elif f_key in tool_shortcuts:
                ultimate_mapping[f_key] = tool_shortcuts[f_key]
                ultimate_mapping[f_key]['source'] = 'tool_shortcuts'
            else:
                ultimate_mapping[f_key] = {
                    'assigned': False,
                    'icon': '➕',
                    'description': f'Available {f_key}',
                    'command': None,
                    'source': 'unassigned'
                }
        
        logger.info("🎯 ULTIMATE MAPPING COMPLETE!")
        return ultimate_mapping
    
    def parse_menu_shortcuts(self) -> Dict:
        """Parse the menu shortcut database"""
        menu_shortcuts = {}
        
        if not self.menu_shortcuts_db.exists():
            logger.warning("❌ Menu shortcuts database not found")
            return menu_shortcuts
        
        try:
            conn = sqlite3.connect(str(self.menu_shortcuts_db))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT menucommandtype, menucommand, shortcut, modifier 
                FROM shortcutmenu 
                WHERE shortcut LIKE 'F%' AND shortcut IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                command_type, command, key, modifier = row
                
                menu_shortcuts[key] = {
                    'assigned': True,
                    'icon': self.get_command_icon(command),
                    'description': self.get_command_description(command),
                    'command': command,
                    'command_type': command_type,
                    'modifier': modifier
                }
                
                logger.info(f"📋 {key}: {menu_shortcuts[key]['icon']} {menu_shortcuts[key]['description']}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error parsing menu shortcuts: {e}")
        
        return menu_shortcuts
    
    def parse_tool_shortcuts(self) -> Dict:
        """Parse the custom tool shortcut database - THE BREAKTHROUGH!"""
        tool_shortcuts = {}
        
        if not self.tool_shortcuts_db.exists():
            logger.warning("❌ Tool shortcuts database not found")
            return tool_shortcuts
        
        try:
            conn = sqlite3.connect(str(self.tool_shortcuts_db))
            cursor = conn.cursor()
            
            # Find tools with shortcut keys in F-key range
            cursor.execute("""
                SELECT NodeName, NodeShortCutKey 
                FROM Node 
                WHERE NodeShortCutKey BETWEEN ? AND ?
            """, (self.f_key_offset + 1, self.f_key_offset + 12))
            
            for row in cursor.fetchall():
                node_name, shortcut_key = row
                
                # Calculate F-key number
                f_number = shortcut_key - self.f_key_offset
                f_key = f"F{f_number}"
                
                tool_shortcuts[f_key] = {
                    'assigned': True,
                    'icon': self.get_tool_icon(node_name),
                    'description': node_name,
                    'command': f'custom_tool_{shortcut_key}',
                    'tool_name': node_name,
                    'shortcut_key': shortcut_key
                }
                
                logger.info(f"🎨 {f_key}: {tool_shortcuts[f_key]['icon']} {node_name}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error parsing tool shortcuts: {e}")
        
        return tool_shortcuts
    
    def get_command_icon(self, command: str) -> str:
        """Get icon for menu commands"""
        icons = {
            'cut': '✂️',
            'copy': '📋',
            'paste': '📥',
            'undo': '↶',
            'redo': '↷',
            'helponlinehowto': '❓',
            'selectinvert': '🔄'
        }
        return icons.get(command, '🔧')
    
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
        """Get description for menu commands"""
        descriptions = {
            'cut': 'Cut',
            'copy': 'Copy',
            'paste': 'Paste',
            'undo': 'Undo',
            'redo': 'Redo',
            'helponlinehowto': 'Help/Tutorial',
            'selectinvert': 'Invert Selection'
        }
        return descriptions.get(command, command.replace('_', ' ').title())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = CSPUltimateParser()
    ultimate_mapping = parser.parse_ultimate_shortcuts()
    
    print("\n🎯 ULTIMATE CSP F-KEY MAPPING:")
    print("=" * 60)
    print("🔥 FIRST SOFTWARE TO CRACK CSP'S TOOL SHORTCUTS! 🔥")
    print("=" * 60)
    
    for key, data in ultimate_mapping.items():
        if data['assigned']:
            source_emoji = "📋" if data['source'] == 'menu_shortcuts' else "🎨" if data['source'] == 'tool_shortcuts' else "❓"
            print(f"{key}: {data['icon']} {data['description']} {source_emoji}")
        else:
            print(f"{key}: {data['icon']} {data['description']}")
    
    # Save the revolutionary mapping
    with open('ultimate_csp_mapping.json', 'w') as f:
        json.dump(ultimate_mapping, f, indent=2, ensure_ascii=False)
    
    print(f"\n💰 REVOLUTIONARY MAPPING SAVED!")
    print("🚀 Ready to destroy the hardware remote market!")
    print("💎 This is the killer feature that makes millions!")
