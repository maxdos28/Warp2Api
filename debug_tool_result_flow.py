#!/usr/bin/env python3
"""
调试工具结果流程
分析为什么Claude Code收不到完整的工具执行结果
"""

import requests
import json

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def test_tool_result_flow():
    """测试完整的工具结果流程"""
    print("🔍 工具结果流程调试")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "code-execution-2025-08-25"
    }
    
    # 第一步：发送工具调用请求
    print("\n[步骤1] 发送工具调用请求")
    
    response1 = requests.post(
        f"{BASE_URL}/v1/messages",
        json={
            "model": "claude-3-5-sonnet-20241022",
            "messages": [{"role": "user", "content": "读取README.md文件的前5行"}],
            "max_tokens": 300
        },
        headers=headers,
        timeout=30
    )
    
    if response1.status_code == 200:
        result1 = response1.json()
        content_blocks = result1.get('content', [])
        
        print("第一次响应内容:")
        tool_uses = []
        for i, block in enumerate(content_blocks):
            print(f"  {i+1}. {block.get('type')}")
            if block.get('type') == 'tool_use':
                tool_uses.append(block)
                print(f"     工具: {block.get('name')}")
                print(f"     ID: {block.get('id')}")
                print(f"     参数: {block.get('input')}")
            elif block.get('type') == 'text':
                text = block.get('text', '')
                print(f"     文本: {text[:150]}...")
        
        # 如果有工具调用，模拟Claude Code的后续步骤
        if tool_uses:
            tool_use = tool_uses[0]
            tool_id = tool_use.get('id')
            
            print(f"\n[步骤2] 模拟发送工具执行结果")
            
            # 构建包含工具结果的消息历史
            messages_with_result = [
                {"role": "user", "content": "读取README.md文件的前5行"},
                {
                    "role": "assistant",
                    "content": content_blocks
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": "# Warp2Api\n\n基于 Python 的桥接服务，为 Warp AI 服务提供 OpenAI Chat Completions API 兼容性\n\n## 🚀 特性"
                        }
                    ]
                },
                {"role": "user", "content": "很好！现在请基于这些信息创建CLAUDE.md文件"}
            ]
            
            response2 = requests.post(
                f"{BASE_URL}/v1/messages",
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "messages": messages_with_result,
                    "max_tokens": 500
                },
                headers=headers,
                timeout=30
            )
            
            if response2.status_code == 200:
                result2 = response2.json()
                content_blocks2 = result2.get('content', [])
                
                print("第二次响应内容:")
                for i, block in enumerate(content_blocks2):
                    print(f"  {i+1}. {block.get('type')}")
                    if block.get('type') == 'tool_use':
                        print(f"     工具: {block.get('name')}")
                        print(f"     参数: {block.get('input')}")
                    elif block.get('type') == 'text':
                        text = block.get('text', '')
                        print(f"     文本: {text[:150]}...")
                
                # 检查是否创建了文件
                import os
                if os.path.exists("/workspace/CLAUDE.md"):
                    print("\n✅ CLAUDE.md文件成功创建！")
                    with open("/workspace/CLAUDE.md", 'r') as f:
                        content = f.read()
                        print(f"   文件大小: {len(content)} 字符")
                    return True
                else:
                    print("\n❌ CLAUDE.md文件未创建")
                    return False
            else:
                print(f"❌ 第二次请求失败: {response2.status_code}")
                return False
        else:
            print("❌ 第一次响应没有工具调用")
            return False
    else:
        print(f"❌ 第一次请求失败: {response1.status_code}")
        return False

def test_single_request_file_creation():
    """测试单个请求的文件创建"""
    print("\n📝 单请求文件创建测试")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "code-execution-2025-08-25"
    }
    
    # 直接要求创建详细的CLAUDE.md文件
    response = requests.post(
        f"{BASE_URL}/v1/messages",
        json={
            "model": "claude-3-5-sonnet-20241022",
            "system": "You are Claude Code. Always complete the requested file creation tasks.",
            "messages": [
                {
                    "role": "user", 
                    "content": "创建一个详细的CLAUDE.md文件，包含以下内容：项目名称、描述、主要功能、技术栈、使用方法。请确保文件内容丰富完整。"
                }
            ],
            "max_tokens": 800
        },
        headers=headers,
        timeout=45
    )
    
    if response.status_code == 200:
        result = response.json()
        content_blocks = result.get('content', [])
        
        print("响应分析:")
        tool_calls = 0
        success_indicators = 0
        
        for block in content_blocks:
            if block.get('type') == 'tool_use':
                tool_calls += 1
                print(f"  工具调用: {block.get('name')} - {block.get('input', {}).get('command')}")
            elif block.get('type') == 'text':
                text = block.get('text', '')
                if '✅' in text:
                    success_indicators += 1
                    print(f"  成功指示: {text[:100]}...")
        
        print(f"\n统计: {tool_calls} 个工具调用, {success_indicators} 个成功指示")
        
        # 检查文件
        import os
        if os.path.exists("/workspace/CLAUDE.md"):
            with open("/workspace/CLAUDE.md", 'r') as f:
                content = f.read()
            print(f"✅ CLAUDE.md创建成功: {len(content)} 字符")
            return True
        else:
            print("❌ CLAUDE.md未创建")
            return False
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return False

def main():
    """主测试函数"""
    print("🔧 Claude Code工具结果流程调试")
    print("="*70)
    
    # 测试工具结果流程
    flow_test = test_tool_result_flow()
    
    # 测试单请求文件创建
    single_test = test_single_request_file_creation()
    
    print("\n" + "="*70)
    print("🎯 调试结论")
    print("="*70)
    
    if flow_test and single_test:
        print("🎉 所有测试通过！Claude Code应该能完整工作了")
    elif single_test:
        print("✅ 单请求文件创建正常")
        print("⚠️ 多步骤流程可能还有问题")
    elif flow_test:
        print("✅ 工具结果流程正常")
        print("⚠️ 单请求处理可能有问题")
    else:
        print("❌ 仍有问题需要进一步调试")

if __name__ == "__main__":
    main()