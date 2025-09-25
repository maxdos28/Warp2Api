#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试图片解释货不对版问题
"""

import requests
import json
import base64
import os
import time

def test_same_image_multiple_times():
    """用同一张图片测试多次，看看是否每次结果都不同"""
    print("=== 测试同一图片多次请求的一致性 ===")

    # 读取图片
    with open("ali.png", 'rb') as f:
        image_data = f.read()
    base64_data = base64.b64encode(image_data).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 0000"
    }

    # 用完全相同的请求测试5次
    test_prompt = "请描述这张图片显示的内容"

    results = []

    for i in range(5):
        print(f"\n--- 第 {i+1} 次测试 ---")

        payload = {
            "model": "claude-4-sonnet",
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": test_prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_data
                            }
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(
                "http://127.0.0.1:28889/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get('content', [])
                if content:
                    ai_response = content[0].get('text', '')
                    results.append(ai_response)

                    # 提取关键词
                    keywords = []
                    if "数据" in ai_response or "可视化" in ai_response or "仪表" in ai_response:
                        keywords.append("数据可视化")
                    if "地图" in ai_response or "动物" in ai_response or "卡通" in ai_response:
                        keywords.append("地图/动物")
                    if "架构" in ai_response or "系统" in ai_response or "插件" in ai_response:
                        keywords.append("系统架构")
                    if "界面" in ai_response or "应用" in ai_response or "软件" in ai_response:
                        keywords.append("软件界面")

                    print(f"关键词: {', '.join(keywords) if keywords else '未识别'}")
                    print(f"回复长度: {len(ai_response)} 字符")
                    print(f"前100字符: {ai_response[:100]}...")

            else:
                print(f"请求失败: {response.status_code}")
                results.append(f"ERROR_{response.status_code}")

        except Exception as e:
            print(f"异常: {e}")
            results.append(f"EXCEPTION_{str(e)}")

        # 稍微等待一下
        time.sleep(2)

    # 分析结果一致性
    print(f"\n=== 一致性分析 ===")
    print(f"总共测试: {len(results)} 次")

    # 检查是否有完全不同的解释
    different_types = set()
    for result in results:
        if "数据" in result or "可视化" in result:
            different_types.add("数据可视化")
        elif "地图" in result or "动物" in result:
            different_types.add("地图动物")
        elif "架构" in result or "插件" in result:
            different_types.add("系统架构")
        else:
            different_types.add("其他")

    print(f"识别出的不同类型: {different_types}")

    if len(different_types) > 1:
        print("❌ 发现货不对版问题：同一图片得到了不同类型的解释！")
        return False
    else:
        print("✅ 解释类型一致")
        return True

def check_conversation_state():
    """检查是否有会话状态影响"""
    print("\n=== 检查会话状态影响 ===")

    # 检查是否有全局状态或缓存
    try:
        # 发送一个完全不同的请求，然后再发送图片请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 0000"
        }

        # 先发送一个文本请求，内容包含可能干扰的词汇
        text_payload = {
            "model": "claude-4-sonnet",
            "max_tokens": 50,
            "messages": [
                {
                    "role": "user",
                    "content": "请告诉我关于世界地图和动物的信息"
                }
            ]
        }

        print("发送干扰性文本请求...")
        response = requests.post(
            "http://127.0.0.1:28889/v1/messages",
            headers=headers,
            json=text_payload,
            timeout=30
        )

        if response.status_code == 200:
            print("文本请求成功")

        # 等待一下
        time.sleep(1)

        # 然后立即发送图片请求
        with open("ali.png", 'rb') as f:
            image_data = f.read()
        base64_data = base64.b64encode(image_data).decode('utf-8')

        image_payload = {
            "model": "claude-4-sonnet",
            "max_tokens": 200,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "这张图片显示了什么？"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_data
                            }
                        }
                    ]
                }
            ]
        }

        print("发送图片请求...")
        response = requests.post(
            "http://127.0.0.1:28889/v1/messages",
            headers=headers,
            json=image_payload,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            content = data.get('content', [])
            if content:
                ai_response = content[0].get('text', '')
                print(f"图片请求回复: {ai_response[:150]}...")

                if "地图" in ai_response or "动物" in ai_response:
                    print("⚠️ 可能受到了前一个请求的影响")
                    return False
                else:
                    print("✅ 没有明显的状态干扰")
                    return True

    except Exception as e:
        print(f"检查状态时出错: {e}")
        return False

def check_image_processing_pipeline():
    """检查图片处理管道是否有问题"""
    print("\n=== 检查图片处理管道 ===")

    # 检查图片是否正确编码
    with open("ali.png", 'rb') as f:
        image_data = f.read()

    print(f"原始图片大小: {len(image_data)} bytes")

    base64_data = base64.b64encode(image_data).decode('utf-8')
    print(f"Base64编码长度: {len(base64_data)} chars")

    # 验证base64编码是否正确
    try:
        decoded_data = base64.b64decode(base64_data)
        if decoded_data == image_data:
            print("✅ Base64编码/解码正确")
        else:
            print("❌ Base64编码/解码有问题")
            return False
    except Exception as e:
        print(f"❌ Base64验证失败: {e}")
        return False

    # 检查图片格式
    if image_data[:8] == b'\x89PNG\r\n\x1a\n':
        print("✅ 图片格式: PNG")
    elif image_data[:2] == b'\xff\xd8':
        print("✅ 图片格式: JPEG")
    else:
        print("⚠️ 未知图片格式")

    return True

if __name__ == "__main__":
    print("开始详细调试图片解释货不对版问题...")

    # 测试一致性
    consistency_ok = test_same_image_multiple_times()

    # 检查状态影响
    state_ok = check_conversation_state()

    # 检查处理管道
    pipeline_ok = check_image_processing_pipeline()

    print("\n" + "="*50)
    print("调试总结:")
    print(f"一致性测试: {'通过' if consistency_ok else '失败'}")
    print(f"状态检查: {'通过' if state_ok else '失败'}")
    print(f"管道检查: {'通过' if pipeline_ok else '失败'}")

    if not consistency_ok:
        print("\n主要问题: 同一图片得到不同解释")
        print("可能原因:")
        print("1. AI模型本身的随机性")
        print("2. 服务器端有缓存或状态混乱")
        print("3. 图片传输过程中的问题")
        print("4. 提示词处理仍有问题")
    elif consistency_ok and state_ok and pipeline_ok:
        print("\n✅ 技术层面没有发现明显问题")
        print("可能是AI模型本身对这张特定图片的理解存在歧义")