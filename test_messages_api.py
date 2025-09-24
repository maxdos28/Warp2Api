#!/usr/bin/env python3
"""
测试 /v1/messages 接口的图片支持功能

该脚本测试新创建的 Anthropic Messages API 兼容接口
"""

import requests
import json
import base64
import sys
from typing import Dict, Any, List


def create_test_image() -> str:
    """创建一个测试用的小图片（1x1像素红色PNG）"""
    # 1x1像素红色PNG的base64数据
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="


def test_text_only_message(base_url: str) -> Dict[str, Any]:
    """测试纯文本消息"""
    print("\n=== 测试1: 纯文本消息 ===")
    
    request_data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [
            {
                "role": "user",
                "content": "Hello, can you see this message?"
            }
        ],
        "max_tokens": 100,
        "stream": False
    }
    
    print("请求数据:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{base_url}/v1/messages",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return {"status": "success", "data": result}
        else:
            print(f"错误响应: {response.text}")
            return {"status": "error", "message": response.text}
            
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return {"status": "error", "message": str(e)}


def test_image_message(base_url: str) -> Dict[str, Any]:
    """测试包含图片的消息"""
    print("\n=== 测试2: 图片消息 (Anthropic 格式) ===")
    
    image_base64 = create_test_image()
    
    request_data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What can you see in this image?"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_base64
                        }
                    }
                ]
            }
        ],
        "max_tokens": 200,
        "stream": False
    }
    
    print("请求数据结构:")
    # 打印简化版本（截断base64数据）
    display_data = json.loads(json.dumps(request_data))
    for msg in display_data["messages"]:
        if isinstance(msg["content"], list):
            for content in msg["content"]:
                if content.get("type") == "image":
                    content["source"]["data"] = content["source"]["data"][:20] + "...[truncated]"
    print(json.dumps(display_data, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{base_url}/v1/messages",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return {"status": "success", "data": result}
        else:
            print(f"错误响应: {response.text}")
            return {"status": "error", "message": response.text}
            
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return {"status": "error", "message": str(e)}


def test_multiple_images(base_url: str) -> Dict[str, Any]:
    """测试多张图片的消息"""
    print("\n=== 测试3: 多张图片消息 ===")
    
    image_base64 = create_test_image()
    
    request_data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Compare these two images:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": " and "
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64  # 使用相同图片但不同MIME类型
                        }
                    },
                    {
                        "type": "text",
                        "text": ". What are the differences?"
                    }
                ]
            }
        ],
        "max_tokens": 200,
        "stream": False
    }
    
    print("消息内容段数:", len(request_data["messages"][0]["content"]))
    print("- 文本段: 3")
    print("- 图片段: 2")
    
    try:
        response = requests.post(
            f"{base_url}/v1/messages",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return {"status": "success", "data": result}
        else:
            print(f"错误响应: {response.text}")
            return {"status": "error", "message": response.text}
            
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return {"status": "error", "message": str(e)}


def test_with_system_prompt(base_url: str) -> Dict[str, Any]:
    """测试带系统提示的图片消息"""
    print("\n=== 测试4: 带系统提示的图片消息 ===")
    
    image_base64 = create_test_image()
    
    request_data = {
        "model": "claude-3-sonnet-20240229",
        "system": "You are an expert image analyst. Always describe images in technical detail.",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this image technically:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_base64
                        }
                    }
                ]
            }
        ],
        "max_tokens": 200,
        "stream": False
    }
    
    print(f"系统提示: {request_data['system'][:50]}...")
    print(f"包含图片: 是")
    
    try:
        response = requests.post(
            f"{base_url}/v1/messages",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return {"status": "success", "data": result}
        else:
            print(f"错误响应: {response.text}")
            return {"status": "error", "message": response.text}
            
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return {"status": "error", "message": str(e)}


def test_openai_format_compatibility(base_url: str) -> Dict[str, Any]:
    """测试 OpenAI 格式的兼容性（通过 /v1/chat/completions）"""
    print("\n=== 测试5: OpenAI 格式图片 (通过 /v1/chat/completions) ===")
    
    image_base64 = create_test_image()
    
    request_data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image:"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "stream": False
    }
    
    print("使用 OpenAI 格式 (image_url)")
    
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return {"status": "success", "data": result}
        else:
            print(f"错误响应: {response.text}")
            return {"status": "error", "message": response.text}
            
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return {"status": "error", "message": str(e)}


def main():
    """主测试函数"""
    # 默认服务器地址
    base_url = "http://localhost:28889"
    
    # 允许从命令行参数指定服务器地址
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    
    print(f"""
╔══════════════════════════════════════════════════════╗
║     /v1/messages 接口图片支持功能测试               ║
╚══════════════════════════════════════════════════════╝

服务器地址: {base_url}

测试内容:
1. 纯文本消息
2. 单张图片消息 (Anthropic 格式)
3. 多张图片消息
4. 带系统提示的图片消息
5. OpenAI 格式兼容性测试
""")
    
    # 检查服务器是否运行
    print("检查服务器连接...")
    try:
        response = requests.get(f"{base_url}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接成功\n")
        else:
            print(f"⚠️ 服务器响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("\n请确保服务器正在运行:")
        print("  python openai_compat.py --port 28889")
        return
    
    # 运行测试
    test_results = []
    
    # 测试1: 纯文本
    result = test_text_only_message(base_url)
    test_results.append(("纯文本消息", result["status"]))
    
    # 测试2: 单张图片
    result = test_image_message(base_url)
    test_results.append(("单张图片 (Anthropic格式)", result["status"]))
    
    # 测试3: 多张图片
    result = test_multiple_images(base_url)
    test_results.append(("多张图片", result["status"]))
    
    # 测试4: 系统提示
    result = test_with_system_prompt(base_url)
    test_results.append(("带系统提示的图片", result["status"]))
    
    # 测试5: OpenAI格式
    result = test_openai_format_compatibility(base_url)
    test_results.append(("OpenAI格式兼容性", result["status"]))
    
    # 打印测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for test_name, status in test_results:
        icon = "✅" if status == "success" else "❌"
        print(f"{icon} {test_name}: {status}")
    
    success_count = sum(1 for _, status in test_results if status == "success")
    total_count = len(test_results)
    
    print(f"\n总计: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过! /v1/messages 接口图片支持功能正常工作!")
    else:
        print("\n⚠️ 部分测试失败，请检查日志以获取详细信息。")


if __name__ == "__main__":
    main()