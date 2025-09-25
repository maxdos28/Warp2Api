from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .logging import logger

from .models import ChatCompletionsRequest, ChatMessage
from .reorder import reorder_messages_for_anthropic
from .helpers import normalize_content_to_list, segments_to_text
from .packets import packet_template, map_history_to_warp_messages, attach_user_and_tools_to_inputs
from .state import STATE
from .config import BRIDGE_BASE_URL
from .bridge import initialize_once
from .sse_transform import stream_openai_sse
from .auth import authenticate_request


router = APIRouter()


def _deduplicate_messages(messages: List[ChatMessage]) -> List[ChatMessage]:
    """移除重复的消息，特别是系统提示和重复的用户消息，但保留最后一条消息"""
    if not messages:
        return messages
    
    # 如果只有一条消息，直接返回
    if len(messages) == 1:
        return messages
    
    seen_content = set()
    deduplicated = []
    
    # 处理除最后一条消息外的所有消息
    for i, msg in enumerate(messages[:-1]):
        # 安全地处理content字段（可能是字符串或列表）
        if isinstance(msg.content, str):
            content_str = msg.content
        elif isinstance(msg.content, list):
            content_str = str(msg.content)
        else:
            content_str = str(msg.content) if msg.content else ""
        
        # 特殊检查：如果包含重复的分析模式，直接跳过
        if _is_repetitive_analysis_content(content_str):
            logger.debug(f"[OpenAI Compat] Skipping repetitive analysis content")
            continue
        
        # 清理内容，移除常见的重复模式
        cleaned_content = _clean_content_for_dedup(content_str)
        
        # 创建消息的唯一标识
        content_key = f"{msg.role}:{cleaned_content[:150]}"  # 使用前150个字符作为标识
        
        if content_key not in seen_content:
            seen_content.add(content_key)
            deduplicated.append(msg)
        else:
            logger.debug(f"[OpenAI Compat] Removed duplicate message: {content_key}")
    
    # 总是保留最后一条消息
    deduplicated.append(messages[-1])
    
    logger.info(f"[OpenAI Compat] Deduplicated messages: {len(messages)} -> {len(deduplicated)}")
    return deduplicated


def _is_repetitive_analysis_content(content: str) -> bool:
    """检查是否包含重复的分析内容"""
    if not content:
        return False
    
    # 检查特定的重复模式
    repetitive_patterns = [
        "I'll analyze your" in content and "create a comprehensive" in content and "Let me start by exploring" in content,
        "Let me start by exploring" in content and "codebase structure and key files" in content and "还是这样啊" in content,
        "I'll analyze your" in content and "Let me start by exploring" in content and "codebase structure" in content,
        "I'll analyze your" in content and "create a comprehensive" in content and "CLAUDE.md" in content and "Let me start by exploring" in content,
        "I'll analyze your" in content and "create a comprehensive" in content and "Let me start by exploring" in content and "codebase structure and key files" in content,
        "I'll analyze your" in content and "create a comprehensive" in content and "Let me start by exploring" in content and "codebase structure and key files" in content and "还是这样啊" in content,
    ]
    
    return any(repetitive_patterns)


