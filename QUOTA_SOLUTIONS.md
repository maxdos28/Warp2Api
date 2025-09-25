# 🚀 配额用尽问题解决方案

## 📋 问题描述

当Warp API配额用尽时，会出现以下错误：
- `"error":"No remaining quota: No AI requests remaining"`
- `HTTP 429: Too Many Requests`
- 匿名token申请也可能被限制

## 🛠️ 解决方案

### 方案1：智能层次化token使用（新功能）

系统现已支持**智能的层次化token使用策略**：
- ✅ **优先个人配额**：首先使用个人Warp账户的配额
- ✅ **自动降级**：个人配额用尽后自动切换到匿名token
- ✅ **避免混用**：明确区分使用哪种token，避免配额混淆
- ✅ **智能重试**：只在合适的时机申请匿名token，避免无效重试

**操作**：配置个人token后，系统会自动按层次使用配额。

### 方案2：使用个人Warp账户（推荐）

如果您有Warp Pro订阅或个人账户，可以配置使用自己的token：

1. **获取个人token**：
   - 登录Warp应用
   - 在开发者设置中获取JWT和Refresh Token

2. **配置环境变量**：
   ```bash
   # 在.env文件中添加
   WARP_JWT=your_personal_jwt_token
   WARP_REFRESH_TOKEN=your_personal_refresh_token
   
   # 可选：禁用匿名token回退（只使用个人账户配额）
   DISABLE_ANONYMOUS_FALLBACK=true
   ```

3. **重启服务**：
   ```bash
   # 停止当前服务
   # 重新启动
   uv run python server.py
   uv run python openai_compat.py
   ```

#### 🔒 禁用匿名token回退

设置 `DISABLE_ANONYMOUS_FALLBACK=true` 的效果：
- ✅ **仅使用个人配额**：不会申请匿名token作为备用
- ✅ **明确配额控制**：配额用尽时直接提示，不会混用其他token
- ✅ **避免频率限制**：不会触发匿名token申请的429限制
- ✅ **简化错误诊断**：错误信息更清晰，便于排查问题

### 方案3：降低使用频率

- **减少并发请求**：避免同时发送多个请求
- **增加请求间隔**：在请求之间添加延迟
- **使用缓存**：缓存常见问题的回答

### 方案4：监控和预警

系统会自动记录：
- `.last_anonymous_attempt` - 上次匿名token申请时间
- `.anonymous_cooldown` - 冷却结束时间
- 日志中的详细错误信息

## 🔧 技术实现

### 新增的智能重试机制

1. **频率限制检查**：
   - 5分钟内不重复申请匿名token
   - 429错误后1小时冷却期

2. **错误分类处理**：
   ```
   配额用尽 → 尝试匿名token → 成功/失败分支处理
   频率限制 → 智能冷却 → 友好错误信息
   服务异常 → 直接返回 → 错误详情记录
   ```

3. **自动清理机制**：
   - 成功获取token后清除限制记录
   - 避免不必要的限制累积

## 📊 监控配额状态

查看实时日志：
```bash
# 查看最新错误
tail -f logs/warp_server.log | grep -E "(429|quota|cooldown)"

# 检查冷却状态
ls -la .anonymous_cooldown .last_anonymous_attempt 2>/dev/null || echo "No cooldown active"
```

## 🎯 最佳实践

1. **预防性监控**：定期检查配额使用情况
2. **合理使用**：避免不必要的API调用
3. **备用方案**：配置个人账户作为备用
4. **错误处理**：客户端实现重试和降级逻辑

## 🔍 故障排除

### 问题：持续429错误
**解决**：等待冷却期结束，或配置个人token

### 问题：匿名token申请失败
**解决**：检查网络连接，或等待更长时间再试

### 问题：配额重置时间未知
**解决**：通常按UTC时间每日或每小时重置，建议等待至少1小时

---

## 📝 配置模板

创建`.env`文件：
```bash
# 基础配置
API_TOKEN=123456

# === 个人Warp账户配置（推荐） ===
# 替换为您的真实token
# WARP_JWT=your_personal_jwt_token_here
# WARP_REFRESH_TOKEN=your_personal_refresh_token_here

# === 配额管理设置 ===
# 禁用匿名token回退 - 设置为true后只使用个人配额
# 推荐：配置个人token后设置为true
DISABLE_ANONYMOUS_FALLBACK=false

# === 其他可选配置 ===
# SERVER_HOST=0.0.0.0
# SERVER_PORT=28889
# OPENAI_COMPAT_PORT=28888
```

### 🎯 推荐配置

#### 选项1：层次化配额使用（推荐）
```bash
# .env 文件内容 - 最大化配额使用
API_TOKEN=123456
WARP_JWT=your_personal_jwt_token
WARP_REFRESH_TOKEN=your_personal_refresh_token
DISABLE_ANONYMOUS_FALLBACK=false  # 启用层次化使用
```

#### 选项2：仅个人配额
```bash
# .env 文件内容 - 仅使用个人配额，避免混用
API_TOKEN=123456
WARP_JWT=your_personal_jwt_token
WARP_REFRESH_TOKEN=your_personal_refresh_token
DISABLE_ANONYMOUS_FALLBACK=true  # 仅使用个人配额
```

#### 🆚 配置对比

| 配置 | 优势 | 适用场景 |
|------|------|----------|
| **层次化使用** | 最大配额量、自动降级 | 大量API调用，希望最大化可用配额 |
| **仅个人配额** | 明确配额控制、简化计费 | 需要明确配额使用情况，避免混用 |

配置完成后重启服务即可生效。
