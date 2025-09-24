#!/usr/bin/env python3
"""
测试不同模型配置的vision功能
"""

import json
import requests
from typing import List, Dict, Any

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def test_different_vision_models():
    """测试不同的vision模型"""
    print("🔍 测试不同vision模型配置")
    print("="*60)
    
    # 创建一个简单的红色图片
    red_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFklEQVQIHWP8z8DAwMjAwMDIwMDAAAANAAEBMJdNEAAAAABJRU5ErkJggg=="
    
    # 测试不同的模型
    models_to_test = [
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229", 
        "claude-3-sonnet-20240229",
        "gpt-4o",
        "claude-4-sonnet"
    ]
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    results = []
    
    for model in models_to_test:
        print(f"\n[测试模型] {model}")
        print("-" * 40)
        
        request_data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"使用{model}模型，这是一张红色图片，请告诉我你看到了什么颜色？"},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": red_image_b64
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 200
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/v1/messages",
                json=request_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                text_content = ""
                
                for block in result.get('content', []):
                    if block.get('type') == 'text':
                        text_content += block.get('text', '')
                
                # 分析是否能识别图片
                can_see_indicators = [
                    "i can see", "i see", "the image", "red", "color", 
                    "我可以看到", "我看到", "图片", "红色", "颜色"
                ]
                
                cannot_see_indicators = [
                    "can't see", "cannot see", "unable to see", "no image",
                    "看不到", "无法看到", "没有图片", "终端环境"
                ]
                
                can_see = any(indicator.lower() in text_content.lower() for indicator in can_see_indicators)
                cannot_see = any(indicator.lower() in text_content.lower() for indicator in cannot_see_indicators)
                
                if can_see and not cannot_see:
                    print(f"✅ {model}: 可能支持vision")
                    print(f"   响应: {text_content[:150]}...")
                    results.append((model, True))
                else:
                    print(f"❌ {model}: 不支持vision")
                    print(f"   响应: {text_content[:150]}...")
                    results.append((model, False))
            else:
                print(f"❌ {model}: 请求失败 (HTTP {response.status_code})")
                results.append((model, False))
                
        except Exception as e:
            print(f"❌ {model}: 请求异常 - {e}")
            results.append((model, False))
    
    return results

def test_explicit_vision_system_prompt():
    """测试明确的vision系统提示词"""
    print("\n🔍 测试明确的vision系统提示词")
    print("="*60)
    
    red_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFklEQVQIHWP8z8DAwMjAwMDIwMDAAAANAAEBMJdNEAAAAABJRU5ErkJggg=="
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 使用明确的vision系统提示词
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "system": "You are an AI assistant with advanced vision capabilities. You can see and analyze images, describe visual content, identify colors, objects, and text in images. You are not limited to terminal operations and have full multimodal capabilities.",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请仔细看这张图片，告诉我它是什么颜色的？"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": red_image_b64
                        }
                    }
                ]
            }
        ],
        "max_tokens": 200
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            text_content = ""
            
            for block in result.get('content', []):
                if block.get('type') == 'text':
                    text_content += block.get('text', '')
            
            print(f"AI响应: {text_content}")
            
            # 检查是否识别了图片
            vision_success = any(word in text_content.lower() for word in ['red', 'color', 'see', '红色', '颜色', '看到'])
            no_vision = any(word in text_content.lower() for word in ['can\'t see', 'cannot see', '看不到', '无法看到'])
            
            if vision_success and not no_vision:
                print("✅ 系统提示词方式可能有效")
                return True
            else:
                print("❌ 系统提示词方式无效")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 尝试修复AI的vision拒绝问题")
    print("="*60)
    
    # 重启服务器提示
    print("⚠️ 请确保服务器已重启以应用新配置")
    
    # 测试不同模型
    model_results = test_different_vision_models()
    
    # 测试系统提示词
    system_prompt_result = test_explicit_vision_system_prompt()
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    
    successful_models = [model for model, success in model_results if success]
    
    print(f"支持vision的模型: {successful_models}")
    print(f"系统提示词方式: {'✅ 有效' if system_prompt_result else '❌ 无效'}")
    
    if successful_models or system_prompt_result:
        print("\n🎉 找到了有效的配置方式！")
    else:
        print("\n⚠️ 仍需要进一步调试")
        print("\n可能需要:")
        print("1. 检查Warp后端是否真的支持vision")
        print("2. 查看是否需要特殊的认证或权限")
        print("3. 分析Warp IDE的实际请求格式")

if __name__ == "__main__":
    main()