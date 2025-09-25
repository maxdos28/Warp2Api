# Claude API 兼容性说明

本项目已添加 Claude API 兼容性支持，实现了 `/v1/messages` 端点，支持流式和非流式响应。

## 认证

使用 API Token: `123456`

支持两种认证方式：
1. Header: `x-api-key: 123456`
2. Header: `Authorization: Bearer 123456`

## 可用端点

### 1. 消息创建 - POST /v1/messages

**请求示例（非流式）:**
```bash
curl -X POST http://127.0.0.1:28888/v1/messages \
  -H "x-api-key: 123456" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-4.1-opus",
    "max_tokens": 1024,
    "messages": [
      {
        "role": "user",
        "content": "Hello! How are you?"
      }
    ]
  }'
```

**请求示例（流式）:**
```bash
curl -X POST http://127.0.0.1:28888/v1/messages \
  -H "x-api-key: 123456" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-4.1-opus",
    "max_tokens": 1024,
    "stream": true,
    "messages": [
      {
        "role": "user",
        "content": "请介绍一下人工智能"
      }
    ]
  }'
```

**带系统提示的请求:**
```bash
curl -X POST http://127.0.0.1:28888/v1/messages \
  -H "x-api-key: 123456" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-4.1-opus",
    "max_tokens": 1024,
    "system": "你是一个友善的助手",
    "messages": [
      {
        "role": "user",
        "content": "什么是机器学习？"
      }
    ]
  }'
```

### 2. 模型列表 - GET /v1/models

```bash
curl -X GET http://127.0.0.1:28888/v1/models \
  -H "x-api-key: 123456"
```

## 支持的参数

- `model`: 模型名称（如 `claude-4.1-opus`）
- `max_tokens`: 最大输出 token 数（默认 4096）
- `messages`: 消息列表
- `system`: 系统提示（可选）
- `temperature`: 温度参数（可选）
- `top_p`: Top-p 采样参数（可选）
- `top_k`: Top-k 采样参数（可选）
- `stream`: 是否启用流式响应（默认 false）
- `tools`: 工具列表（可选）

## 响应格式

### 非流式响应
```json
{
  "id": "msg_123456",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello! I'm doing well, thank you for asking..."
    }
  ],
  "model": "claude-4.1-opus",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0
  }
}
```

### 流式响应
流式响应使用 Server-Sent Events (SSE) 格式，包含以下事件类型：
- `message_start`: 消息开始
- `content_block_start`: 内容块开始
- `content_block_delta`: 内容增量
- `content_block_stop`: 内容块结束
- `message_delta`: 消息元数据更新
- `message_stop`: 消息结束

## 测试

运行测试脚本验证功能：
```bash
python test_claude_api.py
```

## 启动服务器

```bash
# 启动主服务器（包含 Claude API 支持）
python server.py --port 28888

# 或者启动独立的 OpenAI/Claude 兼容服务器
python openai_compat.py --port 28889
```

## 模型映射

Claude API 请求会被转换为内部 protobuf 格式，支持的模型包括：
- `claude-4.1-opus`
- `claude-4.1-sonnet`
- `claude-4.1-haiku`

所有请求最终会通过 Warp API 进行处理。