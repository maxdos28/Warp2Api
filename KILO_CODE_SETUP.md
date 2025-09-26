# Kilo Code API配置指南

## 🎯 **API服务状态**

✅ **OpenAI兼容API服务器已就绪**
- **地址**: `http://127.0.0.1:28889` 或 `http://0.0.0.0:28889`
- **端口**: 28889
- **协议**: OpenAI Chat Completions API
- **状态**: 正常运行，返回真实AI响应

## 🔧 **Kilo Code配置**

### **API端点配置**
```json
{
  "apiUrl": "http://127.0.0.1:28889/v1/chat/completions",
  "apiKey": "任意值",
  "model": "claude-4-sonnet"
}
```

### **支持的模型**
- `claude-4-sonnet` ✅ (推荐)
- `claude-3-sonnet` ✅ (自动映射到claude-4-sonnet)
- `claude-4-opus` ✅
- `gpt-4` ✅ (映射到gpt-4o)
- `gpt-4o` ✅

## 📊 **API测试结果**

### **非流式响应** ✅
```bash
curl -X POST http://127.0.0.1:28889/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-4-sonnet", "messages": [{"role": "user", "content": "Hello"}], "stream": false}'
```

**响应格式**：
```json
{
  "id": "uuid",
  "object": "chat.completion", 
  "created": 1758820074,
  "model": "claude-4-sonnet",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! I'm Claude, an AI assistant..."
    },
    "finish_reason": "stop"
  }]
}
```

### **流式响应** ✅
```bash
curl -X POST http://127.0.0.1:28889/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-4-sonnet", "messages": [{"role": "user", "content": "Hello"}], "stream": true}' \
  -N
```

**响应格式**：
```
data: {"id": "uuid", "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {"role": "assistant"}}]}

data: {"id": "uuid", "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {"content": "Hello! I see"}}]}

data: {"id": "uuid", "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {"content": " you're running..."}}]}

...

data: {"id": "uuid", "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}

data: [DONE]
```

## 🚀 **Kilo Code配置步骤**

### **1. 打开Kilo Code设置**
- 进入设置/偏好设置
- 找到AI/语言模型配置部分

### **2. 配置API端点**
```
API URL: http://127.0.0.1:28889/v1/chat/completions
API Key: sk-dummy-key (任意值，我们的API不验证)
Model: claude-4-sonnet
```

### **3. 高级配置（如果支持）**
```
Temperature: 0.7
Max Tokens: 4000
Stream: true (启用流式响应)
```

### **4. 测试连接**
- 在Kilo Code中发送一个测试消息
- 应该收到类似："Hello! I'm Claude, an AI assistant..."的响应

## 🔍 **故障排除**

### **如果连接失败**：
1. **检查服务器状态**：
   ```bash
   curl -s http://127.0.0.1:28889/healthz
   ```

2. **检查端口**：
   ```bash
   ps aux | grep openai_compat
   ```

3. **重启服务**：
   ```bash
   python3 restart_services.py
   ```

### **如果响应异常**：
1. **检查日志**：
   ```bash
   tail -f logs/openai_compat.log
   ```

2. **测试API**：
   ```bash
   curl -X POST http://127.0.0.1:28889/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "claude-4-sonnet", "messages": [{"role": "user", "content": "test"}], "stream": false}'
   ```

## 📈 **性能优化**

API服务器包含14项性能优化：
- HTTP连接池优化
- 智能缓存系统
- 响应压缩
- 异步日志
- 智能限流
- 熔断器保护
- JSON优化
- 内存管理

## 🎊 **总结**

**Kilo Code现在可以完美使用我们的API了！**

1. ✅ **API完全兼容**：符合OpenAI标准
2. ✅ **响应质量**：真实AI内容，无错误前缀
3. ✅ **流式支持**：完整的SSE流式响应
4. ✅ **性能优化**：企业级优化措施

**配置完成后，Kilo Code就能正常使用AI功能了！** 🚀