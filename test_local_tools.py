#!/usr/bin/env python3
"""
测试本地工具执行功能
"""

import sys
sys.path.append('/workspace')

from protobuf2openai.local_tools import execute_tool_locally

def test_local_file_operations():
    """测试本地文件操作"""
    print("🔧 本地工具执行测试")
    print("="*50)
    
    # 测试1: 创建文件
    print("\n[测试1] 创建文件")
    result1 = execute_tool_locally("str_replace_based_edit_tool", {
        "command": "create",
        "path": "test_local_tool.txt",
        "file_text": "这是本地工具创建的测试文件\n当前时间: 2025-09-25\n"
    })
    
    print(f"结果: {result1}")
    
    # 检查文件是否真的创建了
    import os
    if os.path.exists("/workspace/test_local_tool.txt"):
        print("✅ 文件创建成功")
        
        # 测试2: 查看文件
        print("\n[测试2] 查看文件")
        result2 = execute_tool_locally("str_replace_based_edit_tool", {
            "command": "view",
            "path": "test_local_tool.txt"
        })
        
        print(f"结果: {result2}")
        
        # 测试3: 替换文本
        print("\n[测试3] 替换文本")
        result3 = execute_tool_locally("str_replace_based_edit_tool", {
            "command": "str_replace",
            "path": "test_local_tool.txt",
            "old_str": "2025-09-25",
            "new_str": "2025-09-25 (已修改)"
        })
        
        print(f"结果: {result3}")
        
        # 验证修改
        with open("/workspace/test_local_tool.txt", 'r') as f:
            content = f.read()
            print(f"文件内容: {content}")
            
        return True
    else:
        print("❌ 文件创建失败")
        return False

def test_local_computer_operations():
    """测试本地计算机操作"""
    print("\n🖥️ 本地计算机操作测试")
    print("="*50)
    
    # 测试截图
    print("\n[测试] 截图操作")
    result = execute_tool_locally("computer_20241022", {
        "action": "screenshot"
    })
    
    print(f"结果: {result}")
    return result.get("success", False)

def main():
    """主测试函数"""
    print("🧪 本地工具执行功能验证")
    print("="*60)
    
    file_ops_ok = test_local_file_operations()
    computer_ops_ok = test_local_computer_operations()
    
    print("\n" + "="*60)
    print("📊 测试结果")
    print("="*60)
    
    print(f"文件操作: {'✅ 正常' if file_ops_ok else '❌ 失败'}")
    print(f"计算机操作: {'✅ 正常' if computer_ops_ok else '❌ 失败'}")
    
    if file_ops_ok and computer_ops_ok:
        print("\n🎉 本地工具执行功能正常！")
        print("这应该能解决Claude Code的执行中断问题")
    else:
        print("\n⚠️ 本地工具执行有问题，需要调试")

if __name__ == "__main__":
    main()