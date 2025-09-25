#!/usr/bin/env python3
"""
Basic Claude API image support test
Test /v1/messages endpoint image processing functionality
"""
import asyncio
import base64
import json
import httpx
from typing import Dict, Any

def create_test_image():
    """Create a simple test image"""
    # 1x1 pixel red PNG
    red_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(red_png).decode('utf-8')

async def test_text_only():
    """Test basic text message"""
    print("Testing basic text message...")

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Hello! Please respond with a simple greeting."
            }
        ]
    }

    return await send_request(request_data, "text_only")

async def test_single_image():
    """Test single image"""
    print("Testing single image...")

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
                        "text": "Please describe this image. This is a simple test image."
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

    return await send_request(request_data, "single_image")

async def send_request(request_data: Dict[str, Any], test_name: str) -> Dict[str, Any]:
    """Send request and handle response"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            print(f"Sending request for {test_name}...")
            response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=request_data,
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
            )

            result = {
                "test_name": test_name,
                "status_code": response.status_code,
                "success": False,
                "error": None,
                "response_data": None
            }

            if response.status_code == 200:
                response_data = response.json()
                result["success"] = True
                result["response_data"] = response_data

                print(f"SUCCESS: {test_name}")
                print(f"Response keys: {list(response_data.keys())}")

                # Check response format
                if "content" in response_data:
                    content_blocks = response_data["content"]
                    if content_blocks and isinstance(content_blocks, list):
                        text_content = ""
                        for block in content_blocks:
                            if block.get("type") == "text":
                                text_content += block.get("text", "")

                        print(f"Response length: {len(text_content)} characters")
                        if text_content:
                            print(f"Response preview: {text_content[:100]}...")
                    else:
                        print(f"WARNING: {test_name} - abnormal response format")
                else:
                    print(f"WARNING: {test_name} - missing content field")

            else:
                result["error"] = response.text
                print(f"FAILED: {test_name} (status: {response.status_code})")
                print(f"Error: {response.text}")

            return result

    except Exception as e:
        result = {
            "test_name": test_name,
            "status_code": None,
            "success": False,
            "error": str(e),
            "response_data": None
        }

        print(f"EXCEPTION: {test_name} - {e}")
        return result

async def main():
    """Main test function"""
    print("Starting Claude API image support test")
    print("=" * 50)

    # Run tests
    tests = [
        test_text_only(),
        test_single_image()
    ]

    results = await asyncio.gather(*tests, return_exceptions=True)

    # Summary
    total_tests = len(results)
    successful_tests = sum(1 for r in results if isinstance(r, dict) and r.get("success"))

    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success rate: {successful_tests/total_tests*100:.1f}%")

    if successful_tests == total_tests:
        print("\nAll tests passed! Claude API image support is working.")
    elif successful_tests > 0:
        print(f"\nPartial success. Some image support functionality is working.")
    else:
        print(f"\nAll tests failed. Image support functionality needs investigation.")

if __name__ == "__main__":
    asyncio.run(main())