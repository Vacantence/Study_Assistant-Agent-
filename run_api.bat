@echo off
chcp 65001 >nul
title AI 学习助手 - 后端服务

echo 正在启动 AI 学习助手后端...
echo.

python run_api.py
if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败！请先运行 setup.bat 安装依赖。
    pause
)
