#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证：货不对版问题是否已解决
"""

import requests
import json

def test_model_consistency():
    """测试模型一致性"""
    print("=== 最终验证：货不对版问题修复 ===")

    # 测试用例
    test_cases = [
        {
            "name": "Claude 3.5 Sonnet via Claude API",
            "url": "http://127.0.0.1:28889/v1/messages",
            "payload": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 20,
                "messages": [{"role": "user", "content": "Say 'test successful'"}]
            }
        },
        {
            "name": "Claude 3 Opus via Claude API",
            "url": "http://127.0.0.1:28889/v1/messages",
            "payload": {
                "model": "claude-3-opus-20240229",
                "max_tokens": 20,
                "messages": [{"role": "user", "content": "Say 'test successful'"}]
            }
        },
        {
            "name": "Claude 4 Sonnet via OpenAI API",
            "url": "http://127.0.0.1:28889/v1/chat/completions",
            "payload": {
                "model": "claude-4-sonnet",
                "max_tokens": 20,
                "messages": [{"role": "user", "content": "Say 'test successful'"}]
            }
        }
    ]

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 123456"
    }

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Request model: {test_case['payload']['model']}")

        try:
            response = requests.post(
                test_case['url'],
                headers=headers,
                json=test_case['payload'],
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # 检查响应模型
                if "v1/messages" in test_case['url']:
                    # Claude API format
                    response_model = data.get('model')
                    content = data.get('content', [{}])[0].get('text', '')
                else:
                    # OpenAI API format
                    response_model = data.get('model')
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

                print(f"   Response model: {response_model}")
                print(f"   Content: {content[:50]}")

                # 验证模型匹配
                if response_model == test_case['payload']['model']:
                    print("   Status: PASS - Model matches")
                else:
                    print(f"   Status: FAIL - Model mismatch!")
                    all_passed = False

            else:
                print(f"   Status: FAIL - HTTP {response.status_code}")
                print(f"   Error: {response.text[:100]}")
                all_passed = False

        except Exception as e:
            print(f"   Status: FAIL - Exception: {e}")
            all_passed = False

    print("\n" + "="*50)
    if all_passed:
        print("SUCCESS: 货不对版问题已完全解决!")
        print("- 所有模型请求和响应匹配正确")
        print("- Claude API模型映射工作正常")
        print("- OpenAI API兼容性正常")
    else:
        print("FAILURE: 仍存在货不对版问题")

    return all_passed

if __name__ == "__main__":
    test_model_consistency()