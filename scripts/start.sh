#!/bin/bash

# Warp2API Go - 启动脚本
# 启动所有必要的服务

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

# 检查Go环境
check_go() {
    log_info "检查Go环境..."
    if ! command -v go &> /dev/null; then
        log_error "Go未安装，请先安装Go 1.21+"
        exit 1
    fi
    
    GO_VERSION=$(go version | cut -d' ' -f3 | cut -d'o' -f2)
    log_success "Go版本: $GO_VERSION"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    if [ ! -f "go.mod" ]; then
        log_error "go.mod文件不存在，请确保在项目根目录运行"
        exit 1
    fi
    
    log_info "下载依赖..."
    go mod tidy
    go mod download
    log_success "依赖检查完成"
}

# 构建项目
build_project() {
    log_info "构建项目..."
    
    # 构建主服务器
    log_info "构建主服务器..."
    go build -o bin/warp2api-go main.go
    
    # 构建桥接服务器
    log_info "构建桥接服务器..."
    go build -o bin/bridge cmd/bridge/main.go
    
    log_success "项目构建完成"
}

# 启动桥接服务器
start_bridge() {
    log_info "启动桥接服务器 (端口 28888)..."
    
    # 检查端口是否被占用
    if lsof -Pi :28888 -sTCP:LISTEN -t >/dev/null ; then
        log_warning "端口 28888 已被占用，尝试停止现有进程..."
        pkill -f "bridge" || true
        sleep 2
    fi
    
    # 启动桥接服务器
    nohup ./bin/bridge --port 28888 --host 127.0.0.1 > logs/bridge.log 2>&1 &
    BRIDGE_PID=$!
    echo $BRIDGE_PID > .bridge.pid
    
    # 等待服务器启动
    log_info "等待桥接服务器启动..."
    for i in {1..10}; do
        if curl -s http://127.0.0.1:28888/healthz > /dev/null 2>&1; then
            log_success "桥接服务器启动成功 (PID: $BRIDGE_PID)"
            return 0
        fi
        sleep 1
    done
    
    log_error "桥接服务器启动失败"
    return 1
}

# 启动主服务器
start_main() {
    log_info "启动主服务器 (端口 28889)..."
    
    # 检查端口是否被占用
    if lsof -Pi :28889 -sTCP:LISTEN -t >/dev/null ; then
        log_warning "端口 28889 已被占用，尝试停止现有进程..."
        pkill -f "warp2api-go" || true
        sleep 2
    fi
    
    # 启动主服务器
    nohup ./bin/warp2api-go --port 28889 --host 127.0.0.1 > logs/main.log 2>&1 &
    MAIN_PID=$!
    echo $MAIN_PID > .main.pid
    
    # 等待服务器启动
    log_info "等待主服务器启动..."
    for i in {1..10}; do
        if curl -s http://127.0.0.1:28889/healthz > /dev/null 2>&1; then
            log_success "主服务器启动成功 (PID: $MAIN_PID)"
            return 0
        fi
        sleep 1
    done
    
    log_error "主服务器启动失败"
    return 1
}

# 显示状态
show_status() {
    log_info "服务状态:"
    echo "=================================="
    
    # 检查桥接服务器
    if curl -s http://127.0.0.1:28888/healthz > /dev/null 2>&1; then
        log_success "桥接服务器: http://127.0.0.1:28888 - 运行中"
    else
        log_error "桥接服务器: http://127.0.0.1:28888 - 未运行"
    fi
    
    # 检查主服务器
    if curl -s http://127.0.0.1:28889/healthz > /dev/null 2>&1; then
        log_success "主服务器: http://127.0.0.1:28889 - 运行中"
    else
        log_error "主服务器: http://127.0.0.1:28889 - 未运行"
    fi
    
    echo "=================================="
    log_info "API端点:"
    echo "  OpenAI API: http://127.0.0.1:28889/v1/chat/completions"
    echo "  Claude API: http://127.0.0.1:28889/v1/messages"
    echo "  模型列表: http://127.0.0.1:28889/v1/models"
    echo "  健康检查: http://127.0.0.1:28889/healthz"
    echo "=================================="
}

# 主函数
main() {
    log_info "Warp2API Go - 启动脚本"
    echo "=================================="
    
    # 创建必要的目录
    mkdir -p bin logs
    
    # 检查环境
    check_go
    check_dependencies
    
    # 构建项目
    build_project
    
    # 启动服务
    start_bridge
    start_main
    
    # 显示状态
    show_status
    
    log_success "所有服务启动完成！"
    log_info "查看日志: tail -f logs/*.log"
    log_info "停止服务: ./scripts/stop.sh"
}

# 运行主函数
main "$@"