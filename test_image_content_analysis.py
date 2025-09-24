#!/usr/bin/env python3
"""
图片内容解析功能严格验证测试
验证AI是否真的能够"看到"和分析图片内容
"""

import json
import requests
import base64
from typing import Dict, Any, List

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def create_distinctive_test_images():
    """创建几个有明显特征的测试图片"""
    
    # 红色 2x2 像素图片 (PNG格式)
    red_2x2_png = "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFklEQVQIHWP8z8DAwMjAwMDIwMDAAAANAAEBMJdNEAAAAABJRU5ErkJggg=="
    
    # 蓝色 3x3 像素图片 
    blue_3x3_png = "iVBORw0KGgoAAAANSUhEUgAAAAMAAAADCAYAAABWKLW/AAAAGElEQVQIHWMwNDRkYGBgYGBgYGBgYGBgAAAAGgABAPOKuQAAAABJRU5ErkJggg=="
    
    # 创建一个简单的文字图片 (模拟)
    text_image_png = "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAXElEQVQoU2NkYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGD//wMA/wD/AP8A/wD/AP8A/wD/AP8A/wD/AP8A/wD/AP8A/wD/AP8A/wD/AP8A/wD/AP8A/wD/AP8A/wD/AAAA"
    
    return {
        "red_2x2": red_2x2_png,
        "blue_3x3": blue_3x3_png, 
        "text_image": text_image_png
    }

def print_section(title: str):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def print_test(test_name: str):
    print(f"\n[严格测试] {test_name}")
    print("-"*60)

def analyze_ai_response(response_text: str, expected_features: List[str]) -> Dict[str, Any]:
    """分析AI响应，检查是否真的识别了图片内容"""
    
    response_lower = response_text.lower()
    
    # 检查是否包含预期特征
    found_features = []
    for feature in expected_features:
        if feature.lower() in response_lower:
            found_features.append(feature)
    
    # 检查是否有"看不到图片"的负面回应
    negative_indicators = [
        "can't see", "cannot see", "don't see", "unable to see",
        "no image", "not able to see", "can't view", "cannot view",
        "看不到", "无法看到", "没有看到", "看不见", "无法查看",
        "没有图片", "没有图像", "未能看到"
    ]
    
    has_negative = any(indicator in response_lower for indicator in negative_indicators)
    
    # 检查是否有积极的视觉描述
    positive_indicators = [
        "i can see", "i see", "the image shows", "this image", "in the picture",
        "the photo", "looking at", "appears to be", "seems to be",
        "我可以看到", "我看到", "这张图片", "图片显示", "图像显示",
        "照片中", "画面中", "图中", "可以看出"
    ]
    
    has_positive = any(indicator in response_lower for indicator in positive_indicators)
    
    return {
        "found_features": found_features,
        "has_negative": has_negative,
        "has_positive": has_positive,
        "feature_match_rate": len(found_features) / len(expected_features) if expected_features else 0,
        "likely_seeing_image": has_positive and not has_negative
    }

