#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视觉绕过模块 - 本地图像识别来绕过Warp模型限制
"""

import base64
import io
from typing import Dict, List, Any, Optional
from PIL import Image
import numpy as np

class LocalVisionProcessor:
    """本地图像处理器 - 绕过Warp AI的图像识别限制"""
    
    def __init__(self):
        self.enabled = True
    
    def analyze_image_data(self, image_data: str, mime_type: str) -> Dict[str, Any]:
        """分析图像数据并返回详细信息"""
        try:
            # 解码base64图像数据
            img_bytes = base64.b64decode(image_data)
            
            # 使用PIL加载图像
            img = Image.open(io.BytesIO(img_bytes))
            
            # 获取基本信息
            width, height = img.size
            mode = img.mode
            format_name = img.format or 'PNG'
            
            # 转换为RGB以便分析颜色
            if img.mode != 'RGB':
                img_rgb = img.convert('RGB')
            else:
                img_rgb = img
            
            # 分析颜色
            img_array = np.array(img_rgb)
            
            # 计算主要颜色
            pixels = img_array.reshape(-1, 3)
            unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
            
            # 找到最主要的颜色
            dominant_color_idx = np.argmax(counts)
            dominant_color = unique_colors[dominant_color_idx]
            
            # 颜色名称映射
            color_name = self._rgb_to_color_name(dominant_color)
            
            # 计算平均颜色
            avg_color = np.mean(pixels, axis=0).astype(int)
            
            analysis = {
                "basic_info": {
                    "width": width,
                    "height": height,
                    "format": format_name,
                    "mode": mode,
                    "total_pixels": width * height
                },
                "color_analysis": {
                    "dominant_color": {
                        "rgb": [int(c) for c in dominant_color],
                        "hex": f"#{dominant_color[0]:02x}{dominant_color[1]:02x}{dominant_color[2]:02x}",
                        "name": color_name
                    },
                    "average_color": {
                        "rgb": [int(c) for c in avg_color],
                        "hex": f"#{avg_color[0]:02x}{avg_color[1]:02x}{avg_color[2]:02x}"
                    },
                    "unique_colors": len(unique_colors),
                    "color_distribution": [
                        {
                            "rgb": [int(c) for c in color],
                            "percentage": float(count / len(pixels) * 100)
                        }
                        for color, count in zip(unique_colors, counts)
                    ][:5]  # 前5种颜色
                },
                "content_description": self._generate_description(width, height, color_name, dominant_color)
            }
            
            return analysis
            
        except Exception as e:
            return {
                "error": f"图像分析失败: {str(e)}",
                "basic_info": {"error": True}
            }
    
    def _rgb_to_color_name(self, rgb: np.ndarray) -> str:
        """将RGB值转换为颜色名称"""
        r, g, b = rgb
        
        # 基础颜色识别
        if r > 200 and g < 100 and b < 100:
            return "红色"
        elif r < 100 and g > 200 and b < 100:
            return "绿色"
        elif r < 100 and g < 100 and b > 200:
            return "蓝色"
        elif r > 200 and g > 200 and b < 100:
            return "黄色"
        elif r > 200 and g < 100 and b > 200:
            return "紫色"
        elif r < 100 and g > 200 and b > 200:
            return "青色"
        elif r > 150 and g > 150 and b > 150:
            return "白色"
        elif r < 50 and g < 50 and b < 50:
            return "黑色"
        elif abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30:
            if r > 128:
                return "浅灰色"
            else:
                return "深灰色"
        else:
            return f"混合色(R:{r},G:{g},B:{b})"
    
    def _generate_description(self, width: int, height: int, color_name: str, rgb: np.ndarray) -> str:
        """生成图像描述"""
        r, g, b = rgb
        
        description = f"这是一张 {width}x{height} 像素的图像。"
        description += f"主要颜色是{color_name}，RGB值为({r}, {g}, {b})。"
        
        if width == height:
            if width <= 8:
                description += "这是一个小的正方形色块。"
            else:
                description += "这是一个正方形图像。"
        
        if width * height <= 64:  # 8x8或更小
            description += "图像尺寸很小，主要用于颜色展示。"
        
        return description

# 全局实例
vision_processor = LocalVisionProcessor()

def process_images_locally(segments: List[Dict[str, Any]]) -> Optional[str]:
    """本地处理图像并生成描述"""
    try:
        from .helpers import extract_images_from_segments
        images = extract_images_from_segments(segments)
        
        if not images:
            return None
        
        descriptions = []
        
        for i, img in enumerate(images):
            analysis = vision_processor.analyze_image_data(img['data'], img['mime_type'])
            
            if 'error' not in analysis:
                desc = analysis['content_description']
                color_info = analysis['color_analysis']['dominant_color']
                descriptions.append(f"图像{i+1}: {desc}")
            else:
                descriptions.append(f"图像{i+1}: 处理失败")
        
        return "\n".join(descriptions)
        
    except Exception as e:
        return f"本地图像处理异常: {str(e)}"