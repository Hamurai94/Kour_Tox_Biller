#!/usr/bin/env python3
"""
Performance Cache System for Art Remote Control
Addresses major performance bottlenecks with intelligent caching and connection pooling
"""

import sqlite3
import json
import time
import hashlib
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import logging
from functools import wraps
from contextlib import contextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class DatabaseConnectionPool:
    """Thread-safe SQLite connection pool for better performance"""
    
    def __init__(self, db_path: Path, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._connections = []
        self._lock = threading.Lock()
        self._used_connections = set()
        
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        conn = None
        try:
            with self._lock:
                # Try to get an existing connection
                if self._connections:
                    conn = self._connections.pop()
                elif len(self._used_connections) < self.max_connections:
                    # Create new connection
                    conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
                    conn.row_factory = sqlite3.Row  # Enable dict-like access
                else:
                    # Wait for a connection to become available
                    pass
                    
                if conn:
                    self._used_connections.add(conn)
                    
            if not conn:
                # Fallback: create temporary connection
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row
                
            yield conn
            
        finally:
            if conn:
                with self._lock:
                    if conn in self._used_connections:
                        self._used_connections.remove(conn)
                        self._connections.append(conn)
                    else:
                        # Temporary connection, close it
                        conn.close()
    
    def close_all(self):
        """Close all connections in the pool"""
        with self._lock:
            for conn in self._connections:
                conn.close()
            for conn in self._used_connections:
                conn.close()
            self._connections.clear()
            self._used_connections.clear()

class IntelligentCache:
    """Intelligent caching system with TTL and dependency tracking"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.timestamps = {}
        self.dependencies = {}  # Track file dependencies
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
        
    def _get_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function call"""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        return hashlib.md5(str(key_data).encode()).hexdigest()
    
    def _is_expired(self, key: str, ttl: int) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        return time.time() - self.timestamps[key] > ttl
    
    def _check_file_dependencies(self, key: str) -> bool:
        """Check if any file dependencies have changed"""
        if key not in self.dependencies:
            return False
            
        for file_path, last_mtime in self.dependencies[key].items():
            try:
                current_mtime = Path(file_path).stat().st_mtime
                if current_mtime > last_mtime:
                    return True
            except (OSError, FileNotFoundError):
                # File deleted or inaccessible, invalidate cache
                return True
        return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if valid"""
        with self._lock:
            if key in self.cache:
                if not self._is_expired(key, self.default_ttl) and not self._check_file_dependencies(key):
                    return self.cache[key]
                else:
                    # Expired or dependencies changed
                    self.invalidate(key)
            return None
    
    def set(self, key: str, value: Any, ttl: int = None, file_deps: List[Path] = None):
        """Set cached value with optional file dependencies"""
        with self._lock:
            self.cache[key] = value
            self.timestamps[key] = time.time()
            
            if file_deps:
                self.dependencies[key] = {}
                for file_path in file_deps:
                    try:
                        self.dependencies[key][str(file_path)] = file_path.stat().st_mtime
                    except (OSError, FileNotFoundError):
                        pass
    
    def invalidate(self, key: str):
        """Remove cached entry"""
        with self._lock:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
            self.dependencies.pop(key, None)
    
    def clear(self):
        """Clear all cache"""
        with self._lock:
            self.cache.clear()
            self.timestamps.clear()
            self.dependencies.clear()

class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self):
        self.cache = IntelligentCache()
        self.db_pools = {}
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ArtRemote")
        
    def get_db_pool(self, db_path: Path) -> DatabaseConnectionPool:
        """Get or create database connection pool"""
        str_path = str(db_path)
        if str_path not in self.db_pools:
            self.db_pools[str_path] = DatabaseConnectionPool(db_path)
        return self.db_pools[str_path]
    
    async def run_in_executor(self, func: Callable, *args, **kwargs):
        """Run CPU-intensive operation in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args, **kwargs)
    
    def close(self):
        """Clean up resources"""
        for pool in self.db_pools.values():
            pool.close_all()
        self.executor.shutdown(wait=True)

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()

def cached_db_operation(ttl: int = 300, file_deps: List[str] = None):
    """Decorator for caching database operations with file dependency tracking"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = performance_optimizer.cache._get_cache_key(
                f"{func.__module__}.{func.__name__}", args, kwargs
            )
            
            # Try to get from cache
            cached_result = performance_optimizer.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT for {func.__name__}")
                return cached_result
            
            logger.debug(f"Cache MISS for {func.__name__} - executing...")
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result with file dependencies
            deps = [Path(dep) for dep in (file_deps or [])]
            performance_optimizer.cache.set(cache_key, result, ttl, deps)
            
            return result
        return wrapper
    return decorator

def async_cached_db_operation(ttl: int = 300, file_deps: List[str] = None):
    """Async version of cached_db_operation"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = performance_optimizer.cache._get_cache_key(
                f"{func.__module__}.{func.__name__}", args, kwargs
            )
            
            # Try to get from cache
            cached_result = performance_optimizer.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT for {func.__name__}")
                return cached_result
            
            logger.debug(f"Cache MISS for {func.__name__} - executing async...")
            
            # Execute function in thread pool for CPU-intensive work
            result = await performance_optimizer.run_in_executor(
                lambda: func(*args, **kwargs)
            )
            
            # Cache result
            deps = [Path(dep) for dep in (file_deps or [])]
            performance_optimizer.cache.set(cache_key, result, ttl, deps)
            
            return result
        return wrapper
    return decorator

class DatabaseQueryOptimizer:
    """Optimized database query execution with connection pooling"""
    
    @staticmethod
    def execute_query(db_path: Path, query: str, params: tuple = (), fetch_all: bool = True):
        """Execute optimized database query with connection pooling"""
        pool = performance_optimizer.get_db_pool(db_path)
        
        with pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch_all:
                return cursor.fetchall()
            else:
                return cursor.fetchone()
    
    @staticmethod
    def execute_batch_queries(db_path: Path, queries: List[tuple]):
        """Execute multiple queries in a single connection for better performance"""
        pool = performance_optimizer.get_db_pool(db_path)
        results = []
        
        with pool.get_connection() as conn:
            cursor = conn.cursor()
            for query, params in queries:
                cursor.execute(query, params or ())
                results.append(cursor.fetchall())
                
        return results

def performance_monitor(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 0.1:  # Log slow operations (>100ms)
            logger.warning(f"SLOW OPERATION: {func.__name__} took {execution_time:.3f}s")
        else:
            logger.debug(f"Performance: {func.__name__} took {execution_time:.3f}s")
            
        return result
    return wrapper
