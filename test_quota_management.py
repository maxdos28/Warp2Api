#!/usr/bin/env python3
"""
配额管理测试工具

测试新的智能配额管理和冷却机制
"""

import asyncio
import time
from pathlib import Path
import httpx
import json
from warp2protobuf.core.auth import acquire_anonymous_access_token, get_valid_jwt


async def test_quota_management():
    """测试配额管理功能"""
    
    print("🧪 配额管理测试开始...")
    
    # 1. 检查当前状态和配置
    print("\n📊 检查当前状态:")
    
    # 检查配额管理配置
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    warp_jwt = os.getenv("WARP_JWT")
    disable_fallback = os.getenv("DISABLE_ANONYMOUS_FALLBACK", "false").lower() == "true"
    
    if warp_jwt:
        print(f"   🔑 个人JWT: 已配置 ({warp_jwt[:20]}...)")
    else:
        print("   🔑 个人JWT: 未配置（使用默认token）")
    
    print(f"   🚫 禁用匿名回退: {'✅ 是' if disable_fallback else '❌ 否'}")
    
    cooldown_file = Path(".anonymous_cooldown")
    attempt_file = Path(".last_anonymous_attempt")
    
    if cooldown_file.exists():
        try:
            cooldown_until = float(cooldown_file.read_text().strip())
            remaining = cooldown_until - time.time()
            if remaining > 0:
                print(f"   ⏱️ 冷却中，剩余 {remaining/60:.1f} 分钟")
            else:
                print("   ✅ 冷却已结束")
        except:
            print("   ❓ 冷却文件无效")
    else:
        print("   ✅ 无冷却限制")
    
    if attempt_file.exists():
        try:
            last_attempt = float(attempt_file.read_text().strip())
            since_last = time.time() - last_attempt
            print(f"   📅 上次尝试: {since_last/60:.1f} 分钟前")
        except:
            print("   ❓ 尝试记录无效")
    else:
        print("   ✅ 无最近尝试记录")
    
    # 2. 测试当前JWT
    print("\n🔑 测试当前JWT:")
    try:
        jwt = await get_valid_jwt()
        print(f"   ✅ JWT获取成功: {jwt[:20]}...")
    except Exception as e:
        print(f"   ❌ JWT获取失败: {e}")
    
    # 3. 测试API调用
    print("\n🌐 测试API调用:")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://localhost:28888/v1/chat/completions",
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "messages": [{"role": "user", "content": "测试"}],
                    "max_tokens": 50,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"   ✅ API调用成功: {content[:50]}...")
            else:
                print(f"   ⚠️ API返回 {response.status_code}: {response.text[:100]}...")
                
    except Exception as e:
        print(f"   ❌ API调用失败: {e}")
    
    # 4. 测试匿名token申请（如果不在冷却期）
    print("\n🎭 测试匿名token申请:")
    if cooldown_file.exists():
        print("   ⏸️ 跳过，当前在冷却期")
    else:
        try:
            print("   ⚠️ 这可能会触发新的冷却期...")
            await asyncio.sleep(1)  # 给用户时间看到警告
            
            # 尝试申请（这会触发频率限制检查）
            new_token = await acquire_anonymous_access_token()
            print(f"   ✅ 匿名token申请成功: {new_token[:20]}...")
            
        except Exception as e:
            error_msg = str(e)
            if "cooldown" in error_msg or "too frequent" in error_msg:
                print(f"   ⏱️ 频率限制生效: {error_msg}")
            elif "429" in error_msg:
                print(f"   🔒 服务端限制: {error_msg}")
            else:
                print(f"   ❌ 其他错误: {error_msg}")
    
    # 5. 显示建议
    print("\n💡 建议:")
    
    if disable_fallback and warp_jwt:
        print("   ✅ 已配置个人token且禁用匿名回退 - 仅使用个人配额")
        print("   💡 配额用尽时会收到明确提示，不会混用其他token")
    elif warp_jwt and not disable_fallback:
        print("   🎯 已配置个人token且启用层次化使用 - 推荐配置！")
        print("   💡 优先使用个人配额，用尽后自动切换到匿名token")
        print("   📊 这提供了最大的配额使用量和灵活性")
    elif not warp_jwt and disable_fallback:
        print("   ⚠️ 未配置个人token但禁用了匿名回退")
        print("   💡 建议配置个人token或启用匿名回退")
    else:
        print("   📝 使用默认匿名token，建议配置个人Warp账户以获得更多配额")
    
    if cooldown_file.exists():
        print("   🕒 等待冷却期结束后再试")
    else:
        print("   🔄 可以正常使用服务")
    
    print("   📖 详细解决方案请查看: QUOTA_SOLUTIONS.md")
    print("   📊 监控日志: tail -f logs/warp_server.log | grep -E '(429|quota|cooldown)'")


async def clear_quota_limits():
    """清除配额限制（仅用于测试）"""
    cooldown_file = Path(".anonymous_cooldown")
    attempt_file = Path(".last_anonymous_attempt")
    
    removed = []
    if cooldown_file.exists():
        cooldown_file.unlink()
        removed.append("冷却限制")
    
    if attempt_file.exists():
        attempt_file.unlink()
        removed.append("频率限制")
    
    if removed:
        print(f"✅ 已清除: {', '.join(removed)}")
    else:
        print("ℹ️ 无限制需要清除")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        print("🧹 清除配额限制...")
        asyncio.run(clear_quota_limits())
    else:
        asyncio.run(test_quota_management())
