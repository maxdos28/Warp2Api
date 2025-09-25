#!/usr/bin/env python3
"""
测试新的DriveObject图片传递方法
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

async def test_driveobject_image():
    """测试通过DriveObject传递图片"""
    print("🧪 测试DriveObject图片传递方法")
    print("=" * 50)
    
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
                        "text": "请分析这张图片。这是一个红色像素的PNG图片。请告诉我你是否能看到它以及它的颜色。"
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
        # 等待服务器启动
        await asyncio.sleep(2)
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            # 先测试服务器是否可用
            try:
                health_response = await client.get("http://127.0.0.1:28889/healthz")
                print(f"服务器健康检查: {health_response.status_code}")
            except:
                print("⚠️ 服务器可能未完全启动，继续尝试...")
            
            print("📤 发送图片请求...")
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
                    
                    print(f"\n🔍 AI回复:")
                    print("-" * 40)
                    print(response_text)
                    print("-" * 40)
                    
                    # 检查回复内容
                    response_lower = response_text.lower()
                    
                    # 检查消极指标
                    negative_phrases = [
                        "看不到", "没有看到", "无法看到", "没有图片",
                        "can't see", "cannot see", "don't see", "no image"
                    ]
                    has_negative = any(phrase in response_lower for phrase in negative_phrases)
                    
                    # 检查积极指标  
                    positive_phrases = [
                        "红色", "像素", "图片", "red", "pixel", "image", "看到"
                    ]
                    has_positive = any(phrase in response_lower for phrase in positive_phrases)
                    
                    print(f"\n📊 内容分析:")
                    print(f"   包含消极表述: {has_negative}")
                    print(f"   包含积极表述: {has_positive}")
                    
                    if has_negative:
                        print(f"\n❌ DriveObject方法失败 - AI仍然看不到图片")
                        return False
                    elif has_positive:
                        print(f"\n🎉 DriveObject方法成功 - AI能看到图片！")
                        return True
                    else:
                        print(f"\n❓ 结果不明确")
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
    print("🚀 测试新的DriveObject图片传递方法")
    print("这是基于protobuf schema分析的新尝试")
    print("=" * 60)
    
    success = await test_driveobject_image()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 DriveObject方法成功！图片支持已修复！")
        print("Cline现在应该能正常识别图片了。")
    else:
        print("❌ DriveObject方法仍然失败")
        print("\n💡 可能需要考虑其他方法:")
        print("- 检查Warp AI是否需要特殊的图片格式")
        print("- 验证是否需要预先上传图片到服务器")
        print("- 研究原始Warp终端的图片处理机制")

if __name__ == "__main__":
    asyncio.run(main())
