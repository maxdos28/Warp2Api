#!/usr/bin/env python3
"""
使用真实的、明显的图片进行测试
"""
import asyncio
import base64
import json
import httpx

def create_obvious_image():
    """创建一个更明显的测试图片 - 红绿蓝三色条纹"""
    # 手工制作一个4x3的RGB条纹PNG图片
    # 这个PNG包含明显的红绿蓝垂直条纹
    png_hex = """
    89504e470d0a1a0a0000000d494844520000000400000003080600000094b8
    7b020000001e49444154789c6300ff000000ff0000ff0000ffffff00ff0000
    00000000004000000049454e44ae426082
    """.replace('\n', '').replace(' ', '')
    
    try:
        png_data = bytes.fromhex(png_hex)
        return base64.b64encode(png_data).decode('utf-8')
    except:
        # 如果上面的PNG有问题，使用一个简单的2x2红色方块
        simple_png = """
        89504e470d0a1a0a0000000d49484452000000020000000208060000007b
        cf7db80000001049444154789c6300010000050005015a2f59b30000000049
        454e44ae426082
        """.replace('\n', '').replace(' ', '')
        png_data = bytes.fromhex(simple_png)
        return base64.b64encode(png_data).decode('utf-8')

async def test_with_obvious_image():
    """使用明显的图片进行测试"""
    print("🖼️ 测试明显的RGB条纹图片")
    print("=" * 50)
    
    image_data = create_obvious_image()
    print(f"图片数据长度: {len(image_data)} 字符")
    
    # 验证base64完整性
    try:
        decoded = base64.b64decode(image_data)
        print(f"解码后字节数: {len(decoded)}")
        
        import hashlib
        print(f"MD5哈希: {hashlib.md5(decoded).hexdigest()}")
    except Exception as e:
        print(f"Base64解码失败: {e}")
        return
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请详细描述这张图片中的颜色。这应该是一个包含红、绿、蓝三种颜色条纹的测试图片。"
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
            print("\n📤 发送请求...")
            response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=request_data,
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json"
                }
            )
            
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [])
                
                if content and content[0].get("type") == "text":
                    response_text = content[0].get("text", "")
                    print(f"✅ 响应成功 (长度: {len(response_text)})")
                    print(f"\n🔍 AI响应:")
                    print("-" * 40)
                    print(response_text)
                    print("-" * 40)
                    
                    # 检查AI是否真的看到了图片
                    no_image_phrases = [
                        "can't see", "cannot see", "don't see", "no image",
                        "看不到", "无法看到", "没有看到", "无法查看",
                        "没有图片", "图片未", "upload"
                    ]
                    
                    sees_no_image = any(phrase in response_text.lower() for phrase in no_image_phrases)
                    
                    if sees_no_image:
                        print("\n❌ AI表示看不到图片!")
                        print("可能的问题:")
                        print("- 图片数据没有正确传递给AI")
                        print("- protobuf转换过程中图片丢失")
                        print("- Warp AI服务端图片处理问题")
                        return False
                    else:
                        # 检查是否提到了颜色
                        color_mentions = []
                        colors = ["red", "green", "blue", "红", "绿", "蓝"]
                        for color in colors:
                            if color in response_text.lower():
                                color_mentions.append(color)
                        
                        if color_mentions:
                            print(f"✅ AI看到了图片并提到了颜色: {color_mentions}")
                            return True
                        else:
                            print("⚠️ AI看到了图片但没有提到预期的颜色")
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
    success = await test_with_obvious_image()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 图片支持功能正常工作!")
    else:
        print("❌ 图片支持功能存在问题")
        print("\n🔧 调试建议:")
        print("1. 检查服务器日志中是否有我们的调试信息")
        print("2. 验证图片数据是否正确添加到protobuf context中")
        print("3. 检查Warp AI是否正确处理InputContext.images")
        print("4. 考虑图片尺寸或格式限制")

if __name__ == "__main__":
    asyncio.run(main())
