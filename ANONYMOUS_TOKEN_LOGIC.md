# 匿名Token申请逻辑说明

## 📋 **当前匿名Token申请策略**

### 🔄 **申请触发条件**

匿名token会在以下情况下自动申请：

#### 1. **个人Token配额用尽**
- **条件**：使用个人token且收到HTTP 429配额错误
- **行为**：立即申请匿名token作为备用
- **位置**：`warp2protobuf/warp/api_client.py` 第120-132行

#### 2. **匿名Token配额用尽** ⭐ **新增逻辑**
- **条件**：使用匿名token且收到HTTP 429配额错误
- **行为**：申请新的匿名token（强制刷新）
- **特点**：
  - 移除了`has_tried_anonymous`限制
  - 允许在同一请求中多次申请新匿名token
  - 最多尝试5次（从原来的2次增加）
  - 递增延迟策略：3秒 + 尝试次数 * 2秒

#### 3. **服务器启动时**
- **条件**：启动时没有有效JWT token
- **行为**：申请匿名token用于初始化
- **位置**：`server.py` 第472行

#### 4. **优先使用匿名Token模式**
- **条件**：`PRIORITIZE_ANONYMOUS_TOKEN = True`
- **行为**：优先申请匿名token而非个人token
- **位置**：`warp2protobuf/core/auth.py` 第201行

### 🎯 **重试策略**

#### **标准模式**（send_protobuf_to_warp_api）
```python
max_attempts = 5  # 最多5次尝试
for attempt in range(max_attempts):
    if 配额用尽:
        if attempt < max_attempts - 1:
            申请新匿名token()
            等待(3 + attempt * 2)秒
            continue
```

#### **解析模式**（send_protobuf_to_warp_api_with_parsed_events）
```python
max_attempts = 5  # 最多5次尝试
for attempt in range(max_attempts):
    if 配额用尽:
        if attempt < max_attempts - 1:
            申请新匿名token()
            等待(3 + attempt * 2)秒
            continue
```

#### **SSE流式模式**（send_protobuf_to_warp_api_sse）
```python
max_attempts = 2  # SSE模式保持2次尝试
for attempt in range(max_attempts):
    if 配额用尽:
        if attempt < max_attempts - 1:
            申请新匿名token()
            等待(3 + attempt * 2)秒
            continue
```

### 🚀 **优化特性**

#### **智能延迟策略**
- **第1次重试**：等待3秒
- **第2次重试**：等待5秒
- **第3次重试**：等待7秒
- **第4次重试**：等待9秒
- **申请失败时**：等待10-25秒（递增）

#### **错误处理**
- **429限频**：自动等待并重试
- **网络错误**：记录错误并重试
- **申请失败**：降级到错误消息

#### **日志记录**
- 详细记录每次申请尝试
- 成功/失败状态跟踪
- 性能指标收集

### 📊 **申请频率控制**

为避免触发Warp服务的限频：

1. **递增延迟**：每次重试间隔递增
2. **失败惩罚**：申请失败后等待更长时间
3. **最大尝试限制**：防止无限重试
4. **智能退避**：根据错误类型调整等待时间

### 🔧 **配置参数**

```python
# 主要配置
MAX_ATTEMPTS = 5              # 最大尝试次数
BASE_DELAY = 3               # 基础延迟（秒）
DELAY_MULTIPLIER = 2         # 延迟倍数
FAILURE_PENALTY = 10         # 失败惩罚延迟（秒）

# 错误检测模式
QUOTA_ERROR_PATTERNS = [
    "No remaining quota",
    "No AI requests remaining", 
    "配额已用尽",
    "quota exhausted"
]
```

### 📈 **预期效果**

1. **更高的可用性**：即使匿名token用尽也能继续申请新token
2. **更好的用户体验**：减少"配额用尽"错误
3. **智能重试**：避免频繁申请触发限频
4. **自动恢复**：无需手动干预即可恢复服务

### ⚠️ **注意事项**

1. **申请限频**：Warp服务对匿名token申请有频率限制
2. **配额限制**：每个匿名token都有使用配额限制
3. **网络依赖**：需要稳定的网络连接到Warp服务
4. **延迟影响**：重试会增加响应时间

## 🎯 **使用建议**

- **正常使用**：系统会自动处理token申请和刷新
- **高频使用**：建议配置个人token以获得更高配额
- **监控**：通过日志监控token申请状态和成功率
- **调优**：根据使用模式调整重试参数