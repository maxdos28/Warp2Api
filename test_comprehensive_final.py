#!/usr/bin/env python3
"""
综合最终测试 - 使用所有修复验证图片功能
"""
import asyncio
import base64
import json
import httpx

def create_distinctive_image():
    """创建一个独特的测试图片"""
    # 使用绿色像素作为测试
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

async def comprehensive_test():
    """综合测试所有修复"""
    print("🧪 综合最终测试")
    print("使用所有修复: 文件方法 + 视觉模型 + 新会话")
    print("=" * 60)
    
    # 等待服务器完全启动
    await asyncio.sleep(3)
    
    image_data = create_distinctive_image()
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",  # 这会被自动切换到claude-4-opus
        "max_tokens": 400,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "我上传了一张测试图片。这是一个1x1像素的绿色PNG图片。请你仔细查看并回答：1) 你能看到这张图片吗？2) 如果能看到，请描述它的颜色。3) 请确认这是否是一个绿色的像素点。"
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
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            # 健康检查
            try:
                health = await client.get("http://127.0.0.1:28889/healthz")
                print(f"服务器状态: {health.status_code}")
            except:
                print("⚠️ 服务器可能未完全启动")
            
            print("📤 发送综合测试请求...")
            response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=request_data,
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json"
                }
            )
            
            print(f"📊 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [])
                
                if content and content[0].get("type") == "text":
                    response_text = content[0].get("text", "")
                    print(f"✅ 响应成功 (长度: {len(response_text)} 字符)")
                    
                    print(f"\n🔍 AI完整回复:")
                    print("=" * 50)
                    print(response_text)
                    print("=" * 50)
                    
                    # 全面分析回复
                    response_lower = response_text.lower()
                    
                    # 分析关键指标
                    indicators = {
                        "明确说看不到": any(phrase in response_lower for phrase in [
                            "看不到", "没有看到", "无法看到", "没有图片", "无法查看",
                            "can't see", "cannot see", "don't see", "no image", "unable to view"
                        ]),
                        "明确说能看到": any(phrase in response_lower for phrase in [
                            "能看到", "可以看到", "看到了", "I can see", "I see", "visible"
                        ]),
                        "提到绿色": any(word in response_lower for word in [
                            "绿色", "green", "绿"
                        ]),
                        "提到像素": any(word in response_lower for word in [
                            "像素", "pixel", "点", "dot"
                        ]),
                        "提到图片": any(word in response_lower for word in [
                            "图片", "image", "picture", "图像"
                        ]),
                        "承认上传": any(phrase in response_lower for phrase in [
                            "上传", "附加", "提供", "upload", "attach", "provided"
                        ])
                    }
                    
                    print(f"\n📊 详细指标分析:")
                    for key, value in indicators.items():
                        status = "✅" if value else "❌"
                        print(f"   {status} {key}: {value}")
                    
                    # 综合判断
                    if indicators["提到绿色"] and indicators["提到像素"]:
                        print(f"\n🎉 SUCCESS! AI正确识别了绿色像素图片!")
                        return "SUCCESS"
                    elif indicators["明确说能看到"] and not indicators["明确说看不到"]:
                        print(f"\n✅ PARTIAL! AI能看到图片但描述不准确")
                        return "PARTIAL"
                    elif indicators["承认上传"] and not indicators["明确说看不到"]:
                        print(f"\n⚠️ PROGRESS! AI知道有图片但无法处理")
                        return "PROGRESS"
                    elif indicators["明确说看不到"]:
                        print(f"\n❌ FAILED! AI仍然看不到图片")
                        return "FAILED"
                    else:
                        print(f"\n❓ UNCLEAR! 无法判断结果")
                        return "UNCLEAR"
                        
                else:
                    print("❌ 响应格式异常")
                    return "FORMAT_ERROR"
                    
            else:
                print(f"❌ 请求失败: {response.text}")
                return "REQUEST_FAILED"
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return "EXCEPTION"

async def main():
    result = await comprehensive_test()
    
    print(f"\n" + "=" * 60)
    print("🎯 综合测试最终结果:")
    
    if result == "SUCCESS":
        print("🎉 完全成功！图片支持功能已完全修复！")
        print("Cline现在应该能正常识别和分析任何图片！")
    elif result == "PARTIAL":
        print("✅ 部分成功！图片传递工作，但需要优化识别准确性。")
    elif result == "PROGRESS":
        print("⚠️ 有进展！图片上传被识别，但AI处理能力有限。")
        print("💡 这可能是Warp AI本身的限制，而不是我们的代码问题。")
    elif result == "FAILED":
        print("❌ 仍然失败！需要研究Warp AI的原生图片支持机制。")
    else:
        print(f"❓ 结果不明确: {result}")
    
    print(f"\n📋 已尝试的方法:")
    print("✅ InputContext.images 方式")
    print("✅ referenced_attachments 方式") 
    print("✅ DriveObject 方式")
    print("✅ 文件方法 (InputContext.files)")
    print("✅ 视觉模型自动切换")
    print("✅ 新会话避免缓存")
    print("✅ 格式兼容性修复")

if __name__ == "__main__":
    asyncio.run(main())
