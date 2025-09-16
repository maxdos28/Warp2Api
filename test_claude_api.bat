@echo off
REM Claude API 集成测试脚本 (Windows 批处理版本)

echo 🚀 Claude API 集成测试 (Windows)
echo ==========================================

REM 检查服务器健康状态
echo 🏥 检查服务器健康状态...
curl -s http://localhost:28889/healthz >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ OpenAI 服务器 (28889) 未运行
    echo 请先启动服务器: start.bat
    pause
    exit /b 1
)

curl -s http://localhost:28888/healthz >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Bridge 服务器 (28888) 未运行
    echo 请先启动服务器: start.bat
    pause
    exit /b 1
)

echo ✅ 服务器健康状态正常

REM 测试1: 基本 Claude Messages API
echo.
echo 🧪 测试1: 基本 Claude Messages API
echo ------------------------------------------

curl -X POST http://localhost:28889/v1/messages ^
  -H "Content-Type: application/json" ^
  -d "{\"model\": \"claude-3-5-sonnet-20241022\", \"max_tokens\": 100, \"messages\": [{\"role\": \"user\", \"content\": \"Hello! Please say hi back in one sentence.\"}]}"

echo.
echo ✅ 基本测试完成

REM 测试2: 带系统提示的测试
echo.
echo 🧪 测试2: 带系统提示的 Claude Messages API
echo ------------------------------------------

curl -X POST http://localhost:28889/v1/messages ^
  -H "Content-Type: application/json" ^
  -d "{\"model\": \"claude-3-opus-20240229\", \"max_tokens\": 80, \"system\": \"You are a helpful assistant. Always be very concise.\", \"messages\": [{\"role\": \"user\", \"content\": \"What is the capital of Japan?\"}]}"

echo.
echo ✅ 系统提示测试完成

REM 测试3: 多轮对话测试
echo.
echo 🧪 测试3: 多轮对话 Claude Messages API
echo ------------------------------------------

curl -X POST http://localhost:28889/v1/messages ^
  -H "Content-Type: application/json" ^
  -d "{\"model\": \"claude-3-5-sonnet-20241022\", \"max_tokens\": 60, \"messages\": [{\"role\": \"user\", \"content\": \"What is 5+3?\"}, {\"role\": \"assistant\", \"content\": \"5+3 equals 8.\"}, {\"role\": \"user\", \"content\": \"What about 8+2?\"}]}"

echo.
echo ✅ 多轮对话测试完成

echo.
echo 🎉 所有测试完成!
echo ==========================================

echo.
echo 💡 使用提示:
echo   - 所有测试使用 Claude API 标准格式
echo   - 支持流式和非流式响应  
echo   - 支持系统提示和多轮对话
echo   - 模型名称会自动映射到内部模型

echo.
pause