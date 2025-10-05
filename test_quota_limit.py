#!/usr/bin/env python3
"""测试匿名账户在 claude-4.1-opus 模型上的额度限制"""
import time
from datetime import datetime
from openai import OpenAI
import json

print("="*80)
print("🧪 匿名账户额度测试 - claude-4.1-opus")
print("="*80)

client = OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="0000"  # 匿名token
)

# 测试配置
MODEL = "claude-4.1-opus"
TEST_MESSAGE = "Hello, this is a quota test. Please respond with OK."
MAX_TESTS = 100  # 最多测试次数
DELAY_BETWEEN_REQUESTS = 0.5  # 请求间隔（秒）

# 统计数据
stats = {
    "total_requests": 0,
    "successful": 0,
    "failed": 0,
    "rate_limited": 0,
    "errors": [],
    "start_time": datetime.now(),
    "response_times": []
}

print(f"\n测试配置:")
print(f"  模型: {MODEL}")
print(f"  最大测试次数: {MAX_TESTS}")
print(f"  请求间隔: {DELAY_BETWEEN_REQUESTS}秒")
print(f"\n开始测试...\n")

try:
    for i in range(1, MAX_TESTS + 1):
        stats["total_requests"] = i
        
        print(f"[{i}/{MAX_TESTS}] ", end="", flush=True)
        
        request_start = time.time()
        
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "user", "content": TEST_MESSAGE}
                ],
                max_tokens=50,
                timeout=30
            )
            
            request_time = time.time() - request_start
            stats["response_times"].append(request_time)
            
            # 成功
            stats["successful"] += 1
            content = response.choices[0].message.content
            print(f"✅ 成功 (耗时: {request_time:.2f}s) - {content[:30]}...")
            
        except Exception as e:
            request_time = time.time() - request_start
            error_msg = str(e)
            
            # 检查错误类型
            if "429" in error_msg or "rate" in error_msg.lower():
                stats["rate_limited"] += 1
                print(f"🚫 速率限制 (耗时: {request_time:.2f}s)")
                print(f"   错误: {error_msg[:100]}")
                
                # 遇到速率限制，停止测试
                print(f"\n⚠️ 遇到速率限制，停止测试！")
                break
                
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                stats["failed"] += 1
                print(f"❌ 配额限制 (耗时: {request_time:.2f}s)")
                print(f"   错误: {error_msg[:100]}")
                
                # 遇到配额限制，停止测试
                print(f"\n⚠️ 遇到配额限制，停止测试！")
                break
                
            else:
                stats["failed"] += 1
                print(f"❌ 其他错误 (耗时: {request_time:.2f}s)")
                print(f"   错误: {error_msg[:100]}")
            
            stats["errors"].append({
                "request_num": i,
                "error": error_msg[:200],
                "time": datetime.now().isoformat()
            })
        
        # 请求间隔
        if i < MAX_TESTS:
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
except KeyboardInterrupt:
    print(f"\n\n⚠️ 用户中断测试")

# 计算统计
stats["end_time"] = datetime.now()
stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
stats["success_rate"] = (stats["successful"] / stats["total_requests"] * 100) if stats["total_requests"] > 0 else 0

if stats["response_times"]:
    stats["avg_response_time"] = sum(stats["response_times"]) / len(stats["response_times"])
    stats["min_response_time"] = min(stats["response_times"])
    stats["max_response_time"] = max(stats["response_times"])
else:
    stats["avg_response_time"] = 0
    stats["min_response_time"] = 0
    stats["max_response_time"] = 0

# 打印统计结果
print("\n" + "="*80)
print("📊 测试统计")
print("="*80)

print(f"\n⏱️  测试时长: {stats['duration']:.2f}秒")
print(f"📝 总请求数: {stats['total_requests']}")
print(f"✅ 成功: {stats['successful']} ({stats['success_rate']:.1f}%)")
print(f"❌ 失败: {stats['failed']}")
print(f"🚫 速率限制: {stats['rate_limited']}")

if stats["response_times"]:
    print(f"\n⚡ 响应时间:")
    print(f"   平均: {stats['avg_response_time']:.2f}秒")
    print(f"   最快: {stats['min_response_time']:.2f}秒")
    print(f"   最慢: {stats['max_response_time']:.2f}秒")

if stats["errors"]:
    print(f"\n❌ 错误详情:")
    for error in stats["errors"][:5]:  # 只显示前5个
        print(f"   请求 #{error['request_num']}: {error['error'][:80]}...")
    if len(stats["errors"]) > 5:
        print(f"   ... 还有 {len(stats["errors"]) - 5} 个错误")

# 分析额度
print("\n" + "="*80)
print("💡 额度分析")
print("="*80)

if stats["rate_limited"] > 0:
    print(f"\n🚫 检测到速率限制:")
    print(f"   在第 {stats['successful']} 次请求后被限制")
    print(f"   建议: 降低请求频率或等待一段时间")
elif stats["failed"] > 0 and any("quota" in e["error"].lower() for e in stats["errors"]):
    print(f"\n❌ 检测到配额限制:")
    print(f"   在第 {stats['successful']} 次请求后达到配额")
    print(f"   匿名账户可能的限制: {stats['successful']} 次请求")
elif stats["successful"] == MAX_TESTS:
    print(f"\n✅ 完成所有 {MAX_TESTS} 次测试:")
    print(f"   未遇到明显限制")
    print(f"   匿名账户额度 > {MAX_TESTS} 次请求")
else:
    print(f"\n⚠️ 测试未完成:")
    print(f"   成功 {stats['successful']} 次后停止")
    print(f"   需要更多测试确定确切限制")

# 保存结果
result_file = f"quota_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(result_file, 'w', encoding='utf-8') as f:
    # 转换datetime为字符串
    save_stats = stats.copy()
    save_stats["start_time"] = save_stats["start_time"].isoformat()
    save_stats["end_time"] = save_stats["end_time"].isoformat()
    json.dump(save_stats, f, indent=2, ensure_ascii=False)

print(f"\n💾 详细结果已保存到: {result_file}")

print("\n" + "="*80)
print("✅ 测试完成")
print("="*80)
