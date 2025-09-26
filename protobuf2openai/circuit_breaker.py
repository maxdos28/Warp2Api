from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional, Callable, Awaitable, Union
from dataclasses import dataclass
from enum import Enum
from collections import deque
import random

from .logging import logger


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"        # 关闭状态，正常工作
    OPEN = "open"           # 开启状态，熔断中
    HALF_OPEN = "half_open" # 半开状态，尝试恢复


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5          # 失败阈值
    success_threshold: int = 3          # 恢复成功阈值
    timeout: float = 60.0              # 熔断超时时间（秒）
    reset_timeout: float = 30.0        # 重置超时时间（秒）
    max_failures: int = 10             # 最大失败次数
    window_size: int = 100             # 滑动窗口大小
    min_throughput: int = 10           # 最小吞吐量
    error_rate_threshold: float = 0.5  # 错误率阈值


class CircuitBreakerException(Exception):
    """熔断器异常"""
    
    def __init__(self, message: str, circuit_name: str, state: CircuitState):
        super().__init__(message)
        self.circuit_name = circuit_name
        self.state = state


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # 状态管理
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_success_time = 0
        self.next_attempt_time = 0
        
        # 统计数据
        self.call_history: deque = deque(maxlen=self.config.window_size)
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_timeouts = 0
        self.total_circuit_opens = 0
        
        # 性能数据
        self.response_times: deque = deque(maxlen=100)
        self.last_state_change = time.time()
        
        logger.info(f"[CircuitBreaker] Created circuit breaker '{name}'")
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """执行函数调用，带熔断保护"""
        current_time = time.time()
        
        # 检查熔断器状态
        if not self._can_execute(current_time):
            self._record_call(False, current_time, 0, "circuit_open")
            raise CircuitBreakerException(
                f"Circuit breaker '{self.name}' is open",
                self.name,
                self.state
            )
        
        start_time = time.time()
        try:
            # 执行函数
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            # 记录成功
            execution_time = time.time() - start_time
            self._record_success(current_time, execution_time)
            return result
            
        except asyncio.TimeoutError:
            # 超时处理
            execution_time = time.time() - start_time
            self._record_failure(current_time, execution_time, "timeout")
            self.total_timeouts += 1
            raise
            
        except Exception as e:
            # 其他异常处理
            execution_time = time.time() - start_time
            self._record_failure(current_time, execution_time, type(e).__name__)
            raise
    
    def _can_execute(self, current_time: float) -> bool:
        """检查是否可以执行"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if current_time >= self.next_attempt_time:
                self._transition_to_half_open(current_time)
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def _record_success(self, current_time: float, execution_time: float):
        """记录成功调用"""
        self.total_calls += 1
        self.total_successes += 1
        self.success_count += 1
        self.last_success_time = current_time
        self.response_times.append(execution_time)
        
        self._record_call(True, current_time, execution_time, "success")
        
        # 状态转换逻辑
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed(current_time)
        elif self.state == CircuitState.CLOSED:
            # 重置失败计数
            self.failure_count = max(0, self.failure_count - 1)
    
    def _record_failure(self, current_time: float, execution_time: float, error_type: str):
        """记录失败调用"""
        self.total_calls += 1
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = current_time
        
        self._record_call(False, current_time, execution_time, error_type)
        
        # 检查是否需要开启熔断器
        if self.state == CircuitState.CLOSED:
            if self._should_open_circuit():
                self._transition_to_open(current_time)
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to_open(current_time)
    
    def _record_call(self, success: bool, timestamp: float, execution_time: float, result_type: str):
        """记录调用历史"""
        self.call_history.append({
            "success": success,
            "timestamp": timestamp,
            "execution_time": execution_time,
            "result_type": result_type
        })
    
    def _should_open_circuit(self) -> bool:
        """判断是否应该开启熔断器"""
        # 基于失败次数
        if self.failure_count >= self.config.failure_threshold:
            return True
        
        # 基于错误率和吞吐量
        if len(self.call_history) >= self.config.min_throughput:
            recent_calls = list(self.call_history)[-self.config.window_size:]
            failure_rate = sum(1 for call in recent_calls if not call["success"]) / len(recent_calls)
            
            if failure_rate >= self.config.error_rate_threshold:
                return True
        
        return False
    
    def _transition_to_open(self, current_time: float):
        """转换到开启状态"""
        if self.state != CircuitState.OPEN:
            logger.warning(f"[CircuitBreaker] '{self.name}' opened due to failures")
            self.state = CircuitState.OPEN
            self.next_attempt_time = current_time + self.config.reset_timeout
            self.total_circuit_opens += 1
            self.last_state_change = current_time
    
    def _transition_to_half_open(self, current_time: float):
        """转换到半开状态"""
        logger.info(f"[CircuitBreaker] '{self.name}' transitioning to half-open")
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.failure_count = 0
        self.last_state_change = current_time
    
    def _transition_to_closed(self, current_time: float):
        """转换到关闭状态"""
        logger.info(f"[CircuitBreaker] '{self.name}' closed - service recovered")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = current_time
    
    def force_open(self):
        """强制开启熔断器"""
        logger.warning(f"[CircuitBreaker] '{self.name}' force opened")
        self.state = CircuitState.OPEN
        self.next_attempt_time = time.time() + self.config.reset_timeout
        self.total_circuit_opens += 1
        self.last_state_change = time.time()
    
    def force_close(self):
        """强制关闭熔断器"""
        logger.info(f"[CircuitBreaker] '{self.name}' force closed")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
    
    def reset(self):
        """重置熔断器"""
        logger.info(f"[CircuitBreaker] '{self.name}' reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.call_history.clear()
        self.response_times.clear()
        self.last_state_change = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        current_time = time.time()
        
        # 计算错误率
        error_rate = 0.0
        if self.total_calls > 0:
            error_rate = self.total_failures / self.total_calls
        
        # 计算平均响应时间
        avg_response_time = 0.0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
        
        # 计算最近窗口的统计
        recent_stats = self._get_recent_window_stats()
        
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.total_calls,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "total_timeouts": self.total_timeouts,
            "total_circuit_opens": self.total_circuit_opens,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "current_failure_count": self.failure_count,
            "current_success_count": self.success_count,
            "time_since_last_state_change": current_time - self.last_state_change,
            "next_attempt_in": max(0, self.next_attempt_time - current_time) if self.state == CircuitState.OPEN else 0,
            "recent_window": recent_stats,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
                "reset_timeout": self.config.reset_timeout,
                "error_rate_threshold": self.config.error_rate_threshold
            }
        }
    
    def _get_recent_window_stats(self) -> Dict[str, Any]:
        """获取最近窗口的统计"""
        if not self.call_history:
            return {"calls": 0, "successes": 0, "failures": 0, "error_rate": 0.0}
        
        recent_calls = list(self.call_history)[-50:]  # 最近50次调用
        successes = sum(1 for call in recent_calls if call["success"])
        failures = len(recent_calls) - successes
        error_rate = failures / len(recent_calls) if recent_calls else 0
        
        return {
            "calls": len(recent_calls),
            "successes": successes,
            "failures": failures,
            "error_rate": error_rate
        }


class CircuitBreakerManager:
    """熔断器管理器"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.default_config = CircuitBreakerConfig()
    
    def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """获取或创建熔断器"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config or self.default_config)
        return self.circuit_breakers[name]
    
    def remove_circuit_breaker(self, name: str) -> bool:
        """移除熔断器"""
        if name in self.circuit_breakers:
            del self.circuit_breakers[name]
            logger.info(f"[CircuitBreaker] Removed circuit breaker '{name}'")
            return True
        return False
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有熔断器的统计信息"""
        return {name: cb.get_stats() for name, cb in self.circuit_breakers.items()}
    
    def reset_all(self):
        """重置所有熔断器"""
        for cb in self.circuit_breakers.values():
            cb.reset()
        logger.info("[CircuitBreaker] Reset all circuit breakers")
    
    def force_open_all(self):
        """强制开启所有熔断器"""
        for cb in self.circuit_breakers.values():
            cb.force_open()
        logger.warning("[CircuitBreaker] Force opened all circuit breakers")
    
    def force_close_all(self):
        """强制关闭所有熔断器"""
        for cb in self.circuit_breakers.values():
            cb.force_close()
        logger.info("[CircuitBreaker] Force closed all circuit breakers")


