# 调试和错误处理指南

## 概述
此文档记录了 Warp2Api 项目中的常见问题和解决方案，帮助开发者快速识别和修复问题。

## 常见问题类型

### 1. 代码重复问题

#### 问题描述
- 代码中存在大量重复的逻辑块
- 维护困难，容易出现不一致性
- 增加了出错的可能性

#### 解决方案
1. **提取公共函数**：将重复的逻辑提取为独立的辅助函数
2. **单一职责原则**：确保每个函数只负责一个特定功能
3. **代码重构**：定期审查和重构代码，消除重复

#### 实例
最近修复的 `sse_transform.py` 文件：
- 原问题：280+ 行代码中有大量重复的 SSE 事件处理逻辑
- 解决方案：提取为 `_process_sse_events()` 函数，减少到约 170 行

### 2. JWT Token 刷新问题

#### 问题描述
- Token 刷新逻辑嵌套在主要业务逻辑中
- 错误处理不统一
- 难以追踪 token 状态

#### 解决方案
1. **独立的 Token 管理**：创建专门的 token 刷新函数
2. **统一错误处理**：集中处理认证相关错误
3. **清晰的日志记录**：记录 token 状态变化

#### 实现示例
```python
async def _refresh_jwt_token(client: httpx.AsyncClient) -> bool:
    """尝试刷新JWT token，返回是否成功"""
    try:
        # 刷新逻辑
        return True
    except Exception as e:
        logger.error("[OpenAI Compat] JWT refresh attempt failed: %s", e)
        return False
```

### 3. HTTP 请求处理问题

#### 问题描述
- 重复的请求创建逻辑
- 错误状态码处理不一致
- 超时和重试机制复杂

#### 解决方案
1. **统一请求接口**：创建标准化的请求函数
2. **标准化错误处理**：定义统一的错误处理策略
3. **配置化参数**：将超时、重试等参数配置化

## 调试技巧

### 1. 分步骤调试
当面临复杂问题时：
1. 将任务分解为小步骤
2. 逐步验证每个步骤
3. 使用日志记录关键状态

### 2. 代码审查检查清单
- [ ] 是否存在重复代码？
- [ ] 函数职责是否单一？
- [ ] 错误处理是否完整？
- [ ] 日志记录是否充分？
- [ ] 参数验证是否正确？

### 3. 常用调试工具
1. **Python 日志**：使用 `logger` 记录关键信息
2. **异步调试**：注意 `async/await` 的正确使用
3. **HTTP 调试**：使用 `httpx` 的调试选项

## 预防措施

### 1. 代码规范
- 遵循 PEP 8 编码规范
- 使用类型注解
- 编写清晰的文档字符串

### 2. 测试策略
- 单元测试覆盖核心功能
- 集成测试验证完整流程
- 错误路径测试确保健壮性

### 3. 监控和告警
- 关键错误的日志监控
- 性能指标追踪
- 异常情况的及时告警

## 故障排除步骤

### 步骤 1：问题识别
1. 收集错误信息和日志
2. 确定问题影响范围
3. 分析问题根本原因

### 步骤 2：问题分析
1. 检查相关代码逻辑
2. 验证依赖关系
3. 分析数据流和控制流

### 步骤 3：解决方案制定
1. 设计修复方案
2. 评估影响范围
3. 制定测试计划

### 步骤 4：实施和验证
1. 实施修复方案
2. 执行测试验证
3. 监控运行状态

## 最佳实践

### 1. 错误处理
```python
try:
    # 主要逻辑
    result = await some_async_operation()
    return result
except SpecificError as e:
    # 特定错误处理
    logger.error("Specific error occurred: %s", e)
    # 适当的恢复或重试
except Exception as e:
    # 通用错误处理
    logger.error("Unexpected error: %s", e)
    # 确保系统稳定
```

### 2. 日志记录
```python
# 记录关键操作
logger.info("[Component] Starting operation: %s", operation_name)

# 记录错误详情
logger.error("[Component] Operation failed: %s", error_details)

# 记录调试信息
logger.debug("[Component] Debug info: %s", debug_data)
```

### 3. 函数设计
```python
async def well_designed_function(param: str) -> Optional[Result]:
    """
    清晰的函数文档说明功能、参数和返回值
    
    Args:
        param: 参数说明
        
    Returns:
        返回值说明
        
    Raises:
        SpecificError: 特定错误情况说明
    """
    # 参数验证
    if not param:
        raise ValueError("Parameter cannot be empty")
    
    try:
        # 主要逻辑
        return await process_param(param)
    except Exception as e:
        logger.error("Function failed: %s", e)
        return None
```

## 总结

通过遵循这些指导原则和最佳实践，可以显著减少代码中的错误和问题：

1. **预防**：编写清晰、模块化的代码
2. **检测**：实施全面的测试和监控
3. **修复**：系统性地分析和解决问题
4. **改进**：持续学习和优化开发流程

定期回顾和更新这些指导原则，确保它们与项目的发展保持同步。
