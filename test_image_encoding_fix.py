#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片编码修复效果
"""

import requests
import json
import base64
import time

def test_image_encoding_fix():
    """测试修复后的图片编码处理"""
    print("=== 测试图片编码修复效果 ===")

    # 读取图片
    with open("ali.png", 'rb') as f:
        image_data = f.read()
    base64_data = base64.b64encode(image_data).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    # 测试简单的图片请求
    payload = {
        "model": "claude-4-sonnet",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片"
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

    print("发送图片请求...")
    print(f"图片大小: {len(image_data)} bytes")
    print(f"Base64长度: {len(base64_data)} chars")

    try:
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
            if content:
                ai_response = content[0].get('text', '')
                print(f"AI回复: {ai_response}")
                print("✅ 图片编码修复成功！没有UTF-8解码错误")
                return True
            else:
                print("❌ 响应中没有内容")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")

            # 检查是否还有UTF-8编码错误
            if "utf-8" in response.text.lower() and "decode" in response.text.lower():
                print("⚠️ 仍然存在UTF-8编码问题")

            return False

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_multiple_images():
    """测试多张图片的处理"""
    print("\n=== 测试多张图片处理 ===")

    # 读取图片
    with open("ali.png", 'rb') as f:
        image_data = f.read()
    base64_data = base64.b64encode(image_data).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    # 测试包含多张相同图片的请求
    payload = {
        "model": "claude-4-sonnet",
        "max_tokens": 150,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这两张图片有什么区别？"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_data
                        }
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

    print("发送多图片请求...")

    try:
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
            if content:
                ai_response = content[0].get('text', '')
                print(f"AI回复: {ai_response[:100]}...")
                print("✅ 多图片处理成功")
                return True
            else:
                print("❌ 响应中没有内容")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    print("开始测试图片编码修复...")

    # 测试单张图片
    single_ok = test_image_encoding_fix()

    # 测试多张图片
    multiple_ok = test_multiple_images()

    print("\n" + "="*50)
    print("测试总结:")
    print(f"单张图片: {'通过' if single_ok else '失败'}")
    print(f"多张图片: {'通过' if multiple_ok else '失败'}")

    if single_ok and multiple_ok:
        print("🎉 图片编码问题修复成功！")
        print("- 不再有UTF-8解码错误")
        print("- 图片数据正确传输给AI")
    else:
        print("❌ 仍需进一步调试编码问题")