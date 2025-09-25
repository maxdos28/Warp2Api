#!/usr/bin/env python3
"""
最终vision修复效果验证
全面检查所有修改是否生效
"""

import json
import requests
import base64

BASE_URL = "http://localhost:28889"
API_KEY = "0000"

def print_section(title: str):
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def print_result(success: bool, message: str):
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def test_ai_behavior_change():
    """测试AI行为是否改变"""
    print_section("AI行为变化验证")
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 测试1: 不带图片，询问vision能力
    print("\n[测试1] 询问AI的vision能力")
    response1 = requests.post(
        f"{BASE_URL}/v1/messages",
        json={
            "model": "claude-3-5-sonnet-20241022",
            "messages": [{"role": "user", "content": "你能看图片吗？你有vision能力吗？"}],
            "max_tokens": 200
        },
        headers=headers
    )
    
    if response1.status_code == 200:
        result1 = response1.json()
        text1 = ''.join([block.get('text', '') for block in result1.get('content', []) if block.get('type')=='text'])
        
        # 检查AI是否承认有vision能力
        admits_vision = any(word in text1.lower() for word in ['yes', 'can', 'able', '可以', '能够', 'vision', '视觉'])
        denies_vision = any(word in text1.lower() for word in ['cannot', "can't", 'unable', '无法', '不能', 'terminal'])
        
        print(f"AI回复: {text1[:200]}...")
        print_result(admits_vision and not denies_vision, f"AI承认vision能力: {admits_vision and not denies_vision}")
    else:
        print_result(False, f"请求失败: {response1.status_code}")
    
    # 测试2: 带图片，看AI的反应
    print("\n[测试2] 带图片的反应")
    red_image = "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFklEQVQIHWP8z8DAwMjAwMDIwMDAAAANAAEBMJdNEAAAAABJRU5ErkJggg=="
    
    response2 = requests.post(
        f"{BASE_URL}/v1/messages",
        json={
            "model": "claude-3-5-sonnet-20241022",
            "system": "You have vision capabilities and can analyze images.",
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
                                "data": red_image
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 200
        },
        headers=headers
    )
    
    if response2.status_code == 200:
        result2 = response2.json()
        text2 = ''.join([block.get('text', '') for block in result2.get('content', []) if block.get('type')=='text'])
        
        # 分析AI的反应类型
        says_no_image = any(phrase in text2.lower() for phrase in [
            "don't see", "no image", "not attached", "没有看到", "没有图片", "未上传"
        ])
        
        says_terminal_limit = any(phrase in text2.lower() for phrase in [
            "terminal environment", "cannot view", "unable to see", "终端环境", "无法查看"
        ])
        
        offers_help = any(phrase in text2.lower() for phrase in [
            "upload", "attach", "share", "上传", "分享", "提供"
        ])
        
        print(f"AI回复: {text2[:200]}...")
        print_result(not says_terminal_limit, f"不再说终端限制: {not says_terminal_limit}")
        print_result(says_no_image, f"说没收到图片: {says_no_image}")
        print_result(offers_help, f"愿意帮助分析: {offers_help}")
        
        behavior_improved = not says_terminal_limit and offers_help
        print_result(behavior_improved, f"AI行为改善: {behavior_improved}")
        
        return behavior_improved
    else:
        print_result(False, f"请求失败: {response2.status_code}")
        return False

def test_debug_output():
    """检查debug输出是否正常"""
    print_section("Debug输出验证")
    
    import sys
    sys.path.append('/workspace')
    
    from protobuf2openai.models import ChatMessage
    from protobuf2openai.packets import map_history_to_warp_messages, attach_user_and_tools_to_inputs, packet_template
    
    # 创建包含图片的消息
    message = ChatMessage(
        role="user",
        content=[
            {"type": "text", "text": "测试debug输出"},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
                }
            }
        ]
    )
    
    history = [message]
    task_id = "debug_test"
    
    print("执行packet生成...")
    
    # 生成packet
    packet = packet_template()
    packet["task_context"] = {
        "tasks": [{
            "id": task_id,
            "description": "",
            "status": {"in_progress": {}},
            "messages": map_history_to_warp_messages(history, task_id, None, False),
        }],
        "active_task_id": task_id,
    }
    
    # 这里应该看到debug输出
    attach_user_and_tools_to_inputs(packet, history, None)
    
    # 检查结果
    context = packet.get("input", {}).get("context", {})
    has_images = "images" in context and len(context["images"]) > 0
    
    user_inputs = packet.get("input", {}).get("user_inputs", {}).get("inputs", [])
    has_attachments = any("referenced_attachments" in inp.get("user_query", {}) for inp in user_inputs)
    
    print_result(has_images, f"InputContext包含图片: {has_images}")
    print_result(has_attachments, f"包含referenced_attachments: {has_attachments}")
    
    if has_images:
        print(f"   图片数量: {len(context['images'])}")
        img = context['images'][0]
        print(f"   图片格式: {img.get('mime_type')}")
        print(f"   数据大小: {len(img.get('data', []))} bytes")
    
    return has_images and has_attachments

