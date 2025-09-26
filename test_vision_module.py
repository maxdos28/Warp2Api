#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试本地视觉模块
"""

import sys
sys.path.append('/workspace')

import base64
from protobuf2openai.vision_bypass import vision_processor

def test_vision_processor():
    """测试视觉处理器"""
    print("🧪 测试本地视觉处理器...")
    
    # 创建红色8x8测试图像
    red_image = "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY/z//z8DJYCJgQKQn5+PVwE2MHfuXKTBRRddBMdIMw4mgGoccQLJlBGVA6kFmz///j2G9fPnz6BsgOkFhhNOPTg0gBVhAzi1gLSDwwDSPQA3jgcRlvRVJAAAAABJRU5ErkJggg=="
    
    try:
        # 测试图像分析
        print("🔍 分析红色图像...")
        analysis = vision_processor.analyze_image_data(red_image, "image/png")
        
        print(f"分析结果: {analysis}")
        
        if "error" in analysis:
            print(f"❌ 图像分析失败: {analysis['error']}")
            return False
        else:
            print("✅ 图像分析成功!")
            
            # 检查分析结果的准确性
            basic_info = analysis.get("basic_info", {})
            color_info = analysis.get("color_analysis", {})
            
            print(f"📏 尺寸信息: {basic_info}")
            print(f"🎨 颜色信息: {color_info}")
            
            # 验证准确性
            width = basic_info.get("width")
            height = basic_info.get("height")
            dominant_color = color_info.get("dominant_color", {})
            
            if width == 8 and height == 8:
                print("✅ 尺寸识别正确!")
            else:
                print(f"❌ 尺寸识别错误: {width}x{height} (期望8x8)")
            
            color_name = dominant_color.get("name", "")
            if "红" in color_name or "red" in color_name.lower():
                print("✅ 颜色识别正确!")
            else:
                print(f"❌ 颜色识别错误: {color_name} (期望红色)")
            
            return True
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 本地视觉模块测试")
    print("=" * 60)
    
    result = test_vision_processor()
    
    print("\n" + "=" * 60)
    print(f"测试结果: {'✅ 成功' if result else '❌ 失败'}")
    print("=" * 60)