#!/usr/bin/env python3
"""
测试Cline兼容性
"""
import asyncio
import json
import httpx
import time

async def test_cline_compatibility():
    print("🧪 测试Cline兼容性")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        {
            "name": "基础聊天测试",
            "data": {
                "model": "claude-4-sonnet",
                "messages": [{"role": "user", "content": "Hello, test basic chat"}],
                "max_tokens": 100
            }
        },
        {
            "name": "工具调用测试",
            "data": {
                "model": "claude-4-sonnet",
                "messages": [{"role": "user", "content": "Please help me with a coding task"}],
                "max_tokens": 200,
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "description": "Read a file",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string", "description": "File path"}
                                },
                                "required": ["path"]
                            }
                        }
                    }
                ]
            }
        },
        {
            "name": "流式响应测试",
            "data": {
                "model": "claude-4-sonnet",
                "messages": [{"role": "user", "content": "Write a short story"}],
                "max_tokens": 300,
                "stream": True
            }
        }
    ]
    
    base_url = "http://127.0.0.1:28889"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if test_case['data'].get('stream'):
                    # 流式测试
                    print("   🔄 流式响应测试...")
                    async with client.stream(
                        "POST", 
                        f"{base_url}/v1/chat/completions",
                        headers=headers,
                        json=test_case['data']
                    ) as response:
                        print(f"   📊 状态码: {response.status_code}")
                        
                        if response.status_code == 200:
                            chunk_count = 0
                            content_received = False
                            
                            async for line in response.aiter_lines():
                                if line.startswith("data: "):
                                    data = line[6:]  # 移除 "data: " 前缀
                                    if data.strip() == "[DONE]":
                                        break
                                    
                                    try:
                                        chunk = json.loads(data)
                                        chunk_count += 1
                                        
                                        # 检查内容
                                        if "choices" in chunk and chunk["choices"]:
                                            choice = chunk["choices"][0]
                                            if "delta" in choice and "content" in choice["delta"]:
                                                content_received = True
                                                
                                        # 检查工具调用
                                        if "choices" in chunk and chunk["choices"]:
                                            choice = chunk["choices"][0]
                                            if "delta" in choice and "tool_calls" in choice["delta"]:
                                                print(f"   🔧 工具调用: {choice['delta']['tool_calls']}")
                                                
                                    except json.JSONDecodeError as e:
                                        print(f"   ⚠️ JSON解析错误: {e}")
                                        print(f"   📄 原始数据: {data[:100]}...")
                            
                            print(f"   ✅ 流式测试完成 - 块数: {chunk_count}, 有内容: {content_received}")
                        else:
                            error_text = await response.aread()
                            print(f"   ❌ 流式测试失败: {response.status_code}")
                            print(f"   📄 错误信息: {error_text.decode()[:200]}...")
                else:
                    # 非流式测试
                    print("   📤 非流式响应测试...")
                    response = await client.post(
                        f"{base_url}/v1/chat/completions",
                        headers=headers,
                        json=test_case['data']
                    )
                    
                    print(f"   📊 状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"   ✅ 请求成功")
                        
                        # 检查响应格式
                        required_fields = ["id", "object", "created", "model", "choices"]
                        for field in required_fields:
                            if field in result:
                                print(f"   ✓ {field}: {type(result[field])}")
                            else:
                                print(f"   ✗ 缺少字段: {field}")
                        
                        # 检查choices内容
                        if "choices" in result and result["choices"]:
                            choice = result["choices"][0]
                            print(f"   📝 响应内容长度: {len(choice.get('message', {}).get('content', ''))}")
                            print(f"   🔧 工具调用数量: {len(choice.get('message', {}).get('tool_calls', []))}")
                            print(f"   🏁 完成原因: {choice.get('finish_reason', 'unknown')}")
                            
                            # 检查是否有错误信息
                            content = choice.get('message', {}).get('content', '')
                            if 'This may indicate a failure' in content:
                                print(f"   ⚠️ 检测到错误信息: {content[:100]}...")
                            else:
                                print(f"   ✅ 响应内容正常")
                        else:
                            print(f"   ❌ 响应格式错误: 缺少choices")
                    else:
                        print(f"   ❌ 请求失败: {response.status_code}")
                        print(f"   📄 错误信息: {response.text[:200]}...")
                        
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
    
    print(f"\n💡 建议:")
    print(f"   1. 检查响应格式是否符合OpenAI标准")
    print(f"   2. 确保错误信息被正确过滤")
    print(f"   3. 验证工具调用格式正确")
    print(f"   4. 监控日志中的详细错误信息")

if __name__ == "__main__":
    asyncio.run(test_cline_compatibility())
