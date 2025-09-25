#!/usr/bin/env python3
"""
详细的Claude API图片支持测试
测试不同格式和场景下的图片处理
"""
import asyncio
import base64
import json
import httpx
from typing import Dict, Any

def create_test_images():
    """创建多种测试图片"""
    # 1x1像素的红色PNG
    red_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )

    # 1x1像素的蓝色PNG
    blue_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFhAIAK8yATgAAAABJRU5ErkJggg=="
    )

    return {
        "red_png": base64.b64encode(red_png).decode('utf-8'),
        "blue_png": base64.b64encode(blue_png).decode('utf-8'),
    }

async def test_openai_format_image():
    """测试OpenAI格式的图片（image_url）"""
    print("Testing OpenAI format image (image_url)...")

    images = create_test_images()

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please describe this image."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{images['red_png']}"
                        }
                    }
                ]
            }
        ]
    }

    return await send_request(request_data, "openai_format")

async def test_claude_format_image():
    """测试Claude格式的图片（source）"""
    print("Testing Claude format image (source)...")

    images = create_test_images()

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please describe this image."
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": images['red_png']
                        }
                    }
                ]
            }
        ]
    }

    return await send_request(request_data, "claude_format")

async def test_mixed_content():
    """测试混合内容（文本+多张图片）"""
    print("Testing mixed content (text + multiple images)...")

    images = create_test_images()

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Compare these two images:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": images['red_png']
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
                            "data": images['blue_png']
                        }
                    },
                    {
                        "type": "text",
                        "text": "What are the differences?"
                    }
                ]
            }
        ]
    }

    return await send_request(request_data, "mixed_content")

async def test_invalid_image_data():
    """测试无效的图片数据"""
    print("Testing invalid image data...")

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please describe this image:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": "invalid_base64_data"
                        }
                    }
                ]
            }
        ]
    }

    return await send_request(request_data, "invalid_image", expect_error=True)

async def test_unsupported_media_type():
    """测试不支持的媒体类型"""
    print("Testing unsupported media type...")

    images = create_test_images()

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please describe this image:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "video/mp4",  # 不支持的类型
                            "data": images['red_png']
                        }
                    }
                ]
            }
        ]
    }

    return await send_request(request_data, "unsupported_media", expect_error=True)

async def send_request(request_data: Dict[str, Any], test_name: str, expect_error: bool = False) -> Dict[str, Any]:
    """发送请求并处理响应"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            print(f"Sending request for {test_name}...")

            # 打印请求详情
            print(f"Request model: {request_data.get('model')}")
            print(f"Request messages count: {len(request_data.get('messages', []))}")

            for i, msg in enumerate(request_data.get('messages', [])):
                content = msg.get('content', '')
                if isinstance(content, list):
                    print(f"Message {i} content blocks: {len(content)}")
                    for j, block in enumerate(content):
                        block_type = block.get('type', 'unknown')
                        print(f"  Block {j}: type={block_type}")
                        if block_type == 'image':
                            source = block.get('source', {})
                            data_len = len(source.get('data', '')) if source.get('data') else 0
                            print(f"    Image: {source.get('media_type')}, data_length={data_len}")
                        elif block_type == 'image_url':
                            url = block.get('image_url', {}).get('url', '')
                            print(f"    Image URL: {url[:50]}...")
                else:
                    print(f"Message {i} content: {str(content)[:50]}...")

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

                # 检查token使用情况
                usage = response_data.get('usage', {})
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                print(f"Token usage: input={input_tokens}, output={output_tokens}")

                # 检查响应内容
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
                if expect_error:
                    print(f"EXPECTED ERROR: {test_name} (status: {response.status_code})")
                else:
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

        if expect_error:
            print(f"EXPECTED EXCEPTION: {test_name} - {e}")
        else:
            print(f"EXCEPTION: {test_name} - {e}")

        return result

async def main():
    """主测试函数"""
    print("Starting detailed Claude API image support test")
    print("=" * 60)

    # 执行所有测试
    tests = [
        test_claude_format_image(),
        test_openai_format_image(),
        test_mixed_content(),
        test_invalid_image_data(),
        test_unsupported_media_type()
    ]

    results = await asyncio.gather(*tests, return_exceptions=True)

    # 统计结果
    total_tests = len(results)
    successful_tests = sum(1 for r in results if isinstance(r, dict) and r.get("success"))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success rate: {successful_tests/total_tests*100:.1f}%")

    # 详细结果
    print("\nDetailed Results:")
    for i, result in enumerate(results):
        if isinstance(result, dict):
            status = "PASS" if result.get("success") else "FAIL"
            print(f"{i+1}. {result.get('test_name', 'unknown')}: {status}")
            if not result.get("success") and result.get("error"):
                print(f"   Error: {result['error']}")
        else:
            print(f"{i+1}. Exception: {result}")

    if successful_tests == total_tests:
        print("\nAll tests passed! Claude API image support is fully working.")
    elif successful_tests > 0:
        print(f"\nPartial success. Some image support functionality is working.")
    else:
        print(f"\nAll tests failed. Image support functionality needs investigation.")

if __name__ == "__main__":
    asyncio.run(main())