from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from collections import defaultdict, deque
from enum import Enum

from .logging import logger


class BatchStrategy(Enum):
    """批处理策略"""
    SIZE_BASED = "size_based"  # 基于批次大小
    TIME_BASED = "time_based"  # 基于时间窗口
    ADAPTIVE = "adaptive"      # 自适应策略


@dataclass
class BatchRequest:
    """批处理请求"""
    id: str
    data: Any
    future: asyncio.Future
    timestamp: float
    priority: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not hasattr(self, 'timestamp') or self.timestamp == 0:
            self.timestamp = time.time()


@dataclass
class BatchConfig:
    """批处理配置"""
    max_batch_size: int = 10
    max_wait_time: float = 0.1  # 100ms
    strategy: BatchStrategy = BatchStrategy.ADAPTIVE
    priority_enabled: bool = True
    timeout: float = 30.0


class RequestBatcher:
    """请求批处理器"""
    
    def __init__(self, 
                 batch_processor: Callable[[List[BatchRequest]], Awaitable[List[Any]]],
                 config: BatchConfig = None):
        self.batch_processor = batch_processor
        self.config = config or BatchConfig()
        
        self.pending_requests: deque[BatchRequest] = deque()
        self.processing = False
        self.stats = {
            "total_requests": 0,
            "total_batches": 0,
            "avg_batch_size": 0.0,
            "avg_wait_time": 0.0,
            "timeouts": 0,
            "errors": 0,
        }
        
        # 自适应参数
        self.recent_batch_sizes: deque[int] = deque(maxlen=100)
        self.recent_wait_times: deque[float] = deque(maxlen=100)
        self.performance_history: deque[float] = deque(maxlen=50)
    
    async def add_request(self, data: Any, priority: int = 0) -> Any:
        """添加请求到批处理队列"""
        future = asyncio.Future()
        request = BatchRequest(
            id=str(uuid.uuid4()),
            data=data,
            future=future,
            timestamp=time.time(),
            priority=priority
        )
        
        self.pending_requests.append(request)
        self.stats["total_requests"] += 1
        
        # 触发批处理
        if not self.processing:
            asyncio.create_task(self._process_batches())
        
        # 等待结果
        try:
            return await asyncio.wait_for(future, timeout=self.config.timeout)
        except asyncio.TimeoutError:
            self.stats["timeouts"] += 1
            # 从队列中移除超时的请求
            self.pending_requests = deque(
                req for req in self.pending_requests if req.id != request.id
            )
            raise
    
    async def _process_batches(self):
        """处理批次"""
        if self.processing:
            return
        
        self.processing = True
        
        try:
            while self.pending_requests:
                # 确定批次大小和等待时间
                batch_size, wait_time = self._determine_batch_params()
                
                # 等待收集更多请求
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                
                # 收集批次
                batch = self._collect_batch(batch_size)
                if not batch:
                    break
                
                # 处理批次
                await self._process_single_batch(batch)
                
        finally:
            self.processing = False
    
    def _determine_batch_params(self) -> tuple[int, float]:
        """确定批次参数"""
        if self.config.strategy == BatchStrategy.SIZE_BASED:
            return self.config.max_batch_size, 0.0
        
        elif self.config.strategy == BatchStrategy.TIME_BASED:
            return len(self.pending_requests), self.config.max_wait_time
        
        elif self.config.strategy == BatchStrategy.ADAPTIVE:
            return self._adaptive_batch_params()
        
        else:
            return self.config.max_batch_size, self.config.max_wait_time
    
    def _adaptive_batch_params(self) -> tuple[int, float]:
        """自适应批次参数"""
        current_queue_size = len(self.pending_requests)
        
        # 基于队列大小调整
        if current_queue_size >= self.config.max_batch_size:
            return self.config.max_batch_size, 0.0
        
        # 基于历史性能调整
        if self.performance_history:
            avg_performance = sum(self.performance_history) / len(self.performance_history)
            
            # 如果性能良好，可以等待更多请求
            if avg_performance < 0.1:  # 100ms以下
                wait_time = min(self.config.max_wait_time * 2, 0.2)
                batch_size = min(current_queue_size * 2, self.config.max_batch_size)
            else:
                wait_time = self.config.max_wait_time / 2
                batch_size = max(current_queue_size // 2, 1)
        else:
            wait_time = self.config.max_wait_time
            batch_size = min(current_queue_size, self.config.max_batch_size)
        
        return batch_size, wait_time
    
    def _collect_batch(self, max_size: int) -> List[BatchRequest]:
        """收集批次请求"""
        batch = []
        current_time = time.time()
        
        # 按优先级排序（如果启用）
        if self.config.priority_enabled:
            sorted_requests = sorted(
                list(self.pending_requests),
                key=lambda r: (-r.priority, r.timestamp)
            )
        else:
            sorted_requests = list(self.pending_requests)
        
        # 收集请求
        collected_ids = set()
        for request in sorted_requests:
            if len(batch) >= max_size:
                break
            
            # 检查是否超时
            if current_time - request.timestamp > self.config.timeout:
                request.future.set_exception(asyncio.TimeoutError("Request timeout"))
                collected_ids.add(request.id)
                continue
            
            batch.append(request)
            collected_ids.add(request.id)
        
        # 从队列中移除已收集的请求
        self.pending_requests = deque(
            req for req in self.pending_requests if req.id not in collected_ids
        )
        
        return batch
    
    async def _process_single_batch(self, batch: List[BatchRequest]):
        """处理单个批次"""
        if not batch:
            return
        
        batch_start_time = time.time()
        
        try:
            # 记录批次统计
            self.stats["total_batches"] += 1
            batch_size = len(batch)
            self.recent_batch_sizes.append(batch_size)
            
            # 计算等待时间
            wait_times = [batch_start_time - req.timestamp for req in batch]
            avg_wait_time = sum(wait_times) / len(wait_times)
            self.recent_wait_times.append(avg_wait_time)
            
            logger.debug(f"[Batcher] Processing batch of {batch_size} requests")
            
            # 执行批处理
            results = await self.batch_processor(batch)
            
            # 分发结果
            if len(results) != len(batch):
                logger.warning(f"[Batcher] Result count mismatch: {len(results)} vs {len(batch)}")
                # 用None填充缺失的结果
                results.extend([None] * (len(batch) - len(results)))
            
            for request, result in zip(batch, results):
                if not request.future.done():
                    request.future.set_result(result)
            
            # 记录性能
            processing_time = time.time() - batch_start_time
            self.performance_history.append(processing_time)
            
            logger.debug(f"[Batcher] Batch processed in {processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"[Batcher] Batch processing failed: {e}")
            self.stats["errors"] += 1
            
            # 设置所有请求的异常
            for request in batch:
                if not request.future.done():
                    request.future.set_exception(e)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        
        # 计算平均值
        if self.recent_batch_sizes:
            stats["avg_batch_size"] = sum(self.recent_batch_sizes) / len(self.recent_batch_sizes)
        
        if self.recent_wait_times:
            stats["avg_wait_time"] = sum(self.recent_wait_times) / len(self.recent_wait_times)
        
        if self.performance_history:
            stats["avg_processing_time"] = sum(self.performance_history) / len(self.performance_history)
        
        stats["pending_requests"] = len(self.pending_requests)
        stats["is_processing"] = self.processing
        
        return stats
    
    def clear_stats(self):
        """清空统计信息"""
        self.stats = {
            "total_requests": 0,
            "total_batches": 0,
            "avg_batch_size": 0.0,
            "avg_wait_time": 0.0,
            "timeouts": 0,
            "errors": 0,
        }
        self.recent_batch_sizes.clear()
        self.recent_wait_times.clear()
        self.performance_history.clear()


class BatcherManager:
    """批处理器管理器"""
    
    def __init__(self):
        self.batchers: Dict[str, RequestBatcher] = {}
        self.lock = asyncio.Lock()
    
    async def get_batcher(self, 
                         name: str, 
                         batch_processor: Callable[[List[BatchRequest]], Awaitable[List[Any]]],
                         config: BatchConfig = None) -> RequestBatcher:
        """获取或创建批处理器"""
        if name in self.batchers:
            return self.batchers[name]
        
        async with self.lock:
            if name not in self.batchers:
                self.batchers[name] = RequestBatcher(batch_processor, config)
                logger.info(f"[Batcher] Created batcher '{name}'")
        
        return self.batchers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有批处理器的统计信息"""
        return {name: batcher.get_stats() for name, batcher in self.batchers.items()}
    
    def clear_all_stats(self):
        """清空所有统计信息"""
        for batcher in self.batchers.values():
            batcher.clear_stats()


# 全局批处理器管理器
_global_batcher_manager: Optional[BatcherManager] = None
_manager_lock = asyncio.Lock()


async def get_batcher_manager() -> BatcherManager:
    """获取全局批处理器管理器"""
    global _global_batcher_manager
    if _global_batcher_manager is not None:
        return _global_batcher_manager
    
    async with _manager_lock:
        if _global_batcher_manager is None:
            _global_batcher_manager = BatcherManager()
            logger.info("[Batcher] Global batcher manager initialized")
        return _global_batcher_manager


# 便捷函数
async def create_batcher(name: str,
                        batch_processor: Callable[[List[BatchRequest]], Awaitable[List[Any]]],
                        max_batch_size: int = 10,
                        max_wait_time: float = 0.1,
                        strategy: BatchStrategy = BatchStrategy.ADAPTIVE) -> RequestBatcher:
    """创建批处理器"""
    config = BatchConfig(
        max_batch_size=max_batch_size,
        max_wait_time=max_wait_time,
        strategy=strategy
    )
    
    manager = await get_batcher_manager()
    return await manager.get_batcher(name, batch_processor, config)


async def batch_request(batcher_name: str, data: Any, priority: int = 0) -> Any:
    """发送批处理请求"""
    manager = await get_batcher_manager()
    if batcher_name not in manager.batchers:
        raise ValueError(f"Batcher '{batcher_name}' not found")
    
    batcher = manager.batchers[batcher_name]
    return await batcher.add_request(data, priority)


async def get_batch_stats() -> Dict[str, Dict[str, Any]]:
    """获取所有批处理统计"""
    manager = await get_batcher_manager()
    return manager.get_all_stats()


# 装饰器
def batchable(batcher_name: str, 
              max_batch_size: int = 10,
              max_wait_time: float = 0.1,
              strategy: BatchStrategy = BatchStrategy.ADAPTIVE):
    """批处理装饰器"""
    def decorator(func):
        async def batch_processor(requests: List[BatchRequest]) -> List[Any]:
            """批处理函数"""
            data_list = [req.data for req in requests]
            results = await func(data_list)
            return results if isinstance(results, list) else [results] * len(requests)
        
        # 创建批处理器
        async def wrapper(*args, **kwargs):
            # 对于单个请求，直接调用原函数
            if len(args) == 1 and not kwargs:
                batcher = await create_batcher(
                    batcher_name, batch_processor, 
                    max_batch_size, max_wait_time, strategy
                )
                return await batcher.add_request(args[0])
            else:
                # 多参数调用，直接执行原函数
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator