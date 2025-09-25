from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, List, Optional

from .claude_models import (
    ClaudeMessagesRequest, 
    ClaudeMessage, 
    ClaudeContent,
    ClaudeMessagesResponse,
    ClaudeUsage,
    ClaudeStreamEvent,
    claude_content_to_openai_content,
    openai_content_to_claude_content,
    get_internal_model_name
)
from .models import ChatMessage, ChatCompletionsRequest
from .logging import logger


def claude_to_openai_request(claude_req: ClaudeMessagesRequest) -> ChatCompletionsRequest:
    """Convert Claude API request to OpenAI format"""
    
    # Convert Claude messages to OpenAI format
    openai_messages: List[ChatMessage] = []
    
    # Add system message if present
    if claude_req.system:
        # Handle both string and array formats for system
        if isinstance(claude_req.system, str):
            system_content = claude_req.system
        elif isinstance(claude_req.system, list):
            # Extract text from array format: [{"text": "content", "type": "text"}]
            text_parts = []
            for item in claude_req.system:
                if isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
                elif isinstance(item, str):
                    text_parts.append(item)
            system_content = "\n".join(text_parts)
        else:
            system_content = str(claude_req.system)
            
        if system_content.strip():
            openai_messages.append(ChatMessage(
                role="system",
                content=system_content
            ))
    
    # Convert Claude messages
    for msg in claude_req.messages:
        # Handle different message roles
        if msg.role == "assistant":
            # Check for tool_use content blocks in assistant messages
            tool_calls = []
            text_content = ""
            
            if isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            # Convert to OpenAI tool call format
                            tool_calls.append({
                                "id": block.get("id", str(uuid.uuid4())),
                                "type": "function",
                                "function": {
                                    "name": block.get("name", ""),
                                    "arguments": json.dumps(block.get("input", {}))
                                }
                            })
                        elif block.get("type") == "text":
                            text_content += block.get("text", "")
                    elif hasattr(block, 'type'):  # ClaudeContent object
                        if block.type == "tool_use":
                            tool_calls.append({
                                "id": getattr(block, 'id', None) or str(uuid.uuid4()),
                                "type": "function",
                                "function": {
                                    "name": getattr(block, 'name', "") or "",
                                    "arguments": json.dumps(getattr(block, 'input', {}) or {})
                                }
                            })
                        elif block.type == "text":
                            text_content += getattr(block, 'text', "") or ""
            else:
                # Single string content
                text_content = claude_content_to_openai_content(msg.content)
            
            # Create OpenAI message with tool_calls if present
            openai_msg = ChatMessage(
                role="assistant",
                content=text_content if text_content else None
            )
            if tool_calls:
                openai_msg.tool_calls = tool_calls
            
            openai_messages.append(openai_msg)
            
        else:
            # Handle user messages and other roles normally
            # Convert content (handles both text and images)
            openai_content = claude_content_to_openai_content(msg.content)
            
            # 确保图片内容被正确处理
            if isinstance(openai_content, list):
                print(f"[Claude Converter] Processing {len(openai_content)} content blocks")
                for i, block in enumerate(openai_content):
                    if isinstance(block, dict) and block.get("type") == "image":
                        source = block.get("source", {})
                        data_len = len(source.get("data", "")) if source.get("data") else 0
                        print(f"[Claude Converter] Image block {i}: {source.get('media_type')}, {data_len} chars")
            
            openai_messages.append(ChatMessage(
                role=msg.role,
                content=openai_content
            ))
    
    # Get internal model name
    internal_model = get_internal_model_name(claude_req.model)
    
    # Create OpenAI request
    openai_req = ChatCompletionsRequest(
        model=internal_model,
        messages=openai_messages,
        stream=claude_req.stream or False
    )
    
    logger.info(f"[Claude Compat] Converted Claude model '{claude_req.model}' to internal model '{internal_model}'")
    
    return openai_req


