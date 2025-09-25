from __future__ import annotations

import json
import time
import asyncio
from typing import Any, Dict, Optional, Union, Callable, List
from collections import defaultdict
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading

try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False

try:
    import ujson
    HAS_UJSON = True
except ImportError:
    HAS_UJSON = False

from .logging import logger
from .cache import cache_get, cache_set


@dataclass
class SerializationStats:
    """序列化统计"""
    total_serializations: int = 0
    total_deserializations: int = 0
    total_time_serialization: float = 0.0
    total_time_deserialization: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    orjson_usage: int = 0
    ujson_usage: int = 0
    stdlib_usage: int = 0


class JSONSerializer:
    """高性能JSON序列化器"""
    
    def __init__(self, use_cache: bool = True, cache_ttl: float = 300.0):
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.stats = SerializationStats()
        
        # 选择最优的JSON库
        self.serializer_name, self.serialize_func, self.deserialize_func = self._select_best_json_lib()
        
        # 线程池用于大对象的序列化
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="json-")
        
        logger.info(f"[JSONOptimizer] Using {self.serializer_name} for JSON operations")
    
    def _select_best_json_lib(self) -> tuple[str, Callable, Callable]:
        """选择最佳的JSON库"""
        if HAS_ORJSON:
            return ("orjson", self._orjson_dumps, self._orjson_loads)
        elif HAS_UJSON:
            return ("ujson", self._ujson_dumps, self._ujson_loads)
        else:
            return ("stdlib", self._stdlib_dumps, self._stdlib_loads)
    
    def _orjson_dumps(self, obj: Any) -> str:
        """使用orjson序列化"""
        self.stats.orjson_usage += 1
        return orjson.dumps(obj, default=self._default_serializer).decode('utf-8')
    
    def _orjson_loads(self, s: str) -> Any:
        """使用orjson反序列化"""
        return orjson.loads(s)
    
    def _ujson_dumps(self, obj: Any) -> str:
        """使用ujson序列化"""
        self.stats.ujson_usage += 1
        return ujson.dumps(obj, default=self._default_serializer, ensure_ascii=False)
    
    def _ujson_loads(self, s: str) -> Any:
        """使用ujson反序列化"""
        return ujson.loads(s)
    
    def _stdlib_dumps(self, obj: Any) -> str:
        """使用标准库序列化"""
        self.stats.stdlib_usage += 1
        return json.dumps(obj, default=self._default_serializer, ensure_ascii=False, separators=(',', ':'))
    
    def _stdlib_loads(self, s: str) -> Any:
        """使用标准库反序列化"""
        return json.loads(s)
    
    def _default_serializer(self, obj: Any) -> Any:
        """默认序列化器，处理特殊类型"""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, 'hex'):  # bytes objects
            return obj.hex()
        else:
            return str(obj)
    
    def _generate_cache_key(self, obj: Any) -> str:
        """生成缓存键"""
        import hashlib
        # 对于简单对象，使用其字符串表示的哈希
        if isinstance(obj, (str, int, float, bool)):
            key_str = f"{type(obj).__name__}:{obj}"
        elif isinstance(obj, (list, tuple)):
            key_str = f"{type(obj).__name__}:{len(obj)}:{hash(str(obj)[:100])}"
        elif isinstance(obj, dict):
            key_str = f"dict:{len(obj)}:{hash(str(sorted(obj.keys())[:10]))}"
        else:
            key_str = f"{type(obj).__name__}:{hash(str(obj)[:100])}"
        
        return hashlib.md5(key_str.encode()).hexdigest()[:16]
    
    def dumps(self, obj: Any, use_cache: Optional[bool] = None) -> str:
        """序列化对象为JSON字符串"""
        start_time = time.time()
        use_cache = use_cache if use_cache is not None else self.use_cache
        
        try:
            # 检查缓存
            cache_key = None
            if use_cache:
                cache_key = f"json_serialize_{self._generate_cache_key(obj)}"
                cached_result = asyncio.run(cache_get(cache_key, self.cache_ttl))
                if cached_result is not None:
                    self.stats.cache_hits += 1
                    return cached_result
                self.stats.cache_misses += 1
            
            # 序列化
            result = self.serialize_func(obj)
            
            # 缓存结果
            if use_cache and cache_key:
                asyncio.create_task(cache_set(cache_key, result, self.cache_ttl))
            
            # 更新统计
            self.stats.total_serializations += 1
            self.stats.total_time_serialization += time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"[JSONOptimizer] Serialization failed: {e}")
            # 回退到标准库
            if self.serializer_name != "stdlib":
                return json.dumps(obj, default=self._default_serializer, ensure_ascii=False)
            raise
    
    def loads(self, s: str, use_cache: Optional[bool] = None) -> Any:
        """从JSON字符串反序列化对象"""
        start_time = time.time()
        use_cache = use_cache if use_cache is not None else self.use_cache
        
        try:
            # 检查缓存
            cache_key = None
            if use_cache:
                import hashlib
                cache_key = f"json_deserialize_{hashlib.md5(s.encode()).hexdigest()[:16]}"
                cached_result = asyncio.run(cache_get(cache_key, self.cache_ttl))
                if cached_result is not None:
                    self.stats.cache_hits += 1
                    return cached_result
                self.stats.cache_misses += 1
            
            # 反序列化
            result = self.deserialize_func(s)
            
            # 缓存结果
            if use_cache and cache_key:
                asyncio.create_task(cache_set(cache_key, result, self.cache_ttl))
            
            # 更新统计
            self.stats.total_deserializations += 1
            self.stats.total_time_deserialization += time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"[JSONOptimizer] Deserialization failed: {e}")
            # 回退到标准库
            if self.serializer_name != "stdlib":
                return json.loads(s)
            raise
    
    async def dumps_async(self, obj: Any, use_cache: Optional[bool] = None) -> str:
        """异步序列化（适用于大对象）"""
        # 估算对象大小
        estimated_size = self._estimate_object_size(obj)
        
        if estimated_size > 1024 * 1024:  # 1MB以上使用线程池
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, self.dumps, obj, use_cache)
        else:
            return self.dumps(obj, use_cache)
    
    async def loads_async(self, s: str, use_cache: Optional[bool] = None) -> Any:
        """异步反序列化（适用于大字符串）"""
        if len(s) > 1024 * 1024:  # 1MB以上使用线程池
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, self.loads, s, use_cache)
        else:
            return self.loads(s, use_cache)
    
    def _estimate_object_size(self, obj: Any) -> int:
        """估算对象大小"""
        if isinstance(obj, str):
            return len(obj.encode('utf-8'))
        elif isinstance(obj, (list, tuple)):
            return len(obj) * 100  # 粗略估计
        elif isinstance(obj, dict):
            return len(obj) * 200  # 粗略估计
        else:
            return 1000  # 默认估计
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_operations = self.stats.total_serializations + self.stats.total_deserializations
        
        stats = {
            "serializer": self.serializer_name,
            "total_serializations": self.stats.total_serializations,
            "total_deserializations": self.stats.total_deserializations,
            "total_operations": total_operations,
            "avg_serialization_time": (
                self.stats.total_time_serialization / max(1, self.stats.total_serializations)
            ),
            "avg_deserialization_time": (
                self.stats.total_time_deserialization / max(1, self.stats.total_deserializations)
            ),
            "cache_hit_rate": (
                self.stats.cache_hits / max(1, self.stats.cache_hits + self.stats.cache_misses)
            ),
            "library_usage": {
                "orjson": self.stats.orjson_usage,
                "ujson": self.stats.ujson_usage,
                "stdlib": self.stats.stdlib_usage
            }
        }
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = SerializationStats()
    
    def shutdown(self):
        """关闭序列化器"""
        self.executor.shutdown(wait=True)


