#!/usr/bin/env python3
"""
Token缓存和去重管理器
"""

import time
import hashlib
import asyncio
from typing import Optional, Dict, Any, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

from .logging import logger


@dataclass
class TokenRequest:
    """Token申请请求"""
    request_id: str
    timestamp: float
    error_context: str
    caller_info: str
    
    def __post_init__(self):
        if not self.request_id:
            # 生成基于内容的唯一ID
            content = f"{self.error_context}_{self.caller_info}_{int(self.timestamp/60)}"  # 按分钟分组
            self.request_id = hashlib.md5(content.encode()).hexdigest()[:16]


class TokenRequestDeduplicator:
    """Token申请去重器"""
    
    def __init__(self, dedup_window: int = 300):  # 5分钟去重窗口
        self.dedup_window = dedup_window
        self.recent_requests: Dict[str, TokenRequest] = {}
        self.request_counts = defaultdict(int)
        
    def _cleanup_old_requests(self, current_time: float):
        """清理过期的请求记录"""
        cutoff_time = current_time - self.dedup_window
        
        expired_ids = []
        for req_id, request in self.recent_requests.items():
            if request.timestamp < cutoff_time:
                expired_ids.append(req_id)
        
        for req_id in expired_ids:
            del self.recent_requests[req_id]
    
    def is_duplicate_request(self, error_context: str, caller_info: str) -> Tuple[bool, str]:
        """检查是否是重复请求"""
        current_time = time.time()
        self._cleanup_old_requests(current_time)
        
        # 创建请求对象
        request = TokenRequest("", current_time, error_context, caller_info)
        
        # 检查是否有相同的请求
        if request.request_id in self.recent_requests:
            existing_request = self.recent_requests[request.request_id]
            time_diff = current_time - existing_request.timestamp
            return True, f"重复请求（{int(time_diff)}秒前已申请）"
        
        # 记录新请求
        self.recent_requests[request.request_id] = request
        self.request_counts[request.request_id] += 1
        
        return False, "新请求"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取去重统计"""
        current_time = time.time()
        self._cleanup_old_requests(current_time)
        
        return {
            "active_requests": len(self.recent_requests),
            "total_request_types": len(self.request_counts),
            "dedup_window": self.dedup_window,
            "recent_requests": [
                {
                    "id": req.request_id,
                    "age": int(current_time - req.timestamp),
                    "context": req.error_context[:50],
                    "caller": req.caller_info
                }
                for req in list(self.recent_requests.values())[-5:]  # 最近5个
            ]
        }


class TokenCache:
    """Token缓存管理器"""
    
    def __init__(self, cache_ttl: int = 3600):  # 1小时缓存
        self.cache_ttl = cache_ttl
        self.token_cache: Dict[str, Dict[str, Any]] = {}
        self.usage_stats = defaultdict(int)
        
    def _generate_cache_key(self, token_type: str, context: str = "") -> str:
        """生成缓存键"""
        key_content = f"{token_type}_{context}_{int(time.time()/3600)}"  # 按小时分组
        return hashlib.md5(key_content.encode()).hexdigest()[:16]
    
    def get_cached_token(self, token_type: str, context: str = "") -> Optional[str]:
        """获取缓存的token"""
        cache_key = self._generate_cache_key(token_type, context)
        
        if cache_key in self.token_cache:
            cache_entry = self.token_cache[cache_key]
            
            # 检查是否过期
            if time.time() - cache_entry["created_at"] < self.cache_ttl:
                # 检查token是否仍然有效
                token = cache_entry["token"]
                if token and not is_token_expired(token):
                    self.usage_stats["cache_hits"] += 1
                    logger.debug(f"[TokenCache] 使用缓存token: {cache_key}")
                    return token
            
            # 过期或无效，删除缓存
            del self.token_cache[cache_key]
        
        self.usage_stats["cache_misses"] += 1
        return None
    
    def cache_token(self, token: str, token_type: str, context: str = ""):
        """缓存token"""
        cache_key = self._generate_cache_key(token_type, context)
        
        self.token_cache[cache_key] = {
            "token": token,
            "token_type": token_type,
            "context": context,
            "created_at": time.time(),
            "usage_count": 0
        }
        
        logger.debug(f"[TokenCache] 缓存新token: {cache_key}")
        
        # 清理过期缓存
        self._cleanup_expired_cache()
    
    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, cache_entry in self.token_cache.items():
            if current_time - cache_entry["created_at"] > self.cache_ttl:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.token_cache[key]
        
        if expired_keys:
            logger.debug(f"[TokenCache] 清理 {len(expired_keys)} 个过期缓存")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        self._cleanup_expired_cache()
        
        total_requests = self.usage_stats["cache_hits"] + self.usage_stats["cache_misses"]
        hit_rate = (self.usage_stats["cache_hits"] / max(total_requests, 1)) * 100
        
        return {
            "cache_size": len(self.token_cache),
            "cache_hits": self.usage_stats["cache_hits"],
            "cache_misses": self.usage_stats["cache_misses"],
            "hit_rate": hit_rate,
            "cache_ttl": self.cache_ttl
        }


class OptimizedTokenManager:
    """优化的Token管理器"""
    
    def __init__(self):
        self.deduplicator = TokenRequestDeduplicator()
        self.cache = TokenCache()
        self.request_queue = asyncio.Queue(maxsize=10)
        self.processing_requests: Set[str] = set()
        
    async def smart_request_anonymous_token(self, error_context: str = "", caller_info: str = "") -> Optional[str]:
        """智能申请匿名token"""
        # 1. 检查重复请求
        is_duplicate, reason = self.deduplicator.is_duplicate_request(error_context, caller_info)
        if is_duplicate:
            logger.info(f"[TokenManager] 跳过重复申请: {reason}")
            return None
        
        # 2. 检查缓存
        cached_token = self.cache.get_cached_token("anonymous", error_context)
        if cached_token:
            logger.info("[TokenManager] 使用缓存的匿名token")
            return cached_token
        
        # 3. 检查是否有正在处理的相同请求
        request_signature = hashlib.md5(f"{error_context}_{caller_info}".encode()).hexdigest()[:16]
        if request_signature in self.processing_requests:
            logger.info("[TokenManager] 相同请求正在处理中，等待结果...")
            # 等待一段时间，然后检查缓存
            await asyncio.sleep(2)
            return self.cache.get_cached_token("anonymous", error_context)
        
        # 4. 执行申请
        self.processing_requests.add(request_signature)
        try:
            logger.info(f"[TokenManager] 开始智能申请匿名token: {caller_info}")
            
            from .smart_token_manager import smart_acquire_anonymous_token
            new_token = await smart_acquire_anonymous_token(error_context)
            
            if new_token:
                # 缓存新token
                self.cache.cache_token(new_token, "anonymous", error_context)
                logger.info("[TokenManager] 匿名token申请成功并已缓存")
                return new_token
            else:
                logger.info("[TokenManager] 智能管理器决定不申请token")
                return None
                
        except Exception as e:
            logger.error(f"[TokenManager] 智能申请失败: {e}")
            return None
        finally:
            self.processing_requests.discard(request_signature)
    
    def record_token_performance(self, success: bool, response_time: float, error_type: str = ""):
        """记录token性能"""
        try:
            from .smart_token_manager import record_api_usage
            record_api_usage(success, error_type)
        except:
            pass
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """获取综合统计"""
        try:
            from .smart_token_manager import get_smart_token_stats
            from .token_rate_limiter import get_token_request_stats
            
            return {
                "smart_manager": get_smart_token_stats(),
                "rate_limiter": get_token_request_stats(),
                "deduplicator": self.deduplicator.get_stats(),
                "cache": self.cache.get_stats(),
                "processing_requests": len(self.processing_requests)
            }
        except Exception as e:
            logger.error(f"Failed to get comprehensive stats: {e}")
            return {"error": str(e)}


# 全局实例
_global_optimized_manager: Optional[OptimizedTokenManager] = None


def get_optimized_token_manager() -> OptimizedTokenManager:
    """获取全局优化token管理器"""
    global _global_optimized_manager
    if _global_optimized_manager is None:
        _global_optimized_manager = OptimizedTokenManager()
        logger.info("[OptimizedTokenManager] 优化token管理器已初始化")
    return _global_optimized_manager


async def optimized_request_anonymous_token(error_context: str = "", caller_info: str = "") -> Optional[str]:
    """优化的匿名token申请接口"""
    manager = get_optimized_token_manager()
    return await manager.smart_request_anonymous_token(error_context, caller_info)


def record_token_performance(success: bool, response_time: float, error_type: str = ""):
    """记录token性能"""
    manager = get_optimized_token_manager()
    manager.record_token_performance(success, response_time, error_type)


def get_token_management_stats() -> Dict[str, Any]:
    """获取token管理统计"""
    manager = get_optimized_token_manager()
    return manager.get_comprehensive_stats()