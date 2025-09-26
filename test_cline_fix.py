#!/usr/bin/env python3
"""
测试 Cline 修复
"""

import requests
import json

url = "http://localhost:28889/v1/chat/completions"

# 模拟 Cline 的确切请求格式
data = {
    "model": "claude-4-sonnet",
    "messages": [
        {
            "role": "user", 
            "content": """我来帮您完成PHP版本的发布单每日限制功能。首先让我检查当前PHP代码的结构和已有实现。

Cline wants to read this file:

/...php/app/Models/ReleaseSheet.php"""
        }
    ],
    "stream": False
}

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 0000"
}

print("测试 Cline 修复...")
print(f"请求内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
print("-" * 80)

try:
    resp = requests.post(url, json=data, headers=headers)
    print(f"响应状态: {resp.status_code}")
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 检查是否有工具调用
        choices = result.get("choices", [])
        if choices and choices[0].get("message", {}).get("tool_calls"):
            print("\n✅ 成功返回工具调用!")
            for tool in choices[0]["message"]["tool_calls"]:
                print(f"  - 工具: {tool['function']['name']}")
                print(f"  - 参数: {tool['function']['arguments']}")
        else:
            print("\n❌ 没有返回工具调用")
    else:
        print(f"错误: {resp.text}")
        
except Exception as e:
    print(f"请求失败: {e}")
    print("\n请确保 API 服务器正在运行："")
    print("python openai_compat.py")
