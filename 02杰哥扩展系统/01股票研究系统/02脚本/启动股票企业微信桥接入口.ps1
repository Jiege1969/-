<#
Name: StartStockWeComBridge.ps1
Purpose: Start the local stock WeCom bridge service for gray routing from OpenClaw or n8n to the stock assistant.
Trigger: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\启动股票企业微信桥接入口.ps1"
Dependencies: Python; 股票企业微信桥接入口.py; running stock assistant on 127.0.0.1:19300.
System: 02JiegeExtensionSystem/01StockResearchSystem
Safety: Bind only 127.0.0.1:19302; do not write old system; do not trigger trading; default dry-run unless response_url and real_send are both provided.
ChangeLog: 2026-04-29 Create stock WeCom bridge start script.
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$systemRoot = Split-Path -Parent $scriptDir

function ConvertFrom-Utf8Base64 {
    param([Parameter(Mandatory = $true)][string]$Value)
    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Value))
}

# Windows PowerShell 5.x may misread UTF-8 script literals without BOM.
# Keep Chinese path segments as UTF-8 base64 so the start script remains stable.
$entryScriptName = ConvertFrom-Utf8Base64 "6IKh56Wo5LyB5Lia5b6u5L+h5qGl5o6l5YWl5Y+jLnB5"
$logRootName = ConvertFrom-Utf8Base64 "MDTml6Xlv5c="
$logChildName = ConvertFrom-Utf8Base64 "5LyB5Lia5b6u5L+h5qGl5o6l5YWl5Y+j"

$entryScript = Join-Path $scriptDir $entryScriptName
$logDir = Join-Path (Join-Path $systemRoot $logRootName) $logChildName
$pidRecord = Join-Path $logDir "stock-wework-bridge-service.pid.json"
$stdoutLog = Join-Path $logDir "stock-wework-bridge-service-stdout.log"
$stderrLog = Join-Path $logDir "stock-wework-bridge-service-stderr.log"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Resolve-RealPython {
    try {
        $pythonPath = & py -3 -c "import sys; print(sys.executable)" 2>$null
        if ($pythonPath -and (Test-Path -LiteralPath $pythonPath.Trim())) {
            return $pythonPath.Trim()
        }
    } catch {}
    return "python"
}

$listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 19302 -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    $ownerPid = ($listener | Select-Object -First 1).OwningProcess
    $result = @{
        status = "already_running_or_port_in_use"
        port = 19302
        process_id = $ownerPid
        health = "http://127.0.0.1:19302/health"
        time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    $result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $pidRecord -Encoding UTF8
    $result | ConvertTo-Json -Depth 5
    exit 0
}

$pythonExe = Resolve-RealPython
$process = Start-Process -FilePath $pythonExe -ArgumentList @($entryScript) -WorkingDirectory $systemRoot -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru
Start-Sleep -Seconds 2
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:19302/health" -Method Get -TimeoutSec 5
} catch {
    $health = @{ status = "health_check_failed"; error = $_.Exception.Message }
}
$activeListener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 19302 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
$activeProcessId = $process.Id
if ($activeListener) { $activeProcessId = $activeListener.OwningProcess }
$result = @{
    status = "started"
    starter_process_id = $process.Id
    process_id = $activeProcessId
    health = "http://127.0.0.1:19302/health"
    health_result = $health
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $pidRecord -Encoding UTF8
$result | ConvertTo-Json -Depth 8
