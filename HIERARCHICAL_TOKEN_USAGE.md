# 🎯 层次化Token使用策略

## 📋 概述

Warp2Api现已支持**智能的层次化token使用策略**，可以自动按优先级使用不同的token，最大化可用配额。

## 🔄 工作原理

### 传统方式 vs 层次化策略

| 传统方式 | 层次化策略 |
|---------|-----------|
| 任何429错误都尝试申请匿名token | 仅在个人token配额用尽时申请匿名token |
| 可能混用不同token | 明确区分token类型和使用顺序 |
| 频繁的无效重试 | 智能判断何时切换token |

### 🎯 层次化使用流程

```
1. 🔑 个人Token（优先级1）
   ├─ ✅ 配额充足 → 正常使用
   └─ ❌ 配额用尽 → 切换到步骤2

2. 🎭 匿名Token（优先级2）
   ├─ 🔄 尝试申请新的匿名token
   ├─ ✅ 申请成功 → 使用匿名配额
   └─ ❌ 申请失败 → 返回友好错误信息

3. 📋 配额用尽
   └─ 返回明确的错误信息
```

## ⚙️ 配置选项

### 🎯 推荐配置：层次化使用

```bash
# .env 文件
API_TOKEN=123456
WARP_JWT=your_personal_jwt_token
WARP_REFRESH_TOKEN=your_personal_refresh_token
DISABLE_ANONYMOUS_FALLBACK=false  # 启用层次化使用
```

**优势**：
- ✅ 最大化可用配额
- ✅ 自动降级处理
- ✅ 无需手动干预

### 🔒 替代配置：仅个人配额

```bash
# .env 文件
API_TOKEN=123456
WARP_JWT=your_personal_jwt_token
WARP_REFRESH_TOKEN=your_personal_refresh_token
DISABLE_ANONYMOUS_FALLBACK=true  # 禁用匿名回退
```

**优势**：
- ✅ 明确的配额控制
- ✅ 简化账单和使用统计
- ✅ 避免token混用

## 📊 日志信息

### 正常切换过程
```
🔄 个人token配额已用尽，尝试申请匿名token作为备用…
✅ 成功获取匿名token，切换到匿名配额
```

### 配额完全用尽
```
📋 所有可用配额均已用尽
抱歉，个人配额和匿名配额均已用尽，请稍后再试。
```

### 禁用匿名回退
```
🔄 WARP API 配额用尽，但匿名token回退已禁用
抱歉，您的账户配额已用尽。请等待配额重置或联系管理员。
```

## 🧪 测试工具

### 基础测试
```bash
# 测试当前配置和策略
python test_hierarchical_tokens.py
```

### 切换演示
```bash
# 演示token切换过程
python test_hierarchical_tokens.py --demo
```

### 配额管理测试
```bash
# 完整的配额管理测试
python test_quota_management.py
```

## 🎯 使用场景

### 场景1：大量API调用
**推荐**：层次化使用
- 配置个人token + 启用匿名回退
- 获得最大的配额使用量
- 自动处理配额切换

### 场景2：明确的成本控制
**推荐**：仅个人配额
- 配置个人token + 禁用匿名回退
- 只使用付费配额
- 明确的使用控制

### 场景3：开发测试
**推荐**：层次化使用
- 在开发阶段最大化可用配额
- 减少因配额限制导致的开发中断

## 🔍 故障排除

### 问题：个人token无法切换到匿名token
**检查**：
1. `DISABLE_ANONYMOUS_FALLBACK`是否为`false`
2. 个人token配置是否正确
3. 是否在冷却期内

### 问题：频繁的token切换
**原因**：个人配额用尽过快
**解决**：
1. 增加个人账户配额
2. 优化API调用频率
3. 实现请求缓存

### 问题：匿名token申请失败
**原因**：达到频率限制
**解决**：
1. 等待冷却期结束
2. 减少API调用频率
3. 配置更高等级的个人账户

## 📈 性能优化

### 减少token切换频率
1. **合理规划调用**：批量处理请求
2. **缓存响应**：避免重复请求
3. **监控配额**：提前了解使用情况

### 最佳实践
1. **定期检查**：使用测试工具监控状态
2. **日志监控**：关注切换相关的日志
3. **配额规划**：根据使用模式选择合适的配置

---

## 🚀 快速开始

1. **配置个人token**：
   ```bash
   WARP_JWT=your_jwt_here
   WARP_REFRESH_TOKEN=your_refresh_token_here
   ```

2. **选择策略**：
   ```bash
   # 层次化使用（推荐）
   DISABLE_ANONYMOUS_FALLBACK=false
   
   # 或仅个人配额
   DISABLE_ANONYMOUS_FALLBACK=true
   ```

3. **重启服务**：
   ```bash
   uv run python server.py
   uv run python openai_compat.py
   ```

4. **测试功能**：
   ```bash
   python test_hierarchical_tokens.py
   ```

现在您可以享受智能的层次化token使用策略带来的便利！🎉
