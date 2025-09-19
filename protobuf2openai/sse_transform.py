from __future__ import annotations

import json
import uuid
from typing import Any, AsyncGenerator, Dict

import httpx
from .logging import logger

from .config import BRIDGE_BASE_URL
from .state import get_auth_headers, update_jwt_token
from .helpers import _get


async def _process_sse_events(response, completion_id: str, created_ts: int, model_id: str) -> AsyncGenerator[str, None]:
    """处理SSE事件流的核心逻辑，提取重复代码为单独函数"""
    current = ""
    tool_calls_emitted = False
    
    async for line in response.aiter_lines():
        if line.startswith("data:"):
            payload = line[5:].strip()
            if not payload:
                continue
            # 打印接收到的 Protobuf SSE 原始事件片段
            try:
                logger.info("[OpenAI Compat] 接收到的 Protobuf SSE(data): %s", payload)
            except Exception:
                pass
            if payload == "[DONE]":
                break
            current += payload
            continue
            
        if (line.strip() == "") and current:
            try:
                ev = json.loads(current)
            except Exception:
                current = ""
                continue
            current = ""
            event_data = (ev or {}).get("parsed_data") or {}

            # 打印接收到的 Protobuf 事件（解析后）
            try:
                logger.info("[OpenAI Compat] 接收到的 Protobuf 事件(parsed): %s", json.dumps(event_data, ensure_ascii=False))
            except Exception:
                pass

            if "init" in event_data:
                pass

            client_actions = _get(event_data, "client_actions", "clientActions")
            if isinstance(client_actions, dict):
                actions = _get(client_actions, "actions", "Actions") or []
                for action in actions:
                    append_data = _get(action, "append_to_message_content", "appendToMessageContent")
                    if isinstance(append_data, dict):
                        message = append_data.get("message", {})
                        agent_output = _get(message, "agent_output", "agentOutput") or {}
                        text_content = agent_output.get("text", "")
                        if text_content:
                            delta = {
                                "id": completion_id,
                                "object": "chat.completion.chunk",
                                "created": created_ts,
                                "model": model_id,
                                "choices": [{"index": 0, "delta": {"content": text_content}}],
                            }
                            # 打印转换后的 OpenAI SSE 事件
                            try:
                                logger.info("[OpenAI Compat] 转换后的 SSE(emit): %s", json.dumps(delta, ensure_ascii=False))
                            except Exception:
                                pass
                            yield f"data: {json.dumps(delta, ensure_ascii=False)}\n\n"

                    messages_data = _get(action, "add_messages_to_task", "addMessagesToTask")
                    if isinstance(messages_data, dict):
                        messages = messages_data.get("messages", [])
                        for message in messages:
                            tool_call = _get(message, "tool_call", "toolCall") or {}
                            call_mcp = _get(tool_call, "call_mcp_tool", "callMcpTool") or {}
                            if isinstance(call_mcp, dict) and call_mcp.get("name"):
                                try:
                                    args_obj = call_mcp.get("args", {}) or {}
                                    args_str = json.dumps(args_obj, ensure_ascii=False)
                                except Exception:
                                    args_str = "{}"
                                tool_call_id = tool_call.get("tool_call_id") or str(uuid.uuid4())
                                delta = {
                                    "id": completion_id,
                                    "object": "chat.completion.chunk",
                                    "created": created_ts,
                                    "model": model_id,
                                    "choices": [{
                                        "index": 0,
                                        "delta": {
                                            "tool_calls": [{
                                                "index": 0,
                                                "id": tool_call_id,
                                                "type": "function",
                                                "function": {"name": call_mcp.get("name"), "arguments": args_str},
                                            }]
                                        }
                                    }],
                                }
                                # 打印转换后的 OpenAI 工具调用事件
                                try:
                                    logger.info("[OpenAI Compat] 转换后的 SSE(emit tool_calls): %s", json.dumps(delta, ensure_ascii=False))
                                except Exception:
                                    pass
                                yield f"data: {json.dumps(delta, ensure_ascii=False)}\n\n"
                                tool_calls_emitted = True
                            else:
                                agent_output = _get(message, "agent_output", "agentOutput") or {}
                                text_content = agent_output.get("text", "")
                                if text_content:
                                    delta = {
                                        "id": completion_id,
                                        "object": "chat.completion.chunk",
                                        "created": created_ts,
                                        "model": model_id,
                                        "choices": [{"index": 0, "delta": {"content": text_content}}],
                                    }
                                    try:
                                        logger.info("[OpenAI Compat] 转换后的 SSE(emit): %s", json.dumps(delta, ensure_ascii=False))
                                    except Exception:
                                        pass
                                    yield f"data: {json.dumps(delta, ensure_ascii=False)}\n\n"

            if "finished" in event_data:
                done_chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_id,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": ("tool_calls" if tool_calls_emitted else "stop")}],
                }
                try:
                    logger.info("[OpenAI Compat] 转换后的 SSE(emit done): %s", json.dumps(done_chunk, ensure_ascii=False))
                except Exception:
                    pass
                yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"


