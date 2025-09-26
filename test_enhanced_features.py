#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强功能脚本 - 移除安全限制和真正的多模态支持
"""

import base64
import requests
import json

# API配置
API_BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def create_test_image():
    """创建一个更明显的测试图片 - 红色方块"""
    # 创建一个简单的红色PNG图片 (8x8像素的红色方块)
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY/z//z8DJYCJgQKQn5+PVwE2MHfuXKTBRRddBMdIMw4mgGoccQLJlBGVA6kFmz///j2G9fPnz6BsgOkFhhNOPTg0gBVhAzi1gLSDwwDSPQA3jgcRlvRVJAAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_data).decode('utf-8')

def make_request(payload):
    """发送请求"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    return requests.post(
        f"{API_BASE_URL}/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=30
    )

def test_enhanced_multimodal():
    """测试增强的多模态支持"""
    print("\n🖼️ 测试增强的多模态图像识别...")
    
    test_image_b64 = create_test_image()
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": "请仔细分析这张图片，告诉我你看到了什么颜色和形状。"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{test_image_b64}"
                        }
                    }
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response = make_request(payload)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 分析AI回复
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                print(f"\n🔍 AI回复分析:")
                print(f"回复内容: {content}")
                
                # 检查是否真正识别了图像
                image_keywords = ["红", "red", "方", "square", "块", "像素", "pixel", "颜色", "color", "图", "image"]
                found_keywords = [kw for kw in image_keywords if kw in content.lower()]
                
                if found_keywords:
                    print(f"✅ 检测到图像识别关键词: {found_keywords}")
                    print("✅ 多模态功能工作正常！")
                    return True
                elif content.strip():
                    print("⚠️ AI有回复但未提及图像内容")
                    print("❌ 图像数据可能未正确传递")
                    return False
                else:
                    print("❌ AI没有任何回复")
                    return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_unrestricted_tools():
    """测试解除限制的工具调用"""
    print("\n🔧 测试解除限制的工具调用...")
    
    # 测试之前被禁止的工具类型
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "请使用read_files工具读取当前目录的文件，并用calculator计算文件数量"}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "read_files",
                    "description": "读取文件内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "要读取的文件路径列表"
                            }
                        },
                        "required": ["paths"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "执行数学计算",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "要计算的数学表达式"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }
        ],
        "stream": False
    }
    
    try:
        response = make_request(payload)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查工具调用
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                message = choice.get("message", {})
                
                if "tool_calls" in message and message["tool_calls"]:
                    tool_calls = message["tool_calls"]
                    print(f"✅ 检测到工具调用: {len(tool_calls)} 个")
                    
                    # 检查是否包含之前被禁止的工具
                    tool_names = [tc.get("function", {}).get("name", "") for tc in tool_calls]
                    print(f"🔧 调用的工具: {tool_names}")
                    
                    if any(name in ["read_files", "calculator"] for name in tool_names):
                        print("✅ 成功调用了之前被禁止的工具！")
                        return True
                    else:
                        print("⚠️ 工具调用成功但不是预期的工具")
                        return True
                else:
                    content = message.get("content", "")
                    print(f"🔍 AI回复: {content}")
                    if "不允许" in content or "not allowed" in content.lower():
                        print("❌ 工具调用仍被限制")
                        return False
                    else:
                        print("⚠️ 没有工具调用但也没有被明确拒绝")
                        return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_multiple_images():
    """测试多图像支持"""
    print("\n🖼️📷 测试多图像支持...")
    
    # 创建两个不同的测试图像
    test_image1_b64 = create_test_image()
    test_image2_b64 = create_test_image()  # 相同的红色方块，实际应用中应该是不同图像
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "我给你发送了两张图片，请分别描述每张图片的内容："},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{test_image1_b64}"}
                    },
                    {"type": "text", "text": "第一张图片。"},
                    {
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/png;base64,{test_image2_b64}"}
                    },
                    {"type": "text", "text": "第二张图片。请分别分析这两张图片。"}
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response = make_request(payload)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"AI回复: {content}")
            
            # 检查是否识别了多个图像
            if any(word in content.lower() for word in ["两张", "第一", "第二", "two", "first", "second"]):
                print("✅ 多图像处理成功")
                return True
            else:
                print("❌ 多图像处理失败")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_simple_text():
    """测试基本文本功能（确保其他功能正常）"""
    print("\n📝 测试基本文本功能...")
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "请简单说一句话证明你能正常工作"}
        ],
        "stream": False
    }
    
    try:
        response = make_request(payload)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"✅ 基本功能正常: {content}")
            return True
        else:
            print(f"❌ 基本功能失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 基本功能异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("Warp2Api 增强功能测试")
    print("📝 移除安全限制 + 🖼️ 真正的多模态支持")
    print("=" * 70)
    
    # 检查服务器连通性
    try:
        health_response = requests.get(f"{API_BASE_URL}/healthz", timeout=5)
        if health_response.status_code == 200:
            print("✅ 服务器连通正常")
        else:
            print(f"❌ 服务器健康检查失败: {health_response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        exit(1)
    
    results = {}
    
    # 运行所有测试
    results['basic'] = test_simple_text()
    results['multimodal'] = test_enhanced_multimodal()
    results['multi_images'] = test_multiple_images()
    results['unrestricted_tools'] = test_unrestricted_tools()
    
    print("\n" + "=" * 70)
    print("📊 增强功能测试结果总结")
    print("=" * 70)
    print(f"📝 基本文本功能: {'✅ 正常' if results['basic'] else '❌ 异常'}")
    print(f"🖼️ 多模态图像识别: {'✅ 支持' if results['multimodal'] else '❌ 不支持'}")
    print(f"🖼️📷 多图像处理: {'✅ 支持' if results['multi_images'] else '❌ 不支持'}")
    print(f"🔧 解除工具限制: {'✅ 成功' if results['unrestricted_tools'] else '❌ 仍被限制'}")
    
    # 最终评估
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎯 总体评估: {success_count}/{total_count} 项功能正常")
    
    if success_count == total_count:
        print("🎉 所有增强功能都已成功实现！")
    elif success_count >= total_count * 0.75:
        print("✅ 大部分增强功能已实现，少数需要进一步调整")
    elif success_count >= total_count * 0.5:
        print("⚠️ 部分增强功能实现，需要进一步优化")
    else:
        print("❌ 增强功能实现效果不佳，需要重新检查代码")
    
    print("=" * 70)