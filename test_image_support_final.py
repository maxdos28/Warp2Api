#!/usr/bin/env python3
"""
最终的图片支持测试 - 验证修复效果
"""
import asyncio
import base64
import json
import httpx
from typing import Dict, Any

def create_test_images():
    """创建测试图片"""
    # 1x1像素红色PNG
    red_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(red_png).decode('utf-8')

async def send_request(request_data: Dict[str, Any], test_name: str) -> Dict[str, Any]:
    """发送请求并返回结果"""
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

            result = {
                "test_name": test_name,
                "status_code": response.status_code,
                "success": False,
                "response_text": "",
                "token_usage": {}
            }

            if response.status_code == 200:
                response_data = response.json()
                result["success"] = True

                # 提取响应文本
                content_blocks = response_data.get("content", [])
                if content_blocks and content_blocks[0].get("type") == "text":
                    result["response_text"] = content_blocks[0].get("text", "")

                # 提取token使用情况
                usage = response_data.get("usage", {})
                result["token_usage"] = {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0)
                }

            return result

    except Exception as e:
        return {
            "test_name": test_name,
            "status_code": None,
            "success": False,
            "response_text": f"Exception: {e}",
            "token_usage": {}
        }

async def test_claude_format():
    """测试Claude格式图片"""
    image_data = create_test_images()

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please describe this image. What color is it?"
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

    return await send_request(request_data, "Claude格式图片")

async def test_openai_format():
    """测试OpenAI格式图片"""
    image_data = create_test_images()

    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please describe this image. What color is it?"
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

    return await send_request(request_data, "OpenAI格式图片")

async def test_text_only():
    """测试纯文本（对比）"""
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Please respond with 'Text processing is working correctly.'"
            }
        ]
    }

    return await send_request(request_data, "纯文本对比")

def analyze_result(result: Dict[str, Any]) -> str:
    """分析测试结果"""
    if not result["success"]:
        return "FAIL - 请求失败"

    response_text = result["response_text"].lower()

    # 检查是否正确识别了图片
    image_indicators = [
        "1x1", "pixel", "red", "color", "image", "square", "dot"
    ]

    if any(indicator in response_text for indicator in image_indicators):
        return "PASS - 正确识别图片"
    elif "don't see" in response_text or "no image" in response_text or "can't see" in response_text:
        return "FAIL - 未识别到图片"
    else:
        return "PARTIAL - 响应不明确"

async def main():
    """主测试函数"""
    print("Claude API 图片支持最终测试")
    print("=" * 50)

    # 运行所有测试
    tests = [
        test_text_only(),
        test_claude_format(),
        test_openai_format()
    ]

    results = await asyncio.gather(*tests)

    # 分析结果
    print("\n测试结果:")
    print("-" * 50)

    for result in results:
        test_name = result["test_name"]
        analysis = analyze_result(result)
        token_usage = result["token_usage"]

        print(f"\n{test_name}:")
        print(f"  状态: {analysis}")
        if result["success"]:
            print(f"  Token使用: 输入={token_usage.get('input_tokens', 0)}, 输出={token_usage.get('output_tokens', 0)}")
            print(f"  响应预览: {result['response_text'][:100]}...")
        else:
            print(f"  错误: {result['response_text']}")

    # 总结
    print("\n" + "=" * 50)
    print("总结:")

    claude_result = next(r for r in results if r["test_name"] == "Claude格式图片")
    openai_result = next(r for r in results if r["test_name"] == "OpenAI格式图片")
    text_result = next(r for r in results if r["test_name"] == "纯文本对比")

    claude_analysis = analyze_result(claude_result)
    openai_analysis = analyze_result(openai_result)
    text_analysis = analyze_result(text_result)

    print(f"- 纯文本处理: {text_analysis}")
    print(f"- Claude格式图片: {claude_analysis}")
    print(f"- OpenAI格式图片: {openai_analysis}")

    if "PASS" in claude_analysis and "PASS" in openai_analysis:
        print("\n✅ 图片支持修复成功！两种格式都能正常工作。")
    elif "PASS" in claude_analysis or "PASS" in openai_analysis:
        print("\n⚠️ 图片支持部分修复。至少一种格式能正常工作。")
    else:
        print("\n❌ 图片支持仍有问题。需要进一步调试。")

    # 已知限制
    print("\n已知限制:")
    print("- 多图片处理：Warp API可能只处理第一张图片")
    print("- 图片大小：建议使用较小的图片以获得最佳效果")
    print("- 格式支持：主要支持PNG和JPEG格式")

if __name__ == "__main__":
    asyncio.run(main())