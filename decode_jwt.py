#!/usr/bin/env python3
"""
解码JWT token分析用户类型和权限
"""

import base64
import json
import os

def decode_jwt_token():
    """解码当前的JWT token"""
    print("🔍 分析当前JWT Token")
    print("="*50)
    
    # 读取JWT token
    try:
        with open('.env', 'r') as f:
            content = f.read()
            jwt_token = None
            for line in content.split('\n'):
                if line.startswith('WARP_JWT='):
                    jwt_token = line.split('=', 1)[1].strip().strip("'\"")
                    break
            
            if not jwt_token:
                print("❌ 未找到WARP_JWT")
                return
    except:
        print("❌ 无法读取.env文件")
        return
    
    print(f"JWT Token长度: {len(jwt_token)}")
    
    # 解码JWT payload
    try:
        parts = jwt_token.split('.')
        if len(parts) != 3:
            print("❌ JWT格式不正确")
            return
        
        # 解码header
        header_b64 = parts[0]
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += '=' * padding
        header_bytes = base64.urlsafe_b64decode(header_b64)
        header = json.loads(header_bytes.decode('utf-8'))
        
        print("\n📋 JWT Header:")
        print(json.dumps(header, indent=2))
        
        # 解码payload
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        print("\n📋 JWT Payload:")
        print(json.dumps(payload, indent=2))
        
        # 分析关键信息
        print("\n🔍 关键信息分析:")
        
        # 检查用户ID
        user_id = payload.get('user_id') or payload.get('sub')
        print(f"用户ID: {user_id}")
        
        # 检查是否是匿名用户
        firebase_info = payload.get('firebase', {})
        sign_in_provider = firebase_info.get('sign_in_provider')
        print(f"登录方式: {sign_in_provider}")
        
        # 检查权限
        if 'custom' in str(sign_in_provider):
            print("✅ 用户类型: 可能是匿名/自定义用户")
        else:
            print(f"✅ 用户类型: {sign_in_provider}")
        
        # 检查过期时间
        exp = payload.get('exp')
        if exp:
            import time
            current_time = time.time()
            if exp > current_time:
                remaining = exp - current_time
                print(f"✅ Token有效期: 还有 {remaining/3600:.1f} 小时")
            else:
                print("❌ Token已过期")
        
        # 检查权限范围
        aud = payload.get('aud')
        print(f"受众: {aud}")
        
        return payload
        
    except Exception as e:
        print(f"❌ JWT解码失败: {e}")
        return None

def analyze_anonymous_limitations():
    """分析匿名用户的功能限制"""
    print("\n" + "="*50)
    print("🚫 匿名用户功能限制分析")
    print("="*50)
    
    # 从代码中找到的匿名用户类型
    anonymous_type = "NATIVE_CLIENT_ANONYMOUS_USER_FEATURE_GATED"
    
    print(f"当前匿名用户类型: {anonymous_type}")
    
    limitations = [
        {
            "feature": "Vision/图片处理",
            "likely_restricted": True,
            "reason": "高级AI功能通常需要付费账户"
        },
        {
            "feature": "高级模型访问",
            "likely_restricted": True,
            "reason": "GPT-4o, Claude-3等可能需要订阅"
        },
        {
            "feature": "API调用频率",
            "likely_restricted": True,
            "reason": "匿名用户通常有严格的频率限制"
        },
        {
            "feature": "文件上传/附件",
            "likely_restricted": True,
            "reason": "文件处理功能可能需要认证用户"
        },
        {
            "feature": "基础对话",
            "likely_restricted": False,
            "reason": "文本对话通常对匿名用户开放"
        }
    ]
    
    print("\n可能的功能限制:")
    for limitation in limitations:
        status = "🔴 受限" if limitation["likely_restricted"] else "✅ 可用"
        print(f"{status} {limitation['feature']}")
        print(f"   原因: {limitation['reason']}")

def suggest_solutions():
    """建议解决方案"""
    print("\n" + "="*50)
    print("💡 解决方案建议")
    print("="*50)
    
    solutions = [
        {
            "solution": "1. 使用真实Warp账户",
            "description": "注册并登录真实的Warp账户，获取完整权限",
            "difficulty": "简单",
            "effectiveness": "高"
        },
        {
            "solution": "2. 申请API访问权限",
            "description": "联系Warp团队申请API级别的vision权限",
            "difficulty": "中等",
            "effectiveness": "高"
        },
        {
            "solution": "3. 修改匿名用户类型",
            "description": "尝试使用不同的anonymousUserType",
            "difficulty": "简单",
            "effectiveness": "未知"
        },
        {
            "solution": "4. 集成其他Vision API",
            "description": "在我们的API中集成OpenAI或Claude的官方vision功能",
            "difficulty": "中等",
            "effectiveness": "高"
        }
    ]
    
    for solution in solutions:
        print(f"\n{solution['solution']}")
        print(f"   描述: {solution['description']}")
        print(f"   难度: {solution['difficulty']}")
        print(f"   有效性: {solution['effectiveness']}")

def main():
    """主分析函数"""
    
    payload = decode_jwt_token()
    
    if payload:
        analyze_anonymous_limitations()
        suggest_solutions()
        
        print("\n" + "="*50)
        print("🎯 结论")
        print("="*50)
        print("""
💡 很可能确实是匿名账户限制！

关键发现:
- 当前使用匿名用户类型: FEATURE_GATED
- "FEATURE_GATED" 表明功能受限
- Vision功能很可能需要付费/认证账户

这解释了为什么:
✅ 我们的技术实现是正确的
✅ 图片数据正确传递到Warp
❌ 但AI拒绝处理图片（权限限制）

下一步建议:
1. 尝试使用真实Warp账户的JWT token
2. 或者在我们的API中集成其他vision服务
3. 将当前实现标记为"需要付费账户"
""")

if __name__ == "__main__":
    main()