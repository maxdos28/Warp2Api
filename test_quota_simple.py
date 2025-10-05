#!/usr/bin/env python3
"""简化版额度测试 - 快速验证"""
import time
from datetime import datetime
from openai import OpenAI

print("="*80)
print("🧪 快速额度测试 - claude-4.1-opus vs claude-4-sonnet")
print("="*80)

client = OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="0000"
)

# 测试配置
TEST_MESSAGE = "Hello! Please respond with just 'OK'."
MAX_TESTS = 10  # 快速测试10次
DELAY = 0.3

models_to_test = [
    ("claude-4-sonnet", "基础模型 (1x额度)"),
    ("claude-4.1-opus", "高级模型 (4x额度)")
]

results = {}

for model, desc in models_to_test:
    print(f"\n{'='*80}")
    print(f"测试模型: {model} - {desc}")
    print(f"{'='*80}\n")
    
    stats = {"success": 0, "failed": 0, "errors": []}
    
    for i in range(1, MAX_TESTS + 1):
        print(f"[{i}/{MAX_TESTS}] ", end="", flush=True)
        
        try:
            start = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": TEST_MESSAGE}],
                max_tokens=10,
                timeout=20
            )
            
            elapsed = time.time() - start
            content = response.choices[0].message.content
            stats["success"] += 1
            print(f"✅ {elapsed:.2f}s - {content[:20]}")
            
        except Exception as e:
            elapsed = time.time() - start
            error = str(e)
            stats["failed"] += 1
            stats["errors"].append(error[:100])
            
            if "429" in error or "rate" in error.lower():
                print(f"🚫 速率限制! {elapsed:.2f}s")
                break
            elif "quota" in error.lower() or "limit" in error.lower():
                print(f"❌ 额度限制! {elapsed:.2f}s")
                break
            else:
                print(f"❌ 错误: {error[:50]}")
        
        if i < MAX_TESTS:
            time.sleep(DELAY)
    
    results[model] = stats
    print(f"\n📊 {model}: {stats['success']} 成功, {stats['failed']} 失败")

# 对比结果
print("\n" + "="*80)
print("📊 对比结果")
print("="*80)

for model, desc in models_to_test:
    stats = results[model]
    success_rate = stats['success'] / MAX_TESTS * 100
    print(f"\n{model} ({desc}):")
    print(f"  成功: {stats['success']}/{MAX_TESTS} ({success_rate:.0f}%)")
    print(f"  失败: {stats['failed']}")
    if stats['errors']:
        print(f"  首个错误: {stats['errors'][0][:60]}...")

print("\n" + "="*80)
print("💡 结论")
print("="*80)

sonnet_success = results["claude-4-sonnet"]["success"]
opus_success = results["claude-4.1-opus"]["success"]

if sonnet_success > 0 and opus_success > 0:
    print("\n✅ 两个模型都可以使用")
    print(f"   - claude-4-sonnet: {sonnet_success} 次成功")
    print(f"   - claude-4.1-opus: {opus_success} 次成功")
    print(f"\n💡 记住: opus 消耗约 3-5x 额度")
    print(f"   实际使用中，用 {opus_success} 次 opus ≈ 用 {opus_success*4} 次 sonnet")
elif sonnet_success > 0:
    print("\n⚠️ 只有基础模型可用")
    print("   opus 可能达到额度限制或不可用")
else:
    print("\n❌ 两个模型都不可用")
    print("   可能是额度耗尽或网络问题")

print("\n" + "="*80)
