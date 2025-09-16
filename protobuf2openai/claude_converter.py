from __future__ import annotations

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
        openai_messages.append(ChatMessage(
            role="system",
            content=claude_req.system
        ))
    
    # Convert Claude messages
    for msg in claude_req.messages:
        openai_content = claude_content_to_openai_content(msg.content)
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
    request_id: str
) -> ClaudeMessagesResponse:
    """Convert OpenAI response to Claude API format"""
    
    # Extract content from OpenAI response
    choice = openai_response.get("choices", [{}])[0]
    message = choice.get("message", {})
    content_text = message.get("content", "")
    
    # Determine stop reason
    finish_reason = choice.get("finish_reason", "end_turn")
    stop_reason_mapping = {
        "stop": "end_turn",
        "length": "max_tokens", 
        "tool_calls": "tool_use",
        "content_filter": "end_turn"
    }
    stop_reason = stop_reason_mapping.get(finish_reason, "end_turn")
    
    # Create Claude content blocks
    content_blocks = openai_content_to_claude_content(content_text)
    
    # Create usage info (mock for now, as OpenAI response doesn't always include token counts)
    usage = ClaudeUsage(
        input_tokens=0,  # Would need to calculate or extract from bridge response
        output_tokens=len(content_text.split()) if content_text else 0  # Rough estimate
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
    content_delta: str,
    is_start: bool = False,
    is_end: bool = False,
    claude_model: str = "claude-3-5-sonnet-20241022",
    request_id: str = None
) -> List[ClaudeStreamEvent]:
    """Create Claude streaming events from content delta"""
    
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
        
        # Content block start event
        events.append(ClaudeStreamEvent(
            type="content_block_start",
            index=0,
            content_block=ClaudeContent(type="text", text="")
        ))
    
    if content_delta:
        # Content block delta event
        events.append(ClaudeStreamEvent(
            type="content_block_delta",
            index=0,
            delta={"type": "text_delta", "text": content_delta}
        ))
    
    if is_end:
        # Content block stop event
        events.append(ClaudeStreamEvent(
            type="content_block_stop",
            index=0
        ))
        
        # Message stop event
        events.append(ClaudeStreamEvent(
            type="message_stop"
        ))
    
    return events


def extract_token_usage_from_bridge_response(bridge_response: Dict[str, Any]) -> ClaudeUsage:
    """Extract token usage from bridge response"""
    try:
        parsed_events = bridge_response.get("parsed_events", [])
        total_input = 0
        total_output = 0
        
        for event in parsed_events:
            parsed_data = event.get("parsed_data", {})
            if "finished" in parsed_data:
                finished = parsed_data["finished"]
                token_usage = finished.get("token_usage", [])
                
                for usage in token_usage:
                    total_input += usage.get("total_input", 0)
                    total_output += usage.get("output", 0)
        
        return ClaudeUsage(
            input_tokens=total_input,
            output_tokens=total_output
        )
    except Exception as e:
        logger.warning(f"[Claude Compat] Failed to extract token usage: {e}")
        return ClaudeUsage(input_tokens=0, output_tokens=0)


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