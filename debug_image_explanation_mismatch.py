#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试图片解释内容不匹配问题
专门针对 /v1/messages 接口传入图片时AI解释不准确的问题
"""

import requests
import json
import base64
import os

def create_test_image():
    """创建一个简单的测试图片"""
    try:
        from PIL import Image, ImageDraw, ImageFont

        # 创建一个简单的图片，包含明确的文字
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)

        # 添加明确的文字内容
        text = "TEST IMAGE\nThis is a test\n2024-09-24"
        try:
            # 尝试使用默认字体
            font = ImageFont.load_default()
        except:
            font = None

        draw.text((50, 50), text, fill='black', font=font)

        # 添加一些几何图形
        draw.rectangle([50, 120, 150, 170], outline='red', width=3)
        draw.circle((300, 100), 30, outline='blue', width=3)

        # 保存图片
        img.save('test_image_debug.png')
        print("✅ 创建测试图片: test_image_debug.png")
        return True

    except ImportError:
        print("❌ PIL库未安装，无法创建测试图片")
        return False
    except Exception as e:
        print(f"❌ 创建测试图片失败: {e}")
        return False

def encode_image_to_base64(image_path):
    """将图片编码为base64"""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()

        base64_data = base64.b64encode(image_data).decode('utf-8')
        print(f"✅ 图片编码成功，大小: {len(base64_data)} 字符")
        return base64_data
    except Exception as e:
        print(f"❌ 图片编码失败: {e}")
        return None

def test_image_explanation():
    """测试图片解释功能"""
    print("=== 调试图片解释内容不匹配问题 ===")

    # 1. 创建或使用现有的测试图片
    test_images = []

    # 检查是否有现有的测试图片
    existing_images = ['ali.png', 'test_image_debug.png']
    for img_path in existing_images:
        if os.path.exists(img_path):
            test_images.append(img_path)
            print(f"✅ 找到现有图片: {img_path}")

    # 如果没有现有图片，创建一个
    if not test_images:
        if create_test_image():
            test_images.append('test_image_debug.png')

    if not test_images:
        print("❌ 没有可用的测试图片")
        return

    # 2. 测试每个图片
    for img_path in test_images:
        print(f"\n--- 测试图片: {img_path} ---")

        # 编码图片
        base64_data = encode_image_to_base64(img_path)
        if not base64_data:
            continue

        # 获取图片格式
        img_ext = img_path.split('.')[-1].lower()
        media_type = f"image/{img_ext}" if img_ext in ['png', 'jpg', 'jpeg', 'gif'] else "image/png"

        # 构造请求
        test_cases = [
            {
                "name": "客观描述请求",
                "content": "请客观描述这张图片中的具体内容，不要推测或假设。"
            },
            {
                "name": "详细分析请求",
                "content": "请详细分析这张图片，包括文字、颜色、形状等所有可见元素。"
            },
            {
                "name": "简单识别请求",
                "content": "这张图片显示了什么？"
            }
        ]

        for test_case in test_cases:
            print(f"\n  {test_case['name']}:")
            print(f"  提示词: {test_case['content']}")

            # 构造Claude Messages API请求
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": test_case['content']
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_data
                                }
                            }
                        ]
                    }
                ]
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer 123456"
            }

            try:
                print("  发送请求...")
                response = requests.post(
                    "http://127.0.0.1:28889/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                print(f"  状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    content = data.get('content', [])

                    if content and len(content) > 0:
                        ai_response = content[0].get('text', '')
                        print(f"  AI回复: {ai_response}")

                        # 分析回复质量
                        print("  分析:")
                        if len(ai_response) < 50:
                            print("    - 回复过短，可能信息不足")
                        if "抱歉" in ai_response or "无法" in ai_response:
                            print("    - AI表示无法处理，可能图片传输有问题")
                        if "阿里云" in ai_response and img_path != "ali.png":
                            print("    - ⚠️ 可能出现幻觉，提到了不相关的内容")
                        if "测试" in ai_response and "test" in img_path.lower():
                            print("    - ✅ 正确识别了测试图片特征")

                    else:
                        print("  ❌ 响应中没有内容")

                else:
                    print(f"  ❌ 请求失败: {response.text}")

            except Exception as e:
                print(f"  ❌ 请求异常: {e}")

def check_image_processing_pipeline():
    """检查图片处理管道"""
    print("\n=== 检查图片处理管道 ===")

    # 检查相关的处理文件
    files_to_check = [
        "protobuf2openai/claude_converter.py",
        "protobuf2openai/claude_models.py",
        "protobuf2openai/claude_router.py"
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"\n检查文件: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找图片处理相关的代码
                image_related = []

                if 'image' in content.lower():
                    image_related.append("包含图片处理逻辑")
                if 'base64' in content:
                    image_related.append("包含base64处理")
                if 'media_type' in content:
                    image_related.append("包含媒体类型处理")
                if '阿里云' in content or 'DDD' in content:
                    image_related.append("⚠️ 包含可能导致幻觉的硬编码内容")
                if 'problematic_words' in content:
                    image_related.append("包含问题词汇过滤")

                if image_related:
                    print(f"  发现: {', '.join(image_related)}")
                else:
                    print("  未发现图片相关处理")

            except Exception as e:
                print(f"  读取失败: {e}")

if __name__ == "__main__":
    print("开始调试图片解释内容不匹配问题...")

    # 测试图片解释
    test_image_explanation()

    # 检查处理管道
    check_image_processing_pipeline()

    print("\n=== 调试总结 ===")
    print("如果AI解释内容与图片不符，可能的原因:")
    print("1. 图片编码或传输过程中损坏")
    print("2. AI模型本身的视觉理解问题")
    print("3. 提示词被过度过滤或修改")
    print("4. 存在硬编码的干扰内容")
    print("5. 图片格式或大小不被支持")
    print("6. 缓存或状态管理导致的混乱")