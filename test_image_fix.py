#!/usr/bin/env python3
"""
测试图片传输修复 - 使用正确的InputContext.images字段
"""

import requests
import json
import base64
from PIL import Image
import io

def create_test_image():
    """创建一个简单的测试图片"""
    # 创建一个简单的彩色图片
    img = Image.new('RGB', (100, 100), color='red')
    
    # 转换为base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return img_base64

def test_image_transmission():
    """测试图片传输"""
    print("🧪 测试图片传输修复")
    print("=" * 50)
    
    # 创建测试图片
    print("📸 创建测试图片...")
    img_base64 = create_test_image()
    print(f"✅ 图片创建成功，base64长度: {len(img_base64)}")
    
    # 构建请求
    url = "http://localhost:28889/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-key"
    }
    
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片的内容。"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_base64
                        }
                    }
                ]
            }
        ]
    }
    
    print("🚀 发送请求...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('content', [])
            if content and len(content) > 0:
                text_content = content[0].get('text', '')
                print(f"✅ 响应成功!")
                print(f"📝 响应内容: {text_content}")
                
                # 检查是否包含图片描述
                if "红色" in text_content or "red" in text_content.lower():
                    print("🎯 成功！AI正确识别了红色图片")
                    return True
                else:
                    print("❌ AI没有正确识别图片内容")
                    print(f"实际响应: {text_content}")
                    return False
            else:
                print("❌ 响应格式异常")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    print("🔧 图片传输修复测试")
    print("=" * 60)
    
    success = test_image_transmission()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试成功！图片传输修复有效！")
    else:
        print("💥 测试失败！需要进一步调试")
    print("=" * 60)
