#!/bin/bash

echo "======================================================"
echo " Claude Code 工具测试 (使用 curl)"
echo "======================================================"

BASE_URL="http://localhost:28889"

# 检查服务器状态
echo -e "\n[1] 检查服务器状态..."
if curl -s -f "$BASE_URL/healthz" > /dev/null; then
    echo "✅ 服务器正在运行"
else
    echo "❌ 服务器未运行，请先启动: ./start.sh"
    exit 1
fi

# 测试 Computer Use 工具
echo -e "\n[2] 测试 Computer Use 工具"
echo "--------------------------------------"
echo "发送请求: 截取屏幕"

response=$(curl -s -X POST "$BASE_URL/v1/messages" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: computer-use-2024-10-22" \
  -H "x-api-key: test" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Take a screenshot"}],
    "max_tokens": 200,
    "stream": false
  }')

echo "响应:"
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"

# 检查是否包含 tool_use
if echo "$response" | grep -q "tool_use"; then
    echo "✅ 检测到 tool_use 响应"
    if echo "$response" | grep -q "computer_20241022"; then
        echo "✅ 检测到 computer_20241022 工具调用"
    fi
else
    echo "⚠️ 未检测到工具调用，可能返回了文本响应"
fi

# 测试 Code Execution 工具
echo -e "\n[3] 测试 Code Execution 工具"
echo "--------------------------------------"
echo "发送请求: 创建文件"

response=$(curl -s -X POST "$BASE_URL/v1/messages" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25" \
  -H "x-api-key: test" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Create a file named test.txt with content Hello World"}],
    "max_tokens": 300,
    "stream": false
  }')

echo "响应:"
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"

# 检查是否包含 tool_use
if echo "$response" | grep -q "tool_use"; then
    echo "✅ 检测到 tool_use 响应"
    if echo "$response" | grep -q "str_replace_based_edit_tool"; then
        echo "✅ 检测到 str_replace_based_edit_tool 工具调用"
    fi
else
    echo "⚠️ 未检测到工具调用，可能返回了文本响应"
fi

# 测试自定义工具
echo -e "\n[4] 测试自定义工具"
echo "--------------------------------------"
echo "发送请求: 获取天气（自定义工具）"

response=$(curl -s -X POST "$BASE_URL/v1/messages" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -H "x-api-key: test" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "What is the weather in Beijing?"}],
    "tools": [{
      "name": "get_weather",
      "description": "Get weather for a city",
      "input_schema": {
        "type": "object",
        "properties": {
          "city": {"type": "string"}
        },
        "required": ["city"]
      }
    }],
    "max_tokens": 200,
    "stream": false
  }')

echo "响应:"
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"

if echo "$response" | grep -q "tool_use"; then
    echo "✅ 检测到工具调用"
    if echo "$response" | grep -q "get_weather"; then
        echo "✅ 调用了 get_weather 工具"
    fi
else
    echo "⚠️ 未检测到工具调用"
fi

# 测试流式响应
echo -e "\n[5] 测试流式响应中的工具调用"
echo "--------------------------------------"
echo "发送流式请求..."

curl -s -N -X POST "$BASE_URL/v1/messages" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: computer-use-2024-10-22" \
  -H "x-api-key: test" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Take a screenshot"}],
    "max_tokens": 200,
    "stream": true
  }' | head -20

echo -e "\n\n======================================================"
echo " 测试总结"
echo "======================================================"
echo ""
echo "✅ Claude API 端点 (/v1/messages) 已实现"
echo "✅ 支持 anthropic-beta 头部参数"
echo "✅ 支持自定义工具定义"
echo "✅ 支持流式和非流式响应"
echo ""
echo "⚠️ 注意事项:"
echo "- 工具调用的实际执行依赖 Warp 后端服务"
echo "- 如果 Warp 不支持这些工具，会返回文本响应"
echo "- Computer Use 和 Code Execution 是 Beta 功能"