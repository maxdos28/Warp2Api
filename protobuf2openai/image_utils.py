"""
图片处理工具模块

支持多模态功能：
- 下载远程图片
- Base64 编码/解码
- 图片格式验证
- 图片大小限制
"""

from __future__ import annotations

import base64
import io
import mimetypes
import re
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx

from .logging import logger
from .multimodal_config import config

# 从配置中获取参数
MAX_IMAGE_SIZE_MB = config.MAX_IMAGE_SIZE_MB
MAX_IMAGE_SIZE_BYTES = config.MAX_IMAGE_SIZE_BYTES
SUPPORTED_IMAGE_FORMATS = config.SUPPORTED_IMAGE_FORMATS
REQUEST_TIMEOUT = config.IMAGE_DOWNLOAD_TIMEOUT


def is_base64_image(data: str) -> bool:
    """检查字符串是否为 base64 编码的图片"""
    if not data:
        return False
    # 检查 data URL 格式：data:image/xxx;base64,xxxxx
    if data.startswith('data:image/'):
        return ';base64,' in data
    # 检查纯 base64 字符串
    if re.match(r'^[A-Za-z0-9+/=]+$', data):
        return True
    return False


def is_image_url(url: str) -> bool:
    """检查 URL 是否指向图片资源"""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        if not parsed.scheme in ('http', 'https'):
            return False
        # 检查文件扩展名
        path = parsed.path.lower()
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg')
        if any(path.endswith(ext) for ext in image_extensions):
            return True
        return False
    except Exception:
        return False


def extract_base64_data(data_url: str) -> Tuple[Optional[str], Optional[bytes]]:
    """
    从 data URL 中提取 MIME 类型和二进制数据
    
    Args:
        data_url: data:image/png;base64,iVBORw0KGgo... 格式的字符串
        
    Returns:
        (mime_type, binary_data) 元组
    """
    try:
        if not data_url.startswith('data:'):
            # 尝试直接解码为 base64
            try:
                binary_data = base64.b64decode(data_url)
                return None, binary_data
            except Exception:
                return None, None
        
        # 解析 data URL
        # 格式: data:[<mediatype>][;base64],<data>
        header, encoded = data_url.split(',', 1)
        mime_type = None
        
        if ';base64' in header:
            mime_part = header.replace('data:', '').replace(';base64', '').strip()
            if mime_part:
                mime_type = mime_part
        
        # 解码 base64
        binary_data = base64.b64decode(encoded)
        return mime_type, binary_data
        
    except Exception as e:
        logger.error(f"Failed to extract base64 data: {e}")
        return None, None


