#!/usr/bin/env python3
"""
调试多图片传递问题
"""
import json
import uuid
from protobuf2openai.models import ChatMessage
from protobuf2openai.packets import packet_template, attach_user_and_tools_to_inputs
from protobuf2openai.helpers import normalize_content_to_list, segments_to_text_and_images

def test_multiple_images_packet():
    """测试多图片数据包生成"""
    print("Testing multiple images packet generation...")

    # 创建包含两张图片的消息
    history = [
        ChatMessage(
            role="user",
            content=[
                {
                    "type": "text",
                    "text": "Compare these two images:"
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="  # red
                    }
                },
                {
                    "type": "text",
                    "text": "and"
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFhAIAK8yATgAAAABJRU5ErkJggg=="  # blue
                    }
                }
            ]
        )
    ]

    # 测试内容标准化
    content_segments = normalize_content_to_list(history[0].content)
    print(f"Content segments: {len(content_segments)}")
    for i, seg in enumerate(content_segments):
        print(f"  Segment {i}: type={seg.get('type')}")
        if seg.get('type') == 'image':
            source = seg.get('source', {})
            data_len = len(source.get('data', ''))
            print(f"    Image: {source.get('media_type')}, data length: {data_len}")

    # 测试图片提取
    query_text, images = segments_to_text_and_images(content_segments)
    print(f"\nExtracted text: {query_text}")
    print(f"Extracted images: {len(images)}")
    for i, img in enumerate(images):
        print(f"  Image {i}: {img.get('mime_type')}, data length: {len(img.get('data', ''))}")

    # 生成数据包
    packet = packet_template()
    attach_user_and_tools_to_inputs(packet, history, None)

    # 检查数据包结构
    context = packet.get('input', {}).get('context', {})
    print(f"\nPacket context keys: {list(context.keys())}")

    if 'images' in context:
        print(f"Context images: {len(context['images'])}")
        for i, img in enumerate(context['images']):
            print(f"  Image {i}: {img.get('mime_type')}, data length: {len(img.get('data', ''))}")

    if 'files' in context:
        print(f"Context files: {len(context['files'])}")
        for i, file in enumerate(context['files']):
            content_data = file.get('content', {})
            print(f"  File {i}: {content_data.get('file_path')}, content length: {len(content_data.get('content', ''))}")

    # 检查referenced_attachments
    user_inputs = packet.get('input', {}).get('user_inputs', {}).get('inputs', [])
    if user_inputs:
        user_query = user_inputs[0].get('user_query', {})
        if 'referenced_attachments' in user_query:
            attachments = user_query['referenced_attachments']
            print(f"Referenced attachments: {len(attachments)}")
            for key, attachment in attachments.items():
                if key.startswith('IMAGE_'):
                    print(f"  {key}: text length {len(attachment.get('plain_text', ''))}")

    return packet

def test_mixed_format_packet():
    """测试混合格式数据包"""
    print("\n" + "="*50)
    print("Testing mixed format packet...")

    # 创建混合格式消息（Claude + OpenAI）
    history = [
        ChatMessage(
            role="user",
            content=[
                {
                    "type": "text",
                    "text": "Compare these images:"
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="  # red
                    }
                },
                {
                    "type": "text",
                    "text": "versus"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFhAIAK8yATgAAAABJRU5ErkJggg=="  # blue
                    }
                }
            ]
        )
    ]

    # 测试内容标准化
    content_segments = normalize_content_to_list(history[0].content)
    print(f"Mixed format segments: {len(content_segments)}")
    for i, seg in enumerate(content_segments):
        print(f"  Segment {i}: type={seg.get('type')}")

    # 测试图片提取
    query_text, images = segments_to_text_and_images(content_segments)
    print(f"Mixed format extracted images: {len(images)}")

    return content_segments

if __name__ == "__main__":
    print("Debugging multiple images transmission")
    print("=" * 60)

    packet = test_multiple_images_packet()
    mixed_segments = test_mixed_format_packet()

    print("\n" + "=" * 60)
    print("Analysis:")
    print("- If segments show multiple images but packet only has one, the issue is in packet generation")
    print("- If segments only show one image, the issue is in content normalization")
    print("- Check if all image formats are being processed correctly")