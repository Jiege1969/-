# ============================================================
# Name: read_only_status_check.ps1
# Purpose: Collect machine, Docker, port, GPU, and v3 inventory status.
# Trigger: Manual execution.
# Dependency: PowerShell, Docker, optional nvidia-smi.
# System: 00 system manager.
# Created: 2026-04-26.
# Notes: Read-only outside v3. Writes snapshots only under this v3 tree.
# ============================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $PSCommandPath
$ManagerDir = Split-Path -Parent $ScriptDir
$Root = Split-Path -Parent $ManagerDir

$DataDir = Get-ChildItem -LiteralPath $ManagerDir -Directory | Where-Object { $_.Name -like "03*" } | Select-Object -First 1
$LogRootDir = Get-ChildItem -LiteralPath $ManagerDir -Directory | Where-Object { $_.Name -like "04*" } | Select-Object -First 1

if (-not $DataDir) { throw "Data directory not found under manager directory." }
if (-not $LogRootDir) { throw "Log directory not found under manager directory." }

$SnapshotDirPath = Join-Path $DataDir.FullName "D盘瘦身审计"
if (-not (Test-Path -LiteralPath $SnapshotDirPath)) {
    New-Item -ItemType Directory -Path $SnapshotDirPath -Force | Out-Null
}

$LogDirPath = Join-Path $LogRootDir.FullName "状态检查"
if (-not (Test-Path -LiteralPath $LogDirPath)) {
    New-Item -ItemType Directory -Path $LogDirPath -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SnapshotPath = Join-Path $SnapshotDirPath "snapshot_最新.json"
$LogPath = Join-Path $LogDirPath "read_only_status_check_最新.log"

function Invoke-Safe {
    param(
        [scriptblock]$Script,
        [object]$Fallback = $null
    )
    try {
        & $Script
    } catch {
        $Fallback
    }
}

function Test-Http {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 5 -UseBasicParsing
        [pscustomobject]@{
            url = $Url
            ok = $true
            status_code = [int]$response.StatusCode
        }
    } catch {
        [pscustomobject]@{
            url = $Url
            ok = $false
            error = $_.Exception.Message
        }
    }
}

function Test-LabeledHttp {
    param(
        [string]$Url,
        [string]$Role,
        [bool]$Required = $true
    )
    $result = Test-Http $Url
    $result | Add-Member -NotePropertyName role -NotePropertyValue $Role -Force
    $result | Add-Member -NotePropertyName required -NotePropertyValue $Required -Force
    if (-not $Required) {
        $result | Add-Member -NotePropertyName current_scope -NotePropertyValue "historical registry; failure is allowed" -Force
    } else {
        $result | Add-Member -NotePropertyName current_scope -NotePropertyValue "current dependency" -Force
    }
    $result
}

function Test-HistoricalPortClosed {
    param(
        [int]$Port,
        [string]$Role
    )
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
    [pscustomobject]@{
        url = "tcp://127.0.0.1:$Port"
        ok = ($listeners.Count -eq 0)
        status_code = $null
        role = $Role
        required = $false
        current_scope = "historical port; expected closed; tcp listen check only, no HTTP touch"
        listener_count = $listeners.Count
    }
}

$disk = Get-PSDrive -PSProvider FileSystem | ForEach-Object {
    [pscustomobject]@{
        name = $_.Name
        used_gb = [math]::Round($_.Used / 1GB, 2)
        free_gb = [math]::Round($_.Free / 1GB, 2)
    }
}

$dockerPs = Invoke-Safe {
    docker ps --format '{{json .}}' | ForEach-Object { $_ | ConvertFrom-Json }
} @()

$dockerImages = Invoke-Safe {
    docker images --format '{{json .}}' | ForEach-Object { $_ | ConvertFrom-Json }
} @()

$gpu = Invoke-Safe {
    nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,temperature.gpu,power.draw,power.limit,utilization.gpu --format=csv,noheader,nounits |
        ForEach-Object {
            $parts = $_ -split ',\s*'
            [pscustomobject]@{
                name = $parts[0]
                driver_version = $parts[1]
                memory_total_mib = [int]$parts[2]
                memory_used_mib = [int]$parts[3]
                memory_free_mib = [int]$parts[4]
                temperature_gpu = [int]$parts[5]
                power_draw_w = $parts[6]
                power_limit_w = $parts[7]
                utilization_gpu_percent = [int]$parts[8]
            }
        }
} @()

$ports = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalAddress -in @("127.0.0.1","0.0.0.0","::","::1") } |
    Sort-Object LocalPort |
    Select-Object LocalAddress,LocalPort,OwningProcess,@{Name="ProcessName";Expression={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}}

$checks = @(
    Test-HistoricalPortClosed 18080 "historical local agent gateway port; cloud 18080 is separate tunnel loopback"
    Test-HistoricalPortClosed 18100 "historical local agent core port"
    Test-HistoricalPortClosed 18200 "historical local ops guardian port"
    Test-HistoricalPortClosed 18300 "historical reserved stock service port"
    Test-HistoricalPortClosed 18400 "historical local voice service port"
    Test-HistoricalPortClosed 18679 "historical local n8n port"
    Test-LabeledHttp "http://127.0.0.1:28679/healthz" "current v3 n8n"
    Test-HistoricalPortClosed 19134 "historical local stock Ollama port"
    Test-LabeledHttp "http://127.0.0.1:29134/api/tags" "current v3 Ollama"
    Test-LabeledHttp "http://127.0.0.1:28100/health" "current v3 agent brain"
    Test-LabeledHttp "http://127.0.0.1:11434/api/tags" "current WSL OpenClaw Ollama dependency"
)

$v3Files = Get-ChildItem -LiteralPath $Root -Recurse -File -Force -ErrorAction SilentlyContinue
$v3Dirs = Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force -ErrorAction SilentlyContinue

$snapshot = [pscustomobject]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    root = $Root
    note = "Read-only snapshot. No external system modified. No data migrated. No secret read."
    disk = $disk
    gpu = $gpu
    docker_containers = $dockerPs
    docker_images = $dockerImages
    listening_ports = $ports
    http_checks = $checks
    v3_inventory = [pscustomobject]@{
        directory_count = $v3Dirs.Count
        file_count = $v3Files.Count
        total_kb = [math]::Round((($v3Files | Measure-Object Length -Sum).Sum / 1KB), 2)
    }
}

$json = $snapshot | ConvertTo-Json -Depth 8
$json | Set-Content -LiteralPath $SnapshotPath -Encoding UTF8

$summary = @()
$summary += "Jiege v3 read-only status check"
$summary += "Time: $($snapshot.generated_at)"
$summary += "Snapshot: $SnapshotPath"
$summary += "v3 files: $($snapshot.v3_inventory.file_count)"
$summary += "v3 directories: $($snapshot.v3_inventory.directory_count)"
$summary += "v3 total KB: $($snapshot.v3_inventory.total_kb)"
$summary += "Docker containers: $($dockerPs.Count)"
$requiredChecks = @($checks | Where-Object { $_.required -eq $true })
$historicalChecks = @($checks | Where-Object { $_.required -eq $false })
$summary += "Required HTTP checks OK: $(($requiredChecks | Where-Object { $_.ok }).Count)/$($requiredChecks.Count)"
$summary += "Historical registry HTTP checks OK: $(($historicalChecks | Where-Object { $_.ok }).Count)/$($historicalChecks.Count) (failures allowed)"
$summary | Set-Content -LiteralPath $LogPath -Encoding UTF8

$summary -join [Environment]::NewLine
