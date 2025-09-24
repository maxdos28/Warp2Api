"""
Claude Messages API Router
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, Optional, Union

import requests
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import StreamingResponse

from .logging import logger
from .claude_models import (
    ClaudeMessagesRequest, ClaudeMessage, ClaudeTool,
    TextContent, ToolUseContent, ToolResultContent,
    COMPUTER_USE_TOOL, CODE_EDITOR_TOOL,
    get_claude_model
)
from .models import ChatMessage
from .helpers import normalize_content_to_list, segments_to_text
from .packets import packet_template, map_history_to_warp_messages, attach_user_and_tools_to_inputs
from .state import STATE
from .config import BRIDGE_BASE_URL
from .bridge import initialize_once
from .claude_sse import stream_claude_sse
from .auth import authenticate_request


claude_router = APIRouter()


def convert_claude_to_openai_messages(claude_messages: List[ClaudeMessage], system: Optional[str] = None) -> List[ChatMessage]:
    """Convert Claude messages to OpenAI format"""
    openai_messages = []
    
    # Add system message if provided
    if system:
        openai_messages.append(ChatMessage(role="system", content=system))
    
    for msg in claude_messages:
        if isinstance(msg.content, str):
            # Simple text message
            openai_messages.append(ChatMessage(
                role=msg.role,
                content=msg.content,
                name=msg.name
            ))
        else:
            # Complex content blocks
            text_parts = []
            tool_calls = []
            tool_results = []
            
            for block in msg.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": json.dumps(block.input)
                        }
                    })
                elif block.type == "tool_result":
                    # Collect tool results to process together
                    result_content = block.content if isinstance(block.content, str) else json.dumps(block.content)
                    tool_results.append({
                        "content": result_content,
                        "tool_call_id": block.tool_use_id
                    })
            
            # Add tool results as separate user messages
            for result in tool_results:
                openai_messages.append(ChatMessage(
                    role="user",
                    content=result["content"],
                    tool_call_id=result["tool_call_id"]
                ))
            
            # Create message with text and tool calls
            if text_parts or tool_calls:
                message = ChatMessage(
                    role=msg.role,
                    content=" ".join(text_parts) if text_parts else None,
                    name=msg.name
                )
                if tool_calls:
                    message.tool_calls = tool_calls
                openai_messages.append(message)
    
    return openai_messages


def convert_claude_tools(claude_tools: Optional[List[ClaudeTool]]) -> Optional[List[Dict[str, Any]]]:
    """Convert Claude tools to OpenAI format"""
    if not claude_tools:
        return None
    
    openai_tools = []
    for tool in claude_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema
            }
        })
    
    return openai_tools


def add_claude_builtin_tools(tools: Optional[List[ClaudeTool]], beta_header: Optional[str]) -> List[ClaudeTool]:
    """Add Claude built-in tools based on beta header"""
    if tools is None:
        tools = []
    
    if beta_header:
        beta_features = [f.strip() for f in beta_header.split(",")]
        
        if "computer-use-2024-10-22" in beta_features:
            # Add computer use tool if not already present
            if not any(t.name == "computer_20241022" for t in tools):
                tools.append(ClaudeTool(**COMPUTER_USE_TOOL))
        
        if "code-execution-2025-08-25" in beta_features:
            # Add code editor tool if not already present
            if not any(t.name == "str_replace_based_edit_tool" for t in tools):
                tools.append(ClaudeTool(**CODE_EDITOR_TOOL))
    
    return tools


@claude_router.get("/v1/messages/models")
async def list_claude_models():
    """List available Claude models"""
    models = [
        {"id": "claude-3-opus-20240229", "object": "model", "created": 1709251200, "owned_by": "anthropic"},
        {"id": "claude-3-sonnet-20240229", "object": "model", "created": 1709251200, "owned_by": "anthropic"},
        {"id": "claude-3-haiku-20240307", "object": "model", "created": 1709856000, "owned_by": "anthropic"},
        {"id": "claude-3-5-sonnet-20241022", "object": "model", "created": 1729555200, "owned_by": "anthropic"},
        {"id": "claude-3-5-sonnet-20240620", "object": "model", "created": 1718841600, "owned_by": "anthropic"},
    ]
    return {"object": "list", "data": models}


@claude_router.post("/v1/messages")
async def claude_messages(
    req: ClaudeMessagesRequest,
    request: Request,
    anthropic_version: Optional[str] = Header(None),
    anthropic_beta: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
):
    """Claude Messages API endpoint"""
    
    # Authentication
    if request:
        await authenticate_request(request)
    
    try:
        initialize_once()
    except Exception as e:
        logger.warning(f"[Claude API] initialize_once failed or skipped: {e}")
    
    if not req.messages:
        raise HTTPException(400, "messages cannot be empty")
    
    # Log received request
    logger.info("[Claude API] Received Messages request: %s", json.dumps(req.dict(), ensure_ascii=False))
    logger.info("[Claude API] Headers - anthropic-version: %s, anthropic-beta: %s", anthropic_version, anthropic_beta)
    
    # Add built-in tools based on beta header
    req.tools = add_claude_builtin_tools(req.tools, anthropic_beta)
    
    # Convert Claude messages to OpenAI format
    openai_messages = convert_claude_to_openai_messages(req.messages, req.system)
    
    # Convert tools to OpenAI format
    openai_tools = convert_claude_tools(req.tools)
    
    # Map model name
    warp_model = get_claude_model(req.model)
    
    # Create packet for Warp
    task_id = STATE.baseline_task_id or str(uuid.uuid4())
    packet = packet_template()
    packet["task_context"] = {
        "tasks": [{
            "id": task_id,
            "description": "",
            "status": {"in_progress": {}},
            "messages": map_history_to_warp_messages(openai_messages, task_id, None, False),
        }],
        "active_task_id": task_id,
    }
    
    packet.setdefault("settings", {}).setdefault("model_config", {})
    packet["settings"]["model_config"]["base"] = warp_model
    packet["settings"]["model_config"]["coding"] = "auto"
    packet["settings"]["model_config"]["planning"] = "gpt-5 (high reasoning)"
    packet["settings"]["model_config"]["vision_enabled"] = True  # 启用vision
    
    # 启用vision相关设置
    packet["settings"]["web_context_retrieval_enabled"] = True
    packet["settings"]["warp_drive_context_enabled"] = True
    packet["settings"]["vision_enabled"] = True
    packet["settings"]["multimodal_enabled"] = True
    
    if STATE.conversation_id:
        packet.setdefault("metadata", {})["conversation_id"] = STATE.conversation_id
    
    # Attach system prompt if present
    attach_user_and_tools_to_inputs(packet, openai_messages, req.system)
    
    # Add tools to packet
    if openai_tools:
        mcp_tools = []
        for tool in openai_tools:
            if tool["type"] == "function":
                mcp_tools.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"].get("description", ""),
                    "input_schema": tool["function"].get("parameters", {}),
                })
        if mcp_tools:
            packet.setdefault("mcp_context", {}).setdefault("tools", []).extend(mcp_tools)
    
    # Add temperature and other parameters
    if req.temperature is not None:
        packet["settings"]["model_config"]["temperature"] = req.temperature
    if req.top_p is not None:
        packet["settings"]["model_config"]["top_p"] = req.top_p
    if req.top_k is not None:
        packet["settings"]["model_config"]["top_k"] = req.top_k
    
    logger.info("[Claude API] Sending to Warp: %s", json.dumps(packet, ensure_ascii=False))
    
    # Generate response
    created_ts = int(time.time())
    message_id = f"msg_{uuid.uuid4().hex[:24]}"
    
    if req.stream:
        async def _stream():
            async for chunk in stream_claude_sse(
                packet, message_id, created_ts, req.model, 
                req.max_tokens, anthropic_beta
            ):
                yield chunk
        
        return StreamingResponse(
            _stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Anthropic-Version": anthropic_version or "2023-06-01"
            }
        )
    
    # Non-streaming response - collect from streaming endpoint for full data
    try:
        # Use streaming endpoint to get full response including tool calls
        import httpx
        
        content = []
        text_buffer = ""
        tool_calls = []
        
        with httpx.Client(timeout=60.0) as client:
            with client.stream(
                "POST",
                f"{BRIDGE_BASE_URL}/api/warp/send_stream_sse",
                headers={"accept": "text/event-stream"},
                json={"json_data": packet, "message_type": "warp.multi_agent.v1.Request"},
            ) as response:
                if response.status_code != 200:
                    raise HTTPException(response.status_code, f"Bridge error")
                
                for line in response.iter_lines():
                    if line.startswith("data:"):
                        payload = line[5:].strip()
                        if payload == "[DONE]":
                            break
                        try:
                            event = json.loads(payload)
                            parsed_data = event.get("parsed_data", {})
                            
                            # Extract text and tool calls from parsed data
                            client_actions = parsed_data.get("client_actions", {})
                            if client_actions:
                                actions = client_actions.get("actions", [])
                                for action in actions:
                                    # Text content
                                    append_data = action.get("append_to_message_content", {})
                                    if append_data:
                                        message = append_data.get("message", {})
                                        agent_output = message.get("agent_output", {})
                                        text = agent_output.get("text", "")
                                        if text:
                                            text_buffer += text
                                    
                                    # Tool calls
                                    messages_data = action.get("add_messages_to_task", {})
                                    if messages_data:
                                        messages = messages_data.get("messages", [])
                                        for msg in messages:
                                            tool_call = msg.get("tool_call", {})
                                            call_mcp = tool_call.get("call_mcp_tool", {})
                                            if call_mcp and call_mcp.get("name"):
                                                tool_calls.append({
                                                    "type": "tool_use",
                                                    "id": tool_call.get("tool_call_id", f"toolu_{uuid.uuid4().hex[:16]}"),
                                                    "name": call_mcp.get("name"),
                                                    "input": call_mcp.get("args", {})
                                                })
                        except:
                            pass
        
        # Build content array
        if text_buffer:
            content.append({"type": "text", "text": text_buffer})
        
        # Add tool calls
        content.extend(tool_calls)
        
        # If no content at all, add default message
        if not content:
            content.append({"type": "text", "text": "No response received from Warp"})
        
        return {
            "id": message_id,
            "type": "message",
            "role": "assistant",
            "content": content,
            "model": req.model,
            "stop_reason": "tool_calls" if tool_calls else "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50
            }
        }
    
    except Exception as e:
        logger.error(f"[Claude API] Bridge request failed: {e}")
        raise HTTPException(502, f"Bridge error: {str(e)}")