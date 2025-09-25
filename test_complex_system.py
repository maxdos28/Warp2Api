#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试复杂 system 内容的 Claude API
"""

import json
import requests

# 服务器配置
BASE_URL = "http://127.0.0.1:28889"
API_TOKEN = "123456"

def test_complex_system():
    """测试复杂的 system 内容"""
    print("=== 测试复杂 system 内容 ===")
    
    headers = {
        "x-api-key": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    # 模拟类似错误消息中的复杂 system 结构
    data = {
        "model": "claude-4.1-opus",
        "max_tokens": 1024,
        "system": [
            {
                "type": "text",
                "text": "You are Claude Code, Anthropic's official CLI for Claude.",
                "cache_control": {"type": "ephemeral"}
            },
            {
                "type": "text",
                "text": "\nYou are an interactive CLI tool that helps users with software engineering tasks.",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": "Hello! Can you help me with a simple task?"
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/messages", headers=headers, json=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"消息ID: {result.get('id', 'unknown')}")
            print(f"模型: {result.get('model', 'unknown')}")
            content = result.get('content', [])
            if content and len(content) > 0:
                text_content = content[0].get('text', '')
                print(f"响应内容: {text_content[:200]}...")
            else:
                print("响应内容: (空)")
            print("✅ 复杂 system 内容处理成功")
        else:
            print(f"❌ 错误: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    print()

def test_simple_system():
    """测试简单的 system 内容"""
    print("=== 测试简单 system 内容 ===")
    
    headers = {
        "x-api-key": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "claude-4.1-opus",
        "max_tokens": 1024,
        "system": "You are a helpful assistant.",
        "messages": [
            {
                "role": "user",
                "content": "What's 2+2?"
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/messages", headers=headers, json=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            content = result.get('content', [])
            if content and len(content) > 0:
                text_content = content[0].get('text', '')
                print(f"响应: {text_content}")
            print("✅ 简单 system 内容处理成功")
        else:
            print(f"❌ 错误: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    print()

def main():
    print("复杂 System 内容测试")
    print("=" * 50)
    
    # 等待服务器启动
    import time
    time.sleep(5)
    
    # 检查服务器
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if response.status_code != 200:
            print(f"⚠️ 服务器健康检查失败: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return
    
    print("✅ 服务器连接正常")
    print()
    
    # 运行测试
    test_simple_system()
    test_complex_system()
    
    print("测试完成！")

if __name__ == "__main__":
    main()