#!/usr/bin/env python3
"""
测试 /v1/messages 端点的图片支持功能
"""
import asyncio
import base64
import json
import httpx
from io import BytesIO
from PIL import Image

def create_test_image():
    """创建一个简单的测试图片"""
    # 创建一个简单的测试图片
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

def create_test_image_data_url():
    """创建测试图片的data URL"""
    img_data = create_test_image()
    img_b64 = base64.b64encode(img_data).decode('utf-8')
    return f"data:image/png;base64,{img_b64}"

async def test_image_support():
    """测试图片支持功能"""
    print("🖼️ 测试 /v1/messages 图片支持...")
    
    # 创建测试图片
    print("📸 创建测试图片...")
    image_data_url = create_test_image_data_url()
    print(f"✅ 测试图片创建完成，大小: {len(image_data_url)} 字符")
    
    # 测试请求数据
    test_request = {
        "model": "claude-4-sonnet",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片的内容"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url,
                            "detail": "auto"
                        }
                    }
                ]
            }
        ]
    }
    
    print(f"\n📤 发送测试请求...")
    print(f"请求内容: {json.dumps(test_request, indent=2, ensure_ascii=False)}")
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=test_request,
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json"
                }
            )
            
            print(f"\n📊 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 请求成功!")
                print(f"📝 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # 检查响应中是否包含图片相关信息
                content = result.get("content", [])
                if content:
                    print(f"\n🔍 分析响应内容:")
                    for i, block in enumerate(content):
                        print(f"  块 {i}: {block}")
                        
                        if block.get("type") == "text":
                            text = block.get("text", "")
                            if "图片" in text or "image" in text.lower():
                                print(f"  ✅ 检测到图片相关内容: {text[:100]}...")
                            else:
                                print(f"  ⚠️ 未检测到图片相关内容: {text[:100]}...")
            else:
                print(f"❌ 请求失败")
                error_text = response.text
                print(f"错误内容: {error_text}")
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")

async def test_text_only():
    """测试纯文本消息（作为对比）"""
    print(f"\n📝 测试纯文本消息（对比）...")
    
    test_request = {
        "model": "claude-4-sonnet",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": "请说你好"
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=test_request,
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json"
                }
            )
            
            print(f"📊 纯文本响应状态: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 纯文本请求成功!")
                content = result.get("content", [])
                if content and content[0].get("type") == "text":
                    print(f"📝 纯文本响应: {content[0].get('text', '')[:100]}...")
            else:
                print(f"❌ 纯文本请求失败: {response.text}")
                
    except Exception as e:
        print(f"❌ 纯文本请求异常: {e}")

async def main():
    print("🚀 开始图片支持测试...")
    
    # 测试纯文本消息
    await test_text_only()
    
    # 测试图片消息
    await test_image_support()
    
    print(f"\n💡 测试完成!")
    print(f"如果图片支持正常工作，您应该看到:")
    print(f"1. 图片请求成功返回")
    print(f"2. 响应中包含对图片的描述或分析")
    print(f"3. 没有 '[Image content not supported]' 这样的错误信息")

if __name__ == "__main__":
    asyncio.run(main())
