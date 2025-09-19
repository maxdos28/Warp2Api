from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .logging import logger
from .claude_models import ClaudeMessagesRequest, ClaudeMessagesResponse
from .claude_converter import (
    claude_to_openai_request,
    openai_to_claude_response,
    create_claude_stream_events,
    extract_token_usage_from_bridge_response,
    get_claude_stop_reason_from_bridge
)
from .reorder import reorder_messages_for_anthropic
from .helpers import normalize_content_to_list, segments_to_text
from .packets import packet_template, map_history_to_warp_messages, attach_user_and_tools_to_inputs
from .state import STATE, update_jwt_token, get_auth_headers
from .config import BRIDGE_BASE_URL
from .bridge import initialize_once
from .auth import authenticate_request


claude_router = APIRouter()


@claude_router.post("/v1/messages")
async def claude_messages(req: ClaudeMessagesRequest, request: Request = None):
    """Claude API compatible /v1/messages endpoint"""
    
    # 认证检查
    if request:
        await authenticate_request(request)

    try:
        initialize_once()
    except Exception as e:
        logger.warning(f"[Claude Compat] initialize_once failed or skipped: {e}")

    if not req.messages:
        raise HTTPException(400, "messages cannot be empty")

    if req.max_tokens <= 0:
        raise HTTPException(400, "max_tokens must be positive")

    # 1) 打印接收到的 Claude Messages 原始请求体
    try:
        logger.info("[Claude Compat] Received Claude Messages request: %s", json.dumps(req.dict(), ensure_ascii=False))
    except Exception:
        logger.info("[Claude Compat] Received Claude Messages request serialization failed")

    # 2) 转换为 OpenAI 格式
    openai_req = claude_to_openai_request(req)
    
    # 3) 使用现有的 OpenAI 处理逻辑
    history = reorder_messages_for_anthropic(list(openai_req.messages))

    # 4) 打印转换后的请求体
    try:
        logger.info("[Claude Compat] Converted to OpenAI format: %s", json.dumps({
            **openai_req.dict(),
            "messages": [m.dict() for m in history]
        }, ensure_ascii=False))
    except Exception:
        logger.info("[Claude Compat] Converted request serialization failed")

    # 提取系统提示
    system_prompt_text: Optional[str] = None
    try:
        chunks: List[str] = []
        for _m in history:
            if _m.role == "system":
                _txt = segments_to_text(normalize_content_to_list(_m.content))
                if _txt.strip():
                    chunks.append(_txt)
        if chunks:
            system_prompt_text = "\n\n".join(chunks)
    except Exception:
        system_prompt_text = None

    task_id = STATE.baseline_task_id or str(uuid.uuid4())
    packet = packet_template()
    packet["task_context"] = {
        "tasks": [{
            "id": task_id,
            "description": "",
            "status": {"in_progress": {}},
            "messages": map_history_to_warp_messages(history, task_id, None, False),
        }],
        "active_task_id": task_id,
    }

    # 设置模型配置
    packet.setdefault("settings", {}).setdefault("model_config", {})
    packet["settings"]["model_config"]["base"] = openai_req.model or "claude-4-sonnet"

    if STATE.conversation_id:
        packet.setdefault("metadata", {})["conversation_id"] = STATE.conversation_id

    attach_user_and_tools_to_inputs(packet, history, system_prompt_text)

    # 5) 打印转换成 protobuf JSON 的请求体
    try:
        logger.info("[Claude Compat] Converted to Protobuf JSON: %s", json.dumps(packet, ensure_ascii=False))
    except Exception:
        logger.info("[Claude Compat] Protobuf JSON serialization failed")

    created_ts = int(time.time())
    request_id = f"msg_{str(uuid.uuid4()).replace('-', '')}"

    if req.stream:
        async def _claude_stream_generator():
            """Generate Claude-compatible streaming response"""
            try:
                # Send initial events
                start_events = create_claude_stream_events(
                    content_delta="",
                    is_start=True,
                    claude_model=req.model,
                    request_id=request_id
                )
                
                for event in start_events:
                    yield f"event: {event.type}\n"
                    yield f"data: {json.dumps(event.dict(), ensure_ascii=False)}\n\n"

                # Stream content from bridge using existing SSE transform
                from .sse_transform import stream_openai_sse
                
                accumulated_content = ""
                async for chunk in stream_openai_sse(packet, request_id, created_ts, openai_req.model):
                    try:
                        # Parse OpenAI SSE chunk
                        if chunk.startswith("data: "):
                            data_str = chunk[6:].strip()
                            if data_str == "[DONE]":
                                break
                            
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content_delta = delta.get("content", "")
                                
                                if content_delta:
                                    accumulated_content += content_delta
                                    
                                    # Send content delta event
                                    delta_events = create_claude_stream_events(
                                        content_delta=content_delta,
                                        claude_model=req.model,
                                        request_id=request_id
                                    )
                                    
                                    for event in delta_events:
                                        yield f"event: {event.type}\n"
                                        yield f"data: {json.dumps(event.dict(), ensure_ascii=False)}\n\n"
                    
                    except Exception as e:
                        logger.warning(f"[Claude Compat] Stream parsing error: {e}")
                
                # Send end events
                end_events = create_claude_stream_events(
                    content_delta="",
                    is_end=True,
                    claude_model=req.model,
                    request_id=request_id
                )
                
                for event in end_events:
                    yield f"event: {event.type}\n"
                    yield f"data: {json.dumps(event.dict(), ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.error(f"[Claude Compat] Streaming error: {e}")
                # Send error event
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            _claude_stream_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    # Non-streaming response
    def _post_once() -> requests.Response:
        # 添加JWT token到请求头
        headers = get_auth_headers()
        headers.update({"Content-Type": "application/json"})
        
        return requests.post(
            f"{BRIDGE_BASE_URL}/api/warp/send_stream",
            json={"json_data": packet, "message_type": "warp.multi_agent.v1.Request"},
            headers=headers,
            timeout=(5.0, 180.0),
        )

    try:
        resp = _post_once()
        if resp.status_code == 429:
            try:
                # 刷新JWT token
                refresh_headers = get_auth_headers()
                refresh_headers.update({"Content-Type": "application/json"})
                
                r = requests.post(f"{BRIDGE_BASE_URL}/api/auth/refresh", headers=refresh_headers, timeout=10.0)
                
                if r.status_code == 200:
                    # 成功刷新，提取新token并保存
                    refresh_data = r.json()
                    new_token = refresh_data.get("token") or refresh_data.get("access_token")
                    
                    if new_token:
                        update_jwt_token(new_token)
                        logger.info("[Claude Compat] JWT refresh successful, updated token")
                        
                        # 使用新token重试请求
                        resp = _post_once()
                    else:
                        logger.error("[Claude Compat] JWT refresh returned 200 but no token found in response")
                        raise HTTPException(429, f"JWT refresh failed: No token in response")
                else:
                    logger.error("[Claude Compat] JWT refresh failed with status %s: %s", r.status_code, r.text)
                    raise HTTPException(429, f"JWT refresh failed: HTTP {r.status_code}")
                    
            except HTTPException:
                raise  # 重新抛出HTTPException
            except Exception as _e:
                logger.error("[Claude Compat] JWT refresh attempt failed: %s", _e)
                raise HTTPException(429, f"JWT refresh error: {_e}")
                
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"bridge_error: {resp.text}")
        bridge_resp = resp.json()
    except HTTPException:
        raise  # 重新抛出HTTPException
    except Exception as e:
        raise HTTPException(502, f"bridge_unreachable: {e}")

    try:
        STATE.conversation_id = bridge_resp.get("conversation_id") or STATE.conversation_id
        ret_task_id = bridge_resp.get("task_id")
        if isinstance(ret_task_id, str) and ret_task_id:
            STATE.baseline_task_id = ret_task_id
    except Exception:
        pass

    # 提取并验证响应内容
    response_text = bridge_resp.get("response", "")
    
    # 验证响应内容不为空
    if not response_text or not response_text.strip():
        # 尝试从parsed_events中提取响应文本
        try:
            parsed_events = bridge_resp.get("parsed_events", []) or []
            response_parts = []
            for ev in parsed_events:
                evd = ev.get("parsed_data") or ev.get("raw_data") or {}
                client_actions = evd.get("client_actions") or evd.get("clientActions") or {}
                actions = client_actions.get("actions") or client_actions.get("Actions") or []
                for action in actions:
                    # 从add_messages_to_task中提取agent_output
                    add_msgs = action.get("add_messages_to_task") or action.get("addMessagesToTask") or {}
                    if isinstance(add_msgs, dict):
                        for message in add_msgs.get("messages", []) or []:
                            agent_output = message.get("agent_output") or message.get("agentOutput") or {}
                            text_content = agent_output.get("text", "")
                            if text_content and text_content.strip():
                                response_parts.append(text_content)
            
            response_text = "".join(response_parts).strip()
            
            if not response_text:
                logger.warning("[Claude Compat] Empty response from bridge, using fallback message")
                response_text = "I apologize, but I encountered an issue generating a response. Please try again."
                
        except Exception as e:
            logger.error(f"[Claude Compat] Failed to extract response from parsed_events: {e}")
            response_text = "I apologize, but I encountered an issue generating a response. Please try again."

    # 转换为 Claude 响应格式
    openai_response = {
        "id": request_id,
        "object": "chat.completion",
        "created": created_ts,
        "model": req.model,  # 使用原始Claude模型名，不是内部映射后的模型
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response_text
            },
            "finish_reason": "stop"
        }]
    }

    claude_response = openai_to_claude_response(openai_response, req.model, request_id)
    
    # 更新 token 使用情况
    claude_response.usage = extract_token_usage_from_bridge_response(bridge_resp)
    claude_response.stop_reason = get_claude_stop_reason_from_bridge(bridge_resp)

    return claude_response


def extract_content_delta(stream_data: Dict[str, Any]) -> str:
    """Extract content delta from streaming data"""
    try:
        # Try to extract text content from various possible paths
        if "choices" in stream_data:
            choices = stream_data["choices"]
            if choices and len(choices) > 0:
                delta = choices[0].get("delta", {})
                return delta.get("content", "")
        
        # Try other possible paths based on bridge response format
        parsed_data = stream_data.get("parsed_data", {})
        if "agent_output" in parsed_data:
            return parsed_data["agent_output"].get("text", "")
        
        return ""
    except Exception:
        return ""
