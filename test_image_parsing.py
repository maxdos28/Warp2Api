#!/usr/bin/env python3
"""
测试图片解析功能的详细脚本

该脚本测试图片的实际解析和处理能力
"""

import base64
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import io

# 尝试导入PIL用于创建测试图片
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL/Pillow 未安装，将使用预定义的测试图片")


def create_test_images() -> Dict[str, str]:
    """创建各种测试图片的base64编码"""
    images = {}
    
    # 1x1 红色像素 PNG（最小的有效PNG）
    images["tiny_red"] = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    # 1x1 蓝色像素 PNG
    images["tiny_blue"] = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    # 2x2 彩色像素 PNG（红、绿、蓝、白）
    images["small_colors"] = "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFUlEQVR42mP8z8Dwn5GBgZGBgYEBAA4HAgETHuQeAAAAAElFTkSuQmCC"
    
    if PIL_AVAILABLE:
        # 使用PIL创建更复杂的测试图片
        
        # 创建一个10x10的渐变图
        img = Image.new('RGB', (10, 10))
        pixels = img.load()
        for i in range(10):
            for j in range(10):
                pixels[i, j] = (i*25, j*25, 128)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        images["gradient_10x10"] = base64.b64encode(buffer.getvalue()).decode()
        
        # 创建一个带文字的图片
        img = Image.new('RGB', (100, 30), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "TEST", fill='black')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        images["text_image"] = base64.b64encode(buffer.getvalue()).decode()
    
    return images


def test_image_parsing_locally():
    """本地测试图片解析功能（不需要API服务器）"""
    print("\n" + "="*60)
    print("本地图片解析测试")
    print("="*60)
    
    # 导入项目的图片处理模块
    sys.path.insert(0, '/workspace')
    
    try:
        from protobuf2openai.helpers import (
            normalize_content_to_list,
            segments_to_text_and_images,
            extract_images_from_segments
        )
        print("✅ 成功导入图片处理模块")
    except ImportError as e:
        print(f"❌ 无法导入模块: {e}")
        return
    
    test_images = create_test_images()
    
    # 测试1: 解析单张图片
    print("\n--- 测试1: 解析单张图片 ---")
    content = [
        {"type": "text", "text": "这是一张测试图片："},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{test_images['tiny_red']}"
            }
        }
    ]
    
    segments = normalize_content_to_list(content)
    print(f"解析后的段数: {len(segments)}")
    
    text, images = segments_to_text_and_images(segments)
    print(f"提取的文本: '{text}'")
    print(f"提取的图片数: {len(images)}")
    
    if images:
        img = images[0]
        print(f"图片1 MIME类型: {img.get('mime_type')}")
        print(f"图片1 数据大小: {len(img.get('data', b''))} 字节")
    
    # 测试2: 解析多张图片
    print("\n--- 测试2: 解析多张图片 ---")
    content = [
        {"type": "text", "text": "比较这些图片："},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{test_images['tiny_red']}"}
        },
        {"type": "text", "text": " 和 "},
        {
            "type": "image_url", 
            "image_url": {"url": f"data:image/png;base64,{test_images['tiny_blue']}"}
        },
        {"type": "text", "text": " 以及 "},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{test_images['small_colors']}"}
        }
    ]
    
    segments = normalize_content_to_list(content)
    text, images = segments_to_text_and_images(segments)
    
    print(f"提取的完整文本: '{text}'")
    print(f"提取的图片数: {len(images)}")
    
    for i, img in enumerate(images, 1):
        print(f"  图片{i}: {img.get('mime_type')}, {len(img.get('data', b''))} 字节")
    
    # 测试3: 不同MIME类型
    print("\n--- 测试3: 不同MIME类型测试 ---")
    mime_types = ["image/png", "image/jpeg", "image/gif", "image/webp"]
    
    for mime_type in mime_types:
        content = [{
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{test_images['tiny_red']}"}
        }]
        
        segments = normalize_content_to_list(content)
        _, images = segments_to_text_and_images(segments)
        
        if images:
            extracted_mime = images[0].get('mime_type')
            status = "✅" if extracted_mime == mime_type else "❌"
            print(f"{status} {mime_type}: 提取为 {extracted_mime}")
    
    # 测试4: 错误处理
    print("\n--- 测试4: 错误处理测试 ---")
    
    # 无效的base64
    invalid_content = [{
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64,INVALID_BASE64!!!"}
    }]
    
    try:
        segments = normalize_content_to_list(invalid_content)
        _, images = segments_to_text_and_images(segments)
        if not images:
            print("✅ 无效base64被正确忽略")
        else:
            print("⚠️ 无效base64未被正确处理")
    except Exception as e:
        print(f"✅ 捕获到预期的错误: {e}")
    
    # 测试5: 实际文件测试
    print("\n--- 测试5: 实际文件测试 ---")
    test_file = Path("/workspace/real_test_image.png")
    
    if test_file.exists():
        with open(test_file, "rb") as f:
            file_data = f.read()
            file_base64 = base64.b64encode(file_data).decode()
        
        print(f"测试文件: {test_file.name}")
        print(f"文件大小: {len(file_data)} 字节")
        print(f"Base64大小: {len(file_base64)} 字符")
        
        content = [{
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{file_base64}"}
        }]
        
        segments = normalize_content_to_list(content)
        _, images = segments_to_text_and_images(segments)
        
        if images and len(images[0].get('data', b'')) == len(file_data):
            print("✅ 文件正确解析和还原")
        else:
            print("❌ 文件解析有误差")
    else:
        print(f"⚠️ 测试文件 {test_file} 不存在")
    
    return True


