<#
Name: RegisterPublicCallbackTunnelGuardTask.ps1
Purpose: Register a hidden Windows scheduled task for the stock public callback tunnel guard.
Safety: Registers only the guard task. It does not run business probes, does not send WeCom messages, does not trigger n8n, and does not trade.
ChangeLog: 2026-05-06 created.
#>

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $scriptDir "隐藏启动公网反向隧道守护.vbs"
if (-not (Test-Path -LiteralPath $launcher)) {
    throw "missing launcher: $launcher"
}

$taskName = "杰哥智能化系统_公网反向隧道守护"
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$launcher`""
$triggerAtLogon = New-ScheduledTaskTrigger -AtLogOn
$triggerRepeating = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 3) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

$task = New-ScheduledTask -Action $action -Trigger @($triggerAtLogon, $triggerRepeating) -Settings $settings -Principal $principal
Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null

[ordered]@{
    status = "registered"
    task_name = $taskName
    launcher = $launcher
    interval_minutes = 3
    hidden_window = $true
    run_only_if_network_available = $true
    multiple_instances = "IgnoreNew"
    mode = "Repair"
    safety = [ordered]@{
        post_wecom_business_path = $false
        trigger_n8n = $false
        send_wecom = $false
        call_broker_api = $false
        auto_trade = $false
    }
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 8



