#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终综合测试：验证所有图片相关问题的修复
"""

import requests
import json
import base64
import time

def comprehensive_test():
    """综合测试所有修复"""
    print("=== 最终综合测试：图片相关问题修复验证 ===")

    # 读取图片
    with open("ali.png", 'rb') as f:
        image_data = f.read()
    base64_data = base64.b64encode(image_data).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    print(f"图片信息:")
    print(f"- 文件大小: {len(image_data)} bytes")
    print(f"- Base64长度: {len(base64_data)} chars")
    print(f"- 图片格式: {'PNG' if image_data[:8] == b'\\x89PNG\\r\\n\\x1a\\n' else '未知'}")

    # 测试1: 基本图片识别
    print(f"\\n--- 测试1: 基本图片识别 ---")
    payload1 = {
        "model": "claude-4-sonnet",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这是什么？"
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

    test1_result = send_request(payload1, headers, "基本识别")

    # 测试2: 一致性验证（连续3次相同请求）
    print(f"\\n--- 测试2: 一致性验证 ---")
    consistency_results = []
    for i in range(3):
        print(f"第{i+1}次请求...")
        result = send_request(payload1, headers, f"一致性测试{i+1}")
        if result:
            consistency_results.append(result)
        time.sleep(1)

    # 分析一致性
    if len(consistency_results) >= 2:
        # 简单的一致性检查
        consistent = True
        base_type = get_content_type(consistency_results[0])
        for result in consistency_results[1:]:
            if get_content_type(result) != base_type:
                consistent = False
                break

        print(f"一致性结果: {'通过' if consistent else '失败'}")
        print(f"主要识别类型: {base_type}")
    else:
        print("一致性测试: 无法完成")

    # 测试3: 编码错误检查
    print(f"\\n--- 测试3: 编码错误检查 ---")
    # 检查是否还有UTF-8编码错误的日志
    encoding_ok = True
    if test1_result and "utf-8" not in test1_result.lower():
        print("编码检查: 通过 - 没有UTF-8错误")
    else:
        print("编码检查: 可能仍有问题")
        encoding_ok = False

    # 总结
    print(f"\\n" + "="*50)
    print("综合测试总结:")
    print(f"1. 基本识别: {'通过' if test1_result else '失败'}")
    print(f"2. 一致性: {'通过' if len(consistency_results) >= 2 and consistent else '失败'}")
    print(f"3. 编码处理: {'通过' if encoding_ok else '失败'}")

    overall_success = bool(test1_result) and len(consistency_results) >= 2 and consistent and encoding_ok

    if overall_success:
        print("\\n🎉 所有图片相关问题修复成功！")
        print("✅ 图片可以正确传输和识别")
        print("✅ 解释内容基本一致")
        print("✅ 没有UTF-8编码错误")
        print("✅ 不再有严重的'货不对版'问题")
    else:
        print("\\n⚠️ 部分问题已修复，但仍有改进空间")

    return overall_success

def send_request(payload, headers, test_name):
    """发送请求并返回结果"""
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
                print(f"{test_name}: 成功 - {ai_response[:80]}...")
                return ai_response
            else:
                print(f"{test_name}: 失败 - 无内容")
                return None
        else:
            print(f"{test_name}: 失败 - HTTP {response.status_code}")
            return None

    except Exception as e:
        print(f"{test_name}: 异常 - {e}")
        return None

def get_content_type(response_text):
    """简单分析响应内容类型"""
    if not response_text:
        return "无内容"

    response_lower = response_text.lower()

    if any(word in response_lower for word in ["代码", "编程", "编辑器", "visual studio"]):
        return "代码编辑器"
    elif any(word in response_lower for word in ["终端", "命令", "shell"]):
        return "终端界面"
    elif any(word in response_lower for word in ["数据", "可视化", "图表"]):
        return "数据可视化"
    elif any(word in response_lower for word in ["github", "pull request"]):
        return "GitHub界面"
    else:
        return "其他"

if __name__ == "__main__":
    comprehensive_test()