# 装饰器
def circuit_breaker(name: str, 
                   config: CircuitBreakerConfig = None,
                   fallback: Optional[Callable] = None):
    """熔断器装饰器"""
    def decorator(func: Callable[..., Awaitable[Any]]):
        cb = _global_manager.get_circuit_breaker(name, config)
        
        async def wrapper(*args, **kwargs):
            try:
                return await cb.call(func, *args, **kwargs)
            except CircuitBreakerException:
                if fallback:
                    logger.info(f"[CircuitBreaker] Using fallback for '{name}'")
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    else:
                        return fallback(*args, **kwargs)
                raise
        
        # 添加熔断器控制方法
        wrapper.circuit_breaker = cb
        wrapper.get_stats = cb.get_stats
        wrapper.reset = cb.reset
        wrapper.force_open = cb.force_open
        wrapper.force_close = cb.force_close
        
        return wrapper
    
    return decorator


# 全局管理器
_global_manager = CircuitBreakerManager()


def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """获取熔断器"""
    return _global_manager.get_circuit_breaker(name, config)


def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """获取所有熔断器统计"""
    return _global_manager.get_all_stats()


def reset_all_circuit_breakers():
    """重置所有熔断器"""
    _global_manager.reset_all()


# 预定义配置
class CircuitBreakerPresets:
    """预定义熔断器配置"""
    
    @staticmethod
    def fast_fail() -> CircuitBreakerConfig:
        """快速失败配置"""
        return CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=10.0,
            reset_timeout=15.0,
            error_rate_threshold=0.3
        )
    
    @staticmethod
    def conservative() -> CircuitBreakerConfig:
        """保守配置"""
        return CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=3,
            timeout=30.0,
            reset_timeout=30.0,
            error_rate_threshold=0.5
        )
    
    @staticmethod
    def resilient() -> CircuitBreakerConfig:
        """弹性配置"""
        return CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=5,
            timeout=60.0,
            reset_timeout=60.0,
            error_rate_threshold=0.7
        )
    
    @staticmethod
    def api_gateway() -> CircuitBreakerConfig:
        """API网关配置"""
        return CircuitBreakerConfig(
            failure_threshold=8,
            success_threshold=4,
            timeout=45.0,
            reset_timeout=45.0,
            error_rate_threshold=0.6,
            window_size=200,
            min_throughput=20
        )


