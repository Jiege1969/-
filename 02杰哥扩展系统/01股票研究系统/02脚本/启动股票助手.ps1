<#
Name: StartStockAssistant.ps1
Purpose: Start the local stock assistant experience service for the new stock research system.
Trigger: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\启动股票助手.ps1"
Dependencies: Python; stock assistant Python entry script; stock assistant config.
System: 02JiegeExtensionSystem/01StockResearchSystem
Safety: Bind only 127.0.0.1:19300; do not stop old system; do not use old 18300 port; do not trigger n8n; do not send WeCom; do not call broker APIs.
ChangeLog: 2026-04-28 Create stock assistant start script.
Marker: stock-assistant-experience-start
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$systemRoot = Split-Path -Parent $scriptDir
$entryScript = Get-ChildItem -LiteralPath $scriptDir -Filter "*.py" | Where-Object {
    Select-String -LiteralPath $_.FullName -Pattern "stock-assistant-experience-service" -SimpleMatch -Quiet
} | Select-Object -First 1
if (-not $entryScript) {
    throw "stock assistant entry script not found by marker"
}
$logRootName = "04" + [char]0x65E5 + [char]0x5FD7
$assistantLogName = "" + [char]0x52A9 + [char]0x624B + [char]0x5165 + [char]0x53E3
$logDir = Join-Path (Join-Path $systemRoot $logRootName) $assistantLogName
$pidRecord = Join-Path $logDir "stock-assistant-service.pid.json"
$stdoutLog = Join-Path $logDir "stock-assistant-service-stdout.log"
$stderrLog = Join-Path $logDir "stock-assistant-service-stderr.log"
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

$listener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 19300 -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    $ownerPid = ($listener | Select-Object -First 1).OwningProcess
    $result = @{
        status = "already_running_or_port_in_use"
        port = 19300
        process_id = $ownerPid
        home = "http://127.0.0.1:19300/"
        time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    $result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $pidRecord -Encoding UTF8
    $result | ConvertTo-Json -Depth 5
    exit 0
}

$pythonExe = Resolve-RealPython
$process = Start-Process -FilePath $pythonExe -ArgumentList @($entryScript.FullName) -WorkingDirectory $systemRoot -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru
Start-Sleep -Seconds 2

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:19300/health" -Method Get -TimeoutSec 5
} catch {
    $health = @{
        status = "health_check_failed"
        error = $_.Exception.Message
    }
}
$activeListener = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 19300 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
$activeProcessId = $process.Id
if ($activeListener) {
    $activeProcessId = $activeListener.OwningProcess
}

$result = @{
    status = "started"
    starter_process_id = $process.Id
    process_id = $activeProcessId
    home = "http://127.0.0.1:19300/"
    health = $health
    time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $pidRecord -Encoding UTF8
$result | ConvertTo-Json -Depth 8
