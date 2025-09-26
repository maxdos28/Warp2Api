#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用有效图像测试修复后的视觉模块
"""

import sys
sys.path.append('/workspace')

import json
from protobuf2openai.vision_bypass import vision_processor

def test_with_valid_images():
    """使用有效图像测试"""
    print("🎨 使用有效图像测试...")
    
    # 加载有效的测试图像
    with open('/workspace/valid_test_images.json', 'r') as f:
        images = json.load(f)
    
    # 测试每种颜色
    for color_name, img_b64 in images.items():
        print(f"\n🔍 测试 {color_name} 图像...")
        
        try:
            analysis = vision_processor.analyze_image_data(img_b64, "image/png")
            
            if "error" in analysis:
                print(f"❌ 分析失败: {analysis['error']}")
            else:
                print(f"✅ 分析成功!")
                
                basic_info = analysis.get("basic_info", {})
                color_info = analysis.get("color_analysis", {})
                description = analysis.get("content_description", "")
                
                print(f"📏 尺寸: {basic_info.get('width')}x{basic_info.get('height')}")
                print(f"🎨 主要颜色: {color_info.get('dominant_color', {}).get('name')}")
                print(f"📝 描述: {description}")
                
                # 验证准确性
                expected_colors = {
                    "red": ["红", "red"],
                    "green": ["绿", "green"], 
                    "blue": ["蓝", "blue"],
                    "yellow": ["黄", "yellow"],
                    "white": ["白", "white"],
                    "black": ["黑", "black"]
                }
                
                identified_color = color_info.get("dominant_color", {}).get("name", "").lower()
                expected = expected_colors.get(color_name, [])
                
                if any(exp in identified_color for exp in expected):
                    print(f"✅ {color_name} 识别正确!")
                else:
                    print(f"❌ {color_name} 识别错误: 识别为 {identified_color}")
                    
        except Exception as e:
            print(f"❌ 测试 {color_name} 异常: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 修复后的视觉模块测试")
    print("=" * 60)
    
    test_with_valid_images()
    
    print("=" * 60)