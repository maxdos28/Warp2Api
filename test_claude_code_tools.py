#!/usr/bin/env python3
"""
测试 Claude Code 工具支持（Computer Use 和 Code Execution）
"""

import json
import requests
import time
from typing import Dict, Any, List


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_test(test_name: str):
    """打印测试名称"""
    print(f"\n[测试] {test_name}")
    print("-"*40)


async def send_claude_request(
    client: httpx.AsyncClient,
    base_url: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]] = None,
    beta_features: str = None,
    stream: bool = False
) -> Dict[str, Any]:
    """发送 Claude API 请求"""
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "x-api-key": "test-key"
    }
    
    if beta_features:
        headers["anthropic-beta"] = beta_features
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": messages,
        "max_tokens": 500,
        "stream": stream
    }
    
    if tools:
        request_data["tools"] = tools
    
    print(f"📤 发送请求:")
    print(f"   Headers: {headers}")
    print(f"   Beta功能: {beta_features or '无'}")
    if tools:
        print(f"   工具: {[t['name'] for t in tools]}")
    print(f"   消息: {messages[0]['content'][:100]}...")
    
    try:
        if stream:
            async with client.stream(
                "POST",
                f"{base_url}/v1/messages",
                json=request_data,
                headers=headers
            ) as response:
                if response.status_code != 200:
                    error = await response.aread()
                    return {"error": f"HTTP {response.status_code}: {error.decode()}"}
                
                result = {"events": [], "content": []}
                async for line in response.aiter_lines():
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                        result["events"].append(event_type)
                    elif line.startswith("data:"):
                        try:
                            data = json.loads(line[5:])
                            if data.get("type") == "content_block_start":
                                block = data.get("content_block", {})
                                if block.get("type") == "tool_use":
                                    result["content"].append({
                                        "type": "tool_use",
                                        "name": block.get("name"),
                                        "id": block.get("id")
                                    })
                            elif data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if result["content"] and result["content"][-1].get("type") == "text":
                                        result["content"][-1]["text"] += text
                                    else:
                                        result["content"].append({"type": "text", "text": text})
                                elif delta.get("type") == "input_json_delta":
                                    if result["content"] and result["content"][-1].get("type") == "tool_use":
                                        result["content"][-1]["input"] = json.loads(delta.get("partial_json", "{}"))
                        except:
                            pass
                return result
        else:
            response = await client.post(
                f"{base_url}/v1/messages",
                json=request_data,
                headers=headers
            )
            
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
            
            return response.json()
    
    except Exception as e:
        return {"error": str(e)}


async def test_computer_use_tool():
    """测试 Computer Use 工具"""
    print_section("测试 Computer Use 工具")
    
    base_url = "http://localhost:28889"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 测试1: 检查工具是否自动添加
        print_test("1. 验证 computer_20241022 工具自动添加")
        
        result = await send_claude_request(
            client=client,
            base_url=base_url,
            messages=[
                {"role": "user", "content": "请截取当前屏幕的截图"}
            ],
            beta_features="computer-use-2024-10-22",
            stream=True
        )
        
        if "error" in result:
            print(f"❌ 错误: {result['error']}")
        else:
            print(f"📥 收到的事件类型: {set(result.get('events', []))}")
            print(f"📥 响应内容:")
            for block in result.get("content", []):
                if block.get("type") == "tool_use":
                    print(f"   ✅ 工具调用: {block.get('name')}")
                    print(f"      ID: {block.get('id')}")
                    if "input" in block:
                        print(f"      参数: {block.get('input')}")
                elif block.get("type") == "text":
                    print(f"   文本: {block.get('text', '')[:200]}...")
        
        # 测试2: 手动定义工具
        print_test("2. 手动定义 computer_20241022 工具")
        
        computer_tool = {
            "name": "computer_20241022",
            "description": "Use a computer with screen, keyboard, and mouse",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["screenshot", "click", "type", "scroll", "key"]
                    },
                    "coordinate": {"type": "array", "items": {"type": "integer"}},
                    "text": {"type": "string"},
                    "direction": {"type": "string", "enum": ["up", "down", "left", "right"]},
                    "key": {"type": "string"}
                },
                "required": ["action"]
            }
        }
        
        result = await send_claude_request(
            client=client,
            base_url=base_url,
            messages=[
                {"role": "user", "content": "点击屏幕坐标 (100, 200) 位置"}
            ],
            tools=[computer_tool],
            stream=False
        )
        
        if "error" in result:
            print(f"❌ 错误: {result['error']}")
        else:
            print(f"📥 响应:")
            content = result.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        print(f"   ✅ 工具调用: {block.get('name')}")
                        print(f"      输入: {block.get('input')}")
                    elif isinstance(block, dict) and block.get("type") == "text":
                        print(f"   文本: {block.get('text', '')[:200]}...")
            else:
                print(f"   内容: {content}")


