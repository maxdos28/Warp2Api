# Warp2API Go

基于 Go 的桥接服务，为 Warp AI 服务提供 **OpenAI Chat Completions API** 和 **Claude Messages API** 双重兼容性，通过利用 Warp 的 protobuf 基础架构，实现与主流 AI SDK 的无缝集成。

## 🚀 特性

- **双 API 兼容性**: 完全支持 OpenAI Chat Completions API 和 Claude Messages API 格式 ✨
- **Warp 集成**: 使用 protobuf 通信与 Warp AI 服务无缝桥接
- **双服务器架构**: 
  - 用于 Warp 通信的 Protobuf 编解码服务器
  - 用于客户端应用程序的 OpenAI 兼容 API 服务器
- **JWT 认证**: Warp 服务的自动令牌管理和刷新
- **流式支持**: 与 OpenAI SSE 格式兼容的实时流式响应
- **WebSocket 监控**: 内置监控和调试功能
- **消息重排序**: 针对 Anthropic 风格对话的智能消息处理
- **高性能**: 基于 Go 的高性能实现

## 📋 系统要求

- Go 1.21+ (推荐 1.22+)
- Warp AI 服务访问权限（JWT 令牌会自动获取）
- 支持 Linux、macOS 和 Windows

## 🛠️ 安装

1. **克隆仓库:**
   ```bash
   git clone <repository-url>
   cd warp2api-go
   ```

2. **安装依赖:**
   ```bash
   go mod tidy
   go mod download
   ```

3. **配置环境变量:**
   程序会自动获取匿名JWT TOKEN，您无需手动配置。

   如需自定义配置，可以创建 `.env` 文件:
   ```env
   # Warp2API Go 配置
   # 设置为 true 启用详细日志输出，默认 false（静默模式）
   W2A_VERBOSE=false

   # Bridge服务器URL配置
   WARP_BRIDGE_URL=http://127.0.0.1:28888

   # 禁用代理以避免连接问题
   HTTP_PROXY=
   HTTPS_PROXY=
   NO_PROXY=127.0.0.1,localhost

   # 可选：使用自己的Warp凭证（不推荐，会消耗订阅额度）
   WARP_JWT=your_jwt_token_here
   WARP_REFRESH_TOKEN=your_refresh_token_here
   ```

## 🎯 使用方法

### 快速开始

#### 方法一：一键启动脚本（推荐）

**Linux/macOS:**
```bash
# 启动所有服务器
./scripts/start.sh

# 停止所有服务器
./scripts/stop.sh

# 查看服务器状态
./scripts/stop.sh status

# 测试API接口功能
./scripts/test.sh
```

**Windows:**
```batch
REM 使用批处理脚本
scripts\start.bat          # 启动服务器
scripts\stop.bat           # 停止服务器
scripts\test.bat           # 测试API接口功能
```

启动脚本会自动：
- ✅ 检查Go环境和依赖
- ✅ 自动配置环境变量
- ✅ 按正确顺序启动两个服务器
- ✅ 验证服务器健康状态
- ✅ 显示关键配置信息
- ✅ 显示完整的 API 接口信息
- ✅ 提供详细的错误处理和状态反馈

#### 方法二：手动启动

1. **启动 Protobuf 桥接服务器:**
   ```bash
   go run cmd/bridge/main.go
   ```
   默认地址: `http://localhost:28888`

2. **启动 OpenAI 兼容 API 服务器:**
   ```bash
   go run main.go
   ```
   默认地址: `http://localhost:28889`

### 支持的模型

Warp2API Go 支持以下 AI 模型：

#### Anthropic Claude 系列
- `claude-4-sonnet` - Claude 4 Sonnet 模型
- `claude-4-opus` - Claude 4 Opus 模型
- `claude-4.1-opus` - Claude 4.1 Opus 模型

#### Google Gemini 系列
- `gemini-2.5-pro` - Gemini 2.5 Pro 模型

#### OpenAI GPT 系列
- `gpt-4.1` - GPT-4.1 模型
- `gpt-4o` - GPT-4o 模型
- `gpt-5` - GPT-5 基础模型
- `gpt-5 (high reasoning)` - GPT-5 高推理模式

#### OpenAI o系列
- `o3` - o3 模型
- `o4-mini` - o4-mini 模型

### 使用 API

#### 🔓 认证说明
**重要：Warp2API Go 的 API 接口不需要 API key 验证！**

- 服务器会自动处理 Warp 服务的认证
- 客户端可以发送任意的 `api_key` 值（或完全省略）
- 所有请求都会使用系统自动获取的匿名 JWT token

#### 🎯 支持的 API 格式
Warp2API Go 现在支持两种主流 AI API 格式：

1. **OpenAI Chat Completions API** - `/v1/chat/completions`
2. **Claude Messages API** - `/v1/messages` ✨ **新增**

