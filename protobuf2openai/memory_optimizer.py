from __future__ import annotations

import gc
import sys
import weakref
import asyncio
import time
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict
import psutil

from .logging import logger


class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self):
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5分钟
        self.memory_threshold = 80.0  # 内存使用率阈值（百分比）
        self.weak_refs: Set[weakref.ref] = set()
        self.object_counts: Dict[str, int] = defaultdict(int)
        self.large_objects: List[weakref.ref] = []
        
        # 进程监控
        self.process = psutil.Process()
        
    def track_object(self, obj: Any, obj_type: str = None):
        """跟踪对象以便后续清理"""
        if obj_type is None:
            obj_type = type(obj).__name__
        
        self.object_counts[obj_type] += 1
        
        # 对于大对象，使用弱引用跟踪
        if hasattr(obj, '__sizeof__') and obj.__sizeof__() > 1024 * 1024:  # 1MB
            weak_ref = weakref.ref(obj, self._object_deleted)
            self.weak_refs.add(weak_ref)
            self.large_objects.append(weak_ref)
    
    def _object_deleted(self, weak_ref):
        """对象被删除时的回调"""
        self.weak_refs.discard(weak_ref)
        if weak_ref in self.large_objects:
            self.large_objects.remove(weak_ref)
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        try:
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # 获取系统内存信息
            system_memory = psutil.virtual_memory()
            
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": memory_percent,
                "available_mb": system_memory.available / 1024 / 1024,
                "system_percent": system_memory.percent,
            }
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return {}
    
    def should_cleanup(self) -> bool:
        """判断是否需要清理内存"""
        current_time = time.time()
        
        # 时间间隔检查
        if current_time - self.last_cleanup < self.cleanup_interval:
            return False
        
        # 内存使用率检查
        memory_usage = self.get_memory_usage()
        if memory_usage.get("percent", 0) > self.memory_threshold:
            return True
        
        # 系统内存检查
        if memory_usage.get("system_percent", 0) > 85:
            return True
        
        return False
    
    def cleanup_memory(self) -> Dict[str, int]:
        """执行内存清理"""
        cleanup_start = time.time()
        
        # 清理弱引用
        dead_refs = [ref for ref in self.weak_refs if ref() is None]
        for ref in dead_refs:
            self.weak_refs.discard(ref)
        
        # 强制垃圾回收
        collected = [gc.collect() for _ in range(3)]  # 运行3次GC
        total_collected = sum(collected)
        
        # 清理大对象列表
        self.large_objects = [ref for ref in self.large_objects if ref() is not None]
        
        # 更新最后清理时间
        self.last_cleanup = time.time()
        
        cleanup_duration = self.last_cleanup - cleanup_start
        
        result = {
            "collected_objects": total_collected,
            "dead_refs_removed": len(dead_refs),
            "cleanup_duration": cleanup_duration,
            "large_objects_tracked": len(self.large_objects),
        }
        
        logger.info(f"[Memory] Cleanup completed: {result}")
        return result
    
    def get_object_stats(self) -> Dict[str, Any]:
        """获取对象统计信息"""
        # 获取当前对象计数
        current_objects = {}
        for obj_type in gc.get_objects():
            type_name = type(obj_type).__name__
            current_objects[type_name] = current_objects.get(type_name, 0) + 1
        
        return {
            "tracked_objects": dict(self.object_counts),
            "current_objects": current_objects,
            "weak_refs_count": len(self.weak_refs),
            "large_objects_count": len(self.large_objects),
            "gc_stats": gc.get_stats(),
        }
    
    def optimize_gc_settings(self):
        """优化垃圾回收设置"""
        # 调整GC阈值以减少频繁的小规模GC
        gc.set_threshold(700, 10, 10)  # 默认是 (700, 10, 10)
        
        # 启用GC调试（仅在开发环境）
        if __debug__:
            gc.set_debug(gc.DEBUG_STATS)
        
        logger.info("[Memory] GC settings optimized")


