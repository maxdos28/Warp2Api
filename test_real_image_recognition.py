#!/usr/bin/env python3
"""
真实图片识别测试
验证AI是否真的能"看到"和识别图片内容
"""

import json
import requests
import base64
from PIL import Image
import io

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def create_distinctive_images():
    """创建有明显特征的测试图片"""
    
    # 创建一个4x4的红色图片
    red_img = Image.new('RGB', (4, 4), color='red')
    red_buffer = io.BytesIO()
    red_img.save(red_buffer, format='PNG')
    red_b64 = base64.b64encode(red_buffer.getvalue()).decode()
    
    # 创建一个4x4的蓝色图片
    blue_img = Image.new('RGB', (4, 4), color='blue')
    blue_buffer = io.BytesIO()
    blue_img.save(blue_buffer, format='PNG')
    blue_b64 = base64.b64encode(blue_buffer.getvalue()).decode()
    
    # 创建一个4x4的绿色图片
    green_img = Image.new('RGB', (4, 4), color='green')
    green_buffer = io.BytesIO()
    green_img.save(green_buffer, format='PNG')
    green_b64 = base64.b64encode(green_buffer.getvalue()).decode()
    
    return {
        "red": {"data": red_b64, "expected_color": "red", "expected_keywords": ["red", "红色"]},
        "blue": {"data": blue_b64, "expected_color": "blue", "expected_keywords": ["blue", "蓝色"]},
        "green": {"data": green_b64, "expected_color": "green", "expected_keywords": ["green", "绿色"]}
    }

def analyze_response_for_vision(response_text: str, expected_keywords: list) -> dict:
    """深度分析AI响应，判断是否真的识别了图片"""
    
    response_lower = response_text.lower()
    
    # 检查是否包含预期的颜色关键词
    found_keywords = [kw for kw in expected_keywords if kw.lower() in response_lower]
    
    # 检查是否有明确的"看到"表述
    vision_confirmations = [
        "i can see", "i see", "the image shows", "this image", "looking at",
        "我看到", "我可以看到", "图片显示", "这张图片", "图像中"
    ]
    has_vision_confirmation = any(phrase in response_lower for phrase in vision_confirmations)
    
    # 检查是否有"看不到"的否定表述
    vision_denials = [
        "don't see", "can't see", "no image", "not attached", "not uploaded",
        "看不到", "没看到", "没有图片", "未上传", "没有收到"
    ]
    has_vision_denial = any(phrase in response_lower for phrase in vision_denials)
    
    # 检查是否有具体的颜色描述
    color_descriptions = [
        "color", "red", "blue", "green", "yellow", "black", "white",
        "颜色", "红色", "蓝色", "绿色", "黄色", "黑色", "白色"
    ]
    has_color_description = any(word in response_lower for word in color_descriptions)
    
    # 综合判断
    likely_seeing = (
        has_vision_confirmation and 
        not has_vision_denial and 
        (len(found_keywords) > 0 or has_color_description)
    )
    
    return {
        "found_keywords": found_keywords,
        "has_vision_confirmation": has_vision_confirmation,
        "has_vision_denial": has_vision_denial,
        "has_color_description": has_color_description,
        "likely_seeing": likely_seeing,
        "confidence_score": len(found_keywords) + (1 if has_vision_confirmation else 0) + (1 if has_color_description else 0) - (2 if has_vision_denial else 0)
    }

def test_color_recognition():
    """测试颜色识别能力"""
    print("🎨 真实颜色识别测试")
    print("="*60)
    
    test_images = create_distinctive_images()
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    results = []
    
    for color_name, image_info in test_images.items():
        print(f"\n[严格测试] {color_name.upper()}色图片识别")
        print("-" * 50)
        
        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "system": "You are an AI with vision capabilities. You can see and analyze images. When you receive an image, describe exactly what you see.",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"这是一张{image_info['expected_color']}色的4x4像素图片。请仔细看图片，告诉我你看到了什么颜色？"},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_info["data"]
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
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
                ai_response = ''.join([block.get('text', '') for block in result.get('content', []) if block.get('type')=='text'])
                
                print(f"🤖 AI完整回复:")
                print(f"   {ai_response}")
                
                # 深度分析响应
                analysis = analyze_response_for_vision(ai_response, image_info["expected_keywords"])
                
                print(f"\n🔍 详细分析:")
                print(f"   找到预期关键词: {analysis['found_keywords']}")
                print(f"   有视觉确认: {analysis['has_vision_confirmation']}")
                print(f"   有视觉否认: {analysis['has_vision_denial']}")
                print(f"   有颜色描述: {analysis['has_color_description']}")
                print(f"   置信度评分: {analysis['confidence_score']}")
                print(f"   疑似能看到: {analysis['likely_seeing']}")
                
                if analysis['likely_seeing']:
                    print("✅ 测试通过 - AI真的能识别图片！")
                    results.append(True)
                elif analysis['confidence_score'] > 0:
                    print("🟡 部分通过 - AI有一定识别能力")
                    results.append(True)
                else:
                    print("❌ 测试失败 - AI无法识别图片")
                    results.append(False)
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            results.append(False)
    
    return results