async def _refresh_jwt_token(client: httpx.AsyncClient) -> bool:
    """尝试刷新JWT token，返回是否成功"""
    try:
        refresh_headers = get_auth_headers()
        refresh_headers.update({"Content-Type": "application/json"})
        
        r = await client.post(f"{BRIDGE_BASE_URL}/api/auth/refresh", headers=refresh_headers, timeout=10.0)
        
        if r.status_code == 200:
            # 成功刷新，提取新token并保存
            refresh_data = r.json()
            new_token = refresh_data.get("token") or refresh_data.get("access_token")
            
            if new_token:
                update_jwt_token(new_token)
                logger.info("[OpenAI Compat] JWT refresh successful, updated token")
                return True
            else:
                logger.error("[OpenAI Compat] JWT refresh returned 200 but no token found in response")
        else:
            logger.error("[OpenAI Compat] JWT refresh failed with status %s: %s", r.status_code, r.text)
            
    except Exception as e:
        logger.error("[OpenAI Compat] JWT refresh attempt failed: %s", e)
    
    return False


def _make_stream_request(client: httpx.AsyncClient, packet: Dict[str, Any]):
    """创建流式请求"""
    headers = get_auth_headers()
    headers.update({"accept": "text/event-stream"})
    
    return client.stream(
        "POST",
        f"{BRIDGE_BASE_URL}/api/warp/send_stream_sse",
        headers=headers,
        json={"json_data": packet, "message_type": "warp.multi_agent.v1.Request"},
    )


async def stream_openai_sse(packet: Dict[str, Any], completion_id: str, created_ts: int, model_id: str) -> AsyncGenerator[str, None]:
    """
    将Protobuf格式的SSE流转换为OpenAI兼容格式
    
    Args:
        packet: 要发送的数据包
        completion_id: 完成ID
        created_ts: 创建时间戳  
        model_id: 模型ID
        
    Yields:
        str: OpenAI格式的SSE事件字符串
    """
    try:
        # 发送首个SSE事件（OpenAI格式）
        first = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created_ts,
            "model": model_id,
            "choices": [{"index": 0, "delta": {"role": "assistant"}}],
        }
        try:
            logger.info("[OpenAI Compat] 转换后的 SSE(emit): %s", json.dumps(first, ensure_ascii=False))
        except Exception:
            pass
        yield f"data: {json.dumps(first, ensure_ascii=False)}\n\n"

        timeout = httpx.Timeout(60.0)
        async with httpx.AsyncClient(http2=True, timeout=timeout, trust_env=True) as client:
            # 首次请求
            response_cm = _make_stream_request(client, packet)
            async with response_cm as response:
                if response.status_code == 429:
                    # 尝试刷新JWT token
                    if await _refresh_jwt_token(client):
                        # 使用更新后的token重试
                        response_cm2 = _make_stream_request(client, packet)
                        async with response_cm2 as response2:
                            if response2.status_code != 200:
                                error_text = await response2.aread()
                                error_content = error_text.decode("utf-8") if error_text else ""
                                logger.error(f"[OpenAI Compat] Bridge HTTP error {response2.status_code}: {error_content[:300]}")
                                raise RuntimeError(f"bridge error: {error_content}")
                            
                            # 处理成功的响应
                            async for event in _process_sse_events(response2, completion_id, created_ts, model_id):
                                yield event
                            return
                    else:
                        # Token刷新失败，继续使用原始响应
                        pass

                if response.status_code != 200:
                    error_text = await response.aread()
                    error_content = error_text.decode("utf-8") if error_text else ""
                    logger.error(f"[OpenAI Compat] Bridge HTTP error {response.status_code}: {error_content[:300]}")
                    raise RuntimeError(f"bridge error: {error_content}")

                # 处理成功的响应
                async for event in _process_sse_events(response, completion_id, created_ts, model_id):
                    yield event

        # 发送完成标记
        try:
            logger.info("[OpenAI Compat] 转换后的 SSE(emit): [DONE]")
        except Exception:
            pass
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"[OpenAI Compat] Stream processing failed: {e}")
        error_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created_ts,
            "model": model_id,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "error"}],
            "error": {"message": str(e)},
        }
        try:
            logger.info("[OpenAI Compat] 转换后的 SSE(emit error): %s", json.dumps(error_chunk, ensure_ascii=False))
        except Exception:
            pass
        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
