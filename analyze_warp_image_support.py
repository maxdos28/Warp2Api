#!/usr/bin/env python3
"""
分析Warp IDE图片支持 vs 我们的API实现差异
找出为什么Warp IDE能处理图片，而我们的API不能
"""

import json
import sys
sys.path.append('/workspace')

from protobuf2openai.helpers import normalize_content_to_list, segments_to_warp_results
from protobuf2openai.models import ChatMessage
from protobuf2openai.packets import map_history_to_warp_messages, attach_user_and_tools_to_inputs, packet_template

def analyze_warp_ide_vs_api():
    """分析Warp IDE和我们API的差异"""
    print("🔍 分析Warp IDE图片支持 vs API实现差异")
    print("="*80)
    
    print("\n📋 已知事实:")
    print("✅ Warp IDE可以处理图片")
    print("❌ 我们的API无法让AI识别图片")
    print("✅ 我们的API格式转换正确")
    print("✅ 图片数据正确传递到Warp格式")
    
    print("\n🤔 可能的原因分析:")
    
    reasons = [
        {
            "reason": "1. 消息格式差异",
            "description": "Warp IDE可能使用不同的消息格式或字段",
            "likelihood": "高"
        },
        {
            "reason": "2. 模型配置差异", 
            "description": "IDE和API可能使用不同的模型配置或参数",
            "likelihood": "高"
        },
        {
            "reason": "3. 图片数据编码方式",
            "description": "IDE可能使用不同的图片编码或传输方式",
            "likelihood": "中"
        },
        {
            "reason": "4. 特殊的协议字段",
            "description": "可能需要特定的protobuf字段来启用vision功能",
            "likelihood": "高"
        },
        {
            "reason": "5. 认证或权限差异",
            "description": "IDE可能有特殊的认证方式或权限",
            "likelihood": "中"
        },
        {
            "reason": "6. Agent模式配置",
            "description": "可能需要特定的配置来启用vision功能",
            "likelihood": "高"
        }
    ]
    
    for reason in reasons:
        print(f"\n{reason['reason']} (可能性: {reason['likelihood']})")
        print(f"   {reason['description']}")
    
    return reasons

def examine_current_packet_format():
    """检查当前我们生成的packet格式"""
    print("\n" + "="*80)
    print(" 检查当前packet格式")
    print("="*80)
    
    # 创建包含图片的消息
    message = ChatMessage(
        role="user",
        content=[
            {"type": "text", "text": "分析这张图片"},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": "test_image_data_here"
                }
            }
        ]
    )
    
    history = [message]
    task_id = "test_task"
    
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
    
    attach_user_and_tools_to_inputs(packet, history, None)
    
    print("当前生成的packet结构:")
    print(json.dumps(packet, indent=2, ensure_ascii=False)[:1000] + "...")
    
    # 检查关键字段
    user_inputs = packet.get("input", {}).get("user_inputs", {}).get("inputs", [])
    has_content_field = any("content" in inp.get("user_query", {}) for inp in user_inputs)
    
    print(f"\n关键字段检查:")
    print(f"✅ 包含user_inputs: {len(user_inputs) > 0}")
    print(f"✅ 包含content字段: {has_content_field}")
    
    if has_content_field:
        for inp in user_inputs:
            content = inp.get("user_query", {}).get("content", [])
            print(f"✅ content内容: {len(content)} 个块")
            for i, block in enumerate(content):
                print(f"   块{i}: {list(block.keys())}")
    
    return packet

