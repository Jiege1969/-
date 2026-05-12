# ============================================================
# Name: v3-ai-base-healthcheck-light-repair.ps1
# Purpose: Check v3 Ollama and Redis health and run limited repair for v3-owned services only.
# Trigger: powershell -ExecutionPolicy Bypass -File 执行智能底座健康检查与轻修复.ps1 [-Repair]
# Owner system: 01 core system.
# Dependencies: Docker Desktop; PowerShell; 执行智能底座受控启动.ps1.
# Safety: Read-only by default. With -Repair, only starts v3-owned containers `jiege_v3_ollama` and `jiege_v3_redis`; does not stop old jiege_* services, does not delete data, does not trigger n8n, does not send WeWork messages, does not write old system data, and does not call broker APIs or trading.
# Change log: 2026-04-28 created healthcheck and light repair mechanism by absorbing old startup self-check design.
# ============================================================

[CmdletBinding()]
param(
    [switch]$Repair
)

$ErrorActionPreference = "Continue"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$coreRoot = Split-Path -Parent $scriptDir

function Join-Chars {
    param([int[]]$Codes)
    return -join ($Codes | ForEach-Object { [char]$_ })
}

$logDirName = "04" + (Join-Chars @(0x65E5, 0x5FD7))
$dataDirName = "03" + (Join-Chars @(0x6570, 0x636E))
$runtimeStateName = Join-Chars @(0x8FD0, 0x884C, 0x72B6, 0x6001)
$aiBaseName = Join-Chars @(0x667A, 0x80FD, 0x5E95, 0x5EA7)
$startScriptName = (Join-Chars @(0x6267, 0x884C, 0x667A, 0x80FD, 0x5E95, 0x5EA7, 0x53D7, 0x63A7, 0x542F, 0x52A8)) + ".ps1"

$logDir = Join-Path (Join-Path $coreRoot $logDirName) $aiBaseName
$stateDir = Join-Path (Join-Path $coreRoot $dataDirName) $runtimeStateName
$startScript = Join-Path $scriptDir $startScriptName
New-Item -ItemType Directory -Force -Path $logDir, $stateDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportPath = Join-Path $logDir "v3-ai-base-healthcheck-$timestamp.json"
$latestPath = Join-Path $logDir "v3-ai-base-healthcheck-latest.json"
$envPath = Join-Path $stateDir "system_health.env"

function Test-Port {
    param([string]$Port)
    $hit = netstat -ano | Select-String ":$Port"
    return [bool]$hit
}

function Get-ContainerStatus {
    param([string]$Name)
    $line = docker ps -a --filter "name=^/$Name$" --format "{{.Names}}|{{.Status}}" 2>$null
    if (-not $line) {
        return [pscustomobject]@{ exists = $false; running = $false; status = "missing" }
    }
    $parts = $line -split "\|", 2
    return [pscustomobject]@{
        exists = $true
        running = ($parts[1] -like "Up*")
        status = $parts[1]
    }
}

function Test-Ollama {
    param([int]$MaxWaitSec = 300)
    $deadline = (Get-Date).AddSeconds($MaxWaitSec)
    $lastError = ""
    do {
        try {
            $tags = Invoke-RestMethod -Uri "http://127.0.0.1:29134/api/tags" -TimeoutSec 8
            if ($null -ne $tags.models -and $tags.models.Count -gt 0) {
                return [pscustomobject]@{ ok = $true; model_count = $tags.models.Count; error = ""; waited = $true }
            }
            $lastError = "model list empty"
        } catch {
            $lastError = $_.Exception.Message
        }
        Start-Sleep -Seconds 5
    } while ((Get-Date) -lt $deadline)

    try {
        $tags = Invoke-RestMethod -Uri "http://127.0.0.1:29134/api/tags" -TimeoutSec 8
        return [pscustomobject]@{ ok = ($tags.models.Count -gt 0); model_count = $tags.models.Count; error = $(if ($tags.models.Count -gt 0) { "" } else { "model list empty after wait" }); waited = $true }
    } catch {
        return [pscustomobject]@{ ok = $false; model_count = 0; error = $lastError; waited = $true }
    }
}