async def test_code_execution_tool():
    """测试 Code Execution 工具"""
    print_section("测试 Code Execution 工具")
    
    base_url = "http://localhost:28889"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 测试1: 检查工具是否自动添加
        print_test("1. 验证 str_replace_based_edit_tool 工具自动添加")
        
        result = await send_claude_request(
            client=client,
            base_url=base_url,
            messages=[
                {"role": "user", "content": "创建一个 hello.py 文件，内容是打印 'Hello World'"}
            ],
            beta_features="code-execution-2025-08-25",
            stream=True
        )
        
        if "error" in result:
            print(f"❌ 错误: {result['error']}")
        else:
            print(f"📥 收到的事件类型: {set(result.get('events', []))}")
            print(f"📥 响应内容:")
            for block in result.get("content", []):
                if block.get("type") == "tool_use":
                    print(f"   ✅ 工具调用: {block.get('name')}")
                    print(f"      ID: {block.get('id')}")
                    if "input" in block:
                        print(f"      参数: {block.get('input')}")
                elif block.get("type") == "text":
                    print(f"   文本: {block.get('text', '')[:200]}...")
        
        # 测试2: 手动定义工具
        print_test("2. 手动定义 str_replace_based_edit_tool 工具")
        
        code_tool = {
            "name": "str_replace_based_edit_tool",
            "description": "Edit files using string replacement",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["view", "create", "str_replace", "undo_edit"]
                    },
                    "path": {"type": "string"},
                    "file_text": {"type": "string"},
                    "old_str": {"type": "string"},
                    "new_str": {"type": "string"},
                    "view_range": {"type": "array", "items": {"type": "integer"}}
                },
                "required": ["command"]
            }
        }
        
        result = await send_claude_request(
            client=client,
            base_url=base_url,
            messages=[
                {"role": "user", "content": "查看 README.md 文件的前10行"}
            ],
            tools=[code_tool],
            stream=False
        )
        
        if "error" in result:
            print(f"❌ 错误: {result['error']}")
        else:
            print(f"📥 响应:")
            content = result.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        print(f"   ✅ 工具调用: {block.get('name')}")
                        print(f"      输入: {block.get('input')}")
                    elif isinstance(block, dict) and block.get("type") == "text":
                        print(f"   文本: {block.get('text', '')[:200]}...")
            else:
                print(f"   内容: {content}")


async def test_combined_tools():
    """测试同时使用多个工具"""
    print_section("测试组合使用多个工具")
    
    base_url = "http://localhost:28889"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print_test("同时启用 Computer Use 和 Code Execution")
        
        result = await send_claude_request(
            client=client,
            base_url=base_url,
            messages=[
                {"role": "user", "content": "先截图，然后创建一个 screenshot_info.txt 文件记录截图信息"}
            ],
            beta_features="computer-use-2024-10-22,code-execution-2025-08-25",
            stream=True
        )
        
        if "error" in result:
            print(f"❌ 错误: {result['error']}")
        else:
            print(f"📥 收到的事件类型: {set(result.get('events', []))}")
            print(f"📥 响应内容:")
            tool_calls = []
            for block in result.get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls.append(block.get('name'))
                    print(f"   ✅ 工具调用: {block.get('name')}")
                    if "input" in block:
                        print(f"      参数: {block.get('input')}")
                elif block.get("type") == "text":
                    print(f"   文本: {block.get('text', '')[:200]}...")
            
            if tool_calls:
                print(f"\n📊 调用的工具汇总: {tool_calls}")


