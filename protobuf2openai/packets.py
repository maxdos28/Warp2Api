from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List, Optional
import json

from .state import STATE, ensure_tool_ids
from .helpers import normalize_content_to_list, segments_to_text, segments_to_warp_results, has_images, extract_images
from .models import ChatMessage
from .logging import logger


def packet_template() -> Dict[str, Any]:
    return {
        "task_context": {"active_task_id": ""},
        "input": {"context": {}, "user_inputs": {"inputs": []}},
        "settings": {
            "model_config": {
                "base": "claude-4.1-opus",
                "planning": "gpt-5 (high reasoning)",
                "coding": "auto",
            },
            "rules_enabled": False,
            "web_context_retrieval_enabled": False,
            "supports_parallel_tool_calls": False,
            "planning_enabled": False,
            "warp_drive_context_enabled": False,
            "supports_create_files": False,
            "use_anthropic_text_editor_tools": False,
            "supports_long_running_commands": False,
            "should_preserve_file_content_in_history": False,
            "supports_todos_ui": False,
            "supports_linked_code_blocks": False,
            "supported_tools": [9],
        },
        "metadata": {"logging": {"is_autodetected_user_query": True, "entrypoint": "USER_INITIATED"}},
    }


async def process_message_images(content: Any) -> tuple[str, Optional[Dict[str, Any]]]:
    """
    处理消息中的图片，返回文本内容和图片附件
    
    Args:
        content: 消息内容（可能包含文本和图片）
        
    Returns:
        (text_content, image_attachments) 元组
        image_attachments 格式: {"IMAGE_1": {"plain_text": "..."}, ...}
    """
    from .image_utils import process_image_url, get_image_info
    from .multimodal_config import config
    
    # 检查多模态功能是否启用
    if not config.is_multimodal_enabled():
        logger.debug("Multimodal support is disabled, extracting text only")
        segments = normalize_content_to_list(content)
        return segments_to_text(segments), None
    
    segments = normalize_content_to_list(content)
    
    # 提取文本
    text_content = segments_to_text(segments)
    
    # 检查是否有图片
    if not has_images(segments):
        return text_content, None
    
    # 处理图片
    images = extract_images(segments)
    image_attachments: Dict[str, Any] = {}
    
    for idx, img_seg in enumerate(images):
        image_url_data = img_seg.get("image_url", {})
        
        # 处理图片 URL（下载并转换为 base64）
        try:
            processed_url, error = await process_image_url(image_url_data)
            
            if error:
                logger.warning(f"Failed to process image {idx+1}: {error}")
                # 添加错误提示到附件
                image_attachments[f"IMAGE_{idx+1}_ERROR"] = {
                    "plain_text": f"[图片 {idx+1} 处理失败: {error}]"
                }
                continue
            
            if processed_url:
                # 获取图片信息（用于日志）
                img_info = get_image_info(processed_url)
                logger.info(f"Processed image {idx+1}: {img_info}")
                
                # 将图片作为附件添加
                # 使用 plain_text 格式包含 base64 data URL
                # Warp 可能会在前端渲染这些图片
                image_attachments[f"IMAGE_{idx+1}"] = {
                    "plain_text": f"[图片 {idx+1}]\n{processed_url}"
                }
                
                logger.info(f"Added image attachment IMAGE_{idx+1} ({img_info.get('size_kb')} KB)")
        
        except Exception as e:
            logger.error(f"Error processing image {idx+1}: {e}")
            image_attachments[f"IMAGE_{idx+1}_ERROR"] = {
                "plain_text": f"[图片 {idx+1} 处理异常: {str(e)}]"
            }
    
    return text_content, image_attachments if image_attachments else None