function Test-Redis {
    try {
        $ping = docker exec jiege_v3_redis redis-cli ping 2>$null
        return [pscustomobject]@{ ok = ($ping -match "PONG"); response = $ping; error = "" }
    } catch {
        return [pscustomobject]@{ ok = $false; response = ""; error = $_.Exception.Message }
    }
}

$before = [pscustomobject]@{
    jiege_v3_ollama = Get-ContainerStatus "jiege_v3_ollama"
    jiege_v3_redis = Get-ContainerStatus "jiege_v3_redis"
    old_ollama = Get-ContainerStatus "ollama"
    old_redis = Get-ContainerStatus "redis"
    old_n8n = Get-ContainerStatus "n8n"
    protected_jiege_ollama = Get-ContainerStatus "jiege_ollama"
    protected_jiege_redis = Get-ContainerStatus "jiege_redis"
    port_29134_used = Test-Port "29134"
    port_26379_used = Test-Port "26379"
}

$repairOutput = $null
if ($Repair) {
    $needRepair = (-not $before.jiege_v3_ollama.running) -or (-not $before.jiege_v3_redis.running)
    if ($needRepair -and (Test-Path -LiteralPath $startScript)) {
        $repairOutput = powershell -ExecutionPolicy Bypass -File $startScript 2>&1
    } elseif (-not $needRepair) {
        $repairOutput = "no repair needed"
    } else {
        $repairOutput = "start script missing: $startScript"
    }
}

$ollamaHealth = Test-Ollama
$redisHealth = Test-Redis

$after = [pscustomobject]@{
    jiege_v3_ollama = Get-ContainerStatus "jiege_v3_ollama"
    jiege_v3_redis = Get-ContainerStatus "jiege_v3_redis"
    ollama_health = $ollamaHealth
    redis_health = $redisHealth
}

$ok = $ollamaHealth.ok -and $redisHealth.ok
$report = [pscustomobject]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    ok = $ok
    mode = $(if ($Repair) { "repair" } else { "readonly" })
    before = $before
    after = $after
    repair_output = $repairOutput
    conclusion = $(if ($ok) { "v3 ai base healthy" } elseif ($Repair) { "repair attempted but health check failed" } else { "health check failed; run with -Repair after reviewing" })
    safety = [pscustomobject]@{
        delete_files = $false
        stop_old_jiege_services = $false
        stop_protected_old_stock_system = $false
        n8n_trigger = $false
        wework_send = $false
        old_system_write = $false
        broker_api = $false
        auto_trade = $false
    }
}

$report | ConvertTo-Json -Depth 10 | Set-Content -Path $reportPath -Encoding UTF8
$report | ConvertTo-Json -Depth 10 | Set-Content -Path $latestPath -Encoding UTF8

$envLines = @(
    "GENERATED_AT=$($report.generated_at)",
    "V3_AI_BASE_OK=$($ok.ToString().ToLower())",
    "V3_OLLAMA_OK=$($ollamaHealth.ok.ToString().ToLower())",
    "V3_OLLAMA_MODEL_COUNT=$($ollamaHealth.model_count)",
    "V3_REDIS_OK=$($redisHealth.ok.ToString().ToLower())",
    "V3_HEALTHCHECK_MODE=$($report.mode)",
    "V3_HEALTHCHECK_REPORT=$reportPath",
    "OLD_JIEGE_SERVICE_STOPPED=false",
    "WEWORK_SEND=false",
    "AUTO_TRADE=false"
)
$envLines | Set-Content -Path $envPath -Encoding UTF8

$report | ConvertTo-Json -Depth 10

if (-not $ok) {
    exit 1
}
