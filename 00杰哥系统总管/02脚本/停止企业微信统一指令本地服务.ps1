# ============================================================
# Name: stop-wecom-unified-command-local-service.ps1
# Purpose: Stop the WeCom unified command local service on 127.0.0.1:19310.
# Trigger: Manual PowerShell execution by the system manager.
# Dependencies: PID file or current listener on port 19310.
# Owner system: 00 system manager.
# Writes: Updates no business data; may remove only the service process.
# Safety: Stops only the process recorded for or listening on 127.0.0.1:19310; does not touch stock services, n8n, Docker, databases, broker APIs, or trading.
# Change log: 2026-05-04 created managed stopper for local unified command service.
# ============================================================

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$logDir = Join-Path $root "02杰哥扩展系统\06企业微信助手系统\04日志\统一指令本地服务"
$pidFile = Join-Path $logDir "wecom-unified-local-service.pid"
$pids = @()

if (Test-Path $pidFile) {
    $content = Get-Content -Path $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($content -match '^\d+$') {
        $pids += [int]$content
    }
}

$listener = Get-NetTCPConnection -LocalPort 19310 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" } | Select-Object -First 1
if ($listener) {
    $pids += [int]$listener.OwningProcess
}

$pids = $pids | Select-Object -Unique
if (-not $pids -or $pids.Count -eq 0) {
    Write-Output "no listener found on port 19310"
    exit 0
}

foreach ($servicePid in $pids) {
    $proc = Get-Process -Id $servicePid -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $servicePid -Force
        Write-Output "stopped pid: $servicePid"
    }
}
