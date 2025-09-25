#!/usr/bin/env python3
"""
深度测试工具执行效果
检查工具调用后是否真的有执行结果
"""

import json
import requests
import time

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def test_openai_tool_execution_depth():
    """深度测试OpenAI端点的工具执行"""
    print("🔍 OpenAI端点工具执行深度测试")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 第一步：调用工具
    print("\n[步骤1] 调用截图工具")
    
    response1 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "claude-4-sonnet",
            "messages": [
                {"role": "user", "content": "请截取屏幕截图，然后告诉我截图是否成功"}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "computer_20241022",
                        "description": "Use computer",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["screenshot", "click", "type"]}
                            },
                            "required": ["action"]
                        }
                    }
                }
            ],
            "max_tokens": 200
        },
        headers=headers,
        timeout=30
    )
    
    if response1.status_code == 200:
        result1 = response1.json()
        message1 = result1.get('choices', [{}])[0].get('message', {})
        tool_calls = message1.get('tool_calls', [])
        
        print(f"✅ 工具调用: {len(tool_calls)} 个")
        
        if tool_calls:
            tool_call = tool_calls[0]
            tool_id = tool_call.get('id')
            
            print(f"   工具ID: {tool_id}")
            print(f"   工具名: {tool_call.get('function', {}).get('name')}")
            
            # 第二步：发送工具执行结果
            print("\n[步骤2] 发送工具执行结果")
            
            messages_with_result = [
                {"role": "user", "content": "请截取屏幕截图，然后告诉我截图是否成功"},
                {
                    "role": "assistant",
                    "content": message1.get('content', ''),
                    "tool_calls": tool_calls
                },
                {
                    "role": "user", 
                    "content": "截图已成功保存为screenshot_20241225_123456.png，分辨率1920x1080",
                    "tool_call_id": tool_id
                }
            ]
            
            response2 = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json={
                    "model": "claude-4-sonnet",
                    "messages": messages_with_result,
                    "max_tokens": 200
                },
                headers=headers,
                timeout=30
            )
            
            if response2.status_code == 200:
                result2 = response2.json()
                follow_up = result2.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                print(f"📄 AI后续回复: {follow_up}")
                
                # 检查AI是否理解了执行结果
                understands_result = any(phrase in follow_up.lower() for phrase in [
                    "screenshot", "successful", "1920x1080", "saved", "成功", "截图", "保存"
                ])
                
                print(f"✅ AI理解工具执行结果: {understands_result}")
                return understands_result
            else:
                print(f"❌ 后续请求失败: {response2.status_code}")
                return False
        else:
            print("❌ 没有工具调用")
            return False
    else:
        print(f"❌ 初始请求失败: {response1.status_code}")
        return False

def test_claude_tool_execution_depth():
    """深度测试Claude端点的工具执行"""
    print("\n🔍 Claude端点工具执行深度测试")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "computer-use-2024-10-22",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 第一步：调用工具
    print("\n[步骤1] 调用截图工具")
    
    response1 = requests.post(
        f"{BASE_URL}/v1/messages",
        json={
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {"role": "user", "content": "请截取屏幕截图，然后告诉我截图是否成功"}
            ],
            "max_tokens": 200
        },
        headers=headers,
        timeout=30
    )
    
    if response1.status_code == 200:
        result1 = response1.json()
        content_blocks = result1.get('content', [])
        tool_uses = [block for block in content_blocks if block.get('type') == 'tool_use']
        
        print(f"✅ 工具调用: {len(tool_uses)} 个")
        
        if tool_uses:
            tool_use = tool_uses[0]
            tool_id = tool_use.get('id')
            
            print(f"   工具ID: {tool_id}")
            print(f"   工具名: {tool_use.get('name')}")
            
            # 第二步：发送工具执行结果
            print("\n[步骤2] 发送工具执行结果")
            
            messages_with_result = [
                {"role": "user", "content": "请截取屏幕截图，然后告诉我截图是否成功"},
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
                            "content": "截图已成功保存为screenshot_20241225_123456.png，分辨率1920x1080"
                        }
                    ]
                }
            ]
            
            response2 = requests.post(
                f"{BASE_URL}/v1/messages",
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "messages": messages_with_result,
                    "max_tokens": 200
                },
                headers=headers,
                timeout=30
            )
            
            if response2.status_code == 200:
                result2 = response2.json()
                follow_up = ''.join([block.get('text', '') for block in result2.get('content', []) if block.get('type')=='text'])
                
                print(f"📄 AI后续回复: {follow_up}")
                
                # 检查AI是否理解了执行结果
                understands_result = any(phrase in follow_up.lower() for phrase in [
                    "screenshot", "successful", "1920x1080", "saved", "成功", "截图", "保存"
                ])
                
                print(f"✅ AI理解工具执行结果: {understands_result}")
                return understands_result
            else:
                print(f"❌ 后续请求失败: {response2.status_code}")
                return False
        else:
            print("❌ 没有工具调用")
            return False
    else:
        print(f"❌ 初始请求失败: {response1.status_code}")
        return False

