<#
Name: 运行样本池每周维护入口.ps1
System: 00杰哥系统总管 / 02脚本
Purpose: Weekly maintenance wrapper for 2000-stock sample pool representative drift, metabolism and health reports.
Trigger: Windows Scheduled Task 杰哥智能化系统_样本池每周维护.
Dependencies: Stock sample pool maintenance scripts under 02杰哥扩展系统/01股票研究系统.
Output: stock_sample_pool_weekly_logs and stock sample pool health/maintenance reports.
Safety: Local files/logs only. No real WeCom send, no n8n trigger, no broker API, no trading.
ChangeLog: 2026-05-09 created; 2026-05-10 header standardized.
#>

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$managerDir = Split-Path -Parent $scriptDir
$root = Split-Path -Parent $managerDir
$logDir = Join-Path $scriptDir "stock_sample_pool_weekly_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-JsonFile {
    param([string]$Path, $Value)
    $json = $Value | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText($Path, $json, [System.Text.Encoding]::UTF8)
}

function Invoke-PythonScript {
    param(
        [string]$ScriptDir,
        [string]$ScriptName,
        [string]$RunDir,
        [string]$RunId,
        [int]$TimeoutSeconds = 3600
    )
    $scriptPath = Join-Path $ScriptDir $ScriptName
    if (-not (Test-Path -LiteralPath $scriptPath)) { throw "missing stock script: $ScriptName" }
    $stdout = Join-Path $RunDir ($RunId + "-" + ([System.IO.Path]::GetFileNameWithoutExtension($ScriptName)) + ".out.log")
    $stderr = Join-Path $RunDir ($RunId + "-" + ([System.IO.Path]::GetFileNameWithoutExtension($ScriptName)) + ".err.log")
    $env:PYTHONIOENCODING = "utf-8"
    $env:STOCK_REAL_SEND = "0"
    $env:STOCK_ENABLE_N8N_TRIGGER = "0"
    $env:STOCK_ENABLE_BROKER_API = "0"
    $env:STOCK_ENABLE_AUTO_TRADE = "0"
    $started = Get-Date
    $proc = Start-Process -FilePath "python.exe" `
        -ArgumentList @($scriptPath) `
        -WorkingDirectory $ScriptDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru
    $finished = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $finished) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    if ($finished) { $proc.Refresh() }
    $exitCode = if ($finished -and $null -ne $proc.ExitCode) { [int]$proc.ExitCode } elseif ($finished) { 0 } else { -999 }
    return [ordered]@{
        script = $ScriptName
        path = $scriptPath
        started_at = $started.ToString("yyyy-MM-dd HH:mm:ss")
        ended_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        exit_code = $exitCode
        success = [bool]($finished -and $exitCode -eq 0)
        timed_out = [bool](-not $finished)
        stdout_log = $stdout
        stderr_log = $stderr
    }
}

$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$logPath = Join-Path $logDir ($runId + "-sample-pool-weekly.json")
$globalMutex = New-Object System.Threading.Mutex($false, "Global\JiegeIntelligentSystemSchedulerGlobalLock")
$taskMutex = New-Object System.Threading.Mutex($false, "Global\JiegeStockSamplePoolWeeklyMaintenance")
$globalLock = $false
$taskLock = $false

try {
    $globalLock = $globalMutex.WaitOne(0)
    if (-not $globalLock) {
        $locked = [ordered]@{ status = "locked_by_global_scheduler"; task = "sample_pool_weekly"; time = Get-Date -Format "yyyy-MM-dd HH:mm:ss" }
        Write-JsonFile -Path $logPath -Value $locked
        $locked | ConvertTo-Json -Depth 10
        exit 0
    }
    $taskLock = $taskMutex.WaitOne(0)
    if (-not $taskLock) {
        $locked = [ordered]@{ status = "locked"; task = "sample_pool_weekly"; time = Get-Date -Format "yyyy-MM-dd HH:mm:ss" }
        Write-JsonFile -Path $logPath -Value $locked
        $locked | ConvertTo-Json -Depth 10
        exit 0
    }

    $stockScriptDir = Join-Path $root "02杰哥扩展系统\01股票研究系统\02脚本"
    $actions = New-Object System.Collections.Generic.List[object]
    $actions.Add((Invoke-PythonScript -ScriptDir $stockScriptDir -ScriptName "生成2000只样本股票池.py" -RunDir $logDir -RunId $runId -TimeoutSeconds 3600))
    if ($actions[0].success) {
        $actions.Add((Invoke-PythonScript -ScriptDir $stockScriptDir -ScriptName "生成2000只样本池每周维护报告.py" -RunDir $logDir -RunId $runId -TimeoutSeconds 600))
    }
    $failed = @($actions | Where-Object { -not $_.success })
    $report = [ordered]@{
        status = if ($failed.Count -eq 0) { "completed" } else { "failed" }
        task_name = "杰哥智能化系统_样本池每周维护"
        actions = $actions
        failed_count = $failed.Count
        global_lock_acquired = $globalLock
        lock_acquired = $taskLock
        environment_locks = [ordered]@{
            STOCK_REAL_SEND = "0"
            STOCK_ENABLE_N8N_TRIGGER = "0"
            STOCK_ENABLE_BROKER_API = "0"
            STOCK_ENABLE_AUTO_TRADE = "0"
        }
        time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    Write-JsonFile -Path $logPath -Value $report
    $report | ConvertTo-Json -Depth 20
    if ($failed.Count -gt 0) { exit 1 }
    exit 0
}
finally {
    if ($taskLock) { $taskMutex.ReleaseMutex() | Out-Null }
    if ($globalLock) { $globalMutex.ReleaseMutex() | Out-Null }
    $taskMutex.Dispose()
    $globalMutex.Dispose()
}
