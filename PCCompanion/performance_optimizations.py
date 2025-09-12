#!/usr/bin/env python3
"""
Performance Optimizations Integration for Art Remote Control Server
Patches the main server with high-performance components
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any
from performance_cache import performance_monitor, performance_optimizer
from optimized_parsers import optimized_csp_parser, optimized_krita_parser, optimized_app_detector

logger = logging.getLogger(__name__)

class PerformanceEnhancedServer:
    """Mixin class to add performance optimizations to the main server"""
    
    def __init__(self):
        # Performance tracking
        self._performance_stats = {
            'messages_processed': 0,
            'avg_message_time': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_stats_reset': time.time()
        }
        
        # Async message processing
        self.message_queue = asyncio.Queue(maxsize=100)
        self._processing_task = None
        
        # Rate limiting for expensive operations
        self._last_app_detection = 0
        self._app_detection_interval = 2.0
        
        # Cached data with TTL
        self._cached_shortcuts = {}
        self._shortcuts_cache_time = 0
        self._shortcuts_cache_ttl = 300  # 5 minutes
    
    async def start_performance_systems(self):
        """Start performance-related async tasks"""
        if not self._processing_task:
            self._processing_task = asyncio.create_task(self._message_processor())
            logger.info("🚀 Performance message processor started")
    
    async def stop_performance_systems(self):
        """Stop performance-related async tasks"""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None
            logger.info("⏹️ Performance systems stopped")
    
    @performance_monitor
    async def optimized_handle_message(self, websocket, message):
        """High-performance message handling with async queue"""
        try:
            # Authentication check (fast path)
            if self.require_auth and websocket not in self.authenticated_clients:
                await websocket.send('{"type":"error","message":"Authentication required"}')
                return
            
            # Parse JSON (with error handling)
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                return
            
            # Add to processing queue (non-blocking)
            try:
                self.message_queue.put_nowait((websocket, data, time.time()))
                self._performance_stats['messages_processed'] += 1
            except asyncio.QueueFull:
                logger.warning("Message queue full, dropping message")
                
        except Exception as e:
            logger.error(f"Error in optimized message handler: {e}")
    
    async def _message_processor(self):
        """Async message processor for better throughput"""
        while True:
            try:
                # Process messages in batches for better performance
                messages_batch = []
                
                # Collect up to 10 messages or wait 10ms
                try:
                    websocket, data, timestamp = await asyncio.wait_for(
                        self.message_queue.get(), timeout=0.01
                    )
                    messages_batch.append((websocket, data, timestamp))
                    
                    # Try to get more messages (non-blocking)
                    while len(messages_batch) < 10:
                        try:
                            item = self.message_queue.get_nowait()
                            messages_batch.append(item)
                        except asyncio.QueueEmpty:
                            break
                            
                except asyncio.TimeoutError:
                    continue
                
                # Process batch
                if messages_batch:
                    await self._process_message_batch(messages_batch)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message processor: {e}")
    
    async def _process_message_batch(self, messages_batch):
        """Process a batch of messages efficiently"""
        start_time = time.time()
        
        # Group messages by type for batch processing
        grouped_messages = {}
        for websocket, data, timestamp in messages_batch:
            msg_type = data.get('action', 'unknown')
            if msg_type not in grouped_messages:
                grouped_messages[msg_type] = []
            grouped_messages[msg_type].append((websocket, data, timestamp))
        
        # Process each group
        for msg_type, group in grouped_messages.items():
            try:
                await self._process_message_group(msg_type, group)
            except Exception as e:
                logger.error(f"Error processing {msg_type} group: {e}")
        
        # Update performance stats
        processing_time = time.time() - start_time
        self._update_performance_stats(len(messages_batch), processing_time)
    
    async def _process_message_group(self, msg_type: str, group):
        """Process a group of messages of the same type"""
        # Rate-limited app detection (only once per group)
        if time.time() - self._last_app_detection > self._app_detection_interval:
            self.optimized_detect_current_app()
            self._last_app_detection = time.time()
        
        # Process messages
        for websocket, data, timestamp in group:
            try:
                await self._execute_optimized_action(websocket, data)
            except Exception as e:
                logger.error(f"Error executing {msg_type}: {e}")
    
    @performance_monitor
    async def _execute_optimized_action(self, websocket, data):
        """Execute action with performance optimizations"""
        action = data.get('action')
        value = data.get('value')
        
        # Fast path for common actions
        if action == 'zoom':
            await self.handle_zoom(value)
        elif action == 'rotate':
            await self.handle_rotate(value)
        elif action == 'undo':
            await self.execute_app_shortcut('undo')
        elif action == 'redo':
            await self.execute_app_shortcut('redo')
        elif action == 'tool':
            await self._handle_optimized_tool_switch(value)
        elif action == 'shortcut':
            await self._handle_optimized_shortcut(data)
        else:
            # Fallback to original handler
            await self._handle_other_action(action, value)
    
    async def _handle_optimized_tool_switch(self, value):
        """Optimized tool switching with caching"""
        tool_name = value.get('name') if isinstance(value, dict) else value
        
        # Use cached shortcuts if available
        shortcuts = self._get_cached_shortcuts()
        
        if tool_name in shortcuts:
            shortcut = shortcuts[tool_name]
            await self.execute_app_shortcut(shortcut)
        else:
            logger.warning(f"Unknown tool: {tool_name}")
    
    async def _handle_optimized_shortcut(self, data):
        """Optimized shortcut handling"""
        shortcut_key = data.get('key')
        if shortcut_key:
            await self.execute_app_shortcut(shortcut_key)
    
    def _get_cached_shortcuts(self) -> Dict[str, Any]:
        """Get shortcuts with intelligent caching"""
        current_time = time.time()
        
        # Check cache validity
        if (current_time - self._shortcuts_cache_time > self._shortcuts_cache_ttl or 
            not self._cached_shortcuts):
            
            # Refresh cache
            if self.current_app == 'csp':
                self._cached_shortcuts = optimized_csp_parser.get_complete_shortcuts()
            elif self.current_app == 'krita':
                self._cached_shortcuts = optimized_krita_parser.load_all_brushes()
            else:
                self._cached_shortcuts = {}
            
            self._shortcuts_cache_time = current_time
            self._performance_stats['cache_misses'] += 1
        else:
            self._performance_stats['cache_hits'] += 1
        
        return self._cached_shortcuts
    
    @performance_monitor
    def optimized_detect_current_app(self):
        """Optimized app detection with caching"""
        detected_app = optimized_app_detector.detect_current_app()
        
        if detected_app != self.current_app:
            self.current_app = detected_app
            # Invalidate shortcuts cache when app changes
            self._shortcuts_cache_time = 0
            if detected_app:
                logger.info(f"🎯 App detected: {detected_app}")
    
    def _update_performance_stats(self, message_count: int, processing_time: float):
        """Update performance statistics"""
        # Calculate average processing time
        total_messages = self._performance_stats['messages_processed']
        if total_messages > 0:
            current_avg = self._performance_stats['avg_message_time']
            new_avg = (current_avg * (total_messages - message_count) + 
                      processing_time) / total_messages
            self._performance_stats['avg_message_time'] = new_avg
        
        # Log performance warnings
        avg_per_message = processing_time / message_count if message_count > 0 else 0
        if avg_per_message > 0.05:  # More than 50ms per message
            logger.warning(f"Slow message processing: {avg_per_message:.3f}s per message")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        stats = self._performance_stats.copy()
        stats['queue_size'] = self.message_queue.qsize()
        stats['uptime'] = time.time() - stats['last_stats_reset']
        
        # Calculate cache hit rate
        total_cache_ops = stats['cache_hits'] + stats['cache_misses']
        if total_cache_ops > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / total_cache_ops
        else:
            stats['cache_hit_rate'] = 0
        
        return stats
    
    def reset_performance_stats(self):
        """Reset performance statistics"""
        self._performance_stats = {
            'messages_processed': 0,
            'avg_message_time': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_stats_reset': time.time()
        }

def apply_performance_optimizations(server_instance):
    """Apply performance optimizations to existing server instance"""
    # Add performance methods to server
    for method_name in dir(PerformanceEnhancedServer):
        if not method_name.startswith('_') or method_name in ['__init__']:
            continue
        method = getattr(PerformanceEnhancedServer, method_name)
        if callable(method):
            setattr(server_instance, method_name, method.__get__(server_instance))
    
    # Initialize performance systems
    performance_enhanced = PerformanceEnhancedServer()
    server_instance.__dict__.update(performance_enhanced.__dict__)
    
    logger.info("🚀 Performance optimizations applied to server")
