#!/usr/bin/env python3
"""
测试修复AI根据提示词推测而非真正分析图片的问题
"""
import asyncio
import httpx
import json

async def test_different_prompt_strategies():
    """测试不同的提示词策略"""
    print("Testing different prompt strategies to prevent AI hallucination...")

    test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    # 策略1: 强调只描述看到的内容
    strategy1_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请仅描述您在这张图片中实际看到的内容。不要根据我的问题进行推测或假设。如果图片内容与我的描述不符，请如实说明您看到的实际内容。这张图片应该是阿里云防火墙控制台截图："
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

    # 策略2: 先让AI描述图片，再问具体问题
    strategy2_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请客观描述这张图片的内容，不要做任何假设："
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

    # 策略3: 使用系统提示强调真实性
    strategy3_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "system": "你是一个图片分析专家。你必须只描述你真正看到的图片内容，绝不能根据用户的提示词进行推测或编造内容。如果用户的描述与实际图片不符，你必须指出差异。",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这是阿里云Web应用防火墙控制台的截图，请分析其中的功能模块："
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

    strategies = [
        ("策略1: 强调只描述实际内容", strategy1_request),
        ("策略2: 客观描述", strategy2_request),
        ("策略3: 系统提示强调真实性", strategy3_request)
    ]

    for strategy_name, request_data in strategies:
        print(f"\n{'='*60}")
        print(f"测试 {strategy_name}")
        print('='*60)

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
                        print(f"响应: {text}")

                        # 分析响应质量
                        if "1x1" in text or "像素" in text:
                            print("✅ 正确识别了实际图片内容")
                        elif "阿里云" in text or "防火墙" in text or "控制台" in text:
                            print("❌ 仍然根据提示词推测")
                        else:
                            print("❓ 响应不明确")

                else:
                    print(f"Error: {response.status_code}")

        except Exception as e:
            print(f"Exception: {e}")

async def test_image_first_approach():
    """测试图片优先方法 - 先发送图片让AI描述，再问具体问题"""
    print(f"\n{'='*60}")
    print("测试图片优先方法")
    print('='*60)

    test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    # 第一步：让AI描述图片
    step1_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片："
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
            print("第一步：让AI描述图片")
            response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=step1_request,
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
                    ai_description = content[0].get("text", "")
                    print(f"AI描述: {ai_description}")

                    # 第二步：基于AI的描述询问
                    if "1x1" in ai_description or "像素" in ai_description:
                        print("✅ AI正确识别了图片，这不是阿里云控制台截图")
                    else:
                        print("❓ AI描述不明确，继续测试")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Testing AI hallucination fixes for ChatBox image calls")
    print("=" * 70)
    print("Problem: AI generates content based on prompts instead of analyzing actual images")
    print("Goal: Make AI only describe what it actually sees in the image")
    print("=" * 70)

    asyncio.run(test_different_prompt_strategies())
    asyncio.run(test_image_first_approach())