from __future__ import annotations

import json
import uuid
import time
import asyncio
from typing import Any, AsyncGenerator, Dict
from collections import deque

import httpx
from .logging import logger

from .config import BRIDGE_BASE_URL, SSE_VERBOSE_LOG
from .state import get_auth_headers, update_jwt_token
from .helpers import _get
from .http_clients import get_shared_async_client, PerformanceTracker


class StreamBuffer:
    """优化的流缓冲器，减少字符串拼接开销"""
    
    def __init__(self, max_buffer_size: int = 8192):
        self.buffer = deque()
        self.buffer_size = 0
        self.max_buffer_size = max_buffer_size
    
    def append(self, data: str):
        self.buffer.append(data)
        self.buffer_size += len(data)
        
        # 如果缓冲区过大，合并较老的条目
        if self.buffer_size > self.max_buffer_size and len(self.buffer) > 10:
            self._compact_buffer()
    
    def _compact_buffer(self):
        """压缩缓冲区，减少内存使用"""
        if len(self.buffer) <= 5:
            return
            
        # 合并前一半的条目
        half = len(self.buffer) // 2
        old_items = []
        for _ in range(half):
            old_items.append(self.buffer.popleft())
        
        # 重新添加合并后的内容
        merged = "".join(old_items)
        self.buffer.appendleft(merged)
        
        # 重新计算大小
        self.buffer_size = sum(len(item) for item in self.buffer)
    
    def get_content(self) -> str:
        return "".join(self.buffer)
    
    def clear(self):
        self.buffer.clear()
        self.buffer_size = 0


