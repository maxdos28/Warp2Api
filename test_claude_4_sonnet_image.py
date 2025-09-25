#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用claude-4-sonnet测试图片解释一致性
"""

import requests
import json
import base64
import time

def test_claude_4_sonnet_consistency():
    """使用claude-4-sonnet测试图片解释一致性"""
    print("=== 使用claude-4-sonnet测试图片解释一致性 ===")

    # 读取图片
    with open("ali.png", 'rb') as f:
        image_data = f.read()
    base64_data = base64.b64encode(image_data).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    # 测试3次，看看结果是否一致
    results = []
    test_prompt = "请描述这张图片显示的内容"

    for i in range(3):
        print(f"\n--- 第 {i+1} 次测试 (claude-4-sonnet) ---")

        # 使用Claude Messages API
        payload = {
            "model": "claude-4-sonnet",  # 直接使用内部模型名称
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": test_prompt
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

            print(f"状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                content = data.get('content', [])
                if content:
                    ai_response = content[0].get('text', '')
                    results.append(ai_response)

                    print(f"回复长度: {len(ai_response)} 字符")
                    print(f"前150字符: {ai_response[:150]}...")

                    # 分析回复内容
                    content_type = "未知"
                    if any(word in ai_response for word in ["数据", "可视化", "仪表", "图表", "DataEase"]):
                        content_type = "数据可视化"
                    elif any(word in ai_response for word in ["GitHub", "Pull Request", "PR", "代码"]):
                        content_type = "GitHub界面"
                    elif any(word in ai_response for word in ["终端", "命令行", "shell", "ls"]):
                        content_type = "终端界面"
                    elif any(word in ai_response for word in ["架构", "系统", "客户端", "服务器"]):
                        content_type = "系统架构"
                    elif any(word in ai_response for word in ["地图", "动物", "卡通"]):
                        content_type = "地图/动物"

                    print(f"识别类型: {content_type}")

            else:
                print(f"请求失败: {response.status_code}")
                print(f"错误: {response.text}")
                results.append(f"ERROR_{response.status_code}")

        except Exception as e:
            print(f"异常: {e}")
            results.append(f"EXCEPTION_{str(e)}")

        # 等待一下，避免请求过快
        time.sleep(3)

    # 分析结果
    print(f"\n=== 结果分析 ===")
    print(f"总共测试: {len(results)} 次")

    # 检查内容类型一致性
    content_types = []
    for result in results:
        if "数据" in result or "可视化" in result:
            content_types.append("数据可视化")
        elif "GitHub" in result or "Pull Request" in result:
            content_types.append("GitHub")
        elif "终端" in result or "命令行" in result:
            content_types.append("终端")
        elif "架构" in result or "系统" in result:
            content_types.append("架构")
        elif "地图" in result or "动物" in result:
            content_types.append("地图动物")
        else:
            content_types.append("其他")

    unique_types = set(content_types)
    print(f"识别出的内容类型: {content_types}")
    print(f"不同类型数量: {len(unique_types)}")

    if len(unique_types) == 1:
        print("✅ 结果一致！修复成功")
        return True
    else:
        print("❌ 仍然存在货不对版问题")
        return False

def test_openai_api_with_claude_4_sonnet():
    """通过OpenAI API测试claude-4-sonnet"""
    print("\n=== 通过OpenAI API测试claude-4-sonnet ===")

    # 读取图片
    with open("ali.png", 'rb') as f:
        image_data = f.read()
    base64_data = base64.b64encode(image_data).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

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
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_data}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            "http://127.0.0.1:28889/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            choices = data.get('choices', [])
            if choices:
                content = choices[0].get('message', {}).get('content', '')
                print(f"OpenAI API回复: {content[:200]}...")
                return True
        else:
            print(f"请求失败: {response.text}")
            return False

    except Exception as e:
        print(f"异常: {e}")
        return False

if __name__ == "__main__":
    print("开始测试claude-4-sonnet模型的图片解释一致性...")

    # 测试Claude Messages API
    claude_api_ok = test_claude_4_sonnet_consistency()

    # 测试OpenAI API
    openai_api_ok = test_openai_api_with_claude_4_sonnet()

    print("\n" + "="*50)
    print("测试总结:")
    print(f"Claude Messages API: {'通过' if claude_api_ok else '失败'}")
    print(f"OpenAI Chat API: {'通过' if openai_api_ok else '失败'}")

    if claude_api_ok and openai_api_ok:
        print("🎉 修复成功！图片解释现在一致了")
    else:
        print("❌ 仍需进一步调试")