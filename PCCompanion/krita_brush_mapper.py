#!/usr/bin/env python3
"""
KRITA BRUSH SHORTCUT MAPPER - THE ULTIMATE SOLUTION!
Creates dynamic shortcut mappings for Krita brushes
Can even CONFIGURE Krita to use our shortcuts!

REVOLUTIONARY APPROACH:
1. Detect popular brushes from database
2. Assign F1-F12 shortcuts to them  
3. Optionally configure Krita to use these shortcuts
4. Provide instant brush switching like CSP F-keys

THIS GIVES KRITA THE SAME F-KEY POWER AS CSP!
"""

import sqlite3
import json
import logging
import configparser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import platform

logger = logging.getLogger(__name__)

class KritaBrushMapper:
    def __init__(self):
        self.db_path = self._get_krita_db_path()
        self.shortcut_config_path = self._get_shortcut_config_path()
        self.brush_shortcuts = {}
        
    def _get_krita_db_path(self) -> Optional[Path]:
        """Get Krita database path"""
        if platform.system() == 'Darwin':
            return Path.home() / "Library/Application Support/krita/resourcecache.sqlite"
        elif platform.system() == 'Windows':
            return Path.home() / "AppData/Roaming/krita/resourcecache.sqlite"
        else:
            return Path.home() / ".local/share/krita/resourcecache.sqlite"
    
    def _get_shortcut_config_path(self) -> Optional[Path]:
        """Get Krita shortcut config path"""
        if platform.system() == 'Darwin':
            return Path.home() / "Library/Application Support/krita/kritashortcutsrc"
        elif platform.system() == 'Windows':
            return Path.home() / "AppData/Roaming/krita/kritashortcutsrc"
        else:
            return Path.home() / ".config/krita/kritashortcutsrc"
    
    def get_popular_brushes(self, limit: int = 12) -> List[Dict]:
        """Get most popular brushes for F-key assignment"""
        if not self.db_path or not self.db_path.exists():
            return []
            
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get brushes prioritized by usefulness
            cursor.execute("""
                SELECT DISTINCT
                    r.name,
                    r.filename,
                    GROUP_CONCAT(t.name, ',') as tags
                FROM resources r
                LEFT JOIN resource_tags rt ON r.id = rt.resource_id  
                LEFT JOIN tags t ON rt.tag_id = t.id
                WHERE r.resource_type_id = (
                    SELECT id FROM resource_types WHERE name = 'paintoppresets'
                )
                AND r.status = 1
                AND (
                    r.name LIKE '%basic%' OR
                    r.name LIKE '%default%' OR
                    r.name LIKE '%pencil%' OR
                    r.name LIKE '%ink%' OR
                    r.name LIKE '%watercolor%' OR
                    r.name LIKE '%airbrush%' OR
                    r.name LIKE '%eraser%' OR
                    r.name LIKE '%paint%'
                )
                GROUP BY r.id, r.name, r.filename
                ORDER BY 
                    CASE 
                        WHEN r.name LIKE '%basic%' THEN 1
                        WHEN r.name LIKE '%default%' THEN 2
                        WHEN r.name LIKE '%pencil%' THEN 3
                        WHEN r.name LIKE '%ink%' THEN 4
                        WHEN r.name LIKE '%watercolor%' THEN 5
                        WHEN r.name LIKE '%airbrush%' THEN 6
                        WHEN r.name LIKE '%eraser%' THEN 7
                        ELSE 8
                    END,
                    r.name
                LIMIT ?
            """, (limit,))
            
            popular_brushes = []
            for row in cursor.fetchall():
                name, filename, tags_str = row
                tags = tags_str.split(',') if tags_str else []
                
                popular_brushes.append({
                    'name': name,
                    'filename': filename,
                    'display_name': name,
                    'tags': tags,
                    'icon': self._get_brush_icon(name, tags),
                    'category': self._categorize_brush(name, tags)
                })
            
            conn.close()
            logger.info(f"🎯 Selected {len(popular_brushes)} popular brushes for shortcuts")
            return popular_brushes
            
        except Exception as e:
            logger.error(f"Error getting popular brushes: {e}")
            return []
    
    def create_brush_shortcut_map(self) -> Dict[str, Dict]:
        """Create F1-F12 mappings for popular brushes"""
        popular_brushes = self.get_popular_brushes(12)
        
        shortcut_map = {}
        
        for i, brush in enumerate(popular_brushes):
            f_key = f"F{i + 1}"
            shortcut_map[f_key] = {
                'brush_name': brush['name'],
                'display_name': brush['display_name'],
                'filename': brush['filename'],
                'icon': brush['icon'],
                'category': brush['category'],
                'shortcut_key': f_key.lower()
            }
            
        logger.info(f"🗺️ Created shortcut map for {len(shortcut_map)} brushes")
        return shortcut_map
    
    def _categorize_brush(self, name: str, tags: List[str]) -> str:
        """Categorize brush for organization"""
        name_lower = name.lower()
        tags_lower = [tag.lower() for tag in tags]
        
        if any('pencil' in tag for tag in tags_lower) or 'pencil' in name_lower:
            return 'Pencils'
        elif any('ink' in tag for tag in tags_lower) or 'ink' in name_lower:
            return 'Ink'
        elif any('water' in tag for tag in tags_lower) or 'water' in name_lower:
            return 'Watercolor'
        elif any('paint' in tag for tag in tags_lower) or 'paint' in name_lower:
            return 'Paint'
        elif 'airbrush' in name_lower:
            return 'Airbrush'
        elif 'eraser' in name_lower:
            return 'Erasers'
        elif 'basic' in name_lower:
            return 'Basic'
        else:
            return 'Other'
    
    def _get_brush_icon(self, name: str, tags: List[str]) -> str:
        """Get icon for brush"""
        name_lower = name.lower()
        
        if 'pencil' in name_lower:
            return '✏️'
        elif 'ink' in name_lower:
            return '🖊️'
        elif 'water' in name_lower:
            return '💧'
        elif 'paint' in name_lower:
            return '🎨'
        elif 'eraser' in name_lower:
            return '🧽'
        elif 'airbrush' in name_lower:
            return '💨'
        else:
            return '🖌️'
    
    def generate_krita_shortcuts_config(self) -> str:
        """Generate Krita shortcut configuration for brush F-keys"""
        shortcut_map = self.create_brush_shortcut_map()
        
        config_lines = [
            "# Art Remote Control - Krita Brush Shortcuts",
            "# Auto-generated F-key mappings for popular brushes",
            "",
            "[Shortcuts]"
        ]
        
        for f_key, brush_info in shortcut_map.items():
            # Create shortcut entry for brush preset
            config_lines.extend([
                f"",
                f"[{brush_info['brush_name']}]",
                f"_k_friendly_name={brush_info['display_name']}",
                f"default={f_key}",
                f"# Category: {brush_info['category']}"
            ])
        
        return "\n".join(config_lines)
    
    def install_shortcuts_to_krita(self) -> bool:
        """Install our F-key shortcuts directly into Krita config"""
        try:
            if not self.shortcut_config_path:
                logger.warning("⚠️ Cannot find Krita config path")
                return False
                
            # Backup existing config
            if self.shortcut_config_path.exists():
                backup_path = self.shortcut_config_path.with_suffix('.backup')
                import shutil
                shutil.copy2(self.shortcut_config_path, backup_path)
                logger.info(f"💾 Backed up existing shortcuts to {backup_path}")
            
            # Generate our config
            our_config = self.generate_krita_shortcuts_config()
            
            # Write to Krita
            self.shortcut_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.shortcut_config_path, 'w') as f:
                f.write(our_config)
                
            logger.info(f"✅ Installed F-key shortcuts to {self.shortcut_config_path}")
            logger.info("🔄 Restart Krita to activate new shortcuts")
            return True
            
        except Exception as e:
            logger.error(f"Error installing shortcuts: {e}")
            return False
    
    def get_brush_by_name(self, brush_name: str) -> Optional[Dict]:
        """Get brush info by name for shortcut execution"""
        shortcut_map = self.create_brush_shortcut_map()
        
        for f_key, brush_info in shortcut_map.items():
            if brush_info['brush_name'] == brush_name:
                return brush_info
                
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    mapper = KritaBrushMapper()
    
    print("🎨 KRITA BRUSH SHORTCUT MAPPER")
    print("=" * 50)
    
    # Show popular brushes
    popular = mapper.get_popular_brushes()
    print(f"🎯 Found {len(popular)} popular brushes:")
    for i, brush in enumerate(popular):
        print(f"  F{i+1}: {brush['icon']} {brush['name']} ({brush['category']})")
    
    # Generate shortcut map
    shortcut_map = mapper.create_brush_shortcut_map()
    
    # Option to install shortcuts
    print(f"\n💡 Want to install F-key shortcuts to Krita?")
    print(f"   This will let you use F1-F12 to switch brushes instantly!")
    
    # Save mapping for server use
    with open('krita_brush_shortcuts.json', 'w') as f:
        json.dump(shortcut_map, f, indent=2)
    print(f"💾 Saved brush shortcut mapping!")
