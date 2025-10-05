#!/usr/bin/env python3
"""重新测试opus - 验证配额状态"""
import time
from datetime import datetime
from openai import OpenAI

print("="*80)
print("🔄 重新测试 claude-4.1-opus - 验证配额恢复")
print("="*80)

client = OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="0000"
)

print(f"\n当前时间: {datetime.now().strftime('%H:%M:%S')}")
print(f"距上次测试: ~5分钟")
print(f"\n开始测试...\n")

# 测试配置
MAX_TESTS = 20
TEST_MESSAGE = "Hello, please say OK"

stats = {
    "success": 0,
    "quota_error": 0,
    "rate_error": 0,
    "other_error": 0,
    "first_error_at": None
}

for i in range(1, MAX_TESTS + 1):
    print(f"[{i:2d}/{MAX_TESTS}] ", end="", flush=True)
    
    try:
        start = time.time()
        response = client.chat.completions.create(
            model="claude-4.1-opus",
            messages=[{"role": "user", "content": TEST_MESSAGE}],
            max_tokens=10,
            timeout=20
        )
        
        elapsed = time.time() - start
        content = response.choices[0].message.content or "(空)"
        stats["success"] += 1
        
        print(f"✅ {elapsed:.2f}s - {content[:30]}")
        
    except Exception as e:
        elapsed = time.time() - start
        error = str(e)
        
        if stats["first_error_at"] is None:
            stats["first_error_at"] = i
        
        # 分析错误类型
        if "429" in error and ("quota" in error.lower() or "remaining" in error.lower()):
            stats["quota_error"] += 1
            print(f"❌ 配额用尽 ({elapsed:.2f}s)")
            print(f"   错误: {error[:120]}")
            
            if i == 1:
                print(f"\n⚠️  配额仍然用尽，未恢复")
                print(f"   说明: 匿名账户配额可能需要更长时间恢复")
                print(f"   或: 需要手动申请新的匿名账户")
            
            # 前3次失败就停止
            if i <= 3:
                print(f"\n⏹️  停止测试")
                break
                
        elif "429" in error or "rate" in error.lower():
            stats["rate_error"] += 1
            print(f"🚫 速率限制 ({elapsed:.2f}s)")
            print(f"   等待10秒后继续...")
            time.sleep(10)
            
        else:
            stats["other_error"] += 1
            print(f"⚠️  其他错误 ({elapsed:.2f}s): {error[:80]}")
    
    if i < MAX_TESTS and stats["success"] > 0:
        time.sleep(0.3)

# 统计
print("\n" + "="*80)
print("📊 测试结果")
print("="*80)

total = stats["success"] + stats["quota_error"] + stats["rate_error"] + stats["other_error"]
print(f"\n总请求数: {total}")
print(f"✅ 成功: {stats['success']}")
print(f"❌ 配额错误: {stats['quota_error']}")
print(f"🚫 速率错误: {stats['rate_error']}")
print(f"⚠️  其他错误: {stats['other_error']}")

if stats["first_error_at"]:
    print(f"\n首次错误位置: 第 {stats['first_error_at']} 次请求")

print("\n" + "="*80)
print("💡 分析")
print("="*80)

if stats["success"] > 0:
    print(f"\n✅ 配额已恢复!")
    print(f"   新的成功次数: {stats['success']}")
    print(f"   说明: 匿名账户可能")
    print(f"   - 时间自动刷新")
    print(f"   - 或后台申请成功")
elif stats["quota_error"] > 0:
    print(f"\n❌ 配额仍然用尽")
    print(f"   距上次: ~5分钟")
    print(f"   说明: 配额恢复需要更长时间")
    print(f"   建议: ")
    print(f"   - 等待更长时间 (如1小时)")
    print(f"   - 或使用基础模型 (sonnet)")
    print(f"   - 或手动申请新匿名账户")
else:
    print(f"\n⚠️  其他问题")
    print(f"   需要检查服务器状态")

print("\n" + "="*80)
