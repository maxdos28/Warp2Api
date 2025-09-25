#!/usr/bin/env python3
"""
测试多图片处理功能
"""
import asyncio
import base64
import json
import httpx

def create_test_images():
    """创建多个测试图片"""
    # 1x1像素红色PNG
    red_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )

    # 1x1像素蓝色PNG
    blue_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFhAIAK8yATgAAAABJRU5ErkJggg=="
    )

    return {
        "red": base64.b64encode(red_png).decode('utf-8'),
        "blue": base64.b64encode(blue_png).decode('utf-8'),
    }

async def test_multiple_images():
    """测试多图片处理"""
    print("Testing multiple images...")

    images = create_test_images()

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 400,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please compare these two images and tell me the differences:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": images["red"]
                        }
                    },
                    {
                        "type": "text",
                        "text": "and"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": images["blue"]
                        }
                    },
                    {
                        "type": "text",
                        "text": "What are the main differences between these two images?"
                    }
                ]
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            print("Sending multiple images request...")
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

                # 检查是否正确识别了两张图片
                response_text = content_blocks[0].get("text", "") if content_blocks else ""
                if "red" in response_text.lower() and "blue" in response_text.lower():
                    print("\n✅ SUCCESS: AI correctly identified both red and blue images!")
                elif "two" in response_text.lower() or "both" in response_text.lower():
                    print("\n✅ SUCCESS: AI recognized multiple images!")
                else:
                    print("\n⚠️ PARTIAL: AI response doesn't clearly indicate recognition of both images")

            else:
                print(f"Error response: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

async def test_mixed_formats():
    """测试混合格式（Claude + OpenAI）"""
    print("\n" + "="*50)
    print("Testing mixed formats (Claude + OpenAI)...")

    images = create_test_images()

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 400,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Compare these two images - one in Claude format and one in OpenAI format:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": images["red"]
                        }
                    },
                    {
                        "type": "text",
                        "text": "versus"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{images['blue']}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
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
                if content_blocks:
                    text = content_blocks[0].get("text", "")
                    print(f"Mixed format response:")
                    print(text)

                    # 检查是否识别了两种格式的图片
                    if ("red" in text.lower() or "blue" in text.lower()) and ("two" in text.lower() or "both" in text.lower()):
                        print("\n✅ SUCCESS: Mixed format images processed correctly!")
                    else:
                        print("\n⚠️ PARTIAL: Mixed format processing may have issues")

            else:
                print(f"Error: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Testing multiple images support")
    print("=" * 60)

    asyncio.run(test_multiple_images())
    asyncio.run(test_mixed_formats())