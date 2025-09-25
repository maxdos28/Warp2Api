#!/usr/bin/env python3
"""
Token配额诊断工具
检查个人token配额状态和系统判断逻辑
"""

import os
import asyncio
import httpx
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def check_token_config():
    """检查token配置"""
    print("🔑 Token配置检查:")
    
    warp_jwt = os.getenv("WARP_JWT")
    warp_refresh = os.getenv("WARP_REFRESH_TOKEN")
    disable_fallback = os.getenv("DISABLE_ANONYMOUS_FALLBACK", "false").lower() == "true"
    
    print(f"   WARP_JWT: {'✅ 已配置' if warp_jwt else '❌ 未配置'}")
    if warp_jwt:
        print(f"      值: {warp_jwt[:30]}...")
    
    print(f"   WARP_REFRESH_TOKEN: {'✅ 已配置' if warp_refresh else '❌ 未配置'}")
    if warp_refresh:
        print(f"      值: {warp_refresh[:30]}...")
    
    print(f"   DISABLE_ANONYMOUS_FALLBACK: {disable_fallback}")
    
    # 判断系统是否会识别为个人token
    is_personal = bool(warp_jwt and warp_refresh)
    print(f"   🎯 系统识别: {'个人token' if is_personal else '默认/匿名token'}")
    
    return {
        "has_personal_jwt": bool(warp_jwt),
        "has_refresh_token": bool(warp_refresh),
        "is_personal_token": is_personal,
        "disable_fallback": disable_fallback
    }


def decode_jwt_payload(token: str) -> dict:
    """解码JWT payload查看详细信息"""
    try:
        import base64
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
        return payload
    except Exception as e:
        return {"error": str(e)}


def check_jwt_details():
    """检查JWT详细信息"""
    print("\n🔍 JWT详细信息:")
    
    warp_jwt = os.getenv("WARP_JWT")
    if not warp_jwt:
        print("   ❌ 未找到WARP_JWT")
        return
    
    payload = decode_jwt_payload(warp_jwt)
    if "error" in payload:
        print(f"   ❌ JWT解码失败: {payload['error']}")
        return
    
    print("   ✅ JWT解码成功")
    
    # 检查过期时间
    if 'exp' in payload:
        exp_time = payload['exp']
        current_time = time.time()
        time_left = exp_time - current_time
        hours_left = time_left / 3600
        
        if time_left > 0:
            print(f"   ⏰ 过期时间: 剩余 {hours_left:.1f} 小时")
        else:
            print(f"   ⚠️ JWT已过期 ({-hours_left:.1f} 小时前)")
    
    # 检查用户信息
    if 'email' in payload:
        print(f"   👤 用户邮箱: {payload['email']}")
    
    if 'user_id' in payload:
        print(f"   🆔 用户ID: {payload['user_id']}")


async def test_direct_warp_api():
    """直接测试Warp API，不通过我们的服务"""
    print("\n🌐 直接测试Warp API:")
    
    warp_jwt = os.getenv("WARP_JWT")
    if not warp_jwt:
        print("   ❌ 无个人JWT token进行测试")
        return
    
    # 构造一个简单的protobuf请求
    test_data = {
        "request": {
            "message": {
                "content": "Hello, 这是配额测试"
            }
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 直接调用Warp API
            response = await client.post(
                "https://app.warp.dev/ai/multi-agent",
                headers={
                    "Authorization": f"Bearer {warp_jwt}",
                    "Content-Type": "application/json",
                    "x-warp-client-version": "v0.2025.08.06.08.12.stable_02",
                    "x-warp-os-category": "Windows",
                    "x-warp-os-name": "Windows",
                    "x-warp-os-version": "11 (26100)",
                },
                json=test_data
            )
            
            print(f"   📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ 个人token配额正常!")
                print("   💡 问题可能在于我们的服务层")
            elif response.status_code == 429:
                response_text = response.text
                print(f"   ❌ 确实配额用尽: {response_text[:100]}")
                if "No remaining quota" in response_text:
                    print("   📋 确认：个人账户配额已用尽")
                else:
                    print("   ⚠️ 可能是频率限制，而非配额用尽")
            elif response.status_code == 401:
                print("   🔑 认证失败: token可能无效或过期")
            else:
                print(f"   ⚠️ 其他错误: {response.text[:100]}")
                
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")


async def test_our_service_api():
    """测试我们的服务API，查看具体错误"""
    print("\n🧪 测试我们的服务API:")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "http://localhost:28888/v1/messages",
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 50,
                    "messages": [{"role": "user", "content": "配额测试"}]
                }
            )
            
            print(f"   📊 状态码: {response.status_code}")
            print(f"   📄 响应: {response.text[:200]}...")
            
            if "个人token配额已用尽" in response.text:
                print("   🔍 确认：系统误判个人token配额用尽")
            elif "配额已用尽" in response.text:
                print("   📋 系统报告配额用尽")
                
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")


def check_cooldown_files():
    """检查冷却文件状态"""
    print("\n❄️ 冷却状态检查:")
    
    cooldown_file = Path(".anonymous_cooldown")
    attempt_file = Path(".last_anonymous_attempt")
    
    if cooldown_file.exists():
        try:
            cooldown_until = float(cooldown_file.read_text().strip())
            remaining = cooldown_until - time.time()
            if remaining > 0:
                print(f"   ⏰ 匿名token冷却中: 剩余 {remaining/60:.1f} 分钟")
            else:
                print("   ✅ 匿名token冷却已结束")
        except:
            print("   ❓ 冷却文件格式错误")
    else:
        print("   ✅ 无匿名token冷却限制")
    
    if attempt_file.exists():
        try:
            last_attempt = float(attempt_file.read_text().strip())
            since_last = time.time() - last_attempt
            print(f"   📅 上次匿名token尝试: {since_last/60:.1f} 分钟前")
        except:
            print("   ❓ 尝试记录格式错误")
    else:
        print("   ✅ 无最近尝试记录")


async def main():
    """主诊断程序"""
    print("🔍 个人Token配额诊断")
    print("=" * 50)
    
    # 1. 检查token配置
    config = check_token_config()
    
    # 2. 检查JWT详细信息
    if config["has_personal_jwt"]:
        check_jwt_details()
    
    # 3. 检查冷却状态
    check_cooldown_files()
    
    # 4. 直接测试Warp API
    if config["has_personal_jwt"]:
        await test_direct_warp_api()
    
    # 5. 测试我们的服务
    await test_our_service_api()
    
    # 6. 提供诊断结论
    print("\n💡 诊断结论:")
    
    if not config["is_personal_token"]:
        print("   ⚠️ 系统未识别为个人token，请检查.env配置")
        print("   💡 确保同时配置 WARP_JWT 和 WARP_REFRESH_TOKEN")
    else:
        print("   ✅ 系统正确识别为个人token")
        print("   🔍 如果仍提示配额用尽，可能是:")
        print("      1. JWT token确实过期或无效")
        print("      2. Warp服务端配额确实用尽")
        print("      3. 网络问题导致请求失败")
        print("      4. 我们的配额检测逻辑有误")
    
    print("\n📋 建议操作:")
    print("   1. 查看详细日志: tail -f logs/warp_server.log")
    print("   2. 检查.env配置文件")
    print("   3. 如果JWT过期，获取新的token")


if __name__ == "__main__":
    asyncio.run(main())

