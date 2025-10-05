from __future__ import annotations

from typing import Any, Dict, List

from .logging import logger


def _get(d: Dict[str, Any], *names: str) -> Any:
    for n in names:
        if isinstance(d, dict) and n in d:
            return d[n]
    return None


def normalize_content_to_list(content: Any) -> List[Dict[str, Any]]:
    """
    规范化内容为统一的列表格式，支持多模态（文本和图片）
    
    Args:
        content: 可以是字符串、字典或列表
        
    Returns:
        统一格式的段落列表，每个段落包含 type 字段（text 或 image_url）
    """
    segments: List[Dict[str, Any]] = []
    try:
        # 字符串 -> [{"type": "text", "text": "..."}]
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        
        # 列表 -> 处理每个元素
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type")
                    
                    # 文本内容
                    if item_type == "text" and isinstance(item.get("text"), str):
                        segments.append({"type": "text", "text": item.get("text")})
                    
                    # 图片内容（OpenAI 格式）
                    elif item_type == "image_url":
                        image_url_data = item.get("image_url")
                        if isinstance(image_url_data, dict):
                            # 保留完整的 image_url 对象
                            segments.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url_data.get("url", ""),
                                    "detail": image_url_data.get("detail", "auto")
                                }
                            })
                            logger.debug(f"Added image segment: {image_url_data.get('url', '')[:100]}...")
                        elif isinstance(image_url_data, str):
                            # 简化格式：{"type": "image_url", "image_url": "url"}
                            segments.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url_data,
                                    "detail": "auto"
                                }
                            })
                    
                    # 兼容：没有明确 type 但有 text 字段
                    elif not item_type and isinstance(item.get("text"), str):
                        segments.append({"type": "text", "text": item.get("text")})
                    
                    # 其他未识别的类型，保留原样
                    else:
                        seg: Dict[str, Any] = {}
                        if item_type:
                            seg["type"] = item_type
                        if isinstance(item.get("text"), str):
                            seg["text"] = item.get("text")
                        if seg:
                            segments.append(seg)
                            
            return segments
        
        # 字典 -> 单个元素
        if isinstance(content, dict):
            # 纯文本字典
            if isinstance(content.get("text"), str):
                return [{"type": "text", "text": content.get("text")}]
            # 图片字典
            elif content.get("type") == "image_url":
                image_url_data = content.get("image_url")
                if image_url_data:
                    return [{
                        "type": "image_url",
                        "image_url": image_url_data if isinstance(image_url_data, dict) else {"url": str(image_url_data), "detail": "auto"}
                    }]
    except Exception as e:
        logger.error(f"Error normalizing content: {e}")
        return []
    return []


def segments_to_text(segments: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for seg in segments:
        if isinstance(seg, dict) and seg.get("type") == "text" and isinstance(seg.get("text"), str):
            parts.append(seg.get("text") or "")
    return "".join(parts)


def segments_to_warp_results(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将段落列表转换为 Warp 结果格式
    
    注意：目前只处理文本段落，图片段落会被忽略
    未来可以扩展支持图片转换为 Warp 附件格式
    """
    results: List[Dict[str, Any]] = []
    for seg in segments:
        if isinstance(seg, dict) and seg.get("type") == "text" and isinstance(seg.get("text"), str):
            results.append({"text": {"text": seg.get("text")}})
        elif isinstance(seg, dict) and seg.get("type") == "image_url":
            # TODO: 未来可以将图片转换为 Warp 附件格式
            logger.debug("Image segment in tool result (not yet supported for Warp results)")
    return results


def has_images(segments: List[Dict[str, Any]]) -> bool:
    """检查段落列表中是否包含图片"""
    for seg in segments:
        if isinstance(seg, dict) and seg.get("type") == "image_url":
            return True
    return False


def extract_images(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从段落列表中提取所有图片"""
    images = []
    for seg in segments:
        if isinstance(seg, dict) and seg.get("type") == "image_url":
            images.append(seg)
    return images


def get_text_only(segments: List[Dict[str, Any]]) -> str:
    """从段落列表中提取纯文本（忽略图片）"""
    return segments_to_text(segments) 