from __future__ import annotations

import asyncio
import time
import psutil
import gc
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta

from .logging import logger


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        
        self.start_time = time.time()
        self.last_gc_time = time.time()
        
        # 系统指标
        self.process = psutil.Process()
        
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录指标"""
        metric = PerformanceMetric(name, value, time.time(), tags or {})
        self.metrics[name].append(metric)
        
        # 更新统计
        if name.endswith("_count"):
            self.counters[name] += int(value)
        elif name.endswith("_gauge"):
            self.gauges[name] = value
        elif name.endswith("_time") or name.endswith("_duration"):
            self.histograms[name].append(value)
            # 保持直方图大小
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """递增计数器"""
        self.counters[name] += value
        self.record_metric(f"{name}_count", value, tags)
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """设置仪表值"""
        self.gauges[name] = value
        self.record_metric(f"{name}_gauge", value, tags)
    
    def record_timing(self, name: str, duration: float, tags: Dict[str, str] = None):
        """记录时间指标"""
        self.histograms[name].append(duration)
        self.record_metric(f"{name}_time", duration, tags)
        
        # 保持直方图大小
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-1000:]
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # 获取连接数
            try:
                connections = len(self.process.connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = 0
            
            return {
                "cpu_percent": cpu_percent,
                "memory_rss": memory_info.rss,
                "memory_vms": memory_info.vms,
                "memory_percent": memory_percent,
                "connections": connections,
                "threads": self.process.num_threads(),
                "uptime": time.time() - self.start_time,
            }
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            return {}
    
    def get_gc_metrics(self) -> Dict[str, Any]:
        """获取垃圾回收指标"""
        try:
            gc_stats = gc.get_stats()
            gc_counts = gc.get_count()
            
            return {
                "gc_generation_0": gc_counts[0] if len(gc_counts) > 0 else 0,
                "gc_generation_1": gc_counts[1] if len(gc_counts) > 1 else 0,
                "gc_generation_2": gc_counts[2] if len(gc_counts) > 2 else 0,
                "gc_collections": sum(stat.get("collections", 0) for stat in gc_stats),
                "gc_collected": sum(stat.get("collected", 0) for stat in gc_stats),
                "gc_uncollectable": sum(stat.get("uncollectable", 0) for stat in gc_stats),
            }
        except Exception as e:
            logger.warning(f"Failed to get GC metrics: {e}")
            return {}
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """获取直方图统计"""
        values = self.histograms.get(name, [])
        if not values:
            return {}
        
        sorted_values = sorted(values)
        length = len(sorted_values)
        
        return {
            "count": length,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "mean": sum(sorted_values) / length,
            "p50": sorted_values[length // 2],
            "p90": sorted_values[int(length * 0.9)],
            "p95": sorted_values[int(length * 0.95)],
            "p99": sorted_values[int(length * 0.99)],
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        system_metrics = self.get_system_metrics()
        gc_metrics = self.get_gc_metrics()
        
        # 计算关键指标统计
        request_times = self.histograms.get("request_duration", [])
        cache_hit_rate = 0.0
        if self.counters.get("cache_hits", 0) + self.counters.get("cache_misses", 0) > 0:
            cache_hit_rate = self.counters["cache_hits"] / (self.counters["cache_hits"] + self.counters["cache_misses"])
        
        summary = {
            "system": system_metrics,
            "garbage_collection": gc_metrics,
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "cache_hit_rate": cache_hit_rate,
            "total_requests": self.counters.get("requests_total", 0),
            "error_rate": self.counters.get("errors_total", 0) / max(1, self.counters.get("requests_total", 1)),
        }
        
        # 添加响应时间统计
        if request_times:
            summary["response_time"] = self.get_histogram_stats("request_duration")
        
        return summary
    
    def log_summary(self):
        """记录性能摘要到日志"""
        summary = self.get_summary()
        
        logger.info("=== Performance Summary ===")
        
        # 系统指标
        if "system" in summary:
            sys_metrics = summary["system"]
            logger.info(f"CPU: {sys_metrics.get('cpu_percent', 0):.1f}%")
            logger.info(f"Memory: {sys_metrics.get('memory_percent', 0):.1f}% ({sys_metrics.get('memory_rss', 0) / 1024 / 1024:.1f} MB)")
            logger.info(f"Connections: {sys_metrics.get('connections', 0)}")
            logger.info(f"Uptime: {sys_metrics.get('uptime', 0):.1f}s")
        
        # 请求指标
        logger.info(f"Total Requests: {summary.get('total_requests', 0)}")
        logger.info(f"Error Rate: {summary.get('error_rate', 0):.2%}")
        logger.info(f"Cache Hit Rate: {summary.get('cache_hit_rate', 0):.2%}")
        
        # 响应时间
        if "response_time" in summary:
            rt = summary["response_time"]
            logger.info(f"Response Time - Mean: {rt.get('mean', 0):.3f}s, P95: {rt.get('p95', 0):.3f}s, P99: {rt.get('p99', 0):.3f}s")
        
        logger.info("========================")
    
    def force_gc(self):
        """强制垃圾回收"""
        current_time = time.time()
        if current_time - self.last_gc_time > 30:  # 至少30秒间隔
            collected = gc.collect()
            self.last_gc_time = current_time
            logger.debug(f"[Performance] Forced GC collected {collected} objects")
            return collected
        return 0


# 全局监控器实例
_global_monitor: Optional[PerformanceMonitor] = None
_monitor_lock = asyncio.Lock()


async def get_global_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _global_monitor
    if _global_monitor is not None:
        return _global_monitor
    
    async with _monitor_lock:
        if _global_monitor is None:
            _global_monitor = PerformanceMonitor()
            logger.info("[Performance] Global performance monitor initialized")
        return _global_monitor


async def record_metric(name: str, value: float, tags: Dict[str, str] = None):
    """记录指标"""
    monitor = await get_global_monitor()
    monitor.record_metric(name, value, tags)


async def increment_counter(name: str, value: int = 1, tags: Dict[str, str] = None):
    """递增计数器"""
    monitor = await get_global_monitor()
    monitor.increment_counter(name, value, tags)


async def set_gauge(name: str, value: float, tags: Dict[str, str] = None):
    """设置仪表值"""
    monitor = await get_global_monitor()
    monitor.set_gauge(name, value, tags)


async def record_timing(name: str, duration: float, tags: Dict[str, str] = None):
    """记录时间指标"""
    monitor = await get_global_monitor()
    monitor.record_timing(name, duration, tags)


async def get_performance_summary() -> Dict[str, Any]:
    """获取性能摘要"""
    monitor = await get_global_monitor()
    return monitor.get_summary()


class TimingContext:
    """时间测量上下文管理器"""
    
    def __init__(self, metric_name: str, tags: Dict[str, str] = None):
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            await record_timing(self.metric_name, duration, self.tags)
            
            if exc_type is not None:
                await increment_counter("errors_total", tags={**self.tags, "error_type": exc_type.__name__})
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            # 对于同步上下文，我们直接使用监控器
            asyncio.create_task(record_timing(self.metric_name, duration, self.tags))
            
            if exc_type is not None:
                asyncio.create_task(increment_counter("errors_total", tags={**self.tags, "error_type": exc_type.__name__}))


# 定期监控任务
async def start_performance_monitoring_task(interval: int = 60):
    """启动性能监控任务"""
    async def monitoring_task():
        while True:
            try:
                monitor = await get_global_monitor()
                
                # 记录系统指标
                system_metrics = monitor.get_system_metrics()
                for name, value in system_metrics.items():
                    await set_gauge(f"system_{name}", value)
                
                # 记录GC指标
                gc_metrics = monitor.get_gc_metrics()
                for name, value in gc_metrics.items():
                    await set_gauge(name, value)
                
                # 定期强制GC
                if interval >= 300:  # 5分钟以上的间隔才强制GC
                    monitor.force_gc()
                
                # 记录摘要日志
                if interval >= 300:  # 5分钟以上才记录摘要
                    monitor.log_summary()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"[Performance] Monitoring task error: {e}")
                await asyncio.sleep(60)  # 错误时等待1分钟后重试
    
    asyncio.create_task(monitoring_task())
    logger.info(f"[Performance] Performance monitoring task started (interval: {interval}s)")