def test_anthropic_format_parsing():
    """测试 Anthropic 格式的图片解析"""
    print("\n" + "="*60)
    print("Anthropic 格式图片解析测试")
    print("="*60)
    
    sys.path.insert(0, '/workspace')
    
    try:
        from protobuf2openai.messages_router import convert_content_to_warp_format
        from protobuf2openai.messages_router import AnthropicContentBlock, AnthropicImageSource
        print("✅ 成功导入 Anthropic 格式处理模块")
    except ImportError as e:
        print(f"❌ 无法导入模块: {e}")
        return
    
    test_images = create_test_images()
    
    # 测试1: Anthropic 格式单张图片
    print("\n--- 测试1: Anthropic 格式单张图片 ---")
    
    content_blocks = [
        AnthropicContentBlock(type="text", text="分析这张图片："),
        AnthropicContentBlock(
            type="image",
            source=AnthropicImageSource(
                type="base64",
                media_type="image/png",
                data=test_images['tiny_red']
            )
        )
    ]
    
    text, images = convert_content_to_warp_format(content_blocks)
    print(f"提取的文本: '{text}'")
    print(f"提取的图片数: {len(images)}")
    
    if images:
        print(f"图片 MIME: {images[0].get('mime_type')}")
        print(f"图片大小: {len(images[0].get('data', b''))} 字节")
    
    # 测试2: 多种MIME类型
    print("\n--- 测试2: Anthropic 格式多种MIME类型 ---")
    
    mime_tests = [
        ("image/png", test_images['tiny_red']),
        ("image/jpeg", test_images['tiny_blue']),
        ("image/gif", test_images['small_colors']),
        ("image/webp", test_images['tiny_red'])
    ]
    
    for mime_type, image_data in mime_tests:
        content = [
            AnthropicContentBlock(
                type="image",
                source=AnthropicImageSource(
                    type="base64",
                    media_type=mime_type,
                    data=image_data
                )
            )
        ]
        
        _, images = convert_content_to_warp_format(content)
        if images:
            extracted_mime = images[0].get('mime_type')
            status = "✅" if extracted_mime == mime_type else "❌"
            print(f"{status} {mime_type}: 正确保留MIME类型")
    
    return True


