from __future__ import annotations

import asyncio
import json

import httpx
from fastapi import FastAPI

from .logging import logger

from .config import BRIDGE_BASE_URL, WARMUP_INIT_RETRIES, WARMUP_INIT_DELAY_S
from .bridge import initialize_once
from .router import router
from .claude_router import claude_router
from .http_clients import warmup_shared_client, shutdown_shared_client
from .performance_monitor import start_performance_monitoring_task, get_global_monitor, get_performance_summary
from .cache import start_cache_cleanup_task, cache_stats
from .memory_optimizer import start_memory_optimization_task, get_memory_stats
from .request_batcher import get_batch_stats
from .http_clients import get_performance_metrics
from .compression import CompressionMiddleware
from .async_logging import setup_async_logging, get_async_log_stats
from .rate_limiter import RateLimitMiddleware, setup_rate_limiter, RateLimitPresets, get_rate_limit_stats
from .circuit_breaker import start_circuit_breaker_health_check, get_all_circuit_breaker_stats
from .json_optimizer import get_json_serializer, get_json_stats


app = FastAPI(title="OpenAI & Claude API Compatible (Warp bridge) - Streaming")

# 添加中间件（顺序很重要）
# 1. 压缩中间件（最后处理响应）
app.add_middleware(CompressionMiddleware, minimum_size=1024, compression_level=6)

# 2. 限流中间件
rate_limiter = setup_rate_limiter(RateLimitPresets.moderate())
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

app.include_router(router)
app.include_router(claude_router)


@app.on_event("startup")
async def _on_startup():
    try:
        logger.info("[OpenAI Compat] Server starting. BRIDGE_BASE_URL=%s", BRIDGE_BASE_URL)
        logger.info("[OpenAI Compat] Endpoints: GET /healthz, GET /v1/models, POST /v1/chat/completions, POST /v1/messages")
    except Exception:
        pass

    url = f"{BRIDGE_BASE_URL}/healthz"
    retries = WARMUP_INIT_RETRIES
    delay_s = WARMUP_INIT_DELAY_S
    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=5.0, trust_env=True) as client:
                resp = await client.get(url)
            if resp.status_code == 200:
                logger.info("[OpenAI Compat] Bridge server is ready at %s", url)
                break
            else:
                logger.warning("[OpenAI Compat] Bridge health at %s -> HTTP %s", url, resp.status_code)
        except Exception as e:
            logger.warning("[OpenAI Compat] Bridge health attempt %s/%s failed: %s", attempt, retries, e)
        await asyncio.sleep(delay_s)
    else:
        logger.error("[OpenAI Compat] Bridge server not ready at %s", url)

    try:
        await asyncio.to_thread(initialize_once)
    except Exception as e:
        logger.warning(f"[OpenAI Compat] Warmup initialize_once on startup failed: {e}") 

    # Warm up shared client and keep-alive pool
    try:
        await warmup_shared_client()
    except Exception as e:
        logger.warning(f"[OpenAI Compat] Shared client warmup failed: {e}")
    
    # Initialize performance monitoring
    try:
        await get_global_monitor()
        await start_performance_monitoring_task(interval=300)  # 5分钟间隔
        logger.info("[OpenAI Compat] Performance monitoring started")
    except Exception as e:
        logger.warning(f"[OpenAI Compat] Performance monitoring setup failed: {e}")
    
    # Start cache cleanup task
    try:
        await start_cache_cleanup_task()
        logger.info("[OpenAI Compat] Cache cleanup task started")
    except Exception as e:
        logger.warning(f"[OpenAI Compat] Cache cleanup task setup failed: {e}")
    
    # Start memory optimization task
    try:
        await start_memory_optimization_task(interval=300)  # 5分钟间隔
        logger.info("[OpenAI Compat] Memory optimization started")
    except Exception as e:
        logger.warning(f"[OpenAI Compat] Memory optimization setup failed: {e}")
    
    # Setup async logging
    try:
        setup_async_logging(log_file="logs/openai_compat.jsonl")
        logger.info("[OpenAI Compat] Async logging initialized")
    except Exception as e:
        logger.warning(f"[OpenAI Compat] Async logging setup failed: {e}")
    
    # Start circuit breaker health check
    try:
        await start_circuit_breaker_health_check()
        logger.info("[OpenAI Compat] Circuit breaker health check started")
    except Exception as e:
        logger.warning(f"[OpenAI Compat] Circuit breaker health check setup failed: {e}")
    
    # Initialize JSON optimizer
    try:
        get_json_serializer()
        logger.info("[OpenAI Compat] JSON optimizer initialized")
    except Exception as e:
        logger.warning(f"[OpenAI Compat] JSON optimizer setup failed: {e}")


@app.on_event("shutdown")
async def _on_shutdown():
    try:
        await shutdown_shared_client()
    except Exception as e:
        logger.warning(f"[OpenAI Compat] Shared client shutdown failed: {e}")