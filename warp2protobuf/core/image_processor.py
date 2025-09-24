"""
图片数据处理模块
在 protobuf 编码前处理图片数据
"""

import base64
from typing import Any, Dict, List, Union
from ..core.logging import logger


def process_images_for_protobuf(data: Any) -> Any:
    """
    递归处理数据中的图片字段，将 base64 字符串转换为 bytes
    
    这个函数专门处理 images 字段中的 data，
    将 base64 字符串转换为 bytes 以满足 protobuf 的要求
    
    Args:
        data: 要处理的数据（可以是 dict, list 或其他类型）
    
    Returns:
        处理后的数据
    """
    if isinstance(data, dict):
        # 检查是否是图片对象
        if 'data' in data and 'mime_type' in data and len(data) == 2:
            # 这可能是一个图片对象
            if isinstance(data['data'], str):
                try:
                    # 尝试将 base64 字符串解码为 bytes
                    data['data'] = base64.b64decode(data['data'])
                    logger.debug(f"转换图片数据: {len(data['data'])} bytes, {data['mime_type']}")
                except Exception as e:
                    logger.warning(f"无法解码图片数据: {e}")
            return data
        
        # 递归处理字典中的所有值
        processed = {}
        for key, value in data.items():
            # 特别处理 images 字段
            if key == 'images' and isinstance(value, list):
                processed[key] = [process_images_for_protobuf(item) for item in value]
            else:
                processed[key] = process_images_for_protobuf(value)
        return processed
    
    elif isinstance(data, list):
        # 递归处理列表中的所有元素
        return [process_images_for_protobuf(item) for item in data]
    
    else:
        # 其他类型直接返回
        return data


def prepare_data_for_protobuf(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    准备数据以便 protobuf 编码
    主要处理图片数据的格式转换
    
    Args:
        data: 原始数据字典
    
    Returns:
        处理后的数据字典
    """
    # 处理 input.context.images
    if 'input' in data and isinstance(data['input'], dict):
        if 'context' in data['input'] and isinstance(data['input']['context'], dict):
            if 'images' in data['input']['context']:
                logger.info("处理 input.context.images 中的图片数据")
                data['input']['context'] = process_images_for_protobuf(data['input']['context'])
    
    # 处理 task_context.tasks[].messages[].user_query.context.images
    if 'task_context' in data and isinstance(data['task_context'], dict):
        if 'tasks' in data['task_context'] and isinstance(data['task_context']['tasks'], list):
            for task in data['task_context']['tasks']:
                if 'messages' in task and isinstance(task['messages'], list):
                    for msg in task['messages']:
                        if 'user_query' in msg and isinstance(msg['user_query'], dict):
                            if 'context' in msg['user_query'] and isinstance(msg['user_query']['context'], dict):
                                if 'images' in msg['user_query']['context']:
                                    logger.info("处理 task message 中的图片数据")
                                    msg['user_query']['context'] = process_images_for_protobuf(msg['user_query']['context'])
    
    return data