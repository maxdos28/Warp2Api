#!/usr/bin/env python3
"""
测试错误原因
"""

import requests

# 1. 测试 Bridge 服务
print("1. 测试 Bridge 服务 (端口 28888)...")
try:
    resp = requests.get("http://localhost:28888/healthz", timeout=2)
    print(f"   Bridge 状态: {resp.status_code}")
    if resp.status_code == 200:
        print("   ✅ Bridge 服务正常")
    else:
        print("   ❌ Bridge 服务异常")
except Exception as e:
    print(f"   ❌ Bridge 服务未运行: {e}")

# 2. 测试 OpenAI API 服务
print("\n2. 测试 OpenAI API 服务 (端口 28889)...")
try:
    resp = requests.get("http://localhost:28889/healthz", timeout=2)
    print(f"   API 状态: {resp.status_code}")
    if resp.status_code == 200:
        print("   ✅ API 服务正常")
    else:
        print("   ❌ API 服务异常")
except Exception as e:
    print(f"   ❌ API 服务未运行: {e}")

# 3. 测试简单请求
print("\n3. 测试简单请求...")
try:
    data = {
        "model": "claude-4-sonnet",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    }
    resp = requests.post(
        "http://localhost:28889/v1/chat/completions",
        json=data,
        headers={"Authorization": "Bearer 0000"},
        timeout=10
    )
    print(f"   响应状态: {resp.status_code}")
    if resp.status_code == 200:
        result = resp.json()
        if "error" in result:
            print(f"   ❌ 错误: {result['error']}")
        else:
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"   响应内容: {content[:100]}...")
    else:
        print(f"   ❌ 错误: {resp.text}")
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

print("\n诊断结果：")
print("如果 Bridge 服务未运行，请运行: python server.py")
print("如果 API 服务未运行，请运行: python openai_compat.py")
