"""
Claude 消息格式转换模块
将 Claude API 格式转换为内部 protobuf 格式
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from .models import ClaudeRequest, ClaudeMessage, ClaudeContent, ChatMessage
from .helpers import normalize_content_to_list, segments_to_text
from .packets import packet_template, map_history_to_warp_messages, attach_user_and_tools_to_inputs
from .state import STATE
from .logging import logger


def claude_content_to_text(content: Any) -> str:
    """将 Claude 内容转换为纯文本"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                # 处理文本类型的内容
                if item.get("type") == "text" and item.get("text"):
                    text_parts.append(item["text"])
                # 处理其他可能的文本字段
                elif "text" in item and isinstance(item["text"], str):
                    text_parts.append(item["text"])
            elif isinstance(item, str):
                text_parts.append(item)
        return "\n".join(text_parts)
    elif isinstance(content, dict):
        # 处理单个内容对象
        if content.get("type") == "text" and content.get("text"):
            return content["text"]
        elif "text" in content and isinstance(content["text"], str):
            return content["text"]
    return str(content) if content else ""


def claude_message_to_chat_message(claude_msg: ClaudeMessage) -> ChatMessage:
    """将 Claude 消息转换为内部 ChatMessage 格式"""
    content_text = claude_content_to_text(claude_msg.content)
    
    return ChatMessage(
        role=claude_msg.role,
        content=content_text
    )


def claude_request_to_internal_packet(req: ClaudeRequest) -> Dict[str, Any]:
    """将 Claude 请求转换为内部 protobuf 数据包格式"""
    
    # 转换消息
    history: List[ChatMessage] = []
    for claude_msg in req.messages:
        chat_msg = claude_message_to_chat_message(claude_msg)
        history.append(chat_msg)
    
    # 处理系统提示
    system_prompt_text: Optional[str] = None
    if req.system:
        if isinstance(req.system, str):
            system_prompt_text = req.system
        else:
            # 处理复杂的系统内容结构
            system_prompt_text = claude_content_to_text(req.system)
        
        if system_prompt_text:
            # 在消息列表开头插入系统消息
            system_msg = ChatMessage(role="system", content=system_prompt_text)
            history.insert(0, system_msg)
    
    # 创建任务ID
    task_id = STATE.baseline_task_id or str(uuid.uuid4())
    
    # 创建基础数据包
    packet = packet_template()
    packet["task_context"] = {
        "tasks": [{
            "id": task_id,
            "description": "",
            "status": {"in_progress": {}},
            "messages": map_history_to_warp_messages(history, task_id, None, False),
        }],
        "active_task_id": task_id,
    }
    
    # 设置模型配置
    packet.setdefault("settings", {}).setdefault("model_config", {})
    packet["settings"]["model_config"]["base"] = req.model or "claude-4.1-opus"
    
    # 设置温度和其他参数
    if req.temperature is not None:
        packet["settings"]["model_config"]["temperature"] = req.temperature
    if req.top_p is not None:
        packet["settings"]["model_config"]["top_p"] = req.top_p
    if req.top_k is not None:
        packet["settings"]["model_config"]["top_k"] = req.top_k
    if req.max_tokens:
        packet["settings"]["model_config"]["max_tokens"] = req.max_tokens
    
    # 设置对话ID
    if STATE.conversation_id:
        packet.setdefault("metadata", {})["conversation_id"] = STATE.conversation_id
    
    # 附加用户和工具信息
    attach_user_and_tools_to_inputs(packet, history, system_prompt_text)
    
    # 处理工具
    if req.tools:
        mcp_tools: List[Dict[str, Any]] = []
        for tool in req.tools:
            if isinstance(tool, dict):
                # Claude 工具格式稍有不同，需要适配
                tool_name = tool.get("name", "")
                tool_desc = tool.get("description", "")
                tool_schema = tool.get("input_schema", {})
                
                if tool_name:
                    mcp_tools.append({
                        "name": tool_name,
                        "description": tool_desc,
                        "input_schema": tool_schema,
                    })
        
        if mcp_tools:
            packet.setdefault("mcp_context", {}).setdefault("tools", []).extend(mcp_tools)
    
    logger.info("[Claude Transform] 转换完成: %d 条消息, 模型: %s", len(req.messages), req.model)
    
    return packet


def format_claude_response(bridge_response: Dict[str, Any], request_id: str, model: str) -> Dict[str, Any]:
    """格式化为 Claude API 响应格式"""
    
    # 提取响应内容
    content = bridge_response.get("response", "")
    
    # 构建 Claude 风格的响应
    response = {
        "id": request_id,
        "type": "message",
        "role": "assistant", 
        "content": [
            {
                "type": "text",
                "text": content
            }
        ],
        "model": model,
        "stop_reason": "end_turn",  # Claude 使用 stop_reason 而不是 finish_reason
        "stop_sequence": None,
        "usage": {
            "input_tokens": 0,  # TODO: 实际计算 token 数量
            "output_tokens": 0
        }
    }
    
    # 处理工具调用 (如果有)
    try:
        parsed_events = bridge_response.get("parsed_events", []) or []
        tool_calls = []
        
        for ev in parsed_events:
            evd = ev.get("parsed_data") or ev.get("raw_data") or {}
            client_actions = evd.get("client_actions") or evd.get("clientActions") or {}
            actions = client_actions.get("actions") or client_actions.get("Actions") or []
            
            for action in actions:
                add_msgs = action.get("add_messages_to_task") or action.get("addMessagesToTask") or {}
                if not isinstance(add_msgs, dict):
                    continue
                    
                for message in add_msgs.get("messages", []) or []:
                    tc = message.get("tool_call") or message.get("toolCall") or {}
                    call_mcp = tc.get("call_mcp_tool") or tc.get("callMcpTool") or {}
                    
                    if isinstance(call_mcp, dict) and call_mcp.get("name"):
                        tool_calls.append({
                            "type": "tool_use",
                            "id": tc.get("tool_call_id") or str(uuid.uuid4()),
                            "name": call_mcp.get("name"),
                            "input": call_mcp.get("args", {})
                        })
        
        if tool_calls:
            # Claude 将工具调用作为 content 的一部分
            response["content"].extend(tool_calls)
            response["stop_reason"] = "tool_use"
            
    except Exception as e:
        logger.warning("[Claude Transform] 处理工具调用失败: %s", e)
    
    return response