def _clean_content_for_dedup(content: str) -> str:
    """清理内容以便更好地识别重复"""
    if not content:
        return ""
    
    # 移除常见的重复模式
    cleaned = content
    
    # 移除重复的分析步骤和命令
    patterns_to_remove = [
        r"I'll analyze this codebase.*?Let me start by examining",
        r"Let me start by examining.*?I'll analyze the codebase", 
        r"You're right! Let me use the correct tools.*?I'll start by checking",
        r"Let me try the correct format.*?claude /init",
        r"I'll analyze this codebase.*?create.*?CLAUDE\.md",
        r"Let me start by examining.*?project structure",
        r"Let me use the correct tools.*?analyze the codebase",
        r"Let me try the correct format.*?file_glob",
        r"claude /init.*?输出.*?还是有问题",
        r"Let me start by examining.*?key files",
        r"I'll start by checking.*?existing CLAUDE\.md",
        r"Let me try the correct format.*?file_glob:",
        r"You're absolutely right! Let me use the correct tools.*?I'll start by checking",
        r"Let me correct my previous tool call.*?Now let me examine",
        r"Let me check for an existing CLAUDE\.md.*?using the correct tools",
        r"Let me correct my file_glob call.*?cluade code",
        r"I'll analyze the codebase.*?create a CLAUDE\.md file",
        r"Let me start by examining.*?project structure and key files",
        r"You're absolutely right!.*?Let me use the correct tools",
        r"Let me correct my previous.*?Now let me examine",
        r"Let me check for.*?existing files",
        r"Let me correct my.*?file_glob call",
        r"Now let me examine.*?project structure",
        r"Let me check for an existing.*?CLAUDE\.md file",
        r"Let me correct my file_glob.*?cluade code",
        r"I'll analyze your.*?codebase.*?create.*?CLAUDE\.md",
        r"Let me start by exploring.*?codebase structure",
        r"I'll analyze your.*?Let me start by exploring",
        r"Let me start by exploring.*?I'll analyze your",
        r"Let me start by exploring.*?codebase structure and key files",
        r"I'll analyze your.*?codebase.*?Let me start by exploring",
        r"Let me start by exploring.*?codebase structure.*?key files",
        r"I'll analyze your.*?codebase.*?create.*?comprehensive.*?CLAUDE\.md",
        r"Let me start by exploring.*?codebase structure.*?key files.*?还是这样啊",
        r"I'll analyze your.*?codebase.*?create.*?comprehensive.*?CLAUDE\.md.*?Let me start by exploring",
        r"Let me start by exploring.*?codebase structure.*?key files.*?还是这样啊",
        r"I'll analyze your.*?codebase.*?create.*?comprehensive.*?CLAUDE\.md.*?Let me start by exploring.*?codebase structure.*?key files.*?还是这样啊",
    ]
    
    import re
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)
    
    # 移除多余的空格和换行
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # 检查是否包含多个重复的分析步骤
    analysis_phrases = [
        "I'll analyze",
        "Let me start by examining", 
        "Let me use the correct tools",
        "Let me check for",
        "Let me correct my",
        "Now let me examine",
        "You're absolutely right",
        "Let me try the correct format",
        "Let me start by exploring",
        "I'll analyze your",
        "create a comprehensive",
        "codebase structure",
        "key files",
        "还是这样啊"
    ]
    
    phrase_count = sum(1 for phrase in analysis_phrases if phrase in cleaned)
    
    # 检查是否包含重复的分析模式
    repetitive_patterns = [
        "I'll analyze" in cleaned and "Let me start by" in cleaned,
        "Let me start by" in cleaned and "codebase" in cleaned and "CLAUDE.md" in cleaned,
        "Let me start by exploring" in cleaned and "codebase structure" in cleaned,
        "I'll analyze your" in cleaned and "Let me start by exploring" in cleaned,
        "还是这样啊" in cleaned and ("I'll analyze" in cleaned or "Let me start by" in cleaned),
        "I'll analyze your" in cleaned and "create a comprehensive" in cleaned and "CLAUDE.md" in cleaned,
        "Let me start by exploring" in cleaned and "codebase structure and key files" in cleaned,
        "I'll analyze your" in cleaned and "Let me start by exploring" in cleaned and "codebase structure" in cleaned,
        "I'll analyze your" in cleaned and "create a comprehensive" in cleaned and "Let me start by exploring" in cleaned,
        "Let me start by exploring" in cleaned and "codebase structure and key files" in cleaned and "还是这样啊" in cleaned
    ]
    
    # 如果包含太多分析短语或重复模式，可能是重复内容
    if phrase_count >= 3 or any(repetitive_patterns):
        logger.debug(f"[OpenAI Compat] Detected repetitive analysis content with {phrase_count} phrases and patterns: {repetitive_patterns}")
        return ""
    
    # 特殊处理：如果包含特定的重复模式，直接返回空字符串
    if ("I'll analyze your" in cleaned and "create a comprehensive" in cleaned and 
        "Let me start by exploring" in cleaned and "codebase structure and key files" in cleaned):
        logger.debug(f"[OpenAI Compat] Detected specific repetitive pattern, filtering out")
        return ""
    
    # 如果清理后内容太短，可能是重复内容，返回空字符串
    if len(cleaned) < 10:
        return ""
    
    return cleaned


@router.get("/")
def root():
    return {"service": "OpenAI Chat Completions (Warp bridge) - Streaming", "status": "ok"}


@router.get("/healthz")
def health_check():
    return {"status": "ok", "service": "OpenAI Chat Completions (Warp bridge) - Streaming"}


@router.get("/v1/models")
def list_models():
    """OpenAI-compatible model listing. Forwards to bridge, with local fallback."""
    try:
        resp = requests.get(f"{BRIDGE_BASE_URL}/v1/models", timeout=10.0)
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"bridge_error: {resp.text}")
        return resp.json()
    except Exception as e:
        try:
            # Local fallback: construct models directly if bridge is unreachable
            from warp2protobuf.config.models import get_all_unique_models  # type: ignore
            models = get_all_unique_models()
            return {"object": "list", "data": models}
        except Exception:
            raise HTTPException(502, f"bridge_unreachable: {e}")


