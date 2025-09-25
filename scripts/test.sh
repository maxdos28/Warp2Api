#!/bin/bash

# Warp2API Go - 测试脚本
# 测试API接口功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    # 检查桥接服务器
    if curl -s http://127.0.0.1:28888/healthz > /dev/null 2>&1; then
        log_success "桥接服务器: 运行中"
    else
        log_error "桥接服务器: 未运行"
        return 1
    fi
    
    # 检查主服务器
    if curl -s http://127.0.0.1:28889/healthz > /dev/null 2>&1; then
        log_success "主服务器: 运行中"
    else
        log_error "主服务器: 未运行"
        return 1
    fi
}

# 测试健康检查
test_health() {
    log_info "测试健康检查端点..."
    
    # 测试桥接服务器健康检查
    if curl -s http://127.0.0.1:28888/healthz | grep -q "healthy"; then
        log_success "桥接服务器健康检查: 通过"
    else
        log_error "桥接服务器健康检查: 失败"
        return 1
    fi
    
    # 测试主服务器健康检查
    if curl -s http://127.0.0.1:28889/healthz | grep -q "healthy"; then
        log_success "主服务器健康检查: 通过"
    else
        log_error "主服务器健康检查: 失败"
        return 1
    fi
}

# 测试模型列表
test_models() {
    log_info "测试模型列表端点..."
    
    response=$(curl -s http://127.0.0.1:28889/v1/models)
    if echo "$response" | grep -q "claude-4-sonnet"; then
        log_success "模型列表: 通过"
        echo "可用模型:"
        echo "$response" | jq -r '.data[].id' 2>/dev/null || echo "$response"
    else
        log_error "模型列表: 失败"
        return 1
    fi
}

# 测试OpenAI API
test_openai_api() {
    log_info "测试OpenAI Chat Completions API..."
    
    # 准备测试数据
    test_data='{
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "max_tokens": 100
    }'
    
    # 发送请求
    response=$(curl -s -X POST http://127.0.0.1:28889/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d "$test_data")
    
    if echo "$response" | grep -q "choices"; then
        log_success "OpenAI API: 通过"
        echo "响应示例:"
        echo "$response" | jq -r '.choices[0].message.content' 2>/dev/null || echo "$response"
    else
        log_error "OpenAI API: 失败"
        echo "错误响应: $response"
        return 1
    fi
}

# 测试Claude API
test_claude_api() {
    log_info "测试Claude Messages API..."
    
    # 准备测试数据
    test_data='{
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ]
    }'
    
    # 发送请求
    response=$(curl -s -X POST http://127.0.0.1:28889/v1/messages \
        -H "Content-Type: application/json" \
        -d "$test_data")
    
    if echo "$response" | grep -q "content"; then
        log_success "Claude API: 通过"
        echo "响应示例:"
        echo "$response" | jq -r '.content[0].text' 2>/dev/null || echo "$response"
    else
        log_error "Claude API: 失败"
        echo "错误响应: $response"
        return 1
    fi
}

# 测试流式响应
test_streaming() {
    log_info "测试流式响应..."
    
    # 准备测试数据
    test_data='{
        "model": "claude-4-sonnet",
        "messages": [
            {"role": "user", "content": "Tell me a short story"}
        ],
        "stream": true
    }'
    
    # 发送流式请求
    response=$(curl -s -X POST http://127.0.0.1:28889/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d "$test_data" | head -5)
    
    if echo "$response" | grep -q "data:"; then
        log_success "流式响应: 通过"
        echo "流式响应示例:"
        echo "$response"
    else
        log_warning "流式响应: 可能失败或需要更多时间"
        echo "响应: $response"
    fi
}

# 主函数
main() {
    log_info "Warp2API Go - 测试脚本"
    echo "=================================="
    
    # 检查服务状态
    if ! check_services; then
        log_error "服务未运行，请先运行 ./scripts/start.sh"
        exit 1
    fi
    
    # 运行测试
    test_health
    test_models
    test_openai_api
    test_claude_api
    test_streaming
    
    echo "=================================="
    log_success "所有测试完成！"
    log_info "API端点:"
    echo "  OpenAI API: http://127.0.0.1:28889/v1/chat/completions"
    echo "  Claude API: http://127.0.0.1:28889/v1/messages"
    echo "  模型列表: http://127.0.0.1:28889/v1/models"
    echo "  健康检查: http://127.0.0.1:28889/healthz"
}

# 运行主函数
main "$@"