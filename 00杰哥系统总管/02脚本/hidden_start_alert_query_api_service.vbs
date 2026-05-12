' Name: hidden_start_alert_query_api_service.vbs
' System: 00杰哥系统总管 / 02脚本
' Purpose: Launch alert query API starter without showing a console window.
' Trigger: Windows Scheduled Task 杰哥智能化系统_报警查询API服务.
' Dependencies: start_alert_query_api_service_entry.ps1; Windows Script Host.
' Output: No direct output; delegated logs are written by the PowerShell entrypoint.
' Safety: Window hiding wrapper only; no n8n trigger, no WeCom real send, no broker API, no trading.
' ChangeLog: 2026-05-10 created to stop boot-time black console flashes.
Option Explicit
Dim shell, fso, scriptDir, psScript, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
psScript = fso.BuildPath(scriptDir, "start_alert_query_api_service_entry.ps1")
command = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & psScript & Chr(34)
shell.CurrentDirectory = scriptDir
shell.Run command, 0, True
