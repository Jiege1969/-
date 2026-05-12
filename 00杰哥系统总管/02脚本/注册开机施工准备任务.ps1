# ============================================================
# Name: register-startup-construction-preflight-task.ps1
# Purpose: Register current-user logon task for startup construction preflight.
# Trigger: Manual execution during system construction.
# Dependencies: PowerShell ScheduledTasks module; startup preflight script.
# Owner system: 00 system manager.
# Writes: Windows scheduled task and 04 log registration record.
# Safety: Only creates a new task when absent; does not overwrite an existing different task, restart services, trigger n8n, send WeWork, write formal DB, call broker APIs, or trade.
# Change log: 2026-04-28 created startup construction preflight task registration; made script ASCII-safe for Windows PowerShell 5.
# Marker: startup-construction-preflight-task-register
# ============================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$TaskName = -join ([char[]](0x6770,0x54E5,0x667A,0x80FD,0x5316,0x7CFB,0x7EDF,0x005F,0x5F00,0x673A,0x65BD,0x5DE5,0x51C6,0x5907,0x81EA,0x68C0))
$ScriptDir = Split-Path -Parent $PSCommandPath
$ManagerDir = Split-Path -Parent $ScriptDir
$PreflightFile = Get-ChildItem -LiteralPath $ScriptDir -File -Filter "*.ps1" |
    Where-Object { $_.FullName -ne $PSCommandPath } |
    Where-Object { Select-String -LiteralPath $_.FullName -SimpleMatch "startup-construction-preflight" -Quiet -ErrorAction SilentlyContinue } |
    Select-Object -First 1
$PreflightScript = if ($PreflightFile) { $PreflightFile.FullName } else { "" }
$LogRoot = Get-ChildItem -LiteralPath $ManagerDir -Directory | Where-Object { $_.Name -like "04*" } | Select-Object -First 1
if (-not $LogRoot) { throw "manager log directory not found" }
$StartupName = -join ([char[]](0x5F00,0x673A,0x65BD,0x5DE5,0x51C6,0x5907))
$LogDir = Join-Path $LogRoot.FullName $StartupName
$LatestPath = Join-Path $LogDir "startup-construction-preflight-task-register-latest.json"
$RecordPath = $LatestPath

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (-not (Test-Path -LiteralPath $PreflightScript)) {
    throw "preflight script not found: $PreflightScript"
}

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    $actionText = ($existing.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" }) -join "`n"
    $isSame = $actionText -like "*$PreflightScript*"
    $record = [pscustomobject]@{
        time = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        task_name = $TaskName
        action = if ($isSame) { "exists_same_task_no_change" } else { "exists_different_task_stop" }
        ok = $isSame
        task_state = $existing.State
        action_text = $actionText
        safety = "No overwrite performed."
    }
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $RecordPath -Encoding UTF8
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $LatestPath -Encoding UTF8
    Write-Output ($record | ConvertTo-Json -Compress)
    if (-not $isSame) { exit 1 }
    exit 0
}

$argument = "-NoProfile -ExecutionPolicy Bypass -File `"$PreflightScript`""
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argument
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$description = "Jiege intelligent system: run construction preflight after logon; no real business action."

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description $description | Out-Null

$registered = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
$record = [pscustomobject]@{
    time = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    task_name = $TaskName
    action = "created"
    ok = $true
    task_state = $registered.State
    script = $PreflightScript
    safety = "Creates startup construction preflight only; no formal service restart, no n8n trigger, no WeWork send, no broker API."
}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $RecordPath -Encoding UTF8
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $LatestPath -Encoding UTF8
Write-Output ($record | ConvertTo-Json -Compress)
