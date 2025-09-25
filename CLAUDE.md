# Warp2Api 项目文档

## 项目概述
Warp2Api是一个基于Python的桥接服务，为Warp AI服务提供OpenAI Chat Completions API兼容性。

## 主要功能
- **OpenAI API兼容性**: 完全支持OpenAI Chat Completions API格式
- **Claude API兼容性**: 完全支持Anthropic Claude Messages API格式  
- **工具调用支持**: 支持Computer Use和Code Execution工具
- **流式响应**: 支持实时流式响应
- **多格式转换**: 自动转换不同API格式

## 技术架构
- **前端API**: FastAPI框架，提供HTTP API接口
- **桥接层**: Protobuf通信，连接Warp AI服务
- **工具系统**: 本地工具执行，支持文件操作和计算机控制
- **认证系统**: 支持多种API密钥格式

## 文件结构
```
protobuf2openai/          # API兼容层
├── app.py               # FastAPI应用入口
├── router.py            # OpenAI API路由
├── claude_router.py     # Claude API路由
├── models.py            # 数据模型定义
├── helpers.py           # 工具函数
└── local_tools.py       # 本地工具执行

warp2protobuf/           # Warp通信层
├── core/               # 核心功能
├── api/                # API接口
└── config/             # 配置管理
```

## 使用方法

### 启动服务
```bash
# 方法1: 使用启动脚本
./start.sh

# 方法2: 手动启动
uv run python server.py --port 28888      # 桥接服务器
uv run python openai_compat.py --port 28889  # API服务器
```

### API配置
- **Base URL**: http://localhost:28889/v1
- **API Key**: 0000
- **支持的端点**:
  - GET/POST /v1/messages/init (初始化)
  - GET /v1/messages/models (模型列表)
  - POST /v1/messages (Claude API)
  - POST /v1/chat/completions (OpenAI API)

### 工具支持
- **Computer Use**: anthropic-beta: computer-use-2024-10-22
- **Code Execution**: anthropic-beta: code-execution-2025-08-25
- **自定义工具**: 支持用户定义的工具

## 开发说明

### 环境要求
- Python 3.13+
- uv包管理器
- Warp AI访问权限

### 配置文件
```env
API_TOKEN=0000
WARP_JWT=your_jwt_token
WARP_REFRESH_TOKEN=your_refresh_token
```

### 测试
```bash
# 测试基础功能
python test_claude_api.py

# 测试工具调用
python test_claude_code_tools.py

# 测试图片支持
python test_image_support_comprehensive.py
```

## 注意事项

### 匿名账户限制
- 基础对话功能完全可用
- 工具调用格式支持，但执行可能受限
- 建议升级到付费账户获得完整功能

### 已知问题
- 复杂的连续工具调用可能中断
- 图片处理功能需要付费账户
- 某些高级AI功能受限

## 贡献指南
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证
MIT License

---
文档生成时间: 2025-09-25 04:04:41
由Claude Code自动生成
