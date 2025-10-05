#!/usr/bin/env python3
"""测试真实图片识别"""
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="0000"
)

print("="*60)
print("测试 1: 识别猫的图片")
print("="*60)
print("图片URL: https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg")
print("\n请AI详细描述这张图片：\n")

try:
    response = client.chat.completions.create(
        model="claude-4-sonnet",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请详细描述这张图片中的内容，包括：主要对象、颜色、姿态、背景等。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg"
                        }
                    }
                ]
            }
        ],
        stream=True
    )
    
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content
    
    print("\n\n" + "="*60)
    print("✅ 测试 1 完成")
    
except Exception as e:
    print(f"\n❌ 测试 1 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("测试 2: 识别风景图片")
print("="*60)
print("图片URL: https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/320px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg")
print("\n请AI识别图片内容：\n")

try:
    response = client.chat.completions.create(
        model="claude-4-sonnet",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这是什么地方？请描述图片中的景色。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/320px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
                        }
                    }
                ]
            }
        ],
        stream=True
    )
    
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content
    
    print("\n\n" + "="*60)
    print("✅ 测试 2 完成")
    
except Exception as e:
    print(f"\n❌ 测试 2 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("测试 3: 识别代码截图（文字识别）")
print("="*60)
print("图片URL: https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/HTML5_logo_and_wordmark.svg/320px-HTML5_logo_and_wordmark.svg.png")
print("\n请AI识别图片内容：\n")

try:
    response = client.chat.completions.create(
        model="claude-4-sonnet",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这张图片上显示的是什么？请识别其中的文字和logo。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/HTML5_logo_and_wordmark.svg/320px-HTML5_logo_and_wordmark.svg.png"
                        }
                    }
                ]
            }
        ],
        stream=True
    )
    
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content
    
    print("\n\n" + "="*60)
    print("✅ 测试 3 完成")
    
except Exception as e:
    print(f"\n❌ 测试 3 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("🎉 图片识别测试完成！")
print("="*60)
