#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态功能测试脚本

测试图片识别、文件附件等多模态功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI


def test_text_with_image_url():
    """测试：文本 + 图片 URL"""
    print("\n" + "="*60)
    print("测试 1: 文本 + 图片 URL")
    print("="*60)
    
    client = OpenAI(
        base_url="http://localhost:28889/v1",
        api_key="0000"
    )
    
    try:
        response = client.chat.completions.create(
            model="claude-4-sonnet",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "这张图片里有什么？请详细描述。"
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
        
        print("\n✅ 请求发送成功，接收响应...\n")
        for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        
        print("\n\n✅ 测试 1 完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试 1 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_base64_image():
    """测试：base64 编码的图片"""
    print("\n" + "="*60)
    print("测试 2: Base64 编码图片")
    print("="*60)
    
    # 一个简单的 1x1 红色 PNG 图片的 base64 编码
    tiny_red_pixel = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    
    client = OpenAI(
        base_url="http://localhost:28889/v1",
        api_key="0000"
    )
    
    try:
        response = client.chat.completions.create(
            model="claude-4-sonnet",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "这是什么颜色的图片？"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": tiny_red_pixel
                            }
                        }
                    ]
                }
            ],
            stream=True
        )
        
        print("\n✅ 请求发送成功，接收响应...\n")
        for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        
        print("\n\n✅ 测试 2 完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试 2 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_images():
    """测试：多张图片"""
    print("\n" + "="*60)
    print("测试 3: 多张图片")
    print("="*60)
    
    client = OpenAI(
        base_url="http://localhost:28889/v1",
        api_key="0000"
    )
    
    try:
        response = client.chat.completions.create(
            model="claude-4-sonnet",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "比较这两张图片的异同："
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/320px-Cat_November_2010-1a.jpg"
                            }
                        }
                    ]
                }
            ],
            stream=True
        )
        
        print("\n✅ 请求发送成功，接收响应...\n")
        for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        
        print("\n\n✅ 测试 3 完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试 3 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_text_only():
    """测试：纯文本（确保不影响现有功能）"""
    print("\n" + "="*60)
    print("测试 4: 纯文本（回归测试）")
    print("="*60)
    
    client = OpenAI(
        base_url="http://localhost:28889/v1",
        api_key="0000"
    )
    
    try:
        response = client.chat.completions.create(
            model="claude-4-sonnet",
            messages=[
                {
                    "role": "user",
                    "content": "你好，请用一句话介绍你自己。"
                }
            ],
            stream=True
        )
        
        print("\n✅ 请求发送成功，接收响应...\n")
        for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        
        print("\n\n✅ 测试 4 完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试 4 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("="*60)
    print("Warp2Api 多模态功能测试")
    print("="*60)
    print("\n确保服务器已启动：")
    print("  - Protobuf 桥接服务器: http://localhost:28888")
    print("  - OpenAI API 服务器: http://localhost:28889")
    print("\n开始测试...\n")
    
    results = []
    
    # 测试 1: 图片 URL
    results.append(("图片 URL 测试", test_text_with_image_url()))
    
    # 测试 2: Base64 图片
    results.append(("Base64 图片测试", test_base64_image()))
    
    # 测试 3: 多张图片
    results.append(("多张图片测试", test_multiple_images()))
    
    # 测试 4: 纯文本（回归测试）
    results.append(("纯文本测试", test_text_only()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️ {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(130)