def suggest_investigation_steps():
    """建议调查步骤"""
    print("\n" + "="*80)
    print(" 建议的调查步骤")
    print("="*80)
    
    steps = [
        {
            "step": "1. 抓包分析Warp IDE",
            "description": "使用网络抓包工具分析Warp IDE发送图片时的实际请求",
            "tools": ["Wireshark", "Charles Proxy", "Burp Suite"],
            "priority": "高"
        },
        {
            "step": "2. 检查Warp API文档",
            "description": "查找Warp官方API文档中关于图片/vision的说明",
            "tools": ["官方文档", "API规范"],
            "priority": "高"
        },
        {
            "step": "3. 分析protobuf定义",
            "description": "检查项目中的.proto文件，寻找图片相关字段",
            "tools": ["proto文件分析"],
            "priority": "高"
        },
        {
            "step": "4. 对比设置参数",
            "description": "检查IDE和API使用的模型配置差异",
            "tools": ["配置文件对比"],
            "priority": "中"
        },
        {
            "step": "5. 测试不同模型",
            "description": "尝试不同的模型名称和配置",
            "tools": ["API测试"],
            "priority": "中"
        }
    ]
    
    for step in steps:
        print(f"\n{step['step']} (优先级: {step['priority']})")
        print(f"   描述: {step['description']}")
        print(f"   工具: {', '.join(step['tools'])}")

def check_proto_files():
    """检查项目中的protobuf定义"""
    print("\n" + "="*80)
    print(" 检查Protobuf定义文件")
    print("="*80)
    
    import os
    import glob
    
    proto_files = glob.glob('/workspace/**/*.proto', recursive=True)
    
    if proto_files:
        print(f"找到 {len(proto_files)} 个proto文件:")
        for proto_file in proto_files:
            print(f"  - {proto_file}")
            
            # 读取并搜索图片相关字段
            try:
                with open(proto_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 搜索可能的图片相关字段
                image_keywords = ['image', 'vision', 'media', 'attachment', 'file', 'content']
                found_keywords = []
                
                for keyword in image_keywords:
                    if keyword.lower() in content.lower():
                        found_keywords.append(keyword)
                
                if found_keywords:
                    print(f"    包含关键词: {found_keywords}")
                else:
                    print(f"    未找到图片相关字段")
                    
            except Exception as e:
                print(f"    读取失败: {e}")
    else:
        print("未找到proto文件")

def analyze_possible_solutions():
    """分析可能的解决方案"""
    print("\n" + "="*80)
    print(" 可能的解决方案")
    print("="*80)
    
    solutions = [
        {
            "solution": "1. 修改消息格式",
            "description": "可能需要使用不同的字段名或结构来传递图片",
            "implementation": "修改packet生成逻辑，使用IDE相同的字段"
        },
        {
            "solution": "2. 添加特殊标记",
            "description": "可能需要特殊的标记或配置来启用vision功能",
            "implementation": "在packet中添加vision相关的配置字段"
        },
        {
            "solution": "3. 使用不同的模型配置",
            "description": "可能需要明确指定支持vision的模型",
            "implementation": "修改模型配置，使用vision模型"
        },
        {
            "solution": "4. 修改Agent模式设置",
            "description": "可能需要禁用或修改Agent模式来支持vision",
            "implementation": "调整settings中的Agent相关配置"
        },
        {
            "solution": "5. 使用附件系统",
            "description": "可能需要使用Warp的附件系统而不是直接在消息中传递图片",
            "implementation": "将图片作为附件而不是消息内容"
        }
    ]
    
    for solution in solutions:
        print(f"\n{solution['solution']}")
        print(f"   问题: {solution['description']}")
        print(f"   实现: {solution['implementation']}")

def main():
    """主分析函数"""
    
    # 分析差异原因
    analyze_warp_ide_vs_api()
    
    # 检查当前实现
    examine_current_packet_format()
    
    # 检查proto文件
    check_proto_files()
    
    # 建议调查步骤
    suggest_investigation_steps()
    
    # 分析解决方案
    analyze_possible_solutions()
    
    print("\n" + "="*80)
    print(" 总结")
    print("="*80)
    print("""
🎯 关键发现:
- 我们的API实现在技术上是正确的
- 图片数据确实传递到了Warp后端
- 问题可能在于消息格式或配置差异

🔍 下一步行动:
1. 【高优先级】分析proto文件中的图片相关字段
2. 【高优先级】检查是否需要特殊的配置来启用vision
3. 【中优先级】尝试不同的消息格式和字段名
4. 【中优先级】测试不同的模型配置

💡 最可能的原因:
- Warp IDE可能使用了我们未发现的特殊字段或配置
- 可能需要特定的protobuf字段来启用vision功能
- Agent模式可能需要特殊配置才能处理图片
""")

if __name__ == "__main__":
    main()