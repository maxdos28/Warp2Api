#!/usr/bin/env python3
"""
测试用户发送的实际图片处理
"""
import asyncio
import httpx
import json

async def test_user_image_processing():
    """测试实际图片处理能力"""
    print("Testing actual image processing capability...")

    # 创建一个简单的测试请求，看看系统如何处理图片
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 500,
        "messages": [
            {
                "role": "user",
                "content": "请详细描述您看到的图片内容。这是什么类型的图表、架构图或者其他内容？请具体说明图片中的文字、结构、颜色等细节。"
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
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [])
                if content and content[0].get("type") == "text":
                    text = content[0].get("text", "")
                    print(f"API Response: {text}")

                    # 检查是否提到了图片
                    if "图片" in text or "image" in text.lower():
                        print("\n✅ API认为有图片")
                    else:
                        print("\n❌ API没有识别到图片")

                    # 检查是否提到了DDD或架构
                    if "ddd" in text.lower() or "架构" in text or "layer" in text.lower() or "领域" in text:
                        print("✅ 正确识别了DDD架构内容")
                    else:
                        print("❌ 没有识别到DDD架构内容")

            else:
                print(f"Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

async def test_with_explicit_image():
    """使用明确的图片数据测试"""
    print("\n" + "="*50)
    print("Testing with explicit image data...")

    # 使用一个包含更多信息的测试图片（如果有的话）
    # 这里我们测试系统是否能正确处理图片请求格式

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请分析这张DDD架构图，说明各个层次的作用和关系。"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
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
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [])
                if content and content[0].get("type") == "text":
                    text = content[0].get("text", "")
                    print(f"Response: {text}")

                    # 分析响应
                    if "ddd" in text.lower() or "领域驱动" in text or "架构" in text:
                        print("\n⚠️ 警告：AI可能在根据提示词猜测，而不是真正看到图片")
                    elif "1x1" in text or "像素" in text or "红色" in text:
                        print("\n✅ AI正确识别了测试图片内容")
                    else:
                        print("\n❓ 响应不明确")

            else:
                print(f"Error: {response.status_code}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Testing user image processing")
    print("=" * 60)

    asyncio.run(test_user_image_processing())
    asyncio.run(test_with_explicit_image())