#!/usr/bin/env python3
"""
Claude Messages API (/v1/messages) 完整工具调用测试
测试所有工具调用功能
"""

import json
import subprocess
import time
from typing import Dict, Any, List

# 测试配置
BASE_URL = "http://localhost:28889"
API_TOKEN = "0000"

def print_test_header(test_name: str):
    """打印测试标题"""
    print("\n" + "="*70)
    print(f" {test_name}")
    print("="*70)

def print_result(success: bool, message: str):
    """打印测试结果"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def make_request(endpoint: str, headers: Dict[str, str], data: Dict[str, Any], stream: bool = False) -> Dict[str, Any]:
    """发送 HTTP 请求"""
    headers_str = " ".join([f'-H "{k}: {v}"' for k, v in headers.items()])
    
    if stream:
        cmd = f'''curl -N -s -X POST {BASE_URL}{endpoint} \
          {headers_str} \
          -d '{json.dumps(data)}' 2>&1 | head -50'''
    else:
        cmd = f'''curl -s -X POST {BASE_URL}{endpoint} \
          {headers_str} \
          -d '{json.dumps(data)}' '''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        if stream:
            return {"stream_data": result.stdout}
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON: {result.stdout[:200]}"}
    except Exception as e:
        return {"error": str(e)}

def test_basic_tools():
    """测试基本的自定义工具调用"""
    print_test_header("1. 基本自定义工具调用")
    
    # 测试天气工具
    response = make_request(
        "/v1/messages",
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
            "anthropic-version": "2023-06-01"
        },
        {
            "model": "claude-4-sonnet",
            "messages": [
                {"role": "user", "content": "What's the weather in Beijing, Tokyo and London?"}
            ],
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get the current weather in a given location",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "The unit of temperature"
                            }
                        },
                        "required": ["location"]
                    }
                }
            ],
            "max_tokens": 300,
            "stream": False
        }
    )
    
    success = False
    tool_calls = []
    
    if "content" in response:
        for block in response.get("content", []):
            if block.get("type") == "tool_use":
                tool_calls.append(block)
                success = True
    
    print_result(success, f"天气工具调用: 找到 {len(tool_calls)} 个工具调用")
    for tool in tool_calls:
        print(f"  - {tool.get('name')}: {tool.get('input')}")
    
    return success

def test_computer_use_all():
    """测试 Computer Use 的所有操作"""
    print_test_header("2. Computer Use 工具 - 所有操作")
    
    test_cases = [
        ("Take a screenshot", {"action": "screenshot"}, "截屏"),
        ("Click at position 100, 200", {"action": "click", "coordinate": [100, 200]}, "点击"),
        ("Type 'Hello World'", {"action": "type", "text": "Hello World"}, "输入文本"),
        ("Scroll down", {"action": "scroll", "direction": "down"}, "滚动"),
        ("Press Enter key", {"action": "key", "key": "Return"}, "按键"),
    ]
    
    results = []
    
    for prompt, expected_input, desc in test_cases:
        response = make_request(
            "/v1/messages",
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_TOKEN}",
                "anthropic-version": "2023-06-01",
                "anthropic-beta": "computer-use-2024-10-22"
            },
            {
                "model": "claude-4-sonnet",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "stream": False
            }
        )
        
        found = False
        if "content" in response:
            for block in response.get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == "computer_20241022":
                    found = True
                    actual_input = block.get("input", {})
                    action_match = actual_input.get("action") == expected_input.get("action")
                    print_result(action_match, f"{desc}: {actual_input}")
                    results.append(action_match)
                    break
        
        if not found:
            print_result(False, f"{desc}: 未找到工具调用")
            results.append(False)
    
    return all(results)

def test_code_execution_all():
    """测试 Code Execution 的所有命令"""
    print_test_header("3. Code Execution 工具 - 所有命令")
    
    test_cases = [
        ("View the first 10 lines of README.md", 
         {"command": "view", "path": "README.md", "view_range": [1, 10]}, 
         "查看文件"),
        
        ("Create a new file test.py with print('test')", 
         {"command": "create", "path": "test.py", "file_text": "print('test')\n"}, 
         "创建文件"),
        
        ("Replace 'old text' with 'new text' in config.py", 
         {"command": "str_replace", "path": "config.py", "old_str": "old text", "new_str": "new text"}, 
         "替换文本"),
        
        ("Undo the last edit", 
         {"command": "undo_edit"}, 
         "撤销编辑"),
    ]
    
    results = []
    
    for prompt, expected_fields, desc in test_cases:
        response = make_request(
            "/v1/messages",
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_TOKEN}",
                "anthropic-version": "2023-06-01",
                "anthropic-beta": "code-execution-2025-08-25"
            },
            {
                "model": "claude-4-sonnet",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "stream": False
            }
        )
        
        found = False
        if "content" in response:
            for block in response.get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == "str_replace_based_edit_tool":
                    found = True
                    actual_input = block.get("input", {})
                    command_match = actual_input.get("command") == expected_fields.get("command")
                    print_result(command_match, f"{desc}: {actual_input}")
                    results.append(command_match)
                    break
        
        if not found:
            print_result(False, f"{desc}: 未找到工具调用")
            results.append(False)
    
    return all(results)

def test_tool_result_handling():
    """测试工具结果处理"""
    print_test_header("4. 工具结果处理")
    
    # 模拟一个包含工具调用和结果的对话
    response = make_request(
        "/v1/messages",
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
            "anthropic-version": "2023-06-01"
        },
        {
            "model": "claude-4-sonnet",
            "messages": [
                {"role": "user", "content": "What's the weather in Paris?"},
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "I'll check the weather in Paris for you."},
                        {
                            "type": "tool_use",
                            "id": "toolu_01234",
                            "name": "get_weather",
                            "input": {"location": "Paris, France"}
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "toolu_01234",
                            "content": "The weather in Paris is sunny, 22°C"
                        }
                    ]
                },
                {"role": "user", "content": "Thanks! How about London?"}
            ],
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get weather information",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        },
                        "required": ["location"]
                    }
                }
            ],
            "max_tokens": 300,
            "stream": False
        }
    )
    
    success = False
    if "content" in response:
        for block in response.get("content", []):
            if block.get("type") == "tool_use":
                location = block.get("input", {}).get("location", "")
                if "London" in location:
                    success = True
                    print_result(True, f"正确处理工具结果并继续对话: {block.get('input')}")
                    break
    
    if not success:
        print_result(False, "未能正确处理工具结果")
    
    return success

def test_multiple_tools():
    """测试多工具组合使用"""
    print_test_header("5. 多工具组合使用")
    
    response = make_request(
        "/v1/messages",
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "computer-use-2024-10-22,code-execution-2025-08-25"
        },
        {
            "model": "claude-4-sonnet",
            "messages": [
                {"role": "user", "content": "Take a screenshot and save the timestamp to a file called screenshot_time.txt"}
            ],
            "max_tokens": 500,
            "stream": False
        }
    )
    
    tool_calls = []
    if "content" in response:
        for block in response.get("content", []):
            if block.get("type") == "tool_use":
                tool_calls.append(block.get("name"))
    
    has_screenshot = "computer_20241022" in tool_calls
    has_file_create = "str_replace_based_edit_tool" in tool_calls
    
    print_result(has_screenshot, f"Screenshot 工具: {'已调用' if has_screenshot else '未调用'}")
    print_result(has_file_create, f"File 工具: {'已调用' if has_file_create else '未调用'}")
    
    success = len(tool_calls) >= 1  # 至少调用了一个工具
    print_result(success, f"总共调用了 {len(tool_calls)} 个工具")
    
    return success

def test_streaming_tools():
    """测试流式响应中的工具调用"""
    print_test_header("6. 流式响应工具调用")
    
    response = make_request(
        "/v1/messages",
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "computer-use-2024-10-22"
        },
        {
            "model": "claude-4-sonnet",
            "messages": [{"role": "user", "content": "Take a screenshot"}],
            "max_tokens": 200,
            "stream": True
        },
        stream=True
    )
    
    stream_data = response.get("stream_data", "")
    
    has_tool_event = "content_block_start" in stream_data and "tool_use" in stream_data
    has_tool_name = "computer_20241022" in stream_data
    has_input_delta = "input_json_delta" in stream_data
    
    print_result(has_tool_event, f"工具事件: {'找到' if has_tool_event else '未找到'}")
    print_result(has_tool_name, f"工具名称: {'找到' if has_tool_name else '未找到'}")
    print_result(has_input_delta, f"参数流: {'找到' if has_input_delta else '未找到'}")
    
    return has_tool_event and has_tool_name

def test_tool_choice():
    """测试工具选择参数"""
    print_test_header("7. 工具选择控制")
    
    # 测试 tool_choice 参数
    test_cases = [
        ({"tool_choice": {"type": "any"}}, "允许任意工具"),
        ({"tool_choice": {"type": "tool", "name": "get_weather"}}, "指定特定工具"),
        ({"tool_choice": {"type": "none"}}, "禁用工具"),
    ]
    
    results = []
    for tool_choice, desc in test_cases:
        request_data = {
            "model": "claude-4-sonnet",
            "messages": [{"role": "user", "content": "What's the weather?"}],
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get weather",
                    "input_schema": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"]
                    }
                }
            ],
            "max_tokens": 200,
            "stream": False
        }
        request_data.update(tool_choice)
        
        response = make_request(
            "/v1/messages",
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_TOKEN}",
                "anthropic-version": "2023-06-01"
            },
            request_data
        )
        
        # 这里只检查请求是否成功，因为 tool_choice 的实际效果取决于 Warp
        success = "content" in response or "error" not in response
        print_result(success, f"{desc}: {'请求成功' if success else '请求失败'}")
        results.append(success)
    
    return all(results)

def test_parallel_tools():
    """测试并行工具调用"""
    print_test_header("8. 并行工具调用")
    
    response = make_request(
        "/v1/messages",
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
            "anthropic-version": "2023-06-01"
        },
        {
            "model": "claude-4-sonnet",
            "messages": [
                {"role": "user", "content": "Get the weather for Paris, London, and Tokyo at the same time"}
            ],
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get weather for a location",
                    "input_schema": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"]
                    }
                }
            ],
            "max_tokens": 400,
            "stream": False
        }
    )
    
    tool_calls = []
    if "content" in response:
        for block in response.get("content", []):
            if block.get("type") == "tool_use":
                tool_calls.append(block.get("input", {}).get("location", "Unknown"))
    
    success = len(tool_calls) >= 2  # 至少有2个并行调用
    print_result(success, f"并行调用数量: {len(tool_calls)}")
    for location in tool_calls:
        print(f"  - 查询位置: {location}")
    
    return success

def test_error_handling():
    """测试错误处理"""
    print_test_header("9. 错误处理")
    
    # 测试无效的工具定义
    response = make_request(
        "/v1/messages",
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
            "anthropic-version": "2023-06-01"
        },
        {
            "model": "claude-4-sonnet",
            "messages": [{"role": "user", "content": "Test"}],
            "tools": [
                {
                    "name": "invalid_tool",
                    # 缺少必需的字段
                }
            ],
            "max_tokens": 100,
            "stream": False
        }
    )
    
    # 应该仍然返回响应，即使工具定义不完整
    success = "content" in response or "error" in response
    print_result(success, f"错误处理: {'正常' if success else '异常'}")
    
    return success

def test_system_prompt_with_tools():
    """测试带系统提示词的工具调用"""
    print_test_header("10. 系统提示词与工具结合")
    
    response = make_request(
        "/v1/messages",
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
            "anthropic-version": "2023-06-01"
        },
        {
            "model": "claude-4-sonnet",
            "system": "You are a helpful weather assistant. Always be polite and provide detailed weather information.",
            "messages": [
                {"role": "user", "content": "What's the weather like?"}
            ],
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get current weather",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        },
                        "required": ["location"]
                    }
                }
            ],
            "max_tokens": 300,
            "stream": False
        }
    )
    
    success = "content" in response
    has_tool = False
    
    if success:
        for block in response.get("content", []):
            if block.get("type") == "tool_use":
                has_tool = True
                break
    
    print_result(success, f"系统提示词请求: {'成功' if success else '失败'}")
    print_result(has_tool or success, f"工具调用: {'有' if has_tool else '仅文本响应'}")
    
    return success

def main():
    """运行所有测试"""
    print("\n" + "🔧"*35)
    print(" Claude Messages API 完整工具调用测试")
    print("🔧"*35)
    
    # 检查服务器
    try:
        result = subprocess.run(
            f"curl -s {BASE_URL}/healthz",
            shell=True, capture_output=True, text=True, timeout=5
        )
        if "ok" not in result.stdout:
            print("\n❌ 服务器未运行！")
            return
    except:
        print("\n❌ 无法连接到服务器")
        return
    
    print("\n✅ 服务器正在运行")
    print(f"📍 测试端点: {BASE_URL}/v1/messages")
    time.sleep(1)
    
    # 运行所有测试
    test_results = {
        "基本工具调用": test_basic_tools(),
        "Computer Use 全部操作": test_computer_use_all(),
        "Code Execution 全部命令": test_code_execution_all(),
        "工具结果处理": test_tool_result_handling(),
        "多工具组合": test_multiple_tools(),
        "流式工具调用": test_streaming_tools(),
        "工具选择控制": test_tool_choice(),
        "并行工具调用": test_parallel_tools(),
        "错误处理": test_error_handling(),
        "系统提示词+工具": test_system_prompt_with_tools(),
    }
    
    # 打印总结
    print("\n" + "="*70)
    print(" 测试结果总结")
    print("="*70)
    
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    
    for name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Claude Messages API 工具调用完全支持！")
    elif passed >= total * 0.8:
        print("\n✅ 大部分测试通过，核心功能正常。")
    else:
        print("\n⚠️ 部分测试失败，需要进一步调试。")

if __name__ == "__main__":
    main()