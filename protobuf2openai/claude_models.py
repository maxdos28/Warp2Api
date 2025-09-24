"""
Claude API Models and Types
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum


class ContentType(str, Enum):
    """Claude content block types"""
    TEXT = "text"
    IMAGE = "image"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class TextContent(BaseModel):
    """Text content block"""
    type: Literal["text"] = "text"
    text: str


class ImageContent(BaseModel):
    """Image content block"""
    type: Literal["image"] = "image"
    source: Dict[str, Any]  # {"type": "base64", "media_type": "...", "data": "..."}


class ToolUseContent(BaseModel):
    """Tool use content block"""
    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: Dict[str, Any]


class ToolResultContent(BaseModel):
    """Tool result content block"""
    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: Union[str, List[Dict[str, Any]]]
    is_error: Optional[bool] = False


ContentBlock = Union[TextContent, ImageContent, ToolUseContent, ToolResultContent]


class ClaudeMessage(BaseModel):
    """Claude message format"""
    role: Literal["user", "assistant"]
    content: Union[str, List[ContentBlock]]
    name: Optional[str] = None


class ClaudeTool(BaseModel):
    """Claude tool definition"""
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any]


class ClaudeMessagesRequest(BaseModel):
    """Claude Messages API request format"""
    model: str
    messages: List[ClaudeMessage]
    max_tokens: int = Field(default=4096, description="Required for Claude API")
    system: Optional[str] = None
    tools: Optional[List[ClaudeTool]] = None
    tool_choice: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stream: Optional[bool] = False
    stop_sequences: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


# Claude 内置工具定义
COMPUTER_USE_TOOL = {
    "name": "computer_20241022",
    "description": "Use a computer with screen, keyboard, and mouse. Can take screenshots, click at coordinates, type text, scroll pages, and press keys.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["screenshot", "click", "type", "scroll", "key"],
                "description": "The action to perform: screenshot (take a screenshot), click (click at coordinates), type (type text), scroll (scroll the page), key (press a key)"
            },
            "coordinate": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "[x, y] coordinates for click action"
            },
            "text": {
                "type": "string",
                "description": "Text to type when action is 'type'"
            },
            "direction": {
                "type": "string",
                "enum": ["up", "down", "left", "right"],
                "description": "Scroll direction when action is 'scroll'"
            },
            "key": {
                "type": "string",
                "description": "Key to press when action is 'key' (e.g., 'Return', 'Tab', 'Escape')"
            }
        },
        "required": ["action"]
    }
}

CODE_EDITOR_TOOL = {
    "name": "str_replace_based_edit_tool",
    "description": "Edit files using string replacement. Can view file contents, create new files, replace text in files, and undo edits.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["view", "create", "str_replace", "undo_edit"],
                "description": "The command to execute"
            },
            "path": {
                "type": "string",
                "description": "Path to the file"
            },
            "file_text": {
                "type": "string",
                "description": "Content for create command"
            },
            "old_str": {
                "type": "string",
                "description": "String to replace"
            },
            "new_str": {
                "type": "string",
                "description": "Replacement string"
            },
            "view_range": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "[start_line, end_line] for view command"
            }
        },
        "required": ["command"]
    }
}


# Claude 模型映射 - 从 Claude API 名称到 Warp 支持的名称
CLAUDE_MODEL_MAPPING = {
    # Claude API 模型到 Warp 模型的映射
    "claude-3-5-sonnet-20241022": "claude-4-sonnet",
    "claude-3-5-sonnet-20240620": "claude-4-sonnet",
    "claude-3-opus-20240229": "claude-4-opus",
    "claude-3-sonnet-20240229": "claude-4-sonnet",
    "claude-3-haiku-20240307": "claude-4-sonnet",
    
    # Warp 原生模型名称保持不变
    "claude-4-sonnet": "claude-4-sonnet",
    "claude-4-opus": "claude-4-opus",
    "claude-4.1-opus": "claude-4.1-opus",
}


def get_claude_model(model: str) -> str:
    """获取对应的 Warp 模型名称"""
    return CLAUDE_MODEL_MAPPING.get(model, "claude-4-sonnet")