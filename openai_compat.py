#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI Chat Completions compatible server (system-prompt flavored)

Startup entrypoint that exposes the modular app implemented in protobuf2openai.
"""

from __future__ import annotations

import os
import asyncio

from protobuf2openai.app import app  # FastAPI app


if __name__ == "__main__":
    import argparse
    import uvicorn
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="OpenAI兼容API服务器")
    parser.add_argument("--port", type=int, default=28889, help="服务器监听端口 (默认: 28889)")
    args = parser.parse_args()
    
    # Refresh JWT on startup before running the server
    try:
        from warp2protobuf.core.auth import refresh_jwt_if_needed as _refresh_jwt
        asyncio.run(_refresh_jwt())
    except Exception:
        pass
    uvicorn.run(
        app,
        host=os.getenv("HOST", "127.0.0.1"),
        port=args.port,
        log_level="info",
        timeout_keep_alive=600,  # 增加保活超时到10分钟
        timeout_graceful_shutdown=30,
        limit_max_requests=1000,
        limit_concurrency=100,
        # 增加请求体大小限制以处理 Claude Code 的大请求
        access_log=True,
        use_colors=True,
    )
