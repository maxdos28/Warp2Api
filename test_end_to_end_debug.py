#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端调试测试 - 追踪整个图像处理流程
"""

import base64
import requests
import json
import sys
sys.path.append('/workspace')

from protobuf2openai.json_encoder import serialize_packet_for_json

# API配置
API_BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def create_test_image():
    """创建测试图像"""
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

def test_with_verbose_logging():
    """测试并启用详细日志"""
    print("🔍 端到端调试测试...")
    
    test_image_b64 = create_test_image()
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请分析这张图像并告诉我你看到了什么"},
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
    
    print("📦 发送的请求结构:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print("\n🚀 发送请求到OpenAI兼容API...")
        response = requests.post(
            f"{API_BASE_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print(f"📄 完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 分析响应内容
            content = result["choices"][0]["message"]["content"]
            print(f"\n🤖 AI回复内容:")
            print(f"{content}")
            
            # 详细分析关键词
            analysis_keywords = {
                "图像识别": ["图", "image", "picture", "照片", "图片"],
                "颜色": ["红", "green", "blue", "颜色", "color", "色彩"],
                "形状": ["方", "square", "circle", "triangle", "形状", "shape"],
                "像素": ["像素", "pixel"],
                "看到": ["看到", "see", "观察", "observe", "识别", "recognize"],
                "没有图像": ["没有图", "no image", "don't see", "看不到", "not see"]
            }
            
            found_categories = {}
            for category, keywords in analysis_keywords.items():
                found_words = [kw for kw in keywords if kw in content.lower()]
                if found_words:
                    found_categories[category] = found_words
            
            print(f"\n📊 关键词分析:")
            for category, words in found_categories.items():
                print(f"  {category}: {words}")
            
            if "没有图像" in found_categories:
                print("\n❌ AI明确表示没有看到图像")
                return False
            elif any(cat in found_categories for cat in ["图像识别", "颜色", "形状", "像素"]):
                print("\n✅ AI提到了图像相关内容")
                return True
            else:
                print("\n⚠️ AI回复内容不明确")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_bridge_directly():
    """直接测试bridge服务器"""
    print("\n🌉 直接测试Bridge服务器...")
    
    test_image_b64 = create_test_image()
    
    # 手动构建数据包，但使用正确的序列化
    packet = {
        "task_context": {
            "tasks": [{
                "id": "test_task",
                "description": "图像测试",
                "status": {"in_progress": {}},
                "messages": []
            }],
            "active_task_id": "test_task"
        },
        "input": {
            "context": {
                "images": [{
                    "data": base64.b64decode(test_image_b64),  # 这会被序列化器处理
                    "mime_type": "image/png"
                }]
            },
            "user_inputs": {
                "inputs": [{
                    "user_query": {
                        "query": "请描述这张图像",
                        "referenced_attachments": {
                            "IMAGE_1": {
                                "drive_object": {
                                    "uid": "test_img_001",
                                    "object_payload": {
                                        "generic_string_object": {
                                            "payload": f"data:image/png;base64,{test_image_b64}",
                                            "object_type": "image"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }]
            }
        },
        "settings": {
            "model_config": {
                "base": "claude-4-sonnet",
                "planning": "o3",
                "coding": "auto"
            },
            "supports_parallel_tool_calls": True,
            "supported_tools": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        },
        "metadata": {
            "logging": {
                "is_autodetected_user_query": True,
                "entrypoint": "USER_INITIATED"
            }
        }
    }
    
    print(f"🔧 原始数据包结构 (部分):")
    # 只显示关键部分，避免打印大量二进制数据
    debug_packet = dict(packet)
    if "input" in debug_packet and "context" in debug_packet["input"] and "images" in debug_packet["input"]["context"]:
        images_info = []
        for img in debug_packet["input"]["context"]["images"]:
            images_info.append({
                "mime_type": img["mime_type"],
                "data_type": type(img["data"]).__name__,
                "data_length": len(img["data"]) if hasattr(img["data"], "__len__") else "unknown"
            })
        debug_packet["input"]["context"]["images"] = images_info
    
    print(json.dumps(debug_packet, indent=2, ensure_ascii=False))
    
    try:
        print("\n🔄 序列化数据包...")
        serialized_packet = serialize_packet_for_json(packet)
        print("✅ 序列化成功")
        
        print("\n📤 发送到bridge...")
        response = requests.post(
            "http://localhost:28888/api/warp/send",
            json={"json_data": serialized_packet, "message_type": "warp.multi_agent.v1.Request"},
            timeout=30
        )
        
        print(f"📊 Bridge响应状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"📄 Bridge响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            response_text = result.get("response", "")
            if any(word in response_text.lower() for word in ["图", "image", "看到", "red", "颜色"]):
                print("✅ Bridge响应提到了图像相关内容")
                return True
            else:
                print("❌ Bridge响应没有提到图像")
                return False
        else:
            print(f"❌ Bridge错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Bridge测试异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("端到端图像处理调试测试")
    print("=" * 80)
    
    # 检查服务器
    try:
        health = requests.get(f"{API_BASE_URL}/healthz", timeout=5)
        if health.status_code == 200:
            print("✅ OpenAI API服务器正常")
        else:
            print(f"❌ OpenAI API服务器异常: {health.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ 无法连接到OpenAI API服务器: {e}")
        exit(1)
    
    try:
        bridge_health = requests.get("http://localhost:28888/healthz", timeout=5)
        if bridge_health.status_code == 200:
            print("✅ Bridge服务器正常")
        else:
            print(f"❌ Bridge服务器异常: {bridge_health.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到Bridge服务器: {e}")
    
    results = {}
    
    # 运行测试
    results['openai_api'] = test_with_verbose_logging()
    results['bridge_direct'] = test_bridge_directly()
    
    print("\n" + "=" * 80)
    print("📊 端到端测试结果")
    print("=" * 80)
    print(f"🔄 OpenAI API层: {'✅ 工作' if results['openai_api'] else '❌ 不工作'}")
    print(f"🌉 Bridge直接测试: {'✅ 工作' if results['bridge_direct'] else '❌ 不工作'}")
    
    if not any(results.values()):
        print("\n❌ 所有层都有问题，图像数据完全无法传递")
    elif results['bridge_direct'] and not results['openai_api']:
        print("\n⚠️ Bridge层工作，但OpenAI API层有问题")
    elif not results['bridge_direct'] and results['openai_api']:
        print("\n⚠️ OpenAI API层工作，但Bridge层有问题")
    else:
        print("\n✅ 图像数据传递正常，可能是模型配置问题")
    
    print("=" * 80)