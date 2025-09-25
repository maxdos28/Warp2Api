#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的图片解释测试
"""

import requests
import json
import base64
import os

def test_ali_image():
    """测试ali.png图片的解释"""
    print("=== 测试图片解释准确性 ===")

    # 检查图片文件
    img_path = "ali.png"
    if not os.path.exists(img_path):
        print(f"图片文件不存在: {img_path}")
        return

    print(f"测试图片: {img_path}")

    # 读取并编码图片
    try:
        with open(img_path, 'rb') as f:
            image_data = f.read()

        base64_data = base64.b64encode(image_data).decode('utf-8')
        print(f"图片大小: {len(image_data)} bytes")
        print(f"Base64长度: {len(base64_data)} chars")

    except Exception as e:
        print(f"读取图片失败: {e}")
        return

    # 测试不同的提示词
    test_prompts = [
        "请客观描述这张图片中的具体内容。",
        "这张图片显示了什么？请详细说明。",
        "请分析这张图片，包括文字、界面元素等。"
    ]

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- 测试 {i}: {prompt} ---")

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_data
                            }
                        }
                    ]
                }
            ]
        }

        try:
            print("发送请求...")
            response = requests.post(
                "http://127.0.0.1:28889/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )

            print(f"状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                content = data.get('content', [])

                if content and len(content) > 0:
                    ai_response = content[0].get('text', '')
                    print(f"AI回复长度: {len(ai_response)} 字符")
                    print(f"AI回复内容:")
                    print(f"  {ai_response}")

                    # 检查是否有明显的错误解释
                    print("\n分析:")

                    # 检查是否提到了不相关的内容
                    irrelevant_keywords = ["防火墙", "DDD", "架构图", "系统设计"]
                    mentioned_irrelevant = [kw for kw in irrelevant_keywords if kw in ai_response]
                    if mentioned_irrelevant:
                        print(f"  WARNING: 提到了可能不相关的内容: {mentioned_irrelevant}")

                    # 检查是否是通用回复
                    if "抱歉" in ai_response or "无法" in ai_response:
                        print("  WARNING: AI表示无法处理图片")

                    # 检查回复质量
                    if len(ai_response) < 100:
                        print("  WARNING: 回复过短，可能信息不足")
                    elif len(ai_response) > 300:
                        print("  INFO: 回复详细")

                else:
                    print("ERROR: 响应中没有内容")

            else:
                print(f"ERROR: 请求失败 - {response.status_code}")
                print(f"错误信息: {response.text}")

        except Exception as e:
            print(f"ERROR: 请求异常 - {e}")

def check_image_processing_code():
    """检查图片处理相关代码"""
    print("\n=== 检查图片处理代码 ===")

    # 检查claude_router.py中的图片优化逻辑
    try:
        with open("protobuf2openai/claude_router.py", 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找图片优化相关的代码
        if "_optimize_image_prompts" in content:
            print("发现图片提示词优化函数")

        if "problematic_words" in content:
            print("发现问题词汇过滤")
            # 提取问题词汇列表
            import re
            pattern = r'problematic_words\s*=\s*\[(.*?)\]'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                words_str = match.group(1)
                print(f"  过滤词汇: {words_str}")

        if "阿里云" in content:
            print("WARNING: 代码中包含'阿里云'硬编码")

    except Exception as e:
        print(f"检查代码失败: {e}")

if __name__ == "__main__":
    test_ali_image()
    check_image_processing_code()

    print("\n=== 总结 ===")
    print("如果AI解释与图片内容不符，可能原因:")
    print("1. 图片传输过程中出现问题")
    print("2. 提示词被过度过滤或修改")
    print("3. AI模型的视觉理解偏差")
    print("4. 存在硬编码的干扰内容")
    print("5. 缓存导致的旧回复")