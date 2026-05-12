@echo off
chcp 65001 >nul
python "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\生成股票系统可信IP状态监测.py"
powershell -NoProfile -Command "$p='D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\03数据\155可信IP状态监测\股票系统可信IP状态监测_最新.json'; $j=Get-Content -LiteralPath $p -Raw -Encoding UTF8 | ConvertFrom-Json; Write-Host ('当前应放行IP：' + $j.'当前需放行IP')"
echo 请确认：企业微信后台已加入当前可信IP，且你允许发送本人白名单灰度消息。
choice /M "确认执行企业微信真实推送复测"
if errorlevel 2 exit /b 1
python "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\股票系统企微真实推送复测控制器.py" --real-send --open-report
pause
