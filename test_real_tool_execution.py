#!/usr/bin/env python3
"""
测试工具是否真的在后端执行
检查是否只是AI"假装"调用了工具
"""

import json
import requests
import time

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def test_screenshot_reality():
    """测试截图工具是否真的执行"""
    print("📸 测试截图工具的真实执行")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 使用OpenAI端点（cline使用的）
    print("\n[测试] OpenAI端点 - 截图工具")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "claude-4-sonnet",
            "messages": [
                {"role": "user", "content": "请截取屏幕截图。重要：请告诉我截图文件的确切路径和文件名。"}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "computer_20241022",
                        "description": "Computer operations",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["screenshot"]}
                            },
                            "required": ["action"]
                        }
                    }
                }
            ],
            "max_tokens": 300
        },
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get('choices', [{}])[0].get('message', {})
        content = message.get('content', '')
        tool_calls = message.get('tool_calls', [])
        
        print(f"✅ 工具调用数量: {len(tool_calls)}")
        print(f"📄 AI回复: {content}")
        
        # 分析AI是否提供了具体的文件信息
        mentions_file_path = any(phrase in content.lower() for phrase in [
            "screenshot", "file", "path", "saved", ".png", ".jpg",
            "截图", "文件", "路径", "保存"
        ])
        
        gives_specific_info = any(phrase in content.lower() for phrase in [
            "screenshot_", "image_", "/", "\\", ".png", ".jpg",
            "具体", "确切", "路径"
        ])
        
        print(f"✅ 提到文件相关: {mentions_file_path}")
        print(f"✅ 给出具体信息: {gives_specific_info}")
        
        # 关键判断：AI是否表现得像真的执行了工具
        acts_like_executed = gives_specific_info or "successfully" in content.lower()
        
        return {
            "called": len(tool_calls) > 0,
            "acts_executed": acts_like_executed,
            "response": content
        }
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return {"called": False, "acts_executed": False, "response": ""}

def test_file_creation_reality():
    """测试文件创建工具的真实执行"""
    print("\n📝 测试文件创建工具的真实执行")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "code-execution-2025-08-25",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    print("\n[测试] Claude端点 - 文件创建工具")
    
    response = requests.post(
        f"{BASE_URL}/v1/messages",
        json={
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {"role": "user", "content": "创建一个名为test_reality.txt的文件，内容是当前时间戳。请告诉我文件的确切路径。"}
            ],
            "max_tokens": 300
        },
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        content_blocks = result.get('content', [])
        tool_uses = [block for block in content_blocks if block.get('type') == 'tool_use']
        text_content = ''.join([block.get('text', '') for block in content_blocks if block.get('type')=='text'])
        
        print(f"✅ 工具调用数量: {len(tool_uses)}")
        print(f"📄 AI回复: {text_content}")
        
        if tool_uses:
            tool = tool_uses[0]
            print(f"   工具: {tool.get('name')}")
            print(f"   命令: {tool.get('input', {}).get('command')}")
            print(f"   文件路径: {tool.get('input', {}).get('path')}")
        
        # 检查AI是否表现得像真的创建了文件
        mentions_specific_path = any(phrase in text_content.lower() for phrase in [
            "/", "\\", "test_reality.txt", "path", "directory",
            "路径", "目录", "文件夹"
        ])
        
        claims_success = any(phrase in text_content.lower() for phrase in [
            "created", "successfully", "saved", "成功", "已创建", "创建了"
        ])
        
        print(f"✅ 提到具体路径: {mentions_specific_path}")
        print(f"✅ 声称成功: {claims_success}")
        
        return {
            "called": len(tool_uses) > 0,
            "acts_executed": mentions_specific_path or claims_success,
            "response": text_content
        }
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return {"called": False, "acts_executed": False, "response": ""}

def analyze_execution_patterns():
    """分析工具执行模式"""
    print("\n🔍 工具执行模式分析")
    print("="*60)
    
    screenshot_result = test_screenshot_reality()
    file_result = test_file_creation_reality()
    
    print(f"\n📊 执行模式分析:")
    print(f"截图工具 - 调用: {'✅' if screenshot_result['called'] else '❌'}, 表现像执行: {'✅' if screenshot_result['acts_executed'] else '❌'}")
    print(f"文件工具 - 调用: {'✅' if file_result['called'] else '❌'}, 表现像执行: {'✅' if file_result['acts_executed'] else '❌'}")
    
    # 关键判断
    if screenshot_result['called'] and file_result['called']:
        if screenshot_result['acts_executed'] and file_result['acts_executed']:
            print("\n✅ 工具调用和执行都正常")
            print("这与用户观察不符，需要进一步调查")
        else:
            print("\n🎯 发现问题！")
            print("✅ 工具能够调用")
            print("❌ 但AI表现得像没有真正执行")
            print("\n这可能解释了用户的观察:")
            print("- cline可能不依赖工具的实际执行结果")
            print("- Claude API用户期望看到真实的执行效果")
    
    return {
        "screenshot": screenshot_result,
        "file": file_result
    }

def test_cline_simulation():
    """模拟cline的使用方式"""
    print("\n🤖 模拟cline的使用方式")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # cline通常这样使用：要求AI生成代码，而不是直接执行操作
    print("\n[模拟] cline风格的请求")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "claude-4-sonnet",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a helpful coding assistant. Generate code to accomplish tasks."
                },
                {
                    "role": "user", 
                    "content": "我需要一个Python脚本来截取屏幕截图。请生成代码。"
                }
            ],
            "max_tokens": 400
        },
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        print(f"📄 AI回复: {content[:300]}...")
        
        # 检查是否生成了代码
        has_code = any(phrase in content for phrase in [
            "import", "def", "screenshot", "PIL", "pyautogui", "opencv"
        ])
        
        print(f"✅ 生成了代码: {has_code}")
        
        if has_code:
            print("\n💡 这可能解释了差异：")
            print("✅ cline主要用于代码生成，不依赖工具实际执行")
            print("❌ Claude API用户期望工具真实执行")
            return True
    else:
        print(f"❌ 请求失败: {response.status_code}")
    
    return False

def main():
    """主分析函数"""
    print("🕵️ 深度分析cline/kilo vs Claude的真实差异")
    print("="*70)
    print("目标：找出为什么用户体验不同")
    
    # 分析执行模式
    execution_analysis = analyze_execution_patterns()
    
    # 模拟cline使用方式
    cline_simulation = test_cline_simulation()
    
    print("\n" + "="*70)
    print("🎯 差异分析结论")
    print("="*70)
    
    screenshot_works = execution_analysis['screenshot']['acts_executed']
    file_works = execution_analysis['file']['acts_executed']
    
    if screenshot_works and file_works:
        print("🤔 我们的测试显示工具执行正常")
        print("但用户体验不同，可能的原因:")
        print("1. 测试场景与实际使用场景不同")
        print("2. cline有特殊的处理方式")
        print("3. 用户对'正常'的定义不同")
    else:
        print("🎯 验证了用户观察！")
        print("❌ 工具调用了但没有真正执行")
        print("✅ 这解释了为什么Claude用户觉得有问题")
    
    if cline_simulation:
        print("\n💡 关键洞察：")
        print("✅ cline主要用于代码生成，不依赖工具执行")
        print("❌ Claude API用户期望真实的工具执行")
        print("🎯 这就是差异的根本原因！")

if __name__ == "__main__":
    main()