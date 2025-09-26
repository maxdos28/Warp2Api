@echo off
REM Warp2API Go - Windows 启动脚本

setlocal enabledelayedexpansion

REM 颜色定义（Windows 批处理不支持颜色，使用文本标识）
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

echo %INFO% Warp2API Go - 启动脚本
echo ==================================

REM 检查Go环境
echo %INFO% 检查Go环境...
go version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Go未安装，请先安装Go 1.21+
    pause
    exit /b 1
)

for /f "tokens=3" %%i in ('go version') do set GO_VERSION=%%i
echo %SUCCESS% Go版本: %GO_VERSION%

REM 检查依赖
echo %INFO% 检查依赖...
if not exist "go.mod" (
    echo %ERROR% go.mod文件不存在，请确保在项目根目录运行
    pause
    exit /b 1
)

echo %INFO% 下载依赖...
go mod tidy
go mod download
echo %SUCCESS% 依赖检查完成

REM 创建必要的目录
if not exist "bin" mkdir bin
if not exist "logs" mkdir logs

REM 构建项目
echo %INFO% 构建项目...
echo %INFO% 构建主服务器...
go build -o bin/warp2api-go.exe main.go
if errorlevel 1 (
    echo %ERROR% 主服务器构建失败
    pause
    exit /b 1
)

echo %INFO% 构建桥接服务器...
go build -o bin/bridge.exe cmd/bridge/main.go
if errorlevel 1 (
    echo %ERROR% 桥接服务器构建失败
    pause
    exit /b 1
)

echo %SUCCESS% 项目构建完成

REM 启动桥接服务器
echo %INFO% 启动桥接服务器 (端口 28888)...

REM 检查端口是否被占用
netstat -an | findstr ":28888" | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo %WARNING% 端口 28888 已被占用，尝试停止现有进程...
    taskkill /f /im bridge.exe >nul 2>&1
    timeout /t 2 >nul
)

REM 启动桥接服务器
start /b bin\bridge.exe --port 28888 --host 127.0.0.1 > logs\bridge.log 2>&1

REM 等待服务器启动
echo %INFO% 等待桥接服务器启动...
for /l %%i in (1,1,10) do (
    curl -s http://127.0.0.1:28888/healthz >nul 2>&1
    if not errorlevel 1 (
        echo %SUCCESS% 桥接服务器启动成功
        goto :bridge_started
    )
    timeout /t 1 >nul
)

echo %ERROR% 桥接服务器启动失败
pause
exit /b 1

:bridge_started

REM 启动主服务器
echo %INFO% 启动主服务器 (端口 28889)...

REM 检查端口是否被占用
netstat -an | findstr ":28889" | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo %WARNING% 端口 28889 已被占用，尝试停止现有进程...
    taskkill /f /im warp2api-go.exe >nul 2>&1
    timeout /t 2 >nul
)

REM 启动主服务器
start /b bin\warp2api-go.exe --port 28889 --host 127.0.0.1 > logs\main.log 2>&1

REM 等待服务器启动
echo %INFO% 等待主服务器启动...
for /l %%i in (1,1,10) do (
    curl -s http://127.0.0.1:28889/healthz >nul 2>&1
    if not errorlevel 1 (
        echo %SUCCESS% 主服务器启动成功
        goto :main_started
    )
    timeout /t 1 >nul
)

echo %ERROR% 主服务器启动失败
pause
exit /b 1

:main_started

REM 显示状态
echo %INFO% 服务状态:
echo ==================================
curl -s http://127.0.0.1:28888/healthz >nul 2>&1
if not errorlevel 1 (
    echo %SUCCESS% 桥接服务器: http://127.0.0.1:28888 - 运行中
) else (
    echo %ERROR% 桥接服务器: http://127.0.0.1:28888 - 未运行
)

curl -s http://127.0.0.1:28889/healthz >nul 2>&1
if not errorlevel 1 (
    echo %SUCCESS% 主服务器: http://127.0.0.1:28889 - 运行中
) else (
    echo %ERROR% 主服务器: http://127.0.0.1:28889 - 未运行
)

echo ==================================
echo %INFO% API端点:
echo   OpenAI API: http://127.0.0.1:28889/v1/chat/completions
echo   Claude API: http://127.0.0.1:28889/v1/messages
echo   模型列表: http://127.0.0.1:28889/v1/models
echo   健康检查: http://127.0.0.1:28889/healthz
echo ==================================

echo %SUCCESS% 所有服务启动完成！
echo %INFO% 查看日志: type logs\*.log
echo %INFO% 停止服务: scripts\stop.bat

pause