def openai_to_claude_response(
    openai_response: Dict[str, Any], 
    claude_model: str,
    request_id: str,
    tool_calls: List[Dict[str, Any]] = None
) -> ClaudeMessagesResponse:
    """Convert OpenAI response to Claude API format"""
    
    # Extract content from OpenAI response
    choice = openai_response.get("choices", [{}])[0]
    message = choice.get("message", {})
    content_text = message.get("content", "")
    
    # Create Claude content blocks
    content_blocks = []
    
    # Add text content if present
    if content_text and content_text.strip():
        content_blocks.extend(openai_content_to_claude_content(content_text))
    
    # Add tool calls if present
    if tool_calls:
        for tool_call in tool_calls:
            # Convert OpenAI tool call format to Claude tool_use content block
            function = tool_call.get("function", {})
            tool_name = function.get("name", "")
            tool_args = function.get("arguments", "{}")
            
            # Parse arguments if they're a string
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    tool_args = {}
            
            # Create tool_use content block
            tool_use_block = ClaudeContent(
                type="tool_use",
                id=tool_call.get("id", str(uuid.uuid4())),
                name=tool_name,
                input=tool_args
            )
            content_blocks.append(tool_use_block)
    
    # Ensure we have at least some content
    if not content_blocks:
        logger.warning("[Claude Compat] Empty content in OpenAI response, using fallback message")
        content_blocks = openai_content_to_claude_content("I apologize, but I encountered an issue generating a response. Please try again.")
    
    # Determine stop reason
    finish_reason = choice.get("finish_reason", "end_turn")
    if tool_calls:
        stop_reason = "tool_use"
    else:
        stop_reason_mapping = {
            "stop": "end_turn",
            "length": "max_tokens", 
            "tool_calls": "tool_use",
            "content_filter": "end_turn"
        }
        stop_reason = stop_reason_mapping.get(finish_reason, "end_turn")
    
    # Create usage info (mock for now, as OpenAI response doesn't always include token counts)
    usage = ClaudeUsage(
        input_tokens=0,  # Would need to calculate or extract from bridge response
        output_tokens=sum(len(str(block.dict()).split()) for block in content_blocks)  # Rough estimate
    )
    
    return ClaudeMessagesResponse(
        id=request_id,
        type="message",
        role="assistant", 
        content=content_blocks,
        model=claude_model,
        stop_reason=stop_reason,
        usage=usage
    )


def create_claude_stream_events(
    content_delta: str = None,
    is_start: bool = False,
    is_end: bool = False,
    claude_model: str = "claude-3-5-sonnet-20241022",
    request_id: str = None,
    tool_call: Dict[str, Any] = None,
    content_block_index: int = 0
) -> List[ClaudeStreamEvent]:
    """Create Claude streaming events from content delta or tool calls"""
    
    events = []
    
    if is_start:
        # Message start event
        events.append(ClaudeStreamEvent(
            type="message_start",
            message=ClaudeMessagesResponse(
                id=request_id or str(uuid.uuid4()),
                type="message",
                role="assistant",
                content=[],
                model=claude_model,
                usage=ClaudeUsage(input_tokens=0, output_tokens=0)
            )
        ))
    
    if tool_call:
        # Tool use content block start event
        function = tool_call.get("function", {})
        tool_args = function.get("arguments", "{}")
        
        # Parse arguments if they're a string
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except json.JSONDecodeError:
                tool_args = {}
        
        tool_use_block = ClaudeContent(
            type="tool_use",
            id=tool_call.get("id", str(uuid.uuid4())),
            name=function.get("name", ""),
            input=tool_args
        )
        
        events.append(ClaudeStreamEvent(
            type="content_block_start",
            index=content_block_index,
            content_block=tool_use_block
        ))
        
        # Tool use blocks don't have deltas, just stop immediately
        events.append(ClaudeStreamEvent(
            type="content_block_stop",
            index=content_block_index
        ))
        
    elif content_delta or (is_start and not tool_call):
        # Text content block
        if is_start and not tool_call:
            # Content block start event for text
            events.append(ClaudeStreamEvent(
                type="content_block_start",
                index=content_block_index,
                content_block=ClaudeContent(type="text", text="")
            ))
        
        if content_delta:
            # Content block delta event
            events.append(ClaudeStreamEvent(
                type="content_block_delta",
                index=content_block_index,
                delta={"type": "text_delta", "text": content_delta}
            ))
    
    if is_end:
        # Content block stop event (only if we had text content)
        if not tool_call:
            events.append(ClaudeStreamEvent(
                type="content_block_stop",
                index=content_block_index
            ))
        
        # Message stop event
        events.append(ClaudeStreamEvent(
            type="message_stop"
        ))
    
    return events


