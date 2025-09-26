#!/usr/bin/env python3
"""
测试API响应格式问题
"""

import json
import requests
import time

def test_api_response():
    """测试API响应格式"""
    
    # 测试数据
    test_request = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "Hello, test message"}
        ],
        "stream": False,
        "max_tokens": 100
    }
    
    print("🧪 测试API响应格式...")
    print(f"请求数据: {json.dumps(test_request, indent=2)}")
    
    try:
        # 发送请求
        response = requests.post(
            "http://localhost:28889/v1/chat/completions",
            json=test_request,
            timeout=30
        )
        
        print(f"\n📊 响应状态码: {response.status_code}")
        print(f"📊 响应头: {dict(response.headers)}")
        
        # 获取原始响应文本
        raw_text = response.text
        print(f"📊 原始响应长度: {len(raw_text)} 字符")
        print(f"📊 原始响应前500字符: {raw_text[:500]}")
        
        if not raw_text.strip():
            print("❌ 响应为空!")
            return False
            
        # 尝试解析JSON
        try:
            json_data = response.json()
            print(f"✅ JSON解析成功")
            print(f"📊 JSON数据: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
            
            # 检查OpenAI格式
            if "choices" in json_data:
                print("✅ 包含choices字段")
                if json_data["choices"] and "message" in json_data["choices"][0]:
                    print("✅ 包含message字段")
                    content = json_data["choices"][0]["message"].get("content", "")
                    print(f"✅ 消息内容: {content[:200]}...")
                else:
                    print("❌ choices格式不正确")
            elif "error" in json_data:
                print(f"⚠️ 返回错误: {json_data['error']}")
            else:
                print("❌ 不是标准OpenAI格式")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"❌ 无效的JSON响应")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器 - 服务器可能未启动")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False
        
    return True


def test_streaming_response():
    """测试流式响应"""
    
    test_request = {
        "model": "claude-4-sonnet", 
        "messages": [
            {"role": "user", "content": "Say hello"}
        ],
        "stream": True,
        "max_tokens": 50
    }
    
    print("\n🌊 测试流式响应...")
    
    try:
        response = requests.post(
            "http://localhost:28889/v1/chat/completions",
            json=test_request,
            stream=True,
            timeout=30
        )
        
        print(f"📊 流式响应状态码: {response.status_code}")
        
        chunk_count = 0
        valid_chunks = 0
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                print(f"📊 收到流式数据: {line_str[:100]}...")
                
                chunk_count += 1
                if chunk_count > 10:  # 限制输出
                    print("... (限制输出)")
                    break
                    
                # 检查SSE格式
                if line_str.startswith("data: "):
                    data_part = line_str[6:]
                    if data_part.strip() == "[DONE]":
                        print("✅ 收到流结束标记")
                        break
                    try:
                        chunk_data = json.loads(data_part)
                        valid_chunks += 1
                        print(f"✅ 有效的流式JSON块")
                    except json.JSONDecodeError:
                        print(f"❌ 无效的流式JSON: {data_part[:100]}")
                        
        print(f"📊 总chunk数: {chunk_count}, 有效JSON块: {valid_chunks}")
        
    except Exception as e:
        print(f"❌ 流式请求异常: {e}")
        return False
        
    return True


if __name__ == "__main__":
    print("🚀 开始API响应格式测试...")
    
    # 等待服务启动
    for i in range(5):
        try:
            resp = requests.get("http://localhost:28889/healthz", timeout=5)
            if resp.status_code == 200:
                print("✅ 服务已启动")
                break
        except:
            print(f"⏳ 等待服务启动... ({i+1}/5)")
            time.sleep(2)
    else:
        print("❌ 服务未启动，无法进行测试")
        exit(1)
    
    # 运行测试
    success1 = test_api_response()
    success2 = test_streaming_response()
    
    if success1 and success2:
        print("\n✅ 所有测试通过")
    else:
        print("\n❌ 部分测试失败")