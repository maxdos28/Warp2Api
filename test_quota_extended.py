#!/usr/bin/env python3
"""扩展版额度测试 - 找到真实限制"""
import time
from datetime import datetime
from openai import OpenAI

print("="*80)
print("🧪 扩展额度测试 - 寻找真实限制")
print("="*80)

client = OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="0000"
)

# 测试配置
TEST_MESSAGE = "Say OK"
MAX_TESTS = 200  # 增加到200次
DELAY = 0.2  # 缩短间隔

print(f"\n测试配置:")
print(f"  最大测试次数: {MAX_TESTS}")
print(f"  请求间隔: {DELAY}秒")
print(f"  开始时间: {datetime.now().strftime('%H:%M:%S')}")

# 测试 claude-4.1-opus（费额度的模型）
print("\n" + "="*80)
print("🔥 测试 claude-4.1-opus (高级模型，消耗 3-5x 额度)")
print("="*80)

stats = {
    "success": 0,
    "failed": 0,
    "rate_limited": 0,
    "quota_limited": 0,
    "other_errors": 0,
    "errors": [],
    "start_time": datetime.now()
}

try:
    for i in range(1, MAX_TESTS + 1):
        print(f"[{i:3d}/{MAX_TESTS}] ", end="", flush=True)
        
        start = time.time()
        
        try:
            response = client.chat.completions.create(
                model="claude-4.1-opus",
                messages=[{"role": "user", "content": TEST_MESSAGE}],
                max_tokens=5,
                timeout=15
            )
            
            elapsed = time.time() - start
            content = response.choices[0].message.content or "(空)"
            stats["success"] += 1
            
            # 每10次显示一次详细信息
            if i % 10 == 0:
                print(f"✅ {elapsed:.1f}s [{content[:10]}...] | 累计成功: {stats['success']}")
            else:
                print(f"✅ {elapsed:.1f}s")
            
        except Exception as e:
            elapsed = time.time() - start
            error = str(e)
            stats["failed"] += 1
            
            # 分析错误类型
            error_lower = error.lower()
            
            if "429" in error or "rate limit" in error_lower or "too many" in error_lower:
                stats["rate_limited"] += 1
                print(f"🚫 速率限制! (耗时: {elapsed:.1f}s)")
                print(f"   → 在 {stats['success']} 次成功后遇到速率限制")
                stats["errors"].append(f"[{i}] Rate limited: {error[:150]}")
                
                # 遇到速率限制，等待后继续
                print(f"   ⏳ 等待30秒后继续...")
                time.sleep(30)
                continue
                
            elif "quota" in error_lower or "insufficient" in error_lower or "exceeded" in error_lower:
                stats["quota_limited"] += 1
                print(f"❌ 配额限制! (耗时: {elapsed:.1f}s)")
                print(f"   → 在 {stats['success']} 次成功后达到配额限制")
                stats["errors"].append(f"[{i}] Quota limited: {error[:150]}")
                
                # 遇到配额限制，停止测试
                print(f"\n⚠️  检测到配额限制，停止测试")
                break
                
            else:
                stats["other_errors"] += 1
                print(f"⚠️  其他错误: {error[:80]}")
                stats["errors"].append(f"[{i}] Other: {error[:150]}")
                
                # 连续3次失败就停止
                if stats["failed"] >= 3 and stats["success"] == 0:
                    print(f"\n❌ 连续失败，停止测试")
                    break
        
        # 请求间隔
        if i < MAX_TESTS:
            time.sleep(DELAY)
            
except KeyboardInterrupt:
    print(f"\n\n⚠️  用户中断测试")

# 计算统计
stats["end_time"] = datetime.now()
stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
stats["total_requests"] = stats["success"] + stats["failed"]

# 打印统计结果
print("\n" + "="*80)
print("📊 测试统计")
print("="*80)

print(f"\n⏱️  测试时长: {stats['duration']:.1f}秒 ({stats['duration']/60:.1f}分钟)")
print(f"📝 总请求数: {stats['total_requests']}")
print(f"✅ 成功: {stats['success']} ({stats['success']/stats['total_requests']*100 if stats['total_requests'] > 0 else 0:.1f}%)")
print(f"❌ 失败: {stats['failed']}")

if stats["failed"] > 0:
    print(f"\n失败分类:")
    print(f"  🚫 速率限制: {stats['rate_limited']}")
    print(f"  ❌ 配额限制: {stats['quota_limited']}")
    print(f"  ⚠️  其他错误: {stats['other_errors']}")

# 额度分析
print("\n" + "="*80)
print("💰 额度分析")
print("="*80)

if stats["quota_limited"] > 0:
    print(f"\n❌ 检测到配额限制!")
    print(f"   成功次数: {stats['success']}")
    print(f"   模型: claude-4.1-opus (消耗 ~4x 基础额度)")
    print(f"   等效基础模型使用: {stats['success'] * 4} 次")
    print(f"\n💡 结论:")
    print(f"   - 匿名账户可用 opus 约 {stats['success']} 次")
    print(f"   - 相当于基础模型 {stats['success'] * 4} 次")
    
elif stats["rate_limited"] > 0:
    print(f"\n🚫 遇到速率限制")
    print(f"   成功次数: {stats['success']}")
    print(f"   速率限制次数: {stats['rate_limited']}")
    print(f"\n💡 结论:")
    print(f"   - 请求速度过快，但配额未用完")
    print(f"   - 建议: 增加请求间隔 (如 1-2秒)")
    
elif stats["success"] == MAX_TESTS:
    print(f"\n✅ 完成所有 {MAX_TESTS} 次测试!")
    print(f"   未遇到明显限制")
    print(f"   等效基础模型使用: {stats['success'] * 4} 次")
    print(f"\n💡 结论:")
    print(f"   - 匿名账户额度 > {stats['success']} 次 opus")
    print(f"   - 即 > {stats['success'] * 4} 次基础模型")
    
else:
    print(f"\n⚠️  测试未完成")
    print(f"   成功: {stats['success']} 次")
    print(f"   其他错误: {stats['other_errors']} 次")

# 显示错误详情
if stats["errors"] and len(stats["errors"]) <= 5:
    print(f"\n❌ 错误详情:")
    for err in stats["errors"]:
        print(f"   {err}")

print("\n" + "="*80)
print(f"✅ 测试完成于: {stats['end_time'].strftime('%H:%M:%S')}")
print("="*80)
