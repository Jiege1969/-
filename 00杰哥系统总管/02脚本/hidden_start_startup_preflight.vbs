' Name: hidden_start_startup_preflight.vbs
' System: 00杰哥系统总管 / 02脚本
' Purpose: Launch startup preflight and optional status card without showing a console window.
' Trigger: Windows Scheduled Task 杰哥智能化系统_开机施工准备自检.
' Dependencies: startup_preflight_entry.ps1; show_startup_status_card.ps1; Windows Script Host.
' Output: No direct output; delegated logs are written by the PowerShell entrypoints.
' Safety: Startup readiness check wrapper only; no n8n trigger, no WeCom real send, no broker API, no trading.
' ChangeLog: 2026-05-05 created; 2026-05-10 header standardized.
Option Explicit
Dim shell, fso, scriptDir, psScript, cardScript, command, cardCommand
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
psScript = fso.BuildPath(scriptDir, "startup_preflight_entry.ps1")
cardScript = fso.BuildPath(scriptDir, "show_startup_status_card.ps1")
command = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & psScript & Chr(34)
cardCommand = "powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & cardScript & Chr(34)
shell.CurrentDirectory = scriptDir
If fso.FileExists(cardScript) Then
  shell.Run cardCommand, 0, False
End If
shell.Run command, 0, False