def map_history_to_warp_messages(history: List[ChatMessage], task_id: str, system_prompt_for_last_user: Optional[str] = None, attach_to_history_last_user: bool = False) -> List[Dict[str, Any]]:
    ensure_tool_ids()
    msgs: List[Dict[str, Any]] = []
    # Insert server tool_call preamble as first message
    msgs.append({
        "id": (STATE.tool_message_id or str(uuid.uuid4())),
        "task_id": task_id,
        "tool_call": {
            "tool_call_id": (STATE.tool_call_id or str(uuid.uuid4())),
            "server": {"payload": "IgIQAQ=="},
        },
    })

    # Determine the last input message index (either last 'user' or last 'tool' with tool_call_id)
    last_input_index: Optional[int] = None
    for idx in range(len(history) - 1, -1, -1):
        _m = history[idx]
        if _m.role == "user":
            last_input_index = idx
            break
        if _m.role == "tool" and _m.tool_call_id:
            last_input_index = idx
            break

    for i, m in enumerate(history):
        mid = str(uuid.uuid4())
        # Skip the final input message; it will be placed into input.user_inputs
        if (last_input_index is not None) and (i == last_input_index):
            continue
        if m.role == "user":
            user_query_obj: Dict[str, Any] = {"query": segments_to_text(normalize_content_to_list(m.content))}
            msgs.append({"id": mid, "task_id": task_id, "user_query": user_query_obj})
        elif m.role == "assistant":
            _assistant_text = segments_to_text(normalize_content_to_list(m.content))
            if _assistant_text:
                msgs.append({"id": mid, "task_id": task_id, "agent_output": {"text": _assistant_text}})
            for tc in (m.tool_calls or []):
                msgs.append({
                    "id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "tool_call": {
                        "tool_call_id": tc.get("id") or str(uuid.uuid4()),
                        "call_mcp_tool": {
                            "name": (tc.get("function", {}) or {}).get("name", ""),
                            "args": (json.loads((tc.get("function", {}) or {}).get("arguments", "{}")) if isinstance((tc.get("function", {}) or {}).get("arguments"), str) else (tc.get("function", {}) or {}).get("arguments", {})) or {},
                        },
                    },
                })
        elif m.role == "tool":
            # Preserve tool_result adjacency by placing it directly in task_context
            if m.tool_call_id:
                msgs.append({
                    "id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "tool_call_result": {
                        "tool_call_id": m.tool_call_id,
                        "call_mcp_tool": {
                            "success": {
                                "results": segments_to_warp_results(normalize_content_to_list(m.content))
                            }
                        },
                    },
                })
    return msgs


async def attach_user_and_tools_to_inputs(packet: Dict[str, Any], history: List[ChatMessage], system_prompt_text: Optional[str]) -> None:
    """
    将用户输入和工具结果附加到数据包中（支持多模态）
    
    注意：此函数现在是异步的，因为需要处理图片下载
    """
    # Use the final post-reorder message as input (user or tool result)
    if not history:
        assert False, "post-reorder 必须至少包含一条消息"
    last = history[-1]
    
    if last.role == "user":
        # 处理用户消息（可能包含图片）
        text_content, image_attachments = await process_message_images(last.content)
        
        user_query_payload: Dict[str, Any] = {"query": text_content}
        
        # 构建附件字典
        attachments: Dict[str, Any] = {}
        
        # 添加 system prompt（如果有）
        if system_prompt_text:
            attachments["SYSTEM_PROMPT"] = {
                "plain_text": f"""<ALERT>you are not allowed to call following tools:  - `read_files`
- `write_files`
- `run_commands`
- `list_files`
- `str_replace_editor`
- `ask_followup_question`
- `attempt_completion`</ALERT>{system_prompt_text}"""
            }
        
        # 添加图片附件（如果有）
        if image_attachments:
            attachments.update(image_attachments)
            logger.info(f"Added {len(image_attachments)} image attachment(s) to user query")
        
        # 如果有附件，添加到 payload
        if attachments:
            user_query_payload["referenced_attachments"] = attachments
        
        packet["input"]["user_inputs"]["inputs"].append({"user_query": user_query_payload})
        return
    
    if last.role == "tool" and last.tool_call_id:
        packet["input"]["user_inputs"]["inputs"].append({
            "tool_call_result": {
                "tool_call_id": last.tool_call_id,
                "call_mcp_tool": {
                    "success": {"results": segments_to_warp_results(normalize_content_to_list(last.content))}
                },
            }
        })
        return
    
    # If neither, assert to catch protocol violations
    assert False, "post-reorder 最后一条必须是 user 或 tool 结果" 