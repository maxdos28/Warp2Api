#!/usr/bin/env python3
"""
简单图片测试 - 验证图片传输是否工作
"""

import requests
import json
import base64

def test_simple_image():
    """测试简单的图片传输"""
    print("🧪 简单图片传输测试")
    print("=" * 40)
    
    # 使用一个非常简单的1x1红色像素图片
    red_pixel_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    url = "http://localhost:28889/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }
    
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 500,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片。这是一个1x1的红色像素图片。"
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
        ]
    }
    
    print(f"📤 发送请求...")
    print(f"   - 图片数据长度: {len(red_pixel_base64)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('content', [])
            if content and len(content) > 0:
                text_content = content[0].get('text', '')
                print(f"\n📝 AI响应:")
                print(f"   {text_content}")
                
                # 检查是否包含图片描述
                if "红色" in text_content or "red" in text_content.lower():
                    print("\n✅ 成功！AI正确识别了红色图片")
                    return True
                elif "无法" in text_content or "看不到" in text_content or "cannot" in text_content.lower():
                    print("\n❌ AI仍然无法看到图片")
                    return False
                else:
                    print("\n⚠️ AI响应了，但没有明确描述图片")
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
    print("🔧 简单图片传输测试")
    print("=" * 50)
    
    success = test_simple_image()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试成功！图片传输工作正常！")
    else:
        print("💥 测试失败！图片传输仍有问题")
    print("=" * 50)
