#!/usr/bin/env python3
"""
简单测试 Cline 格式的请求
"""

import requests
import json

# 测试 API 是否运行
try:
    resp = requests.get("http://localhost:28889/healthz")
    print(f"API 健康检查: {resp.status_code} - {resp.text}")
except Exception as e:
    print(f"API 似乎没有运行: {e}")
    exit(1)

# 发送一个简单的请求
url = "http://localhost:28889/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 0000"
}

# 最简单的请求
data = {
    "model": "claude-4-sonnet",
    "messages": [
        {"role": "user", "content": "Hello"}
    ],
    "stream": False
}

print("\n发送简单请求...")
resp = requests.post(url, json=data, headers=headers)
print(f"响应状态: {resp.status_code}")
if resp.status_code == 200:
    print(f"响应: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
else:
    print(f"错误: {resp.text}")

# 测试 Cline 格式
print("\n" + "="*60)
print("测试 Cline 格式...")

cline_data = {
    "model": "claude-4-sonnet", 
    "messages": [
        {
            "role": "user",
            "content": "Cline wants to read this file:\n/test/file.php"
        }
    ],
    "stream": False
}

resp = requests.post(url, json=cline_data, headers=headers)
print(f"响应状态: {resp.status_code}")
if resp.status_code == 200:
    result = resp.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 检查是否有工具调用
    if result.get("choices", [{}])[0].get("message", {}).get("tool_calls"):
        print("\n✅ 检测到工具调用!")
    else:
        print("\n❌ 没有检测到工具调用")
else:
    print(f"错误: {resp.text}")
