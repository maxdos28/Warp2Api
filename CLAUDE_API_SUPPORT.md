# Claude API 支持说明

## ✨ 新增功能

Warp2Api 现在支持 **Claude Messages API** 标准格式！这意味着您可以使用任何支持 Claude API 的客户端直接连接到 Warp AI 服务。

## 🎯 支持的端点

### `/v1/messages`
- **方法**: POST
- **格式**: Claude Messages API 标准
- **功能**: 完整的 Claude API 兼容性

## 📋 支持的功能

### ✅ 已支持
- [x] 基本消息对话
- [x] 系统提示 (`system` 参数)
- [x] 多轮对话
- [x] 流式响应 (`stream: true`)
- [x] Token 限制 (`max_tokens`)
- [x] 模型选择和自动映射
- [x] 温度和其他参数
- [x] Claude 标准响应格式
- [x] Claude 流式事件格式

### 🔄 模型映射

Claude API 模型名称会自动映射到内部模型：

| Claude 模型 | 内部模型 |
|------------|----------|
| `claude-3-5-sonnet-20241022` | `claude-4-sonnet` |
| `claude-3-5-sonnet-20240620` | `claude-4-sonnet` |
| `claude-3-5-haiku-20241022` | `claude-4-sonnet` |
| `claude-3-opus-20240229` | `claude-4-opus` |
| `claude-3-sonnet-20240229` | `claude-4-sonnet` |
| `claude-3-haiku-20240307` | `claude-4-sonnet` |
| `claude-2.1` | `claude-4-opus` |
| `claude-2.0` | `claude-4-opus` |
| `claude-instant-1.2` | `claude-4-sonnet` |

## 🧪 测试方法

### 方法1: 使用测试脚本
```bash
# Linux/macOS
python3 test_claude_api.py
./test_claude_curl.sh

# Windows
python test_claude_api.py
test_claude_api.bat
```

### 方法2: 手动测试
```bash
curl -X POST http://localhost:28889/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1000,
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## 📊 响应格式

### 非流式响应
```json
{
  "id": "msg_01234567890abcdef",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello! How can I help you today?"
    }
  ],
  "model": "claude-3-5-sonnet-20241022",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 15
  }
}
```

### 流式响应
```
event: message_start
data: {"type": "message_start", "message": {...}}

event: content_block_start  
data: {"type": "content_block_start", "index": 0, "content_block": {...}}

event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hello"}}

event: content_block_stop
data: {"type": "content_block_stop", "index": 0}

event: message_stop
data: {"type": "message_stop"}
```

## 🔧 实现细节

### 核心文件
- `protobuf2openai/claude_models.py` - Claude API 数据模型
- `protobuf2openai/claude_converter.py` - 格式转换器
- `protobuf2openai/claude_router.py` - 路由处理器

### 转换流程
1. 接收 Claude API 请求
2. 转换为内部 OpenAI 格式
3. 使用现有的 Warp 处理管道
4. 转换响应为 Claude 格式
5. 返回标准 Claude API 响应

## 🎉 使用场景

现在您可以：
- 使用 Claude SDK 连接到 Warp AI
- 将现有的 Claude 应用迁移到 Warp AI
- 在同一个服务上同时支持 OpenAI 和 Claude 客户端
- 享受 Warp AI 的强大功能，同时保持 Claude API 的熟悉接口

## 🚀 快速开始

1. 启动服务器：
   ```bash
   ./start.sh  # Linux/macOS
   start.bat   # Windows
   ```

2. 测试 Claude API：
   ```bash
   curl -X POST http://localhost:28889/v1/messages \
     -H "Content-Type: application/json" \
     -d '{
       "model": "claude-3-5-sonnet-20241022",
       "max_tokens": 100,
       "messages": [
         {"role": "user", "content": "Hello Claude API!"}
       ]
     }'
   ```

3. 享受双 API 兼容性！

---

**注意**: 这个实现完全向后兼容，现有的 OpenAI API 调用不会受到任何影响。