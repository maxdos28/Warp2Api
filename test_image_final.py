"""
最终图片测试 - 验证AI是否能正确看到并描述图片内容
"""
import requests
import base64
import json

# API配置
API_URL = "http://localhost:11899/v1/messages"
API_KEY = "123456"

# 创建一个简单的测试图片 (3x3 红色方块)
def create_red_square():
    """创建一个3x3像素的纯红色图片"""
    # 这是一个3x3的纯红色PNG图片的base64编码
    # 每个像素都是RGB(255, 0, 0)
    red_square_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAMAAAADCAYAAABWKLW/AAAADklEQVQIHWP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
    return red_square_base64

def test_image_description():
    """测试AI是否能正确描述图片"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 准备测试图片
    image_base64 = create_red_square()
    
    # 构建请求
    request_data = {
        "model": "claude-3-opus-20240229",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片的内容。图片是什么颜色？有什么形状？"
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
        "max_tokens": 500,
        "stream": False
    }
    
    print("🖼️ 图片测试")
    print("=" * 50)
    print(f"📤 发送请求到 {API_URL}")
    print(f"   - 图片类型: 3x3 纯红色方块")
    print(f"   - Base64长度: {len(image_base64)} 字符")
    print()
    
    try:
        response = requests.post(API_URL, headers=headers, json=request_data)
        
        if response.status_code == 200:
            result = response.json()
            
            # 提取AI的回复
            if "content" in result and result["content"]:
                ai_response = result["content"][0].get("text", "")
                
                print("✅ API调用成功！")
                print()
                print("🤖 AI回复:")
                print("-" * 50)
                print(ai_response)
                print("-" * 50)
                
                # 检查AI是否正确识别了红色
                keywords = ["红", "red", "红色", "Red", "RED"]
                if any(keyword in ai_response for keyword in keywords):
                    print()
                    print("✅ 成功！AI正确识别了图片中的红色！")
                    return True
                else:
                    print()
                    print("❌ 失败！AI没有正确识别图片中的红色")
                    return False
            else:
                print("❌ 响应格式错误")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return False
                
        else:
            print(f"❌ API错误: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    print("🚀 最终图片功能测试")
    print("=" * 50)
    print()
    
    success = test_image_description()
    
    print()
    print("=" * 50)
    if success:
        print("🎉 测试通过！图片功能正常工作！")
    else:
        print("💔 测试失败！请检查日志排查问题")

if __name__ == "__main__":
    main()