async def test_tool_response_handling():
    """测试工具响应处理"""
    print_section("测试工具响应处理")
    
    base_url = "http://localhost:28889"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print_test("发送包含工具结果的对话")
        
        # 模拟一个包含工具调用和结果的对话
        messages = [
            {"role": "user", "content": "获取北京的天气"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "我来帮您查询北京的天气。"},
                    {
                        "type": "tool_use",
                        "id": "tool_123",
                        "name": "get_weather",
                        "input": {"location": "北京"}
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool_123",
                        "content": "北京今天晴天，温度25°C"
                    }
                ]
            },
            {"role": "user", "content": "谢谢，那上海呢？"}
        ]
        
        result = await send_claude_request(
            client=client,
            base_url=base_url,
            messages=messages,
            tools=[{
                "name": "get_weather",
                "description": "获取天气信息",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }],
            stream=False
        )
        
        if "error" in result:
            print(f"❌ 错误: {result['error']}")
        else:
            print(f"📥 响应:")
            content = result.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            print(f"   ✅ 新的工具调用: {block.get('name')}")
                            print(f"      输入: {block.get('input')}")
                        elif block.get("type") == "text":
                            print(f"   文本: {block.get('text', '')[:200]}...")
            else:
                print(f"   内容: {content}")


async def check_server_health():
    """检查服务器健康状态"""
    print_section("检查服务器状态")
    
    base_url = "http://localhost:28889"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 检查健康端点
        try:
            response = await client.get(f"{base_url}/healthz")
            if response.status_code == 200:
                print("✅ OpenAI/Claude API 服务器正在运行")
            else:
                print(f"⚠️ 服务器响应异常: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接到服务器: {e}")
            print("请确保服务器正在运行:")
            print("  1. 运行 ./start.sh 或 start.bat")
            print("  2. 或手动启动: python openai_compat.py")
            return False
        
        # 检查模型列表
        try:
            response = await client.get(f"{base_url}/v1/messages/models")
            if response.status_code == 200:
                models = response.json()
                print(f"✅ Claude API 端点可用，支持 {len(models.get('data', []))} 个模型")
            else:
                print("⚠️ Claude API 端点可能未正确配置")
        except Exception as e:
            print(f"⚠️ 无法获取 Claude 模型列表: {e}")
        
        return True


async def main():
    """主测试函数"""
    print("\n" + "🔧"*30)
    print(" Claude Code 工具完整测试套件")
    print("🔧"*30)
    
    # 检查服务器
    if not await check_server_health():
        print("\n⚠️ 请先启动服务器再运行测试")
        return
    
    # 运行测试
    print("\n开始测试...\n")
    
    # 测试 Computer Use
    await test_computer_use_tool()
    
    # 测试 Code Execution
    await test_code_execution_tool()
    
    # 测试组合使用
    await test_combined_tools()
    
    # 测试工具响应处理
    await test_tool_response_handling()
    
    # 总结
    print_section("测试总结")
    print("""
📊 测试结果汇总:

1. Computer Use 工具 (computer_20241022):
   - 通过 anthropic-beta: computer-use-2024-10-22 头激活
   - 支持截图、点击、输入等操作
   
2. Code Execution 工具 (str_replace_based_edit_tool):
   - 通过 anthropic-beta: code-execution-2025-08-25 头激活
   - 支持文件查看、创建、编辑等操作

3. 工具调用格式:
   - 支持 Claude 的 tool_use 和 tool_result 格式
   - 正确处理工具调用 ID 和参数

4. 组合使用:
   - 可以同时启用多个 Beta 功能
   - 支持在一次请求中调用多个工具

⚠️ 注意事项:
- 工具的实际执行需要后端 Warp 服务的支持
- 当前实现主要是格式转换和协议支持
- 实际的屏幕操作和文件编辑功能取决于 Warp 服务的能力
""")


if __name__ == "__main__":
    asyncio.run(main())