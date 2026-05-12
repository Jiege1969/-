<#
Name: StopStockWeComBridge.ps1
Purpose: Stop only the local stock WeCom bridge service bound to 127.0.0.1:19302.
Trigger: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\停止股票企业微信桥接入口.ps1"
Dependencies: Windows PowerShell; stock-wework-bridge-service.pid.json; local health endpoint 127.0.0.1:19302/health.
System: 02JiegeExtensionSystem/01StockResearchSystem
Safety: Stop only the verified new stock WeCom bridge process; do not stop stock assistant; do not stop public SSH tunnel; do not stop old system; do not trigger n8n; do not send WeCom; do not call broker APIs; do not trade.
ChangeLog: 2026-05-04 created controlled stop script for stock WeCom bridge reload.
Marker: stock-wework-bridge-stop
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$systemRoot = Split-Path -Parent $scriptDir

function ConvertFrom-Utf8Base64 {
    param([Parameter(Mandatory = $true)][string]$Value)
    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Value))
}

$logRootName = ConvertFrom-Utf8Base64 "MDTml6Xlv5c="
$logChildName = ConvertFrom-Utf8Base64 "5LyB5Lia5b6u5L+h5qGl5o6l5YWl5Y+j"
$pidRecord = Join-Path (Join-Path (Join-Path $systemRoot $logRootName) $logChildName) "stock-wework-bridge-service.pid.json"

$processId = $null
if (Test-Path -LiteralPath $pidRecord) {
    $record = Get-Content -LiteralPath $pidRecord -Encoding UTF8 | ConvertFrom-Json
    $processId = $record.process_id
}

if ($processId) {
    $recordedProcess = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if (-not $recordedProcess) {
        $processId = $null
    }
}

if (-not $processId) {
    $listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 19302 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        try {
            Invoke-RestMethod -Uri "http://127.0.0.1:19302/health" -Method Get -TimeoutSec 5 | Out-Null
            $processId = $listener.OwningProcess
        } catch {
            $processId = $null
        }
    }
}

if (-not $processId) {
    @{
        status = "stock_wecom_bridge_process_not_found"
        time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        stopped_public_tunnel = $false
        send_wecom = $false
        trade = $false
    } | ConvertTo-Json -Depth 5
    exit 0
}

$process = Get-Process -Id $processId -ErrorAction SilentlyContinue
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
    stopped_public_tunnel = $false
    send_wecom = $false
    trade = $false
} | ConvertTo-Json -Depth 5
