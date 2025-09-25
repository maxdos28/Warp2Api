#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证测试：对比修复前后的效果
"""

import requests
import json
import base64
import time

def final_verification():
    """最终验证修复效果"""
    print("=== 最终验证：图片解释货不对版修复效果 ===")

    # 读取图片
    with open("ali.png", 'rb') as f:
        image_data = f.read()
    base64_data = base64.b64encode(image_data).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    # 测试5次，看看现在的一致性
    results = []
    content_types = []

    print("进行5次连续测试...")

    for i in range(5):
        print(f"\n--- 测试 {i+1} ---")

        payload = {
            "model": "claude-4-sonnet",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "简单描述这张图片"
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
                if content:
                    ai_response = content[0].get('text', '')
                    results.append(ai_response)

                    # 分类内容类型
                    if "终端" in ai_response or "命令" in ai_response or "shell" in ai_response:
                        content_type = "终端界面"
                    elif "数据" in ai_response or "可视化" in ai_response or "图表" in ai_response:
                        content_type = "数据可视化"
                    elif "GitHub" in ai_response or "Pull Request" in ai_response:
                        content_type = "GitHub界面"
                    elif "地图" in ai_response or "动物" in ai_response or "卡通" in ai_response:
                        content_type = "地图/动物"
                    elif "架构" in ai_response or "系统" in ai_response:
                        content_type = "系统架构"
                    else:
                        content_type = "其他"

                    content_types.append(content_type)
                    print(f"识别为: {content_type}")
                    print(f"回复: {ai_response[:80]}...")

        except Exception as e:
            print(f"异常: {e}")
            content_types.append("错误")

        time.sleep(1)

    # 分析结果
    print(f"\n=== 修复效果分析 ===")
    print(f"总测试次数: {len(content_types)}")
    print(f"识别类型: {content_types}")

    # 统计类型分布
    type_counts = {}
    for ct in content_types:
        type_counts[ct] = type_counts.get(ct, 0) + 1

    print(f"类型分布: {type_counts}")

    # 计算一致性
    most_common_type = max(type_counts, key=type_counts.get)
    consistency_rate = type_counts[most_common_type] / len(content_types)

    print(f"最常见类型: {most_common_type}")
    print(f"一致性比例: {consistency_rate:.1%}")

    print(f"\n=== 修复前后对比 ===")
    print("修复前的问题:")
    print("- 同一图片被解释为完全不同的内容")
    print("- 出现数据可视化、GitHub界面、地图动物、系统架构等完全不相关的解释")
    print("- 一致性接近0%")

    print(f"\n修复后的效果:")
    print(f"- 主要识别为: {most_common_type}")
    print(f"- 一致性提升到: {consistency_rate:.1%}")

    if consistency_rate >= 0.8:
        print("✅ 修复成功！图片解释一致性大幅提升")
        success = True
    elif consistency_rate >= 0.6:
        print("⚠️ 部分修复成功，仍有改进空间")
        success = True
    else:
        print("❌ 修复效果不明显，需要进一步调试")
        success = False

    return success

if __name__ == "__main__":
    final_verification()