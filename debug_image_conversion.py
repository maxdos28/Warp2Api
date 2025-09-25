#!/usr/bin/env python3
"""
调试图片转换过程
"""
import json
from protobuf2openai.claude_models import claude_content_to_openai_content, ClaudeContent

def test_claude_format():
    """测试Claude格式转换"""
    print("Testing Claude format conversion...")

    # 模拟Claude格式输入
    claude_content = [
        ClaudeContent(type="text", text="Please describe this image."),
        ClaudeContent(
            type="image",
            source={
                "type": "base64",
                "media_type": "image/png",
                "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            }
        )
    ]

    result = claude_content_to_openai_content(claude_content)
    print(f"Claude format result type: {type(result)}")
    print(f"Claude format result: {json.dumps(result, indent=2)}")
    return result

def test_openai_format():
    """测试OpenAI格式转换"""
    print("\nTesting OpenAI format conversion...")

    # 模拟OpenAI格式输入（这是问题所在）
    openai_content = [
        ClaudeContent(type="text", text="Please describe this image."),
        ClaudeContent(
            type="image_url",
            image_url={
                "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            }
        )
    ]

    result = claude_content_to_openai_content(openai_content)
    print(f"OpenAI format result type: {type(result)}")
    print(f"OpenAI format result: {json.dumps(result, indent=2)}")
    return result

def test_raw_dict_format():
    """测试原始字典格式"""
    print("\nTesting raw dict format...")

    # 直接使用字典格式（这可能是实际接收到的格式）
    raw_content = [
        {"type": "text", "text": "Please describe this image."},
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            }
        }
    ]

    # 需要先转换为ClaudeContent对象
    claude_objects = []
    for item in raw_content:
        if item["type"] == "text":
            claude_objects.append(ClaudeContent(type="text", text=item["text"]))
        elif item["type"] == "image_url":
            claude_objects.append(ClaudeContent(type="image_url", image_url=item["image_url"]))

    result = claude_content_to_openai_content(claude_objects)
    print(f"Raw dict format result type: {type(result)}")
    print(f"Raw dict format result: {json.dumps(result, indent=2)}")
    return result

if __name__ == "__main__":
    print("Debugging image conversion process")
    print("=" * 50)

    claude_result = test_claude_format()
    openai_result = test_openai_format()
    raw_result = test_raw_dict_format()

    print("\n" + "=" * 50)
    print("Summary:")
    print(f"Claude format has images: {any(block.get('type') == 'image' for block in claude_result if isinstance(block, dict))}")
    print(f"OpenAI format has images: {any(block.get('type') == 'image' for block in openai_result if isinstance(block, dict))}")
    print(f"Raw dict format has images: {any(block.get('type') == 'image' for block in raw_result if isinstance(block, dict))}")