#!/usr/bin/env python3
"""
KRITA BRUSH PARSER - THE NEXT REVOLUTION!
Parses Krita's brush preset system to dynamically build tool palettes
Just like we cracked CSP, now we crack Krita!

Krita stores brush presets in:
- macOS: ~/Library/Application Support/krita/
- Windows: %APPDATA%/krita/
- Linux: ~/.local/share/krita/

Files:
- kritarc - Main config file  
- paintoppresets/ - Brush preset files (.kpp)
- tags/ - Tag assignments for brushes
- workspaces/ - Custom workspace layouts
"""

import os
import json
import logging
import configparser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
import platform

logger = logging.getLogger(__name__)

class KritaBrushParser:
    def __init__(self):
        self.base_paths = self._get_krita_paths()
        self.brush_presets = {}
        self.brush_categories = {}
        self.tag_assignments = {}
        
    def _get_krita_paths(self) -> Dict[str, Path]:
        """Get Krita config paths for current platform"""
        system = platform.system()
        
        if system == 'Darwin':  # macOS
            base = Path.home() / "Library/Application Support/krita"
        elif system == 'Windows':
            base = Path.home() / "AppData/Roaming/krita"
        else:  # Linux
            base = Path.home() / ".local/share/krita"
            
        return {
            'base': base,
            'config': base / 'kritarc',
            'presets': base / 'paintoppresets',
            'tags': base / 'tags',
            'workspaces': base / 'workspaces',
            'resources': base / 'resources'
        }
    
    def is_krita_installed(self) -> bool:
        """Check if Krita is installed by looking for config files"""
        return self.base_paths['base'].exists() and self.base_paths['presets'].exists()
    
    def parse_brush_presets(self) -> Dict:
        """Parse all Krita brush presets - THE MAIN EVENT!"""
        if not self.is_krita_installed():
            logger.warning("⚠️ Krita not found - no brush presets available")
            return {}
            
        logger.info("🎨 PARSING KRITA BRUSH PRESETS...")
        
        presets_dir = self.base_paths['presets']
        if not presets_dir.exists():
            logger.warning("No brush presets directory found")
            return {}
            
        brush_data = {
            'categories': {},
            'presets': {},
            'total_count': 0
        }
        
        # Parse .kpp files (Krita Paint Presets)
        for preset_file in presets_dir.glob('*.kpp'):
            try:
                preset_info = self._parse_kpp_file(preset_file)
                if preset_info:
                    category = preset_info.get('category', 'Other')
                    
                    if category not in brush_data['categories']:
                        brush_data['categories'][category] = []
                        
                    brush_data['categories'][category].append(preset_info)
                    brush_data['presets'][preset_info['name']] = preset_info
                    brush_data['total_count'] += 1
                    
            except Exception as e:
                logger.warning(f"Failed to parse {preset_file.name}: {e}")
                
        logger.info(f"🖌️ Found {brush_data['total_count']} brush presets in {len(brush_data['categories'])} categories")
        return brush_data
    
    def _parse_kpp_file(self, preset_file: Path) -> Optional[Dict]:
        """Parse individual .kpp brush preset file"""
        try:
            # .kpp files are actually ZIP archives with XML inside
            import zipfile
            
            with zipfile.ZipFile(preset_file, 'r') as zip_file:
                # Look for the main preset XML
                for file_info in zip_file.filelist:
                    if file_info.filename.endswith('.kpp') or 'preset' in file_info.filename.lower():
                        with zip_file.open(file_info) as xml_file:
                            return self._parse_preset_xml(xml_file.read(), preset_file.stem)
                            
        except Exception as e:
            # Fallback: treat as plain text/ini file
            logger.debug(f"ZIP parsing failed for {preset_file.name}, trying text parsing: {e}")
            return self._parse_preset_text(preset_file)
            
        return None
    
    def _parse_preset_xml(self, xml_data: bytes, preset_name: str) -> Dict:
        """Parse XML data from .kpp file"""
        try:
            root = ET.fromstring(xml_data)
            
            # Extract brush info from XML
            preset_info = {
                'name': preset_name,
                'display_name': preset_name.replace('_', ' ').title(),
                'category': 'Default',
                'engine': 'unknown',
                'icon': '🖌️',
                'file_path': preset_name  # Use preset_name since preset_file not available here
            }
            
            # Look for specific XML elements
            for elem in root.iter():
                if 'paintop' in elem.tag.lower():
                    preset_info['engine'] = elem.text or 'brush'
                elif 'category' in elem.tag.lower():
                    preset_info['category'] = elem.text or 'Default'
                    
            return preset_info
            
        except ET.ParseError as e:
            logger.debug(f"XML parsing failed: {e}")
            return self._create_basic_preset_info(preset_name)
    
    def _parse_preset_text(self, preset_file: Path) -> Dict:
        """Fallback: parse as text/ini file"""
        try:
            config = configparser.ConfigParser()
            config.read(preset_file)
            
            preset_info = self._create_basic_preset_info(preset_file.stem)
            
            # Try to extract info from INI sections
            if config.sections():
                for section in config.sections():
                    if 'paintop' in section.lower():
                        preset_info['engine'] = section
                        break
                        
            return preset_info
            
        except Exception as e:
            logger.debug(f"Text parsing failed: {e}")
            return self._create_basic_preset_info(preset_file.stem)
    
    def _create_basic_preset_info(self, preset_name: str) -> Dict:
        """Create basic preset info when parsing fails"""
        # Categorize based on name patterns
        name_lower = preset_name.lower()
        
        if any(word in name_lower for word in ['pencil', 'hb', '2b', '4b']):
            category = 'Pencils'
            icon = '✏️'
        elif any(word in name_lower for word in ['pen', 'ink', 'marker']):
            category = 'Pens'  
            icon = '🖊️'
        elif any(word in name_lower for word in ['water', 'wet', 'paint']):
            category = 'Watercolor'
            icon = '💧'
        elif any(word in name_lower for word in ['oil', 'acrylic', 'impasto']):
            category = 'Oil Paint'
            icon = '🎨'
        elif any(word in name_lower for word in ['charcoal', 'chalk', 'pastel']):
            category = 'Dry Media'
            icon = '🖤'
        elif any(word in name_lower for word in ['texture', 'effect', 'experimental']):
            category = 'Effects'
            icon = '✨'
        else:
            category = 'Brushes'
            icon = '🖌️'
            
        return {
            'name': preset_name,
            'display_name': preset_name.replace('_', ' ').title(),
            'category': category,
            'engine': 'brush',
            'icon': icon,
            'file_path': preset_name
        }
    
    def get_popular_presets(self, limit: int = 12) -> List[Dict]:
        """Get most commonly used brush presets for quick access"""
        brush_data = self.parse_brush_presets()
        
        # Priority order for popular brushes
        priority_brushes = [
            'basic_tip_default',
            'basic_circle',
            'pencil_2b',
            'ink_pen',
            'watercolor_basic',
            'oil_paint_basic',
            'charcoal_soft',
            'eraser_soft',
            'smudge_basic',
            'clone_basic',
            'blur_basic',
            'texture_basic'
        ]
        
        popular = []
        
        # Add priority brushes first
        for brush_name in priority_brushes:
            for preset_name, preset_info in brush_data.get('presets', {}).items():
                if any(priority in preset_name.lower() for priority in [brush_name, brush_name.replace('_', '')]):
                    if preset_info not in popular:
                        popular.append(preset_info)
                        break
                        
        # Fill remaining slots with first brush from each category
        for category, presets in brush_data.get('categories', {}).items():
            if len(popular) >= limit:
                break
            if presets and presets[0] not in popular:
                popular.append(presets[0])
                
        return popular[:limit]
    
    def build_krita_tool_palette(self) -> Dict:
        """Build complete Krita tool palette structure"""
        logger.info("🏗️ Building Krita tool palette structure...")
        
        brush_data = self.parse_brush_presets()
        popular_presets = self.get_popular_presets()
        
        palette = {
            'app': 'krita',
            'version': '1.0',
            'total_brushes': brush_data.get('total_count', 0),
            'categories': {},
            'quick_access': popular_presets,
            'tools': {
                'brush': {
                    'name': 'Brush Engine',
                    'icon': '🖌️',
                    'shortcut': 'B',
                    'subcategories': brush_data.get('categories', {})
                },
                'eraser': {
                    'name': 'Eraser',
                    'icon': '🧽', 
                    'shortcut': 'E',
                    'subcategories': {}
                },
                'selection': {
                    'name': 'Selection Tools',
                    'icon': '⬚',
                    'shortcut': 'R',
                    'subcategories': {
                        'Rectangle': [{'name': 'Rectangle Select', 'shortcut': 'R'}],
                        'Ellipse': [{'name': 'Ellipse Select', 'shortcut': 'J'}],
                        'Polygon': [{'name': 'Polygon Select', 'shortcut': 'U'}],
                        'Freehand': [{'name': 'Freehand Select', 'shortcut': 'O'}]
                    }
                }
            }
        }
        
        logger.info(f"🎨 Built Krita palette with {len(brush_data.get('categories', {}))} brush categories")
        return palette

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    parser = KritaBrushParser()
    
    if parser.is_krita_installed():
        print("🎨 Krita installation detected!")
        palette = parser.build_krita_tool_palette()
        
        # Save the palette data
        with open('krita_tool_palette.json', 'w') as f:
            json.dump(palette, f, indent=2)
            
        print(f"✅ Krita palette built with {palette['total_brushes']} brushes!")
        print(f"📁 Categories: {list(palette['tools']['brush']['subcategories'].keys())}")
        
    else:
        print("❌ Krita not found on this system")
