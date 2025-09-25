"""
Claude 风格的 SSE 流式响应处理
"""
from __future__ import annotations

import json
import uuid
from typing import Any, AsyncGenerator, Dict

import requests
from .config import BRIDGE_BASE_URL
from .logging import logger


async def stream_claude_sse(packet: Dict[str, Any], message_id: str, model: str, input_text: str = "") -> AsyncGenerator[str, None]:
    """生成 Claude 风格的 SSE 流式响应"""
    
    # 发送流式请求到 bridge
    def _post_stream():
        return requests.post(
            f"{BRIDGE_BASE_URL}/api/warp/send_stream_sse",
            json={"json_data": packet, "message_type": "warp.multi_agent.v1.Request"},
            stream=True,
            timeout=(5.0, 180.0),
        )
    
    try:
        resp = _post_stream()
        if resp.status_code == 429:
            # 尝试刷新 JWT token
            try:
                r = requests.post(f"{BRIDGE_BASE_URL}/api/auth/refresh", timeout=10.0)
                logger.warning("[Claude Streaming] Bridge returned 429. Tried JWT refresh -> HTTP %s", getattr(r, 'status_code', 'N/A'))
            except Exception as e:
                logger.warning("[Claude Streaming] JWT refresh attempt failed after 429: %s", e)
            resp = _post_stream()
        
        if resp.status_code != 200:
            error_msg = f"Bridge error: HTTP {resp.status_code}"
            yield f"event: error\ndata: {json.dumps({'error': {'type': 'api_error', 'message': error_msg}})}\n\n"
            return
        
        # 发送开始事件
        start_event = {
            "type": "message_start",
            "message": {
                "id": message_id,
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": model,
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }
        }
        yield f"event: message_start\ndata: {json.dumps(start_event)}\n\n"
        
        # 发送内容开始事件
        content_start_event = {
            "type": "content_block_start",
            "index": 0,
            "content_block": {
                "type": "text",
                "text": ""
            }
        }
        yield f"event: content_block_start\ndata: {json.dumps(content_start_event)}\n\n"
        
        # 处理流式响应
        accumulated_text = ""
        
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.strip():
                continue
            
            # 解析 SSE 数据
            if line.startswith("data: "):
                try:
                    data_json = line[6:]  # 移除 "data: " 前缀
                    if data_json.strip() == "[DONE]":
                        break
                    
                    event_data = json.loads(data_json)
                    
                    # 提取文本内容
                    text_delta = ""
                    if "response_delta" in event_data:
                        text_delta = event_data["response_delta"]
                    elif "parsed_data" in event_data:
                        parsed = event_data["parsed_data"]
                        if isinstance(parsed, dict) and "response" in parsed:
                            # 这是完整响应，计算增量
                            full_text = parsed["response"]
                            if full_text.startswith(accumulated_text):
                                text_delta = full_text[len(accumulated_text):]
                            else:
                                text_delta = full_text
                    
                    if text_delta:
                        accumulated_text += text_delta
                        
                        # 发送文本增量事件
                        delta_event = {
                            "type": "content_block_delta",
                            "index": 0,
                            "delta": {
                                "type": "text_delta",
                                "text": text_delta
                            }
                        }
                        yield f"event: content_block_delta\ndata: {json.dumps(delta_event)}\n\n"
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.warning("[Claude Streaming] Error processing line: %s", e)
                    continue
        
        # 发送内容结束事件
        content_stop_event = {
            "type": "content_block_stop",
            "index": 0
        }
        yield f"event: content_block_stop\ndata: {json.dumps(content_stop_event)}\n\n"
        
        # 发送消息结束事件
        message_stop_event = {
            "type": "message_delta",
            "delta": {
                "stop_reason": "end_turn",
                "stop_sequence": None
            },
            "usage": {
                "output_tokens": len(accumulated_text.split())  # 简单的 token 计算
            }
        }
        yield f"event: message_delta\ndata: {json.dumps(message_stop_event)}\n\n"
        
        # 最终的消息结束事件
        final_stop_event = {
            "type": "message_stop"
        }
        yield f"event: message_stop\ndata: {json.dumps(final_stop_event)}\n\n"
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        logger.error("[Claude Streaming] Network error: %s", e)
        yield f"event: error\ndata: {json.dumps({'error': {'type': 'api_error', 'message': error_msg}})}\n\n"
    except Exception as e:
        error_msg = f"Internal error: {str(e)}"
        logger.error("[Claude Streaming] Internal error: %s", e)
        yield f"event: error\ndata: {json.dumps({'error': {'type': 'api_error', 'message': error_msg}})}\n\n"