' Name: hidden_start_blood_probe.vbs
' System: 00杰哥系统总管 / 02脚本
' Purpose: Launch minutely bloodline probe without showing a console window.
' Trigger: Windows Scheduled Task 杰哥智能化系统_血脉分钟级只读探针.
' Dependencies: blood_probe_minutely.ps1; Windows Script Host.
' Output: No direct output; delegated logs are written by blood_probe_minutely.ps1.
' Safety: Window hiding wrapper only; no n8n trigger, no broker API, no trading.
' ChangeLog: 2026-05-06 created; 2026-05-10 header standardized.
Option Explicit
Dim shell, fso, scriptDir, psScript, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
psScript = fso.BuildPath(scriptDir, "blood_probe_minutely.ps1")
command = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & psScript & Chr(34)
shell.CurrentDirectory = scriptDir
shell.Run command, 0, False
