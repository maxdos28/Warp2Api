# Warp2API Go - Dockerfile

# 构建阶段
FROM golang:1.21-alpine AS builder

# 设置工作目录
WORKDIR /app

# 安装必要的包
RUN apk add --no-cache git curl

# 复制go mod文件
COPY go.mod go.sum ./

# 下载依赖
RUN go mod download

# 复制源代码
COPY . .

# 构建应用
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o bin/warp2api-go main.go
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o bin/bridge cmd/bridge/main.go

# 运行阶段
FROM alpine:latest

# 安装必要的包
RUN apk --no-cache add ca-certificates curl

# 创建非root用户
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# 设置工作目录
WORKDIR /app

# 从构建阶段复制二进制文件
COPY --from=builder /app/bin/ /app/bin/
COPY --from=builder /app/scripts/ /app/scripts/

# 创建日志目录
RUN mkdir -p logs && chown -R appuser:appgroup /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 28888 28889

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:28889/healthz || exit 1

# 启动脚本
COPY --chown=appuser:appgroup scripts/docker-start.sh /app/scripts/
RUN chmod +x /app/scripts/docker-start.sh

# 启动命令
CMD ["/app/scripts/docker-start.sh"]