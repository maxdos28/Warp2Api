#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
响应增强器 - 混合本地图像识别和Warp AI响应
"""

from typing import Dict, List, Any, Optional
import json
import re

class ResponseEnhancer:
    """响应增强器 - 处理和增强AI响应"""
    
    def __init__(self):
        self.vision_enabled = True
    
    def enhance_response_with_vision(
        self, 
        original_response: Dict[str, Any], 
        local_vision_results: List[str],
        original_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """增强响应，集成本地视觉结果"""
        
        if not local_vision_results or not self.vision_enabled:
            return original_response
        
        try:
            # 获取原始回复内容
            original_content = original_response["choices"][0]["message"]["content"]
            
            # 检查原始回复是否拒绝了图像处理
            rejection_patterns = [
                "无法查看", "不能看到", "没有图像", "cannot see", "don't see", 
                "no image", "terminal", "终端", "文本模式", "text-based"
            ]
            
            is_vision_rejected = any(pattern in original_content.lower() for pattern in rejection_patterns)
            
            if is_vision_rejected:
                # 如果Warp AI拒绝了图像处理，用本地结果替换
                enhanced_content = self._create_vision_response(local_vision_results, original_messages)
                
                # 更新响应
                enhanced_response = dict(original_response)
                enhanced_response["choices"][0]["message"]["content"] = enhanced_content
                
                # 添加元数据标记
                enhanced_response["vision_bypass"] = {
                    "enabled": True,
                    "method": "local_processing",
                    "original_rejected": True
                }
                
                return enhanced_response
            else:
                # 如果Warp AI给出了回复，增强它
                enhanced_content = self._merge_responses(original_content, local_vision_results)
                
                enhanced_response = dict(original_response)
                enhanced_response["choices"][0]["message"]["content"] = enhanced_content
                enhanced_response["vision_bypass"] = {
                    "enabled": True,
                    "method": "response_enhancement",
                    "original_rejected": False
                }
                
                return enhanced_response
                
        except Exception as e:
            # 如果增强失败，返回原始响应
            original_response["vision_bypass"] = {
                "enabled": False,
                "error": str(e)
            }
            return original_response
    
    def _create_vision_response(self, vision_results: List[str], original_messages: List[Dict[str, Any]]) -> str:
        """基于本地视觉结果创建响应"""
        
        # 分析用户的问题类型
        user_query = ""
        for msg in original_messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "text":
                            user_query += item.get("text", "")
                elif isinstance(content, str):
                    user_query += content
        
        user_query = user_query.lower()
        
        # 根据问题类型生成合适的回复
        vision_summary = "\n".join(vision_results)
        
        if any(word in user_query for word in ["什么颜色", "颜色", "color"]):
            response = f"根据我的图像分析，{vision_summary}"
            response += "\n\n我可以清楚地看到图像中的颜色信息。"
        elif any(word in user_query for word in ["描述", "分析", "describe", "analyze"]):
            response = f"通过图像分析，我可以看到：\n\n{vision_summary}"
            response += "\n\n这是基于我对图像内容的直接观察得出的分析结果。"
        elif any(word in user_query for word in ["尺寸", "大小", "size", "dimension"]):
            response = f"图像分析结果：\n{vision_summary}"
            response += "\n\n我已经分析了图像的技术参数。"
        else:
            response = f"基于图像内容分析：\n\n{vision_summary}"
            response += "\n\n我已经处理了您提供的图像。"
        
        return response
    
    def _merge_responses(self, original: str, vision_results: List[str]) -> str:
        """合并原始响应和视觉结果"""
        
        vision_summary = "\n".join(vision_results)
        
        # 如果原始回复很短或通用，主要使用视觉结果
        if len(original.strip()) < 50:
            return f"{vision_summary}\n\n{original}"
        
        # 否则将视觉结果作为补充
        return f"{original}\n\n[补充图像分析]\n{vision_summary}"

# 全局实例
response_enhancer = ResponseEnhancer()