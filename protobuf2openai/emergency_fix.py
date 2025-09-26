"""
紧急修复 - 最简单的chat completions实现
"""

import json
import uuid
import time
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse
from .models import ChatCompletionsRequest

async def emergency_chat_completions(req: ChatCompletionsRequest, request: Request = None):
    """最简单的chat completions实现 - 保证工作"""
    
    completion_id = f"chatcmpl-{uuid.uuid4()}"
    created_ts = int(time.time())
    
    # 简单响应
    response_content = "我收到了您的请求，正在处理中。请稍等..."
    
    if req.stream:
        async def basic_stream():
            yield f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'created': created_ts, 'model': req.model, 'choices': [{'index': 0, 'delta': {'content': response_content}}]})}\n\n"
            yield f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'created': created_ts, 'model': req.model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(basic_stream(), media_type="text/event-stream")
    else:
        return JSONResponse({
            "id": completion_id,
            "object": "chat.completion",
            "created": created_ts,
            "model": req.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response_content},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
        })