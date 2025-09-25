from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .logging import logger

from .models import ChatCompletionsRequest, ChatMessage
from .reorder import reorder_messages_for_anthropic
from .helpers import normalize_content_to_list, segments_to_text
from .packets import packet_template, map_history_to_warp_messages, attach_user_and_tools_to_inputs
from .state import STATE
from .config import BRIDGE_BASE_URL, HTTP_CLIENT_TIMEOUT, HTTP_CONNECT_TIMEOUT, HTTP_CLIENT_LIMITS
from .bridge import initialize_once
from .sse_transform import stream_openai_sse
from .auth import authenticate_request

# 缓存机制：缓存模型配置以减少重复计算
_MODEL_CONFIG_CACHE = {}
_PACKET_TEMPLATE_CACHE = None


def _get_cached_model_config(model: str) -> Dict[str, Any]:
    """获取缓存的模型配置"""
    if model not in _MODEL_CONFIG_CACHE:
        _MODEL_CONFIG_CACHE[model] = {"base": model}
    return _MODEL_CONFIG_CACHE[model]


def _get_cached_packet_template() -> Dict[str, Any]:
    """获取缓存的packet模板"""
    global _PACKET_TEMPLATE_CACHE
    if _PACKET_TEMPLATE_CACHE is None:
        _PACKET_TEMPLATE_CACHE = packet_template()
    return _PACKET_TEMPLATE_CACHE.copy()


router = APIRouter()


@router.get("/")
def root():
    return {"service": "OpenAI Chat Completions (Warp bridge) - Streaming", "status": "ok"}


@router.get("/healthz")
def health_check():
    return {"status": "ok", "service": "OpenAI Chat Completions (Warp bridge) - Streaming"}


@router.get("/v1/models")
async def list_models():
    """OpenAI-compatible model listing. Forwards to bridge, with local fallback."""
    timeout = httpx.Timeout(HTTP_CLIENT_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)
    async with httpx.AsyncClient(
        timeout=timeout,
        trust_env=True,
        limits=httpx.Limits(**HTTP_CLIENT_LIMITS)
    ) as client:
        try:
            resp = await client.get(f"{BRIDGE_BASE_URL}/v1/models")
            if resp.status_code != 200:
                raise HTTPException(resp.status_code, f"bridge_error: {resp.text}")
            return resp.json()
        except Exception as e:
            try:
                # Local fallback: construct models directly if bridge is unreachable
                from warp2protobuf.config.models import get_all_unique_models  # type: ignore
                models = get_all_unique_models()
                return {"object": "list", "data": models}
            except Exception:
                raise HTTPException(502, f"bridge_unreachable: {e}")


