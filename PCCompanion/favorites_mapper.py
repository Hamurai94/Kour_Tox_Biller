#!/usr/bin/env python3
"""
CSP Favorites Mapper - Lets users teach the app their F1-F10 assignments
"""

import json
import logging
from pathlib import Path

class CSPFavoritesMapper:
    def __init__(self):
        self.favorites_file = Path("csp_favorites_mapping.json")
        self.favorites_map = self.load_favorites()
        
    def load_favorites(self):
        """Load existing favorites mapping or create default"""
        if self.favorites_file.exists():
            try:
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load favorites: {e}")
        
        # Default mapping
        return {
            "f1": {"name": "Favorite 1", "icon": "🖌️", "tool_type": "brush"},
            "f2": {"name": "Favorite 2", "icon": "🖊️", "tool_type": "pen"},
            "f3": {"name": "Favorite 3", "icon": "✏️", "tool_type": "pencil"},
            "f4": {"name": "Favorite 4", "icon": "🎨", "tool_type": "airbrush"},
            "f5": {"name": "Favorite 5", "icon": "🧹", "tool_type": "eraser"},
            "f6": {"name": "Favorite 6", "icon": "🖌️", "tool_type": "brush"},
            "f7": {"name": "Favorite 7", "icon": "🖌️", "tool_type": "brush"},
            "f8": {"name": "Favorite 8", "icon": "🖌️", "tool_type": "brush"},
            "f9": {"name": "Favorite 9", "icon": "🖌️", "tool_type": "brush"},
            "f10": {"name": "Favorite 10", "icon": "🖌️", "tool_type": "brush"}
        }
    
    def update_favorite(self, fkey, name, icon, tool_type):
        """Update a favorite assignment"""
        self.favorites_map[fkey] = {
            "name": name,
            "icon": icon, 
            "tool_type": tool_type
        }
        self.save_favorites()
    
    def save_favorites(self):
        """Save favorites mapping to file"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites_map, f, indent=2, ensure_ascii=False)
            logging.info(f"Favorites saved to {self.favorites_file}")
        except Exception as e:
            logging.error(f"Failed to save favorites: {e}")
    
    def get_favorites_for_android(self):
        """Get favorites in format for Android app"""
        android_favorites = []
        
        for fkey, data in self.favorites_map.items():
            android_favorites.append({
                "uuid": f"fav_{fkey}",
                "name": f"{data['name']} ({fkey.upper()})",
                "icon": data['icon'],
                "shortcut": fkey.upper(),
                "parentTool": "favorites"
            })
            
        return android_favorites

if __name__ == "__main__":
    # Example usage
    mapper = CSPFavoritesMapper()
    
    # User could update their favorites like this:
    # mapper.update_favorite("f1", "G-pen (Thick)", "🖊️", "pen")
    # mapper.update_favorite("f2", "Wind Brush Large", "🌪️", "brush")
    
    print("Current favorites mapping:")
    favorites = mapper.get_favorites_for_android()
    for fav in favorites:
        print(f"  {fav['shortcut']}: {fav['icon']} {fav['name']}")
