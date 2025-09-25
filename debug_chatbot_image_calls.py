#!/usr/bin/env python3
"""
调试ChatBot调用/v1/messages接口的图片处理问题
模拟ChatBot的调用方式
"""
import asyncio
import base64
import httpx
import json

def create_chatbot_style_request():
    """创建ChatBot风格的请求"""
    # ChatBot通常使用OpenAI格式的image_url
    # 模拟ChatBot发送阿里云防火墙截图的请求

    # 使用一个测试图片模拟ChatBot的调用
    test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    return {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 400,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请分析这张阿里云Web应用防火墙控制台的截图，说明界面中的功能模块和配置选项。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{test_image_data}"
                        }
                    }
                ]
            }
        ]
    }

async def test_chatbot_image_call():
    """测试ChatBot风格的图片调用"""
    print("Testing ChatBot-style image call...")

    request_data = create_chatbot_style_request()

    # 打印请求详情
    print("Request details:")
    print(f"- Model: {request_data['model']}")
    print(f"- Messages count: {len(request_data['messages'])}")

    for i, msg in enumerate(request_data['messages']):
        content = msg.get('content', [])
        print(f"- Message {i} content blocks: {len(content)}")
        for j, block in enumerate(content):
            block_type = block.get('type', 'unknown')
            print(f"  Block {j}: {block_type}")
            if block_type == 'image_url':
                url = block.get('image_url', {}).get('url', '')
                print(f"    URL prefix: {url[:50]}...")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            print("\nSending ChatBot-style request...")
            response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=request_data,
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                    "User-Agent": "ChatBot/1.0"
                }
            )

            print(f"Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [])
                if content and content[0].get("type") == "text":
                    text = content[0].get("text", "")
                    print(f"\nAPI Response:")
                    print("=" * 60)
                    print(text)
                    print("=" * 60)

                    # 分析响应内容
                    print("\n分析响应内容:")

                    # 检查是否正确识别了图片
                    if "图片" in text or "image" in text.lower():
                        print("✅ API识别到了图片")
                    else:
                        print("❌ API没有识别到图片")

                    # 检查是否出现了错误的内容识别
                    wrong_content_indicators = [
                        "ddd", "领域驱动", "架构图", "分层架构", "domain driven"
                    ]

                    found_wrong_content = []
                    for indicator in wrong_content_indicators:
                        if indicator in text.lower():
                            found_wrong_content.append(indicator)

                    if found_wrong_content:
                        print(f"❌ 发现错误内容识别: {found_wrong_content}")
                        print("   这表明存在图片内容混乱或缓存问题")

                    # 检查是否正确识别了测试图片
                    correct_indicators = ["1x1", "像素", "红色", "pixel", "red"]
                    found_correct = []
                    for indicator in correct_indicators:
                        if indicator in text.lower():
                            found_correct.append(indicator)

                    if found_correct:
                        print(f"✅ 正确识别了测试图片: {found_correct}")

                    # 检查是否提到了阿里云（这应该是错误的，因为我们发送的是测试图片）
                    aliyun_indicators = ["阿里云", "alibaba", "aliyun", "防火墙", "控制台"]
                    found_aliyun = []
                    for indicator in aliyun_indicators:
                        if indicator in text.lower():
                            found_aliyun.append(indicator)

                    if found_aliyun:
                        print(f"❌ 错误提到了阿里云内容: {found_aliyun}")
                        print("   这说明AI可能根据提示词推测而不是真正看图片")

                    # 检查token使用
                    usage = data.get("usage", {})
                    print(f"\nToken使用: 输入={usage.get('input_tokens', 0)}, 输出={usage.get('output_tokens', 0)}")

            else:
                print(f"Error response: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

async def test_chatbot_without_leading_prompt():
    """测试ChatBot调用但不带引导性提示"""
    print("\n" + "="*60)
    print("Testing ChatBot call without leading prompt...")

    test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片的内容。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{test_image_data}"
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
                    print(f"Response without leading prompt:")
                    print(text)

                    # 这个测试应该正确识别1x1红色像素
                    if "1x1" in text or "像素" in text or "红色" in text:
                        print("✅ 正确识别了实际图片内容")
                    else:
                        print("❌ 图片内容识别有问题")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Debugging ChatBot calls to /v1/messages with images")
    print("=" * 70)
    print("Issue: ChatBot sends image but gets wrong content recognition")
    print("Expected: Correct image analysis")
    print("Actual: Wrong content or AI hallucination")
    print("=" * 70)

    asyncio.run(test_chatbot_image_call())
    asyncio.run(test_chatbot_without_leading_prompt())