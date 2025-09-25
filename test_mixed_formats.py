#!/usr/bin/env python3
"""
测试Claude接口对OpenAI和Claude两种图片格式的支持
"""
import asyncio
import base64
import json
import httpx

def create_test_image():
    """创建测试图片"""
    # 使用简单的红色像素
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

async def test_claude_format():
    """测试Claude标准格式"""
    print("📋 测试Claude标准格式...")
    
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
                        "text": "请描述这张图片的颜色"
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
    
    return await send_request(request_data, "Claude格式")

async def test_openai_format():
    """测试OpenAI格式（在Claude接口上）"""
    print("📋 测试OpenAI格式（在Claude接口上）...")
    
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
                        "text": "请描述这张图片的颜色"
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
    
    return await send_request(request_data, "OpenAI格式")

async def send_request(request_data, format_name):
    """发送请求并处理响应"""
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
            
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [])
                
                if content and content[0].get("type") == "text":
                    response_text = content[0].get("text", "")
                    print(f"  ✅ {format_name} 成功")
                    print(f"  响应长度: {len(response_text)} 字符")
                    
                    # 检查AI是否能看到图片
                    no_image_phrases = [
                        "can't see", "cannot see", "don't see", "no image",
                        "看不到", "无法看到", "没有看到", "没有图片"
                    ]
                    
                    sees_no_image = any(phrase in response_text.lower() for phrase in no_image_phrases)
                    
                    if sees_no_image:
                        print(f"  ❌ AI看不到图片")
                        print(f"  响应: {response_text[:100]}...")
                        return False
                    else:
                        print(f"  ✅ AI能看到图片")
                        print(f"  响应: {response_text[:100]}...")
                        return True
                        
                else:
                    print(f"  ❌ {format_name} 响应格式异常")
                    return False
                    
            else:
                print(f"  ❌ {format_name} 请求失败: {response.status_code}")
                print(f"  错误: {response.text}")
                return False
                
    except Exception as e:
        print(f"  ❌ {format_name} 请求异常: {e}")
        return False

async def main():
    print("🧪 测试Claude接口的图片格式兼容性")
    print("=" * 60)
    
    # 测试两种格式
    claude_success = await test_claude_format()
    await asyncio.sleep(1)
    openai_success = await test_openai_format()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"Claude格式: {'✅ 成功' if claude_success else '❌ 失败'}")
    print(f"OpenAI格式: {'✅ 成功' if openai_success else '❌ 失败'}")
    
    if claude_success and openai_success:
        print("\n🎉 两种格式都支持！Cline应该能正常工作。")
    elif claude_success:
        print("\n⚠️ 只有Claude格式工作，需要修复OpenAI格式兼容性。")
    elif openai_success:
        print("\n⚠️ 只有OpenAI格式工作，Claude标准格式有问题。")
    else:
        print("\n❌ 两种格式都不工作，图片支持功能需要进一步调试。")
        print("\n🔧 调试建议:")
        print("- 检查图片数据是否正确传递到protobuf")
        print("- 验证Warp AI是否正确处理InputContext.images")
        print("- 检查base64编码/解码过程")

if __name__ == "__main__":
    asyncio.run(main())
