#!/usr/bin/env python3
"""
测试Warp API的原始响应，获取详细错误信息
"""
import asyncio
import json
import os
from dotenv import load_dotenv
from warp2protobuf.core.auth import get_valid_jwt
from warp2protobuf.core.protobuf_utils import dict_to_protobuf_bytes
import httpx

async def test_warp_raw_response():
    print("🔍 测试Warp API原始响应...")
    
    # 加载.env
    load_dotenv()
    
    try:
        # 获取当前JWT
        jwt = await get_valid_jwt()
        print(f"🔑 使用JWT: {jwt[:30]}...")
        
        # 构造测试请求
        test_request = {
            "task_context": {
                "active_task_id": "test-quota-check"
            },
            "input": {
                "context": {},
                "user_inputs": {
                    "inputs": [{
                        "user_query": {
                            "query": "简单测试配额状态"
                        }
                    }]
                }
            },
            "settings": {
                "model_config": {
                    "base": "claude-4-sonnet"
                }
            }
        }
        
        # 编码为protobuf
        protobuf_bytes = dict_to_protobuf_bytes(test_request, "warp.multi_agent.v1.Request")
        print(f"📦 Protobuf大小: {len(protobuf_bytes)} bytes")
        
        # 发送到Warp API
        warp_url = "https://warp.dev/api/v1/multi_agent"
        headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/x-protobuf",
            "User-Agent": "WarpTerminal/0.2024.10.29.08.02.stable_02"
        }
        
        print(f"🌐 请求URL: {warp_url}")
        print(f"📋 请求头: Authorization=Bearer {jwt[:20]}...")
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(warp_url, headers=headers, content=protobuf_bytes)
            
            print(f"\n📊 == Warp API 原始响应 ==")
            print(f"🔢 状态码: {response.status_code}")
            print(f"📄 响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                print(f"✅ 请求成功")
                response_text = response.text
                print(f"📝 响应内容 (前200字符): {response_text[:200]}")
            elif response.status_code == 429:
                print(f"❌ 配额限制 (429)")
                error_text = response.text
                print(f"📝 错误内容: {error_text}")
                
                # 尝试解析JSON错误
                try:
                    error_json = response.json()
                    print(f"📋 JSON错误详情:")
                    print(json.dumps(error_json, indent=2, ensure_ascii=False))
                except:
                    print(f"📄 原始错误文本: {error_text}")
            elif response.status_code == 401:
                print(f"❌ 认证失败 (401)")
                print(f"📝 错误内容: {response.text}")
            elif response.status_code == 403:
                print(f"❌ 权限不足 (403)")
                print(f"📝 错误内容: {response.text}")
            else:
                print(f"❌ 其他错误 ({response.status_code})")
                print(f"📝 错误内容: {response.text}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def check_warp_account_info():
    print(f"\n🔍 == Warp账户信息检查 ==")
    
    # 解析JWT获取用户信息
    load_dotenv()
    jwt = os.getenv("WARP_JWT")
    
    if jwt:
        try:
            import jwt as jwt_lib
            payload = jwt_lib.decode(jwt, options={"verify_signature": False})
            
            print(f"👤 用户ID: {payload.get('user_id', 'Unknown')}")
            print(f"⏰ JWT签发时间: {payload.get('iat', 'Unknown')}")
            print(f"⏰ JWT过期时间: {payload.get('exp', 'Unknown')}")
            
            import time
            exp = payload.get('exp', 0)
            if exp:
                remaining = (exp - time.time()) / 3600
                print(f"⏳ JWT剩余有效期: {remaining:.1f} 小时")
                
                if remaining < 0.1:  # 小于6分钟
                    print(f"⚠️ JWT即将过期，可能需要刷新")
            
            # 检查firebase信息
            firebase = payload.get('firebase', {})
            print(f"🔥 Firebase信息: {firebase}")
            
        except Exception as e:
            print(f"❌ JWT解析失败: {e}")
    else:
        print(f"❌ 未找到JWT token")

async def main():
    print("🚀 开始Warp API和账户诊断...")
    
    await test_warp_raw_response()
    await check_warp_account_info()
    
    print(f"\n💡 == 诊断建议 ==")
    print(f"1. 检查Warp应用中的配额使用情况")
    print(f"2. 确认Pro订阅状态")
    print(f"3. 如果配额确实用尽，可以:")
    print(f"   - 等待配额重置（通常按月重置）")
    print(f"   - 升级到更高套餐")
    print(f"   - 临时启用匿名配额作为备用")

if __name__ == "__main__":
    asyncio.run(main())
