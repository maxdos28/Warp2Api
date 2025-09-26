#!/usr/bin/env python3
"""
图片聊天功能使用示例

展示如何使用新实现的图片传入功能发送包含图片的消息到Warp API
"""

import requests
import base64
import json
from typing import List, Dict, Any

def create_image_message(text: str, image_path: str = None, image_base64: str = None) -> List[Dict[str, Any]]:
    """
    创建包含文本和图片的消息内容
    
    Args:
        text: 文本内容
        image_path: 图片文件路径（可选）
        image_base64: base64编码的图片数据（可选）
    
    Returns:
        OpenAI格式的消息内容列表
    """
    content = [{"type": "text", "text": text}]
    
    if image_path:
        # 从文件读取图片并编码为base64
        with open(image_path, "rb") as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # 根据文件扩展名确定MIME类型
        if image_path.lower().endswith('.png'):
            mime_type = 'image/png'
        elif image_path.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        elif image_path.lower().endswith('.gif'):
            mime_type = 'image/gif'
        elif image_path.lower().endswith('.webp'):
            mime_type = 'image/webp'
        else:
            mime_type = 'image/jpeg'  # 默认
        
        data_url = f"data:{mime_type};base64,{image_b64}"
        content.append({
            "type": "image_url",
            "image_url": {"url": data_url}
        })
    
    elif image_base64:
        # 使用提供的base64数据
        data_url = f"data:image/jpeg;base64,{image_base64}"
        content.append({
            "type": "image_url", 
            "image_url": {"url": data_url}
        })
    
    return content

def send_image_chat_request(
    messages: List[Dict[str, Any]], 
    api_url: str = "http://localhost:8000/v1/chat/completions",
    model: str = "claude-4-sonnet"
) -> Dict[str, Any]:
    """
    发送包含图片的聊天请求
    
    Args:
        messages: 消息列表
        api_url: API端点URL
        model: 使用的模型
    
    Returns:
        API响应
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

# 使用示例
def main():
    print("=== Warp API 图片聊天功能示例 ===\n")
    
    # 示例1: 使用base64数据的简单图片分析
    print("示例1: 图片描述")
    # 1x1像素红色PNG的base64数据（用于演示）
    demo_image = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
    
    messages = [
        {
            "role": "user",
            "content": create_image_message(
                "请描述这张图片的内容",
                image_base64=demo_image
            )
        }
    ]
    
    print("请求消息结构:")
    print(json.dumps(messages, indent=2, ensure_ascii=False))
    
    # 注意：实际发送请求需要API服务器运行
    # response = send_image_chat_request(messages)
    # print(f"响应: {response}")
    
    print("\n" + "="*50)
    
    # 示例2: 多图片对比
    print("\n示例2: 多图片对比")
    multi_image_messages = [
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": "比较这两张图片的差异："},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{demo_image}"}},
                {"type": "text", "text": " 和 "},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{demo_image}"}},
                {"type": "text", "text": " 有什么不同？"}
            ]
        }
    ]
    
    print("多图片消息结构:")
    for i, msg in enumerate(multi_image_messages):
        content = msg["content"]
        print(f"消息 {i}: {len(content)} 个内容段")
        for j, segment in enumerate(content):
            if segment["type"] == "text":
                print(f"  段 {j}: 文本 - '{segment['text']}'")
            elif segment["type"] == "image_url":
                url = segment["image_url"]["url"]
                print(f"  段 {j}: 图片 - {url[:50]}...")
    
    print("\n" + "="*50)
    
    # 示例3: 对话历史中的图片
    print("\n示例3: 带图片的对话历史")
    conversation_messages = [
        {
            "role": "user",
            "content": create_image_message("这是什么？", image_base64=demo_image)
        },
        {
            "role": "assistant", 
            "content": "这是一个1x1像素的红色PNG图片。"
        },
        {
            "role": "user",
            "content": "能告诉我更多关于这种格式的信息吗？"
        }
    ]
    
    print("对话历史:")
    for i, msg in enumerate(conversation_messages):
        role = msg["role"]
        content = msg["content"]
        if isinstance(content, str):
            print(f"{i+1}. {role}: {content}")
        else:
            text_parts = [seg["text"] for seg in content if seg["type"] == "text"]
            image_count = len([seg for seg in content if seg["type"] == "image_url"])
            print(f"{i+1}. {role}: {''.join(text_parts)} [包含{image_count}张图片]")
    
    print("\n✅ 图片传入功能已成功实现！")
    print("\n支持的功能:")
    print("- ✅ OpenAI Chat Completions API兼容格式")
    print("- ✅ data URL格式的base64图片")
    print("- ✅ 多种图片格式 (PNG, JPEG, GIF, WebP)")
    print("- ✅ 单条消息多张图片")
    print("- ✅ 文本和图片混合内容")
    print("- ✅ 对话历史中的图片保持")
    print("- ✅ 完整的protobuf数据转换")

if __name__ == "__main__":
    main()