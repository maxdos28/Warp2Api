from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
import json

from .state import STATE, ensure_tool_ids
from .helpers import normalize_content_to_list, segments_to_text, segments_to_text_and_images, segments_to_warp_results
from .models import ChatMessage


def packet_template() -> Dict[str, Any]:
    packet = {
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
            "supports_parallel_tool_calls": True,
            "planning_enabled": False,
            "warp_drive_context_enabled": False,
            "supports_create_files": True,
            "use_anthropic_text_editor_tools": True,
            "supports_long_running_commands": True,
            "should_preserve_file_content_in_history": True,
            "supports_todos_ui": True,
            "supports_linked_code_blocks": True,
            # Enable core tools: 2 RunShellCommand, 3 SearchCodebase, 5 ReadFiles, 6 ApplyFileDiffs,
            # 9 Grep, 11 ReadMCPResource, 12 CallMCPTool, 13 WriteToLongRunningShellCommand, 15 FileGlobV2
            "supported_tools": [2, 3, 5, 6, 9, 11, 12, 13, 15],
        },
        "metadata": {"logging": {"is_autodetected_user_query": True, "entrypoint": "USER_INITIATED"}},
    }
    
    # Debug logging to verify tools are enabled
    print(f"[Packet Debug] Created packet with tools: {packet['settings']['supported_tools']}")
    print(f"[Packet Debug] Tool support flags: parallel={packet['settings']['supports_parallel_tool_calls']}, create_files={packet['settings']['supports_create_files']}, anthropic_tools={packet['settings']['use_anthropic_text_editor_tools']}")
    
    return packet


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
            # Extract text and images from content
            content_segments = normalize_content_to_list(m.content)
            query_text, images = segments_to_text_and_images(content_segments)
            
            user_query_obj: Dict[str, Any] = {"query": query_text}
            
            # Add images if present (for history messages, we'll include a note about images)
            if images:
                # Add a note about attached images in the query text
                if "images" not in query_text.lower():
                    user_query_obj["query"] = f"{query_text}\n[Note: {len(images)} image(s) were attached to this message]"
            
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
        # Extract text and images from content
        content_segments = normalize_content_to_list(last.content)
        query_text, images = segments_to_text_and_images(content_segments)
        
        print(f"[Packet Debug] Processing user input:")
        print(f"[Packet Debug]   - Content segments: {len(content_segments)}")
        print(f"[Packet Debug]   - Extracted images: {len(images)}")
        print(f"[Packet Debug]   - Query text: {query_text[:100]}...")
        
        user_query_payload: Dict[str, Any] = {"query": query_text}
        
        # Handle referenced attachments (system prompt only)
        referenced_attachments = {}
        
        # Add system prompt if present
        if system_prompt_text:
            referenced_attachments["SYSTEM_PROMPT"] = {
                "plain_text": f"""{system_prompt_text}"""
            }
        
        # 使用正确的InputContext.images字段传输图片
        if images:
            import base64
            import hashlib

            for i, image in enumerate(images):
                try:
                    image_data = image.get("data", "")
                    if image_data:
                        # 验证base64数据完整性
                        try:
                            test_decode = base64.b64decode(image_data)
                            data_hash = hashlib.md5(test_decode).hexdigest()
                            print(f"[Claude Compat] Image {i}: {len(image_data)} chars -> {len(test_decode)} bytes (MD5: {data_hash[:8]})")
                        except Exception as decode_error:
                            print(f"[Claude Compat] ⚠️ Image {i} base64 decode failed: {decode_error}")
                            continue

                        # 使用InputContext.images字段 - 这是protobuf定义的正确方式
                        packet.setdefault("input", {}).setdefault("context", {}).setdefault("images", []).append({
                            "data": f"base64:{image_data}",  # protobuf_utils会处理base64:前缀
                            "mime_type": image.get('mime_type', 'image/png')
                        })

                        # 在referenced_attachments中添加文本描述作为补充
                        attachment_key = f"IMAGE_{i}"
                        referenced_attachments[attachment_key] = {
                            "plain_text": f"[Image {i}]\nType: {image.get('mime_type', 'image/png')}\nSize: {len(test_decode)} bytes\nMD5: {data_hash[:8]}\n\n[This is an uploaded image. Please analyze and describe its content.]"
                        }

                        print(f"[Claude Compat] ✅ Added image {i} to InputContext.images")
                        print(f"[Claude Compat]   - Attachment key: {attachment_key}")
                        print(f"[Claude Compat]   - Mime type: {image.get('mime_type', 'image/png')}")

                except Exception as e:
                    print(f"[Claude Compat] ❌ Failed to process image {i}: {e}")
            
            # 在查询中添加图片分析提示
            if images:
                user_query_payload["query"] = f"{query_text}\n\n[Note: {len(images)} image(s) attached for analysis.]"
        
        if referenced_attachments:
            user_query_payload["referenced_attachments"] = referenced_attachments
        
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