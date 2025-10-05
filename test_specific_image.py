#!/usr/bin/env python3
"""测试特定图片 - 验证识别准确性"""
from openai import OpenAI
import base64

client = OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="0000"
)

print("="*60)
print("测试: Python logo 识别")
print("="*60)
print("图片: Python官方logo")
print("\n")

# 使用Python logo的URL
python_logo_url = "https://www.python.org/static/community_logos/python-logo-master-v3-TM.png"

try:
    response = client.chat.completions.create(
        model="claude-4-sonnet",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请告诉我这张图片中显示的是什么编程语言的logo？请识别文字和图标。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": python_logo_url,
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        stream=True
    )
    
    print("AI识别结果：\n")
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print("\n\n" + "="*60)
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("测试: 数字图片识别")
print("="*60)

# 创建一个简单的数字"42"的文本图片URL
# 使用placeholder服务
number_img_url = "https://via.placeholder.com/300x100/0066cc/ffffff?text=Number:+42"

try:
    response = client.chat.completions.create(
        model="claude-4-sonnet",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "图片中显示的数字是多少？"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": number_img_url
                        }
                    }
                ]
            }
        ],
        stream=True
    )
    
    print("\nAI识别结果：\n")
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print("\n\n" + "="*60)
    print("✅ 测试完成")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
