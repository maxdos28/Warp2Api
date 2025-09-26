#!/usr/bin/env python3
"""
Token申请频率限制器
"""

import time
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from .logging import logger

class TokenRateLimiter:
    """Token申请频率限制器"""
    
    def __init__(self, max_requests_per_hour: int = 10, max_requests_per_day: int = 50):
        self.max_requests_per_hour = max_requests_per_hour
        self.max_requests_per_day = max_requests_per_day
        self.state_file = Path(".token_rate_limit_state.json")
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load rate limit state: {e}")
        
        return {
            "hourly_requests": [],
            "daily_requests": [],
            "last_successful_request": 0,
            "consecutive_failures": 0,
            "total_requests": 0
        }
    
    def _save_state(self):
        """保存状态"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save rate limit state: {e}")
    
    def _cleanup_old_requests(self, current_time: float):
        """清理过期的请求记录"""
        # 清理1小时前的记录
        hour_ago = current_time - 3600
        self.state["hourly_requests"] = [
            req_time for req_time in self.state["hourly_requests"] 
            if req_time > hour_ago
        ]
        
        # 清理24小时前的记录
        day_ago = current_time - 86400
        self.state["daily_requests"] = [
            req_time for req_time in self.state["daily_requests"]
            if req_time > day_ago
        ]
    
    def can_make_request(self) -> tuple[bool, str, int]:
        """检查是否可以发起请求"""
        current_time = time.time()
        self._cleanup_old_requests(current_time)
        
        # 检查小时限制
        hourly_count = len(self.state["hourly_requests"])
        if hourly_count >= self.max_requests_per_hour:
            next_available = min(self.state["hourly_requests"]) + 3600
            wait_time = int(next_available - current_time)
            return False, f"小时限制已达到 ({hourly_count}/{self.max_requests_per_hour})", wait_time
        
        # 检查日限制
        daily_count = len(self.state["daily_requests"])
        if daily_count >= self.max_requests_per_day:
            next_available = min(self.state["daily_requests"]) + 86400
            wait_time = int(next_available - current_time)
            return False, f"日限制已达到 ({daily_count}/{self.max_requests_per_day})", wait_time
        
        # 检查连续失败
        if self.state["consecutive_failures"] >= 5:
            last_request = self.state.get("last_failed_request", 0)
            cooldown_time = 300 * (2 ** min(self.state["consecutive_failures"] - 5, 4))  # 指数退避
            if current_time - last_request < cooldown_time:
                wait_time = int(cooldown_time - (current_time - last_request))
                return False, f"连续失败冷却中 ({self.state['consecutive_failures']} 次失败)", wait_time
        
        # 检查最小间隔（防止过于频繁）
        min_interval = 60  # 最小1分钟间隔
        if self.state.get("last_successful_request", 0) > 0:
            time_since_last = current_time - self.state["last_successful_request"]
            if time_since_last < min_interval:
                wait_time = int(min_interval - time_since_last)
                return False, f"请求间隔过短，需等待 {wait_time} 秒", wait_time
        
        return True, "允许申请", 0
    
    def record_request_attempt(self):
        """记录申请尝试"""
        current_time = time.time()
        self.state["hourly_requests"].append(current_time)
        self.state["daily_requests"].append(current_time)
        self.state["total_requests"] += 1
        self._save_state()
    
    def record_request_success(self):
        """记录申请成功"""
        current_time = time.time()
        self.state["last_successful_request"] = current_time
        self.state["consecutive_failures"] = 0
        self._save_state()
        logger.info(f"[TokenRateLimit] 记录成功申请，重置失败计数")
    
    def record_request_failure(self, error_type: str = "unknown"):
        """记录申请失败"""
        current_time = time.time()
        self.state["consecutive_failures"] += 1
        self.state["last_failed_request"] = current_time
        self.state.setdefault("failure_types", {})
        self.state["failure_types"][error_type] = self.state["failure_types"].get(error_type, 0) + 1
        self._save_state()
        logger.warning(f"[TokenRateLimit] 记录申请失败: {error_type}, 连续失败 {self.state['consecutive_failures']} 次")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        current_time = time.time()
        self._cleanup_old_requests(current_time)
        
        return {
            "total_requests": self.state["total_requests"],
            "hourly_requests": len(self.state["hourly_requests"]),
            "daily_requests": len(self.state["daily_requests"]),
            "consecutive_failures": self.state["consecutive_failures"],
            "last_successful_request": self.state.get("last_successful_request", 0),
            "failure_types": self.state.get("failure_types", {}),
            "limits": {
                "max_per_hour": self.max_requests_per_hour,
                "max_per_day": self.max_requests_per_day
            }
        }
    
    def reset_stats(self):
        """重置统计"""
        self.state = {
            "hourly_requests": [],
            "daily_requests": [],
            "last_successful_request": 0,
            "consecutive_failures": 0,
            "total_requests": 0
        }
        self._save_state()
        logger.info("[TokenRateLimit] 统计信息已重置")


# 全局实例
_global_rate_limiter: Optional[TokenRateLimiter] = None

def get_token_rate_limiter() -> TokenRateLimiter:
    """获取全局token频率限制器"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = TokenRateLimiter()
    return _global_rate_limiter

def can_request_anonymous_token() -> tuple[bool, str, int]:
    """检查是否可以申请匿名token"""
    limiter = get_token_rate_limiter()
    return limiter.can_make_request()

def record_anonymous_token_attempt():
    """记录匿名token申请尝试"""
    limiter = get_token_rate_limiter()
    limiter.record_request_attempt()

def record_anonymous_token_success():
    """记录匿名token申请成功"""
    limiter = get_token_rate_limiter()
    limiter.record_request_success()

def record_anonymous_token_failure(error_type: str = "unknown"):
    """记录匿名token申请失败"""
    limiter = get_token_rate_limiter()
    limiter.record_request_failure(error_type)

def get_token_request_stats() -> Dict[str, Any]:
    """获取token申请统计"""
    limiter = get_token_rate_limiter()
    return limiter.get_stats()