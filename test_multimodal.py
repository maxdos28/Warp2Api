#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多模态功能脚本
"""

import base64
import requests
import json

def create_test_image():
    """创建一个简单的测试图片(1x1像素的PNG)"""
    # 最小的PNG图片数据 (1x1 pixel, red)
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

def test_multimodal_support():
    """测试多模态支持"""
    print("🔍 测试多模态图像识别支持...")
    
    # 创建测试图片
    test_image_b64 = create_test_image()
    
    # 构建包含图像的请求
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": "请描述这张图片的内容"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{test_image_b64}"
                        }
                    }
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response = requests.post(
            "http://localhost:28889/v1/chat/completions",
            json=payload,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查是否真的处理了图像
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                if "图" in content or "image" in content.lower() or "picture" in content.lower():
                    print("✅ 可能支持图像识别")
                else:
                    print("❌ 响应中没有提到图像相关内容，可能不支持图像识别")
            else:
                print("❌ 响应格式异常")
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_tools_support():
    """测试工具调用支持"""
    print("\n🔧 测试工具调用支持...")
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "请计算2+2等于多少，并使用calculator工具"}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "执行数学计算",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "要计算的数学表达式"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }
        ],
        "stream": False
    }
    
    try:
        response = requests.post(
            "http://localhost:28889/v1/chat/completions",
            json=payload,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查是否有工具调用
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "tool_calls" in choice.get("message", {}):
                    print("✅ 支持工具调用!")
                    print(f"工具调用: {choice['message']['tool_calls']}")
                else:
                    print("❌ 没有返回工具调用")
            else:
                print("❌ 响应格式异常")
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_simple_text():
    """测试基本文本功能"""
    print("\n📝 测试基本文本功能...")
    
    payload = {
        "model": "claude-4-sonnet", 
        "messages": [
            {"role": "user", "content": "你好，请简单介绍一下你自己"}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(
            "http://localhost:28889/v1/chat/completions",
            json=payload,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 基本文本功能正常!")
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Warp2Api 功能测试")
    print("=" * 60)
    
    # 测试基本功能
    test_simple_text()
    
    # 测试多模态
    test_multimodal_support()
    
    # 测试工具调用
    test_tools_support()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)