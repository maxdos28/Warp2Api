"""
简化的响应处理器，专门修复Cline的解析问题
"""

import json
import uuid
import time
from typing import Dict, Any


def create_simple_chat_response(bridge_response: Dict[str, Any], model: str, stream: bool = False) -> Dict[str, Any]:
    """创建简化的chat completion响应"""
    
    # 提取响应文本
    response_text = bridge_response.get("response", "")
    
    if not response_text:
        response_text = "I'm ready to help you with your task. Please let me know what you need assistance with."
    
    # 创建基本响应结构
    completion_id = f"chatcmpl-{str(uuid.uuid4())}"
    created_ts = int(time.time())
    
    if stream:
        # 流式响应 - 返回异步生成器函数
        async def generate_stream():
            # 开始chunk
            yield f"data: {json.dumps({
                'id': completion_id,
                'object': 'chat.completion.chunk',
                'created': created_ts,
                'model': model,
                'choices': [{
                    'index': 0,
                    'delta': {
                        'role': 'assistant',
                        'content': ''
                    }
                }]
            }, ensure_ascii=False)}\n\n"
            
            # 内容chunk
            yield f"data: {json.dumps({
                'id': completion_id,
                'object': 'chat.completion.chunk', 
                'created': created_ts,
                'model': model,
                'choices': [{
                    'index': 0,
                    'delta': {
                        'content': response_text
                    }
                }]
            }, ensure_ascii=False)}\n\n"
            
            # 结束chunk
            yield f"data: {json.dumps({
                'id': completion_id,
                'object': 'chat.completion.chunk',
                'created': created_ts,
                'model': model,
                'choices': [{
                    'index': 0,
                    'delta': {},
                    'finish_reason': 'stop'
                }]
            }, ensure_ascii=False)}\n\n"
            
            # 完成标记
            yield "data: [DONE]\n\n"
            
        return generate_stream()
    else:
        # 非流式响应
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created_ts,
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": max(1, len(str(bridge_response).split()) // 4),
                "completion_tokens": max(1, len(response_text.split())),
                "total_tokens": max(2, len(str(bridge_response).split()) // 4 + len(response_text.split()))
            }
        }


def extract_response_from_bridge(bridge_response: Dict[str, Any]) -> str:
    """从bridge响应中提取文本内容"""
    try:
        # 直接从response字段获取
        if "response" in bridge_response:
            response_text = bridge_response["response"]
            if isinstance(response_text, str) and response_text.strip():
                return response_text
        
        # 尝试从parsed_events中提取
        parsed_events = bridge_response.get("parsed_events", [])
        extracted_text = ""
        
        for event in parsed_events:
            if isinstance(event, dict):
                parsed_data = event.get("parsed_data", {})
                
                # 检查client_actions中的内容
                if "client_actions" in parsed_data:
                    actions = parsed_data["client_actions"].get("actions", [])
                    for action in actions:
                        if "append_to_message_content" in action:
                            message = action["append_to_message_content"].get("message", {})
                            agent_output = message.get("agent_output", {})
                            text = agent_output.get("text", "")
                            if text:
                                extracted_text += text
                        elif "add_messages_to_task" in action:
                            messages = action["add_messages_to_task"].get("messages", [])
                            for msg in messages:
                                agent_output = msg.get("agent_output", {})
                                text = agent_output.get("text", "")
                                if text:
                                    extracted_text += text
        
        if extracted_text.strip():
            return extracted_text
            
        # 最后备选方案
        return "I'm ready to assist you. Please let me know what you need help with."
        
    except Exception as e:
        print(f"Error extracting response: {e}")
        return "I encountered an issue processing the response. Please try again."


def is_valid_response(response: Any) -> bool:
    """检查响应是否有效"""
    if not response:
        return False
        
    if isinstance(response, dict):
        # 检查是否有必要的字段
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return bool(choice["message"]["content"].strip())
        elif "error" in response:
            return True  # 错误响应也是有效的
            
    return False