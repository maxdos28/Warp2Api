#!/usr/bin/env python3
"""
分析cline/kilo vs Claude的差异
为什么cline调用匿名账户工具没问题，Claude就不行
"""

import json
import requests
import sys
sys.path.append('/workspace')

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def test_openai_vs_claude_endpoints():
    """对比OpenAI和Claude端点的工具调用"""
    print("🔍 OpenAI vs Claude端点工具调用对比")
    print("="*70)
    
    # 相同的工具调用请求，但使用不同的端点
    
    # 测试1: OpenAI格式端点 (cline/kilo使用的)
    print("\n[测试1] OpenAI Chat Completions端点 (/v1/chat/completions)")
    print("这是cline/kilo等工具使用的端点")
    print("-"*50)
    
    openai_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    openai_request = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "请截取屏幕截图"}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "computer_20241022",
                    "description": "Use computer with screen, keyboard, and mouse",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["screenshot", "click", "type", "scroll", "key"]
                            }
                        },
                        "required": ["action"]
                    }
                }
            }
        ],
        "max_tokens": 200
    }
    
    try:
        response1 = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=openai_request,
            headers=openai_headers,
            timeout=30
        )
        
        print(f"状态码: {response1.status_code}")
        
        if response1.status_code == 200:
            result1 = response1.json()
            
            # 检查OpenAI格式的响应
            choices = result1.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                content = message.get('content', '')
                tool_calls = message.get('tool_calls', [])
                
                print(f"✅ OpenAI格式响应:")
                print(f"   内容: {content[:100]}...")
                print(f"   工具调用: {len(tool_calls)} 个")
                
                if tool_calls:
                    for tool in tool_calls:
                        print(f"   - {tool.get('function', {}).get('name')}: {tool.get('function', {}).get('arguments')}")
                
                openai_success = len(tool_calls) > 0
            else:
                print("❌ 无效的OpenAI响应格式")
                openai_success = False
        else:
            print(f"❌ OpenAI端点失败: {response1.text[:200]}")
            openai_success = False
            
    except Exception as e:
        print(f"❌ OpenAI端点异常: {e}")
        openai_success = False
    
    # 测试2: Claude格式端点
    print("\n[测试2] Claude Messages端点 (/v1/messages)")
    print("这是我们实现的Claude API端点")
    print("-"*50)
    
    claude_headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "computer-use-2024-10-22",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    claude_request = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "请截取屏幕截图"}
        ],
        "max_tokens": 200
    }
    
    try:
        response2 = requests.post(
            f"{BASE_URL}/v1/messages",
            json=claude_request,
            headers=claude_headers,
            timeout=30
        )
        
        print(f"状态码: {response2.status_code}")
        
        if response2.status_code == 200:
            result2 = response2.json()
            
            # 检查Claude格式的响应
            content_blocks = result2.get('content', [])
            tool_uses = [block for block in content_blocks if block.get('type') == 'tool_use']
            text_blocks = [block.get('text', '') for block in content_blocks if block.get('type') == 'text']
            
            print(f"✅ Claude格式响应:")
            print(f"   文本内容: {''.join(text_blocks)[:100]}...")
            print(f"   工具调用: {len(tool_uses)} 个")
            
            if tool_uses:
                for tool in tool_uses:
                    print(f"   - {tool.get('name')}: {tool.get('input')}")
            
            claude_success = len(tool_uses) > 0
        else:
            print(f"❌ Claude端点失败: {response2.text[:200]}")
            claude_success = False
            
    except Exception as e:
        print(f"❌ Claude端点异常: {e}")
        claude_success = False
    
    # 对比结果
    print("\n" + "="*70)
    print("📊 端点对比结果")
    print("="*70)
    
    print(f"OpenAI端点 (/v1/chat/completions): {'✅ 工具调用成功' if openai_success else '❌ 工具调用失败'}")
    print(f"Claude端点 (/v1/messages): {'✅ 工具调用成功' if claude_success else '❌ 工具调用失败'}")
    
    if openai_success and not claude_success:
        print("\n💡 发现差异！")
        print("✅ OpenAI端点工具调用正常（cline/kilo使用的）")
        print("❌ Claude端点工具调用有问题")
        print("\n可能的原因:")
        print("1. 两个端点使用不同的packet生成逻辑")
        print("2. Claude端点的配置有问题")
        print("3. anthropic-beta头的处理差异")
        print("4. 工具定义格式的差异")
    elif claude_success and not openai_success:
        print("\n💡 Claude端点更好？")
        print("❌ OpenAI端点有问题")
        print("✅ Claude端点工具调用正常")
    elif openai_success and claude_success:
        print("\n✅ 两个端点都正常工作")
        print("问题可能在其他地方")
    else:
        print("\n❌ 两个端点都有问题")
        print("可能是更深层的配置问题")
    
    return {"openai": openai_success, "claude": claude_success}

