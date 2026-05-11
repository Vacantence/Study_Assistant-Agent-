@echo off
chcp 65001 >nul
title AI 学习助手 - 环境安装

echo ============================================
echo   AI 学习助手 - 环境安装脚本
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python！请先安装 Python 3.14+
    echo 下载地址：https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

for /f "delims=" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo [1/4] 检测到 %PY_VER%

:: Install dependencies
echo [2/4] 正在安装 Python 依赖...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败！
    pause
    exit /b 1
)
echo [OK] 依赖安装完成

:: Setup .env
echo [3/4] 检查环境变量配置...
if not exist .env (
    echo 未检测到 .env 文件，正在从模板创建...
    copy .env.example .env >nul
    echo.
    echo 请编辑 .env 文件，填入你的 API Key：
    echo   DEEPSEEK_API_KEY=你的 DeepSeek API Key
    echo   ALIYUN_EMBEDDING_API_KEY=你的阿里云 DashScope Key
    echo.
    echo 也可以启动后用设置页面添加 LLM 提供商。
) else (
    echo [OK] .env 已存在
)

:: Create outputs directory
echo [4/4] 创建必要目录...
if not exist outputs mkdir outputs

echo.
echo ============================================
echo   安装完成！
echo.
echo   启动方式：
echo     1. 双击 run_api.bat（启动后端服务）
echo     2. 打开 Tauri 桌面应用
echo.
echo   若使用浏览器，访问 http://localhost:8000
echo ============================================
echo.
pause
