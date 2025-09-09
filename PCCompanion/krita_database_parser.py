#!/usr/bin/env python3
"""
KRITA DATABASE PARSER - THE REAL BREAKTHROUGH!
Just like we cracked CSP's SQLite database, now we crack Krita's!

Krita stores ALL brush presets in: resourcecache.sqlite
This contains 276+ brush presets vs the 16 we were finding in files!

THIS IS THE SAME REVOLUTIONARY APPROACH AS CSP!
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import platform

logger = logging.getLogger(__name__)

class KritaDatabaseParser:
    def __init__(self):
        self.db_paths = self._get_krita_db_paths()
        self.brush_cache = {}
        
    def _get_krita_db_paths(self) -> List[Path]:
        """Get possible Krita database locations"""
        system = platform.system()
        
        paths = []
        
        if system == 'Darwin':  # macOS
            paths.append(Path.home() / "Library/Application Support/krita/resourcecache.sqlite")
        elif system == 'Windows':
            paths.extend([
                Path.home() / "AppData/Roaming/krita/resourcecache.sqlite",
                Path.home() / "AppData/Local/krita/resourcecache.sqlite"
            ])
        else:  # Linux
            paths.append(Path.home() / ".local/share/krita/resourcecache.sqlite")
            
        return paths
    
    def find_database(self) -> Optional[Path]:
        """Find the Krita resource database"""
        for path in self.db_paths:
            if path.exists():
                logger.info(f"📁 Found Krita database: {path}")
                return path
                
        logger.warning("❌ No Krita database found")
        return None
    
    def parse_all_brushes(self) -> Dict:
        """Parse ALL brush presets from Krita's database - THE MAIN EVENT!"""
        db_path = self.find_database()
        
        if not db_path:
            return {'brushes': [], 'categories': {}, 'total_count': 0}
            
        try:
            logger.info("🎨 PARSING KRITA DATABASE...")
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get all brush presets with tags
            cursor.execute("""
                SELECT DISTINCT
                    r.name,
                    r.filename,
                    r.id as resource_id,
                    GROUP_CONCAT(t.name, ',') as tags
                FROM resources r
                LEFT JOIN resource_tags rt ON r.id = rt.resource_id  
                LEFT JOIN tags t ON rt.tag_id = t.id
                WHERE r.resource_type_id = (
                    SELECT id FROM resource_types WHERE name = 'paintoppresets'
                )
                AND r.status = 1
                GROUP BY r.id, r.name, r.filename
                ORDER BY r.name
            """)
            
            brushes = []
            categories = {}
            
            for row in cursor.fetchall():
                name, filename, resource_id, tags_str = row
                
                # Parse tags for categorization
                tags = tags_str.split(',') if tags_str else []
                category = self._categorize_brush(name, tags)
                
                brush_info = {
                    'id': resource_id,
                    'name': name,
                    'filename': filename,
                    'display_name': name,
                    'category': category,
                    'tags': tags,
                    'icon': self._get_brush_icon(name, tags)
                }
                
                brushes.append(brush_info)
                
                # Add to category
                if category not in categories:
                    categories[category] = []
                categories[category].append(brush_info)
            
            conn.close()
            
            result = {
                'brushes': brushes,
                'categories': categories,
                'total_count': len(brushes)
            }
            
            logger.info(f"🖌️ Found {len(brushes)} brush presets in {len(categories)} categories")
            for category, brush_list in categories.items():
                logger.info(f"  📁 {category}: {len(brush_list)} brushes")
                
            return result
            
        except Exception as e:
            logger.error(f"Error parsing Krita database: {e}")
            return {'brushes': [], 'categories': {}, 'total_count': 0}
    
    def _categorize_brush(self, name: str, tags: List[str]) -> str:
        """Categorize brush based on name and tags"""
        name_lower = name.lower()
        tags_lower = [tag.lower() for tag in tags]
        
        # Check tags first (most reliable)
        if any('pencil' in tag for tag in tags_lower):
            return 'Pencils'
        elif any('ink' in tag for tag in tags_lower):
            return 'Ink'
        elif any('water' in tag for tag in tags_lower):
            return 'Watercolor'
        elif any('paint' in tag for tag in tags_lower):
            return 'Paint'
        elif any('digital' in tag for tag in tags_lower):
            return 'Digital'
        elif any('eraser' in tag for tag in tags_lower):
            return 'Erasers'
        elif any('fx' in tag for tag in tags_lower):
            return 'Effects'
            
        # Fallback to name patterns
        if any(word in name_lower for word in ['pencil', 'hb', '2b', '4b']):
            return 'Pencils'
        elif any(word in name_lower for word in ['ink', 'pen', 'marker']):
            return 'Ink'
        elif any(word in name_lower for word in ['water', 'wet']):
            return 'Watercolor'
        elif any(word in name_lower for word in ['oil', 'acrylic', 'paint']):
            return 'Paint'
        elif any(word in name_lower for word in ['airbrush', 'spray']):
            return 'Airbrush'
        elif any(word in name_lower for word in ['eraser', 'erase']):
            return 'Erasers'
        elif any(word in name_lower for word in ['basic', 'circle', 'tip']):
            return 'Basic'
        else:
            return 'Other'
    
    def _get_brush_icon(self, name: str, tags: List[str]) -> str:
        """Get appropriate icon for brush"""
        name_lower = name.lower()
        tags_lower = [tag.lower() for tag in tags]
        
        if any('pencil' in tag for tag in tags_lower) or 'pencil' in name_lower:
            return '✏️'
        elif any('ink' in tag for tag in tags_lower) or 'ink' in name_lower:
            return '🖊️'
        elif any('water' in tag for tag in tags_lower) or 'water' in name_lower:
            return '💧'
        elif any('paint' in tag for tag in tags_lower) or 'paint' in name_lower:
            return '🎨'
        elif any('eraser' in tag for tag in tags_lower) or 'eraser' in name_lower:
            return '🧽'
        elif 'airbrush' in name_lower:
            return '💨'
        else:
            return '🖌️'
    
    def get_popular_brushes(self, limit: int = 20) -> List[Dict]:
        """Get most popular/useful brushes for quick access"""
        all_brushes = self.parse_all_brushes()
        
        # Priority brushes that most artists use
        priority_names = [
            'basic tip default',
            'basic circle', 
            'pencil',
            'ink pen',
            'watercolor',
            'oil paint',
            'airbrush',
            'eraser'
        ]
        
        popular = []
        
        # Add priority brushes first
        for brush in all_brushes['brushes']:
            brush_name_lower = brush['name'].lower()
            
            for priority in priority_names:
                if priority in brush_name_lower and len(popular) < limit:
                    popular.append(brush)
                    break
                    
        # Fill remaining slots with one from each category
        for category, brushes in all_brushes['categories'].items():
            if len(popular) >= limit:
                break
            if brushes and brushes[0] not in popular:
                popular.append(brushes[0])
                
        return popular[:limit]
    
    def build_complete_krita_palette(self) -> Dict:
        """Build complete Krita palette with ALL brushes"""
        logger.info("🏗️ Building COMPLETE Krita palette from database...")
        
        all_brushes = self.parse_all_brushes()
        popular_brushes = self.get_popular_brushes()
        
        palette = {
            'app': 'krita',
            'version': '2.0',
            'source': 'database',
            'total_brushes': all_brushes['total_count'],
            'categories': all_brushes['categories'],
            'quick_access': popular_brushes,
            'tools': {
                'brush_engine': {
                    'name': 'Brush Engine',
                    'icon': '🖌️',
                    'shortcut': 'B',
                    'total_presets': all_brushes['total_count'],
                    'subcategories': all_brushes['categories']
                }
            }
        }
        
        logger.info(f"🎨 Built COMPLETE palette: {all_brushes['total_count']} brushes, {len(all_brushes['categories'])} categories")
        return palette

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    parser = KritaDatabaseParser()
    palette = parser.build_complete_krita_palette()
    
    print(f"🎨 KRITA DATABASE BREAKTHROUGH!")
    print(f"✅ Total brushes: {palette['total_brushes']}")
    print(f"📁 Categories: {list(palette['categories'].keys())}")
    print(f"⭐ Quick access: {len(palette['quick_access'])} popular brushes")
    
    # Save the complete data
    with open('krita_complete_palette.json', 'w') as f:
        json.dump(palette, f, indent=2)
    print("💾 Saved complete palette data!")
