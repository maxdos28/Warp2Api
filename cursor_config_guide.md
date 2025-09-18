# Cursor IDE Background Agents 配置指南

## 问题诊断

如果 Cursor IDE 的 Background Agents 加载不出来，请按照以下步骤检查和配置：

## 1. 检查服务器状态

确保 Warp2Api 服务器正在运行：

```bash
# 检查服务器状态
curl http://localhost:28889/healthz

# 应该返回：
# {"status":"ok","service":"OpenAI Chat Completions (Warp bridge) - Streaming"}
```

## 2. Cursor IDE 配置

### 方法一：通过设置界面配置

1. 打开 Cursor IDE
2. 进入设置 (Settings)
3. 找到 "AI" 或 "Background Agents" 部分
4. 配置以下参数：
   - **API Base URL**: `http://localhost:28889/v1`
   - **API Key**: `0000`
   - **Model**: `claude-4-sonnet`

### 方法二：通过配置文件配置

在 Cursor IDE 的配置文件中添加：

```json
{
  "cursor.ai.apiBaseUrl": "http://localhost:28889/v1",
  "cursor.ai.apiKey": "0000",
  "cursor.ai.model": "claude-4-sonnet"
}
```

## 3. 支持的模型列表

可以通过以下命令查看所有支持的模型：

```bash
curl http://localhost:28889/v1/models
```

支持的模型包括：
- `claude-4-sonnet`
- `claude-4-opus`
- `claude-4.1-opus`
- `gpt-4.1`
- `gpt-4o`
- `gpt-5`
- `o3`
- `o4-mini`
- `gemini-2.5-pro`

## 4. 常见问题排查

### 问题 1: 连接被拒绝
**症状**: Cursor IDE 显示连接错误
**解决方案**: 
- 确保服务器正在运行：`ps aux | grep python3`
- 检查端口是否被占用：`lsof -i :28889`

### 问题 2: 认证失败
**症状**: 401 Unauthorized 错误
**解决方案**:
- 确保 API Key 设置为 `0000`
- 检查 `.env` 文件中的 `API_TOKEN=0000`

### 问题 3: 模型不支持
**症状**: 模型选择错误
**解决方案**:
- 使用支持的模型名称
- 检查模型列表：`curl http://localhost:28889/v1/models`

### 问题 4: 网络连接问题
**症状**: 超时或连接失败
**解决方案**:
- 确保防火墙允许本地连接
- 检查代理设置
- 尝试使用 `127.0.0.1` 而不是 `localhost`

## 5. 测试配置

使用以下命令测试 API 是否正常工作：

```bash
curl -X POST http://localhost:28889/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 0000" \
  -d '{
    "model": "claude-4-sonnet",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10,
    "stream": false
  }'
```

## 6. 重启服务

如果配置正确但仍然无法加载，尝试重启服务：

```bash
# 停止服务
pkill -f "python3.*server.py"
pkill -f "python3.*openai_compat.py"

# 重新启动
export PATH="$HOME/.local/bin:$PATH"
python3 server.py --port 28888 &
python3 openai_compat.py --port 28889 &
```

## 7. 日志检查

查看服务器日志以获取更多信息：

```bash
# 查看日志文件
tail -f logs/warp_server.log
tail -f openai_server.log
```

## 8. 验证步骤

1. ✅ 服务器正在运行
2. ✅ API 端点可访问
3. ✅ 认证配置正确
4. ✅ 模型名称正确
5. ✅ Cursor IDE 配置正确
6. ✅ 网络连接正常

如果所有步骤都正确但仍然无法加载，请检查 Cursor IDE 的版本和更新状态。