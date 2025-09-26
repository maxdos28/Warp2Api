#!/usr/bin/env python3
"""
智能Token管理器
"""

import time
import json
import asyncio
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .logging import logger
from .auth import get_jwt_token, is_token_expired, is_using_personal_token


class TokenType(Enum):
    """Token类型"""
    PERSONAL = "personal"
    ANONYMOUS = "anonymous"
    UNKNOWN = "unknown"


class QuotaStatus(Enum):
    """配额状态"""
    AVAILABLE = "available"      # 有可用配额
    LOW = "low"                 # 配额较低
    EXHAUSTED = "exhausted"     # 配额用尽
    UNKNOWN = "unknown"         # 状态未知


@dataclass
class TokenInfo:
    """Token信息"""
    token: str
    token_type: TokenType
    quota_status: QuotaStatus
    expires_at: float
    last_used: float
    usage_count: int = 0
    error_count: int = 0


class SmartTokenManager:
    """智能Token管理器"""
    
    def __init__(self):
        self.state_file = Path(".smart_token_state.json")
        self.state = self._load_state()
        
        # 配置参数
        self.quota_check_interval = 300  # 5分钟检查一次配额
        self.token_reuse_threshold = 0.8  # 80%配额用完才考虑申请新token
        self.min_token_lifetime = 1800   # 最小token生命周期30分钟
        self.max_anonymous_tokens_per_hour = 3  # 每小时最多3个匿名token
        
    def _load_state(self) -> Dict[str, Any]:
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load smart token state: {e}")
        
        return {
            "current_token_info": None,
            "token_history": [],
            "quota_usage_pattern": {},
            "last_quota_check": 0,
            "anonymous_requests_this_hour": [],
            "performance_metrics": {
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_response_time": 0.1
            }
        }
    
    def _save_state(self):
        """保存状态"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save smart token state: {e}")
    
    def _cleanup_old_records(self, current_time: float):
        """清理过期记录"""
        # 清理1小时前的匿名请求记录
        hour_ago = current_time - 3600
        self.state["anonymous_requests_this_hour"] = [
            req_time for req_time in self.state["anonymous_requests_this_hour"]
            if req_time > hour_ago
        ]
        
        # 清理24小时前的token历史
        day_ago = current_time - 86400
        self.state["token_history"] = [
            token_info for token_info in self.state["token_history"]
            if token_info.get("created_at", 0) > day_ago
        ]
    
    def _analyze_current_token(self) -> Optional[TokenInfo]:
        """分析当前token"""
        current_token = get_jwt_token()
        if not current_token:
            return None
        
        # 判断token类型
        is_personal = is_using_personal_token()
        token_type = TokenType.PERSONAL if is_personal else TokenType.ANONYMOUS
        
        # 检查过期状态
        is_expired = is_token_expired(current_token)
        expires_at = time.time() + 3600 if not is_expired else time.time()
        
        # 从状态中获取使用信息
        current_info = self.state.get("current_token_info", {})
        if current_info and current_info.get("token") == current_token[:50]:
            usage_count = current_info.get("usage_count", 0)
            error_count = current_info.get("error_count", 0)
            last_used = current_info.get("last_used", time.time())
        else:
            usage_count = 0
            error_count = 0
            last_used = time.time()
        
        # 估算配额状态（基于使用模式）
        quota_status = self._estimate_quota_status(token_type, usage_count, error_count)
        
        return TokenInfo(
            token=current_token,
            token_type=token_type,
            quota_status=quota_status,
            expires_at=expires_at,
            last_used=last_used,
            usage_count=usage_count,
            error_count=error_count
        )
    
    def _estimate_quota_status(self, token_type: TokenType, usage_count: int, error_count: int) -> QuotaStatus:
        """估算配额状态"""
        # 基于错误率估算
        if usage_count > 0:
            error_rate = error_count / usage_count
            if error_rate > 0.5:
                return QuotaStatus.EXHAUSTED
            elif error_rate > 0.2:
                return QuotaStatus.LOW
        
        # 基于使用次数估算（匿名token通常有较低配额）
        if token_type == TokenType.ANONYMOUS:
            if usage_count > 40:
                return QuotaStatus.EXHAUSTED
            elif usage_count > 25:
                return QuotaStatus.LOW
        else:  # 个人token
            if usage_count > 200:
                return QuotaStatus.LOW
        
        return QuotaStatus.AVAILABLE
    
    def should_request_new_anonymous_token(self, error_context: str = "") -> Tuple[bool, str]:
        """判断是否应该申请新的匿名token"""
        current_time = time.time()
        self._cleanup_old_records(current_time)
        
        # 分析当前token
        current_token_info = self._analyze_current_token()
        
        # 检查申请频率
        recent_requests = len(self.state["anonymous_requests_this_hour"])
        if recent_requests >= self.max_anonymous_tokens_per_hour:
            return False, f"小时申请限制 ({recent_requests}/{self.max_anonymous_tokens_per_hour})"
        
        # 如果没有token，应该申请
        if not current_token_info:
            return True, "无可用token"
        
        # 如果token已过期，应该申请
        if is_token_expired(current_token_info.token):
            return True, "当前token已过期"
        
        # 如果使用个人token且工作正常，不申请匿名token
        if current_token_info.token_type == TokenType.PERSONAL:
            if current_token_info.quota_status in [QuotaStatus.AVAILABLE, QuotaStatus.LOW]:
                return False, "个人token仍可用"
        
        # 如果当前是匿名token但还有配额，不申请新的
        if current_token_info.token_type == TokenType.ANONYMOUS:
            if current_token_info.quota_status == QuotaStatus.AVAILABLE:
                return False, "当前匿名token仍有配额"
            
            # 检查token生命周期
            token_age = current_time - (current_token_info.expires_at - 3600)
            if token_age < self.min_token_lifetime:
                return False, f"当前匿名token太新 ({int(token_age/60)} 分钟)"
        
        # 检查错误上下文
        if error_context:
            if "429" in error_context:
                return False, "遇到429限频，不应立即申请"
            elif "quota" not in error_context.lower() and "配额" not in error_context:
                return False, "非配额相关错误，不需要申请新token"
        
        # 检查最近是否有成功的申请
        last_request_time = max(self.state["anonymous_requests_this_hour"]) if self.state["anonymous_requests_this_hour"] else 0
        if current_time - last_request_time < 300:  # 5分钟内有申请
            return False, "最近已有申请，等待生效"
        
        return True, "配额可能用尽，建议申请新token"
    
    def record_token_usage(self, success: bool, error_type: str = ""):
        """记录token使用"""
        current_time = time.time()
        current_token = get_jwt_token()
        
        if current_token:
            # 更新当前token信息
            current_info = self.state.get("current_token_info", {})
            if not current_info or current_info.get("token_preview") != current_token[:50]:
                # 新token
                current_info = {
                    "token_preview": current_token[:50],
                    "token_type": "personal" if is_using_personal_token() else "anonymous",
                    "created_at": current_time,
                    "usage_count": 0,
                    "error_count": 0,
                    "last_used": current_time
                }
            
            # 更新使用统计
            current_info["usage_count"] += 1
            current_info["last_used"] = current_time
            
            if not success:
                current_info["error_count"] += 1
                current_info["last_error"] = error_type
                current_info["last_error_time"] = current_time
            
            self.state["current_token_info"] = current_info
            
            # 更新性能指标
            if success:
                self.state["performance_metrics"]["successful_requests"] += 1
            else:
                self.state["performance_metrics"]["failed_requests"] += 1
        
        self._save_state()
    
    def record_anonymous_token_request(self):
        """记录匿名token申请"""
        current_time = time.time()
        self.state["anonymous_requests_this_hour"].append(current_time)
        self._save_state()
        logger.info(f"[SmartTokenManager] 记录匿名token申请，本小时已申请 {len(self.state['anonymous_requests_this_hour'])} 次")
    
    def get_recommendation(self) -> Dict[str, Any]:
        """获取token使用建议"""
        current_token_info = self._analyze_current_token()
        
        if not current_token_info:
            return {
                "action": "request_anonymous",
                "reason": "无可用token",
                "priority": "high"
            }
        
        if current_token_info.token_type == TokenType.PERSONAL:
            if current_token_info.quota_status == QuotaStatus.EXHAUSTED:
                return {
                    "action": "request_anonymous", 
                    "reason": "个人token配额用尽",
                    "priority": "medium"
                }
            else:
                return {
                    "action": "keep_current",
                    "reason": "个人token工作正常",
                    "priority": "low"
                }
        
        else:  # 匿名token
            if current_token_info.quota_status == QuotaStatus.EXHAUSTED:
                recent_requests = len(self.state["anonymous_requests_this_hour"])
                if recent_requests < self.max_anonymous_tokens_per_hour:
                    return {
                        "action": "request_anonymous",
                        "reason": "匿名token配额用尽",
                        "priority": "medium"
                    }
                else:
                    return {
                        "action": "wait",
                        "reason": "申请频率限制",
                        "priority": "low"
                    }
            else:
                return {
                    "action": "keep_current",
                    "reason": "匿名token仍可用", 
                    "priority": "low"
                }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        current_time = time.time()
        self._cleanup_old_records(current_time)
        
        current_token_info = self._analyze_current_token()
        
        return {
            "current_token": {
                "exists": current_token_info is not None,
                "type": current_token_info.token_type.value if current_token_info else "none",
                "quota_status": current_token_info.quota_status.value if current_token_info else "unknown",
                "usage_count": current_token_info.usage_count if current_token_info else 0,
                "error_count": current_token_info.error_count if current_token_info else 0,
                "expires_in": int(current_token_info.expires_at - current_time) if current_token_info else 0
            },
            "anonymous_requests": {
                "this_hour": len(self.state["anonymous_requests_this_hour"]),
                "max_per_hour": self.max_anonymous_tokens_per_hour,
                "remaining": self.max_anonymous_tokens_per_hour - len(self.state["anonymous_requests_this_hour"])
            },
            "performance": self.state["performance_metrics"],
            "recommendation": self.get_recommendation()
        }


# 全局实例
_global_smart_manager: Optional[SmartTokenManager] = None


def get_smart_token_manager() -> SmartTokenManager:
    """获取全局智能token管理器"""
    global _global_smart_manager
    if _global_smart_manager is None:
        _global_smart_manager = SmartTokenManager()
        logger.info("[SmartTokenManager] 智能token管理器已初始化")
    return _global_smart_manager


async def smart_acquire_anonymous_token(error_context: str = "") -> Optional[str]:
    """智能申请匿名token"""
    manager = get_smart_token_manager()
    
    # 检查是否应该申请
    should_request, reason = manager.should_request_new_anonymous_token(error_context)
    
    if not should_request:
        logger.info(f"[SmartTokenManager] 跳过匿名token申请: {reason}")
        return None
    
    logger.info(f"[SmartTokenManager] 开始申请匿名token: {reason}")
    
    try:
        # 记录申请
        manager.record_anonymous_token_request()
        
        # 执行申请
        from .auth import acquire_anonymous_access_token
        new_token = await acquire_anonymous_access_token()
        
        if new_token:
            logger.info("[SmartTokenManager] 匿名token申请成功")
            return new_token
        else:
            logger.warning("[SmartTokenManager] 匿名token申请失败：返回空token")
            return None
            
    except Exception as e:
        logger.error(f"[SmartTokenManager] 匿名token申请异常: {e}")
        return None


def record_api_usage(success: bool, error_type: str = ""):
    """记录API使用情况"""
    manager = get_smart_token_manager()
    manager.record_token_usage(success, error_type)


def get_smart_token_stats() -> Dict[str, Any]:
    """获取智能token管理统计"""
    manager = get_smart_token_manager()
    return manager.get_stats()


def should_use_current_token() -> bool:
    """判断是否应该使用当前token"""
    manager = get_smart_token_manager()
    recommendation = manager.get_recommendation()
    return recommendation["action"] in ["keep_current", "wait"]