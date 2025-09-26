#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试protobuf结构 - 检查图像数据是否正确转换
"""

import base64
import requests
import json
import sys
import os

# 添加项目路径
sys.path.append('/workspace')

from protobuf2openai.helpers import normalize_content_to_list, extract_images_from_segments
from protobuf2openai.packets import packet_template, attach_user_and_tools_to_inputs
from protobuf2openai.models import ChatMessage

def create_test_image():
    """创建测试图像"""
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

def test_helper_functions():
    """测试辅助函数"""
    print("🧪 测试辅助函数...")
    
    test_image_b64 = create_test_image()
    
    # 模拟OpenAI格式的content
    content = [
        {"type": "text", "text": "测试图像"},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{test_image_b64}"
            }
        }
    ]
    
    print("🔍 测试 normalize_content_to_list...")
    normalized = normalize_content_to_list(content)
    print(f"标准化结果: {json.dumps(normalized, indent=2, ensure_ascii=False)}")
    
    print("\n🖼️ 测试 extract_images_from_segments...")
    images = extract_images_from_segments(normalized)
    print(f"提取的图像数量: {len(images)}")
    if images:
        for i, img in enumerate(images):
            print(f"图像 {i+1}:")
            print(f"  - 类型: {img['mime_type']}")
            print(f"  - 数据长度: {len(img['data'])}")
            print(f"  - 数据前50字符: {img['data'][:50]}...")
    else:
        print("❌ 没有提取到图像！")
    
    return len(images) > 0

def test_packet_building():
    """测试数据包构建"""
    print("\n📦 测试数据包构建...")
    
    test_image_b64 = create_test_image()
    
    # 创建ChatMessage对象
    message = ChatMessage(
        role="user",
        content=[
            {"type": "text", "text": "请描述这张图像"},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{test_image_b64}"
                }
            }
        ]
    )
    
    print(f"创建的消息: {message}")
    
    # 创建基础数据包
    packet = packet_template()
    print(f"基础数据包结构: {json.dumps(packet, indent=2, ensure_ascii=False)}")
    
    # 测试attach_user_and_tools_to_inputs函数
    history = [message]
    try:
        attach_user_and_tools_to_inputs(packet, history, None)
        print(f"\n添加用户输入后的数据包: {json.dumps(packet, indent=2, ensure_ascii=False)}")
        
        # 检查是否包含图像数据
        user_inputs = packet.get("input", {}).get("user_inputs", {}).get("inputs", [])
        if user_inputs:
            user_query = user_inputs[0].get("user_query", {})
            attachments = user_query.get("referenced_attachments", {})
            
            print(f"\n附件数量: {len(attachments)}")
            for key, attachment in attachments.items():
                print(f"附件 {key}: {type(attachment)}")
                if isinstance(attachment, dict):
                    print(f"  内容预览: {str(attachment)[:200]}...")
            
            # 检查input context中的images
            context_images = packet.get("input", {}).get("context", {}).get("images", [])
            print(f"\nContext中的图像数量: {len(context_images)}")
            
            return len(attachments) > 0 or len(context_images) > 0
        else:
            print("❌ 没有用户输入数据！")
            return False
            
    except Exception as e:
        print(f"❌ 数据包构建异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bridge_request():
    """测试直接发送到bridge的请求"""
    print("\n🌉 测试bridge请求...")
    
    test_image_b64 = create_test_image()
    
    # 手动构建包含图像的protobuf数据包
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
                    "data": base64.b64decode(test_image_b64),
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
    
    print(f"手动构建的数据包结构: {json.dumps(packet, indent=2, ensure_ascii=False, default=str)}")
    
    try:
        # 发送到bridge
        response = requests.post(
            "http://localhost:28888/api/warp/send",
            json={"json_data": packet, "message_type": "warp.multi_agent.v1.Request"},
            timeout=30
        )
        
        print(f"\nBridge响应状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Bridge响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 检查响应中是否提到了图像
            response_text = result.get("response", "")
            if any(word in response_text.lower() for word in ["图", "image", "看到", "see", "像素", "pixel"]):
                print("✅ 响应中提到了图像相关内容")
                return True
            else:
                print("❌ 响应中没有提到图像")
                return False
        else:
            print(f"Bridge错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Bridge请求异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🐛 Protobuf结构调试测试")
    print("=" * 70)
    
    results = {}
    
    # 测试各个环节
    results['helpers'] = test_helper_functions()
    results['packet_building'] = test_packet_building()
    results['bridge_request'] = test_bridge_request()
    
    print("\n" + "=" * 70)
    print("🔍 Protobuf调试结果")
    print("=" * 70)
    print(f"🧪 辅助函数: {'✅ 正常' if results['helpers'] else '❌ 异常'}")
    print(f"📦 数据包构建: {'✅ 正常' if results['packet_building'] else '❌ 异常'}")
    print(f"🌉 Bridge请求: {'✅ 正常' if results['bridge_request'] else '❌ 异常'}")
    
    success_count = sum(results.values())
    if success_count == 0:
        print("\n❌ 所有环节都有问题，图像数据完全无法传递")
    elif success_count == 1:
        print("\n⚠️ 部分环节工作，需要修复其他环节")
    elif success_count == 2:
        print("\n⚠️ 大部分环节正常，最后一步有问题")
    else:
        print("\n✅ 所有环节都正常，图像数据传递成功")
    
    print("=" * 70)