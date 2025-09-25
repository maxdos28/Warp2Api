#!/usr/bin/env python3
"""
完整的Claude API图片支持测试脚本
测试 /v1/messages 端点的图片处理功能
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

async def test_basic_text_message():
    """测试基础文本消息"""
    print("🔸 测试基础文本消息...")
    
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
    
    return await send_request(request_data, "基础文本")

async def test_single_image():
    """测试单张图片"""
    print("🔸 测试单张图片...")
    
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
                        "text": "请描述这张图片。这是一个简单的测试图片。"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": images["red_png"]
                        }
                    }
                ]
            }
        ]
    }
    
    return await send_request(request_data, "单张图片")

async def test_multiple_images():
    """测试多张图片"""
    print("🔸 测试多张图片...")
    
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
                        "text": "请比较这两张图片的差异："
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png", 
                            "data": images["red_png"]
                        }
                    },
                    {
                        "type": "text",
                        "text": "和"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": images["blue_png"]
                        }
                    }
                ]
            }
        ]
    }
    
    return await send_request(request_data, "多张图片")

async def test_conversation_with_images():
    """测试包含图片的多轮对话"""
    print("🔸 测试多轮对话（含图片）...")
    
    images = create_test_images()
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 250,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这是一张红色的图片："
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": images["red_png"]
                        }
                    }
                ]
            },
            {
                "role": "assistant",
                "content": "我看到了这张红色的图片。它是一个1x1像素的红色PNG图像。"
            },
            {
                "role": "user",
                "content": "非常好！现在请告诉我红色在心理学上通常代表什么？"
            }
        ]
    }
    
    return await send_request(request_data, "多轮对话")

async def test_invalid_image():
    """测试无效图片数据"""
    print("🔸 测试无效图片数据...")
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片："
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
    
    return await send_request(request_data, "无效图片", expect_error=True)

async def send_request(request_data: Dict[str, Any], test_name: str, expect_error: bool = False) -> Dict[str, Any]:
    """发送请求并处理响应"""
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
                "error": None,
                "response_data": None
            }
            
            if response.status_code == 200:
                response_data = response.json()
                result["success"] = True
                result["response_data"] = response_data
                
                # 检查响应格式
                if "content" in response_data:
                    content_blocks = response_data["content"]
                    if content_blocks and isinstance(content_blocks, list):
                        text_content = ""
                        for block in content_blocks:
                            if block.get("type") == "text":
                                text_content += block.get("text", "")
                        
                        print(f"  ✅ {test_name} 成功")
                        print(f"     响应长度: {len(text_content)} 字符")
                        if text_content:
                            print(f"     响应预览: {text_content[:100]}...")
                    else:
                        print(f"  ⚠️ {test_name} 响应格式异常")
                else:
                    print(f"  ⚠️ {test_name} 缺少content字段")
                    
            else:
                result["error"] = response.text
                if expect_error:
                    print(f"  ✅ {test_name} 符合预期（错误状态 {response.status_code}）")
                else:
                    print(f"  ❌ {test_name} 失败 (状态码: {response.status_code})")
                    print(f"     错误信息: {response.text}")
            
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
            print(f"  ✅ {test_name} 符合预期（异常: {e}）")
        else:
            print(f"  ❌ {test_name} 异常: {e}")
        
        return result

async def main():
    """主测试函数"""
    print("🚀 开始Claude API图片支持完整测试")
    print("=" * 60)
    
    # 执行所有测试
    tests = [
        test_basic_text_message(),
        test_single_image(), 
        test_multiple_images(),
        test_conversation_with_images(),
        test_invalid_image()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # 统计结果
    total_tests = len(results)
    successful_tests = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"总测试数: {total_tests}")
    print(f"成功测试: {successful_tests}")
    print(f"失败测试: {total_tests - successful_tests}")
    print(f"成功率: {successful_tests/total_tests*100:.1f}%")
    
    print("\n💡 测试说明:")
    print("- ✅ 表示测试成功，功能正常工作")
    print("- ❌ 表示测试失败，需要检查功能实现")
    print("- ⚠️ 表示响应异常，可能需要进一步调试")
    
    if successful_tests == total_tests:
        print("\n🎉 所有测试通过！Claude API图片支持功能正常。")
    elif successful_tests > 0:
        print(f"\n⚠️ 部分测试通过。图片支持功能部分正常，建议检查失败的测试。")
    else:
        print(f"\n❌ 所有测试失败。图片支持功能可能存在问题，需要排查。")

if __name__ == "__main__":
    asyncio.run(main())
