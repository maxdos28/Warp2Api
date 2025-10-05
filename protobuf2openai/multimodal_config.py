"""
多模态功能配置

管理图片处理、文件附件等多模态功能的配置选项
"""

from __future__ import annotations

import os
from typing import Optional


class MultimodalConfig:
    """多模态功能配置类"""
    
    # 图片处理配置
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("W2A_MAX_IMAGE_SIZE_MB", "20"))
    MAX_IMAGE_SIZE_BYTES: int = MAX_IMAGE_SIZE_MB * 1024 * 1024
    
    # 支持的图片格式
    SUPPORTED_IMAGE_FORMATS = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
        'image/webp', 'image/bmp', 'image/tiff'
    }
    
    # 下载配置
    IMAGE_DOWNLOAD_TIMEOUT: float = float(os.getenv("W2A_IMAGE_DOWNLOAD_TIMEOUT", "30.0"))
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("W2A_MAX_CONCURRENT_DOWNLOADS", "5"))
    
    # 功能开关
    ENABLE_MULTIMODAL: bool = os.getenv("W2A_ENABLE_MULTIMODAL", "true").lower() in ("true", "1", "yes")
    ENABLE_IMAGE_DOWNLOAD: bool = os.getenv("W2A_ENABLE_IMAGE_DOWNLOAD", "true").lower() in ("true", "1", "yes")
    
    # 图片处理选项
    AUTO_RESIZE_LARGE_IMAGES: bool = os.getenv("W2A_AUTO_RESIZE_IMAGES", "false").lower() in ("true", "1", "yes")
    MAX_IMAGE_DIMENSION: Optional[int] = int(os.getenv("W2A_MAX_IMAGE_DIMENSION", "2048")) if os.getenv("W2A_MAX_IMAGE_DIMENSION") else None
    
    # 缓存配置
    ENABLE_IMAGE_CACHE: bool = os.getenv("W2A_ENABLE_IMAGE_CACHE", "false").lower() in ("true", "1", "yes")
    IMAGE_CACHE_DIR: str = os.getenv("W2A_IMAGE_CACHE_DIR", ".cache/images")
    IMAGE_CACHE_MAX_SIZE_MB: int = int(os.getenv("W2A_IMAGE_CACHE_MAX_SIZE_MB", "100"))
    
    @classmethod
    def is_multimodal_enabled(cls) -> bool:
        """检查多模态功能是否启用"""
        return cls.ENABLE_MULTIMODAL
    
    @classmethod
    def can_download_images(cls) -> bool:
        """检查是否允许下载图片"""
        return cls.ENABLE_MULTIMODAL and cls.ENABLE_IMAGE_DOWNLOAD
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """获取配置摘要（用于日志）"""
        return {
            "multimodal_enabled": cls.ENABLE_MULTIMODAL,
            "image_download_enabled": cls.ENABLE_IMAGE_DOWNLOAD,
            "max_image_size_mb": cls.MAX_IMAGE_SIZE_MB,
            "download_timeout": cls.IMAGE_DOWNLOAD_TIMEOUT,
            "supported_formats": list(cls.SUPPORTED_IMAGE_FORMATS),
            "auto_resize": cls.AUTO_RESIZE_LARGE_IMAGES,
        }


# 全局配置实例
config = MultimodalConfig()
