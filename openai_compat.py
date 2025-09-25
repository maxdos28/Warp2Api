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
    parser.add_argument("--host", type=str, default="127.0.0.1", help="服务器监听地址 (默认: 127.0.0.1)")
    args = parser.parse_args()
    
    # Refresh JWT on startup before running the server
    try:
        from warp2protobuf.core.auth import refresh_jwt_if_needed as _refresh_jwt
        asyncio.run(_refresh_jwt())
    except Exception:
        pass
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
    )
