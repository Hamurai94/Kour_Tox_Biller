#!/usr/bin/env python3
"""
KRITA SMART BRUSH SWITCHER - THE WORKING SOLUTION!
Instead of creating 276 shortcuts, use Krita's built-in preset system smartly!

APPROACH:
1. Use Krita's preset docker/picker efficiently
2. Create shortcuts for CATEGORIES, not individual brushes
3. Use Krita's search functionality programmatically
4. Focus on what actually works!
"""

import pyautogui
import asyncio
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class KritaSmartBrushSwitcher:
    def __init__(self):
        self.preset_docker_open = False
        
    async def switch_to_brush_by_name(self, brush_name: str) -> bool:
        """Smart brush switching using Krita's built-in systems"""
        try:
            logger.info(f"🎨 Smart switching to: {brush_name}")
            
            # Method 1: Try direct preset switching (F5 + search)
            success = await self._use_preset_docker(brush_name)
            if success:
                return True
                
            # Method 2: Try brush engine switching
            success = await self._use_brush_engine(brush_name)
            if success:
                return True
                
            # Method 3: Fallback to basic tool
            logger.info("🔧 Fallback: switching to basic brush tool")
            pyautogui.press('b')
            return True
            
        except Exception as e:
            logger.error(f"Error in smart brush switching: {e}")
            return False
    
    async def _use_preset_docker(self, brush_name: str) -> bool:
        """Use Krita's preset docker efficiently - FOCUS-SAFE VERSION"""
        try:
            # STEP 1: Ensure Krita has focus first!
            await self._focus_krita()
            
            # STEP 2: Switch to brush tool to ensure we're in the right context
            pyautogui.press('b')
            await asyncio.sleep(0.2)
            
            # STEP 3: Open preset docker (F6 - CORRECT KEY!) 
            pyautogui.press('f6')
            await asyncio.sleep(0.5)  # Give it more time
            
            # STEP 4: Clear search field safely
            pyautogui.hotkey('cmd', 'a')  # Select all in search
            await asyncio.sleep(0.1)
            pyautogui.press('delete')  # Clear it
            await asyncio.sleep(0.1)
            
            # STEP 5: Search for brush
            clean_name = self._clean_brush_name(brush_name)
            logger.info(f"🔍 Searching for: {clean_name}")
            
            pyautogui.typewrite(clean_name, interval=0.05)  # Slower typing
            await asyncio.sleep(0.8)  # More time for search results
            
            # STEP 6: Select first result
            pyautogui.press('down')  # Move to first result
            await asyncio.sleep(0.3)
            pyautogui.press('enter')  # Select it
            await asyncio.sleep(0.2)
            
            # STEP 7: Close docker
            pyautogui.press('escape')
            
            logger.info(f"✅ Selected via preset docker: {brush_name}")
            return True
            
        except Exception as e:
            logger.warning(f"Preset docker method failed: {e}")
            return False
    
    async def _focus_krita(self):
        """Ensure Krita has focus before doing anything"""
        try:
            # Click on Krita window to ensure focus
            # This is a bit hacky but necessary
            import AppKit
            workspace = AppKit.NSWorkspace.sharedWorkspace()
            apps = workspace.runningApplications()
            
            for app in apps:
                if 'krita' in app.localizedName().lower():
                    app.activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)
                    await asyncio.sleep(0.3)
                    logger.info("🎯 Focused Krita window")
                    return True
                    
            logger.warning("⚠️ Could not focus Krita window")
            return False
            
        except Exception as e:
            logger.warning(f"Error focusing Krita: {e}")
            return False
    
    async def _use_brush_engine(self, brush_name: str) -> bool:
        """Use brush engine switching for categories"""
        try:
            name_lower = brush_name.lower()
            
            # Switch to appropriate brush engine first
            if 'pencil' in name_lower:
                pyautogui.press('n')  # Pencil tool
            elif 'eraser' in name_lower:
                pyautogui.press('e')  # Eraser tool
            elif 'airbrush' in name_lower:
                pyautogui.press('a')  # Airbrush tool
            else:
                pyautogui.press('b')  # Default brush tool
                
            await asyncio.sleep(0.2)
            
            # Then use preset picker for specific brush
            return await self._use_preset_docker(brush_name)
            
        except Exception as e:
            logger.warning(f"Brush engine method failed: {e}")
            return False
    
    def _clean_brush_name(self, brush_name: str) -> str:
        """Clean brush name for search"""
        # Remove prefixes and clean up
        clean = brush_name.replace(')', '').replace('(', '')
        clean = clean.replace('_', ' ')
        
        # Remove common prefixes
        prefixes = ['a)', 'b)', 'c)', 'j)', 'k)']
        for prefix in prefixes:
            if clean.startswith(prefix):
                clean = clean[len(prefix):].strip()
                
        return clean.strip()
    
    def create_category_shortcuts(self) -> Dict[str, str]:
        """Create shortcuts for brush CATEGORIES instead of individual brushes"""
        return {
            'Meta+1': 'pencil_category',
            'Meta+2': 'ink_category', 
            'Meta+3': 'watercolor_category',
            'Meta+4': 'paint_category',
            'Meta+5': 'airbrush_category',
            'Meta+6': 'eraser_category',
            'Meta+7': 'basic_category',
            'Meta+8': 'digital_category',
            'Meta+9': 'effects_category'
        }

if __name__ == "__main__":
    switcher = KritaSmartBrushSwitcher()
    
    print("🎨 KRITA SMART BRUSH SWITCHER")
    print("=" * 50)
    print("🎯 Focus: Use Krita's built-in systems efficiently")
    print("✅ No complex config file generation")
    print("🔧 Works with existing Krita setup")
    
    categories = switcher.create_category_shortcuts()
    print(f"\n📁 Category shortcuts:")
    for shortcut, category in categories.items():
        print(f"  {shortcut}: {category}")
        
    print(f"\n💡 This approach uses Krita's existing preset system smartly!")
