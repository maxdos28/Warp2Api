#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI Chat Completions compatible server - Simplified version
"""

from __future__ import annotations

import os
import asyncio
import logging

# 设置基本日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_simple_app():
    """创建简化版本的FastAPI应用"""
    try:
        from protobuf2openai.app import app
        logger.info("✅ Full optimized app loaded successfully")
        return app
    except ImportError as e:
        logger.warning(f"⚠️ Failed to load optimized app: {e}")
        logger.info("🔄 Loading basic app without advanced optimizations...")
        
        # 创建基础版本的应用
        from fastapi import FastAPI
        from protobuf2openai.router import router
        
        basic_app = FastAPI(title="OpenAI Compatible API (Basic)")
        basic_app.include_router(router)
        
        logger.info("✅ Basic app loaded successfully")
        return basic_app
    except Exception as e:
        logger.error(f"❌ Failed to load any app: {e}")
        raise

if __name__ == "__main__":
    import argparse
    import uvicorn
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="OpenAI兼容API服务器")
    parser.add_argument("--port", type=int, default=28889, help="服务器监听端口 (默认: 28889)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="服务器监听地址 (默认: 127.0.0.1)")
    args = parser.parse_args()
    
    # 尝试刷新JWT
    try:
        from warp2protobuf.core.auth import refresh_jwt_if_needed as _refresh_jwt
        asyncio.run(_refresh_jwt())
        logger.info("✅ JWT refreshed")
    except Exception as e:
        logger.warning(f"⚠️ JWT refresh failed: {e}")
    
    # 创建应用
    try:
        app = create_simple_app()
        
        logger.info("🚀 Starting server...")
        logger.info(f"   Host: {args.host}")
        logger.info(f"   Port: {args.port}")
        logger.info(f"   URL: http://{args.host}:{args.port}")
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info",
        )
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        raise