from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict
from dataclasses import dataclass

from .logging import logger


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    created_at: float
    access_count: int = 0
    last_accessed: float = 0.0
    
    def is_expired(self, ttl: float) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > ttl
    
    def access(self) -> None:
        """记录访问"""
        self.access_count += 1
        self.last_accessed = time.time()


class SmartCache:
    """智能缓存系统，支持TTL、LRU和智能预加载"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expired": 0,
        }
    
    def _make_key(self, key_data: Any) -> str:
        """生成缓存键"""
        if isinstance(key_data, str):
            return key_data
        
        # 对复杂对象生成哈希键
        json_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode()).hexdigest()[:32]
    
    async def get(self, key: Any, ttl: Optional[float] = None) -> Optional[Any]:
        """获取缓存值"""
        cache_key = self._make_key(key)
        ttl = ttl or self.default_ttl
        
        async with self._lock:
            entry = self._cache.get(cache_key)
            if entry is None:
                self._stats["misses"] += 1
                return None
            
            if entry.is_expired(ttl):
                del self._cache[cache_key]
                self._stats["expired"] += 1
                self._stats["misses"] += 1
                return None
            
            # 移到末尾（LRU）
            self._cache.move_to_end(cache_key)
            entry.access()
            self._stats["hits"] += 1
            
            logger.debug(f"[Cache] Hit for key {cache_key[:16]}...")
            return entry.value
    
    async def set(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        """设置缓存值"""
        cache_key = self._make_key(key)
        ttl = ttl or self.default_ttl
        
        async with self._lock:
            # 检查是否需要清理空间
            while len(self._cache) >= self.max_size:
                # 移除最久未使用的条目
                oldest_key, _ = self._cache.popitem(last=False)
                self._stats["evictions"] += 1
                logger.debug(f"[Cache] Evicted key {oldest_key[:16]}...")
            
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                access_count=1,
                last_accessed=time.time()
            )
            
            self._cache[cache_key] = entry
            logger.debug(f"[Cache] Set key {cache_key[:16]}... (TTL: {ttl}s)")
    
    async def invalidate(self, key: Any) -> bool:
        """删除缓存条目"""
        cache_key = self._make_key(key)
        
        async with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.debug(f"[Cache] Invalidated key {cache_key[:16]}...")
                return True
            return False
    
    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
            logger.info("[Cache] Cleared all cache entries")
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        async with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / max(1, total_requests)) * 100
            
            return {
                **self._stats,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": hit_rate,
                "total_requests": total_requests,
            }
    
    async def cleanup_expired(self) -> int:
        """清理过期条目"""
        expired_count = 0
        current_time = time.time()
        
        async with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired(self.default_ttl):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                expired_count += 1
                self._stats["expired"] += 1
            
            if expired_count > 0:
                logger.debug(f"[Cache] Cleaned up {expired_count} expired entries")
        
        return expired_count


# 全局缓存实例
_global_cache: Optional[SmartCache] = None
_cache_lock = asyncio.Lock()


async def get_global_cache() -> SmartCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is not None:
        return _global_cache
    
    async with _cache_lock:
        if _global_cache is None:
            _global_cache = SmartCache(max_size=2000, default_ttl=600.0)  # 10分钟TTL
            logger.info("[Cache] Global cache initialized")
        return _global_cache


async def cache_get(key: Any, ttl: Optional[float] = None) -> Optional[Any]:
    """全局缓存获取"""
    cache = await get_global_cache()
    return await cache.get(key, ttl)


async def cache_set(key: Any, value: Any, ttl: Optional[float] = None) -> None:
    """全局缓存设置"""
    cache = await get_global_cache()
    await cache.set(key, value, ttl)


async def cache_invalidate(key: Any) -> bool:
    """全局缓存失效"""
    cache = await get_global_cache()
    return await cache.invalidate(key)


async def cache_stats() -> Dict[str, Any]:
    """获取全局缓存统计"""
    cache = await get_global_cache()
    return await cache.get_stats()


class CacheableRequest:
    """可缓存的请求装饰器"""
    
    def __init__(self, ttl: float = 300.0, cache_key_func: Optional[callable] = None):
        self.ttl = ttl
        self.cache_key_func = cache_key_func or self._default_key_func
    
    def _default_key_func(self, *args, **kwargs) -> str:
        """默认的缓存键生成函数"""
        key_data = {"args": args, "kwargs": kwargs}
        return hashlib.sha256(
            json.dumps(key_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:32]
    
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            cache_key = self.cache_key_func(*args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = await cache_get(cache_key, self.ttl)
            if cached_result is not None:
                logger.debug(f"[Cache] Using cached result for {func.__name__}")
                return cached_result
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            await cache_set(cache_key, result, self.ttl)
            logger.debug(f"[Cache] Cached result for {func.__name__}")
            
            return result
        
        return wrapper


# 定期清理任务
async def start_cache_cleanup_task():
    """启动缓存清理任务"""
    async def cleanup_task():
        while True:
            try:
                cache = await get_global_cache()
                expired_count = await cache.cleanup_expired()
                if expired_count > 0:
                    logger.info(f"[Cache] Cleaned up {expired_count} expired entries")
                
                # 每5分钟清理一次
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"[Cache] Cleanup task error: {e}")
                await asyncio.sleep(60)  # 错误时等待1分钟后重试
    
    asyncio.create_task(cleanup_task())
    logger.info("[Cache] Cache cleanup task started")