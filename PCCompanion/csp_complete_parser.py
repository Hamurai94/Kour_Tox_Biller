#!/usr/bin/env python3
"""
CSP COMPLETE PARSER - Complete Integration
Cross-references CSP's Material DB + Tool Groups + Shortcuts
This is the killer feature that destroys the hardware remote market!
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class CSPCompleteParser:
    def __init__(self):
        self.base_path = Path.home() / "Library/CELSYS"
        self.shortcut_db = self.base_path / "CLIPStudioPaintVer1_5_0/Shortcut/default.khc"
        self.tool_db = self.base_path / "CLIPStudioPaintVer1_5_0/Tool/default.tgm"
        self.material_path = self.base_path / "CLIPStudioCommon/Material"
        
        # Cache for performance
        self.material_cache = {}
        self.tool_groups = {}
        self.shortcuts = {}
        
    def parse_complete_setup(self) -> Dict:
        """Parse the complete CSP setup - materials, tools, and shortcuts"""
        logger.info("🔥 PARSING COMPLETE CSP SETUP...")
        
        # Step 1: Parse material database (brush metadata)
        logger.info("📚 Step 1: Parsing material database...")
        self.parse_materials()
        
        # Step 2: Parse active tool groups (what's in sub-tool palette)
        logger.info("🛠️ Step 2: Parsing active tool groups...")
        self.parse_tool_groups()
        
        # Step 3: Parse shortcut assignments (F-key mappings)
        logger.info("⌨️ Step 3: Parsing shortcut assignments...")
        self.parse_shortcuts()
        
        # Step 4: Cross-reference everything
        logger.info("🔗 Step 4: Cross-referencing databases...")
        return self.build_complete_mapping()
    
    def parse_materials(self):
        """Parse the material database to get brush metadata"""
        self.material_cache = {}
        
        # Look for catalog.xml files in material directories
        import os
        for root, dirs, files in os.walk(self.material_path):
            if Path(root).name != "Material" and "catalog.xml" in files:
                catalog_path = Path(root) / "catalog.xml"
                try:
                    tree = ET.parse(catalog_path)
                    root_elem = tree.getroot()
                    
                    # Find all items with type="brush"
                    for item in root_elem.findall('.//item'):
                        type_elem = item.find('type')
                        uuid = item.get('uuid', '')
                        name_elem = item.find('name')
                        
                        if type_elem is not None and 'brush' in type_elem.text and uuid:
                            name = name_elem.text if name_elem is not None else 'Unknown Brush'
                            
                            # Find thumbnail path
                            thumbnail_elem = item.find('.//thumbnail/fileref')
                            thumbnail_path = None
                            if thumbnail_elem is not None:
                                thumb_id = thumbnail_elem.get('idref')
                                # Find actual file path in files section
                                for file_elem in root_elem.findall('.//file'):
                                    if file_elem.get('id') == thumb_id:
                                        path_elem = file_elem.find('path')
                                        if path_elem is not None:
                                            thumbnail_path = catalog_path.parent / path_elem.text
                                            break
                            
                            self.material_cache[uuid] = {
                                'name': name,
                                'thumbnail_path': str(thumbnail_path) if thumbnail_path else None,
                                'uuid': uuid,
                                'type': 'brush'
                            }
                            
                except Exception as e:
                    logger.debug(f"Error parsing {catalog_path}: {e}")
        
        logger.info(f"📚 Found {len(self.material_cache)} brushes in material database")
    
    def parse_tool_groups(self):
        """Parse the active tool groups (what's actually in the sub-tool palette)"""
        if not self.tool_db.exists():
            logger.warning("❌ Tool group database not found")
            return
        
        try:
            conn = sqlite3.connect(str(self.tool_db))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT toolgroupgroupindex, toolgroupvariantnodeuuid 
                FROM toolgroup 
                WHERE toolgroupvariantnodeuuid IS NOT NULL
            """)
            
            self.tool_groups = {}
            for row in cursor.fetchall():
                group_index, uuid_blob = row
                
                # Convert binary UUID to string
                if uuid_blob:
                    try:
                        # Try to decode the UUID blob
                        uuid_str = uuid_blob.hex()
                        # Format as standard UUID (this might need adjustment)
                        formatted_uuid = f"{uuid_str[:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}-{uuid_str[16:20]}-{uuid_str[20:]}"
                        
                        if group_index not in self.tool_groups:
                            self.tool_groups[group_index] = []
                        
                        self.tool_groups[group_index].append({
                            'uuid': formatted_uuid,
                            'raw_uuid': uuid_str
                        })
                        
                    except Exception as e:
                        logger.debug(f"Error processing UUID: {e}")
            
            conn.close()
            
            total_tools = sum(len(tools) for tools in self.tool_groups.values())
            logger.info(f"🛠️ Found {total_tools} tools across {len(self.tool_groups)} groups")
            
        except Exception as e:
            logger.error(f"❌ Error parsing tool groups: {e}")
    
    def parse_shortcuts(self):
        """Parse shortcut assignments"""
        if not self.shortcut_db.exists():
            logger.warning("❌ Shortcut database not found")
            return
        
        try:
            conn = sqlite3.connect(str(self.shortcut_db))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT menucommandtype, menucommand, shortcut, modifier 
                FROM shortcutmenu 
                WHERE shortcut LIKE 'F%' AND shortcut IS NOT NULL
            """)
            
            self.shortcuts = {}
            for row in cursor.fetchall():
                command_type, command, key, modifier = row
                
                self.shortcuts[key] = {
                    'command_type': command_type,
                    'command': command,
                    'modifier': modifier
                }
            
            conn.close()
            
            logger.info(f"⌨️ Found {len(self.shortcuts)} F-key shortcuts")
            
        except Exception as e:
            logger.error(f"❌ Error parsing shortcuts: {e}")
    
    def build_complete_mapping(self) -> Dict:
        """Cross-reference all databases to build complete F-key mapping"""
        complete_mapping = {}
        
        for i in range(1, 13):
            f_key = f"F{i}"
            
            if f_key in self.shortcuts:
                shortcut_data = self.shortcuts[f_key]
                command = shortcut_data['command']
                
                # Try to find the brush/tool this command refers to
                brush_info = self.find_brush_by_command(command)
                
                if brush_info:
                    complete_mapping[f_key] = {
                        'assigned': True,
                        'icon': self.get_brush_icon(brush_info),
                        'description': brush_info['name'],
                        'command': command,
                        'brush_uuid': brush_info['uuid'],
                        'thumbnail_path': brush_info.get('thumbnail_path')
                    }
                else:
                    # Standard menu command
                    complete_mapping[f_key] = {
                        'assigned': True,
                        'icon': self.get_command_icon(command),
                        'description': self.get_command_description(command),
                        'command': command,
                        'brush_uuid': None,
                        'thumbnail_path': None
                    }
            else:
                complete_mapping[f_key] = {
                    'assigned': False,
                    'icon': '➕',
                    'description': f'Available {f_key}',
                    'command': None,
                    'brush_uuid': None,
                    'thumbnail_path': None
                }
        
        logger.info("🔗 Complete F-key mapping built!")
        return complete_mapping
    
    def find_brush_by_command(self, command: str) -> Optional[Dict]:
        """Find brush info by command/UUID"""
        # If command looks like a UUID, search material cache
        if len(command) > 20:  # Likely a UUID
            for uuid, brush_info in self.material_cache.items():
                if command in uuid or uuid in command:
                    return brush_info
        
        return None
    
    def get_brush_icon(self, brush_info: Dict) -> str:
        """Get appropriate icon for brush based on name"""
        name = brush_info['name'].lower()
        
        if '風' in name or 'wind' in name:
            return '🌪️'
        elif '水' in name or 'water' in name:
            return '💧'
        elif '煙' in name or 'smoke' in name:
            return '💨'
        elif '体液' in name:
            return '💦'
        elif 'pen' in name or 'ペン' in name:
            return '🖊️'
        elif 'pencil' in name or '鉛筆' in name:
            return '✏️'
        else:
            return '🎨'
    
    def get_command_icon(self, command: str) -> str:
        """Get icon for standard commands"""
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
    
    def get_command_description(self, command: str) -> str:
        """Get description for standard commands"""
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
    
    parser = CSPCompleteParser()
    mapping = parser.parse_complete_setup()
    
    print("\n🎯 COMPLETE CSP F-KEY MAPPING:")
    print("=" * 50)
    
    for key, data in mapping.items():
        if data['assigned']:
            print(f"{key}: {data['icon']} {data['description']}")
            if data['brush_uuid']:
                print(f"    └─ Brush UUID: {data['brush_uuid']}")
        else:
            print(f"{key}: {data['icon']} {data['description']}")
    
    # Save for integration
    with open('complete_csp_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Complete mapping saved to complete_csp_mapping.json")
    print("🚀 Ready to revolutionize the art remote market!")