class JSONStreamProcessor:
    """JSON流处理器"""
    
    def __init__(self, serializer: JSONSerializer):
        self.serializer = serializer
        self.buffer_size = 8192
    
    async def stream_serialize(self, objects: List[Any]) -> AsyncGenerator[str, None]:
        """流式序列化多个对象"""
        for obj in objects:
            try:
                json_str = await self.serializer.dumps_async(obj)
                yield json_str + '\n'
            except Exception as e:
                logger.error(f"[JSONOptimizer] Stream serialization error: {e}")
                # 跳过有问题的对象
                continue
    
    async def stream_deserialize(self, json_stream: AsyncGenerator[str, None]) -> AsyncGenerator[Any, None]:
        """流式反序列化JSON字符串流"""
        buffer = ""
        
        async for chunk in json_stream:
            buffer += chunk
            
            # 按行分割处理
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                
                if line:
                    try:
                        obj = await self.serializer.loads_async(line)
                        yield obj
                    except Exception as e:
                        logger.error(f"[JSONOptimizer] Stream deserialization error: {e}")
                        # 跳过有问题的行
                        continue
        
        # 处理剩余缓冲区
        if buffer.strip():
            try:
                obj = await self.serializer.loads_async(buffer.strip())
                yield obj
            except Exception as e:
                logger.error(f"[JSONOptimizer] Final buffer deserialization error: {e}")


