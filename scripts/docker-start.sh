#!/bin/sh

# Warp2API Go - Docker 启动脚本

set -e

echo "[INFO] Warp2API Go - Docker 启动脚本"
echo "=================================="

# 创建日志目录
mkdir -p logs

# 启动桥接服务器
echo "[INFO] 启动桥接服务器 (端口 28888)..."
./bin/bridge --port 28888 --host 0.0.0.0 > logs/bridge.log 2>&1 &
BRIDGE_PID=$!

# 等待桥接服务器启动
echo "[INFO] 等待桥接服务器启动..."
for i in $(seq 1 10); do
    if curl -s http://localhost:28888/healthz > /dev/null 2>&1; then
        echo "[SUCCESS] 桥接服务器启动成功 (PID: $BRIDGE_PID)"
        break
    fi
    sleep 1
done

# 启动主服务器
echo "[INFO] 启动主服务器 (端口 28889)..."
./bin/warp2api-go --port 28889 --host 0.0.0.0 > logs/main.log 2>&1 &
MAIN_PID=$!

# 等待主服务器启动
echo "[INFO] 等待主服务器启动..."
for i in $(seq 1 10); do
    if curl -s http://localhost:28889/healthz > /dev/null 2>&1; then
        echo "[SUCCESS] 主服务器启动成功 (PID: $MAIN_PID)"
        break
    fi
    sleep 1
done

# 显示状态
echo "[INFO] 服务状态:"
echo "=================================="
echo "桥接服务器: http://0.0.0.0:28888 - 运行中"
echo "主服务器: http://0.0.0.0:28889 - 运行中"
echo "=================================="
echo "[INFO] API端点:"
echo "  OpenAI API: http://0.0.0.0:28889/v1/chat/completions"
echo "  Claude API: http://0.0.0.0:28889/v1/messages"
echo "  模型列表: http://0.0.0.0:28889/v1/models"
echo "  健康检查: http://0.0.0.0:28889/healthz"
echo "=================================="

echo "[SUCCESS] 所有服务启动完成！"

# 保持容器运行
wait