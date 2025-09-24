#!/usr/bin/env python3
"""
最终的图片功能测试脚本
"""

import requests
import json
import base64

def test_image_with_api():
    """测试图片API功能"""
    
    # API配置
    api_url = "http://localhost:28889/v1/chat/completions"
    api_token = "001"
    
    # 创建一个简单的测试图片（1x1红色像素PNG）
    red_pixel_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    print("="*60)
    print("图片API功能测试")
    print("="*60)
    
    # 测试1: 单张图片
    print("\n1. 测试单张图片识别:")
    request_data = {
        "model": "claude-4.1-opus",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "This is a 1x1 pixel image. What color is it? Please describe what you see."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{red_pixel_base64}"
                        }
                    }
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            json=request_data,
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"   AI响应: {content[:300] if content else '(空响应)'}")
        else:
            print(f"   错误: {response.text[:200]}")
    except Exception as e:
        print(f"   异常: {str(e)[:200]}")
    
    # 测试2: 文本+图片混合
    print("\n2. 测试文本和图片混合消息:")
    request_data = {
        "model": "claude-4.1-opus",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "I'm showing you a tiny test image. "
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{red_pixel_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": " Can you confirm you received it?"
                    }
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            json=request_data,
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"   AI响应: {content[:300] if content else '(空响应)'}")
        else:
            print(f"   错误: {response.text[:200]}")
    except Exception as e:
        print(f"   异常: {str(e)[:200]}")
    
    # 测试3: Anthropic Messages API格式
    print("\n3. 测试 /v1/messages 接口 (Anthropic格式):")
    
    messages_url = "http://localhost:28889/v1/messages"
    request_data = {
        "model": "claude-4.1-opus",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this image:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": red_pixel_base64
                        }
                    }
                ]
            }
        ],
        "max_tokens": 200
    }
    
    try:
        response = requests.post(
            messages_url,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            json=request_data,
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'content' in result:
                # Anthropic格式响应
                content = result['content'][0]['text'] if result.get('content') else ''
            else:
                # 可能是错误消息
                content = str(result)
            print(f"   AI响应: {content[:300] if content else '(空响应)'}")
        else:
            print(f"   错误: {response.text[:200]}")
    except Exception as e:
        print(f"   异常: {str(e)[:200]}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    
    # 提供诊断信息
    print("\n诊断信息:")
    print(f"- API Token: {api_token}")
    print(f"- OpenAI API: {api_url}")
    print(f"- Messages API: {messages_url}")
    print(f"- 图片数据长度: {len(red_pixel_base64)} 字符")
    
    # 检查服务器健康状态
    try:
        health_response = requests.get("http://localhost:28889/healthz", timeout=5)
        print(f"- 服务器状态: {health_response.json() if health_response.status_code == 200 else '不可用'}")
    except:
        print("- 服务器状态: 连接失败")

if __name__ == "__main__":
    test_image_with_api()