# ============================================================
# Name: prebuild_check.ps1
# Purpose: Validate v3 skeleton before formal build work.
# Trigger: Manual execution before implementation/migration.
# Dependency: PowerShell only.
# System: 00 system manager.
# Created: 2026-04-26.
# Notes: Only reads v3 files and writes report under v3 logs/data.
# ============================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $PSCommandPath
$ManagerDir = Split-Path -Parent $ScriptDir
$Root = Split-Path -Parent $ManagerDir

$DataDir = Get-ChildItem -LiteralPath $ManagerDir -Directory | Where-Object { $_.Name -like "03*" } | Select-Object -First 1
$LogRootDir = Get-ChildItem -LiteralPath $ManagerDir -Directory | Where-Object { $_.Name -like "04*" } | Select-Object -First 1
$ConfigDir = Get-ChildItem -LiteralPath $ManagerDir -Directory | Where-Object { $_.Name -like "01*" } | Select-Object -First 1

if (-not $DataDir) { throw "Data directory not found." }
if (-not $LogRootDir) { throw "Log directory not found." }
if (-not $ConfigDir) { throw "Config directory not found." }

$MachineDir = Join-Path $ConfigDir.FullName "machine"
$LogDir = Get-ChildItem -LiteralPath $LogRootDir.FullName -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $LogDir) {
    $LogDirPath = Join-Path $LogRootDir.FullName "prebuild-check"
    New-Item -ItemType Directory -Path $LogDirPath -Force | Out-Null
} else {
    $LogDirPath = $LogDir.FullName
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportPath = Join-Path $LogDirPath "prebuild_check_$Timestamp.json"
$TextPath = Join-Path $LogDirPath "prebuild_check_$Timestamp.log"

$checks = New-Object System.Collections.Generic.List[object]

function Add-Check {
    param(
        [string]$Name,
        [bool]$Ok,
        [string]$Detail
    )
    $script:checks.Add([pscustomobject]@{
        name = $Name
        ok = $Ok
        detail = $Detail
    })
}

Add-Check "root exists" (Test-Path -LiteralPath $Root) $Root

$requiredTop = @(
    "00*",
    "01*",
    "02*",
    "03*",
    "09*"
)
foreach ($pattern in $requiredTop) {
    $found = Get-ChildItem -LiteralPath $Root -Directory | Where-Object { $_.Name -like $pattern } | Select-Object -First 1
    Add-Check "top directory $pattern" ([bool]$found) ($(if ($found) { $found.FullName } else { "missing" }))
}

$machineFiles = @(
    "service_registry.json",
    "port_registry.json",
    "model_router.json",
    "component_ownership.json",
    "backup_policy.json",
    "acceptance_criteria.json",
    "health_rules.json"
)

foreach ($name in $machineFiles) {
    $path = Join-Path $MachineDir $name
    if (-not (Test-Path -LiteralPath $path)) {
        Add-Check "machine config $name" $false "missing"
        continue
    }
    try {
        Get-Content -LiteralPath $path -Encoding UTF8 | ConvertFrom-Json | Out-Null
        Add-Check "machine config $name" $true "valid json"
    } catch {
        Add-Check "machine config $name" $false $_.Exception.Message
    }
}

$forbidden = @(
    "independent_system_root",
    "legacy_ollama_model_store",
    "v25_ollama_model_store"
)
foreach ($label in $forbidden) {
    Add-Check "forbidden asset registered $label" $true "must not touch during v3 prebuild"
}

$files = Get-ChildItem -LiteralPath $Root -Recurse -File -Force -ErrorAction SilentlyContinue
$dirs = Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force -ErrorAction SilentlyContinue
Add-Check "v3 inventory" $true ("files={0}; dirs={1}; kb={2}" -f $files.Count, $dirs.Count, [math]::Round((($files | Measure-Object Length -Sum).Sum / 1KB), 2))

$okCount = ($checks | Where-Object { $_.ok }).Count
$failCount = ($checks | Where-Object { -not $_.ok }).Count

$report = [pscustomobject]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    root = $Root
    ok = ($failCount -eq 0)
    ok_count = $okCount
    fail_count = $failCount
    checks = $checks
}

$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReportPath -Encoding UTF8

$lines = @()
$lines += "Jiege v3 prebuild check"
$lines += "Time: $($report.generated_at)"
$lines += "OK: $($report.ok)"
$lines += "Passed: $okCount"
$lines += "Failed: $failCount"
$lines += "Report: $ReportPath"
foreach ($c in $checks) {
    $status = if ($c.ok) { "OK" } else { "FAIL" }
    $lines += ("[{0}] {1} - {2}" -f $status, $c.name, $c.detail)
}
$lines | Set-Content -LiteralPath $TextPath -Encoding UTF8

$lines -join [Environment]::NewLine
