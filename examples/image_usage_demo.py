#!/usr/bin/env python3
"""
图片传入功能使用演示

展示如何构造包含图片的OpenAI格式消息
"""

import json
import base64

def demo_image_messages():
    """演示各种图片消息格式"""
    
    # 1x1像素红色PNG的base64数据（用于演示）
    demo_image = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
    
    print("=== Warp API 图片传入功能使用演示 ===\n")
    
    # 示例1: 基本的图片分析请求
    print("1. 基本图片分析请求")
    basic_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "请分析这张图片"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{demo_image}"
                }
            }
        ]
    }
    
    print("消息结构:")
    print(json.dumps(basic_message, indent=2, ensure_ascii=False))
    print(f"内容段数: {len(basic_message['content'])}")
    print()
    
    # 示例2: 多图片对比
    print("2. 多图片对比请求")
    multi_image_message = {
        "role": "user", 
        "content": [
            {"type": "text", "text": "比较这两张图片："},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{demo_image}"}},
            {"type": "text", "text": " 和 "},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{demo_image}"}},
            {"type": "text", "text": " 有什么区别？"}
        ]
    }
    
    text_segments = [seg for seg in multi_image_message["content"] if seg["type"] == "text"]
    image_segments = [seg for seg in multi_image_message["content"] if seg["type"] == "image_url"]
    
    print(f"总段数: {len(multi_image_message['content'])}")
    print(f"文本段数: {len(text_segments)}")
    print(f"图片段数: {len(image_segments)}")
    
    combined_text = "".join([seg["text"] for seg in text_segments])
    print(f"组合文本: '{combined_text}'")
    print()
    
    # 示例3: 完整的聊天会话
    print("3. 包含图片的完整会话")
    conversation = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "这张图片显示什么？"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{demo_image}"}}
            ]
        },
        {
            "role": "assistant",
            "content": "这是一个1x1像素的红色PNG图片，通常用作占位符或测试图像。"
        },
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": "现在看这张："},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{demo_image}"}},
                {"type": "text", "text": " 它们有什么不同？"}
            ]
        }
    ]
    
    print("会话结构:")
    for i, msg in enumerate(conversation):
        role = msg["role"]
        content = msg["content"]
        
        if isinstance(content, str):
            print(f"  消息 {i+1} ({role}): 纯文本")
            print(f"    文本: '{content[:50]}...' ({len(content)} 字符)")
        else:
            text_parts = [seg["text"] for seg in content if seg["type"] == "text"]
            image_count = len([seg for seg in content if seg["type"] == "image_url"])
            print(f"  消息 {i+1} ({role}): 多媒体")
            print(f"    文本: '{''.join(text_parts)}'")
            print(f"    图片数量: {image_count}")
    print()
    
    # 示例4: API请求格式
    print("4. 完整的API请求格式")
    api_request = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "分析这个图片并告诉我它的技术规格"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{demo_image}"}}
                ]
            }
        ],
        "stream": False
    }
    
    print("API请求结构:")
    # 为了显示简洁，截断base64数据
    display_request = json.loads(json.dumps(api_request))
    for msg in display_request["messages"]:
        for content in msg.get("content", []):
            if content.get("type") == "image_url":
                url = content["image_url"]["url"]
                if len(url) > 100:
                    content["image_url"]["url"] = url[:50] + "..." + url[-10:]
    
    print(json.dumps(display_request, indent=2, ensure_ascii=False))
    print()
    
    print("=== 实现的核心功能 ===")
    print("✅ OpenAI Chat Completions API 兼容")
    print("✅ data URL 格式支持 (data:image/type;base64,data)")
    print("✅ 多种图片格式 (PNG, JPEG, GIF, WebP)")
    print("✅ 文本和图片混合消息")
    print("✅ 单消息多图片支持")
    print("✅ 会话历史中的图片保持")
    print("✅ 完整的 protobuf 数据转换")
    
    print("\n=== 使用方法 ===")
    print("1. 准备图片数据（base64编码）")
    print("2. 构造OpenAI格式的消息内容")
    print("3. 发送到 /v1/chat/completions 端点")
    print("4. 系统自动处理图片数据转换")
    
    print("\n=== 支持的图片格式 ===")
    print("- PNG: data:image/png;base64,...")
    print("- JPEG: data:image/jpeg;base64,...")
    print("- GIF: data:image/gif;base64,...")
    print("- WebP: data:image/webp;base64,...")
    
    return api_request

if __name__ == "__main__":
    demo_request = demo_image_messages()
    
    print(f"\n🎉 图片传入功能已成功实现并可以使用！")
    print(f"\n💡 提示：启动API服务器后，可以使用上述格式发送包含图片的请求。")