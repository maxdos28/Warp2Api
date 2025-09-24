from __future__ import annotations

import base64
import re
from typing import Any, Dict, List


def _get(d: Dict[str, Any], *names: str) -> Any:
    for n in names:
        if isinstance(d, dict) and n in d:
            return d[n]
    return None


def normalize_content_to_list(content: Any) -> List[Dict[str, Any]]:
    segments: List[Dict[str, Any]] = []
    try:
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    t = item.get("type") or ("text" if isinstance(item.get("text"), str) else None)
                    if t == "text" and isinstance(item.get("text"), str):
                        segments.append({"type": "text", "text": item.get("text")})
                    elif t == "image_url":
                        # 处理 OpenAI 格式的图片
                        image_url_data = item.get("image_url", {})
                        if isinstance(image_url_data, dict) and "url" in image_url_data:
                            segments.append({
                                "type": "image_url",
                                "image_url": image_url_data
                            })
                    else:
                        seg: Dict[str, Any] = {}
                        if t:
                            seg["type"] = t
                        if isinstance(item.get("text"), str):
                            seg["text"] = item.get("text")
                        # 保留其他可能的图片相关字段
                        if "image_url" in item:
                            seg["image_url"] = item["image_url"]
                        if seg:
                            segments.append(seg)
            return segments
        if isinstance(content, dict):
            if isinstance(content.get("text"), str):
                return [{"type": "text", "text": content.get("text")}]
    except Exception:
        return []
    return []


def segments_to_text(segments: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for seg in segments:
        if isinstance(seg, dict) and seg.get("type") == "text" and isinstance(seg.get("text"), str):
            parts.append(seg.get("text") or "")
    return "".join(parts)


def segments_to_warp_results(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for seg in segments:
        if isinstance(seg, dict) and seg.get("type") == "text" and isinstance(seg.get("text"), str):
            results.append({"text": {"text": seg.get("text")}})
    return results


def extract_images_from_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从消息段中提取图片数据，转换为protobuf格式"""
    images: List[Dict[str, Any]] = []
    
    for seg in segments:
        if not isinstance(seg, dict) or seg.get("type") != "image_url":
            continue
            
        image_url_data = seg.get("image_url", {})
        if not isinstance(image_url_data, dict) or "url" not in image_url_data:
            continue
            
        url = image_url_data["url"]
        
        try:
            # 处理 data URL 格式 (data:image/jpeg;base64,...)
            if url.startswith("data:"):
                # 解析 data URL
                match = re.match(r"data:([^;]+);base64,(.+)", url)
                if match:
                    mime_type = match.group(1)
                    base64_data = match.group(2)
                    
                    # 解码 base64 数据
                    image_bytes = base64.b64decode(base64_data)
                    
                    images.append({
                        "data": image_bytes,
                        "mime_type": mime_type
                    })
            else:
                # 处理普通 URL - 这里可以考虑下载图片，但出于安全考虑暂不实现
                # 可以记录日志或返回错误
                pass
                
        except Exception as e:
            # 记录错误但不中断处理
            continue
    
    return images


def segments_to_text_and_images(segments: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
    """从消息段中提取文本和图片数据"""
    text_parts: List[str] = []
    images: List[Dict[str, Any]] = []
    
    for seg in segments:
        if isinstance(seg, dict):
            if seg.get("type") == "text" and isinstance(seg.get("text"), str):
                text_parts.append(seg.get("text") or "")
            elif seg.get("type") == "image_url":
                # 提取图片数据
                image_url_data = seg.get("image_url", {})
                if isinstance(image_url_data, dict) and "url" in image_url_data:
                    url = image_url_data["url"]
                    
                    try:
                        # 处理 data URL 格式
                        if url.startswith("data:"):
                            match = re.match(r"data:([^;]+);base64,(.+)", url)
                            if match:
                                mime_type = match.group(1)
                                base64_data = match.group(2)
                                # 解码为bytes，这是protobuf期望的格式
                                image_bytes = base64.b64decode(base64_data)
                                images.append({
                                    "data": image_bytes,  # 使用bytes
                                    "mime_type": mime_type
                                })
                    except Exception:
                        continue
    
    return "".join(text_parts), images 