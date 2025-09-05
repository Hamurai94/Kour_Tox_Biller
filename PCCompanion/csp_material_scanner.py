#!/usr/bin/env python3
"""
CSP Material Scanner - Parses Clip Studio Paint materials and brushes
Builds a database of available tools with thumbnails for the Android app
"""

import os
import xml.etree.ElementTree as ET
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class CSPMaterialScanner:
    def __init__(self):
        self.material_paths = [
            Path.home() / "Library/CELSYS/CLIPStudioCommon/Material",
            Path.home() / "Documents/CELSYS/CLIPStudioCommon/Material",
            Path.home() / "Library/CELSYS/CLIPStudioPaintVer1_5_0/Material"
        ]
        self.brush_database = []
        
    def scan_all_materials(self) -> List[Dict]:
        """Scan all CSP material directories for brushes and tools"""
        logger.info("🔍 Scanning CSP materials...")
        
        all_brushes = []
        
        for base_path in self.material_paths:
            if base_path.exists():
                logger.info(f"📁 Scanning: {base_path}")
                brushes = self._scan_material_directory(base_path)
                all_brushes.extend(brushes)
                logger.info(f"✅ Found {len(brushes)} brushes in {base_path.name}")
            else:
                logger.warning(f"❌ Path not found: {base_path}")
        
        # Remove duplicates based on UUID
        unique_brushes = {}
        for brush in all_brushes:
            uuid = brush.get('uuid')
            if uuid and uuid not in unique_brushes:
                unique_brushes[uuid] = brush
        
        final_brushes = list(unique_brushes.values())
        logger.info(f"🎨 Total unique brushes found: {len(final_brushes)}")
        
        return final_brushes
    
    def _scan_material_directory(self, base_path: Path) -> List[Dict]:
        """Scan a specific material directory"""
        brushes = []
        
        # Look for catalog.xml files in subdirectories
        for root, dirs, files in os.walk(base_path):
            if 'catalog.xml' in files:
                catalog_path = Path(root) / 'catalog.xml'
                try:
                    brush_data = self._parse_catalog_xml(catalog_path)
                    if brush_data:
                        brushes.extend(brush_data)
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing {catalog_path}: {e}")
        
        return brushes
    
    def _parse_catalog_xml(self, catalog_path: Path) -> List[Dict]:
        """Parse a catalog.xml file to extract brush information"""
        try:
            tree = ET.parse(catalog_path)
            root = tree.getroot()
            
            brushes = []
            
            # Find all items with type="brush"
            for item in root.findall('.//item'):
                type_elem = item.find('type')
                if type_elem is not None and 'brush' in type_elem.text:
                    brush_info = self._extract_brush_info(item, catalog_path.parent)
                    if brush_info:
                        brushes.append(brush_info)
            
            return brushes
            
        except ET.ParseError as e:
            logger.error(f"❌ XML Parse error in {catalog_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error parsing {catalog_path}: {e}")
            return []
    
    def _extract_brush_info(self, item_elem: ET.Element, base_path: Path) -> Optional[Dict]:
        """Extract brush information from an item element"""
        try:
            # Get basic info
            uuid = item_elem.get('uuid', '')
            name_elem = item_elem.find('name')
            name = name_elem.text if name_elem is not None else 'Unknown Brush'
            
            type_elem = item_elem.find('type')
            brush_type = type_elem.text if type_elem is not None else 'brush'
            
            # Get thumbnail path
            thumbnail_elem = item_elem.find('.//thumbnail/fileref')
            thumbnail_path = None
            if thumbnail_elem is not None:
                # Find the corresponding file in the files section
                thumbnail_id = thumbnail_elem.get('idref')
                thumbnail_path = self._find_file_path(item_elem, thumbnail_id, base_path)
            
            # Get creation date
            created_elem = item_elem.find('created_date')
            created_date = created_elem.text if created_elem is not None else ''
            
            brush_info = {
                'uuid': uuid,
                'name': name,
                'type': brush_type,
                'thumbnail_path': str(thumbnail_path) if thumbnail_path else None,
                'created_date': created_date,
                'category': self._determine_category(name),
                'base_path': str(base_path)
            }
            
            return brush_info
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting brush info: {e}")
            return None
    
    def _find_file_path(self, item_elem: ET.Element, file_id: str, base_path: Path) -> Optional[Path]:
        """Find the actual file path for a given file ID"""
        try:
            # Look for files section in the parent catalog
            catalog_root = item_elem
            while catalog_root.getparent() is not None:
                catalog_root = catalog_root.getparent()
            
            # Find file with matching ID
            for file_elem in catalog_root.findall('.//file'):
                if file_elem.get('id') == file_id:
                    path_elem = file_elem.find('path')
                    if path_elem is not None:
                        relative_path = path_elem.text
                        full_path = base_path / relative_path
                        if full_path.exists():
                            return full_path
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Error finding file path: {e}")
            return None
    
    def _determine_category(self, name: str) -> str:
        """Determine brush category based on name"""
        name_lower = name.lower()
        
        if '風' in name or 'wind' in name_lower:
            return 'Wind/Nature'
        elif 'pen' in name_lower or 'ペン' in name:
            return 'Pen'
        elif 'pencil' in name_lower or '鉛筆' in name:
            return 'Pencil'
        elif 'water' in name_lower or '水彩' in name:
            return 'Watercolor'
        elif 'oil' in name_lower or '油彩' in name:
            return 'Oil Paint'
        elif 'marker' in name_lower or 'マーカー' in name:
            return 'Marker'
        elif 'airbrush' in name_lower or 'エアブラシ' in name:
            return 'Airbrush'
        else:
            return 'Other'
    
    def generate_brush_database(self) -> Dict:
        """Generate complete brush database for the Android app"""
        logger.info("🎨 Generating brush database...")
        
        brushes = self.scan_all_materials()
        
        # Organize by category
        categories = {}
        for brush in brushes:
            category = brush['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(brush)
        
        # Sort categories by number of brushes (most used first)
        sorted_categories = dict(sorted(categories.items(), 
                                      key=lambda x: len(x[1]), 
                                      reverse=True))
        
        database = {
            'version': '1.0.0',
            'generated_at': str(Path().cwd()),
            'total_brushes': len(brushes),
            'categories': sorted_categories,
            'recent_brushes': brushes[:10]  # First 10 as "recent"
        }
        
        return database
    
    def save_database(self, output_path: str):
        """Save brush database to JSON file"""
        database = self.generate_brush_database()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Brush database saved to: {output_path}")
        return database

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    scanner = CSPMaterialScanner()
    database = scanner.save_database('csp_brush_database.json')
    
    print(f"\n🎨 CSP Material Scan Complete!")
    print(f"📊 Total brushes found: {database['total_brushes']}")
    print(f"📁 Categories: {len(database['categories'])}")
    
    for category, brushes in database['categories'].items():
        print(f"  • {category}: {len(brushes)} brushes")
    
    print(f"\n💾 Database saved to: csp_brush_database.json")
