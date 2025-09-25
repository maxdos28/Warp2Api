#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试个人 token 保护机制
"""

import os
from pathlib import Path
from dotenv import load_dotenv, set_key

def test_protection():
    """测试保护机制"""
    print("=== 测试个人 Token 保护机制 ===")
    
    # 加载当前环境变量
    load_dotenv()
    
    current_token = os.getenv("WARP_REFRESH_TOKEN", "未设置")
    protect_flag = os.getenv("WARP_PROTECT_PERSONAL_TOKEN", "false")
    
    print(f"当前 WARP_REFRESH_TOKEN: {current_token[:20] + '...' if len(current_token) > 20 else current_token}")
    print(f"保护标志: {protect_flag}")
    
    if protect_flag.lower() != "true":
        print("\n❌ 保护未启用！")
        print("请运行以下命令启用保护:")
        print("python3 protect_personal_token.py")
        return False
    else:
        print("\n✅ 保护已启用")
        return True

def enable_protection_quick():
    """快速启用保护"""
    env_path = Path(".env")
    
    if not env_path.exists():
        env_path.touch()
    
    set_key(str(env_path), "WARP_PROTECT_PERSONAL_TOKEN", "true")
    print("✅ 已快速启用个人 token 保护")

if __name__ == "__main__":
    if not test_protection():
        choice = input("\n是否现在启用保护？(y/N): ").strip().lower()
        if choice == 'y':
            enable_protection_quick()
            print("保护已启用，请重启服务器以生效")
        else:
            print("请手动启用保护后重试")