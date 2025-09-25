from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: Optional[Union[str, List[Dict[str, Any]]]] = ""
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    name: Optional[str] = None


class OpenAIFunctionDef(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class OpenAITool(BaseModel):
    type: str = Field("function", description="Only 'function' is supported")
    function: OpenAIFunctionDef


class ChatCompletionsRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    tools: Optional[List[OpenAITool]] = None
    tool_choice: Optional[Any] = None


# Claude API 兼容模型
class ClaudeContent(BaseModel):
    type: str  # "text" 或 "image" 等
    text: Optional[str] = None
    source: Optional[Dict[str, Any]] = None  # 用于图片等内容


class ClaudeMessage(BaseModel):
    role: str  # "user" 或 "assistant"
    content: Union[str, List[ClaudeContent]]


class ClaudeRequest(BaseModel):
    model: str
    max_tokens: int = 4096
    messages: List[ClaudeMessage]
    system: Optional[Union[str, List[ClaudeContent]]] = None  # 支持字符串或内容数组
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None 