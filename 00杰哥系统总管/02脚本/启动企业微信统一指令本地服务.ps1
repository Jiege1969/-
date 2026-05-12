# ============================================================
# Name: start-wecom-unified-command-local-service.ps1
# Purpose: Start the WeCom unified command local service on 127.0.0.1:19310.
# Trigger: Manual PowerShell execution or Windows Scheduled Task at user logon.
# Dependencies: Python; 02 extension public WeCom access component local service entry script.
# Owner system: 00 system manager.
# Writes: PID file and service logs under 02 extension public WeCom access component log directory.
# Safety: Binds only to 127.0.0.1; does not send WeCom messages, trigger n8n, write databases, call broker APIs, or trade.
# Change log: 2026-05-04 created managed launcher for local unified command service.
# ============================================================

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$serviceScript = Join-Path $root "02杰哥扩展系统\00公共组件\企业微信接入设置\02脚本\企业微信统一指令本地服务入口.py"
$logDir = Join-Path $root "02杰哥扩展系统\00公共组件\企业微信接入设置\04日志\统一指令本地服务"
$pidFile = Join-Path $logDir "wecom-unified-local-service.pid"
$pythonCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Python\pythoncore-3.14-64\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\python.exe"),
    "python.exe"
)
$pythonExe = $pythonCandidates | Where-Object { $_ -eq "python.exe" -or (Test-Path $_) } | Select-Object -First 1

if (-not (Test-Path $serviceScript)) {
    throw "service script not found: $serviceScript"
}

$existing = Get-NetTCPConnection -LocalPort 19310 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" } | Select-Object -First 1
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
if ($existing) {
    Set-Content -Path $pidFile -Value $existing.OwningProcess -Encoding ASCII
    Write-Output "port 19310 already in use"
    Write-Output "recorded existing listener pid: $($existing.OwningProcess)"
    $existing | Select-Object LocalAddress,LocalPort,State,OwningProcess
    exit 0
}

$stdout = Join-Path $logDir "wecom-unified-local-service.stdout.log"
$stderr = Join-Path $logDir "wecom-unified-local-service.stderr.log"
$proc = Start-Process -FilePath $pythonExe -ArgumentList @($serviceScript) -WorkingDirectory (Split-Path -Parent $serviceScript) -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
Start-Sleep -Seconds 2

$listener = Get-NetTCPConnection -LocalPort 19310 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" } | Select-Object -First 1
if ($listener) {
    Set-Content -Path $pidFile -Value $listener.OwningProcess -Encoding ASCII
    $recordedPid = $listener.OwningProcess
} else {
    Set-Content -Path $pidFile -Value $proc.Id -Encoding ASCII
    $recordedPid = $proc.Id
}

Write-Output "started WeCom unified command local service"
Write-Output "launcher pid: $($proc.Id)"
Write-Output "recorded pid: $recordedPid"
Write-Output "url: http://127.0.0.1:19310/health"

