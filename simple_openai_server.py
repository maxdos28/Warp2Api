#!/usr/bin/env python3
"""
简单直接的OpenAI兼容服务器 - 专门修复Cline问题
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import json
import time
import uuid
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn

app = FastAPI(title="Simple OpenAI Compatible API")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

@app.get("/healthz")
def health():
    return {"status": "ok", "service": "Simple OpenAI Compatible API"}

@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "claude-4-sonnet", "object": "model", "created": int(time.time())},
            {"id": "claude-3-sonnet", "object": "model", "created": int(time.time())},
            {"id": "gpt-4", "object": "model", "created": int(time.time())},
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """简单的chat completions实现"""
    
    completion_id = str(uuid.uuid4())
    created_ts = int(time.time())
    
    # 简单的AI响应模拟
    ai_response = f"Hello! I'm a working AI assistant. You asked: '{request.messages[-1].content}'. I can help you with various tasks including code analysis, file operations, and development work. What would you like me to help you with?"
    
    if request.stream:
        # 流式响应
        async def generate_stream():
            # 发送角色
            chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk", 
                "created": created_ts,
                "model": request.model,
                "choices": [{"index": 0, "delta": {"role": "assistant"}}]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            
            # 分块发送内容
            words = ai_response.split()
            for i in range(0, len(words), 3):  # 每3个词一块
                chunk_words = " ".join(words[i:i+3])
                if i > 0:
                    chunk_words = " " + chunk_words
                
                chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts, 
                    "model": request.model,
                    "choices": [{"index": 0, "delta": {"content": chunk_words}}]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                
            # 发送完成
            chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": request.model, 
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate_stream(), media_type="text/event-stream")
    
    else:
        # 非流式响应
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created_ts,
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": ai_response},
                "finish_reason": "stop"
            }]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=28889)