@router.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionsRequest, request: Request = None):
    # 认证检查
    if request:
        await authenticate_request(request)

    try:
        initialize_once()
    except Exception as e:
        logger.warning(f"[OpenAI Compat] initialize_once failed or skipped: {e}")

    if not req.messages:
        raise HTTPException(400, "messages 不能为空")

    # 1) 打印接收到的 Chat Completions 原始请求体（仅在调试模式）
    try:
        if logger.isEnabledFor(10):  # DEBUG级别
            logger.debug("[OpenAI Compat] 接收到的 Chat Completions 请求体(原始): %s", json.dumps(req.dict(), ensure_ascii=False))
    except Exception:
        pass

    # 整理消息
    history: List[ChatMessage] = reorder_messages_for_anthropic(list(req.messages))

    # 2) 打印整理后的请求体（post-reorder，仅在调试模式）
    try:
        if logger.isEnabledFor(10):  # DEBUG级别
            logger.debug("[OpenAI Compat] 整理后的请求体(post-reorder): %s", json.dumps({
                **req.dict(),
                "messages": [m.dict() for m in history]
            }, ensure_ascii=False))
    except Exception:
        pass

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
    packet = _get_cached_packet_template()
    packet["task_context"] = {
        "tasks": [{
            "id": task_id,
            "description": "",
            "status": {"in_progress": {}},
            "messages": map_history_to_warp_messages(history, task_id, None, False),
        }],
        "active_task_id": task_id,
    }

    # 使用缓存的模型配置
    model_config = _get_cached_model_config(req.model or "claude-4.1-opus")
    packet.setdefault("settings", {}).setdefault("model_config", model_config)

    if STATE.conversation_id:
        packet.setdefault("metadata", {})["conversation_id"] = STATE.conversation_id

    attach_user_and_tools_to_inputs(packet, history, system_prompt_text)

    if req.tools:
        mcp_tools: List[Dict[str, Any]] = []
        for t in req.tools:
            if t.type != "function" or not t.function:
                continue
            mcp_tools.append({
                "name": t.function.name,
                "description": t.function.description or "",
                "input_schema": t.function.parameters or {},
            })
        if mcp_tools:
            packet.setdefault("mcp_context", {}).setdefault("tools", []).extend(mcp_tools)

    # 3) 打印转换成 protobuf JSON 的请求体（仅在调试模式）
    try:
        if logger.isEnabledFor(10):  # DEBUG级别
            logger.debug("[OpenAI Compat] 转换成 Protobuf JSON 的请求体: %s", json.dumps(packet, ensure_ascii=False))
    except Exception:
        pass

    created_ts = int(time.time())
    completion_id = str(uuid.uuid4())
    model_id = req.model or "warp-default"

    if req.stream:
        async def _agen():
            async for chunk in stream_openai_sse(packet, completion_id, created_ts, model_id):
                yield chunk
        return StreamingResponse(_agen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})

    # 使用异步HTTP客户端发送请求
    timeout = httpx.Timeout(HTTP_CLIENT_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)
    async with httpx.AsyncClient(
        timeout=timeout,
        trust_env=True,
        limits=httpx.Limits(**HTTP_CLIENT_LIMITS)
    ) as client:
        def _post_once() -> httpx.Response:
            return client.post(
                f"{BRIDGE_BASE_URL}/api/warp/send_stream",
                json={"json_data": packet, "message_type": "warp.multi_agent.v1.Request"},
            )

        try:
            resp = await _post_once()
            if resp.status_code == 429:
                try:
                    r = await client.post(f"{BRIDGE_BASE_URL}/api/auth/refresh")
                    logger.warning("[OpenAI Compat] Bridge returned 429. Tried JWT refresh -> HTTP %s", getattr(r, 'status_code', 'N/A'))
                except Exception as _e:
                    logger.warning("[OpenAI Compat] JWT refresh attempt failed after 429: %s", _e)
                resp = await _post_once()
            if resp.status_code != 200:
                raise HTTPException(resp.status_code, f"bridge_error: {resp.text}")
            bridge_resp = resp.json()
        except Exception as e:
            raise HTTPException(502, f"bridge_unreachable: {e}")

    try:
        STATE.conversation_id = bridge_resp.get("conversation_id") or STATE.conversation_id
        ret_task_id = bridge_resp.get("task_id")
        if isinstance(ret_task_id, str) and ret_task_id:
            STATE.baseline_task_id = ret_task_id
    except Exception:
        pass

    tool_calls: List[Dict[str, Any]] = []
    try:
        parsed_events = bridge_resp.get("parsed_events", []) or []
        for ev in parsed_events:
            evd = ev.get("parsed_data") or ev.get("raw_data") or {}
            client_actions = evd.get("client_actions") or evd.get("clientActions") or {}
            actions = client_actions.get("actions") or client_actions.get("Actions") or []
            for action in actions:
                add_msgs = action.get("add_messages_to_task") or action.get("addMessagesToTask") or {}
                if not isinstance(add_msgs, dict):
                    continue
                for message in add_msgs.get("messages", []) or []:
                    tc = message.get("tool_call") or message.get("toolCall") or {}
                    call_mcp = tc.get("call_mcp_tool") or tc.get("callMcpTool") or {}
                    if isinstance(call_mcp, dict) and call_mcp.get("name"):
                        try:
                            args_obj = call_mcp.get("args", {}) or {}
                            args_str = json.dumps(args_obj, ensure_ascii=False)
                        except Exception:
                            args_str = "{}"
                        tool_calls.append({
                            "id": tc.get("tool_call_id") or str(uuid.uuid4()),
                            "type": "function",
                            "function": {"name": call_mcp.get("name"), "arguments": args_str},
                        })
    except Exception:
        pass

    if tool_calls:
        msg_payload = {"role": "assistant", "content": "", "tool_calls": tool_calls}
        finish_reason = "tool_calls"
    else:
        response_text = bridge_resp.get("response", "")
        msg_payload = {"role": "assistant", "content": response_text}
        finish_reason = "stop"

    final = {
        "id": completion_id,
        "object": "chat.completion",
        "created": created_ts,
        "model": model_id,
        "choices": [{"index": 0, "message": msg_payload, "finish_reason": finish_reason}],
    }
    return final 