from __future__ import annotations

import json
import uuid
from typing import Any, AsyncGenerator, Dict

import httpx
from .logging import logger

from .config import (
    BRIDGE_BASE_URL,
    HTTP_CLIENT_TIMEOUT,
    HTTP_CONNECT_TIMEOUT,
    HTTP_CLIENT_LIMITS,
    LOG_MAX_REQUEST_SIZE,
    LOG_MAX_RESPONSE_SIZE,
    ENABLE_DEBUG_LOGGING
)
from .helpers import _get


def _create_text_chunk(base_chunk: Dict[str, Any], text_content: str) -> str:
    """创建文本内容块，减少重复代码"""
    chunk = {**base_chunk, "choices": [{"index": 0, "delta": {"content": text_content}}]}
    return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"


def _create_tool_calls_chunk(base_chunk: Dict[str, Any], tool_call_id: str, name: str, args_str: str) -> str:
    """创建工具调用块，减少重复代码"""
    chunk = {
        **base_chunk,
        "choices": [{
            "index": 0,
            "delta": {
                "tool_calls": [{
                    "index": 0,
                    "id": tool_call_id,
                    "type": "function",
                    "function": {"name": name, "arguments": args_str},
                }]
            }
        }],
    }
    return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"


def _create_done_chunk(base_chunk: Dict[str, Any], finish_reason: str) -> str:
    """创建完成块，减少重复代码"""
    chunk = {**base_chunk, "choices": [{"index": 0, "delta": {}, "finish_reason": finish_reason}]}
    return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"


def _log_debug_json(logger, message: str, data: Any) -> None:
    """调试日志辅助函数"""
    try:
        if ENABLE_DEBUG_LOGGING and logger.isEnabledFor(10):  # DEBUG级别
            # 限制日志大小以提高性能
            json_str = json.dumps(data, ensure_ascii=False)
            if len(json_str) > LOG_MAX_REQUEST_SIZE:
                json_str = json_str[:LOG_MAX_REQUEST_SIZE] + "..."
            logger.debug(message, json_str)
    except Exception:
        pass


def _log_limited_response(logger, message: str, response_text: str) -> None:
    """限制响应文本长度的日志记录"""
    try:
        if ENABLE_DEBUG_LOGGING and logger.isEnabledFor(10):  # DEBUG级别
            limited_text = response_text[:LOG_MAX_RESPONSE_SIZE] if len(response_text) > LOG_MAX_RESPONSE_SIZE else response_text
            logger.debug(message, limited_text)
    except Exception:
        pass


async def stream_openai_sse(packet: Dict[str, Any], completion_id: str, created_ts: int, model_id: str) -> AsyncGenerator[str, None]:
    """优化的流式SSE处理函数，减少重复代码和内存分配"""
    # 预构建常用结构，减少重复创建
    base_chunk = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created_ts,
        "model": model_id,
    }

    try:
        first = {**base_chunk, "choices": [{"index": 0, "delta": {"role": "assistant"}}]}
        _log_debug_json(logger, "[OpenAI Compat] 转换后的 SSE(emit): %s", first)
        yield f"data: {json.dumps(first, ensure_ascii=False)}\n\n"

        timeout = httpx.Timeout(HTTP_CLIENT_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)
        async with httpx.AsyncClient(
            http2=True,
            timeout=timeout,
            trust_env=True,
            limits=httpx.Limits(**HTTP_CLIENT_LIMITS)
        ) as client:
            def _do_stream():
                return client.stream(
                    "POST",
                    f"{BRIDGE_BASE_URL}/api/warp/send_stream_sse",
                    headers={"accept": "text/event-stream"},
                    json={"json_data": packet, "message_type": "warp.multi_agent.v1.Request"},
                )

            # 首次请求
            response_cm = _do_stream()
            async with response_cm as response:
                if response.status_code == 429:
                    try:
                        r = await client.post(f"{BRIDGE_BASE_URL}/api/auth/refresh")
                        logger.warning("[OpenAI Compat] Bridge returned 429. Tried JWT refresh -> HTTP %s", r.status_code)
                    except Exception as _e:
                        logger.warning("[OpenAI Compat] JWT refresh attempt failed after 429: %s", _e)
                    # 重试一次
                    response_cm2 = _do_stream()
                    async with response_cm2 as response2:
                        response = response2

                if response.status_code != 200:
                    error_text = await response.aread()
                    error_content = error_text.decode("utf-8") if error_text else ""
                    logger.error(f"[OpenAI Compat] Bridge HTTP error {response.status_code}: {error_content[:300]}")
                    raise RuntimeError(f"bridge error: {error_content}")

                await _process_stream_response(response, base_chunk, logger)
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
            if logger.isEnabledFor(10):  # DEBUG级别
                logger.debug("[OpenAI Compat] 转换后的 SSE(emit error): %s", json.dumps(error_chunk, ensure_ascii=False))
        except Exception:
            pass
        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"


async def _process_stream_response(response, base_chunk: Dict[str, Any], logger) -> None:
    """处理流式响应，优化的事件处理逻辑"""
    current = ""
    tool_calls_emitted = False

    async for line in response.aiter_lines():
        if line.startswith("data:"):
            payload = line[5:].strip()
            if not payload:
                continue
            # 打印接收到的 Protobuf SSE 原始事件片段（仅在调试模式）
            try:
                if logger.isEnabledFor(10):  # DEBUG级别
                    logger.debug("[OpenAI Compat] 接收到的 Protobuf SSE(data): %s", payload)
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

            # 打印接收到的 Protobuf 事件（解析后，仅在调试模式）
            try:
                if logger.isEnabledFor(10):  # DEBUG级别
                    logger.debug("[OpenAI Compat] 接收到的 Protobuf 事件(parsed): %s", json.dumps(event_data, ensure_ascii=False))
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
                            chunk = _create_text_chunk(base_chunk, text_content)
                            _log_debug_json(logger, "[OpenAI Compat] 转换后的 SSE(emit): %s", {"content": text_content})
                            yield chunk

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
                                chunk = _create_tool_calls_chunk(base_chunk, tool_call_id, call_mcp.get("name"), args_str)
                                _log_debug_json(logger, "[OpenAI Compat] 转换后的 SSE(emit tool_calls): %s", {"name": call_mcp.get("name")})
                                yield chunk
                                tool_calls_emitted = True
                            else:
                                agent_output = _get(message, "agent_output", "agentOutput") or {}
                                text_content = agent_output.get("text", "")
                                if text_content:
                                    chunk = _create_text_chunk(base_chunk, text_content)
                                    _log_debug_json(logger, "[OpenAI Compat] 转换后的 SSE(emit): %s", {"content": text_content})
                                    yield chunk

            if "finished" in event_data:
                finish_reason = "tool_calls" if tool_calls_emitted else "stop"
                chunk = _create_done_chunk(base_chunk, finish_reason)
                _log_debug_json(logger, "[OpenAI Compat] 转换后的 SSE(emit done): %s", {"finish_reason": finish_reason})
                yield chunk

    # 打印完成标记（仅在调试模式）
    try:
        if logger.isEnabledFor(10):  # DEBUG级别
            logger.debug("[OpenAI Compat] 转换后的 SSE(emit): [DONE]")
    except Exception:
        pass
    yield "data: [DONE]\n\n" 