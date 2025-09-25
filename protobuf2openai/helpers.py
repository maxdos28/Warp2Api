from __future__ import annotations

from typing import Any, Dict, List

from .logging import logger


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
                    elif t == "image" and isinstance(item.get("source"), dict):
                        # Handle Claude API image content
                        source = item.get("source", {})
                        segments.append({
                            "type": "image",
                            "source": source
                        })
                    elif t == "image_url" and isinstance(item.get("image_url"), dict):
                        # Handle OpenAI format image content - convert to Claude format
                        image_url = item.get("image_url", {})
                        url = image_url.get("url", "")
                        
                        if url.startswith("data:"):
                            # Parse data URL: data:image/png;base64,iVBORw0KGgo...
                            try:
                                header, data = url.split(",", 1)
                                mime_type = header.split(":")[1].split(";")[0]
                                # Convert OpenAI format to Claude format
                                segments.append({
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": data
                                    }
                                })
                                print(f"[OpenAI Compat] Converted OpenAI image_url to Claude format: {mime_type}")
                            except Exception as e:
                                print(f"[OpenAI Compat] Failed to parse data URL: {e}")
                                # Keep original format as fallback
                                segments.append({
                                    "type": "image_url",
                                    "image_url": image_url
                                })
                        else:
                            # Keep original format for external URLs
                            segments.append({
                                "type": "image_url", 
                                "image_url": image_url
                            })
                    else:
                        seg: Dict[str, Any] = {}
                        if t:
                            seg["type"] = t
                        if isinstance(item.get("text"), str):
                            seg["text"] = item.get("text")
                        if isinstance(item.get("image_url"), dict):
                            seg["image_url"] = item.get("image_url")
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


def segments_to_text_and_images(segments: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
    """Extract text and images from segments, return (text, images)"""
    text_parts: List[str] = []
    images: List[Dict[str, Any]] = []
    
    for seg in segments:
        if isinstance(seg, dict):
            if seg.get("type") == "text" and isinstance(seg.get("text"), str):
                text_parts.append(seg.get("text") or "")
            elif seg.get("type") == "image" and isinstance(seg.get("source"), dict):
                # Extract image data from Claude API format
                source = seg.get("source", {})
                if source.get("type") == "base64":
                    try:
                        import base64
                        image_data_b64 = source.get("data", "")
                        mime_type = source.get("media_type", "image/png")
                        images.append({
                            "data": image_data_b64,  # Keep as base64 string
                            "mime_type": mime_type
                        })
                    except Exception as e:
                        logger.warning(f"Failed to process image base64 data: {e}")
            elif seg.get("type") == "image_url" and isinstance(seg.get("image_url"), dict):
                # Extract image data from OpenAI format (fallback)
                image_url = seg.get("image_url", {})
                url = image_url.get("url", "")
                if url.startswith("data:"):
                    # Handle data URL format: data:image/jpeg;base64,/9j/4AAQ...
                    try:
                        header, data = url.split(",", 1)
                        mime_type = header.split(":")[1].split(";")[0]
                        images.append({
                            "data": data,  # Keep as base64 string
                            "mime_type": mime_type
                        })
                    except Exception as e:
                        logger.warning(f"Failed to process image data URL: {e}")
    
    return "".join(text_parts), images


def segments_to_warp_results(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for seg in segments:
        if isinstance(seg, dict) and seg.get("type") == "text" and isinstance(seg.get("text"), str):
            results.append({"text": {"text": seg.get("text")}})
    return results 