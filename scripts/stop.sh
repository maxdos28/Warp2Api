#!/bin/bash

# Warp2API Go - 停止脚本
# 停止所有服务

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

# 停止服务
stop_services() {
    log_info "停止Warp2API Go服务..."
    
    # 停止主服务器
    if [ -f ".main.pid" ]; then
        MAIN_PID=$(cat .main.pid)
        if kill -0 $MAIN_PID 2>/dev/null; then
            log_info "停止主服务器 (PID: $MAIN_PID)..."
            kill $MAIN_PID
            sleep 2
            if kill -0 $MAIN_PID 2>/dev/null; then
                log_warning "强制停止主服务器..."
                kill -9 $MAIN_PID
            fi
            log_success "主服务器已停止"
        else
            log_warning "主服务器进程不存在"
        fi
        rm -f .main.pid
    else
        log_warning "主服务器PID文件不存在"
    fi
    
    # 停止桥接服务器
    if [ -f ".bridge.pid" ]; then
        BRIDGE_PID=$(cat .bridge.pid)
        if kill -0 $BRIDGE_PID 2>/dev/null; then
            log_info "停止桥接服务器 (PID: $BRIDGE_PID)..."
            kill $BRIDGE_PID
            sleep 2
            if kill -0 $BRIDGE_PID 2>/dev/null; then
                log_warning "强制停止桥接服务器..."
                kill -9 $BRIDGE_PID
            fi
            log_success "桥接服务器已停止"
        else
            log_warning "桥接服务器进程不存在"
        fi
        rm -f .bridge.pid
    else
        log_warning "桥接服务器PID文件不存在"
    fi
    
    # 清理进程
    log_info "清理残留进程..."
    pkill -f "warp2api-go" || true
    pkill -f "bridge" || true
    
    log_success "所有服务已停止"
}

# 显示状态
show_status() {
    log_info "服务状态:"
    echo "=================================="
    
    # 检查桥接服务器
    if curl -s http://127.0.0.1:28888/healthz > /dev/null 2>&1; then
        log_warning "桥接服务器: http://127.0.0.1:28888 - 仍在运行"
    else
        log_success "桥接服务器: http://127.0.0.1:28888 - 已停止"
    fi
    
    # 检查主服务器
    if curl -s http://127.0.0.1:28889/healthz > /dev/null 2>&1; then
        log_warning "主服务器: http://127.0.0.1:28889 - 仍在运行"
    else
        log_success "主服务器: http://127.0.0.1:28889 - 已停止"
    fi
    
    echo "=================================="
}

# 主函数
main() {
    log_info "Warp2API Go - 停止脚本"
    echo "=================================="
    
    # 停止服务
    stop_services
    
    # 显示状态
    show_status
    
    log_success "停止完成！"
}

# 运行主函数
main "$@"