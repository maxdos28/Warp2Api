# 多模态功能快速开始

## 🚀 3 分钟上手

### 1. 启动服务器

```bash
./start.sh
```

等待看到：
```
✅ 运行时请保证 https://app.warp.dev 网络联通性
🚀 Warp2Api 服务器状态
📍 OpenAI兼容API服务器: http://localhost:28889
```

### 2. 运行测试

```bash
python test_multimodal.py
```

### 3. 开始使用

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="0000"
)

# 发送图片 + 文本
response = client.chat.completions.create(
    model="claude-4-sonnet",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "这是什么？"},
            {"type": "image_url", "image_url": {
                "url": "https://example.com/cat.jpg"
            }}
        ]
    }]
)

print(response.choices[0].message.content)
```

## 📝 支持的图片格式

✅ **图片 URL**
```python
"url": "https://example.com/image.jpg"
```

✅ **Base64 Data URL**
```python
"url": "data:image/png;base64,iVBORw0KGgo..."
```

✅ **支持的格式**: JPEG, PNG, GIF, WebP, BMP, TIFF

## 🎯 常用场景

### 场景 1: 图片描述
```python
"请详细描述这张图片"
```

### 场景 2: OCR 文字识别
```python
"提取图片中的所有文字"
```

### 场景 3: 图片对比
```python
content: [
    {"type": "text", "text": "比较这两张图的异同"},
    {"type": "image_url", "image_url": {"url": "..."}},
    {"type": "image_url", "image_url": {"url": "..."}}
]
```

### 场景 4: 图表分析
```python
"分析这个图表的数据趋势"
```

## ⚙️ 环境变量配置（可选）

```bash
# 在 .env 文件中添加：

# 调整最大图片大小（默认 20MB）
W2A_MAX_IMAGE_SIZE_MB=30

# 调整下载超时（默认 30秒）
W2A_IMAGE_DOWNLOAD_TIMEOUT=60

# 禁用多模态功能
W2A_ENABLE_MULTIMODAL=false
```

## 🐛 快速问题排查

### 问题：图片无法下载
```
Failed to download image: HTTP 404
```
**解决**: 检查 URL 是否正确，或改用 base64 格式

### 问题：图片太大
```
Image size exceeds maximum 20MB
```
**解决**: 
```bash
export W2A_MAX_IMAGE_SIZE_MB=30
./start.sh
```

### 问题：模型不支持图片
```
Model does not support vision
```
**解决**: 使用支持 vision 的模型：
- ✅ claude-4-sonnet
- ✅ claude-4-opus  
- ✅ gemini-2.5-pro
- ✅ gpt-5
- ✅ gpt-4o

## 📚 更多资源

- 📖 [完整文档](MULTIMODAL.md)
- 🐛 [故障排除](TROUBLESHOOTING.md)
- 🧪 [测试脚本](../test_multimodal.py)
- 💬 [示例代码](MULTIMODAL.md#使用示例)
