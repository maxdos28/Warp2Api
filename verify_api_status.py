#!/usr/bin/env python3
"""
验证API状态和Claude Code兼容性
"""

import requests
import json

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def check_all_endpoints():
    """检查所有端点状态"""
    print("🔍 API端点状态检查")
    print("="*50)
    
    endpoints = [
        {"method": "GET", "url": "/healthz", "name": "健康检查"},
        {"method": "GET", "url": "/v1/models", "name": "OpenAI模型列表"},
        {"method": "GET", "url": "/v1/messages/models", "name": "Claude模型列表"},
        {"method": "GET", "url": "/v1/messages/init", "name": "Claude Code初始化(GET)"},
        {"method": "POST", "url": "/v1/messages/init", "name": "Claude Code初始化(POST)"},
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\n[测试] {endpoint['name']}")
        
        headers = {"Authorization": f"Bearer {API_KEY}"}
        if endpoint["method"] == "POST":
            headers["Content-Type"] = "application/json"
        
        try:
            if endpoint["method"] == "GET":
                response = requests.get(f"{BASE_URL}{endpoint['url']}", headers=headers, timeout=10)
            else:
                response = requests.post(f"{BASE_URL}{endpoint['url']}", headers=headers, json={}, timeout=10)
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ 正常")
                results.append(True)
            elif response.status_code == 401:
                print("   ❌ 认证失败")
                results.append(False)
            else:
                print(f"   ⚠️ 异常状态: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
            results.append(False)
    
    return results

def test_claude_code_compatibility():
    """测试Claude Code兼容性"""
    print("\n🤖 Claude Code兼容性测试")
    print("="*50)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "anthropic-version": "2023-06-01"
    }
    
    # 测试Claude Code典型的请求
    claude_code_request = {
        "model": "claude-3-5-sonnet-20241022",
        "system": [
            {
                "type": "text",
                "text": "You are Claude Code, Anthropic's official CLI for Claude.",
                "cache_control": {"type": "ephemeral"}
            },
            {
                "type": "text",
                "text": "You help with software development tasks."
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": "Hello Claude Code, can you help me?"
            }
        ],
        "max_tokens": 200
    }
    
    print("\n[测试] Claude Code典型请求")
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json=claude_code_request,
            headers=headers,
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('content', [])
            text_content = ''.join([block.get('text', '') for block in content if block.get('type') == 'text'])
            
            print("   ✅ 请求成功")
            print(f"   响应长度: {len(text_content)} 字符")
            print(f"   响应预览: {text_content[:100]}...")
            return True
        elif response.status_code == 401:
            print("   ❌ 认证失败 - API密钥问题")
            print(f"   错误: {response.text}")
            return False
        else:
            print(f"   ❌ 其他错误: {response.status_code}")
            print(f"   错误: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
        return False

def debug_auth_issue():
    """调试认证问题"""
    print("\n🔐 认证问题调试")
    print("="*50)
    
    # 测试不同的认证方式
    test_cases = [
        {"name": "无认证头", "headers": {}},
        {"name": "错误的API密钥", "headers": {"Authorization": "Bearer wrong-key"}},
        {"name": "正确的API密钥", "headers": {"Authorization": "Bearer 0000"}},
        {"name": "x-api-key格式", "headers": {"x-api-key": "0000"}},
    ]
    
    for case in test_cases:
        print(f"\n[测试] {case['name']}")
        
        try:
            response = requests.get(
                f"{BASE_URL}/v1/messages/models",
                headers=case['headers'],
                timeout=10
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ 认证成功")
            elif response.status_code == 401:
                print("   ❌ 认证失败")
            else:
                print(f"   ⚠️ 其他状态: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")

def main():
    """主检查函数"""
    print("🔧 API状态和Claude Code兼容性检查")
    print("="*60)
    print(f"目标服务器: {BASE_URL}")
    print(f"API密钥: {API_KEY}")
    
    # 检查所有端点
    endpoint_results = check_all_endpoints()
    
    # 调试认证问题
    debug_auth_issue()
    
    # 测试Claude Code兼容性
    claude_code_ok = test_claude_code_compatibility()
    
    # 总结
    print("\n" + "="*60)
    print("📊 检查结果总结")
    print("="*60)
    
    endpoint_success = sum(endpoint_results) / len(endpoint_results) if endpoint_results else 0
    
    print(f"端点可用性: {sum(endpoint_results)}/{len(endpoint_results)} ({endpoint_success:.1%})")
    print(f"Claude Code兼容性: {'✅ 正常' if claude_code_ok else '❌ 有问题'}")
    
    if endpoint_success < 0.8:
        print("\n❌ 多个端点认证失败")
        print("可能的解决方案:")
        print("1. 检查服务器是否正确读取了API_TOKEN环境变量")
        print("2. 重启服务器: pkill -f python && ./start.sh")
        print("3. 检查.env文件中的API_TOKEN设置")
    elif not claude_code_ok:
        print("\n⚠️ Claude Code特定问题")
        print("可能需要进一步调试Claude Code的请求格式")
    else:
        print("\n✅ 所有功能正常")
        print("Claude Code应该可以正常连接了")

if __name__ == "__main__":
    main()