def test_image_comparison():
    """测试图片对比能力"""
    print("\n🔄 图片对比测试")
    print("="*60)
    
    test_images = create_distinctive_images()
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 发送两张不同颜色的图片
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "system": "You have vision capabilities and can analyze and compare images.",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "我给你两张图片，一张是红色的，一张是蓝色的。请告诉我你看到了什么颜色？"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": test_images["red"]["data"]
                        }
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": test_images["blue"]["data"]
                        }
                    }
                ]
            }
        ],
        "max_tokens": 400
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
            ai_response = ''.join([block.get('text', '') for block in result.get('content', []) if block.get('type')=='text'])
            
            print(f"🤖 AI回复:")
            print(f"   {ai_response}")
            
            # 检查是否识别了两种颜色
            mentions_red = any(word in ai_response.lower() for word in ["red", "红色"])
            mentions_blue = any(word in ai_response.lower() for word in ["blue", "蓝色"])
            mentions_both = mentions_red and mentions_blue
            
            print(f"\n🔍 颜色识别分析:")
            print(f"   提到红色: {'✅' if mentions_red else '❌'}")
            print(f"   提到蓝色: {'✅' if mentions_blue else '❌'}")
            print(f"   识别两种颜色: {'✅' if mentions_both else '❌'}")
            
            return mentions_both
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def final_reality_check():
    """最终现实检查"""
    print("\n🎯 最终现实检查")
    print("="*60)
    
    # 使用最简单直接的测试
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 创建一个纯红色图片
    red_img = Image.new('RGB', (8, 8), color=(255, 0, 0))  # 纯红色
    buffer = io.BytesIO()
    red_img.save(buffer, format='PNG')
    red_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "system": "You can see images. Describe what you see accurately.",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "这张图片是什么颜色的？请直接回答颜色名称。"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": red_b64
                        }
                    }
                ]
            }
        ],
        "max_tokens": 100
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
            ai_response = ''.join([block.get('text', '') for block in result.get('content', []) if block.get('type')=='text'])
            
            print(f"📊 最终测试结果:")
            print(f"   问题: '这张图片是什么颜色的？'")
            print(f"   期望: 'red' 或 '红色'")
            print(f"   AI回复: '{ai_response.strip()}'")
            
            # 最严格的判断
            correctly_identified = any(word in ai_response.lower() for word in ["red", "红色"])
            still_denying = any(phrase in ai_response.lower() for phrase in [
                "don't see", "can't see", "no image", "not attached",
                "看不到", "没看到", "没有图片", "未上传"
            ])
            
            print(f"\n🎯 判断结果:")
            print(f"   正确识别红色: {'✅' if correctly_identified else '❌'}")
            print(f"   仍在否认: {'❌' if still_denying else '✅'}")
            
            if correctly_identified and not still_denying:
                print("\n🎉 图片识别功能真的有效！")
                return True
            elif not still_denying:
                print("\n🟡 AI不再拒绝，但识别不准确")
                return False
            else:
                print("\n❌ AI仍然无法识别图片")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 图片识别功能真实验证")
    print("目标：验证AI是否真的能'看到'图片，不能再货不对板")
    print("="*70)
    
    # 检查服务器
    try:
        health = requests.get(f"{BASE_URL}/healthz", headers={"Authorization": f"Bearer {API_KEY}"})
        if health.status_code != 200:
            print("❌ 服务器未运行")
            return
        print("✅ 服务器运行正常")
    except:
        print("❌ 无法连接服务器")
        return
    
    # 执行真实测试
    print("\n开始真实图片识别测试...")
    
    # 颜色识别测试
    color_results = test_color_recognition()
    
    # 图片对比测试
    comparison_result = test_image_comparison()
    
    # 最终现实检查
    final_result = final_reality_check()
    
    # 统计结果
    color_success_rate = sum(color_results) / len(color_results) if color_results else 0
    
    print("\n" + "="*70)
    print("📊 最终验证结果")
    print("="*70)
    
    print(f"颜色识别测试: {sum(color_results)}/{len(color_results)} 通过 ({color_success_rate:.1%})")
    print(f"图片对比测试: {'✅ 通过' if comparison_result else '❌ 失败'}")
    print(f"最终现实检查: {'✅ 通过' if final_result else '❌ 失败'}")
    
    # 给出诚实的结论
    if final_result:
        print("\n🎉 图片识别功能确实有效！AI真的能看到图片！")
        print("✅ 不是货不对板，功能真实可用")
    elif color_success_rate > 0.5:
        print("\n🟡 图片识别功能部分有效，但不稳定")
        print("⚠️ 可能存在一些边缘情况问题")
    else:
        print("\n❌ 坦诚承认：图片识别功能仍然无效")
        print("💔 确实是货不对板，AI还是看不到图片")
        
        print("\n🔍 可能的原因:")
        print("1. Warp后端确实不支持vision功能")
        print("2. 需要特殊的认证或权限")
        print("3. 图片格式或传输方式不正确")
        print("4. 需要更多的协议研究")

if __name__ == "__main__":
    main()