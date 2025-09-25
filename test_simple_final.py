#!/usr/bin/env python3
"""
简化的最终测试
"""
import asyncio
import base64
import httpx

async def test_claude_image():
    """测试Claude格式图片"""
    # 1x1像素红色PNG
    red_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    image_data = base64.b64encode(red_png).decode('utf-8')

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 150,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What color is this image?"
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
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [])
                if content and content[0].get("type") == "text":
                    text = content[0].get("text", "")
                    print(f"Claude format response: {text}")

                    if "red" in text.lower():
                        print("SUCCESS: Claude format correctly identified red color!")
                        return True
                    else:
                        print("PARTIAL: Claude format responded but didn't identify color")
                        return False
            else:
                print(f"Claude format failed: {response.status_code}")
                return False

    except Exception as e:
        print(f"Claude format exception: {e}")
        return False

async def test_openai_image():
    """测试OpenAI格式图片"""
    # 1x1像素红色PNG
    red_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    image_data = base64.b64encode(red_png).decode('utf-8')

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 150,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What color is this image?"
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
                    print(f"OpenAI format response: {text}")

                    if "red" in text.lower() or "1x1" in text.lower():
                        print("SUCCESS: OpenAI format correctly processed image!")
                        return True
                    else:
                        print("PARTIAL: OpenAI format responded but processing unclear")
                        return False
            else:
                print(f"OpenAI format failed: {response.status_code}")
                return False

    except Exception as e:
        print(f"OpenAI format exception: {e}")
        return False

async def main():
    print("Final Image Support Test")
    print("=" * 40)

    claude_success = await test_claude_image()
    print()
    openai_success = await test_openai_image()

    print("\n" + "=" * 40)
    print("Summary:")
    print(f"Claude format: {'PASS' if claude_success else 'FAIL'}")
    print(f"OpenAI format: {'PASS' if openai_success else 'FAIL'}")

    if claude_success and openai_success:
        print("\nImage support is working for both formats!")
    elif claude_success or openai_success:
        print("\nImage support is partially working.")
    else:
        print("\nImage support needs more work.")

if __name__ == "__main__":
    asyncio.run(main())