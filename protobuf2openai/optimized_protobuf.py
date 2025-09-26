from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional
from functools import lru_cache

from .logging import logger
from .cache import cache_get, cache_set


# 线程池用于CPU密集型的protobuf操作
_protobuf_executor: Optional[ThreadPoolExecutor] = None
_executor_lock = asyncio.Lock()


async def get_protobuf_executor() -> ThreadPoolExecutor:
    """获取protobuf处理线程池"""
    global _protobuf_executor
    if _protobuf_executor is not None:
        return _protobuf_executor
    
    async with _executor_lock:
        if _protobuf_executor is None:
            # 使用CPU核心数的2倍作为线程数
            import os
            thread_count = (os.cpu_count() or 4) * 2
            _protobuf_executor = ThreadPoolExecutor(
                max_workers=thread_count,
                thread_name_prefix="protobuf-"
            )
            logger.info(f"[Protobuf] Created thread pool with {thread_count} workers")
        
        return _protobuf_executor


@lru_cache(maxsize=1000)
def _get_cached_message_class(message_type: str):
    """缓存的消息类获取"""
    from warp2protobuf.core.protobuf import msg_cls
    return msg_cls(message_type)


def _sync_protobuf_to_dict(protobuf_bytes: bytes, message_type: str) -> Dict[str, Any]:
    """同步的protobuf解码（在线程池中运行）"""
    from warp2protobuf.core.protobuf import ensure_proto_runtime
    from google.protobuf.json_format import MessageToDict
    
    ensure_proto_runtime()
    
    start_time = time.time()
    try:
        MessageClass = _get_cached_message_class(message_type)
        message = MessageClass()
        message.ParseFromString(protobuf_bytes)
        
        data = MessageToDict(message, preserving_proto_field_name=True)
        
        # 解析server_message_data
        from warp2protobuf.core.protobuf_utils import _decode_smd_inplace
        data = _decode_smd_inplace(data)
        
        decode_time = time.time() - start_time
        logger.debug(f"[Protobuf] Decoded {len(protobuf_bytes)} bytes in {decode_time:.3f}s")
        
        return data
    
    except Exception as e:
        decode_time = time.time() - start_time
        logger.error(f"[Protobuf] Decode failed after {decode_time:.3f}s: {e}")
        raise


def _sync_dict_to_protobuf(data_dict: Dict[str, Any], message_type: str) -> bytes:
    """同步的protobuf编码（在线程池中运行）"""
    from warp2protobuf.core.protobuf import ensure_proto_runtime
    from warp2protobuf.core.protobuf_utils import _encode_smd_inplace, _populate_protobuf_from_dict
    
    ensure_proto_runtime()
    
    start_time = time.time()
    try:
        MessageClass = _get_cached_message_class(message_type)
        message = MessageClass()
        
        # 处理server_message_data
        safe_dict = _encode_smd_inplace(data_dict)
        
        _populate_protobuf_from_dict(message, safe_dict, path="$")
        
        result = message.SerializeToString()
        
        encode_time = time.time() - start_time
        logger.debug(f"[Protobuf] Encoded to {len(result)} bytes in {encode_time:.3f}s")
        
        return result
    
    except Exception as e:
        encode_time = time.time() - start_time
        logger.error(f"[Protobuf] Encode failed after {encode_time:.3f}s: {e}")
        raise


async def protobuf_to_dict_async(protobuf_bytes: bytes, message_type: str, use_cache: bool = True) -> Dict[str, Any]:
    """异步protobuf解码，支持缓存和线程池"""
    
    # 生成缓存键
    cache_key = None
    if use_cache:
        import hashlib
        cache_key = f"decode_{hashlib.md5(protobuf_bytes).hexdigest()}_{message_type}"
        
        # 检查缓存
        cached_result = await cache_get(cache_key, ttl=300.0)
        if cached_result is not None:
            logger.debug("[Protobuf] Using cached decode result")
            return cached_result
    
    # 在线程池中执行CPU密集型操作
    executor = await get_protobuf_executor()
    loop = asyncio.get_event_loop()
    
    try:
        result = await loop.run_in_executor(
            executor, 
            _sync_protobuf_to_dict, 
            protobuf_bytes, 
            message_type
        )
        
        # 缓存结果
        if use_cache and cache_key:
            await cache_set(cache_key, result, ttl=300.0)
            logger.debug("[Protobuf] Cached decode result")
        
        return result
        
    except Exception as e:
        logger.error(f"[Protobuf] Async decode failed: {e}")
        raise


