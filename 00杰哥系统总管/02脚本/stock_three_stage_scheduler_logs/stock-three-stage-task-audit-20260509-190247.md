# 股票三阶段计划任务只读巡检日志

- 生成时间：2026-05-09 19:02:48
- 入口脚本：D:\杰哥智能化系统\00杰哥系统总管\02脚本\运行股票系统三阶段定时入口.ps1
- 巡检方式：创建一次性 audit_only 标志后，通过 Start-ScheduledTask 触发计划任务；入口只抢锁、写日志、复核安全开关，不执行完整业务链。

## 任务计划程序清单

| 任务 | 状态 | 上次运行 | 返回码 | 下次运行 | 阶段 | 巡检 | 锁 | 安全 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 杰哥智能化系统_股票_盘后短线观察 | Ready | 2026-05-09 19:01:49 | 0 | 2026-05-10 15:30:00 | postclose | audit_pass | True | True |
| 杰哥智能化系统_股票_晚间三维深度分析 | Ready | 2026-05-09 19:01:49 | 0 | 2026-05-09 21:00:00 | night | audit_pass | True | True |
| 杰哥智能化系统_股票_盘前出击排序 | Ready | 2026-05-09 19:01:49 | 0 | 2026-05-10 08:50:00 | preopen | audit_pass | True | True |

## 封锁确认

| 任务 | 真实企微成功 | 允许真实发送 | 自动交易 | 券商接口 | n8n触发 |
| --- | --- | --- | --- | --- | --- |
| 杰哥智能化系统_股票_盘后短线观察 | False | False | False | False | False |
| 杰哥智能化系统_股票_晚间三维深度分析 | False | False | False | False | False |
| 杰哥智能化系统_股票_盘前出击排序 | False | False | False | False | False |

## 日志文件

- 杰哥智能化系统_股票_盘后短线观察：D:\杰哥智能化系统\00杰哥系统总管\02脚本\stock_three_stage_scheduler_logs\20260509-190150-postclose.json
- 杰哥智能化系统_股票_晚间三维深度分析：D:\杰哥智能化系统\00杰哥系统总管\02脚本\stock_three_stage_scheduler_logs\20260509-190150-night.json
- 杰哥智能化系统_股票_盘前出击排序：D:\杰哥智能化系统\00杰哥系统总管\02脚本\stock_three_stage_scheduler_logs\20260509-190150-preopen.json

## Action

- 杰哥智能化系统_股票_盘后短线观察：powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\00杰哥系统总管\02脚本\运行股票系统三阶段定时入口.ps1" -Stage postclose
- 杰哥智能化系统_股票_晚间三维深度分析：powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\00杰哥系统总管\02脚本\运行股票系统三阶段定时入口.ps1" -Stage night
- 杰哥智能化系统_股票_盘前出击排序：powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\00杰哥系统总管\02脚本\运行股票系统三阶段定时入口.ps1" -Stage preopen
