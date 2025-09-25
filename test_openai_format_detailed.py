#!/usr/bin/env python3
"""
详细测试OpenAI格式图片支持
"""
import asyncio
import base64
import json
import httpx

def create_test_image():
    """创建测试图片"""
    # 1x1像素红色PNG
    red_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(red_png).decode('utf-8')

async def test_openai_format():
    """测试OpenAI格式图片"""
    print("Testing OpenAI format image...")

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
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            print("Sending OpenAI format request...")
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

                # 打印完整响应
                print("Full response:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))

                # 提取响应内容
                content_blocks = response_data.get("content", [])
                if content_blocks:
                    for i, block in enumerate(content_blocks):
                        if block.get("type") == "text":
                            text = block.get("text", "")
                            print(f"\nResponse text:")
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

if __name__ == "__main__":
    print("Testing OpenAI format image support")
    print("=" * 50)
    asyncio.run(test_openai_format())