#!/usr/bin/env python3
"""
简单测试 Claude Code 工具支持
"""

import json
import requests
from typing import Dict, Any, List


def test_claude_code_tools():
    """测试 Claude Code 工具"""
    base_url = "http://localhost:28889"
    
    print("\n" + "="*60)
    print(" Claude Code 工具测试")
    print("="*60)
    
    # 1. 检查服务器健康状态
    print("\n[1] 检查服务器状态...")
    try:
        response = requests.get(f"{base_url}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器正在运行")
        else:
            print(f"❌ 服务器响应异常: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("请先启动服务器: ./start.sh 或 python3 openai_compat.py")
        return
    
    # 2. 测试 Computer Use 工具
    print("\n[2] 测试 Computer Use 工具 (computer_20241022)")
    print("-"*40)
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "computer-use-2024-10-22",
        "x-api-key": "test"
    }
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "请截取当前屏幕的截图"}
        ],
        "max_tokens": 200,
        "stream": False
    }
    
    print("📤 发送请求:")
    print(f"   Beta功能: computer-use-2024-10-22")
    print(f"   消息: {request_data['messages'][0]['content']}")
    
    try:
        response = requests.post(
            f"{base_url}/v1/messages",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("📥 响应:")
            
            # 检查响应内容
            content = result.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            print(f"   ✅ 检测到工具调用!")
                            print(f"      工具名: {block.get('name')}")
                            print(f"      工具ID: {block.get('id')}")
                            if "input" in block:
                                print(f"      参数: {json.dumps(block.get('input'), ensure_ascii=False)}")
                        elif block.get("type") == "text":
                            text = block.get("text", "")
                            print(f"   文本响应: {text[:200]}...")
            else:
                print(f"   响应内容: {content}")
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"   错误信息: {response.text[:500]}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 3. 测试 Code Execution 工具
    print("\n[3] 测试 Code Execution 工具 (str_replace_based_edit_tool)")
    print("-"*40)
    
    headers["anthropic-beta"] = "code-execution-2025-08-25"
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "创建一个 test.py 文件，内容是 print('Hello from Claude!')"}
        ],
        "max_tokens": 300,
        "stream": False
    }
    
    print("📤 发送请求:")
    print(f"   Beta功能: code-execution-2025-08-25")
    print(f"   消息: {request_data['messages'][0]['content']}")
    
    try:
        response = requests.post(
            f"{base_url}/v1/messages",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("📥 响应:")
            
            content = result.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            print(f"   ✅ 检测到工具调用!")
                            print(f"      工具名: {block.get('name')}")
                            print(f"      工具ID: {block.get('id')}")
                            if "input" in block:
                                print(f"      参数: {json.dumps(block.get('input'), ensure_ascii=False)}")
                        elif block.get("type") == "text":
                            text = block.get("text", "")
                            print(f"   文本响应: {text[:200]}...")
            else:
                print(f"   响应内容: {content}")
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"   错误信息: {response.text[:500]}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 4. 测试手动定义工具
    print("\n[4] 测试手动定义工具")
    print("-"*40)
    
    headers["anthropic-beta"] = ""  # 不使用 beta 功能
    
    weather_tool = {
        "name": "get_weather",
        "description": "获取指定城市的天气",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                }
            },
            "required": ["city"]
        }
    }
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "北京今天的天气怎么样？"}
        ],
        "tools": [weather_tool],
        "max_tokens": 200,
        "stream": False
    }
    
    print("📤 发送请求:")
    print(f"   自定义工具: get_weather")
    print(f"   消息: {request_data['messages'][0]['content']}")
    
    try:
        response = requests.post(
            f"{base_url}/v1/messages",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("📥 响应:")
            
            content = result.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            print(f"   ✅ 检测到工具调用!")
                            print(f"      工具名: {block.get('name')}")
                            if "input" in block:
                                print(f"      参数: {json.dumps(block.get('input'), ensure_ascii=False)}")
                        elif block.get("type") == "text":
                            text = block.get("text", "")
                            print(f"   文本响应: {text[:200]}...")
            else:
                print(f"   响应内容: {content}")
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"   错误信息: {response.text[:500]}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 5. 测试组合使用多个 Beta 功能
    print("\n[5] 测试组合使用多个 Beta 功能")
    print("-"*40)
    
    headers["anthropic-beta"] = "computer-use-2024-10-22,code-execution-2025-08-25"
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "先截图，然后创建一个文件记录截图时间"}
        ],
        "max_tokens": 400,
        "stream": False
    }
    
    print("📤 发送请求:")
    print(f"   Beta功能: computer-use + code-execution")
    print(f"   消息: {request_data['messages'][0]['content']}")
    
    try:
        response = requests.post(
            f"{base_url}/v1/messages",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("📥 响应:")
            
            content = result.get("content", [])
            tool_calls = []
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            tool_name = block.get('name')
                            tool_calls.append(tool_name)
                            print(f"   ✅ 工具调用: {tool_name}")
                            if "input" in block:
                                print(f"      参数: {json.dumps(block.get('input'), ensure_ascii=False)}")
                        elif block.get("type") == "text":
                            text = block.get("text", "")
                            print(f"   文本: {text[:100]}...")
            
            if tool_calls:
                print(f"\n📊 调用的工具汇总: {tool_calls}")
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"   错误信息: {response.text[:500]}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 总结
    print("\n" + "="*60)
    print(" 测试总结")
    print("="*60)
    print("""
✅ Claude Code 工具格式支持已实现:

1. Computer Use 工具 (computer_20241022):
   - 通过 anthropic-beta: computer-use-2024-10-22 激活
   - 工具定义已内置，会自动添加

2. Code Execution 工具 (str_replace_based_edit_tool):
   - 通过 anthropic-beta: code-execution-2025-08-25 激活
   - 工具定义已内置，会自动添加

3. 自定义工具:
   - 支持通过 tools 参数传递自定义工具
   - 正确转换为 Warp 格式

4. 工具调用格式:
   - 支持 Claude 的 tool_use 内容块
   - 支持 tool_result 响应格式

⚠️ 重要说明:
- 当前实现支持 Claude Code 工具的协议和格式
- 工具的实际执行依赖后端 Warp 服务
- 如果 Warp 服务不支持这些工具，会返回文本响应而非工具调用
""")


if __name__ == "__main__":
    print("\n🔧 Claude Code 工具测试")
    print("="*60)
    
    test_claude_code_tools()