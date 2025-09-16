from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field


class ClaudeContent(BaseModel):
    """Claude API content block"""
    type: Literal["text", "image"] = "text"
    text: Optional[str] = None
    source: Optional[Dict[str, Any]] = None  # For image content


class ClaudeMessage(BaseModel):
    """Claude API message format"""
    role: Literal["user", "assistant"]
    content: Union[str, List[ClaudeContent]]


class ClaudeMessagesRequest(BaseModel):
    """Claude API /v1/messages request format"""
    model: str
    max_tokens: int
    messages: List[ClaudeMessage]
    system: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(None, ge=1)
    stop_sequences: Optional[List[str]] = None
    stream: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = None


class ClaudeUsage(BaseModel):
    """Claude API usage statistics"""
    input_tokens: int
    output_tokens: int


class ClaudeMessagesResponse(BaseModel):
    """Claude API /v1/messages response format"""
    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: List[ClaudeContent]
    model: str
    stop_reason: Optional[Literal["end_turn", "max_tokens", "stop_sequence", "tool_use"]] = None
    stop_sequence: Optional[str] = None
    usage: ClaudeUsage


class ClaudeStreamEvent(BaseModel):
    """Claude API streaming event"""
    type: Literal[
        "message_start", 
        "content_block_start", 
        "content_block_delta", 
        "content_block_stop", 
        "message_delta", 
        "message_stop"
    ]
    message: Optional[ClaudeMessagesResponse] = None
    content_block: Optional[ClaudeContent] = None
    delta: Optional[Dict[str, Any]] = None
    usage: Optional[ClaudeUsage] = None
    index: Optional[int] = None


# Claude model mapping to internal models
CLAUDE_MODEL_MAPPING = {
    "claude-3-5-sonnet-20241022": "claude-4-sonnet",
    "claude-3-5-sonnet-20240620": "claude-4-sonnet", 
    "claude-3-5-haiku-20241022": "claude-4-sonnet",
    "claude-3-opus-20240229": "claude-4-opus",
    "claude-3-sonnet-20240229": "claude-4-sonnet",
    "claude-3-haiku-20240307": "claude-4-sonnet",
    "claude-2.1": "claude-4-opus",
    "claude-2.0": "claude-4-opus",
    "claude-instant-1.2": "claude-4-sonnet",
}


def get_internal_model_name(claude_model: str) -> str:
    """Convert Claude API model name to internal model name"""
    return CLAUDE_MODEL_MAPPING.get(claude_model, "claude-4-sonnet")


def claude_content_to_openai_content(content: Union[str, List[ClaudeContent]]) -> str:
    """Convert Claude content format to OpenAI text format"""
    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if block.type == "text" and block.text:
                text_parts.append(block.text)
            elif block.type == "image":
                text_parts.append("[Image content not supported in text conversion]")
        return "\n".join(text_parts)
    
    return ""


def openai_content_to_claude_content(content: str) -> List[ClaudeContent]:
    """Convert OpenAI text content to Claude content blocks"""
    if not content:
        return []
    
    return [ClaudeContent(type="text", text=content)]