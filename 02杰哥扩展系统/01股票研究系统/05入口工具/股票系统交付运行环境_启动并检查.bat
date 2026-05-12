@echo off
chcp 65001 >nul
set "SCRIPT=D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\启动股票系统交付运行环境.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
pause
