#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建有效的测试图像
"""

from PIL import Image
import numpy as np
import base64
import io

def create_solid_color_image(color_rgb, size=(8, 8)):
    """创建纯色图像"""
    
    # 创建图像数组
    img_array = np.full((size[1], size[0], 3), color_rgb, dtype=np.uint8)
    
    # 创建PIL图像
    img = Image.fromarray(img_array, 'RGB')
    
    # 转换为PNG bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # 转换为base64
    img_b64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    
    return img_b64

def create_test_images():
    """创建测试图像集"""
    
    images = {
        "red": create_solid_color_image((255, 0, 0)),      # 纯红色
        "green": create_solid_color_image((0, 255, 0)),    # 纯绿色
        "blue": create_solid_color_image((0, 0, 255)),     # 纯蓝色
        "yellow": create_solid_color_image((255, 255, 0)), # 纯黄色
        "white": create_solid_color_image((255, 255, 255)), # 纯白色
        "black": create_solid_color_image((0, 0, 0)),      # 纯黑色
    }
    
    return images

if __name__ == "__main__":
    print("🎨 创建有效的测试图像...")
    
    try:
        images = create_test_images()
        
        print("✅ 成功创建测试图像:")
        for color, img_b64 in images.items():
            print(f"  {color}: {len(img_b64)} 字符")
        
        # 验证图像可以被正确加载
        print("\n🔍 验证图像有效性...")
        for color, img_b64 in images.items():
            try:
                img_bytes = base64.b64decode(img_b64)
                img = Image.open(io.BytesIO(img_bytes))
                width, height = img.size
                mode = img.mode
                print(f"  {color}: {width}x{height}, 模式={mode} ✅")
            except Exception as e:
                print(f"  {color}: 验证失败 - {e} ❌")
        
        # 保存到文件供其他脚本使用
        import json
        with open('/workspace/valid_test_images.json', 'w') as f:
            json.dump(images, f, indent=2)
        
        print("\n✅ 测试图像已保存到 valid_test_images.json")
        
    except Exception as e:
        print(f"❌ 创建图像失败: {e}")
        import traceback
        traceback.print_exc()