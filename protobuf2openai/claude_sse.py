"""
Claude SSE Streaming Response Handler
"""
from __future__ import annotations

import json
import uuid
from typing import Any, AsyncGenerator, Dict, Optional, List

import httpx
from .logging import logger
from .config import BRIDGE_BASE_URL
from .helpers import _get
from .local_tools import execute_tool_locally


async def stream_claude_sse(
    packet: Dict[str, Any],
    message_id: str,
    created_ts: int,
    model_id: str,
    max_tokens: int,
    anthropic_beta: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Stream Claude-formatted SSE responses
    
    Claude SSE format:
    - event: message_start
    - event: content_block_start
    - event: content_block_delta
    - event: content_block_stop
    - event: message_delta
    - event: message_stop
    """
    
    try:
        # Send message_start event
        message_start = {
            "type": "message_start",
            "message": {
                "id": message_id,
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": model_id,
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0
                }
            }
        }
        yield f"event: message_start\ndata: {json.dumps(message_start)}\n\n"
        
        # Connect to bridge and stream
        timeout = httpx.Timeout(60.0)
        async with httpx.AsyncClient(http2=True, timeout=timeout, trust_env=True) as client:
            
            response_cm = client.stream(
                "POST",
                f"{BRIDGE_BASE_URL}/api/warp/send_stream_sse",
                headers={"accept": "text/event-stream"},
                json={"json_data": packet, "message_type": "warp.multi_agent.v1.Request"},
            )
            
            async with response_cm as response:
                if response.status_code == 429:
                    # Try to refresh JWT
                    try:
                        r = await client.post(f"{BRIDGE_BASE_URL}/api/auth/refresh", timeout=10.0)
                        logger.warning("[Claude SSE] Bridge returned 429. Tried JWT refresh -> HTTP %s", r.status_code)
                    except Exception as e:
                        logger.warning("[Claude SSE] JWT refresh attempt failed after 429: %s", e)
                    
                    # Retry once
                    response_cm2 = client.stream(
                        "POST",
                        f"{BRIDGE_BASE_URL}/api/warp/send_stream_sse",
                        headers={"accept": "text/event-stream"},
                        json={"json_data": packet, "message_type": "warp.multi_agent.v1.Request"},
                    )
                    async with response_cm2 as response2:
                        response = response2
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_content = error_text.decode("utf-8") if error_text else ""
                    logger.error(f"[Claude SSE] Bridge HTTP error {response.status_code}: {error_content[:300]}")
                    
                    # Send error event
                    error_event = {
                        "type": "error",
                        "error": {
                            "type": "api_error",
                            "message": f"Bridge error: {error_content}"
                        }
                    }
                    yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
                    return
                
                # Track state
                current = ""
                content_block_index = 0
                current_tool_calls: List[Dict[str, Any]] = []
                total_text = ""
                input_tokens = 0
                output_tokens = 0
                
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        payload = line[5:].strip()
                        if not payload:
                            continue
                        
                        logger.debug("[Claude SSE] Received data: %s", payload)
                        
                        if payload == "[DONE]":
                            break
                        
                        current += payload
                        continue
                    
                    if line.strip() == "" and current:
                        try:
                            ev = json.loads(current)
                        except Exception:
                            current = ""
                            continue
                        
                        current = ""
                        event_data = (ev or {}).get("parsed_data") or {}
                        
                        # Process Warp events
                        client_actions = _get(event_data, "client_actions", "clientActions")
                        if isinstance(client_actions, dict):
                            actions = _get(client_actions, "actions", "Actions") or []
                            
                            for action in actions:
                                # Handle text content
                                append_data = _get(action, "append_to_message_content", "appendToMessageContent")
                                if isinstance(append_data, dict):
                                    message = append_data.get("message", {})
                                    agent_output = _get(message, "agent_output", "agentOutput") or {}
                                    text_content = agent_output.get("text", "")
                                    
                                    if text_content:
                                        # Send content_block_start for first text
                                        if not total_text:
                                            block_start = {
                                                "type": "content_block_start",
                                                "index": content_block_index,
                                                "content_block": {
                                                    "type": "text",
                                                    "text": ""
                                                }
                                            }
                                            yield f"event: content_block_start\ndata: {json.dumps(block_start)}\n\n"
                                        
                                        # Send content_block_delta
                                        delta = {
                                            "type": "content_block_delta",
                                            "index": content_block_index,
                                            "delta": {
                                                "type": "text_delta",
                                                "text": text_content
                                            }
                                        }
                                        yield f"event: content_block_delta\ndata: {json.dumps(delta)}\n\n"
                                        
                                        total_text += text_content
                                        output_tokens += len(text_content.split())  # Rough estimate
                                
                                # Handle tool calls
                                messages_data = _get(action, "add_messages_to_task", "addMessagesToTask")
                                if isinstance(messages_data, dict):
                                    messages = messages_data.get("messages", [])
                                    
                                    for message in messages:
                                        tool_call = _get(message, "tool_call", "toolCall") or {}
                                        call_mcp = _get(tool_call, "call_mcp_tool", "callMcpTool") or {}
                                        
                                        if isinstance(call_mcp, dict) and call_mcp.get("name"):
                                            # Close previous text block if exists
                                            if total_text:
                                                block_stop = {
                                                    "type": "content_block_stop",
                                                    "index": content_block_index
                                                }
                                                yield f"event: content_block_stop\ndata: {json.dumps(block_stop)}\n\n"
                                                content_block_index += 1
                                                total_text = ""
                                            
                                            # Start tool use block
                                            tool_id = tool_call.get("tool_call_id") or f"toolu_{uuid.uuid4().hex[:16]}"
                                            tool_block_start = {
                                                "type": "content_block_start",
                                                "index": content_block_index,
                                                "content_block": {
                                                    "type": "tool_use",
                                                    "id": tool_id,
                                                    "name": call_mcp.get("name"),
                                                    "input": {}
                                                }
                                            }
                                            yield f"event: content_block_start\ndata: {json.dumps(tool_block_start)}\n\n"
                                            
                                            # Send tool input
                                            tool_input = call_mcp.get("args", {}) or {}
                                            tool_delta = {
                                                "type": "content_block_delta",
                                                "index": content_block_index,
                                                "delta": {
                                                    "type": "input_json_delta",
                                                    "partial_json": json.dumps(tool_input)
                                                }
                                            }
                                            yield f"event: content_block_delta\ndata: {json.dumps(tool_delta)}\n\n"
                                            
                                            # Stop tool block
                                            tool_block_stop = {
                                                "type": "content_block_stop",
                                                "index": content_block_index
                                            }
                                            yield f"event: content_block_stop\ndata: {json.dumps(tool_block_stop)}\n\n"
                                            
                                            content_block_index += 1
                                            current_tool_calls.append({
                                                "id": tool_id,
                                                "name": call_mcp.get("name"),
                                                "input": tool_input
                                            })
                                            
                                            # Execute tool locally and send result immediately
                                            tool_name = call_mcp.get("name")
                                            if tool_name in ["str_replace_based_edit_tool", "computer_20241022"]:
                                                try:
                                                    local_result = execute_tool_locally(tool_name, tool_input)
                                                    
                                                    # Send tool execution result in Claude standard format
                                                    if local_result.get("success"):
                                                        actual_content = local_result.get("content", local_result.get("message", "Operation completed"))
                                                        is_error = False
                                                    else:
                                                        actual_content = f"Error: {local_result.get('error', 'Operation failed')}"
                                                        is_error = True
                                                    
                                                    # Send tool_result as new content block
                                                    tool_result_start = {
                                                        "type": "content_block_start",
                                                        "index": content_block_index,
                                                        "content_block": {
                                                            "type": "tool_result",
                                                            "tool_use_id": tool_id,
                                                            "content": actual_content,
                                                            "is_error": is_error
                                                        }
                                                    }
                                                    yield f"event: content_block_start\ndata: {json.dumps(tool_result_start)}\n\n"
                                                    
                                                    # Send the actual content
                                                    tool_result_delta = {
                                                        "type": "content_block_delta",
                                                        "index": content_block_index,
                                                        "delta": {
                                                            "type": "tool_result_delta",
                                                            "content": actual_content
                                                        }
                                                    }
                                                    yield f"event: content_block_delta\ndata: {json.dumps(tool_result_delta)}\n\n"
                                                    
                                                    tool_result_stop = {
                                                        "type": "content_block_stop",
                                                        "index": content_block_index
                                                    }
                                                    yield f"event: content_block_stop\ndata: {json.dumps(tool_result_stop)}\n\n"
                                                    
                                                    content_block_index += 1
                                                    
                                                except Exception as e:
                                                    error_text = f"\n⚠️ Local execution error: {str(e)}"
                                                    # Send error as text block
                                                    error_delta = {
                                                        "type": "content_block_delta",
                                                        "index": content_block_index,
                                                        "delta": {
                                                            "type": "text_delta",
                                                            "text": error_text
                                                        }
                                                    }
                                                    yield f"event: content_block_delta\ndata: {json.dumps(error_delta)}\n\n"
                
                # Close any open content blocks
                if total_text:
                    block_stop = {
                        "type": "content_block_stop",
                        "index": content_block_index
                    }
                    yield f"event: content_block_stop\ndata: {json.dumps(block_stop)}\n\n"
                
                # Send message_delta with usage
                message_delta = {
                    "type": "message_delta",
                    "delta": {
                        "stop_reason": "end_turn",
                        "stop_sequence": None
                    },
                    "usage": {
                        "output_tokens": output_tokens
                    }
                }
                yield f"event: message_delta\ndata: {json.dumps(message_delta)}\n\n"
                
                # Send message_stop
                message_stop = {
                    "type": "message_stop"
                }
                yield f"event: message_stop\ndata: {json.dumps(message_stop)}\n\n"
    
    except Exception as e:
        logger.error(f"[Claude SSE] Streaming error: {e}")
        
        # Send error event
        error_event = {
            "type": "error",
            "error": {
                "type": "api_error",
                "message": str(e)
            }
        }
        yield f"event: error\ndata: {json.dumps(error_event)}\n\n"