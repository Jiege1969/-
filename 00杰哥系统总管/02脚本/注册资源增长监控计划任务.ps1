<#
Name: RegisterDiskGrowthMonitorTask.ps1
Purpose: Register hidden daily disk growth monitoring task.
Safety: Registers only a read-only local inventory task.
ChangeLog: 2026-05-06 created.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $scriptDir "隐藏启动资源增长监控.vbs"
if (-not (Test-Path -LiteralPath $launcher)) { throw "missing launcher: $launcher" }

$taskName = "杰哥智能化系统_D盘资源增长监控日报"
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$launcher`""
$trigger = New-ScheduledTaskTrigger -Daily -At "08:10"
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal
Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null

[ordered]@{
    status = "registered"
    task_name = $taskName
    launcher = $launcher
    schedule = "daily 08:10"
    hidden_window = $true
    multiple_instances = "IgnoreNew"
    safety = [ordered]@{
        delete_files = $false
        compress_files = $false
        move_files = $false
        trigger_n8n = $false
        send_wecom = $false
        call_broker_api = $false
        auto_trade = $false
    }
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 8


