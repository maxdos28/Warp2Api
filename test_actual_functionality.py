#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实际功能测试 - 验证多模态和工具调用的真实效果
"""

import base64
import requests
import json
import time

# API配置
API_BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def create_test_images():
    """创建几个不同的测试图像"""
    
    # 红色4x4方块
    red_4x4 = "iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAYAAACp8Z5+AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAAuSURBVAiZY/z//z8DAwMD4///DAwMjAxAAP///1+G////MzIyMjAwMDBQ6AIAVQcHAIqHCb0AAAAASUVORK5CYII="
    
    # 蓝色4x4方块  
    blue_4x4 = "iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAYAAACp8Z5+AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAAuSURBVAiZY2D4//8/AwMDA+P//xkYGBgZgAD//v+/DP///2dkZGRgYGBgoNAFAFUHBwCTRwq9AAAAASUVORK5CYII="
    
    # 绿色4x4方块
    green_4x4 = "iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAYAAACp8Z5+AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAAuSURBVAiZY2Bg+P+fgYGBgfH//wwMDIwMQAD//v+/DP///2dkZGRgYGBgoNAFAFUHBwCKhwm9AAAAASUVORK5CYII="
    
    return {
        "red": red_4x4,
        "blue": blue_4x4, 
        "green": green_4x4
    }

def make_request(payload):
    """发送请求到API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    return requests.post(
        f"{API_BASE_URL}/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=60
    )

def test_multimodal_actual():
    """实际测试多模态功能"""
    print("🖼️ 实际多模态测试...")
    
    images = create_test_images()
    
    # 测试1：单图像识别
    print("\n1️⃣ 测试单图像识别...")
    payload1 = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "这是什么颜色？"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{images['red']}"}
                    }
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response1 = make_request(payload1)
        if response1.status_code == 200:
            result1 = response1.json()
            content1 = result1["choices"][0]["message"]["content"]
            print(f"AI回答1: {content1}")
            
            # 检查是否有具体的视觉描述
            visual_words = ["红", "red", "颜色", "color", "方", "square", "像素", "pixel", "图像", "image"]
            found_visual = [w for w in visual_words if w in content1.lower()]
            
            if found_visual:
                print(f"✅ 检测到视觉相关词汇: {found_visual}")
            else:
                print("❌ 没有检测到具体的视觉描述")
        else:
            print(f"❌ 单图像测试失败: {response1.text}")
            return False
    except Exception as e:
        print(f"❌ 单图像测试异常: {e}")
        return False
    
    time.sleep(2)
    
    # 测试2：多图像对比
    print("\n2️⃣ 测试多图像对比...")
    payload2 = {
        "model": "claude-4-sonnet", 
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "比较这三张图片的颜色，分别是什么颜色？"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{images['red']}"}},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{images['blue']}"}},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{images['green']}"}},
                    {"type": "text", "text": "请告诉我每张图的颜色。"}
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response2 = make_request(payload2)
        if response2.status_code == 200:
            result2 = response2.json()
            content2 = result2["choices"][0]["message"]["content"]
            print(f"AI回答2: {content2}")
            
            # 检查是否识别了多种颜色
            colors = {"红": ["红", "red"], "蓝": ["蓝", "blue"], "绿": ["绿", "green"]}
            found_colors = []
            for color_name, keywords in colors.items():
                if any(kw in content2.lower() for kw in keywords):
                    found_colors.append(color_name)
            
            print(f"识别的颜色: {found_colors}")
            return len(found_colors) >= 2  # 至少识别2种颜色算成功
        else:
            print(f"❌ 多图像测试失败: {response2.text}")
            return False
    except Exception as e:
        print(f"❌ 多图像测试异常: {e}")
        return False

def test_tools_actual():
    """实际测试工具调用功能"""
    print("\n🔧 实际工具调用测试...")
    
    # 测试1：基础工具调用
    print("\n1️⃣ 测试基础工具调用...")
    payload1 = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "请使用calculator工具计算 15 * 7 + 23"}
        ],
        "tools": [
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
                                "description": "数学表达式"
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
        response1 = make_request(payload1)
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"工具调用响应: {json.dumps(result1, ensure_ascii=False, indent=2)}")
            
            choice = result1["choices"][0]
            message = choice["message"]
            
            if "tool_calls" in message and message["tool_calls"]:
                print("✅ 成功触发工具调用!")
                tool_calls = message["tool_calls"]
                for i, tc in enumerate(tool_calls):
                    print(f"工具调用 {i+1}:")
                    print(f"  ID: {tc.get('id')}")
                    print(f"  函数: {tc.get('function', {}).get('name')}")
                    print(f"  参数: {tc.get('function', {}).get('arguments')}")
                return True
            else:
                print("❌ 没有工具调用，只有文本回复")
                print(f"文本回复: {message.get('content', '')}")
                return False
        else:
            print(f"❌ 工具调用测试失败: {response1.text}")
            return False
    except Exception as e:
        print(f"❌ 工具调用测试异常: {e}")
        return False

