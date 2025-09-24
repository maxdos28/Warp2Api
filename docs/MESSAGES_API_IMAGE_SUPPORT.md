# /v1/messages 接口图片支持文档

## 概述

本项目现已支持两种 API 格式的图片传入：

1. **OpenAI Chat Completions API** (`/v1/chat/completions`) - 已有实现
2. **Anthropic Messages API** (`/v1/messages`) - 新增实现

两种接口都完整支持图片传入功能，可以处理文本和图片的多模态输入。

## 支持的接口

### 1. OpenAI 格式 (`/v1/chat/completions`)

**端点**: `POST /v1/chat/completions`

**图片格式**:
```json
{
  "model": "claude-3-sonnet",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "描述这张图片"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,{base64_encoded_image}"
          }
        }
      ]
    }
  ]
}
```

### 2. Anthropic 格式 (`/v1/messages`)

**端点**: `POST /v1/messages`

**图片格式**:
```json
{
  "model": "claude-3-sonnet-20240229",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "描述这张图片"
        },
        {
          "type": "image",
          "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": "{base64_encoded_image}"
          }
        }
      ]
    }
  ],
  "max_tokens": 1024
}
```

## 功能特性

### ✅ 已实现功能

1. **多种图片格式支持**
   - PNG (`image/png`)
   - JPEG (`image/jpeg`)
   - GIF (`image/gif`)
   - WebP (`image/webp`)

2. **灵活的内容组合**
   - 纯文本消息
   - 单张图片 + 文本
   - 多张图片 + 文本
   - 文本和图片交替排列

3. **完整的数据转换**
   - Base64 解码
   - MIME 类型识别
   - Protobuf 格式转换
   - 图片数据传递到 Warp API

4. **系统提示支持**
   - OpenAI: 通过 `role: "system"` 消息
   - Anthropic: 通过 `system` 参数

5. **流式响应**
   - 两种 API 都支持 `stream: true` 参数

## 实现细节

### 数据处理流程

1. **接收请求**
   - 解析 JSON 请求体
   - 验证消息格式

2. **图片提取**
   - 识别图片内容块
   - 解析 data URL 或 base64 数据
   - 提取 MIME 类型

3. **格式转换**
   - OpenAI → Warp protobuf
   - Anthropic → Warp protobuf
   - 图片数据 → 二进制格式

4. **Protobuf 封装**
   - 文本内容 → `user_query.query`
   - 图片数据 → `input.context.images`
   - 系统提示 → `referenced_attachments`

5. **发送到 Warp API**
   - 构建完整的请求包
   - 通过 bridge 转发

### 关键文件

- `/workspace/protobuf2openai/router.py` - OpenAI 格式路由
- `/workspace/protobuf2openai/messages_router.py` - Anthropic 格式路由
- `/workspace/protobuf2openai/helpers.py` - 图片处理辅助函数
- `/workspace/protobuf2openai/packets.py` - Protobuf 数据包构建

## 使用示例

### Python 示例

```python
import requests
import base64

# 读取图片
with open("image.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

# OpenAI 格式
openai_request = {
    "model": "claude-3-sonnet",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"}
            }
        ]
    }]
}

# Anthropic 格式
anthropic_request = {
    "model": "claude-3-sonnet-20240229",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_base64
                }
            }
        ]
    }],
    "max_tokens": 1024
}

# 发送请求
response_openai = requests.post(
    "http://localhost:28889/v1/chat/completions",
    json=openai_request
)

response_anthropic = requests.post(
    "http://localhost:28889/v1/messages",
    json=anthropic_request
)
```

### cURL 示例

```bash
# OpenAI 格式
curl -X POST http://localhost:28889/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-sonnet",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image"},
        {
          "type": "image_url",
          "image_url": {"url": "data:image/png;base64,iVBORw0KG..."}
        }
      ]
    }]
  }'

# Anthropic 格式
curl -X POST http://localhost:28889/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-sonnet-20240229",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image"},
        {
          "type": "image",
          "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": "iVBORw0KG..."
          }
        }
      ]
    }],
    "max_tokens": 1024
  }'
```

## 测试

运行测试脚本验证功能：

```bash
# 启动服务器
python openai_compat.py --port 28889

# 运行测试
python test_messages_api.py

# 或指定自定义服务器地址
python test_messages_api.py http://localhost:8000
```

## 注意事项

1. **图片大小限制**
   - 建议图片大小不超过 10MB
   - 大图片可能导致请求超时

2. **Base64 编码**
   - OpenAI 格式需要完整的 data URL
   - Anthropic 格式只需要纯 base64 字符串

3. **MIME 类型**
   - 必须正确指定图片的 MIME 类型
   - 支持的类型: image/png, image/jpeg, image/gif, image/webp

4. **性能考虑**
   - 多张图片会增加处理时间
   - 建议使用适当压缩的图片

## 故障排查

### 常见问题

1. **图片无法解析**
   - 检查 base64 编码是否正确
   - 验证 MIME 类型是否匹配实际图片格式

2. **请求超时**
   - 减小图片大小
   - 检查网络连接
   - 增加超时时间

3. **格式错误**
   - 确保使用正确的 API 格式
   - 检查 JSON 结构是否完整

### 日志查看

启用详细日志：
```python
# 在 protobuf2openai/logging.py 中设置日志级别
logger.setLevel(logging.DEBUG)
```

查看日志文件：
```bash
tail -f warp_server.log
```

## 总结

本项目现已完整支持图片传入功能：

- ✅ `/v1/chat/completions` - OpenAI 格式（已有）
- ✅ `/v1/messages` - Anthropic 格式（新增）
- ✅ 多种图片格式支持
- ✅ 灵活的内容组合
- ✅ 完整的数据转换
- ✅ 流式响应支持

两种 API 格式都经过测试验证，可以正常处理包含图片的多模态输入。