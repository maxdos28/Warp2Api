#!/usr/bin/env python3
"""
简单的认证测试
"""

import requests
import json

BASE_URL = "http://localhost:28889"

def test_auth():
    """测试认证"""
    print("测试API认证...")
    
    # 测试无认证头
    print("\n1. 无认证头:")
    response = requests.get(f"{BASE_URL}/v1/messages/models")
    print(f"   状态码: {response.status_code}")
    
    # 测试错误的认证头
    print("\n2. 错误的认证头:")
    headers = {"Authorization": "Bearer wrong-key"}
    response = requests.get(f"{BASE_URL}/v1/messages/models", headers=headers)
    print(f"   状态码: {response.status_code}")
    
    # 测试正确的认证头
    print("\n3. 正确的认证头:")
    headers = {"Authorization": "Bearer test-key"}
    response = requests.get(f"{BASE_URL}/v1/messages/models", headers=headers)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        models = response.json()
        print(f"   模型数量: {len(models.get('data', []))}")
    
    # 测试简单消息
    print("\n4. 简单消息测试:")
    headers = {
        "Authorization": "Bearer test-key",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 50
    }
    
    response = requests.post(f"{BASE_URL}/v1/messages", headers=headers, json=data)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   响应类型: {result.get('type', 'unknown')}")
        content = result.get('content', [])
        if content:
            print(f"   内容块数: {len(content)}")
    else:
        print(f"   错误: {response.text[:200]}")

if __name__ == "__main__":
    test_auth()