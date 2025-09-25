"""
直接测试图片功能 - 使用28889端口
"""
import requests
import json

# API配置 - 使用正确的端口
API_URL = "http://localhost:28889/v1/messages"
API_KEY = "123456"

# 创建一个明显的测试图片 - 10x10 纯红色方块
def create_red_square_10x10():
    """创建一个10x10像素的纯红色PNG图片"""
    # 这是一个10x10的纯红色PNG图片的base64编码
    red_square_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8z8BQz0AEYBxVSF+FABJADveWkH6oAAAAAElFTkSuQmCC"
    return red_square_base64

def test_image():
    """测试图片功能"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 准备测试图片
    image_base64 = create_red_square_10x10()
    
    # 构建请求
    request_data = {
        "model": "claude-3-opus-20240229",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这是一张纯色图片。请告诉我：1) 图片是什么颜色？2) 是红色、绿色还是蓝色？请直接回答。"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_base64
                        }
                    }
                ]
            }
        ],
        "max_tokens": 200,
        "stream": False
    }
    
    print("🖼️ 图片直接测试")
    print("=" * 50)
    print(f"📤 发送请求到 {API_URL}")
    print(f"   - 图片: 10x10 纯红色方块")
    print(f"   - 问题: 直接询问颜色")
    print()
    
    try:
        response = requests.post(API_URL, headers=headers, json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # 提取AI的回复
            if "content" in result and result["content"]:
                ai_response = result["content"][0].get("text", "")
                
                print("✅ API调用成功！")
                print()
                print("🤖 AI回复:")
                print("-" * 50)
                print(ai_response[:500])  # 只显示前500字符
                if len(ai_response) > 500:
                    print("\n... (回复太长，已截断)")
                print("-" * 50)
                
                # 检查关键词
                keywords_correct = ["红", "red", "红色", "Red", "RED"]
                keywords_wrong = ["看不", "无法", "没有", "不能", "cannot", "unable"]
                
                has_correct = any(keyword in ai_response for keyword in keywords_correct)
                has_wrong = any(keyword in ai_response for keyword in keywords_wrong)
                
                if has_correct and not has_wrong:
                    print("\n✅ 成功！AI正确识别了红色！")
                elif has_wrong:
                    print("\n❌ 失败！AI表示无法看到图片")
                else:
                    print("\n⚠️ 不确定！AI的回复没有明确提到颜色")
                
                # 打印原始响应用于调试
                print("\n📋 原始响应:")
                print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
                
            else:
                print("❌ 响应格式错误")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
        else:
            print(f"❌ API错误: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_image()
