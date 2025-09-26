#!/usr/bin/env python3
"""
Cline兼容性最终测试脚本
"""

import json
import requests
import time

def test_cline_compatibility():
    """测试Cline兼容性"""
    
    print("🧪 Cline兼容性测试开始...")
    
    # 模拟Cline发送的实际请求
    cline_request = {
        "model": "claude-4-sonnet",
        "messages": [
            {
                "role": "user", 
                "content": "现在让我查看PHP现有的Controller结构，然后实现每天限制一个发布单的功能。"
            }
        ],
        "stream": True,
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    print(f"📤 发送Cline样式请求...")
    print(f"Model: {cline_request['model']}")
    print(f"Stream: {cline_request['stream']}")
    print(f"Message: {cline_request['messages'][0]['content'][:100]}...")
    
    try:
        response = requests.post(
            "http://localhost:28889/v1/chat/completions",
            json=cline_request,
            stream=True,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ 错误响应: {response.text}")
            return False
        
        # 解析流式响应
        chunk_count = 0
        total_content = ""
        error_chunks = 0
        valid_chunks = 0
        
        print("📥 流式响应内容:")
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                if line_str.startswith("data: "):
                    data_part = line_str[6:]
                    chunk_count += 1
                    
                    if data_part.strip() == "[DONE]":
                        print("✅ 收到流结束标记")
                        break
                        
                    try:
                        chunk_data = json.loads(data_part)
                        valid_chunks += 1
                        
                        if "choices" in chunk_data and chunk_data["choices"]:
                            choice = chunk_data["choices"][0]
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                if content:
                                    total_content += content
                                    print(f"📝 内容片段: '{content[:30]}...'")
                                    
                        # 检查是否有错误信息
                        if "error" in chunk_data:
                            error_chunks += 1
                            print(f"❌ 错误chunk: {chunk_data['error']}")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ 无效JSON chunk: {data_part[:100]}...")
                        error_chunks += 1
                        
                    if chunk_count > 50:  # 限制输出
                        print("... (限制输出，停止显示更多chunks)")
                        break
                        
        print(f"\n📊 流式响应统计:")
        print(f"   总chunk数: {chunk_count}")
        print(f"   有效JSON块: {valid_chunks}")  
        print(f"   错误块: {error_chunks}")
        print(f"   总内容长度: {len(total_content)} 字符")
        print(f"   总内容预览: '{total_content[:200]}...'")
        
        # 判断成功标准
        success = (
            valid_chunks > 0 and 
            len(total_content) > 50 and 
            error_chunks == 0 and
            "I apologize" not in total_content and
            "high demand" not in total_content
        )
        
        if success:
            print("✅ Cline兼容性测试**通过**！")
        else:
            print("❌ Cline兼容性测试**失败**！")
            
        return success
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


def test_non_streaming():
    """测试非流式请求"""
    
    print("\n🧪 非流式请求测试...")
    
    request_data = {
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "请简单介绍一下你自己"}
        ],
        "stream": False,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(
            "http://localhost:28889/v1/chat/completions",
            json=request_data,
            timeout=30
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and data["choices"]:
                content = data["choices"][0]["message"]["content"]
                print(f"✅ 非流式响应成功")
                print(f"📝 内容: {content[:100]}...")
                return True
            else:
                print(f"❌ 响应格式错误: {data}")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 非流式测试异常: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Cline兼容性最终测试...")
    
    # 等待服务启动
    for i in range(10):
        try:
            resp = requests.get("http://localhost:28889/healthz", timeout=3)
            if resp.status_code == 200:
                print("✅ 服务已就绪")
                break
        except:
            print(f"⏳ 等待服务启动... ({i+1}/10)")
            time.sleep(2)
    else:
        print("❌ 服务启动超时")
        exit(1)
    
    # 运行测试
    test1 = test_non_streaming()
    test2 = test_cline_compatibility()
    
    print(f"\n🎯 最终结果:")
    print(f"   非流式测试: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"   Cline流式测试: {'✅ 通过' if test2 else '❌ 失败'}")
    
    if test1 and test2:
        print("\n🎉 所有测试通过！Cline应该可以正常工作了！")
    else:
        print("\n💥 部分测试失败，仍需进一步调试。")