#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试Claude Messages API的脚本

重点测试"The language model did not provide any assistant messages"错误
"""

import json
import requests
from typing import Dict, Any

# 服务器配置
CLAUDE_API_BASE = "http://localhost:28889"

def test_claude_api_detailed():
    """详细测试Claude Messages API"""
    print("🧪 详细测试Claude Messages API...")
    
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
            "Authorization": "Bearer 123456"
        }
        response = requests.post(
            f"{CLAUDE_API_BASE}/v1/messages",
            json=test_payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response JSON: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 详细验证Claude响应格式
            print("\n📋 详细验证:")
            
            # 检查基本字段
            required_fields = ["id", "type", "role", "content", "model"]
            for field in required_fields:
                if field in data:
                    print(f"✅ {field}: {data[field] if field != 'content' else f'[{len(data[field])} items]'}")
                else:
                    print(f"❌ Missing field: {field}")
            
            # 检查content数组
            if "content" in data and isinstance(data["content"], list):
                if len(data["content"]) > 0:
                    first_content = data["content"][0]
                    if isinstance(first_content, dict) and "text" in first_content:
                        text_content = first_content["text"]
                        if text_content and text_content.strip():
                            print(f"✅ Content text: '{text_content[:50]}{'...' if len(text_content) > 50 else ''}'")
                            print("✅ Claude API响应格式正确，包含有效内容")
                            return True
                        else:
                            print("❌ Content text为空")
                            return False
                    else:
                        print("❌ Content格式错误")
                        return False
                else:
                    print("❌ Content数组为空")
                    return False
            else:
                print("❌ Content字段缺失或格式错误")
                return False
        else:
            print(f"❌ Claude API请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Claude API测试异常: {e}")
        return False

def test_claude_stream_api():
    """测试Claude流式API"""
    print("\n🌊 测试Claude流式API...")
    
    test_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "stream": True,
        "messages": [
            {"role": "user", "content": "Say hello briefly"}
        ]
    }
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 123456"
        }
        response = requests.post(
            f"{CLAUDE_API_BASE}/v1/messages",
            json=test_payload,
            headers=headers,
            stream=True,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("流式响应内容:")
            content_received = False
            events_count = 0
            total_content = ""
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    print(f"  {line}")
                    events_count += 1
                    
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str and data_str != "[DONE]":
                            try:
                                data = json.loads(data_str)
                                # 检查Claude流式响应格式
                                if data.get("type") == "content_block_delta":
                                    delta = data.get("delta", {})
                                    text = delta.get("text", "")
                                    if text:
                                        content_received = True
                                        total_content += text
                            except json.JSONDecodeError:
                                pass
            
            print(f"\n📊 流式响应统计:")
            print(f"总事件数: {events_count}")
            print(f"累积内容: '{total_content}'")
            
            if content_received and total_content.strip():
                print("✅ 流式Claude API响应包含有效内容")
                return True
            else:
                print("❌ 流式Claude API响应没有有效内容")
                return False
        else:
            print(f"❌ 流式Claude API请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 流式Claude API测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🔍 Claude Messages API 专项测试")
    print("=" * 60)
    
    # 检查服务器健康状态
    try:
        response = requests.get(f"{CLAUDE_API_BASE}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器健康状态正常")
        else:
            print(f"❌ 服务器健康状态异常: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return
    
    results = []
    
    # 执行测试
    results.append(("Claude Messages API", test_claude_api_detailed()))
    results.append(("Claude Stream API", test_claude_stream_api()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s} {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有Claude API测试通过！")
    else:
        print("⚠️  部分Claude API测试失败，可能存在assistant messages问题。")

if __name__ == "__main__":
    main()
