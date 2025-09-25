from __future__ import annotations

import asyncio
import logging
import time
import json
import sys
from typing import Any, Dict, Optional, List
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

from .logging import logger


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: float
    level: str
    message: str
    module: str
    extra: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra is None:
            self.extra = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "level": self.level,
            "message": self.message,
            "module": self.module,
            **self.extra
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class AsyncLogHandler(logging.Handler):
    """异步日志处理器"""
    
    def __init__(self, 
                 max_queue_size: int = 10000,
                 batch_size: int = 100,
                 flush_interval: float = 1.0,
                 log_file: Optional[str] = None):
        super().__init__()
        
        self.max_queue_size = max_queue_size
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.log_file = log_file
        
        self.log_queue: deque[LogEntry] = deque(maxlen=max_queue_size)
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="async-log-")
        self.flush_task = None
        self.shutdown_event = threading.Event()
        
        # 统计信息
        self.stats = {
            "total_logs": 0,
            "queued_logs": 0,
            "dropped_logs": 0,
            "flush_count": 0,
            "last_flush_time": 0,
        }
        
        # 启动异步处理
        self._start_async_processing()
    
    def emit(self, record: logging.LogRecord):
        """发送日志记录"""
        try:
            # 创建日志条目
            entry = LogEntry(
                timestamp=record.created,
                level=record.levelname,
                message=self.format(record),
                module=record.module if hasattr(record, 'module') else record.name,
                extra={
                    "filename": record.filename,
                    "lineno": record.lineno,
                    "funcName": record.funcName,
                    "thread": record.thread,
                    "threadName": record.threadName,
                }
            )
            
            # 添加到队列
            if len(self.log_queue) >= self.max_queue_size:
                # 队列满了，丢弃最老的日志
                self.log_queue.popleft()
                self.stats["dropped_logs"] += 1
            
            self.log_queue.append(entry)
            self.stats["total_logs"] += 1
            self.stats["queued_logs"] = len(self.log_queue)
            
        except Exception as e:
            # 避免日志处理本身出错影响主程序
            print(f"AsyncLogHandler error: {e}", file=sys.stderr)
    
    def _start_async_processing(self):
        """启动异步处理任务"""
        def run_async_loop():
            """运行异步事件循环"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self._async_flush_loop())
            except Exception as e:
                print(f"Async log processing error: {e}", file=sys.stderr)
            finally:
                loop.close()
        
        # 在独立线程中运行异步循环
        thread = threading.Thread(target=run_async_loop, daemon=True, name="async-log-processor")
        thread.start()
    
    async def _async_flush_loop(self):
        """异步刷新循环"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_logs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Async flush error: {e}", file=sys.stderr)
        
        # 最后一次刷新
        await self._flush_logs()
    
    async def _flush_logs(self):
        """刷新日志到文件"""
        if not self.log_queue:
            return
        
        # 收集一批日志
        batch = []
        while self.log_queue and len(batch) < self.batch_size:
            batch.append(self.log_queue.popleft())
        
        if not batch:
            return
        
        # 在线程池中执行IO操作
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._write_logs_sync, batch)
        
        # 更新统计
        self.stats["flush_count"] += 1
        self.stats["last_flush_time"] = time.time()
        self.stats["queued_logs"] = len(self.log_queue)
    
    def _write_logs_sync(self, batch: List[LogEntry]):
        """同步写入日志"""
        try:
            if self.log_file:
                # 写入文件
                log_path = Path(self.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(log_path, 'a', encoding='utf-8') as f:
                    for entry in batch:
                        f.write(entry.to_json() + '\n')
            else:
                # 写入标准输出
                for entry in batch:
                    print(entry.to_json(), flush=True)
                    
        except Exception as e:
            print(f"Failed to write logs: {e}", file=sys.stderr)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def close(self):
        """关闭处理器"""
        self.shutdown_event.set()
        
        # 等待队列清空
        max_wait = 5.0  # 最多等待5秒
        start_time = time.time()
        while self.log_queue and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        self.executor.shutdown(wait=True)
        super().close()


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str, async_handler: AsyncLogHandler = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.async_handler = async_handler
        
        if async_handler and async_handler not in self.logger.handlers:
            self.logger.addHandler(async_handler)
    
    def _log_with_context(self, level: str, message: str, **context):
        """带上下文的日志记录"""
        # 创建LogRecord
        record = logging.LogRecord(
            name=self.name,
            level=getattr(logging, level.upper()),
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        
        # 添加上下文信息
        for key, value in context.items():
            setattr(record, key, value)
        
        self.logger.handle(record)
    
    def info(self, message: str, **context):
        """记录信息日志"""
        self._log_with_context('INFO', message, **context)
    
    def warning(self, message: str, **context):
        """记录警告日志"""
        self._log_with_context('WARNING', message, **context)
    
    def error(self, message: str, **context):
        """记录错误日志"""
        self._log_with_context('ERROR', message, **context)
    
    def debug(self, message: str, **context):
        """记录调试日志"""
        self._log_with_context('DEBUG', message, **context)
    
    def critical(self, message: str, **context):
        """记录严重错误日志"""
        self._log_with_context('CRITICAL', message, **context)


class LogMetrics:
    """日志指标收集器"""
    
    def __init__(self):
        self.metrics = {
            "log_counts": {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0},
            "error_patterns": {},
            "performance_logs": deque(maxlen=1000),
            "request_logs": deque(maxlen=1000),
        }
    
    def record_log(self, level: str, message: str, extra: Dict[str, Any] = None):
        """记录日志指标"""
        self.metrics["log_counts"][level] = self.metrics["log_counts"].get(level, 0) + 1
        
        # 记录错误模式
        if level in ["ERROR", "CRITICAL"]:
            # 简化错误消息作为模式
            error_pattern = message.split(':')[0] if ':' in message else message[:50]
            self.metrics["error_patterns"][error_pattern] = self.metrics["error_patterns"].get(error_pattern, 0) + 1
        
        # 记录性能日志
        if extra and "duration" in extra:
            self.metrics["performance_logs"].append({
                "timestamp": time.time(),
                "duration": extra["duration"],
                "operation": extra.get("operation", "unknown")
            })
        
        # 记录请求日志
        if extra and "request_id" in extra:
            self.metrics["request_logs"].append({
                "timestamp": time.time(),
                "request_id": extra["request_id"],
                "status": extra.get("status", "unknown"),
                "duration": extra.get("duration", 0)
            })
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        # 计算性能统计
        perf_stats = {}
        if self.metrics["performance_logs"]:
            durations = [log["duration"] for log in self.metrics["performance_logs"]]
            perf_stats = {
                "avg_duration": sum(durations) / len(durations),
                "max_duration": max(durations),
                "min_duration": min(durations),
                "total_operations": len(durations)
            }
        
        # 计算请求统计
        request_stats = {}
        if self.metrics["request_logs"]:
            recent_requests = list(self.metrics["request_logs"])[-100:]  # 最近100个请求
            durations = [req["duration"] for req in recent_requests]
            if durations:
                request_stats = {
                    "avg_response_time": sum(durations) / len(durations),
                    "total_requests": len(self.metrics["request_logs"]),
                    "recent_requests": len(recent_requests)
                }
        
        return {
            "log_counts": self.metrics["log_counts"].copy(),
            "error_patterns": dict(list(self.metrics["error_patterns"].items())[:10]),  # 前10个错误模式
            "performance": perf_stats,
            "requests": request_stats,
        }
    
    def reset_metrics(self):
        """重置指标"""
        self.metrics = {
            "log_counts": {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0},
            "error_patterns": {},
            "performance_logs": deque(maxlen=1000),
            "request_logs": deque(maxlen=1000),
        }


# 全局实例
_async_log_handler: Optional[AsyncLogHandler] = None
_log_metrics = LogMetrics()
_structured_loggers: Dict[str, StructuredLogger] = {}


def setup_async_logging(log_file: Optional[str] = None,
                       max_queue_size: int = 10000,
                       batch_size: int = 100,
                       flush_interval: float = 1.0) -> AsyncLogHandler:
    """设置异步日志"""
    global _async_log_handler
    
    if _async_log_handler is None:
        _async_log_handler = AsyncLogHandler(
            max_queue_size=max_queue_size,
            batch_size=batch_size,
            flush_interval=flush_interval,
            log_file=log_file
        )
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        _async_log_handler.setFormatter(formatter)
        
        logger.info("[AsyncLogging] Async logging system initialized")
    
    return _async_log_handler


def get_structured_logger(name: str) -> StructuredLogger:
    """获取结构化日志记录器"""
    if name not in _structured_loggers:
        handler = _async_log_handler or setup_async_logging()
        _structured_loggers[name] = StructuredLogger(name, handler)
    
    return _structured_loggers[name]


def get_async_log_stats() -> Dict[str, Any]:
    """获取异步日志统计"""
    stats = {}
    
    if _async_log_handler:
        stats["handler"] = _async_log_handler.get_stats()
    
    stats["metrics"] = _log_metrics.get_metrics()
    
    return stats


def log_performance(operation: str, duration: float, **context):
    """记录性能日志"""
    structured_logger = get_structured_logger("performance")
    
    context.update({
        "operation": operation,
        "duration": duration
    })
    
    structured_logger.info(f"Performance: {operation} took {duration:.3f}s", **context)
    _log_metrics.record_log("INFO", f"Performance: {operation}", context)


def log_request(request_id: str, method: str, path: str, status: int, duration: float, **context):
    """记录请求日志"""
    structured_logger = get_structured_logger("requests")
    
    context.update({
        "request_id": request_id,
        "method": method,
        "path": path,
        "status": status,
        "duration": duration
    })
    
    structured_logger.info(f"Request {method} {path} -> {status} ({duration:.3f}s)", **context)
    _log_metrics.record_log("INFO", f"Request {method} {path}", context)


def log_error(error: Exception, context: str = "", **extra):
    """记录错误日志"""
    structured_logger = get_structured_logger("errors")
    
    extra.update({
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context
    })
    
    structured_logger.error(f"Error in {context}: {error}", **extra)
    _log_metrics.record_log("ERROR", f"Error in {context}", extra)


class AsyncLogContext:
    """异步日志上下文管理器"""
    
    def __init__(self, operation: str, logger_name: str = "operation"):
        self.operation = operation
        self.logger = get_structured_logger(logger_name)
        self.start_time = None
        self.context = {}
    
    def add_context(self, **kwargs):
        """添加上下文信息"""
        self.context.update(kwargs)
        return self
    
    async def __aenter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting {self.operation}", **self.context)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            if exc_type is None:
                self.logger.info(f"Completed {self.operation} in {duration:.3f}s", 
                               duration=duration, **self.context)
                log_performance(self.operation, duration, **self.context)
            else:
                self.logger.error(f"Failed {self.operation} after {duration:.3f}s: {exc_val}", 
                                duration=duration, error_type=exc_type.__name__, **self.context)
                log_error(exc_val, self.operation, duration=duration, **self.context)


def shutdown_async_logging():
    """关闭异步日志系统"""
    global _async_log_handler
    
    if _async_log_handler:
        _async_log_handler.close()
        _async_log_handler = None
        
    logger.info("[AsyncLogging] Async logging system shutdown")