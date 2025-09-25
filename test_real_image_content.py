#!/usr/bin/env python3
"""
测试真实图片内容处理
"""
import asyncio
import base64
import httpx

async def test_with_real_image():
    """使用您提到的DDD架构图进行测试"""
    print("Testing with actual image content...")

    # 请您提供实际的图片base64数据，或者我们使用一个更复杂的测试图片
    # 这里我先用一个稍微复杂一点的测试图片

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片的内容。这是什么类型的图表或架构图？"
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

                    # 检查是否提到了DDD或架构
                    if "ddd" in text.lower() or "架构" in text.lower() or "layer" in text.lower():
                        print("WARNING: AI is seeing different image content than expected!")
                        print("This suggests there might be image data corruption or caching issues.")
                    else:
                        print("Response seems consistent with test image.")

            else:
                print(f"Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

async def test_claude_vs_openai_same_image():
    """对比Claude和OpenAI格式处理同一张图片"""
    print("\nComparing Claude vs OpenAI format with same image...")

    # 使用相同的图片数据
    image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    # Claude格式
    claude_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in detail."
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

    # OpenAI格式
    openai_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in detail."
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
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            # 测试Claude格式
            print("Claude format:")
            claude_response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=claude_request,
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
            )

            if claude_response.status_code == 200:
                data = claude_response.json()
                content = data.get("content", [])
                if content:
                    print(f"  {content[0].get('text', '')}")
            else:
                print(f"  Error: {claude_response.status_code}")

            print("\nOpenAI format:")
            openai_response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=openai_request,
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
            )

            if openai_response.status_code == 200:
                data = openai_response.json()
                content = data.get("content", [])
                if content:
                    print(f"  {content[0].get('text', '')}")
            else:
                print(f"  Error: {openai_response.status_code}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Testing real image content processing")
    print("=" * 50)

    asyncio.run(test_with_real_image())
    asyncio.run(test_claude_vs_openai_same_image())