"""
Cline 专用修复模块
"""

import json
import uuid
from typing import Dict, Any, Optional, Tuple

def detect_cline_request(req: Any) -> Tuple[bool, Optional[str]]:
    """
    检测是否是 Cline 的文件请求
    返回: (是否是Cline请求, 文件路径)
    """
    if not req.messages:
        return False, None
    
    # 检查所有用户消息
    for msg in req.messages:
        if msg.role == "user" and isinstance(msg.content, str):
            content = msg.content
            
            # 直接检查是否包含 Cline 的标志性文本
            if "Cline wants to read this file:" in content:
                # 提取文件路径 - 查找冒号后的所有内容
                parts = content.split("Cline wants to read this file:")
                if len(parts) > 1:
                    # 获取冒号后的所有内容，包括换行
                    file_content = parts[1].strip()
                    
                    # 按行分割，找到第一个非空行
                    lines = file_content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('//') and not line.startswith('#'):
                            # 找到了文件路径
                            return True, line
                
                # 如果没找到有效路径，但确实是 Cline 请求
                return True, None
            
            # 备选检测：检查是否包含 PHP 文件路径模式
            if ".php" in content or "Controller" in content:
                # 简单的文件路径提取
                import re
                # 匹配任何看起来像文件路径的内容
                patterns = [
                    r'(/[^/\s]+(?:/[^/\s]+)*\.php)',  # Unix 路径
                    r'([a-zA-Z]:\\[^\\s]+(?:\\[^\\s]+)*\.php)',  # Windows 路径
                    r'([^/\s]+(?:/[^/\s]+)*\.php)',  # 相对路径
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, content)
                    if match:
                        return True, match.group(1)
    
    return False, None


def create_cline_tool_response(file_path: Optional[str]) -> Dict[str, Any]:
    """
    创建 Cline 期望的工具调用响应
    """
    if not file_path:
        # 如果没有检测到文件路径，返回一个列出文件的工具调用
        return {
            "role": "assistant",
            "content": "I'll help you with the PHP code. Let me check the available files first.",
            "tool_calls": [{
                "id": f"call_{uuid.uuid4().hex[:24]}",
                "type": "function",
                "function": {
                    "name": "list_files",
                    "arguments": json.dumps({"path": "."})
                }
            }]
        }
    
    # 返回读取文件的工具调用
    return {
        "role": "assistant",
        "content": f"I'll help you examine the PHP file. Let me read {file_path} for you.",
        "tool_calls": [{
            "id": f"call_{uuid.uuid4().hex[:24]}",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": json.dumps({"path": file_path})
            }
        }]
    }
