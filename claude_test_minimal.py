#!/usr/bin/env python3
"""
Minimal test to see what's actually happening
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json
import uuid

app = FastAPI()

@app.post("/v1/messages")
async def simple_claude_test(request: Request):
    """Ultra-simple Claude API that always returns tool calls"""
    
    body = await request.json()
    print(f"📥 Received request: {json.dumps(body, indent=2)}")
    
    # Check if this is a tool result
    messages = body.get("messages", [])
    has_tool_result = False
    
    for msg in messages:
        content = msg.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    has_tool_result = True
                    print(f"📤 Found tool result: {block}")
    
    request_id = f"msg_{uuid.uuid4().hex[:16]}"
    
    if has_tool_result:
        # Return analysis based on tool result
        print("🔄 Returning analysis for tool result")
        
        if body.get("stream"):
            async def stream_analysis():
                yield "event: message_start\n"
                yield f"data: {json.dumps({'type': 'message_start', 'message': {'id': request_id, 'type': 'message', 'role': 'assistant', 'content': [], 'model': body.get('model'), 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
                
                yield "event: content_block_start\n"
                yield f"data: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
                
                yield "event: content_block_delta\n"
                yield f"data: {json.dumps({'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': 'Great! I can see the project files. This is a Warp2Api bridge service. Analysis complete!'}})}\n\n"
                
                yield "event: content_block_stop\n"
                yield f"data: {json.dumps({'type': 'content_block_stop', 'index': 0})}\n\n"
                
                yield "event: message_stop\n"
                yield f"data: {json.dumps({'type': 'message_stop'})}\n\n"
                
            return StreamingResponse(stream_analysis(), media_type="text/event-stream")
        else:
            return {
                "id": request_id,
                "type": "message", 
                "role": "assistant",
                "content": [{"type": "text", "text": "Great! I analyzed the project. This is a Warp2Api bridge service."}],
                "model": body.get("model"),
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 20, "output_tokens": 30}
            }
    
    # Initial request - return tool call
    print("🔧 Returning initial tool call")
    
    if body.get("stream"):
        async def stream_tool_call():
            yield "event: message_start\n"
            yield f"data: {json.dumps({'type': 'message_start', 'message': {'id': request_id, 'type': 'message', 'role': 'assistant', 'content': [], 'model': body.get('model'), 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
            
            yield "event: content_block_start\n"
            yield f"data: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
            
            yield "event: content_block_delta\n"
            yield f"data: {json.dumps({'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': 'Let me analyze this codebase using the available tools.'}})}\n\n"
            
            yield "event: content_block_stop\n"
            yield f"data: {json.dumps({'type': 'content_block_stop', 'index': 0})}\n\n"
            
            yield "event: content_block_start\n"
            yield f"data: {json.dumps({'type': 'content_block_start', 'index': 1, 'content_block': {'type': 'tool_use', 'id': 'toolu_01test123456789', 'name': 'bash', 'input': {'command': 'ls'}}})}\n\n"
            
            yield "event: content_block_stop\n"
            yield f"data: {json.dumps({'type': 'content_block_stop', 'index': 1})}\n\n"
            
            yield "event: message_stop\n"
            yield f"data: {json.dumps({'type': 'message_stop'})}\n\n"
            
        return StreamingResponse(stream_tool_call(), media_type="text/event-stream")
    else:
        return {
            "id": request_id,
            "type": "message",
            "role": "assistant", 
            "content": [
                {"type": "text", "text": "Let me analyze this codebase using the available tools."},
                {"type": "tool_use", "id": "toolu_01test123456789", "name": "bash", "input": {"command": "ls"}}
            ],
            "model": body.get("model"),
            "stop_reason": "tool_use", 
            "usage": {"input_tokens": 20, "output_tokens": 30}
        }

if __name__ == "__main__":
    import uvicorn
    print("🧪 Starting minimal Claude API test server on port 28890...")
    print("Configure Claude Code to use: http://localhost:28890")
    uvicorn.run(app, host="0.0.0.0", port=28890)
