from __future__ import annotations

import os

BRIDGE_BASE_URL = os.getenv("WARP_BRIDGE_URL", "http://127.0.0.1:28888")
FALLBACK_BRIDGE_URLS = [
    BRIDGE_BASE_URL,
    "http://127.0.0.1:28888",
]

WARMUP_INIT_RETRIES = int(os.getenv("WARP_COMPAT_INIT_RETRIES", "10"))
WARMUP_INIT_DELAY_S = float(os.getenv("WARP_COMPAT_INIT_DELAY", "0.5"))
WARMUP_REQUEST_RETRIES = int(os.getenv("WARP_COMPAT_WARMUP_RETRIES", "3"))
WARMUP_REQUEST_DELAY_S = float(os.getenv("WARP_COMPAT_WARMUP_DELAY", "1.5"))

# 性能优化配置
HTTP_CLIENT_TIMEOUT = float(os.getenv("HTTP_CLIENT_TIMEOUT", "180.0"))
HTTP_CONNECT_TIMEOUT = float(os.getenv("HTTP_CONNECT_TIMEOUT", "5.0"))
HTTP_MAX_CONNECTIONS = int(os.getenv("HTTP_MAX_CONNECTIONS", "100"))
HTTP_MAX_CONNECTIONS_PER_HOST = int(os.getenv("HTTP_MAX_CONNECTIONS_PER_HOST", "10"))
HTTP_CLIENT_LIMITS = {
    "max_keepalive_connections": HTTP_MAX_CONNECTIONS,
    "max_connections": HTTP_MAX_CONNECTIONS,
    "keepalive_expiry": 30.0,
}

# 日志优化配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # 可设置为 DEBUG, INFO, WARNING, ERROR
LOG_MAX_REQUEST_SIZE = int(os.getenv("LOG_MAX_REQUEST_SIZE", "1000"))  # 限制日志中请求体的最大长度
LOG_MAX_RESPONSE_SIZE = int(os.getenv("LOG_MAX_RESPONSE_SIZE", "500"))  # 限制日志中响应体的最大长度
ENABLE_DEBUG_LOGGING = os.getenv("ENABLE_DEBUG_LOGGING", "false").lower() == "true" 