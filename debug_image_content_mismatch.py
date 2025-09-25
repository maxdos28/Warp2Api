#!/usr/bin/env python3
"""
调试图片内容识别错误问题
"""
import asyncio
import httpx
import json

async def test_image_content_accuracy():
    """测试图片内容识别准确性"""
    print("Testing image content recognition accuracy...")

    # 测试1: 使用明确的提示词，不暗示任何特定内容
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 400,
        "messages": [
            {
                "role": "user",
                "content": "请客观描述这张图片中的具体内容。不要猜测，只描述你真正看到的内容。包括：界面类型、文字内容、按钮、颜色、布局等具体细节。"
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

                    # 分析响应内容
                    keywords_found = []
                    if "阿里云" in text or "aliyun" in text.lower():
                        keywords_found.append("阿里云")
                    if "防火墙" in text or "firewall" in text.lower():
                        keywords_found.append("防火墙")
                    if "控制台" in text or "console" in text.lower():
                        keywords_found.append("控制台")
                    if "web" in text.lower():
                        keywords_found.append("Web")
                    if "ddd" in text.lower() or "领域驱动" in text or "架构" in text:
                        keywords_found.append("DDD架构(错误)")

                    print(f"\n识别到的关键词: {keywords_found}")

                    if "阿里云" in keywords_found and "防火墙" in keywords_found:
                        print("✅ 正确识别了阿里云防火墙内容")
                    elif "DDD架构(错误)" in keywords_found:
                        print("❌ 错误识别为DDD架构")
                    else:
                        print("❓ 识别结果不明确")

            else:
                print(f"Error: {response.status_code}")

    except Exception as e:
        print(f"Exception: {e}")

async def test_without_leading_questions():
    """测试不带引导性问题的图片识别"""
    print("\n" + "="*50)
    print("Testing without leading questions...")

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": "这是什么？"
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
                    print(f"Simple question response: {text}")

            else:
                print(f"Error: {response.status_code}")

    except Exception as e:
        print(f"Exception: {e}")

async def test_explicit_image_data():
    """测试明确的图片数据传递"""
    print("\n" + "="*50)
    print("Testing with explicit image data...")

    # 使用一个已知的测试图片
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这张图片显示的是什么？"
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
                    print(f"Explicit image response: {text}")

                    if "1x1" in text or "像素" in text or "红色" in text:
                        print("✅ 正确识别了测试图片")
                    elif "阿里云" in text or "防火墙" in text:
                        print("❌ 仍然显示错误的图片内容")
                    else:
                        print("❓ 响应不明确")

            else:
                print(f"Error: {response.status_code}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Debugging image content recognition mismatch")
    print("=" * 60)
    print("Expected: Alibaba Cloud WAF Console Screenshot")
    print("Actual: DDD Architecture Diagram")
    print("=" * 60)

    asyncio.run(test_image_content_accuracy())
    asyncio.run(test_without_leading_questions())
    asyncio.run(test_explicit_image_data())