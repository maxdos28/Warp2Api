"""
Quota and Rate Limiting Handler for Warp2Api
处理API配额限制和高负载情况的专用模块
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from fastapi import HTTPException
from .logging import logger


class QuotaHandler:
    """配额和负载处理器"""
    
    def __init__(self):
        self.last_quota_check = 0
        self.quota_status = "normal"
        self.error_count = 0
        self.request_count = 0
        self.high_demand_responses = 0
        self.last_request_time = 0
        
        # 配置参数
        self.quota_check_interval = 60  # 1分钟检查一次
        self.max_errors_per_minute = 10  # 每分钟最大错误数
        self.high_demand_threshold = 5   # 连续5次high demand后暂停
        self.rate_limit_window = 60      # 速率限制窗口(秒)
        
    def check_quota_status(self) -> Tuple[bool, str]:
        """检查配额状态"""
        current_time = time.time()
        
        # 重置计数器（每分钟）
        if current_time - self.last_quota_check > self.quota_check_interval:
            self.error_count = 0
            self.request_count = 0
            self.high_demand_responses = 0
            self.last_quota_check = current_time
            self.quota_status = "normal"
            
        # 检查是否需要限制
        if self.error_count > self.max_errors_per_minute:
            self.quota_status = "rate_limited"
            return False, f"Too many errors ({self.error_count}) in the last minute"
            
        if self.high_demand_responses > self.high_demand_threshold:
            self.quota_status = "high_demand"
            return False, f"Too many high demand responses ({self.high_demand_responses})"
            
        return True, "OK"
    
    def record_request(self):
        """记录请求"""
        self.request_count += 1
        self.last_request_time = time.time()
        
    def record_error(self, error_type: str = "unknown"):
        """记录错误"""
        self.error_count += 1
        if "high demand" in error_type.lower():
            self.high_demand_responses += 1
        
        logger.warning(f"[QuotaHandler] Recorded error: {error_type} (total: {self.error_count})")
        
    def record_success(self):
        """记录成功请求"""
        # 成功请求可以降低错误计数
        if self.error_count > 0:
            self.error_count = max(0, self.error_count - 1)
            
    def should_throttle_request(self) -> Tuple[bool, str]:
        """检查是否应该限制请求"""
        can_proceed, reason = self.check_quota_status()
        
        if not can_proceed:
            return True, reason
            
        # 注意：移除了过于严格的频率限制，允许正常的API使用
        # 只有在明确检测到配额问题时才限制请求
        return False, "OK"
    
    def get_retry_after_seconds(self) -> int:
        """获取重试等待时间"""
        if self.quota_status == "high_demand":
            return 60  # 高负载时等待1分钟
        elif self.quota_status == "rate_limited":
            return 30  # 频率限制时等待30秒
        else:
            return 10  # 默认等待10秒
    
    def get_status_info(self) -> Dict:
        """获取状态信息"""
        current_time = time.time()
        return {
            "quota_status": self.quota_status,
            "error_count": self.error_count,
            "request_count": self.request_count,
            "high_demand_responses": self.high_demand_responses,
            "time_since_last_check": int(current_time - self.last_quota_check),
            "time_since_last_request": int(current_time - self.last_request_time),
        }
    
    def handle_high_demand_response(self, message: str = None) -> Dict:
        """处理高负载响应"""
        self.record_error("high_demand")
        
        retry_after = self.get_retry_after_seconds()
        
        error_response = {
            "error": {
                "message": message or "I'm currently experiencing high demand. Please try again in a moment.",
                "type": "server_error",
                "code": "high_demand",
                "param": None,
                "details": {
                    "retry_after": retry_after,
                    "quota_status": self.quota_status,
                    "error_count": self.error_count
                }
            }
        }
        
        logger.warning(f"[QuotaHandler] Returning high demand response: {error_response}")
        return error_response
    
    def handle_rate_limit_response(self, reason: str = None) -> Dict:
        """处理速率限制响应"""
        self.record_error("rate_limit")
        
        retry_after = self.get_retry_after_seconds()
        
        error_response = {
            "error": {
                "message": f"Rate limit exceeded. {reason or 'Please try again later.'}",
                "type": "rate_limit_exceeded", 
                "code": "rate_limit",
                "param": None,
                "details": {
                    "retry_after": retry_after,
                    "quota_status": self.quota_status
                }
            }
        }
        
        logger.warning(f"[QuotaHandler] Returning rate limit response: {error_response}")
        return error_response


# 全局配额处理器实例
quota_handler = QuotaHandler()


def get_quota_handler() -> QuotaHandler:
    """获取全局配额处理器"""
    return quota_handler


async def check_request_throttling() -> Optional[Dict]:
    """检查请求是否应该被限制"""
    handler = get_quota_handler()
    
    should_throttle, reason = handler.should_throttle_request()
    
    if should_throttle:
        if "high demand" in reason.lower():
            return handler.handle_high_demand_response()
        else:
            return handler.handle_rate_limit_response(reason)
    
    # 记录正常请求
    handler.record_request()
    return None


def is_high_demand_message(content: str) -> bool:
    """检查是否是高负载消息"""
    if not isinstance(content, str):
        return False
        
    high_demand_indicators = [
        "I'm currently experiencing high demand",
        "experiencing high demand", 
        "high demand",
        "Please try again in a moment",
        "try again in a moment",
        "server is currently overloaded"
    ]
    
    content_lower = content.lower()
    return any(indicator in content_lower for indicator in high_demand_indicators)


def extract_high_demand_message(messages: list) -> Optional[str]:
    """从消息中提取高负载消息 - 只检查assistant角色的消息"""
    for msg in messages:
        # 只检查assistant的消息，不检查user消息
        if hasattr(msg, 'role') and msg.role == "assistant":
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                if is_high_demand_message(msg.content):
                    return msg.content
    return None


async def handle_quota_aware_request(request_data: Dict) -> Optional[Dict]:
    """处理考虑配额的请求"""
    handler = get_quota_handler()
    
    # 首先检查是否应该限制请求
    throttle_response = await check_request_throttling()
    if throttle_response:
        return throttle_response
    
    # 检查请求中是否包含高负载消息
    if 'messages' in request_data:
        high_demand_msg = extract_high_demand_message(request_data['messages'])
        if high_demand_msg:
            return handler.handle_high_demand_response(high_demand_msg)
    
    return None