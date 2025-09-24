#!/usr/bin/env python3
"""
测试API认证
"""

import requests
import json

def test_auth():
    """测试不同的认证方式"""
    
    base_url = "http://localhost:28889"
    
    # 测试请求体
    test_request = {
        "model": "claude-3-sonnet",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "stream": False
    }
    
    print("测试API认证")
    print("="*50)
    
    # 1. 无认证
    print("\n1. 无认证头:")
    try:
        resp = requests.post(
            f"{base_url}/v1/chat/completions",
            json=test_request,
            timeout=5
        )
        print(f"   状态码: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   响应: {resp.text[:100]}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 2. Bearer token: 001
    print("\n2. Bearer token '001':")
    try:
        resp = requests.post(
            f"{base_url}/v1/chat/completions",
            json=test_request,
            headers={"Authorization": "Bearer 001"},
            timeout=5
        )
        print(f"   状态码: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   响应: {resp.text[:100]}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 3. 直接使用001作为token
    print("\n3. 直接token '001':")
    try:
        resp = requests.post(
            f"{base_url}/v1/chat/completions",
            json=test_request,
            headers={"Authorization": "001"},
            timeout=5
        )
        print(f"   状态码: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   响应: {resp.text[:100]}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 4. 检查环境变量
    print("\n4. 检查环境变量:")
    import os
    print(f"   API_TOKEN = {os.getenv('API_TOKEN', '未设置')}")
    
    # 5. 尝试读取.env文件
    print("\n5. 检查.env文件:")
    try:
        with open('/workspace/.env', 'r') as f:
            for line in f:
                if 'API_TOKEN' in line:
                    print(f"   {line.strip()}")
    except:
        print("   .env文件不存在或无法读取")

if __name__ == "__main__":
    test_auth()