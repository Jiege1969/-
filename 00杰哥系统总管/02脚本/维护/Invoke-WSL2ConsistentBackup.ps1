param(
    [switch]$IUnderstandStopDockerAndWsl,
    [string]$TargetRoot = "F:\系统备份"
)

$ErrorActionPreference = "Stop"

if (-not $IUnderstandStopDockerAndWsl) {
    Write-Host "Refused: this backup requires stopping Docker/WSL."
    Write-Host "Run with -IUnderstandStopDockerAndWsl during a controlled maintenance window."
    exit 2
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$target = Join-Path $TargetRoot "WSL2一致性备份_$timestamp"
$manifestPath = Join-Path $target "backup_manifest.json"

$assets = @(
    "D:\杰哥智能化系统\01杰哥智能系统\03数据\WSL2\docker-desktop\disk\docker_data.vhdx",
    "D:\杰哥智能化系统\01杰哥智能系统\03数据\WSL2\Ubuntu-24.04\ext4.vhdx"
)

function Save-Text($Path, $Value) {
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $Value | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-WslVerboseText {
    try {
        return (wsl --list --verbose) -join "`n"
    } catch {
        return "wsl --list --verbose failed: $($_.Exception.Message)"
    }
}

function Test-WslRunning {
    $text = Get-WslVerboseText
    return ($text -match "Running")
}

New-Item -ItemType Directory -Path $target -Force | Out-Null

$pre = [ordered]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
    target = $target
    assets = $assets
    pre_wsl = Get-WslVerboseText
    pre_docker = (& docker ps --format "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}" 2>&1) -join "`n"
    safety = [ordered]@{
        trigger_n8n = $false
        send_wecom = $false
        call_broker_api = $false
        auto_trade = $false
    }
}
Save-Text (Join-Path $target "pre_status.json") ($pre | ConvertTo-Json -Depth 6)

Write-Host "Stopping WSL/Docker runtime with wsl --shutdown..."
wsl --shutdown

$deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $deadline) {
    if (-not (Test-WslRunning)) { break }
    Start-Sleep -Seconds 3
}

if (Test-WslRunning) {
    throw "WSL still has Running distributions after shutdown wait. Backup aborted before copying VHDX."
}

$copied = @()
foreach ($src in $assets) {
    if (-not (Test-Path -LiteralPath $src)) {
        throw "Missing asset: $src"
    }
    $dst = Join-Path $target (Split-Path -Leaf $src)
    Write-Host "Copying $src"
    Copy-Item -LiteralPath $src -Destination $dst -Force

    $srcItem = Get-Item -LiteralPath $src
    $dstItem = Get-Item -LiteralPath $dst
    $srcHash = Get-FileHash -LiteralPath $src -Algorithm SHA256
    $dstHash = Get-FileHash -LiteralPath $dst -Algorithm SHA256

    $copied += [ordered]@{
        source = $src
        destination = $dst
        source_bytes = $srcItem.Length
        destination_bytes = $dstItem.Length
        source_sha256 = $srcHash.Hash
        destination_sha256 = $dstHash.Hash
        match = (($srcItem.Length -eq $dstItem.Length) -and ($srcHash.Hash -eq $dstHash.Hash))
    }
}

$dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path -LiteralPath $dockerDesktop) {
    Write-Host "Starting Docker Desktop..."
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
} else {
    Write-Host "Docker Desktop executable not found at default path; start Docker manually if needed."
}

$health = [ordered]@{}
Start-Sleep -Seconds 20
try {
    $health.n8n = (Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:28679/healthz" -TimeoutSec 10).StatusCode
} catch {
    $health.n8n = $_.Exception.Message
}
try {
    $health.ollama = (Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:29134/api/tags" -TimeoutSec 15).StatusCode
} catch {
    $health.ollama = $_.Exception.Message
}
try {
    $health.redis_tcp = Test-NetConnection -ComputerName 127.0.0.1 -Port 26379 -InformationLevel Quiet
} catch {
    $health.redis_tcp = $_.Exception.Message
}

$manifest = [ordered]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
    target = $target
    copied = $copied
    all_hashes_match = -not ($copied | Where-Object { -not $_.match })
    post_wsl = Get-WslVerboseText
    post_docker = (& docker ps --format "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}" 2>&1) -join "`n"
    health = $health
    safety = [ordered]@{
        trigger_n8n = $false
        send_wecom = $false
        call_broker_api = $false
        auto_trade = $false
        hot_copy = $false
    }
}

Save-Text $manifestPath ($manifest | ConvertTo-Json -Depth 8)
Write-Host "WSL2 consistent backup completed: $target"
Write-Host "Manifest: $manifestPath"
