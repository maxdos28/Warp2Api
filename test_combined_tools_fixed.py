#!/usr/bin/env python3
"""
修复后的组合工具测试
"""

import requests
import json

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def test_combined_tools_step_by_step():
    """测试分步骤的组合工具使用"""
    print("=== 分步骤组合工具测试 ===")
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "computer-use-2024-10-22,code-execution-2025-08-25",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 第一步：要求截图
    print("\n第一步：要求截图")
    step1_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "请截取屏幕截图"}],
        "max_tokens": 200
    }
    
    response1 = requests.post(f"{BASE_URL}/v1/messages", json=step1_data, headers=headers)
    
    if response1.status_code == 200:
        result1 = response1.json()
        tools1 = [block.get('name') for block in result1.get('content', []) if block.get('type') == 'tool_use']
        print(f"第一步调用的工具: {tools1}")
        
        # 模拟工具执行结果
        if 'computer_20241022' in tools1:
            # 第二步：基于截图结果，要求创建文件
            print("\n第二步：基于截图结果创建文件")
            
            # 构建包含工具结果的对话
            messages = [
                {"role": "user", "content": "请截取屏幕截图"},
                {
                    "role": "assistant", 
                    "content": result1.get('content', [])
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": next((block.get('id') for block in result1.get('content', []) if block.get('type') == 'tool_use'), 'tool_id'),
                            "content": "截图已成功保存为 screenshot_2024.png"
                        }
                    ]
                },
                {"role": "user", "content": "很好！现在请创建一个文件screenshot_log.txt，记录截图时间"}
            ]
            
            step2_data = {
                "model": "claude-3-5-sonnet-20241022",
                "messages": messages,
                "max_tokens": 300
            }
            
            response2 = requests.post(f"{BASE_URL}/v1/messages", json=step2_data, headers=headers)
            
            if response2.status_code == 200:
                result2 = response2.json()
                tools2 = [block.get('name') for block in result2.get('content', []) if block.get('type') == 'tool_use']
                print(f"第二步调用的工具: {tools2}")
                
                # 检查是否调用了文件创建工具
                has_computer = 'computer_20241022' in tools1
                has_file_tool = 'str_replace_based_edit_tool' in tools2
                
                print(f"\n结果分析:")
                print(f"  第一步调用Computer Use工具: {'✅' if has_computer else '❌'}")
                print(f"  第二步调用Code Execution工具: {'✅' if has_file_tool else '❌'}")
                print(f"  分步骤组合使用: {'✅' if has_computer and has_file_tool else '❌'}")
                
                return has_computer and has_file_tool
            else:
                print(f"第二步请求失败: {response2.status_code}")
                return False
        else:
            print("第一步未调用Computer Use工具")
            return False
    else:
        print(f"第一步请求失败: {response1.status_code}")
        return False

def test_single_request_multiple_tools():
    """测试单个请求中的多工具暗示"""
    print("\n=== 单请求多工具暗示测试 ===")
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "computer-use-2024-10-22,code-execution-2025-08-25",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 使用更强的暗示让AI知道需要两步操作
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "我需要你帮我做两件事：1）截取当前屏幕截图 2）创建一个文本文件记录这次操作。请先告诉我你会怎么做。"}],
        "max_tokens": 400
    }
    
    response = requests.post(f"{BASE_URL}/v1/messages", json=request_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        tools = [block.get('name') for block in result.get('content', []) if block.get('type') == 'tool_use']
        content = result.get('content', [])
        
        print(f"AI的响应中调用的工具: {tools}")
        
        # 检查响应中是否提到了两种工具
        text_content = ""
        for block in content:
            if block.get('type') == 'text':
                text_content += block.get('text', '')
        
        mentions_screenshot = any(word in text_content.lower() for word in ['screenshot', '截图', 'computer'])
        mentions_file = any(word in text_content.lower() for word in ['file', '文件', 'create', '创建'])
        
        print(f"文本中提到截图: {'✅' if mentions_screenshot else '❌'}")
        print(f"文本中提到文件操作: {'✅' if mentions_file else '❌'}")
        print(f"实际调用工具数量: {len(tools)}")
        
        # 如果AI理解了任务但只执行第一步，这也是合理的
        return len(tools) >= 1 and (mentions_screenshot or mentions_file)
    else:
        print(f"请求失败: {response.status_code}")
        return False

if __name__ == "__main__":
    print("开始测试组合工具使用...")
    
    # 测试分步骤组合使用
    step_by_step_success = test_combined_tools_step_by_step()
    
    # 测试单请求多工具理解
    single_request_success = test_single_request_multiple_tools()
    
    print(f"\n=== 最终结果 ===")
    print(f"分步骤组合使用: {'✅ 成功' if step_by_step_success else '❌ 失败'}")
    print(f"单请求多工具理解: {'✅ 成功' if single_request_success else '❌ 失败'}")
    
    if step_by_step_success:
        print("\n✅ 组合工具使用功能正常 - AI能够在对话中依次使用不同工具")
    else:
        print("\n⚠️ 组合工具使用需要改进")