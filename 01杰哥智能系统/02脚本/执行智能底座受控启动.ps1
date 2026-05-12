# ============================================================
# Name: start-v3-ai-base-controlled.ps1
# Purpose: Start only the v3 Ollama and Redis base services after safety checks.
# Trigger: powershell -ExecutionPolicy Bypass -File 执行智能底座受控启动.ps1
# Owner system: 01 core system.
# Dependencies: Docker Desktop; docker compose; docker-compose.智能底座.yml.
# Safety: Does not delete files, does not stop or restart old jiege_* services, does not trigger n8n, does not send WeWork messages, does not write old system data, and does not call broker APIs or trading.
# Change log: 2026-04-28 created controlled v3 AI base startup script.
# ============================================================

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$coreRoot = Split-Path -Parent $scriptDir

function Join-Chars {
    param([int[]]$Codes)
    return -join ($Codes | ForEach-Object { [char]$_ })
}

$configDirName = "01" + (Join-Chars @(0x914D, 0x7F6E))
$dataDirName = "03" + (Join-Chars @(0x6570, 0x636E))
$logDirName = "04" + (Join-Chars @(0x65E5, 0x5FD7))
$aiBaseName = Join-Chars @(0x667A, 0x80FD, 0x5E95, 0x5EA7)

$configDir = Join-Path $coreRoot $configDirName
$dataDir = Join-Path $coreRoot $dataDirName
$logDir = Join-Path (Join-Path $coreRoot $logDirName) $aiBaseName
$composePath = Join-Path $configDir ("docker-compose." + $aiBaseName + ".yml")
$ollamaData = Join-Path $dataDir "ollama"
$redisData = Join-Path $dataDir "redis"

New-Item -ItemType Directory -Force -Path $ollamaData, $redisData, $logDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportPath = Join-Path $logDir "v3-ai-base-controlled-start-$timestamp.json"
$latestPath = Join-Path $logDir "v3-ai-base-controlled-start-latest.json"

function Write-Report {
    param(
        [bool]$Ok,
        [string]$Stage,
        [string]$Message,
        [object]$Extra = $null
    )

    $report = [pscustomobject]@{
        generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        ok = $Ok
        stage = $Stage
        message = $Message
        compose = $composePath
        containers = @("jiege_v3_ollama", "jiege_v3_redis")
        ports = @{
            ollama = "127.0.0.1:29134"
            redis = "127.0.0.1:26379"
        }
        data_paths = @{
            ollama = $ollamaData
            redis = $redisData
        }
        safety = [pscustomobject]@{
            old_jiege_service_stop = $false
            old_system_write = $false
            n8n_trigger = $false
            wework_send = $false
            production_db_write = $false
            broker_api = $false
            auto_trade = $false
        }
        extra = $Extra
    }

    $report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding UTF8
    $report | ConvertTo-Json -Depth 8 | Set-Content -Path $latestPath -Encoding UTF8
    return $report
}

if (-not (Test-Path -LiteralPath $composePath)) {
    Write-Report -Ok $false -Stage "preflight" -Message "compose file missing" | Out-Null
    exit 1
}

$protectedRunning = docker ps --format "{{.Names}}" | Where-Object { $_ -in @("jiege_ollama", "jiege_redis", "jiege_n8n", "jiege_stock_service") }

$port29134 = netstat -ano | Select-String ":29134"
$port26379 = netstat -ano | Select-String ":26379"
$runningV3 = docker ps --format "{{.Names}}" | Where-Object { $_ -in @("jiege_v3_ollama", "jiege_v3_redis") }

if ($port29134 -and ($runningV3 -notcontains "jiege_v3_ollama")) {
    Write-Report -Ok $false -Stage "preflight" -Message "port 29134 is occupied by another process" | Out-Null
    exit 1
}

if ($port26379 -and ($runningV3 -notcontains "jiege_v3_redis")) {
    Write-Report -Ok $false -Stage "preflight" -Message "port 26379 is occupied by another process" | Out-Null
    exit 1
}

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$upOutput = & docker compose -f $composePath up -d 2>&1
$composeExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
$upOutputText = @($upOutput | ForEach-Object { $_.ToString() })
if ($composeExitCode -ne 0) {
    Write-Report -Ok $false -Stage "docker-compose-up" -Message "docker compose up failed" -Extra $upOutputText | Out-Null
    exit 1
}

Start-Sleep -Seconds 5

function Test-ContainerMountRoot {
    param(
        [string]$Container,
        [string]$Destination
    )

    $mountInfo = & docker exec $Container sh -lc "cat /proc/self/mountinfo | grep ' $Destination '" 2>&1
    $mountText = @($mountInfo | ForEach-Object { $_.ToString() }) -join "`n"
    return [pscustomobject]@{
        container = $Container
        destination = $Destination
        ok = ($mountText -and ($mountText -notmatch "\s/01"))
        mount_info = $mountText
    }
}

$mountChecks = @(
    (Test-ContainerMountRoot -Container "jiege_v3_ollama" -Destination "/root/.ollama"),
    (Test-ContainerMountRoot -Container "jiege_v3_redis" -Destination "/data")
)

if (($mountChecks | Where-Object { -not $_.ok }).Count -gt 0) {
    Write-Report -Ok $false -Stage "mount-root-check" -Message "container mounted old D root path after startup" -Extra $mountChecks | Out-Null
    exit 1
}

$ollamaHealth = $null
$redisHealth = $null
try {
    $ollamaHealth = Invoke-RestMethod -Uri "http://127.0.0.1:29134/api/tags" -TimeoutSec 10
} catch {
    $ollamaHealth = @{ error = $_.Exception.Message }
}

try {
    $redisHealth = docker exec jiege_v3_redis redis-cli ping
} catch {
    $redisHealth = $_.Exception.Message
}

$ok = ($ollamaHealth.models -ne $null) -and ($redisHealth -match "PONG")

Write-Report -Ok $ok -Stage "health-check" -Message $(if ($ok) { "v3 ai base services healthy" } else { "v3 ai base health check failed" }) -Extra ([pscustomobject]@{
    docker_compose_output = $upOutputText
    mount_checks = $mountChecks
    protected_old_services_still_running = $protectedRunning
    ollama_model_count = $(if ($ollamaHealth.models) { $ollamaHealth.models.Count } else { 0 })
    redis_ping = $redisHealth
}) | ConvertTo-Json -Depth 8

if (-not $ok) {
    exit 1
}
