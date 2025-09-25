#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试版本不匹配问题
实际测试API调用，查看具体哪里还有货不对版的问题
"""

import requests
import json
import time
import os
import sys

def test_claude_api_call():
    """测试Claude API调用"""
    print("=== 测试Claude Messages API ===")

    url = "http://127.0.0.1:28889/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    # 测试用例1: Claude 3.5 Sonnet
    payload1 = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 50,
        "messages": [
            {"role": "user", "content": "Hello, please respond with just 'Hi there!'"}
        ]
    }

    print(f"发送请求: {payload1['model']}")
    try:
        response = requests.post(url, headers=headers, json=payload1, timeout=30)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"响应模型: {data.get('model', 'N/A')}")
            print(f"响应内容: {data.get('content', [{}])[0].get('text', 'N/A')[:100]}")

            # 检查模型是否匹配
            if data.get('model') == payload1['model']:
                print("✅ 模型匹配正确")
            else:
                print(f"❌ 模型不匹配! 请求: {payload1['model']}, 响应: {data.get('model')}")
        else:
            print(f"请求失败: {response.text}")
            return False

    except Exception as e:
        print(f"请求异常: {e}")
        return False

    return True

def test_openai_api_call():
    """测试OpenAI API调用"""
    print("\n=== 测试OpenAI Chat Completions API ===")

    url = "http://127.0.0.1:28889/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    # 测试用例: Claude模型通过OpenAI接口
    payload = {
        "model": "claude-4-sonnet",
        "max_tokens": 50,
        "messages": [
            {"role": "user", "content": "Hello, please respond with just 'Hi there!'"}
        ]
    }

    print(f"发送请求: {payload['model']}")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"响应模型: {data.get('model', 'N/A')}")

            choices = data.get('choices', [])
            if choices:
                content = choices[0].get('message', {}).get('content', 'N/A')
                print(f"响应内容: {content[:100]}")

            # 检查模型是否匹配
            if data.get('model') == payload['model']:
                print("✅ 模型匹配正确")
            else:
                print(f"❌ 模型不匹配! 请求: {payload['model']}, 响应: {data.get('model')}")
        else:
            print(f"请求失败: {response.text}")
            return False

    except Exception as e:
        print(f"请求异常: {e}")
        return False

    return True

def test_model_conversion():
    """测试模型转换逻辑"""
    print("\n=== 测试模型转换逻辑 ===")

    # 导入转换函数
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    try:
        from protobuf2openai.claude_models import get_internal_model_name

        test_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-4-sonnet",
            "unknown-model"
        ]

        for model in test_models:
            internal = get_internal_model_name(model)
            print(f"{model} -> {internal}")

    except Exception as e:
        print(f"导入或转换失败: {e}")

def check_logs():
    """检查日志文件"""
    print("\n=== 检查最近的日志 ===")

    log_files = [
        "logs/openai_compat.log",
        "logs/server.log"
    ]

    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n--- {log_file} (最后10行) ---")
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(line.strip())
            except Exception as e:
                print(f"读取日志失败: {e}")
        else:
            print(f"{log_file} 不存在")

if __name__ == "__main__":
    print("开始调试版本不匹配问题...")

    # 测试模型转换逻辑
    test_model_conversion()

    # 测试实际API调用
    claude_success = test_claude_api_call()
    openai_success = test_openai_api_call()

    # 检查日志
    check_logs()

    print("\n=== 调试总结 ===")
    if claude_success and openai_success:
        print("✅ API调用成功，模型映射正常工作")
    else:
        print("❌ 仍存在问题，请检查上述错误信息")
        print("可能的问题:")
        print("1. 服务器未正常启动")
        print("2. JWT token过期")
        print("3. 网络连接问题")
        print("4. 模型映射仍有问题")