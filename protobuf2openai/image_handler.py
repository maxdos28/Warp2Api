"""
图片处理辅助模块
处理图片数据的编码和传递
"""

import base64
from typing import Dict, List, Any, Union


def prepare_images_for_protobuf(images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    准备图片数据以便protobuf编码
    
    Args:
        images: 图片数据列表，每个包含 'data' 和 'mime_type'
    
    Returns:
        处理后的图片列表
    """
    processed_images = []
    
    for img in images:
        if not isinstance(img, dict):
            continue
            
        processed_img = {}
        
        # 处理MIME类型
        if 'mime_type' in img:
            processed_img['mime_type'] = img['mime_type']
        
        # 处理图片数据
        if 'data' in img:
            data = img['data']
            
            # 如果是字符串（base64），解码为bytes
            if isinstance(data, str):
                try:
                    # 尝试解码base64
                    processed_img['data'] = base64.b64decode(data)
                except Exception:
                    # 如果解码失败，尝试作为普通字符串编码
                    processed_img['data'] = data.encode('utf-8')
            elif isinstance(data, bytes):
                # 如果已经是bytes，直接使用
                processed_img['data'] = data
            else:
                # 其他类型，尝试转换
                processed_img['data'] = str(data).encode('utf-8')
        
        if processed_img:
            processed_images.append(processed_img)
    
    return processed_images


def prepare_packet_for_bridge(packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    准备数据包以便发送到bridge
    不做任何修改，让protobuf编码器处理bytes
    
    Args:
        packet: 原始数据包
    
    Returns:
        原始数据包（不修改）
    """
    # 直接返回原始packet，让protobuf编码器处理bytes类型
    # protobuf编码器知道如何正确处理bytes字段
    return packet
    
    # 处理 task_context.tasks[].messages[].user_query.context.images
    if 'task_context' in processed and 'tasks' in processed.get('task_context', {}):
        for task in processed['task_context'].get('tasks', []):
            if 'messages' in task:
                for msg in task['messages']:
                    if 'user_query' in msg:
                        user_query = msg['user_query']
                        if 'context' in user_query and 'images' in user_query['context']:
                            for img in user_query['context']['images']:
                                if isinstance(img, dict) and 'data' in img:
                                    if isinstance(img['data'], bytes):
                                        img['data'] = base64.b64encode(img['data']).decode('utf-8')
    
    return processed