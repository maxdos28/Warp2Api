#!/usr/bin/env python3
"""
测试chunked响应问题
诊断peer closed connection错误
"""

import requests
import json

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def test_response_completeness():
    """测试响应完整性"""
    print("🔍 响应完整性测试")
    print("="*50)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "Connection": "close"  # 强制关闭连接，避免keep-alive问题
    }
    
    test_cases = [
        {
            "name": "短响应",
            "data": {
                "model": "claude-4-sonnet",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10
            }
        },
        {
            "name": "中等响应", 
            "data": {
                "model": "claude-4-sonnet",
                "messages": [{"role": "user", "content": "请简单介绍一下Python"}],
                "max_tokens": 100
            }
        },
        {
            "name": "长响应",
            "data": {
                "model": "claude-4-sonnet", 
                "messages": [{"role": "user", "content": "请详细解释什么是机器学习，包括各种算法"}],
                "max_tokens": 500
            }
        }
    ]
    
    for case in test_cases:
        print(f"\n[测试] {case['name']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json=case['data'],
                headers=headers,
                timeout=30
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应大小: {len(response.text)} 字节")
            
            # 检查响应头
            print(f"Content-Length: {response.headers.get('content-length', 'N/A')}")
            print(f"Transfer-Encoding: {response.headers.get('transfer-encoding', 'N/A')}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # 检查响应是否完整
                    has_usage = 'usage' in result
                    content_length = len(result.get('choices', [{}])[0].get('message', {}).get('content', ''))
                    
                    print(f"✅ JSON解析: 成功")
                    print(f"✅ 包含usage: {has_usage}")
                    print(f"✅ 内容长度: {content_length} 字符")
                    
                    if has_usage and content_length > 0:
                        print("✅ 响应完整")
                    else:
                        print("❌ 响应不完整")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    print(f"原始响应: {response.text[:200]}...")
            else:
                print(f"❌ HTTP错误: {response.text[:100]}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 连接错误: {e}")
        except requests.exceptions.Timeout as e:
            print(f"❌ 超时错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")

def test_streaming_vs_non_streaming():
    """测试流式vs非流式响应"""
    print("\n🌊 流式vs非流式响应测试")
    print("="*50)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    base_request = {
        "model": "claude-4-sonnet",
        "messages": [{"role": "user", "content": "Hello, write a short response"}],
        "max_tokens": 100
    }
    
    # 测试非流式
    print("\n[测试] 非流式响应")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={**base_request, "stream": False},
            headers=headers,
            timeout=30
        )
        
        print(f"非流式 - 状态码: {response.status_code}, 大小: {len(response.text)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"非流式 - 解析成功: {'usage' in result}")
        
    except Exception as e:
        print(f"非流式错误: {e}")
    
    # 测试流式
    print("\n[测试] 流式响应")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={**base_request, "stream": True},
            headers=headers,
            stream=True,
            timeout=30
        )
        
        print(f"流式 - 状态码: {response.status_code}")
        
        if response.status_code == 200:
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    if chunk_count <= 3:  # 只显示前几个chunk
                        print(f"   chunk {chunk_count}: {line.decode()[:50]}...")
            
            print(f"流式 - 收到 {chunk_count} 个chunks")
        
    except Exception as e:
        print(f"流式错误: {e}")

def main():
    """主诊断函数"""
    print("🔧 Cline连接问题诊断")
    print("="*50)
    print("目标：解决'peer closed connection'错误")
    
    # 测试响应完整性
    test_response_completeness()
    
    # 测试流式vs非流式
    test_streaming_vs_non_streaming()
    
    print("\n" + "="*50)
    print("💡 问题解决建议")
    print("="*50)
    print("""
常见的'peer closed connection'原因和解决方法:

1. 响应过大或超时
   - 减少max_tokens参数
   - 增加timeout设置

2. 服务器内存不足
   - 重启服务器
   - 检查系统资源

3. HTTP连接配置问题
   - 在Cline中设置Connection: close
   - 禁用HTTP keep-alive

4. 响应格式问题
   - 我们已添加usage字段
   - 已修复空响应问题

建议Cline配置:
- 设置合理的timeout (30-60秒)
- 使用较小的max_tokens (100-500)
- 启用重试机制
- 检查网络连接稳定性
""")

if __name__ == "__main__":
    main()