class JSONBatchProcessor:
    """JSON批处理器"""
    
    def __init__(self, serializer: JSONSerializer, batch_size: int = 100):
        self.serializer = serializer
        self.batch_size = batch_size
    
    async def batch_serialize(self, objects: List[Any]) -> List[str]:
        """批量序列化"""
        results = []
        
        # 分批处理
        for i in range(0, len(objects), self.batch_size):
            batch = objects[i:i + self.batch_size]
            
            # 并行序列化批次
            tasks = [self.serializer.dumps_async(obj) for obj in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"[JSONOptimizer] Batch serialization error for object {i+j}: {result}")
                    results.append(None)
                else:
                    results.append(result)
        
        return results
    
    async def batch_deserialize(self, json_strings: List[str]) -> List[Any]:
        """批量反序列化"""
        results = []
        
        # 分批处理
        for i in range(0, len(json_strings), self.batch_size):
            batch = json_strings[i:i + self.batch_size]
            
            # 并行反序列化批次
            tasks = [self.serializer.loads_async(s) for s in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"[JSONOptimizer] Batch deserialization error for string {i+j}: {result}")
                    results.append(None)
                else:
                    results.append(result)
        
        return results


# 全局序列化器实例
_global_serializer: Optional[JSONSerializer] = None
_serializer_lock = threading.Lock()


def get_json_serializer() -> JSONSerializer:
    """获取全局JSON序列化器"""
    global _global_serializer
    
    if _global_serializer is not None:
        return _global_serializer
    
    with _serializer_lock:
        if _global_serializer is None:
            _global_serializer = JSONSerializer()
            logger.info("[JSONOptimizer] Global JSON serializer initialized")
    
    return _global_serializer


def dumps(obj: Any, use_cache: bool = True) -> str:
    """快速JSON序列化"""
    serializer = get_json_serializer()
    return serializer.dumps(obj, use_cache)


def loads(s: str, use_cache: bool = True) -> Any:
    """快速JSON反序列化"""
    serializer = get_json_serializer()
    return serializer.loads(s, use_cache)


async def dumps_async(obj: Any, use_cache: bool = True) -> str:
    """异步JSON序列化"""
    serializer = get_json_serializer()
    return await serializer.dumps_async(obj, use_cache)


async def loads_async(s: str, use_cache: bool = True) -> Any:
    """异步JSON反序列化"""
    serializer = get_json_serializer()
    return await serializer.loads_async(s, use_cache)


def get_json_stats() -> Dict[str, Any]:
    """获取JSON处理统计"""
    serializer = get_json_serializer()
    return serializer.get_stats()


def reset_json_stats():
    """重置JSON处理统计"""
    serializer = get_json_serializer()
    serializer.reset_stats()


# 性能基准测试
class JSONBenchmark:
    """JSON性能基准测试"""
    
    @staticmethod
    def create_test_data(size: str = "medium") -> Dict[str, Any]:
        """创建测试数据"""
        if size == "small":
            return {
                "id": 123,
                "name": "test",
                "active": True,
                "data": [1, 2, 3, 4, 5]
            }
        elif size == "medium":
            return {
                "users": [
                    {
                        "id": i,
                        "name": f"user_{i}",
                        "email": f"user_{i}@example.com",
                        "active": i % 2 == 0,
                        "metadata": {
                            "created_at": f"2024-01-{i:02d}T00:00:00Z",
                            "tags": [f"tag_{j}" for j in range(5)]
                        }
                    }
                    for i in range(100)
                ]
            }
        else:  # large
            return {
                "data": [
                    {
                        "id": i,
                        "values": list(range(100)),
                        "nested": {
                            "level1": {
                                "level2": {
                                    "level3": f"deep_value_{i}"
                                }
                            }
                        }
                    }
                    for i in range(1000)
                ]
            }
    
    @staticmethod
    async def run_benchmark(iterations: int = 1000, size: str = "medium") -> Dict[str, Any]:
        """运行基准测试"""
        test_data = JSONBenchmark.create_test_data(size)
        serializer = get_json_serializer()
        
        # 序列化基准
        start_time = time.time()
        for _ in range(iterations):
            json_str = serializer.dumps(test_data, use_cache=False)
        serialize_time = time.time() - start_time
        
        # 反序列化基准
        json_str = serializer.dumps(test_data, use_cache=False)
        start_time = time.time()
        for _ in range(iterations):
            obj = serializer.loads(json_str, use_cache=False)
        deserialize_time = time.time() - start_time
        
        return {
            "iterations": iterations,
            "data_size": size,
            "serialization": {
                "total_time": serialize_time,
                "avg_time": serialize_time / iterations,
                "ops_per_second": iterations / serialize_time
            },
            "deserialization": {
                "total_time": deserialize_time,
                "avg_time": deserialize_time / iterations,
                "ops_per_second": iterations / deserialize_time
            },
            "json_size": len(json_str),
            "serializer": serializer.serializer_name
        }


def shutdown_json_optimizer():
    """关闭JSON优化器"""
    global _global_serializer
    
    if _global_serializer:
        _global_serializer.shutdown()
        _global_serializer = None
        logger.info("[JSONOptimizer] JSON optimizer shutdown")