#!/usr/bin/env python3
"""
Optimized Database Parsers for Art Remote Control
High-performance versions of CSP and Krita parsers with intelligent caching
"""

import sqlite3
import json
import platform
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from performance_cache import (
    cached_db_operation, 
    async_cached_db_operation,
    DatabaseQueryOptimizer,
    performance_monitor,
    performance_optimizer
)

logger = logging.getLogger(__name__)

class OptimizedCSPParser:
    """High-performance CSP database parser with intelligent caching"""
    
    def __init__(self):
        self.base_path = self._get_csp_base_path()
        self.menu_db_path = self.base_path / "Shortcut/default.khc"
        self.tool_db_path = self.base_path / "Tool/EditImageTool.todb"
    
    def _get_csp_base_path(self) -> Path:
        """Get CSP base path for current platform"""
        if platform.system() == 'Darwin':
            return Path.home() / "Library/CELSYS/CLIPStudioPaintVer1_5_0"
        else:  # Windows
            return Path.home() / "AppData/Roaming/CELSys/CLIPStudioPaintVer1_5_0"
    
    @performance_monitor
    @cached_db_operation(ttl=600, file_deps=None)  # 10 minute cache
    def load_menu_shortcuts(self) -> Dict[str, Any]:
        """Optimized menu shortcuts loading with caching"""
        if not self.menu_db_path.exists():
            logger.warning(f"CSP menu database not found: {self.menu_db_path}")
            return {}
        
        # Use optimized batch query instead of individual queries
        queries = [
            ("SELECT menucommandtype, menucommand, shortcut, modifier FROM shortcutmenu WHERE shortcut LIKE 'F%' AND shortcut IS NOT NULL", ()),
            ("SELECT COUNT(*) FROM shortcutmenu WHERE shortcut IS NOT NULL", ())
        ]
        
        try:
            results = DatabaseQueryOptimizer.execute_batch_queries(
                self.menu_db_path, queries
            )
            
            shortcuts_data, count_data = results
            shortcuts = {}
            
            for row in shortcuts_data:
                command_type, command, key, modifier = row
                shortcuts[key] = {
                    'command': command,
                    'description': self._get_command_description(command),
                    'icon': self._get_command_icon(command),
                    'source': 'menu',
                    'modifier': modifier
                }
            
            total_shortcuts = count_data[0][0] if count_data else 0
            logger.info(f"✅ Loaded {len(shortcuts)} F-key shortcuts from {total_shortcuts} total CSP shortcuts")
            
            return shortcuts
            
        except Exception as e:
            logger.error(f"Error loading CSP menu shortcuts: {e}")
            return {}
    
    @performance_monitor  
    @cached_db_operation(ttl=600, file_deps=None)
    def load_tool_shortcuts(self) -> Dict[str, Any]:
        """Optimized tool shortcuts loading with caching"""
        if not self.tool_db_path.exists():
            logger.warning(f"CSP tool database not found: {self.tool_db_path}")
            return {}
        
        try:
            # Optimized query with JOIN to reduce round trips
            query = """
                SELECT DISTINCT 
                    t.NodeShortCutKey,
                    t.ToolName,
                    t.SubToolName,
                    g.GroupName
                FROM Tool t
                LEFT JOIN ToolGroup g ON t.GroupID = g.GroupID
                WHERE t.NodeShortCutKey >= 37 AND t.NodeShortCutKey <= 48
                ORDER BY t.NodeShortCutKey
            """
            
            rows = DatabaseQueryOptimizer.execute_query(
                self.tool_db_path, query
            )
            
            shortcuts = {}
            for row in rows:
                shortcut_key, tool_name, subtool_name, group_name = row
                f_key = f"F{shortcut_key - 36}"
                
                shortcuts[f_key] = {
                    'tool': tool_name or 'Unknown Tool',
                    'subtool': subtool_name or '',
                    'group': group_name or 'Default',
                    'source': 'custom_tool',
                    'shortcut_key': shortcut_key
                }
            
            logger.info(f"✅ Loaded {len(shortcuts)} custom tool shortcuts from CSP")
            return shortcuts
            
        except Exception as e:
            logger.error(f"Error loading CSP tool shortcuts: {e}")
            return {}
    
    @performance_monitor
    def get_complete_shortcuts(self) -> Dict[str, Any]:
        """Get complete CSP shortcuts with intelligent merging"""
        menu_shortcuts = self.load_menu_shortcuts()
        tool_shortcuts = self.load_tool_shortcuts()
        
        # Merge with tool shortcuts taking priority
        complete_shortcuts = menu_shortcuts.copy()
        complete_shortcuts.update(tool_shortcuts)
        
        return {
            'shortcuts': complete_shortcuts,
            'menu_count': len(menu_shortcuts),
            'tool_count': len(tool_shortcuts),
            'total_count': len(complete_shortcuts),
            'last_updated': self._get_db_modification_time()
        }
    
    def _get_command_description(self, command: str) -> str:
        """Get human-readable description for command"""
        command_map = {
            'NewLayer': '🆕 New Layer',
            'Undo': '↶ Undo',
            'Redo': '↷ Redo',
            'ZoomIn': '🔍+ Zoom In',
            'ZoomOut': '🔍- Zoom Out',
            'RotateLeft': '↺ Rotate Left',
            'RotateRight': '↻ Rotate Right'
        }
        return command_map.get(command, f"📋 {command}")
    
    def _get_command_icon(self, command: str) -> str:
        """Get icon for command"""
        icon_map = {
            'NewLayer': '🆕',
            'Undo': '↶',
            'Redo': '↷',
            'ZoomIn': '🔍+',
            'ZoomOut': '🔍-'
        }
        return icon_map.get(command, '⚡')
    
    def _get_db_modification_time(self) -> float:
        """Get the latest modification time of CSP databases"""
        latest_time = 0
        for db_path in [self.menu_db_path, self.tool_db_path]:
            if db_path.exists():
                latest_time = max(latest_time, db_path.stat().st_mtime)
        return latest_time

