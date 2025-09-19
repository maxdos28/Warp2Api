#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API响应验证修复的脚本

这个脚本测试修复后的API是否能正确处理空响应和错误情况。
"""

import json
import time
import requests
from typing import Dict, Any

# 服务器配置
OPENAI_API_BASE = "http://localhost:28889"
CLAUDE_API_BASE = "http://localhost:28889"

def test_server_health():
    """测试服务器健康状态"""
    print("🏥 检查服务器健康状态...")
    
    try:
        # 测试OpenAI兼容API服务器
        response = requests.get(f"{OPENAI_API_BASE}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ OpenAI兼容API服务器正常")
            return True
        else:
            print(f"❌ OpenAI兼容API服务器异常: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

def test_openai_api():
    """测试OpenAI Chat Completions API"""
    print("\n🧪 测试OpenAI Chat Completions API...")
    
    # 测试数据
    test_payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "Hello, please respond with just 'Hi'"}
        ],
        "stream": False
    }
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 123456"  # 使用正确的API token
        }
        response = requests.post(
            f"{OPENAI_API_BASE}/v1/chat/completions",
            json=test_payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 验证响应格式
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    if content and content.strip():
                        print("✅ OpenAI API响应包含有效内容")
                        return True
                    else:
                        print("❌ OpenAI API响应内容为空")
                        return False
                else:
                    print("❌ OpenAI API响应格式异常")
                    return False
            else:
                print("❌ OpenAI API响应缺少choices")
                return False
        else:
            print(f"❌ OpenAI API请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API测试异常: {e}")
        return False

def test_claude_api():
    """测试Claude Messages API"""
    print("\n🧪 测试Claude Messages API...")
    
    # 测试数据
    test_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Hello, please respond with just 'Hi'"}
        ]
    }
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 123456"  # 使用正确的API token
        }
        response = requests.post(
            f"{CLAUDE_API_BASE}/v1/messages",
            json=test_payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 验证Claude响应格式
            if "content" in data and len(data["content"]) > 0:
                content_block = data["content"][0]
                if "text" in content_block:
                    text = content_block["text"]
                    if text and text.strip():
                        print("✅ Claude API响应包含有效内容")
                        return True
                    else:
                        print("❌ Claude API响应内容为空")
                        return False
                else:
                    print("❌ Claude API响应格式异常")
                    return False
            else:
                print("❌ Claude API响应缺少content")
                return False
        else:
            print(f"❌ Claude API请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Claude API测试异常: {e}")
        return False

def test_streaming_api():
    """测试流式API响应"""
    print("\n🧪 测试流式API响应...")
    
    test_payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "Say hello and count to 3"}
        ],
        "stream": True
    }
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 123456"  # 使用正确的API token
        }
        response = requests.post(
            f"{OPENAI_API_BASE}/v1/chat/completions",
            json=test_payload,
            headers=headers,
            stream=True,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("流式响应内容:")
            content_received = False
            total_content = ""
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    print(f"  {line}")
                    
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str != "[DONE]":
                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        content_received = True
                                        total_content += content
                            except json.JSONDecodeError:
                                pass
            
            if content_received and total_content.strip():
                print("✅ 流式API响应包含有效内容")
                return True
            else:
                print("❌ 流式API响应没有有效内容")
                return False
        else:
            print(f"❌ 流式API请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 流式API测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 API响应验证修复测试")
    print("=" * 60)
    
    # 检查服务器健康状态
    if not test_server_health():
        print("\n❌ 服务器未运行，请先启动服务器:")
        print("   python server.py --port 28888")
        print("   python openai_compat.py --port 28889")
        return
    
    results = []
    
    # 执行各项测试
    results.append(("OpenAI API", test_openai_api()))
    results.append(("Claude API", test_claude_api()))
    results.append(("流式API", test_streaming_api()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15s} {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！API响应验证修复成功。")
    else:
        print("⚠️  部分测试失败，可能需要进一步检查。")

if __name__ == "__main__":
    main()