# 熔断器健康检查
class CircuitBreakerHealthChecker:
    """熔断器健康检查器"""
    
    def __init__(self, manager: CircuitBreakerManager):
        self.manager = manager
        self.health_check_interval = 60  # 1分钟检查一次
        self.running = False
        self.task = None
    
    async def start(self):
        """启动健康检查"""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._health_check_loop())
        logger.info("[CircuitBreaker] Health checker started")
    
    async def stop(self):
        """停止健康检查"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("[CircuitBreaker] Health checker stopped")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[CircuitBreaker] Health check error: {e}")
                await asyncio.sleep(10)  # 错误时短暂等待
    
    async def _perform_health_check(self):
        """执行健康检查"""
        current_time = time.time()
        
        for name, cb in self.manager.circuit_breakers.items():
            stats = cb.get_stats()
            
            # 检查长时间开启的熔断器
            if cb.state == CircuitState.OPEN:
                time_open = stats["time_since_last_state_change"]
                if time_open > cb.config.reset_timeout * 3:  # 超过3倍重置时间
                    logger.warning(f"[CircuitBreaker] '{name}' has been open for {time_open:.1f}s")
            
            # 检查高错误率
            if stats["error_rate"] > 0.8 and stats["total_calls"] > 50:
                logger.warning(f"[CircuitBreaker] '{name}' has high error rate: {stats['error_rate']:.2%}")
            
            # 检查性能问题
            if stats["avg_response_time"] > cb.config.timeout * 0.8:
                logger.warning(f"[CircuitBreaker] '{name}' has slow response time: {stats['avg_response_time']:.2f}s")


# 启动健康检查器
async def start_circuit_breaker_health_check():
    """启动熔断器健康检查"""
    health_checker = CircuitBreakerHealthChecker(_global_manager)
    await health_checker.start()
    return health_checker