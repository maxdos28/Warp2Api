#!/usr/bin/env python3
"""
测试匿名账户的功能限制
"""

import requests
import json

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def test_basic_vs_advanced_features():
    """对比基础功能和高级功能的可用性"""
    print("🔍 匿名账户功能限制测试")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    tests = [
        {
            "name": "基础文本对话",
            "type": "basic",
            "request": {
                "model": "claude-3-5-sonnet-20241022",
                "messages": [{"role": "user", "content": "你好，请说一句话"}],
                "max_tokens": 50
            }
        },
        {
            "name": "工具调用功能",
            "type": "advanced",
            "request": {
                "model": "claude-3-5-sonnet-20241022",
                "messages": [{"role": "user", "content": "请截取屏幕截图"}],
                "max_tokens": 100
            },
            "headers_extra": {"anthropic-beta": "computer-use-2024-10-22"}
        },
        {
            "name": "图片分析功能",
            "type": "premium",
            "request": {
                "model": "claude-3-5-sonnet-20241022",
                "system": "You have vision capabilities.",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "这张图片是什么颜色？"},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFklEQVQIHWP8z8DAwMjAwMDIwMDAAAANAAEBMJdNEAAAAABJRU5ErkJggg=="
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 200
            }
        }
    ]
    
    results = {}
    
    for test in tests:
        print(f"\n[测试] {test['name']} ({test['type']})")
        print("-" * 40)
        
        test_headers = headers.copy()
        if 'headers_extra' in test:
            test_headers.update(test['headers_extra'])
        
        try:
            response = requests.post(
                f"{BASE_URL}/v1/messages",
                json=test['request'],
                headers=test_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = ''.join([block.get('text', '') for block in result.get('content', []) if block.get('type')=='text'])
                
                # 分析响应类型
                if test['type'] == 'basic':
                    success = len(content) > 10  # 有实际回复
                elif test['type'] == 'advanced':
                    success = any(block.get('type') == 'tool_use' for block in result.get('content', []))
                else:  # premium
                    success = not any(phrase in content.lower() for phrase in [
                        "can't see", "don't see", "no image", "看不到", "没有图片"
                    ])
                
                results[test['name']] = success
                status = "✅ 可用" if success else "❌ 受限"
                print(f"{status} - {content[:100]}...")
                
            else:
                results[test['name']] = False
                print(f"❌ 请求失败: HTTP {response.status_code}")
                
        except Exception as e:
            results[test['name']] = False
            print(f"❌ 请求异常: {e}")
    
    # 总结
    print("\n" + "="*60)
    print("📊 功能可用性总结")
    print("="*60)
    
    for test_name, available in results.items():
        status = "✅ 可用" if available else "❌ 受限"
        print(f"{test_name:<20}: {status}")
    
    # 验证匿名限制理论
    basic_works = results.get("基础文本对话", False)
    advanced_works = results.get("工具调用功能", False) 
    premium_works = results.get("图片分析功能", False)
    
    print(f"\n🎯 匿名账户限制验证:")
    print(f"基础功能可用: {'✅' if basic_works else '❌'}")
    print(f"高级功能可用: {'✅' if advanced_works else '❌'}")
    print(f"付费功能可用: {'✅' if premium_works else '❌'}")
    
    if basic_works and advanced_works and not premium_works:
        print("\n💡 结论: 匿名账户确实限制了vision功能！")
        return True
    elif basic_works and not advanced_works and not premium_works:
        print("\n💡 结论: 匿名账户限制了所有高级功能！")
        return True
    else:
        print("\n🤔 结论: 限制模式不明确，需要进一步分析")
        return False

if __name__ == "__main__":
    test_basic_vs_advanced_features()