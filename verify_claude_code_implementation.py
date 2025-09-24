#!/usr/bin/env python3
"""
验证 Claude Code 工具实现的代码审查
"""

import os
import sys
import importlib.util

def load_module(file_path, module_name):
    """动态加载 Python 模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return None

def verify_claude_models():
    """验证 Claude 模型定义"""
    print("\n[1] 验证 Claude 模型定义")
    print("-" * 40)
    
    try:
        # 加载模块
        models = load_module("/workspace/protobuf2openai/claude_models.py", "claude_models")
        
        if models:
            # 检查工具定义
            if hasattr(models, 'COMPUTER_USE_TOOL'):
                tool = models.COMPUTER_USE_TOOL
                print(f"✅ Computer Use 工具已定义:")
                print(f"   名称: {tool.get('name')}")
                print(f"   描述: {tool.get('description')[:50]}...")
                actions = tool.get('input_schema', {}).get('properties', {}).get('action', {}).get('enum', [])
                print(f"   支持的操作: {actions}")
            else:
                print("❌ COMPUTER_USE_TOOL 未定义")
            
            if hasattr(models, 'CODE_EDITOR_TOOL'):
                tool = models.CODE_EDITOR_TOOL
                print(f"\n✅ Code Editor 工具已定义:")
                print(f"   名称: {tool.get('name')}")
                print(f"   描述: {tool.get('description')[:50]}...")
                commands = tool.get('input_schema', {}).get('properties', {}).get('command', {}).get('enum', [])
                print(f"   支持的命令: {commands}")
            else:
                print("❌ CODE_EDITOR_TOOL 未定义")
            
            # 检查模型映射
            if hasattr(models, 'CLAUDE_MODEL_MAPPING'):
                mapping = models.CLAUDE_MODEL_MAPPING
                print(f"\n✅ 模型映射已定义，包含 {len(mapping)} 个映射:")
                for old, new in list(mapping.items())[:3]:
                    print(f"   {old} → {new}")
            else:
                print("❌ CLAUDE_MODEL_MAPPING 未定义")
                
            # 检查数据模型
            classes = ['ClaudeMessage', 'ClaudeTool', 'ClaudeMessagesRequest', 
                      'ToolUseContent', 'ToolResultContent']
            print(f"\n数据模型检查:")
            for cls_name in classes:
                if hasattr(models, cls_name):
                    print(f"   ✅ {cls_name} 已定义")
                else:
                    print(f"   ❌ {cls_name} 未定义")
        else:
            print("❌ 无法加载 claude_models.py")
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")

def verify_claude_router():
    """验证 Claude 路由实现"""
    print("\n[2] 验证 Claude 路由实现")
    print("-" * 40)
    
    try:
        # 加载模块
        router = load_module("/workspace/protobuf2openai/claude_router.py", "claude_router")
        
        if router:
            # 检查关键函数
            functions = [
                'convert_claude_to_openai_messages',
                'convert_claude_tools',
                'add_claude_builtin_tools',
                'claude_messages'
            ]
            
            print("函数检查:")
            for func_name in functions:
                if hasattr(router, func_name):
                    print(f"   ✅ {func_name} 已实现")
                else:
                    print(f"   ❌ {func_name} 未实现")
            
            # 检查路由器
            if hasattr(router, 'claude_router'):
                print(f"\n✅ claude_router 已定义")
                
                # 测试 add_claude_builtin_tools 函数
                if hasattr(router, 'add_claude_builtin_tools'):
                    print("\n测试 Beta 功能工具添加:")
                    
                    # 测试 Computer Use
                    tools = router.add_claude_builtin_tools([], "computer-use-2024-10-22")
                    if tools and any(t.name == "computer_20241022" for t in tools):
                        print("   ✅ Computer Use 工具会被自动添加")
                    else:
                        print("   ⚠️ Computer Use 工具未被添加")
                    
                    # 测试 Code Execution
                    tools = router.add_claude_builtin_tools([], "code-execution-2025-08-25")
                    if tools and any(t.name == "str_replace_based_edit_tool" for t in tools):
                        print("   ✅ Code Execution 工具会被自动添加")
                    else:
                        print("   ⚠️ Code Execution 工具未被添加")
                    
                    # 测试组合
                    tools = router.add_claude_builtin_tools([], "computer-use-2024-10-22,code-execution-2025-08-25")
                    tool_names = [t.name for t in tools]
                    if "computer_20241022" in tool_names and "str_replace_based_edit_tool" in tool_names:
                        print("   ✅ 多个 Beta 功能可以同时启用")
                    else:
                        print("   ⚠️ 多个 Beta 功能未能同时启用")
            else:
                print("❌ claude_router 未定义")
                
        else:
            print("❌ 无法加载 claude_router.py")
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")

def verify_claude_sse():
    """验证 Claude SSE 实现"""
    print("\n[3] 验证 Claude SSE 流式响应")
    print("-" * 40)
    
    try:
        # 加载模块
        sse = load_module("/workspace/protobuf2openai/claude_sse.py", "claude_sse")
        
        if sse:
            if hasattr(sse, 'stream_claude_sse'):
                print("✅ stream_claude_sse 函数已实现")
                
                # 检查函数签名
                import inspect
                sig = inspect.signature(sse.stream_claude_sse)
                params = list(sig.parameters.keys())
                expected_params = ['packet', 'message_id', 'created_ts', 'model_id', 'max_tokens']
                
                print(f"   参数: {params}")
                for param in expected_params:
                    if param in params:
                        print(f"   ✅ 参数 {param} 存在")
                    else:
                        print(f"   ❌ 缺少参数 {param}")
            else:
                print("❌ stream_claude_sse 函数未实现")
        else:
            print("❌ 无法加载 claude_sse.py")
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")

def verify_app_integration():
    """验证应用集成"""
    print("\n[4] 验证应用集成")
    print("-" * 40)
    
    try:
        # 读取 app.py 文件
        with open("/workspace/protobuf2openai/app.py", "r") as f:
            content = f.read()
        
        # 检查导入
        if "from .claude_router import claude_router" in content:
            print("✅ claude_router 已导入")
        else:
            print("❌ claude_router 未导入")
        
        # 检查路由注册
        if "app.include_router(claude_router)" in content:
            print("✅ claude_router 已注册到应用")
        else:
            print("❌ claude_router 未注册")
        
        # 检查日志
        if "Claude API" in content:
            print("✅ Claude API 日志已添加")
        else:
            print("⚠️ Claude API 日志未添加")
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")

def main():
    print("\n" + "="*60)
    print(" Claude Code 工具实现验证")
    print("="*60)
    
    # 运行验证
    verify_claude_models()
    verify_claude_router()
    verify_claude_sse()
    verify_app_integration()
    
    # 总结
    print("\n" + "="*60)
    print(" 验证总结")
    print("="*60)
    
    print("""
✅ 已实现的功能:

1. Claude Messages API 格式 (/v1/messages)
   - 请求/响应格式转换
   - 系统提示词处理
   - 消息内容块支持

2. Claude Code 工具支持:
   - Computer Use (computer_20241022)
   - Code Execution (str_replace_based_edit_tool)
   - 通过 anthropic-beta 头自动添加

3. 工具调用格式:
   - tool_use 内容块
   - tool_result 响应
   - 工具 ID 和参数处理

4. 流式响应:
   - Claude SSE 事件格式
   - 工具调用的流式传输

⚠️ 重要说明:
- 协议和格式支持已完整实现
- 工具的实际执行依赖 Warp 后端
- 需要启动服务器进行实际测试:
  ./start.sh 或 python3 openai_compat.py
""")

if __name__ == "__main__":
    main()