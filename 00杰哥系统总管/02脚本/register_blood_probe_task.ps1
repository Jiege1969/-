<#
Name: register_blood_probe_task.ps1
Purpose: Register hidden minutely read-only bloodline probe task.
Safety: Registers only a read-only probe. No workflow trigger, no external send, no repair.
ChangeLog: 2026-05-06 created.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $scriptDir "hidden_start_blood_probe.vbs"
if (-not (Test-Path -LiteralPath $launcher)) { throw "missing launcher: $launcher" }

$taskName = "杰哥智能化系统_血脉分钟级只读探针"
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$launcher`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -Hidden `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal
Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null

[ordered]@{
    status = "registered"
    task_name = $taskName
    launcher = $launcher
    schedule = "every 1 minute"
    hidden_window = $true
    multiple_instances = "IgnoreNew"
    execution_time_limit_minutes = 2
    safety = [ordered]@{
        read_only_probe = $true
        trigger_n8n = $false
        send_wecom = $false
        repair_service = $false
        call_broker_api = $false
        auto_trade = $false
        delete_data = $false
    }
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 8
