from __future__ import annotations

import asyncio
import time
import hashlib
from typing import Any, Dict, Optional, List, Tuple, Callable
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import logger


class RateLimitStrategy(Enum):
    """限流策略"""
    FIXED_WINDOW = "fixed_window"      # 固定窗口
    SLIDING_WINDOW = "sliding_window"  # 滑动窗口
    TOKEN_BUCKET = "token_bucket"      # 令牌桶
    LEAKY_BUCKET = "leaky_bucket"      # 漏桶
    ADAPTIVE = "adaptive"              # 自适应


@dataclass
class RateLimitConfig:
    """限流配置"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    key_func: Optional[Callable[[Request], str]] = None
    whitelist: List[str] = None
    blacklist: List[str] = None
    
    def __post_init__(self):
        if self.whitelist is None:
            self.whitelist = []
        if self.blacklist is None:
            self.blacklist = []


class RateLimitState:
    """限流状态"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: deque = deque()
        self.tokens = config.burst_size
        self.last_refill = time.time()
        self.total_requests = 0
        self.blocked_requests = 0
        
    def is_allowed(self, current_time: float) -> Tuple[bool, Dict[str, Any]]:
        """检查是否允许请求"""
        self.total_requests += 1
        
        if self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._fixed_window_check(current_time)
        elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._sliding_window_check(current_time)
        elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._token_bucket_check(current_time)
        elif self.config.strategy == RateLimitStrategy.LEAKY_BUCKET:
            return self._leaky_bucket_check(current_time)
        elif self.config.strategy == RateLimitStrategy.ADAPTIVE:
            return self._adaptive_check(current_time)
        else:
            return True, {}
    
    def _fixed_window_check(self, current_time: float) -> Tuple[bool, Dict[str, Any]]:
        """固定窗口检查"""
        window_start = int(current_time // 60) * 60  # 1分钟窗口
        
        # 清理旧请求
        self.requests = deque([req_time for req_time in self.requests if req_time >= window_start])
        
        if len(self.requests) >= self.config.requests_per_minute:
            self.blocked_requests += 1
            return False, {
                "window_start": window_start,
                "requests_in_window": len(self.requests),
                "limit": self.config.requests_per_minute
            }
        
        self.requests.append(current_time)
        return True, {"requests_remaining": self.config.requests_per_minute - len(self.requests)}
    
    def _sliding_window_check(self, current_time: float) -> Tuple[bool, Dict[str, Any]]:
        """滑动窗口检查"""
        # 1分钟窗口
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        # 清理过期请求
        while self.requests and self.requests[0] < hour_ago:
            self.requests.popleft()
        
        # 统计最近1分钟和1小时的请求
        minute_requests = sum(1 for req_time in self.requests if req_time >= minute_ago)
        hour_requests = len(self.requests)
        
        # 检查限制
        if minute_requests >= self.config.requests_per_minute:
            self.blocked_requests += 1
            return False, {
                "reason": "minute_limit_exceeded",
                "minute_requests": minute_requests,
                "minute_limit": self.config.requests_per_minute
            }
        
        if hour_requests >= self.config.requests_per_hour:
            self.blocked_requests += 1
            return False, {
                "reason": "hour_limit_exceeded",
                "hour_requests": hour_requests,
                "hour_limit": self.config.requests_per_hour
            }
        
        self.requests.append(current_time)
        return True, {
            "minute_requests_remaining": self.config.requests_per_minute - minute_requests,
            "hour_requests_remaining": self.config.requests_per_hour - hour_requests
        }
    
    def _token_bucket_check(self, current_time: float) -> Tuple[bool, Dict[str, Any]]:
        """令牌桶检查"""
        # 计算需要添加的令牌
        time_passed = current_time - self.last_refill
        tokens_to_add = int(time_passed * (self.config.requests_per_minute / 60))
        
        if tokens_to_add > 0:
            self.tokens = min(self.config.burst_size, self.tokens + tokens_to_add)
            self.last_refill = current_time
        
        # 检查是否有令牌
        if self.tokens <= 0:
            self.blocked_requests += 1
            return False, {
                "tokens_available": self.tokens,
                "bucket_size": self.config.burst_size
            }
        
        self.tokens -= 1
        return True, {"tokens_remaining": self.tokens}
    
    def _leaky_bucket_check(self, current_time: float) -> Tuple[bool, Dict[str, Any]]:
        """漏桶检查"""
        # 计算泄漏的请求数
        time_passed = current_time - self.last_refill
        leaked_requests = int(time_passed * (self.config.requests_per_minute / 60))
        
        if leaked_requests > 0:
            # 移除泄漏的请求
            for _ in range(min(leaked_requests, len(self.requests))):
                if self.requests:
                    self.requests.popleft()
            self.last_refill = current_time
        
        # 检查桶是否已满
        if len(self.requests) >= self.config.burst_size:
            self.blocked_requests += 1
            return False, {
                "bucket_size": len(self.requests),
                "max_size": self.config.burst_size
            }
        
        self.requests.append(current_time)
        return True, {"bucket_space_remaining": self.config.burst_size - len(self.requests)}
    
    def _adaptive_check(self, current_time: float) -> Tuple[bool, Dict[str, Any]]:
        """自适应检查"""
        # 基于历史性能调整限制
        recent_window = 300  # 5分钟窗口
        recent_start = current_time - recent_window
        
        # 清理旧请求
        while self.requests and self.requests[0] < recent_start:
            self.requests.popleft()
        
        recent_requests = len(self.requests)
        
        # 计算动态限制
        if self.total_requests > 100:  # 有足够的历史数据
            block_rate = self.blocked_requests / self.total_requests
            
            if block_rate > 0.1:  # 阻塞率超过10%，放宽限制
                dynamic_limit = int(self.config.requests_per_minute * 1.2)
            elif block_rate < 0.01:  # 阻塞率低于1%，收紧限制
                dynamic_limit = int(self.config.requests_per_minute * 0.8)
            else:
                dynamic_limit = self.config.requests_per_minute
        else:
            dynamic_limit = self.config.requests_per_minute
        
        # 转换为5分钟窗口的限制
        window_limit = int(dynamic_limit * (recent_window / 60))
        
        if recent_requests >= window_limit:
            self.blocked_requests += 1
            return False, {
                "reason": "adaptive_limit_exceeded",
                "recent_requests": recent_requests,
                "adaptive_limit": window_limit,
                "block_rate": self.blocked_requests / self.total_requests
            }
        
        self.requests.append(current_time)
        return True, {
            "requests_remaining": window_limit - recent_requests,
            "adaptive_limit": window_limit
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        block_rate = self.blocked_requests / max(1, self.total_requests)
        
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": block_rate,
            "current_tokens": getattr(self, 'tokens', 0),
            "requests_in_window": len(self.requests),
            "strategy": self.config.strategy.value
        }


class RateLimiter:
    """限流器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.states: Dict[str, RateLimitState] = {}
        self.cleanup_interval = 300  # 5分钟清理一次
        self.last_cleanup = time.time()
        
        # 全局统计
        self.global_stats = {
            "total_requests": 0,
            "total_blocked": 0,
            "unique_clients": 0,
        }
    
    def get_client_key(self, request: Request) -> str:
        """获取客户端标识"""
        if self.config.key_func:
            return self.config.key_func(request)
        
        # 默认使用IP地址
        client_ip = request.client.host if request.client else "unknown"
        
        # 检查X-Forwarded-For头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # 检查X-Real-IP头
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            client_ip = real_ip.strip()
        
        return client_ip
    
    def is_whitelisted(self, client_key: str) -> bool:
        """检查是否在白名单中"""
        return client_key in self.config.whitelist
    
    def is_blacklisted(self, client_key: str) -> bool:
        """检查是否在黑名单中"""
        return client_key in self.config.blacklist
    
    async def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, Any]]:
        """检查限流"""
        current_time = time.time()
        client_key = self.get_client_key(request)
        
        # 更新全局统计
        self.global_stats["total_requests"] += 1
        
        # 检查黑名单
        if self.is_blacklisted(client_key):
            self.global_stats["total_blocked"] += 1
            return False, {"reason": "blacklisted", "client": client_key}
        
        # 检查白名单
        if self.is_whitelisted(client_key):
            return True, {"reason": "whitelisted", "client": client_key}
        
        # 获取或创建客户端状态
        if client_key not in self.states:
            self.states[client_key] = RateLimitState(self.config)
            self.global_stats["unique_clients"] = len(self.states)
        
        state = self.states[client_key]
        allowed, info = state.is_allowed(current_time)
        
        if not allowed:
            self.global_stats["total_blocked"] += 1
        
        # 定期清理
        await self._cleanup_if_needed(current_time)
        
        info.update({"client": client_key, "timestamp": current_time})
        return allowed, info
    
    async def _cleanup_if_needed(self, current_time: float):
        """按需清理过期状态"""
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        # 清理长时间未活动的客户端状态
        inactive_threshold = 3600  # 1小时
        inactive_clients = []
        
        for client_key, state in self.states.items():
            # 检查最后活动时间
            if hasattr(state, 'requests') and state.requests:
                last_activity = max(state.requests) if state.requests else 0
                if current_time - last_activity > inactive_threshold:
                    inactive_clients.append(client_key)
            elif current_time - state.last_refill > inactive_threshold:
                inactive_clients.append(client_key)
        
        # 移除非活跃客户端
        for client_key in inactive_clients:
            del self.states[client_key]
        
        self.global_stats["unique_clients"] = len(self.states)
        self.last_cleanup = current_time
        
        if inactive_clients:
            logger.debug(f"[RateLimit] Cleaned up {len(inactive_clients)} inactive client states")
    
    def get_client_stats(self, client_key: str) -> Optional[Dict[str, Any]]:
        """获取客户端统计"""
        if client_key in self.states:
            return self.states[client_key].get_stats()
        return None
    
    def get_global_stats(self) -> Dict[str, Any]:
        """获取全局统计"""
        stats = self.global_stats.copy()
        
        if stats["total_requests"] > 0:
            stats["global_block_rate"] = stats["total_blocked"] / stats["total_requests"]
        else:
            stats["global_block_rate"] = 0
        
        stats["active_clients"] = len(self.states)
        stats["config"] = {
            "requests_per_minute": self.config.requests_per_minute,
            "requests_per_hour": self.config.requests_per_hour,
            "strategy": self.config.strategy.value
        }
        
        return stats
    
    def add_to_whitelist(self, client_key: str):
        """添加到白名单"""
        if client_key not in self.config.whitelist:
            self.config.whitelist.append(client_key)
            logger.info(f"[RateLimit] Added {client_key} to whitelist")
    
    def add_to_blacklist(self, client_key: str):
        """添加到黑名单"""
        if client_key not in self.config.blacklist:
            self.config.blacklist.append(client_key)
            logger.info(f"[RateLimit] Added {client_key} to blacklist")
    
    def remove_from_whitelist(self, client_key: str):
        """从白名单移除"""
        if client_key in self.config.whitelist:
            self.config.whitelist.remove(client_key)
            logger.info(f"[RateLimit] Removed {client_key} from whitelist")
    
    def remove_from_blacklist(self, client_key: str):
        """从黑名单移除"""
        if client_key in self.config.blacklist:
            self.config.blacklist.remove(client_key)
            logger.info(f"[RateLimit] Removed {client_key} from blacklist")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查限流
        allowed, info = await self.rate_limiter.check_rate_limit(request)
        
        if not allowed:
            # 返回429状态码
            logger.warning(f"[RateLimit] Request blocked: {info}")
            
            # 添加限流头部
            headers = {
                "X-RateLimit-Limit": str(self.rate_limiter.config.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + 60)),
                "Retry-After": "60"
            }
            
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "info": info
                },
                headers=headers
            )
        
        # 执行请求
        response = await call_next(request)
        
        # 添加限流头部到响应
        if "requests_remaining" in info:
            response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.config.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(info["requests_remaining"])
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        return response


# 预定义配置
class RateLimitPresets:
    """预定义限流配置"""
    
    @staticmethod
    def conservative() -> RateLimitConfig:
        """保守配置"""
        return RateLimitConfig(
            requests_per_minute=30,
            requests_per_hour=500,
            burst_size=5,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
    
    @staticmethod
    def moderate() -> RateLimitConfig:
        """中等配置"""
        return RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_size=10,
            strategy=RateLimitStrategy.TOKEN_BUCKET
        )
    
    @staticmethod
    def liberal() -> RateLimitConfig:
        """宽松配置"""
        return RateLimitConfig(
            requests_per_minute=120,
            requests_per_hour=2000,
            burst_size=20,
            strategy=RateLimitStrategy.ADAPTIVE
        )
    
    @staticmethod
    def api_heavy() -> RateLimitConfig:
        """API密集型配置"""
        return RateLimitConfig(
            requests_per_minute=300,
            requests_per_hour=5000,
            burst_size=50,
            strategy=RateLimitStrategy.LEAKY_BUCKET
        )


# 全局限流器实例
_global_rate_limiter: Optional[RateLimiter] = None


def setup_rate_limiter(config: RateLimitConfig) -> RateLimiter:
    """设置全局限流器"""
    global _global_rate_limiter
    _global_rate_limiter = RateLimiter(config)
    logger.info(f"[RateLimit] Rate limiter configured: {config.strategy.value}, {config.requests_per_minute}/min")
    return _global_rate_limiter


def get_rate_limiter() -> Optional[RateLimiter]:
    """获取全局限流器"""
    return _global_rate_limiter


def get_rate_limit_stats() -> Dict[str, Any]:
    """获取限流统计"""
    if _global_rate_limiter:
        return _global_rate_limiter.get_global_stats()
    return {"error": "Rate limiter not configured"}