#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多模态功能脚本 - 带认证
"""

import base64
import requests
import json

# API配置
API_BASE_URL = "http://localhost:28889"
API_KEY = "0000"  # 根据README.md中的说明，使用默认API token

def create_test_image():
    """创建一个简单的测试图片(1x1像素的PNG)"""
    # 最小的PNG图片数据 (1x1 pixel, red)
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

def make_request(payload):
    """发送请求"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    return requests.post(
        f"{API_BASE_URL}/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=30
    )

def test_simple_text():
    """测试基本文本功能"""
    print("\n📝 测试基本文本功能...")
    
    payload = {
        "model": "claude-4-sonnet", 
        "messages": [
            {"role": "user", "content": "你好，请用一句话介绍你自己"}
        ],
        "stream": False
    }
    
    try:
        response = make_request(payload)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 基本文本功能正常!")
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_multimodal_support():
    """测试多模态支持"""
    print("\n🔍 测试多模态图像识别支持...")
    
    # 创建测试图片
    test_image_b64 = create_test_image()
    
    # 构建包含图像的请求
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": "请描述这张图片的内容，这是什么颜色的像素？"},
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
        response = make_request(payload)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查是否真的处理了图像
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                print(f"\n🔍 AI回复内容分析:")
                print(f"回复内容: {content}")
                
                # 检查关键词
                image_keywords = ["图", "image", "picture", "像素", "pixel", "颜色", "color", "红", "red"]
                found_keywords = [kw for kw in image_keywords if kw in content.lower()]
                
                if found_keywords:
                    print(f"✅ 发现图像相关关键词: {found_keywords}")
                    print("✅ 可能支持图像识别功能")
                    return True
                else:
                    print("❌ 响应中没有图像相关关键词")
                    print("❌ 不支持图像识别或图像内容被忽略")
                    return False
            else:
                print("❌ 响应格式异常")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_tools_support():
    """测试工具调用支持"""
    print("\n🔧 测试工具调用支持...")
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "请使用calculator工具计算25*4等于多少"}
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
        response = make_request(payload)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查是否有工具调用
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                message = choice.get("message", {})
                
                if "tool_calls" in message and message["tool_calls"]:
                    print("✅ 支持工具调用!")
                    print(f"工具调用详情: {message['tool_calls']}")
                    return True
                else:
                    content = message.get("content", "")
                    print(f"🔍 AI回复内容: {content}")
                    print("❌ 没有返回工具调用，可能工具调用被禁用或不支持")
                    return False
            else:
                print("❌ 响应格式异常")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_complex_multimodal():
    """测试复杂多模态内容"""
    print("\n🖼️ 测试复杂多模态内容...")
    
    # 创建另一个测试图片
    test_image_b64 = create_test_image()
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "分析这张图片"},
                    {
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/png;base64,{test_image_b64}"}
                    },
                    {"type": "text", "text": "并告诉我这是什么"}
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response = make_request(payload)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"AI回复: {content}")
            
            # 更严格的检查
            if any(word in content.lower() for word in ["图", "image", "pixel", "红色", "颜色"]):
                print("✅ 复杂多模态内容处理正常")
                return True
            else:
                print("❌ 复杂多模态内容处理失败")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Warp2Api 功能详细测试")
    print("=" * 60)
    
    # 测试服务器连通性
    try:
        health_response = requests.get(f"{API_BASE_URL}/healthz", timeout=5)
        if health_response.status_code == 200:
            print("✅ 服务器连通正常")
        else:
            print(f"❌ 服务器健康检查失败: {health_response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        exit(1)
    
    results = {}
    
    # 测试基本功能
    results['text'] = test_simple_text()
    
    # 测试多模态
    results['multimodal'] = test_multimodal_support()
    
    # 测试复杂多模态
    results['complex_multimodal'] = test_complex_multimodal()
    
    # 测试工具调用
    results['tools'] = test_tools_support()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    print(f"📝 基本文本功能: {'✅ 支持' if results['text'] else '❌ 不支持'}")
    print(f"🖼️ 多模态图像识别: {'✅ 支持' if results['multimodal'] else '❌ 不支持'}")
    print(f"🖼️ 复杂多模态处理: {'✅ 支持' if results['complex_multimodal'] else '❌ 不支持'}")
    print(f"🔧 工具调用功能: {'✅ 支持' if results['tools'] else '❌ 不支持'}")
    
    # 最终结论
    print("\n🎯 最终结论:")
    if results['multimodal'] or results['complex_multimodal']:
        print("✅ 项目确实支持多模态功能")
    else:
        print("❌ 项目不支持多模态功能 - 图片会被忽略")
        
    if results['tools']:
        print("✅ 项目确实支持工具调用功能")
    else:
        print("❌ 项目不支持工具调用功能 - 工具调用被禁用")
        
    print("=" * 60)