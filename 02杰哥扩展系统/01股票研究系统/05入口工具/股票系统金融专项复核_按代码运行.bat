@echo off
chcp 65001 >nul
cd /d "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本"
set /p STOCK_CODE=请输入L5股票代码（如 sh688047 或 688047.SH）：
python "执行股票金融专项复核.py" --code %STOCK_CODE%
python "生成股票金融专项复核索引.py"
start "" "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\03数据\149金融专项复核\股票金融专项复核_最新.md"
pause
