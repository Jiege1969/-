' Name: 隐藏启动公网反向隧道守护.vbs
' System: 00杰哥系统总管 / 02脚本
' Purpose: Launch stock public callback tunnel guard without showing a console window.
' Trigger: Windows Scheduled Task 杰哥智能化系统_公网反向隧道守护.
' Dependencies: guard_stock_public_tunnel.ps1; Windows Script Host.
' Output: No direct output; delegated logs are written by the PowerShell entrypoint.
' Safety: Tunnel guard wrapper only; no n8n trigger, no WeCom real send, no broker API, no trading.
' ChangeLog: 2026-05-06 created; 2026-05-10 header standardized.
Option Explicit
Dim shell, fso, scriptDir, psScript, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
psScript = fso.BuildPath(scriptDir, "guard_stock_public_tunnel.ps1")
command = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & psScript & Chr(34) & " -Mode Repair"
shell.CurrentDirectory = scriptDir
shell.Run command, 0, False



