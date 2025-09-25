#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import base64

def test_image():
    """简单的图片测试"""
    print("测试图片解析...")

    # 读取图片
    with open("ali.png", 'rb') as f:
        image_data = f.read()
    base64_data = base64.b64encode(image_data).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "API_TOKEN": "123456"
    }

    payload = {
        "model": "claude-4-sonnet",
        "max_tokens": 500,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请详细描述这张图片的内容"
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
            timeout=120
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

            content = data.get('content', [])
            if content:
                ai_response = content[0].get('text', '')
                print(f"\nAI回复: {ai_response}")
                return ai_response
        else:
            print(f"错误: {response.text}")
            return None

    except Exception as e:
        print(f"异常: {e}")
        return None

if __name__ == "__main__":
    result = test_image()
    if result:
        print("\n测试成功!")
    else:
        print("\n测试失败!")