from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any
from collections import defaultdict

import httpx
from .logging import logger


_async_client: Optional[httpx.AsyncClient] = None
_lock = asyncio.Lock()
_connection_stats = defaultdict(int)
_performance_metrics = {
    "total_requests": 0,
    "total_response_time": 0.0,
    "failed_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "connection_reuses": 0,
    "new_connections": 0,
}


async def get_shared_async_client() -> httpx.AsyncClient:
    """Return a process-wide shared AsyncClient with HTTP/2 and connection pooling.

    The client is created lazily and reused across requests to reduce connection setup time
    and improve throughput. Caller MUST NOT close it.
    """
    global _async_client
    if _async_client is not None:
        _performance_metrics["connection_reuses"] += 1
        return _async_client
    
    async with _lock:
        if _async_client is None:
            logger.info("[HTTP Client] Creating new optimized HTTP client with enhanced connection pooling")
            
            # Enhanced connection limits for better performance
            limits = httpx.Limits(
                max_connections=200,  # Increased from 100
                max_keepalive_connections=50,  # Increased from 20
                keepalive_expiry=60.0,  # Increased from 30.0
            )
            
            # Optimized timeout settings for large requests
            timeout = httpx.Timeout(
                connect=15.0,  # Connection timeout
                read=300.0,    # Read timeout for very long responses (5 minutes)
                write=60.0,    # Write timeout
                pool=10.0      # Pool timeout
            )
            
            # Performance-optimized headers
            headers = {
                "Connection": "keep-alive",
                "Keep-Alive": "timeout=60, max=1000",
                "Accept-Encoding": "gzip, deflate, br",
                "User-Agent": "OpenAI-Compat-Client/1.0 (optimized)",
            }
            
            _async_client = httpx.AsyncClient(
                http2=True,
                timeout=timeout,
                limits=limits,
                headers=headers,
                trust_env=True,
                follow_redirects=True,
            )
            
            _performance_metrics["new_connections"] += 1
            logger.info("[HTTP Client] New HTTP client created with enhanced performance settings")
        
        return _async_client


async def warmup_shared_client() -> None:
    """Warm up the shared client and establish connection pools"""
    logger.info("[HTTP Client] Warming up shared HTTP client...")
    client = await get_shared_async_client()
    
    # Pre-warm connection pools by making health check requests
    try:
        from .config import BRIDGE_BASE_URL
        health_url = f"{BRIDGE_BASE_URL}/healthz"
        start_time = time.time()
        response = await client.get(health_url, timeout=5.0)
        warmup_time = time.time() - start_time
        
        if response.status_code == 200:
            logger.info(f"[HTTP Client] Warmup successful in {warmup_time:.3f}s")
        else:
            logger.warning(f"[HTTP Client] Warmup returned HTTP {response.status_code}")
    except Exception as e:
        logger.warning(f"[HTTP Client] Warmup failed: {e}")


async def shutdown_shared_client() -> None:
    global _async_client
    async with _lock:
        if _async_client is not None:
            logger.info("[HTTP Client] Shutting down shared HTTP client")
            await _async_client.aclose()
            _async_client = None
            
            # Log performance metrics
            if _performance_metrics["total_requests"] > 0:
                avg_response_time = _performance_metrics["total_response_time"] / _performance_metrics["total_requests"]
                success_rate = ((_performance_metrics["total_requests"] - _performance_metrics["failed_requests"]) 
                               / _performance_metrics["total_requests"]) * 100
                
                logger.info(f"[HTTP Client] Performance Summary:")
                logger.info(f"  Total requests: {_performance_metrics['total_requests']}")
                logger.info(f"  Average response time: {avg_response_time:.3f}s")
                logger.info(f"  Success rate: {success_rate:.2f}%")
                logger.info(f"  Connection reuses: {_performance_metrics['connection_reuses']}")
                logger.info(f"  Cache hit rate: {_performance_metrics['cache_hits'] / max(1, _performance_metrics['cache_hits'] + _performance_metrics['cache_misses']) * 100:.2f}%")


def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics"""
    return _performance_metrics.copy()


def reset_performance_metrics() -> None:
    """Reset performance metrics"""
    global _performance_metrics
    _performance_metrics = {
        "total_requests": 0,
        "total_response_time": 0.0,
        "failed_requests": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "connection_reuses": 0,
        "new_connections": 0,
    }
    logger.info("[HTTP Client] Performance metrics reset")


class PerformanceTracker:
    """Context manager for tracking request performance"""
    
    def __init__(self, operation: str):
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            _performance_metrics["total_requests"] += 1
            _performance_metrics["total_response_time"] += duration
            
            if exc_type is not None:
                _performance_metrics["failed_requests"] += 1
                logger.warning(f"[HTTP Client] {self.operation} failed in {duration:.3f}s: {exc_val}")
            else:
                logger.debug(f"[HTTP Client] {self.operation} completed in {duration:.3f}s")

