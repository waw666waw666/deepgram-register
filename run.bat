@echo off
chcp 65001 >nul
title Deepgram Register
echo ========================================================
echo   Deepgram Register
echo   Deepgram 语音 AI 平台自动化注册与 $200 免费额度 API Key 极速直出工具
echo ========================================================
echo.
echo [1] 默认启动运行 (生成 1 个账号凭据)
echo [2] 批量运行 (生成 3 个账号凭据)
echo [3] 无头后台运行 (--headless)
echo.
set /p opt="请选择运行模式 (默认 1): "
if "%opt%"=="" set opt=1
if "%opt%"=="1" python main.py -n 1
if "%opt%"=="2" python main.py -n 3
if "%opt%"=="3" python main.py --headless -n 1
echo.
pause
