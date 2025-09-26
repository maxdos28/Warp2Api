#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试图像传递过程 - 检查每一步的数据流
"""

import base64
import requests
import json

# API配置
API_BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def create_simple_test_image():
    """创建一个简单的测试图像"""
    # 最小的PNG图片 (1x1 red pixel)
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

def test_openai_request_structure():
    """测试OpenAI格式的请求结构"""
    print("🔍 测试OpenAI格式请求结构...")
    
    test_image_b64 = create_simple_test_image()
    
    # 构建标准OpenAI格式请求
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "图像调试测试"},
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
    
    print("📦 构建的请求结构:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # 先测试直接发送到bridge服务器
        print("\n🌉 测试发送到bridge服务器...")
        bridge_response = requests.post(
            "http://localhost:28888/api/warp/send",
            json={"json_data": payload, "message_type": "warp.multi_agent.v1.Request"},
            timeout=30
        )
        
        print(f"Bridge响应状态: {bridge_response.status_code}")
        if bridge_response.status_code != 200:
            print(f"Bridge错误: {bridge_response.text}")
        else:
            bridge_result = bridge_response.json()
            print(f"Bridge响应: {json.dumps(bridge_result, indent=2, ensure_ascii=False)}")
        
        print("\n🔄 测试通过OpenAI兼容层...")
        # 再测试通过OpenAI兼容层
        openai_response = requests.post(
            f"{API_BASE_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"OpenAI API响应状态: {openai_response.status_code}")
        if openai_response.status_code != 200:
            print(f"OpenAI API错误: {openai_response.text}")
        else:
            openai_result = openai_response.json()
            print(f"OpenAI API响应: {json.dumps(openai_result, indent=2, ensure_ascii=False)}")
        
        return openai_response.status_code == 200
        
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_anthropic_format():
    """测试Anthropic格式"""
    print("\n🤖 测试Anthropic格式...")
    
    test_image_b64 = create_simple_test_image()
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "图像调试测试 - Anthropic格式"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": test_image_b64
                        }
                    }
                ]
            }
        ],
        "stream": False
    }
    
    print("📦 Anthropic格式请求:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Anthropic格式响应状态: {response.status_code}")
        if response.status_code != 200:
            print(f"错误: {response.text}")
            return False
        else:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"AI回答: {content}")
            return True
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_simple_text_baseline():
    """测试纯文本基线"""
    print("\n📝 测试纯文本基线...")
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "请回答：如果你能看到图像，你会如何描述它？"}
        ],
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"纯文本回答: {content}")
            return True
        else:
            print(f"纯文本测试失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🐛 图像传递调试测试")
    print("=" * 70)
    
    # 检查服务器
    try:
        health = requests.get(f"{API_BASE_URL}/healthz", timeout=5)
        if health.status_code == 200:
            print("✅ 服务器正常")
        else:
            print(f"❌ 服务器异常: {health.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        exit(1)
    
    # 运行调试测试
    results = {}
    results['text_baseline'] = test_simple_text_baseline()
    results['openai_format'] = test_openai_request_structure()
    results['anthropic_format'] = test_anthropic_format()
    
    print("\n" + "=" * 70)
    print("🔍 调试结果总结")
    print("=" * 70)
    print(f"📝 纯文本基线: {'✅ 正常' if results['text_baseline'] else '❌ 异常'}")
    print(f"🔄 OpenAI格式: {'✅ 正常' if results['openai_format'] else '❌ 异常'}")
    print(f"🤖 Anthropic格式: {'✅ 正常' if results['anthropic_format'] else '❌ 异常'}")
    
    if not any(results.values()):
        print("\n❌ 所有测试都失败了，可能是服务器配置问题")
    elif results['text_baseline'] and not (results['openai_format'] or results['anthropic_format']):
        print("\n❌ 图像处理代码有问题，文本正常但图像失败")
    elif any([results['openai_format'], results['anthropic_format']]):
        print("\n⚠️ 部分图像格式工作，需要进一步测试识别准确性")
    
    print("=" * 70)