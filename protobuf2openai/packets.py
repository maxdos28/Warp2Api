from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
import json

from .state import STATE, ensure_tool_ids
from .helpers import normalize_content_to_list, segments_to_text, segments_to_warp_results, extract_images_from_segments
from .models import ChatMessage


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
            "rules_enabled": True,
            "web_context_retrieval_enabled": True,
            "supports_parallel_tool_calls": True,
            "planning_enabled": True,
            "warp_drive_context_enabled": True,
            "supports_create_files": True,
            "use_anthropic_text_editor_tools": True,
            "supports_long_running_commands": True,
            "should_preserve_file_content_in_history": True,
            "supports_todos_ui": True,
            "supports_linked_code_blocks": True,
            "supported_tools": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        },
        "metadata": {"logging": {"is_autodetected_user_query": True, "entrypoint": "USER_INITIATED"}},
    }


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
            content_segments = normalize_content_to_list(m.content)
            user_query_obj: Dict[str, Any] = {"query": segments_to_text(content_segments)}
            
            # 提取图像数据
            images = extract_images_from_segments(content_segments)
            if images:
                user_query_obj["referenced_attachments"] = {}
                for idx, img in enumerate(images):
                    attachment_key = f"IMAGE_{idx+1}"
                    # 图像数据已经是base64字符串格式
                    img_b64 = img['data']
                    
                    user_query_obj["referenced_attachments"][attachment_key] = {
                        "drive_object": {
                            "uid": f"img_{uuid.uuid4()}",
                            "object_payload": {
                                "generic_string_object": {
                                    "payload": f"data:{img['mime_type']};base64,{img_b64}",
                                    "object_type": "image"
                                }
                            }
                        }
                    }
            
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


def attach_user_and_tools_to_inputs(packet: Dict[str, Any], history: List[ChatMessage], system_prompt_text: Optional[str]) -> None:
    # Use the final post-reorder message as input (user or tool result)
    if not history:
        assert False, "post-reorder 必须至少包含一条消息"
    last = history[-1]
    if last.role == "user":
        content_segments = normalize_content_to_list(last.content)
        user_query_payload: Dict[str, Any] = {"query": segments_to_text(content_segments)}
        
        # 处理附件（系统提示词和图像）
        attachments = {}
        
        if system_prompt_text:
            attachments["SYSTEM_PROMPT"] = {
                "plain_text": system_prompt_text
            }
        
        # 提取图像数据
        images = extract_images_from_segments(content_segments)
        if images:
            for idx, img in enumerate(images):
                attachment_key = f"IMAGE_{idx+1}"
                # 图像数据已经是base64字符串格式
                img_b64 = img['data']
                
                attachments[attachment_key] = {
                    "drive_object": {
                        "uid": f"img_{uuid.uuid4()}",
                        "object_payload": {
                            "generic_string_object": {
                                "payload": f"data:{img['mime_type']};base64,{img_b64}",
                                "object_type": "image"
                            }
                        }
                    }
                }
        
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