def analyze_packet_differences():
    """分析两个端点生成的packet差异"""
    print("\n" + "="*70)
    print("🔍 分析packet生成差异")
    print("="*70)
    
    try:
        from protobuf2openai.models import ChatMessage, ChatCompletionsRequest
        from protobuf2openai.claude_models import ClaudeMessagesRequest, ClaudeMessage
        from protobuf2openai.packets import packet_template, map_history_to_warp_messages, attach_user_and_tools_to_inputs
        from protobuf2openai.claude_router import convert_claude_to_openai_messages, add_claude_builtin_tools
        
        print("\n[分析1] OpenAI端点的packet生成")
        
        # 模拟OpenAI请求
        openai_messages = [ChatMessage(role="user", content="请截取屏幕截图")]
        
        packet1 = packet_template()
        packet1["task_context"] = {
            "tasks": [{
                "id": "test1",
                "description": "",
                "status": {"in_progress": {}},
                "messages": map_history_to_warp_messages(openai_messages, "test1", None, False),
            }],
            "active_task_id": "test1",
        }
        
        # OpenAI端点的配置
        packet1["settings"]["model_config"]["base"] = "claude-4-sonnet"
        
        attach_user_and_tools_to_inputs(packet1, openai_messages, None)
        
        print("OpenAI端点设置:")
        print(json.dumps(packet1["settings"], indent=2)[:300] + "...")
        
        print("\n[分析2] Claude端点的packet生成")
        
        # 模拟Claude请求
        claude_messages = [ClaudeMessage(role="user", content="请截取屏幕截图")]
        openai_converted = convert_claude_to_openai_messages(claude_messages, None)
        
        packet2 = packet_template()
        packet2["task_context"] = {
            "tasks": [{
                "id": "test2", 
                "description": "",
                "status": {"in_progress": {}},
                "messages": map_history_to_warp_messages(openai_converted, "test2", None, False),
            }],
            "active_task_id": "test2",
        }
        
        # Claude端点的配置（我们修改过的）
        packet2["settings"]["model_config"]["base"] = "claude-4-sonnet"
        packet2["settings"]["model_config"]["vision_enabled"] = True
        packet2["settings"]["web_context_retrieval_enabled"] = True
        packet2["settings"]["warp_drive_context_enabled"] = True
        packet2["settings"]["vision_enabled"] = True
        packet2["settings"]["multimodal_enabled"] = True
        
        attach_user_and_tools_to_inputs(packet2, openai_converted, None)
        
        print("Claude端点设置:")
        print(json.dumps(packet2["settings"], indent=2)[:300] + "...")
        
        # 对比差异
        print("\n[分析3] 关键差异")
        
        openai_settings = set(packet1["settings"].keys())
        claude_settings = set(packet2["settings"].keys())
        
        print(f"OpenAI端点设置字段: {openai_settings}")
        print(f"Claude端点设置字段: {claude_settings}")
        print(f"差异字段: {claude_settings - openai_settings}")
        
        return True
        
    except Exception as e:
        print(f"❌ packet分析失败: {e}")
        return False

def main():
    """主分析函数"""
    print("🕵️ cline/kilo vs Claude差异分析")
    print("="*70)
    print("目标：找出为什么cline调用匿名账户没问题，Claude有问题")
    
    # 对比端点
    endpoint_results = test_openai_vs_claude_endpoints()
    
    # 分析packet差异
    packet_analysis = analyze_packet_differences()
    
    print("\n" + "="*70)
    print("🎯 最终分析结论")
    print("="*70)
    
    if endpoint_results["openai"] and not endpoint_results["claude"]:
        print("💡 发现根本原因！")
        print("✅ OpenAI端点 (/v1/chat/completions) 工具调用正常")
        print("❌ Claude端点 (/v1/messages) 工具调用有问题")
        print("\n这解释了为什么:")
        print("✅ cline/kilo使用OpenAI端点 → 工具调用正常")
        print("❌ Claude API使用Claude端点 → 工具调用有问题")
        print("\n可能的原因:")
        print("1. 我们对Claude端点的修改影响了工具调用")
        print("2. Claude端点的packet配置与OpenAI不同")
        print("3. anthropic-beta头的处理可能有问题")
        print("4. 工具定义的转换可能有差异")
    elif endpoint_results["claude"] and not endpoint_results["openai"]:
        print("🤔 意外结果：Claude端点更好")
    elif endpoint_results["openai"] and endpoint_results["claude"]:
        print("✅ 两个端点都正常，问题可能在其他地方")
    else:
        print("❌ 两个端点都有问题")

if __name__ == "__main__":
    main()