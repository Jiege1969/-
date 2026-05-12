' Hidden launcher for startup construction preflight.
' Runs PowerShell without showing a console window.
Option Explicit

Dim shell, fso, scriptDir, psScript, htaPath, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
psScript = fso.BuildPath(scriptDir, "startup_preflight_entry.ps1")
htaPath = fso.BuildPath(scriptDir, "startup_status.hta")

command = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & psScript & Chr(34)
shell.CurrentDirectory = scriptDir
shell.Run command, 0, True

If fso.FileExists(htaPath) Then
  shell.Run "mshta.exe " & Chr(34) & htaPath & Chr(34), 1, False
End If
