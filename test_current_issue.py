#!/usr/bin/env python3
"""
测试当前图片识别的实际问题
"""
import asyncio
import base64
import json
import httpx

def create_test_image():
    """创建一个测试图片"""
    # 使用一个稍大的测试图片，类似用户可能上传的截图
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

async def test_aliyun_style_image():
    """模拟用户上传阿里云控制台截图的情况"""
    print("🖼️ 测试阿里云控制台风格的图片识别")
    print("=" * 60)
    
    image_data = create_test_image()
    
    # 使用Claude标准格式
    claude_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 500,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请分析这张阿里云Web应用防火墙控制台的截图，告诉我看到了什么数据和功能模块。"
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
    
    print("📤 发送Claude格式请求...")
    claude_result = await send_request(claude_request, "Claude格式")
    
    # 使用OpenAI格式（Cline风格）
    openai_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 500,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请分析这张阿里云Web应用防火墙控制台的截图，告诉我看到了什么数据和功能模块。"
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
    
    print("\n📤 发送OpenAI格式请求...")
    openai_result = await send_request(openai_request, "OpenAI格式")
    
    return claude_result, openai_result

async def send_request(request_data, format_name):
    """发送请求并分析响应"""
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
                    print(f"  ✅ {format_name} 成功响应")
                    print(f"  响应长度: {len(response_text)} 字符")
                    
                    # 分析响应的矛盾性
                    cant_see_phrases = [
                        "没有看到", "看不到", "无法看到", "can't see", "cannot see", "don't see",
                        "没有图片", "no image", "没有提供", "未看到"
                    ]
                    
                    can_see_phrases = [
                        "可以看到", "我看到", "看到了", "图片显示", "can see", "I can see",
                        "这张图片", "图片中", "截图", "控制台"
                    ]
                    
                    has_cant_see = any(phrase in response_text for phrase in cant_see_phrases)
                    has_can_see = any(phrase in response_text for phrase in can_see_phrases)
                    
                    print(f"  包含'看不到'类似表述: {has_cant_see}")
                    print(f"  包含'能看到'类似表述: {has_can_see}")
                    
                    if has_cant_see and has_can_see:
                        print("  ⚠️ 检测到矛盾回复！AI前后表述不一致")
                        return "contradictory"
                    elif has_cant_see:
                        print("  ❌ AI表示看不到图片")
                        return "cannot_see"
                    elif has_can_see:
                        print("  ✅ AI能正常识别图片")
                        return "can_see"
                    else:
                        print("  ❓ 无法判断AI是否看到图片")
                        return "unclear"
                    
                else:
                    print(f"  ❌ {format_name} 响应格式异常")
                    return "format_error"
                    
            else:
                print(f"  ❌ {format_name} 请求失败: {response.status_code}")
                print(f"  错误: {response.text}")
                return "request_failed"
                
    except Exception as e:
        print(f"  ❌ {format_name} 请求异常: {e}")
        return "exception"

async def main():
    print("🧪 诊断当前图片识别问题")
    print("模拟用户上传阿里云控制台截图的场景")
    print("=" * 60)
    
    claude_result, openai_result = await test_aliyun_style_image()
    
    print(f"\n" + "=" * 60)
    print("📊 诊断结果:")
    print(f"Claude格式结果: {claude_result}")
    print(f"OpenAI格式结果: {openai_result}")
    
    if claude_result == "contradictory" or openai_result == "contradictory":
        print("\n❌ 发现问题：AI回复前后矛盾")
        print("💡 可能原因:")
        print("- 图片数据部分丢失导致AI识别不稳定")
        print("- 图片处理流程中存在竞态条件")
        print("- 图片大小或格式问题")
        
    elif claude_result == "can_see" and openai_result == "can_see":
        print("\n🎉 两种格式都能正常识别图片！")
        
    else:
        print(f"\n⚠️ 仍存在问题需要进一步调试")
        print("💡 建议:")
        print("- 检查服务器日志中的图片处理信息")
        print("- 验证图片数据完整性")
        print("- 测试不同大小和格式的图片")

if __name__ == "__main__":
    asyncio.run(main())