class MemoryPool:
    """内存池，用于重用对象"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.pools: Dict[str, List[Any]] = defaultdict(list)
        self.pool_sizes: Dict[str, int] = defaultdict(int)
    
    def get_object(self, obj_type: str, factory_func: callable = None):
        """从池中获取对象"""
        pool = self.pools[obj_type]
        if pool:
            obj = pool.pop()
            self.pool_sizes[obj_type] -= 1
            return obj
        
        # 池中没有对象，创建新的
        if factory_func:
            return factory_func()
        
        return None
    
    def return_object(self, obj: Any, obj_type: str = None):
        """将对象返回到池中"""
        if obj_type is None:
            obj_type = type(obj).__name__
        
        pool = self.pools[obj_type]
        if len(pool) < self.max_size:
            # 清理对象状态（如果有reset方法）
            if hasattr(obj, 'reset'):
                obj.reset()
            elif hasattr(obj, 'clear'):
                obj.clear()
            
            pool.append(obj)
            self.pool_sizes[obj_type] += 1
    
    def get_stats(self) -> Dict[str, int]:
        """获取池统计信息"""
        return dict(self.pool_sizes)
    
    def clear_pool(self, obj_type: str = None):
        """清空指定类型的池，或清空所有池"""
        if obj_type:
            self.pools[obj_type].clear()
            self.pool_sizes[obj_type] = 0
        else:
            self.pools.clear()
            self.pool_sizes.clear()


# 全局实例
_memory_optimizer: Optional[MemoryOptimizer] = None
_memory_pool: Optional[MemoryPool] = None
_optimizer_lock = asyncio.Lock()


async def get_memory_optimizer() -> MemoryOptimizer:
    """获取全局内存优化器"""
    global _memory_optimizer
    if _memory_optimizer is not None:
        return _memory_optimizer
    
    async with _optimizer_lock:
        if _memory_optimizer is None:
            _memory_optimizer = MemoryOptimizer()
            _memory_optimizer.optimize_gc_settings()
            logger.info("[Memory] Memory optimizer initialized")
        return _memory_optimizer


async def get_memory_pool() -> MemoryPool:
    """获取全局内存池"""
    global _memory_pool
    if _memory_pool is not None:
        return _memory_pool
    
    async with _optimizer_lock:
        if _memory_pool is None:
            _memory_pool = MemoryPool()
            logger.info("[Memory] Memory pool initialized")
        return _memory_pool


async def check_and_cleanup_memory():
    """检查并清理内存"""
    optimizer = await get_memory_optimizer()
    
    if optimizer.should_cleanup():
        logger.info("[Memory] Starting memory cleanup...")
        result = optimizer.cleanup_memory()
        
        # 记录内存使用情况
        memory_usage = optimizer.get_memory_usage()
        logger.info(f"[Memory] Current usage: {memory_usage}")
        
        return result
    
    return None


async def track_object(obj: Any, obj_type: str = None):
    """跟踪对象"""
    optimizer = await get_memory_optimizer()
    optimizer.track_object(obj, obj_type)


async def get_memory_stats() -> Dict[str, Any]:
    """获取内存统计信息"""
    optimizer = await get_memory_optimizer()
    pool = await get_memory_pool()
    
    return {
        "memory_usage": optimizer.get_memory_usage(),
        "object_stats": optimizer.get_object_stats(),
        "pool_stats": pool.get_stats(),
    }


class MemoryEfficientDict(dict):
    """内存高效的字典实现"""
    
    __slots__ = ('_max_size', '_access_times')
    
    def __init__(self, max_size: int = 10000):
        super().__init__()
        self._max_size = max_size
        self._access_times: Dict[Any, float] = {}
    
    def __setitem__(self, key, value):
        # 如果达到最大大小，移除最久未访问的项
        if len(self) >= self._max_size and key not in self:
            self._evict_lru()
        
        super().__setitem__(key, value)
        self._access_times[key] = time.time()
    
    def __getitem__(self, key):
        self._access_times[key] = time.time()
        return super().__getitem__(key)
    
    def _evict_lru(self):
        """移除最久未访问的项"""
        if not self._access_times:
            return
        
        # 找到最久未访问的键
        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        
        # 移除项
        del self[oldest_key]
        del self._access_times[oldest_key]


# 定期内存优化任务
async def start_memory_optimization_task(interval: int = 300):
    """启动内存优化任务"""
    async def optimization_task():
        while True:
            try:
                result = await check_and_cleanup_memory()
                if result:
                    logger.info(f"[Memory] Optimization completed: {result}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"[Memory] Optimization task error: {e}")
                await asyncio.sleep(60)  # 错误时等待1分钟后重试
    
    asyncio.create_task(optimization_task())
    logger.info(f"[Memory] Memory optimization task started (interval: {interval}s)")


# 内存使用装饰器
def memory_efficient(max_cache_size: int = 1000):
    """内存高效装饰器，限制缓存大小"""
    def decorator(func):
        cache = MemoryEfficientDict(max_cache_size)
        
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = (args, tuple(sorted(kwargs.items())))
            
            if cache_key in cache:
                return cache[cache_key]
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            cache[cache_key] = result
            
            return result
        
        wrapper.cache = cache
        return wrapper
    
    return decorator