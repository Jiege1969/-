' Name: hidden_start_wecom_unified.vbs
' System: 00杰哥系统总管 / 02脚本
' Purpose: Launch WeCom unified command local service starter without showing a console window.
' Trigger: Windows Scheduled Task 杰哥智能化系统_企业微信统一指令本地服务.
' Dependencies: start_wecom_unified_entry.ps1; Windows Script Host.
' Output: No direct output; delegated logs are written by the PowerShell entrypoint.
' Safety: Starts local WeCom command service only; no n8n trigger, no unsolicited WeCom real send, no broker API, no trading.
' ChangeLog: 2026-05-05 created; 2026-05-10 header standardized.
Option Explicit
Dim shell, fso, scriptDir, psScript, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
psScript = fso.BuildPath(scriptDir, "start_wecom_unified_entry.ps1")
command = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & psScript & Chr(34)
shell.CurrentDirectory = scriptDir
shell.Run command, 0, True