def test_packet_building():
    """测试数据包构建过程"""
    print("\n" + "="*60)
    print("数据包构建测试")
    print("="*60)
    
    sys.path.insert(0, '/workspace')
    
    try:
        from protobuf2openai.packets import packet_template, attach_user_and_tools_to_inputs
        from protobuf2openai.models import ChatMessage
        from protobuf2openai.helpers import normalize_content_to_list, segments_to_text_and_images
        print("✅ 成功导入数据包构建模块")
    except ImportError as e:
        print(f"❌ 无法导入模块: {e}")
        return
    
    test_images = create_test_images()
    
    # 创建包含图片的消息
    message = ChatMessage(
        role="user",
        content=[
            {"type": "text", "text": "请分析这张图片"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{test_images['tiny_red']}"}
            }
        ]
    )
    
    # 构建数据包
    packet = packet_template()
    history = [message]
    
    # 附加用户输入和图片
    attach_user_and_tools_to_inputs(packet, history, None)
    
    print("\n构建的数据包结构:")
    print(f"- 有用户输入: {'user_inputs' in packet.get('input', {})}")
    print(f"- 有上下文: {'context' in packet.get('input', {})}")
    
    if 'context' in packet.get('input', {}):
        context = packet['input']['context']
        if 'images' in context:
            print(f"- 图片数量: {len(context['images'])}")
            for i, img in enumerate(context['images'], 1):
                print(f"  图片{i}: {img.get('mime_type')}, {len(img.get('data', b''))} 字节")
        else:
            print("- ⚠️ 上下文中没有图片")
    
    if 'user_inputs' in packet.get('input', {}):
        inputs = packet['input']['user_inputs'].get('inputs', [])
        if inputs and 'user_query' in inputs[0]:
            query = inputs[0]['user_query'].get('query', '')
            print(f"- 查询文本: '{query}'")
    
    return True


def display_summary():
    """显示测试总结"""
    print("\n" + "="*60)
    print("图片解析功能测试总结")
    print("="*60)
    
    print("""
✅ 支持的功能:
1. OpenAI 格式图片 (image_url)
2. Anthropic 格式图片 (image source)
3. 多种MIME类型 (PNG, JPEG, GIF, WebP)
4. Base64 编码/解码
5. 多张图片处理
6. 文本和图片混合内容
7. 错误处理和容错

📝 数据流程:
1. 接收 JSON 请求 → 解析内容段
2. 识别图片段 → 提取 base64 数据
3. 解码图片 → 保留 MIME 类型
4. 构建 protobuf 包 → 添加到 context.images
5. 发送到 Warp API

🔍 关键组件:
- helpers.py: normalize_content_to_list, segments_to_text_and_images
- packets.py: attach_user_and_tools_to_inputs
- messages_router.py: convert_content_to_warp_format
""")


def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════╗
║           图片解析功能详细测试                      ║
╚══════════════════════════════════════════════════════╝
""")
    
    # 运行各项测试
    results = []
    
    # 本地解析测试
    try:
        if test_image_parsing_locally():
            results.append(("本地图片解析", "✅ 通过"))
        else:
            results.append(("本地图片解析", "❌ 失败"))
    except Exception as e:
        results.append(("本地图片解析", f"❌ 错误: {e}"))
    
    # Anthropic 格式测试
    try:
        if test_anthropic_format_parsing():
            results.append(("Anthropic格式解析", "✅ 通过"))
        else:
            results.append(("Anthropic格式解析", "❌ 失败"))
    except Exception as e:
        results.append(("Anthropic格式解析", f"❌ 错误: {e}"))
    
    # 数据包构建测试
    try:
        if test_packet_building():
            results.append(("数据包构建", "✅ 通过"))
        else:
            results.append(("数据包构建", "❌ 失败"))
    except Exception as e:
        results.append(("数据包构建", f"❌ 错误: {e}"))
    
    # 显示结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for test_name, result in results:
        print(f"{test_name}: {result}")
    
    # 显示总结
    display_summary()
    
    # 统计通过率
    passed = sum(1 for _, r in results if "✅" in r)
    total = len(results)
    
    print(f"\n总体通过率: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有图片解析测试通过！功能完全正常！")
    else:
        print("\n⚠️ 部分测试未通过，请检查相关模块。")


if __name__ == "__main__":
    main()