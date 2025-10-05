# 多模态支持文档

Warp2Api 现已支持多模态功能，包括图片识别、文件附件等。

## 🎨 功能特性

### ✅ 已支持

- **图片识别（Vision）**
  - 支持 HTTP/HTTPS URL 图片
  - 支持 Base64 编码图片（data URL 格式）
  - 自动下载远程图片并转换为 base64
  - 多张图片同时处理
  - 图片格式验证和大小限制

- **支持的图片格式**
  - JPEG/JPG
  - PNG
  - GIF
  - WebP
  - BMP
  - TIFF

### ⚙️ 配置选项

可以通过环境变量配置多模态功能：

```bash
# 启用/禁用多模态支持（默认：启用）
W2A_ENABLE_MULTIMODAL=true

# 启用/禁用图片下载（默认：启用）
W2A_ENABLE_IMAGE_DOWNLOAD=true

# 最大图片大小（MB，默认：20）
W2A_MAX_IMAGE_SIZE_MB=20

# 图片下载超时（秒，默认：30）
W2A_IMAGE_DOWNLOAD_TIMEOUT=30

# 最大并发下载数（默认：5）
W2A_MAX_CONCURRENT_DOWNLOADS=5

# 自动调整大图片尺寸（默认：禁用）
W2A_AUTO_RESIZE_IMAGES=false

# 最大图片尺寸（像素，默认：2048）
W2A_MAX_IMAGE_DIMENSION=2048

# 启用图片缓存（默认：禁用）
W2A_ENABLE_IMAGE_CACHE=false

# 图片缓存目录（默认：.cache/images）
W2A_IMAGE_CACHE_DIR=.cache/images

# 缓存最大大小（MB，默认：100）
W2A_IMAGE_CACHE_MAX_SIZE_MB=100
```

## 📖 使用示例

### Python SDK

#### 示例 1: 单张图片 + 文本

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="0000"  # 任意值
)

response = client.chat.completions.create(
    model="claude-4-sonnet",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "这张图片里有什么？"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg"
                    }
                }
            ]
        }
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

#### 示例 2: Base64 编码图片

```python
# Base64 data URL 格式
image_data_url = "data:image/png;base64,iVBORw0KGgo..."

response = client.chat.completions.create(
    model="claude-4-sonnet",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "分析这张图片"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url
                    }
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
```

#### 示例 3: 多张图片对比

```python
response = client.chat.completions.create(
    model="claude-4-sonnet",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "比较这两张图片的异同："
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image1.jpg"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image2.jpg"
                    }
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
```

#### 示例 4: 详细控制（detail 参数）

```python
response = client.chat.completions.create(
    model="claude-4-sonnet",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "详细描述这张图片"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "high"  # low, high, auto
                    }
                }
            ]
        }
    ]
)
```

### cURL

```bash
curl -X POST http://localhost:28889/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 0000" \
  -d '{
    "model": "claude-4-sonnet",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "这张图片里有什么？"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "https://example.com/image.jpg"
            }
          }
        ]
      }
    ],
    "stream": true
  }'
```

### JavaScript/Node.js

```javascript
const OpenAI = require('openai');

const client = new OpenAI({
  baseURL: 'http://localhost:28889/v1',
  apiKey: '0000'
});

async function analyzeImage() {
  const response = await client.chat.completions.create({
    model: 'claude-4-sonnet',
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'text',
            text: '描述这张图片'
          },
          {
            type: 'image_url',
            image_url: {
              url: 'https://example.com/image.jpg'
            }
          }
        ]
      }
    ],
    stream: true
  });

  for await (const chunk of response) {
    process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
}

analyzeImage();
```

## 🧪 测试

运行测试脚本验证多模态功能：

```bash
# 确保服务器已启动
./start.sh

# 运行多模态测试
python test_multimodal.py
```

测试包括：
1. ✅ 图片 URL 下载和识别
2. ✅ Base64 编码图片处理
3. ✅ 多张图片同时处理
4. ✅ 纯文本（回归测试）

## 🔍 工作原理

1. **接收请求**：客户端发送包含图片的 OpenAI 格式请求
2. **内容解析**：`normalize_content_to_list()` 识别文本和图片段落
3. **图片处理**：
   - 如果是 URL：下载图片并验证
   - 如果是 base64：直接验证
   - 转换为统一的 base64 data URL 格式
4. **附件构建**：图片作为 `referenced_attachments` 添加到 Warp 请求
5. **发送到 Warp**：protobuf 编码后发送到 Warp AI 服务
6. **接收响应**：Warp AI 模型分析图片并返回结果

## 📊 性能考虑

- **图片大小限制**：默认最大 20MB，可通过环境变量调整
- **下载超时**：默认 30 秒，可配置
- **并发限制**：同时处理多张图片时有并发控制
- **格式验证**：自动检查图片格式和魔数
- **错误处理**：图片处理失败不会影响整体请求

## ⚠️ 注意事项

1. **模型支持**：
   - ✅ `claude-4-sonnet` - 推荐
   - ✅ `claude-4-opus`
   - ✅ `claude-4.1-opus`
   - ✅ `gemini-2.5-pro`
   - ✅ `gpt-5`
   - ✅ `gpt-4o`
   - ❌ `gpt-5 (high reasoning)` - 不支持 vision

2. **网络要求**：
   - 下载远程图片需要网络连接
   - 确保防火墙允许出站 HTTP/HTTPS 请求
   - 建议使用 base64 格式避免网络问题

3. **隐私和安全**：
   - 远程图片会被下载到服务器
   - 图片数据会随请求发送到 Warp AI 服务
   - 敏感图片建议使用私有部署或禁用图片下载

4. **成本考虑**：
   - 图片识别可能消耗更多 token
   - 大图片会增加请求大小和处理时间

## 🐛 故障排除

### 问题 1: 图片无法加载

```
Failed to process image: Failed to download image: HTTP 404
```

**解决方案**：
- 检查图片 URL 是否正确
- 确认图片可公开访问
- 尝试使用 base64 编码格式

### 问题 2: 图片太大

```
Image size 25.3MB exceeds maximum 20MB
```

**解决方案**：
```bash
# 调整最大图片大小
export W2A_MAX_IMAGE_SIZE_MB=30
./start.sh
```

### 问题 3: 下载超时

```
Timeout downloading image from https://...
```

**解决方案**：
```bash
# 增加下载超时时间
export W2A_IMAGE_DOWNLOAD_TIMEOUT=60
./start.sh
```

### 问题 4: 模型不支持图片

```
Model does not support vision
```

**解决方案**：
- 切换到支持 vision 的模型（如 `claude-4-sonnet`）
- 查看支持的模型列表：`http://localhost:28889/v1/models`

### 问题 5: 图片格式不支持

```
Unsupported image format: image/svg+xml
```

**解决方案**：
- 转换图片为支持的格式（JPEG, PNG, GIF, WebP, BMP, TIFF）
- 或将图片内容转换为文本描述

## 📚 相关文档

- [OpenAI Vision API 文档](https://platform.openai.com/docs/guides/vision)
- [Warp AI 模型列表](http://localhost:28889/v1/models)
- [故障排除指南](TROUBLESHOOTING.md)

## 🔮 未来计划

- [ ] 支持图片压缩和自动调整大小
- [ ] 支持本地文件路径
- [ ] 图片缓存机制
- [ ] 批量图片处理优化
- [ ] 支持更多文件类型（PDF, 文档等）
- [ ] 图片 OCR 预处理
- [ ] 图片元数据提取
