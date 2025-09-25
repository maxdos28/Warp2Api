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


app = FastAPI(title="OpenAI & Claude API Compatible (Warp bridge) - Streaming")
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


@app.on_event("shutdown")
async def _on_shutdown():
    try:
        await shutdown_shared_client()
    except Exception as e:
        logger.warning(f"[OpenAI Compat] Shared client shutdown failed: {e}")