def test_claude_image_analysis():
    """测试Claude API的图片分析能力"""
    print_section("Claude API 图片内容分析测试")
    
    test_images = create_distinctive_test_images()
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    test_cases = [
        {
            "name": "红色像素图片识别",
            "image_key": "red_2x2",
            "prompt": "请仔细观察这张图片，告诉我它的颜色、大小和任何你能看到的细节。",
            "expected_features": ["red", "color", "pixel", "small", "2x2", "红色", "颜色", "像素", "小"],
            "model": "claude-3-5-sonnet-20241022"
        },
        {
            "name": "蓝色像素图片对比",
            "image_key": "blue_3x3", 
            "prompt": "描述这张图片的颜色和特征。这是什么颜色的图片？",
            "expected_features": ["blue", "color", "pixel", "蓝色", "颜色", "像素"],
            "model": "claude-3-5-sonnet-20241022"
        }
    ]
    
    results = []
    
    for case in test_cases:
        print_test(case["name"])
        
        request_data = {
            "model": case["model"],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": case["prompt"]},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": test_images[case["image_key"]]
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
                text_content = ""
                
                for block in result.get('content', []):
                    if block.get('type') == 'text':
                        text_content += block.get('text', '')
                
                print(f"📄 AI响应: {text_content}")
                
                # 分析响应
                analysis = analyze_ai_response(text_content, case["expected_features"])
                
                print(f"\n🔍 分析结果:")
                print(f"   找到的特征: {analysis['found_features']}")
                print(f"   特征匹配率: {analysis['feature_match_rate']:.1%}")
                print(f"   有负面回应: {analysis['has_negative']}")
                print(f"   有积极描述: {analysis['has_positive']}")
                print(f"   疑似能看到图片: {analysis['likely_seeing_image']}")
                
                success = analysis['likely_seeing_image'] and analysis['feature_match_rate'] > 0
                results.append(success)
                
                if success:
                    print("✅ 测试通过 - AI能够分析图片内容")
                else:
                    print("❌ 测试失败 - AI无法有效分析图片内容")
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                print(f"   错误: {response.text}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            results.append(False)
    
    return results

def test_openai_image_analysis():
    """测试OpenAI API的图片分析能力"""
    print_section("OpenAI API 图片内容分析测试")
    
    test_images = create_distinctive_test_images()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    test_cases = [
        {
            "name": "OpenAI红色图片识别",
            "image_key": "red_2x2",
            "prompt": "What color is this image? Describe what you see in detail.",
            "expected_features": ["red", "color", "pixel", "small"],
            "model": "gpt-4o"
        }
    ]
    
    results = []
    
    for case in test_cases:
        print_test(case["name"])
        
        request_data = {
            "model": case["model"],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": case["prompt"]},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{test_images[case['image_key']]}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json=request_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                print(f"📄 AI响应: {content}")
                
                # 分析响应
                analysis = analyze_ai_response(content, case["expected_features"])
                
                print(f"\n🔍 分析结果:")
                print(f"   找到的特征: {analysis['found_features']}")
                print(f"   特征匹配率: {analysis['feature_match_rate']:.1%}")
                print(f"   疑似能看到图片: {analysis['likely_seeing_image']}")
                
                success = analysis['likely_seeing_image'] and analysis['feature_match_rate'] > 0
                results.append(success)
                
                if success:
                    print("✅ 测试通过 - AI能够分析图片内容")
                else:
                    print("❌ 测试失败 - AI无法有效分析图片内容")
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            results.append(False)
    
    return results

def test_mixed_text_image_scenarios():
    """测试文本+图片混合场景"""
    print_section("文本+图片混合场景测试")
    
    test_images = create_distinctive_test_images()
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 复杂的混合场景测试
    complex_scenarios = [
        {
            "name": "多轮对话中的图片分析",
            "messages": [
                {"role": "user", "content": "你好，我想让你帮我分析一些图片。"},
                {"role": "assistant", "content": "你好！我很乐意帮你分析图片。请上传你想要分析的图片。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "这是第一张图片，请告诉我它是什么颜色的："},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": test_images["red_2x2"]
                            }
                        }
                    ]
                }
            ],
            "expected_features": ["red", "color", "红色", "颜色"]
        },
        {
            "name": "图片前后文本描述",
            "messages": [
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": "我有一张很小的图片，只有几个像素："},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64", 
                                "media_type": "image/png",
                                "data": test_images["blue_3x3"]
                            }
                        },
                        {"type": "text", "text": "请告诉我这张图片的主要颜色是什么？"}
                    ]
                }
            ],
            "expected_features": ["blue", "color", "蓝色", "颜色", "pixel", "像素"]
        }
    ]
    
    results = []
    
    for scenario in complex_scenarios:
        print_test(scenario["name"])
        
        request_data = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": scenario["messages"],
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
                text_content = ""
                
                for block in result.get('content', []):
                    if block.get('type') == 'text':
                        text_content += block.get('text', '')
                
                print(f"📄 AI响应: {text_content}")
                
                # 分析响应
                analysis = analyze_ai_response(text_content, scenario["expected_features"])
                
                print(f"\n🔍 分析结果:")
                print(f"   找到的特征: {analysis['found_features']}")
                print(f"   疑似能看到图片: {analysis['likely_seeing_image']}")
                
                success = analysis['likely_seeing_image']
                results.append(success)
                
                if success:
                    print("✅ 混合场景测试通过")
                else:
                    print("❌ 混合场景测试失败")
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            results.append(False)
    
    return results

def test_data_transmission_verification():
    """验证数据传输是否正确"""
    print_section("数据传输验证")
    
    print_test("检查发送到Warp的数据格式")
    
    # 启用详细日志模式，检查发送到Warp的数据
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01", 
        "Authorization": f"Bearer {API_KEY}"
    }
    
    test_images = create_distinctive_test_images()
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "测试图片传输"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png", 
                            "data": test_images["red_2x2"]
                        }
                    }
                ]
            }
        ],
        "max_tokens": 100
    }
    
    print("发送的请求数据结构:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False)[:500] + "...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功发送和接收")
            
            # 检查响应中是否有图片相关的内容
            text_content = ""
            for block in result.get('content', []):
                if block.get('type') == 'text':
                    text_content += block.get('text', '')
            
            print(f"响应内容: {text_content[:200]}...")
            return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 图片内容解析功能严格验证")
    print("="*80)
    print("目标：验证AI是否真的能够'看到'和分析图片内容")
    
    # 检查服务器
    try:
        response = requests.get(f"{BASE_URL}/healthz", headers={"Authorization": f"Bearer {API_KEY}"})
        if response.status_code != 200:
            print("❌ 服务器未运行")
            return
        print("✅ 服务器运行正常")
    except:
        print("❌ 无法连接服务器")
        return
    
    # 执行严格测试
    all_results = []
    
    # Claude API测试
    claude_results = test_claude_image_analysis()
    all_results.extend(claude_results)
    
    # OpenAI API测试  
    openai_results = test_openai_image_analysis()
    all_results.extend(openai_results)
    
    # 混合场景测试
    mixed_results = test_mixed_text_image_scenarios()
    all_results.extend(mixed_results)
    
    # 数据传输验证
    transmission_ok = test_data_transmission_verification()
    
    # 最终评估
    print_section("严格验证结果")
    
    passed_tests = sum(all_results)
    total_tests = len(all_results)
    
    print(f"图片内容分析测试: {passed_tests}/{total_tests} 通过")
    print(f"数据传输验证: {'✅ 正常' if transmission_ok else '❌ 异常'}")
    
    if passed_tests > 0:
        print(f"\n✅ 部分图片解析功能正常工作 ({passed_tests}/{total_tests})")
    else:
        print(f"\n❌ 图片解析功能未能正常工作")
        print("\n可能的问题:")
        print("1. Warp后端不支持vision功能")
        print("2. 图片数据传输格式不正确") 
        print("3. 模型配置问题")
        print("4. 图片太小或格式不支持")
    
    # 给出明确结论
    if passed_tests >= total_tests * 0.5:
        print(f"\n🎯 结论: 图片解析功能基本可用")
    else:
        print(f"\n🎯 结论: 图片解析功能需要进一步调试")

if __name__ == "__main__":
    main()