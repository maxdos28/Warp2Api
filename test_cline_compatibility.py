#!/usr/bin/env python3
"""
测试Cline兼容性的脚本
"""

import json
import requests
import time

def test_openai_compatibility():
    """测试OpenAI API兼容性"""
    base_url = "http://127.0.0.1:28889"
    
    print("🧪 Testing OpenAI API Compatibility for Cline...")
    print("=" * 60)
    
    # 测试1: 非流式请求
    print("\n📝 Test 1: Non-streaming request")
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json={
                "model": "claude-3-sonnet",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            },
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Response structure validation:")
            
            # 验证必需字段
            required_fields = ["id", "object", "created", "model", "choices"]
            for field in required_fields:
                if field in data:
                    print(f"  ✅ {field}: {data[field] if field != 'choices' else f'{len(data[field])} choices'}")
                else:
                    print(f"  ❌ Missing field: {field}")
            
            # 验证choices结构
            if "choices" in data and data["choices"]:
                choice = data["choices"][0]
                choice_fields = ["index", "message", "finish_reason"]
                for field in choice_fields:
                    if field in choice:
                        if field == "message":
                            msg = choice[field]
                            print(f"  ✅ choice.{field}.role: {msg.get('role')}")
                            print(f"  ✅ choice.{field}.content: {len(msg.get('content', ''))} chars")
                        else:
                            print(f"  ✅ choice.{field}: {choice[field]}")
                    else:
                        print(f"  ❌ Missing choice field: {field}")
            
            print(f"\n📄 Full response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # 测试2: 流式请求
    print("\n\n📡 Test 2: Streaming request")
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json={
                "model": "claude-3-sonnet", 
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True
            },
            stream=True,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            print("✅ Streaming response chunks:")
            
            chunk_count = 0
            has_role = False
            has_content = False
            has_finish_reason = False
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_part = line_str[6:]
                        if data_part == '[DONE]':
                            print(f"  ✅ Chunk {chunk_count + 1}: [DONE]")
                            break
                        
                        try:
                            chunk_data = json.loads(data_part)
                            chunk_count += 1
                            
                            # 检查chunk结构
                            choices = chunk_data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                finish_reason = choices[0].get("finish_reason")
                                
                                if "role" in delta:
                                    has_role = True
                                    print(f"  ✅ Chunk {chunk_count}: role = {delta['role']}")
                                
                                if "content" in delta:
                                    has_content = True
                                    print(f"  ✅ Chunk {chunk_count}: content = {delta['content'][:50]}...")
                                
                                if finish_reason:
                                    has_finish_reason = True
                                    print(f"  ✅ Chunk {chunk_count}: finish_reason = {finish_reason}")
                            
                        except json.JSONDecodeError as e:
                            print(f"  ❌ Chunk {chunk_count + 1}: Invalid JSON - {e}")
            
            print(f"\n📊 Stream validation summary:")
            print(f"  - Total chunks: {chunk_count}")
            print(f"  - Has role: {'✅' if has_role else '❌'}")
            print(f"  - Has content: {'✅' if has_content else '❌'}")
            print(f"  - Has finish_reason: {'✅' if has_finish_reason else '❌'}")
            
            # Cline兼容性检查
            if has_role and has_content and has_finish_reason:
                print("🎉 CLINE COMPATIBILITY: ✅ PASS")
            else:
                print("⚠️ CLINE COMPATIBILITY: ❌ FAIL")
                if not has_role:
                    print("  - Missing assistant role")
                if not has_content:
                    print("  - Missing content in response")
                if not has_finish_reason:
                    print("  - Missing finish_reason")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 If Cline still reports errors, check the logs above for missing fields.")

if __name__ == "__main__":
    test_openai_compatibility()