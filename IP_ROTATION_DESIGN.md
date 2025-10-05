# 🌐 多出口IP利用方案

## 📊 当前情况

### 服务器配置
```
出口IP数量: 8个
当前使用: 单一IP（默认路由）
```

### Warp限制
```
速率限制: ~10秒内最多2次匿名申请
限制维度: 推测基于IP
```

---

## 💡 优化方案

### 方案A: IP轮换请求（推荐）⭐⭐⭐⭐⭐

**原理**:
```
每次申请匿名token时轮换不同的出口IP
避免单IP触发速率限制
```

**实现方式**:

1. **配置环境变量**
```bash
# .env
OUTBOUND_IPS=1.2.3.4,1.2.3.5,1.2.3.6,1.2.3.7,1.2.3.8,1.2.3.9,1.2.3.10,1.2.3.11
```

2. **修改 `auth.py`**
```python
import random
import os

def get_random_outbound_ip():
    """获取随机出口IP"""
    ips = os.getenv("OUTBOUND_IPS", "").split(",")
    ips = [ip.strip() for ip in ips if ip.strip()]
    return random.choice(ips) if ips else None

async def _create_anonymous_user() -> dict:
    # 选择随机IP
    source_ip = get_random_outbound_ip()
    
    # 配置httpx使用特定出口IP
    transport = httpx.AsyncHTTPTransport(
        local_address=source_ip if source_ip else "0.0.0.0"
    )
    
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0), 
        trust_env=True,
        transport=transport  # 使用指定IP
    ) as client:
        resp = await client.post(_ANON_GQL_URL, headers=headers, json=body)
        # ...
```

**效果**:
```
申请1 → IP1 → ✅ 成功
申请2 → IP2 → ✅ 成功
申请3 → IP3 → ✅ 成功（不受IP1的速率限制）
...
申请16 → IP8 → ✅ 成功

理论容量: 8个IP × 2次/10秒 = 16次/10秒
```

---

### 方案B: IP池管理（最优）⭐⭐⭐⭐⭐

**原理**:
```
维护每个IP的使用状态
智能选择可用的IP
避免所有IP被同时限制
```

**实现**:
```python
from dataclasses import dataclass
from typing import Dict, Optional
import time

@dataclass
class IPStatus:
    ip: str
    last_used: float = 0
    use_count: int = 0  # 最近10秒内使用次数
    
class IPPool:
    def __init__(self, ips: list):
        self.ips = {ip: IPStatus(ip) for ip in ips}
        self.cooldown = 10  # 10秒冷却期
        self.max_uses_per_window = 2
    
    def get_available_ip(self) -> Optional[str]:
        """获取可用的IP"""
        now = time.time()
        
        # 清理过期的使用记录
        for status in self.ips.values():
            if now - status.last_used > self.cooldown:
                status.use_count = 0
        
        # 优先选择未使用或使用次数少的IP
        available = [
            s for s in self.ips.values() 
            if s.use_count < self.max_uses_per_window
        ]
        
        if not available:
            # 所有IP都被限制，返回冷却时间最长的
            return min(self.ips.values(), key=lambda s: s.last_used).ip
        
        # 返回使用次数最少的IP
        best = min(available, key=lambda s: s.use_count)
        return best.ip
    
    def mark_used(self, ip: str):
        """标记IP已使用"""
        if ip in self.ips:
            status = self.ips[ip]
            status.last_used = time.time()
            status.use_count += 1

# 全局IP池
_ip_pool = None

def init_ip_pool():
    global _ip_pool
    ips = os.getenv("OUTBOUND_IPS", "").split(",")
    ips = [ip.strip() for ip in ips if ip.strip()]
    if ips:
        _ip_pool = IPPool(ips)
        logger.info(f"IP池已初始化: {len(ips)} 个IP")

async def _create_anonymous_user() -> dict:
    global _ip_pool
    if _ip_pool is None:
        init_ip_pool()
    
    # 获取可用IP
    source_ip = _ip_pool.get_available_ip() if _ip_pool else None
    
    if source_ip:
        logger.info(f"使用出口IP: {source_ip}")
        transport = httpx.AsyncHTTPTransport(local_address=source_ip)
    else:
        transport = None
    
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0), 
            trust_env=True,
            transport=transport
        ) as client:
            resp = await client.post(_ANON_GQL_URL, headers=headers, json=body)
            # ...
        
        # 标记IP已使用
        if _ip_pool and source_ip:
            _ip_pool.mark_used(source_ip)
        
        return data
    except Exception as e:
        # 如果失败，不计入使用次数
        raise
```

