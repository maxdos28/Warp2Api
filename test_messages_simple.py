#!/usr/bin/env python3
"""
简单测试 Claude Messages API
"""
import httpx
import json
import asyncio

async def test_messages_api():
    """测试 /v1/messages 接口"""
    print("🧪 测试 Claude Messages API (/v1/messages)")
    print("密钥: 123456")
    print("-" * 50)
    
    # 测试数据
    test_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "你好，请简单回复一下，测试API是否正常"}
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("📤 发送请求...")
            response = await client.post(
                "http://localhost:28888/v1/messages",
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json=test_data
            )
            
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ 请求成功!")
                try:
                    data = response.json()
                    content = data.get("content", [])
                    if content and len(content) > 0:
                        text = content[0].get("text", "")
                        print(f"💬 AI回复: {text}")
                    else:
                        print("⚠️ 响应格式异常，没有找到content")
                        print(f"📄 原始响应: {response.text[:200]}...")
                except json.JSONDecodeError:
                    print("❌ 响应不是有效的JSON格式")
                    print(f"📄 原始响应: {response.text[:200]}...")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"📄 错误信息: {response.text[:300]}...")
                
                # 分析常见错误
                if response.status_code == 401:
                    print("🔑 可能的原因: API密钥无效")
                elif response.status_code == 404:
                    print("🔍 可能的原因: 接口路径不存在，请检查服务是否正确启动")
                elif response.status_code == 500:
                    print("🔥 可能的原因: 服务器内部错误，请检查日志")
                elif response.status_code == 429:
                    print("⏰ 可能的原因: 配额用尽或请求频率过高")
                    
    except httpx.ConnectError:
        print("❌ 连接失败: 无法连接到服务器")
        print("💡 请确认:")
        print("   1. API服务器是否启动 (端口28888)")
        print("   2. Bridge服务器是否启动 (端口28889)")
        print("   3. 检查命令: netstat -an | findstr 28888")
    except httpx.TimeoutException:
        print("⏰ 请求超时: 服务器响应时间过长")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_messages_api())
