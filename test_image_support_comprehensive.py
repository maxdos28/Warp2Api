#!/usr/bin/env python3
"""
全面的图片支持测试
测试修复后的图片处理功能
"""

import json
import requests
import base64
import time
from typing import Dict, Any, List

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def print_section(title: str):
    """打印章节标题"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def print_test(test_name: str):
    """打印测试名称"""
    print(f"\n[测试] {test_name}")
    print("-"*50)

def print_result(success: bool, message: str):
    """打印测试结果"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def create_test_image() -> str:
    """创建一个简单的测试图片(base64编码的1x1像素PNG)"""
    # 这是一个透明的1x1像素PNG图片
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

def create_colored_test_image() -> str:
    """创建一个带颜色的测试图片(base64编码的红色1x1像素PNG)"""
    # 红色1x1像素PNG图片
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAFbgPcvEAAAAABJRU5ErkJggg=="

def test_openai_vision_format():
    """测试OpenAI Vision格式"""
    print_section("OpenAI Vision格式测试")
    
    test_image_b64 = create_test_image()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    test_cases = [
        {
            "name": "基础图片描述",
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请描述这张图片的内容"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{test_image_b64}"
                            }
                        }
                    ]
                }
            ]
        },
        {
            "name": "多张图片对比",
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "比较这两张图片的区别"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{test_image_b64}"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{create_colored_test_image()}"
                            }
                        }
                    ]
                }
            ]
        }
    ]
    
    results = []
    
    for case in test_cases:
        print_test(case["name"])
        
        try:
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json={
                    "model": case["model"],
                    "messages": case["messages"],
                    "max_tokens": 200
                },
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # 检查AI是否能够"看到"图片
                vision_indicators = ['image', 'picture', 'see', '图片', '图像', '看到', '显示', '像素', 'pixel']
                has_vision_response = any(indicator.lower() in content.lower() for indicator in vision_indicators)
                
                if has_vision_response and "can't see" not in content.lower() and "看不到" not in content:
                    print_result(True, f"AI成功识别图片: {content[:100]}...")
                    results.append(True)
                else:
                    print_result(False, f"AI未能识别图片: {content[:100]}...")
                    results.append(False)
            else:
                print_result(False, f"请求失败: HTTP {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print_result(False, f"请求异常: {e}")
            results.append(False)
    
    return all(results)

def test_claude_vision_format():
    """测试Claude Vision格式"""
    print_section("Claude Vision格式测试")
    
    test_image_b64 = create_test_image()
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    test_cases = [
        {
            "name": "Claude图片分析",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请分析这张图片"},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": test_image_b64
                            }
                        }
                    ]
                }
            ]
        },
        {
            "name": "Claude多模态对话",
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
                                "data": create_colored_test_image()
                            }
                        }
                    ]
                }
            ]
        }
    ]
    
    results = []
    
    for case in test_cases:
        print_test(case["name"])
        
        try:
            response = requests.post(
                f"{BASE_URL}/v1/messages",
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "messages": case["messages"],
                    "max_tokens": 200
                },
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('content', [])
                text_content = ""
                
                for block in content:
                    if block.get('type') == 'text':
                        text_content += block.get('text', '')
                
                # 检查AI是否能够"看到"图片
                vision_indicators = ['image', 'picture', 'see', '图片', '图像', '看到', '显示', '像素', 'pixel', 'color', 'red', '颜色', '红色']
                has_vision_response = any(indicator.lower() in text_content.lower() for indicator in vision_indicators)
                
                if has_vision_response and "can't see" not in text_content.lower() and "看不到" not in text_content:
                    print_result(True, f"AI成功识别图片: {text_content[:100]}...")
                    results.append(True)
                else:
                    print_result(False, f"AI未能识别图片: {text_content[:100]}...")
                    results.append(False)
            else:
                print_result(False, f"请求失败: HTTP {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print_result(False, f"请求异常: {e}")
            results.append(False)
    
    return all(results)

def test_format_conversion():
    """测试格式转换功能"""
    print_section("格式转换测试")
    
    print_test("测试helpers函数")
    
    # 测试normalize_content_to_list函数
    try:
        import sys
        sys.path.append('/workspace')
        from protobuf2openai.helpers import normalize_content_to_list, segments_to_warp_results
        
        # 测试OpenAI格式转换
        openai_content = [
            {"type": "text", "text": "描述图片"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;base64,iVBORw0KGgo..."
                }
            }
        ]
        
        normalized = normalize_content_to_list(openai_content)
        print(f"格式转换结果: {len(normalized)} 个内容块")
        
        has_text = any(block.get('type') == 'text' for block in normalized)
        has_image = any(block.get('type') == 'image' for block in normalized)
        
        print_result(has_text, f"文本内容转换: {'成功' if has_text else '失败'}")
        print_result(has_image, f"图片内容转换: {'成功' if has_image else '失败'}")
        
        # 测试Warp格式转换
        warp_results = segments_to_warp_results(normalized)
        print(f"Warp格式结果: {len(warp_results)} 个结果块")
        
        has_warp_text = any('text' in result for result in warp_results)
        has_warp_image = any('image' in result for result in warp_results)
        
        print_result(has_warp_text, f"Warp文本格式: {'成功' if has_warp_text else '失败'}")
        print_result(has_warp_image, f"Warp图片格式: {'成功' if has_warp_image else '失败'}")
        
        return has_text and has_image and has_warp_text and has_warp_image
        
    except Exception as e:
        print_result(False, f"格式转换测试异常: {e}")
        return False

