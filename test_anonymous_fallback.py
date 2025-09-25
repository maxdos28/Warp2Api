#!/usr/bin/env python3
"""
测试匿名token回退功能
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_anonymous_fallback():
    print("🔄 测试匿名token回退功能")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    try:
        from warp2protobuf.config.settings import DISABLE_ANONYMOUS_FALLBACK, PRIORITIZE_ANONYMOUS_TOKEN
        from warp2protobuf.core.auth import is_using_personal_token
        
        print(f"📋 当前配置:")
        print(f"   DISABLE_ANONYMOUS_FALLBACK: {DISABLE_ANONYMOUS_FALLBACK}")
        print(f"   PRIORITIZE_ANONYMOUS_TOKEN: {PRIORITIZE_ANONYMOUS_TOKEN}")
        print(f"   使用个人token: {is_using_personal_token()}")
        
        if DISABLE_ANONYMOUS_FALLBACK:
            print(f"   ❌ 匿名token回退已禁用")
            print(f"   💡 需要设置 DISABLE_ANONYMOUS_FALLBACK=false")
        else:
            print(f"   ✅ 匿名token回退已启用")
            
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")

async def test_api_with_fallback():
    print(f"\n🌐 测试API调用（带回退功能）:")
    try:
        import httpx
        
        # 测试API调用
        url = "http://127.0.0.1:28889/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 123456"
        }
        data = {
            "model": "claude-4-sonnet",
            "messages": [{"role": "user", "content": "测试匿名token回退功能是否正常工作"}],
            "max_tokens": 100
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)
            print(f"   📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 请求成功")
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f"   📝 响应内容: {content[:200]}...")
                
                # 检查是否使用了回退机制
                if "配额已用尽" in content or "quota" in content.lower():
                    print(f"   🔄 检测到配额用尽，回退功能应该已触发")
                else:
                    print(f"   ✅ 正常响应，无需回退")
            else:
                print(f"   ❌ 请求失败: {response.text[:200]}")
                
    except Exception as e:
        print(f"   ❌ API调用失败: {e}")

async def test_quota_management():
    print(f"\n📊 测试配额管理:")
    try:
        from warp2protobuf.core.auth import get_priority_token, acquire_anonymous_access_token
        
        print(f"   🔑 测试token获取:")
        try:
            token = await get_priority_token()
            print(f"   ✅ 成功获取token: {token[:30]}...")
        except Exception as e:
            print(f"   ❌ 获取token失败: {e}")
            
        print(f"   🔄 测试匿名token申请:")
        try:
            # 清除冷却限制（如果有的话）
            import os
            if os.path.exists(".anonymous_cooldown"):
                os.remove(".anonymous_cooldown")
            if os.path.exists(".last_anonymous_attempt"):
                os.remove(".last_anonymous_attempt")
                
            anonymous_token = await acquire_anonymous_access_token()
            print(f"   ✅ 成功获取匿名token: {anonymous_token[:30]}...")
        except Exception as e:
            print(f"   ❌ 获取匿名token失败: {e}")
            
    except Exception as e:
        print(f"   ❌ 配额管理测试失败: {e}")

async def main():
    await test_anonymous_fallback()
    await test_api_with_fallback()
    await test_quota_management()
    
    print(f"\n💡 说明:")
    print(f"   1. DISABLE_ANONYMOUS_FALLBACK=false 启用匿名token回退")
    print(f"   2. 当个人token配额用尽时，系统会自动申请匿名token")
    print(f"   3. 这提供了最大的配额使用灵活性")
    print(f"   4. 可以通过日志查看回退过程")

if __name__ == "__main__":
    asyncio.run(main())
