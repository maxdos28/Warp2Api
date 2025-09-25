#!/usr/bin/env python3
"""
检查服务器状态和网络配置
"""

import socket
import requests
import json
import subprocess
import time

def check_port_binding(port):
    """检查端口绑定情况"""
    try:
        # 检查localhost
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result_local = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        # 检查0.0.0.0
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        sock.settimeout(1)
        result_all = sock.connect_ex(('0.0.0.0', port))
        sock.close()
        
        return {
            'localhost': result_local == 0,
            'all_interfaces': result_all == 0,
            'accessible': result_local == 0 or result_all == 0
        }
    except Exception as e:
        return {'error': str(e)}

def test_api_endpoints():
    """测试API端点"""
    base_url = "http://127.0.0.1:28889"
    
    results = {}
    
    # 测试健康检查
    try:
        resp = requests.get(f"{base_url}/healthz", timeout=5)
        results['health'] = {
            'status': resp.status_code,
            'response': resp.json() if resp.status_code == 200 else resp.text
        }
    except Exception as e:
        results['health'] = {'error': str(e)}
    
    # 测试模型列表
    try:
        resp = requests.get(f"{base_url}/v1/models", timeout=5)
        results['models'] = {
            'status': resp.status_code,
            'count': len(resp.json().get('data', [])) if resp.status_code == 200 else 0
        }
    except Exception as e:
        results['models'] = {'error': str(e)}
    
    # 测试chat completions（非流式）
    try:
        resp = requests.post(
            f"{base_url}/v1/chat/completions",
            json={
                "model": "claude-3-sonnet",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            },
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            results['chat_non_stream'] = {
                'status': resp.status_code,
                'has_choices': 'choices' in data and len(data['choices']) > 0,
                'has_assistant_message': False,
                'content_length': 0
            }
            
            if data.get('choices'):
                choice = data['choices'][0]
                message = choice.get('message', {})
                if message.get('role') == 'assistant':
                    results['chat_non_stream']['has_assistant_message'] = True
                    results['chat_non_stream']['content_length'] = len(message.get('content', ''))
        else:
            results['chat_non_stream'] = {'status': resp.status_code, 'error': resp.text}
    except Exception as e:
        results['chat_non_stream'] = {'error': str(e)}
    
    # 测试chat completions（流式）
    try:
        resp = requests.post(
            f"{base_url}/v1/chat/completions",
            json={
                "model": "claude-3-sonnet",
                "messages": [{"role": "user", "content": "Hello"}], 
                "stream": True
            },
            stream=True,
            timeout=10
        )
        
        if resp.status_code == 200:
            chunks = []
            has_role = False
            has_content = False
            has_finish_reason = False
            
            for line in resp.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_part = line_str[6:]
                        if data_part == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(data_part)
                            chunks.append(chunk_data)
                            
                            choices = chunk_data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                finish_reason = choices[0].get("finish_reason")
                                
                                if "role" in delta and delta["role"] == "assistant":
                                    has_role = True
                                if "content" in delta:
                                    has_content = True
                                if finish_reason:
                                    has_finish_reason = True
                        except json.JSONDecodeError:
                            pass
            
            results['chat_stream'] = {
                'status': resp.status_code,
                'chunk_count': len(chunks),
                'has_role': has_role,
                'has_content': has_content, 
                'has_finish_reason': has_finish_reason,
                'cline_compatible': has_role and has_content and has_finish_reason
            }
        else:
            results['chat_stream'] = {'status': resp.status_code, 'error': resp.text}
    except Exception as e:
        results['chat_stream'] = {'error': str(e)}
    
    return results

def main():
    print("🔍 Server Status Check")
    print("=" * 50)
    
    # 检查端口绑定
    print("\n🌐 Port binding check:")
    for port in [28888, 28889]:
        binding = check_port_binding(port)
        print(f"  Port {port}: {binding}")
    
    # 检查进程
    print("\n🔧 Process check:")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        server_processes = [line for line in lines if 'server.py' in line or 'openai_compat' in line]
        for process in server_processes:
            if 'grep' not in process and process.strip():
                print(f"  ✅ {process.split()[10:12]}")  # 显示命令部分
    except Exception as e:
        print(f"  ❌ Process check failed: {e}")
    
    # 测试API端点
    print("\n🧪 API endpoint tests:")
    results = test_api_endpoints()
    
    for endpoint, result in results.items():
        print(f"\n  📡 {endpoint}:")
        if 'error' in result:
            print(f"    ❌ Error: {result['error']}")
        else:
            for key, value in result.items():
                icon = "✅" if (isinstance(value, bool) and value) or (isinstance(value, int) and value > 0) else "📊"
                print(f"    {icon} {key}: {value}")
    
    # Cline兼容性总结
    print("\n" + "=" * 50)
    print("🎯 CLINE COMPATIBILITY SUMMARY:")
    
    chat_stream = results.get('chat_stream', {})
    if chat_stream.get('cline_compatible'):
        print("✅ STREAMING API: COMPATIBLE")
    else:
        print("❌ STREAMING API: NOT COMPATIBLE")
        print("   Issues:")
        if not chat_stream.get('has_role'):
            print("   - Missing assistant role")
        if not chat_stream.get('has_content'):
            print("   - Missing content")
        if not chat_stream.get('has_finish_reason'):
            print("   - Missing finish_reason")
    
    chat_non_stream = results.get('chat_non_stream', {})
    if chat_non_stream.get('has_assistant_message') and chat_non_stream.get('content_length', 0) > 0:
        print("✅ NON-STREAMING API: COMPATIBLE")
    else:
        print("❌ NON-STREAMING API: NOT COMPATIBLE")
    
    print("\n🔗 API Endpoints for external Cline agents:")
    print("   http://0.0.0.0:28889/v1/chat/completions")
    print("   http://127.0.0.1:28889/v1/chat/completions")
    print("   http://localhost:28889/v1/chat/completions")

if __name__ == "__main__":
    main()