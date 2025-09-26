#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON编码器 - 处理bytes对象的序列化
"""

import json
import base64
from typing import Any

class BytesJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，将bytes对象编码为base64字符串"""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super().default(obj)

def serialize_packet_for_json(packet: Any) -> Any:
    """递归处理数据包，将bytes对象转换为base64字符串"""
    if isinstance(packet, dict):
        return {key: serialize_packet_for_json(value) for key, value in packet.items()}
    elif isinstance(packet, list):
        return [serialize_packet_for_json(item) for item in packet]
    elif isinstance(packet, bytes):
        return base64.b64encode(packet).decode('utf-8')
    else:
        return packet

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """安全的JSON序列化，处理bytes对象"""
    try:
        # 先尝试标准序列化
        return json.dumps(obj, **kwargs)
    except TypeError:
        # 如果失败，使用自定义编码器
        return json.dumps(obj, cls=BytesJSONEncoder, **kwargs)