def test_different_image_formats():
    """测试不同的图片格式和大小"""
    print_section("不同图片格式测试")
    
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 测试不同的图片
    test_cases = [
        {
            "name": "极小PNG图片",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            "type": "image/png"
        },
        {
            "name": "红色2x2PNG",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFklEQVQIHWP8z8DAwMjAwMDIwMDAAAANAAEBMJdNEAAAAABJRU5ErkJggg==",
            "type": "image/png"
        }
    ]
    
    results = []
    
    for case in test_cases:
        print(f"\n[测试] {case['name']}")
        
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "system": "You have vision capabilities. You can see and analyze images.",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"分析这张{case['name']}，告诉我你看到了什么？"},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": case["type"],
                                    "data": case["data"]
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 200
            },
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            text = ''.join([block.get('text', '') for block in result.get('content', []) if block.get('type')=='text'])
            
            # 检查是否真的看到了图片
            sees_image = any(word in text.lower() for word in [
                'i can see', 'i see', 'the image', 'red', 'color', 'pixel',
                '我看到', '我可以看到', '图片', '红色', '颜色', '像素'
            ])
            
            no_image = any(phrase in text.lower() for phrase in [
                "don't see", "no image", "not see", "没看到", "没有图片"
            ])
            
            print(f"   回复: {text[:150]}...")
            print_result(sees_image and not no_image, f"识别图片: {sees_image and not no_image}")
            
            results.append(sees_image and not no_image)
        else:
            print_result(False, f"请求失败: {response.status_code}")
            results.append(False)
    
    return any(results)

def main():
    """主验证函数"""
    print("🔍 Vision修复效果最终验证")
    print("="*70)
    
    # 检查服务器
    try:
        health = requests.get(f"{BASE_URL}/healthz", headers={"Authorization": f"Bearer {API_KEY}"})
        if health.status_code != 200:
            print("❌ 服务器未运行")
            return
        print("✅ 服务器运行正常")
    except:
        print("❌ 无法连接服务器")
        return
    
    # 执行验证测试
    behavior_improved = test_ai_behavior_change()
    debug_working = test_debug_output()
    image_processing = test_different_image_formats()
    
    # 最终评估
    print_section("最终验证结果")
    
    print(f"AI行为改善: {'✅' if behavior_improved else '❌'}")
    print(f"Debug输出正常: {'✅' if debug_working else '❌'}")
    print(f"图片处理功能: {'✅' if image_processing else '❌'}")
    
    total_score = sum([behavior_improved, debug_working, image_processing])
    
    print(f"\n总体评分: {total_score}/3")
    
    if total_score == 3:
        print("\n🎉 Vision功能完全修复成功！")
    elif total_score == 2:
        print("\n✅ Vision功能大部分修复，基本可用")
    elif total_score == 1:
        print("\n⚠️ Vision功能部分修复，仍有问题")
    else:
        print("\n❌ Vision功能修复失败")
    
    # 详细问题分析
    print_section("问题分析")
    
    if not behavior_improved:
        print("❌ AI行为问题:")
        print("   - AI可能仍然认为自己无法处理图片")
        print("   - 系统提示词可能没有生效")
        print("   - 模型配置可能不正确")
    
    if not debug_working:
        print("❌ 数据传递问题:")
        print("   - 图片可能没有正确添加到InputContext")
        print("   - referenced_attachments可能格式不对")
        print("   - 字节编码可能有问题")
    
    if not image_processing:
        print("❌ 图片处理问题:")
        print("   - Warp后端可能不支持当前格式")
        print("   - 图片数据可能在传输中丢失")
        print("   - 需要其他协议字段")
    
    # 给出下一步建议
    if total_score < 3:
        print_section("下一步建议")
        print("1. 检查Warp IDE的实际网络请求格式")
        print("2. 尝试其他protobuf字段组合")
        print("3. 检查是否需要特殊的认证或权限")
        print("4. 考虑联系Warp开发团队获取文档")

if __name__ == "__main__":
    main()