def test_streaming_vs_non_streaming():
    """测试流式vs非流式的差异"""
    print("\n🌊 流式vs非流式对比测试")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 测试非流式
    print("\n[测试] 非流式工具调用")
    response1 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "claude-4-sonnet",
            "messages": [{"role": "user", "content": "请截取屏幕截图"}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "computer_20241022",
                        "description": "Computer tool",
                        "parameters": {
                            "type": "object",
                            "properties": {"action": {"type": "string"}},
                            "required": ["action"]
                        }
                    }
                }
            ],
            "stream": False,
            "max_tokens": 100
        },
        headers=headers
    )
    
    non_streaming_success = False
    if response1.status_code == 200:
        result1 = response1.json()
        tool_calls = result1.get('choices', [{}])[0].get('message', {}).get('tool_calls', [])
        non_streaming_success = len(tool_calls) > 0
        print(f"✅ 非流式: {len(tool_calls)} 个工具调用")
    else:
        print(f"❌ 非流式失败: {response1.status_code}")
    
    # 测试流式
    print("\n[测试] 流式工具调用")
    try:
        response2 = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "claude-4-sonnet",
                "messages": [{"role": "user", "content": "请截取屏幕截图"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "computer_20241022",
                            "description": "Computer tool",
                            "parameters": {
                                "type": "object",
                                "properties": {"action": {"type": "string"}},
                                "required": ["action"]
                            }
                        }
                    }
                ],
                "stream": True,
                "max_tokens": 100
            },
            headers=headers,
            stream=True,
            timeout=30
        )
        
        tool_call_found = False
        if response2.status_code == 200:
            for line in response2.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if 'tool_calls' in line_text or 'function_call' in line_text:
                        tool_call_found = True
                        break
        
        print(f"✅ 流式: {'发现工具调用' if tool_call_found else '未发现工具调用'}")
        
    except Exception as e:
        print(f"❌ 流式测试异常: {e}")
        tool_call_found = False
    
    return {"non_streaming": non_streaming_success, "streaming": tool_call_found}

def main():
    """主测试函数"""
    print("🕵️ 深度分析cline/kilo vs Claude的工具执行差异")
    print("="*70)
    
    # 深度测试工具执行
    openai_execution = test_openai_tool_execution_depth()
    claude_execution = test_claude_tool_execution_depth()
    
    # 测试流式差异
    streaming_results = test_streaming_vs_non_streaming()
    
    print("\n" + "="*70)
    print("🎯 深度分析结论")
    print("="*70)
    
    print(f"OpenAI端点工具执行效果: {'✅ 有效' if openai_execution else '❌ 无效'}")
    print(f"Claude端点工具执行效果: {'✅ 有效' if claude_execution else '❌ 无效'}")
    print(f"非流式工具调用: {'✅ 正常' if streaming_results['non_streaming'] else '❌ 异常'}")
    print(f"流式工具调用: {'✅ 正常' if streaming_results['streaming'] else '❌ 异常'}")
    
    # 分析可能的差异原因
    print(f"\n💡 可能的差异原因:")
    
    if openai_execution and not claude_execution:
        print("1. Claude端点的工具结果处理有问题")
        print("2. Claude消息格式转换影响了工具执行")
        print("3. anthropic-beta头可能影响了执行逻辑")
    elif not openai_execution and claude_execution:
        print("1. OpenAI端点的工具结果处理有问题")
        print("2. OpenAI格式转换有缺陷")
    elif not openai_execution and not claude_execution:
        print("1. 匿名账户确实限制了工具的实际执行")
        print("2. 工具能调用但不能真正执行")
        print("3. 这解释了用户的观察：注册账户正常，匿名账户有问题")
    else:
        print("1. 两个端点都正常，问题可能在其他层面")
        print("2. 可能是工具执行的时机或方式问题")
    
    # 给出最终判断
    if not openai_execution and not claude_execution:
        print(f"\n🎯 验证了用户观察：")
        print("✅ 匿名账户的工具调用确实有问题")
        print("✅ 能调用工具，但不能实际执行")
        print("✅ 这解释了为什么cline/kilo看起来正常但实际效果不好")

if __name__ == "__main__":
    main()