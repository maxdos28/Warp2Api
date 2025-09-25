#!/usr/bin/env python3
"""
测试全新会话的图片识别 - 避免缓存混乱
"""
import asyncio
import base64
import json
import httpx
import hashlib

def create_distinctive_test_image():
    """创建一个独特的测试图片"""
    # 使用一个特殊的测试图片 - 单个绿色像素
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    image_b64 = base64.b64encode(png_data).decode('utf-8')
    
    # 计算唯一标识
    image_hash = hashlib.md5(png_data).hexdigest()
    
    print(f"📸 创建独特测试图片:")
    print(f"   类型: 绿色像素PNG")
    print(f"   大小: {len(png_data)} 字节")
    print(f"   Base64: {len(image_b64)} 字符")
    print(f"   MD5: {image_hash}")
    
    return image_b64, image_hash

async def test_fresh_image_session():
    """测试全新会话的图片识别"""
    print("🧪 测试全新会话图片识别（避免缓存）")
    print("=" * 60)
    
    image_data, expected_hash = create_distinctive_test_image()
    
    # 使用Claude格式，明确指定这是绿色像素
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"请分析这张图片。这是一个测试图片，包含单个绿色像素。图片的MD5哈希值是: {expected_hash}。请告诉我你看到了什么颜色。"
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
            print("📤 发送全新会话请求...")
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
                    
                    print(f"\n🔍 AI回复内容:")
                    print("-" * 40)
                    print(response_text)
                    print("-" * 40)
                    
                    # 验证AI看到的内容是否正确
                    response_lower = response_text.lower()
                    
                    # 检查是否提到绿色
                    mentions_green = any(word in response_lower for word in ["绿色", "green", "绿"])
                    
                    # 检查是否提到像素
                    mentions_pixel = any(word in response_lower for word in ["像素", "pixel"])
                    
                    # 检查是否提到MD5或哈希
                    mentions_hash = any(word in response_lower for word in ["md5", "哈希", "hash"])
                    
                    # 检查是否有矛盾表述
                    cant_see = any(phrase in response_lower for phrase in ["看不到", "没有看到", "无法看到", "can't see"])
                    can_see = any(phrase in response_lower for phrase in ["看到", "能看到", "可以看到", "I can see"])
                    
                    print(f"\n📊 内容分析:")
                    print(f"   提到绿色: {mentions_green}")
                    print(f"   提到像素: {mentions_pixel}")
                    print(f"   提到哈希: {mentions_hash}")
                    print(f"   说看不到: {cant_see}")
                    print(f"   说能看到: {can_see}")
                    
                    if cant_see and can_see:
                        print(f"\n❌ 发现矛盾回复！AI前后表述不一致")
                        return "contradictory"
                    elif cant_see:
                        print(f"\n❌ AI仍然看不到图片")
                        return "cannot_see"
                    elif mentions_green and mentions_pixel:
                        print(f"\n🎉 完美！AI正确识别了绿色像素图片")
                        return "perfect_match"
                    elif mentions_green:
                        print(f"\n✅ 良好！AI识别了绿色，但可能缺少细节")
                        return "good_match"
                    else:
                        print(f"\n⚠️ AI看到了图片但识别内容不正确")
                        return "incorrect_content"
                        
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
    result = await test_fresh_image_session()
    
    print(f"\n" + "=" * 60)
    print("🎯 最终诊断结果:")
    
    if result == "perfect_match":
        print("🎉 图片支持功能完全正常！Cline应该能正常工作。")
    elif result == "good_match":
        print("✅ 图片支持基本正常，可能需要微调。")
    elif result == "incorrect_content":
        print("⚠️ 图片传递正常，但AI识别内容错误。")
        print("💡 可能是图片数据被替换或损坏。")
    elif result == "contradictory":
        print("❌ AI回复矛盾，存在状态混乱问题。")
        print("💡 需要清理会话状态和缓存。")
    elif result == "cannot_see":
        print("❌ 图片支持仍不正常，AI无法看到图片。")
        print("💡 需要检查protobuf传递逻辑。")
    else:
        print(f"❌ 测试失败: {result}")
        print("💡 需要进一步调试技术问题。")

if __name__ == "__main__":
    asyncio.run(main())
