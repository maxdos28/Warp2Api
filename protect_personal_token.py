#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保护个人 WARP_REFRESH_TOKEN 不被匿名 token 覆盖的脚本
"""

import os
from pathlib import Path
from dotenv import load_dotenv, set_key

def protect_personal_token():
    """启用个人 token 保护"""
    env_path = Path(".env")
    
    # 创建 .env 文件（如果不存在）
    if not env_path.exists():
        env_path.touch()
    
    # 设置保护标志
    set_key(str(env_path), "WARP_PROTECT_PERSONAL_TOKEN", "true")
    print("✅ 已启用个人 token 保护")
    print("   现在系统不会自动覆盖您的 WARP_REFRESH_TOKEN")

def unprotect_personal_token():
    """禁用个人 token 保护"""
    env_path = Path(".env")
    
    if env_path.exists():
        set_key(str(env_path), "WARP_PROTECT_PERSONAL_TOKEN", "false")
    print("✅ 已禁用个人 token 保护")
    print("   系统现在可以自动更新 WARP_REFRESH_TOKEN")

def set_personal_token(token: str):
    """设置个人 refresh token"""
    env_path = Path(".env")
    
    # 创建 .env 文件（如果不存在）
    if not env_path.exists():
        env_path.touch()
    
    set_key(str(env_path), "WARP_REFRESH_TOKEN", token)
    print("✅ 已设置个人 WARP_REFRESH_TOKEN")

def show_current_status():
    """显示当前状态"""
    load_dotenv()
    
    refresh_token = os.getenv("WARP_REFRESH_TOKEN", "未设置")
    protect_flag = os.getenv("WARP_PROTECT_PERSONAL_TOKEN", "false")
    
    print("=" * 60)
    print("当前 WARP Token 状态:")
    print("=" * 60)
    print(f"WARP_REFRESH_TOKEN: {refresh_token[:20] + '...' if len(refresh_token) > 20 else refresh_token}")
    print(f"个人 Token 保护: {'✅ 已启用' if protect_flag.lower() == 'true' else '❌ 未启用'}")
    print("=" * 60)

def main():
    print("WARP 个人 Token 保护工具")
    print("=" * 60)
    
    while True:
        print("\n请选择操作:")
        print("1. 查看当前状态")
        print("2. 启用个人 token 保护")
        print("3. 禁用个人 token 保护") 
        print("4. 设置个人 refresh token")
        print("5. 退出")
        
        choice = input("\n请输入选项 (1-5): ").strip()
        
        if choice == "1":
            show_current_status()
        elif choice == "2":
            protect_personal_token()
        elif choice == "3":
            unprotect_personal_token()
        elif choice == "4":
            token = input("请输入您的个人 WARP_REFRESH_TOKEN: ").strip()
            if token:
                set_personal_token(token)
                # 同时启用保护
                protect_personal_token()
            else:
                print("❌ Token 不能为空")
        elif choice == "5":
            print("再见！")
            break
        else:
            print("❌ 无效选项，请重试")

if __name__ == "__main__":
    main()