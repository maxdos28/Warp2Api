"""
Claude API 兼容路由处理器
实现 /v1/messages 端点
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .logging import logger
from .models import ClaudeRequest
from .claude_auth import authenticate_claude_request
from .claude_transform import claude_request_to_internal_packet, format_claude_response
from .claude_streaming import stream_claude_sse
from .config import BRIDGE_BASE_URL
from .bridge import initialize_once
from .state import STATE


router = APIRouter(prefix="/v1", tags=["Claude API"])


@router.post("/messages")
async def create_message(req: ClaudeRequest, request: Request = None):
    """
    Claude API 兼容的消息创建端点
    支持流式和非流式响应
    """
    # 认证检查
    if request:
        await authenticate_claude_request(request)
    
    # 初始化 bridge 连接
    try:
        initialize_once()
    except Exception as e:
        logger.warning("[Claude API] initialize_once failed or skipped: %s", e)
    
    if not req.messages:
        raise HTTPException(400, "messages cannot be empty")
    
    # 日志记录原始请求
    try:
        logger.info("[Claude API] 接收到的 Claude 请求: %s", json.dumps(req.dict(), ensure_ascii=False))
    except Exception:
        logger.info("[Claude API] 接收到的 Claude 请求序列化失败")
    
    # 转换为内部格式
    try:
        packet = claude_request_to_internal_packet(req)
    except Exception as e:
        logger.error("[Claude API] 请求转换失败: %s", e)
        raise HTTPException(400, f"Request transformation failed: {str(e)}")
    
    # 日志记录转换后的数据包
    try:
        logger.info("[Claude API] 转换后的数据包: %s", json.dumps(packet, ensure_ascii=False))
    except Exception:
        logger.info("[Claude API] 转换后的数据包序列化失败")
    
    message_id = str(uuid.uuid4())
    model = req.model
    
    # 流式响应
    if req.stream:
        async def _stream_generator():
            async for chunk in stream_claude_sse(packet, message_id, model):
                yield chunk
        
        return StreamingResponse(
            _stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    # 非流式响应
    def _post_once() -> requests.Response:
        return requests.post(
            f"{BRIDGE_BASE_URL}/api/warp/send_stream",
            json={"json_data": packet, "message_type": "warp.multi_agent.v1.Request"},
            timeout=(5.0, 180.0),
        )
    
    try:
        resp = _post_once()
        if resp.status_code == 429:
            try:
                r = requests.post(f"{BRIDGE_BASE_URL}/api/auth/refresh", timeout=10.0)
                logger.warning("[Claude API] Bridge returned 429. Tried JWT refresh -> HTTP %s", getattr(r, 'status_code', 'N/A'))
            except Exception as e:
                logger.warning("[Claude API] JWT refresh attempt failed after 429: %s", e)
            resp = _post_once()
        
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"bridge_error: {resp.text}")
        
        bridge_resp = resp.json()
    except Exception as e:
        raise HTTPException(502, f"bridge_unreachable: {e}")
    
    # 更新状态
    try:
        STATE.conversation_id = bridge_resp.get("conversation_id") or STATE.conversation_id
        ret_task_id = bridge_resp.get("task_id")
        if isinstance(ret_task_id, str) and ret_task_id:
            STATE.baseline_task_id = ret_task_id
    except Exception:
        pass
    
    # 格式化响应
    try:
        claude_response = format_claude_response(bridge_resp, message_id, model)
        logger.info("[Claude API] 响应格式化完成")
        return claude_response
    except Exception as e:
        logger.error("[Claude API] 响应格式化失败: %s", e)
        raise HTTPException(500, f"Response formatting failed: {str(e)}")


@router.get("/models")
def list_claude_models():
    """列出可用的 Claude 模型"""
    try:
        # 尝试从 bridge 获取模型列表
        resp = requests.get(f"{BRIDGE_BASE_URL}/v1/models", timeout=10.0)
        if resp.status_code == 200:
            models_data = resp.json()
            # 过滤出 Claude 相关模型
            claude_models = []
            for model in models_data.get("data", []):
                model_id = model.get("id", "")
                if "claude" in model_id.lower():
                    claude_models.append(model)
            
            if claude_models:
                return {"object": "list", "data": claude_models}
    except Exception as e:
        logger.warning("[Claude API] Failed to get models from bridge: %s", e)
    
    # 本地回退：返回默认 Claude 模型列表
    default_models = [
        {
            "id": "claude-4.1-opus",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "anthropic"
        },
        {
            "id": "claude-4.1-sonnet", 
            "object": "model",
            "created": int(time.time()),
            "owned_by": "anthropic"
        },
        {
            "id": "claude-4.1-haiku",
            "object": "model", 
            "created": int(time.time()),
            "owned_by": "anthropic"
        }
    ]
    
    return {"object": "list", "data": default_models}