' Name: 隐藏启动资源增长监控.vbs
' System: 00杰哥系统总管 / 02脚本
' Purpose: Launch disk growth monitor without showing a console window.
' Trigger: Windows Scheduled Task 杰哥智能化系统_D盘资源增长监控日报.
' Dependencies: collect_disk_growth_report.ps1; Windows Script Host.
' Output: No direct output; delegated logs are written by the PowerShell entrypoint.
' Safety: Local disk usage reporting wrapper only; no n8n trigger, no WeCom real send, no broker API, no trading.
' ChangeLog: 2026-05-06 created; 2026-05-10 header standardized.
Option Explicit
Dim shell, fso, scriptDir, psScript, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
psScript = fso.BuildPath(scriptDir, "collect_disk_growth_report.ps1")
command = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & psScript & Chr(34)
shell.CurrentDirectory = scriptDir
shell.Run command, 0, False
