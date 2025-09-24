"""
Anthropic Messages API compatible router
支持 /v1/messages 端点，兼容 Anthropic 的消息格式
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, Optional, Union
import base64

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .logging import logger
from .config import BRIDGE_BASE_URL
from .bridge import initialize_once
from .sse_transform import stream_openai_sse
from .auth import authenticate_request
from .state import STATE
from .packets import packet_template
from .helpers import extract_images_from_segments
from .image_handler import prepare_packet_for_bridge


# Anthropic Messages API 模型定义
class AnthropicImageSource(BaseModel):
    """Anthropic 格式的图片源"""
    type: str = Field("base64", description="图片源类型")
    media_type: str = Field(..., description="MIME类型，如 image/jpeg")
    data: str = Field(..., description="Base64编码的图片数据")


class AnthropicContentBlock(BaseModel):
    """Anthropic 格式的内容块"""
    type: str = Field(..., description="内容类型: text 或 image")
    text: Optional[str] = Field(None, description="文本内容")
    source: Optional[AnthropicImageSource] = Field(None, description="图片源")


class AnthropicMessage(BaseModel):
    """Anthropic 格式的消息"""
    role: str = Field(..., description="角色: user 或 assistant")
    content: Union[str, List[AnthropicContentBlock]] = Field(..., description="消息内容")


class MessagesRequest(BaseModel):
    """Anthropic Messages API 请求格式"""
    model: str = Field(..., description="模型名称")
    messages: List[AnthropicMessage] = Field(..., description="消息列表")
    max_tokens: Optional[int] = Field(1024, description="最大生成令牌数")
    temperature: Optional[float] = Field(None, description="温度参数")
    stream: Optional[bool] = Field(False, description="是否流式输出")
    system: Optional[str] = Field(None, description="系统提示")


messages_router = APIRouter()


def convert_anthropic_to_openai_format(messages: List[AnthropicMessage]) -> List[Dict[str, Any]]:
    """
    将 Anthropic 格式的消息转换为 OpenAI 格式
    """
    openai_messages = []
    
    for msg in messages:
        openai_msg = {"role": msg.role}
        
        if isinstance(msg.content, str):
            # 纯文本消息
            openai_msg["content"] = msg.content
        else:
            # 多模态消息
            content_parts = []
            for block in msg.content:
                if block.type == "text":
                    content_parts.append({
                        "type": "text",
                        "text": block.text or ""
                    })
                elif block.type == "image" and block.source:
                    # 转换 Anthropic 图片格式为 OpenAI 格式
                    data_url = f"data:{block.source.media_type};base64,{block.source.data}"
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": data_url}
                    })
            openai_msg["content"] = content_parts
        
        openai_messages.append(openai_msg)
    
    return openai_messages


def convert_content_to_warp_format(content: Union[str, List[AnthropicContentBlock]]) -> tuple[str, List[Dict[str, Any]]]:
    """
    将 Anthropic 内容转换为 Warp 格式
    返回: (文本内容, 图片列表)
    """
    if isinstance(content, str):
        return content, []
    
    text_parts = []
    images = []
    
    for block in content:
        if block.type == "text":
            text_parts.append(block.text or "")
        elif block.type == "image" and block.source:
            # 解码base64为bytes，这是protobuf期望的格式
            try:
                image_bytes = base64.b64decode(block.source.data)
                images.append({
                    "data": image_bytes,  # 使用bytes
                    "mime_type": block.source.media_type
                })
            except Exception as e:
                logger.error(f"Failed to decode image: {e}")
    
    return " ".join(text_parts), images


@messages_router.post("/v1/messages")
async def create_message(req: MessagesRequest, request: Request = None):
    """
    Anthropic Messages API 兼容端点
    支持文本和图片的多模态输入
    """
    # 认证检查
    if request:
        await authenticate_request(request)
    
    try:
        initialize_once()
    except Exception as e:
        logger.warning(f"[Messages API] initialize_once failed: {e}")
    
    if not req.messages:
        raise HTTPException(400, "messages 不能为空")
    
    # 记录原始请求
    try:
        logger.info("[Messages API] 接收到的请求: %s", json.dumps(req.dict(), ensure_ascii=False))
    except Exception:
        logger.info("[Messages API] 请求序列化失败")
    
    # 转换消息格式
    openai_messages = convert_anthropic_to_openai_format(req.messages)
    
    # 如果有系统提示，添加到消息列表开头
    if req.system:
        openai_messages.insert(0, {"role": "system", "content": req.system})
    
    # 构建 Warp 数据包
    task_id = STATE.baseline_task_id or str(uuid.uuid4())
    packet = packet_template()
    
    packet["task_context"] = {
        "tasks": [{
            "id": task_id,
            "description": "",
            "status": {"in_progress": {}},
            "messages": [],
        }],
        "active_task_id": task_id,
    }
    
    # 设置模型
    packet["settings"]["model_config"]["base"] = req.model
    
    # 处理最后一条用户消息
    if req.messages and req.messages[-1].role == "user":
        last_msg = req.messages[-1]
        text_content, images = convert_content_to_warp_format(last_msg.content)
        
        # 构建用户输入
        user_input = {"query": text_content}
        
        # 添加图片到input的context中
        if images:
            # 图片数据需要是base64字符串格式
            packet["input"]["context"] = {"images": images}
            logger.info(f"[Messages API] 添加了 {len(images)} 张图片到请求")
        
        # 如果有系统提示，添加为附件
        if req.system:
            user_input["referenced_attachments"] = {
                "SYSTEM_PROMPT": {
                    "plain_text": req.system
                }
            }
        
        packet["input"]["user_inputs"]["inputs"].append({"user_query": user_input})
    
    # 准备数据包以便发送
    packet = prepare_packet_for_bridge(packet)
    
    # 记录转换后的数据包
    try:
        logger.info("[Messages API] 转换后的 Warp 数据包: %s", json.dumps(packet, ensure_ascii=False))
    except Exception:
        logger.info("[Messages API] 数据包序列化失败")
    
    # 设置响应元数据
    created_ts = int(time.time())
    message_id = f"msg_{uuid.uuid4().hex[:24]}"
    
    if req.stream:
        # 流式响应
        async def _stream():
            async for chunk in stream_openai_sse(packet, message_id, created_ts, req.model):
                # 转换为 Anthropic 格式的 SSE
                yield chunk
        
        return StreamingResponse(
            _stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    else:
        # 非流式响应 - 使用 bridge_send_stream 来处理 bytes
        from .bridge import bridge_send_stream
        
        try:
            bridge_resp = bridge_send_stream(packet)
            if not bridge_resp:
                raise HTTPException(502, "bridge_error: no response")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(502, f"bridge_unreachable: {e}")
        
        # 提取响应文本
        response_text = bridge_resp.get("response", "")
        
        # 构建 Anthropic 格式的响应
        return {
            "id": message_id,
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": response_text
                }
            ],
            "model": req.model,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": 0,  # 需要实际计算
                "output_tokens": 0  # 需要实际计算
            }
        }


@messages_router.get("/v1/messages/models")
def list_messages_models():
    """列出支持的模型"""
    try:
        resp = requests.get(f"{BRIDGE_BASE_URL}/v1/models", timeout=10.0)
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"bridge_error: {resp.text}")
        return resp.json()
    except Exception as e:
        # 本地后备
        return {
            "models": [
                {"id": "claude-3-opus-20240229", "object": "model"},
                {"id": "claude-3-sonnet-20240229", "object": "model"},
                {"id": "claude-3-haiku-20240307", "object": "model"},
                {"id": "claude-3-5-sonnet-20241022", "object": "model"}
            ]
        }