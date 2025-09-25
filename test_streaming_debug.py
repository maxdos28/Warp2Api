#!/usr/bin/env python3
"""
调试流式响应中的工具调用
"""

import requests
import json

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def test_streaming_tool_call():
    """测试流式工具调用"""
    print("=== 流式工具调用调试 ===")
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "computer-use-2024-10-22",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "请截取屏幕截图"}],
        "max_tokens": 200,
        "stream": True
    }
    
    print("发送流式请求...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json=request_data,
            headers=headers,
            stream=True,
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"错误: {response.text}")
            return False
        
        events = []
        content_blocks = []
        tool_uses = []
        
        print("\n--- 流式事件 ---")
        
        for line_num, line in enumerate(response.iter_lines()):
            if line:
                line_text = line.decode('utf-8')
                print(f"[{line_num:02d}] {line_text}")
                
                if line_text.startswith('event:'):
                    event_type = line_text[6:].strip()
                    events.append(event_type)
                    
                elif line_text.startswith('data:'):
                    try:
                        data_json = line_text[5:].strip()
                        if data_json and data_json != "[DONE]":
                            data = json.loads(data_json)
                            
                            # 检测工具使用
                            if data.get("type") == "content_block_start":
                                block = data.get("content_block", {})
                                content_blocks.append(block.get("type", "unknown"))
                                
                                if block.get("type") == "tool_use":
                                    tool_uses.append({
                                        "name": block.get("name"),
                                        "id": block.get("id")
                                    })
                                    
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {e}")
                        print(f"数据: {data_json}")
        
        print(f"\n--- 统计结果 ---")
        print(f"事件类型: {list(set(events))}")
        print(f"内容块类型: {content_blocks}")
        print(f"工具使用: {tool_uses}")
        
        # 判断是否成功
        has_tool_event = "content_block_start" in events
        has_tool_use = any("tool_use" == block_type for block_type in content_blocks)
        
        print(f"\n--- 结果判断 ---")
        print(f"包含内容块事件: {has_tool_event}")
        print(f"包含工具使用: {has_tool_use}")
        
        return has_tool_event and has_tool_use
        
    except Exception as e:
        print(f"请求异常: {e}")
        return False

def test_non_streaming_comparison():
    """对比非流式响应"""
    print("\n=== 非流式响应对比 ===")
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "computer-use-2024-10-22",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "请截取屏幕截图"}],
        "max_tokens": 200,
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("content", [])
            
            print("非流式响应内容:")
            for i, block in enumerate(content):
                print(f"  [{i}] 类型: {block.get('type')}")
                if block.get("type") == "tool_use":
                    print(f"      工具: {block.get('name')}")
                    print(f"      ID: {block.get('id')}")
                    print(f"      参数: {block.get('input', {})}")
            
            return any(block.get("type") == "tool_use" for block in content)
        else:
            print(f"非流式请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"非流式请求异常: {e}")
        return False

if __name__ == "__main__":
    print("开始调试流式工具调用...")
    
    # 测试非流式作为参考
    non_streaming_success = test_non_streaming_comparison()
    
    # 测试流式
    streaming_success = test_streaming_tool_call()
    
    print(f"\n=== 最终结果 ===")
    print(f"非流式工具调用: {'成功' if non_streaming_success else '失败'}")
    print(f"流式工具调用: {'成功' if streaming_success else '失败'}")
    
    if non_streaming_success and not streaming_success:
        print("⚠️ 流式响应中的工具调用处理有问题")
    elif streaming_success:
        print("✅ 流式工具调用正常工作")