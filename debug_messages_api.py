#!/usr/bin/env python3
"""
Claude Messages API (/v1/messages) 错误诊断工具

系统性排查 /v1/messages 接口的各种可能问题
"""

import asyncio
import httpx
import json
import os
import subprocess
import socket
from pathlib import Path


def check_port_status(port: int) -> dict:
    """检查端口状态"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return {
            "port": port,
            "status": "listening" if result == 0 else "not_listening",
            "accessible": result == 0
        }
    except Exception as e:
        return {
            "port": port,
            "status": "error",
            "error": str(e),
            "accessible": False
        }


def check_log_files() -> dict:
    """检查日志文件状态"""
    log_files = [
        "logs/openai_compat.log",
        "logs/warp_server.log",
        "logs/warp_api.log"
    ]
    
    results = {}
    for log_file in log_files:
        log_path = Path(log_file)
        if log_path.exists():
            try:
                # 读取最后几行
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    last_lines = lines[-5:] if len(lines) >= 5 else lines
                
                results[log_file] = {
                    "exists": True,
                    "size": log_path.stat().st_size,
                    "last_lines": [line.strip() for line in last_lines],
                    "has_errors": any("ERROR" in line or "Exception" in line for line in last_lines)
                }
            except Exception as e:
                results[log_file] = {
                    "exists": True,
                    "error": str(e)
                }
        else:
            results[log_file] = {
                "exists": False
            }
    
    return results


async def test_messages_api() -> dict:
    """测试 Claude Messages API"""
    test_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 50,
        "messages": [
            {"role": "user", "content": "Hello, 请简单回复一下测试"}
        ]
    }
    
    results = {}
    
    # 测试不同的请求方式
    tests = [
        {
            "name": "basic_test",
            "url": "http://localhost:28888/v1/messages",
            "headers": {
                "Authorization": "Bearer 123456",
                "Content-Type": "application/json"
            }
        },
        {
            "name": "with_anthropic_version",
            "url": "http://localhost:28888/v1/messages", 
            "headers": {
                "Authorization": "Bearer 123456",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        }
    ]
    
    for test in tests:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    test["url"],
                    headers=test["headers"],
                    json=test_data
                )
                
                results[test["name"]] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_text": response.text[:500] if response.text else "",
                    "headers": dict(response.headers),
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        results[test["name"]]["content"] = data.get("content", [{}])[0].get("text", "")[:100]
                    except:
                        pass
                        
        except Exception as e:
            results[test["name"]] = {
                "success": False,
                "error": str(e)
            }
    
    return results


async def test_openai_api_comparison() -> dict:
    """对比测试 OpenAI 格式的 API"""
    test_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 50,
        "messages": [
            {"role": "user", "content": "Hello, 请简单回复一下测试"}
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://localhost:28888/v1/chat/completions",
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json"
                },
                json=test_data
            )
            
            return {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_text": response.text[:500] if response.text else "",
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def check_environment() -> dict:
    """检查环境配置"""
    env_vars = [
        "API_TOKEN",
        "WARP_JWT", 
        "WARP_REFRESH_TOKEN",
        "DISABLE_ANONYMOUS_FALLBACK"
    ]
    
    results = {}
    for var in env_vars:
        value = os.getenv(var)
        results[var] = {
            "set": value is not None,
            "value": value[:20] + "..." if value and len(value) > 20 else value
        }
    
    return results


async def main():
    """主诊断程序"""
    print("🔍 Claude Messages API (/v1/messages) 错误诊断")
    print("=" * 60)
    
    # 1. 检查端口状态
    print("\n📡 1. 检查服务端口状态:")
    ports = [28888, 28889]  # API服务器和Bridge服务器
    for port in ports:
        status = check_port_status(port)
        icon = "✅" if status["accessible"] else "❌"
        print(f"   {icon} 端口 {port}: {status['status']}")
        if not status["accessible"]:
            print(f"      ⚠️  建议检查服务是否启动: uv run python {'openai_compat.py' if port == 28888 else 'server.py'}")
    
    # 2. 检查环境配置
    print("\n⚙️ 2. 检查环境配置:")
    env_status = check_environment()
    for var, info in env_status.items():
        icon = "✅" if info["set"] else "❌"
        print(f"   {icon} {var}: {'已设置' if info['set'] else '未设置'}")
        if info["set"] and info["value"]:
            print(f"      📄 值: {info['value']}")
    
    # 3. 检查日志文件
    print("\n📋 3. 检查日志文件:")
    log_status = check_log_files()
    for log_file, info in log_status.items():
        if info["exists"]:
            icon = "⚠️" if info.get("has_errors") else "✅"
            print(f"   {icon} {log_file}: 存在 ({info.get('size', 0)} 字节)")
            if info.get("has_errors"):
                print(f"      🔥 发现错误信息，建议查看详细日志")
            if info.get("last_lines"):
                print(f"      📝 最后几行:")
                for line in info["last_lines"][-2:]:  # 只显示最后2行
                    if line.strip():
                        print(f"         {line[:80]}")
        else:
            print(f"   ❌ {log_file}: 不存在")
    
    # 4. 测试 Claude Messages API
    print("\n🧪 4. 测试 Claude Messages API:")
    messages_results = await test_messages_api()
    for test_name, result in messages_results.items():
        if result.get("success"):
            print(f"   ✅ {test_name}: 成功 (状态码: {result['status_code']})")
            if "content" in result:
                print(f"      📝 响应内容: {result['content']}")
        else:
            print(f"   ❌ {test_name}: 失败")
            if "error" in result:
                print(f"      🔥 错误: {result['error']}")
            elif "status_code" in result:
                print(f"      🔥 状态码: {result['status_code']}")
                print(f"      📄 响应: {result.get('response_text', '')[:100]}")
    
    # 5. 对比测试 OpenAI API
    print("\n🆚 5. 对比测试 OpenAI Chat Completions API:")
    openai_result = await test_openai_api_comparison()
    if openai_result.get("success"):
        print(f"   ✅ OpenAI API: 正常 (状态码: {openai_result['status_code']})")
    else:
        print(f"   ❌ OpenAI API: 失败")
        if "error" in openai_result:
            print(f"      🔥 错误: {openai_result['error']}")
        elif "status_code" in openai_result:
            print(f"      🔥 状态码: {openai_result['status_code']}")
    
    # 6. 提供诊断建议
    print("\n💡 6. 诊断建议:")
    
    # 检查服务是否都在运行
    port_28888 = check_port_status(28888)["accessible"]
    port_28889 = check_port_status(28889)["accessible"]
    
    if not port_28888 and not port_28889:
        print("   🚨 两个服务都未启动，请先启动服务:")
        print("      uv run python server.py")
        print("      uv run python openai_compat.py")
    elif not port_28889:
        print("   🚨 Bridge服务器(28889)未启动，请启动:")
        print("      uv run python server.py")
    elif not port_28888:
        print("   🚨 API服务器(28888)未启动，请启动:")
        print("      uv run python openai_compat.py")
    else:
        print("   ✅ 服务端口正常")
        
        # 检查具体的API问题
        if not any(result.get("success", False) for result in messages_results.values()):
            print("   🔥 Claude Messages API 调用失败，可能原因:")
            print("      1. 检查日志: tail -f logs/openai_compat.log")
            print("      2. 检查配额: python test_quota_management.py")
            print("      3. 检查token配置: 确认.env文件中的配置")
            print("      4. 网络问题: 如果在大陆服务器，Google接口可能被屏蔽")
    
    print("\n📚 更多诊断工具:")
    print("   python test_quota_management.py     # 配额管理测试")
    print("   python test_hierarchical_tokens.py  # Token层次化使用测试")
    print("   tail -f logs/openai_compat.log      # 实时查看API日志")


if __name__ == "__main__":
    asyncio.run(main())
