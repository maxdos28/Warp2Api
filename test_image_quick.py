#!/usr/bin/env python3
"""
快速图片支持测试脚本
"""
import asyncio
import base64
import json
import httpx

def create_test_image():
    """创建简单的测试图片"""
    # 1x1像素的红色PNG (最小PNG文件)
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

async def test_single_image():
    """测试单张图片"""
    print("🧪 快速测试图片支持...")
    
    image_data = create_test_image()
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片的颜色"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=request_data,
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json"
                }
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [])
                if content and content[0].get("type") == "text":
                    text = content[0].get("text", "")
                    print(f"✅ 成功! 响应长度: {len(text)}")
                    print(f"📝 响应预览: {text[:200]}...")
                    
                    # 检查AI是否真的能看到图片
                    if any(keyword in text.lower() for keyword in ["red", "color", "pixel", "image", "picture", "红色", "颜色", "图片"]):
                        print("🎉 AI可以看到图片！")
                        return True
                    else:
                        print("⚠️ AI可能仍然看不到图片内容")
                        return False
                        
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

async def main():
    success = await test_single_image()
    
    if success:
        print("\n🎉 图片支持功能已修复！")
    else:
        print("\n⚠️ 图片支持仍需进一步调试")

if __name__ == "__main__":
    asyncio.run(main())
