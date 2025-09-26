from __future__ import annotations

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
                    elif t == "image_url" and item.get("image_url"):
                        # 处理图像URL格式
                        segments.append({"type": "image_url", "image_url": item.get("image_url")})
                    elif t == "image" and item.get("source"):
                        # 处理Anthropic格式的图像
                        segments.append({"type": "image", "source": item.get("source")})
                    else:
                        seg: Dict[str, Any] = {}
                        if t:
                            seg["type"] = t
                        if isinstance(item.get("text"), str):
                            seg["text"] = item.get("text")
                        if item.get("image_url"):
                            seg["image_url"] = item.get("image_url")
                        if item.get("source"):
                            seg["source"] = item.get("source")
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
    """从segments中提取图像数据，转换为Warp protobuf格式"""
    import base64
    import re
    
    images: List[Dict[str, Any]] = []
    
    for seg in segments:
        if not isinstance(seg, dict):
            continue
            
        # 处理image_url格式 (OpenAI格式)
        if seg.get("type") == "image_url":
            image_url = seg.get("image_url", {})
            url = image_url.get("url", "")
            
            # 解析data URL: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
            data_url_match = re.match(r'data:image/([^;]+);base64,(.+)', url)
            if data_url_match:
                mime_type = f"image/{data_url_match.group(1)}"
                image_data = data_url_match.group(2)
                try:
                    # 验证base64数据，但保存为字符串而不是bytes
                    base64.b64decode(image_data)  # 验证数据有效性
                    images.append({
                        "data": image_data,  # 保存为base64字符串，不解码
                        "mime_type": mime_type
                    })
                except Exception as e:
                    print(f"Warning: Failed to decode image data: {e}")
            
        # 处理image格式 (Anthropic格式)  
        elif seg.get("type") == "image":
            source = seg.get("source", {})
            if source.get("type") == "base64":
                media_type = source.get("media_type", "image/png")
                image_data = source.get("data", "")
                try:
                    base64.b64decode(image_data)  # 验证数据有效性
                    images.append({
                        "data": image_data,  # 保存为base64字符串，不解码
                        "mime_type": media_type
                    })
                except Exception as e:
                    print(f"Warning: Failed to decode Anthropic image data: {e}")
    
    return images 