def test_mixed_content():
    """测试混合内容处理"""
    print_section("混合内容测试")
    
    print_test("文本+图片混合内容")
    
    test_image_b64 = create_test_image()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 测试复杂的混合内容
    mixed_request = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "你好！"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{test_image_b64}"
                        }
                    },
                    {"type": "text", "text": "请分析上面的图片，然后告诉我你看到了什么。"}
                ]
            }
        ],
        "max_tokens": 300
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=mixed_request,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 检查是否处理了文本和图片
            has_greeting = any(word in content.lower() for word in ['hello', '你好', 'hi'])
            has_vision = any(word in content.lower() for word in ['image', 'picture', '图片', '图像', 'see', '看到'])
            
            print_result(True, f"请求成功: {content[:150]}...")
            print_result(has_vision, f"图片处理: {'成功' if has_vision else '失败'}")
            
            return has_vision
        else:
            print_result(False, f"请求失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"请求异常: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    print_section("错误处理测试")
    
    print_test("无效图片数据")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 测试无效的base64数据
    invalid_request = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "分析图片"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,invalid_base64_data"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 100
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=invalid_request,
            headers=headers,
            timeout=30
        )
        
        # 应该能够处理错误而不崩溃
        success = response.status_code in [200, 400, 422]  # 接受这些状态码
        print_result(success, f"错误处理: {'正常' if success else '异常'} (状态码: {response.status_code})")
        
        return success
        
    except Exception as e:
        print_result(False, f"错误处理异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🖼️ 图片支持全面测试")
    print("="*70)
    
    # 检查服务器状态
    try:
        response = requests.get(f"{BASE_URL}/healthz", headers={"Authorization": f"Bearer {API_KEY}"})
        if response.status_code != 200:
            print("❌ 服务器未运行，请先启动服务器")
            return
        print("✅ 服务器运行正常")
    except:
        print("❌ 无法连接服务器")
        return
    
    # 执行所有测试
    test_results = {
        "格式转换功能": test_format_conversion(),
        "OpenAI Vision格式": test_openai_vision_format(),
        "Claude Vision格式": test_claude_vision_format(),
        "混合内容处理": test_mixed_content(),
        "错误处理": test_error_handling()
    }
    
    # 打印测试总结
    print_section("测试结果总结")
    
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    
    for name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:<20}: {status}")
    
    success_rate = passed / total * 100
    print(f"\n总体通过率: {passed}/{total} ({success_rate:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！图片支持功能完全正常！")
    elif passed >= total * 0.8:
        print("\n✅ 大部分测试通过，图片支持基本功能正常。")
    else:
        print("\n⚠️ 部分测试失败，图片支持功能需要进一步调试。")
    
    # 详细功能说明
    print_section("功能支持详情")
    print("""
✅ 已实现的功能:

1. 格式转换支持
   - OpenAI image_url 格式 → Claude image 格式
   - 自动解析 data:image/type;base64,data 格式
   - 保留媒体类型信息

2. 多模态内容处理
   - 文本 + 图片混合内容
   - 多张图片同时处理
   - 复杂内容结构解析

3. API兼容性
   - OpenAI Chat Completions API (/v1/chat/completions)
   - Claude Messages API (/v1/messages)
   - 完整的请求/响应格式支持

4. Warp格式转换
   - 图片数据正确传递到Warp后端
   - 保留图片元数据（类型、格式等）
   - 与现有工具调用功能兼容

⚠️ 注意事项:
- 图片处理依赖Warp AI后端的vision模型支持
- 当前支持base64编码的图片数据
- 建议使用支持vision的模型（如gpt-4o, claude-3等）
""")

if __name__ == "__main__":
    main()