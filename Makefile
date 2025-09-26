# Warp2API Go - Makefile

.PHONY: help build clean run test deps fmt vet lint

# 默认目标
help:
	@echo "Warp2API Go - 可用命令:"
	@echo "  make deps     - 下载依赖"
	@echo "  make build    - 构建项目"
	@echo "  make run      - 运行主服务器"
	@echo "  make bridge   - 运行桥接服务器"
	@echo "  make test     - 运行测试"
	@echo "  make fmt      - 格式化代码"
	@echo "  make vet      - 代码检查"
	@echo "  make lint     - 静态分析"
	@echo "  make clean    - 清理构建文件"
	@echo "  make start    - 启动所有服务"
	@echo "  make stop     - 停止所有服务"

# 下载依赖
deps:
	@echo "下载依赖..."
	go mod tidy
	go mod download

# 构建项目
build: deps
	@echo "构建项目..."
	@mkdir -p bin
	go build -o bin/warp2api-go main.go
	go build -o bin/bridge cmd/bridge/main.go
	@echo "构建完成!"

# 运行主服务器
run: build
	@echo "启动主服务器..."
	./bin/warp2api-go

# 运行桥接服务器
bridge: build
	@echo "启动桥接服务器..."
	./bin/bridge

# 运行测试
test:
	@echo "运行测试..."
	go test ./...

# 格式化代码
fmt:
	@echo "格式化代码..."
	go fmt ./...

# 代码检查
vet:
	@echo "代码检查..."
	go vet ./...

# 静态分析
lint:
	@echo "静态分析..."
	@if command -v staticcheck >/dev/null 2>&1; then \
		staticcheck ./...; \
	else \
		echo "staticcheck 未安装，跳过静态分析"; \
	fi

# 清理构建文件
clean:
	@echo "清理构建文件..."
	rm -rf bin/
	rm -f *.pid
	rm -rf logs/

# 启动所有服务
start:
	@echo "启动所有服务..."
	@chmod +x scripts/start.sh
	./scripts/start.sh

# 停止所有服务
stop:
	@echo "停止所有服务..."
	@chmod +x scripts/stop.sh
	./scripts/stop.sh

# 测试API
test-api:
	@echo "测试API..."
	@chmod +x scripts/test.sh
	./scripts/test.sh

# 开发模式运行
dev: build
	@echo "开发模式运行..."
	@echo "启动桥接服务器 (后台)..."
	./bin/bridge --port 28888 --host 127.0.0.1 > logs/bridge.log 2>&1 &
	@echo $$! > .bridge.pid
	@sleep 2
	@echo "启动主服务器..."
	./bin/warp2api-go --port 28889 --host 127.0.0.1

# 安装工具
install-tools:
	@echo "安装开发工具..."
	go install honnef.co/go/tools/cmd/staticcheck@latest
	go install golang.org/x/tools/cmd/goimports@latest

# 检查代码质量
check: fmt vet lint
	@echo "代码质量检查完成!"

# 完整构建流程
all: clean deps build test check
	@echo "完整构建流程完成!"