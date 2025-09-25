from __future__ import annotations

import asyncio
from typing import Optional

import httpx


_async_client: Optional[httpx.AsyncClient] = None
_lock = asyncio.Lock()


async def get_shared_async_client() -> httpx.AsyncClient:
    """Return a process-wide shared AsyncClient with HTTP/2 and connection pooling.

    The client is created lazily and reused across requests to reduce connection setup time
    and improve throughput. Caller MUST NOT close it.
    """
    global _async_client
    if _async_client is not None:
        return _async_client
    async with _lock:
        if _async_client is None:
            # Generous limits but prevent unbounded concurrency; tune as needed
            limits = httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=30.0,
            )
            timeout = httpx.Timeout(60.0)
            _async_client = httpx.AsyncClient(
                http2=True,
                timeout=timeout,
                limits=limits,
                headers={"Connection": "keep-alive"},
                trust_env=True,
            )
        return _async_client


async def warmup_shared_client() -> None:
    # Ensure the client is instantiated early to establish pools
    await get_shared_async_client()


async def shutdown_shared_client() -> None:
    global _async_client
    async with _lock:
        if _async_client is not None:
            await _async_client.aclose()
            _async_client = None

