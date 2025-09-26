@echo off
REM Warp2API Go - Windows 停止脚本

setlocal enabledelayedexpansion

REM 颜色定义
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

echo %INFO% Warp2API Go - 停止脚本
echo ==================================

REM 停止服务
echo %INFO% 停止Warp2API Go服务...

REM 停止主服务器
tasklist /fi "imagename eq warp2api-go.exe" | findstr "warp2api-go.exe" >nul
if not errorlevel 1 (
    echo %INFO% 停止主服务器...
    taskkill /f /im warp2api-go.exe >nul 2>&1
    echo %SUCCESS% 主服务器已停止
) else (
    echo %WARNING% 主服务器进程不存在
)

REM 停止桥接服务器
tasklist /fi "imagename eq bridge.exe" | findstr "bridge.exe" >nul
if not errorlevel 1 (
    echo %INFO% 停止桥接服务器...
    taskkill /f /im bridge.exe >nul 2>&1
    echo %SUCCESS% 桥接服务器已停止
) else (
    echo %WARNING% 桥接服务器进程不存在
)

REM 清理进程
echo %INFO% 清理残留进程...
taskkill /f /im warp2api-go.exe >nul 2>&1
taskkill /f /im bridge.exe >nul 2>&1

echo %SUCCESS% 所有服务已停止

REM 显示状态
echo %INFO% 服务状态:
echo ==================================

curl -s http://127.0.0.1:28888/healthz >nul 2>&1
if not errorlevel 1 (
    echo %WARNING% 桥接服务器: http://127.0.0.1:28888 - 仍在运行
) else (
    echo %SUCCESS% 桥接服务器: http://127.0.0.1:28888 - 已停止
)

curl -s http://127.0.0.1:28889/healthz >nul 2>&1
if not errorlevel 1 (
    echo %WARNING% 主服务器: http://127.0.0.1:28889 - 仍在运行
) else (
    echo %SUCCESS% 主服务器: http://127.0.0.1:28889 - 已停止
)

echo ==================================
echo %SUCCESS% 停止完成！

pause