#!/usr/bin/env python3
"""
测试Claude Code完整工作流程
分步骤验证每个环节
"""

import requests
import json
import time
import os

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def test_step_by_step_workflow():
    """分步骤测试Claude Code工作流程"""
    print("🔄 Claude Code分步骤工作流程测试")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "code-execution-2025-08-25"
    }
    
    steps = [
        {
            "name": "步骤1: 查看项目结构",
            "prompt": "查看当前目录的文件列表",
            "expected_tool": "str_replace_based_edit_tool",
            "expected_command": "view"
        },
        {
            "name": "步骤2: 读取README文件",
            "prompt": "读取README.md文件的内容",
            "expected_tool": "str_replace_based_edit_tool", 
            "expected_command": "view"
        },
        {
            "name": "步骤3: 创建CLAUDE.md文件",
            "prompt": "创建一个CLAUDE.md文件，内容包含项目名称和简要描述",
            "expected_tool": "str_replace_based_edit_tool",
            "expected_command": "create"
        }
    ]
    
    results = []
    
    for step in steps:
        print(f"\n[测试] {step['name']}")
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{BASE_URL}/v1/messages",
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "messages": [{"role": "user", "content": step["prompt"]}],
                    "max_tokens": 500
                },
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content_blocks = result.get('content', [])
                
                # 分析响应
                tool_calls = [block for block in content_blocks if block.get('type') == 'tool_use']
                text_blocks = [block.get('text', '') for block in content_blocks if block.get('type') == 'text']
                
                print(f"✅ HTTP响应正常")
                print(f"   工具调用: {len(tool_calls)} 个")
                print(f"   文本块: {len(text_blocks)} 个")
                
                # 检查工具调用
                if tool_calls:
                    tool = tool_calls[0]
                    tool_name = tool.get('name')
                    tool_input = tool.get('input', {})
                    command = tool_input.get('command')
                    
                    print(f"   调用工具: {tool_name}")
                    print(f"   执行命令: {command}")
                    
                    # 检查是否符合预期
                    correct_tool = tool_name == step["expected_tool"]
                    correct_command = command == step["expected_command"]
                    
                    print(f"   工具正确: {'✅' if correct_tool else '❌'}")
                    print(f"   命令正确: {'✅' if correct_command else '❌'}")
                
                # 检查本地执行结果
                all_text = ' '.join(text_blocks)
                has_success = '✅' in all_text
                has_error = '❌' in all_text
                
                print(f"   本地执行成功: {'✅' if has_success else '❌'}")
                print(f"   本地执行错误: {'✅' if has_error else '❌'}")
                
                # 对于文件创建步骤，检查文件是否真的存在
                if step["expected_command"] == "create":
                    if tool_calls:
                        file_path = tool_calls[0].get('input', {}).get('path')
                        if file_path and os.path.exists(f"/workspace/{file_path}"):
                            print(f"   ✅ 文件确实创建: {file_path}")
                            results.append(True)
                        else:
                            print(f"   ❌ 文件未创建: {file_path}")
                            results.append(False)
                    else:
                        print("   ❌ 没有工具调用")
                        results.append(False)
                else:
                    results.append(has_success and not has_error)
                
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"   错误: {response.text[:200]}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            results.append(False)
    
    return results

