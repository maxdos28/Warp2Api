#!/usr/bin/env python3
"""
调试图片检测逻辑
"""
from protobuf2openai.claude_models import claude_content_to_openai_content, ClaudeContent

def test_image_detection():
    """测试图片检测逻辑"""
    print("Testing image detection logic...")

    # 测试Claude格式
    claude_content = [
        ClaudeContent(type="text", text="What color is this?"),
        ClaudeContent(
            type="image",
            source={
                "type": "base64",
                "media_type": "image/png",
                "data": "test_data"
            }
        )
    ]

    print("Claude format:")
    result = claude_content_to_openai_content(claude_content)
    print(f"  Result type: {type(result)}")
    print(f"  Has images: {isinstance(result, list) and any(block.get('type') == 'image' for block in result if isinstance(block, dict))}")

    # 测试OpenAI格式
    openai_content = [
        ClaudeContent(type="text", text="What color is this?"),
        ClaudeContent(
            type="image_url",
            image_url={
                "url": "data:image/png;base64,test_data"
            }
        )
    ]

    print("\nOpenAI format:")
    result = claude_content_to_openai_content(openai_content)
    print(f"  Result type: {type(result)}")
    print(f"  Has images: {isinstance(result, list) and any(block.get('type') == 'image' for block in result if isinstance(block, dict))}")

    # 检查has_images逻辑
    print("\nTesting has_images detection:")
    print(f"  Claude format has_images: {any(block.type in ['image', 'image_url'] for block in claude_content)}")
    print(f"  OpenAI format has_images: {any(block.type in ['image', 'image_url'] for block in openai_content)}")

if __name__ == "__main__":
    test_image_detection()