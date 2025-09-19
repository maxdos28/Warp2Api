#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude API 集成测试脚本
"""

import json
import requests
import time
from typing import Dict, Any


def test_claude_messages_basic():
    """测试基本的 Claude Messages API"""
    url = "http://localhost:28889/v1/messages"
    
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Hello! Please introduce yourself in one sentence."
            }
        ]
    }
    
    print("🧪 Testing Claude Messages API (Basic)...")
    print(f"📤 Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        headers = {"Authorization": "Bearer 0000"}
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_claude_messages_with_system():
    """测试带系统提示的 Claude Messages API"""
    url = "http://localhost:28889/v1/messages"
    
    payload = {
        "model": "claude-3-opus-20240229", 
        "max_tokens": 150,
        "system": "You are a helpful AI assistant. Always be concise and friendly.",
        "messages": [
            {
                "role": "user",
                "content": "What's the capital of France?"
            }
        ]
    }
    
    print("\n🧪 Testing Claude Messages API (With System Prompt)...")
    print(f"📤 Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        headers = {"Authorization": "Bearer 0000"}
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_claude_messages_streaming():
    """测试流式 Claude Messages API"""
    url = "http://localhost:28889/v1/messages"
    
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "stream": True,
        "messages": [
            {
                "role": "user", 
                "content": "Tell me a very short story about a robot learning to paint."
            }
        ]
    }
    
    print("\n🧪 Testing Claude Messages API (Streaming)...")
    print(f"📤 Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        headers = {"Authorization": "Bearer 0000"}
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=60)
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Streaming response:")
            content_parts = []
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    print(f"📡 {line_str}")
                    
                    # Extract content from Claude streaming format
                    if line_str.startswith("data: "):
                        try:
                            data = json.loads(line_str[6:])
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    content_parts.append(delta.get("text", ""))
                        except:
                            pass
            
            full_content = "".join(content_parts)
            print(f"📝 Full content: {full_content}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_claude_multi_turn():
    """测试多轮对话"""
    url = "http://localhost:28889/v1/messages"
    
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 120,
        "messages": [
            {
                "role": "user",
                "content": "What's 2+2?"
            },
            {
                "role": "assistant", 
                "content": "2+2 equals 4."
            },
            {
                "role": "user",
                "content": "What about 3+3?"
            }
        ]
    }
    
    print("\n🧪 Testing Claude Messages API (Multi-turn)...")
    print(f"📤 Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        headers = {"Authorization": "Bearer 0000"}
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def check_server_health():
    """检查服务器健康状态"""
    print("🏥 Checking server health...")
    
    try:
        # Check OpenAI server
        openai_resp = requests.get("http://localhost:28889/healthz", timeout=5)
        print(f"🔹 OpenAI server (28889): {openai_resp.status_code}")
        
        # Check Bridge server  
        bridge_resp = requests.get("http://localhost:28888/healthz", timeout=5)
        print(f"🔹 Bridge server (28888): {bridge_resp.status_code}")
        
        return openai_resp.status_code == 200 and bridge_resp.status_code == 200
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 Claude API 集成测试")
    print("=" * 60)
    
    # 健康检查
    if not check_server_health():
        print("❌ Servers are not healthy. Please start them first:")
        print("   ./start.sh  # Linux/macOS")
        print("   start.bat   # Windows")
        return
    
    print("✅ Servers are healthy!")
    
    # 运行测试
    tests = [
        ("Basic Messages", test_claude_messages_basic),
        ("With System Prompt", test_claude_messages_with_system), 
        ("Streaming", test_claude_messages_streaming),
        ("Multi-turn", test_claude_multi_turn),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        success = test_func()
        results.append((test_name, success))
        time.sleep(1)  # Brief pause between tests
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 总计: {passed}/{len(results)} 测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过! Claude API 集成成功!")
    else:
        print("⚠️  部分测试失败，请检查日志")


if __name__ == "__main__":
    main()