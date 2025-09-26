"""
Cline 请求拦截器 - 极简版本
"""

import json
import uuid
from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse


async def intercept_cline_request(request: Request, call_next):
    """
    中间件：拦截 Cline 请求并直接返回工具调用
    """
    # 只处理 chat completions 请求
    if request.url.path != "/v1/chat/completions":
        return await call_next(request)
    
    try:
        # 获取请求体
        body = await request.body()
        data = json.loads(body)
        
        # 检查是否是 Cline 请求
        messages = data.get("messages", [])
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if "Cline wants to read this file:" in content:
                    # 找到了 Cline 请求！
                    print("[Cline Interceptor] Detected Cline request!")
                    
                    # 提取文件路径
                    parts = content.split("Cline wants to read this file:")
                    file_path = None
                    if len(parts) > 1:
                        lines = parts[1].strip().split('\n')
                        for line in lines:
                            line = line.strip()
                            if line:
                                file_path = line
                                break
                    
                    # 创建响应
                    completion_id = str(uuid.uuid4())
                    response = {
                        "id": completion_id,
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": data.get("model", "claude-4-sonnet"),
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": f"I'll help you examine the file. Let me read {file_path or 'the file'} for you.",
                                "tool_calls": [{
                                    "id": f"call_{uuid.uuid4().hex[:24]}",
                                    "type": "function",
                                    "function": {
                                        "name": "read_file",
                                        "arguments": json.dumps({"path": file_path or "."})
                                    }
                                }]
                            },
                            "finish_reason": "tool_calls"
                        }]
                    }
                    
                    return JSONResponse(content=response)
        
        # 重新设置请求体
        async def receive():
            return {"type": "http.request", "body": body}
        
        request._receive = receive
        
    except Exception as e:
        print(f"[Cline Interceptor] Error: {e}")
    
    # 不是 Cline 请求，继续正常处理
    return await call_next(request)
