#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终图片解释测试
"""

import requests
import json
import base64
import os

def final_test():
    """最终测试"""
    print("=== 最终图片解释测试 ===")

    # 读取图片
    with open("ali.png", 'rb') as f:
        image_data = f.read()
    base64_data = base64.b64encode(image_data).decode('utf-8')

    # 简单测试
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这张图片显示了什么？"
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

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

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
            print(f"AI回复: {ai_response}")

            # 检查是否正确
            if any(word in ai_response for word in ["数据", "可视化", "界面", "仪表", "图表"]):
                print("\nRESULT: SUCCESS - AI正确识别了数据可视化界面")
                return True
            elif any(word in ai_response for word in ["动物", "地图", "卡通"]):
                print("\nRESULT: FAILED - AI仍然给出错误解释")
                return False
            else:
                print("\nRESULT: UNCLEAR - 需要人工判断")
                return False
    else:
        print(f"ERROR: {response.status_code}")
        return False

if __name__ == "__main__":
    final_test()