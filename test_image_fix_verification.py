#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证图片解释修复效果
"""

import requests
import json
import base64
import os

def test_image_fix():
    """测试修复后的图片解释功能"""
    print("=== 验证图片解释修复效果 ===")

    # 使用ali.png进行测试
    img_path = "ali.png"
    if not os.path.exists(img_path):
        print(f"图片文件不存在: {img_path}")
        return

    # 读取并编码图片
    try:
        with open(img_path, 'rb') as f:
            image_data = f.read()
        base64_data = base64.b64encode(image_data).decode('utf-8')
        print(f"图片编码成功: {len(base64_data)} chars")
    except Exception as e:
        print(f"图片编码失败: {e}")
        return

    # 测试多个不同的提示词，验证是否都能得到准确回复
    test_cases = [
        {
            "name": "具体描述请求",
            "prompt": "请详细描述这张图片显示的内容，包括界面元素、文字、图表等。"
        },
        {
            "name": "系统识别请求",
            "prompt": "这是什么系统的界面？请分析其功能。"
        },
        {
            "name": "简单问题",
            "prompt": "这张图片显示了什么？"
        },
        {
            "name": "包含关键词的问题",
            "prompt": "这个数据可视化界面有哪些功能模块？"
        }
    ]

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    all_correct = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}: {test_case['name']} ---")
        print(f"提示词: {test_case['prompt']}")

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 400,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": test_case['prompt']
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
            response = requests.post(
                "http://127.0.0.1:28889/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get('content', [])

                if content and len(content) > 0:
                    ai_response = content[0].get('text', '')
                    print(f"AI回复: {ai_response[:200]}...")

                    # 检查回复质量
                    is_correct = True

                    # 检查是否提到了正确的内容（数据可视化、仪表板等）
                    correct_keywords = ["数据", "可视化", "仪表", "图表", "DataEase", "界面"]
                    has_correct_content = any(kw in ai_response for kw in correct_keywords)

                    # 检查是否提到了错误的内容（动物、地图等）
                    wrong_keywords = ["动物", "地图", "卡通", "世界", "大陆", "海洋"]
                    has_wrong_content = any(kw in ai_response for kw in wrong_keywords)

                    if has_wrong_content:
                        print("  ❌ 错误：AI提到了不相关的内容（动物、地图等）")
                        is_correct = False
                        all_correct = False

                    if has_correct_content:
                        print("  ✅ 正确：AI识别了数据可视化相关内容")
                    else:
                        print("  ⚠️  警告：AI没有识别出数据可视化特征")
                        is_correct = False

                    if "抱歉" in ai_response or "无法" in ai_response:
                        print("  ❌ 错误：AI表示无法处理")
                        is_correct = False
                        all_correct = False

                    if is_correct:
                        print("  结果: PASS")
                    else:
                        print("  结果: FAIL")

                else:
                    print("  ❌ 错误：响应中没有内容")
                    all_correct = False

            else:
                print(f"  ❌ 错误：HTTP {response.status_code}")
                print(f"  错误信息: {response.text}")
                all_correct = False

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            all_correct = False

    print("\n" + "="*50)
    if all_correct:
        print("🎉 修复成功！所有测试都通过了")
        print("✅ 图片解释现在准确匹配实际内容")
        print("✅ 不再有过度过滤导致的错误解释")
    else:
        print("❌ 仍存在问题，需要进一步调试")

    return all_correct

if __name__ == "__main__":
    test_image_fix()