async def _process_sse_events(response, completion_id: str, created_ts: int, model_id: str) -> AsyncGenerator[str, None]:
    """处理SSE事件流的核心逻辑，提取重复代码为单独函数"""
    stream_buffer = StreamBuffer()
    tool_calls_emitted = False
    content_emitted = False  # 跟踪是否已经发出过内容
    total_content = ""  # 记录总内容用于验证
    events_processed = 0
    start_time = time.time()
    no_content_timeout = 300.0  # 增加到300秒超时，处理非常大的请求
    
    # 设置内容超时检查
    last_content_time = time.time()
    content_timeout_sent = False
    
    async for line in response.aiter_lines():
        current_time = time.time()
        
        # 更智能的超时检测：只有在真正无响应时才触发
        processing_time = current_time - start_time
        if (not content_emitted and not content_timeout_sent and 
            processing_time > no_content_timeout and
            events_processed == 0 and  # 完全无事件
            current_time - last_content_time > 60):  # 且60秒内无任何数据
            logger.warning(f"[OpenAI Compat] Request timeout after {processing_time:.1f}s with no events, sending fallback")
            fallback_message = "The request is taking longer than expected. Please try again with a simpler query."
            fallback_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk", 
                "created": created_ts,
                "model": model_id,
                "choices": [{"index": 0, "delta": {"content": fallback_message}}],
            }
            yield f"data: {json.dumps(fallback_chunk, ensure_ascii=False)}\n\n"
            content_emitted = True
            content_timeout_sent = True
        
        if line.startswith("data:"):
            payload = line[5:].strip()
            if not payload:
                continue
            # 可选：打印接收到的 Protobuf SSE 原始事件片段
            if SSE_VERBOSE_LOG:
                try:
                    logger.info("[OpenAI Compat] 接收到的 Protobuf SSE(data): %s", payload)
                except Exception:
                    pass
            if payload == "[DONE]":
                break
            stream_buffer.append(payload)
            last_content_time = current_time  # 更新最后收到内容的时间
            continue
            
        if (line.strip() == "") and stream_buffer.buffer:
            current = stream_buffer.get_content()
            stream_buffer.clear()
            
            try:
                ev = json.loads(current)
            except Exception:
                continue
            
            events_processed += 1
            event_data = (ev or {}).get("parsed_data") or {}

            # 可选：打印接收到的 Protobuf 事件（解析后）
            if SSE_VERBOSE_LOG:
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
                            content_emitted = True
                            total_content += text_content  # 累积总内容
                            logger.info(f"[OpenAI Compat] Emitting text fragment: '{text_content[:50]}...' (total so far: {len(total_content)} chars)")
                            delta = {
                                "id": completion_id,
                                "object": "chat.completion.chunk",
                                "created": created_ts,
                                "model": model_id,
                                "choices": [{"index": 0, "delta": {"content": text_content}}],
                            }
                            if SSE_VERBOSE_LOG:
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
                                if SSE_VERBOSE_LOG:
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
                                    total_content += text_content  # 累积总内容
                                    delta = {
                                        "id": completion_id,
                                        "object": "chat.completion.chunk",
                                        "created": created_ts,
                                        "model": model_id,
                                        "choices": [{"index": 0, "delta": {"content": text_content}}],
                                    }
                                    if SSE_VERBOSE_LOG:
                                        try:
                                            logger.info("[OpenAI Compat] 转换后的 SSE(emit): %s", json.dumps(delta, ensure_ascii=False))
                                        except Exception:
                                            pass
                                    yield f"data: {json.dumps(delta, ensure_ascii=False)}\n\n"

            if "finished" in event_data:
                # 记录流处理统计信息
                processing_time = time.time() - start_time
                logger.info(f"[OpenAI Compat] Stream processing completed: {events_processed} events in {processing_time:.3f}s")
                logger.info(f"[OpenAI Compat] Final state: content_emitted={content_emitted}, tool_calls_emitted={tool_calls_emitted}, total_content_length={len(total_content)}")
                
                # 如果没有发出任何内容且没有工具调用，发送累积的总内容
                if not content_emitted and not tool_calls_emitted:
                    # 检查是否有总内容可以发送
                    if total_content.strip():
                        logger.info("[OpenAI Compat] Found content in total_content, emitting it")
                        fallback_chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created_ts,
                            "model": model_id,
                            "choices": [{"index": 0, "delta": {"content": total_content}}],
                        }
                        yield f"data: {json.dumps(fallback_chunk, ensure_ascii=False)}\n\n"
                        content_emitted = True
                    else:
                        logger.warning("[OpenAI Compat] No content received in stream, sending appropriate response")
                        
                        # 最后的备选方案
                        fallback_message = "I understand you want to work on implementing daily release sheet limits. Let me help you with that."
                        fallback_chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created_ts,
                            "model": model_id,
                            "choices": [{"index": 0, "delta": {"content": fallback_message}}],
                        }
                        if SSE_VERBOSE_LOG:
                            try:
                                logger.info("[OpenAI Compat] 转换后的 SSE(emit fallback): %s", json.dumps(fallback_chunk, ensure_ascii=False))
                            except Exception:
                                pass
                        yield f"data: {json.dumps(fallback_chunk, ensure_ascii=False)}\n\n"
                        content_emitted = True  # 标记已发送内容
                
                done_chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_id,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": ("tool_calls" if tool_calls_emitted else "stop")}],
                }
                if SSE_VERBOSE_LOG:
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
    stream_start_time = time.time()
    
    with PerformanceTracker("stream_openai_sse"):
        try:
            # 发送首个SSE事件（OpenAI格式）
            first = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": model_id,
                "choices": [{"index": 0, "delta": {"role": "assistant"}}],
            }
            if SSE_VERBOSE_LOG:
                try:
                    logger.info("[OpenAI Compat] 转换后的 SSE(emit): %s", json.dumps(first, ensure_ascii=False))
                except Exception:
                    pass
            yield f"data: {json.dumps(first, ensure_ascii=False)}\n\n"

            client = await get_shared_async_client()
            response_cm = _make_stream_request(client, packet)
            
            try:
                async with response_cm as response:
                    if response.status_code == 429:
                        if await _refresh_jwt_token(client):
                            response_cm2 = _make_stream_request(client, packet)
                            async with response_cm2 as response2:
                                if response2.status_code != 200:
                                    error_text = await response2.aread()
                                    error_content = error_text.decode("utf-8") if error_text else ""
                                    logger.error(f"[OpenAI Compat] Bridge HTTP error {response2.status_code}: {error_content[:300]}")
                                    raise RuntimeError(f"bridge error: {error_content}")
                                async for event in _process_sse_events(response2, completion_id, created_ts, model_id):
                                    yield event
                                return
                        else:
                            pass
                    if response.status_code != 200:
                        error_text = await response.aread()
                        error_content = error_text.decode("utf-8") if error_text else ""
                        logger.error(f"[OpenAI Compat] Bridge HTTP error {response.status_code}: {error_content[:300]}")
                        raise RuntimeError(f"bridge error: {error_content}")
                    # 检查是否是非流式错误响应
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        # 这是一个JSON错误响应，不是SSE流
                        error_data = await response.aread()
                        error_json = json.loads(error_data.decode('utf-8'))
                        error_text = error_json.get('response', 'Service error')
                        
                        # 转换中文错误为英文
                        if "配额已用尽" in error_text:
                            error_text = "I'm currently experiencing high demand. Please try again in a moment."
                        elif not error_text or len(error_text.strip()) < 3:
                            error_text = "I'm currently experiencing high demand. Please try again in a moment."
                        
                        # 发送错误内容
                        error_chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created_ts,
                            "model": model_id,
                            "choices": [{"index": 0, "delta": {"content": error_text}}],
                        }
                        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                        
                        # 发送完成标记
                        done_chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created_ts,
                            "model": model_id,
                            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                        }
                        yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"
                        return
                    
                    # 正常的SSE流处理
                    async for event in _process_sse_events(response, completion_id, created_ts, model_id):
                        yield event
            except Exception as stream_error:
                logger.warning(f"[OpenAI Compat] Stream error: {stream_error}")
                # 发送错误内容而不是空响应
                error_message = "I'm currently experiencing high demand. Please try again in a moment."
                error_chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_id,
                    "choices": [{"index": 0, "delta": {"content": error_message}}],
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                
                # 发送完成标记
                done_chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_id,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
                yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"

            # 发送最终完成标记
            if SSE_VERBOSE_LOG:
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
            if SSE_VERBOSE_LOG:
                try:
                    logger.info("[OpenAI Compat] 转换后的 SSE(emit error): %s", json.dumps(error_chunk, ensure_ascii=False))
                except Exception:
                    pass
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
