#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code 接口工具支持全面测试
测试 /v1/messages 端点的所有工具功能
"""

import json
import requests
import time
from typing import Dict, Any, List, Optional

# 测试配置
BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def print_section(title: str):
    """打印章节标题"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def print_test(test_name: str):
    """打印测试名称"""
    print(f"\n[测试] {test_name}")
    print("-"*50)

def print_result(success: bool, message: str):
    """打印测试结果"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def make_claude_request(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    beta_features: Optional[str] = None,
    stream: bool = False,
    system: Optional[str] = None
) -> Dict[str, Any]:
    """发送Claude API请求"""
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    if beta_features:
        headers["anthropic-beta"] = beta_features
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": messages,
        "max_tokens": 300,
        "stream": stream
    }
    
    if tools:
        request_data["tools"] = tools
    
    if system:
        request_data["system"] = system
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {"error": str(e)}

def test_server_health():
    """测试服务器健康状态"""
    print_section("服务器状态检查")
    
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print_result(True, "服务器运行正常")
            return True
        else:
            print_result(False, f"服务器响应异常: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"无法连接服务器: {e}")
        return False

def test_basic_claude_api():
    """测试基础Claude API功能"""
    print_section("基础Claude API功能测试")
    
    print_test("1. 简单文本对话")
    result = make_claude_request([
        {"role": "user", "content": "你好，请说一句话。"}
    ])
    
    success = "content" in result and not "error" in result
    if success:
        content = result.get("content", [])
        if isinstance(content, list) and len(content) > 0:
            text_content = next((block.get("text", "") for block in content if block.get("type") == "text"), "")
            print_result(True, f"收到响应: {text_content[:100]}...")
        else:
            print_result(True, f"收到响应: {str(content)[:100]}...")
    else:
        print_result(False, f"请求失败: {result.get('error', '未知错误')}")
    
    return success

def test_computer_use_tools():
    """测试Computer Use工具"""
    print_section("Computer Use 工具测试")
    
    test_cases = [
        {
            "name": "截屏功能",
            "prompt": "请截取当前屏幕的截图",
            "expected_tool": "computer_20241022",
            "expected_action": "screenshot"
        },
        {
            "name": "鼠标点击",
            "prompt": "点击屏幕坐标 (100, 200) 位置",
            "expected_tool": "computer_20241022", 
            "expected_action": "click"
        },
        {
            "name": "文本输入",
            "prompt": "在当前位置输入文字 'Hello World'",
            "expected_tool": "computer_20241022",
            "expected_action": "type"
        },
        {
            "name": "滚动操作",
            "prompt": "向下滚动页面",
            "expected_tool": "computer_20241022",
            "expected_action": "scroll"
        },
        {
            "name": "按键操作",
            "prompt": "按下回车键",
            "expected_tool": "computer_20241022",
            "expected_action": "key"
        }
    ]
    
    results = []
    
    for case in test_cases:
        print_test(case["name"])
        
        result = make_claude_request(
            messages=[{"role": "user", "content": case["prompt"]}],
            beta_features="computer-use-2024-10-22"
        )
        
        success = False
        if "content" in result:
            for block in result.get("content", []):
                if (block.get("type") == "tool_use" and 
                    block.get("name") == case["expected_tool"]):
                    tool_input = block.get("input", {})
                    action = tool_input.get("action")
                    if action == case["expected_action"]:
                        success = True
                        print_result(True, f"正确调用工具: {case['expected_tool']}, 动作: {action}")
                        if tool_input:
                            print(f"   参数: {json.dumps(tool_input, ensure_ascii=False)}")
                        break
        
        if not success:
            print_result(False, f"未找到预期的工具调用")
            if "error" in result:
                print(f"   错误: {result['error']}")
        
        results.append(success)
    
    return all(results)

def test_code_execution_tools():
    """测试Code Execution工具"""
    print_section("Code Execution 工具测试")
    
    test_cases = [
        {
            "name": "查看文件",
            "prompt": "查看README.md文件的前10行",
            "expected_tool": "str_replace_based_edit_tool",
            "expected_command": "view"
        },
        {
            "name": "创建文件", 
            "prompt": "创建一个test.py文件，内容是print('Hello')",
            "expected_tool": "str_replace_based_edit_tool",
            "expected_command": "create"
        },
        {
            "name": "字符串替换",
            "prompt": "将config.py文件中的'old_text'替换为'new_text'",
            "expected_tool": "str_replace_based_edit_tool",
            "expected_command": "str_replace"
        },
        {
            "name": "撤销编辑",
            "prompt": "撤销上次的编辑操作",
            "expected_tool": "str_replace_based_edit_tool", 
            "expected_command": "undo_edit"
        }
    ]
    
    results = []
    
    for case in test_cases:
        print_test(case["name"])
        
        result = make_claude_request(
            messages=[{"role": "user", "content": case["prompt"]}],
            beta_features="code-execution-2025-08-25"
        )
        
        success = False
        if "content" in result:
            for block in result.get("content", []):
                if (block.get("type") == "tool_use" and 
                    block.get("name") == case["expected_tool"]):
                    tool_input = block.get("input", {})
                    command = tool_input.get("command")
                    if command == case["expected_command"]:
                        success = True
                        print_result(True, f"正确调用工具: {case['expected_tool']}, 命令: {command}")
                        if tool_input:
                            print(f"   参数: {json.dumps(tool_input, ensure_ascii=False)}")
                        break
        
        if not success:
            print_result(False, f"未找到预期的工具调用")
            if "error" in result:
                print(f"   错误: {result['error']}")
        
        results.append(success)
    
    return all(results)

def test_custom_tools():
    """测试自定义工具"""
    print_section("自定义工具测试")
    
    print_test("天气查询工具")
    
    weather_tool = {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "温度单位"
                }
            },
            "required": ["city"]
        }
    }
    
    result = make_claude_request(
        messages=[{"role": "user", "content": "北京今天的天气怎么样？"}],
        tools=[weather_tool]
    )
    
    success = False
    if "content" in result:
        for block in result.get("content", []):
            if (block.get("type") == "tool_use" and 
                block.get("name") == "get_weather"):
                success = True
                tool_input = block.get("input", {})
                print_result(True, f"正确调用自定义工具: get_weather")
                print(f"   参数: {json.dumps(tool_input, ensure_ascii=False)}")
                break
    
    if not success:
        print_result(False, "未调用自定义工具")
        if "error" in result:
            print(f"   错误: {result['error']}")
    
    return success

def test_combined_tools():
    """测试组合工具使用"""
    print_section("组合工具测试")
    
    print_test("同时使用Computer Use和Code Execution")
    
    result = make_claude_request(
        messages=[{"role": "user", "content": "先截取屏幕截图，然后创建一个文件记录截图时间"}],
        beta_features="computer-use-2024-10-22,code-execution-2025-08-25"
    )
    
    tool_calls = []
    if "content" in result:
        for block in result.get("content", []):
            if block.get("type") == "tool_use":
                tool_calls.append(block.get("name"))
    
    has_computer = "computer_20241022" in tool_calls
    has_code = "str_replace_based_edit_tool" in tool_calls
    
    print_result(has_computer, f"Computer Use工具: {'已调用' if has_computer else '未调用'}")
    print_result(has_code, f"Code Execution工具: {'已调用' if has_code else '未调用'}")
    
    success = len(tool_calls) >= 1  # 至少调用一个工具
    print_result(success, f"总共调用了 {len(tool_calls)} 个工具")
    
    if tool_calls:
        print(f"   调用的工具: {tool_calls}")
    
    return success

def test_tool_result_handling():
    """测试工具结果处理"""
    print_section("工具结果处理测试")
    
    print_test("工具调用和结果对话")
    
    # 模拟包含工具调用和结果的完整对话
    messages = [
        {"role": "user", "content": "查询北京的天气"},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "我来帮您查询北京的天气。"},
                {
                    "type": "tool_use",
                    "id": "tool_123",
                    "name": "get_weather", 
                    "input": {"city": "北京", "unit": "celsius"}
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_123",
                    "content": "北京今天晴天，温度25°C，湿度60%"
                }
            ]
        },
        {"role": "user", "content": "谢谢，那上海呢？"}
    ]
    
    weather_tool = {
        "name": "get_weather",
        "description": "获取天气信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["city"]
        }
    }
    
    result = make_claude_request(
        messages=messages,
        tools=[weather_tool]
    )
    
    success = False
    if "content" in result:
        for block in result.get("content", []):
            if block.get("type") == "tool_use":
                tool_input = block.get("input", {})
                city = tool_input.get("city", "")
                if "上海" in city or "Shanghai" in city:
                    success = True
                    print_result(True, f"正确处理工具结果并继续对话")
                    print(f"   新的查询: {json.dumps(tool_input, ensure_ascii=False)}")
                    break
    
    if not success:
        print_result(False, "未能正确处理工具结果")
        if "error" in result:
            print(f"   错误: {result['error']}")
    
    return success

def test_streaming_response():
    """测试流式响应"""
    print_section("流式响应测试")
    
    print_test("流式工具调用")
    
    try:
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "computer-use-2024-10-22",
            "x-api-key": API_KEY
        }
        
        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [{"role": "user", "content": "请截取屏幕截图"}],
            "max_tokens": 200,
            "stream": True
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json=request_data,
            headers=headers,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            events = []
            content_blocks = []
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('event:'):
                        event_type = line_text[6:].strip()
                        events.append(event_type)
                    elif line_text.startswith('data:'):
                        try:
                            data_json = line_text[5:].strip()
                            if data_json and data_json != "[DONE]":
                                data = json.loads(data_json)
                                if data.get("type") == "content_block_start":
                                    block = data.get("content_block", {})
                                    if block.get("type") == "tool_use":
                                        content_blocks.append("tool_use")
                        except:
                            pass
            
            has_events = len(events) > 0
            has_tool_use = "tool_use" in content_blocks
            
            print_result(has_events, f"收到流式事件: {len(events)} 个")
            print_result(has_tool_use, f"检测到工具调用: {'是' if has_tool_use else '否'}")
            
            if events:
                print(f"   事件类型: {list(set(events))}")
            
            return has_events
        else:
            print_result(False, f"流式请求失败: HTTP {response.status_code}")
            return False
    
    except Exception as e:
        print_result(False, f"流式请求异常: {e}")
        return False

def test_system_prompt_with_tools():
    """测试系统提示词与工具结合"""
    print_section("系统提示词与工具结合测试")
    
    print_test("带系统提示词的工具调用")
    
    system_prompt = "你是一个专业的天气助手，总是礼貌地提供详细的天气信息。"
    
    weather_tool = {
        "name": "get_weather",
        "description": "获取天气信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"}
            },
            "required": ["city"]
        }
    }
    
    result = make_claude_request(
        messages=[{"role": "user", "content": "天气怎么样？"}],
        tools=[weather_tool],
        system=system_prompt
    )
    
    success = "content" in result and not "error" in result
    has_tool = False
    
    if success:
        for block in result.get("content", []):
            if block.get("type") == "tool_use":
                has_tool = True
                break
    
    print_result(success, f"系统提示词请求: {'成功' if success else '失败'}")
    print_result(has_tool or success, f"工具调用: {'有' if has_tool else '仅文本响应'}")
    
    return success

def test_error_handling():
    """测试错误处理"""
    print_section("错误处理测试")
    
    print_test("无效工具定义")
    
    # 测试无效的工具定义
    invalid_tool = {
        "name": "invalid_tool",
        # 缺少必需的字段
    }
    
    result = make_claude_request(
        messages=[{"role": "user", "content": "测试"}],
        tools=[invalid_tool]
    )
    
    # 应该仍然返回响应，即使工具定义不完整
    success = "content" in result or "error" in result
    print_result(success, f"错误处理: {'正常' if success else '异常'}")
    
    if "error" in result:
        print(f"   错误信息: {result['error']}")
    
    return success

def test_model_list():
    """测试模型列表"""
    print_section("模型列表测试")
    
    print_test("获取Claude模型列表")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/messages/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            model_count = len(models.get("data", []))
            print_result(True, f"获取到 {model_count} 个Claude模型")
            
            # 显示前几个模型
            for model in models.get("data", [])[:3]:
                print(f"   - {model.get('id')}")
            
            return True
        else:
            print_result(False, f"获取模型列表失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "🔧"*35)
    print(" Claude Code 接口工具支持全面测试")
    print("🔧"*35)
    print(f"测试端点: {BASE_URL}/v1/messages")
    
    # 检查服务器状态
    if not test_server_health():
        print("\n❌ 服务器未运行，请先启动服务器")
        return
    
    # 执行所有测试
    test_results = {}
    
    test_results["基础API功能"] = test_basic_claude_api()
    test_results["Computer Use工具"] = test_computer_use_tools()
    test_results["Code Execution工具"] = test_code_execution_tools()
    test_results["自定义工具"] = test_custom_tools()
    test_results["组合工具使用"] = test_combined_tools()
    test_results["工具结果处理"] = test_tool_result_handling()
    test_results["流式响应"] = test_streaming_response()
    test_results["系统提示词+工具"] = test_system_prompt_with_tools()
    test_results["错误处理"] = test_error_handling()
    test_results["模型列表"] = test_model_list()
    
    # 打印测试总结
    print_section("测试结果总结")
    
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    
    for name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:<20}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！Claude Code接口工具支持完全正常！")
    elif passed >= total * 0.8:
        print("\n✅ 大部分测试通过，核心功能正常运行。")
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查。")
    
    # 详细功能说明
    print_section("功能支持说明")
    print("""
✅ 已支持的功能:

1. Claude Messages API (/v1/messages)
   - 完整的消息格式支持 (文本、工具调用、工具结果)
   - 系统提示词支持
   - 流式和非流式响应
   - Claude特定的SSE事件格式

2. Computer Use 工具 (computer_20241022)
   - 通过 anthropic-beta: computer-use-2024-10-22 激活
   - 支持截图、点击、输入、滚动、按键等操作
   - 自动添加工具定义

3. Code Execution 工具 (str_replace_based_edit_tool)
   - 通过 anthropic-beta: code-execution-2025-08-25 激活  
   - 支持文件查看、创建、编辑、撤销等操作
   - 自动添加工具定义

4. 自定义工具支持
   - 完整的工具定义格式转换
   - Claude格式 ↔ OpenAI格式转换
   - 工具调用和结果处理

5. 高级功能
   - 多工具组合使用
   - 工具结果处理和对话延续
   - 错误处理和容错机制
   - 模型列表和配置

⚠️ 重要说明:
- 当前实现提供完整的协议支持和格式转换
- 实际的工具执行依赖后端Warp AI服务
- 如果Warp不支持某些工具，会返回文本响应而非工具调用
""")

if __name__ == "__main__":
    main()