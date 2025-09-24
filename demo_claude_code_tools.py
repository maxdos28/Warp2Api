#!/usr/bin/env python3
"""
Claude Code 工具演示
展示 Computer Use 和 Code Execution 工具的使用
"""

import json
import subprocess
import time

def print_section(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def run_api_call(endpoint, headers, data):
    """执行 API 调用并返回格式化的结果"""
    headers_str = " ".join([f'-H "{k}: {v}"' for k, v in headers.items()])
    
    cmd = f'''curl -s -X POST http://localhost:28889{endpoint} \
      {headers_str} \
      -d '{json.dumps(data)}' '''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}

def demo_openai_tools():
    """演示 OpenAI API 格式的工具调用"""
    print_section("OpenAI API 工具调用演示")
    
    # 自定义工具
    response = run_api_call(
        "/v1/chat/completions",
        {
            "Content-Type": "application/json",
            "Authorization": "Bearer 0000"
        },
        {
            "model": "claude-4-sonnet",
            "messages": [
                {"role": "user", "content": "What's the weather in Beijing and Tokyo?"}
            ],
            "tools": [{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "City name"}
                        },
                        "required": ["city"]
                    }
                }
            }],
            "stream": False
        }
    )
    
    print("\n📤 请求: 查询北京和东京的天气")
    print("📥 响应:")
    
    if "choices" in response:
        message = response["choices"][0]["message"]
        if "tool_calls" in message:
            print("  ✅ 检测到工具调用:")
            for tool_call in message["tool_calls"]:
                func = tool_call["function"]
                print(f"    - {func['name']}: {func['arguments']}")
        else:
            print(f"  文本响应: {message.get('content', '')[:100]}")
    else:
        print(f"  错误: {response}")

def demo_claude_computer_use():
    """演示 Claude Computer Use 工具"""
    print_section("Claude Computer Use 工具演示")
    
    response = run_api_call(
        "/v1/messages",
        {
            "Content-Type": "application/json",
            "Authorization": "Bearer 0000",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "computer-use-2024-10-22"
        },
        {
            "model": "claude-4-sonnet",
            "messages": [
                {"role": "user", "content": "Take a screenshot of the current screen"}
            ],
            "max_tokens": 200,
            "stream": False
        }
    )
    
    print("\n📤 请求: 截取当前屏幕")
    print("📥 响应:")
    
    if "content" in response:
        for block in response["content"]:
            if block["type"] == "text":
                print(f"  文本: {block['text'][:100]}...")
            elif block["type"] == "tool_use":
                print(f"  ✅ 工具调用:")
                print(f"    名称: {block['name']}")
                print(f"    ID: {block['id']}")
                print(f"    参数: {json.dumps(block['input'], ensure_ascii=False)}")
    else:
        print(f"  错误: {response}")

def demo_claude_code_execution():
    """演示 Claude Code Execution 工具"""
    print_section("Claude Code Execution 工具演示")
    
    response = run_api_call(
        "/v1/messages",
        {
            "Content-Type": "application/json",
            "Authorization": "Bearer 0000",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "code-execution-2025-08-25"
        },
        {
            "model": "claude-4-sonnet",
            "messages": [
                {"role": "user", "content": "Create a Python file called hello.py with a hello world program"}
            ],
            "max_tokens": 300,
            "stream": False
        }
    )
    
    print("\n📤 请求: 创建一个 hello.py 文件")
    print("📥 响应:")
    
    if "content" in response:
        for block in response["content"]:
            if block["type"] == "text":
                print(f"  文本: {block['text'][:100]}...")
            elif block["type"] == "tool_use":
                print(f"  ✅ 工具调用:")
                print(f"    名称: {block['name']}")
                print(f"    参数: {json.dumps(block['input'], ensure_ascii=False, indent=4)}")
    else:
        print(f"  错误: {response}")

def demo_combined_tools():
    """演示组合使用多个工具"""
    print_section("组合工具使用演示")
    
    response = run_api_call(
        "/v1/messages",
        {
            "Content-Type": "application/json",
            "Authorization": "Bearer 0000",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "computer-use-2024-10-22,code-execution-2025-08-25"
        },
        {
            "model": "claude-4-sonnet",
            "messages": [
                {"role": "user", "content": "Take a screenshot and save the timestamp to a file"}
            ],
            "max_tokens": 400,
            "stream": False
        }
    )
    
    print("\n📤 请求: 截图并保存时间戳到文件")
    print("📥 响应:")
    
    if "content" in response:
        tool_count = 0
        for block in response["content"]:
            if block["type"] == "text":
                print(f"  文本: {block['text'][:150]}...")
            elif block["type"] == "tool_use":
                tool_count += 1
                print(f"  ✅ 工具调用 #{tool_count}:")
                print(f"    名称: {block['name']}")
                if block['name'] == "computer_20241022":
                    print(f"    操作: 截屏")
                elif block['name'] == "str_replace_based_edit_tool":
                    print(f"    操作: 文件编辑")
                print(f"    参数: {json.dumps(block['input'], ensure_ascii=False)}")
    else:
        print(f"  错误: {response}")

def main():
    print("\n" + "🚀"*30)
    print(" Claude Code 工具完整演示")
    print("🚀"*30)
    
    # 检查服务器
    try:
        result = subprocess.run(
            "curl -s http://localhost:28889/healthz",
            shell=True, capture_output=True, text=True, timeout=5
        )
        if "ok" not in result.stdout:
            print("\n❌ 服务器未运行！请先启动服务器:")
            print("  source $HOME/.local/bin/env")
            print("  API_TOKEN=0000 uv run server.py &")
            print("  API_TOKEN=0000 uv run openai_compat.py &")
            return
    except:
        print("\n❌ 无法连接到服务器")
        return
    
    print("\n✅ 服务器正在运行")
    time.sleep(1)
    
    # 运行演示
    demo_openai_tools()
    demo_claude_computer_use()
    demo_claude_code_execution()
    demo_combined_tools()
    
    # 总结
    print_section("演示总结")
    print("""
✅ Claude Code 工具完全支持！

支持的功能:
1. OpenAI API 格式的工具调用
2. Claude Computer Use (computer_20241022)
   - 通过 anthropic-beta: computer-use-2024-10-22 激活
   - 支持截屏、点击、输入等操作
3. Claude Code Execution (str_replace_based_edit_tool)
   - 通过 anthropic-beta: code-execution-2025-08-25 激活
   - 支持文件查看、创建、编辑等操作
4. 组合使用多个工具

使用方式:
- OpenAI API: /v1/chat/completions
- Claude API: /v1/messages
- 认证: Authorization: Bearer 0000

工具的实际执行依赖 Warp AI 后端服务。
""")

if __name__ == "__main__":
    main()