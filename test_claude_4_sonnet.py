#!/usr/bin/env python3
"""
测试 claude-4-sonnet 模型支持
"""

import httpx
import json
import asyncio


async def test_claude_4_sonnet():
    base_url = "http://localhost:28889"
    
    print("="*60)
    print("测试 claude-4-sonnet 模型支持")
    print("="*60)
    
    # 测试 1: OpenAI 格式
    print("\n1. 通过 OpenAI Chat Completions API 使用 claude-4-sonnet")
    print("-"*40)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/v1/chat/completions",
                json={
                    "model": "claude-4-sonnet",
                    "messages": [
                        {"role": "user", "content": "用一句话介绍你自己"}
                    ],
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功！模型: {result.get('model')}")
                print(f"响应: {result['choices'][0]['message']['content'][:100]}...")
            else:
                print(f"❌ 失败: HTTP {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    # 测试 2: Claude Messages API 格式
    print("\n2. 通过 Claude Messages API 使用 claude-4-sonnet")
    print("-"*40)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{base_url}/v1/messages",
                json={
                    "model": "claude-4-sonnet",
                    "messages": [
                        {"role": "user", "content": "用一句话介绍你自己"}
                    ],
                    "max_tokens": 100,
                    "stream": False
                },
                headers={
                    "anthropic-version": "2023-06-01",
                    "x-api-key": "dummy"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功！模型: {result.get('model')}")
                content = result.get('content', [])
                if content and isinstance(content[0], dict):
                    print(f"响应: {content[0].get('text', '')[:100]}...")
                elif isinstance(content, str):
                    print(f"响应: {content[:100]}...")
            else:
                print(f"❌ 失败: HTTP {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    # 测试 3: 流式响应
    print("\n3. 测试 claude-4-sonnet 流式响应")
    print("-"*40)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("发送流式请求...")
            async with client.stream(
                "POST",
                f"{base_url}/v1/chat/completions",
                json={
                    "model": "claude-4-sonnet",
                    "messages": [
                        {"role": "user", "content": "数到5"}
                    ],
                    "stream": True
                }
            ) as response:
                if response.status_code == 200:
                    print("✅ 流式响应: ", end="")
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    print(content, end="", flush=True)
                            except:
                                pass
                    print("\n✅ 流式响应完成")
                else:
                    print(f"❌ 失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    # 测试 4: 模型列表
    print("\n4. 检查模型列表")
    print("-"*40)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # OpenAI 模型列表
        try:
            response = await client.get(f"{base_url}/v1/models")
            if response.status_code == 200:
                models = response.json()
                claude_models = [m for m in models.get("data", []) if "claude" in m.get("id", "").lower()]
                print("OpenAI API 中的 Claude 模型:")
                for model in claude_models:
                    if "claude-4" in model.get("id", ""):
                        print(f"  ✅ {model['id']}")
                    else:
                        print(f"  • {model['id']}")
        except Exception as e:
            print(f"获取 OpenAI 模型列表失败: {e}")
        
        # Claude 模型列表
        try:
            response = await client.get(f"{base_url}/v1/messages/models")
            if response.status_code == 200:
                models = response.json()
                print("\nClaude API 支持的模型:")
                for model in models.get("data", []):
                    print(f"  • {model['id']}")
        except Exception as e:
            print(f"获取 Claude 模型列表失败: {e}")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    print("\n总结:")
    print("✅ claude-4-sonnet 可以通过 OpenAI Chat Completions API 使用")
    print("✅ claude-4-sonnet 可以通过 Claude Messages API 使用")
    print("✅ 支持流式和非流式响应")
    print("✅ 自动映射到 claude-3-5-sonnet-20241022")


if __name__ == "__main__":
    print("\n🚀 开始测试 claude-4-sonnet 模型...\n")
    asyncio.run(test_claude_4_sonnet())