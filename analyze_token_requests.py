#!/usr/bin/env python3
"""
分析匿名token申请的原因和模式
"""

import re
import os
from collections import defaultdict, Counter
from datetime import datetime

def analyze_token_requests():
    print("🔍 分析匿名Token申请模式")
    print("=" * 60)
    
    # 收集所有申请记录
    requests = []
    sources = defaultdict(list)
    
    # 遍历所有日志文件
    log_dir = "logs"
    for filename in os.listdir(log_dir):
        if filename.endswith(".log"):
            filepath = os.path.join(log_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines):
                    if "acquire_anonymous_access_token" in line and "INFO" in line:
                        # 提取时间戳
                        time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if time_match:
                            timestamp = time_match.group(1)
                            
                            # 查找前面的上下文（触发原因）
                            context_lines = []
                            for j in range(max(0, i-10), i):
                                if j < len(lines):
                                    context_lines.append(lines[j].strip())
                            
                            # 分析触发源
                            trigger_source = analyze_trigger_source(context_lines)
                            
                            requests.append({
                                'timestamp': timestamp,
                                'file': filename,
                                'line_num': i,
                                'trigger': trigger_source,
                                'context': context_lines[-3:] if context_lines else []
                            })
                            
                            sources[trigger_source].append(timestamp)
                            
            except Exception as e:
                print(f"⚠️ Error reading {filename}: {e}")
    
    print(f"📊 总计发现 {len(requests)} 次匿名token申请")
    print()
    
    # 按触发源分组统计
    print("📋 按触发源分类：")
    for source, timestamps in sources.items():
        print(f"  {source}: {len(timestamps)} 次")
        if len(timestamps) <= 5:
            for ts in timestamps:
                print(f"    - {ts}")
        else:
            print(f"    - 首次: {timestamps[0]}")
            print(f"    - 末次: {timestamps[-1]}")
            print(f"    - 中间省略 {len(timestamps)-2} 次")
    print()
    
    # 时间分布分析
    print("⏰ 时间分布分析：")
    time_buckets = defaultdict(int)
    for req in requests:
        # 提取小时:分钟
        time_part = req['timestamp'].split()[1][:5]  # HH:MM
        time_buckets[time_part] += 1
    
    # 显示最频繁的时间段
    sorted_times = sorted(time_buckets.items(), key=lambda x: x[1], reverse=True)
    print("  最频繁的申请时间段：")
    for time_slot, count in sorted_times[:10]:
        print(f"    {time_slot}: {count} 次")
    print()
    
    # 查找连续申请
    print("🔄 连续申请检测：")
    consecutive_groups = find_consecutive_requests(requests)
    for group in consecutive_groups:
        if len(group) > 3:
            print(f"  连续申请组 ({len(group)} 次):")
            print(f"    时间范围: {group[0]['timestamp']} - {group[-1]['timestamp']}")
            print(f"    触发源: {group[0]['trigger']}")
    
    return requests, sources

def analyze_trigger_source(context_lines):
    """分析触发源"""
    context_text = " ".join(context_lines).lower()
    
    # 定义触发模式
    triggers = {
        "服务器重启": ["server starting", "startup", "started server", "application startup"],
        "手动测试": ["test", "testing", "curl", "check", "verify"],
        "重启脚本": ["restart", "重启", "service restart", "restart_services"],
        "API调用失败": ["failed", "error", "http error", "配额", "quota"],
        "Cline请求": ["fs/js", "cline", "user-agent", "chat completions"],
        "性能测试": ["performance", "benchmark", "load test"],
        "初始化": ["initialize", "warmup", "init", "warming up"],
        "配额检查": ["quota", "配额", "limit", "exceeded"],
        "未知原因": []
    }
    
    for trigger_name, patterns in triggers.items():
        for pattern in patterns:
            if pattern in context_text:
                return trigger_name
    
    return "未知原因"

def find_consecutive_requests(requests):
    """查找连续申请"""
    if not requests:
        return []
    
    # 按时间排序
    sorted_requests = sorted(requests, key=lambda x: x['timestamp'])
    
    consecutive_groups = []
    current_group = [sorted_requests[0]]
    
    for i in range(1, len(sorted_requests)):
        current_req = sorted_requests[i]
        prev_req = sorted_requests[i-1]
        
        # 解析时间戳
        try:
            current_time = datetime.strptime(current_req['timestamp'], '%Y-%m-%d %H:%M:%S')
            prev_time = datetime.strptime(prev_req['timestamp'], '%Y-%m-%d %H:%M:%S')
            
            # 如果间隔小于5分钟，认为是连续的
            time_diff = (current_time - prev_time).total_seconds()
            if time_diff < 300:  # 5分钟
                current_group.append(current_req)
            else:
                if len(current_group) > 1:
                    consecutive_groups.append(current_group)
                current_group = [current_req]
        except:
            continue
    
    if len(current_group) > 1:
        consecutive_groups.append(current_group)
    
    return consecutive_groups

if __name__ == "__main__":
    requests, sources = analyze_token_requests()
    
    print("🎯 结论和建议：")
    print()
    
    total_requests = len(requests)
    if total_requests > 50:
        print(f"⚠️ 申请次数过多 ({total_requests} 次)，可能的原因：")
        
        # 分析主要原因
        main_sources = sorted(sources.items(), key=lambda x: len(x[1]), reverse=True)
        for source, timestamps in main_sources[:3]:
            percentage = len(timestamps) / total_requests * 100
            print(f"  - {source}: {len(timestamps)} 次 ({percentage:.1f}%)")
        
        print()
        print("💡 优化建议：")
        print("  1. 减少不必要的服务重启")
        print("  2. 增加申请前的检查逻辑")
        print("  3. 实现申请频率控制")
        print("  4. 使用缓存减少重复申请")
    else:
        print("✅ 申请次数在正常范围内")