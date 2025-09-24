#!/usr/bin/env python3
"""
全面测试 OpenAI 和 Claude API
"""

import json
import time
import subprocess
import sys

def run_curl(command):
    """运行 curl 命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

def test_openai_basic():
    """测试 OpenAI API 基本对话"""
    print("\n[1] OpenAI API - 基本对话")
    print("-" * 40)
    
    cmd = '''curl -s -X POST http://localhost:28889/v1/chat/completions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer 0000" \
      -d '{
        "model": "claude-4-sonnet",
        "messages": [{"role": "user", "content": "Say hello"}],
        "stream": false
      }' '''
    
    response = run_curl(cmd)
    try:
        data = json.loads(response)
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"✅ 成功! 响应: {content[:100]}")
        return True
    except:
        print(f"❌ 失败: {response[:200]}")
        return False

def test_openai_tools():
    """测试 OpenAI API 工具调用"""
    print("\n[2] OpenAI API - 工具调用")
    print("-" * 40)
    
    cmd = '''curl -s -X POST http://localhost:28889/v1/chat/completions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer 0000" \
      -d '{
        "model": "claude-4-sonnet",
        "messages": [{"role": "user", "content": "What is the weather in Beijing?"}],
        "tools": [{
          "type": "function",
          "function": {
            "name": "get_weather",
            "description": "Get weather for a city",
            "parameters": {
              "type": "object",
              "properties": {
                "city": {"type": "string"}
              },
              "required": ["city"]
            }
          }
        }],
        "stream": false
      }' '''
    
    response = run_curl(cmd)
    try:
        data = json.loads(response)
        tool_calls = data.get('choices', [{}])[0].get('message', {}).get('tool_calls', [])
        if tool_calls:
            print(f"✅ 成功! 工具调用: {tool_calls[0].get('function', {}).get('name')}")
            return True
        else:
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"⚠️ 未调用工具，返回文本: {content[:100]}")
            return False
    except:
        print(f"❌ 失败: {response[:200]}")
        return False

def test_openai_streaming():
    """测试 OpenAI API 流式响应"""
    print("\n[3] OpenAI API - 流式响应")
    print("-" * 40)
    
    cmd = '''curl -s -N -X POST http://localhost:28889/v1/chat/completions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer 0000" \
      -d '{
        "model": "claude-4-sonnet",
        "messages": [{"role": "user", "content": "Count to 3"}],
        "stream": true
      }' 2>&1 | head -5'''
    
    response = run_curl(cmd)
    if "data:" in response:
        print(f"✅ 成功! 收到流式数据")
        return True
    else:
        print(f"❌ 失败: {response[:200]}")
        return False

def test_claude_basic():
    """测试 Claude API 基本对话"""
    print("\n[4] Claude API - 基本对话")
    print("-" * 40)
    
    cmd = '''curl -s -X POST http://localhost:28889/v1/messages \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer 0000" \
      -H "anthropic-version: 2023-06-01" \
      -d '{
        "model": "claude-4-sonnet",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 50,
        "stream": false
      }' '''
    
    response = run_curl(cmd)
    try:
        data = json.loads(response)
        content = data.get('content', [])
        if content and isinstance(content[0], dict):
            text = content[0].get('text', '')
            if text and text != "No response received from Warp":
                print(f"✅ 成功! 响应: {text[:100]}")
                return True
            else:
                print(f"⚠️ 响应为空或默认消息: {text}")
                return False
        else:
            print(f"⚠️ 无内容: {data}")
            return False
    except Exception as e:
        print(f"❌ 失败: {e} - {response[:200]}")
        return False

def test_claude_tools():
    """测试 Claude API 工具调用"""
    print("\n[5] Claude API - 工具调用")
    print("-" * 40)
    
    cmd = '''curl -s -X POST http://localhost:28889/v1/messages \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer 0000" \
      -H "anthropic-version: 2023-06-01" \
      -H "anthropic-beta: computer-use-2024-10-22" \
      -d '{
        "model": "claude-4-sonnet",
        "messages": [{"role": "user", "content": "Take a screenshot"}],
        "max_tokens": 200,
        "stream": false
      }' '''
    
    response = run_curl(cmd)
    try:
        data = json.loads(response)
        content = data.get('content', [])
        has_tool = False
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'tool_use':
                has_tool = True
                print(f"✅ 成功! 工具调用: {block.get('name')}")
                break
        
        if not has_tool:
            text = content[0].get('text', '') if content else ''
            print(f"⚠️ 未调用工具，返回文本: {text[:100]}")
            return False
        return True
    except Exception as e:
        print(f"❌ 失败: {e} - {response[:200]}")
        return False

def test_claude_streaming():
    """测试 Claude API 流式响应"""
    print("\n[6] Claude API - 流式响应")
    print("-" * 40)
    
    cmd = '''curl -s -N -X POST http://localhost:28889/v1/messages \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer 0000" \
      -H "anthropic-version: 2023-06-01" \
      -d '{
        "model": "claude-4-sonnet",
        "messages": [{"role": "user", "content": "Count to 3"}],
        "max_tokens": 50,
        "stream": true
      }' 2>&1 | head -10'''
    
    response = run_curl(cmd)
    if "event:" in response and "data:" in response:
        if "message_start" in response:
            print(f"✅ 成功! 收到 Claude 格式的流式数据")
            return True
        else:
            print(f"⚠️ 收到流式数据但格式不完整")
            return False
    else:
        print(f"❌ 失败: {response[:200]}")
        return False

def test_model_compatibility():
    """测试不同模型名称的兼容性"""
    print("\n[7] 模型兼容性测试")
    print("-" * 40)
    
    models = [
        ("claude-4-sonnet", "Warp 原生模型"),
        ("claude-3-5-sonnet-20241022", "Claude API 模型"),
        ("gpt-4o", "GPT 模型"),
    ]
    
    results = []
    for model, desc in models:
        cmd = f'''curl -s -X POST http://localhost:28889/v1/chat/completions \
          -H "Content-Type: application/json" \
          -H "Authorization: Bearer 0000" \
          -d '{{"model": "{model}", "messages": [{{"role": "user", "content": "Hi"}}], "stream": false}}' '''
        
        response = run_curl(cmd)
        try:
            data = json.loads(response)
            if 'choices' in data:
                print(f"  ✅ {model} ({desc}): 成功")
                results.append(True)
            else:
                print(f"  ❌ {model} ({desc}): 失败")
                results.append(False)
        except:
            print(f"  ❌ {model} ({desc}): 解析失败")
            results.append(False)
    
    return all(results)

def main():
    print("\n" + "="*60)
    print(" 全面 API 测试")
    print("="*60)
    
    # 检查服务器
    cmd = "curl -s http://localhost:28889/healthz"
    response = run_curl(cmd)
    if "ok" not in response:
        print("❌ 服务器未运行！请先启动服务器。")
        return
    
    print("✅ 服务器正在运行")
    
    # 运行测试
    results = {
        "OpenAI 基本对话": test_openai_basic(),
        "OpenAI 工具调用": test_openai_tools(),
        "OpenAI 流式响应": test_openai_streaming(),
        "Claude 基本对话": test_claude_basic(),
        "Claude 工具调用": test_claude_tools(),
        "Claude 流式响应": test_claude_streaming(),
        "模型兼容性": test_model_compatibility(),
    }
    
    # 总结
    print("\n" + "="*60)
    print(" 测试结果总结")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    elif passed >= total * 0.7:
        print("\n⚠️ 大部分测试通过，但仍有问题需要修复。")
    else:
        print("\n❌ 多数测试失败，需要进一步调试。")

if __name__ == "__main__":
    main()