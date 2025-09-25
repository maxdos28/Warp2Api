#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude API 兼容性测试脚本
"""

import json
import requests
import time
import sys

# 服务器配置
BASE_URL = "http://127.0.0.1:28888"
API_TOKEN = "123456"

def test_claude_models():
    """测试 Claude 模型列表"""
    print("=== 测试 Claude 模型列表 ===")
    
    headers = {
        "x-api-key": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/v1/models", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            print(f"模型数量: {len(models.get('data', []))}")
            for model in models.get('data', [])[:3]:  # 显示前3个模型
                print(f"  - {model.get('id', 'unknown')}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    print()

def test_claude_message_simple():
    """测试 Claude 简单消息（非流式）"""
    print("=== 测试 Claude 简单消息（非流式）===")
    
    headers = {
        "x-api-key": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "claude-4.1-opus",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": "Hello! Please say hi back."
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
            print(f"停止原因: {result.get('stop_reason', 'unknown')}")
            
            content = result.get('content', [])
            if content and len(content) > 0:
                text_content = content[0].get('text', '')
                print(f"响应内容: {text_content[:100]}...")
            else:
                print("响应内容: (空)")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    print()

def test_claude_message_stream():
    """测试 Claude 流式消息"""
    print("=== 测试 Claude 流式消息 ===")
    
    headers = {
        "x-api-key": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "claude-4.1-opus",
        "max_tokens": 1024,
        "stream": True,
        "messages": [
            {
                "role": "user", 
                "content": "请用中文简单介绍一下人工智能。"
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/messages", headers=headers, json=data, stream=True)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("流式响应:")
            event_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line and line.strip():
                    print(f"  {line}")
                    event_count += 1
                    if event_count >= 10:  # 限制显示前10个事件
                        print("  ... (省略更多事件)")
                        break
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    print()

def test_claude_with_system():
    """测试带系统提示的 Claude 消息"""
    print("=== 测试带系统提示的 Claude 消息 ===")
    
    headers = {
        "x-api-key": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "claude-4.1-opus",
        "max_tokens": 512,
        "system": "你是一个友善的助手，总是用简洁的方式回答问题。",
        "messages": [
            {
                "role": "user",
                "content": "什么是机器学习？"
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
            else:
                print("响应: (空)")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    print()

def main():
    print("Claude API 兼容性测试")
    print("=" * 50)
    print(f"服务器: {BASE_URL}")
    print(f"API Token: {API_TOKEN}")
    print()
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if response.status_code != 200:
            print(f"⚠️ 服务器健康检查失败: HTTP {response.status_code}")
            print("请确保服务器正在运行: python server.py")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("请确保服务器正在运行: python server.py")
        sys.exit(1)
    
    print("✅ 服务器连接正常")
    print()
    
    # 运行测试
    test_claude_models()
    test_claude_message_simple()
    test_claude_message_stream()
    test_claude_with_system()
    
    print("测试完成！")

if __name__ == "__main__":
    main()