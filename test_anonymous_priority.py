#!/usr/bin/env python3
"""
测试匿名token优先使用功能
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_anonymous_priority():
    print("🎯 测试匿名token优先使用功能")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    # 设置优先使用匿名token
    os.environ["PRIORITIZE_ANONYMOUS_TOKEN"] = "true"
    
    try:
        from warp2protobuf.core.auth import get_priority_token, is_using_personal_token
        from warp2protobuf.config.settings import PRIORITIZE_ANONYMOUS_TOKEN
        
        print(f"📋 当前配置:")
        print(f"   PRIORITIZE_ANONYMOUS_TOKEN: {PRIORITIZE_ANONYMOUS_TOKEN}")
        print(f"   使用个人token: {is_using_personal_token()}")
        
        print(f"\n🔑 测试获取优先token:")
        try:
            token = await get_priority_token()
            print(f"   ✅ 成功获取token: {token[:30]}...")
            
            # 解析JWT查看详情
            try:
                import jwt as jwt_lib
                payload = jwt_lib.decode(token, options={"verify_signature": False})
                print(f"   👤 用户ID: {payload.get('user_id', 'Unknown')}")
                print(f"   📧 邮箱: {payload.get('email', 'Unknown')}")
                print(f"   ⏰ 过期时间: {payload.get('exp', 'Unknown')}")
            except Exception as e:
                print(f"   ⚠️ JWT解析失败: {e}")
                
        except Exception as e:
            print(f"   ❌ 获取token失败: {e}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_api_call():
    print(f"\n🌐 测试API调用:")
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
            "messages": [{"role": "user", "content": "测试匿名token优先使用"}],
            "max_tokens": 50
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)
            print(f"   📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 请求成功")
                print(f"   📝 响应: {result.get('choices', [{}])[0].get('message', {}).get('content', '')}")
            else:
                print(f"   ❌ 请求失败: {response.text[:200]}")
                
    except Exception as e:
        print(f"   ❌ API调用失败: {e}")

async def main():
    await test_anonymous_priority()
    await test_api_call()
    
    print(f"\n💡 说明:")
    print(f"   1. 设置 PRIORITIZE_ANONYMOUS_TOKEN=true 启用匿名token优先")
    print(f"   2. 系统会优先尝试获取匿名token")
    print(f"   3. 如果匿名token获取失败，会回退到个人token")
    print(f"   4. 这提供了最大的配额使用灵活性")

if __name__ == "__main__":
    asyncio.run(main())