class OptimizedKritaParser:
    """High-performance Krita database parser with intelligent caching"""
    
    def __init__(self):
        self.db_paths = self._get_krita_db_paths()
        self.active_db_path = self._find_active_database()
    
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
    
    def _find_active_database(self) -> Optional[Path]:
        """Find the active Krita database"""
        for path in self.db_paths:
            if path.exists():
                logger.info(f"📁 Found Krita database: {path}")
                return path
        logger.warning("❌ No Krita database found")
        return None
    
    @performance_monitor
    @cached_db_operation(ttl=300, file_deps=None)  # 5 minute cache (brushes change more often)
    def load_all_brushes(self) -> Dict[str, Any]:
        """Optimized brush loading with intelligent caching"""
        if not self.active_db_path:
            return {'brushes': [], 'categories': {}, 'total_count': 0}
        
        try:
            # Optimized query with better indexing
            query = """
                SELECT DISTINCT
                    r.name,
                    r.filename,
                    r.id as resource_id,
                    GROUP_CONCAT(t.name, ',') as tags,
                    r.md5sum
                FROM resources r
                LEFT JOIN resource_tags rt ON r.id = rt.resource_id  
                LEFT JOIN tags t ON rt.tag_id = t.id
                WHERE r.resource_type_id = (
                    SELECT id FROM resource_types WHERE name = 'paintoppresets'
                )
                AND r.status = 1
                GROUP BY r.id, r.name, r.filename, r.md5sum
                ORDER BY r.name
                LIMIT 1000
            """
            
            rows = DatabaseQueryOptimizer.execute_query(
                self.active_db_path, query
            )
            
            brushes = []
            categories = {}
            
            for row in rows:
                name, filename, resource_id, tags, md5sum = row
                
                # Parse tags for categorization
                tag_list = tags.split(',') if tags else []
                category = self._determine_category(name, tag_list)
                
                brush_data = {
                    'name': name,
                    'filename': filename,
                    'id': resource_id,
                    'tags': tag_list,
                    'category': category,
                    'md5': md5sum
                }
                
                brushes.append(brush_data)
                
                # Build category index
                if category not in categories:
                    categories[category] = []
                categories[category].append(brush_data)
            
            result = {
                'brushes': brushes,
                'categories': categories,
                'total_count': len(brushes),
                'category_count': len(categories),
                'last_updated': self._get_db_modification_time()
            }
            
            logger.info(f"✅ Loaded {len(brushes)} Krita brushes in {len(categories)} categories")
            return result
            
        except Exception as e:
            logger.error(f"Error loading Krita brushes: {e}")
            return {'brushes': [], 'categories': {}, 'total_count': 0}
    
    @performance_monitor
    @cached_db_operation(ttl=600, file_deps=None)
    def load_popular_brushes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Load most commonly used brushes for quick access"""
        if not self.active_db_path:
            return []
        
        try:
            # Query for brushes with usage statistics
            query = """
                SELECT DISTINCT
                    r.name,
                    r.filename,
                    r.id,
                    COUNT(rt.resource_id) as tag_count
                FROM resources r
                LEFT JOIN resource_tags rt ON r.id = rt.resource_id
                WHERE r.resource_type_id = (
                    SELECT id FROM resource_types WHERE name = 'paintoppresets'
                )
                AND r.status = 1
                GROUP BY r.id, r.name, r.filename
                ORDER BY tag_count DESC, r.name
                LIMIT ?
            """
            
            rows = DatabaseQueryOptimizer.execute_query(
                self.active_db_path, query, (limit,)
            )
            
            popular_brushes = []
            for row in rows:
                name, filename, resource_id, tag_count = row
                popular_brushes.append({
                    'name': name,
                    'filename': filename,
                    'id': resource_id,
                    'popularity_score': tag_count
                })
            
            logger.info(f"✅ Loaded {len(popular_brushes)} popular Krita brushes")
            return popular_brushes
            
        except Exception as e:
            logger.error(f"Error loading popular brushes: {e}")
            return []
    
    def _determine_category(self, name: str, tags: List[str]) -> str:
        """Determine brush category from name and tags"""
        name_lower = name.lower()
        
        # Category mapping based on common patterns
        if any(tag in ['Basic', 'basic'] for tag in tags):
            return 'Basic'
        elif any(keyword in name_lower for keyword in ['pencil', 'sketch']):
            return 'Sketching'
        elif any(keyword in name_lower for keyword in ['paint', 'brush']):
            return 'Painting'
        elif any(keyword in name_lower for keyword in ['ink', 'pen']):
            return 'Inking'
        elif any(keyword in name_lower for keyword in ['texture', 'rough']):
            return 'Texture'
        elif any(keyword in name_lower for keyword in ['water', 'wet']):
            return 'Watercolor'
        elif any(keyword in name_lower for keyword in ['digital', 'airbrush']):
            return 'Digital'
        else:
            return 'Other'
    
    def _get_db_modification_time(self) -> float:
        """Get database modification time"""
        if self.active_db_path and self.active_db_path.exists():
            return self.active_db_path.stat().st_mtime
        return 0

class OptimizedAppDetector:
    """High-performance app detection with caching"""
    
    def __init__(self):
        self._last_detected_app = None
        self._last_detection_time = 0
        self._detection_interval = 2.0  # Check every 2 seconds instead of constantly
    
    @performance_monitor
    def detect_current_app(self) -> Optional[str]:
        """Optimized app detection with rate limiting"""
        current_time = time.time()
        
        # Rate limit detection to avoid constant polling
        if current_time - self._last_detection_time < self._detection_interval:
            return self._last_detected_app
        
        try:
            if platform.system() == 'Darwin':
                # macOS detection
                detected_app = self._detect_macos_app()
            else:
                # Windows detection
                detected_app = self._detect_windows_app()
            
            # Only log if app changed
            if detected_app != self._last_detected_app:
                logger.info(f"🎯 App changed: {self._last_detected_app} → {detected_app}")
                self._last_detected_app = detected_app
            
            self._last_detection_time = current_time
            return detected_app
            
        except Exception as e:
            logger.error(f"Error detecting app: {e}")
            return self._last_detected_app
    
    def _detect_macos_app(self) -> Optional[str]:
        """Detect active app on macOS"""
        try:
            import AppKit
            workspace = AppKit.NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            app_name = active_app['NSApplicationName']
            
            if 'clip studio paint' in app_name.lower():
                return 'csp'
            elif 'krita' in app_name.lower():
                return 'krita'
            else:
                return None
                
        except ImportError:
            return self._detect_fallback()
    
    def _detect_windows_app(self) -> Optional[str]:
        """Detect active app on Windows"""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                name = proc.info['name'].lower()
                if 'clipstudiopaint' in name or 'csp' in name:
                    return 'csp'
                elif 'krita' in name:
                    return 'krita'
            return None
            
        except ImportError:
            return self._detect_fallback()
    
    def _detect_fallback(self) -> Optional[str]:
        """Fallback detection method"""
        return self._last_detected_app

# Global instances for easy access
optimized_csp_parser = OptimizedCSPParser()
optimized_krita_parser = OptimizedKritaParser()
optimized_app_detector = OptimizedAppDetector()