**效果**:
```
智能调度:
- 自动选择最空闲的IP
- 避免触发速率限制
- 最大化并发能力

容量提升:
- 短时间内: 16次（8IP × 2次）
- 持续使用: 无限制（轮换使用）
```

---

### 方案C: 简单轮询（快速实现）⭐⭐⭐

**实现**:
```python
_ip_index = 0
_outbound_ips = []

def get_next_ip():
    global _ip_index, _outbound_ips
    if not _outbound_ips:
        ips = os.getenv("OUTBOUND_IPS", "").split(",")
        _outbound_ips = [ip.strip() for ip in ips if ip.strip()]
    
    if not _outbound_ips:
        return None
    
    ip = _outbound_ips[_ip_index]
    _ip_index = (_ip_index + 1) % len(_outbound_ips)
    return ip
```

---

## 📊 效果对比

### 单IP（当前）
```
容量: 2次/10秒
配额耗尽: 需等待10-60秒
适用: 低频使用
```

### 8个IP（优化后）
```
容量: 16次/10秒
配额耗尽: 极难触发
适用: 高频使用、生产环境
```

---

## 🚀 实施建议

### 第1步: 测试IP可用性
```bash
# 测试每个IP是否能访问Warp API
curl --interface 1.2.3.4 https://app.warp.dev/graphql/v2
curl --interface 1.2.3.5 https://app.warp.dev/graphql/v2
# ... 测试所有8个IP
```

### 第2步: 配置环境变量
```bash
echo 'OUTBOUND_IPS=1.2.3.4,1.2.3.5,1.2.3.6,1.2.3.7,1.2.3.8,1.2.3.9,1.2.3.10,1.2.3.11' >> .env
```

### 第3步: 修改代码
```bash
# 实现方案B（推荐）或方案C（简单）
```

### 第4步: 测试验证
```python
# 连续申请10次，验证是否使用了不同IP
# 验证是否避免了429限制
```

---

## 💰 收益分析

### 容量提升
```
申请速率: 8倍提升
并发能力: 16次/10秒
稳定性: 大幅提升
```

### 配额管理
```
当前: 200次opus/账户
优化后: 200次 × 8IP = 1600次/轮
实际: 几乎无限（不断申请新账户）
```

### 可靠性
```
单点故障: 从1个IP → 8个IP
容错能力: 提升8倍
```

---

## 🎯 最终推荐

### 推荐方案: B（IP池管理）

**理由**:
```
✅ 智能调度
✅ 避免浪费
✅ 最大化容量
✅ 可监控统计
```

**实施复杂度**: 中等
**收益**: 最高
**适用场景**: 生产环境、高并发

### 快速方案: C（简单轮询）

**理由**:
```
✅ 实现简单
✅ 快速上线
✅ 效果明显
```

**实施复杂度**: 低
**收益**: 高
**适用场景**: 快速验证、小规模

---

## 📋 注意事项

### Linux系统配置

**确保每个IP都已配置**:
```bash
ip addr show

# 应该看到8个IP地址
```

**测试绑定**:
```bash
curl --interface 1.2.3.4 https://httpbin.org/ip
# 应该返回指定的IP
```

### 代码兼容性

**httpx local_address支持**:
```python
# 需要 httpx >= 0.23.0
pip install -U httpx
```

### 监控建议

**记录IP使用情况**:
```python
logger.info(f"匿名申请使用IP: {source_ip}")
logger.info(f"IP池状态: {_ip_pool.get_status()}")
```

---

## 🎉 预期效果

### 优化前
```
单IP限制: 2次/10秒
配额耗尽: 经常等待
适用场景: 测试、个人使用
```

### 优化后
```
多IP容量: 16次/10秒
配额耗尽: 几乎不会
适用场景: 生产、高并发、商业化
```

**提升倍数: 8倍！** 🚀
