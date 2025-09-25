#!/usr/bin/env python3
"""
测试基于文件的图片传递方法
"""
import asyncio
import base64
import json
import httpx

def create_distinctive_image():
    """创建一个独特的测试图片"""
    # 使用一个绿色像素作为测试
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

async def test_file_based_image():
    """测试基于文件的图片传递"""
    print("🧪 测试基于文件的图片传递方法")
    print("=" * 50)
    
    image_data = create_distinctive_image()
    print(f"测试图片: 绿色像素PNG")
    print(f"Base64长度: {len(image_data)} 字符")
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "我上传了一张绿色像素的PNG图片。请仔细查看附件中的图片文件并告诉我：1) 你是否能看到这张图片？2) 如果能看到，图片是什么颜色？3) 图片的尺寸大概是多少？"
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
            print("\n📤 发送文件方法请求...")
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
                    print("-" * 50)
                    print(response_text)
                    print("-" * 50)
                    
                    # 详细分析回复内容
                    response_lower = response_text.lower()
                    
                    # 检查是否提到绿色
                    mentions_green = any(word in response_lower for word in ["绿色", "green", "绿"])
                    
                    # 检查是否提到像素或尺寸
                    mentions_pixel = any(word in response_lower for word in ["像素", "pixel", "1x1", "small"])
                    
                    # 检查是否说看不到
                    cant_see = any(phrase in response_lower for phrase in [
                        "看不到", "没有看到", "无法看到", "没有图片",
                        "can't see", "cannot see", "don't see", "no image"
                    ])
                    
                    # 检查是否说能看到
                    can_see = any(phrase in response_lower for phrase in [
                        "看到", "能看到", "可以看到", "图片", "image",
                        "i can see", "i see", "visible"
                    ])
                    
                    print(f"\n📊 详细分析:")
                    print(f"   提到绿色: {mentions_green}")
                    print(f"   提到像素/尺寸: {mentions_pixel}")
                    print(f"   说看不到: {cant_see}")
                    print(f"   说能看到: {can_see}")
                    
                    # 最终判断
                    if mentions_green and (mentions_pixel or can_see):
                        print(f"\n🎉 完美！AI正确识别了绿色像素图片！")
                        return "perfect"
                    elif can_see and not cant_see:
                        print(f"\n✅ 良好！AI能看到图片但细节不完整")
                        return "good"
                    elif cant_see and not can_see:
                        print(f"\n❌ 失败！AI仍然看不到图片")
                        return "failed"
                    elif cant_see and can_see:
                        print(f"\n⚠️ 矛盾！AI回复前后不一致")
                        return "contradictory"
                    else:
                        print(f"\n❓ 不明确！无法判断结果")
                        return "unclear"
                        
                else:
                    print("❌ 响应格式异常")
                    return "format_error"
                    
            else:
                print(f"❌ 请求失败: {response.text}")
                return "request_failed"
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return "exception"

async def main():
    print("🚀 测试文件方法图片传递")
    print("基于InputContext.files的新尝试")
    print("=" * 60)
    
    result = await test_file_based_image()
    
    print(f"\n{'='*60}")
    print("🎯 最终测试结果:")
    
    if result == "perfect":
        print("🎉 图片支持完全修复！AI能正确识别图片内容！")
    elif result == "good":
        print("✅ 图片支持基本修复！AI能看到图片但可能缺少细节。")
    elif result == "failed":
        print("❌ 图片支持仍有问题。AI无法看到图片。")
        print("💡 可能需要研究Warp AI的原生图片处理机制。")
    elif result == "contradictory":
        print("⚠️ AI回复仍然矛盾。需要进一步调试状态管理。")
    else:
        print(f"❓ 测试结果不明确: {result}")
    
    print(f"\n💡 如果问题仍然存在，可能的原因:")
    print("- Warp AI本身对图片支持有限制")
    print("- 需要特殊的图片预处理步骤")
    print("- 可能需要通过专门的上传API")

if __name__ == "__main__":
    asyncio.run(main())
