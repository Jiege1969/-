# ============================================================
# Name: refresh-isolated-n8n-controlled.ps1
# Purpose: Refresh or restart only the isolated v3 n8n service so registered webhooks can take effect.
# Trigger: powershell -ExecutionPolicy Bypass -File 执行隔离n8n受控刷新重启.ps1
# Owner system: 01 core system.
# Dependencies: Docker Desktop; docker compose; docker-compose.n8n隔离.yml.
# Safety: High-risk controlled action. Only restart jiege_v3_n8n after explicit authorization. Does not touch old system containers, does not delete files or volumes, does not import, enable, or trigger workflows, does not send WeWork messages, does not write production DB, and does not call broker APIs or trading.
# Change log: 2026-04-28 created controlled isolated n8n refresh/restart script for webhook registration.
# ============================================================

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$coreRoot = Split-Path -Parent $scriptDir
$configDirName = "01" + [char]0x914D + [char]0x7F6E
$dataDirName = "03" + [char]0x6570 + [char]0x636E
$logDirName = "04" + [char]0x65E5 + [char]0x5FD7
$isolatedName = [string]([char]0x9694) + [string]([char]0x79BB)
$controlledName = [string]([char]0x53D7) + [string]([char]0x63A7)
$refreshName = [string]([char]0x5237) + [string]([char]0x65B0)
$restartName = [string]([char]0x91CD) + [string]([char]0x542F)
$composePath = Join-Path (Join-Path $coreRoot $configDirName) ("docker-compose.n8n" + $isolatedName + ".yml")
$dataPath = Join-Path (Join-Path $coreRoot $dataDirName) "n8n"
$logDir = Join-Path (Join-Path $coreRoot $logDirName) ($isolatedName + "n8n" + $controlledName + $refreshName + $restartName)
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportPath = Join-Path $logDir "isolated-n8n-controlled-refresh-restart-$timestamp.json"
$latestPath = Join-Path $logDir "isolated-n8n-controlled-refresh-restart-latest.json"

function Write-Result {
    param(
        [bool]$Ok,
        [string]$Stage,
        [string]$Message
    )
    $result = [pscustomobject]@{
        generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        ok = $Ok
        stage = $Stage
        message = $Message
        compose = $composePath
        data_path = $dataPath
        target_container = "jiege_v3_n8n"
        protected_container = "jiege_n8n"
        port = "127.0.0.1:28679"
        safety = [pscustomobject]@{
            old_system_write = $false
            old_system_restart = $false
            docker_compose_down = $false
            delete_volume = $false
            workflow_import = $false
            workflow_enable = $false
            workflow_trigger = $false
            wework_send = $false
            production_db_write = $false
            broker_api = $false
            auto_trade = $false
        }
    }
    $result | ConvertTo-Json -Depth 6 | Set-Content -Path $reportPath -Encoding UTF8
    $result | ConvertTo-Json -Depth 6 | Set-Content -Path $latestPath -Encoding UTF8
    return $result
}

if (-not (Test-Path -LiteralPath $composePath)) {
    Write-Result -Ok $false -Stage "preflight" -Message "compose file missing"
    exit 1
}

if (-not (Test-Path -LiteralPath $dataPath)) {
    Write-Result -Ok $false -Stage "preflight" -Message "data path missing"
    exit 1
}

$oldSystemContainer = docker ps --format "{{.Names}}" | Select-String "^jiege_n8n$"
if (-not $oldSystemContainer) {
    Write-Result -Ok $false -Stage "preflight" -Message "old system n8n was not detected; environment is unclear"
    exit 1
}

$targetContainer = docker ps --format "{{.Names}}" | Select-String "^jiege_v3_n8n$"
if (-not $targetContainer) {
    Write-Result -Ok $false -Stage "preflight" -Message "target isolated n8n is not running"
    exit 1
}

Push-Location (Split-Path -Parent $composePath)
try {
    docker compose -f $composePath restart n8n | Out-Null
} finally {
    Pop-Location
}

Start-Sleep -Seconds 8
$running = docker ps --filter "name=jiege_v3_n8n" --format "{{.Names}} {{.Status}} {{.Ports}}"
if (-not $running) {
    Write-Result -Ok $false -Stage "refresh_restart" -Message "jiege_v3_n8n is not running after restart"
    exit 1
}

try {
    $status = (Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:28679" -TimeoutSec 10).StatusCode
} catch {
    Write-Result -Ok $false -Stage "health_check" -Message $_.Exception.Message
    exit 1
}

if ($status -ne 200) {
    Write-Result -Ok $false -Stage "health_check" -Message "n8n health check status $status"
    exit 1
}

Write-Result -Ok $true -Stage "refresh_restart" -Message $running
Write-Output $running
exit 0