async def dict_to_protobuf_async(data_dict: Dict[str, Any], message_type: str = "warp.multi_agent.v1.Request", use_cache: bool = True) -> bytes:
    """异步protobuf编码，支持缓存和线程池"""
    
    # 生成缓存键
    cache_key = None
    if use_cache:
        import hashlib
        import json
        dict_str = json.dumps(data_dict, sort_keys=True, ensure_ascii=False)
        cache_key = f"encode_{hashlib.md5(dict_str.encode()).hexdigest()}_{message_type}"
        
        # 检查缓存
        cached_result = await cache_get(cache_key, ttl=300.0)
        if cached_result is not None:
            logger.debug("[Protobuf] Using cached encode result")
            return cached_result
    
    # 在线程池中执行CPU密集型操作
    executor = await get_protobuf_executor()
    loop = asyncio.get_event_loop()
    
    try:
        result = await loop.run_in_executor(
            executor,
            _sync_dict_to_protobuf,
            data_dict,
            message_type
        )
        
        # 缓存结果
        if use_cache and cache_key:
            await cache_set(cache_key, result, ttl=300.0)
            logger.debug("[Protobuf] Cached encode result")
        
        return result
        
    except Exception as e:
        logger.error(f"[Protobuf] Async encode failed: {e}")
        raise


class ProtobufBatch:
    """批量protobuf处理器"""
    
    def __init__(self, max_batch_size: int = 10, max_wait_time: float = 0.1):
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self._encode_queue = []
        self._decode_queue = []
        self._processing = False
    
    async def add_encode_request(self, data_dict: Dict[str, Any], message_type: str) -> bytes:
        """添加编码请求到批处理队列"""
        future = asyncio.Future()
        self._encode_queue.append((data_dict, message_type, future))
        
        if not self._processing:
            asyncio.create_task(self._process_batches())
        
        return await future
    
    async def add_decode_request(self, protobuf_bytes: bytes, message_type: str) -> Dict[str, Any]:
        """添加解码请求到批处理队列"""
        future = asyncio.Future()
        self._decode_queue.append((protobuf_bytes, message_type, future))
        
        if not self._processing:
            asyncio.create_task(self._process_batches())
        
        return await future
    
    async def _process_batches(self):
        """处理批量请求"""
        if self._processing:
            return
        
        self._processing = True
        
        try:
            # 等待一小段时间收集更多请求
            await asyncio.sleep(self.max_wait_time)
            
            # 处理编码批次
            if self._encode_queue:
                batch = self._encode_queue[:self.max_batch_size]
                self._encode_queue = self._encode_queue[self.max_batch_size:]
                
                await self._process_encode_batch(batch)
            
            # 处理解码批次
            if self._decode_queue:
                batch = self._decode_queue[:self.max_batch_size]
                self._decode_queue = self._decode_queue[self.max_batch_size:]
                
                await self._process_decode_batch(batch)
        
        finally:
            self._processing = False
            
            # 如果还有待处理的请求，继续处理
            if self._encode_queue or self._decode_queue:
                asyncio.create_task(self._process_batches())
    
    async def _process_encode_batch(self, batch):
        """处理编码批次"""
        executor = await get_protobuf_executor()
        loop = asyncio.get_event_loop()
        
        tasks = []
        for data_dict, message_type, future in batch:
            task = loop.run_in_executor(
                executor,
                _sync_dict_to_protobuf,
                data_dict,
                message_type
            )
            tasks.append((task, future))
        
        for task, future in tasks:
            try:
                result = await task
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
    
    async def _process_decode_batch(self, batch):
        """处理解码批次"""
        executor = await get_protobuf_executor()
        loop = asyncio.get_event_loop()
        
        tasks = []
        for protobuf_bytes, message_type, future in batch:
            task = loop.run_in_executor(
                executor,
                _sync_protobuf_to_dict,
                protobuf_bytes,
                message_type
            )
            tasks.append((task, future))
        
        for task, future in tasks:
            try:
                result = await task
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)


# 全局批处理器实例
_global_batch_processor: Optional[ProtobufBatch] = None


async def get_batch_processor() -> ProtobufBatch:
    """获取全局批处理器"""
    global _global_batch_processor
    if _global_batch_processor is None:
        _global_batch_processor = ProtobufBatch()
        logger.info("[Protobuf] Batch processor initialized")
    return _global_batch_processor


async def shutdown_protobuf_executor():
    """关闭protobuf线程池"""
    global _protobuf_executor
    if _protobuf_executor is not None:
        _protobuf_executor.shutdown(wait=True)
        _protobuf_executor = None
        logger.info("[Protobuf] Thread pool shutdown")