#!/usr/bin/env python3
"""
测试阿里云防火墙图片的解析
"""
import asyncio
import base64
import httpx
import json

async def test_ali_image():
    """测试阿里云图片解析"""
    print("Testing Alibaba Cloud WAF image recognition...")

    # 读取并编码图片
    try:
        with open("D:\\Warp2Api\\ali.png", "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        print(f"Image loaded, base64 length: {len(image_data)}")
    except Exception as e:
        print(f"Failed to load image: {e}")
        return

    # 发送请求
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 500,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请详细描述这张图片中显示的内容，包括界面类型、文字、数字、功能模块等具体信息。"
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
                    print(f"\nAI Response:\n{text}")

                    # 检查关键词识别
                    keywords_found = []
                    expected_keywords = ["Web应用防火墙", "阿里云", "防护", "CLB", "ECS", "API安全", "BOT管理", "RASP"]

                    for keyword in expected_keywords:
                        if keyword in text:
                            keywords_found.append(keyword)

                    print(f"\n识别到的关键词: {keywords_found}")
                    print(f"识别准确率: {len(keywords_found)}/{len(expected_keywords)} ({len(keywords_found)/len(expected_keywords)*100:.1f}%)")

                    # 检查数字识别
                    numbers_in_image = ["605.0 K", "11.6 K", "3", "6", "0"]
                    numbers_found = []
                    for num in numbers_in_image:
                        if num in text:
                            numbers_found.append(num)

                    print(f"识别到的数字: {numbers_found}")

                    # Token使用情况
                    usage = data.get("usage", {})
                    print(f"\nToken usage: input={usage.get('input_tokens', 0)}, output={usage.get('output_tokens', 0)}")

                else:
                    print("ERROR: No text content in response")
            else:
                print(f"ERROR: HTTP {response.status_code}")
                print(f"Response: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_ali_image())