"""
完整的图片流程调试
"""
import requests
import json
import base64

# API配置
API_URL = "http://localhost:28889/v1/messages"
API_KEY = "123456"

def create_test_image():
    """创建一个简单的测试图片 - 红色方块"""
    # 10x10 红色方块的base64
    return "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8z8BQz0AEYBxVSF+FABJADveWkH6oAAAAAElFTkSuQmCC"

def test_image_with_debug():
    """测试图片功能并输出详细调试信息"""
    
    print("🔍 图片功能完整调试")
    print("=" * 60)
    
    # 1. 准备数据
    image_base64 = create_test_image()
    print("\n1️⃣ 准备测试数据:")
    print(f"   - 图片类型: 10x10 红色方块")
    print(f"   - Base64长度: {len(image_base64)} 字符")
    print(f"   - Base64前20字符: {image_base64[:20]}...")
    
    # 验证base64
    try:
        decoded = base64.b64decode(image_base64)
        print(f"   - 解码后大小: {len(decoded)} 字节")
        print(f"   - ✅ Base64数据有效")
    except Exception as e:
        print(f"   - ❌ Base64解码失败: {e}")
        return
    
    # 2. 构建请求
    request_data = {
        "model": "claude-3-opus-20240229",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片的颜色。是红色、绿色还是蓝色？"
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
        "max_tokens": 100,
        "stream": False
    }
    
    print("\n2️⃣ 请求结构:")
    print(f"   - 模型: {request_data['model']}")
    print(f"   - 消息数: {len(request_data['messages'])}")
    print(f"   - 内容块数: {len(request_data['messages'][0]['content'])}")
    
    # 3. 发送请求
    print(f"\n3️⃣ 发送请求到: {API_URL}")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            API_URL, 
            headers=headers, 
            json=request_data,
            timeout=30
        )
        
        print(f"   - 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n4️⃣ 响应分析:")
            
            # 检查响应结构
            if "content" in result and result["content"]:
                ai_text = result["content"][0].get("text", "")
                print(f"   - AI回复长度: {len(ai_text)} 字符")
                
                print("\n5️⃣ AI回复内容:")
                print("-" * 60)
                print(ai_text[:300])
                if len(ai_text) > 300:
                    print("... (已截断)")
                print("-" * 60)
                
                # 分析回复
                print("\n6️⃣ 回复分析:")
                
                # 检查是否识别到颜色
                color_keywords = {
                    "红": ["红", "red", "红色", "Red", "RED"],
                    "绿": ["绿", "green", "绿色", "Green", "GREEN"],
                    "蓝": ["蓝", "blue", "蓝色", "Blue", "BLUE"]
                }
                
                found_colors = []
                for color, keywords in color_keywords.items():
                    if any(k in ai_text for k in keywords):
                        found_colors.append(color)
                
                if "红" in found_colors:
                    print("   - ✅ AI正确识别了红色！")
                else:
                    print(f"   - ❌ AI识别的颜色: {found_colors if found_colors else '未识别到颜色'}")
                
                # 检查是否表示看不到图片
                cant_see_keywords = ["看不", "无法", "没有", "不能", "cannot", "unable", "查看", "接收"]
                if any(k in ai_text for k in cant_see_keywords):
                    print("   - ⚠️ AI可能表示无法看到图片")
                
                # 检查是否在描述分析步骤
                analysis_keywords = ["分析", "步骤", "首先", "然后", "接下来", "基本信息", "技术特点"]
                if sum(1 for k in analysis_keywords if k in ai_text) >= 3:
                    print("   - ⚠️ AI可能在描述分析步骤而非实际内容")
                
            else:
                print("   - ❌ 响应格式异常")
                print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
        
        else:
            print(f"\n❌ API错误:")
            print(response.text[:500])
            
    except requests.exceptions.Timeout:
        print("\n❌ 请求超时！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
    
    print("\n" + "=" * 60)
    print("调试完成")

if __name__ == "__main__":
    test_image_with_debug()
