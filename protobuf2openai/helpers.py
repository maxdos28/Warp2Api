from __future__ import annotations

from typing import Any, Dict, List


def _get(d: Dict[str, Any], *names: str) -> Any:
    for n in names:
        if isinstance(d, dict) and n in d:
            return d[n]
    return None


def normalize_content_to_list(content: Any) -> List[Dict[str, Any]]:
    """
    Normalize content to a list of content blocks, supporting both OpenAI and Claude formats.
    Converts OpenAI image_url format to Claude image format.
    """
    segments: List[Dict[str, Any]] = []
    try:
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type")
                    
                    # Handle text content
                    if item_type == "text" and isinstance(item.get("text"), str):
                        segments.append({"type": "text", "text": item.get("text")})
                    
                    # Handle OpenAI image_url format -> convert to Claude image format
                    elif item_type == "image_url":
                        image_url_data = item.get("image_url", {})
                        url = image_url_data.get("url", "")
                        
                        if url.startswith("data:"):
                            # Parse data URL: data:image/png;base64,iVBORw0KGgo...
                            try:
                                header, data = url.split(",", 1)
                                media_type = header.split(";")[0].split(":")[1]  # Extract image/png
                                
                                # Convert to Claude format
                                claude_image = {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": data
                                    }
                                }
                                segments.append(claude_image)
                            except (ValueError, IndexError):
                                # If parsing fails, skip this image
                                continue
                        elif url.startswith("http"):
                            # For HTTP URLs, we'll need to download and convert
                            # For now, we'll add a placeholder
                            claude_image = {
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": url
                                }
                            }
                            segments.append(claude_image)
                    
                    # Handle Claude image format (pass through)
                    elif item_type == "image":
                        segments.append(item)
                    
                    # Handle other content types
                    elif item_type in ["tool_use", "tool_result"]:
                        segments.append(item)
                    
                    # Handle legacy format or unknown types
                    else:
                        seg: Dict[str, Any] = {}
                        if item_type:
                            seg["type"] = item_type
                        if isinstance(item.get("text"), str):
                            seg["text"] = item.get("text")
                        # Preserve other properties
                        for key, value in item.items():
                            if key not in ["type", "text"] and value is not None:
                                seg[key] = value
                        if seg:
                            segments.append(seg)
            
            return segments
        
        if isinstance(content, dict):
            # Single content block
            if isinstance(content.get("text"), str):
                return [{"type": "text", "text": content.get("text")}]
            elif content.get("type") in ["image", "image_url"]:
                # Process single image
                return normalize_content_to_list([content])
    
    except Exception as e:
        # Log error but don't crash
        print(f"Warning: Error normalizing content: {e}")
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
    Convert content segments to Warp results format, supporting text and images.
    """
    results: List[Dict[str, Any]] = []
    
    for seg in segments:
        if not isinstance(seg, dict):
            continue
            
        seg_type = seg.get("type")
        
        # Handle text content
        if seg_type == "text" and isinstance(seg.get("text"), str):
            results.append({"text": {"text": seg.get("text")}})
        
        # Handle image content
        elif seg_type == "image":
            source = seg.get("source", {})
            
            if isinstance(source, dict):
                # Convert Claude image format to Warp format
                if source.get("type") == "base64":
                    results.append({
                        "image": {
                            "type": "base64",
                            "media_type": source.get("media_type", "image/png"),
                            "data": source.get("data", "")
                        }
                    })
                elif source.get("type") == "url":
                    results.append({
                        "image": {
                            "type": "url",
                            "url": source.get("url", "")
                        }
                    })
        
        # Handle other content types (tool_use, tool_result, etc.)
        elif seg_type in ["tool_use", "tool_result"]:
            # Pass through tool-related content
            results.append({"tool": seg})
    
    return results 