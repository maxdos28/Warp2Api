# Claude API 实现指南

## 概述

本文档详细说明了在 Warp2Api 中实现 Claude Messages API 兼容性和 Claude Code 工具支持所需的工作。

## 已完成的实现

### 1. Claude Messages API 格式支持 ✅

我们已经实现了完整的 Claude Messages API (`/v1/messages`) 端点支持：

#### 文件结构
- `protobuf2openai/claude_models.py` - Claude 数据模型定义
- `protobuf2openai/claude_router.py` - Claude API 路由处理
- `protobuf2openai/claude_sse.py` - Claude SSE 流式响应处理

#### 主要功能
- **请求格式转换**：将 Claude Messages API 格式转换为内部 Warp 格式
- **系统提示词处理**：Claude 的 `system` 参数正确转换为 OpenAI 格式
- **消息格式兼容**：支持文本和复杂内容块（text, image, tool_use, tool_result）
- **模型映射**：自动将 Claude 模型名称映射到 Warp 支持的模型

### 2. Claude 工具调用支持 ✅

实现了完整的 Claude 工具调用格式：

#### 工具定义格式
```json
{
  "tools": [{
    "name": "tool_name",
    "description": "工具描述",
    "input_schema": {
      "type": "object",
      "properties": {...}
    }
  }]
}
```

#### 工具使用消息格式
```json
{
  "role": "assistant",
  "content": [{
    "type": "tool_use",
    "id": "tool_call_id",
    "name": "tool_name",
    "input": {...}
  }]
}
```

#### 工具结果消息格式
```json
{
  "role": "user",
  "content": [{
    "type": "tool_result",
    "tool_use_id": "tool_call_id",
    "content": "结果内容"
  }]
}
```

### 3. Claude Computer Use 工具 ✅

支持 Claude 的 Computer Use 功能：

#### 激活方式
在请求头中添加：
```
anthropic-beta: computer-use-2024-10-22
```

#### 内置工具
- **computer_20241022**：屏幕截图、鼠标点击、键盘输入等操作
  - `screenshot` - 截取屏幕
  - `click` - 鼠标点击
  - `type` - 键盘输入
  - `scroll` - 滚动
  - `key` - 按键

### 4. Claude Code Execution 工具 ✅

支持代码执行功能：

#### 激活方式
在请求头中添加：
```
anthropic-beta: code-execution-2025-08-25
```

#### 内置工具
- **str_replace_based_edit_tool**：文件编辑工具
  - `view` - 查看文件
  - `create` - 创建文件
  - `str_replace` - 字符串替换
  - `undo_edit` - 撤销编辑

### 5. Claude 特定请求头支持 ✅

完整支持 Claude API 的特定请求头：

- `anthropic-version`: API 版本（如 "2023-06-01"）
- `anthropic-beta`: Beta 功能标识
- `x-api-key`: API 密钥（我们的服务器不强制验证）

### 6. Claude SSE 流式响应格式 ✅

实现了 Claude 特定的 SSE 事件格式：

```
event: message_start
data: {"type": "message_start", "message": {...}}

event: content_block_start
data: {"type": "content_block_start", "index": 0, "content_block": {...}}

event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {...}}

event: content_block_stop
data: {"type": "content_block_stop", "index": 0}

event: message_delta
data: {"type": "message_delta", "delta": {...}}

event: message_stop
data: {"type": "message_stop"}
```

### 7. 模型映射 ✅

支持以下 Claude 模型：

- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
- `claude-3-5-sonnet-20241022`
- `claude-3-5-sonnet-20240620`

同时保持与现有模型名称的兼容：
- `claude-4-sonnet` → `claude-3-5-sonnet-20241022`
- `claude-4-opus` → `claude-3-opus-20240229`
- `claude-4.1-opus` → `claude-3-opus-20240229`

## 使用方法

### 1. 使用 Anthropic Python SDK

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:28889/v1",
    api_key="dummy",
)

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
```

### 2. 使用 cURL

```bash
curl -X POST http://localhost:28889/v1/messages \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

### 3. 使用工具

```python
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=300,
    messages=[
        {"role": "user", "content": "What's the weather?"}
    ],
    tools=[{
        "name": "get_weather",
        "description": "Get weather information",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }]
)
```

### 4. 使用 Computer Use

```python
client = Anthropic(
    base_url="http://localhost:28889/v1",
    api_key="dummy",
    default_headers={
        "anthropic-beta": "computer-use-2024-10-22"
    }
)

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=200,
    messages=[
        {"role": "user", "content": "Take a screenshot"}
    ]
)
```

## 测试

运行测试脚本验证 Claude API 兼容性：

```bash
# 运行完整测试
python test_claude_api.py

# 仅列出可用模型
python test_claude_api.py --models-only

# 测试非流式响应
python test_claude_api.py --no-stream
```

## 架构设计

### 请求流程

1. **接收请求**：Claude API 端点接收 Messages API 格式的请求
2. **格式转换**：将 Claude 格式转换为 OpenAI 格式
3. **工具处理**：根据 beta 头添加内置工具
4. **发送到 Warp**：将转换后的请求发送到 Warp 服务
5. **响应转换**：将 Warp 响应转换回 Claude 格式
6. **流式处理**：对于流式请求，转换为 Claude SSE 格式

### 关键组件

- **ClaudeMessagesRequest**：Claude 请求数据模型
- **ClaudeMessage**：Claude 消息格式
- **ContentBlock**：支持多种内容类型（文本、图像、工具使用等）
- **claude_router**：处理 Claude API 路由
- **stream_claude_sse**：处理 Claude 格式的流式响应

## 注意事项

1. **API Key**：我们的服务器不验证 API key，但某些客户端可能需要提供
2. **max_tokens**：Claude API 要求必须提供 `max_tokens` 参数
3. **系统提示词**：Claude 使用独立的 `system` 参数，而非系统消息
4. **Beta 功能**：某些功能需要特定的 `anthropic-beta` 头
5. **模型名称**：确保使用正确的 Claude 模型名称格式

## 未来改进

1. **完整的错误处理**：改进错误消息和异常处理
2. **令牌计数**：实现准确的输入/输出令牌计数
3. **更多工具支持**：根据需要添加更多内置工具
4. **性能优化**：优化格式转换和流式处理
5. **监控和日志**：添加更详细的监控和日志记录

## 参考资源

- [Anthropic API 文档](https://docs.anthropic.com/)
- [Claude Messages API](https://docs.anthropic.com/claude/reference/messages)
- [Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
- [Computer Use](https://docs.anthropic.com/claude/docs/computer-use)
- [Code Execution](https://docs.anthropic.com/claude/docs/code-execution)