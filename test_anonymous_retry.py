#!/usr/bin/env python3
"""
测试匿名token重试逻辑
"""

import asyncio
import json
from warp2protobuf.warp.api_client import send_protobuf_to_warp_api
from warp2protobuf.core.protobuf_utils import dict_to_protobuf_bytes
from warp2protobuf.core.auth import get_jwt_token, is_using_personal_token

async def test_anonymous_retry():
    print("🧪 Testing Anonymous Token Retry Logic")
    print("=" * 50)
    
    # 检查当前token状态
    current_token = get_jwt_token()
    using_personal = is_using_personal_token()
    
    print(f"📋 Current Status:")
    print(f"  Token exists: {'✅' if current_token else '❌'}")
    print(f"  Using personal token: {'✅' if using_personal else '❌'}")
    print(f"  Token preview: {current_token[:30]}...{current_token[-10:] if current_token else 'None'}")
    
    # 创建测试数据包
    test_packet = {
        "task_context": {
            "active_task_id": "test-12345"
        },
        "input": {
            "context": {},
            "user_inputs": {
                "inputs": [{"user_query": {"query": "Test anonymous token retry logic"}}]
            }
        },
        "settings": {
            "model_config": {"base": "claude-3-sonnet"},
            "rules_enabled": False
        },
        "metadata": {
            "logging": {"entrypoint": "TEST"}
        }
    }
    
    print(f"\n🚀 Testing API call with retry logic...")
    print(f"  This should trigger anonymous token retry if quota is exhausted")
    
    try:
        # 编码为protobuf
        protobuf_bytes = dict_to_protobuf_bytes(test_packet)
        print(f"  📦 Protobuf packet size: {len(protobuf_bytes)} bytes")
        
        # 发送到API（这会触发重试逻辑）
        response, conversation_id, task_id = await send_protobuf_to_warp_api(protobuf_bytes, show_all_events=False)
        
        print(f"\n📊 Response Analysis:")
        print(f"  Response length: {len(response)} chars")
        print(f"  Conversation ID: {conversation_id}")
        print(f"  Task ID: {task_id}")
        print(f"  Response preview: {repr(response[:100])}")
        
        # 分析响应类型
        if "配额已用尽" in response:
            print("  🔴 Status: Quota exhausted (Chinese)")
        elif "quota" in response.lower():
            print("  🔴 Status: Quota exhausted (English)")
        elif "Service is temporarily unavailable" in response:
            print("  🟡 Status: Service unavailable")
        elif len(response) > 100:
            print("  🟢 Status: Normal AI response")
        else:
            print("  🟡 Status: Short response (possibly error)")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print(f"\n📋 Check logs for retry attempts:")
    print(f"  tail -50 logs/warp_api.log | grep -E '第.*次|匿名token|配额'")

if __name__ == "__main__":
    asyncio.run(test_anonymous_retry())