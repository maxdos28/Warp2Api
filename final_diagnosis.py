#!/usr/bin/env python3
"""
最终诊断：到底哪里出了问题
"""

import json
import requests
import sys
sys.path.append('/workspace')

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def diagnose_image_transmission():
    """诊断图片传输的每一个环节"""
    print("🔍 图片传输环节诊断")
    print("="*60)
    
    # 测试1: 检查我们发送的请求格式
    print("\n[诊断1] 检查请求格式")
    
    red_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFklEQVQIHWP8z8DAwMjAwMDIwMDAAAANAAEBMJdNEAAAAABJRU5ErkJggg=="
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "system": "You can see and analyze images. You have vision capabilities.",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "这张图片是什么颜色？"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": red_image_b64
                        }
                    }
                ]
            }
        ],
        "max_tokens": 200
    }
    
    print("✅ 请求格式检查:")
    print(f"   模型: {request_data['model']}")
    print(f"   系统提示: {request_data['system']}")
    print(f"   消息数量: {len(request_data['messages'])}")
    print(f"   内容块数量: {len(request_data['messages'][0]['content'])}")
    print(f"   图片数据长度: {len(red_image_b64)}")
    
    # 测试2: 发送请求并分析响应
    print("\n[诊断2] 发送请求并分析响应")
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        print(f"✅ HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ 响应结构: {list(result.keys())}")
            print(f"✅ 内容块数量: {len(result.get('content', []))}")
            
            ai_text = ''.join([block.get('text', '') for block in result.get('content', []) if block.get('type')=='text'])
            
            print(f"\n🤖 AI完整响应:")
            print(f"   {ai_text}")
            
            # 详细分析AI的回复模式
            print(f"\n🔍 响应分析:")
            
            # 检查AI是否提到了图片
            mentions_image = any(word in ai_text.lower() for word in ['image', 'picture', '图片', '图像'])
            print(f"   提到图片: {'✅' if mentions_image else '❌'}")
            
            # 检查AI是否说没收到
            says_not_received = any(phrase in ai_text.lower() for phrase in [
                "don't see", "no image", "not attached", "没看到", "没有图片", "没有包含"
            ])
            print(f"   说没收到: {'✅' if says_not_received else '❌'}")
            
            # 检查AI是否愿意分析
            willing_to_analyze = any(phrase in ai_text.lower() for phrase in [
                "upload", "attach", "share", "analyze", "上传", "分享", "分析"
            ])
            print(f"   愿意分析: {'✅' if willing_to_analyze else '❌'}")
            
            # 检查是否说终端限制
            says_terminal = any(phrase in ai_text.lower() for phrase in [
                "terminal", "command line", "终端", "命令行"
            ])
            print(f"   说终端限制: {'❌' if says_terminal else '✅'}")
            
            return {
                "request_ok": True,
                "response_ok": True,
                "mentions_image": mentions_image,
                "says_not_received": says_not_received,
                "willing_to_analyze": willing_to_analyze,
                "says_terminal": says_terminal
            }
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"   错误内容: {response.text[:200]}")
            return {"request_ok": False, "response_ok": False}
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return {"request_ok": False, "response_ok": False}

def final_conclusion():
    """最终结论"""
    print("\n" + "="*60)
    print("🎯 最终诊断结论")
    print("="*60)
    
    diagnosis = diagnose_image_transmission()
    
    if diagnosis.get("request_ok") and diagnosis.get("response_ok"):
        print("✅ API通信正常")
        
        if diagnosis.get("willing_to_analyze") and not diagnosis.get("says_terminal"):
            print("✅ AI态度改善 - 不再说终端限制，愿意分析图片")
            
            if diagnosis.get("says_not_received"):
                print("❌ 核心问题: AI说没收到图片")
                print("\n可能的原因:")
                print("1. 🎯 匿名账户vision功能被禁用（最可能）")
                print("2. 图片数据在Warp内部被过滤")
                print("3. 需要特殊的协议字段或配置")
                print("4. Warp后端不支持当前的图片格式")
                
                print("\n💡 验证方法:")
                print("1. 使用真实Warp账户的JWT token测试")
                print("2. 检查Warp IDE是否使用付费账户")
                print("3. 联系Warp团队确认匿名用户的功能限制")
            else:
                print("✅ AI可能真的看到了图片！")
        else:
            print("❌ AI仍然拒绝处理图片")
    else:
        print("❌ API通信有问题")
    
    return diagnosis

if __name__ == "__main__":
    final_conclusion()