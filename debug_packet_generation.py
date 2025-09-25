#!/usr/bin/env python3
"""
调试数据包生成过程，检查图片数据是否正确传递
"""
import json
import uuid
from protobuf2openai.models import ChatMessage
from protobuf2openai.packets import packet_template, attach_user_and_tools_to_inputs
from protobuf2openai.helpers import normalize_content_to_list

def test_claude_format_packet():
    """测试Claude格式的数据包生成"""
    print("Testing Claude format packet generation...")

    # 创建测试消息
    history = [
        ChatMessage(
            role="user",
            content=[
                {
                    "type": "text",
                    "text": "Please describe this image."
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                    }
                }
            ]
        )
    ]

    # 生成数据包
    packet = packet_template()
    attach_user_and_tools_to_inputs(packet, history, None)

    print("Generated packet structure:")
    print(f"- input.context keys: {list(packet.get('input', {}).get('context', {}).keys())}")
    print(f"- input.user_inputs.inputs count: {len(packet.get('input', {}).get('user_inputs', {}).get('inputs', []))}")

    # 检查图片数据
    context = packet.get('input', {}).get('context', {})
    if 'images' in context:
        print(f"- images count: {len(context['images'])}")
        for i, img in enumerate(context['images']):
            print(f"  Image {i}: {img.get('mime_type')}, data length: {len(img.get('data', ''))}")

    if 'files' in context:
        print(f"- files count: {len(context['files'])}")
        for i, file in enumerate(context['files']):
            content = file.get('content', {})
            print(f"  File {i}: {content.get('file_path')}, content length: {len(content.get('content', ''))}")

    # 检查用户输入
    user_inputs = packet.get('input', {}).get('user_inputs', {}).get('inputs', [])
    if user_inputs:
        user_query = user_inputs[0].get('user_query', {})
        print(f"- user_query keys: {list(user_query.keys())}")
        if 'referenced_attachments' in user_query:
            attachments = user_query['referenced_attachments']
            print(f"- referenced_attachments count: {len(attachments)}")
            for key, attachment in attachments.items():
                text_len = len(attachment.get('plain_text', ''))
                print(f"  {key}: text length {text_len}")

    return packet

def test_openai_format_packet():
    """测试OpenAI格式的数据包生成"""
    print("\nTesting OpenAI format packet generation...")

    # 创建测试消息
    history = [
        ChatMessage(
            role="user",
            content=[
                {
                    "type": "text",
                    "text": "Please describe this image."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                    }
                }
            ]
        )
    ]

    # 生成数据包
    packet = packet_template()
    attach_user_and_tools_to_inputs(packet, history, None)

    print("Generated packet structure:")
    print(f"- input.context keys: {list(packet.get('input', {}).get('context', {}).keys())}")
    print(f"- input.user_inputs.inputs count: {len(packet.get('input', {}).get('user_inputs', {}).get('inputs', []))}")

    # 检查图片数据
    context = packet.get('input', {}).get('context', {})
    if 'images' in context:
        print(f"- images count: {len(context['images'])}")
        for i, img in enumerate(context['images']):
            print(f"  Image {i}: {img.get('mime_type')}, data length: {len(img.get('data', ''))}")

    if 'files' in context:
        print(f"- files count: {len(context['files'])}")
        for i, file in enumerate(context['files']):
            content = file.get('content', {})
            print(f"  File {i}: {content.get('file_path')}, content length: {len(content.get('content', ''))}")

    # 检查用户输入
    user_inputs = packet.get('input', {}).get('user_inputs', {}).get('inputs', [])
    if user_inputs:
        user_query = user_inputs[0].get('user_query', {})
        print(f"- user_query keys: {list(user_query.keys())}")
        if 'referenced_attachments' in user_query:
            attachments = user_query['referenced_attachments']
            print(f"- referenced_attachments count: {len(attachments)}")
            for key, attachment in attachments.items():
                text_len = len(attachment.get('plain_text', ''))
                print(f"  {key}: text length {text_len}")

    return packet

def test_content_normalization():
    """测试内容标准化过程"""
    print("\nTesting content normalization...")

    # 测试Claude格式
    claude_content = [
        {
            "type": "text",
            "text": "Please describe this image."
        },
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            }
        }
    ]

    normalized_claude = normalize_content_to_list(claude_content)
    print(f"Claude format normalized: {len(normalized_claude)} segments")
    for i, seg in enumerate(normalized_claude):
        print(f"  Segment {i}: type={seg.get('type')}")
        if seg.get('type') == 'image':
            source = seg.get('source', {})
            print(f"    Source: {source.get('media_type')}, data length: {len(source.get('data', ''))}")

    # 测试OpenAI格式
    openai_content = [
        {
            "type": "text",
            "text": "Please describe this image."
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            }
        }
    ]

    normalized_openai = normalize_content_to_list(openai_content)
    print(f"OpenAI format normalized: {len(normalized_openai)} segments")
    for i, seg in enumerate(normalized_openai):
        print(f"  Segment {i}: type={seg.get('type')}")
        if seg.get('type') == 'image':
            source = seg.get('source', {})
            print(f"    Source: {source.get('media_type')}, data length: {len(source.get('data', ''))}")

if __name__ == "__main__":
    print("Debugging packet generation process")
    print("=" * 60)

    test_content_normalization()
    claude_packet = test_claude_format_packet()
    openai_packet = test_openai_format_packet()

    print("\n" + "=" * 60)
    print("Summary:")
    print("Both formats should generate packets with image data in multiple locations")
    print("If images are missing, the issue is in the normalization or packet generation process")