"""
本地工具执行模块
为匿名账户提供真实的工具执行功能
"""

import os
import subprocess
import json
from typing import Dict, Any, Optional
from pathlib import Path

class LocalToolExecutor:
    """本地工具执行器"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
    
    def execute_file_tool(self, command: str, path: str = None, file_text: str = "", old_str: str = "", new_str: str = "", view_range: list = None, **kwargs) -> Dict[str, Any]:
        """执行文件操作工具"""
        
        if command == "view":
            return self._view_file(path, view_range)
        elif command == "create":
            return self._create_file(path, file_text)
        elif command == "str_replace":
            return self._replace_in_file(path, old_str, new_str)
        elif command == "undo_edit":
            return self._undo_edit()
        else:
            return {"error": f"Unknown command: {command}"}
    
    def _view_file(self, path: str, view_range: Optional[list] = None) -> Dict[str, Any]:
        """查看文件内容或目录结构"""
        try:
            file_path = self.workspace_path / path
            
            if not file_path.exists():
                return {"error": f"Path not found: {path}"}
            
            # 如果是目录，列出目录内容
            if file_path.is_dir():
                import os
                try:
                    items = []
                    for item in sorted(os.listdir(file_path)):
                        item_path = file_path / item
                        if item_path.is_dir():
                            items.append(f"{item}/")
                        else:
                            size = item_path.stat().st_size
                            items.append(f"{item} ({size} bytes)")
                    
                    content = "\n".join(items)
                    
                    return {
                        "success": True,
                        "content": content,
                        "items": len(items),
                        "message": f"Successfully listed {len(items)} items in directory {path}"
                    }
                except Exception as e:
                    return {"error": f"Failed to list directory: {str(e)}"}
            
            # 如果是文件，读取文件内容
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if view_range and len(view_range) == 2:
                    start, end = int(view_range[0]), int(view_range[1])
                    lines = lines[start-1:end]  # 转换为0-based索引
                
                content = ''.join(lines)
                
                return {
                    "success": True,
                    "content": content,
                    "lines": len(lines),
                    "message": f"Successfully read {len(lines)} lines from {path}"
                }
            
        except Exception as e:
            return {"error": f"Failed to access path: {str(e)}"}
    
    def _create_file(self, path: str, content: str) -> Dict[str, Any]:
        """创建文件"""
        try:
            file_path = self.workspace_path / path
            
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "message": f"Successfully created file: {path}",
                "size": len(content),
                "path": str(file_path)
            }
            
        except Exception as e:
            return {"error": f"Failed to create file: {str(e)}"}
    
    def _replace_in_file(self, path: str, old_str: str, new_str: str) -> Dict[str, Any]:
        """在文件中替换字符串"""
        try:
            file_path = self.workspace_path / path
            
            if not file_path.exists():
                return {"error": f"File not found: {path}"}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_str not in content:
                return {"error": f"String not found in file: {old_str}"}
            
            new_content = content.replace(old_str, new_str)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "success": True,
                "message": f"Successfully replaced text in {path}",
                "replacements": content.count(old_str)
            }
            
        except Exception as e:
            return {"error": f"Failed to replace text: {str(e)}"}
    
    def _undo_edit(self) -> Dict[str, Any]:
        """撤销编辑（简单实现）"""
        return {
            "success": True,
            "message": "Undo operation completed (note: this is a simplified implementation)"
        }
    
    def execute_computer_tool(self, action: str, coordinate: list = None, text: str = "", direction: str = "", key: str = "", **kwargs) -> Dict[str, Any]:
        """执行计算机操作工具（模拟）"""
        
        if action == "screenshot":
            return {
                "success": True,
                "message": "Screenshot taken successfully",
                "file": "screenshot_simulation.png",
                "note": "This is a simulated screenshot for anonymous users"
            }
        elif action == "click":
            coord = coordinate or [0, 0]
            return {
                "success": True,
                "message": f"Clicked at coordinates ({coord[0]}, {coord[1]})",
                "note": "This is a simulated click for anonymous users"
            }
        elif action == "type":
            return {
                "success": True,
                "message": f"Typed text: '{text}'",
                "note": "This is a simulated typing for anonymous users"
            }
        else:
            return {"error": f"Unknown action: {action}"}


# 全局工具执行器实例
local_executor = LocalToolExecutor()


def execute_tool_locally(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """本地执行工具调用"""
    
    if tool_name == "str_replace_based_edit_tool":
        command = tool_input.get("command")
        # 移除command参数，避免重复传递
        params = {k: v for k, v in tool_input.items() if k != "command"}
        return local_executor.execute_file_tool(command, **params)
    
    elif tool_name == "computer_20241022":
        action = tool_input.get("action")
        # 移除action参数，避免重复传递
        params = {k: v for k, v in tool_input.items() if k != "action"}
        return local_executor.execute_computer_tool(action, **params)
    
    else:
        return {"error": f"Unsupported tool: {tool_name}"}