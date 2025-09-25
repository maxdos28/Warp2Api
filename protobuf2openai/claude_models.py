from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field


class ClaudeContent(BaseModel):
    """Claude API content block"""
    type: Literal["text", "image", "image_url", "tool_use", "tool_result"] = "text"  # Support all Claude content types
    text: Optional[str] = None
    source: Optional[Dict[str, Any]] = None  # For image content
    image_url: Optional[Dict[str, Any]] = None  # For OpenAI format compatibility
    # Tool use fields
    id: Optional[str] = None  # Tool use ID
    name: Optional[str] = None  # Tool name
    input: Optional[Dict[str, Any]] = None  # Tool input/arguments
    # Tool result fields
    tool_use_id: Optional[str] = None  # Reference to tool_use.id
    content: Optional[Union[str, List[Dict[str, Any]]]] = None  # Tool result content
    is_error: Optional[bool] = None  # Whether tool execution failed


class ClaudeMessage(BaseModel):
    """Claude API message format"""
    role: Literal["user", "assistant", "tool"]  # Add tool role for tool results
    content: Union[str, List[Union[ClaudeContent, Dict[str, Any]]]]  # Allow mixed format for compatibility


class ClaudeMessagesRequest(BaseModel):
    """Claude API /v1/messages request format"""
    model: str
    max_tokens: int
    messages: List[ClaudeMessage]
    system: Optional[Union[str, List[Dict[str, Any]]]] = None
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
# 根据warp2protobuf/config/models.py中实际支持的模型进行映射
CLAUDE_MODEL_MAPPING = {
    # Claude 3.5 Sonnet系列 -> claude-4-sonnet (支持视觉)
    "claude-3-5-sonnet-20241022": "claude-4-sonnet",
    "claude-3-5-sonnet-20240620": "claude-4-sonnet",
    "claude-3-5-haiku-20241022": "claude-4-sonnet",

    # Claude 3 Opus系列 -> claude-4.1-opus (最强模型，支持视觉)
    "claude-3-opus-20240229": "claude-4.1-opus",

    # Claude 3 Sonnet/Haiku系列 -> claude-4-sonnet
    "claude-3-sonnet-20240229": "claude-4-sonnet",
    "claude-3-haiku-20240307": "claude-4-sonnet",

    # Claude 2系列 -> claude-4-opus (较强模型)
    "claude-2.1": "claude-4-opus",
    "claude-2.0": "claude-4-opus",

    # Claude Instant系列 -> claude-4-sonnet (快速模型)
    "claude-instant-1.2": "claude-4-sonnet",

    # 直接支持的内部模型名称（无需映射）
    "claude-4-sonnet": "claude-4-sonnet",
    "claude-4-opus": "claude-4-opus",
    "claude-4.1-opus": "claude-4.1-opus",
}


def get_internal_model_name(claude_model: str) -> str:
    """Convert Claude API model name to internal model name"""
    return CLAUDE_MODEL_MAPPING.get(claude_model, "claude-4-sonnet")


def claude_content_to_openai_content(content: Union[str, List[ClaudeContent]]) -> Union[str, List[Dict[str, Any]]]:
    """Convert Claude content format to OpenAI format (preserves images)"""
    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        # Check if there are any images (both Claude and OpenAI formats)
        has_images = any(block.type in ["image", "image_url"] for block in content)
        
        if not has_images:
            # Pure text content - return as string
            text_parts = []
            for block in content:
                if block.type == "text" and block.text:
                    text_parts.append(block.text)
            return "\n".join(text_parts)
        else:
            # Mixed content with images - return structured format
            content_blocks = []
            for block in content:
                if block.type == "text" and block.text:
                    content_blocks.append({
                        "type": "text",
                        "text": block.text
                    })
                elif block.type == "image" and block.source:
                    try:
                        # Validate image source format
                        source = block.source
                        if not isinstance(source, dict):
                            print(f"[Claude Compat] Invalid image source format: not a dict")
                            continue
                            
                        if source.get("type") != "base64":
                            print(f"[Claude Compat] Unsupported image source type: {source.get('type')}")
                            continue
                            
                        data = source.get("data", "")
                        if not data or not isinstance(data, str):
                            print(f"[Claude Compat] Invalid or missing image data")
                            continue
                            
                        # Basic validation of base64 data
                        try:
                            import base64
                            base64.b64decode(data, validate=True)
                        except Exception as e:
                            print(f"[Claude Compat] Invalid base64 image data: {e}")
                            continue
                        
                        # Validate media type
                        media_type = source.get("media_type", "")
                        if not media_type.startswith("image/"):
                            print(f"[Claude Compat] Invalid media type: {media_type}")
                            continue
                        
                        # Keep Claude image format for internal processing
                        content_blocks.append({
                            "type": "image",
                            "source": source
                        })
                        print(f"[Claude Compat] Successfully processed image: {media_type}, data length: {len(data)}")
                        
                    except Exception as e:
                        print(f"[Claude Compat] Error processing image content: {e}")
                        continue
                        
                elif block.type == "image_url" and block.image_url:
                    try:
                        # Handle OpenAI format - convert to Claude format for internal processing
                        image_url = block.image_url
                        url = image_url.get("url", "")
                        
                        if url.startswith("data:"):
                            # Parse data URL: data:image/png;base64,iVBORw0KGgo...
                            try:
                                header, data = url.split(",", 1)
                                media_type = header.split(":")[1].split(";")[0]

                                # 验证base64数据
                                import base64
                                base64.b64decode(data, validate=True)

                                # Convert to Claude format for consistent internal processing
                                content_blocks.append({
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": data
                                    }
                                })
                                print(f"[Claude Compat] Converted OpenAI image_url to Claude format: {media_type}, data length: {len(data)}")
                            except Exception as e:
                                print(f"[Claude Compat] Failed to parse data URL: {e}")
                                continue
                        else:
                            print(f"[Claude Compat] External image URLs not supported: {url}")
                            
                    except Exception as e:
                        print(f"[Claude Compat] Error processing OpenAI image_url: {e}")
                        continue
                        
            return content_blocks
    
    return ""


def openai_content_to_claude_content(content: str) -> List[ClaudeContent]:
    """Convert OpenAI text content to Claude content blocks"""
    if not content:
        return []
    
    return [ClaudeContent(type="text", text=content)]