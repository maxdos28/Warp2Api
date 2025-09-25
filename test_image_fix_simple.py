#!/usr/bin/env python3
"""
Simple image test to verify the fix
"""
import asyncio
import httpx
import json

async def test_image_recognition():
    """Test image recognition with a simple request"""
    print("Testing image recognition fix...")

    # Test with explicit image data (1x1 red pixel)
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What do you see in this image?"
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

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [])
                if content and content[0].get("type") == "text":
                    text = content[0].get("text", "")
                    print(f"Response: {text}")

                    # Check if it correctly identifies the test image
                    if "1x1" in text or "pixel" in text or "red" in text.lower():
                        print("SUCCESS: Correctly identified test image")
                    else:
                        print("INFO: Response received but content unclear")

                    # Check token usage
                    usage = data.get("usage", {})
                    print(f"Token usage: input={usage.get('input_tokens', 0)}, output={usage.get('output_tokens', 0)}")
                else:
                    print("ERROR: No text content in response")
            else:
                print(f"ERROR: HTTP {response.status_code}")
                print(f"Response: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_image_recognition())