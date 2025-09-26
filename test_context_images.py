#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试context中的图像添加逻辑
"""

import sys
sys.path.append('/workspace')

import base64
from protobuf2openai.helpers import normalize_content_to_list, extract_images_from_segments
from protobuf2openai.models import ChatMessage

def test_context_images():
    """测试图像添加到context的逻辑"""
    
    # 创建测试图像
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )
    test_image_b64 = base64.b64encode(png_data).decode('utf-8')
    
    # 创建ChatMessage
    message = ChatMessage(
        role="user",
        content=[
            {"type": "text", "text": "测试图像"},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{test_image_b64}"
                }
            }
        ]
    )
    
    print(f"原始消息: {message}")
    print(f"消息角色: {message.role}")
    print(f"消息内容类型: {type(message.content)}")
    
    # 模拟router.py中的逻辑
    history = [message]
    all_images = []
    
    for msg in history:
        print(f"\n处理消息: 角色={msg.role}")
        if msg.role == "user":
            print("✅ 是用户消息，开始处理...")
            content_segments = normalize_content_to_list(msg.content)
            print(f"标准化后的segments: {content_segments}")
            
            images = extract_images_from_segments(content_segments)
            print(f"提取的图像数量: {len(images)}")
            
            for i, img in enumerate(images):
                print(f"图像 {i+1}: 类型={img['mime_type']}, 数据长度={len(img['data'])}")
                try:
                    img_bytes = base64.b64decode(img['data'])
                    all_images.append({
                        "data": img_bytes,
                        "mime_type": img['mime_type']
                    })
                    print(f"✅ 图像 {i+1} 成功转换为bytes")
                except Exception as e:
                    print(f"❌ 图像 {i+1} 转换失败: {e}")
        else:
            print(f"⚠️ 跳过非用户消息，角色: {msg.role}")
    
    print(f"\n最终收集的图像数量: {len(all_images)}")
    for i, img in enumerate(all_images):
        print(f"图像 {i+1}: 类型={img['mime_type']}, 数据类型={type(img['data'])}, 长度={len(img['data']) if isinstance(img['data'], bytes) else 'N/A'}")
    
    return len(all_images) > 0

if __name__ == "__main__":
    print("=" * 60)
    print("测试Context图像添加逻辑")
    print("=" * 60)
    
    result = test_context_images()
    
    print("\n" + "=" * 60)
    print(f"测试结果: {'✅ 成功' if result else '❌ 失败'}")
    print("=" * 60)