def test_streaming_vs_non_streaming():
    """测试流式vs非流式的工具执行"""
    print("\n🌊 流式vs非流式工具执行对比")
    print("="*60)
    
    headers_base = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "code-execution-2025-08-25"
    }
    
    test_request = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "创建一个test_streaming.txt文件，内容是流式测试"}],
        "max_tokens": 200
    }
    
    # 测试非流式
    print("\n[测试] 非流式响应")
    try:
        response1 = requests.post(
            f"{BASE_URL}/v1/messages",
            json={**test_request, "stream": False},
            headers=headers_base,
            timeout=30
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            has_local_result = any('✅' in block.get('text', '') for block in result1.get('content', []) if block.get('type') == 'text')
            print(f"   本地执行结果: {'✅ 有' if has_local_result else '❌ 无'}")
            
            # 检查文件
            if os.path.exists("/workspace/test_streaming.txt"):
                print("   ✅ 文件创建成功")
                non_streaming_success = True
            else:
                print("   ❌ 文件未创建")
                non_streaming_success = False
        else:
            print(f"   ❌ 请求失败: {response1.status_code}")
            non_streaming_success = False
    except Exception as e:
        print(f"   ❌ 非流式测试异常: {e}")
        non_streaming_success = False
    
    # 测试流式
    print("\n[测试] 流式响应")
    try:
        response2 = requests.post(
            f"{BASE_URL}/v1/messages",
            json={**test_request, "stream": True, "messages": [{"role": "user", "content": "创建一个test_streaming2.txt文件，内容是流式测试2"}]},
            headers=headers_base,
            stream=True,
            timeout=30
        )
        
        if response2.status_code == 200:
            local_result_found = False
            for line in response2.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if 'data:' in line_text and ('✅' in line_text or '❌' in line_text):
                        local_result_found = True
                        print(f"   ✅ 发现本地执行结果")
                        break
            
            if not local_result_found:
                print("   ❌ 未发现本地执行结果")
            
            # 检查文件
            time.sleep(2)  # 等待文件创建
            if os.path.exists("/workspace/test_streaming2.txt"):
                print("   ✅ 文件创建成功")
                streaming_success = True
            else:
                print("   ❌ 文件未创建")
                streaming_success = False
        else:
            print(f"   ❌ 流式请求失败: {response2.status_code}")
            streaming_success = False
    except Exception as e:
        print(f"   ❌ 流式测试异常: {e}")
        streaming_success = False
    
    return {"non_streaming": non_streaming_success, "streaming": streaming_success}

def main():
    """主测试函数"""
    print("🧪 Claude Code完整工作流程诊断")
    print("="*60)
    print("目标: 找出为什么Claude Code会停止执行")
    
    # 等待服务器
    time.sleep(3)
    
    # 分步骤测试
    step_results = test_step_by_step_workflow()
    
    # 测试流式vs非流式
    streaming_results = test_streaming_vs_non_streaming()
    
    # 最终检查CLAUDE.md文件
    claude_md_exists = os.path.exists("/workspace/CLAUDE.md")
    if claude_md_exists:
        with open("/workspace/CLAUDE.md", 'r') as f:
            content = f.read()
            print(f"\n📄 CLAUDE.md文件存在: ✅")
            print(f"   大小: {len(content)} 字符")
            print(f"   内容预览: {content[:200]}...")
    else:
        print(f"\n📄 CLAUDE.md文件: ❌ 不存在")
    
    # 总结
    print("\n" + "="*60)
    print("🎯 诊断结果")
    print("="*60)
    
    step_success_rate = sum(step_results) / len(step_results) if step_results else 0
    
    print(f"分步骤测试: {sum(step_results)}/{len(step_results)} 成功 ({step_success_rate:.1%})")
    print(f"非流式工具执行: {'✅ 正常' if streaming_results['non_streaming'] else '❌ 异常'}")
    print(f"流式工具执行: {'✅ 正常' if streaming_results['streaming'] else '❌ 异常'}")
    print(f"CLAUDE.md文件: {'✅ 存在' if claude_md_exists else '❌ 不存在'}")
    
    if step_success_rate < 0.7:
        print("\n❌ 主要问题: 工具执行失败率高")
        print("可能原因:")
        print("1. 本地工具执行没有完全替代Warp工具")
        print("2. 工具执行错误导致Claude Code停止")
        print("3. 流式响应中的本地工具执行有问题")
    elif not claude_md_exists:
        print("\n⚠️ 工具执行正常，但最终任务未完成")
        print("可能原因:")
        print("1. Claude Code在某个步骤后停止了")
        print("2. 需要更好的错误恢复机制")
        print("3. 可能需要调整max_tokens限制")
    else:
        print("\n✅ 所有功能正常工作")

if __name__ == "__main__":
    main()