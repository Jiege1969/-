<#
Name: StopStockAssistant.ps1
Purpose: Stop the local stock assistant experience service for the new stock research system.
Trigger: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\停止股票助手.ps1"
Dependencies: Windows PowerShell; stock-assistant-service.pid.json.
System: 02JiegeExtensionSystem/01StockResearchSystem
Safety: Stop only the recorded new stock assistant process; do not stop old system; do not stop Docker; do not trigger n8n; do not send WeCom.
ChangeLog: 2026-04-28 Create stock assistant stop script.
Marker: stock-assistant-experience-stop
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$systemRoot = Split-Path -Parent $scriptDir
$logRootName = "04" + [char]0x65E5 + [char]0x5FD7
$assistantLogName = "" + [char]0x52A9 + [char]0x624B + [char]0x5165 + [char]0x53E3
$pidRecord = Join-Path (Join-Path (Join-Path $systemRoot $logRootName) $assistantLogName) "stock-assistant-service.pid.json"

$processId = $null
if (Test-Path -LiteralPath $pidRecord) {
    $record = Get-Content -LiteralPath $pidRecord -Encoding UTF8 | ConvertFrom-Json
    $processId = $record.process_id
}

if (-not $processId) {
    $listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 19300 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        try {
            Invoke-RestMethod -Uri "http://127.0.0.1:19300/health" -Method Get -TimeoutSec 5 | Out-Null
            $processId = $listener.OwningProcess
        } catch {
            $processId = $null
        }
    }
}

if (-not $processId) {
    @{
        status = "stock_assistant_process_not_found"
        time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    } | ConvertTo-Json -Depth 5
    exit 0
}

$process = Get-Process -Id $processId -ErrorAction SilentlyContinue
if (-not $process) {
    $listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 19300 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        try {
            Invoke-RestMethod -Uri "http://127.0.0.1:19300/health" -Method Get -TimeoutSec 5 | Out-Null
            $processId = $listener.OwningProcess
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        } catch {
            $process = $null
        }
    }
}
if ($process) {
    Stop-Process -Id $processId -Force
    $status = "stopped"
} else {
    $status = "process_not_found"
}

@{
    status = $status
    process_id = $processId
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 5