def test_tools_followup():
    """测试工具调用的后续处理"""
    print("\n2️⃣ 测试工具调用后续处理...")
    
    # 首先发起工具调用
    payload_call = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "使用weather工具查询北京天气"}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "weather",
                    "description": "查询天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "城市名称"}
                        },
                        "required": ["city"]
                    }
                }
            }
        ],
        "stream": False
    }
    
    try:
        response_call = make_request(payload_call)
        if response_call.status_code != 200:
            print(f"❌ 工具调用请求失败: {response_call.text}")
            return False
            
        result_call = response_call.json()
        message_call = result_call["choices"][0]["message"]
        
        if "tool_calls" not in message_call or not message_call["tool_calls"]:
            print("❌ 没有工具调用，无法测试后续处理")
            return False
            
        tool_call = message_call["tool_calls"][0]
        tool_call_id = tool_call["id"]
        
        print(f"✅ 获得工具调用ID: {tool_call_id}")
        
        time.sleep(1)
        
        # 模拟工具执行结果并发送回复
        payload_result = {
            "model": "claude-4-sonnet",
            "messages": [
                {"role": "user", "content": "使用weather工具查询北京天气"},
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [tool_call]
                },
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": "北京今天晴朗，温度25°C，湿度60%，微风"
                }
            ],
            "tools": [
                {
                    "type": "function", 
                    "function": {
                        "name": "weather",
                        "description": "查询天气信息",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string", "description": "城市名称"}
                            },
                            "required": ["city"]
                        }
                    }
                }
            ],
            "stream": False
        }
        
        response_result = make_request(payload_result)
        if response_result.status_code == 200:
            result_result = response_result.json()
            final_message = result_result["choices"][0]["message"]["content"]
            print(f"✅ 工具结果处理成功!")
            print(f"最终回复: {final_message}")
            
            # 检查是否整合了工具结果
            if any(word in final_message.lower() for word in ["北京", "25", "晴", "weather", "温度"]):
                print("✅ AI成功整合了工具调用结果")
                return True
            else:
                print("⚠️ AI回复了但未整合工具结果")
                return False
        else:
            print(f"❌ 工具结果处理失败: {response_result.text}")
            return False
            
    except Exception as e:
        print(f"❌ 工具后续处理异常: {e}")
        return False

def test_complex_scenario():
    """测试复杂场景：图像+工具"""
    print("\n🎭 测试复杂场景：多模态+工具调用...")
    
    images = create_test_images()
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请分析这张图片的颜色，然后用calculator计算如果有100个这样颜色的方块，总面积是多少（每个方块4x4像素）"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{images['red']}"}
                    }
                ]
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "执行数学计算",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string", "description": "数学表达式"}
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
        if response.status_code == 200:
            result = response.json()
            print(f"复杂场景响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            message = result["choices"][0]["message"]
            has_tool_calls = "tool_calls" in message and message["tool_calls"]
            content = message.get("content", "")
            
            # 检查是否同时处理了图像和工具
            mentions_color = any(word in content.lower() for word in ["红", "red", "颜色", "color"])
            mentions_calculation = any(word in content.lower() for word in ["计算", "100", "面积", "像素"])
            
            print(f"提到颜色: {mentions_color}")
            print(f"提到计算: {mentions_calculation}")
            print(f"有工具调用: {has_tool_calls}")
            
            if has_tool_calls and (mentions_color or mentions_calculation):
                print("✅ 复杂场景部分成功")
                return True
            elif has_tool_calls:
                print("⚠️ 有工具调用但缺少图像处理")
                return True
            else:
                print("❌ 复杂场景失败")
                return False
        else:
            print(f"❌ 复杂场景请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 复杂场景异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 实际功能测试 - 多模态和工具调用的真实效果")
    print("=" * 80)
    
    # 检查服务器状态
    try:
        health = requests.get(f"{API_BASE_URL}/healthz", timeout=5)
        if health.status_code == 200:
            print("✅ 服务器连接正常")
        else:
            print(f"❌ 服务器状态异常: {health.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ 无法连接服务器: {e}")
        exit(1)
    
    print("\n" + "="*50)
    print("开始实际功能测试...")
    print("="*50)
    
    results = {}
    
    # 运行所有实际测试
    results['multimodal'] = test_multimodal_actual()
    results['tools_basic'] = test_tools_actual()
    results['tools_followup'] = test_tools_followup()
    results['complex'] = test_complex_scenario()
    
    print("\n" + "=" * 80)
    print("📊 实际功能测试结果汇总")
    print("=" * 80)
    print(f"🖼️ 多模态实际效果: {'✅ 有效' if results['multimodal'] else '❌ 无效'}")
    print(f"🔧 基础工具调用: {'✅ 有效' if results['tools_basic'] else '❌ 无效'}")
    print(f"🔄 工具后续处理: {'✅ 有效' if results['tools_followup'] else '❌ 无效'}")
    print(f"🎭 复杂场景测试: {'✅ 有效' if results['complex'] else '❌ 无效'}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎯 总体实际效果: {success_count}/{total_count} 项功能真正可用")
    
    if success_count == 0:
        print("❌ 所有功能都不能实际使用")
    elif success_count == total_count:
        print("🎉 所有功能都能实际使用！")
    else:
        print("⚠️ 部分功能可以实际使用")
        
    # 具体分析
    print("\n📋 详细分析:")
    if not results['multimodal']:
        print("- 多模态：图像数据传递但AI拒绝处理")
    if not results['tools_basic']:
        print("- 工具调用：可能仍有限制或配置问题")
    if not results['tools_followup']:
        print("- 工具流程：工具调用后的结果处理有问题")
    if not results['complex']:
        print("- 复合功能：多功能组合使用存在问题")
        
    print("=" * 80)