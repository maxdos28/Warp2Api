#!/usr/bin/env python3
"""
简化的Warp API测试脚本
"""
import asyncio
import os
import time
from dotenv import load_dotenv
import httpx

async def test_warp_api_simple():
    print("🔍 简化Warp API测试...")
    
    # 加载.env
    load_dotenv()
    
    # 获取JWT
    jwt = os.getenv("WARP_JWT")
    if not jwt:
        print("❌ 未找到WARP_JWT")
        return
    
    print(f"🔑 使用JWT: {jwt[:30]}...")
    
    # 解析JWT查看详情
    try:
        import jwt as jwt_lib
        payload = jwt_lib.decode(jwt, options={"verify_signature": False})
        
        print(f"\n👤 == JWT信息 ==")
        print(f"用户ID: {payload.get('user_id', 'Unknown')}")
        exp = payload.get('exp', 0)
        if exp:
            remaining = (exp - time.time()) / 3600
            print(f"⏳ 剩余有效期: {remaining:.1f} 小时")
            if remaining < 0.1:
                print(f"⚠️ JWT即将过期！")
    except Exception as e:
        print(f"⚠️ JWT解析失败: {e}")
    
    # 测试简单的HTTP请求到Warp API
    print(f"\n🌐 == 测试Warp API连接 ==")
    
    # 使用我们的本地protobuf编码服务
    local_url = "http://127.0.0.1:28888/api/warp/send"
    test_data = {
        "task_context": {"active_task_id": "quota-test"},
        "input": {
            "context": {},
            "user_inputs": {"inputs": [{"user_query": {"query": "测试配额"}}]}
        },
        "settings": {"model_config": {"base": "claude-4-sonnet"}}
    }
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            print(f"📤 发送请求到本地服务...")
            response = await client.post(local_url, json=test_data)
            
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 请求成功")
                print(f"📝 响应内容: {result.get('response', '')[:100]}...")
                print(f"📊 请求大小: {result.get('request_size', 0)} bytes")
                print(f"📊 响应大小: {result.get('response_size', 0)} bytes")
            else:
                print(f"❌ 请求失败")
                error_text = response.text
                print(f"📝 错误内容: {error_text[:300]}...")
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")

    # 检查配额相关设置
    print(f"\n⚙️ == 配置检查 ==")
    disable_anonymous = os.getenv("DISABLE_ANONYMOUS_FALLBACK", "false").lower()
    print(f"🔒 禁用匿名回退: {disable_anonymous}")
    
    refresh_token = os.getenv("WARP_REFRESH_TOKEN")
    print(f"🔄 有refresh token: {'是' if refresh_token else '否'}")

async def main():
    await test_warp_api_simple()
    
    print(f"\n💡 == 诊断建议 ==")
    print(f"1. 检查JWT有效期是否充足")
    print(f"2. 确认Warp应用中的配额状态")
    print(f"3. 如果配额确实用尽:")
    print(f"   - 等待下月重置")
    print(f"   - 升级到更高套餐")
    print(f"   - 临时启用匿名配额: DISABLE_ANONYMOUS_FALLBACK=false")

if __name__ == "__main__":
    asyncio.run(main())
