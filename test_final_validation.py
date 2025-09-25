#!/usr/bin/env python3
"""
最终验证测试 - 确认图片功能是否完全修复
"""
import asyncio
import base64
import json
import httpx

def create_test_image():
    """创建测试图片"""
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

async def test_image_consistency():
    """测试图片识别的一致性"""
    print("🧪 测试图片识别一致性")
    print("=" * 50)
    
    image_data = create_test_image()
    
    # 测试Claude格式
    request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这是一张简单的测试图片，请告诉我你是否能看到它。"
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
            response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=request,
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
                    print(f"响应长度: {len(response_text)} 字符")
                    print(f"AI回复: {response_text}")
                    
                    # 检查回复的一致性
                    negative_phrases = ["看不到", "没有看到", "无法看到", "can't see", "cannot see", "no image"]
                    positive_phrases = ["看到", "能看到", "可以看到", "I can see", "I see", "图片"]
                    
                    has_negative = any(phrase in response_text for phrase in negative_phrases)
                    has_positive = any(phrase in response_text for phrase in positive_phrases)
                    
                    if has_negative and has_positive:
                        print("\n❌ 发现矛盾回复！AI前后表述不一致")
                        return False
                    elif has_negative:
                        print("\n❌ AI无法看到图片")
                        return False
                    elif has_positive:
                        print("\n✅ AI能正常看到图片")
                        return True
                    else:
                        print("\n❓ 回复不明确")
                        return False
                        
                else:
                    print("❌ 响应格式异常")
                    return False
                    
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

async def main():
    success = await test_image_consistency()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 图片支持功能已完全修复!")
        print("Cline现在应该能正常识别图片了。")
    else:
        print("⚠️ 图片支持仍需调试")
        print("\n💡 可能的问题:")
        print("- 配额限制影响了图片处理")
        print("- 图片数据在某个环节丢失")
        print("- 需要检查服务器状态和日志")

if __name__ == "__main__":
    asyncio.run(main())
