#!/usr/bin/env python3
"""
尝试完全不同的方法
也许问题不在于我们的实现，而在于方法
"""

import requests
import json
import time

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def try_disable_local_tools():
    """尝试禁用本地工具执行，看是否是我们的修改导致的问题"""
    print("🔧 尝试不同的方法")
    print("="*60)
    print("假设：也许我们的本地工具执行修改反而干扰了正常流程")
    
    # 让我们回到最基础的实现，看看是否能让Claude Code继续
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01"
    }
    
    # 不使用任何beta功能，看看基础对话是否正常
    print("\n[测试] 基础对话（无工具）")
    
    response = requests.post(
        f"{BASE_URL}/v1/messages",
        json={
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {"role": "user", "content": "请帮我分析这个项目并创建CLAUDE.md文档。请用纯文本方式分析，不要使用工具。"}
            ],
            "max_tokens": 1000
        },
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        content = ''.join([block.get('text', '') for block in result.get('content', []) if block.get('type') == 'text'])
        
        print(f"✅ 基础对话成功")
        print(f"响应长度: {len(content)} 字符")
        print(f"响应预览: {content[:300]}...")
        
        # 检查AI是否提供了有用的分析
        has_analysis = any(word in content.lower() for word in ['project', 'analysis', 'structure', '项目', '分析'])
        print(f"包含项目分析: {'✅' if has_analysis else '❌'}")
        
        return has_analysis
    else:
        print(f"❌ 基础对话失败: {response.status_code}")
        return False

def try_minimal_tool_usage():
    """尝试最小化的工具使用"""
    print("\n🔨 最小化工具使用测试")
    print("="*50)
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "code-execution-2025-08-25"
    }
    
    # 只要求一个简单的操作
    print("\n[测试] 单一文件创建任务")
    
    response = requests.post(
        f"{BASE_URL}/v1/messages",
        json={
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {"role": "user", "content": "只做一件事：创建一个简单的CLAUDE.md文件，内容是'# 项目文档\\n\\n这是一个测试项目。'"}
            ],
            "max_tokens": 200
        },
        headers=headers,
        timeout=15
    )
    
    if response.status_code == 200:
        result = response.json()
        
        # 检查是否有工具调用
        has_tool_use = any(block.get('type') == 'tool_use' for block in result.get('content', []))
        has_tool_result = any(block.get('type') == 'tool_result' for block in result.get('content', []))
        
        print(f"工具调用: {'✅' if has_tool_use else '❌'}")
        print(f"工具结果: {'✅' if has_tool_result else '❌'}")
        
        # 检查文件是否创建
        import os
        time.sleep(2)
        if os.path.exists("/workspace/CLAUDE.md"):
            print("✅ 文件创建成功")
            return True
        else:
            print("❌ 文件未创建")
            return False
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return False

def try_cline_approach():
    """尝试模拟cline的方法"""
    print("\n🤖 模拟cline方法")
    print("="*50)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 使用OpenAI端点，要求生成代码而不是执行工具
    print("\n[测试] 代码生成方式（cline风格）")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "claude-4-sonnet",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful coding assistant. Generate code to accomplish tasks instead of using tools."
                },
                {
                    "role": "user",
                    "content": "我需要创建一个CLAUDE.md文件来描述这个项目。请生成Python代码来创建这个文件。"
                }
            ],
            "max_tokens": 500
        },
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        print(f"✅ 代码生成成功")
        print(f"响应长度: {len(content)} 字符")
        
        # 检查是否生成了有用的代码
        has_code = any(keyword in content for keyword in ['with open', 'write', '.md', 'file'])
        print(f"包含文件操作代码: {'✅' if has_code else '❌'}")
        
        if has_code:
            print(f"生成的代码预览: {content[:300]}...")
        
        return has_code
    else:
        print(f"❌ 代码生成失败: {response.status_code}")
        return False

def main():
    """尝试不同方法的主函数"""
    print("🔄 尝试完全不同的方法")
    print("="*70)
    print("也许问题不在技术实现，而在方法选择")
    
    # 方法1: 纯文本分析
    text_analysis = try_disable_local_tools()
    
    # 方法2: 最小化工具使用
    minimal_tools = try_minimal_tool_usage()
    
    # 方法3: 代码生成方式
    code_generation = try_cline_approach()
    
    print("\n" + "="*70)
    print("🎯 不同方法的效果对比")
    print("="*70)
    
    print(f"纯文本分析: {'✅ 有效' if text_analysis else '❌ 无效'}")
    print(f"最小化工具: {'✅ 有效' if minimal_tools else '❌ 无效'}")
    print(f"代码生成: {'✅ 有效' if code_generation else '❌ 无效'}")
    
    if code_generation:
        print("\n💡 关键发现：代码生成方式可能是解决方案！")
        print("这就是为什么cline能正常工作的原因")
        print("建议：引导Claude Code使用代码生成而不是直接工具执行")
    elif text_analysis:
        print("\n💡 发现：纯文本方式可能更可靠")
        print("建议：让Claude Code先分析，再手动创建文件")
    elif minimal_tools:
        print("\n💡 发现：简单工具调用是可行的")
        print("建议：分解任务，一次只做一件事")
    else:
        print("\n😤 所有方法都有问题")
        print("可能真的是匿名账户的根本限制")

if __name__ == "__main__":
    main()