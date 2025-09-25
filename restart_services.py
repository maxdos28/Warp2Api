#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重启所有服务的脚本
"""

import subprocess
import time
import signal
import os
import sys

def kill_processes():
    """停止所有相关进程"""
    print("🛑 Stopping all services...")
    
    # 停止所有相关进程
    processes_to_kill = [
        "server.py",
        "openai_compat.py",
        "openai_compat_simple.py"
    ]
    
    for process_name in processes_to_kill:
        try:
            result = subprocess.run(
                ["pkill", "-f", process_name], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print(f"  ✅ Stopped {process_name}")
            else:
                print(f"  ℹ️ No {process_name} process found")
        except Exception as e:
            print(f"  ⚠️ Error stopping {process_name}: {e}")
    
    # 等待进程完全停止
    print("⏳ Waiting for processes to stop...")
    time.sleep(3)

def check_processes():
    """检查进程状态"""
    try:
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        
        lines = result.stdout.split('\n')
        server_processes = [
            line for line in lines 
            if ('server.py' in line or 'openai_compat' in line) 
            and 'grep' not in line 
            and line.strip()
        ]
        
        return server_processes
    except Exception as e:
        print(f"⚠️ Error checking processes: {e}")
        return []

def start_services():
    """启动所有服务"""
    print("🚀 Starting services...")
    
    # 启动主Warp服务器
    print("  📡 Starting main Warp server (port 28888)...")
    try:
        subprocess.Popen([
            "python3", "server.py", "--port", "28888"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("  ✅ Main Warp server started")
    except Exception as e:
        print(f"  ❌ Failed to start main server: {e}")
        return False
    
    # 等待主服务器启动
    print("  ⏳ Waiting for main server to initialize...")
    time.sleep(8)
    
    # 启动OpenAI兼容服务器
    print("  🌐 Starting OpenAI compatible server (port 28889)...")
    try:
        subprocess.Popen([
            "python3", "openai_compat.py", "--port", "28889", "--host", "0.0.0.0"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("  ✅ OpenAI compatible server started")
    except Exception as e:
        print(f"  ❌ Failed to start OpenAI server: {e}")
        return False
    
    # 等待OpenAI服务器启动
    print("  ⏳ Waiting for OpenAI server to initialize...")
    time.sleep(5)
    
    return True

def test_services():
    """测试服务是否正常工作"""
    print("🧪 Testing services...")
    
    import requests
    
    # 测试主服务器
    try:
        resp = requests.get("http://127.0.0.1:28888/healthz", timeout=5)
        if resp.status_code == 200:
            print("  ✅ Main server (28888): OK")
        else:
            print(f"  ❌ Main server (28888): HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ❌ Main server (28888): {e}")
    
    # 测试OpenAI兼容服务器
    try:
        resp = requests.get("http://127.0.0.1:28889/healthz", timeout=5)
        if resp.status_code == 200:
            print("  ✅ OpenAI server (28889): OK")
        else:
            print(f"  ❌ OpenAI server (28889): HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ❌ OpenAI server (28889): {e}")
    
    # 测试API功能
    try:
        resp = requests.post(
            "http://127.0.0.1:28889/v1/chat/completions",
            json={
                "model": "claude-3-sonnet",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            },
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            content = data['choices'][0]['message']['content']
            print(f"  ✅ API test: {len(content)} chars response")
            if len(content) > 100:
                print("  🎉 Receiving full AI responses!")
            else:
                print("  ⚠️ Short response (may be error message)")
        else:
            print(f"  ❌ API test: HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ❌ API test: {e}")

def main():
    print("🔄 Service Restart Script")
    print("=" * 50)
    
    # 检查当前进程
    current_processes = check_processes()
    if current_processes:
        print("📋 Current running processes:")
        for proc in current_processes:
            print(f"  - {proc.split()[10:12]}")  # 显示命令部分
    else:
        print("📋 No services currently running")
    
    # 停止所有服务
    kill_processes()
    
    # 确认停止
    remaining_processes = check_processes()
    if remaining_processes:
        print("⚠️ Some processes still running:")
        for proc in remaining_processes:
            print(f"  - {proc}")
        print("🔨 Force killing remaining processes...")
        try:
            subprocess.run(["pkill", "-9", "-f", "server.py"], capture_output=True)
            subprocess.run(["pkill", "-9", "-f", "openai_compat"], capture_output=True)
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Force kill error: {e}")
    
    # 启动服务
    if start_services():
        print("\n" + "=" * 50)
        test_services()
        print("\n" + "=" * 50)
        print("🎉 Service restart completed!")
        print("\n📋 Service URLs:")
        print("  🔧 Main Warp Server: http://127.0.0.1:28888")
        print("  🌐 OpenAI Compatible: http://127.0.0.1:28889")
        print("  📊 Performance Monitor: http://127.0.0.1:28889/v1/performance")
        print("  🏥 Health Check: http://127.0.0.1:28889/v1/health/detailed")
    else:
        print("❌ Service startup failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        kill_processes()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)