#!/usr/bin/env python3
"""
调试packet结构，检查图片是否正确添加到InputContext
"""

import json
import sys
sys.path.append('/workspace')

from protobuf2openai.models import ChatMessage
from protobuf2openai.packets import packet_template, map_history_to_warp_messages, attach_user_and_tools_to_inputs

def debug_packet_with_image():
    """调试包含图片的packet结构"""
    print("🔍 调试包含图片的packet结构")
    print("="*60)
    
    # 创建包含图片的消息
    message = ChatMessage(
        role="user",
        content=[
            {"type": "text", "text": "分析这张红色图片"},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFklEQVQIHWP8z8DAwMjAwMDIwMDAAAANAAEBMJdNEAAAAABJRU5ErkJggg=="
                }
            }
        ]
    )
    
    history = [message]
    task_id = "test_task"
    
    print("1. 原始消息:")
    print(json.dumps(message.dict(), indent=2, ensure_ascii=False))
    
    # 生成packet
    packet = packet_template()
    packet["task_context"] = {
        "tasks": [{
            "id": task_id,
            "description": "",
            "status": {"in_progress": {}},
            "messages": map_history_to_warp_messages(history, task_id, None, False),
        }],
        "active_task_id": task_id,
    }
    
    print("\n2. map_history_to_warp_messages后:")
    print(json.dumps(packet["task_context"]["tasks"][0]["messages"], indent=2, ensure_ascii=False))
    
    # 附加用户输入和工具
    attach_user_and_tools_to_inputs(packet, history, None)
    
    print("\n3. attach_user_and_tools_to_inputs后:")
    print("input.context:")
    print(json.dumps(packet.get("input", {}).get("context", {}), indent=2, ensure_ascii=False))
    
    print("\ninput.user_inputs:")
    print(json.dumps(packet.get("input", {}).get("user_inputs", {}), indent=2, ensure_ascii=False))
    
    # 检查关键字段
    context = packet.get("input", {}).get("context", {})
    has_images = "images" in context and len(context["images"]) > 0
    
    user_inputs = packet.get("input", {}).get("user_inputs", {}).get("inputs", [])
    has_content = any("content" in inp.get("user_query", {}) for inp in user_inputs)
    
    print(f"\n4. 关键字段检查:")
    print(f"   ✅ input.context.images: {has_images}")
    if has_images:
        print(f"      图片数量: {len(context['images'])}")
        for i, img in enumerate(context["images"]):
            print(f"      图片{i}: mime_type={img.get('mime_type')}, data_length={len(img.get('data', ''))}")
    
    print(f"   ✅ user_query.content: {has_content}")
    
    return has_images

if __name__ == "__main__":
    debug_packet_with_image()