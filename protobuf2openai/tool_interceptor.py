"""
工具调用拦截器
完全拦截工具调用，防止发送到Warp后端
"""

from typing import Dict, Any, List, Optional
import json
import uuid
from .local_tools import execute_tool_locally

def should_intercept_tool(tool_name: str) -> bool:
    """判断是否应该拦截这个工具调用"""
    intercepted_tools = [
        "str_replace_based_edit_tool",
        "computer_20241022"
    ]
    return tool_name in intercepted_tools

def intercept_and_execute_tools(packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    拦截工具调用并本地执行
    返回修改后的packet或直接的响应
    """
    
    # 检查是否有工具调用
    user_inputs = packet.get("input", {}).get("user_inputs", {}).get("inputs", [])
    
    intercepted_results = []
    
    for user_input in user_inputs:
        user_query = user_input.get("user_query", {})
        query_text = user_query.get("query", "")
        
        # 检测可能的工具调用意图
        tool_intents = detect_tool_intents(query_text)
        
        for intent in tool_intents:
            if should_intercept_tool(intent["tool"]):
                # 本地执行工具
                try:
                    result = execute_tool_locally(intent["tool"], intent["params"])
                    intercepted_results.append({
                        "tool": intent["tool"],
                        "params": intent["params"],
                        "result": result
                    })
                except Exception as e:
                    intercepted_results.append({
                        "tool": intent["tool"],
                        "params": intent["params"],
                        "result": {"error": str(e)}
                    })
    
    # 如果有拦截的工具执行，直接返回结果
    if intercepted_results:
        return create_direct_response(intercepted_results, packet)
    
    # 否则返回原始packet
    return packet

def detect_tool_intents(query_text: str) -> List[Dict[str, Any]]:
    """检测查询文本中的工具调用意图"""
    intents = []
    
    query_lower = query_text.lower()
    
    # 检测文件操作意图
    if "读取" in query_text or "查看" in query_text or "read" in query_lower:
        # 提取文件路径
        words = query_text.split()
        for word in words:
            if "." in word or "/" in word:
                intents.append({
                    "tool": "str_replace_based_edit_tool",
                    "params": {
                        "command": "view",
                        "path": word.strip("，。！？、")
                    }
                })
                break
    
    elif "创建" in query_text or "create" in query_lower:
        # 检测文件创建
        if ".md" in query_text or ".txt" in query_text:
            # 提取文件名
            words = query_text.split()
            for word in words:
                if ".md" in word or ".txt" in word:
                    # 生成基础内容
                    if "claude.md" in word.lower():
                        content = generate_claude_md_content()
                    else:
                        content = f"# {word}\n\n由Claude Code创建的文件。"
                    
                    intents.append({
                        "tool": "str_replace_based_edit_tool",
                        "params": {
                            "command": "create",
                            "path": word.strip("，。！？、"),
                            "file_text": content
                        }
                    })
                    break
    
    elif "截图" in query_text or "screenshot" in query_lower:
        intents.append({
            "tool": "computer_20241022",
            "params": {
                "action": "screenshot"
            }
        })
    
    return intents

def generate_claude_md_content() -> str:
    """生成CLAUDE.md文件的内容"""
    import time
    
    return f"""# Warp2Api 项目分析

## 项目概述
Warp2Api是一个Python桥接服务，为Warp AI提供OpenAI和Claude API兼容性。

## 核心功能
- **API兼容性**: 支持OpenAI Chat Completions和Claude Messages API格式
- **工具调用**: 支持Computer Use和Code Execution工具
- **流式响应**: 实时流式数据传输
- **多模态**: 支持文本和图片处理
- **认证系统**: 灵活的API密钥认证

## 技术架构

### 服务层
- **API服务器** (端口28889): 处理HTTP API请求
- **桥接服务器** (端口28888): 处理Warp protobuf通信

### 核心模块
- `protobuf2openai/`: API兼容层实现
- `warp2protobuf/`: Warp通信层
- `proto/`: Protobuf协议定义

## 主要文件说明

### API层 (protobuf2openai/)
- `app.py`: FastAPI应用入口
- `router.py`: OpenAI API路由
- `claude_router.py`: Claude API路由  
- `models.py`: 数据模型定义
- `helpers.py`: 工具函数
- `local_tools.py`: 本地工具执行

### 通信层 (warp2protobuf/)
- `core/auth.py`: JWT认证管理
- `core/session.py`: 会话管理
- `api/protobuf_routes.py`: Protobuf API路由

## 使用指南

### 快速启动
```bash
# 安装依赖
uv sync

# 启动服务
./start.sh

# 或手动启动
uv run python server.py --port 28888
uv run python openai_compat.py --port 28889
```

### API配置
- **Base URL**: http://localhost:28889/v1
- **API Key**: 0000
- **支持模型**: claude-3-5-sonnet-20241022, claude-4-sonnet, gpt-4o

### 使用示例
```bash
# Claude API
curl -H 'x-api-key: 0000' \\
     -H 'Content-Type: application/json' \\
     -d '{{"model":"claude-3-5-sonnet-20241022","messages":[{{"role":"user","content":"Hello"}}],"max_tokens":100}}' \\
     http://localhost:28889/v1/messages

# OpenAI API  
curl -H 'Authorization: Bearer 0000' \\
     -H 'Content-Type: application/json' \\
     -d '{{"model":"claude-4-sonnet","messages":[{{"role":"user","content":"Hello"}}],"max_tokens":100}}' \\
     http://localhost:28889/v1/chat/completions
```

## 工具支持

### Computer Use工具
```bash
# 启用方式
anthropic-beta: computer-use-2024-10-22

# 支持操作
- screenshot: 截取屏幕
- click: 鼠标点击
- type: 键盘输入
- scroll: 页面滚动
- key: 按键操作
```

### Code Execution工具
```bash
# 启用方式  
anthropic-beta: code-execution-2025-08-25

# 支持命令
- view: 查看文件/目录
- create: 创建文件
- str_replace: 替换文本
- undo_edit: 撤销编辑
```

## 开发说明

### 环境要求
- Python 3.13+
- uv包管理器
- Warp AI账户(可选，有匿名模式)

### 配置文件(.env)
```env
API_TOKEN=0000
WARP_JWT=your_jwt_token_here
WARP_REFRESH_TOKEN=your_refresh_token_here
```

### 测试
```bash
# 基础API测试
python test_claude_api.py

# 工具调用测试
python test_claude_code_tools.py

# 完整功能测试
python test_claude_comprehensive.py
```

## 限制说明

### 匿名账户限制
- ✅ 基础对话完全可用
- ✅ 工具调用格式支持
- ⚠️ 复杂工具执行可能受限
- ❌ 图片处理需要付费账户

### 性能考虑
- 建议max_tokens设置在100-1000范围
- 复杂任务建议分步执行
- 长文件读取会自动截断

## 故障排除

### 常见问题
1. **401错误**: 检查API_TOKEN环境变量
2. **连接超时**: 确保两个服务都在运行
3. **工具调用失败**: 检查anthropic-beta头设置
4. **文件操作错误**: 确保路径正确且有权限

### 调试命令
```bash
# 检查服务状态
curl http://localhost:28888/healthz  # 桥接服务器
curl http://localhost:28889/healthz  # API服务器

# 检查模型列表
curl -H 'x-api-key: 0000' http://localhost:28889/v1/messages/models
```

## 更新日志

### 最新更新
- 添加了Claude Code专用优化
- 修复了目录读取错误
- 改进了工具执行可靠性
- 增强了错误处理机制

---

**项目状态**: 生产就绪 ✅  
**文档版本**: 1.0  
**最后更新**: {time.strftime('%Y-%m-%d %H:%M:%S')}  
**生成工具**: Claude Code  
"""

def create_direct_response(intercepted_results: List[Dict[str, Any]], original_packet: Dict[str, Any]) -> Dict[str, Any]:
    """创建直接响应，绕过Warp后端"""
    
    content_blocks = []
    
    # 添加说明文本
    content_blocks.append({
        "type": "text",
        "text": "我来帮您执行这些操作："
    })
    
    # 处理每个拦截的工具结果
    for result_info in intercepted_results:
        tool_name = result_info["tool"]
        params = result_info["params"] 
        result = result_info["result"]
        
        # 添加工具调用块
        content_blocks.append({
            "type": "tool_use",
            "id": f"toolu_{uuid.uuid4().hex[:16]}",
            "name": tool_name,
            "input": params
        })
        
        # 添加工具结果块
        if result.get("success"):
            content = result.get("content", result.get("message", "操作完成"))
        else:
            content = f"错误: {result.get('error', '操作失败')}"
        
        content_blocks.append({
            "type": "tool_result", 
            "tool_use_id": f"toolu_{uuid.uuid4().hex[:16]}",
            "content": content
        })
    
    # 返回直接响应格式
    return {
        "type": "direct_response",
        "content_blocks": content_blocks,
        "bypass_warp": True
    }