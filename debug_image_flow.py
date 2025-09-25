#!/usr/bin/env python3
"""
彻底诊断图片数据流 - 追踪每一步的数据变化
"""

import requests
import json
import base64
import hashlib

def create_simple_test_image():
    """创建一个简单的测试图片 - 使用预定义的base64数据"""
    # 创建一个1x1的红色像素图片的base64数据
    # 这是一个最小的PNG图片，包含一个红色像素
    red_pixel_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    # 计算hash用于验证
    img_bytes = base64.b64decode(red_pixel_base64)
    img_hash = hashlib.md5(img_bytes).hexdigest()
    
    print(f"🔍 测试图片详情:")
    print(f"   - 类型: 1x1红色像素PNG")
    print(f"   - Base64长度: {len(red_pixel_base64)}")
    print(f"   - MD5: {img_hash}")
    
    return red_pixel_base64, img_hash

def test_image_flow():
    """测试完整的图片数据流"""
    print("🔍 开始图片数据流诊断")
    print("=" * 60)
    
    # 1. 创建测试图片
    print("📸 步骤1: 创建测试图片")
    img_base64, expected_hash = create_simple_test_image()
    
    # 2. 构建请求
    print("\n📤 步骤2: 构建API请求")
    url = "http://localhost:28889/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
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
                        "text": f"请详细描述这张图片。这是一个1x1的红色像素图片。图片MD5应该是: {expected_hash}"
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
    
    print(f"📊 请求详情:")
    print(f"   - URL: {url}")
    print(f"   - 图片数据长度: {len(img_base64)}")
    print(f"   - 期望MD5: {expected_hash}")
    
    # 3. 发送请求
    print("\n🚀 步骤3: 发送请求")
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
                
                # 4. 分析响应
                print(f"\n🔍 步骤4: 分析AI响应")
                
                # 检查关键词
                keywords = ["红色", "red", "像素", "pixel", "1x1"]
                found_keywords = [kw for kw in keywords if kw in text_content.lower()]
                
                if found_keywords:
                    print(f"✅ 找到相关关键词: {found_keywords}")
                else:
                    print(f"❌ 没有找到预期的关键词")
                
                # 检查是否提到MD5
                if expected_hash in text_content:
                    print(f"✅ AI提到了正确的MD5: {expected_hash}")
                else:
                    print(f"❌ AI没有提到正确的MD5")
                
                # 检查是否描述了错误的内容
                wrong_keywords = ["任务", "待办", "todo", "任务清单", "task"]
                wrong_found = [kw for kw in wrong_keywords if kw in text_content.lower()]
                
                if wrong_found:
                    print(f"⚠️ 发现错误描述关键词: {wrong_found}")
                    print(f"   AI可能看到了错误的图片或缓存数据！")
                
                return {
                    "success": True,
                    "response": text_content,
                    "found_keywords": found_keywords,
                    "wrong_keywords": wrong_found,
                    "mentioned_md5": expected_hash in text_content
                }
            else:
                print("❌ 响应格式异常")
                return {"success": False, "error": "响应格式异常"}
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("🔍 图片数据流诊断工具")
    print("=" * 60)
    
    result = test_image_flow()
    
    print("\n" + "=" * 60)
    print("📊 诊断结果:")
    print(f"   - 请求成功: {result.get('success', False)}")
    if result.get('success'):
        print(f"   - 找到关键词: {result.get('found_keywords', [])}")
        print(f"   - 错误关键词: {result.get('wrong_keywords', [])}")
        print(f"   - 提到MD5: {result.get('mentioned_md5', False)}")
        
        if result.get('wrong_keywords'):
            print("\n🚨 问题诊断:")
            print("   AI看到了错误的图片内容！")
            print("   可能原因:")
            print("   1. 图片数据在传输过程中被替换")
            print("   2. AI模型有缓存，看到了之前的图片")
            print("   3. 会话状态被污染")
            print("   4. Protobuf字段映射错误")
    else:
        print(f"   - 错误: {result.get('error', 'Unknown')}")
    
    print("=" * 60)
