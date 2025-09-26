#!/usr/bin/env python3
"""
配额预测器
"""

import time
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from collections import deque
from dataclasses import dataclass
from enum import Enum

from .logging import logger


class QuotaLevel(Enum):
    """配额级别"""
    HIGH = "high"        # 80%+ 可用
    MEDIUM = "medium"    # 50-80% 可用
    LOW = "low"         # 20-50% 可用
    CRITICAL = "critical" # <20% 可用
    EXHAUSTED = "exhausted" # 0% 可用


@dataclass
class QuotaDataPoint:
    """配额数据点"""
    timestamp: float
    request_count: int
    success_count: int
    error_count: int
    response_time: float
    error_type: str = ""


class QuotaPredictor:
    """配额预测器"""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.data_points: deque[QuotaDataPoint] = deque(maxlen=history_size)
        self.state_file = Path(".quota_predictor_state.json")
        self.state = self._load_state()
        
        # 预测参数
        self.quota_patterns = {
            "high_error_rate_threshold": 0.3,      # 30%错误率表示配额紧张
            "critical_error_rate_threshold": 0.7,  # 70%错误率表示配额临界
            "slow_response_threshold": 5.0,        # 5秒响应时间表示服务压力
            "prediction_window": 300,              # 5分钟预测窗口
        }
    
    def _load_state(self) -> Dict[str, Any]:
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # 重构数据点
                    for point_data in data.get("data_points", []):
                        self.data_points.append(QuotaDataPoint(**point_data))
                    return data.get("state", {})
            except Exception as e:
                logger.warning(f"Failed to load quota predictor state: {e}")
        
        return {
            "last_quota_check": 0,
            "estimated_quota_level": "unknown",
            "prediction_accuracy": 0.0,
            "total_predictions": 0,
            "correct_predictions": 0
        }
    
    def _save_state(self):
        """保存状态"""
        try:
            data = {
                "state": self.state,
                "data_points": [
                    {
                        "timestamp": point.timestamp,
                        "request_count": point.request_count,
                        "success_count": point.success_count,
                        "error_count": point.error_count,
                        "response_time": point.response_time,
                        "error_type": point.error_type
                    }
                    for point in list(self.data_points)[-100:]  # 只保存最近100个数据点
                ]
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save quota predictor state: {e}")
    
    def record_api_call(self, success: bool, response_time: float, error_type: str = ""):
        """记录API调用"""
        current_time = time.time()
        
        # 获取最近的数据点或创建新的
        if self.data_points and current_time - self.data_points[-1].timestamp < 60:
            # 合并到最近的数据点（1分钟内）
            last_point = self.data_points[-1]
            last_point.request_count += 1
            if success:
                last_point.success_count += 1
            else:
                last_point.error_count += 1
                if error_type:
                    last_point.error_type = error_type
            
            # 更新平均响应时间
            total_requests = last_point.request_count
            last_point.response_time = (last_point.response_time * (total_requests - 1) + response_time) / total_requests
        else:
            # 创建新数据点
            self.data_points.append(QuotaDataPoint(
                timestamp=current_time,
                request_count=1,
                success_count=1 if success else 0,
                error_count=0 if success else 1,
                response_time=response_time,
                error_type=error_type if not success else ""
            ))
        
        self._save_state()
    
    def predict_quota_level(self, window_minutes: int = 5) -> Tuple[QuotaLevel, float, str]:
        """预测配额级别"""
        if not self.data_points:
            return QuotaLevel.HIGH, 0.0, "无历史数据"
        
        current_time = time.time()
        window_start = current_time - (window_minutes * 60)
        
        # 获取窗口内的数据点
        recent_points = [
            point for point in self.data_points
            if point.timestamp >= window_start
        ]
        
        if not recent_points:
            return QuotaLevel.HIGH, 0.0, "无最近数据"
        
        # 计算统计指标
        total_requests = sum(point.request_count for point in recent_points)
        total_successes = sum(point.success_count for point in recent_points)
        total_errors = sum(point.error_count for point in recent_points)
        
        if total_requests == 0:
            return QuotaLevel.HIGH, 0.0, "无请求数据"
        
        error_rate = total_errors / total_requests
        avg_response_time = sum(point.response_time * point.request_count for point in recent_points) / total_requests
        
        # 分析错误类型
        quota_errors = sum(
            point.error_count for point in recent_points
            if "quota" in point.error_type.lower() or "配额" in point.error_type
        )
        quota_error_rate = quota_errors / total_requests if total_requests > 0 else 0
        
        # 预测逻辑
        confidence = min(1.0, len(recent_points) / 10)  # 基于数据点数量的置信度
        
        if quota_error_rate > 0.5:
            return QuotaLevel.EXHAUSTED, confidence, f"配额错误率{quota_error_rate:.1%}"
        elif quota_error_rate > 0.2:
            return QuotaLevel.CRITICAL, confidence, f"配额错误率{quota_error_rate:.1%}"
        elif error_rate > self.quota_patterns["critical_error_rate_threshold"]:
            return QuotaLevel.LOW, confidence, f"总错误率{error_rate:.1%}"
        elif error_rate > self.quota_patterns["high_error_rate_threshold"]:
            return QuotaLevel.MEDIUM, confidence, f"错误率{error_rate:.1%}"
        elif avg_response_time > self.quota_patterns["slow_response_threshold"]:
            return QuotaLevel.MEDIUM, confidence, f"响应慢{avg_response_time:.1f}s"
        else:
            return QuotaLevel.HIGH, confidence, "状态良好"
    
    def should_request_new_token(self) -> Tuple[bool, str]:
        """判断是否应该申请新token"""
        quota_level, confidence, reason = self.predict_quota_level()
        
        # 只有在高置信度且配额确实用尽时才建议申请
        if confidence > 0.7 and quota_level in [QuotaLevel.EXHAUSTED, QuotaLevel.CRITICAL]:
            return True, f"预测配额{quota_level.value} (置信度{confidence:.1%}): {reason}"
        
        return False, f"预测配额{quota_level.value} (置信度{confidence:.1%}): {reason}"
    
    def get_prediction_stats(self) -> Dict[str, Any]:
        """获取预测统计"""
        if not self.data_points:
            return {"status": "no_data"}
        
        quota_level, confidence, reason = self.predict_quota_level()
        
        # 计算最近的性能指标
        recent_points = list(self.data_points)[-10:]  # 最近10个数据点
        if recent_points:
            total_requests = sum(point.request_count for point in recent_points)
            total_errors = sum(point.error_count for point in recent_points)
            error_rate = total_errors / max(total_requests, 1)
            avg_response_time = sum(point.response_time * point.request_count for point in recent_points) / max(total_requests, 1)
        else:
            error_rate = 0
            avg_response_time = 0
        
        return {
            "current_quota_level": quota_level.value,
            "confidence": confidence,
            "reason": reason,
            "should_request_new_token": self.should_request_new_token()[0],
            "recent_performance": {
                "error_rate": error_rate,
                "avg_response_time": avg_response_time,
                "data_points": len(recent_points)
            },
            "prediction_accuracy": self.state.get("prediction_accuracy", 0.0),
            "total_data_points": len(self.data_points)
        }


# 全局实例
_global_quota_predictor: Optional[QuotaPredictor] = None


def get_quota_predictor() -> QuotaPredictor:
    """获取全局配额预测器"""
    global _global_quota_predictor
    if _global_quota_predictor is None:
        _global_quota_predictor = QuotaPredictor()
        logger.info("[QuotaPredictor] 配额预测器已初始化")
    return _global_quota_predictor


def record_quota_usage(success: bool, response_time: float, error_type: str = ""):
    """记录配额使用"""
    predictor = get_quota_predictor()
    predictor.record_api_call(success, response_time, error_type)


def predict_quota_exhaustion() -> Tuple[bool, str]:
    """预测配额是否用尽"""
    predictor = get_quota_predictor()
    return predictor.should_request_new_token()


def get_quota_prediction_stats() -> Dict[str, Any]:
    """获取配额预测统计"""
    predictor = get_quota_predictor()
    return predictor.get_prediction_stats()