def validate_image_data(data: bytes, mime_type: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    验证图片数据
    
    Args:
        data: 二进制图片数据
        mime_type: MIME 类型（可选）
        
    Returns:
        (is_valid, error_message) 元组
    """
    # 检查大小
    if len(data) > MAX_IMAGE_SIZE_BYTES:
        return False, f"Image size {len(data)/1024/1024:.2f}MB exceeds maximum {MAX_IMAGE_SIZE_MB}MB"
    
    # 检查 MIME 类型
    if mime_type and mime_type not in SUPPORTED_IMAGE_FORMATS:
        return False, f"Unsupported image format: {mime_type}"
    
    # 检查文件头魔数（基本验证）
    if len(data) < 8:
        return False, "Invalid image data: too short"
    
    # 常见图片格式的魔数
    magic_numbers = {
        b'\xFF\xD8\xFF': 'image/jpeg',  # JPEG
        b'\x89PNG\r\n\x1a\n': 'image/png',  # PNG
        b'GIF87a': 'image/gif',  # GIF87a
        b'GIF89a': 'image/gif',  # GIF89a
        b'RIFF': 'image/webp',  # WebP (需要进一步检查)
        b'BM': 'image/bmp',  # BMP
        b'II*\x00': 'image/tiff',  # TIFF (little-endian)
        b'MM\x00*': 'image/tiff',  # TIFF (big-endian)
    }
    
    detected_format = None
    for magic, fmt in magic_numbers.items():
        if data.startswith(magic):
            detected_format = fmt
            break
    
    if not detected_format:
        logger.warning("Could not detect image format from magic number")
    
    return True, None


async def download_image(url: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """
    从 URL 下载图片
    
    Args:
        url: 图片 URL
        
    Returns:
        (binary_data, mime_type, error_message) 元组
    """
    try:
        logger.info(f"Downloading image from: {url}")
        
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                error_msg = f"Failed to download image: HTTP {response.status_code}"
                logger.error(error_msg)
                return None, None, error_msg
            
            # 获取 MIME 类型
            content_type = response.headers.get('content-type', '').split(';')[0].strip()
            
            # 验证是否为图片
            if content_type and not content_type.startswith('image/'):
                error_msg = f"URL does not point to an image: {content_type}"
                logger.error(error_msg)
                return None, None, error_msg
            
            # 获取数据
            image_data = response.content
            
            # 验证图片数据
            is_valid, error_msg = validate_image_data(image_data, content_type)
            if not is_valid:
                logger.error(f"Image validation failed: {error_msg}")
                return None, None, error_msg
            
            logger.info(f"Successfully downloaded image: {len(image_data)} bytes, type: {content_type}")
            return image_data, content_type, None
            
    except httpx.TimeoutException:
        error_msg = f"Timeout downloading image from {url}"
        logger.error(error_msg)
        return None, None, error_msg
    except Exception as e:
        error_msg = f"Error downloading image: {e}"
        logger.error(error_msg)
        return None, None, error_msg


def encode_image_to_base64(image_data: bytes, mime_type: Optional[str] = None) -> str:
    """
    将图片数据编码为 base64 字符串
    
    Args:
        image_data: 二进制图片数据
        mime_type: MIME 类型（可选）
        
    Returns:
        base64 编码的字符串（如果提供了 mime_type，返回完整的 data URL）
    """
    encoded = base64.b64encode(image_data).decode('utf-8')
    
    if mime_type:
        return f"data:{mime_type};base64,{encoded}"
    else:
        return encoded


async def process_image_url(image_url_data: dict) -> Tuple[Optional[str], Optional[str]]:
    """
    处理 OpenAI 格式的 image_url 对象
    
    Args:
        image_url_data: {"url": "...", "detail": "auto"} 格式的字典
        
    Returns:
        (processed_url, error_message) 元组
        processed_url 为 base64 data URL 格式
    """
    url = image_url_data.get('url', '')
    if not url:
        return None, "Missing image URL"
    
    # 如果已经是 base64 data URL，直接返回
    if is_base64_image(url):
        logger.info("Image is already in base64 format")
        # 验证 base64 数据
        mime_type, data = extract_base64_data(url)
        if data:
            is_valid, error_msg = validate_image_data(data, mime_type)
            if not is_valid:
                return None, error_msg
            return url, None
        else:
            return None, "Invalid base64 image data"
    
    # 如果是 HTTP(S) URL，下载并转换
    if is_image_url(url):
        image_data, mime_type, error = await download_image(url)
        if error:
            return None, error
        
        # 编码为 base64 data URL
        data_url = encode_image_to_base64(image_data, mime_type)
        return data_url, None
    
    return None, f"Unsupported image URL format: {url}"


def get_image_info(data_url: str) -> dict:
    """
    获取图片信息（用于调试和日志）
    
    Args:
        data_url: base64 data URL
        
    Returns:
        包含图片信息的字典
    """
    mime_type, data = extract_base64_data(data_url)
    
    if not data:
        return {"error": "Invalid image data"}
    
    size_kb = len(data) / 1024
    
    return {
        "mime_type": mime_type or "unknown",
        "size_bytes": len(data),
        "size_kb": f"{size_kb:.2f}",
        "size_mb": f"{size_kb/1024:.2f}",
    }
