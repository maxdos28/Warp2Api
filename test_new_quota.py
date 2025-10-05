#!/usr/bin/env python3
"""测试恢复后的新配额"""
import time
from datetime import datetime
from openai import OpenAI

print("="*80)
print("🎯 测试新配额限制 - claude-4.1-opus")
print("="*80)

client = OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="0000"
)

print(f"\n已知信息:")
print(f"  - 刚才20次测试全部成功 ✅")
print(f"  - 配额已恢复")
print(f"  - 现在测试新的配额限制\n")
print(f"开始时间: {datetime.now().strftime('%H:%M:%S')}\n")

MAX_TESTS = 300
stats = {"success": 0, "failed": 0, "start": datetime.now()}

for i in range(1, MAX_TESTS + 1):
    # 每50次显示进度
    if i % 50 == 1 and i > 1:
        print(f"\n{'='*80}")
        print(f"进度: {i-1} 次完成，继续测试...")
        print(f"{'='*80}\n")
    
    # 显示格式：紧凑型
    if i % 10 == 1:
        print(f"[{i:3d}-{min(i+9, MAX_TESTS):3d}] ", end="", flush=True)
    
    try:
        start = time.time()
        response = client.chat.completions.create(
            model="claude-4.1-opus",
            messages=[{"role": "user", "content": "OK?"}],
            max_tokens=5,
            timeout=15
        )
        
        elapsed = time.time() - start
        stats["success"] += 1
        
        # 紧凑显示
        if elapsed < 1:
            print("✅", end="", flush=True)
        else:
            print(f"✅{elapsed:.0f}", end="", flush=True)
        
        # 每10次换行
        if i % 10 == 0:
            print(f" | {stats['success']}")
        
    except Exception as e:
        error = str(e)
        stats["failed"] += 1
        
        if "429" in error and ("quota" in error.lower() or "remaining" in error.lower()):
            print(f"\n\n❌ 配额用尽!")
            print(f"   成功次数: {stats['success']}")
            print(f"   错误信息: {error[:150]}")
            break
        elif "429" in error:
            print(f"\n🚫 速率限制，等待5秒...")
            time.sleep(5)
        else:
            print(f"\n⚠️  {error[:60]}")
            if stats["failed"] >= 3:
                break
    
    time.sleep(0.2)

# 统计
stats["end"] = datetime.now()
stats["duration"] = (stats["end"] - stats["start"]).total_seconds()

print(f"\n\n{'='*80}")
print("📊 最终结果")
print("="*80)

print(f"\n⏱️  测试时长: {stats['duration']:.1f}秒")
print(f"✅ 成功: {stats['success']} 次")
print(f"❌ 失败: {stats['failed']} 次")
print(f"💰 等效基础模型: {stats['success'] * 4} 次")

if stats["failed"] > 0:
    print(f"\n⚠️  在第 {stats['success']} 次后遇到限制")
    print(f"   新配额: ~{stats['success']} 次 opus")
else:
    print(f"\n✅ 完成所有 {stats['success']} 次测试")
    print(f"   新配额 > {stats['success']} 次 opus")

print(f"\n{'='*80}")
