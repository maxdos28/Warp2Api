#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试货不对版问题
"""

import requests
import json
import sys
import os

def test_specific_issue():
    """测试具体的货不对版问题"""
    print("=== 详细调试货不对版问题 ===")

    # 测试不同的场景
    test_cases = [
        {
            "name": "Claude API - 标准请求",
            "url": "http://127.0.0.1:28889/v1/messages",
            "payload": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 100,
                "messages": [
                    {"role": "user", "content": "请告诉我你是什么模型"}
                ]
            }
        },
        {
            "name": "OpenAI API - 标准请求",
            "url": "http://127.0.0.1:28889/v1/chat/completions",
            "payload": {
                "model": "claude-4-sonnet",
                "max_tokens": 100,
                "messages": [
                    {"role": "user", "content": "请告诉我你是什么模型"}
                ]
            }
        },
        {
            "name": "Claude API - 流式请求",
            "url": "http://127.0.0.1:28889/v1/messages",
            "payload": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 50,
                "stream": True,
                "messages": [
                    {"role": "user", "content": "Hello"}
                ]
            }
        }
    ]

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   URL: {test_case['url']}")
        print(f"   Request Model: {test_case['payload']['model']}")
        print(f"   Stream: {test_case['payload'].get('stream', False)}")

        try:
            if test_case['payload'].get('stream'):
                # 流式请求
                response = requests.post(
                    test_case['url'],
                    headers=headers,
                    json=test_case['payload'],
                    stream=True,
                    timeout=30
                )

                print(f"   Status: {response.status_code}")

                if response.status_code == 200:
                    # 读取前几个流式响应
                    lines = []
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            lines.append(line)
                            if len(lines) >= 5:  # 只读取前5行
                                break

                    print(f"   Stream Response (first 5 lines):")
                    for line in lines:
                        print(f"     {line}")

                        # 尝试解析JSON找模型信息
                        if line.startswith("data: ") and not line.endswith("[DONE]"):
                            try:
                                data_str = line[6:]
                                data = json.loads(data_str)
                                if "model" in data:
                                    print(f"   Response Model Found: {data['model']}")
                            except:
                                pass
                else:
                    print(f"   Error: {response.text}")

            else:
                # 非流式请求
                response = requests.post(
                    test_case['url'],
                    headers=headers,
                    json=test_case['payload'],
                    timeout=30
                )

                print(f"   Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()

                    # 检查响应格式
                    if "v1/messages" in test_case['url']:
                        # Claude API 格式
                        response_model = data.get('model')
                        content = data.get('content', [])
                        if content and len(content) > 0:
                            text = content[0].get('text', '')[:100]
                        else:
                            text = 'No content'
                    else:
                        # OpenAI API 格式
                        response_model = data.get('model')
                        choices = data.get('choices', [])
                        if choices:
                            text = choices[0].get('message', {}).get('content', '')[:100]
                        else:
                            text = 'No choices'

                    print(f"   Response Model: {response_model}")
                    print(f"   Content: {text}")

                    # 检查是否货不对版
                    if response_model == test_case['payload']['model']:
                        print("   Result: MATCH - 模型匹配正确")
                    else:
                        print(f"   Result: MISMATCH - 货不对版!")
                        print(f"           Expected: {test_case['payload']['model']}")
                        print(f"           Got: {response_model}")

                        # 详细分析不匹配原因
                        print("   Analysis:")
                        if not response_model:
                            print("     - 响应中没有model字段")
                        elif response_model != test_case['payload']['model']:
                            print(f"     - 模型被错误映射或替换")

                            # 检查是否是内部模型泄露
                            internal_models = ["claude-4-sonnet", "claude-4-opus", "claude-4.1-opus"]
                            if response_model in internal_models and test_case['payload']['model'] not in internal_models:
                                print(f"     - 内部模型泄露: 应该返回请求的模型名称")
                else:
                    print(f"   Error: {response.text}")

        except Exception as e:
            print(f"   Exception: {e}")

def check_current_code():
    """检查当前代码中可能导致货不对版的地方"""
    print("\n=== 检查代码中可能的问题 ===")

    # 检查响应构造的地方
    files_to_check = [
        "protobuf2openai/claude_router.py",
        "protobuf2openai/claude_converter.py",
        "protobuf2openai/router.py"
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"\n检查文件: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找可能导致模型不匹配的代码
                issues = []

                # 检查是否有硬编码的模型名称
                if 'model=' in content and 'claude-4' in content:
                    issues.append("发现硬编码的内部模型名称")

                # 检查响应构造
                if 'ClaudeMessagesResponse' in content:
                    issues.append("包含Claude响应构造逻辑")

                if 'openai_to_claude_response' in content:
                    issues.append("包含OpenAI到Claude的响应转换")

                if issues:
                    print(f"   潜在问题: {', '.join(issues)}")
                else:
                    print("   未发现明显问题")

            except Exception as e:
                print(f"   读取失败: {e}")
        else:
            print(f"文件不存在: {file_path}")

if __name__ == "__main__":
    test_specific_issue()
    check_current_code()

    print("\n=== 总结 ===")
    print("如果发现MISMATCH，说明存在以下可能问题:")
    print("1. 响应构造时使用了内部模型名称而不是请求的模型名称")
    print("2. 模型映射逻辑有误")
    print("3. 响应格式转换时丢失了原始模型信息")
    print("4. 缓存或状态管理问题")