"""
Claude API 认证模块
"""
from __future__ import annotations

from fastapi import HTTPException, Request
from .logging import logger

# Claude API Token (可通过环境变量覆盖)
import os
CLAUDE_API_TOKEN = os.getenv("CLAUDE_API_TOKEN", "123456")


async def authenticate_claude_request(request: Request) -> None:
    """验证 Claude API 请求的认证"""
    # 先检查 x-api-key header（Claude API 的标准方式）
    api_key = request.headers.get("x-api-key")
    if api_key:
        token = api_key
    else:
        # 检查 authorization header（支持 Bearer token）
        auth_header = request.headers.get("authorization")
        if not auth_header:
            logger.warning("[Claude Auth] Missing x-api-key or authorization header")
            raise HTTPException(status_code=401, detail="Missing x-api-key or authorization header")
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # 移除 "Bearer " 前缀
        elif auth_header.startswith("x-api-key "):
            token = auth_header[10:]  # 移除 "x-api-key " 前缀
        else:
            logger.warning("[Claude Auth] Invalid authorization format")
            raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    if token != CLAUDE_API_TOKEN:
        logger.warning("[Claude Auth] Invalid API token: %s", token[:8] + "..." if len(token) > 8 else token)
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    logger.info("[Claude Auth] Authentication successful")