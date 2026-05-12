# ============================================================
# Name: stop-v3-agent-brain-test.ps1
# Purpose: Stop the v3 agent brain test service started by the launcher.
# Trigger: Manual PowerShell execution by the system manager.
# Dependencies: PID file under the v3 log directory.
# Owner system: 00 system manager.
# Writes: Removes only the v3 test PID file.
# Safety: Stops only the PID recorded by the v3 test launcher.
# Change log: 2026-04-26 created alpha test stopper.
# ============================================================

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$coreRoot = Get-ChildItem -Path $root -Directory | Where-Object { $_.Name -like "01*" } | Select-Object -First 1
if (-not $coreRoot) { throw "core root not found under $root" }

$logRoot = Get-ChildItem -Path $coreRoot.FullName -Directory | Where-Object { $_.Name -like "04*" } | Select-Object -First 1
if (-not $logRoot) { throw "log root not found under $($coreRoot.FullName)" }

$logDir = Join-Path $logRoot.FullName "agent-brain-test"
$pidFile = Join-Path $logDir "v3-agent-brain.pid"

if (-not (Test-Path $pidFile)) {
    Write-Output "pid file not found; service may already be stopped"
    exit 0
}

$pidText = (Get-Content -Path $pidFile -Raw).Trim()
if (-not $pidText) {
    Remove-Item -Path $pidFile -Force
    Write-Output "empty pid file removed"
    exit 0
}

$proc = Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue
if ($proc) {
    Stop-Process -Id $proc.Id -Force
    Write-Output "stopped process pid: $($proc.Id)"
} else {
    Write-Output "process not found; removing stale pid file"
}

Remove-Item -Path $pidFile -Force
