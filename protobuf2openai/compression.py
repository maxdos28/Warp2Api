from __future__ import annotations

import gzip
import zlib
import brotli
import asyncio
import time
from typing import Any, Dict, Optional, Union, Callable
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from .logging import logger


class CompressionMiddleware(BaseHTTPMiddleware):
    """响应压缩中间件"""
    
    def __init__(self, app, minimum_size: int = 1024, compression_level: int = 6):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        
        # 支持的压缩算法优先级
        self.compression_methods = {
            'br': self._compress_brotli,
            'gzip': self._compress_gzip,
            'deflate': self._compress_deflate,
        }
        
        # 不需要压缩的内容类型
        self.skip_content_types = {
            'image/', 'video/', 'audio/', 'application/zip', 
            'application/gzip', 'application/x-brotli'
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求和响应"""
        start_time = time.time()
        
        response = await call_next(request)
        
        # 检查是否需要压缩
        if not self._should_compress(request, response):
            return response
        
        # 选择压缩方法
        compression_method = self._select_compression_method(request)
        if not compression_method:
            return response
        
        # 执行压缩
        compressed_response = await self._compress_response(response, compression_method)
        
        # 记录压缩统计
        processing_time = time.time() - start_time
        logger.debug(f"[Compression] Response compressed using {compression_method} in {processing_time:.3f}s")
        
        return compressed_response
    
    def _should_compress(self, request: Request, response: Response) -> bool:
        """判断是否应该压缩响应"""
        # 检查状态码
        if response.status_code < 200 or response.status_code >= 300:
            return False
        
        # 检查内容类型
        content_type = response.headers.get('content-type', '')
        for skip_type in self.skip_content_types:
            if content_type.startswith(skip_type):
                return False
        
        # 检查是否已经压缩
        if 'content-encoding' in response.headers:
            return False
        
        # 检查内容长度
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) < self.minimum_size:
            return False
        
        return True
    
    def _select_compression_method(self, request: Request) -> Optional[str]:
        """选择压缩方法"""
        accept_encoding = request.headers.get('accept-encoding', '').lower()
        
        for method in self.compression_methods:
            if method in accept_encoding:
                return method
        
        return None
    
    async def _compress_response(self, response: Response, method: str) -> Response:
        """压缩响应"""
        compress_func = self.compression_methods[method]
        
        if isinstance(response, StreamingResponse):
            # 流式响应压缩
            return await self._compress_streaming_response(response, compress_func, method)
        else:
            # 普通响应压缩
            return await self._compress_regular_response(response, compress_func, method)
    
    async def _compress_regular_response(self, response: Response, compress_func: Callable, method: str) -> Response:
        """压缩普通响应"""
        try:
            # 获取响应内容
            if hasattr(response, 'body') and response.body:
                original_content = response.body
                if isinstance(original_content, str):
                    original_content = original_content.encode('utf-8')
            else:
                original_content = b''
            
            # 压缩内容
            compressed_content = compress_func(original_content)
            
            # 创建新响应
            compressed_response = Response(
                content=compressed_content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            # 更新头部
            compressed_response.headers['content-encoding'] = method
            compressed_response.headers['content-length'] = str(len(compressed_content))
            compressed_response.headers['vary'] = 'Accept-Encoding'
            
            # 记录压缩比率
            original_size = len(original_content)
            compressed_size = len(compressed_content)
            compression_ratio = (1 - compressed_size / max(original_size, 1)) * 100
            
            logger.debug(f"[Compression] {method.upper()}: {original_size} -> {compressed_size} bytes ({compression_ratio:.1f}% reduction)")
            
            return compressed_response
            
        except Exception as e:
            logger.warning(f"[Compression] Failed to compress response with {method}: {e}")
            return response
    
    async def _compress_streaming_response(self, response: StreamingResponse, compress_func: Callable, method: str) -> StreamingResponse:
        """压缩流式响应"""
        async def compressed_generator():
            compressor = None
            
            # 初始化压缩器
            if method == 'gzip':
                compressor = GzipStreamCompressor(self.compression_level)
            elif method == 'deflate':
                compressor = DeflateStreamCompressor(self.compression_level)
            elif method == 'br':
                compressor = BrotliStreamCompressor(self.compression_level)
            
            if not compressor:
                # 如果压缩器初始化失败，返回原始流
                async for chunk in response.body_iterator:
                    yield chunk
                return
            
            try:
                async for chunk in response.body_iterator:
                    if isinstance(chunk, str):
                        chunk = chunk.encode('utf-8')
                    
                    compressed_chunk = compressor.compress(chunk)
                    if compressed_chunk:
                        yield compressed_chunk
                
                # 完成压缩
                final_chunk = compressor.finalize()
                if final_chunk:
                    yield final_chunk
                    
            except Exception as e:
                logger.warning(f"[Compression] Streaming compression failed: {e}")
                # 如果压缩失败，尝试发送剩余的原始数据
                async for chunk in response.body_iterator:
                    yield chunk
        
        # 创建压缩的流式响应
        compressed_response = StreamingResponse(
            compressed_generator(),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
        
        # 更新头部
        compressed_response.headers['content-encoding'] = method
        compressed_response.headers['vary'] = 'Accept-Encoding'
        # 移除content-length，因为压缩后的长度未知
        compressed_response.headers.pop('content-length', None)
        
        return compressed_response
    
    def _compress_gzip(self, data: bytes) -> bytes:
        """Gzip压缩"""
        return gzip.compress(data, compresslevel=self.compression_level)
    
    def _compress_deflate(self, data: bytes) -> bytes:
        """Deflate压缩"""
        return zlib.compress(data, level=self.compression_level)
    
    def _compress_brotli(self, data: bytes) -> bytes:
        """Brotli压缩"""
        return brotli.compress(data, quality=self.compression_level)


class GzipStreamCompressor:
    """Gzip流式压缩器"""
    
    def __init__(self, level: int = 6):
        self.compressor = zlib.compressobj(
            level=level,
            method=zlib.DEFLATED,
            wbits=zlib.MAX_WBITS | 16  # 启用gzip头部
        )
        self.finished = False
    
    def compress(self, data: bytes) -> bytes:
        """压缩数据块"""
        if self.finished:
            return b''
        return self.compressor.compress(data)
    
    def finalize(self) -> bytes:
        """完成压缩"""
        if self.finished:
            return b''
        self.finished = True
        return self.compressor.flush()


class DeflateStreamCompressor:
    """Deflate流式压缩器"""
    
    def __init__(self, level: int = 6):
        self.compressor = zlib.compressobj(level=level)
        self.finished = False
    
    def compress(self, data: bytes) -> bytes:
        """压缩数据块"""
        if self.finished:
            return b''
        return self.compressor.compress(data)
    
    def finalize(self) -> bytes:
        """完成压缩"""
        if self.finished:
            return b''
        self.finished = True
        return self.compressor.flush()


class BrotliStreamCompressor:
    """Brotli流式压缩器"""
    
    def __init__(self, quality: int = 6):
        self.compressor = brotli.Compressor(quality=quality)
        self.finished = False
    
    def compress(self, data: bytes) -> bytes:
        """压缩数据块"""
        if self.finished:
            return b''
        return self.compressor.process(data)
    
    def finalize(self) -> bytes:
        """完成压缩"""
        if self.finished:
            return b''
        self.finished = True
        return self.compressor.finish()


# 压缩统计
class CompressionStats:
    """压缩统计"""
    
    def __init__(self):
        self.total_requests = 0
        self.compressed_requests = 0
        self.total_original_bytes = 0
        self.total_compressed_bytes = 0
        self.compression_times = []
        self.method_usage = {'gzip': 0, 'deflate': 0, 'br': 0}
    
    def record_compression(self, method: str, original_size: int, compressed_size: int, time_taken: float):
        """记录压缩统计"""
        self.total_requests += 1
        self.compressed_requests += 1
        self.total_original_bytes += original_size
        self.total_compressed_bytes += compressed_size
        self.compression_times.append(time_taken)
        self.method_usage[method] = self.method_usage.get(method, 0) + 1
        
        # 保持统计数据在合理范围内
        if len(self.compression_times) > 1000:
            self.compression_times = self.compression_times[-500:]
    
    def record_uncompressed(self):
        """记录未压缩请求"""
        self.total_requests += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if self.total_requests == 0:
            return {"compression_rate": 0, "total_requests": 0}
        
        compression_rate = self.compressed_requests / self.total_requests
        
        if self.total_original_bytes > 0:
            size_reduction = 1 - (self.total_compressed_bytes / self.total_original_bytes)
        else:
            size_reduction = 0
        
        avg_compression_time = 0
        if self.compression_times:
            avg_compression_time = sum(self.compression_times) / len(self.compression_times)
        
        return {
            "compression_rate": compression_rate,
            "size_reduction": size_reduction,
            "total_requests": self.total_requests,
            "compressed_requests": self.compressed_requests,
            "total_original_bytes": self.total_original_bytes,
            "total_compressed_bytes": self.total_compressed_bytes,
            "avg_compression_time": avg_compression_time,
            "method_usage": self.method_usage.copy()
        }


# 全局压缩统计实例
_compression_stats = CompressionStats()


def get_compression_stats() -> Dict[str, Any]:
    """获取压缩统计信息"""
    return _compression_stats.get_stats()


def reset_compression_stats():
    """重置压缩统计"""
    global _compression_stats
    _compression_stats = CompressionStats()


# 智能压缩配置
class AdaptiveCompressionConfig:
    """自适应压缩配置"""
    
    def __init__(self):
        self.min_size_for_compression = 1024  # 1KB
        self.max_compression_level = 9
        self.target_compression_time = 0.05  # 50ms
        self.performance_window = 100  # 性能窗口大小
        
        self.recent_performance = []
        self.current_level = 6  # 默认压缩级别
    
    def adjust_compression_level(self, compression_time: float, size_reduction: float):
        """根据性能调整压缩级别"""
        self.recent_performance.append({
            'time': compression_time,
            'reduction': size_reduction,
            'level': self.current_level
        })
        
        # 保持窗口大小
        if len(self.recent_performance) > self.performance_window:
            self.recent_performance = self.recent_performance[-self.performance_window:]
        
        # 如果样本不足，不调整
        if len(self.recent_performance) < 10:
            return
        
        # 计算平均性能
        avg_time = sum(p['time'] for p in self.recent_performance) / len(self.recent_performance)
        avg_reduction = sum(p['reduction'] for p in self.recent_performance) / len(self.recent_performance)
        
        # 调整策略
        if avg_time > self.target_compression_time * 1.5:
            # 压缩时间过长，降低级别
            if self.current_level > 1:
                self.current_level -= 1
                logger.info(f"[Compression] Reduced compression level to {self.current_level} (avg time: {avg_time:.3f}s)")
        elif avg_time < self.target_compression_time * 0.5 and avg_reduction < 0.3:
            # 压缩时间很短但效果不佳，提高级别
            if self.current_level < self.max_compression_level:
                self.current_level += 1
                logger.info(f"[Compression] Increased compression level to {self.current_level} (avg reduction: {avg_reduction:.1%})")
    
    def get_compression_level(self) -> int:
        """获取当前压缩级别"""
        return self.current_level


# 全局自适应配置
_adaptive_config = AdaptiveCompressionConfig()


def get_adaptive_compression_level() -> int:
    """获取自适应压缩级别"""
    return _adaptive_config.get_compression_level()


def update_compression_performance(compression_time: float, size_reduction: float):
    """更新压缩性能数据"""
    _adaptive_config.adjust_compression_level(compression_time, size_reduction)