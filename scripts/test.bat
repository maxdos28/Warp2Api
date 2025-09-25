@echo off
REM Warp2API Go - Windows 测试脚本

setlocal enabledelayedexpansion

REM 颜色定义
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

echo %INFO% Warp2API Go - 测试脚本
echo ==================================

REM 检查服务状态
echo %INFO% 检查服务状态...

REM 检查桥接服务器
curl -s http://127.0.0.1:28888/healthz >nul 2>&1
if not errorlevel 1 (
    echo %SUCCESS% 桥接服务器: 运行中
) else (
    echo %ERROR% 桥接服务器: 未运行
    echo %ERROR% 服务未运行，请先运行 scripts\start.bat
    pause
    exit /b 1
)

REM 检查主服务器
curl -s http://127.0.0.1:28889/healthz >nul 2>&1
if not errorlevel 1 (
    echo %SUCCESS% 主服务器: 运行中
) else (
    echo %ERROR% 主服务器: 未运行
    echo %ERROR% 服务未运行，请先运行 scripts\start.bat
    pause
    exit /b 1
)

REM 测试健康检查
echo %INFO% 测试健康检查端点...

REM 测试桥接服务器健康检查
curl -s http://127.0.0.1:28888/healthz | findstr "healthy" >nul
if not errorlevel 1 (
    echo %SUCCESS% 桥接服务器健康检查: 通过
) else (
    echo %ERROR% 桥接服务器健康检查: 失败
    pause
    exit /b 1
)

REM 测试主服务器健康检查
curl -s http://127.0.0.1:28889/healthz | findstr "healthy" >nul
if not errorlevel 1 (
    echo %SUCCESS% 主服务器健康检查: 通过
) else (
    echo %ERROR% 主服务器健康检查: 失败
    pause
    exit /b 1
)

REM 测试模型列表
echo %INFO% 测试模型列表端点...
curl -s http://127.0.0.1:28889/v1/models | findstr "claude-4-sonnet" >nul
if not errorlevel 1 (
    echo %SUCCESS% 模型列表: 通过
    echo 可用模型:
    curl -s http://127.0.0.1:28889/v1/models
) else (
    echo %ERROR% 模型列表: 失败
    pause
    exit /b 1
)

REM 测试OpenAI API
echo %INFO% 测试OpenAI Chat Completions API...

REM 创建临时测试文件
echo {> test_openai.json
echo   "model": "claude-4-sonnet",>> test_openai.json
echo   "messages": [>> test_openai.json
echo     {"role": "user", "content": "Hello, how are you?"}>> test_openai.json
echo   ],>> test_openai.json
echo   "max_tokens": 100>> test_openai.json
echo }>> test_openai.json

REM 发送请求
curl -s -X POST http://127.0.0.1:28889/v1/chat/completions -H "Content-Type: application/json" -d @test_openai.json | findstr "choices" >nul
if not errorlevel 1 (
    echo %SUCCESS% OpenAI API: 通过
    echo 响应示例:
    curl -s -X POST http://127.0.0.1:28889/v1/chat/completions -H "Content-Type: application/json" -d @test_openai.json
) else (
    echo %ERROR% OpenAI API: 失败
    echo 错误响应:
    curl -s -X POST http://127.0.0.1:28889/v1/chat/completions -H "Content-Type: application/json" -d @test_openai.json
    del test_openai.json
    pause
    exit /b 1
)

REM 清理临时文件
del test_openai.json

REM 测试Claude API
echo %INFO% 测试Claude Messages API...

REM 创建临时测试文件
echo {> test_claude.json
echo   "model": "claude-3-5-sonnet-20241022",>> test_claude.json
echo   "max_tokens": 100,>> test_claude.json
echo   "messages": [>> test_claude.json
echo     {"role": "user", "content": "Hello, how are you?"}>> test_claude.json
echo   ]>> test_claude.json
echo }>> test_claude.json

REM 发送请求
curl -s -X POST http://127.0.0.1:28889/v1/messages -H "Content-Type: application/json" -d @test_claude.json | findstr "content" >nul
if not errorlevel 1 (
    echo %SUCCESS% Claude API: 通过
    echo 响应示例:
    curl -s -X POST http://127.0.0.1:28889/v1/messages -H "Content-Type: application/json" -d @test_claude.json
) else (
    echo %ERROR% Claude API: 失败
    echo 错误响应:
    curl -s -X POST http://127.0.0.1:28889/v1/messages -H "Content-Type: application/json" -d @test_claude.json
    del test_claude.json
    pause
    exit /b 1
)

REM 清理临时文件
del test_claude.json

echo ==================================
echo %SUCCESS% 所有测试完成！
echo %INFO% API端点:
echo   OpenAI API: http://127.0.0.1:28889/v1/chat/completions
echo   Claude API: http://127.0.0.1:28889/v1/messages
echo   模型列表: http://127.0.0.1:28889/v1/models
echo   健康检查: http://127.0.0.1:28889/healthz

pause