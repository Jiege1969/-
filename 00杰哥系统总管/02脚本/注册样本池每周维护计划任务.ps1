$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$entry = Join-Path $scriptDir "运行样本池每周维护入口.ps1"
if (-not (Test-Path -LiteralPath $entry)) { throw "missing entry script: $entry" }

$taskName = "杰哥智能化系统_样本池每周维护"
$argument = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $entry + '"'
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argument -WorkingDirectory $scriptDir
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday -At "09:00"
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden -ExecutionTimeLimit (New-TimeSpan -Minutes 120)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal
Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null

[ordered]@{
    status = "registered"
    task_name = $taskName
    schedule = "weekly Saturday 09:00"
    entry = $entry
    safety = [ordered]@{
        real_wecom_send = $false
        n8n_trigger = $false
        broker_api = $false
        auto_trade = $false
    }
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 8
