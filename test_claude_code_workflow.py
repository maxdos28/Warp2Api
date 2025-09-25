#!/usr/bin/env python3
"""
测试Claude Code完整工作流程
模拟创建CLAUDE.md文件的过程
"""

import requests
import json
import time

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def simulate_claude_code_workflow():
    """模拟Claude Code的完整工作流程"""
    print("🤖 模拟Claude Code完整工作流程")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "code-execution-2025-08-25"
    }
    
    # 步骤1: 分析项目结构
    print("\n[步骤1] 要求分析项目并创建CLAUDE.md")
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "system": [
            {
                "type": "text",
                "text": "You are Claude Code. You help with software development tasks. Always complete the requested tasks fully.",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": "请分析这个项目的代码库结构，然后创建一个comprehensive CLAUDE.md文件，包含项目概述、主要功能、技术栈等信息。"
            }
        ],
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json=request_data,
            headers=headers,
            timeout=60
        )
        
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content_blocks = result.get('content', [])
            
            print(f"响应内容块数量: {len(content_blocks)}")
            
            tool_calls = []
            text_responses = []
            
            for i, block in enumerate(content_blocks):
                block_type = block.get('type')
                print(f"  {i+1}. {block_type}")
                
                if block_type == 'tool_use':
                    tool_calls.append({
                        'name': block.get('name'),
                        'input': block.get('input'),
                        'id': block.get('id')
                    })
                    print(f"     工具: {block.get('name')}")
                    print(f"     参数: {block.get('input')}")
                elif block_type == 'text':
                    text = block.get('text', '')
                    text_responses.append(text)
                    print(f"     文本: {text[:100]}...")
            
            print(f"\n📊 执行统计:")
            print(f"   工具调用: {len(tool_calls)} 个")
            print(f"   文本响应: {len(text_responses)} 个")
            
            # 检查是否有文件创建操作
            file_operations = [
                tool for tool in tool_calls 
                if tool['name'] == 'str_replace_based_edit_tool' and 
                tool['input'].get('command') == 'create'
            ]
            
            print(f"   文件创建操作: {len(file_operations)} 个")
            
            if file_operations:
                for op in file_operations:
                    file_path = op['input'].get('path')
                    print(f"     创建文件: {file_path}")
                    
                    # 检查文件是否真的被创建
                    import os
                    if os.path.exists(f"/workspace/{file_path}"):
                        print(f"     ✅ 文件确实存在")
                        with open(f"/workspace/{file_path}", 'r') as f:
                            content = f.read()
                            print(f"     文件大小: {len(content)} 字符")
                    else:
                        print(f"     ❌ 文件不存在")
            
            # 检查是否有成功的执行结果指示
            has_success_indicator = any("✅" in text for text in text_responses)
            has_error_indicator = any("❌" in text for text in text_responses)
            
            print(f"\n🔍 执行结果分析:")
            print(f"   包含成功指示: {'✅' if has_success_indicator else '❌'}")
            print(f"   包含错误指示: {'✅' if has_error_indicator else '❌'}")
            
            return {
                "success": response.status_code == 200,
                "tool_calls": len(tool_calls),
                "file_operations": len(file_operations),
                "has_success": has_success_indicator,
                "has_error": has_error_indicator
            }
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"错误内容: {response.text[:300]}")
            return {"success": False}
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return {"success": False}

def check_created_files():
    """检查是否创建了预期的文件"""
    print("\n📁 检查创建的文件")
    print("="*40)
    
    expected_files = ["CLAUDE.md", "claude.md", "Claude.md"]
    found_files = []
    
    import os
    for filename in expected_files:
        if os.path.exists(f"/workspace/{filename}"):
            found_files.append(filename)
            size = os.path.getsize(f"/workspace/{filename}")
            print(f"✅ 找到文件: {filename} ({size} 字节)")
        else:
            print(f"❌ 未找到: {filename}")
    
    # 检查所有.md文件
    md_files = [f for f in os.listdir("/workspace") if f.endswith('.md')]
    print(f"\n所有.md文件: {md_files}")
    
    return len(found_files) > 0

def main():
    """主测试函数"""
    print("🧪 Claude Code工作流程完整测试")
    print("="*60)
    print("目标: 验证Claude Code能否完整执行并创建CLAUDE.md文件")
    
    # 等待服务器启动
    print("\n等待服务器启动...")
    time.sleep(8)
    
    # 检查服务器状态
    try:
        health = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if health.status_code != 200:
            print("❌ 服务器未正常运行")
            return
        print("✅ 服务器运行正常")
    except:
        print("❌ 无法连接服务器")
        return
    
    # 执行工作流程测试
    workflow_result = simulate_claude_code_workflow()
    
    # 检查文件创建
    files_created = check_created_files()
    
    # 总结
    print("\n" + "="*60)
    print("🎯 测试结果总结")
    print("="*60)
    
    if workflow_result.get("success"):
        print("✅ API调用成功")
        print(f"   工具调用: {workflow_result.get('tool_calls', 0)} 个")
        print(f"   文件操作: {workflow_result.get('file_operations', 0)} 个")
        print(f"   执行成功: {'✅' if workflow_result.get('has_success') else '❌'}")
        print(f"   执行错误: {'✅' if workflow_result.get('has_error') else '❌'}")
    else:
        print("❌ API调用失败")
    
    print(f"CLAUDE.md文件创建: {'✅ 成功' if files_created else '❌ 失败'}")
    
    if workflow_result.get("success") and files_created:
        print("\n🎉 Claude Code工作流程完全正常！")
        print("✅ 能够完整执行任务")
        print("✅ 能够创建文件")
        print("✅ 不会中途停止")
    elif workflow_result.get("success"):
        print("\n🟡 Claude Code部分正常")
        print("✅ 能够执行工具调用")
        print("❌ 但文件创建可能有问题")
    else:
        print("\n❌ Claude Code仍有问题")
        print("需要进一步调试")

if __name__ == "__main__":
    main()