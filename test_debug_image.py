#!/usr/bin/env python3
"""
调试图片数据传递的测试脚本
"""
import asyncio
import base64
import json
import httpx
import hashlib
from io import BytesIO

def create_obvious_test_image():
    """创建一个明显的测试图片 - 彩色条纹"""
    try:
        from PIL import Image, ImageDraw
        
        # 创建一个100x100的彩色条纹图片
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # 绘制彩色条纹
        colors = ['red', 'green', 'blue', 'yellow', 'purple']
        stripe_height = 20
        
        for i, color in enumerate(colors):
            y_start = i * stripe_height
            y_end = (i + 1) * stripe_height
            draw.rectangle([(0, y_start), (100, y_end)], fill=color)
        
        # 转换为字节
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        image_data = img_bytes.getvalue()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        print(f"✅ 创建了彩色条纹测试图片")
        print(f"   尺寸: 100x100")
        print(f"   格式: PNG")
        print(f"   原始字节数: {len(image_data)}")
        print(f"   Base64长度: {len(image_b64)}")
        print(f"   MD5哈希: {hashlib.md5(image_data).hexdigest()}")
        
        return image_b64, image_data
        
    except ImportError:
        print("⚠️ PIL未安装，使用简单测试图片")
        # 使用1x1红色像素作为后备
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        image_b64 = base64.b64encode(png_data).decode('utf-8')
        
        print(f"✅ 使用简单红色像素测试图片")
        print(f"   尺寸: 1x1")
        print(f"   格式: PNG")
        print(f"   原始字节数: {len(png_data)}")
        print(f"   Base64长度: {len(image_b64)}")
        print(f"   MD5哈希: {hashlib.md5(png_data).hexdigest()}")
        
        return image_b64, png_data

def verify_base64_integrity(original_data, base64_string):
    """验证base64编码解码的完整性"""
    try:
        decoded_data = base64.b64decode(base64_string)
        original_hash = hashlib.md5(original_data).hexdigest()
        decoded_hash = hashlib.md5(decoded_data).hexdigest()
        
        print(f"\n🔍 Base64完整性验证:")
        print(f"   原始数据MD5: {original_hash}")
        print(f"   解码数据MD5: {decoded_hash}")
        print(f"   数据完整性: {'✅ 正确' if original_hash == decoded_hash else '❌ 损坏'}")
        
        return original_hash == decoded_hash
    except Exception as e:
        print(f"❌ Base64验证失败: {e}")
        return False

async def test_image_with_debug():
    """测试图片并输出详细调试信息"""
    print("🧪 开始图片数据完整性调试测试")
    print("=" * 60)
    
    # 创建测试图片
    image_b64, original_data = create_obvious_test_image()
    
    # 验证base64完整性
    verify_base64_integrity(original_data, image_b64)
    
    # 构建请求
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请详细描述这张图片中的颜色和图案。这是一个测试图片，应该包含明显的颜色条纹（红、绿、蓝、黄、紫）。"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64
                        }
                    }
                ]
            }
        ]
    }
    
    print(f"\n📤 发送请求...")
    print(f"   请求数据大小: {len(json.dumps(request_data))} 字符")
    print(f"   图片Base64长度: {len(image_b64)} 字符")
    
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
            
            print(f"\n📊 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [])
                
                if content and content[0].get("type") == "text":
                    response_text = content[0].get("text", "")
                    print(f"✅ 请求成功!")
                    print(f"📝 响应长度: {len(response_text)} 字符")
                    print(f"\n🔍 AI响应内容:")
                    print("-" * 40)
                    print(response_text)
                    print("-" * 40)
                    
                    # 分析响应内容
                    print(f"\n📊 响应分析:")
                    
                    # 检查是否提到了图片
                    if any(keyword in response_text.lower() for keyword in ["image", "picture", "photo", "图片", "图像"]):
                        print("✅ AI识别到了图片")
                    else:
                        print("❌ AI未识别到图片")
                    
                    # 检查是否提到了颜色
                    mentioned_colors = []
                    color_keywords = {
                        'red': ['red', '红色', '红'],
                        'green': ['green', '绿色', '绿'], 
                        'blue': ['blue', '蓝色', '蓝'],
                        'yellow': ['yellow', '黄色', '黄'],
                        'purple': ['purple', '紫色', '紫']
                    }
                    
                    for color, keywords in color_keywords.items():
                        if any(keyword in response_text.lower() for keyword in keywords):
                            mentioned_colors.append(color)
                    
                    print(f"🎨 提到的颜色: {mentioned_colors if mentioned_colors else '无'}")
                    
                    # 检查是否提到条纹或图案
                    if any(keyword in response_text.lower() for keyword in ["stripe", "band", "pattern", "条纹", "图案", "带状"]):
                        print("✅ AI识别到了图案/条纹")
                    else:
                        print("❌ AI未识别到图案/条纹")
                    
                    # 判断整体匹配度
                    if len(mentioned_colors) >= 3:
                        print("🎉 图片内容匹配度: 高 - AI正确识别了多种颜色")
                        return True
                    elif len(mentioned_colors) >= 1:
                        print("⚠️ 图片内容匹配度: 中 - AI识别了部分颜色")
                        return False
                    else:
                        print("❌ 图片内容匹配度: 低 - AI未正确识别图片内容")
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
    success = await test_image_with_debug()
    
    print(f"\n" + "=" * 60)
    if success:
        print("🎉 图片支持功能工作正常!")
    else:
        print("⚠️ 图片支持需要进一步调试")
        print("\n💡 可能的问题:")
        print("- 图片数据在protobuf转换过程中损坏")
        print("- Base64编码/解码过程有误")
        print("- AI模型接收到的数据格式不正确")
        print("- 需要检查服务器日志获取更多信息")

if __name__ == "__main__":
    asyncio.run(main())
