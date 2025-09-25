#!/usr/bin/env python3
"""
层次化Token使用策略测试工具

测试系统的智能token切换功能：个人token -> 匿名token
"""

import asyncio
import httpx
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


async def test_hierarchical_token_usage():
    """测试层次化token使用策略"""
    
    print("🎯 层次化Token使用策略测试")
    print("=" * 50)
    
    # 1. 检查当前配置
    print("\n📋 当前配置:")
    warp_jwt = os.getenv("WARP_JWT")
    warp_refresh = os.getenv("WARP_REFRESH_TOKEN")
    disable_fallback = os.getenv("DISABLE_ANONYMOUS_FALLBACK", "false").lower() == "true"
    
    if warp_jwt and warp_refresh:
        print(f"   🔑 个人Token: ✅ 已配置")
        print(f"   🔄 匿名回退: {'❌ 禁用' if disable_fallback else '✅ 启用'}")
        
        if disable_fallback:
            print("   📊 策略: 仅使用个人配额")
        else:
            print("   📊 策略: 层次化使用（个人 → 匿名）")
    else:
        print("   🔑 个人Token: ❌ 未配置")
        print("   📊 策略: 使用默认/匿名配额")
    
    # 2. 测试API调用并观察token使用模式
    print("\n🧪 测试API调用:")
    
    test_requests = [
        {"model": "claude-3-5-sonnet-20241022", "content": "简单测试1"},
        {"model": "claude-3-5-sonnet-20241022", "content": "简单测试2"},
        {"model": "claude-3-5-sonnet-20241022", "content": "简单测试3"},
    ]
    
    success_count = 0
    quota_exhausted = False
    switched_to_anonymous = False
    
    for i, test_req in enumerate(test_requests, 1):
        print(f"\n   📤 测试请求 {i}/3:")
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "http://localhost:28888/v1/chat/completions",
                    headers={
                        "Authorization": "Bearer 123456",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": test_req["model"],
                        "messages": [{"role": "user", "content": test_req["content"]}],
                        "max_tokens": 20,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"      ✅ 成功: {content[:30]}...")
                    success_count += 1
                    
                    # 检查是否是来自匿名token的响应（通过响应内容判断）
                    if "个人配额" in content or "匿名配额" in content:
                        switched_to_anonymous = True
                        
                else:
                    response_text = response.text
                    print(f"      ❌ 失败 ({response.status_code}): {response_text[:100]}...")
                    
                    if "个人配额和匿名配额均已用尽" in response_text:
                        quota_exhausted = True
                        print("      📋 检测到：所有配额均已用尽")
                    elif "个人token配额已用尽" in response_text:
                        print("      🔄 检测到：个人配额用尽，尝试切换匿名token")
                    elif "您的账户配额已用尽" in response_text:
                        print("      📋 检测到：个人配额用尽（匿名回退已禁用）")
                    elif "配额已用尽" in response_text:
                        quota_exhausted = True
                        print("      📋 检测到：配额用尽")
                        
        except Exception as e:
            print(f"      ❌ 连接错误: {e}")
    
    # 3. 分析测试结果
    print(f"\n📊 测试结果分析:")
    print(f"   ✅ 成功请求: {success_count}/3")
    
    if success_count == 3:
        print("   🎉 所有请求成功 - 配额充足")
    elif success_count > 0:
        print("   ⚠️ 部分请求失败 - 可能遇到配额限制")
        if switched_to_anonymous:
            print("   🔄 观察到token切换行为")
    else:
        print("   ❌ 所有请求失败 - 配额可能已用尽")
    
    if quota_exhausted:
        print("   📋 配额状态: 已用尽")
    
    # 4. 提供建议
    print(f"\n💡 建议:")
    
    if warp_jwt and not disable_fallback:
        print("   🎯 当前使用层次化策略 - 配置正确！")
        print("   📈 这提供了最大的配额使用量")
        if quota_exhausted:
            print("   ⏰ 等待配额重置，或减少使用频率")
    elif warp_jwt and disable_fallback:
        print("   🔒 当前仅使用个人配额 - 配置明确")
        if quota_exhausted:
            print("   💡 可考虑启用匿名回退获得更多配额")
    else:
        print("   📝 建议配置个人Warp账户以获得更多配额")
        print("   🎯 配置后可启用层次化使用策略")


async def demonstrate_token_switching():
    """演示token切换过程"""
    
    print("\n🔄 Token切换过程演示")
    print("=" * 30)
    
    warp_jwt = os.getenv("WARP_JWT")
    disable_fallback = os.getenv("DISABLE_ANONYMOUS_FALLBACK", "false").lower() == "true"
    
    if not warp_jwt:
        print("❌ 需要配置个人token才能演示切换过程")
        return
    
    if disable_fallback:
        print("❌ 匿名回退已禁用，无法演示切换过程")
        print("💡 设置 DISABLE_ANONYMOUS_FALLBACK=false 来启用")
        return
    
    print("🎯 当前配置支持token切换演示")
    print("📋 预期行为:")
    print("   1. 🔑 首先使用个人token")
    print("   2. ❌ 个人配额用尽时显示切换日志")
    print("   3. 🎭 尝试申请匿名token")
    print("   4. ✅ 成功切换到匿名配额（如果可用）")
    
    print("\n📊 请查看服务器日志以观察切换过程:")
    print("   tail -f logs/warp_server.log | grep -E '(个人token|匿名token|配额|切换)'")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        asyncio.run(demonstrate_token_switching())
    else:
        asyncio.run(test_hierarchical_token_usage())
