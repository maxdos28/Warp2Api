#!/usr/bin/env python3
"""
模拟Cline可能的图片上传格式进行测试
"""
import asyncio
import base64
import json
import httpx

def create_simple_test_image():
    """创建简单测试图片"""
    # 使用一个稍大一点的红色方块
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

async def test_various_formats():
    """测试Cline可能使用的各种图片格式"""
    
    image_data = create_simple_test_image()
    
    test_cases = [
        {
            "name": "标准Claude格式",
            "request": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请描述这张图片"
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
        },
        {
            "name": "OpenAI风格在Claude接口",
            "request": {
                "model": "claude-3-5-sonnet-20241022", 
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请描述这张图片"
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
        },
        {
            "name": "混合content字符串",
            "request": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": "请描述这张图片: [图片已上传]"
                    }
                ]
            }
        },
        {
            "name": "空图片数据",
            "request": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请描述这张图片"
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": ""
                                }
                            }
                        ]
                    }
                ]
            }
        }
    ]
    
    print("🧪 测试Cline可能的图片上传格式")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 测试: {test_case['name']}")
        print("-" * 40)
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.post(
                    "http://127.0.0.1:28889/v1/messages",
                    json=test_case['request'],
                    headers={
                        "Authorization": "Bearer 123456",
                        "Content-Type": "application/json"
                    }
                )
                
                print(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("content", [])
                    
                    if content and content[0].get("type") == "text":
                        response_text = content[0].get("text", "")
                        print(f"✅ 成功响应 (长度: {len(response_text)})")
                        
                        # 检查是否提到看不到图片
                        no_image_indicators = [
                            "没有看到", "看不到", "无法看到", "未看到",
                            "no image", "can't see", "cannot see", "don't see",
                            "没有图片", "未上传", "上传失败"
                        ]
                        
                        has_no_image = any(indicator in response_text for indicator in no_image_indicators)
                        
                        if has_no_image:
                            print("⚠️ AI表示看不到图片")
                        else:
                            print("✅ AI能看到图片内容")
                            
                        # 显示响应预览
                        preview = response_text[:150] + "..." if len(response_text) > 150 else response_text
                        print(f"响应预览: {preview}")
                        
                    else:
                        print("❌ 响应格式异常")
                        
                else:
                    print(f"❌ 请求失败: {response.text}")
                    
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        
        await asyncio.sleep(1)  # 避免请求过快

async def test_edge_cases():
    """测试边缘情况"""
    print("\n\n🔍 测试边缘情况")
    print("=" * 60)
    
    # 测试非常大的图片（模拟）
    large_fake_data = "A" * 10000  # 10KB的假数据
    
    edge_cases = [
        {
            "name": "超大图片数据",
            "data": large_fake_data,
            "should_fail": True
        },
        {
            "name": "无效base64",
            "data": "invalid-base64-data-!@#$%",
            "should_fail": True
        },
        {
            "name": "空白数据",
            "data": "",
            "should_fail": True
        }
    ]
    
    for case in edge_cases:
        print(f"\n测试: {case['name']}")
        print(f"预期失败: {case['should_fail']}")
        
        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请描述这张图片"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": case['data']
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
                        "Content-Type": "application/json"
                    }
                )
                
                print(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("content", [])
                    if content:
                        text = content[0].get("text", "")
                        if "看不到" in text or "无法" in text:
                            print("✅ 正确处理了无效数据")
                        else:
                            print("⚠️ 可能未正确验证数据")
                else:
                    print(f"服务器返回错误: {response.text}")
                    
        except Exception as e:
            print(f"请求异常: {e}")

async def main():
    await test_various_formats()
    await test_edge_cases()
    
    print("\n\n💡 调试建议:")
    print("1. 检查服务器日志中的图片处理信息")
    print("2. 确认Cline使用的确切请求格式")
    print("3. 验证图片数据的完整性")
    print("4. 检查是否有特殊的编码问题")

if __name__ == "__main__":
    asyncio.run(main())
