# Claude API 工具支持修复说明

## 问题描述

`/v1/messages` 接口在处理 Claude Code (Cline) 等工具调用时存在以下问题：

1. **工具调用未正确返回**：响应中缺少 `tool_use` 类型的内容块
2. **工具结果未正确处理**：请求中的 `tool_result` 消息未正确转换
3. **模型定义不完整**：`ClaudeContent` 模型缺少工具相关字段

## 解决方案

### 1. 扩展 ClaudeContent 模型

在 `protobuf2openai/claude_models.py` 中添加了工具支持：

```python
class ClaudeContent(BaseModel):
    type: Literal["text", "image", "image_url", "tool_use", "tool_result"]
    # 工具调用字段
    id: Optional[str] = None  # tool_use ID
    name: Optional[str] = None  # 工具名称
    input: Optional[Dict[str, Any]] = None  # 工具参数
    # 工具结果字段
    tool_use_id: Optional[str] = None  # 关联的 tool_use ID
    content: Optional[Union[str, List[Dict[str, Any]]]] = None  # 工具结果内容
    is_error: Optional[bool] = None  # 是否执行失败
```

### 2. 更新响应转换逻辑

在 `protobuf2openai/claude_converter.py` 中：

- **添加工具调用转换**：将从 Warp 响应中提取的工具调用转换为 Claude `tool_use` 内容块
- **处理工具结果**：在请求转换中正确处理 `tool_result` 消息

### 3. 修复响应处理

在 `protobuf2openai/claude_router.py` 中：

- **提取工具调用**：从 `parsed_events` 中提取 `tool_call` 信息
- **传递给转换器**：将工具调用列表传递给 `openai_to_claude_response` 函数

## 主要代码更改

### claude_converter.py

```python
def openai_to_claude_response(
    openai_response: Dict[str, Any], 
    claude_model: str,
    request_id: str,
    tool_calls: List[Dict[str, Any]] = None  # 新增参数
) -> ClaudeMessagesResponse:
    # ... 
    # 添加工具调用转换逻辑
    if tool_calls:
        for tool_call in tool_calls:
            tool_use_block = ClaudeContent(
                type="tool_use",
                id=tool_call.get("id"),
                name=function.get("name"),
                input=json.loads(function.get("arguments"))
            )
            content_blocks.append(tool_use_block)
```

### claude_router.py

```python
# 提取工具调用
tool_calls = []
for ev in parsed_events:
    # ... 解析事件
    tc = message.get("tool_call") or message.get("toolCall") or {}
    call_mcp = tc.get("call_mcp_tool") or tc.get("callMcpTool") or {}
    if call_mcp.get("name"):
        tool_calls.append({
            "id": tc.get("tool_call_id"),
            "type": "function",
            "function": {
                "name": call_mcp.get("name"),
                "arguments": json.dumps(call_mcp.get("args"))
            }
        })

# 传递给转换器
claude_response = openai_to_claude_response(
    openai_response, req.model, request_id, tool_calls
)
```

## 测试方法

### 1. 运行测试脚本

```bash
# 测试基本工具支持
python test_claude_tool_support.py

# 测试 Cline 兼容性
python test_cline_tool_compatibility.py
```

### 2. 手动测试

发送包含工具调用的请求：

```bash
curl -X POST http://localhost:28889/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1000,
    "messages": [
      {
        "role": "user",
        "content": "Use a tool to get the current time"
      }
    ]
  }'
```

## 兼容性

✅ **支持的工具格式**：
- Claude API 标准 `tool_use` 和 `tool_result` 内容块
- Cline (Claude Code) 工具调用格式
- 流式响应中的工具事件

✅ **与现有功能兼容**：
- 文本消息处理
- 图片支持
- 系统提示
- 流式响应

## 注意事项

1. **工具 ID 格式**：Cline 使用 `toolu_` 前缀的 ID，系统会自动处理
2. **参数序列化**：工具参数会自动在 JSON 字符串和对象之间转换
3. **错误处理**：工具执行失败时会返回相应的错误信息

## 后续优化建议

1. **添加工具定义支持**：支持在请求中定义可用工具列表
2. **增强错误处理**：更详细的工具执行错误信息
3. **工具结果验证**：验证工具结果格式的正确性
4. **性能优化**：缓存工具调用结果以减少重复执行
