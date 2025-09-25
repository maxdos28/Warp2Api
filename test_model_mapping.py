#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模型映射功能
"""

import json
import requests

# 服务器配置
BASE_URL = "http://127.0.0.1:28889"
API_TOKEN = "123456"

def test_model_mapping():
    """测试模型映射功能"""
    print("=== 测试模型映射功能 ===")
    
    headers = {
        "x-api-key": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    # 测试原始模型名称 claude-sonnet-4-20250514
    data = {
        "model": "claude-sonnet-4-20250514",  # 应该映射为 claude-sonnet-4
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": "What model are you?"
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/messages", headers=headers, json=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"请求的模型: claude-sonnet-4-20250514")
            print(f"响应中的模型: {result.get('model', 'unknown')}")
            content = result.get('content', [])
            if content and len(content) > 0:
                text_content = content[0].get('text', '')
                print(f"响应内容: {text_content[:150]}...")
            
            # 检查是否正确映射
            if result.get('model') == "claude-sonnet-4-20250514":
                print("✅ 模型映射成功 - 响应中保持原始模型名称")
            else:
                print(f"⚠️ 响应模型名称: {result.get('model')}")
            
        else:
            print(f"❌ 错误: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    print()

def test_standard_model():
    """测试标准模型名称"""
    print("=== 测试标准模型名称 ===")
    
    headers = {
        "x-api-key": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "claude-sonnet-4",  # 标准模型名称
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": "Hello!"
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/messages", headers=headers, json=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"请求的模型: claude-sonnet-4")
            print(f"响应中的模型: {result.get('model', 'unknown')}")
            print("✅ 标准模型名称正常工作")
        else:
            print(f"❌ 错误: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    print()

def test_model_list():
    """测试模型列表"""
    print("=== 测试模型列表 ===")
    
    headers = {
        "x-api-key": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/v1/models", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            print(f"可用模型数量: {len(models.get('data', []))}")
            print("模型列表:")
            for model in models.get('data', []):
                print(f"  - {model.get('id', 'unknown')}")
            
            # 检查是否包含 claude-sonnet-4
            model_ids = [model.get('id') for model in models.get('data', [])]
            if 'claude-sonnet-4' in model_ids:
                print("✅ 模型列表包含 claude-sonnet-4")
            else:
                print("❌ 模型列表不包含 claude-sonnet-4")
        else:
            print(f"❌ 错误: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    print()

def main():
    print("模型映射功能测试")
    print("=" * 50)
    
    # 检查服务器
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if response.status_code != 200:
            print(f"⚠️ 服务器健康检查失败: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return
    
    print("✅ 服务器连接正常")
    print()
    
    # 运行测试
    test_model_list()
    test_standard_model()
    test_model_mapping()
    
    print("测试完成！")

if __name__ == "__main__":
    main()