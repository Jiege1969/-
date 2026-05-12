$ErrorActionPreference = "Stop"

function U { param([int[]]$CodePoints) return -join ($CodePoints | ForEach-Object { [char]$_ }) }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$entryName = U @(0x8fd0,0x884c,0x80a1,0x7968,0x7cfb,0x7edf,0x4e09,0x9636,0x6bb5,0x5b9a,0x65f6,0x5165,0x53e3,0x2e,0x70,0x73,0x31)
$entry = Join-Path $scriptDir $entryName
if (-not (Test-Path -LiteralPath $entry)) { throw "missing entry script: $entry" }

$taskName = U @(0x6770,0x54e5,0x667a,0x80fd,0x5316,0x7cfb,0x7edf,0x5f,0x80a1,0x7968,0x5f,0x76d8,0x524d,0x51fa,0x51fb,0x6392,0x5e8f)
$argument = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$entry`" -Stage preopen"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argument -WorkingDirectory $scriptDir
$trigger = New-ScheduledTaskTrigger -Daily -At "08:50"
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal
Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null

[ordered]@{
    status = "registered"
    task_name = $taskName
    stage = "preopen"
    schedule = "daily 08:50"
    entry = $entry
    safety = [ordered]@{
        real_wecom_send = $false
        n8n_trigger = $false
        broker_api = $false
        auto_trade = $false
    }
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 8