两个服务器都运行后，您可以使用任何兼容的客户端:

#### Go 示例
```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
)

func main() {
    // OpenAI API 调用
    openaiReq := map[string]interface{}{
        "model": "claude-4-sonnet",
        "messages": []map[string]interface{}{
            {"role": "user", "content": "你好，你好吗？"},
        },
        "stream": true,
    }
    
    reqBody, _ := json.Marshal(openaiReq)
    resp, err := http.Post("http://localhost:28889/v1/chat/completions", 
        "application/json", bytes.NewBuffer(reqBody))
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()
    
    body, _ := io.ReadAll(resp.Body)
    fmt.Println(string(body))
}
```

#### Python 示例
```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="dummy"  # 可选：某些客户端需要，但服务器不强制验证
)

response = client.chat.completions.create(
    model="claude-4-sonnet",  # 选择支持的模型
    messages=[
        {"role": "user", "content": "你好，你好吗？"}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

#### Claude API 示例 ✨
```python
import requests

# 基本 Claude Messages API 调用
response = requests.post(
    "http://localhost:28889/v1/messages",
    json={
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
        "messages": [
            {"role": "user", "content": "你好，请介绍一下你自己"}
        ]
    }
)

result = response.json()
print(result["content"][0]["text"])
```

#### cURL 示例

##### OpenAI 格式
```bash
# 基本请求
curl -X POST http://localhost:28889/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-4-sonnet",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
    "stream": true
  }'

