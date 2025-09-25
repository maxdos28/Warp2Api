#!/usr/bin/env python3
"""
测试图片支持并查看详细日志
"""
import asyncio
import base64
import json
import httpx
from typing import Dict, Any

def create_test_image():
    """创建测试图片"""
    # 1x1像素红色PNG
    red_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(red_png).decode('utf-8')

async def test_claude_format_with_logs():
    """测试Claude格式并查看详细响应"""
    print("Testing Claude format with detailed logging...")

    image_data = create_test_image()

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please analyze this image in detail. What do you see? What colors, shapes, or objects are present?"
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
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            print("Sending Claude format request...")
            response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=request_data,
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
            )

            print(f"Response status: {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()

                # 打印完整响应结构
                print("Full response structure:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))

                # 提取响应内容
                content_blocks = response_data.get("content", [])
                if content_blocks:
                    for i, block in enumerate(content_blocks):
                        if block.get("type") == "text":
                            text = block.get("text", "")
                            print(f"\nResponse text block {i}:")
                            print(text)

                # 检查token使用情况
                usage = response_data.get("usage", {})
                print(f"\nToken usage:")
                print(f"  Input tokens: {usage.get('input_tokens', 0)}")
                print(f"  Output tokens: {usage.get('output_tokens', 0)}")

            else:
                print(f"Error response: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

async def test_simple_text():
    """测试简单文本作为对比"""
    print("\n" + "="*50)
    print("Testing simple text for comparison...")

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Please respond with 'Hello, I can see your message clearly.'"
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
                response_data = response.json()
                content_blocks = response_data.get("content", [])
                if content_blocks and content_blocks[0].get("type") == "text":
                    print(f"Text response: {content_blocks[0].get('text', '')}")
            else:
                print(f"Error: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Testing image support with detailed logging")
    print("=" * 60)

    asyncio.run(test_claude_format_with_logs())
    asyncio.run(test_simple_text())