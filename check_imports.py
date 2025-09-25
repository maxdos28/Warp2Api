#!/usr/bin/env python3
"""
检查所有导入是否正常
"""

import sys

def check_import(module_name, description=""):
    try:
        __import__(module_name)
        print(f"✅ {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - {description}: {e}")
        return False
    except Exception as e:
        print(f"⚠️ {module_name} - {description}: {e}")
        return False

def main():
    print("🔍 Checking imports...")
    print("=" * 50)
    
    # 基础库检查
    print("\n📦 Basic libraries:")
    check_import("asyncio", "Async support")
    check_import("json", "JSON processing")
    check_import("time", "Time utilities")
    check_import("typing", "Type hints")
    
    # FastAPI相关
    print("\n🌐 Web framework:")
    check_import("fastapi", "FastAPI framework")
    check_import("uvicorn", "ASGI server")
    check_import("httpx", "HTTP client")
    check_import("starlette", "ASGI toolkit")
    
    # 可选优化库
    print("\n🚀 Optimization libraries (optional):")
    check_import("psutil", "System monitoring")
    check_import("brotli", "Brotli compression")
    check_import("orjson", "Fast JSON")
    check_import("ujson", "Ultra JSON")
    
    # 项目模块
    print("\n📁 Project modules:")
    check_import("warp2protobuf", "Warp protobuf module")
    check_import("warp2protobuf.core.logging", "Logging module")
    check_import("warp2protobuf.core.auth", "Auth module")
    check_import("protobuf2openai", "OpenAI compat module")
    
    # 尝试导入主要组件
    print("\n🔧 Main components:")
    try:
        from protobuf2openai.router import router
        print("✅ protobuf2openai.router - Main router")
    except Exception as e:
        print(f"❌ protobuf2openai.router: {e}")
    
    try:
        from protobuf2openai.app import app
        print("✅ protobuf2openai.app - Full app with optimizations")
    except Exception as e:
        print(f"❌ protobuf2openai.app: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Import check completed!")

if __name__ == "__main__":
    main()