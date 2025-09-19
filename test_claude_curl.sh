#!/bin/bash

# Claude API 集成测试脚本 (curl 版本)

echo "🚀 Claude API 集成测试 (curl)"
echo "=========================================="

# 检查服务器健康状态
echo "🏥 检查服务器健康状态..."
if ! curl -s http://localhost:28889/healthz > /dev/null; then
    echo "❌ OpenAI 服务器 (28889) 未运行"
    exit 1
fi

if ! curl -s http://localhost:28888/healthz > /dev/null; then
    echo "❌ Bridge 服务器 (28888) 未运行"
    exit 1
fi

echo "✅ 服务器健康状态正常"

# 测试1: 基本 Claude Messages API
echo ""
echo "🧪 测试1: 基本 Claude Messages API"
echo "------------------------------------------"

curl -X POST http://localhost:28889/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [
      {
        "role": "user",
        "content": "Hello! Please say hi back in one sentence."
      }
    ]
  }' | python3 -m json.tool

echo ""
echo "✅ 基本测试完成"

# 测试2: 带系统提示的测试
echo ""
echo "🧪 测试2: 带系统提示的 Claude Messages API"
echo "------------------------------------------"

curl -X POST http://localhost:28889/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-opus-20240229",
    "max_tokens": 80,
    "system": "You are a helpful assistant. Always be very concise.",
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of Japan?"
      }
    ]
  }' | python3 -m json.tool

echo ""
echo "✅ 系统提示测试完成"

# 测试3: 流式响应测试
echo ""
echo "🧪 测试3: 流式 Claude Messages API"
echo "------------------------------------------"

echo "📡 流式响应 (前10行):"
curl -X POST http://localhost:28889/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 150,
    "stream": true,
    "messages": [
      {
        "role": "user",
        "content": "Count from 1 to 5 slowly."
      }
    ]
  }' | head -20

echo ""
echo "✅ 流式测试完成"

# 测试4: 多轮对话测试
echo ""
echo "🧪 测试4: 多轮对话 Claude Messages API"
echo "------------------------------------------"

curl -X POST http://localhost:28889/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022", 
    "max_tokens": 60,
    "messages": [
      {
        "role": "user",
        "content": "What is 5+3?"
      },
      {
        "role": "assistant",
        "content": "5+3 equals 8."
      },
      {
        "role": "user", 
        "content": "What about 8+2?"
      }
    ]
  }' | python3 -m json.tool

echo ""
echo "✅ 多轮对话测试完成"

echo ""
echo "🎉 所有 curl 测试完成!"
echo "=========================================="

# 测试模型列表
echo ""
echo "📋 支持的模型列表:"
curl -s http://localhost:28889/v1/models | python3 -c "
import json, sys
data = json.load(sys.stdin)
models = data.get('data', [])
claude_models = [m for m in models if 'claude' in m.get('id', '').lower()]
print('Claude 相关模型:')
for model in claude_models:
    print(f'  - {model[\"id\"]} ({model.get(\"display_name\", \"N/A\")})')
"

echo ""
echo "💡 使用提示:"
echo "  - 所有测试使用 Claude API 标准格式"
echo "  - 支持流式和非流式响应"
echo "  - 支持系统提示和多轮对话"
echo "  - 模型名称会自动映射到内部模型"