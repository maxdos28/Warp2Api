#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的图片一致性测试
"""

import requests
import json
import base64
import time

def simple_consistency_test():
    """简单的一致性测试"""
    print("=== 简单图片一致性测试 ===")

    # 读取图片
    with open("ali.png", 'rb') as f:
        image_data = f.read()
    base64_data = base64.b64encode(image_data).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    # 测试3次，使用相同的简单提示词
    results = []

    for i in range(3):
        print(f"\n--- 测试 {i+1} ---")

        payload = {
            "model": "claude-4-sonnet",
            "max_tokens": 150,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "这是什么？"
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
                    print(f"回复: {ai_response}")
                else:
                    results.append("NO_CONTENT")
                    print("无内容")
            else:
                results.append(f"ERROR_{response.status_code}")
                print(f"错误: {response.status_code}")

        except Exception as e:
            results.append(f"EXCEPTION")
            print(f"异常: {e}")

        # 等待
        time.sleep(2)

    # 分析结果
    print(f"\n=== 结果分析 ===")

    # 检查关键词一致性
    keywords_sets = []
    for result in results:
        keywords = set()
        if "终端" in result or "命令" in result or "shell" in result:
            keywords.add("终端")
        if "代码" in result or "编程" in result or "git" in result:
            keywords.add("代码")
        if "数据" in result or "可视化" in result or "图表" in result:
            keywords.add("数据")
        if "界面" in result or "应用" in result or "软件" in result:
            keywords.add("界面")

        keywords_sets.append(keywords)

    print(f"关键词集合: {keywords_sets}")

    # 检查是否有共同的关键词
    if keywords_sets:
        common_keywords = keywords_sets[0]
        for kw_set in keywords_sets[1:]:
            common_keywords = common_keywords.intersection(kw_set)

        print(f"共同关键词: {common_keywords}")

        if len(common_keywords) > 0:
            print("RESULT: 有一定一致性")
            return True
        else:
            print("RESULT: 完全不一致")
            return False
    else:
        print("RESULT: 无法分析")
        return False

if __name__ == "__main__":
    simple_consistency_test()