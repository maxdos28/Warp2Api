#!/usr/bin/env python3
"""
简化的测试服务器，用于验证图片传入功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import base64
import uuid
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import re

class ImageTestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """重写日志方法，添加时间戳"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/healthz":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "ok", "service": "Image Test Server"}
            self.wfile.write(json.dumps(response).encode())
        
        elif parsed_path.path == "/v1/models":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "object": "list",
                "data": [
                    {
                        "id": "claude-4-sonnet",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "warp",
                        "vision_supported": True
                    }
                ]
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
        
        else:
            self.send_error(404)
    
    def do_POST(self):
        """处理POST请求"""
        if self.path == "/v1/chat/completions":
            self.handle_chat_completions()
        else:
            self.send_error(404)
    
    def handle_chat_completions(self):
        """处理聊天完成请求"""
        try:
            # 读取请求数据
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            print(f"收到聊天请求: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
            
            # 处理消息
            messages = request_data.get("messages", [])
            model = request_data.get("model", "claude-4-sonnet")
            
            # 分析最后一条消息
            if messages:
                last_message = messages[-1]
                content = last_message.get("content", [])
                
                # 处理图片和文本
                analysis_result = self.analyze_message_content(content)
                
                # 构建响应
                response = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": analysis_result
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": len(analysis_result.split()),
                        "total_tokens": 100 + len(analysis_result.split())
                    }
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response, indent=2, ensure_ascii=False).encode('utf-8'))
                
                print(f"发送响应: {analysis_result}")
            
            else:
                self.send_error(400, "No messages provided")
                
        except Exception as e:
            print(f"处理请求时出错: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, f"Internal server error: {e}")
    
    def analyze_message_content(self, content):
        """分析消息内容，提取文本和图片"""
        if isinstance(content, str):
            return f"收到文本消息: {content}"
        
        if not isinstance(content, list):
            return "无法解析消息内容格式"
        
        text_parts = []
        images_info = []
        
        for item in content:
            if not isinstance(item, dict):
                continue
                
            item_type = item.get("type")
            
            if item_type == "text":
                text_parts.append(item.get("text", ""))
            
            elif item_type == "image_url":
                image_url_data = item.get("image_url", {})
                url = image_url_data.get("url", "")
                
                if url.startswith("data:"):
                    # 解析data URL
                    match = re.match(r"data:([^;]+);base64,(.+)", url)
                    if match:
                        mime_type = match.group(1)
                        base64_data = match.group(2)
                        
                        try:
                            # 解码图片数据
                            image_bytes = base64.b64decode(base64_data)
                            
                            # 验证PNG文件头
                            is_valid_png = image_bytes.startswith(b'\\x89PNG\\r\\n\\x1a\\n')
                            
                            images_info.append({
                                "mime_type": mime_type,
                                "size_bytes": len(image_bytes),
                                "base64_length": len(base64_data),
                                "is_valid_png": is_valid_png,
                                "file_header": image_bytes[:8].hex() if len(image_bytes) >= 8 else "insufficient_data"
                            })
                            
                        except Exception as e:
                            images_info.append({
                                "mime_type": mime_type,
                                "error": f"解码失败: {e}"
                            })
        
        # 构建分析结果
        combined_text = "".join(text_parts)
        
        result_parts = []
        
        if combined_text:
            result_parts.append(f"📝 文本内容: {combined_text}")
        
        if images_info:
            result_parts.append(f"🖼️ 检测到 {len(images_info)} 张图片:")
            
            for i, img_info in enumerate(images_info):
                if "error" in img_info:
                    result_parts.append(f"  图片 {i+1}: ❌ {img_info['error']}")
                else:
                    result_parts.append(f"  图片 {i+1}:")
                    result_parts.append(f"    - 格式: {img_info['mime_type']}")
                    result_parts.append(f"    - 大小: {img_info['size_bytes']} 字节")
                    result_parts.append(f"    - Base64长度: {img_info['base64_length']} 字符")
                    result_parts.append(f"    - PNG格式验证: {'✅ 有效' if img_info['is_valid_png'] else '❌ 无效'}")
                    result_parts.append(f"    - 文件头: {img_info['file_header']}")
        
        if not combined_text and not images_info:
            result_parts.append("未检测到有效的文本或图片内容")
        
        result_parts.append("\\n🎉 图片传入功能测试成功！服务器成功解析了图片数据。")
        
        return "\\n".join(result_parts)

def run_server(port=8000):
    """运行测试服务器"""
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, ImageTestHandler)
    
    print(f"🚀 图片测试服务器启动")
    print(f"📍 地址: http://127.0.0.1:{port}")
    print(f"🔗 健康检查: http://127.0.0.1:{port}/healthz")
    print(f"📋 模型列表: http://127.0.0.1:{port}/v1/models") 
    print(f"💬 聊天接口: POST http://127.0.0.1:{port}/v1/chat/completions")
    print(f"⏹️  停止服务器: Ctrl+C")
    print("="*60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n🛑 服务器停止")
        httpd.server_close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="图片传入功能测试服务器")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口 (默认: 8000)")
    args = parser.parse_args()
    
    run_server(args.port)