# ============================================================
# Name: start-v3-agent-brain-test.ps1
# Purpose: Start the v3 agent brain test service on 127.0.0.1:28100.
# Trigger: Manual PowerShell execution by the system manager.
# Dependencies: Python venv under the v3 agent brain service directory.
# Owner system: 00 system manager.
# Writes: PID file and service logs under 01 core system log directory.
# Safety: Does not touch old systems, production containers, or external ports.
# Change log: 2026-04-26 created alpha test launcher.
# ============================================================

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$coreRoot = Get-ChildItem -Path $root -Directory | Where-Object { $_.Name -like "01*" } | Select-Object -First 1
if (-not $coreRoot) { throw "core root not found under $root" }

$scriptRoot = Get-ChildItem -Path $coreRoot.FullName -Directory | Where-Object { $_.Name -like "02*" } | Select-Object -First 1
if (-not $scriptRoot) { throw "script root not found under $($coreRoot.FullName)" }

$serviceRoot = Get-ChildItem -Path $scriptRoot.FullName -Directory | Where-Object { Test-Path (Join-Path $_.FullName ".venv\Scripts\python.exe") } | Select-Object -First 1
if (-not $serviceRoot) { throw "service root not found under $($scriptRoot.FullName)" }

$logRoot = Get-ChildItem -Path $coreRoot.FullName -Directory | Where-Object { $_.Name -like "04*" } | Select-Object -First 1
if (-not $logRoot) { throw "log root not found under $($coreRoot.FullName)" }

$serviceDir = $serviceRoot.FullName
$logDir = Join-Path $logRoot.FullName "agent-brain-test"
$pidFile = Join-Path $logDir "v3-agent-brain.pid"
$pythonExe = Join-Path $serviceDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "venv python not found: $pythonExe"
}

$existing = Get-NetTCPConnection -LocalPort 28100 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($existing) {
    Write-Output "port 28100 already in use"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $listener = $existing | Select-Object -First 1
    Set-Content -Path $pidFile -Value $listener.OwningProcess -Encoding ASCII
    Write-Output "recorded existing listener pid: $($listener.OwningProcess)"
    $existing | Select-Object LocalAddress,LocalPort,State,OwningProcess
    exit 0
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stdout = Join-Path $logDir "v3-agent-brain.stdout.log"
$stderr = Join-Path $logDir "v3-agent-brain.stderr.log"
$args = "-m uvicorn app:app --host 127.0.0.1 --port 28100"

$proc = Start-Process -FilePath $pythonExe -ArgumentList $args -WorkingDirectory $serviceDir -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
Start-Sleep -Seconds 2
$listener = Get-NetTCPConnection -LocalPort 28100 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" } | Select-Object -First 1
if ($listener) {
    Set-Content -Path $pidFile -Value $listener.OwningProcess -Encoding ASCII
    $recordedPid = $listener.OwningProcess
} else {
    Set-Content -Path $pidFile -Value $proc.Id -Encoding ASCII
    $recordedPid = $proc.Id
}

Write-Output "started v3 agent brain test service"
Write-Output "launcher pid: $($proc.Id)"
Write-Output "recorded pid: $recordedPid"
Write-Output "url: http://127.0.0.1:28100/health"
