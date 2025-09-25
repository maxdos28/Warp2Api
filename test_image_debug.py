#!/usr/bin/env python3
"""
图片数据传递调试测试
验证图片数据是否正确传递到Warp格式
"""

import json
import sys
sys.path.append('/workspace')

from protobuf2openai.helpers import normalize_content_to_list, segments_to_warp_results

def test_openai_to_claude_conversion():
    """测试OpenAI格式到Claude格式的转换"""
    print("=== OpenAI到Claude格式转换测试 ===")
    
    # OpenAI格式输入
    openai_content = [
        {"type": "text", "text": "请分析这张图片"},
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            }
        }
    ]
    
    print("输入 (OpenAI格式):")
    print(json.dumps(openai_content, indent=2, ensure_ascii=False))
    
    # 转换为标准化格式
    normalized = normalize_content_to_list(openai_content)
    print("\n转换后 (标准化格式):")
    print(json.dumps(normalized, indent=2, ensure_ascii=False))
    
    # 转换为Warp格式
    warp_results = segments_to_warp_results(normalized)
    print("\nWarp格式:")
    print(json.dumps(warp_results, indent=2, ensure_ascii=False))
    
    # 验证转换结果
    has_text = any('text' in result for result in warp_results)
    has_image = any('image' in result for result in warp_results)
    
    print(f"\n✅ 包含文本: {has_text}")
    print(f"✅ 包含图片: {has_image}")
    
    return has_text and has_image

def test_claude_format_passthrough():
    """测试Claude格式的直接传递"""
    print("\n=== Claude格式传递测试 ===")
    
    # Claude格式输入
    claude_content = [
        {"type": "text", "text": "请分析这张图片"},
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            }
        }
    ]
    
    print("输入 (Claude格式):")
    print(json.dumps(claude_content, indent=2, ensure_ascii=False))
    
    # 处理
    normalized = normalize_content_to_list(claude_content)
    print("\n标准化后:")
    print(json.dumps(normalized, indent=2, ensure_ascii=False))
    
    warp_results = segments_to_warp_results(normalized)
    print("\nWarp格式:")
    print(json.dumps(warp_results, indent=2, ensure_ascii=False))
    
    # 验证
    has_text = any('text' in result for result in warp_results)
    has_image = any('image' in result for result in warp_results)
    
    print(f"\n✅ 包含文本: {has_text}")
    print(f"✅ 包含图片: {has_image}")
    
    return has_text and has_image

def test_packet_integration():
    """测试与packet系统的集成"""
    print("\n=== Packet集成测试 ===")
    
    try:
        from protobuf2openai.models import ChatMessage
        from protobuf2openai.packets import map_history_to_warp_messages, attach_user_and_tools_to_inputs, packet_template
        
        # 创建包含图片的消息
        message = ChatMessage(
            role="user",
            content=[
                {"type": "text", "text": "分析图片"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,test_data"
                    }
                }
            ]
        )
        
        history = [message]
        
        # 创建packet
        packet = packet_template()
        task_id = "test_task"
        
        # 测试消息映射
        messages = map_history_to_warp_messages(history, task_id)
        print("Warp消息:")
        print(json.dumps(messages, indent=2, ensure_ascii=False))
        
        # 测试输入附加
        attach_user_and_tools_to_inputs(packet, history, None)
        print("\nPacket输入部分:")
        print(json.dumps(packet.get("input", {}), indent=2, ensure_ascii=False))
        
        # 检查是否包含图片数据
        user_inputs = packet.get("input", {}).get("user_inputs", {}).get("inputs", [])
        has_content = any("content" in inp.get("user_query", {}) for inp in user_inputs)
        
        print(f"\n✅ 包含多模态内容: {has_content}")
        
        return has_content
        
    except Exception as e:
        print(f"❌ Packet集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 图片数据传递调试测试")
    print("="*50)
    
    results = {
        "OpenAI到Claude转换": test_openai_to_claude_conversion(),
        "Claude格式传递": test_claude_format_passthrough(),
        "Packet集成": test_packet_integration()
    }
    
    print("\n" + "="*50)
    print("📊 调试测试结果")
    print("="*50)
    
    for test_name, result in results.items():
        status = "✅ 成功" if result else "❌ 失败"
        print(f"{test_name:<20}: {status}")
    
    success_rate = sum(results.values()) / len(results) * 100
    print(f"\n总体成功率: {success_rate:.1f}%")
    
    if all(results.values()):
        print("\n🎉 所有调试测试通过！图片数据传递机制正常工作！")
    else:
        print("\n⚠️ 部分调试测试失败，需要进一步检查。")

if __name__ == "__main__":
    main()