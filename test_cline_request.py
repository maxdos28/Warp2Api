#!/usr/bin/env python3
"""
测试 Cline 请求的脚本
"""

import requests
import json

def test_cline_request():
    """模拟 Cline 的文件读取请求"""
    
    url = "http://localhost:28889/v1/chat/completions"
    
    # 模拟 Cline 的请求格式
    request_data = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": "您说得对！我确实需要为PHP版本也实现发布单每日限制功能。让我先查看PHP版本的发布单控制器代码：\n\nCline wants to read this file:\n\n/rms_php/app/Http/Controllers/ReleaseSheetController.php"
            }
        ],
        "stream": False,
        "max_tokens": 4096
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 0000",
        "User-Agent": "Cline/1.0"  # 模拟 Cline 的 User-Agent
    }
    
    print("发送 Cline 测试请求...")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Body: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    print("-" * 80)
    
    try:
        response = requests.post(url, json=request_data, headers=headers)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 检查是否返回了工具调用
            if data.get("choices"):
                message = data["choices"][0].get("message", {})
                if message.get("tool_calls"):
                    print("\n✅ 成功返回工具调用!")
                    for tool_call in message["tool_calls"]:
                        print(f"  - 工具: {tool_call['function']['name']}")
                        print(f"  - 参数: {tool_call['function']['arguments']}")
                else:
                    print("\n❌ 没有返回工具调用")
                    print(f"返回的内容: {message.get('content', '')}")
        else:
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_cline_request()
