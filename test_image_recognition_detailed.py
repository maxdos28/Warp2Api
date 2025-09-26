#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细测试图像识别功能 - 验证AI是否真的能看到和分析图像
"""

import base64
import requests
import json
import time

# API配置
API_BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def create_distinct_test_images():
    """创建几个明显不同的测试图像"""
    
    # 1. 红色正方形 (8x8)
    red_square = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY/z//z8DJYCJgQKQn5+PVwE2MHfuXKTBRRddBMdIMw4mgGoccQLJlBGVA6kFmz///j2G9fPnz6BsgOkFhhNOPTg0gBVhAzi1gLSDwwDSPQA3jgcRlvRVJAAAAABJRU5ErkJggg=="
    )
    
    # 2. 绿色正方形 (8x8) - 修改颜色
    green_square = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY2D4/58BCgATAwUgPz8frwJsYO7cuUiDiy66CI6RZhxMAOw4kUSKeMqByoHUgs3/9+8xrJ8/fwZlA0wvMJxw6sGhAawIG8CpBaQdHAaQ7gEAkAgHJUgn+4MAAAAASUVORK5CYII="
    )
    
    # 3. 蓝色正方形 (8x8)
    blue_square = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY2Bg+M9ACWBioATk5+fjVYANzJ07F2lw0UUXwTHSjIMJgB1HkkgRT1lQOZBasPn//j2G9fPnz6BsgOkFhhNOPTg0gBVhAzi1gLSDwwDSPQAAJwgHJQJPkPgAAAAASUVORK5CYII="
    )
    
    return {
        "red": base64.b64encode(red_square).decode('utf-8'),
        "green": base64.b64encode(green_square).decode('utf-8'), 
        "blue": base64.b64encode(blue_square).decode('utf-8')
    }

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
        timeout=60
    )

def test_single_color_recognition():
    """测试单个颜色识别"""
    print("\n🔴 测试单个颜色识别 - 红色方块")
    
    images = create_distinct_test_images()
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "这张图片是什么颜色的？请只回答颜色名称，比如：红色、绿色、蓝色等。"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{images['red']}"
                        }
                    }
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response = make_request(payload)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"AI回答: {content}")
            
            # 检查是否识别出了红色
            if any(word in content.lower() for word in ["红", "red", "红色"]):
                print("✅ 成功识别出红色!")
                return True
            elif any(word in content.lower() for word in ["颜色", "color", "看到", "图", "image"]):
                print("⚠️ AI提到了颜色/图像相关内容，但未正确识别颜色")
                return False
            else:
                print("❌ AI完全没有识别出图像内容")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_color_discrimination():
    """测试颜色区分能力"""
    print("\n🌈 测试颜色区分能力 - 三种不同颜色")
    
    images = create_distinct_test_images()
    
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "我给你三张图片，每张都是不同颜色的正方形。请分别说出每张图片的颜色："},
                    {"type": "text", "text": "第一张图片："},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{images['red']}"}
                    },
                    {"type": "text", "text": "第二张图片："},
                    {
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/png;base64,{images['green']}"}
                    },
                    {"type": "text", "text": "第三张图片："},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{images['blue']}"}
                    },
                    {"type": "text", "text": "请按顺序回答每张图片的颜色。"}
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response = make_request(payload)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"AI回答: {content}")
            
            # 检查是否识别出了多个颜色
            colors_mentioned = []
            if any(word in content.lower() for word in ["红", "red"]):
                colors_mentioned.append("红色")
            if any(word in content.lower() for word in ["绿", "green"]):
                colors_mentioned.append("绿色")
            if any(word in content.lower() for word in ["蓝", "blue"]):
                colors_mentioned.append("蓝色")
            
            if len(colors_mentioned) >= 2:
                print(f"✅ 识别出了多种颜色: {colors_mentioned}")
                return True
            elif len(colors_mentioned) == 1:
                print(f"⚠️ 只识别出了一种颜色: {colors_mentioned}")
                return False
            else:
                print("❌ 没有识别出任何具体颜色")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_shape_recognition():
    """测试形状识别"""
    print("\n⬜ 测试形状识别")
    
    images = create_distinct_test_images()
    
    payload = {
        "model": "claude-4-sonnet", 
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "这张图片中的形状是什么？请描述形状（比如：正方形、圆形、三角形等）和颜色。"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{images['blue']}"}
                    }
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response = make_request(payload)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"AI回答: {content}")
            
            # 检查形状和颜色识别
            shape_identified = any(word in content.lower() for word in ["方", "square", "正方", "矩形"])
            color_identified = any(word in content.lower() for word in ["蓝", "blue"])
            
            if shape_identified and color_identified:
                print("✅ 成功识别出形状和颜色!")
                return True
            elif shape_identified or color_identified:
                print("⚠️ 部分识别成功（形状或颜色）")
                return False
            else:
                print("❌ 未能识别出形状和颜色")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_image_vs_no_image():
    """对比测试：有图像 vs 无图像"""
    print("\n🔍 对比测试：有图像请求 vs 无图像请求")
    
    images = create_distinct_test_images()
    
    # 测试1：包含图像的请求
    print("\n1️⃣ 发送包含图像的请求...")
    payload_with_image = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请描述这张图片"},
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
        response_with = make_request(payload_with_image)
        if response_with.status_code == 200:
            result_with = response_with.json()
            content_with = result_with["choices"][0]["message"]["content"]
            print(f"有图像时的回答: {content_with}")
        else:
            print(f"有图像请求失败: {response_with.text}")
            return False
    except Exception as e:
        print(f"有图像请求异常: {e}")
        return False
    
    time.sleep(1)  # 避免请求过快
    
    # 测试2：不包含图像的请求
    print("\n2️⃣ 发送不包含图像的请求...")
    payload_no_image = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "请描述这张图片"}
        ],
        "stream": False
    }
    
    try:
        response_without = make_request(payload_no_image)
        if response_without.status_code == 200:
            result_without = response_without.json()
            content_without = result_without["choices"][0]["message"]["content"]
            print(f"无图像时的回答: {content_without}")
        else:
            print(f"无图像请求失败: {response_without.text}")
            return False
    except Exception as e:
        print(f"无图像请求异常: {e}")
        return False
    
    # 分析对比结果
    print("\n📊 对比分析:")
    
    # 检查有图像时是否有具体描述
    has_specific_content = any(word in content_with.lower() for word in [
        "红", "颜色", "方", "色块", "red", "color", "square", "像素", "pixel"
    ])
    
    # 检查无图像时是否提示需要图像
    asks_for_image = any(phrase in content_without.lower() for phrase in [
        "没有图", "no image", "看不到", "don't see", "需要图", "need image", "上传", "upload"
    ])
    
    if has_specific_content and asks_for_image:
        print("✅ 完美！有图像时给出具体描述，无图像时正确提示")
        return True
    elif has_specific_content:
        print("⚠️ 有图像时有描述，但无图像时的响应不明确")
        return True
    elif asks_for_image:
        print("❌ 无图像时正确提示，但有图像时没有具体描述")
        return False
    else:
        print("❌ 两种情况下的响应都不明确")
        return False

def test_debug_image_data():
    """调试测试：检查图像数据是否正确传递"""
    print("\n🐛 调试测试：验证图像数据传递")
    
    images = create_distinct_test_images()
    
    # 创建一个特殊的提示，要求AI报告它接收到的内容
    payload = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请告诉我：1）你是否接收到了图像数据？2）如果是，请描述图像的内容。3）如果没有，请明确说明没有收到图像。"},
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
        response = make_request(payload)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"AI的详细回答: {content}")
            
            # 分析回答内容
            mentions_image_received = any(phrase in content.lower() for phrase in [
                "接收到", "received", "看到", "see", "图像", "image", "图片", "picture"
            ])
            
            mentions_no_image = any(phrase in content.lower() for phrase in [
                "没有接收", "no image", "没有图", "don't see", "未收到", "not received"
            ])
            
            if mentions_image_received and not mentions_no_image:
                print("✅ AI明确表示接收到了图像数据")
                return True
            elif mentions_no_image:
                print("❌ AI明确表示没有接收到图像数据")
                return False
            else:
                print("⚠️ AI的回答不够明确")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("详细图像识别测试 - 验证AI是否真正能看到和理解图像")
    print("=" * 80)
    
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
    
    # 运行详细测试
    results = {}
    
    print("\n" + "="*50)
    print("开始详细图像识别测试...")
    print("="*50)
    
    results['debug'] = test_debug_image_data()
    results['single_color'] = test_single_color_recognition()
    results['color_discrimination'] = test_color_discrimination()
    results['shape'] = test_shape_recognition()
    results['comparison'] = test_image_vs_no_image()
    
    print("\n" + "=" * 80)
    print("📊 详细测试结果总结")
    print("=" * 80)
    print(f"🐛 调试测试（图像数据传递）: {'✅ 成功' if results['debug'] else '❌ 失败'}")
    print(f"🔴 单色识别测试: {'✅ 成功' if results['single_color'] else '❌ 失败'}")
    print(f"🌈 颜色区分测试: {'✅ 成功' if results['color_discrimination'] else '❌ 失败'}")
    print(f"⬜ 形状识别测试: {'✅ 成功' if results['shape'] else '❌ 失败'}")
    print(f"🔍 对比测试: {'✅ 成功' if results['comparison'] else '❌ 失败'}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎯 总体评估: {success_count}/{total_count} 项测试通过")
    
    if success_count == 0:
        print("❌ 图像识别功能完全不工作 - 图像数据未被正确传递或处理")
    elif success_count == 1 and results['debug']:
        print("⚠️ 图像数据能传递，但AI无法正确解析图像内容")
    elif success_count < total_count / 2:
        print("⚠️ 图像识别功能部分工作，但效果有限")
    elif success_count >= total_count * 0.8:
        print("✅ 图像识别功能基本正常，仅有少数问题")
    else:
        print("✅ 图像识别功能大部分正常")
    
    print("\n" + "=" * 80)
    print("详细测试完成")
    print("=" * 80)