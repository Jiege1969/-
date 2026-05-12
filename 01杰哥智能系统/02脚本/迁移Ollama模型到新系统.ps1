# ============================================================
# Name: migrate-ollama-models-to-v3.ps1
# Purpose: Copy Ollama model data from the protected old stock system path into the new v3 system path.
# Trigger: powershell -ExecutionPolicy Bypass -File 迁移Ollama模型到新系统.ps1
# Owner system: 01 core system.
# Dependencies: PowerShell; robocopy; source path D:\杰哥智能体操作系统\03_系统数据\01_模型数据\ollama.
# Safety: Copy-only migration. Does not delete, move, overwrite old data, stop old jiege_* services, send messages, write old system data, or call broker APIs/trading.
# Change log: 2026-04-28 created copy-only Ollama model migration script.
# ============================================================

$ErrorActionPreference = "Stop"

function Join-Chars {
    param([int[]]$Codes)
    return -join ($Codes | ForEach-Object { [char]$_ })
}

$oldRootName = Join-Chars @(0x6770, 0x54E5, 0x667A, 0x80FD, 0x4F53, 0x64CD, 0x4F5C, 0x7CFB, 0x7EDF)
$newRootName = Join-Chars @(0x6770, 0x54E5, 0x667A, 0x80FD, 0x5316, 0x7CFB, 0x7EDF)
$managerCoreName = "01" + (Join-Chars @(0x6770, 0x54E5, 0x667A, 0x80FD, 0x7CFB, 0x7EDF))
$systemDataName = "03_" + (Join-Chars @(0x7CFB, 0x7EDF, 0x6570, 0x636E))
$modelDataName = "01_" + (Join-Chars @(0x6A21, 0x578B, 0x6570, 0x636E))
$dataDirName = "03" + (Join-Chars @(0x6570, 0x636E))
$logDirName = "04" + (Join-Chars @(0x65E5, 0x5FD7))
$aiBaseName = Join-Chars @(0x667A, 0x80FD, 0x5E95, 0x5EA7)

$source = Join-Path (Join-Path (Join-Path ("D:\" + $oldRootName) $systemDataName) $modelDataName) "ollama"
$newCoreRoot = Join-Path ("D:\" + $newRootName) $managerCoreName
$target = Join-Path (Join-Path $newCoreRoot $dataDirName) "ollama"
$logDir = Join-Path (Join-Path $newCoreRoot $logDirName) $aiBaseName

New-Item -ItemType Directory -Force -Path $target, $logDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$robocopyLog = Join-Path $logDir "ollama-model-copy-$timestamp.log"
$reportPath = Join-Path $logDir "ollama-model-copy-$timestamp.json"
$latestPath = Join-Path $logDir "ollama-model-copy-latest.json"

function Get-DirectorySummary {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{ exists = $false; files = 0; size_gb = 0 }
    }
    $items = Get-ChildItem -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
    $size = ($items | Measure-Object -Property Length -Sum).Sum
    return [pscustomobject]@{
        exists = $true
        files = ($items | Measure-Object).Count
        size_gb = [math]::Round(($size / 1GB), 3)
    }
}

if (-not (Test-Path -LiteralPath $source)) {
    throw "Source path missing: $source"
}

$beforeSource = Get-DirectorySummary -Path $source
$beforeTarget = Get-DirectorySummary -Path $target

robocopy $source $target /E /COPY:DAT /DCOPY:DAT /R:1 /W:2 /MT:8 /NP /TEE /LOG:$robocopyLog
$code = $LASTEXITCODE

$afterSource = Get-DirectorySummary -Path $source
$afterTarget = Get-DirectorySummary -Path $target
$ok = $code -le 7

$report = [pscustomobject]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    ok = $ok
    robocopy_exit_code = $code
    source = $source
    target = $target
    before_source = $beforeSource
    before_target = $beforeTarget
    after_source = $afterSource
    after_target = $afterTarget
    robocopy_log = $robocopyLog
    safety = [pscustomobject]@{
        copy_only = $true
        old_data_delete = $false
        old_data_move = $false
        old_jiege_service_stop = $false
        wework_send = $false
        n8n_trigger = $false
        broker_api = $false
        auto_trade = $false
    }
}

$report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding UTF8
$report | ConvertTo-Json -Depth 8 | Set-Content -Path $latestPath -Encoding UTF8
$report | ConvertTo-Json -Depth 8

if (-not $ok) {
    exit 1
}