def extract_token_usage_from_bridge_response(bridge_response: Dict[str, Any]) -> ClaudeUsage:
    """Extract token usage from bridge response"""
    try:
        # Try to get token usage from context_window_info first
        parsed_events = bridge_response.get("parsed_events", [])
        total_input = 0
        total_output = 0
        
        for event in parsed_events:
            parsed_data = event.get("parsed_data", {})
            
            # Check for context_window_info
            if "finished" in parsed_data:
                finished = parsed_data["finished"]
                context_info = finished.get("context_window_info", {})
                if context_info:
                    # Extract from context window usage
                    usage_ratio = context_info.get("context_window_usage", 0.0)
                    if usage_ratio > 0:
                        # Estimate tokens based on usage ratio (rough approximation)
                        estimated_tokens = int(usage_ratio * 200000)  # Assuming 200k context window
                        total_input = max(total_input, estimated_tokens)
                        logger.info(f"[Claude Compat] Extracted context window usage: {usage_ratio:.6f} -> {estimated_tokens} tokens")
                
                # Check for token_usage array
                token_usage = finished.get("token_usage", [])
                if token_usage:
                    for usage in token_usage:
                        total_input += usage.get("total_input", 0)
                        total_output += usage.get("output", 0)
        
        # If no token usage found, try to estimate from response content
        if total_input == 0 and total_output == 0:
            response_text = bridge_response.get("response", "")
            if response_text:
                # Rough estimation: ~4 characters per token
                estimated_output = max(1, len(response_text) // 4)
                total_output = estimated_output
                
                # Estimate input tokens (rough)
                request_size = bridge_response.get("request_size", 0)
                if request_size > 0:
                    total_input = max(1, request_size // 4)
                else:
                    total_input = max(1, estimated_output // 2)  # Assume input is roughly half of output
                
                logger.info(f"[Claude Compat] Estimated tokens from content: input={total_input}, output={total_output}")
        
        # If we have input tokens but no output tokens, estimate output
        if total_input > 0 and total_output == 0:
            response_text = bridge_response.get("response", "")
            if response_text:
                total_output = max(1, len(response_text) // 4)
                logger.info(f"[Claude Compat] Estimated output tokens from content: {total_output}")
        
        return ClaudeUsage(
            input_tokens=max(1, total_input),  # Ensure at least 1 token
            output_tokens=max(1, total_output)  # Ensure at least 1 token
        )
    except Exception as e:
        logger.warning(f"[Claude Compat] Failed to extract token usage: {e}")
        # Return minimal usage instead of zero
        return ClaudeUsage(input_tokens=1, output_tokens=1)


def get_claude_stop_reason_from_bridge(bridge_response: Dict[str, Any]) -> str:
    """Extract stop reason from bridge response"""
    try:
        parsed_events = bridge_response.get("parsed_events", [])
        
        for event in parsed_events:
            parsed_data = event.get("parsed_data", {})
            if "finished" in parsed_data:
                finished = parsed_data["finished"]
                
                if "max_token_limit" in finished.get("reason", {}):
                    return "max_tokens"
                elif "done" in finished.get("reason", {}):
                    return "end_turn"
                elif "context_window_exceeded" in finished.get("reason", {}):
                    return "max_tokens"
        
        return "end_turn"
    except Exception:
        return "end_turn"