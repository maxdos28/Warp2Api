# Warp Token刷新逻辑详细分析

## 🔍 当前Token刷新逻辑

### 📋 **Token类型和优先级**

#### 1. **个人账户Token (优先级最高)**
```python
# 来源：环境变量 WARP_REFRESH_TOKEN
env_refresh = os.getenv("WARP_REFRESH_TOKEN")
if env_refresh:
    payload = f"grant_type=refresh_token&refresh_token={env_refresh}".encode("utf-8")
```

#### 2. **内置Token (备用)**
```python
# 来源：代码中的 REFRESH_TOKEN_B64
else:
    payload = base64.b64decode(REFRESH_TOKEN_B64)
```

#### 3. **匿名Token (配额耗尽时)**
```python
# 触发条件：HTTP 429 + "No remaining quota"
if response.status_code == 429 and (
    ("No remaining quota" in error_content) or 
    ("No AI requests remaining" in error_content)
):
    new_jwt = await acquire_anonymous_access_token()
```

### 🔄 **完整的刷新流程**

#### **正常情况下的流程：**
```
1. 使用现有JWT token
2. 如果token过期 → 使用 WARP_REFRESH_TOKEN 刷新
3. 如果没有 WARP_REFRESH_TOKEN → 使用内置 REFRESH_TOKEN_B64
4. 更新 .env 文件中的 WARP_JWT
```

#### **配额耗尽时的流程：**
```
1. 收到 HTTP 429 "No remaining quota"
2. 调用 acquire_anonymous_access_token()
3. 创建匿名用户：NATIVE_CLIENT_ANONYMOUS_USER_FEATURE_GATED
4. 获取匿名JWT token
5. 更新 .env 文件
6. 重试原始请求
```

### 📊 **当前使用的Token类型**

从 .env 文件分析：
```bash
WARP_JWT='eyJhbGciOiJSUzI1NiI...'  # 当前使用的JWT
WARP_REFRESH_TOKEN='AMf-vBw4yYR...'  # 刷新token
```

解码JWT payload显示：
```json
{
  "user_id": "bjL8S12XVqehGtKWvz3sqV6AY8X2",
  "firebase": {
    "sign_in_provider": "custom"  // 表明是匿名/自定义用户
  }
}
```

### 🎯 **结论：当前使用匿名Token**

#### **证据：**
1. `sign_in_provider: "custom"` - 表明是匿名用户
2. 代码中的匿名用户类型：`NATIVE_CLIENT_ANONYMOUS_USER_FEATURE_GATED`
3. 功能限制表现：工具调用格式支持，但执行受限

#### **刷新优先级：**
```
1. 个人账户 WARP_REFRESH_TOKEN (如果有) 
2. 内置 REFRESH_TOKEN_B64 (备用)
3. 匿名token (配额耗尽时自动申请)
```

### 💡 **如果要使用个人账户Token**

#### **方法1：设置个人refresh token**
```bash
# 在 .env 文件中设置你的个人refresh token
WARP_REFRESH_TOKEN=your_personal_refresh_token_here
```

#### **方法2：设置个人JWT token**
```bash
# 直接设置个人JWT token
WARP_JWT=your_personal_jwt_token_here
```

### 🔍 **检查当前Token状态**

当前系统会：
1. **优先使用个人token** (如果 WARP_REFRESH_TOKEN 存在)
2. **回退到内置token** (如果个人token不存在)
3. **最后使用匿名token** (如果配额耗尽)

### 🎯 **关键发现**

**当前使用的是匿名token，这解释了所有的功能限制！**

- ✅ 基础对话：正常
- ✅ 工具调用格式：支持
- ❌ 工具实际执行：受限
- ❌ 复杂任务：中断
- ❌ Vision功能：不可用

**如果有个人Warp账户的token，设置到 .env 文件中应该能解决所有问题！**