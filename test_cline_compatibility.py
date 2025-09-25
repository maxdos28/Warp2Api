#!/usr/bin/env python3
"""
测试Cline兼容性问题
诊断为什么Cline报告"empty or unparsable response"
"""

import json
import requests

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def test_empty_response_issue():
    """测试空响应问题"""
    print("🔍 Cline空响应问题诊断")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 测试各种可能导致空响应的情况
    test_cases = [
        {
            "name": "基础请求",
            "data": {
                "model": "claude-4-sonnet",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 50
            }
        },
        {
            "name": "空消息",
            "data": {
                "model": "claude-4-sonnet", 
                "messages": [{"role": "user", "content": ""}],
                "max_tokens": 50
            }
        },
        {
            "name": "长消息",
            "data": {
                "model": "claude-4-sonnet",
                "messages": [{"role": "user", "content": "请写一个很长的回复，至少200个字，详细解释什么是人工智能"}],
                "max_tokens": 300
            }
        },
        {
            "name": "工具调用",
            "data": {
                "model": "claude-4-sonnet",
                "messages": [{"role": "user", "content": "请截取屏幕截图"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "computer_20241022",
                            "description": "Computer operations",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string", "enum": ["screenshot"]}
                                },
                                "required": ["action"]
                            }
                        }
                    }
                ],
                "max_tokens": 200
            }
        }
    ]
    
    results = []
    
    for case in test_cases:
        print(f"\n[测试] {case['name']}")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json=case['data'],
                headers=headers,
                timeout=30
            )
            
            print(f"HTTP状态码: {response.status_code}")
            print(f"响应长度: {len(response.text)} 字节")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # 检查响应结构完整性
                    required_fields = ['id', 'object', 'created', 'model', 'choices']
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if missing_fields:
                        print(f"❌ 缺少字段: {missing_fields}")
                        results.append(False)
                    else:
                        print("✅ 响应结构完整")
                        
                        # 检查choices内容
                        choices = result.get('choices', [])
                        if not choices:
                            print("❌ choices为空")
                            results.append(False)
                        else:
                            choice = choices[0]
                            message = choice.get('message', {})
                            content = message.get('content', '')
                            
                            print(f"✅ 内容长度: {len(content)} 字符")
                            print(f"✅ 内容预览: {content[:100]}...")
                            
                            if len(content) == 0:
                                print("❌ 内容为空")
                                results.append(False)
                            else:
                                print("✅ 内容正常")
                                results.append(True)
                
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    print(f"原始响应: {response.text[:200]}...")
                    results.append(False)
            else:
                print(f"❌ HTTP错误: {response.text[:200]}...")
                results.append(False)
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            results.append(False)
    
    return results

def test_cline_specific_requirements():
    """测试Cline特定的要求"""
    print("\n🤖 Cline特定要求测试")
    print("="*60)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "Cline/1.0"  # 模拟Cline的User-Agent
    }
    
    # Cline通常发送的请求格式
    cline_request = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {
                "role": "system",
                "content": "You are Cline, an AI assistant that helps with coding tasks."
            },
            {
                "role": "user", 
                "content": "Hello, can you help me write a simple Python script?"
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7,
        "stream": False
    }
    
    print("\n[测试] 模拟Cline请求格式")
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=cline_request,
            headers=headers,
            timeout=30
        )
        
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # 检查Cline期望的字段
            print("✅ 响应结构检查:")
            print(f"   id: {result.get('id', 'MISSING')}")
            print(f"   object: {result.get('object', 'MISSING')}")
            print(f"   model: {result.get('model', 'MISSING')}")
            print(f"   choices: {len(result.get('choices', []))} 个")
            
            if result.get('choices'):
                choice = result['choices'][0]
                message = choice.get('message', {})
                
                print(f"   message.role: {message.get('role', 'MISSING')}")
                print(f"   message.content: {len(message.get('content', ''))} 字符")
                print(f"   finish_reason: {choice.get('finish_reason', 'MISSING')}")
                
                # 检查是否有usage字段（Cline可能需要）
                if 'usage' in result:
                    print(f"   usage: {result['usage']}")
                else:
                    print("   usage: MISSING (可能导致Cline报错)")
                
                return True
            else:
                print("❌ choices为空")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"错误内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def check_bridge_connection():
    """检查桥接服务连接"""
    print("\n🌉 桥接服务连接检查")
    print("="*60)
    
    # 检查桥接服务器
    try:
        bridge_response = requests.get("http://localhost:28888/healthz", timeout=5)
        print(f"桥接服务器(28888): HTTP {bridge_response.status_code}")
        if bridge_response.status_code == 200:
            print(f"   状态: {bridge_response.json()}")
        else:
            print(f"   错误: {bridge_response.text}")
    except Exception as e:
        print(f"❌ 桥接服务器连接失败: {e}")
        return False
    
    # 检查API服务器
    try:
        api_response = requests.get("http://localhost:28889/healthz", timeout=5)
        print(f"API服务器(28889): HTTP {api_response.status_code}")
        if api_response.status_code == 200:
            print(f"   状态: {api_response.json()}")
        else:
            print(f"   错误: {api_response.text}")
    except Exception as e:
        print(f"❌ API服务器连接失败: {e}")
        return False
    
    return True

def main():
    """主诊断函数"""
    print("🔧 Cline API兼容性问题诊断")
    print("="*60)
    print("目标：解决'empty or unparsable response'错误")
    
    # 检查服务器连接
    if not check_bridge_connection():
        print("\n❌ 服务器连接有问题，请重启服务器")
        return
    
    # 测试空响应问题
    empty_response_results = test_empty_response_issue()
    
    # 测试Cline特定要求
    cline_compatibility = test_cline_specific_requirements()
    
    # 总结
    print("\n" + "="*60)
    print("🎯 诊断结果")
    print("="*60)
    
    success_rate = sum(empty_response_results) / len(empty_response_results) if empty_response_results else 0
    
    print(f"基础响应测试: {sum(empty_response_results)}/{len(empty_response_results)} 通过 ({success_rate:.1%})")
    print(f"Cline兼容性测试: {'✅ 通过' if cline_compatibility else '❌ 失败'}")
    
    if success_rate < 0.8:
        print("\n❌ 发现响应问题：")
        print("1. 某些请求返回空响应")
        print("2. 可能是Warp后端连接问题")
        print("3. 建议检查网络连接和服务配置")
    elif not cline_compatibility:
        print("\n❌ 发现Cline兼容性问题：")
        print("1. 响应格式可能不完整")
        print("2. 缺少Cline期望的字段（如usage）")
        print("3. 需要修复OpenAI响应格式")
    else:
        print("\n✅ API响应正常")
        print("Cline的错误可能是暂时性的，建议：")
        print("1. 重试请求")
        print("2. 检查Cline的网络配置")
        print("3. 确认Cline使用的API端点正确")

if __name__ == "__main__":
    main()