@router.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionsRequest, request: Request = None):
    # 认证检查
    if request:
        await authenticate_request(request)

    try:
        initialize_once()
    except Exception as e:
        logger.warning(f"[OpenAI Compat] initialize_once failed or skipped: {e}")

    if not req.messages:
        raise HTTPException(400, "messages 不能为空")

    # 1) 打印接收到的 Chat Completions 原始请求体
    try:
        logger.info("[OpenAI Compat] 接收到的 Chat Completions 请求体(原始): %s", json.dumps(req.dict(), ensure_ascii=False))
    except Exception:
        logger.info("[OpenAI Compat] 接收到的 Chat Completions 请求体(原始) 序列化失败")

    # 整理消息
    history: List[ChatMessage] = reorder_messages_for_anthropic(list(req.messages))
    
    # 消息去重 - 移除重复的系统提示和用户消息
    history = _deduplicate_messages(history)

    # 2) 打印整理后的请求体（post-reorder）
    try:
        logger.info("[OpenAI Compat] 整理后的请求体(post-reorder): %s", json.dumps({
            **req.dict(),
            "messages": [m.dict() for m in history]
        }, ensure_ascii=False))
    except Exception:
        logger.info("[OpenAI Compat] 整理后的请求体(post-reorder) 序列化失败")

    system_prompt_text: Optional[str] = None
    try:
        chunks: List[str] = []
        for _m in history:
            if _m.role == "system":
                _txt = segments_to_text(normalize_content_to_list(_m.content))
                if _txt.strip():
                    chunks.append(_txt)
        if chunks:
            system_prompt_text = "\n\n".join(chunks)
    except Exception:
        system_prompt_text = None

    task_id = STATE.baseline_task_id or str(uuid.uuid4())
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

    # 设置模型配置 - 检查是否有图片，使用支持视觉的模型
    packet.setdefault("settings", {}).setdefault("model_config", {})

    # 检查是否包含图片内容
    has_images = False
    for msg in history:
        if hasattr(msg, 'content') and isinstance(msg.content, list):
            for content_item in msg.content:
                if isinstance(content_item, dict) and content_item.get("type") in ["image", "image_url"]:
                    has_images = True
                    break

    # 根据是否包含图片选择合适的模型
    if has_images:
        print("[OpenAI Compat] Detected images, using vision-capable model")
        # 对于图片处理，优先使用更强的模型
        if req.model in ["claude-4.1-opus", "claude-4-opus", "gpt-4o", "gpt-4.1"]:
            packet["settings"]["model_config"]["base"] = req.model
        else:
            # 默认使用claude-4.1-opus处理图片（最强的视觉模型）
            packet["settings"]["model_config"]["base"] = "claude-4.1-opus"
    else:
        # 文本处理使用指定模型或默认模型
        packet["settings"]["model_config"]["base"] = req.model or "claude-4-sonnet"

    if STATE.conversation_id:
        packet.setdefault("metadata", {})["conversation_id"] = STATE.conversation_id

    attach_user_and_tools_to_inputs(packet, history, system_prompt_text)

    if req.tools:
        mcp_tools: List[Dict[str, Any]] = []
        for t in req.tools:
            if t.type != "function" or not t.function:
                continue
            mcp_tools.append({
                "name": t.function.name,
                "description": t.function.description or "",
                "input_schema": t.function.parameters or {},
            })
        if mcp_tools:
            packet.setdefault("mcp_context", {}).setdefault("tools", []).extend(mcp_tools)

    # 3) 打印转换成 protobuf JSON 的请求体（发送到 bridge 的数据包）
    try:
        logger.info("[OpenAI Compat] 转换成 Protobuf JSON 的请求体: %s", json.dumps(packet, ensure_ascii=False))
    except Exception:
        logger.info("[OpenAI Compat] 转换成 Protobuf JSON 的请求体 序列化失败")

    created_ts = int(time.time())
    completion_id = str(uuid.uuid4())
    model_id = req.model or "warp-default"

    if req.stream:
        async def _agen():
            async for chunk in stream_openai_sse(packet, completion_id, created_ts, model_id):
                yield chunk
        return StreamingResponse(_agen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})

    def _post_once() -> requests.Response:
        return requests.post(
            f"{BRIDGE_BASE_URL}/api/warp/send_stream",
            json={"json_data": packet, "message_type": "warp.multi_agent.v1.Request"},
            timeout=(5.0, 180.0),
        )

    try:
        resp = _post_once()
        if resp.status_code == 429:
            try:
                r = requests.post(f"{BRIDGE_BASE_URL}/api/auth/refresh", timeout=10.0)
                logger.warning("[OpenAI Compat] Bridge returned 429. Tried JWT refresh -> HTTP %s", getattr(r, 'status_code', 'N/A'))
            except Exception as _e:
                logger.warning("[OpenAI Compat] JWT refresh attempt failed after 429: %s", _e)
            resp = _post_once()
        if resp.status_code != 200:
            logger.error("[OpenAI Compat] Bridge error %s: %s", resp.status_code, resp.text[:500])
            raise HTTPException(resp.status_code, f"bridge_error: {resp.text}")
        
        try:
            bridge_resp = resp.json()
        except Exception as json_e:
            logger.error("[OpenAI Compat] Failed to parse bridge response as JSON: %s", json_e)
            logger.error("[OpenAI Compat] Raw response: %s", resp.text[:1000])
            raise HTTPException(502, f"bridge_response_parse_error: {json_e}")
            
        # 记录响应信息用于调试
        logger.info("[OpenAI Compat] Bridge response received: %s", {
            "status": resp.status_code,
            "response_length": len(bridge_resp.get("response", "")),
            "events_count": len(bridge_resp.get("parsed_events", [])),
            "conversation_id": bridge_resp.get("conversation_id"),
            "task_id": bridge_resp.get("task_id")
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[OpenAI Compat] Bridge request failed: %s", e)
        raise HTTPException(502, f"bridge_unreachable: {e}")

    try:
        STATE.conversation_id = bridge_resp.get("conversation_id") or STATE.conversation_id
        ret_task_id = bridge_resp.get("task_id")
        if isinstance(ret_task_id, str) and ret_task_id:
            STATE.baseline_task_id = ret_task_id
    except Exception:
        pass

    tool_calls: List[Dict[str, Any]] = []
    try:
        parsed_events = bridge_resp.get("parsed_events", []) or []
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
                        try:
                            args_obj = call_mcp.get("args", {}) or {}
                            args_str = json.dumps(args_obj, ensure_ascii=False)
                        except Exception:
                            args_str = "{}"
                        tool_calls.append({
                            "id": tc.get("tool_call_id") or str(uuid.uuid4()),
                            "type": "function",
                            "function": {"name": call_mcp.get("name"), "arguments": args_str},
                        })
    except Exception:
        pass

    if tool_calls:
        msg_payload = {"role": "assistant", "content": "", "tool_calls": tool_calls}
        finish_reason = "tool_calls"
    else:
        response_text = bridge_resp.get("response", "")
        
        # 验证响应内容不为空
        if not response_text or not response_text.strip():
            # 尝试从parsed_events中提取响应文本
            try:
                parsed_events = bridge_resp.get("parsed_events", []) or []
                response_parts = []
                for ev in parsed_events:
                    evd = ev.get("parsed_data") or ev.get("raw_data") or {}
                    client_actions = evd.get("client_actions") or evd.get("clientActions") or {}
                    actions = client_actions.get("actions") or client_actions.get("Actions") or []
                    for action in actions:
                        # 从add_messages_to_task中提取agent_output
                        add_msgs = action.get("add_messages_to_task") or action.get("addMessagesToTask") or {}
                        if isinstance(add_msgs, dict):
                            for message in add_msgs.get("messages", []) or []:
                                agent_output = message.get("agent_output") or message.get("agentOutput") or {}
                                text_content = agent_output.get("text", "")
                                if text_content and text_content.strip():
                                    response_parts.append(text_content)
                
                response_text = "".join(response_parts).strip()
                
                if not response_text:
                    logger.warning("[OpenAI Compat] Empty response from bridge, using fallback message")
                    response_text = "I apologize, but I encountered an issue generating a response. Please try again."
                    
            except Exception as e:
                logger.error(f"[OpenAI Compat] Failed to extract response from parsed_events: {e}")
                response_text = "I apologize, but I encountered an issue generating a response. Please try again."
        
        # 额外的内容验证和清理
        if response_text:
            # 移除可能的错误信息前缀
            error_prefixes = [
                "This may indicate a failure in his thought process",
                "inability to use a tool properly",
                "which can be mitigated with some user guidance"
            ]
            for prefix in error_prefixes:
                if prefix in response_text:
                    response_text = response_text.replace(prefix, "").strip()
            
            # 确保响应不为空
            if not response_text.strip():
                response_text = "I apologize, but I encountered an issue generating a response. Please try again."
        
        msg_payload = {"role": "assistant", "content": response_text}
        finish_reason = "stop"

    final = {
        "id": completion_id,
        "object": "chat.completion",
        "created": created_ts,
        "model": model_id,
        "choices": [{"index": 0, "message": msg_payload, "finish_reason": finish_reason}],
    }
    return final 