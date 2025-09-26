"""
直接响应处理器 - 绕过所有复杂逻辑，直接返回Warp响应
"""

import json
import uuid
import time
import httpx
from typing import Dict, Any
from .config import BRIDGE_BASE_URL
from .logging import logger


async def handle_chat_request_directly(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """直接处理chat请求，绕过所有复杂的SSE逻辑"""
    
    try:
        # 构建简单的Warp请求
        warp_request = {
            "json_data": {
                "input": {
                    "context": {},
                    "user_inputs": {
                        "inputs": [
                            {
                                "user_query": {
                                    "query": request_data["messages"][-1]["content"] if request_data.get("messages") else "Hello"
                                }
                            }
                        ]
                    }
                },
                "settings": {
                    "model_config": {
                        "base": request_data.get("model", "claude-4-sonnet"),
                        "planning": "gpt-5 (high reasoning)",
                        "coding": "auto"
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
                    "supported_tools": [2, 3, 5, 6, 9, 11, 12, 13, 15]
                },
                "metadata": {
                    "logging": {
                        "is_autodetected_user_query": True,
                        "entrypoint": "USER_INITIATED"
                    }
                }
            },
            "message_type": "warp.multi_agent.v1.Request"
        }
        
        # 发送请求到Warp
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BRIDGE_BASE_URL}/api/warp/send_stream",
                json=warp_request
            )
            
            if response.status_code != 200:
                raise Exception(f"Warp request failed: {response.status_code}")
                
            warp_response = response.json()
            
        # 直接从Warp响应中提取文本
        response_text = warp_response.get("response", "")
        
        if not response_text:
            response_text = "I'm ready to help you. Please let me know what you need assistance with."
        
        # 创建标准OpenAI格式响应
        completion_id = f"chatcmpl-{uuid.uuid4()}"
        created_ts = int(time.time())
        
        if request_data.get("stream", False):
            # 流式响应
            async def stream_generator():
                # 发送角色开始
                yield f"data: {json.dumps({
                    'id': completion_id,
                    'object': 'chat.completion.chunk',
                    'created': created_ts,
                    'model': request_data.get('model', 'claude-4-sonnet'),
                    'choices': [{
                        'index': 0,
                        'delta': {
                            'role': 'assistant'
                        }
                    }]
                })}\n\n"
                
                # 发送内容
                yield f"data: {json.dumps({
                    'id': completion_id,
                    'object': 'chat.completion.chunk',
                    'created': created_ts,
                    'model': request_data.get('model', 'claude-4-sonnet'),
                    'choices': [{
                        'index': 0,
                        'delta': {
                            'content': response_text
                        }
                    }]
                })}\n\n"
                
                # 发送结束
                yield f"data: {json.dumps({
                    'id': completion_id,
                    'object': 'chat.completion.chunk', 
                    'created': created_ts,
                    'model': request_data.get('model', 'claude-4-sonnet'),
                    'choices': [{
                        'index': 0,
                        'delta': {},
                        'finish_reason': 'stop'
                    }]
                })}\n\n"
                
                yield "data: [DONE]\n\n"
                
            return stream_generator()
        else:
            # 非流式响应
            return {
                "id": completion_id,
                "object": "chat.completion",
                "created": created_ts,
                "model": request_data.get("model", "claude-4-sonnet"),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(str(request_data).split()) // 4,
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": len(str(request_data).split()) // 4 + len(response_text.split())
                }
            }
            
    except Exception as e:
        logger.error(f"[DirectResponse] Failed: {e}")
        
        # 最简单的错误响应
        return {
            "error": {
                "message": f"Service temporarily unavailable: {str(e)}",
                "type": "service_unavailable",
                "code": "temp_error"
            }
        }