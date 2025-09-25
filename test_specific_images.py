#!/usr/bin/env python3
"""
测试特定图片，验证AI是否能正确识别
"""
import asyncio
import json
import httpx
import subprocess
import sys

async def test_specific_image(image_name, image_data, expected_description):
    """测试特定图片"""
    print(f"测试图片: {image_name}")
    print(f"预期: {expected_description}")
    
    request_data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"请准确描述这张图片。这是一个测试图片，名称是'{image_name}'。请说出你看到的主要颜色和图案。"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                "http://127.0.0.1:28889/v1/messages",
                json=request_data,
                headers={
                    "Authorization": "Bearer 123456",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [])
                
                if content and content[0].get("type") == "text":
                    response_text = content[0].get("text", "")
                    print(f"AI回复: {response_text}")
                    
                    # 智能的匹配检查
                    response_lower = response_text.lower()
                    
                    # 为不同图片定义更灵活的匹配规则
                    if image_name == "blue_square":
                        # 检查是否提到蓝色和方形/正方形
                        has_blue = any(word in response_lower for word in ["蓝色", "blue", "蓝"])
                        has_square = any(word in response_lower for word in ["方形", "正方形", "square", "方块"])
                        success = has_blue and has_square
                        print(f"检测结果: 蓝色={has_blue}, 方形={has_square}")
                        
                    elif image_name == "green_square":
                        # 检查是否提到绿色和方形/正方形
                        has_green = any(word in response_lower for word in ["绿色", "green", "绿"])
                        has_square = any(word in response_lower for word in ["方形", "正方形", "square", "方块"])
                        success = has_green and has_square
                        print(f"检测结果: 绿色={has_green}, 方形={has_square}")
                        
                    elif image_name == "checkerboard":
                        # 检查是否提到棋盘格/格子/黑白图案
                        has_pattern = any(word in response_lower for word in ["棋盘", "格子", "checkerboard", "格", "pattern", "黑白"])
                        success = has_pattern
                        print(f"检测结果: 图案模式={has_pattern}")
                        
                    else:
                        # 后备匹配逻辑
                        expected_keywords = expected_description.lower().split()
                        matched_keywords = [kw for kw in expected_keywords if kw in response_lower]
                        success = len(matched_keywords) > 0
                        print(f"匹配的关键词: {matched_keywords}")
                    
                    if success:
                        print("匹配度: 高 - AI正确识别了图片内容")
                        return True
                    else:
                        print("匹配度: 低 - AI未正确识别图片内容")
                        return False
                        
                else:
                    print("响应格式异常")
                    return False
                    
            else:
                print(f"请求失败: {response.text}")
                return False
                
    except Exception as e:
        print(f"请求异常: {e}")
        return False
    
    finally:
        print("-" * 60)

async def main():
    # 首先创建测试图片
    print("创建测试图片...")
    try:
        result = subprocess.run([sys.executable, "create_test_image.py"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"创建测试图片失败: {result.stderr}")
            return
        print(result.stdout)
    except Exception as e:
        print(f"执行创建脚本失败: {e}")
        return
    
    # 加载测试图片
    try:
        with open('test_images.json', 'r') as f:
            images = json.load(f)
    except Exception as e:
        print(f"加载测试图片失败: {e}")
        return
    
    print("开始测试特定图片...")
    print("=" * 60)
    
    # 定义测试案例
    test_cases = [
        ("blue_square", images["blue_square"], "blue square color"),
        ("green_square", images["green_square"], "green square color"), 
        ("checkerboard", images["checkerboard"], "checkerboard pattern black white")
    ]
    
    results = []
    for image_name, image_data, expected in test_cases:
        success = await test_specific_image(image_name, image_data, expected)
        results.append((image_name, success))
        await asyncio.sleep(1)  # 避免请求过快
    
    # 汇总结果
    print("测试结果汇总:")
    print("=" * 60)
    
    success_count = 0
    for image_name, success in results:
        status = "通过" if success else "失败"
        print(f"{image_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n总体通过率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    
    if success_count == len(results):
        print("所有测试通过！图片支持功能正常工作。")
    elif success_count > 0:
        print("部分测试通过，可能存在图片数据传递问题。")
    else:
        print("所有测试失败，图片支持功能需要进一步调试。")
        print("\n可能的问题:")
        print("- 图片数据在传递过程中被替换或修改")
        print("- AI接收到的图片与发送的不匹配")
        print("- 存在缓存问题")
        print("- protobuf转换过程中数据损坏")

if __name__ == "__main__":
    asyncio.run(main())