# 指定其他模型
curl -X POST http://localhost:28889/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5",
    "messages": [
      {"role": "user", "content": "解释量子计算的基本原理"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

##### Claude 格式 ✨
```bash
# 基本 Claude Messages API 请求
curl -X POST http://localhost:28889/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1000,
    "messages": [
      {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
  }'
```

### 模型选择建议

- **编程任务**: 推荐使用 `claude-4-sonnet` 或 `gpt-5`
- **创意写作**: 推荐使用 `claude-4-opus` 或 `gpt-4o`
- **代码审查**: 推荐使用 `claude-4.1-opus`
- **推理任务**: 推荐使用 `gpt-5 (high reasoning)` 或 `o3`
- **轻量任务**: 推荐使用 `o4-mini` 或 `gpt-4o`

### 可用端点

#### Protobuf 桥接服务器 (`http://localhost:28888`)
- `GET /healthz` - 健康检查
- `POST /api/encode` - 将 JSON 编码为 protobuf
- `POST /api/decode` - 将 protobuf 解码为 JSON
- `POST /api/stream-decode` - 流式protobuf解码
- `POST /api/warp/send` - JSON -> Protobuf -> Warp API转发
- `POST /api/warp/send_stream` - JSON -> Protobuf -> Warp API转发(返回解析事件)
- `POST /api/warp/send_stream_sse` - JSON -> Protobuf -> Warp API转发(实时SSE，事件已解析)
- `GET /api/warp/graphql/*` - GraphQL请求转发到Warp API（带鉴权）
- `GET /api/schemas` - Protobuf schema信息
- `GET /api/auth/status` - JWT认证状态
- `POST /api/auth/refresh` - 刷新JWT token
- `GET /api/auth/user_id` - 获取当前用户ID
- `GET /api/packets/history` - 数据包历史记录
- `WS /ws` - WebSocket实时监控

#### OpenAI & Claude API 服务器 (`http://localhost:28889`)
- `GET /` - 服务状态
- `GET /healthz` - 健康检查
- `GET /v1/models` - 模型列表
- `POST /v1/chat/completions` - OpenAI Chat Completions 兼容端点
- `POST /v1/messages` - Claude Messages API 兼容端点 ✨

## 🏗️ 架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    客户端应用     │───▶│ OpenAI & Claude │───▶│   Protobuf      │
│ (OpenAI/Claude) │    │   API 服务器    │    │    桥接服务器    │
│      SDK        │    │  (端口 28889)   │    │  (端口 28888)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │    Warp AI      │
                                               │      服务       │
                                               └─────────────────┘
```

### 核心组件

- **`internal/handlers/`**: OpenAI & Claude API 兼容层
  - 消息格式转换 (OpenAI ↔ Warp, Claude ↔ Warp)
  - 流式响应处理 (SSE)
  - 错误映射和验证
  - Claude API 标准支持 ✨

- **`internal/bridge/`**: Warp protobuf 通信层
  - JWT 认证管理
  - Protobuf 编解码
  - WebSocket 监控
  - 请求路由和验证

- **`internal/warp/`**: Warp API 客户端
  - HTTP 客户端管理
  - 请求/响应处理
  - 错误处理

- **`internal/auth/`**: 认证管理
  - JWT 令牌管理
  - 令牌刷新
  - 匿名令牌获取

## 🔧 配置

### 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `WARP_JWT` | Warp 认证 JWT 令牌 | 自动获取 |
| `WARP_REFRESH_TOKEN` | JWT 刷新令牌 | 可选 |
| `WARP_BRIDGE_URL` | Protobuf 桥接服务器 URL | `http://127.0.0.1:28888` |
| `HTTP_PROXY` | HTTP 代理设置 | 空（禁用代理） |
| `HTTPS_PROXY` | HTTPS 代理设置 | 空（禁用代理） |
| `NO_PROXY` | 不使用代理的主机 | `127.0.0.1,localhost` |
| `HOST` | 服务器主机地址 | `127.0.0.1` |
| `PORT` | OpenAI API 服务器端口 | `28889` |
| `W2A_VERBOSE` | 启用详细日志输出 | `false` |

### 项目结构

```
warp2api-go/
├── cmd/                        # 命令行工具
│   └── bridge/                 # 桥接服务器入口
├── internal/                   # 内部包
│   ├── auth/                   # 认证管理
│   ├── bridge/                 # 桥接服务器
│   │   ├── handlers/           # 桥接处理器
│   │   └── services/           # 桥接服务
│   ├── config/                 # 配置管理
│   ├── handlers/               # API处理器
│   ├── logger/                 # 日志管理
│   ├── middleware/             # 中间件
│   ├── models/                 # 数据模型
│   ├── protobuf/               # Protobuf处理
│   ├── server/                 # 服务器管理
│   ├── services/               # 业务服务
│   ├── streaming/              # 流式处理
│   └── warp/                   # Warp API客户端
├── scripts/                    # 脚本文件
│   ├── start.sh               # 启动脚本
│   ├── stop.sh                # 停止脚本
│   └── test.sh                # 测试脚本
├── main.go                    # 主服务器入口
├── go.mod                     # Go模块文件
└── README_GO.md              # 项目文档
```

## 🔐 认证

服务会自动处理 Warp 认证:

1. **JWT 管理**: 自动令牌验证和刷新
2. **匿名访问**: 在需要时回退到匿名令牌
3. **令牌持久化**: 安全的令牌存储和重用

## 🧪 开发

### 构建项目

```bash
# 构建主服务器
go build -o bin/warp2api-go main.go

# 构建桥接服务器
go build -o bin/bridge cmd/bridge/main.go

# 构建所有组件
go build ./...
```

### 运行测试

```bash
# 运行所有测试
go test ./...

# 运行特定包测试
go test ./internal/handlers

# 运行基准测试
go test -bench=./...
```

### 代码格式化

```bash
# 格式化代码
go fmt ./...

# 运行代码检查
go vet ./...

# 运行静态分析
go run honnef.co/go/tools/cmd/staticcheck@latest ./...
```

## 🐛 故障排除

### 常见问题

1. **"Server disconnected without sending a response" 错误**
    - 检查 `.env` 文件中的 `WARP_BRIDGE_URL` 配置是否正确
    - 确保代理设置已禁用：`HTTP_PROXY=`, `HTTPS_PROXY=`, `NO_PROXY=127.0.0.1,localhost`
    - 验证桥接服务器是否在端口 28888 上运行
    - 检查防火墙是否阻止了本地连接

2. **JWT 令牌过期**
    - 服务会自动刷新令牌
    - 检查日志中的认证错误
    - 验证 `WARP_REFRESH_TOKEN` 是否有效

3. **桥接服务器未就绪**
    - 确保首先运行 protobuf 桥接服务器
    - 检查 `WARP_BRIDGE_URL` 配置（应为 `http://127.0.0.1:28888`）
    - 验证端口可用性

4. **代理连接错误**
    - 如果遇到 `ProxyError` 或端口 1082 错误
    - 在 `.env` 文件中设置：`HTTP_PROXY=`, `HTTPS_PROXY=`, `NO_PROXY=127.0.0.1,localhost`
    - 或者在系统环境中禁用代理

5. **连接错误**
    - 检查到 Warp 服务的网络连接
    - 验证防火墙设置
    - 确保本地端口 28888 和 28889 未被其他应用占用

### 日志记录

两个服务器都提供详细的日志记录:
- 认证状态和令牌刷新
- 请求/响应处理
- 错误详情和堆栈跟踪
- 性能指标

查看日志:
```bash
# 查看主服务器日志
tail -f logs/main.log

# 查看桥接服务器日志
tail -f logs/bridge.log

# 查看所有日志
tail -f logs/*.log
```

## 📄 许可证

该项目配置为内部使用。请与项目维护者联系了解许可条款。

## 🤝 贡献

1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 如适用，添加测试
5. 提交 pull request

## 📞 支持

如有问题和疑问:
1. 查看故障排除部分
2. 查看服务器日志获取错误详情
3. 创建包含重现步骤的 issue